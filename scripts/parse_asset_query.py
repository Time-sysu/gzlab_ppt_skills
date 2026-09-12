#!/usr/bin/env python3
"""parse_asset_query.py — natural language → lexiang asset filter conditions.

Rule-based converter implementing references/gzlab-asset-retrieval.md §2.
Synonyms and option value IDs come from templates/lexiang_properties.schema.json
(single source of truth, mirrors the live KB). Hard filters (审核状态=已审核,
有效状态=有效, 允许用途) are NOT added here — the retrieval workflow injects
them (see gzlab-knowledge-retrieval.md Step R3).

Usage:
  python3 parse_asset_query.py "冷冻电镜平台的横版实景图，用于项目申报"
  python3 parse_asset_query.py "..." --intended-use 项目申报 --json-out asset_request_fragment.json

Output: JSON with semantic_query, hard_filters_applied (informational),
filters (relevance fields, option labels), filters_resolved (option value IDs
ready for the OpenAPI), leftover_terms (query words no rule consumed — feed
them to 内容描述 fuzzy search), missing_field_warnings.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PROPERTIES_PATH = SKILL_DIR / "templates" / "lexiang_properties.schema.json"

# Orientation cues are not lexiang fields yet (planned_missing_fields); they are
# returned separately so the caller can post-filter by aspect ratio.
ORIENTATION_RULES = {
    "横版": ["横版", "横图", "宽图", "横版照片", "横幅"],
    "竖版": ["竖版", "竖图", "竖版照片", "竖幅"],
    "方形": ["方形", "方图"],
    "全景": ["全景"],
}

# Media-type cues → file-extension groups (素材类型 field is not configured yet;
# see lexiang_properties.schema.json planned_missing_fields).
MEDIA_TYPE_RULES = {
    "图片": ["图片", "照片", "配图", "实景图", "影像"],
    "视频": ["视频", "录像", "片段"],
    "视频关键帧": ["关键帧", "截帧", "视频截图"],
}


def _load_properties() -> dict:
    return json.loads(PROPERTIES_PATH.read_text(encoding="utf-8"))


def _option_index(props: dict) -> dict[str, dict[str, dict[str, str]]]:
    """field name -> {label -> value, child_label -> value}."""
    index: dict[str, dict[str, dict[str, str]]] = {}
    for field in props.get("fields", []):
        name = field.get("name")
        if not name:
            continue
        label_map: dict[str, str] = {}

        def walk(options):
            for opt in options or []:
                label_map[opt["label"]] = opt["value"]
                walk(opt.get("children"))

        walk(field.get("options"))
        index[name] = label_map
    return index


def parse(query: str, intended_use: str | None, props: dict) -> dict:
    option_index = _option_index(props)
    filters: dict[str, list[str]] = {}
    resolved: dict[str, list[str]] = {}
    consumed_spans: list[tuple[int, int]] = []
    warnings: list[str] = []

    def consume(term: str, field: str, label: str):
        filters.setdefault(field, [])
        if label not in filters[field]:
            filters[field].append(label)
        value = option_index.get(field, {}).get(label)
        if value:
            resolved.setdefault(field, [])
            if value not in resolved[field]:
                resolved[field].append(value)
        for m in re.finditer(re.escape(term), query):
            consumed_spans.append(m.span())

    # 1) synonym rules from the property contract
    for field in props.get("fields", []):
        name = field.get("name")
        synonyms = field.get("synonyms") or {}
        for term, label in sorted(synonyms.items(), key=lambda kv: -len(kv[0])):
            if term and term in query:
                if label in option_index.get(name, {}):
                    consume(term, name, label)
                else:
                    warnings.append(f"synonym '{term}' -> '{label}' not an option of {name}")

    # 2) direct option-label matches (query literally names an option)
    for field_name, label_map in option_index.items():
        for label in sorted(label_map, key=len, reverse=True):
            if len(label) >= 2 and label in query and label not in filters.get(field_name, []):
                consume(label, field_name, label)

    # 3) orientation / media type (fields not yet configured in the KB)
    orientation = None
    for label, cues in ORIENTATION_RULES.items():
        hit = next((c for c in cues if c in query), None)
        if hit:
            orientation = label
            for m in re.finditer(re.escape(hit), query):
                consumed_spans.append(m.span())
            break
    media_types = []
    for label, cues in MEDIA_TYPE_RULES.items():
        hit = next((c for c in cues if c in query), None)
        if hit:
            media_types.append(label)
            for m in re.finditer(re.escape(hit), query):
                consumed_spans.append(m.span())

    # 4) leftover terms → 内容描述 fuzzy search
    mask = list(query)
    for start, end in consumed_spans:
        for i in range(start, end):
            mask[i] = " "
    leftover = re.sub(r"[，。、；：\s]+", " ", "".join(mask)).strip()
    leftover_terms = [t for t in leftover.split(" ") if len(t) >= 2]

    missing = set(props.get("planned_missing_fields", {}).get("items", []))
    result = {
        "semantic_query": query,
        "filters": filters,
        "filters_resolved": resolved,
        "leftover_terms": leftover_terms,
        "orientation_hint": orientation,
        "media_type_hint": media_types or None,
    }
    if orientation and "图片方向" in missing:
        warnings.append("图片方向 field not configured in KB — post-filter candidates by aspect ratio")
    if media_types and "素材类型" in missing:
        warnings.append("素材类型 field not configured in KB — filter candidates by file extension")
    if intended_use:
        result["intended_use"] = intended_use
        use_value = option_index.get("允许用途", {}).get(intended_use)
        if not use_value:
            warnings.append(f"intended_use '{intended_use}' is not an 允许用途 option")
    result["missing_field_warnings"] = warnings
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="自然语言素材需求")
    parser.add_argument("--intended-use", help="本次PPT用途（注入硬过滤用），如 项目申报")
    parser.add_argument("--json-out", help="将结果写入指定文件")
    args = parser.parse_args()

    props = _load_properties()
    result = parse(args.query, args.intended_use, props)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
