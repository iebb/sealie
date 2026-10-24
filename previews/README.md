# Font previews

The current **v1.0.0** design covers 11,328 characters, with **180 shared templates registered to 3,763 glyphs**. Compounds and simple/root forms use different optical sizes. Comparisons illustrate specific edits; they do not imply one template for every radical or exhaustive visual approval at every weight.

- [optical-size-strip.png](optical-size-strip.png): the 王/玉 area, showing smaller natural whole forms beside larger compounds.
- [optical-size-first16.png](optical-size-first16.png): the first sixteen codepoints, including U+3D000's 550×30 horizontal stroke.
- [optical-size-representatives.png](optical-size-representatives.png): representative compounds and optically smaller simple/root forms.
- [cap-refinement.png](cap-refinement.png): focused parent-curve and cap corrections, including the U+3E680 terminal repair.
- [Live variable specimen](https://iebb.github.io/sealie/): editable text, 300–700 weight control and character lookup.
- [weight-slider.html](weight-slider.html): local interactive weight preview.
- [glyphs.png](glyphs.png): repertoire sample; complete square sheets are in [png/](../png/).

The [size report](../reports/optical-sizing.json) records target sizes and contact-limited exceptions. [Radical expansion](../reports/radical-expansion-v4.json) records 290 additional shared assignments; [cap refinement](../reports/cap-refinement.json) records the bounded source repairs.

## Historical comparisons

The initial [source comparison](normalization-before-after.png), [radical consistency](radical-consistency.png), [metrics](normalization-metrics.png) and [stress cases](normalization-stress.png) retain their original source and measurement scope. The later [size-fit sheets](residual-size-fit-1.png), [second size-fit sheet](residual-size-fit-2.png), [cap repair](cap-repair.png), [micro-knots](cap-microknots.png), [U+3D7B7 joins](join-refinement.png) and [shared joins](shared-join-refinement.png) document earlier repairs. They are not current optical-sizing proofs.

See [normalization notes](../docs/NORMALIZATION.md), the [source manifest](../svg/manifest.json) and [stable font assets](https://github.com/iebb/sealie/releases/latest).

## 中文

当前 **v1.0.0** 覆盖 11,328 个字，**180 个共享模板登记用于 3,763 个字形**。复合字与简单独体字采用不同的视觉尺寸；独体字和独立部首保持自然比例，不会为了填满方框而放大。笔画接触限制导致的尺寸例外在[尺寸报告](../reports/optical-sizing.json)中明确记录。

- [部首附近对比](optical-size-strip.png)：王、玉一带较小的自然独体形式及较大的复合字。
- [前十六码位](optical-size-first16.png)：包含最终为 550×30 单位横画的 U+3D000。
- [代表性字形](optical-size-representatives.png)：复合字与简单字的不同视觉尺度。
- [笔端修整](cap-refinement.png)：局部主笔画和笔端修正，包括 U+3E680。
- [在线可变字体展示](https://iebb.github.io/sealie/)：文本输入、300–700 字重调整和码位查询。

较早的规范化、尺寸、笔端和连接处对比图保留各自历史范围，并不代表当前全部字形或所有字重的视觉验收。
