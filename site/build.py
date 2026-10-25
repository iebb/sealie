#!/usr/bin/env python3
"""Build a small, dependency-free GitHub Pages specimen artifact.

Only explicitly named web assets, the variable font CSS and its WOFF subsets,
and font licenses are copied. No SVG sources, reports, ZIPs, TTFs, or build tools
are included. Font compilation is deliberately outside this deployment.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys

SITE_ASSETS = ('index.html', 'characters.html', 'site/styles.css', 'site/showcase.js',
               'site/characters.js', 'site/character-map.json', 'site/coverage.json')
LICENSES = ('LICENSE-OFL.txt', 'OFL-1.1.txt')
CSS_URL = re.compile(r'url\(\s*[\"\']?([^\s)\"\']+)[\"\']?\s*\)')
VERSION_LENGTH = 16


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def validate_coverage(coverage: dict, webfonts: dict, manifest_hash: str,
                      font_hashes: dict[str, str] | None = None) -> None:
    """Bind the measured cmap inventory to the exact fonts being deployed."""
    first, last = 0x3D000, 0x3FC3F
    if (coverage.get('first'), coverage.get('last')) != (first, last):
        raise ValueError('Coverage must describe the Unicode 18 Small Seal repertoire')
    if (coverage.get('source_webfont_manifest_sha256') != manifest_hash or
            coverage.get('source_svg_manifest_sha256') != webfonts['source_svg_manifest_sha256'] or
            coverage.get('family') != webfonts['family'] or
            coverage.get('version') != webfonts['version']):
        raise ValueError('Coverage inventory does not match the current webfont manifest')
    supported: set[int] = set()
    previous = first - 1
    for interval in coverage['supported_ranges']:
        if (not isinstance(interval, list) or len(interval) != 2 or
                any(type(cp) is not int for cp in interval)):
            raise ValueError('Invalid supported codepoint interval')
        start, stop = interval
        if not first <= start <= stop <= last or start <= previous:
            raise ValueError('Coverage intervals must be ordered, disjoint and within the repertoire')
        supported.update(range(start, stop + 1))
        previous = stop
    if (coverage.get('repertoire_count') != last - first + 1 or
            coverage.get('glyph_count') != len(supported) or
            coverage.get('missing_count') != last - first + 1 - len(supported) or
            len(supported) != webfonts['glyph_count']):
        raise ValueError('Coverage totals disagree with supported codepoints')
    rows = coverage['chunks']
    if len(rows) != len(webfonts['chunks']):
        raise ValueError('Coverage subset count differs from the deployed fonts')
    previous = first - 1
    for row, expected in zip(rows, webfonts['chunks']):
        start, stop = int(expected['first'][2:], 16), int(expected['last'][2:], 16)
        if (row['first'] != start or row['last'] != stop or start != previous + 1 or
                row['file'] != expected['file'] or row['sha256'] != expected['sha256'] or
                row['count'] != expected['glyph_count'] or
                row['count'] != sum(cp in supported for cp in range(start, stop + 1))):
            raise ValueError(f'Invalid coverage subset: {expected["file"]}')
        if font_hashes is not None:
            path = 'fonts/variable/' + row['file']
            if font_hashes.get(path) != row['sha256']:
                raise ValueError(f'Coverage was measured from different font bytes: {row["file"]}')
        previous = stop
    if previous != last:
        raise ValueError('Coverage subset intervals do not span the complete repertoire')


def version_assets(output: Path, source_css: str, references: list[str]) -> dict[str, str]:
    """Version the copied bytes; source URLs and font CSS remain unchanged.

    A WOFF change versions its URL, which changes the generated font stylesheet,
    which versions the index stylesheet link. Map changes likewise version the
    generated JS URL. All URLs remain relative to the Pages project directory.
    """
    versions = {f'fonts/{reference}': fingerprint(output / 'fonts' / reference)
                for reference in references}

    def version_font(match: re.Match[str]) -> str:
        reference = match.group(1)
        version = versions[f'fonts/{reference}'][:VERSION_LENGTH]
        return match.group(0).replace(reference, f'{reference}?v={version}', 1)

    generated_css = CSS_URL.sub(version_font, source_css)
    font_css = output / 'fonts/variable.css'
    font_css.write_text(generated_css, encoding='utf-8')
    versions['fonts/variable.css'] = fingerprint(font_css)
    for reference in ('site/styles.css', 'site/character-map.json', 'site/coverage.json'):
        versions[reference] = fingerprint(output / reference)
    for filename, data_files in [('showcase.js', ('character-map.json',)),
                                  ('characters.js', ('character-map.json', 'coverage.json'))]:
        script_path = output / 'site' / filename
        script = script_path.read_text(encoding='utf-8')
        for data_file in data_files:
            original = f'"{data_file}"'
            if script.count(original) != 1:
                raise ValueError(f'Expected one relative {data_file} reference in site/{filename}')
            versioned = f'"{data_file}?v={versions["site/" + data_file][:VERSION_LENGTH]}"'
            script = script.replace(original, versioned, 1)
        script_path.write_text(script, encoding='utf-8')
        versions['site/' + filename] = fingerprint(script_path)
    for page, script in [('index.html', 'site/showcase.js'), ('characters.html', 'site/characters.js')]:
        page_path = output / page
        html = page_path.read_text(encoding='utf-8')
        for reference in ('fonts/variable.css', 'site/styles.css', script):
            original = f'"{reference}"'
            if html.count(original) != 1:
                raise ValueError(f'Expected one simple relative asset reference in {page}: {reference}')
            versioned = f'"{reference}?v={versions[reference][:VERSION_LENGTH]}"'
            html = html.replace(original, versioned, 1)
        page_path.write_text(html, encoding='utf-8')
        versions[page] = fingerprint(page_path)
    return versions


def build(repo_root: Path, site_root: Path, output: Path) -> dict:
    repo_root, site_root, output = repo_root.resolve(), site_root.resolve(), output.resolve()
    # Never delete or write over the repository or the source assets.
    if output == repo_root or output in repo_root.parents:
        raise ValueError('Output cannot replace the repository or one of its parent directories')
    for protected in (site_root / 'site', repo_root / 'fonts', repo_root / 'svg', repo_root / 'components', repo_root / '.git'):
        protected = protected.resolve()
        if output == protected or protected in output.parents:
            raise ValueError('Output must be separate from maintained source and font directories')
    if output.exists() and any(output.iterdir()):
        raise ValueError('Output must be empty; choose a fresh build directory')
    css_path = repo_root / 'fonts/variable.css'
    css = css_path.read_text(encoding='utf-8')
    references = CSS_URL.findall(css)
    if len(references) != 177 or len(set(references)) != 177:
        raise ValueError('Expected exactly 177 distinct variable WOFF subsets in fonts/variable.css')
    webfont_manifest = repo_root / 'fonts/variable/manifest.json'
    webfonts = json.loads(webfont_manifest.read_text(encoding='utf-8'))
    coverage = json.loads((site_root / 'site/coverage.json').read_text(encoding='utf-8'))
    manifest_hash = fingerprint(webfont_manifest)
    validate_coverage(coverage, webfonts, manifest_hash)
    fonts = []
    for reference in references:
        relative = PurePosixPath(reference)
        if relative.is_absolute() or '..' in relative.parts or len(relative.parts) != 2 or relative.parts[0] != 'variable' or relative.suffix != '.woff':
            raise ValueError(f'Unexpected font CSS asset path: {reference}')
        path = repo_root / 'fonts' / reference
        if not path.is_file():
            raise FileNotFoundError(f'Missing variable font subset: {reference}')
        with path.open('rb') as stream:
            if stream.read(4) != b'wOFF':
                raise ValueError(f'Expected WOFF data: {reference}')
        fonts.append(('fonts/' + reference, path))
    inputs = [(name, site_root / name) for name in SITE_ASSETS]
    inputs += [('fonts/variable.css', css_path), *fonts]
    inputs += [(name, repo_root / name) for name in LICENSES]
    for name, source in inputs:
        if not source.is_file():
            raise FileNotFoundError(f'Missing Pages input: {name}')
    # Check every input before making a partial output artifact.
    output.mkdir(parents=True, exist_ok=True)
    for name, source in inputs:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    versions = version_assets(output, css, references)
    validate_coverage(coverage, webfonts, manifest_hash, versions)
    inventory = [{'file': name, 'bytes': (output / name).stat().st_size}
                 for name, _source in inputs]
    report = {'schema_version': 1, 'site': 'Sealie variable font specimen',
              'variable_woff_subsets': len(fonts), 'copied_files': len(inputs),
              'copied_bytes': sum(row['bytes'] for row in inventory),
              'source_font_css_sha256': fingerprint(css_path),
              'font_css_sha256': versions['fonts/variable.css'],
              'character_map_sha256': versions['site/character-map.json'],
              'coverage_sha256': versions['site/coverage.json'],
              'covered_glyphs': coverage['glyph_count'],
              'repertoire_count': coverage['repertoire_count'],
              'missing_glyphs': coverage['missing_count'],
              'cache_busting': {'query_key': 'v', 'sha256_prefix_length': VERSION_LENGTH,
                               'woff_files_fingerprinted': len(fonts),
                               'basis': 'Actual copied WOFF bytes; generated stylesheet and index references'},
              'asset_versions': versions,
              'files': inventory}
    (output / 'site-manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--site-root', type=Path, help='Optional separate website source tree; defaults to repo-root')
    parser.add_argument('--output', type=Path, default=Path('_site'))
    args = parser.parse_args()
    try:
        report = build(args.repo_root, args.site_root or args.repo_root, args.output)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Pages build failed: {error}\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'asset_versions')}, indent=2))


if __name__ == '__main__':
    main()
