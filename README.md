# Sealie

English · [简体中文](README.zh-CN.md)

**A rounded Gothic typeface for Small Seal script.**

![Sealie — Small Seal typography inspired by the Dao De Jing](marketing/sealie-marketing.png)

Sealie brings the flowing structures of Small Seal script into a clean, monoline typeface. Rounded stroke ends, even weight and generous spaces give its characters a calm, geometric rhythm. It is designed for display typography: titles, posters, book covers, seal-inspired graphics and character studies.

The family covers **11,328 Small Seal characters** and includes a **300–700 variable font** alongside five static weights. All characters have a fixed advance, making the font suitable for horizontal text, vertical arrangements and square compositions.

**[Try the variable font](https://iebb.github.io/sealie/)** · **[Download fonts](https://github.com/iebb/sealie/releases/latest)** · [Installation guide](fonts/README.md)

## The family

| Weight | Name |
| --- | --- |
| 300 | Light |
| 400 | Regular |
| 500 | Medium |
| 600 | SemiBold |
| 700 | Bold |

The variable font moves continuously between Light and Bold. Each weight follows the same stroke centerlines, retaining the character structure as the strokes become heavier.

![Sealie character specimen](previews/glyphs.png)

Explore the [interactive specimen](https://iebb.github.io/sealie/) to adjust weight, enter text and look up characters. The [complete character sheets](png/) show every supported codepoint in 16×16 grids.

## Character coverage

Sealie covers the **Unicode 18 Small Seal block, U+3D000–U+3FC3F**. The family name in installed fonts is **Sealie**.

Small Seal characters use their own Unicode codepoints. Typing an ordinary Chinese character does not automatically select its Small Seal form in a text editor. Use the showcase's character lookup to find and copy supported characters, or insert Small Seal codepoints directly. The font does not include a general Latin alphabet or the ordinary CJK repertoire.

## Download and use

The [font package](https://github.com/iebb/sealie/releases/latest) contains the variable TTF, five static TTFs, full Regular and variable WOFF files, and licenses. Each font file is attached directly to the release. See the [download and installation instructions](fonts/README.md).

Install `Sealie-Variable.ttf` in applications that support variable fonts, or choose a static TTF for a specific weight. Regular is 400.

For websites, use [fonts/variable.css](fonts/variable.css). It loads small character subsets as needed and defines the CSS family name `Seal`:

```html
<link rel="stylesheet" href="fonts/variable.css">
<p style="font-family: 'Seal', sans-serif; font-weight: 450;">
  &#x3D000; &#x3D001; &#x3D002;
</p>
```

Keep the `fonts/variable/` directory beside the stylesheet when hosting these files.

## Sources and making

Sealie is developed by **ieb**, with **OpenAI Codex (GPT-6)** and parallel agents assisting with drawing, vector work, tooling and review. OpenAI image generation produced the initial drawings; reviewed centerlines and reusable radical components form the editable font source. See [how the font is made](docs/MAKING.md) for the models, reference process and artwork credits.

The [glyph SVGs](svg/) and [shared components](components/) are maintained sources. Building the published font requires no AI service or model key. See the [SVG build guide](docs/BUILD-FROM-SVG.md) and the [GitHub Actions build workflow](https://github.com/iebb/sealie/actions/workflows/build-font.yml).

Sealie is an experimental font under active refinement. Design methods, review scope and source measurements are documented in [the design notes](docs/NORMALIZATION.md) and [reports](reports/README.md).

## Contribute

Glyph corrections, references, spacing improvements and code contributions are welcome. Include the codepoint and a clear comparison when proposing a drawing change. Shared radicals are edited in `components/`; complete glyphs are in `svg/`. The [editing guide](docs/BUILD-FROM-SVG.md) explains how to synchronize sources and rebuild the font.

## License

Fonts, SVG sources and font software are released under the **SIL Open Font License 1.1**, allowing personal and commercial use, redistribution and modification under its terms. See [LICENSE-OFL.txt](LICENSE-OFL.txt) and [OFL-1.1.txt](OFL-1.1.txt).
