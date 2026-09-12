# GZLab Quality Gate Workflow

> Expert review loop between generation and export. Triggered by the main
> pipeline after Step 6 according to the deck's `quality_mode`
> (`slide_briefs.json.quality_mode`, default `standard`). This is NOT the
> opt-in `visual-review` workflow — it is a pipeline quality gate with
> structured output and convergence rules.

## Quality modes

| Mode | Policy | When |
|---|---|---|
| `draft` | Technical checks only (svg_quality_checker + check_slide_focus) | Quick internal discussion |
| `standard` | 1 expert review round | Routine project reports |
| `final` | Up to 2 expert review rounds | Project applications, formal defenses |

## Pipeline position

```text
Step 6.1  Technical checks (svg_quality_checker.py + check_slide_focus.py --svg) — must be 0 errors
Step 6.2  GZLab review expert → review/review_report_r1.json     [skipped in draft mode]
Step 6.3  Routed fixes + re-check (page-scoped, see below)
Step 6.2' (final mode only, if r1 verdict = revise) second round → review_report_r2.json
Step 7    Export
```

## Step 6.2 — run the review

1. Read [`references/gzlab-reviewer.md`](../references/gzlab-reviewer.md) and
   follow it exactly (independence rule, inputs, six dimensions, routing).
2. Produce `<project>/review/review_report_r<N>.json` per
   `templates/review_report.schema.json` plus a short chat summary.

## Step 6.3 — routed fixes

Dispatch by each issue's `route_to`, fixing ONLY affected pages:

| route_to | Fix action |
|---|---|
| Strategist | Revise `slide_briefs.json` / outline for the listed pages; re-run `check_slide_focus.py --briefs` |
| 知识库检索 | Re-run asset retrieval for the listed pages; update `asset_sources.json` |
| Executor | Regenerate ONLY the listed SVG pages; re-run both Gate-B checks on them |
| 质量检查器 | Fix the concrete technical error; re-run `svg_quality_checker.py` |
| 人工 | STOP and present the question to the user — never auto-decide facts, permissions or sensitive content |

After fixes, re-run `svg_quality_checker.py` + `check_slide_focus.py --svg` —
the fix MUST NOT introduce new technical errors.

## Convergence (no infinite loops)

- At most **2** automatic review rounds.
- Export allowed only when: critical = 0, major = 0 or human-waived,
  total_score ≥ 85, and no new technical errors after fixes.
- Two consecutive rounds without meaningful improvement (total score gain < 5)
  → stop and escalate to a human with both reports.
- `standard` mode runs round 1 only; `verdict: revise` issues are fixed in
  6.3 and the deck proceeds once convergence criteria are met.
- `draft` mode skips 6.2/6.3 entirely.
