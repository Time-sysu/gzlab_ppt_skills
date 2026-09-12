#!/usr/bin/env python3
"""extract_ppt_assets.py — targeted image extraction from source PPTX pages.

Cold-retrieval step (references/gzlab-asset-retrieval.md §4): given a source
PPTX and target page numbers, extract embedded pictures from ONLY those pages,
filtering low-value elements:

- images smaller than --min-side pixels on either side (icons, decorations);
- images repeated on more than --decor-ratio of ALL pages (logos, headers,
  footers, template backgrounds) — detected by SHA-256 of the image blob.

For each kept image we save the ORIGINAL embedded bitmap (highest resolution)
plus a JSON manifest with provenance (来源文件/来源位置) ready for
submit_lexiang_asset.py and asset_sources.json.

Usage:
  python3 extract_ppt_assets.py source.pptx --pages 4,7 --out-dir ./extracted \
      --manifest extracted_manifest.json

Dependency: python-pptx + Pillow (skill requirements.txt).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

IMAGE_PLACEHOLDER_KINDS = ("PICTURE", "PLACEHOLDER_PICTURE")


def _iter_picture_shapes(shapes):
    """Yield picture shapes recursively (walks into groups)."""
    for shape in shapes:
        st = str(getattr(shape, "shape_type", ""))
        if "GROUP" in st:
            yield from _iter_picture_shapes(shape.shapes)
        elif any(k in st for k in IMAGE_PLACEHOLDER_KINDS) or hasattr(shape, "image"):
            try:
                _ = shape.image  # raises when not a picture
                yield shape
            except Exception:
                continue


def _page_image_hashes(prs) -> tuple[dict[int, list[str]], Counter]:
    """Map 1-based page -> [sha256 of each picture blob]; and global hash frequency."""
    page_hashes: dict[int, list[str]] = {}
    freq: Counter = Counter()
    for idx, slide in enumerate(prs.slides, start=1):
        hashes = []
        for shape in _iter_picture_shapes(slide.shapes):
            digest = hashlib.sha256(shape.image.blob).hexdigest()
            hashes.append(digest)
        page_hashes[idx] = hashes
        for h in set(hashes):
            freq[h] += 1
    return page_hashes, freq


def extract(pptx_path: Path, pages: list[int], out_dir: Path,
            min_side: int, decor_ratio: float) -> dict:
    from pptx import Presentation  # deferred import: clear error if missing
    from PIL import Image
    import io

    prs = Presentation(str(pptx_path))
    total = len(prs.slides)
    page_hashes, freq = _page_image_hashes(prs)
    decor_cutoff = max(1, int(total * decor_ratio))
    decor_hashes = {h for h, n in freq.items() if n >= decor_cutoff and total > 2}

    out_dir.mkdir(parents=True, exist_ok=True)
    items, skipped = [], []
    for page in pages:
        if not (1 <= page <= total):
            skipped.append({"page": page, "reason": f"page out of range (deck has {total})"})
            continue
        slide = prs.slides[page - 1]
        seen_on_page: set[str] = set()
        pic_no = 0
        for shape in _iter_picture_shapes(slide.shapes):
            image = shape.image
            digest = hashlib.sha256(image.blob).hexdigest()
            if digest in seen_on_page:
                continue
            seen_on_page.add(digest)
            pic_no += 1
            with Image.open(io.BytesIO(image.blob)) as im:
                width, height = im.size
            if width < min_side or height < min_side:
                skipped.append({"page": page, "sha256": digest[:12],
                                "reason": f"too small ({width}x{height} < {min_side}px) — icon/decoration"})
                continue
            if digest in decor_hashes:
                skipped.append({"page": page, "sha256": digest[:12],
                                "reason": f"appears on >= {decor_cutoff} pages — template/logo element"})
                continue
            ext = image.ext or "png"
            name = f"p{page:02d}_{pic_no}_{digest[:8]}.{ext}"
            target = out_dir / name
            target.write_bytes(image.blob)
            items.append({
                "file": name,
                "kind": "原始嵌入图片",
                "source_page": page,
                "width": width,
                "height": height,
                "orientation": "横版" if width > height else ("竖版" if height > width else "方形"),
                "sha256": digest,
                "crop_hint": {
                    "left": round(getattr(shape, "crop_left", 0) or 0, 4),
                    "top": round(getattr(shape, "crop_top", 0) or 0, 4),
                    "right": round(getattr(shape, "crop_right", 0) or 0, 4),
                    "bottom": round(getattr(shape, "crop_bottom", 0) or 0, 4),
                },
                "suggested_properties": {
                    "来源文件": pptx_path.name,
                    "来源位置": f"PPT 第 {page} 页",
                },
            })
    return {
        "version": 1,
        "source_file": str(pptx_path),
        "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "deck_pages": total,
        "pages_requested": pages,
        "items": items,
        "skipped": skipped,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pptx", help="源 PPTX 文件")
    parser.add_argument("--pages", required=True, help="目标页码（1 起），逗号分隔，如 4,7,12")
    parser.add_argument("--out-dir", required=True, help="抽取图片输出目录")
    parser.add_argument("--manifest", help="清单 JSON 输出路径（默认 <out-dir>/extracted_manifest.json）")
    parser.add_argument("--min-side", type=int, default=200, help="小于该边长的图片视为图标/装饰（默认 200px）")
    parser.add_argument("--decor-ratio", type=float, default=0.5,
                        help="出现在超过该比例页面上的图片视为模板元素（默认 0.5）")
    args = parser.parse_args()

    pptx_path = Path(args.pptx).resolve()
    if not pptx_path.is_file():
        print(f"source PPTX not found: {pptx_path}", file=sys.stderr)
        return 2
    try:
        pages = sorted({int(p) for p in args.pages.split(",") if p.strip()})
    except ValueError:
        print(f"invalid --pages: {args.pages}", file=sys.stderr)
        return 2

    try:
        result = extract(pptx_path, pages, Path(args.out_dir), args.min_side, args.decor_ratio)
    except ImportError as exc:
        print(f"missing dependency: {exc} — pip install python-pptx Pillow", file=sys.stderr)
        return 2

    manifest_path = Path(args.manifest) if args.manifest else Path(args.out_dir) / "extracted_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"kept": len(result["items"]), "skipped": len(result["skipped"]),
                      "manifest": str(manifest_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
