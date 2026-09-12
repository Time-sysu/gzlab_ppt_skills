# Guangzhou Laboratory Knowledge Base (Lexiang) — Structure & Governance

> 乐享是文件、元数据、权限和审核的唯一权威数据源。本文件记录 skill 侧需要
> 知道的库结构、权限边界和状态机。真实凭证永不进入本仓库；配置样例见
> `.env.example`，运行期凭证由环境变量 / WorkBuddy 连接配置注入。

## 1. 线上结构（2026-09-12 快照，权威 ID 见 `templates/lexiang_properties.schema.json`）

```text
广州实验室知识库 (space a74abe9d…)
├── 01_综合文档库          项目申报与政策 / 高端科研仪器项目 / 历史优秀PPT / 宣传与视频材料 / 方法论与结构化思维
├── 02_正式素材库          实验室与园区 / 仪器设备 / 科研场景 / 项目成果 / 人物与活动 / 图表与示意图 / 视频片段与关键帧
├── 03_待审核区            人工上传材料 / 文档抽取素材 / AI生成素材 / PPT-master生成成果
└── 04_归档区              已替代版本 / 已过期素材 / 已驳回记录
```

正式素材库的常规检索只返回「审核状态=已审核、有效状态=有效」的文件。
待审核素材仅提交人、管理员和指定项目成员可访问。

## 2. 双通道检索

| 通道 | 用途 | 当前实现 |
|---|---|---|
| 乐享 Agent / 语义检索 | 正文理解、源文档定位（页码/时间点） | WorkBuddy 乐享 MCP 连接（已连接） |
| 乐享 OpenAPI | 自定义属性的查询、过滤、写入、更新 | 本 skill 的 MCP 工具直连；独立脚本（`scripts/lexiang_openapi_client.py` 等）按 `references/gzlab-asset-retrieval.md` §5 接口契约后续实现 |

乐享 Agent 不能检索自定义属性 —— 属性过滤一律走 OpenAPI（MCP
`entry_list_children` 的 `filters.field_values` 或后续脚本）。

## 3. 权限红线（不可违反）

1. 乐享平台权限是访问控制的权威依据；自定义属性中的「保密级别」仅用于检索治理。
2. 返回素材 = 下载行为，必须验证下载权限，不能只验证「可查看」。
3. 每次检索/下载/写入都携带用户身份；统一应用身份下必须二次校验用户权限。
4. 严禁统一应用凭证让普通用户间接获得受限文档或图片；无权访问的结果不返回内容，也不泄露标题、描述、来源位置。
5. 抽取素材默认继承源文件权限，衍生物权限不得比源文件更宽。
6. 自动回写只进待审核区，永不自动公开发布。

## 4. 状态机

```text
人工/自动提交 → 待审核 → 已审核 ──→ 有效 ──→ 待复核 ──→ 有效
                  │          │                        │
                  ├→ 需修改   └→ 已过期/已归档         └→ 已归档
                  └→ 已驳回
```

源文件更新 → 衍生素材标记「待复核」→ 管理员确认后恢复「有效」或归档旧版。
源文件权限收紧 → 按来源文件ID定位衍生物并同步收紧（依赖待补的「来源文件ID」字段）。

## 5. 存储边界

本仓库只保存：工作流与规则、属性 schema 与受控词表、清单格式、配置样例。
不保存：乐享凭证、知识库实体数据、真实素材文件。

## 6. 项目运行清单（可审计产物，非中心数据库）

| 文件 | 内容 | Schema |
|---|---|---|
| `asset_request.json` | 每页需要什么素材 | `templates/asset_request.schema.json` |
| `asset_manifest.json` | 最终选择了哪些素材 | `templates/asset_manifest.schema.json` |
| `asset_sources.json` | 来源、权限与血缘 | `templates/asset_sources.schema.json` |
| `writeback_manifest.json` | 待回写成果清单 | `templates/writeback_manifest.schema.json` |
