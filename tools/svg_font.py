#!/usr/bin/env python3
"""Standalone exact centerline SVG -> bounded-chunk Regular TTF/WOFF2."""
from __future__ import annotations
import argparse, hashlib, json, math, os, re, struct, tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import fontTools
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph
from stroke_backend import build_font, codepoint_number
NS='{http://www.w3.org/2000/svg}'
TRANSFORM='matrix(1 0 0 -1 0 832)'

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomic(path,data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp'); tmp.write_bytes(data); os.replace(tmp,path)
def write_if_changed(path,data):
    path=Path(path)
    if path.exists() and path.read_bytes()==data: return False
    atomic(path,data); return True

def read_svg(path):
    path=Path(path); root=ET.fromstring(path.read_bytes())
    if root.tag!=NS+'svg' or root.get('viewBox')!='0 0 1024 1024': raise ValueError('Expected 1024 SVG viewBox')
    cp=codepoint_number(root.attrib['data-codepoint'])
    if path.stem!=f'U{cp:05X}': raise ValueError('SVG filename/codepoint mismatch')
    if set(root.attrib)-{'viewBox','data-codepoint','data-advance','data-schema'}: raise ValueError('Unsupported root SVG attributes')
    if root.get('data-advance')!='1024' or root.get('data-schema')!='seal-centerline-1': raise ValueError('Unsupported SVG schema/advance')
    children=list(root)
    if len(children)!=1: raise ValueError('Expected one centerline group')
    group=children[0]
    expected={'transform':TRANSFORM,'fill':'none','stroke':'#000','stroke-width':'30','stroke-linecap':'round','stroke-linejoin':'round'}
    if group.tag!=NS+'g' or group.attrib!=expected: raise ValueError('Unsupported group transform/stroke attributes')
    strokes=[]
    token=re.compile(r'[MLZ]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')
    for node in group:
        if node.tag!=NS+'path' or set(node.attrib)-{'id','d'}: raise ValueError('Only untransformed M/L/Z paths supported')
        text=node.attrib['d']; tokens=token.findall(text)
        if token.sub('',text).strip(' ,\t\n\r'): raise ValueError('Unsupported path command')
        if not tokens or tokens[0]!='M': raise ValueError('Path must begin M')
        points=[]; i=0; closed=False
        while i<len(tokens):
            command=tokens[i]; i+=1
            if command=='Z':
                if i!=len(tokens): raise ValueError('Z must terminate path')
                closed=True; break
            if command not in ('M','L') or (command=='M' and points): raise ValueError('One subpath per stroke required')
            if i+1>=len(tokens): raise ValueError('Incomplete point')
            x,y=float(tokens[i]),float(tokens[i+1]); i+=2
            if not math.isfinite(x+y): raise ValueError('Nonfinite coordinate')
            points.append((x,y))
        if not points: raise ValueError('Empty stroke')
        strokes.append((points,closed))
    if not strokes: raise ValueError('Empty glyph')
    return {'codepoint':cp,'width':30.0,'strokes':strokes}

def raw_records(font):
    offsets=font['loca'].locations; raw=font.getTableData('glyf'); order=font.getGlyphOrder()
    return {n:raw[offsets[i]:offsets[i+1]] for i,n in enumerate(order)}

def merge_static(paths,target,expected):
    """Retain serialized glyphs; never globally expand completed chunks."""
    first=TTFont(paths[0],recalcBBoxes=False,recalcTimestamp=False)
    for tag in ('glyf','hmtx','cmap','maxp'): first[tag]
    records={}; metrics={}; cmap={}; maximum={}; horizontal={}; bounds=[]
    for path in paths:
        with TTFont(path,lazy=True,recalcBBoxes=False,recalcTimestamp=False) as font:
            if 'gvar' in font or 'HVAR' in font: raise ValueError('Only static fonts supported')
            if font['hhea'].lineGap!=first['hhea'].lineGap: raise ValueError('Inconsistent line gap')
            if font.getTableData('name')!=first.getTableData('name'): raise ValueError('Inconsistent names')
            for name,raw in raw_records(font).items():
                if len(raw)>=2 and struct.unpack('>h',raw[:2])[0]<0: raise ValueError('Composites unsupported')
                metric=font['hmtx'][name]
                if name in records:
                    if name!='.notdef' or records[name]!=raw or metrics[name]!=metric: raise ValueError('Duplicate/different glyph')
                    continue
                records[name]=raw; metrics[name]=metric
            for cp,name in font.getBestCmap().items():
                if cp in cmap: raise ValueError('Duplicate codepoint')
                cmap[cp]=name
            bounds.append([getattr(font['head'],k) for k in ('xMin','yMin','xMax','yMax')])
            for key,value in vars(font['maxp']).items():
                if key.startswith('max') and isinstance(value,int): maximum[key]=max(maximum.get(key,0),value)
            for key in ('advanceWidthMax','minLeftSideBearing','minRightSideBearing','xMaxExtent','ascent','descent'):
                value=getattr(font['hhea'],key); horizontal[key]=(min if key.startswith('min') or key=='descent' else max)(horizontal.get(key,value),value)
    if cmap!=expected: raise ValueError('Merged cmap differs from SVG manifest')
    order=['.notdef']+[cmap[cp] for cp in sorted(cmap)]
    if set(order)!=set(records): raise ValueError('Unexpected glyphs')
    first.setGlyphOrder(order); first['glyf'].glyphOrder=order
    first['glyf'].glyphs={n:Glyph(data=records[n]) for n in order}; first['hmtx'].metrics=metrics
    first['maxp'].numGlyphs=len(order)
    for key,value in maximum.items(): setattr(first['maxp'],key,value)
    for key,value in horizontal.items(): setattr(first['hhea'],key,value)
    for i,key in enumerate(('xMin','yMin','xMax','yMax')): setattr(first['head'],key,(min if i<2 else max)(b[i] for b in bounds))
    for table in first['cmap'].tables:
        if table.isUnicode():
            table.ensureDecompiled(); table.data=None; table.cmap={cp:n for cp,n in cmap.items() if table.format in (12,13) or cp<=65535}
    os2=first['OS/2']; os2.sTypoAscender=horizontal['ascent']; os2.sTypoDescender=horizontal['descent']; os2.usWinAscent=horizontal['ascent']; os2.usWinDescent=-horizontal['descent']
    os2.recalcUnicodeRanges(first); os2.recalcAvgCharWidth(first)
    os2.usFirstCharIndex=min(min(cmap),65535); os2.usLastCharIndex=min(max(cmap),65535)
    first.save(target); first.close()
    with TTFont(target,lazy=True) as check:
        if check.getBestCmap()!=expected or check.getGlyphOrder()!=order or check['hmtx'].metrics!=metrics or raw_records(check)!=records: raise ValueError('Serialized readback mismatch')

def build(svg_dir,output,family='Panorama Gothic Seal Individual',chunk_size=64,woff2=True):
    svg_dir=Path(svg_dir); output=Path(output)
    if not 1<=chunk_size<=64: raise ValueError('Chunk size must be 1..64')
    manifest=json.loads((svg_dir/'manifest.json').read_bytes()); rows=manifest['glyphs']
    if not rows: raise ValueError('Empty SVG manifest')
    cps=[codepoint_number(r['codepoint']) for r in rows]
    if cps!=sorted(set(cps)): raise ValueError('Manifest must have unique sorted codepoints')
    expected={cp:f'u{cp:05X}' for cp in cps}; output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.svg-build-',dir=output) as tmp:
        tmp=Path(tmp); paths=[]
        for start in range(0,len(rows),chunk_size):
            sources=[]
            for row,cp in zip(rows[start:start+chunk_size],cps[start:start+chunk_size]):
                path=svg_dir/f'U{cp:05X}.svg'
                if digest(path)!=row['svg_sha256']: raise ValueError(f'SVG hash mismatch: {path.name}; refresh manifest after intentional edits')
                source=read_svg(path)
                if source['codepoint']!=cp: raise ValueError('Manifest/codepoint mismatch')
                sources.append(source)
            target=tmp/f'chunk-{start:05}.ttf'; build_font(sources,target,family,font_stroke_width=30.0); paths.append(target)
        target=tmp/'Regular.ttf'; merge_static(paths,target,expected)
        files={'Regular.ttf':digest(target)}
        if woff2:
            with TTFont(target,recalcBBoxes=False,recalcTimestamp=False) as font:
                font.flavor='woff2'; font.save(tmp/'Regular.woff2')
            with TTFont(tmp/'Regular.woff2') as check:
                if check.getBestCmap()!=expected: raise ValueError('WOFF2 cmap mismatch')
            files['Regular.woff2']=digest(tmp/'Regular.woff2')
        report={'schema_version':1,'glyph_count':len(rows),'family':family,'units_per_em':1024,'weight':400,'pen_width':30,'chunk_size':chunk_size,'fonttools':fontTools.__version__,'svg_manifest_sha256':digest(svg_dir/'manifest.json'),'code_sha256':{p.name:digest(p) for p in (Path(__file__),Path(__file__).with_name('stroke_backend.py'))},'files':files}
        for name in files: atomic(output/name,(tmp/name).read_bytes())
        atomic(output/'build-manifest.json',(json.dumps(report,indent=2)+'\n').encode())
    return report

def refresh(svg_dir):
    path=Path(svg_dir)/'manifest.json'; data=json.loads(path.read_bytes())
    for row in data['glyphs']:
        cp=codepoint_number(row['codepoint']); file=path.parent/f'U{cp:05X}.svg'; read_svg(file); row['svg_sha256']=digest(file)
    atomic(path,(json.dumps(data,indent=2)+'\n').encode())
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--svg-dir',type=Path,default=Path('svg')); p.add_argument('--output',type=Path,default=Path('fonts')); p.add_argument('--family',default='Panorama Gothic Seal Individual'); p.add_argument('--chunk-size',type=int,default=64); p.add_argument('--refresh-manifest',action='store_true'); p.add_argument('--no-woff2',action='store_true'); a=p.parse_args()
    if a.refresh_manifest: refresh(a.svg_dir)
    else: print(json.dumps(build(a.svg_dir,a.output,a.family,a.chunk_size,not a.no_woff2),indent=2))
