#!/usr/bin/env python3
"""Refresh measured webfont coverage after replacing the variable font subsets.

Run ``python site/update_coverage.py`` from a checkout with the font build
requirements installed. FontTools is used only by this local generator; the
normal Pages build uses the resulting JSON and Python's standard library.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont

FIRST, LAST = 0x3D000, 0x3FC3F


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(repo: Path, output: Path) -> dict:
    manifest_path = repo / 'fonts/variable/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    supported: set[int] = set()
    chunks = []
    previous = FIRST - 1
    for row in manifest['chunks']:
        filename = row['file']
        require(Path(filename).name == filename and filename.endswith('.woff'), 'Invalid subset filename')
        path = manifest_path.parent / filename
        require(fingerprint(path) == row['sha256'] and path.stat().st_size == row['bytes'],
                f'Stale font manifest: {filename}')
        first, last = int(row['first'][2:], 16), int(row['last'][2:], 16)
        require(first == previous + 1 and FIRST <= first <= last <= LAST, 'Invalid subset interval')
        with TTFont(path, lazy=True) as font:
            codepoints = set(font.getBestCmap() or {})
            require(font['name'].getDebugName(1) == manifest['family'], f'Wrong font family: {filename}')
            axes = [(axis.axisTag, axis.minValue, axis.defaultValue, axis.maxValue) for axis in font['fvar'].axes]
            require(axes == [('wght', 300, 400, 700)], f'Unexpected weight axis: {filename}')
        require(len(codepoints) == row['glyph_count'] and codepoints <= set(range(first, last + 1)),
                f'Font cmap differs from subset metadata: {filename}')
        require(not codepoints & supported, f'Duplicate encoded characters: {filename}')
        supported.update(codepoints)
        chunks.append({'first': first, 'last': last, 'count': len(codepoints),
                       'file': filename, 'sha256': row['sha256']})
        previous = last
    require(previous == LAST and len(supported) == manifest['glyph_count'], 'Incomplete subset inventory')
    ranges: list[list[int]] = []
    for codepoint in sorted(supported):
        if ranges and codepoint == ranges[-1][1] + 1:
            ranges[-1][1] = codepoint
        else:
            ranges.append([codepoint, codepoint])
    result = {'schema_version': 1, 'family': manifest['family'], 'version': manifest['version'],
              'unicode_version': '18.0.0', 'first': FIRST, 'last': LAST,
              'repertoire_count': LAST - FIRST + 1, 'glyph_count': len(supported),
              'missing_count': LAST - FIRST + 1 - len(supported), 'supported_ranges': ranges,
              'chunks': chunks, 'source_svg_manifest_sha256': manifest['source_svg_manifest_sha256'],
              'source_webfont_manifest_sha256': fingerprint(manifest_path),
              'measurement': 'Unicode cmap entries read from every shipped variable WOFF subset; each file SHA-256 verified against the webfont manifest. Character mappings are independent of font coverage.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, separators=(',', ':')) + '\n', encoding='utf-8')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, help='Defaults to site/coverage.json in the checkout')
    args = parser.parse_args()
    try:
        result = generate(args.repo_root, args.output or args.repo_root / 'site/coverage.json')
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'Coverage generation failed: {error}\n')
    print(json.dumps({key: result[key] for key in ('glyph_count', 'repertoire_count', 'missing_count')}))


if __name__ == '__main__':
    main()
