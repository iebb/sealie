#!/usr/bin/env python3
"""Build Regular and 300–700 variable fonts from canonical centerline SVGs.

All five named-weight masters use one source geometry. At most 64 glyphs are
expanded at once. Completed chunks are merged as serialized glyph/variation
data; there is no full-font outline expansion or variable instancing.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, logging, math, os, struct, tempfile, time
import fontTools
import pathops
from pathlib import Path
from functools import partial
from collections import deque
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables.DefaultTable import DefaultTable
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.ttLib.tables._g_v_a_r import compileGlyph_
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.varLib.models import VariationModel
from fontTools.varLib.iup import iup_delta_optimize
from compact_backend import compatible_masters
from stroke_backend import expand_polylines
from svg_font import read_svg, digest, atomic, raw_records

WEIGHTS = [300, 400, 500, 600, 700]
WIDTHS = [23.5, 30.0, 36.5, 43.0, 49.5]
STYLES = ['Light', 'Regular', 'Medium', 'SemiBold', 'Bold']
MODEL = VariationModel([{'wght': (w-400)/(100 if w<400 else 300)}
                        if w != 400 else {} for w in WEIGHTS], ['wght'])


def payload_size(variation):
    points = variation.getUsedPoints()
    if points is None:
        return 0
    if points and len(points) > 0x7FFF:
        return 0x10000
    return len(variation.compilePoints(points)) + len(variation.compileDeltas())


def encode_variation(variation, coordinates, end_points):
    optimized = TupleVariation(variation.axes, iup_delta_optimize(
        variation.coordinates, coordinates, end_points, tolerance=0.5))
    raw_size, opt_size = payload_size(variation), payload_size(optimized)
    chosen = optimized if opt_size < raw_size else variation
    if min(raw_size, opt_size) <= 0xFFFF:
        return [chosen] if chosen.getUsedPoints() is not None else []
    # Format-safe additive blocks; explicit zeros prevent unintended IUP.
    output = []
    for start in range(0, len(variation.coordinates), 8192):
        block = variation.coordinates[start:start+8192]
        if not any(delta != (0, 0) for delta in block):
            continue
        coordinates = [(0, 0)] * len(variation.coordinates)
        coordinates[start:start+len(block)] = block
        part = TupleVariation(variation.axes, coordinates)
        if payload_size(part) > 0xFFFF:
            raise ValueError('Split variation exceeds tuple limit')
        output.append(part)
    return output


def gvar_bytes(blocks, axis_count=1):
    offsets = [0]
    for block in blocks:
        offsets.append(offsets[-1] + len(block))
    start = 20 + 4 * len(offsets)
    return (struct.pack('>HHHHIHHI', 1, 0, axis_count, 0, start,
                        len(blocks), 1, start)
            + struct.pack('>' + str(len(offsets)) + 'I', *offsets)
            + b''.join(blocks))


def raw_variations(font):
    raw = font.getTableData('gvar')
    version, reserved, axes, shared, shared_at, count, flags, start = struct.unpack('>HHHHIHHI', raw[:20])
    if version != 1 or reserved or shared or axes != 1 or flags != 1:
        raise ValueError('Expected explicit-peak long-offset gvar')
    offsets = struct.unpack('>' + str(count+1) + 'I', raw[20:20+4*(count+1)])
    order = font.getGlyphOrder()
    if count != len(order):
        raise ValueError('gvar/glyph count mismatch')
    return {name: raw[start+offsets[i]:start+offsets[i+1]] for i, name in enumerate(order)}


def make_font(glyphs, cps, family, style, weight, variable=False):
    fb = FontBuilder(1024, isTTF=True)
    order = ['.notdef'] + [f'u{cp:05X}' for cp in cps]
    for glyph in glyphs.values():
        glyph.recalcBounds(None)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({cp:f'u{cp:05X}' for cp in cps})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({name:(1024, glyph.xMin) for name, glyph in glyphs.items()})
    fb.setupHorizontalHeader(ascent=896, descent=-192, lineGap=0)
    base = ''.join(c for c in family if c.isascii() and c.isalnum())
    fb.setupNameTable({
        'copyright':'Copyright 2026 ieb and Sealie contributors.',
        'familyName':family, 'styleName':style,
        'uniqueFontIdentifier':f'{base};1.0;{style}',
        'fullName':family+' '+style, 'psName':base+'-'+style,
        'version':'Version 1.0; normalized SVG source',
        'description':'Small Seal rounded monoline; SVG sources and normalization history accompany this font.',
        'licenseDescription':'Licensed under the SIL Open Font License, Version 1.1.',
        'licenseInfoURL':'https://openfontlicense.org/',
        'typographicFamily':family, 'typographicSubfamily':style,
    })
    selection = (1<<5) if weight >= 700 else ((1<<6) if weight == 400 else 0)
    fb.setupOS2(sTypoAscender=896, sTypoDescender=-192, sTypoLineGap=0,
                usWinAscent=896, usWinDescent=192, usWeightClass=weight,
                fsSelection=selection, sxHeight=512, sCapHeight=704)
    fb.setupPost(keepGlyphNames=True)
    fb.setupMaxp()
    fb.font['head'].created = fb.font['head'].modified = 3875126400
    fb.font['head'].fontRevision = 1.0
    fb.font['head'].macStyle = 1 if weight >= 700 else 0
    fb.font.recalcTimestamp = False
    if variable:
        fb.setupFvar([('wght', 300, 400, 700, 'Weight')],
                     [{'location':{'wght':w},'stylename':s} for w,s in zip(WEIGHTS,STYLES)])
    return fb.font


def save_webfont(path, target, flavor='woff'):
    with TTFont(path, recalcBBoxes=False, recalcTimestamp=False) as font:
        font.flavor = flavor
        font.save(target)


def build_chunk(rows, svg_dir, folder, family):
    folder.mkdir(parents=True, exist_ok=True)
    for row in rows:
        cp = int(row['codepoint'][2:],16)
        if digest(svg_dir/f'U{cp:05X}.svg') != row['svg_sha256']:
            raise ValueError('Stale SVG manifest: '+row['codepoint'])
    identity = hashlib.sha256(json.dumps({'rows':rows,'family':family,
        'tool':digest(__file__),'backend':digest(Path(__file__).with_name('compact_backend.py')),
        'reader':digest(Path(read_svg.__code__.co_filename)),
        'legacy':digest(Path(expand_polylines.__code__.co_filename)),
        'fonttools':fontTools.__version__,'skia_pathops':pathops.__version__},sort_keys=True).encode()).hexdigest()
    marker = folder/'complete.json'
    if marker.exists():
        old = json.loads(marker.read_text())
        if old['identity'] == identity and all((folder/name).exists() and digest(folder/name)==sha for name,sha in old['files'].items()):
            return old
    cps = [int(row['codepoint'][2:],16) for row in rows]
    notdef,_ = expand_polylines([([(160,0),(160,640),(640,640),(640,0)],True)],16)
    masters = [{'.notdef':notdef} for _ in WEIGHTS]
    variations = {'.notdef':[]}
    fallbacks = []
    bounds = []
    for row,cp in zip(rows,cps):
        path = svg_dir/f'U{cp:05X}.svg'
        if digest(path) != row['svg_sha256']:
            raise ValueError('Stale SVG manifest: '+path.name)
        source = read_svg(path)
        candidates, fallback = compatible_masters(source['strokes'], WIDTHS, expand_polylines)
        if fallback:
            fallbacks.append(row['codepoint'])
        name = f'u{cp:05X}'
        coordinates = []
        for index,(glyph,_) in enumerate(candidates):
            if not glyph.numberOfContours:
                raise ValueError('Empty generated glyph: '+name)
            glyph.recalcBounds(None)
            if glyph.xMin < 0 or glyph.xMax > 1024 or glyph.yMin < -192 or glyph.yMax > 896:
                raise ValueError('Glyph exceeds fixed em/line metrics: '+name)
            masters[index][name] = glyph
            coordinates.append(GlyphCoordinates(list(glyph.coordinates)+[(0,0),(1024,0),(0,0),(0,0)]))
        deltas = MODEL.getDeltas(coordinates,
            round=partial(GlyphCoordinates.__round__, round=round))
        base = coordinates[1]
        default = candidates[1][0]
        encoded = []
        for delta,support in zip(deltas[1:],MODEL.supports[1:]):
            if any(x or y for x,y in delta):
                encoded.extend(encode_variation(TupleVariation(support,list(delta)),base,default.endPtsOfContours))
        variations[name] = encoded
        bounds.append({'codepoint':row['codepoint'],'regular':[default.xMin,default.yMin,default.xMax,default.yMax],
                       'points':len(default.coordinates),'fallback':fallback})
    files = {}
    for index,style in enumerate(STYLES):
        font = make_font(masters[index], cps, family, style, WEIGHTS[index])
        target = folder/(style+'.ttf')
        font.save(target);font.close()
        files[target.name] = digest(target)
    font = make_font(masters[1],cps,family,'Regular',400,variable=True)
    blocks = [compileGlyph_(2,variations[name],0,['wght'],{},optimizeSize=True) if variations[name] else b''
              for name in font.getGlyphOrder()]
    raw = DefaultTable('gvar');raw.data = gvar_bytes(blocks);font['gvar'] = raw
    target = folder/'Variable.ttf';font.save(target);font.close()
    files[target.name] = digest(target)
    report = {'identity':identity,'glyph_count':len(cps),'fallbacks':fallbacks,'bounds':bounds,'files':files}
    atomic(marker,(json.dumps(report,indent=2)+'\n').encode())
    return report


def merge_chunks(paths, target, expected):
    first = TTFont(paths[0],recalcBBoxes=False,recalcTimestamp=False)
    for tag in ['glyf','hmtx','cmap','maxp']:
        first[tag]
    records, metrics, cmap, variations = {}, {}, {}, {}
    maximum, head_bounds = {}, []
    variable = 'gvar' in first
    for path in paths:
        with TTFont(path,recalcBBoxes=False,recalcTimestamp=False) as font:
            if ('gvar' in font) != variable:
                raise ValueError('Mixed static/variable chunks')
            for tag in ['name','fvar']:
                if (tag in font)!=(tag in first) or (tag in font and font.getTableData(tag)!=first.getTableData(tag)):
                    raise ValueError('Inconsistent chunk '+tag)
            raw = raw_records(font)
            delta = raw_variations(font) if variable else {}
            for name,block in raw.items():
                metric = font['hmtx'][name]
                if name in records:
                    if name!='.notdef' or records[name]!=block or metrics[name]!=metric or (variable and variations[name]!=delta[name]):
                        raise ValueError('Duplicate/different glyph '+name)
                    continue
                records[name],metrics[name] = block,metric
                if variable:variations[name] = delta[name]
            for cp,name in font.getBestCmap().items():
                if cp in cmap:raise ValueError('Duplicate codepoint')
                cmap[cp] = name
            head_bounds.append([getattr(font['head'],k) for k in ['xMin','yMin','xMax','yMax']])
            for key,value in vars(font['maxp']).items():
                if key.startswith('max') and isinstance(value,int):maximum[key] = max(maximum.get(key,0),value)
    if cmap != expected:raise ValueError('Merged repertoire mismatch')
    order = ['.notdef']+[cmap[cp] for cp in sorted(cmap)]
    first.setGlyphOrder(order);first['glyf'].glyphOrder=order
    first['glyf'].glyphs={name:Glyph(data=records[name]) for name in order}
    first['hmtx'].metrics=metrics;first['maxp'].numGlyphs=len(order)
    for key,value in maximum.items():setattr(first['maxp'],key,value)
    for i,key in enumerate(['xMin','yMin','xMax','yMax']):setattr(first['head'],key,(min if i<2 else max)(b[i] for b in head_bounds))
    first['hhea'].advanceWidthMax=1024
    first['hhea'].minLeftSideBearing=min(m[1] for m in metrics.values())
    first['hhea'].minRightSideBearing=min(1024-m[1]-(struct.unpack('>hhhh',records[n][2:10])[2]-struct.unpack('>hhhh',records[n][2:10])[0]) for n,m in metrics.items())
    first['hhea'].xMaxExtent=max(struct.unpack('>hhhh',raw[2:10])[2] for raw in records.values())
    for table in first['cmap'].tables:
        if table.isUnicode():
            table.ensureDecompiled();table.data=None
            table.cmap={cp:name for cp,name in cmap.items() if table.format in [12,13] or cp<=65535}
    first['OS/2'].recalcUnicodeRanges(first);first['OS/2'].recalcAvgCharWidth(first)
    first['OS/2'].usFirstCharIndex=min(min(cmap),65535);first['OS/2'].usLastCharIndex=min(max(cmap),65535)
    if variable:
        table=DefaultTable('gvar');table.data=gvar_bytes([variations[n] for n in order]);first['gvar']=table
    first.save(target);first.close()
    with TTFont(target,lazy=True,recalcBBoxes=False,recalcTimestamp=False) as font:
        if font.getBestCmap()!=expected or font.getGlyphOrder()!=order or font['hmtx'].metrics!=metrics:
            raise ValueError('Saved cmap/order/metrics mismatch')
        # Serialized glyf blocks may acquire padding; require canonical content.
        saved=raw_records(font)
        for name,raw in records.items():
            if not saved[name].startswith(raw) or any(saved[name][len(raw):]):
                raise ValueError('Saved glyph bytes mismatch '+name)
        if variable and raw_variations(font)!=variations:
            raise ValueError('Saved variation bytes mismatch')


def build(svg_dir, output, cache, family='Sealie', chunk_size=64, woff2=False, workers=None):
    started=time.monotonic();svg_dir=Path(svg_dir);output=Path(output);cache=Path(cache)
    manifest=json.loads((svg_dir/'manifest.json').read_text());rows=manifest['glyphs']
    cps=[int(row['codepoint'][2:],16) for row in rows]
    if not rows or cps!=sorted(set(cps)) or not 1<=chunk_size<=64:
        raise ValueError('Expected sorted unique repertoire and chunk size1–64')
    output.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
    web=output/'variable';web.mkdir(exist_ok=True)
    folders=[];reports=[];css=['/* Normalized Sealie; weights300–700; SVG sources in repository. */']
    jobs=[]
    for start in range(0,len(rows),chunk_size):
        selected=rows[start:start+chunk_size];first,last=selected[0]['codepoint'][2:],selected[-1]['codepoint'][2:]
        stem=f'U{first}-U{last}';folder=cache/stem
        jobs.append((selected,svg_dir,folder,family,web))
    worker_count=min(4,max(1,workers or os.cpu_count() or 1))
    with concurrent.futures.ProcessPoolExecutor(max_workers=worker_count) as pool:
        # Bound submitted work and return results in deterministic repertoire
        # order. At most four complete chunks are running or awaiting receipt.
        submitted=min(worker_count,len(jobs))
        pending=deque(pool.submit(_build_chunk_job,job) for job in jobs[:submitted])
        for number,(selected,_,folder,_,_) in enumerate(jobs,1):
            report=pending.popleft().result()
            if submitted<len(jobs):
                pending.append(pool.submit(_build_chunk_job,jobs[submitted]));submitted+=1
            first,last=selected[0]['codepoint'][2:],selected[-1]['codepoint'][2:]
            stem=folder.name;folders.append(folder);reports.append(report)
            target=web/(stem+'.woff')
            css.append('@font-face{font-family:"Seal";src:url("variable/'+target.name+'") format("woff");font-style:normal;font-weight:300 700;font-display:swap;unicode-range:U+'+first+'-'+last+';}')
            print(json.dumps({'phase':'chunks','complete':number,'total':math.ceil(len(rows)/chunk_size),'fallbacks':sum(len(r['fallbacks']) for r in reports),'elapsed_seconds':round(time.monotonic()-started,1)}),flush=True)
    expected={cp:f'u{cp:05X}' for cp in cps}
    for style in STYLES+['Variable']:
        target=output/(style+'.ttf');merge_chunks([p/(style+'.ttf') for p in folders],target,expected)
        print(json.dumps({'phase':'merged','style':style,'bytes':target.stat().st_size}),flush=True)
    for style in ['Regular','Variable']:
        save_webfont(output/(style+'.ttf'),output/(style+'.woff'))
    if woff2:save_webfont(output/'Regular.ttf',output/'Regular.woff2','woff2')
    atomic(output/'variable.css',('\n'.join(css)+'\n').encode())
    files=[p for p in output.iterdir() if p.is_file() and p.suffix in ['.ttf','.woff','.woff2','.css']]+sorted(web.glob('*.woff'))
    report={'schema_version':1,'glyph_count':len(cps),'family':family,
            'svg_manifest_sha256':digest(svg_dir/'manifest.json'),
            'axis':{'tag':'wght','minimum':300,'default':400,'maximum':700},
            'pen_widths':dict(zip(map(str,WEIGHTS),WIDTHS)),
            'backend':'analytic round strokes; compatible legacy fallback per glyph',
            'fallback_glyphs':[cp for r in reports for cp in r['fallbacks']],
            'source_polylines_simplified':False,'chunk_size':chunk_size,
            'elapsed_seconds':time.monotonic()-started,
            'files':[{'name':str(p.relative_to(output)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in files]}
    atomic(output/'build-manifest.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def _build_chunk_job(arguments):
    rows,svg_dir,folder,family,web=arguments
    report=build_chunk(rows,svg_dir,folder,family)
    target=web/(folder.name+'.woff')
    cached=report.get('webfont',{})
    if not target.exists() or cached.get('sha256')!=digest(target):
        save_webfont(folder/'Variable.ttf',target)
        report['webfont']={'name':target.name,'bytes':target.stat().st_size,'sha256':digest(target)}
        atomic(folder/'complete.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--svg-dir',type=Path,default=Path('svg'))
    p.add_argument('--output',type=Path,default=Path('build'))
    p.add_argument('--cache',type=Path)
    p.add_argument('--family',default='Sealie')
    p.add_argument('--chunk-size',type=int,default=64)
    p.add_argument('--woff2',action='store_true')
    p.add_argument('--workers',type=int,default=min(4,os.cpu_count() or 1))
    a=p.parse_args();build(a.svg_dir,a.output,a.cache or a.output/'.build-cache',a.family,a.chunk_size,a.woff2,a.workers)
