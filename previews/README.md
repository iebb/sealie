# Font previews

The current **v1.1.0** design covers 11,328 characters, with **180 shared templates registered to 3,763 glyphs**. Ordinary upright characters share a body height and retain different widths. Reference measurements guide naturally shorter forms; horizontal bars have their own sizes. Comparisons illustrate their stated samples and do not imply exhaustive visual approval at every weight.

- [optical-alignment.png](optical-alignment.png): representative text, showing the height relationship of 道、可、非、常 and 名.
- [optical-primitives.png](optical-primitives.png): open structures and shallow forms, including 王、工、土、士 and horizontal primitives.
- [Live variable specimen](https://iebb.github.io/sealie/): editable text, 300–700 weight control and character lookup.
- [weight-slider.html](weight-slider.html): local interactive weight preview.
- [glyphs.png](glyphs.png): current repertoire sample; complete square sheets are in [png/](../png/).

The [sizing report](../reports/optical-sizing.json) records actual dimensions and contact-safe exceptions. The [reference report](../reports/reference-dimensions.json) contains numeric bounds from 257 public raster previews, not copied reference-font artwork. See the [design notes](../docs/NORMALIZATION.md) for the mapping and measurement limits.

## Historical comparisons

The v1.0.0 [王/玉 strip](optical-size-strip.png), [first sixteen codepoints](optical-size-first16.png) and [representative forms](optical-size-representatives.png) show the earlier simple/compound size split. [cap-refinement.png](cap-refinement.png) records that revision's local parent-curve and cap repairs, including U+3E680. These images retain their original scope.

The initial [source comparison](normalization-before-after.png), [radical consistency](radical-consistency.png), [metrics](normalization-metrics.png) and [stress cases](normalization-stress.png) also retain their original source and measurement scope. The later [size-fit sheets](residual-size-fit-1.png), [second size-fit sheet](residual-size-fit-2.png), [cap repair](cap-repair.png), [micro-knots](cap-microknots.png), [U+3D7B7 joins](join-refinement.png) and [shared joins](shared-join-refinement.png) document earlier repairs.

See the [source manifest](../svg/manifest.json) and [stable font assets](https://github.com/iebb/sealie/releases/latest).

## 中文

当前 **v1.1.0** 覆盖 11,328 个字，**180 个共享模板登记用于 3,763 个字形**。一般直立字形采用共同的字身高度，保留自然的宽度差异；参考尺寸指导自然较矮的字形，横画形式另有相应尺寸。实际尺寸及接触安全例外记录于[尺寸报告](../reports/optical-sizing.json)。[参考报告](../reports/reference-dimensions.json)仅包含 257 个公开栅格预览的数值度量，不包含参考字体的图像或轮廓。

- [文字高度对齐](optical-alignment.png)：道、可、非、常、名等代表字的高度关系。
- [基本形式](optical-primitives.png)：王、工、土、士等疏朗结构及较浅的横向形式。
- [在线可变字体展示](https://iebb.github.io/sealie/)：文本输入、300–700 字重调整和码位查询。

较早的规范化、尺寸、笔端和连接处对比图保留各自历史范围，并不代表当前全部字形或所有字重的视觉验收。
