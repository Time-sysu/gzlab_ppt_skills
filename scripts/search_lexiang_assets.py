#!/usr/bin/env python3
"""search_lexiang_assets.py — hot retrieval from the reviewed lexiang asset library.

Implements `search_gzlab_assets` from references/gzlab-asset-retrieval.md §5:
  1. NL query → filters via parse_asset_query.py (synonyms + option key IDs);
  2. hard filters auto-injected: 审核状态=已审核, 有效状态=有效, 允许用途=<intended_use>
     (references/gzlab-knowledge-base.md §3 — never relaxed);
  3. POST /kb/entries/search with filters.properties (AND-combined, option key IDs);
  4. media-type hint post-filter by file extension; orientation_hint is returned
     for the caller to post-check with analyze_images.py;
  5. permission failures return EMPTY results, never error details.

Usage:
  python3 search_lexiang_assets.py "冷冻电镜平台的横版实景图" \
      --intended-use 项目申报 --max-results 5 --user-identity zhangjie
  python3 search_lexiang_assets.py ... --out candidates.json

Exit codes: 0 ok (possibly 0 candidates), 1 config/permission error, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse_asset_query  # noqa: E402
from lexiang_openapi_client import (  # noqa: E402
    LexiangClient, LexiangError, LexiangPermissionError, load_contract,
)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff"}
VIDEO_EXTS = {".mp4", ".mov", ".wmv", ".avi", ".mkv", ".flv", ".webm", ".m4v"}


def _hard_filters(contract: dict, intended_use: str | None) -> list[dict]:
    """审核状态=已审核 + 有效状态=有效 + 允许用途=<intended_use> (option key IDs)."""
    def opt(field_name: str, label: str) -> str | None:
        for f in contract.get("fields", []):
            if f.get("name") == field_name:
                for o in f.get("options", []):
                    if o.get("label") == label:
                        return o.get("value")
        return None

    props = []
    review = opt("审核状态", "已审核")
    valid = opt("有效状态", "有效")
    if review:
        props.append({"id": _field_id(contract, "审核状态"), "keys": [review]})
    if valid:
        props.append({"id": _field_id(contract, "有效状态"), "keys": [valid]})
    if intended_use:
        use = opt("允许用途", intended_use)
        if use:
            props.append({"id": _field_id(contract, "允许用途"), "keys": [use]})
    return props


def _field_id(contract: dict, name: str) -> str | None:
    for f in contract.get("fields", []):
        if f.get("name") == name:
            return f.get("field_id")
    return None


def _fetch_entries(client: LexiangClient, keyword: str, properties: list[dict],
                   limit: int) -> list[dict]:
    resp = client.search_entries(keyword=keyword, space_id=client.cfg["space_id"],
                                 properties=properties, limit=limit)
    entries = resp.get("data") or []
    if isinstance(entries, dict):  # defensive: some APIs wrap lists
        entries = entries.get("items") or []
    return entries


def search_assets(query: str, intended_use: str | None, max_results: int,
                  client: LexiangClient, contract: dict) -> dict:
    parsed = parse_asset_query.parse(query, intended_use, contract)
    properties = _hard_filters(contract, intended_use)
    for field_name, values in (parsed.get("filters_resolved") or {}).items():
        fid = _field_id(contract, field_name)
        if fid and values:
            properties.append({"id": fid, "keys": values})

    # Leftover semantics go to the 内容描述 TEXT filter (fuzzy) — the generic
    # `keyword` only matches entry titles, which are asset IDs in this KB and
    # would AND-filter everything away (verified live 2026-09-13). Relaxation
    # chain (hard filters NEVER relax, gzlab-knowledge-base.md §3):
    #   1) properties + 内容描述~leftover
    #   2) properties + title keyword
    #   3) properties only — leftover text is a relevance constraint, droppable
    leftover = " ".join(parsed.get("leftover_terms") or [])
    desc_fid = _field_id(contract, "内容描述")
    keyword_used = ""
    relaxations: list[str] = []
    entries: list[dict] = []
    if leftover and desc_fid:
        entries = _fetch_entries(client, "", properties + [{"id": desc_fid, "keys": [leftover]}],
                                 max_results * 3)
        keyword_used = f"内容描述~{leftover}"
    if not entries and leftover:
        entries = _fetch_entries(client, leftover, properties, max_results * 3)
        keyword_used = leftover
        if entries:
            relaxations.append("内容描述 fuzzy miss → title keyword")
    if not entries and leftover:
        entries = _fetch_entries(client, "", properties, max_results * 3)
        keyword_used = "(property-only)"
        if entries:
            relaxations.append(f"text constraint '{leftover}' relaxed — property-only pass")

    # Extension post-filter is a LEGACY fallback — only when the query did not
    # resolve to a real 素材类型 filter (field exists since 2026-09-13).
    media_hints = [] if (parsed.get("filters") or {}).get("素材类型") else (parsed.get("media_type_hint") or [])
    candidates = []
    for item in entries:
        attrs = item.get("attributes") or {}
        name = attrs.get("name") or ""
        ext = Path(name).suffix.lower()
        if "图片" in media_hints and "视频" not in media_hints and ext and ext not in IMAGE_EXTS:
            continue
        if "视频" in media_hints and ext and ext not in VIDEO_EXTS:
            continue
        candidates.append({
            "entry_id": item.get("id"),
            "name": name,
            "entry_type": attrs.get("entry_type"),
            "extension": ext or None,
            "edited_at": attrs.get("updated_at") or attrs.get("edited_at"),
        })
        if len(candidates) >= max_results:
            break

    return {
        "query": query,
        "intended_use": intended_use,
        "hard_filters_injected": ["审核状态=已审核", "有效状态=有效"]
        + ([f"允许用途={intended_use}"] if intended_use else []),
        "applied_property_filters": parsed.get("filters") or {},
        "keyword_used": keyword_used,
        "orientation_hint": parsed.get("orientation_hint"),
        "media_type_hint": media_hints,
        "missing_field_warnings": parsed.get("missing_field_warnings") or [],
        "relaxations": relaxations,
        "candidates": candidates,
        "candidate_count": len(candidates),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="自然语言素材需求")
    parser.add_argument("--intended-use", help="本次PPT用途（注入允许用途硬过滤）")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--user-identity", help="调用用户身份（记录于输出，权限由乐享侧强制执行）")
    parser.add_argument("--out", help="结果写入 JSON 文件")
    args = parser.parse_args()

    contract = load_contract()
    try:
        client = LexiangClient()
        result = search_assets(args.query, args.intended_use, args.max_results,
                               client, contract)
    except LexiangPermissionError as exc:
        # red line: never leak restricted content; empty result + terse note
        result = {"query": args.query, "candidates": [], "candidate_count": 0,
                  "note": f"permission denied by lexiang — no content returned ({exc.status})"}
        text = json.dumps(result, ensure_ascii=False, indent=2)
        print(text, file=sys.stderr)
        return 1
    except LexiangError as exc:
        print(f"search failed: {exc}", file=sys.stderr)
        return 1

    result["user_identity"] = args.user_identity
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
