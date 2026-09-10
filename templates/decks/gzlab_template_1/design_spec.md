---
template_id: gzlab_template_1
deck_id: gzlab_template_1
display_name: 模板1
kind: deck
category: brand
summary: 模板1：广州实验室浅蓝点阵背景、蓝绿品牌色，适合科研申报、平台建设与综合进展汇报。
keywords: [广州实验室, 模板1, 科研汇报, 平台建设, 蓝绿多图]
primary_color: "#0443AE"
canvas_format: ppt169
replication_mode: fidelity
fixed_page_fidelity: literal
---

# 模板1 — Design Specification

## I. Template Overview

科研申报、实验室介绍、平台建设、阶段汇报。浅色主题，以浅蓝点阵/曲面背景、蓝色标题、绿色强调和右上角广州实验室标识为识别特征。来源：用户提供的《模板1.pptx》（13页）；fidelity 提炼版式，不将原有业务文字和数字作为新演示文稿事实。

## II. Color Scheme

| Role | Color | Use |
|---|---|---|
| Primary | #0443AE | 标题、分区头、结论条 |
| Accent | #00B050 | 当前章节、正向强调 |
| Secondary | #4472C4 | 平台标题与层级 |
| Dark | #002060 | 重要说明 |
| Body | #333F50 | 正文 |
| Muted | #808080 | 非当前目录、辅助信息 |
| Panel | #FFFFFF | 内容面板 |
| Image slot | #EAF2FB | 待替换图片区 |
| Rule | #7DACFC | 细边线 |
| Alert | #C04F15 | 问题、例外 |

## III. Typography

微软雅黑（Microsoft YaHei）优先，Arial 用于英文。标题32px，封面64px，正文参考24px；六列密集对照参考18–20px。原始等线/Arial主题不覆盖源页面的微软雅黑显式格式。

## IV. Signature Design Elements

- 内容页固定白色页眉高76.5px；标题从x82、y48开始；左侧蓝绿点阵和右上标识保留。
- 封面与结束页居中标识、浅蓝点阵及曲面使用原 PowerPoint 去除文字后导出的2560×1440背景，保留原始层叠、透明度与裁切外观；它们是不可拆分的位图装饰层，正文、图形及替换图片槽可编辑。
- 目录保留x370竖线与左侧竖排“目录 / CONTENTS”，右侧使用四项可变目录。
- 原文件母版1的版式2、3是实际样例的共用视觉来源。页1从自动chapter候选纠正为封面，页2/8纠正为目录/章节定位。
- 原页9的OLE引用不带入最终模板，替换为可填的图片证据区。业务照片和仪器示意图以图片槽呈现，生成时必须使用与新主题相符、已核实的素材。

## V. Page Roster

| SVG | Source cluster | Character and content slot |
|---|---|---|
| `01_cover.svg` | 源1 | 原居中封面；标题、副标题、汇报人、日期 |
| `02_chapter.svg` | 源1派生 | 同背景章节开场；章节序号、标题、简述 |
| `02_toc.svg` | 源2/8 | 原竖排目录与四项导航；当前项用品牌蓝 |
| `03_content.svg` | 版式2 | 仅固定页眉，正文自由布局 |
| `03a_content_intro.svg` | 源3 | 上方简介面板、下方三张实景图 |
| `03b_content_quote_compare.svg` | 源4 | 上方关键依据、下方双区比较 |
| `03c_content_timeline.svg` | 源5 | 六节点时间线及六个图片槽、底部结论 |
| `03d_content_comparison.svg` | 源6 | 六列图文比较、底部结论；用于项目对照 |
| `03e_content_platforms.svg` | 源7 | 六平台图片与状态、下方双服务支撑区 |
| `03f_content_evolution.svg` | 源9 | 上方五阶段演进，下方两个图文证据区 |
| `03g_content_hierarchy.svg` | 源10 | 左图与四层金字塔、右侧规模说明 |
| `03h_content_pipeline.svg` | 源11 | 四阶段图文流程；样本/处理/数据/设备可替换 |
| `03i_content_problem_solution.svg` | 源12 | 左问题列表、右大图及解决方案结论 |
| `04_ending.svg` | 源13 | 原结束背景与居中文字；感谢、联系信息 |

## VI. Assets

| Asset | Dimensions | Usage |
|---|---|---|
| cover_bg.png | 2560×1440 | 源1删除可变文字后的固定装饰 |
| ending_bg.png | 2560×1440 | 源13删除可变文字后的固定装饰 |
| content_bg.png | 2560×1440 | 源版式2的标题栏/标识/背景，不含标题占位文本 |
| toc_bg.png | 2560×1440 | 源版式3目录固定结构 |

包内SVG引用同目录素材。导入新项目时，随模板复制这些位图到images/，将href改为../images/，不要遗漏或重新生成背景。{{CONTENT_AREA}}是内容区契约；各区域里的文字与图片占位符是可替换槽，不得出现在交付给领导的最终PPT中。
