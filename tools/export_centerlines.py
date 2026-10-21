#!/usr/bin/env python3
"""Incrementally export reviewed source JSON as standalone editable SVGs."""
from __future__ import annotations
import argparse, hashlib, json
import fontTools
from pathlib import Path
from stroke_backend import codepoint_number, source_transform, flatten_path, normalize_sources
from svg_font import digest, write_if_changed

def geometry_hash(data):
    geometry={key:data[key] for key in ('viewBox','stroke_width','strokes')}
    return hashlib.sha256(json.dumps(geometry,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def source_from_json(data):
    transform,scale=source_transform(data['viewBox'])
    if data.get('linecap','round')!='round' or data.get('linejoin','round')!='round': raise ValueError('Only round cap/join supported')
    strokes=[]
    for stroke in data['strokes']:
        points,closed=flatten_path(stroke['path'],stroke.get('closed'))
        strokes.append(([transform(point) for point in points],closed))
    return normalize_sources([{'codepoint':codepoint_number(data['codepoint']),'width':30.0,'strokes':strokes}],738.0)[0]

def svg_bytes(source):
    cp=source['codepoint']
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" data-codepoint="U+{cp:05X}" data-advance="1024" data-schema="seal-centerline-1">',
           '  <g transform="matrix(1 0 0 -1 0 832)" fill="none" stroke="#000" stroke-width="30" stroke-linecap="round" stroke-linejoin="round">']
    for i,(points,closed) in enumerate(source['strokes'],1):
        d=' '.join(('M' if j==0 else 'L')+' '+repr(x)+' '+repr(y) for j,(x,y) in enumerate(points))+(' Z' if closed else '')
        lines.append(f'    <path id="stroke-{i}" d="{d}"/>')
    return ('\n'.join(lines+['  </g>','</svg>',''])).encode()

def export_identity():
    return {'format':'seal-centerline-1','exact_float_serialization':1,
            'normalization_extent':738.0,'pen_width':30.0,
            'backend_sha256':digest(Path(__file__).with_name('stroke_backend.py')),
            'fonttools':fontTools.__version__}

def artifact_stat(path):
    stat=path.stat()
    return {'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns,'ctime_ns':stat.st_ctime_ns}

def export(source_root,registry,output,codepoints=None):
    source_root=Path(source_root); output=Path(output)
    data=json.loads(Path(registry).read_bytes())
    if data.get('schema_version')!=1: raise ValueError('Unsupported acceptance registry')
    entries={}
    for entry in data['glyphs']:
        cp=codepoint_number(entry['codepoint'])
        if cp in entries: raise ValueError('Duplicate registry codepoint')
        entries[cp]=entry
    selected=set(entries) if codepoints is None else set(codepoints)
    if not selected or not selected<=set(entries): raise ValueError('Requested codepoints are absent from registry')
    identity=export_identity()
    prior={}; cached={}
    manifest_path=output/'manifest.json'; cache_path=output/'.export-cache.json'
    try:
        old=json.loads(manifest_path.read_bytes())
        cache=json.loads(cache_path.read_bytes())
        if (old.get('export_identity')==identity and cache.get('export_identity')==identity
                and cache.get('manifest_sha256')==digest(manifest_path)):
            prior={codepoint_number(r['codepoint']):r for r in old['glyphs']}
            cached=cache.get('artifacts',{})
    except (FileNotFoundError,ValueError,KeyError,TypeError):
        pass # Missing/stale optional cache never weakens normal export validation.
    rows=[]; changed=0; reused=0; artifacts={}

    for cp in sorted(selected):
        filename=f'U{cp:05X}.json'; source=source_root/filename
        if not source.exists(): source=source_root/'auto'/filename
        raw=source.read_bytes(); source_hash=hashlib.sha256(raw).hexdigest(); entry=entries[cp]
        destination=output/f'U{cp:05X}.svg'; previous=prior.get(cp); cache_entry=cached.get(f'U{cp:05X}')
        if (previous and cache_entry and destination.is_file()
                and previous.get('source_sha256')==source_hash
                and previous.get('geometry_sha256')==entry['geometry_sha256']
                and cache_entry.get('svg_sha256')==previous.get('svg_sha256')
                and cache_entry.get('stat')==artifact_stat(destination)):
            rows.append(previous); artifacts[f'U{cp:05X}']=cache_entry; reused+=1
            continue
        item=json.loads(raw)
        if codepoint_number(item['codepoint'])!=cp or item.get('visual_reference_match_reviewed') is not True: raise ValueError(f'U+{cp:X}: unreviewed source')
        geometry=geometry_hash(item)
        if geometry!=entry['geometry_sha256']: raise ValueError(f'U+{cp:X}: stale accepted geometry')
        content=svg_bytes(source_from_json(item)); changed+=write_if_changed(destination,content)
        artifacts[f'U{cp:05X}']={'svg_sha256':hashlib.sha256(content).hexdigest(),'stat':artifact_stat(destination)}
        rows.append({'codepoint':f'U+{cp:05X}','svg_sha256':hashlib.sha256(content).hexdigest(),'source_sha256':hashlib.sha256(raw).hexdigest(),'geometry_sha256':geometry})
    manifest={'schema_version':1,'format':'seal-centerline-1','units_per_em':1024,'advance':1024,'baseline':832,'pen_width':30,'normalization_extent':738,'registry_sha256':digest(registry),'export_identity':identity,'glyphs':rows}
    write_if_changed(output/'manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())
    write_if_changed(cache_path,(json.dumps({'schema_version':1,'export_identity':identity,'manifest_sha256':digest(manifest_path),'artifacts':artifacts},indent=2)+'\n').encode())
    return {'reused_without_flattening':reused,'flattened_sources':len(rows)-reused,'glyph_count':len(rows),'changed_svg_files':changed,'unchanged_svg_files':len(rows)-changed,'manifest_sha256':digest(output/'manifest.json')}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--source-root',required=True,type=Path); p.add_argument('--registry',required=True,type=Path); p.add_argument('--output',type=Path,default=Path('svg')); p.add_argument('--codepoints',nargs='*',help='Optional U+... subset for validation'); a=p.parse_args()
    print(json.dumps(export(a.source_root,a.registry,a.output,None if a.codepoints is None else [codepoint_number(cp) for cp in a.codepoints]),indent=2))
