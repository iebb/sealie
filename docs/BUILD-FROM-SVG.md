# Build Sealie from SVG sources

`svg/` contains the complete 11,328-codepoint font source. Reusable radicals live in `components/`: **180 templates registered to 3,763 glyphs**. Sources already include the current optical sizing and reviewed repairs; no private drawings, reference images or existing font outlines are needed to build them.

Each `Uxxxxx.svg` uses a 1024-unit advance, a 30-unit round pen and exact centerline coordinates. Font software and sources use SIL Open Font License 1.1; see [LICENSE-OFL.txt](../LICENSE-OFL.txt) and [OFL-1.1.txt](../OFL-1.1.txt).

## Build

With Python 3.11 or newer, run from the repository root:

```sh
python -m pip install -r requirements.txt
python tools/sync_components.py --check
python tools/build_normalized_fonts.py --svg-dir svg --output build
```

This creates `Light.ttf`, `Regular.ttf`, `Medium.ttf`, `SemiBold.ttf`, `Bold.ttf`, `Variable.ttf`, Regular/variable WOFFs, variable webfont subsets and a build manifest. Add `--woff2` for a Regular WOFF2. The [Build font from SVG workflow](https://github.com/iebb/sealie/actions/workflows/build-font.yml) runs the same builder and uploads artifacts; it does not automatically publish a release.

The compact stroker uses pinned `skia-pathops` round caps and joins without simplifying the source polylines or applying Boolean union. It checks contour endpoints and on/off flags across all five masters. If compact topology changes with weight, all masters of that glyph use the original disk/rectangle stroker.

Chunks contain at most 64 glyphs, with up to four workers by default; `--workers 2` lowers concurrency. Exact-input caches live under `build/.build-cache`. Finished chunks are merged as serialized glyph and variation data. Source hashes, coverage, bounds, compatible masters, metrics and serialized preservation are checked; no global variable-font instancing is needed. Final serialization and optional WOFF2 compression still require memory proportional to font size.

## Edit glyphs or shared radicals

Preserve the SVG wrapper: `viewBox="0 0 1024 1024"`, the baseline-832 group transform, codepoint, advance and round-stroke attributes. Paths accept explicit absolute `M`, `L` and terminal `Z`, with one path per stroke. Current coordinates retain six decimal places; preserve that precision when editing. Arbitrary transforms, filled shapes and other commands are rejected. Convert curves to sufficiently fine polylines before building.

After an intentional individual edit:

```sh
python tools/svg_font.py --svg-dir svg --refresh-manifest
python tools/sync_components.py --check
python tools/build_normalized_fonts.py --svg-dir svg --output build
```

Refreshing hashes records changed bytes, not visual approval. The build reads only the unique codepoints listed in `svg/manifest.json`; missing or stale files fail. Historical `authoring_source_sha256` and `authoring_geometry_sha256` fields preserve lineage, while `svg_sha256` binds the current source.

For an assigned radical, edit its canonical SVG in `components/`, then run:

```sh
python tools/sync_components.py --apply
python tools/sync_components.py --check
python tools/build_normalized_fonts.py --svg-dir svg --output build
```

Templates include exact placement. Preserve path count and closures; the updater changes only assigned paths, preserves unrelated paths and IDs, and refreshes hashes. It rejects overlapping assignments, missing paths, incompatible closures, unsupported constructs and stale glyph hashes. Different positions and allographs remain separate templates.

The current optical profiles share a vertical band for ordinary forms, with shorter sparse forms and naturally varying widths. Rebuilding compiles those maintained coordinates. See [normalization policy](NORMALIZATION.md) and [optical sizing](../reports/optical-sizing.json). The [radical expansion](../reports/radical-expansion-v4.json) and [cap refinement](../reports/cap-refinement.json) reports retain their v1.0 source scope.

## Validation and endpoint cleanup

For development changes, the fixture suite can be run with:

```sh
python -m unittest discover -s tests
python tools/cleanup_caps.py --check
```

All **11 existing fixture tests were rerun for v1.1.0**, after updating the font version metadata. Current source, contact, shared-component and compiled-output checks have their own revision-bound reports.

The tests cover mixed SVG fixtures, static/variable output, named weights, default-master geometry, webfont coverage, stale source rejection, topology fallback and component propagation. They require compatible masters, exact Regular coordinates, at most one font unit of named-instance coordinate/sidebearing error and unchanged 1024-unit advances. The legacy `tools/svg_font.py` Regular builder and its optional `SEAL_PRODUCTION_REGULAR` comparison remain historical tools, not exact-byte checks for the current compact font.

The default endpoint cleaner removes only consecutive terminal vertices within 0.25 units of a fixed endpoint, preserving meaningful hooks, interior vertices and closures. Larger visible defects require focused source corrections and visual review. Shared corrections must be propagated through their templates. The optional exact-loop closure migration is separate and is not implied by the default cleanup.

## Stable downloads and browser preview

The [stable release](https://github.com/iebb/sealie/releases/latest) provides individual assets, including [Sealie-Variable.ttf](https://github.com/iebb/sealie/releases/latest/download/Sealie-Variable.ttf), [Sealie-Regular.ttf](https://github.com/iebb/sealie/releases/latest/download/Sealie-Regular.ttf), the other named weights, Regular/variable WOFFs, licenses and [font-hashes.json](https://github.com/iebb/sealie/releases/latest/download/font-hashes.json). No archive assembly is required. See [font downloads](../fonts/README.md).

The [live specimen](https://iebb.github.io/sealie/) loads `fonts/variable.css` and the needed variable WOFF subsets, each containing at most 64 glyphs. The Pages builder versions copied font URLs from their actual bytes so new deployments load the new font revision. Current compiled outputs are bound by the [build](../reports/normalized-font-build.json) and [validation](../reports/normalized-font-validation.json) reports.

The [character library](https://iebb.github.io/sealie/characters.html) lists the complete repertoire, with searchable modern equivalents and coverage measured from the actual webfont cmaps. After replacing the published webfonts and refreshing `fonts/variable/manifest.json`, run `python site/update_coverage.py` to refresh `site/coverage.json`. This local measurement uses the existing fontTools dependency; the Pages build itself uses only Python's standard library and verifies that the coverage inventory matches the deployed font files.

`png/` retains 45 square Regular grid sheets. Individual 16×16 glyph PNGs are not tracked. Optional local bitmap exports belong under the ignored `build/` directory and are previews, not font sources.

## Historical authoring imports

The optional JSON importer recreates the original authoring export and its earlier proportional fitting. It does not include current SVG sizing, radical sharing or later repairs. Keep historical investigations in a separate output directory:

```sh
python tools/export_centerlines.py \
  --source-root /path/to/design/strokes-individual \
  --registry /path/to/design/quality/accepted-geometry.json \
  --output build/historical-svg
```

Only accepted-hash registry geometry is exported; manual overrides take precedence over `auto/`. Unlisted files do not enter a build. Earlier sources remain available at the [initial checkpoint](https://github.com/iebb/sealie/tree/checkpoint-011328) and [radical/join source revision](https://github.com/iebb/sealie/tree/radical-joins-011328).
