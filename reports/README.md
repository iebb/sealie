# Report scope

Current **v1.2.0** evidence:

| Report | Scope |
| --- | --- |
| [coverage.json](coverage.json) | The 11,328-codepoint repertoire and current source/review identities |
| [geometric-simplification.json](geometric-simplification.json) | Bounded curve cleanup, coordinated axis alignment, retained sensitive paths, exact shared copies and the deliberate 道 redraw |
| [geometry-review.json](geometry-review.json) | Selected visual review, with the reviewed source or compiled-font identities and its exact scope |
| [normalized-font-build.json](normalized-font-build.json) | Current compiled fonts, axis, fallback glyphs and checksums |
| [normalized-font-validation.json](normalized-font-validation.json) | Current compiled validation, executed checks and any exact-byte evidence reused |

General curve cleanup has a 2.55-unit displacement budget, measured with a densified discrete Hausdorff comparison. Long near-axis traces have a separate 6-unit straightening budget; fitted curves are flattened to editable polylines at 0.4-unit tolerance. 道 (U+3D55D) has a deliberate geometric redraw, recorded separately from those bounded edits. Path counts, path order and closure flags are retained.

Complete distinct-path contacts are compared at the five pen widths 23.5, 30, 36.5, 43 and 49.5 units, checking both new and lost contacts. Previously open counters in valid explicitly closed source rings are compared at each named weight. The source report records retained paths and the limits of those checks. These are separate from compiled outline validation and sampled visual review.

The [character library](https://iebb.github.io/sealie/characters.html) displays coverage measured from all shipped variable WOFF cmaps. Its [data inventory](../site/coverage.json) is bound to the webfont manifest and actual font hashes. It reports encoded character support, independently of the modern-character mappings.

## Optical design evidence from v1.1

[optical-sizing.json](optical-sizing.json) records the common body heights, varying widths, shared-template profiles and contact-safe width exceptions established in v1.1. [optical-review.json](optical-review.json) records its independent review of 143 selected source glyphs. [optical-counter-check.json](optical-counter-check.json) records that revision's explicitly closed-ring counters at Regular. These reports retain their original source identities and do not measure the later geometric outlines.

[reference-dimensions.json](reference-dimensions.json) contains numeric raster bounds for 257 reference characters, with source URLs and measurement limits. Of 292 requested previews, 35 without ink were excluded. The previews were rendered at 32 points on 56-pixel canvases; bounding-box uncertainty is approximately ±1 pixel. These are selected raster samples, not vendor font metrics or a measurement of the complete reference font. Reference fonts, raster images and outlines are not redistributed.

The geometric design carries forward those optical frames. Ordinary upright forms use a 768-unit body-height target; known sparse forms have smaller optical heights, and dense forms can retain extra width. The [design notes](../docs/NORMALIZATION.md) explain how those frames and the current geometric edits relate.

## Earlier evidence

[radical-expansion-v4.json](radical-expansion-v4.json) records the v1.0 addition of 290 shared assignments, yielding 180 templates and 3,763 registered glyphs. [cap-refinement.json](cap-refinement.json) records three shared parent-curve repairs propagated to 46 glyphs and U+3E680's terminal repair. Both retain their original source identities.

[normalization.json](normalization.json) and [normalization-review.json](normalization-review.json) describe the first normalized revision. [supplementary-size-fit.json](supplementary-size-fit.json), [size-fit-contact-check.json](size-fit-contact-check.json), [cap-cleanup.json](cap-cleanup.json), [radical-expansion.json](radical-expansion.json) and [join-refinement.json](join-refinement.json) retain the scope of their earlier follow-ups.

Changed outlines do not inherit exact-byte approval from earlier geometry. Historical sources remain available in Git: [initial complete checkpoint](https://github.com/iebb/sealie/tree/checkpoint-011328), [v1.0.0](https://github.com/iebb/sealie/tree/v1.0.0) and [v1.1.0](https://github.com/iebb/sealie/tree/v1.1.0).

[Stable font assets](https://github.com/iebb/sealie/releases/latest) · [Live specimen](https://iebb.github.io/sealie/) · [Character library](https://iebb.github.io/sealie/characters.html)
