# Guangzhou Laboratory Content Focus Rules

> Page-level content discipline for every deck produced by this skill. These
> rules exist because prompt-level "be concise" advice is not stable across
> models — the contract lives in `slide_briefs.json` and is enforced by
> `scripts/check_slide_focus.py`. Strategist owns the briefs; Executor must not
> out-grow them.

## 1. The core principle

> 一页只表达一个结论，为该结论检索一个最有说服力的广州实验室证据，再使用一个主要视觉焦点完成呈现。
>
> One page = one question = one takeaway = at most three supporting points = one primary visual.

## 2. Hard rules (enforced, violations block the pipeline)

| # | Rule | Enforcement |
|---|---|---|
| R1 | Every page answers exactly one question (`page_question`) and states exactly one conclusion (`takeaway`) | brief schema + checker E01/E02 |
| R2 | At most 3 supporting points per page (`supporting_evidence`) | schema `maxItems: 3` + checker E03 |
| R3 | Exactly one primary visual focus per page (`max_primary_visuals: 1`) | checker E04 (brief) / E11 (SVG) |
| R4 | Overfull pages are fixed by deleting secondary content or splitting the page — NEVER by shrinking font size or compressing line spacing | reviewer + checker W03 |
| R5 | Secondary detail goes to speaker notes (`notes_hint`) or appendix, not the page body | Strategist |
| R6 | Do NOT fill template card slots just because they exist — a 4-slot layout with 2 strong points uses 2 slots | reviewer |
| R7 | Titles are conclusion-style statements, not section labels ("项目背景" / "技术路线" are banned as page titles on content pages) | checker W01 |
| R8 | `anchor` / `breathing` pages carry core messages, real photos and big numbers; `dense` is reserved for technical architecture, metric comparisons and validation results only | checker W02 |
| R9 | Pages needing real GZLab evidence (`needs_real_asset: true`) must carry an `asset_query`; the asset must resolve to a sourced file with provenance before Executor starts | checker E05/E06 (asset stage) |
| R10 | R7–R9 apply to every template; switching templates never relaxes content budgets | — |

## 3. Text budgets (total extracted page text, CJK chars count double weight = 1 char each)

| Rhythm | Total page text budget | Use |
|---|---|---|
| `anchor` | ≤ 120 chars | Core statement pages, big-number pages, real-photo pages |
| `breathing` | ≤ 260 chars | Transition, summary, single-idea explanation |
| `dense` | ≤ 650 chars | Architecture, comparisons, validation data — only when necessary |

Cover / chapter / ending pages are exempt from budgets but still follow R1/R7.

`check_slide_focus.py --svg` measures the generated pages against these budgets
and reports `E10` when a page exceeds its rhythm budget by >10%.

## 4. slide_briefs.json — the contract

Written by Strategist to `<project_path>/slide_briefs.json` **together with**
`design_spec.md` / `spec_lock.md`, before any SVG generation. Schema:
`templates/slide_briefs.schema.json`. Minimal page example:

```json
{
  "page_id": "P04",
  "page_question": "为什么高端科学仪器研发需要智能体？",
  "takeaway": "复杂仪器研发的核心瓶颈是跨学科知识与工程流程难以协同。",
  "supporting_evidence": ["跨学科知识分散", "研发周期长", "设计验证反复"],
  "primary_visual": "广州实验室高端仪器研发场景",
  "needs_real_asset": true,
  "asset_query": "广州实验室 高端科学仪器 研发 场景",
  "max_points": 3,
  "max_primary_visuals": 1,
  "rhythm": "anchor"
}
```

Consistency requirements with the rest of the pipeline:

- `pages[].page_id` must cover every content page planned in `design_spec.md`
  § outline, in order, with no gaps (`P01`, `P02`, …).
- `rhythm` must match `spec_lock.md page_rhythm` for the same page.
- When `needs_real_asset` is true, `design_spec.md` §VIII must contain a
  corresponding image row for that page; after acquisition its status must be
  terminal (`Sourced` / `Generated` / user-provided) — see
  `references/gzlab-asset-retrieval.md`.
- Executor must not add body text blocks beyond the brief's evidence points;
  extra detail belongs to `notes/total.md`.

## 5. Checker integration

```bash
# Gate A — after Strategist output, BEFORE Step 6 generation:
python3 ${SKILL_DIR}/scripts/check_slide_focus.py <project_path> --briefs

# Gate B — after all SVGs, together with svg_quality_checker.py:
python3 ${SKILL_DIR}/scripts/check_slide_focus.py <project_path> --svg
```

Exit code is non-zero when any `E`-level finding exists; `W` findings are
reported but non-blocking. Both gates feed the structured issue list consumed
by the gzlab quality gate (`workflows/gzlab-quality-gate.md`).
