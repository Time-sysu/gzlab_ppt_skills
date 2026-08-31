---
deck_id: gzlab_research_deck
template_id: gzlab_research_deck
kind: deck
display_name: 广州实验室高端科学仪器科研汇报模板
category: brand
summary: 广州实验室高端科学仪器项目申报、技术方案、阶段汇报与验收汇报使用的严谨蓝绿科研模板。
keywords: [广州实验室, 高端科学仪器, 科研汇报, 技术路线, MBSE]
primary_color: "#0070C0"
canvas_format: ppt169
page_count: 10
replication_mode: fidelity
placeholders:
  01_cover: ["{{TITLE}}", "{{SUBTITLE}}", "{{AUTHOR}}", "{{DATE}}", "{{BRAND_LOGO}}"]
  02_toc: ["{{TOC_ITEM_1_TITLE}}", "{{TOC_ITEM_1_DESC}}", "{{TOC_ITEM_2_TITLE}}", "{{TOC_ITEM_2_DESC}}", "{{TOC_ITEM_3_TITLE}}", "{{TOC_ITEM_3_DESC}}"]
  02_chapter: ["{{CHAPTER_NUM}}", "{{CHAPTER_TITLE}}", "{{CHAPTER_DESC}}"]
  03_content: ["{{PAGE_TITLE}}", "{{CONTENT_AREA}}", "{{SECTION_NAME}}", "{{PAGE_NUM}}"]
  03a_content_two_col: ["{{PAGE_TITLE}}", "{{LEFT_TITLE}}", "{{LEFT_CONTENT}}", "{{RIGHT_TITLE}}", "{{RIGHT_CONTENT}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03b_content_figure: ["{{PAGE_TITLE}}", "{{FIGURE}}", "{{FIGURE_CAPTION}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03c_content_case_grid: ["{{PAGE_TITLE}}", "{{CASE_1_TITLE}}", "{{CASE_1_CONTENT}}", "{{CASE_2_TITLE}}", "{{CASE_2_CONTENT}}", "{{CASE_3_TITLE}}", "{{CASE_3_CONTENT}}", "{{CASE_4_TITLE}}", "{{CASE_4_CONTENT}}", "{{PAGE_NUM}}"]
  03d_content_process: ["{{PAGE_TITLE}}", "{{STEP_1_TITLE}}", "{{STEP_1_CONTENT}}", "{{STEP_2_TITLE}}", "{{STEP_2_CONTENT}}", "{{STEP_3_TITLE}}", "{{STEP_3_CONTENT}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  03e_content_validation: ["{{PAGE_TITLE}}", "{{LEFT_FIGURE}}", "{{RIGHT_FIGURE}}", "{{LEFT_CAPTION}}", "{{RIGHT_CAPTION}}", "{{KEY_MESSAGE}}", "{{PAGE_NUM}}"]
  04_ending: ["{{THANK_YOU}}", "{{ENDING_SUBTITLE}}", "{{CONTACT_INFO}}", "{{PAGE_NUM}}"]
---

# 广州实验室高端科学仪器科研汇报模板 — Design Specification

## I. Template Overview

- 适用场景：高端科学仪器项目申报、技术路线阐述、阶段进展、测试验证、验收汇报和学术技术报告。
- 设计基调：严谨、学术、工程化、结构清晰；浅色内容页配蓝绿科技识别。
- 视觉识别：正文统一使用蓝色顶部标题带、左端蓝绿渐变短条和右上广州实验室标识；内容区以白底、蓝色标题和低饱和浅蓝分区组织技术证据。
- 复刻策略：封面按原样板的“科研图像 + 蓝色波浪”构图适配重建；目录、章节导航与结束页保持高保真；正文从26页中聚类为通用、双栏、主图、案例宫格、流程和验证对照六类。

## II. Color Scheme

- 主色 `#0070C0`：封面底色、重点标题、章节编号。
- 品牌蓝 `#2E75B6`：顶部标题带、标签、描边、流程节点。
- 主题蓝 `#4472C4`：次级箭头和层级强调。
- 强调绿 `#92D050`：蓝绿渐变短条、完成状态与正向结果。
- 中性灰 `#A6A6A6`：未激活目录项、辅助文字。
- 背景 `#FFFFFF`，正文 `#1F2937`，浅蓝分区 `#EAF3FA`。

## III. Typography

- 中文：`"Microsoft YaHei", "微软雅黑", sans-serif`。
- 西文、数字及技术缩写：`"Times New Roman", "Microsoft YaHei", sans-serif`。
- 正文基准：20 px；页标题32 px；内容标题24–26 px；封面标题44 px。

## IV. Signature Design Elements

- 79 px高品牌顶栏：左侧蓝绿渐变短条、主体品牌蓝、右侧广州实验室标识。
- 目录使用三段纵向编号和双箭头提示；激活项为蓝色，未激活项为灰色。
- 技术内容页使用圆角标签、蓝色虚线框、浅蓝信息区和结论条，强调“需求—模型—验证—产品化”的证据链。
- 页码固定在右下角；页面内容应避开右上品牌标识区域。

## V. Page Roster

| File | Cluster source | Visual character and intended slot |
|---|---|---|
| `01_cover.svg` | 源第1页 | 冷冻电镜科研图像占上半页，底部蓝色波浪承载标题、作者和日期；适合项目封面。 |
| `02_toc.svg` | 源第2、3、7、12页 | 三段式目录，编号与双箭头形成章节状态导航；适合三章结构的申报或汇报。 |
| `02_chapter.svg` | 由目录状态页提炼 | 大号章节编号与标题居中，保留品牌顶栏和渐变指示；适合章节过渡。 |
| `03_content.svg` | 全部正文页的共同母版 | 仅锁定品牌顶栏、页标题、页码和开放内容区；适合自由排版。 |
| `03a_content_two_col.svg` | 源第4、8、14、18页 | 左右双栏、分区标题和底部结论条；适合定义对比、问题—方案、双模块说明。 |
| `03b_content_figure.svg` | 源第5、6、19、21、23、25页 | 大幅技术图或系统截图居中，配图题和结论条；适合架构图、仿真图和全景图。 |
| `03c_content_case_grid.svg` | 源第9、10、11页 | 2×2案例宫格，每格含标题与摘要；适合行业案例、文献证据和能力清单。 |
| `03d_content_process.svg` | 源第13、17页 | 三节点闭环流程，围绕需求分析、模型计算和协同验证；适合技术路线和研发闭环。 |
| `03e_content_validation.svg` | 源第15、16、22、24、26页 | 左右验证图对照、误差说明和底部结论；适合多软件、多模型或仿真—实验验证。 |
| `04_ending.svg` | 源第20页 | 全幅科研场景图与半透明蓝色斜切面板，保留广州实验室署名；适合致谢和联系方式。 |

## VI. Assets

| File | Dimensions | Intended usage |
|---|---:|---|
| `brand_logo.png` | 7626×2108 | 母版右上广州实验室品牌标识。 |
| `cover_bg.jpg` | 2785×1031 | 封面默认冷冻电镜科研图像，可在项目中替换。 |
| `ending_bg.png` | 1111×619 | 结束页默认科研场景背景，可在项目中替换。 |

## VII. Placeholder Overrides

正文变体使用语义化区域占位符，例如双栏页的 `{{LEFT_CONTENT}}` / `{{RIGHT_CONTENT}}`、验证页的 `{{LEFT_FIGURE}}` / `{{RIGHT_FIGURE}}`。这些占位符在前置元数据中逐页声明；通用正文页仍保留标准 `{{CONTENT_AREA}}`。
