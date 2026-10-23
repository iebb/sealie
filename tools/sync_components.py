#!/usr/bin/env python3
"""Synchronize exact shared radical paths into the editable glyph SVGs.

The component manifest is ``components/manifest.json``::

    {"schema_version": 1, "components": [
      {"id": "water-left", "family": "410.3EF5E", "position": "left",
       "file": "water-left.svg", "instances": [
         {"codepoint": "U+3EF60", "path_indices_zero_based": [2, 3, 4, 5, 6]}
       ]}
    ]}

Templates have the same 1024-unit, pen-30 SVG wrapper as glyph sources. Their
``data-codepoint`` identifies the canonical drawing; filenames may use the
component ID. Path order in each template corresponds to the instance's index
list. Path IDs in the destination are retained. Only absolute M/L/Z paths are
accepted. No drawing, tracing, font compilation, or model service is involved.

The default --check verifies assigned geometry and current source hashes.
--apply validates every input before writing, copies template d attributes,
and refreshes changed svg_sha256 fields in the glyph manifest. Historical
authoring/geometry hashes and all unassigned paths remain unchanged. An optional
component svg_sha256 field is checked and refreshed on apply. Each file is
replaced atomically; the glyph manifest is written after the glyph SVGs.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import xml.etree.ElementTree as ET


URI = 'http://www.w3.org/2000/svg'
NS = '{' + URI + '}'
ET.register_namespace('', URI)
FIRST, LAST = 0x3D000, 0x3FC3F
TOKEN = re.compile(r'[MLZ]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z')
GROUP = {
    'transform': 'matrix(1 0 0 -1 0 832)', 'fill': 'none', 'stroke': '#000',
    'stroke-width': '30', 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
}
ROOT_ATTRIBUTES = {'viewBox', 'data-codepoint', 'data-advance', 'data-schema'}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def codepoint(value):
    if not isinstance(value, str) or not re.fullmatch(r'U\+?[0-9A-Fa-f]{5}', value):
        raise ValueError(f'Invalid Small Seal codepoint: {value!r}')
    number = int(value.removeprefix('U').removeprefix('+'), 16)
    if not FIRST <= number <= LAST:
        raise ValueError(f'Codepoint outside Small Seal repertoire: {value}')
    return number


def parse_path(text):
    if not isinstance(text, str):
        raise ValueError('Missing SVG path data')
    tokens = TOKEN.findall(text)
    if TOKEN.sub('', text).strip(' ,\t\n\r'):
        raise ValueError('Only absolute M/L/Z path commands are supported')
    if not tokens or tokens[0] != 'M':
        raise ValueError('Each stroke must begin with M')
    points, closed, index = [], False, 0
    while index < len(tokens):
        command = tokens[index]
        index += 1
        if command == 'Z':
            if not points or index != len(tokens):
                raise ValueError('Z must end one nonempty stroke')
            closed = True
            break
        if command not in ('M', 'L') or (command == 'M' and points):
            raise ValueError('Each stroke must contain one M and one subpath')
        if index + 1 >= len(tokens):
            raise ValueError('Incomplete SVG coordinate pair')
        try:
            x, y = float(tokens[index]), float(tokens[index + 1])
        except ValueError as error:
            raise ValueError('Invalid SVG coordinate pair') from error
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError('Nonfinite SVG coordinate')
        points.append((x, y))
        index += 2
    if not points:
        raise ValueError('Empty SVG stroke')
    return tuple(points), closed


@dataclass
class Drawing:
    path: Path
    raw: bytes
    root: ET.Element
    group: ET.Element
    nodes: list
    strokes: list
    codepoint: int


def read_drawing(path, expected_codepoint=None):
    path = Path(path)
    raw = path.read_bytes()
    if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
        raise ValueError(f'{path}: SVG declarations/entities are unsupported')
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as error:
        raise ValueError(f'{path}: invalid SVG XML') from error
    if root.tag != NS + 'svg' or root.get('viewBox') != '0 0 1024 1024':
        raise ValueError(f'{path}: expected a 1024-unit SVG')
    if set(root.attrib) != ROOT_ATTRIBUTES:
        raise ValueError(f'{path}: unsupported or missing root attributes')
    cp = codepoint(root.get('data-codepoint'))
    if expected_codepoint is not None and cp != expected_codepoint:
        raise ValueError(f'{path}: SVG/codepoint mismatch')
    if root.get('data-advance') != '1024' or root.get('data-schema') != 'seal-centerline-1':
        raise ValueError(f'{path}: unsupported SVG schema or advance')
    children = list(root)
    if len(children) != 1 or children[0].tag != NS + 'g' or children[0].attrib != GROUP:
        raise ValueError(f'{path}: expected the unchanged round-stroke group')
    group = children[0]
    nodes, strokes, identifiers = [], [], set()
    for node in group:
        if node.tag != NS + 'path' or set(node.attrib) - {'id', 'd'} or len(node):
            raise ValueError(f'{path}: only untransformed path nodes are supported')
        if node.text and node.text.strip():
            raise ValueError(f'{path}: unexpected text inside path')
        identifier = node.get('id')
        if identifier is not None:
            if identifier in identifiers:
                raise ValueError(f'{path}: duplicate SVG path ID {identifier!r}')
            identifiers.add(identifier)
        nodes.append(node)
        strokes.append(parse_path(node.get('d')))
    if not nodes:
        raise ValueError(f'{path}: no stroke paths')
    if (root.text and root.text.strip()) or (group.text and group.text.strip()):
        raise ValueError(f'{path}: unexpected SVG text')
    return Drawing(path, raw, root, group, nodes, strokes, cp)


def safe_component_path(directory, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('Component file must be a relative SVG path')
    relative = Path(name)
    if '..' in relative.parts or relative.suffix != '.svg':
        raise ValueError('Component file must stay inside the components directory')
    target = (directory / relative).resolve()
    if not target.is_relative_to(directory.resolve()):
        raise ValueError('Component file resolves outside the components directory')
    return target


def atomic(path, data):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.' + path.name + '.', suffix='.tmp',
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        temporary.chmod(path.stat().st_mode & 0o777 if path.exists() else 0o644)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def json_bytes(data):
    return (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode()


def sync(svg_dir, components_dir, apply=False):
    """Validate the atlas, then check or apply exact component assignments."""
    svg_dir, components_dir = Path(svg_dir), Path(components_dir)
    glyph_manifest_path = svg_dir / 'manifest.json'
    component_manifest_path = components_dir / 'manifest.json'
    glyph_manifest_raw = glyph_manifest_path.read_bytes()
    component_manifest_raw = component_manifest_path.read_bytes()
    glyph_manifest = json.loads(glyph_manifest_raw)
    component_manifest = json.loads(component_manifest_raw)
    rows = glyph_manifest.get('glyphs')
    components = component_manifest.get('components')
    if not isinstance(rows, list) or not rows:
        raise ValueError('Glyph manifest must contain a nonempty glyphs array')
    if component_manifest.get('schema_version') != 1 or not isinstance(components, list):
        raise ValueError('Component manifest must use schema_version1 and a components array')
    glyph_rows = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid glyph manifest row')
        cp = codepoint(row.get('codepoint'))
        if cp in glyph_rows:
            raise ValueError(f'Duplicate glyph manifest codepoint U+{cp:05X}')
        if not isinstance(row.get('svg_sha256'), str):
            raise ValueError(f'Missing glyph SVG hash for U+{cp:05X}')
        glyph_rows[cp] = row

    identifiers, assigned, drawings, changes, templates = set(), {}, {}, {}, {}
    mismatches, template_updates, instance_count = [], [], 0
    for component in components:
        if not isinstance(component, dict):
            raise ValueError('Invalid component manifest entry')
        identifier = component.get('id')
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
            raise ValueError(f'Invalid component ID {identifier!r}')
        if identifier in identifiers:
            raise ValueError(f'Duplicate component ID {identifier!r}')
        identifiers.add(identifier)
        if not isinstance(component.get('family'), str) or not component['family']:
            raise ValueError(f'{identifier}: missing radical family')
        if component.get('position') not in {'left', 'right', 'top', 'bottom', 'enclosure', 'center'}:
            raise ValueError(f'{identifier}: unsupported component position')
        instances = component.get('instances')
        if not isinstance(instances, list) or not instances:
            raise ValueError(f'{identifier}: expected a nonempty instances array')
        template = read_drawing(safe_component_path(components_dir, component.get('file')))
        templates[template.path] = template.raw
        template_hash = sha256(template.raw)
        if 'svg_sha256' in component and component['svg_sha256'] != template_hash:
            if not apply:
                raise ValueError(f'{identifier}: stale template SVG hash; use --apply after an intentional edit')
            template_updates.append((component, template_hash))
        for instance in instances:
            if not isinstance(instance, dict):
                raise ValueError(f'{identifier}: invalid component instance')
            cp = codepoint(instance.get('codepoint'))
            if cp not in glyph_rows:
                raise ValueError(f'{identifier}: U+{cp:05X} is outside the glyph manifest')
            indices = instance.get('path_indices_zero_based')
            if (not isinstance(indices, list) or not indices
                    or any(type(index) is not int or index < 0 for index in indices)
                    or len(set(indices)) != len(indices)):
                raise ValueError(f'{identifier}: invalid or duplicate path indices for U+{cp:05X}')
            if len(indices) != len(template.nodes):
                raise ValueError(f'{identifier}: template/instance path count differs for U+{cp:05X}')
            if cp not in drawings:
                drawing = read_drawing(svg_dir / f'U{cp:05X}.svg', cp)
                if sha256(drawing.raw) != glyph_rows[cp]['svg_sha256']:
                    raise ValueError(f'U+{cp:05X}: stale glyph SVG hash; refresh the glyph manifest after an intentional source edit')
                drawings[cp] = drawing
            drawing = drawings[cp]
            if max(indices) >= len(drawing.nodes):
                raise ValueError(f'{identifier}: path index outside U+{cp:05X}')
            for index, template_node, stroke in zip(indices, template.nodes, template.strokes):
                key = cp, index
                if key in assigned:
                    raise ValueError(f'U+{cp:05X} path{index}: overlapping assignments from {assigned[key]} and {identifier}')
                assigned[key] = identifier
                if drawing.strokes[index][1] != stroke[1]:
                    raise ValueError(f'{identifier}: template changes path closure in U+{cp:05X} path{index}')
                if drawing.strokes[index] != stroke:
                    mismatches.append((identifier, cp, index))
                    changes.setdefault(cp, {})[index] = template_node.get('d')
            instance_count += 1

    if mismatches and not apply:
        first = mismatches[0]
        raise ValueError(f'{len(mismatches)} component path mismatches; first: {first[0]} in U+{first[1]:05X} path{first[2]}; use --apply to synchronize')

    replacements = {}
    for cp, paths in changes.items():
        drawing = drawings[cp]
        root = deepcopy(drawing.root)
        nodes = list(root[0])
        for index, text in paths.items():
            nodes[index].set('d', text)
        for index, node in enumerate(nodes):
            if index not in paths and node.attrib != drawing.nodes[index].attrib:
                raise ValueError('Internal error: an unassigned path changed')
        if len(nodes) != len(drawing.nodes):
            raise ValueError('Internal error: glyph path count changed')
        raw = ET.tostring(root, encoding='utf-8', short_empty_elements=True)
        if not raw.endswith(b'\n'):
            raw += b'\n'
        replacements[cp] = raw

    if apply:
        if glyph_manifest_path.read_bytes() != glyph_manifest_raw or component_manifest_path.read_bytes() != component_manifest_raw:
            raise ValueError('A source manifest changed concurrently; retry after the other edit finishes')
        for drawing in drawings.values():
            if drawing.path.read_bytes() != drawing.raw:
                raise ValueError(f'{drawing.path}: source changed concurrently')
        for path, raw in templates.items():
            if path.read_bytes() != raw:
                raise ValueError(f'{path}: component template changed concurrently')
        for cp, raw in replacements.items():
            atomic(drawings[cp].path, raw)
            glyph_rows[cp]['svg_sha256'] = sha256(raw)
        for component, template_hash in template_updates:
            component['svg_sha256'] = template_hash
        if template_updates:
            atomic(component_manifest_path, json_bytes(component_manifest))
        if replacements:
            atomic(glyph_manifest_path, json_bytes(glyph_manifest))

    return {
        'status': 'applied' if apply else 'in_sync',
        'components': len(components), 'instances': instance_count,
        'glyphs_checked': len(drawings), 'assigned_paths': len(assigned),
        'changed_glyphs': len(replacements), 'changed_paths': len(mismatches),
        'refreshed_template_hashes': len(template_updates),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--svg-dir', type=Path, default=Path('svg'))
    parser.add_argument('--components-dir', type=Path, default=Path('components'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='Check exact sharing and current hashes (default)')
    mode.add_argument('--apply', action='store_true', help='Copy shared paths into glyph SVGs and refresh their hashes')
    args = parser.parse_args(argv)
    try:
        result = sync(args.svg_dir, args.components_dir, apply=args.apply)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f'error: {error}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
