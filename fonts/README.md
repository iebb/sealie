# Normalized Sealie fonts

Download all four parts of the complete static and variable TTF package from the [normalized prerelease](https://github.com/iebb/sealie/releases/tag/normalized-caps-011328): [001](https://github.com/iebb/sealie/raw/normalized-caps-011328/fonts/Sealie-Normalized-Caps-011328.zip.001) · [002](https://github.com/iebb/sealie/raw/normalized-caps-011328/fonts/Sealie-Normalized-Caps-011328.zip.002) · [003](https://github.com/iebb/sealie/raw/normalized-caps-011328/fonts/Sealie-Normalized-Caps-011328.zip.003) · [004](https://github.com/iebb/sealie/raw/normalized-caps-011328/fonts/Sealie-Normalized-Caps-011328.zip.004).

Put every part in one folder. 7-Zip can open the first part, or join them with `cat Sealie-Normalized-Caps-011328.zip.* > Sealie-Normalized-Caps-011328.zip` and unzip the result.

The family is **Sealie**, covering all 11,328 Small Seal codepoints. The ZIP contains Light 300, Regular 400, Medium 500, SemiBold 600, Bold 700, a 300–700 variable TTF, full Regular/variable WOFFs, hashes and licenses.

Files kept here for browser use:

- [Sealie-Regular.woff](Sealie-Regular.woff)
- [variable.css](variable.css), using the CSS family `Seal`
- [variable/](variable/), with 177 subsets of at most 64 glyphs

The SVG and component manifests bind this revision's sources. Build and font hashes are recorded in [normalized-font-build.json](../reports/normalized-font-build.json); normalization measurements are in [normalization.json](../reports/normalization.json).

The [earlier checkpoint](https://github.com/iebb/sealie/releases/tag/checkpoint-011328) preserves the previous font binaries and archive. The new four-part package is tracked in this repository and linked from the normalized release.

## 中文

完整静态字体和可变字体请从[规范化版本发布页面](https://github.com/iebb/sealie/releases/tag/normalized-caps-011328)下载全部四个 ZIP 分卷，放入同一目录后打开或合并解压。字体家族名称为 **Sealie**，覆盖全部 11,328 个小篆码位，提供 300、400、500、600、700 五个字重及 300–700 可变字体。

本目录保留 Regular WOFF 及按需加载的 177 个可变网页字体子集。SVG 和共享部件是维护中的源文件；旧字体及旧分卷仍保留在先前的检查点版本中。
