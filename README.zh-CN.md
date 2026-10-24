# Sealie

[English](README.md) · 简体中文

**一款圆头等线风格的小篆黑体。**

![Sealie《道德经》主题小篆排版](marketing/sealie-marketing.png)

Sealie 将小篆流动、舒展的结构融入简洁的等线字体。圆润的笔端、均匀的笔画与疏朗的留白，形成平静而富有几何感的节奏；修长的比例与协调的字身高度，使简单字和复杂字在排版中保持平衡。适用于标题、海报、书籍封面、篆意图形及字形研究等展示性排版。

字体覆盖 **11,328 个小篆字符**，提供 **300–700 可变字重**及五个静态字重。全部字符具有固定的前进宽度，便于横排、竖向排列及方形构图。

**[在线试用可变字体](https://iebb.github.io/sealie/)** · **[下载字体](https://github.com/iebb/sealie/releases/latest)** · [安装说明](fonts/README.md)

## 字体家族

| 字重 | 名称 |
| --- | --- |
| 300 | Light 细体 |
| 400 | Regular 常规 |
| 500 | Medium 中等 |
| 600 | SemiBold 半粗 |
| 700 | Bold 粗体 |

可变字体可在 Light 与 Bold 之间连续调整。各字重共用相同的笔画中心线，使笔画加粗时仍保留一致的字形结构。

![Sealie 字形样张](previews/glyphs.png)

在[交互样张](https://iebb.github.io/sealie/)中调整字重、输入文字并查询字符。[完整字符网格](png/)以每张 16×16 格列出所有支持的码位。

## 字符覆盖

Sealie 覆盖 **Unicode 18 小篆区块 U+3D000–U+3FC3F**。安装后的字体家族名称为 **Sealie**。

小篆字符使用独立的 Unicode 码位。在文字编辑器中输入普通汉字，不会自动选择相应的小篆字形。可以通过在线样张的字符查询功能查找并复制支持的字符，或直接插入小篆码位。本字体不包含完整的拉丁字母或普通 CJK 汉字字集。

## 下载与使用

[字体下载包](https://github.com/iebb/sealie/releases/latest)包含可变 TTF、五个静态 TTF、完整的 Regular 与可变 WOFF，以及许可证。各字体文件直接附在发布页面中，安装方法见[下载与安装说明](fonts/README.md)。

支持可变字体的应用可安装 `Sealie-Variable.ttf`；需要固定字重时，可选择相应的静态 TTF。Regular 对应 400。

网页可使用 [fonts/variable.css](fonts/variable.css)，按需加载较小的字符子集。样式表定义的 CSS 字体名称为 `Seal`：

```html
<link rel="stylesheet" href="fonts/variable.css">
<p style="font-family: 'Seal', sans-serif; font-weight: 450;">
  &#x3D000; &#x3D001; &#x3D002;
</p>
```

自行托管时，请将 `fonts/variable/` 目录与样式表放在对应位置。

## 源文件与制作

Sealie 由 **ieb** 开发，使用 **OpenAI Codex（GPT-6）**与并行代理辅助绘制、矢量修整、工具开发及审查。初始单字图通过 OpenAI 图像生成工具制作，经过审查的笔画中心线与可复用偏旁共同构成可编辑的字体源文件。模型、参考流程及宣传图制作说明见[字体制作过程](docs/MAKING.md)。

[逐字 SVG](svg/)与[共享部件](components/)是持续维护的源文件。构建已发布的字体无需调用 AI 服务，也不需要模型密钥。操作方法见 [SVG 构建指南](docs/BUILD-FROM-SVG.md)及 [GitHub Actions 构建工作流](https://github.com/iebb/sealie/actions/workflows/build-font.yml)。

Sealie 仍是持续完善中的实验字体。设计方法、审查范围及源文件测量记录位于[设计说明](docs/NORMALIZATION.md)与[报告目录](reports/README.md)。

## 参与贡献

欢迎提交字形修正、参考资料、字距改进及代码贡献。提出字形修改时，请注明码位并附上清晰的对比。共享偏旁位于 `components/`，完整字形位于 `svg/`；同步源文件与重新构建的方法见[编辑指南](docs/BUILD-FROM-SVG.md)。

## 许可证

字体、SVG 源文件与字体软件采用 **SIL Open Font License 1.1**，允许依照许可证条款进行个人及商业使用、再分发与修改。详见 [LICENSE-OFL.txt](LICENSE-OFL.txt) 和 [OFL-1.1.txt](OFL-1.1.txt)。
