#!/usr/bin/env python3
"""submit_lexiang_asset.py — review-style writeback to the lexiang 待审核区.

Implements `submit_asset_for_review` / `submit_generated_artifact` from
references/gzlab-asset-retrieval.md §5 and workflows/gzlab-asset-writeback.md:

  1. 3-step upload (upload-params → COS PUT → create entry) into the 待审核区
     target subfolder (entry id from templates/lexiang_properties.schema.json
     libraries, or a resolved subfolder name);
  2. fill custom properties (审核状态 is FORCED to 待审核 — automatic writeback
     never publishes; option labels are translated to the update format);
  3. failures are reported as 待回写 — never pretend the asset is in the KB.

Property value rules (official API): text → string; select → label string;
multi-select → [labels]; category → "path/child". This script accepts property
LABELS by field NAME (e.g. {"审核状态": "待审核", "所属项目": ["电镜"]}) and
maps them through the contract — callers never handle raw field IDs.

Usage:
  python3 submit_lexiang_asset.py ./frame_0012.jpg \
      --target-subfolder 文档抽取素材 \
      --properties '{"内容描述":"冷冻电镜操作界面","所属项目":["电镜"],"来源文件":"平台介绍.pptx","来源位置":"PPT 第 4 页","责任人":"张洁"}' \
      --provenance '{"source_file_entry_id":"abc123","source_location":"PPT 第 4 页"}' \
      --user-identity zhangjie

Exit codes: 0 submitted, 1 failed (待回写), 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lexiang_openapi_client import (  # noqa: E402
    LexiangClient, LexiangError, LexiangPermissionError, load_contract,
)

MEDIA_TYPE_BY_EXT = {
    ".mp4": "video", ".mov": "video", ".wmv": "video", ".avi": "video",
    ".mkv": "video", ".flv": "video", ".webm": "video", ".m4v": "video",
    ".mp3": "audio", ".m4a": "audio", ".flac": "audio", ".wav": "audio",
    ".aac": "audio", ".ogg": "audio",
}
VIDEO_ENTRY_EXTS = {".mp4", ".mov", ".wmv", ".avi", ".mkv", ".flv", ".webm", ".m4v"}
# 待审核区 standard subfolders (workflows/gzlab-asset-writeback.md W1)
PENDING_SUBFOLDERS = ["人工上传材料", "文档抽取素材", "AI生成素材", "PPT-master生成成果"]


def _resolve_subfolder_id(client: LexiangClient, contract: dict,
                          subfolder: str | None) -> str:
    """待审核区 root id, or the id of a named subfolder under it."""
    pending_id = contract["space"]["libraries"]["待审核区"]
    if not subfolder:
        return pending_id
    resp = client.list_entries(client.cfg["space_id"], parent_id=pending_id)
    entries = resp.get("data") or []
    if isinstance(entries, dict):
        entries = entries.get("items") or []
    for item in entries:
        if (item.get("attributes") or {}).get("name") == subfolder:
            return item.get("id")
    raise LexiangError(
        f"待审核区 subfolder '{subfolder}' not found — create it in lexiang first "
        f"(expected one of: {', '.join(PENDING_SUBFOLDERS)})")


def _map_properties(contract: dict, props_by_name: dict) -> tuple[dict, list[str]]:
    """field-name/label → {field_id: value-for-update}; returns (values, warnings)."""
    fields = {f.get("name"): f for f in contract.get("fields", [])}
    values: dict = {}
    warnings: list[str] = []
    for name, raw in props_by_name.items():
        field = fields.get(name)
        if not field:
            warnings.append(f"unknown field '{name}' — skipped (not in contract)")
            continue
        ftype, fid = field.get("field_type"), field.get("field_id")
        options = {o.get("label") for o in field.get("options", [])}
        if ftype == "text":
            values[fid] = str(raw)
        elif ftype == "select":
            label = str(raw)
            if label not in options:
                warnings.append(f"'{label}' is not an option of {name} — sent anyway")
            values[fid] = label
        elif ftype == "multi_select":
            labels = [str(x) for x in (raw if isinstance(raw, list) else [raw])]
            unknown = [x for x in labels if x not in options]
            if unknown:
                warnings.append(f"{unknown} not options of {name} — sent anyway")
            values[fid] = labels
        elif ftype == "category":
            labels = [str(x) for x in (raw if isinstance(raw, list) else [raw])]
            values[fid] = "/".join(labels) if len(labels) > 1 else labels[0]
    return values, warnings


def submit(file_path: Path, target_subfolder: str | None,
           properties: dict, provenance: dict | None,
           client: LexiangClient, contract: dict) -> dict:
    parent_id = _resolve_subfolder_id(client, contract, target_subfolder)
    ext = file_path.suffix.lower()
    media_type = MEDIA_TYPE_BY_EXT.get(ext, "file")
    entry_type = "video" if ext in VIDEO_ENTRY_EXTS else "file"

    # 审核状态 is forced — automatic writeback NEVER publishes
    properties = dict(properties)
    forced = properties.get("审核状态") != "待审核"
    properties["审核状态"] = "待审核"
    values, warnings = _map_properties(contract, properties)
    if forced:
        warnings.append("审核状态 forced to 待审核 — automatic writeback never publishes")

    state = client.upload_file(file_path, media_type=media_type)
    entry_id = client.create_file_entry(
        client.cfg["space_id"], parent_id, file_path.name, state, entry_type=entry_type)
    prop_result = client.update_properties(entry_id, values)

    return {
        "status": "submitted",
        "entry_id": entry_id,
        "target_subfolder": target_subfolder or "待审核区(根)",
        "file": file_path.name,
        "properties_written": {k: v for k, v in properties.items()},
        "warnings": warnings,
        "provenance": provenance or {},
        "submitted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "property_api_response": prop_result.get("data") is not None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="待提交文件")
    parser.add_argument("--target-subfolder",
                        help=f"待审核区子目录：{' / '.join(PENDING_SUBFOLDERS)}（缺省为待审核区根）")
    parser.add_argument("--properties", required=True,
                        help="属性 JSON（按字段名+选项 label，如 {\"内容描述\":\"...\",\"所属项目\":[\"电镜\"]}）")
    parser.add_argument("--provenance", help="来源血缘 JSON（source_file_entry_id / source_location / ai_generation）")
    parser.add_argument("--user-identity", help="提交人身份（x-staff-id 缺省回退到 LEXIANG_STAFF_ID）")
    parser.add_argument("--out", help="结果写入 JSON 文件")
    args = parser.parse_args()

    file_path = Path(args.file).resolve()
    if not file_path.is_file():
        print(f"file not found: {file_path}", file=sys.stderr)
        return 2
    try:
        properties = json.loads(args.properties)
        provenance = json.loads(args.provenance) if args.provenance else None
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2

    contract = load_contract()
    try:
        client = LexiangClient()
        result = submit(file_path, args.target_subfolder, properties,
                        provenance, client, contract)
    except LexiangPermissionError as exc:
        result = {"status": "待回写", "file": str(file_path),
                  "error": f"permission denied ({exc.status}) — {exc}"}
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    except LexiangError as exc:
        result = {"status": "待回写", "file": str(file_path), "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    result["user_identity"] = args.user_identity
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
