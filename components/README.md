# Shared Small Seal components

[manifest.json](manifest.json) assigns **173 SVG templates to 3,473 glyphs**. A template includes its exact geometry and placement. The same radical, position and reviewed structural form therefore appears identically in every registered glyph.

The radical and join revision adds 309 occurrences of existing templates and 318 occurrences using 11 new templates. Ordinary forms are consolidated within the same position and layout band; connected and detached 虫 forms remain separate. Three shared templates also receive bounded parent-curve smoothing at plain stem joins, synchronized to all registered copies.

Edit a template, then run from the repository root:

```sh
python tools/sync_components.py --apply
python tools/sync_components.py --check
python tools/build_normalized_fonts.py --svg-dir svg --output build
```

Preserve the template's `1024×1024` viewBox, font-coordinate transform, 30-unit round pen, path count and path closures. The updater preserves unrelated glyph paths and refreshes current source hashes. The zero-based indices in the manifest refer to the glyph SVG's path list; they do not describe historical stroke order.

The [radical expansion report](../reports/radical-expansion.json) records the new assignments; the [join refinement report](../reports/join-refinement.json) records the shared curve repairs.

Different positions and structural variants have separate templates. Unassigned or ambiguous forms keep their individual SVG geometry. See [normalization policy and comparisons](../docs/NORMALIZATION.md).

## 中文

本目录包含 **173 个共享 SVG 部件模板，登记用于 3,473 个字形**。同一部件、位置和经过审查的结构形式，具有完全相同的形状、尺寸与位置。本次新增 309 个已有模板实例，以及采用 11 个新模板的 318 个实例。常见形式仅在相同位置和布局分区内合并；虫部件的相接与分离形式仍分别维护。另有三个共享模板的普通笔画连接处经过局部主笔画曲线平滑，并同步到所有登记字形。修改模板后，运行上面的同步、检查和构建命令即可更新所有登记字形。

请保留模板的方框、坐标变换、30 单位圆头笔画、路径数量及闭合状态。不同位置和结构异体分别维护；没有可靠对应关系的字形仍保留独立 SVG。清单中的路径索引从零开始，并不代表历史笔顺。
