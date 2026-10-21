"""One mixed seven-glyph roundtrip, chunk boundary and integrity regression."""
import json, os, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fontTools.ttLib import TTFont
from svg_font import build, read_svg, raw_records, digest
ROOT=Path(__file__).resolve().parents[1]
class Roundtrip(unittest.TestCase):
    def test_mixed_roundtrip(self):
        svg=ROOT/'tests/sample-svg'
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            report=build(svg,tmp/'a',chunk_size=3)
            build(svg,tmp/'b',chunk_size=3)
            self.assertEqual(digest(tmp/'a/Regular.ttf'),digest(tmp/'b/Regular.ttf'))
            self.assertEqual(digest(tmp/'a/Regular.woff2'),digest(tmp/'b/Regular.woff2'))
            with TTFont(tmp/'a/Regular.ttf') as font:
                self.assertEqual(font['head'].unitsPerEm,1024)
                self.assertEqual(font['OS/2'].usWeightClass,400)
                expected={int(r['codepoint'][2:],16):f"u{int(r['codepoint'][2:],16):05X}" for r in json.loads((svg/'manifest.json').read_text())['glyphs']}
                self.assertEqual(font.getBestCmap(),expected)
                with TTFont(tmp/'a/Regular.woff2') as web:
                    self.assertEqual(web.getBestCmap(),expected)
                    for name in font.getGlyphOrder():
                        self.assertEqual(web['glyf'][name].getCoordinates(web['glyf']),font['glyf'][name].getCoordinates(font['glyf']))
                        self.assertEqual(web['hmtx'][name],font['hmtx'][name])
                production=os.environ.get('SEAL_PRODUCTION_REGULAR')
                if production:
                    with TTFont(production,lazy=True) as old:
                        raw=raw_records(old); current=raw_records(font)
                        for name in font.getGlyphOrder():
                            # Short-loca subsets may pad glyph blocks; compare canonical glyph encoding.
                            font['glyf'][name].getCoordinates(font['glyf'])
                            old['glyf'][name].getCoordinates(old['glyf'])
                            self.assertEqual(font['glyf'][name].compile(font['glyf']),old['glyf'][name].compile(old['glyf']),name)
                            self.assertEqual(font['hmtx'][name],old['hmtx'][name],name)
            # An altered SVG cannot silently build against the old manifest.
            import shutil
            edited=tmp/'edited'; shutil.copytree(svg,edited)
            file=edited/'U3D000.svg'; file.write_text(file.read_text().replace('30"','31"'))
            with self.assertRaisesRegex(ValueError,'SVG hash mismatch'): build(edited,tmp/'bad')
            with self.assertRaisesRegex(ValueError,'Unsupported group'): read_svg(file)
if __name__=='__main__': unittest.main()
