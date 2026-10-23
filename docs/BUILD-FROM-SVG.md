# Editable Small Seal SVGs → static and variable fonts

The `svg/` directory is the font source, with reusable radical sources in `components/`. Each named `Uxxxxx.svg` contains one complete glyph, with a matching Unicode codepoint, 1024-unit advance, a 30-unit round pen and exact centerline coordinates. No reference images, private drawing files or existing font outlines are needed to build it. Font software and these sources use the SIL Open Font License 1.1; see [LICENSE-OFL.txt](../LICENSE-OFL.txt) and [OFL-1.1.txt](../OFL-1.1.txt).

## Build

Use Python 3.11 or newer:

```sh
python -m pip install -r requirements.txt
python tools/sync_components.py --check
python tools/build_normalized_fonts.py --svg-dir svg --output build
```

This builds `Light.ttf`, `Regular.ttf`, `Medium.ttf`, `SemiBold.ttf`, `Bold.ttf`, `Variable.ttf`, full Regular/variable WOFFs, variable webfont subsets and a build manifest. Add `--woff2` to generate a Regular WOFF2. The GitHub **Build font from SVG** action runs the same builder and uploads the fonts, licenses and manifest. It can be started manually or by changing sources/tooling. Artifacts are not automatically committed or published.

The compact stroker uses pinned `skia-pathops` round caps and joins, without simplifying source polylines or performing Boolean union. Conic conversion tolerance is 0.05 font units at Regular, scaled with pen width. It compares contour endpoints and on/off flags across all five masters. If a glyph's compact topology changes with weight, every master of that glyph uses the original disk/rectangle stroker instead.

At most 64 glyphs are expanded per chunk, with up to four workers by default (`--workers 2` lowers concurrency). Finished chunks are merged as serialized glyphs and variation data. No global variable-font instancing occurs. The builder checks source hashes, coverage, em bounds and compatible masters, then checks serialized glyphs, metrics and variation bytes after merging. Exact-input caches live under `build/.build-cache`. The complete serialized output and optional WOFF2 compressor still need memory proportional to the final font size.

## Edit

The visible SVG is editable vector artwork. Its group flips font y coordinates around baseline 832 to display correctly in a square 1024 viewBox. Preserve that group, its stroke attributes, filename/codepoint and advance. Paths support explicit absolute `M`, `L`, and terminal `Z`; retain one path per stroke. Coordinates are intentionally full-precision decimals, not rounded display coordinates. Do not flatten or remove this wrapper in an editor. Curves must be converted to sufficiently fine polylines before building; arbitrary SVG transforms, filled shapes and other commands are rejected.

After an intentional source edit, refresh the manifest hashes, review the artwork, then build:

```sh
python tools/svg_font.py --svg-dir svg --refresh-manifest
python tools/sync_components.py --check
python tools/build_normalized_fonts.py --svg-dir svg --output build
```

Refreshing hashes declares changed source bytes; it does not confer historical or visual review approval. The build reads only the codepoints listed in `svg/manifest.json`; unlisted SVGs are ignored, and missing or stale listed files fail. Add/remove manifest rows explicitly when changing the repertoire. `authoring_source_sha256` and `authoring_geometry_sha256` preserve historical authoring lineage and are not updated by editing SVGs. `svg_sha256` binds the current maintained source.

## Shared radicals

`components/manifest.json` maps each reviewed component template to its glyphs and zero-based path indices. Templates include the final placement, so registered occurrences use identical geometry and position. Different structural variants and positions have separate templates.

Edit the component SVG, preserving its round-pen wrapper and path count, then run:

```sh
python tools/sync_components.py --apply
python tools/sync_components.py --check
python tools/build_normalized_fonts.py --svg-dir svg --output build
```

The updater changes only assigned paths, preserves unrelated paths and IDs, and refreshes current hashes. It rejects overlapping assignments, missing paths, incompatible closures, unsupported SVG constructs and stale glyph hashes before writing. If you intentionally change an assigned glyph directly, refresh its hash before applying a component update; `--check` will still catch divergence from the shared template.

See [normalization policy and comparisons](NORMALIZATION.md) for how the initial component assignments were selected.

## Historical authoring imports

The optional legacy importer is for maintainers with the original reviewed JSON source tree and acceptance registry. It recreates the earlier authoring export, including its original proportional fitting. It does not include this revision's optical sizing or radical sharing. Export to a separate directory when investigating history; importing directly over maintained sources would discard later SVG edits:

```sh
python tools/export_centerlines.py \
  --source-root /path/to/design/strokes-individual \
  --registry /path/to/design/quality/accepted-geometry.json \
  --output build/historical-svg
```

Only registry-listed, accepted-hash geometry is exported; manual JSON overrides `auto/`. The exporter uses the original adaptive flattening and per-glyph 738-unit normalization before writing exact float coordinates. It skips rewriting identical SVG bytes and writes the sorted manifest atomically. Old unlisted SVG files are retained on disk but excluded from the manifest/build, so removed coverage cannot silently survive. No reference or provenance PNGs are copied. `--codepoints U+3D000 U+3D12F` selects a small validation subset.

## Validation

The tests cover mixed SVG fixtures, deterministic static/variable builds, all named weights, exact default-master geometry, webfont coverage, source hash rejection, a real topology fallback case, and safe shared-component propagation:

```sh
python -m unittest discover -s tests
```

The original `tools/svg_font.py` Regular-only builder remains available for legacy comparisons. Its optional `SEAL_PRODUCTION_REGULAR` test compares the seven historical fixture glyphs with the earlier production font; it is not an exact-byte test for the compact normalized font. SVG rendering and TrueType quantization can differ at subpixel edges. The new variable tests require matching topology, exact Regular coordinates, at most one font unit of named-instance coordinate/sidebearing error, and unchanged 1024-unit advances. Arbitrary SVG interpretation remains unsupported.

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

The browser weight preview uses `fonts/variable.css` to load normalized variable WOFF subsets of at most 64 glyphs as needed. The complete variable TTF and WOFF are in the four-part font ZIP linked from the normalized release.
