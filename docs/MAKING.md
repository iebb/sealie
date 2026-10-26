# How Sealie is made

## Models and drawing process

Codex coordinated the work, wrote generation instructions and build tools, made vector repairs, and ran reviews. Parallel agents worked in **64-codepoint assignments**, with independent review before geometry was accepted. OpenAI image generation (`image_gen.imagegen`) produced the native character drawings. Python tracing and fontTools then turned the reviewed drawings into font geometry.

The process was:

1. **Read the references.** Character structures were compared with the THX, CCZ, QJZ and DYC specimens available in the official Unicode charts. When specimens differed, the drawing followed a coherent attested form.
2. **Create and review each drawing.** Generated drawings were checked for the correct branches, detached strokes, counters and proportions. Failed drawings and later vector corrections were recorded separately.
3. **Construct centerlines.** Automatic tracking followed the skeleton of the generated drawing and fitted editable centerlines. Reviewed vector overrides corrected structural or tracing defects. Reference-font outlines were not extracted to construct the font.
4. **Apply one shared style.** Drawings were initially proportionally fitted within a 1024-unit em, with a 1024-unit advance and a maximum centerline extent of 738 units. Optical editing establishes common body heights, naturally different widths and exact shared radical slots. Geometric editing smooths tracing wobble and straightens nearly horizontal or vertical strokes while retaining the encoded structures. Regular uses a 30-unit pen with round caps and joins. The variable weights share the same centerlines and change the pen width.
5. **Review the actual font.** Independent agent reviews compared the compiled Regular glyphs with the references. Coverage, bounds, spacing and serialized glyph data were checked, and accepted geometry was bound to hashes. Unchanged work reused prior checks when its recorded geometry and font data matched.

Sealie is an AI-assisted design with recorded review and an explicit review scope. The source path order does not establish historical writing order. Building or using the published font requires no AI service or model key.

## Editable source

The maintained glyph drawings are in [svg/](../svg/), with reusable radical drawings in [components/](../components/). Fonts are built from these centerlines by the repository’s round-stroke font builder. See the [SVG build and editing guide](BUILD-FROM-SVG.md).

## Geometric drawing

The v1.2 design uses simpler centerlines while retaining the Small Seal stroke structures and the optical frames established in v1.1. Curve fitting removes small tracing irregularities; coordinated axis alignment turns long, nearly straight traces into clean stems and bars. Coincident junctions move together, and sensitive paths retain their earlier geometry when a proposed change would alter a join or close a gap. Shared templates are edited once and propagated identically to their registered copies.

The general curve-cleanup budget is 2.55 font units, measured with a densified discrete Hausdorff comparison. Long near-axis traces have a separate 6-unit straightening budget. Fitted curves are flattened to editable `M`/`L` paths at 0.4-unit tolerance. These limits describe bounded source editing, not an analytic proof of continuous curve distance.

道 (U+3D55D) also has a deliberate geometric redraw: straight sides, a rounded eye, a symmetric internal Y and matching repeated curves. Its 15 open source paths and 490×768-unit Regular ink frame are retained. This specific redesign is separate from the bounded general cleanup. The [geometry study](../previews/geometric-simplification.png), [source report](../reports/geometric-simplification.json) and [review record](../reports/geometry-review.json) distinguish their scopes.

## Optical proportion reference

方正小篆体 (FZXiaoZhuanTi-S13T) provides a reference for Sealie's body heights and varying widths. The typeface is identified by its [official description](https://www.foundertype.com/index.php/FontInfo/ductdetail/id/165.html) and [distributor listing](https://lets.fontworks.co.jp/fonts/492). Dimensions were measured from a [public raster preview](https://www.fonts.net.cn/font-31681245180.html): 257 of 292 requested characters contained ink, with 35 blank previews excluded.

These 32-point previews use 56-pixel canvases, so the measured bounds have approximately ±1 pixel uncertainty. They provide proportion samples rather than vendor font metrics or full-repertoire measurements. Only the numeric bounds and source URLs are included in the [reference report](../reports/reference-dimensions.json); reference fonts, raster images and outlines are not redistributed. This evidence retains its v1.1 source scope. The maintained Sealie drawings remain the source, and the [design notes](NORMALIZATION.md) explain how the optical frames carry into the geometric design.

## Specimen artwork

The marketing artwork uses “道可道，非常道” from the first chapter of the *Dao De Jing*, with project glyphs from the earlier checkpoint at weights 300, 400, 500, 600 and 700 in shades of gray. Image generation added the paper and ink finish to a rendered font specimen. The [exact-font SVG reference](../marketing/sealie-dao-reference.svg) and [artwork provenance](../marketing/provenance.json) are included.
