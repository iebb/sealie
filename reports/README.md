# Report scope

Current **v1.1.0** reports:

| Report | Scope |
| --- | --- |
| [coverage.json](coverage.json) | All 11,328 codepoints and current source/review identities |
| [optical-sizing.json](optical-sizing.json) | Common body heights, naturally varying widths, shared-template family transforms and contact-limited width exceptions |
| [optical-review.json](optical-review.json) | Independent optical review of 143 selected source glyphs, with source identities and exact scope |
| [reference-dimensions.json](reference-dimensions.json) | Numeric raster bounds for 257 reference characters, excluded blank previews, source URLs and measurement limits |
| [optical-counter-check.json](optical-counter-check.json) | Survival of 73 previously open counters in explicitly closed source rings at Regular |
| [normalized-font-build.json](normalized-font-build.json) | Current compiled fonts, axis, fallback glyphs and checksums |
| [normalized-font-validation.json](normalized-font-validation.json) | Current compiled validation, executed checks and any reused evidence |

Ordinary upright forms use a 768-unit body height. Measured short forms use individual optical heights; examples include 王 620, 工 580, 土 680 and 士 640 units. Measured widths follow the reference proportions, with a preferred maximum of 520 units; unmeasured forms retain their own pre-box-fitting proportions. A single horizontal bar uses 470×30 units, while two, three and four bars use width 430 and heights 440, 540 and 640. Contact limits can require explicit exceptions to the preferred dimensions. The [design notes](../docs/NORMALIZATION.md) explain the mapping.

The reference measurements come from public raster previews at 32 points on 56-pixel canvases. Of 292 requested characters, 257 have measurable ink; 35 blank previews are excluded. Bounding-box uncertainty is approximately ±1 pixel. These numbers are not vendor font metrics or measurements of the full repertoire. Reference fonts, raster images and outlines are not included in the repository.

Source path contact checks cover distinct paths at the Regular 30-unit pen width and the half-unit gap threshold. They do not establish same-path overlap safety or exhaustive optical approval of every weight. Current source and compiled-font identities are bound to their respective reports.

## Historical evidence

[radical-expansion-v4.json](radical-expansion-v4.json) records the v1.0.0 addition of 290 shared assignments, yielding 180 templates and 3,763 registered glyphs. [cap-refinement.json](cap-refinement.json) records three shared parent-curve repairs propagated to 46 glyphs and U+3E680's terminal repair. Both retain their original source identities; their measurements do not describe the subsequent optical width and height adjustments.

[normalization.json](normalization.json) and [normalization-review.json](normalization-review.json) describe the first normalized revision, including its full-raster metrics and component review. [supplementary-size-fit.json](supplementary-size-fit.json), [size-fit-contact-check.json](size-fit-contact-check.json), [cap-cleanup.json](cap-cleanup.json), [radical-expansion.json](radical-expansion.json) and [join-refinement.json](join-refinement.json) retain the identities and scope of earlier follow-ups.

Other original acceptance and outline-preservation reports also remain historical; changed outlines do not inherit those exact-byte claims. Earlier sources are accessible through Git history: [initial complete checkpoint](https://github.com/iebb/sealie/tree/checkpoint-011328), [radical/join revision](https://github.com/iebb/sealie/tree/radical-joins-011328) and [v1.0.0 sources](https://github.com/iebb/sealie/tree/v1.0.0).

[Stable font assets](https://github.com/iebb/sealie/releases/latest) · [Live specimen](https://iebb.github.io/sealie/)
