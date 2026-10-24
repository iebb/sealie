# Shared Small Seal components

[manifest.json](manifest.json) assigns **180 SVG templates to 3,763 glyphs**. Each template includes the exact geometry, size and placement of one reviewed radical form. Every registered occurrence uses that same drawing and slot; different positions and structural allographs remain separate.

The v1.0.0 revision adds **290 assignments**: 219 extensions of existing templates, eight additional 雨 occurrences, and 63 glyphs using seven new 子、鳥、巾 templates. Three shared parent-curve repairs propagate to 46 glyphs; a separate terminal correction affects U+3E680. See [radical expansion](../reports/radical-expansion-v4.json) and [cap refinement](../reports/cap-refinement.json).

Optical sizing transforms each shared template once and preserves identical copies while fitting the remaining strokes around it. Compounds and simple whole forms use different size targets; contact-limited cases are retained explicitly. See the [normalization policy](../docs/NORMALIZATION.md) and [optical-sizing report](../reports/optical-sizing.json).

Edit a template, then run from the repository root:

```sh
python tools/sync_components.py --apply
python tools/sync_components.py --check
python tools/build_normalized_fonts.py --svg-dir svg --output build
```

Preserve its `1024×1024` viewBox, font-coordinate transform, 30-unit round pen, path count and closure flags. The updater changes assigned paths, preserves unrelated paths and refreshes current source hashes. Manifest indices are zero-based positions in a glyph's path list, not historical stroke order. Unassigned and ambiguous forms retain their individual SVG geometry.

[Live font specimen](https://iebb.github.io/sealie/) · [Stable font assets](https://github.com/iebb/sealie/releases/latest)

## 中文

[清单](manifest.json)包含 **180 个共享 SVG 模板，登记用于 3,763 个字形**。同一偏旁、位置及经过审查的结构形式，共用完全一致的形状、尺寸和位置；不同位置和结构异体分别维护。

v1.0.0 新增 **290 个实例**：219 个已有模板扩展、八个雨部件实例，以及使用七个新子、鳥、巾模板的 63 个字形。三个共享模板的主笔画曲线修整同步到 46 个字形；U+3E680 另有一处笔端修正。

视觉尺寸调整只对共享模板本身进行一次变换，再围绕它调整其余笔画，保持所有登记副本一致。复合字与简单独体字采用不同尺寸目标；会导致笔画新接触的调整保留为明确的例外。修改模板后，请运行上述同步、检查和构建命令。

请保留方框、坐标变换、30 单位圆头笔画、路径数量和闭合状态。清单中的路径索引从零开始，并不代表历史笔顺；没有可靠对应关系的形式仍保留独立 SVG。
