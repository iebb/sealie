# Sealie font downloads

Download individual files from the [latest release](https://github.com/iebb/sealie/releases/latest). Every font, hash manifest and license is attached directly under **Assets**.

## Desktop fonts

The variable font covers the entire 300–700 weight range. Install it in applications with variable-font support, or choose a static weight.

| Font | Download |
| --- | --- |
| Variable 300–700 | [Sealie-Variable.ttf](https://github.com/iebb/sealie/releases/latest/download/Sealie-Variable.ttf) |
| Light 300 | [Sealie-Light.ttf](https://github.com/iebb/sealie/releases/latest/download/Sealie-Light.ttf) |
| Regular 400 | [Sealie-Regular.ttf](https://github.com/iebb/sealie/releases/latest/download/Sealie-Regular.ttf) |
| Medium 500 | [Sealie-Medium.ttf](https://github.com/iebb/sealie/releases/latest/download/Sealie-Medium.ttf) |
| SemiBold 600 | [Sealie-SemiBold.ttf](https://github.com/iebb/sealie/releases/latest/download/Sealie-SemiBold.ttf) |
| Bold 700 | [Sealie-Bold.ttf](https://github.com/iebb/sealie/releases/latest/download/Sealie-Bold.ttf) |

The installed family name is **Sealie**. All fonts cover 11,328 Unicode 18 Small Seal characters, U+3D000–U+3FC3F. Ordinary CJK codepoints do not automatically select these forms; use the [character library](https://iebb.github.io/sealie/characters.html) to browse coverage, look up forms and copy Small Seal characters.

## Webfonts

- [Full variable WOFF](https://github.com/iebb/sealie/releases/latest/download/Sealie-Variable.woff)
- [Full Regular WOFF](https://github.com/iebb/sealie/releases/latest/download/Sealie-Regular.woff)
- [variable.css](variable.css) and [177 WOFF subsets](variable/), for loading only the characters used on a page
- [Interactive variable-font specimen](https://iebb.github.io/sealie/)
- [Complete character library and coverage](https://iebb.github.io/sealie/characters.html)

Keep `variable/` beside `variable.css` when hosting the subsets. The stylesheet defines the CSS font-family name `Seal`; its weight range is 300–700.

## Hashes, sources and license

The release includes [font-hashes.json](https://github.com/iebb/sealie/releases/latest/download/font-hashes.json), [LICENSE-OFL.txt](https://github.com/iebb/sealie/releases/latest/download/LICENSE-OFL.txt) and [OFL-1.1.txt](https://github.com/iebb/sealie/releases/latest/download/OFL-1.1.txt). Fonts, SVG sources and font software use SIL OFL 1.1.

Editable [SVG glyphs](../svg/) and [shared components](../components/) are maintained in the repository. See the [build guide](../docs/BUILD-FROM-SVG.md), [current font hashes](../reports/normalized-font-build.json) and [validation report](../reports/normalized-font-validation.json).

## 中文

请从[最新发布页面](https://github.com/iebb/sealie/releases/latest)的 **Assets** 中直接下载字体文件、哈希清单及许可证。

支持可变字体的应用建议安装 `Sealie-Variable.ttf`，可连续调整 300–700 字重；也可选择 Light、Regular、Medium、SemiBold、Bold 五个静态字重。字体家族名称为 **Sealie**，覆盖全部 11,328 个 Unicode 18 小篆字符。

网页可使用完整 WOFF，或通过 `variable.css` 按需加载子集；托管时保持样式表和 `variable/` 目录的相对位置。普通汉字不会自动转换为小篆码位，可使用[字符总览](https://iebb.github.io/sealie/characters.html)浏览覆盖率、检索字形并复制。
