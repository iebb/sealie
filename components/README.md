# Shared Small Seal components

[manifest.json](manifest.json) assigns **180 SVG templates to 3,763 glyphs**. Each template includes the exact geometry, size and placement of one reviewed radical form. Every registered occurrence uses that same drawing and slot; different positions and structural allographs remain separate.

Optical sizing makes one coherent horizontal profile for a shared-template family, preserving identical registered copies and the ordinary 768-unit body height. Other forms can use shorter reference-informed heights and naturally different widths. Fitting stops before it closes a previously open Regular-weight gap. See the [normalization policy](../docs/NORMALIZATION.md) and [current sizing report](../reports/optical-sizing.json).

Edit a template, then run from the repository root:

```sh
python tools/sync_components.py --apply
python tools/sync_components.py --check
python tools/build_normalized_fonts.py --svg-dir svg --output build
```

Preserve its `1024×1024` viewBox, font-coordinate transform, 30-unit round pen, path count and closure flags. The updater changes assigned paths, preserves unrelated paths and refreshes current source hashes. Manifest indices are zero-based positions in a glyph's path list, not historical stroke order. Unassigned and ambiguous forms retain their individual SVG geometry.

## Source history

The v1.0.0 revision added **290 assignments**: 219 extensions of existing templates, eight additional 雨 occurrences, and 63 glyphs using seven new 子、鳥、巾 templates. Three shared parent-curve repairs propagated to 46 glyphs; a separate terminal correction affected U+3E680. The [radical-expansion report](../reports/radical-expansion-v4.json) and [cap-refinement report](../reports/cap-refinement.json) retain those earlier source identities. Current optical dimensions are recorded separately.

[Live font specimen](https://iebb.github.io/sealie/) · [Stable font assets](https://github.com/iebb/sealie/releases/latest)

## 中文

[清单](manifest.json)包含 **180 个共享 SVG 模板，登记用于 3,763 个字形**。同一偏旁、位置及经过审查的结构形式，共用完全一致的形状、尺寸和位置；不同位置和结构异体分别维护。

视觉尺寸调整为同一共享模板族选择一致的横向变换，保持所有登记副本完全相同，并采用一般字形的 768 单位字身高度。其他字形可依据参考测量采用较矮的高度和自然的宽度差异；若继续压缩会使 Regular 字重下原有的留白闭合，就保留接触安全的尺寸。实际尺寸和例外见[尺寸报告](../reports/optical-sizing.json)。修改模板后，请运行上述同步、检查和构建命令。

请保留方框、坐标变换、30 单位圆头笔画、路径数量和闭合状态。清单中的路径索引从零开始，并不代表历史笔顺；没有可靠对应关系的形式仍保留独立 SVG。

v1.0.0 新增的 290 个共享实例、三个模板曲线修整及 U+3E680 笔端修正，保留在相应历史报告中。这些报告的源文件身份与当前视觉尺寸报告分别记录。
