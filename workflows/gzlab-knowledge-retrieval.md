# GZLab Knowledge Retrieval Workflow

> 主流程 Step 5（Image Acquisition）的广州实验室知识库优先路径。规则与接口
> 契约：`references/gzlab-asset-retrieval.md`；属性字典：
> `references/gzlab-lexiang-properties.md`；权限红线：
> `references/gzlab-knowledge-base.md` §3（最高优先级）。

🚧 **GATE**: `slide_briefs.json` 已通过 `check_slide_focus.py --briefs`；至少一个页面
`needs_real_asset: true` 或用户要求使用知识库素材。

## Step R1 — 形成素材请求

1. 从 `slide_briefs.json` 提取所有 `needs_real_asset: true` 的页面。
2. 写出 `<project>/asset_request.json`（schema: `templates/asset_request.schema.json`）：
   每页一条，`semantic_query` 来自 `asset_query`，`filters` 只写相关性字段，
   `intended_use` 取本次 PPT 用途（八项确认中的受众/用途）。

## Step R2 — 热检索（正式素材库）

对每条请求执行 `search_gzlab_assets`（当前经乐享 MCP
`entry_list_children` + `filters.field_values`；脚本实现后走
`scripts/search_lexiang_assets.py`）：

1. 注入硬过滤：审核状态=已审核、有效状态=有效、允许用途⊇本次用途；
   对外用途追加 是否允许对外使用=允许。
2. 应用请求 filters（缺失属性按检索规则 §3.1 降级）。
3. 候选按内容描述相关度 + 质量重排，取前 `max_results` 条。
4. **命中即下载**该独立文件到 `<project>/images/`，不再触碰源文档。

## Step R3 — 冷检索（源文档定位 + 定向抽取）

热检索未命中的页面：

1. `locate_source_media`：乐享 Agent 正文检索综合文档库，定位源文件与页码/时间点。
2. 校验当前用户对源文件的**下载权限**（无权限 → 该源立即排除，不泄露其信息）。
3. `extract_source_asset` 下载并只处理目标页/时间段，剔除 Logo、页眉页脚、模板背景。
4. 候选结合页标题与上下文生成属性建议；与用户确认后选定实际采用的素材。
5. 采用的素材上传待审核区（`submit_asset_for_review`，审核状态=待审核），
   当前内部任务按规则临时使用（origin = `lexiang_pending_internal`）。

## Step R4 — 锁定与记录

1. 全部候选放入 `images/` 后运行 `analyze_images.py`，确认最终素材。
2. 写 `asset_manifest.json`（最终选择）与 `asset_sources.json`（来源、权限、血缘）。
3. 将素材写入 `design_spec.md` §VIII 与 `spec_lock.md` images。
   第一版 `Acquire Via` 记为 `user`（已下载到项目），来源真相以
   `asset_sources.json` 为准；待核心枚举扩展后启用 `Acquire Via: gzlab-kb`。
4. 仍无结果的页面按 `asset_request.fallback`：询问用户是否 AI 生成
   （**不得默认用 AI 图替代真实实验室证据**），否则占位符 + `needs_manual`。

**✅ Checkpoint**：
- [ ] 每个 `needs_real_asset` 页面：已命中素材 或 已走 fallback 并经用户确认
- [ ] `asset_sources.json` 每条含来源位置、权限校验记录、审核状态
- [ ] `check_slide_focus.py --svg` 阶段 E06 不会缺 provenance

## 异常处理

按 `references/gzlab-asset-retrieval.md` §3 降级表执行；乐享服务不可用时
不阻塞主流程 —— 用用户提供素材或经确认的 AI/占位符路径继续。
