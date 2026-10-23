"""Endpoint-only cleanup, shared-source propagation and fail-before-write checks."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import cleanup_caps as cleanup
import sync_components as shared


def svg(cp, paths):
    lines = [f'<svg xmlns="{shared.URI}" viewBox="0 0 1024 1024" data-codepoint="U+{cp:05X}" data-advance="1024" data-schema="seal-centerline-1">',
             '  <g transform="matrix(1 0 0 -1 0 832)" fill="none" stroke="#000" stroke-width="30" stroke-linecap="round" stroke-linejoin="round">']
    lines += [f'    <path id="stroke-{index}" d="{path}"/>' for index, path in enumerate(paths, 1)]
    return ('\n'.join(lines + ['  </g>', '</svg>', ''])).encode()


class NumericalCleanup(unittest.TestCase):
    def test_only_terminal_micro_knots_change_and_cleanup_is_idempotent(self):
        original = [(0, 0), (.249, 0), (.0001, 0), (.249, .0001), (0, .0002),
                    (10, 10), (30, 20), (40, 20), (49.9, 20), (50, 20)]
        points, closed, record = cleanup.cleanup_stroke(original, False, close_exact_loops=False)
        self.assertEqual(points, [(0, 0), (10, 10), (30, 20), (40, 20), (50, 20)])
        self.assertFalse(closed)
        self.assertEqual(len(record['removed_start_vertices']), 4)
        self.assertEqual(len(record['removed_end_vertices']), 1)
        self.assertEqual(cleanup.cleanup_stroke(points, closed, close_exact_loops=False)[0], points)
        # Do not reach across even a tiny meaningful excursion outside the disk.
        hook = [(0, 0), (.251, 0), (.05, 0), (10, 0)]
        self.assertEqual(cleanup.cleanup_stroke(hook, False, close_exact_loops=False)[0], hook)
        self.assertEqual(cleanup.cleanup_stroke([(4, 5)], False)[0], [(4, 5)])
        self.assertEqual(cleanup.cleanup_stroke(original, True)[0], original)
        with self.assertRaises(ValueError):
            cleanup.cleanup_stroke(original, False, epsilon=12)

    def test_full_loop_closure_is_separate_and_rejects_dots_hairpins_and_real_gaps(self):
        loop = [(0, 0), (100, 0), (100, 100), (0, 100), (1e-8, 0)]
        points, closed, record = cleanup.cleanup_stroke(loop, False, close_exact_loops=True)
        self.assertTrue(closed)
        self.assertTrue(record['closed_exact_full_loop'])
        self.assertEqual(points, loop[:-1])
        self.assertEqual(cleanup.cleanup_stroke(points, True)[0], points)
        self.assertFalse(cleanup.cleanup_stroke(loop, False, close_exact_loops=False)[1])
        for candidate in [
            [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)],
            [(0, 0), (50, 50), (100, 100), (50, 50), (0, 0)],
            [(0, 0), (100, 0), (100, 100), (0, 100), (.01, 0)],
        ]:
            self.assertFalse(cleanup.cleanup_stroke(candidate, False, close_exact_loops=True)[1])


class SourceCleanup(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.svg, self.components = self.root / 'svg', self.root / 'components'
        self.svg.mkdir()
        self.components.mkdir()
        self.component_paths = ['M 100 100 L 100.1 100 L 100 100 L 200 100',
                                'M 100 200 L 200 200 L 200 300 L 100 300 L 100 200']
        sources = {
            0x3D001: ['M 600 100 L 600 120 L 620 120', *self.component_paths],
            0x3D002: [self.component_paths[0], 'M 700 200 L 799.9 200 L 800 200', self.component_paths[1]],
        }
        manifest = {'schema_version': 1, 'upstream': {'original': 'untouched'}, 'glyphs': []}
        for cp, paths in sources.items():
            raw = svg(cp, paths)
            (self.svg / f'U{cp:05X}.svg').write_bytes(raw)
            manifest['glyphs'].append({'codepoint': f'U+{cp:05X}', 'svg_sha256': cleanup._digest(raw),
                                      'authoring_source_sha256': 'a' * 64, 'authoring_geometry_sha256': 'b' * 64})
        self.original_manifest = deepcopy(manifest)
        (self.svg / 'manifest.json').write_bytes(shared.json_bytes(manifest))
        template = svg(0x3D001, self.component_paths)
        (self.components / 'example-left.svg').write_bytes(template)
        atlas = {'schema_version': 1, 'components': [{
            'id': 'example-left', 'family': '1.3D000', 'position': 'left', 'file': 'example-left.svg',
            'svg_sha256': cleanup._digest(template), 'bbox_font_units': [100, 100, 200, 300],
            'instances': [{'codepoint': 'U+3D001', 'path_indices_zero_based': [1, 2]},
                          {'codepoint': 'U+3D002', 'path_indices_zero_based': [0, 2]}],
        }]}
        (self.components / 'manifest.json').write_bytes(shared.json_bytes(atlas))

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}

    def test_shared_template_cleanup_updates_all_copies_and_keeps_lineage_and_path_ids(self):
        before = self.snapshot()
        report = cleanup.clean_sources(self.svg, self.components)
        self.assertEqual(report['status'], 'cleanup_available')
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(report['counts']['changed_glyphs'], 2)
        self.assertEqual(report['counts']['changed_templates'], 1)
        self.assertEqual(report['counts']['changed_paths'], 3)
        self.assertEqual(report['counts']['exact_full_loops_closed'], 0)
        report = cleanup.clean_sources(self.svg, self.components, apply=True)
        self.assertEqual(report['status'], 'applied')
        self.assertEqual(shared.sync(self.svg, self.components)['status'], 'in_sync')
        first = shared.read_drawing(self.svg / 'U3D001.svg')
        self.assertEqual(first.nodes[0].get('d'), 'M 600 100 L 600 120 L 620 120')
        self.assertEqual([node.get('id') for node in first.nodes], ['stroke-1', 'stroke-2', 'stroke-3'])
        self.assertEqual(first.strokes[1][0], ((100, 100), (200, 100)))
        updated = json.loads((self.svg / 'manifest.json').read_text())
        self.assertEqual(updated['upstream'], self.original_manifest['upstream'])
        for before_row, after_row in zip(self.original_manifest['glyphs'], updated['glyphs']):
            self.assertEqual({key: value for key, value in before_row.items() if key != 'svg_sha256'},
                             {key: value for key, value in after_row.items() if key != 'svg_sha256'})
        clean = self.snapshot()
        self.assertEqual(cleanup.clean_sources(self.svg, self.components, apply=True)['status'], 'clean')
        self.assertEqual(self.snapshot(), clean)
        # Full loops are an explicit separate migration, including shared copies.
        report = cleanup.clean_sources(self.svg, self.components, apply=True, close_exact_loops=True)
        self.assertEqual(report['counts']['exact_full_loops_closed'], 2)
        self.assertTrue(shared.read_drawing(self.svg / 'U3D001.svg').strokes[2][1])
        self.assertEqual(shared.sync(self.svg, self.components)['status'], 'in_sync')

    def test_stale_unassigned_source_hash_fails_before_templates_or_glyphs_are_written(self):
        path = self.svg / 'U3D002.svg'
        path.write_bytes(path.read_bytes().replace(b'L 799.9 200', b'L 799.8 200'))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'stale'):
            cleanup.clean_sources(self.svg, self.components, apply=True)
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
