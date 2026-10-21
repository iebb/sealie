# Sealie

Built outputs for the Panorama Gothic Small Seal font for Unicode 18.

Current checkpoint: **1,770 of 11,328 glyphs reviewed at Regular 400**. Work continues across the full Small Seal block, U+3D000–U+3FC3F, in batches of 64.

- [Font ZIP part 1 of 2](fonts/Sealie-SmallSeal-001770.zip.001)
- [Font ZIP part 2 of 2](fonts/Sealie-SmallSeal-001770.zip.002)
- [Variable WOFF](fonts/PanoramaGothicSealIndividualVariable.woff)
- [Regular WOFF](fonts/PanoramaGothicSealIndividual-Regular.woff)
- [Weight preview](previews/weight-slider.html)
- [Coverage and validation](reports/coverage.json)

Download every ZIP part into one folder. 7-Zip can open the first part when all parts are present. On macOS/Linux, join and extract them:

```sh
cat Sealie-SmallSeal-001770.zip.* > Sealie-SmallSeal-001770.zip
unzip Sealie-SmallSeal-001770.zip
```

The ZIP includes the variable TTF, direct Regular, five named-weight TTFs, WOFF files and licenses. WOFF files stay in [fonts](fonts/) for local browser previews. The glyphs use a shared rounded monoline construction with proportional sizing and a 1024-unit advance. The original 128 outlines and metrics remain unchanged. All five named weights pass compiled size checks; their optical review continues. This is an incomplete development font.

Latest additions in this checkpoint:

![Latest glyph additions](previews/glyphs.png)

This repository contains built font files, previews, licenses, and output reports. Drawing sources, drafts, and build tooling stay in the working repository. Paths inside diagnostic reports identify that build workspace.

Fonts are distributed under the [SIL Open Font License](OFL-1.1.txt).
