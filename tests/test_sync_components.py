"""Focused source-integrity tests for the shared-component updater."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import sync_components as subject


def document(cp, paths):
    lines = [f'<svg xmlns="{subject.URI}" viewBox="0 0 1024 1024" data-codepoint="U+{cp:05X}" data-advance="1024" data-schema="seal-centerline-1">',
             '  <g transform="matrix(1 0 0 -1 0 832)" fill="none" stroke="#000" stroke-width="30" stroke-linecap="round" stroke-linejoin="round">']
    lines.extend(f'    <path id="stroke-{i}" d="{path}"/>' for i, path in enumerate(paths, 1))
    return ('\n'.join(lines + ['  </g>', '</svg>', ''])).encode()


class ComponentSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.svg, self.components = self.root / 'svg', self.root / 'components'
        self.svg.mkdir()
        self.components.mkdir()
        self.old = ['M 100 100 L 200 100', 'M 100 200 L 200 200 L 200 300 L 100 300 Z']
        self.new = ['M 120 100 L 230 110', 'M 120 200 L 230 200 L 230 300 L 120 300 Z']
        self.files = {
            0x3D001: ['M 700 100 L 800 100', *self.old],
            0x3D002: [self.old[0], 'M 700 200 L 800 200', self.old[1], 'M 700 300 L 800 300'],
        }
        self.manifest = {'schema_version': 1, 'original_registry_sha256': 'c' * 64, 'glyphs': []}
        for cp, paths in self.files.items():
            raw = document(cp, paths)
            (self.svg / f'U{cp:05X}.svg').write_bytes(raw)
            self.manifest['glyphs'].append({'codepoint': f'U+{cp:05X}', 'svg_sha256': subject.sha256(raw),
                                            'source_sha256': 'a' * 64, 'geometry_sha256': 'b' * 64})
        self.save_glyph_manifest()
        self.template_path = self.components / 'example-left.svg'
        self.template_path.write_bytes(document(0x3D001, self.old))
        self.atlas = {'schema_version': 1, 'components': [{
            'id': 'example-left', 'family': '1.3D000', 'position': 'left', 'file': 'example-left.svg',
            'svg_sha256': subject.sha256(self.template_path.read_bytes()),
            'instances': [
                {'codepoint': 'U+3D001', 'path_indices_zero_based': [1, 2]},
                {'codepoint': 'U+3D002', 'path_indices_zero_based': [0, 2]},
            ],
        }]}
        self.save_atlas()

    def save_glyph_manifest(self):
        (self.svg / 'manifest.json').write_bytes(subject.json_bytes(self.manifest))

    def save_atlas(self):
        (self.components / 'manifest.json').write_bytes(subject.json_bytes(self.atlas))

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob('*') if path.is_file()}

    def test_one_template_updates_both_glyphs_without_changing_other_strokes_or_lineage(self):
        self.assertEqual(subject.sync(self.svg, self.components)['status'], 'in_sync')
        before_nodes = {cp: [dict(n.attrib) for n in subject.read_drawing(self.svg / f'U{cp:05X}.svg').nodes]
                        for cp in self.files}
        self.template_path.write_bytes(document(0x3D001, self.new))
        with self.assertRaisesRegex(ValueError, 'stale template SVG hash'):
            subject.sync(self.svg, self.components)
        report = subject.sync(self.svg, self.components, apply=True)
        self.assertEqual((report['changed_glyphs'], report['changed_paths'], report['refreshed_template_hashes']), (2, 4, 1))
        expected = [subject.parse_path(path) for path in self.new]
        assignments = {0x3D001: [1, 2], 0x3D002: [0, 2]}
        for cp, indices in assignments.items():
            drawing = subject.read_drawing(self.svg / f'U{cp:05X}.svg')
            self.assertEqual(len(drawing.nodes), len(self.files[cp]))
            for index, stroke in zip(indices, expected):
                self.assertEqual(drawing.strokes[index], stroke)
                self.assertEqual(drawing.nodes[index].get('id'), before_nodes[cp][index]['id'])
            for index in set(range(len(drawing.nodes))) - set(indices):
                self.assertEqual(drawing.nodes[index].attrib, before_nodes[cp][index])
        updated = json.loads((self.svg / 'manifest.json').read_text())
        self.assertEqual(updated['original_registry_sha256'], self.manifest['original_registry_sha256'])
        for row in updated['glyphs']:
            self.assertEqual(row['source_sha256'], 'a' * 64)
            self.assertEqual(row['geometry_sha256'], 'b' * 64)
        synced = self.snapshot()
        self.assertEqual(subject.sync(self.svg, self.components, apply=True)['changed_glyphs'], 0)
        self.assertEqual(subject.sync(self.svg, self.components)['status'], 'in_sync')
        self.assertEqual(self.snapshot(), synced)

    def test_unsafe_assignments_fail_before_any_write(self):
        initial_atlas = deepcopy(self.atlas)
        mutations = {
            'duplicate component ID': lambda atlas: atlas['components'].append(deepcopy(atlas['components'][0])),
            'overlap': lambda atlas: atlas['components'][0]['instances'].append({'codepoint': 'U+3D001', 'path_indices_zero_based': [1, 2]}),
            'missing glyph': lambda atlas: atlas['components'][0]['instances'][0].update(codepoint='U+3D003'),
            'out of range': lambda atlas: atlas['components'][0]['instances'][0].update(path_indices_zero_based=[1, 10]),
            'extra path': lambda atlas: atlas['components'][0]['instances'][0].update(path_indices_zero_based=[0, 1, 2]),
            'duplicate path': lambda atlas: atlas['components'][0]['instances'][0].update(path_indices_zero_based=[1, 1]),
            'bool index': lambda atlas: atlas['components'][0]['instances'][0].update(path_indices_zero_based=[False, 2]),
            'escape template directory': lambda atlas: atlas['components'][0].update(file='../outside.svg'),
            'closure change': lambda atlas: atlas['components'][0]['instances'][0].update(path_indices_zero_based=[0, 1]),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                self.atlas = deepcopy(initial_atlas)
                mutate(self.atlas)
                self.save_atlas()
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    subject.sync(self.svg, self.components, apply=True)
                self.assertEqual(self.snapshot(), before)

    def test_numeric_equivalence_hash_binding_and_svg_format(self):
        path = self.svg / 'U3D001.svg'
        raw = path.read_bytes().replace(b'M 100 100 L 200 100', b'M100.0,100 L200,100.0')
        path.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'stale glyph SVG hash'):
            subject.sync(self.svg, self.components, apply=True)
        self.manifest['glyphs'][0]['svg_sha256'] = subject.sha256(raw)
        self.save_glyph_manifest()
        self.assertEqual(subject.sync(self.svg, self.components)['status'], 'in_sync')
        self.assertEqual(subject.sync(self.svg, self.components, apply=True)['changed_glyphs'], 0)
        before = self.snapshot()
        self.template_path.write_bytes(document(0x3D001, ['M 100 100 C 100 200 200 200 200 100', self.old[1]]))
        with self.assertRaisesRegex(ValueError, 'Only absolute M/L/Z'):
            subject.sync(self.svg, self.components, apply=True)
        self.assertEqual(path.read_bytes(), before['svg/U3D001.svg'])
        self.assertEqual((self.svg / 'manifest.json').read_bytes(), before['svg/manifest.json'])


if __name__ == '__main__':
    unittest.main()
