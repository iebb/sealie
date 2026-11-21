# Composition rules

These are Sealie's own rules for how a character is placed, sized and assembled. They are stated as numbers so that a drawing can be checked against them, and [`tools/check_composition.py`](../tools/check_composition.py) checks every glyph. The values are Sealie's design parameters. They are not taken from another typeface.

Two things are kept apart throughout:

- **Structure** is which strokes exist, where each starts and ends, and what it joins, crosses or stays clear of. Structure comes from the historical sources (rules T1–T4).
- **Composition** is everything else: the frame, the widths, how components share the frame, spacing and stroke style. Composition is decided here (rules F, C, S and R).

All measurements are in font units in a 1024-unit em, y up, baseline 0, at the Regular pen of 30 units. "Ink" means the stroked shape; a centerline lies 15 units inside it.

## Structure: what the sources decide

The Unicode Small Seal block (U+3D000–U+3FC3F) is defined by four editions of the *Shuowen Jiezi*, shown as four specimens per character in the code chart. Unicode's `SealSources.txt` gives each character's serial number in each edition. The encoding proposal ([WG2 N5318R](https://www.unicode.org/wg2/docs/n5318R-Proposal%20to%20encode%20Four-Column%20Small%20Seal%20Script%20in%20UCS.pdf)) describes them:

| Code | Edition | Role |
| --- | --- | --- |
| THX | 藤花榭本, the Tenghuaxie edition (額勒布) of Xu Xuan's text, the 大徐本 | Sets the repertoire and the order; made by following Song printed books |
| CCZ | 陳昌治本, Chen Changzhi's single-line edition, based on the 平津館 edition | Same text family as THX, rearranged for reading |
| QJZ | 小徐本, Xu Kai's 說文繫傳 in the Daoguang-period 祁寯藻 printing | Independent text family |
| DYC | 段注本, Duan Yucai's 說文解字注 | Duan's corrected forms and order |

The THX chart glyphs are not raw scans. The original proposal ([N4688](https://www.unicode.org/L2/L2015/15281-n4688-small-seal.pdf), from TCA and China) pairs each scanned character with a digital font glyph, and [N5189](https://www.unicode.org/wg2/docs/n5189-THX-ModificationPrinciples.pdf) records where the font deliberately departs from the woodblock: taboo forms restored, exact duplicates and broken glyphs repaired, inconsistent components unified, and a few forms replaced from another edition. The working record is public at the [CMEX Shuowen Seal database](https://seal.cmex.org.tw/). The chart fonts are licensed to Unicode by their owners and may not be extracted; Sealie reads the chart for structure only and copies no outline from it.

- **T1. THX decides structure.** Where the specimens agree, Sealie has the same strokes and the same joins. The heavier specimens merge parts by weight alone, so a join seen only in CCZ, QJZ or DYC is not evidence.
- **T2. A drawing is wrong only if it contradicts every specimen**, or all but one that is plainly a different variant. Where the editions differ and Sealie matches one, it stands.
- **T3. Structure outranks composition.** If the correct structure does not fit the frame at this pen, the glyph is re-spaced (rules C and S), not left wrong and not squeezed.
- **T4. Proportion is not structure.** The specimens' widths, heights, stroke modulation and curvature are not copied. Rules F and C set those.

## Frame

- **F1. Em.** Every glyph has a 1024-unit advance. All ink lies inside x 0…1024, y −192…896.
- **F2. Body frame.** An ordinary character's ink runs from **y = 704** to **y = −64**, a height of 768, and is centred on **x = 512**. The body's middle is y = 320. Simple and complex characters share this frame: 可 is as tall as 道. Tolerance is 2 units.
- **F3. Width.** Width is chosen from three classes, always centred on x = 512.

  | Class | Ink width | Use | Glyphs |
  | --- | --- | --- | --- |
  | Standard | 520 (x 252…772) | The default | 6,827 |
  | Narrow | under 520, at the form's natural width | Forms with one main stem or a slender body, such as 木 380 or 弓 320 | 1,696 |
  | Wide | over 520, up to 640 | Only when 520 cannot hold the structure at rule S4's clearance | 2,805 |

  A glyph is never widened for emphasis, and never past 640.
- **F4. Short forms.** A closed list of 51 basic characters is drawn shorter than the body, each at a registered size and centred on y = 320: for example 一 30×470 (height × width), 二 440×430, 三 540×430, 工 580×430, 王 620×430, 日 640×360, 田 640×400, 土 680×430, 月 700×430. The full list is `SHORT_FORMS` in the checker. A character is short only if it is on that list; a short component inside a larger character follows rule C4 instead.

## Composition

A character is one of five layouts. The checker finds side-by-side and stacked layouts by looking for a white channel at least 8 units wide that crosses the whole glyph; the shares below are the current font's measured values and are the targets for new or redrawn glyphs.

- **C1. One body.** 6,313 glyphs have no channel that divides them. The whole form fills the frame of F2 and F3.
- **C2. Side by side** (4,761 glyphs). The left component takes about **41%** of the ink width and the right about **55%** (middle half of the font: 37–46% and 49–58%), with a channel of about **25 units** between them (middle half 18–35). The radical side is the narrower one in four glyphs out of five. Three side-by-side parts divide roughly 34 / 27 / 29%.
- **C3. Stacked** (1,214 glyphs in two parts, 165 in more). In a two-part stack the upper part is usually the smaller: it takes about **31%** of the height (middle half 27–46%), as a crown such as 艸, 宀 or 竹 does, and the two parts are separated by about **26 units**. Each part is centred on x = 512 and normally spans the full ink width.
- **C4. Components fill their slot, not the frame.** In a side-by-side glyph the frame's top and bottom are each reached by at least one component, not necessarily both: only 7% of such glyphs have both sides at full height. A component that is short by nature (口, 日, 田) keeps a short height inside its slot and is not stretched to 768.
- **C5. Enclosures.** An enclosing stroke takes the frame of F2 and F3 itself; the enclosed part is centred inside it with the clearance of S4 on every side.
- **C6. No rescaling to fit.** A component is not squeezed or stretched by more than about 12% in one direction to make room. If the structure does not fit, the glyph moves to the wide class or its free strokes are re-spaced.

## Strokes

- **S1. One pen.** Every stroke is a centerline drawn with a round pen: 30 units at Regular, and 23.5, 36.5, 43 and 49.5 at the other weights. All weights share the same centerlines.
- **S2. Geometry.** Stems and bars are exactly straight and exactly vertical or horizontal. Curves are single smooth arcs. A shape that is mirror-symmetric in the sources is exactly symmetric about its own axis. Parallel bars in one component are equally spaced.
- **S3. Joins meet.** Two strokes that join share a point: one centerline ends on, or crosses, the other. A stroke does not stop short of the stroke it joins, and does not run through it.
- **S4. Separate strokes stay clear.** Strokes that do not join keep at least **0.5 units** of white at Regular; touching edge to edge is neither a join nor a gap and is a fault. **20 units** of white is the target, because the Bold pen is 19.5 units wider and anything less closes. A detached dot keeps 50 units from its centre to any other centerline.

## Shared components

- **R1. One drawing per radical and slot.** A radical that recurs in the same position at the same size is one template in `components/`, copied unchanged into each glyph: 180 templates serve 3,763 glyphs. Its shape, size and position are identical in every copy.
- **R2. Fix the template, not the copy.** A fault inside a template is corrected in the template and synced to every glyph that uses it, after checking that every one of them shows the fault.
- **R3. Free drawings follow the template.** Where a glyph draws the same radical without a template, it uses the template's construction and proportions.

## Checking

```sh
python tools/check_composition.py            # audit and rewrite reports/composition.json
python tools/check_composition.py --check    # fail if a glyph leaves a rule it kept before
```

The checker measures F1–F4 and S4 for every glyph, and records each glyph's layout, channel widths and tightest gap in [`reports/composition.json`](../reports/composition.json). Rules C, S2, S3, R3 and T are judged by eye against the chart; the layout figures in the report show where a glyph sits against the C targets.

The current audit of 11,328 glyphs:

| Rule | Result |
| --- | --- |
| F1, F2, F4 | No departures. All 11,277 body glyphs and 51 short forms are on their frames |
| F3 | 3 glyphs are wider than 640: U+3DAFB (723), U+3DAFF (751) and U+3E96C (646) |
| S4, 0.5 units | 60 glyphs have two strokes that touch edge to edge without joining |
| S4, 20 units | 4,623 glyphs have at least one gap under 20 units, which closes by Bold |

The F3 and S4 departures are recorded in the report as known exceptions and are still to be redrawn. `--check` passes while that list does not grow.

## 中文摘要

本文件规定 Sealie 的字形布局规则，数值为 Sealie 自身的设计参数，不取自其他字体。**结构**（笔画的有无、起止与连接）依据 Unicode 小篆码表的四种《说文》版本：藤花榭本（THX，大徐本）决定字集、顺序与结构，陈昌治本（CCZ）、小徐本（QJZ，祁寯藻刻本）与段注本（DYC）作为对照；仅当字形与全部样张矛盾时才修改。**布局**由本文件决定：一般字身墨迹自 y = 704 至 y = −64（高 768），以 x = 512 为中轴；标准宽 520，天然窄字取其自然宽度，结构容纳不下时可加宽至 640；51 个基本字使用登记的较矮尺寸。左右结构中左旁约占宽度的 41%、右旁约 55%，间隔约 25 单位；上下结构的上部约占高度的 31%。相接的笔画必须共用一点，不相接的笔画至少留白 0.5 单位，目标为 20 单位，以保证 Bold 字重下不粘连。相同位置的相同偏旁使用同一个共享模板。`tools/check_composition.py` 对全部 11,328 个字形检查上述框架与间距规则，结果见 `reports/composition.json`。
