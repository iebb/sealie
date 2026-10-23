# Shared Small Seal components

[manifest.json](manifest.json) assigns **162 SVG templates to 2,846 glyphs**. A template includes its exact geometry and placement. The same radical, position and reviewed structural allograph therefore appears identically in every registered glyph.

Edit a template, then run from the repository root:

```sh
python tools/sync_components.py --apply
python tools/sync_components.py --check
python tools/build_normalized_fonts.py --svg-dir svg --output build
```

Preserve the template's `1024×1024` viewBox, font-coordinate transform, 30-unit round pen, path count and path closures. The updater preserves unrelated glyph paths and refreshes current source hashes. The zero-based indices in the manifest refer to the glyph SVG's path list; they do not describe historical stroke order.

Different positions and structural variants have separate templates. Unassigned or ambiguous forms keep their individual SVG geometry. See [normalization policy and comparisons](../docs/NORMALIZATION.md).

## 中文

本目录包含 **162 个共享 SVG 部件模板，登记用于 2,846 个字形**。同一部件、位置和经过审查的异体形式，具有完全相同的形状、尺寸与位置。修改模板后，运行上面的同步、检查和构建命令即可更新所有登记字形。

请保留模板的方框、坐标变换、30 单位圆头笔画、路径数量及闭合状态。不同位置和结构异体分别维护；没有可靠对应关系的字形仍保留独立 SVG。清单中的路径索引从零开始，并不代表历史笔顺。
