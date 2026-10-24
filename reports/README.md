# Report scope

Current **v1.0.0** reports:

| Report | Scope |
| --- | --- |
| [coverage.json](coverage.json) | All 11,328 codepoints and current source/review identities |
| [optical-sizing.json](optical-sizing.json) | 10,387 compounds with a 640×768 target; 941 proportionally smaller simple/root forms with a 550×650 maximum target; contact-limited exceptions |
| [radical-expansion-v4.json](radical-expansion-v4.json) | 290 added assignments; current 180 templates and 3,763 registered glyphs |
| [cap-refinement.json](cap-refinement.json) | Three shared parent-curve repairs propagated to 46 glyphs, plus U+3E680's terminal repair |
| [normalized-font-build.json](normalized-font-build.json) | Current compiled fonts, axis, fallback glyphs and checksums |
| [normalized-font-validation.json](normalized-font-validation.json) | Current compiled validation and the distinction between newly executed checks and reused evidence |

The size report identifies 10,384 compounds at the exact target, three contact-limited compounds and 18 simple forms whose reduction is contact-limited. Those simple exceptions may exceed the nominal small-form target. Source path contact checks cover Regular 30-unit strokes; they do not establish exhaustive optical approval of every weight.

The unchanged builder's prior **11-test fixture result is reused**, not claimed as eleven new runs. Current source and font identities remain separately bound to the current reports.

## Historical evidence

[normalization.json](normalization.json) and [normalization-review.json](normalization-review.json) describe the first normalized revision, including its full-raster metrics and component review. They do not measure the current optical size classes. [supplementary-size-fit.json](supplementary-size-fit.json), [size-fit-contact-check.json](size-fit-contact-check.json), [cap-cleanup.json](cap-cleanup.json), [radical-expansion.json](radical-expansion.json) and [join-refinement.json](join-refinement.json) retain the identities and scope of their earlier follow-ups.

Other original acceptance and outline-preservation reports also remain historical; changed outlines do not inherit those exact-byte claims. Earlier sources are accessible through Git history: [initial complete checkpoint](https://github.com/iebb/sealie/tree/checkpoint-011328) and [radical/join revision](https://github.com/iebb/sealie/tree/radical-joins-011328).

[Stable font assets](https://github.com/iebb/sealie/releases/latest) · [Live specimen](https://iebb.github.io/sealie/)
