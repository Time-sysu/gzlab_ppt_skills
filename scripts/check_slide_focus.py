#!/usr/bin/env python3
"""check_slide_focus.py — Guangzhou Laboratory page-focus checker.

Two gates (see references/gzlab-content-rules.md):

  --briefs   Validate <project>/slide_briefs.json against the content contract
             (run after Strategist output, BEFORE SVG generation).
  --svg      Measure generated svg_output/*.svg against rhythm text budgets,
             card-wall and visual-focus heuristics (run with svg_quality_checker).

Exit code: 1 when any E-level finding exists, else 0. W-level findings are
reported but non-blocking. Stdlib only — no third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = SKILL_DIR / "templates" / "slide_briefs.schema.json"

# Rhythm text budgets (references/gzlab-content-rules.md §3)
RHYTHM_BUDGET = {"anchor": 120, "breathing": 260, "dense": 650}
OVERAGE_TOLERANCE = 1.10  # E10 fires only beyond budget * 1.10

# Conclusion-style title rule: banned label-style titles on content pages (R7)
BANNED_TITLES = {
    "项目背景", "研究背景", "背景", "技术路线", "研究内容", "研究方案",
    "工作汇报", "工作总结", "工作总结汇报", "目录", "致谢", "总结",
    "项目介绍", "项目概述", "进展情况", "下一步计划", "参考文献",
}

VISUAL_GROUP_IDS = ("hero", "figure-", "image", "img-", "kpi")
CARD_GROUP_ID = "card"


class Finding:
    def __init__(self, code: str, level: str, page: str, message: str, action: str, route: str):
        self.code, self.level, self.page = code, level, page
        self.message, self.action, self.route = message, action, route

    def as_dict(self) -> dict:
        return {
            "code": self.code, "level": self.level, "page": self.page,
            "message": self.message, "action": self.action, "route_to": self.route,
        }


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _text_weight(text: str) -> float:
    """CJK chars count 1, others 0.5 (approximate visual weight)."""
    cjk = sum(1 for ch in text if "一" <= ch <= "鿿" or "　" <= ch <= "〿" or "＀" <= ch <= "￯")
    return cjk + (len(text) - cjk) * 0.5


def _svg_text(svg: str) -> str:
    svg = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", svg, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", svg)


def _brief_total_chars(page: dict) -> float:
    parts = [page.get("takeaway", ""), page.get("page_question", "")]
    parts += [str(x) for x in page.get("supporting_evidence") or []]
    return _text_weight(" ".join(p for p in parts if p))


# ---------------------------------------------------------------------------
# Gate A: briefs validation
# ---------------------------------------------------------------------------

def check_briefs(project: Path) -> list[Finding]:
    findings: list[Finding] = []
    briefs_path = project / "slide_briefs.json"
    if not briefs_path.is_file():
        return [Finding("E00", "E", "-", "slide_briefs.json not found in project root",
                        "Strategist writes slide_briefs.json before any SVG generation",
                        "Strategist")]
    data = _load_json(briefs_path)
    if not isinstance(data, dict) or not isinstance(data.get("pages"), list):
        return [Finding("E00", "E", "-", "slide_briefs.json is not valid JSON with a pages array",
                        "Fix the file against templates/slide_briefs.schema.json", "Strategist")]

    pages = [p for p in data["pages"] if isinstance(p, dict)]
    seen_ids: list[str] = []

    for page in pages:
        pid = str(page.get("page_id") or "P??")
        seen_ids.append(pid)
        ptype = page.get("page_type", "content")

        # E01 — one question, one takeaway (R1)
        if not page.get("page_question") or not page.get("takeaway"):
            findings.append(Finding("E01", "E", pid,
                                    "page_question or takeaway missing/empty — every page needs exactly one question and one conclusion",
                                    "Rewrite the brief with a single question and a single conclusion", "Strategist"))
        # E02 — takeaway length
        takeaway = page.get("takeaway") or ""
        if len(takeaway) > 120:
            findings.append(Finding("E02", "E", pid,
                                    f"takeaway is {len(takeaway)} chars (>120) — conclusion must be one sentence",
                                    "Shorten to a single conclusion sentence; move detail to notes_hint", "Strategist"))
        # E03 — at most 3 supporting points (R2)
        evidence = page.get("supporting_evidence") or []
        if len(evidence) > int(page.get("max_points") or 3):
            findings.append(Finding("E03", "E", pid,
                                    f"{len(evidence)} supporting points (>3)",
                                    "Delete secondary points or split the page; never shrink fonts to fit", "Strategist"))
        # E04 — exactly one primary visual (R3)
        if page.get("max_primary_visuals") != 1:
            findings.append(Finding("E04", "E", pid,
                                    "max_primary_visuals must be 1 — one page has one visual focus",
                                    "Set max_primary_visuals to 1 and name the single primary_visual", "Strategist"))
        # E05 — real-asset pages must carry an asset query (R9)
        if page.get("needs_real_asset") and not page.get("asset_query"):
            findings.append(Finding("E05", "E", pid,
                                    "needs_real_asset=true but asset_query is empty",
                                    "Add an asset_query for the GZLab knowledge base retrieval", "Strategist"))
        # W01 — conclusion-style title (R7)
        if ptype == "content":
            title_core = re.sub(r"[：:，,。\s].*$", "", takeaway).strip()
            if title_core in BANNED_TITLES or takeaway.strip() in BANNED_TITLES:
                findings.append(Finding("W01", "W", pid,
                                        f"'{title_core}' is a section label, not a conclusion",
                                        "Rewrite the title as a conclusion sentence", "Strategist"))
        # W02 — anchor page loaded like a dense page (R8)
        if page.get("rhythm") == "anchor" and (len(evidence) >= 3 and _brief_total_chars(page) > 100):
            findings.append(Finding("W02", "W", pid,
                                    "anchor page carries dense-page content — anchor pages are for core statements, photos and big numbers",
                                    "Reduce evidence or reclassify the page rhythm as dense with justification", "Strategist"))
        # W06 — asset provenance placeholder (asset stage fills asset_sources.json)
        if page.get("needs_real_asset") and not (project / "asset_sources.json").is_file():
            findings.append(Finding("W06", "W", pid,
                                    "needs_real_asset=true but asset_sources.json does not exist yet",
                                    "Run the knowledge-base retrieval before Executor; record provenance", "知识库检索"))

    # E07 — page id sequence has no gaps
    nums = []
    for pid in seen_ids:
        m = re.fullmatch(r"P(\d{2})", pid)
        if m:
            nums.append(int(m.group(1)))
    if nums and nums != list(range(nums[0], nums[0] + len(nums))):
        findings.append(Finding("E07", "E", "-",
                                f"page_id sequence has gaps or duplicates: {seen_ids}",
                                "Renumber pages P01..Pn to match the design spec outline", "Strategist"))

    # W07 — rhythm cross-check against spec_lock.md (best effort)
    spec_lock = project / "spec_lock.md"
    if spec_lock.is_file():
        lock_text = spec_lock.read_text(encoding="utf-8", errors="ignore")
        for page in pages:
            pid = page.get("page_id")
            rhythm = page.get("rhythm")
            if not pid or not rhythm:
                continue
            for line in lock_text.splitlines():
                if pid in line and re.search(r"anchor|dense|breathing", line):
                    if rhythm not in line:
                        findings.append(Finding("W07", "W", pid,
                                                f"brief rhythm '{rhythm}' differs from spec_lock.md entry",
                                                "Align slide_briefs.json and spec_lock.md page_rhythm", "Strategist"))
                    break
    return findings


# ---------------------------------------------------------------------------
# Gate B: generated SVG measurement
# ---------------------------------------------------------------------------

def check_svg(project: Path) -> list[Finding]:
    findings: list[Finding] = []
    svg_dir = project / "svg_output"
    if not svg_dir.is_dir():
        return [Finding("E08", "E", "-", "svg_output/ not found — run Executor first",
                        "Generate pages before Gate B", "Executor")]

    briefs = _load_json(project / "slide_briefs.json") or {}
    brief_by_id = {p.get("page_id"): p for p in briefs.get("pages", []) if isinstance(p, dict)}
    asset_sources = _load_json(project / "asset_sources.json") or {}
    sourced_pages = {
        str(a.get("page_id"))
        for a in (asset_sources.get("assets") or [])
        if isinstance(a, dict) and (a.get("file_id") or a.get("lexiang_file_id") or a.get("local_path"))
    }

    svgs = sorted(p for p in svg_dir.glob("*.svg") if p.is_file())
    for index, svg_path in enumerate(svgs, start=1):
        pid = f"P{index:02d}"
        brief = brief_by_id.get(pid) or {}
        rhythm = brief.get("rhythm", "dense")
        ptype = brief.get("page_type", "content")
        raw = svg_path.read_text(encoding="utf-8", errors="ignore")

        # E10 / W03 — text budget by rhythm (R4)
        if ptype == "content":
            weight = _text_weight(_svg_text(raw))
            budget = RHYTHM_BUDGET.get(rhythm, RHYTHM_BUDGET["dense"])
            if weight > budget * OVERAGE_TOLERANCE:
                findings.append(Finding("E10", "E", pid,
                                        f"page text ≈{int(weight)} chars exceeds {rhythm} budget {budget}",
                                        "Delete secondary content or split the page — never shrink fonts", "Strategist"))
            elif weight > budget:
                findings.append(Finding("W03", "W", pid,
                                        f"page text ≈{int(weight)} chars near {rhythm} budget {budget}",
                                        "Trim wording or move detail to speaker notes", "Strategist"))

        group_ids = re.findall(r'<g[^>]*\bid="([^"]+)"', raw)
        card_count = sum(1 for g in group_ids if g.lower().startswith(CARD_GROUP_ID))
        visual_ids = [g for g in group_ids if g.lower().startswith(VISUAL_GROUP_IDS)]

        # W05 — card wall on anchor/breathing pages (R8)
        if rhythm in ("anchor", "breathing") and card_count >= 3:
            findings.append(Finding("W05", "W", pid,
                                    f"{card_count} card groups on a {rhythm} page — card-wall pattern",
                                    "Recompose around the single takeaway and one primary visual", "Executor"))
        # E11 — multiple competing visual centers (R3)
        if len(visual_ids) > 2:
            findings.append(Finding("E11", "E", pid,
                                    f"{len(visual_ids)} primary-visual candidates ({', '.join(visual_ids[:4])}) — competing visual centers",
                                    "Keep one primary visual; demote or remove the rest", "Executor"))
        # E06 — real-asset page without provenance after generation (R9)
        if brief.get("needs_real_asset") and pid not in sourced_pages:
            findings.append(Finding("E06", "E", pid,
                                    "page requires real GZLab evidence but asset_sources.json has no sourced asset for it",
                                    "Re-run knowledge-base retrieval or escalate to the user", "知识库检索"))
    return findings


# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", help="PPT Master project directory")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--briefs", action="store_true", help="Gate A: validate slide_briefs.json")
    group.add_argument("--svg", action="store_true", help="Gate B: measure svg_output pages")
    parser.add_argument("--json", dest="json_out", help="Write findings JSON to this path")
    args = parser.parse_args()

    project = Path(args.project_dir).resolve()
    if not project.is_dir():
        print(f"project directory not found: {project}", file=sys.stderr)
        return 2

    findings = check_briefs(project) if args.briefs else check_svg(project)

    for f in findings:
        print(f"[{f.level}][{f.code}] {f.page}: {f.message}")
        print(f"    → action: {f.action} | route: {f.route}")
    errors = [f for f in findings if f.level == "E"]
    warnings = [f for f in findings if f.level == "W"]
    print(f"\ncheck_slide_focus ({'briefs' if args.briefs else 'svg'}): "
          f"{len(errors)} error(s), {len(warnings)} warning(s)")

    if args.json_out:
        out = Path(args.json_out)
        out.write_text(json.dumps({
            "gate": "briefs" if args.briefs else "svg",
            "errors": len(errors), "warnings": len(warnings),
            "findings": [f.as_dict() for f in findings],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
