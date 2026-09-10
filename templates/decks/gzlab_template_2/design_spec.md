---
template_id: gzlab_template_2
deck_id: gzlab_template_2
display_name: 模板2
kind: deck
category: brand
summary: 模板2：广州实验室建筑封面、蓝绿强调、大图成果卡片与技术对比，适合领导汇报和成果展示。
keywords: [广州实验室, 模板2, 领导汇报, 成果展示, 技术对比]
primary_color: "#006EBD"
canvas_format: ppt169
replication_mode: fidelity
fixed_page_fidelity: literal
---

# 模板2 — Design Specification

## I. Template Overview

用于领导汇报、科研成果、技术方案比较。浅色正文与深色大图交替，品牌蓝绿强调关键结论。来源为用户《模板2.pptx》（5页）。源5标题为“空白 / 模板”，实际背景含设备外观图，保留为章节/结束背景；不机械沿用自动ending分类。示例中的合同、专利、性能和获奖信息不作为模板固定事实。

## II. Color Scheme

| Role | Color | Use |
|---|---|---|
| Primary | #006EBD | 主强调、成果卡片 |
| Accent | #00A871 | 关键数字、正向结论 |
| Deep green | #00754D | 第三卡片、次级强调 |
| Deep blue | #0A4A7A | 对照旧方案、深色标签 |
| Body | #17191C | 正文与页标题 |
| Muted | #6B7280 | 图注与来源 |
| Arrow neutral | #808080 | 原页眉箭头渐变起点 |
| Panel | #EFF5FB | 浅蓝内容区 |
| Line | #E3E6EA | 卡片边框 |
| White | #FFFFFF | 图片上文字、卡片底 |
| Light text | #CFE9E0 | 深色背景辅助文字 |

## III. Typography

微软雅黑（Microsoft YaHei）优先，英文Arial。正文参考22–24px，内容标题42.67px；封面保留大字居中逻辑，长标题可分行。字体跟随源页显式样式，而非机械采用源主题Calibri。

## IV. Signature Design Elements

- 封面保留原实验室建筑照片、白色标识、绿色弧线和绿色汇报人条。
- 正文标题从x115、y62起，右侧标识维持原裁切：外框x1098.31/y10.82/w181.66/h75.06，内部viewBox="0 0.08826 1 0.91174"。
- 正文品牌主要存在于页面层，而不是母版；必须一并保留背景、箭头和标识。源页重复标识仅保留一份，阴影降为干净边框。
- 封面及深色结束背景使用原PowerPoint去除可变文字后的2560×1440图，精确保留复杂装饰；位图背景不可拆分，正文与业务内容保持可编辑。
- 内容图片槽不填入与新主题无关的旧成果照片。图文布局需保留但原始数据必须重新核实。
- Fidelity例外：源5右侧设备外观已合成在整页背景图片中，本包按确认的原样保留，不把它作为新主题的成果证明。该设备图不可独立编辑；主题不适用时不选该章节/结束版式，可使用通用内容页。若要删除或替换，应另行制作去设备版本，不可假称已经完成。
- 校验器对页眉标识给出的“1×1显示尺寸”提示源于嵌套归一化裁切，实际显示框为181.66×75.06。该警告不应通过将图片缩成1像素解决。

## V. Page Roster

| SVG | Source cluster | Character and content slot |
|---|---|---|
| `01_cover.svg` | 源1 | 建筑照片、白色居中大标题、绿色汇报人条、日期 |
| `02_chapter.svg` | 源5派生 | 深色背景、左绿色竖线、章节标题与简述 |
| `03_content.svg` | 源2–4页眉 | 保留页眉和标识，正文可自由布局 |
| `03a_content_hero_cards.svg` | 源2 | 上部大图/关键结论/大数字，下部三张成果图片卡片 |
| `03b_content_impact.svg` | 源3 | 上部双区：证据图片与关键指标；下部四项成果图片 |
| `03c_content_technical_compare.svg` | 源4 | 上部挑战→方案，下部左右设备图与中央比较图 |
| `04_ending.svg` | 源5 | 原深色背景、左对齐结束文字及联系信息 |

## VI. Assets

| Asset | Dimensions | Usage |
|---|---|---|
| cover_bg.png | 2560×1440 | 源1固定装饰，文字已移除 |
| ending_bg.png | 2560×1440 | 源5固定装饰，文字已移除 |
| content_bg.png | 1326×730 | 源image3正文背景 |
| brand_logo.png | 192×87 | 源image4；必须保留嵌套裁切，不要拉伸改比例 |
| hero_bg.jpeg | 2560×680 | 源image5的大图背景；只用作氛围，不作为技术事实证据 |

包内SVG引用同目录素材。导入项目时复制位图至images/并改href为../images/；保持嵌套裁切。{{CONTENT_AREA}}描述内容区契约，所有示例提示、图位和变量需在最终PPT中替换。源正文标识分辨率较低，沿用原件，不将插值放大称为高清增强。
