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

SITE_ASSETS = ('index.html', 'site/styles.css', 'site/showcase.js', 'site/character-map.json')
LICENSES = ('LICENSE-OFL.txt', 'OFL-1.1.txt')
CSS_URL = re.compile(r'url\(\s*[\"\']?([^\s)\"\']+)[\"\']?\s*\)')
VERSION_LENGTH = 16


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


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
    versions['site/styles.css'] = fingerprint(output / 'site/styles.css')
    versions['site/character-map.json'] = fingerprint(output / 'site/character-map.json')
    script_path = output / 'site/showcase.js'
    script = script_path.read_text(encoding='utf-8')
    map_reference = '"character-map.json"'
    if script.count(map_reference) != 1:
        raise ValueError('Expected one relative character-map reference in site/showcase.js')
    versioned_map = f'"character-map.json?v={versions["site/character-map.json"][:VERSION_LENGTH]}"'
    script_path.write_text(script.replace(map_reference, versioned_map, 1), encoding='utf-8')
    versions['site/showcase.js'] = fingerprint(script_path)
    index_path = output / 'index.html'
    index = index_path.read_text(encoding='utf-8')
    for reference in ('fonts/variable.css', 'site/styles.css', 'site/showcase.js'):
        original = f'"{reference}"'
        if index.count(original) != 1:
            raise ValueError(f'Expected one simple relative index asset reference: {reference}')
        versioned = f'"{reference}?v={versions[reference][:VERSION_LENGTH]}"'
        index = index.replace(original, versioned, 1)
    index_path.write_text(index, encoding='utf-8')
    versions['index.html'] = fingerprint(index_path)
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
    inventory = [{'file': name, 'bytes': (output / name).stat().st_size}
                 for name, _source in inputs]
    report = {'schema_version': 1, 'site': 'Sealie variable font specimen',
              'variable_woff_subsets': len(fonts), 'copied_files': len(inputs),
              'copied_bytes': sum(row['bytes'] for row in inventory),
              'source_font_css_sha256': fingerprint(css_path),
              'font_css_sha256': versions['fonts/variable.css'],
              'character_map_sha256': versions['site/character-map.json'],
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
