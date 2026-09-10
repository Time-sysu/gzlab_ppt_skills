# gzlab_ppt_skills

广州实验室定制版 PPT Master Skill。当前版本内置三套广州实验室模板，可从 DOCX、PDF、PPTX、Markdown、网页或文本材料生成可编辑 PPTX。默认科研汇报模板不变，2026-09-10新增“模板1”和“模板2”（fidelity模式）。

## 安装

### WorkBuddy 用户级

将仓库克隆或解压到：

```text
%USERPROFILE%\.codebuddy\skills\gzlab-ppt-skills
```

### Codex 用户级

将仓库克隆或解压到：

```text
%USERPROFILE%\.codex\skills\gzlab-ppt-skills
```

安装 Python 依赖：

```powershell
python -m pip install -r requirements.txt
```

## 使用

在 WorkBuddy 或 Codex 中输入：

```text
使用广州实验室PPT Skill，根据这份材料生成项目申报PPT。
```

没有指定其他模板时，Skill 默认使用：

```text
templates/decks/gzlab_research_deck
```

模板路径相对于 Skill 根目录解析，不依赖安装用户的本机用户名。

要使用本次新增模板，请明确提供模板目录。例如：

```text
使用广州实验室PPT Skill，根据这份材料生成汇报PPT。
模板目录：templates/decks/gzlab_template_1
```

上述目录对应“模板1”；改为 `templates/decks/gzlab_template_2` 即使用“模板2”。仅说“使用模板1”不是当前工作流的可靠触发方式，建议始终给出目录。可用模板的权威索引为 `templates/decks/decks_index.json`，页面清单和使用约束见各模板内的 `design_spec.md`。

本次新增模板保留原稿复杂背景和品牌装饰，文字、图形与业务图片位置可编辑。固定背景是位图，不能逐个拆分编辑；模板2的深色章节/结束页背景还包含原稿设备外观，不能将其当作新项目成果证明。无关主题应避开该版式。

## 更新

通过 Git 安装的同事可在安装目录运行 `git pull --ff-only`；通过 ZIP 安装的同事可重新下载并替换安装文件，替换前请备份自己的定制内容。更新后按客户端需要重新加载 Skill。本次无需重新导入原始PPT，也无需重新运行 create-template。

## 当前范围

- 内置广州实验室科研汇报及新增的两套品牌模板；
- 保留 PPT Master 的八项确认、实时预览、SVG质量检查和PPTX导出流程；
- 暂未加入多模板确认页，后续版本将增加“模板选择 + 八项设计确认”。

## 来源与授权

本项目基于 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 修改，遵循 MIT License。广州实验室品牌素材及模板仅供获得授权的实验室成员内部使用。
