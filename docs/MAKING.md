# How Sealie is made

## Models and drawing process

Codex coordinated the work, wrote generation instructions and build tools, made vector repairs, and ran reviews. Parallel agents worked in **64-codepoint assignments**, with independent review before geometry was accepted. OpenAI image generation (`image_gen.imagegen`) produced the native character drawings. Python tracing and fontTools then turned the reviewed drawings into font geometry.

The process was:

1. **Read the references.** Character structures were compared with the THX, CCZ, QJZ and DYC specimens available in the official Unicode charts. When specimens differed, the drawing followed a coherent attested form.
2. **Create and review each drawing.** Generated drawings were checked for the correct branches, detached strokes, counters and proportions. Failed drawings and later vector corrections were recorded separately.
3. **Construct centerlines.** Automatic tracking followed the skeleton of the generated drawing and fitted editable centerlines. Reviewed vector overrides corrected structural or tracing defects. Reference-font outlines were not extracted to construct the font.
4. **Apply one shared style.** Drawings were initially proportionally fitted within a 1024-unit em, with a 1024-unit advance and a maximum centerline extent of 738 units. Later editing standardizes character proportions and maintains shared radical slots. Regular uses a 30-unit pen with round caps and joins. The variable weights share the same centerlines and change the pen width.
5. **Review the actual font.** Independent agent reviews compared the compiled Regular glyphs with the references. Coverage, bounds, spacing and serialized glyph data were checked, and accepted geometry was bound to hashes. Unchanged work reused prior checks when its recorded geometry and font data matched.

These are AI-assisted designs with recorded review, with a documented review scope. The source path order does not establish historical writing order. Building or using the published font requires no AI service or model key.

## Editable source

The maintained glyph drawings are in [svg/](../svg/), with reusable radical drawings in [components/](../components/). Fonts are built from these centerlines by the repository’s round-stroke font builder. See the [SVG build and editing guide](BUILD-FROM-SVG.md).

## Specimen artwork

The marketing artwork uses “道可道，非常道” from the first chapter of the *Dao De Jing*, with project glyphs from the earlier checkpoint at weights 300, 400, 500, 600 and 700 in shades of gray. Image generation added the paper and ink finish to a rendered font specimen. The [exact-font SVG reference](../marketing/sealie-dao-reference.svg) and [artwork provenance](../marketing/provenance.json) are included.
