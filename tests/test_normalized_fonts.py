"""Real stroke topology fallback and mixed SVG→static/variable roundtrip."""
from pathlib import Path
import hashlib, json, shutil, sys, tempfile, unittest
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from compact_backend import compact_outline, compatible_masters, signature
from stroke_backend import expand_polylines
from build_normalized_fonts import build, WIDTHS, WEIGHTS, STYLES


class NormalizedFonts(unittest.TestCase):
    def test_roundtrip_and_cached_input_integrity(self):
        fixture=ROOT/'tests/sample-svg'
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);cache=folder/'cache'
            first=build(fixture,folder/'a',cache,chunk_size=3,workers=2)
            second=build(fixture,folder/'b',cache,chunk_size=3,workers=2)
            self.assertEqual(first['glyph_count'],7)
            self.assertEqual({r['name']:r['sha256'] for r in first['files']},
                             {r['name']:r['sha256'] for r in second['files']})
            expected={int(r['codepoint'][2:],16):f"u{int(r['codepoint'][2:],16):05X}"
                      for r in json.loads((fixture/'manifest.json').read_text())['glyphs']}
            with TTFont(folder/'a/Variable.woff') as web:
                self.assertEqual(web.getBestCmap(),expected)
                self.assertEqual([(a.axisTag,a.minValue,a.defaultValue,a.maxValue)
                                  for a in web['fvar'].axes],[('wght',300,400,700)])
            for weight,style in zip(WEIGHTS,STYLES):
                with TTFont(folder/'a/Variable.ttf') as variable, TTFont(folder/'a'/(style+'.ttf')) as master:
                    instance=instantiateVariableFont(variable,{'wght':weight},inplace=True)
                    self.assertEqual(instance.getBestCmap(),expected)
                    for name in master.getGlyphOrder():
                        direct=master['glyf'][name];actual=instance['glyf'][name]
                        self.assertEqual(direct.endPtsOfContours,actual.endPtsOfContours)
                        self.assertEqual([v&1 for v in direct.flags],[v&1 for v in actual.flags])
                        maximum=max(abs(a-b) for p,q in zip(direct.coordinates,actual.coordinates) for a,b in zip(p,q))
                        self.assertLessEqual(maximum,1)
                        self.assertEqual(instance['hmtx'][name][0],1024)
                        self.assertLessEqual(abs(instance['hmtx'][name][1]-master['hmtx'][name][1]),1)
                        if weight==400:
                            self.assertEqual(direct.coordinates,actual.coordinates)
            edited=folder/'edited';shutil.copytree(fixture,edited)
            path=edited/'U3D000.svg';path.write_text(path.read_text().replace('143.0','144.0'))
            # A valid cache must never hide an SVG changed without a manifest update.
            with self.assertRaisesRegex(ValueError,'Stale SVG manifest'):
                build(edited,folder/'bad',cache,chunk_size=3,workers=2)

    def test_real_microcusp_uses_one_backend_for_every_master(self):
        # Four-point reduction of an actual U+3D4D9 path. Skia0.9.2 chooses
        # different join topology as width changes; the legacy disks stay compatible.
        points=[(702.8579260027111,300.7472290885894),
                (702.8579750377991,300.74737642397287),
                (703.1337386115454,300.7524177957682),
                (702.857926002711,300.74722908858973)]
        strokes=[(points,False)]
        analytic=[compact_outline(strokes,width/2)[0] for width in WIDTHS]
        self.assertTrue(any(signature(g)!=signature(analytic[0]) for g in analytic))
        masters,fallback=compatible_masters(strokes,WIDTHS,expand_polylines)
        self.assertTrue(fallback)
        self.assertTrue(all(signature(g)==signature(masters[0][0]) for g,_ in masters))


if __name__=='__main__':unittest.main()
