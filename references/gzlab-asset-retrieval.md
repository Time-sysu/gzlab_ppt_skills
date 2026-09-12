# GZLab Asset Retrieval — Rules & Interface Contracts

> 检索规则、优先级、降级策略与统一接口契约。执行流程见
> `workflows/gzlab-knowledge-retrieval.md`。知识库治理与权限红线见
> `references/gzlab-knowledge-base.md`（红线部分优先级最高）。

## 1. 检索优先级（严格按序）

1. 用户本次任务直接提供的素材
2. 乐享正式素材库：已审核 + 有效 + 权限匹配的独立图片/视频素材（热检索）
3. 乐享 Agent 检索综合文档库，定位 PPT/Word/PDF/视频的页码或时间点 → 下载源文件定向抽取（冷检索）
4. 用户明确允许后的 AI 生成
5. 占位符 + 标记人工补充

每次检索先过硬过滤（审核状态、有效状态、保密级别、允许用途、对外使用），
再做内容相关度与视觉质量排序 —— 不允许直接采用搜索结果第一项。

## 2. 自然语言 → 属性条件

用户用自然语言提需求，由 Strategist 转成结构化查询（asset_request.json）：

```json
{
  "semantic_query": "广州实验室冷冻电镜平台的横版实景图",
  "filters": {
    "所属项目": ["电镜"],
    "内容描述": ["冷冻电镜", "平台实景"],
    "素材类型": ["图片"],
    "图片方向": ["横版"]
  }
}
```

转换规则：同义词表见 `references/gzlab-lexiang-properties.md` §2；硬过滤
字段（审核状态=已审核、有效状态=有效、允许用途=本次用途）由检索工作流
自动注入，Strategist 的 filters 只写相关性字段。

## 3. 降级规则

| 异常 | 处理 |
|---|---|
| OpenAPI 属性检索无结果 | 放宽非关键属性（先放质量等级、场景标签），硬过滤不动 |
| 乐享 Agent 无法定位 | 关键词 + 文档范围缩小重试；仍失败请求人工指定文件 |
| 源文件过大下载慢 | 告知用户这是冷检索；只处理目标页/时间段；素材沉淀后下次热检索秒回 |
| 抽取图片分辨率不足 | 尝试页面呈现版本；AI增强/生成需用户允许 |
| 无法取得原始图片 | 输出高清页面区域截图并在素材类型标记，不得冒充原始照片 |
| 当前用户无权限 | 立即停止返回该素材；不得借统一应用身份绕过 |
| 属性写入失败 | 任务清单标记「待回写」，不得伪装已入库 |
| 乐享服务不可用 | 用用户本次提供素材；否则按确认策略进入 AI 或占位符路径 |

### 3.1 缺失属性期间的临时降级（截至 2026-09-12，见 lexiang_properties.schema.json `planned_missing_fields`）

| 缺失字段 | 临时替代 |
|---|---|
| 素材类型 | 按文件扩展名过滤（jpg/png/webp = 图片；mp4/mov = 视频） |
| 图片方向 | 下载后用 `analyze_images.py` 测量宽高比再筛选 |
| 质量等级 | 跳过，由模型读内容描述 + 预览重排 |
| 场景标签 / PPT用途 | 并入「内容描述」模糊搜索词 |
| 素材来源 | 以 asset_sources.json `origin` 为准，回写时备注 |
| 来源文件ID | 以 asset_sources.json `source_file_entry_id` 为准（项目侧血缘不断） |

## 4. 冷检索抽取规则

- 只处理目标页/目标时间段；剔除 Logo、页眉页脚、模板背景等低价值元素。
- PPT 图片按需保存三份：原始嵌入图（最高分辨率）、页面呈现版本（保留裁剪组合）、检索缩略图。
- 组合图形/复杂图表无法独立恢复时，保存高清「页面区域截图」并明确标记素材类型。
- 只把**实际采用**的素材提交乐享待审核区；未采用候选留在任务临时目录并定期清理。
- 同一源文件同一任务内只下载解析一次（任务级缓存）。

## 5. 统一接口契约（脚本实现前的稳定签名）

以下接口是 skill 与乐享适配层之间的稳定边界。当前由 WorkBuddy 乐享 MCP
工具实现；独立脚本（scripts/lexiang_*.py）实现时必须保持签名与语义不变：

```text
search_gzlab_assets(query, user_identity, intended_use, filters, max_results)
    → 热检索正式素材库。返回 [{entry_id, name, 内容描述, 属性摘要, preview_ref}]
    硬过滤自动注入；无权访问的条目不返回任何信息。

locate_source_media(query, user_identity, document_types)
    → 乐享 Agent 正文检索综合文档库。
    返回 [{entry_id, name, doc_type, page_or_timecode, 上下文摘要}]

extract_source_asset(source_file_entry_id, page_or_timecode, user_identity)
    → 校验下载权限 → 下载源文件（任务级缓存）→ 定向抽取 →
    返回 {candidates: [{file, kind, width, height, 建议属性}]}

submit_asset_for_review(file, properties, source_provenance)
    → 上传待审核区并通过 OpenAPI 填写属性（审核状态=待审核）。
    返回 {entry_id}；失败保留「待回写」标记。

update_lexiang_properties(entry_id, property_patch, user_identity)
    → 属性补丁写入；记录操作人与时间。

submit_generated_artifact(file, generation_manifest)
    → PPT/AI图片成果提交待审核区对应子目录。
```

约定：所有接口显式接收 `user_identity`；任何权限失败返回空结果而非错误
详情；脚本配置走环境变量（`.env.example` 列出键名，真实值永不入库）。
