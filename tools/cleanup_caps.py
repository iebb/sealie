#!/usr/bin/env python3
"""Remove only subpixel terminal micro-knots from round-stroke SVG sources.

Default --check is read-only and exits 1 when cleanup is available. --apply
validates current glyph and component hashes before replacing files atomically.
Shared templates are cleaned once and propagated to all bound copies; unassigned
paths are cleaned independently. Stroke IDs, count, order, pen width and historical
authoring hashes are retained. No interior simplification or stroke deletion occurs.

The endpoint disk radius defaults to 0.25 font units (1/120 of the Regular pen).
Near-exact full-loop closure is a separate, explicit --close-exact-loops option.
"""
from __future__ import annotations

import math
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import sync_components as shared

DEFAULT_EPSILON = .25
EXACT_LOOP_EPSILON = 1e-6


def path_length(points):
    return sum(math.dist(p, q) for p, q in zip(points, points[1:]))


def bounds(points):
    return (min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points))


def signed_area(points):
    # Translate before summing to avoid cancellation in tiny loops at large x/y.
    origin = points[0]
    pairs = list(zip(points, points[1:] + points[:1]))
    return sum((p[0] - origin[0]) * (q[1] - origin[1])
               - (p[1] - origin[1]) * (q[0] - origin[0])
               for p, q in pairs) / 2


def exact_full_loop(points):
    if len(points) < 5:
        return False
    if math.dist(points[0], points[-1]) > EXACT_LOOP_EPSILON:
        return False
    box = bounds(points)
    return (path_length(points) > 60
            and min(box[2] - box[0], box[3] - box[1]) >= 15
            and abs(signed_area(points)) >= 225)


def cleanup_stroke(points, closed, epsilon=DEFAULT_EPSILON, close_exact_loops=False):
    """Return ``(new_points, closed, evidence)`` without changing the input.

    The 0.25-unit default is 1/120 of the Regular pen diameter. Only endpoint
    micro-knots are candidates, not all short segments in the drawing.
    """
    if not math.isfinite(epsilon) or not 0 <= epsilon <= .5:
        raise ValueError('Endpoint epsilon must be between 0 and 0.5 font units')
    original = [tuple(map(float, point)) for point in points]
    if not original or any(len(p) != 2 or not all(math.isfinite(v) for v in p) for p in original):
        raise ValueError('Expected a nonempty finite polyline')
    result = original[:]
    evidence = {'changed': False, 'before_points': len(original),
                'removed_start_vertices': [], 'removed_end_vertices': [],
                'closed_exact_full_loop': False,
                'centerline_hausdorff_bound_font_units': 0.0}
    if closed or len(result) < 3:
        evidence['after_points'] = len(result)
        return result, bool(closed), evidence

    # Keep each endpoint fixed. Remove only a consecutive terminal cluster,
    # never a vertex reached after a meaningful excursion outside that disk.
    start = result[0]
    end = result[-1]
    original_indices = list(range(len(result)))
    while len(result) > 2 and math.dist(result[1], start) <= epsilon + 1e-12:
        evidence['removed_start_vertices'].append(original_indices.pop(1))
        result.pop(1)
    while len(result) > 2 and math.dist(result[-2], end) <= epsilon + 1e-12:
        evidence['removed_end_vertices'].append(original_indices.pop(-2))
        result.pop(-2)

    output_closed = bool(closed)
    if close_exact_loops and exact_full_loop(result):
        evidence['closed_exact_full_loop'] = True
        evidence['original_seam_distance'] = math.dist(result[0], result[-1])
        # Z supplies the final segment. Removing the near-identical explicit
        # endpoint avoids creating a second zero-length seam segment.
        result.pop()
        output_closed = True
    removed = len(evidence['removed_start_vertices']) + len(evidence['removed_end_vertices'])
    evidence['changed'] = removed > 0 or output_closed != bool(closed)
    evidence['after_points'] = len(result)
    if removed:
        evidence['centerline_hausdorff_bound_font_units'] = epsilon
    if evidence['closed_exact_full_loop']:
        evidence['centerline_hausdorff_bound_font_units'] = max(
            evidence['centerline_hausdorff_bound_font_units'], EXACT_LOOP_EPSILON)
    if not output_closed:
        assert result[0] == original[0] and result[-1] == original[-1]
    return result, output_closed, evidence


def cleanup_strokes(strokes, epsilon=DEFAULT_EPSILON, close_exact_loops=False):
    result, records = [], []
    for index, (points, closed) in enumerate(strokes):
        output, new_closed, evidence = cleanup_stroke(points, closed, epsilon, close_exact_loops)
        result.append((output, new_closed))
        if evidence['changed']:
            records.append({'path_index_zero_based': index, **evidence})
    assert len(result) == len(strokes)
    return result, records


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _path_data(points, closed):
    data = ' '.join(('M' if index == 0 else 'L') + ' ' + repr(float(x)) + ' ' + repr(float(y))
                    for index, (x, y) in enumerate(points))
    return data + (' Z' if closed else '')


def _drawing_bytes(drawing, replacements):
    root = deepcopy(drawing.root)
    nodes = list(root[0])
    for index, (points, closed) in replacements.items():
        nodes[index].set('d', _path_data(points, closed))
    assert len(nodes) == len(drawing.nodes)
    for index, node in enumerate(nodes):
        assert node.get('id') == drawing.nodes[index].get('id')
        if index not in replacements:
            assert node.attrib == drawing.nodes[index].attrib
    raw = ET.tostring(root, encoding='utf-8', short_empty_elements=True)
    return raw if raw.endswith(b'\n') else raw + b'\n'


def _template_bounds(strokes):
    points = [point for points, closed in strokes for point in points]
    return list(bounds(points))


def clean_sources(svg_dir, components_dir, apply=False, epsilon=DEFAULT_EPSILON,
                  close_exact_loops=False, detail_limit=100):
    """Plan/check or apply a hash-bound cap cleanup without a font rebuild.

    Applying intentional closure migrations uses the same strict shared-source
    parser and validates with sync_components before and after propagation.
    The normal synchronizer's closure-change guard remains unchanged.
    """
    if type(detail_limit) is not int or not 0 <= detail_limit <= 10000:
        raise ValueError('Detail limit must be an integer between 0 and 10000')
    svg_dir, components_dir = Path(svg_dir), Path(components_dir)
    source_manifest_path, atlas_path = svg_dir / 'manifest.json', components_dir / 'manifest.json'
    source_manifest_raw, atlas_raw = source_manifest_path.read_bytes(), atlas_path.read_bytes()
    manifest, atlas = json.loads(source_manifest_raw), json.loads(atlas_raw)
    # This verifies all assignment indices, component geometry, closures and
    # currently assigned hashes before the migration is planned.
    sync_before = shared.sync(svg_dir, components_dir, apply=False)
    template_drawings, template_outputs, template_changes = {}, {}, {}
    assignments = {}
    counts = {'glyphs_checked': 0, 'paths_checked': 0, 'changed_glyphs': 0,
              'changed_paths': 0, 'changed_templates': 0,
              'terminal_micro_knot_paths': 0, 'removed_terminal_vertices': 0,
              'exact_full_loops_closed': 0, 'shared_component_paths_changed': 0,
              'unassigned_paths_changed': 0}
    details = []
    changed_files = {}
    old_file_hashes = {}
    original_lineage = {}

    for component in atlas['components']:
        drawing = shared.read_drawing(shared.safe_component_path(components_dir, component['file']))
        template_drawings[component['id']] = drawing
        if 'svg_sha256' in component and component['svg_sha256'] != _digest(drawing.raw):
            raise ValueError(f'{component["id"]}: stale component SVG hash')
        output, evidence = cleanup_strokes(drawing.strokes, epsilon, close_exact_loops)
        template_outputs[component['id']] = output
        replacement = {record['path_index_zero_based']: output[record['path_index_zero_based']]
                       for record in evidence}
        if replacement:
            raw = _drawing_bytes(drawing, replacement)
            template_changes[component['id']] = raw
            changed_files[drawing.path] = raw
            old_file_hashes[drawing.path] = _digest(drawing.raw)
            component['svg_sha256'] = _digest(raw)
            component['bbox_font_units'] = _template_bounds(output)
        for instance in component['instances']:
            cp = shared.codepoint(instance['codepoint'])
            for template_index, path_index in enumerate(instance['path_indices_zero_based']):
                assert (cp, path_index) not in assignments
                assignments[cp, path_index] = component['id'], template_index

    seen = set()
    for row in manifest['glyphs']:
        cp = shared.codepoint(row['codepoint'])
        if cp in seen:
            raise ValueError(f'Duplicate source codepoint U+{cp:05X}')
        seen.add(cp)
        drawing = shared.read_drawing(svg_dir / f'U{cp:05X}.svg', cp)
        if _digest(drawing.raw) != row['svg_sha256']:
            raise ValueError(f'U+{cp:05X}: stale source SVG hash')
        original_lineage[cp] = {key: deepcopy(value) for key, value in row.items() if key != 'svg_sha256'}
        replacements = {}
        counts['glyphs_checked'] += 1
        counts['paths_checked'] += len(drawing.strokes)
        for index, (points, closed) in enumerate(drawing.strokes):
            binding = assignments.get((cp, index))
            if binding:
                component_id, template_index = binding
                template = template_drawings[component_id]
                if drawing.strokes[index] != template.strokes[template_index]:
                    raise ValueError(f'U+{cp:05X}: source component differs from its bound template')
                output, output_closed = template_outputs[component_id][template_index]
                _, _, evidence = cleanup_stroke(points, closed, epsilon, close_exact_loops)
            else:
                output, output_closed, evidence = cleanup_stroke(points, closed, epsilon, close_exact_loops)
            if not evidence['changed']:
                continue
            replacements[index] = output, output_closed
            counts['changed_paths'] += 1
            removed = len(evidence['removed_start_vertices']) + len(evidence['removed_end_vertices'])
            counts['terminal_micro_knot_paths'] += int(removed > 0)
            counts['removed_terminal_vertices'] += removed
            counts['exact_full_loops_closed'] += int(evidence['closed_exact_full_loop'])
            counts['shared_component_paths_changed' if binding else 'unassigned_paths_changed'] += 1
            if len(details) < detail_limit:
                details.append({'codepoint': f'U+{cp:05X}',
                                'path_index_zero_based': index,
                                'path_id': drawing.nodes[index].get('id'),
                                'component_id': binding[0] if binding else None,
                                **evidence})
        if replacements:
            raw = _drawing_bytes(drawing, replacements)
            changed_files[drawing.path] = raw
            old_file_hashes[drawing.path] = _digest(drawing.raw)
            row['svg_sha256'] = _digest(raw)
            counts['changed_glyphs'] += 1
        assert {key: value for key, value in row.items() if key != 'svg_sha256'} == original_lineage[cp]

    counts['changed_templates'] = len(template_changes)
    # The parser source, manifests and files may not change between validation
    # and publication of this plan. No output is written before these checks.
    if source_manifest_path.read_bytes() != source_manifest_raw or atlas_path.read_bytes() != atlas_raw:
        raise ValueError('A source manifest changed concurrently; rerun the cleanup')
    for path, before_hash in old_file_hashes.items():
        if _digest(path.read_bytes()) != before_hash:
            raise ValueError(f'{path}: source changed concurrently')
    changed = bool(changed_files)
    proposed_source_raw = shared.json_bytes(manifest) if counts['changed_glyphs'] else source_manifest_raw
    proposed_atlas_raw = shared.json_bytes(atlas) if template_changes else atlas_raw
    if apply and changed:
        # Templates first, then all exact copies and unassigned paths. We do not
        # weaken the ordinary synchronizer's guard against accidental closures.
        for path, raw in changed_files.items():
            shared.atomic(path, raw)
        if template_changes:
            shared.atomic(atlas_path, proposed_atlas_raw)
        if counts['changed_glyphs']:
            shared.atomic(source_manifest_path, proposed_source_raw)
        shared.sync(svg_dir, components_dir, apply=False)
    return {
        'schema_version': 1,
        'status': 'applied' if apply and changed else ('cleanup_available' if changed else 'clean'),
        'policy': {'epsilon_font_units': epsilon,
                   'endpoint_only': True, 'interior_simplification': False,
                   'stroke_deletion': False, 'open_endpoints_preserved': True,
                   'close_exact_loops': close_exact_loops,
                   'loop_guards': {'endpoint_distance': EXACT_LOOP_EPSILON, 'length_greater_than': 60,
                                   'minimum_bbox_dimension': 15, 'minimum_absolute_signed_area': 225},
                   'micro_knot_hausdorff_bound_font_units': epsilon,
                   'loop_seam_bound_font_units': EXACT_LOOP_EPSILON},
        'counts': counts,
        'shared_components': {'templates': sync_before['components'], 'instances': sync_before['instances'],
                              'before': 'in_sync', 'after': 'in_sync' if apply else 'not_applied'},
        'source_manifest_before_sha256': _digest(source_manifest_raw),
        'source_manifest_after_sha256': _digest(proposed_source_raw),
        'component_manifest_before_sha256': _digest(atlas_raw),
        'component_manifest_after_sha256': _digest(proposed_atlas_raw),
        'historical_authoring_fields_preserved': True,
        'details': details, 'details_truncated': counts['changed_paths'] > len(details),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--svg-dir', type=Path, default=Path('svg'))
    parser.add_argument('--components-dir', type=Path, default=Path('components'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--check', action='store_true', help='Report candidates without writing sources (default)')
    mode.add_argument('--apply', action='store_true', help='Apply validated source cleanup and refresh current hashes')
    parser.add_argument('--epsilon', type=float, default=DEFAULT_EPSILON)
    parser.add_argument('--close-exact-loops', action='store_true',
                        help='Also declare substantial near-exact full loops closed; omitted by default')
    parser.add_argument('--detail-limit', type=int, default=100, help='Maximum path records in the report')
    parser.add_argument('--report', type=Path, help='Optional bounded JSON report path')
    args = parser.parse_args(argv)
    try:
        report = clean_sources(args.svg_dir, args.components_dir, apply=args.apply,
                               epsilon=args.epsilon, close_exact_loops=args.close_exact_loops,
                               detail_limit=args.detail_limit)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            shared.atomic(args.report, shared.json_bytes(report))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f'error: {error}\n')
    print(json.dumps(report, indent=2))
    if not args.apply and report['status'] == 'cleanup_available':
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
