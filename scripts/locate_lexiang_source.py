#!/usr/bin/env python3
"""locate_lexiang_source.py — cold retrieval step 1: locate source documents.

Implements `locate_source_media` from references/gzlab-asset-retrieval.md §5:
lexiang Agent semantic search (POST /v1/ai/search, x-staff-id = user identity)
over the 综合文档库 to find PPT/Word/PDF/video documents — and, when the Agent
answer includes page/timecode hints, pass them through for extract_ppt_assets.py
/ extract_video_keyframes.py. Falls back to keyword entry search when the AI
search yields nothing.

Usage:
  python3 locate_lexiang_source.py "冷冻电镜平台实景照片在哪个PPT里" \
      --document-types pptx,pdf --user-identity zhangjie --out locate.json

Exit codes: 0 ok, 1 error, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lexiang_openapi_client import (  # noqa: E402
    LexiangClient, LexiangError, LexiangPermissionError,
)

DOC_TYPE_EXTS = {
    "pptx": {".pptx", ".ppt"},
    "pdf": {".pdf"},
    "word": {".docx", ".doc", ".wps"},
    "video": {".mp4", ".mov", ".wmv", ".avi", ".mkv", ".flv", ".webm", ".m4v"},
}


def _ext_doc_type(name: str) -> str | None:
    ext = Path(name).suffix.lower()
    for doc_type, exts in DOC_TYPE_EXTS.items():
        if ext in exts:
            return doc_type
    return None


def locate(query: str, document_types: list[str] | None,
           client: LexiangClient, limit: int) -> dict:
    """AI search first; keyword entry search as fallback."""
    hits: list[dict] = []
    ai_error = None
    try:
        resp = client.ai_search(query, limit=limit)
        items = resp.get("data") or resp.get("results") or []
        if isinstance(items, dict):
            items = items.get("items") or items.get("entries") or []
        for item in items:
            attrs = item.get("attributes") or item
            name = attrs.get("name") or attrs.get("title") or ""
            hits.append({
                "entry_id": item.get("id") or attrs.get("id"),
                "name": name,
                "doc_type": _ext_doc_type(name),
                "channel": "ai_search",
                "context": attrs.get("summary") or attrs.get("highlight") or "",
            })
    except LexiangError as exc:  # AI search unavailable → keyword fallback
        ai_error = str(exc)

    if not hits:
        resp = client.search_entries(keyword=query, space_id=client.cfg["space_id"],
                                     limit=limit * 2)
        entries = resp.get("data") or []
        if isinstance(entries, dict):
            entries = entries.get("items") or []
        for item in entries:
            attrs = item.get("attributes") or {}
            name = attrs.get("name") or ""
            if attrs.get("entry_type") == "folder":
                continue
            hits.append({
                "entry_id": item.get("id"),
                "name": name,
                "doc_type": _ext_doc_type(name),
                "channel": "keyword_search",
                "context": "",
            })

    if document_types:
        wanted = set(document_types)
        hits = [h for h in hits if h["doc_type"] in wanted]
    hits = hits[:limit]
    return {
        "query": query,
        "document_types": document_types,
        "ai_search_error": ai_error,
        "sources": hits,
        "source_count": len(hits),
        "next_step": "download_entry() then scripts/extract_ppt_assets.py --pages or "
                     "scripts/extract_video_keyframes.py --timecodes",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="自然语言定位需求")
    parser.add_argument("--document-types", help="限定文档类型，逗号分隔：pptx,pdf,word,video")
    parser.add_argument("--user-identity", help="调用用户身份（AI 搜索经 x-staff-id 强制权限）")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--out", help="结果写入 JSON 文件")
    args = parser.parse_args()

    document_types = ([t.strip() for t in args.document_types.split(",") if t.strip()]
                      if args.document_types else None)
    try:
        client = LexiangClient()
        result = locate(args.query, document_types, client, args.limit)
    except LexiangPermissionError as exc:
        print(f"permission denied by lexiang ({exc.status}) — no content returned",
              file=sys.stderr)
        return 1
    except LexiangError as exc:
        print(f"locate failed: {exc}", file=sys.stderr)
        return 1

    result["user_identity"] = args.user_identity
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
