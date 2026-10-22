# Sealie

English · [简体中文](README.zh-CN.md)

![Sealie — Dao De Jing marketing artwork](marketing/sealie-marketing.png)

Sealie is an AI-assisted Small Seal Gothic font developed by **ieb** with **OpenAI Codex (GPT-6)** and parallel subagents. It covers **all 11,328 Unicode 18 Small Seal codepoints, U+3D000–U+3FC3F**, in a consistent rounded monoline style. The font family is named *Panorama Gothic Seal Individual* in the downloadable files.

**Regular 400 has completed recorded visual review across the full repertoire.** The variable font spans weights 300–700; the other weights still need further optical review, so the release remains a prerelease. See the [coverage report](reports/coverage.json).

## Models and creation process

Codex coordinated the work, wrote generation instructions and build tools, made vector repairs, and ran reviews. Parallel agents worked in **64-codepoint assignments**, with independent review before geometry was accepted. OpenAI image generation (`image_gen.imagegen`) produced the native character drawings. Python tracing and fontTools then turned the reviewed drawings into font geometry.

The process was:

1. **Read the references.** Character structures were compared with the THX, CCZ, QJZ and DYC specimens available in the official Unicode charts. When specimens differed, the drawing followed a coherent attested form.
2. **Create and review each drawing.** Generated drawings were checked for the correct branches, detached strokes, counters and proportions. Failed drawings and later vector corrections were recorded separately.
3. **Construct centerlines.** Automatic tracking followed the skeleton of the generated drawing and fitted editable centerlines. Reviewed vector overrides corrected structural or tracing defects. Reference-font outlines were not extracted to construct the font.
4. **Apply one shared style.** Glyphs were proportionally normalized within a 1024-unit em, with a 1024-unit advance and a maximum centerline extent of 738 units. Regular uses a 30-unit pen with round caps and joins. The variable weights share the same centerlines and change the pen width.
5. **Review the actual font.** Independent agent reviews compared the compiled Regular glyphs with the references. Coverage, bounds, spacing and serialized glyph data were checked, and accepted geometry was bound to hashes. Unchanged work reused prior checks when its recorded geometry and font data matched.

These are AI-assisted designs with recorded review, rather than specialist paleographic certification. The source path order does not establish historical writing order. Building or using the published font requires no AI service or model key.

## SVG source and builds

**[svg/](svg/) is the maintained glyph source in this repository.** It contains one editable SVG per codepoint and a [manifest](svg/manifest.json) binding the filenames, codepoints and hashes. The SVGs contain exact normalized centerlines in the `seal-centerline-1` format. Private drawing drafts and reference images are not needed to rebuild Regular 400.

With Python 3.11 or newer, run from the repository root:

```sh
python -m pip install -r requirements.txt
python tools/svg_font.py --svg-dir svg --output build
```

This creates `build/Regular.ttf`, `build/Regular.woff2` and a build manifest. The [Build font from SVG workflow](https://github.com/iebb/sealie/actions/workflows/build-font.yml) runs the same command and uploads the results. It can run manually or after SVG/tooling changes. This builder produces Regular 400; the existing variable fonts are supplied separately in the download bundle.

See the [build and editing guide](docs/BUILD-FROM-SVG.md) for the SVG constraints, manifest updates and validation commands.

## Downloads and previews

- [Font prerelease](https://github.com/iebb/sealie/releases/tag/checkpoint-011328) · [font files and all 13 ZIP parts](fonts/)
- [Regular WOFF](fonts/PanoramaGothicSealIndividual-Regular.woff)
- [Variable webfont CSS](fonts/variable.css) · [177 webfont subsets, at most 64 glyphs each](fonts/variable/)
- [Weight preview](previews/weight-slider.html)
- [45 square PNG grid sheets covering the complete repertoire](png/)
- [Editable SVG sources](svg/)

Download all parts named `Sealie-SmallSeal-011328.zip.001` through `.013` into one folder. 7-Zip can open the first part when all parts are present. On macOS/Linux:

```sh
cat Sealie-SmallSeal-011328.zip.* > Sealie-SmallSeal-011328.zip
unzip Sealie-SmallSeal-011328.zip
```

The bundle contains the variable TTF, direct Regular, five named-weight TTFs, WOFF files and licenses. The webfont CSS loads small subsets as needed. Small Seal uses its own Unicode codepoints; typing an ordinary CJK character does not automatically select its seal form.

![Sample of the completed Small Seal repertoire](previews/glyphs.png)

The grid sheets use 16×16 cells per sheet, with 128-pixel cells. Individual 16×16-pixel glyph PNGs are no longer tracked; edit the SVG sources instead.

## Contributions

**Contributions and commits are welcome**, including glyph corrections, spacing improvements, documentation and build-tool fixes. For a glyph correction, identify the codepoint, explain the structural issue and include the reference or comparison used to assess it.

Edit `svg/Uxxxxx.svg`, preserving its codepoint, advance, group transform and round-stroke attributes. After an intentional edit, refresh the manifest and build:

```sh
python tools/svg_font.py --svg-dir svg --refresh-manifest
python tools/svg_font.py --svg-dir svg --output build
```

Review the rendered glyph before submitting a focused commit or pull request. Refreshing a hash records new source bytes; it does not give the change visual approval. Keep glyph sources as SVGs and generated individual bitmaps out of commits.

## Artwork and license

The marketing artwork uses “道可道，非常道” from the first chapter of the *Dao De Jing*, with real project glyphs at weights 300, 400, 500, 600 and 700 in shades of gray. Image generation added the paper and ink finish to a rendered font specimen. The [exact-font SVG reference](marketing/sealie-dao-reference.svg) and [artwork provenance](marketing/provenance.json) are included.

Fonts, SVG sources and font software are distributed under the **SIL Open Font License 1.1**. See [LICENSE-OFL.txt](LICENSE-OFL.txt) and [OFL-1.1.txt](OFL-1.1.txt).
