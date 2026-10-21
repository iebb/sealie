#!/usr/bin/env python3
"""Incrementally export accepted Small Seal glyphs as transparent 16x16 PNGs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont, __version__ as PILLOW_VERSION, features

FIRST, LAST = 0x3D000, 0x3FC3F
PIXELS, SUPERSAMPLE = 16, 8
EXPECTED_METRICS = {'units_per_em': 1024, 'advance': 1024, 'baseline': 832,
                    'pen_width': 30, 'normalization_extent': 738}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


def write_json(path, value):
    temp = path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temp, path)


def export(font_path, source_manifest, geometry_manifest, output, expected_font_sha=None):
    source_bytes = source_manifest.read_bytes()
    geometry_bytes = geometry_manifest.read_bytes()
    source = json.loads(source_bytes)
    geometry = json.loads(geometry_bytes)
    for key, value in EXPECTED_METRICS.items():
        if geometry.get(key) != value:
            raise ValueError(f'Unexpected shared {key}: {geometry.get(key)!r}')
    if source['registry_sha256'] != geometry['registry_sha256']:
        raise ValueError('Production and accepted-SVG registry bindings differ')
    sources = {row['codepoint']: row for row in source['sources']}
    accepted = {row['codepoint']: row for row in geometry['glyphs']}
    if len(sources) != len(source['sources']) or len(accepted) != len(geometry['glyphs']):
        raise ValueError('Duplicate codepoint')
    if sources.keys() != accepted.keys():
        raise ValueError('Production sources and accepted glyph delivery differ')
    if not all(FIRST <= int(cp[2:], 16) <= LAST for cp in accepted):
        raise ValueError('Codepoint outside Small Seal')
    font_sha = sha(font_path)
    if expected_font_sha and font_sha != expected_font_sha:
        raise ValueError('Production Regular font fingerprint differs')
    settings = {'schema': 1, 'weight': 400, 'pixels': [PIXELS, PIXELS],
        'mode': 'RGBA', 'color': [0, 0, 0], 'background_alpha': 0,
        'supersample': SUPERSAMPLE, 'downsample': 'LANCZOS',
        'anchor': 'ls', 'origin_font_units': [0, 832],
        'metrics': EXPECTED_METRICS, 'renderer': 'Pillow.FreeType',
        'pillow_version': PILLOW_VERSION,
        'freetype_version': features.version_module('freetype2'),
        'outline_export_identity': geometry['export_identity']}
    output.mkdir(parents=True, exist_ok=True)
    index = output / 'manifest.json'
    old = json.loads(index.read_text()) if index.exists() else {}
    prior = {row['codepoint']: row for row in old.get('glyphs', [])}
    font = None
    rows = []
    rendered = reused = removed = 0
    for cp in sorted(accepted, key=lambda label: int(label[2:], 16)):
        row = sources[cp]
        glyph = accepted[cp]
        if glyph['source_sha256'] != row['sha256']:
            raise ValueError(f'{cp}: production and accepted source bindings differ')
        name = f'U{int(cp[2:], 16):X}.png'
        dest = output / name
        key = canonical_sha({'codepoint': cp,
            'geometry_sha256': glyph['geometry_sha256'],
            'normalization': row['normalization'], 'render': settings})
        previous = prior.get(cp)
        if (previous and previous.get('input_sha256') == key
                and previous.get('file') == name and dest.is_file()
                and sha(dest) == previous.get('sha256')):
            entry = dict(previous)
            reused += 1
        else:
            if font is None:
                font = ImageFont.truetype(str(font_path), PIXELS * SUPERSAMPLE,
                    layout_engine=ImageFont.Layout.BASIC)
            im = Image.new('RGBA', (PIXELS * SUPERSAMPLE,) * 2, (0, 0, 0, 0))
            baseline = EXPECTED_METRICS['baseline'] / 1024 * PIXELS * SUPERSAMPLE
            ImageDraw.Draw(im).text((0, baseline), chr(int(cp[2:], 16)),
                font=font, fill=(0, 0, 0, 255), anchor='ls')
            im = im.resize((PIXELS, PIXELS), Image.Resampling.LANCZOS)
            bbox = im.getchannel('A').getbbox()
            if bbox is None:
                raise ValueError(f'{cp}: empty raster')
            temp = dest.with_suffix('.png.tmp')
            im.save(temp, format='PNG', optimize=True)
            os.replace(temp, dest)
            entry = {'codepoint': cp, 'file': name, 'input_sha256': key,
                'sha256': sha(dest), 'image_pixels': [PIXELS, PIXELS],
                'mode': 'RGBA', 'alpha_bbox': list(bbox),
                'font_sha256_when_rendered': font_sha}
            rendered += 1
        # Source metadata may change without changing the proven glyph geometry.
        entry['source_sha256'] = row['sha256']
        entry['geometry_sha256'] = glyph['geometry_sha256']
        rows.append(entry)
    for cp, previous in prior.items():
        if cp not in accepted:
            name = f'U{int(cp[2:], 16):X}.png'
            if previous.get('file') == name:
                (output / name).unlink(missing_ok=True)
                removed += 1
    manifest = {'schema_version': 1, 'unicode_version': '18.0',
        'block': 'Small Seal', 'first': f'U+{FIRST:X}', 'last': f'U+{LAST:X}',
        'repertoire_count': LAST - FIRST + 1, 'rendered_glyphs': len(rows),
        'pending_glyphs': LAST - FIRST + 1 - len(rows),
        'pending_individual_files_emitted': False,
        'style': 'Regular400; individual transparent16x16 glyphs from accepted production outlines',
        'render_settings': settings, 'registry_sha256': source['registry_sha256'],
        'font_sha256': font_sha, 'source_manifest_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'accepted_geometry_manifest_sha256': hashlib.sha256(geometry_bytes).hexdigest(), 'glyphs': rows}
    write_json(index, manifest)
    readme = (f'# Individual 16×16 PNGs\n\n{len(rows):,} accepted Small Seal glyphs, each a '
        'transparent 16×16-pixel RGBA PNG rendered from the production Regular400 font. '
        f'{manifest["pending_glyphs"]:,} pending glyphs have no individual file. '
        'The separate 45 PNG grids continue to show every block position.\n\n'
        'Files are named `U3D000.png` and so on. `manifest.json` binds each bitmap to its '
        'accepted geometry, source, render settings and PNG fingerprint. '
        'Unchanged glyph bitmaps are reused across checkpoints.\n')
    readme_path = output / 'README.md'
    if not readme_path.exists() or readme_path.read_text() != readme:
        readme_path.write_text(readme)
    result = {'accepted_glyphs': len(rows), 'rendered': rendered,
        'reused': reused, 'removed': removed,
        'pending': manifest['pending_glyphs'], 'image_pixels': [PIXELS, PIXELS],
        'font_rebuild': False}
    print(json.dumps(result), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True,
        help='Same accepted production manifest used by export_png_grids.py')
    parser.add_argument('--geometry-manifest', type=Path, required=True,
        help='Accepted svg/manifest.json, for stable per-glyph geometry cache identities')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-font-sha256')
    args = parser.parse_args()
    export(args.font, args.manifest, args.geometry_manifest, args.output,
        args.expected_font_sha256)


if __name__ == '__main__':
    main()
