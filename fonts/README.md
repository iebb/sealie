# Sealie fonts — radical and join revision

Download all four parts of the complete static and variable TTF package from the [radical and join prerelease](https://github.com/iebb/sealie/releases/tag/radical-joins-011328): [001](https://github.com/iebb/sealie/raw/radical-joins-011328/fonts/Sealie-Radical-Joins-011328.zip.001) · [002](https://github.com/iebb/sealie/raw/radical-joins-011328/fonts/Sealie-Radical-Joins-011328.zip.002) · [003](https://github.com/iebb/sealie/raw/radical-joins-011328/fonts/Sealie-Radical-Joins-011328.zip.003) · [004](https://github.com/iebb/sealie/raw/radical-joins-011328/fonts/Sealie-Radical-Joins-011328.zip.004).

Put every part in one folder. 7-Zip can open the first part, or join them with `cat Sealie-Radical-Joins-011328.zip.* > Sealie-Radical-Joins-011328.zip` and unzip the result.

This revision adds 627 registered shared-radical glyphs and refines local parent-curve waves in U+3D7B7 and three shared templates. The sources now register 3,473 glyphs against 173 templates.

The family is **Sealie**, covering all 11,328 Small Seal codepoints. The ZIP contains Light 300, Regular 400, Medium 500, SemiBold 600, Bold 700, a 300–700 variable TTF, full Regular/variable WOFFs, hashes and licenses.

Files kept here for browser use:

- [Sealie-Regular.woff](Sealie-Regular.woff)
- [variable.css](variable.css), using the CSS family `Seal`
- [variable/](variable/), with 177 subsets of at most 64 glyphs

The SVG and component manifests bind this revision's sources. Current outputs and checks are recorded in [normalized-font-build.json](../reports/normalized-font-build.json) and [normalized-font-validation.json](../reports/normalized-font-validation.json). The [radical expansion](../reports/radical-expansion.json) and [join refinement](../reports/join-refinement.json) reports record this pass; [normalization.json](../reports/normalization.json) retains the first normalization's measurements.

The [earlier checkpoint](https://github.com/iebb/sealie/releases/tag/checkpoint-011328) preserves the previous font binaries and archive. The new four-part package is tracked in this repository and linked from the radical and join release.

## 中文

完整静态字体和可变字体请从[偏旁与连接处修整版本发布页面](https://github.com/iebb/sealie/releases/tag/radical-joins-011328)下载全部四个 ZIP 分卷，放入同一目录后打开或合并解压。字体家族名称为 **Sealie**，覆盖全部 11,328 个小篆码位，提供 300、400、500、600、700 五个字重及 300–700 可变字体。

本次新增 627 个共享偏旁登记字形，并修整 U+3D7B7 及三个共享模板中连接处的局部主笔画曲线起伏。现有 3,473 个字形登记使用 173 个共享模板。

本目录保留 Regular WOFF 及按需加载的 177 个可变网页字体子集。SVG 和共享部件是维护中的源文件；旧字体及旧分卷仍保留在先前的检查点版本中。
