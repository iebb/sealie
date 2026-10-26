# Font previews

The current **v1.2.0** design covers 11,328 characters. Simple curves, straight stems and round turns retain the Small Seal structures and optical frames. **180 shared templates are registered to 3,763 glyphs**. The images illustrate their stated samples; they do not imply exhaustive visual approval of every glyph at every weight.

- [geometric-simplification.png](geometric-simplification.png): the construction of 道, showing straight sides, a rounded eye, a symmetric internal Y and matching repeated curves.
- [glyphs.png](glyphs.png): a sample rendered from the current font. Complete square sheets are in [png/](../png/).
- [Live variable specimen](https://iebb.github.io/sealie/): editable text, 300–700 weight control and character lookup.
- [Character library and coverage](https://iebb.github.io/sealie/characters.html): the complete repertoire, search, codepoint ranges, glyph details and copying.

The [geometric source report](../reports/geometric-simplification.json) separates bounded general cleanup from the deliberate 道 redraw. The [geometry review](../reports/geometry-review.json) records the samples and source or compiled-font identities used for visual review. See the [design notes](../docs/NORMALIZATION.md) for the editing budgets, optical frames and guard scope.

## Historical comparisons

The v1.1 [text alignment](optical-alignment.png) and [primitive sizes](optical-primitives.png) show the optical profiles before geometric cleanup. Their source identities are in the [sizing report](../reports/optical-sizing.json) and [optical review](../reports/optical-review.json). The [reference report](../reports/reference-dimensions.json) retains numeric bounds from 257 public raster previews; it contains no copied reference-font artwork.

The v1.0 [王/玉 strip](optical-size-strip.png), [first sixteen codepoints](optical-size-first16.png) and [representative forms](optical-size-representatives.png) show the earlier simple/compound size split. [cap-refinement.png](cap-refinement.png) records that revision's local parent-curve and cap repairs, including U+3E680.

The initial [source comparison](normalization-before-after.png), [radical consistency](radical-consistency.png), [metrics](normalization-metrics.png) and [stress cases](normalization-stress.png) retain their original scope. The later [size-fit sheets](residual-size-fit-1.png), [second size-fit sheet](residual-size-fit-2.png), [cap repair](cap-repair.png), [micro-knots](cap-microknots.png), [U+3D7B7 joins](join-refinement.png) and [shared joins](shared-join-refinement.png) document earlier repairs.

See the [maintained source manifest](../svg/manifest.json), [v1.1 source checkpoint](https://github.com/iebb/sealie/tree/v1.1.0) and [stable font assets](https://github.com/iebb/sealie/releases/latest).

## 中文

当前 **v1.2.0** 覆盖 11,328 个字，以简练曲线、平直字干和圆润转折整理造型，保留小篆结构与既有视觉尺寸。**180 个共享模板登记用于 3,763 个字形**。

- [几何造型](geometric-simplification.png)：道的平直两侧、圆角字腔、对称内部 Y 形和一致重复曲线。
- [当前字体样张](glyphs.png)：完整方格字表位于 [png/](../png/)。
- [在线可变字体展示](https://iebb.github.io/sealie/)：文本输入、300–700 字重调整和码位查询。
- [字符总览与覆盖率](https://iebb.github.io/sealie/characters.html)：全部码位、搜索、字形详情与复制。

[几何报告](../reports/geometric-simplification.json)区分一般受限清理与道的明确重绘；[视觉审查](../reports/geometry-review.json)记录实际样本与相应源文件或字体身份。v1.1 的对齐、基本形式与参考尺寸证据，以及更早的尺寸、笔端和连接处图像，均保留各自历史范围。
