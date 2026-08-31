# gzlab_ppt_skills

广州实验室定制版 PPT Master Skill。当前版本内置 `gzlab_research_deck` 高保真科研汇报模板，可从 DOCX、PDF、PPTX、Markdown、网页或文本材料生成可编辑 PPTX。

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

## 当前范围

- 内置广州实验室高端科学仪器科研汇报模板；
- 保留 PPT Master 的八项确认、实时预览、SVG质量检查和PPTX导出流程；
- 暂未加入多模板确认页，后续版本将增加“模板选择 + 八项设计确认”。

## 来源与授权

本项目基于 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) 修改，遵循 MIT License。广州实验室品牌素材及模板仅供获得授权的实验室成员内部使用。
