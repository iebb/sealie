"""Focused routing check: unchanged inputs avoid flattening; changed one does not."""
import json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import export_centerlines as exporter
class IncrementalExport(unittest.TestCase):
    def test_same_input_and_changed_subset(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); sources=root/'sources'; sources.mkdir(); registry=root/'registry.json'; output=root/'svg'
            def save(number,end):
                data={'codepoint':f'U+{number:05X}','viewBox':[0,0,1024,1024],'stroke_width':43,'visual_reference_match_reviewed':True,'strokes':[{'path':f'M 100 100 L {end} 700'}]}
                (sources/f'U{number:05X}.json').write_text(json.dumps(data))
                return {'codepoint':data['codepoint'],'geometry_sha256':exporter.geometry_hash(data)}
            rows=[save(0x3D000,600),save(0x3D001,700)]
            registry.write_text(json.dumps({'schema_version':1,'glyphs':rows}))
            original=exporter.source_from_json
            with patch.object(exporter,'source_from_json',wraps=original) as flatten:
                first=exporter.export(sources,registry,output); self.assertEqual(flatten.call_count,2)
            before=(output/'U3D000.svg').stat().st_mtime_ns
            with patch.object(exporter,'source_from_json',side_effect=AssertionError('Unchanged source flattened')):
                same=exporter.export(sources,registry,output)
            self.assertEqual(same['reused_without_flattening'],2)
            self.assertEqual((output/'U3D000.svg').stat().st_mtime_ns,before)
            rows[1]=save(0x3D001,800); registry.write_text(json.dumps({'schema_version':1,'glyphs':rows}))
            with patch.object(exporter,'source_from_json',wraps=original) as flatten:
                changed=exporter.export(sources,registry,output); self.assertEqual(flatten.call_count,1)
            self.assertEqual(changed['reused_without_flattening'],1)
            self.assertEqual(changed['changed_svg_files'],1)
            # Edited art cannot hit the immutable-art fast route, even with same source.
            art=output/'U3D000.svg'; art.write_text(art.read_text().replace('30"','31"'))
            with patch.object(exporter,'source_from_json',wraps=original) as flatten:
                repaired=exporter.export(sources,registry,output); self.assertEqual(flatten.call_count,1)
            self.assertEqual(repaired['reused_without_flattening'],1)
            self.assertEqual(repaired['changed_svg_files'],1)
            # Accepted geometry changes without matching source bytes must be rejected.
            rows[0]['geometry_sha256']='0'*64; registry.write_text(json.dumps({'schema_version':1,'glyphs':rows}))
            with self.assertRaisesRegex(ValueError,'stale accepted geometry'): exporter.export(sources,registry,output)
if __name__=='__main__': unittest.main()
