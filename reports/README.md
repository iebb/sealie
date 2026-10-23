# Report scope

Current radical and join revision:

- [coverage.json](coverage.json): current repertoire, source identities and review scope
- [normalization.json](normalization.json): identical-method before/after measurements across all 11,328 glyphs
- [normalization-review.json](normalization-review.json): independent component-group review and final source reconciliation
- [radical-expansion.json](radical-expansion.json): 627 new shared-radical assignments; current 173 templates and 3,473 registered glyphs
- [join-refinement.json](join-refinement.json): focused parent-curve repairs in U+3D7B7 and three synchronized shared templates
- [normalized-font-build.json](normalized-font-build.json): current fonts, axis, fallback glyphs and checksums
- [normalized-font-validation.json](normalized-font-validation.json): current compiled-font validation
- [supplementary-size-fit.json](supplementary-size-fit.json): 26 additional reviewed compound fits; two contact-producing proposals preserved
- [size-fit-contact-check.json](size-fit-contact-check.json): executed Regular-weight centerline contact distances for the 28 proposals
- [cap-cleanup.json](cap-cleanup.json): historical endpoint-cleanup scope and source identities

The full-raster `normalization.json` measurements and component review describe the first normalized revision, as bound by their source hashes. The cap cleanup and supplementary size-fit reports record earlier follow-ups. Radical expansion and join refinement have their own current source identities; the font build and validation reports bind the current compiled outputs.

The other reports in this directory describe the [earlier checkpoint](https://github.com/iebb/sealie/releases/tag/checkpoint-011328), as identified by their original source/font hashes. Their old outline-preservation and acceptance claims do not apply to changed normalized outlines. They remain available as historical evidence.

The normalized font is a prerelease. Full geometric checks and representative optical review do not establish exhaustive optical approval at every weight.
