# GZLab Asset Writeback Workflow

> PPT 导出后的审核式回写。「自动更新知识库」= 自动提交审核，**不是**自动
> 公开发布。权限红线见 `references/gzlab-knowledge-base.md` §3。

🚧 **GATE**: Step 7 导出完成；`asset_sources.json` 存在。

## Step W1 — 生成回写清单

扫描项目产物，写 `<project>/writeback_manifest.json`
（schema: `templates/writeback_manifest.schema.json`，status 初始 =
`pending_user_confirm`）：

| 产物 | kind | 待审核区子目录 |
|---|---|---|
| 导出的完整 PPTX | `generated_pptx` | PPT-master生成成果 |
| AI 生成图片 | `ai_image` | AI生成素材（附模型/提示词/时间） |
| 冷检索抽取且实际采用的素材 | `extracted_asset` | 文档抽取素材 |
| 新产生且有复用价值的图片 | `new_reusable_image` | 人工上传材料 |

**不回写**：已来自乐享的旧素材（只在 asset_sources.json 保留引用）、模板
Logo/背景/装饰元素、未采用的候选。

## Step W2 — 用户确认

⛔ **BLOCKING**：向用户列出清单（文件、目标目录、属性建议），等待明确确认
后才执行上传。用户可剔除条目。

## Step W3 — 提交与属性填写

对确认的每条：`submit_asset_for_review` / `submit_generated_artifact` ——

```bash
python3 ${SKILL_DIR}/scripts/submit_lexiang_asset.py <文件> \
    --target-subfolder <文档抽取素材|AI生成素材|PPT-master生成成果|人工上传材料> \
    --properties '{"内容描述":"...","所属项目":["..."],"来源文件":"...","来源位置":"...","责任人":"..."}' \
    --provenance '{"source_file_entry_id":"...","source_location":"..."}' \
    --user-identity "<用户>"
```

1. 上传到 03_待审核区 对应子目录。
2. OpenAPI 填写属性：内容描述、所属项目、来源文件、来源位置、素材ID、
   责任人；**审核状态强制 = 待审核**（脚本内强制，调用方无法覆盖）；
   AI 素材记录模型与提示词。
3. 结果回填 `writeback_manifest.json items[].result`（entry_id / submitted_at
   / error）；失败时脚本输出 `status: 待回写` 并保留清单，不得伪装成功。

## Step W4 — 收尾

- 全部成功 → status = `submitted`；部分失败 → `partial_failure` 并告知用户。
- 提醒用户：待审核区内容由管理员审核后才进入正式素材库供他人复用。
- 源文件后续更新/权限收紧时，按血缘（来源文件 + 来源位置，字段补齐后为
  来源文件ID）定位衍生素材并标记「待复核」。
