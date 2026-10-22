# Editable Small Seal SVGs → Regular font

The `svg/` directory is the font source. Each named `Uxxxxx.svg` contains one complete glyph, with a matching Unicode codepoint, 1024-unit advance, a 30-unit round pen and exact normalized centerline coordinates. No reference images, private drawing files or existing font outlines are needed to build it. Font software and these sources use the SIL Open Font License 1.1; see [LICENSE-OFL.txt](../LICENSE-OFL.txt) and [OFL-1.1.txt](../OFL-1.1.txt).

## Build

Use Python 3.11 or newer:

```sh
python -m pip install -r requirements.txt
python tools/svg_font.py --svg-dir svg --output build
```

The GitHub **Build font from SVG** action runs the same command and uploads `Regular.ttf`, `Regular.woff2`, license files and a build manifest. It can be started manually or by changing SVGs/tooling. Artifacts are not automatically committed or published. Only the Regular 400 weight is generated.

The pinned original stroker expands each centerline into the same ordered round disks and segment rectangles as the reviewed production font, with the same TrueType rounding. At most 64 glyphs are expanded together; finished chunks are merged as serialized glyphs. No global variable-font instancing occurs. Final output retains the full manifest cmap and checks every serialized glyph and metric after saving. The complete serialized output and WOFF2 compressor still need memory proportional to the final font size.

## Edit

The visible SVG is editable vector artwork. Its group flips font y coordinates around baseline 832 to display correctly in a square 1024 viewBox. Preserve that group, its stroke attributes, filename/codepoint and advance. Paths support explicit absolute `M`, `L`, and terminal `Z`; retain one path per stroke. Coordinates are intentionally full-precision decimals, not rounded display coordinates. Do not flatten or remove this wrapper in an editor. Curves must be converted to sufficiently fine polylines before building; arbitrary SVG transforms, filled shapes and other commands are rejected.

After an intentional source edit, refresh the manifest hashes, review the artwork, then build:

```sh
python tools/svg_font.py --svg-dir svg --refresh-manifest
python tools/svg_font.py --svg-dir svg --output build
```

Refreshing hashes declares changed source bytes; it does not confer historical or visual review approval. The build reads only the codepoints listed in `svg/manifest.json`; unlisted SVGs are ignored, and missing or stale listed files fail. Add/remove manifest rows explicitly when changing the repertoire. `source_sha256` and `geometry_sha256` preserve the original export lineage and are not updated by editing SVGs.

## Incremental export from reviewed authoring sources

Maintainers with the reviewed JSON source tree and acceptance registry can run:

```sh
python tools/export_centerlines.py \
  --source-root /path/to/design/strokes-individual \
  --registry /path/to/design/quality/accepted-geometry.json \
  --output svg
```

Only registry-listed, accepted-hash geometry is exported; manual JSON overrides `auto/`. The exporter uses the original adaptive flattening and per-glyph 738-unit normalization before writing exact float coordinates. It skips rewriting identical SVG bytes and writes the sorted manifest atomically. Old unlisted SVG files are retained on disk but excluded from the manifest/build, so removed coverage cannot silently survive. No reference or provenance PNGs are copied. `--codepoints U+3D000 U+3D12F` selects a small validation subset.

## Validation

A seven-glyph fixture mixes the first legacy block, a round/dense glyph, fine branches and crossings. It spans three build chunks in the test, checks deterministic TTF/WOFF2 output, exact webfont coordinates/metrics/cmap, and rejects changed SVG hashes and unsupported stroke styles:

```sh
python -m unittest discover -s tests
```

Maintainers can also set `SEAL_PRODUCTION_REGULAR=/path/to/production-Regular.ttf` for exact canonical `glyf` encoding and `hmtx` comparison of those seven glyphs plus `.notdef`. Small subsets can use short-loca glyph padding while the full font uses long offsets. Whole-font table bytes may differ because repertoire-dependent tables, names and metadata are rebuilt. SVG rendering uses native SVG circles/joins; the generated font preserves the established TrueType disk approximation and quantization. Variable weights and arbitrary SVG interpretation are outside this delivery.

Subsequent exports reuse unchanged accepted source geometry through a local, ignored `.export-cache.json`. Changed sources, edited SVGs or changed export settings invalidate the relevant entry. The published manifest remains the build input.

## Preview images

`svg/` is the maintained glyph source. `png/` retains 45 square sheets with 16×16 grids of cells covering all 11,328 glyphs at Regular 400. Individual 16×16-pixel glyph PNGs and their export manifest are not tracked in this repository.

Maintainers who need individual bitmaps locally can use the optional exporter with the original production font and its manifest. Install Pillow separately and write the results under the ignored `build/` directory:

```sh
python -m pip install Pillow
python tools/export_png_glyphs.py \
  --font /path/to/production-Regular.ttf \
  --manifest /path/to/production/manifest.json \
  --geometry-manifest svg/manifest.json \
  --output build/png16
```

The production and SVG manifests must bind the same accepted sources and geometry. Unchanged bitmaps retain their bytes and modification times on subsequent exports. These local previews are not font sources and should not be committed.

The browser weight preview uses `fonts/variable.css` to load variable WOFF subsets of at most 64 glyphs as needed. These preserve the verified glyph, variation, metric and axis tables. Unchanged subsets are reused across checkpoints. The complete variable TTF and WOFF remain in the ZIP download bundle.
