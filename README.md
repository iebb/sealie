# Sealie

Built outputs for the Panorama Gothic Small Seal font for Unicode 18.

Current checkpoint: **4,948 of 11,328 glyphs reviewed at Regular 400**. Work continues across the full Small Seal block, U+3D000–U+3FC3F, in batches of 64.

- [Font ZIP part 1 of 6](fonts/Sealie-SmallSeal-004948.zip.001)
- [Font ZIP part 2 of 6](fonts/Sealie-SmallSeal-004948.zip.002)
- [Font ZIP part 3 of 6](fonts/Sealie-SmallSeal-004948.zip.003)
- [Font ZIP part 4 of 6](fonts/Sealie-SmallSeal-004948.zip.004)
- [Font ZIP part 5 of 6](fonts/Sealie-SmallSeal-004948.zip.005)
- [Font ZIP part 6 of 6](fonts/Sealie-SmallSeal-004948.zip.006)
- [Variable webfont CSS](fonts/variable.css) · [64-glyph webfonts](fonts/variable/)
- [Regular WOFF](fonts/PanoramaGothicSealIndividual-Regular.woff)
- [Weight preview](previews/weight-slider.html)
- [All codepoints in 16×16 PNG grids](png/)
- [Individual 16×16-pixel PNGs](png16/)
- [Editable per-glyph SVGs](svg/)
- [Build a font from SVG](docs/BUILD-FROM-SVG.md) · [GitHub workflow](https://github.com/iebb/sealie/actions/workflows/build-font.yml)
- [Coverage and validation](reports/coverage.json)

Download every ZIP part into one folder. 7-Zip can open the first part when all parts are present. On macOS/Linux, join and extract them:

```sh
cat Sealie-SmallSeal-004948.zip.* > Sealie-SmallSeal-004948.zip
unzip Sealie-SmallSeal-004948.zip
```

The ZIP includes the variable TTF, direct Regular, five named-weight TTFs, WOFF files and licenses. The Regular WOFF and variable webfont subsets stay in [fonts](fonts/) for local browser previews. The glyphs use a shared rounded monoline construction with proportional sizing and a 1024-unit advance. The original 128 outlines and metrics remain unchanged. All five named weights pass compiled size checks; their optical review continues. This is an incomplete development font.

A sample of the latest additions in this checkpoint:

![Latest glyph additions](previews/glyphs.png)

The repository includes one normalized, editable SVG for each of the 4,948 reviewed glyphs, one transparent 16×16-pixel PNG per reviewed glyph, and 45 square PNG sheets covering every Small Seal codepoint position. Each PNG contains a 16×16 grid; uncreated glyphs are labeled pending. Each checkpoint adds its new reviewed SVGs and updates the affected sheets.

To rebuild the Regular font from the SVGs, run from the repository root:

```sh
python -m pip install -r requirements.txt
python tools/svg_font.py --svg-dir svg --output build
```

This creates Regular TTF and WOFF2 files. The same build is available in GitHub Actions. The [build guide](docs/BUILD-FROM-SVG.md) explains editing and the SVG format. Production variable fonts remain available in the download bundle.

This repository publishes font files, editable SVG outputs, grid previews, licenses, reports, and the SVG build workflow. Private authoring drafts and reference images stay in the working repository. Paths inside diagnostic reports identify that build workspace.

Fonts are distributed under the [SIL Open Font License](OFL-1.1.txt).
