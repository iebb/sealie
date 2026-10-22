# Sealie

[English](README.md) · 简体中文

![Sealie《道德经》主题宣传图](marketing/sealie-marketing.png)

Sealie 是由 **ieb** 主导，使用 **OpenAI Codex（GPT-6）**及多个并行子代理协作制作的小篆黑体。字体以统一的圆头等线风格，覆盖 **Unicode 18 小篆区块的全部 11,328 个码位：U+3D000–U+3FC3F**。下载文件中的字体家族名称为 *Panorama Gothic Seal Individual*。

**Regular 400 已完成全字集的视觉审查并留有记录。** 可变字体提供 300–700 字重，其余字重仍需进一步进行视觉调整与审查，因此当前版本仍为预发布版。详见[覆盖报告](reports/coverage.json)。

## 使用的模型与制作过程

Codex 负责协调任务、编写生成指令和构建工具、修正矢量字形，并组织审查。多个子代理按**每批 64 个码位**并行工作，字形几何数据通过独立审查后才被接受。OpenAI 图像生成工具（`image_gen.imagegen`）用于生成原始单字图；随后通过 Python 中心线追踪与 fontTools，将经过审查的字形转换成字体轮廓。

具体流程如下：

1. **查阅字形参考。** 对照 Unicode 官方码表中可用的 THX、CCZ、QJZ、DYC 字形资料，核对字形结构。不同资料存在异体差异时，选择有依据且结构一致的形式。
2. **生成并审查单字图。** 检查分支、分离笔画、字腔及比例。未通过的原始图与后续的矢量修正分别保留记录。
3. **构造笔画中心线。** 自动追踪生成图的骨架，拟合成可编辑的中心线，再通过经过审查的矢量修正处理结构或追踪问题。字体轮廓并非从参考字体中提取。
4. **统一设计参数。** 每个字按比例归一化到 1024 单位的 em 方框中，字宽固定为 1024 单位，中心线最大尺寸为 738 单位。Regular 的笔画宽度为 30 单位，使用圆头和圆角连接。各可变字重共用中心线，通过改变笔宽生成。
5. **检查实际编译结果。** 独立代理将编译后的 Regular 字形与参考资料进行比较，并检查覆盖范围、边界、字宽与序列化字形数据。通过审查的几何数据使用哈希绑定；几何与字体数据一致时，复用已有检查结果。

这是经过记录和审查的 AI 辅助字体设计，并不代表古文字学专家认证。源文件中路径的排列顺序也不代表历史笔顺。构建和使用已发布的字体无需调用 AI 服务，也不需要模型密钥。

## SVG 源文件与构建

**[svg/](svg/) 是本仓库维护的字形源文件目录。** 每个码位对应一个可编辑的 SVG，[清单文件](svg/manifest.json)记录文件名、码位及哈希。SVG 使用 `seal-centerline-1` 格式，保存精确归一化后的笔画中心线。重新构建 Regular 400 不需要私有工作区中的草稿或参考图片。

安装 Python 3.11 或更新版本后，在仓库根目录运行：

```sh
python -m pip install -r requirements.txt
python tools/svg_font.py --svg-dir svg --output build
```

命令生成 `build/Regular.ttf`、`build/Regular.woff2` 及构建清单。[Build font from SVG 工作流](https://github.com/iebb/sealie/actions/workflows/build-font.yml)使用同样的命令，并上传构建产物；可手动运行，也可由 SVG 或工具代码变更触发。此构建器生成 Regular 400，现有可变字体另行包含在下载包中。

SVG 格式限制、清单更新与验证命令见[构建和编辑指南](docs/BUILD-FROM-SVG.md)。

## 下载与预览

- [字体预发布版](https://github.com/iebb/sealie/releases/tag/checkpoint-011328) · [字体文件及全部 13 个 ZIP 分卷](fonts/)
- [Regular WOFF](fonts/PanoramaGothicSealIndividual-Regular.woff)
- [可变网页字体 CSS](fonts/variable.css) · [177 个网页字体子集，每个最多 64 字](fonts/variable/)
- [字重预览](previews/weight-slider.html)
- [覆盖完整字集的 45 张方形 PNG 网格预览](png/)
- [可编辑的 SVG 源文件](svg/)

将 `Sealie-SmallSeal-011328.zip.001` 至 `.013` 全部分卷下载到同一目录。分卷齐全后，可用 7-Zip 打开第一卷。macOS 或 Linux 也可以运行：

```sh
cat Sealie-SmallSeal-011328.zip.* > Sealie-SmallSeal-011328.zip
unzip Sealie-SmallSeal-011328.zip
```

下载包包含可变 TTF、独立 Regular、五个命名字重的 TTF、WOFF 文件及许可证。网页字体 CSS 会按需加载较小的字体子集。小篆使用独立的 Unicode 码位，输入普通汉字不会自动转换成对应的小篆字形。

![已完成的小篆字集样例](previews/glyphs.png)

网格预览每张包含 16×16 个单元格，每格为 128 像素。仓库不再跟踪逐字的 16×16 像素 PNG；字形修改请直接编辑 SVG 源文件。

## 参与贡献

**欢迎贡献和提交代码**，包括字形修正、字距改进、文档完善及构建工具修复。提交字形修正时，请注明码位、说明结构问题，并附上用于判断的参考资料或对比图。

编辑 `svg/Uxxxxx.svg` 时，请保留码位、字宽、分组变换及圆头笔画属性。有意修改源文件后，刷新清单并构建：

```sh
python tools/svg_font.py --svg-dir svg --refresh-manifest
python tools/svg_font.py --svg-dir svg --output build
```

检查渲染后的字形，再提交范围明确的 commit 或 pull request。刷新哈希仅记录新的源文件内容，并不表示该修改已经通过视觉审查。字形源文件应保持为 SVG，请勿提交生成的逐字位图。

## 宣传图与许可证

宣传图使用《道德经》第一章中的“道可道，非常道”，以本项目的真实字形，在 300、400、500、600、700 字重和不同灰度下排版。图像生成工具在字体排版图的基础上添加了纸张与油墨质感。仓库同时提供[使用精确字形的 SVG 参考图](marketing/sealie-dao-reference.svg)及[制作来源记录](marketing/provenance.json)。

字体、SVG 源文件和字体软件采用 **SIL Open Font License 1.1**。详见 [LICENSE-OFL.txt](LICENSE-OFL.txt) 和 [OFL-1.1.txt](OFL-1.1.txt)。
