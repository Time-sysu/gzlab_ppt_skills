#!/usr/bin/env python3
"""Apply one curated Guangzhou Laboratory deck after Confirm UI selection."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import time
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CATALOG_PATH = SKILL_DIR / "templates" / "gzlab_templates.json"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
MANIFEST_NAME = ".selected_template_manifest.json"


class TemplateSelectionError(RuntimeError):
    pass


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplateSelectionError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TemplateSelectionError(f"expected a JSON object: {path}")
    return value


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _catalog_entry(template_id: str) -> dict:
    catalog = _load_json(CATALOG_PATH)
    entries = catalog.get("templates") or []
    for entry in entries:
        if isinstance(entry, dict) and entry.get("id") == template_id:
            return entry
    allowed = ", ".join(str(e.get("id")) for e in entries if isinstance(e, dict))
    raise TemplateSelectionError(f"unknown template_id {template_id!r}; allowed: {allowed}")


def _selected_id(project: Path, explicit_id: str | None) -> str:
    if explicit_id:
        return explicit_id
    result_path = project / "confirm_ui" / "result.json"
    result = _load_json(result_path)
    if result.get("status") != "confirmed":
        raise TemplateSelectionError("confirm_ui/result.json is not confirmed")
    template_id = result.get("template_id")
    if not isinstance(template_id, str) or not template_id:
        raise TemplateSelectionError("confirmed result has no template_id")
    return template_id


def _remove_previous(project: Path) -> None:
    manifest_path = project / "templates" / MANIFEST_NAME
    if not manifest_path.exists():
        return
    manifest = _load_json(manifest_path)
    for item in manifest.get("managed_files") or []:
        if not isinstance(item, str):
            continue
        target = project / item
        if _inside(target, project) and target.is_file():
            target.unlink()
    if manifest_path.exists():
        manifest_path.unlink()


def _rewrite_svg_images(svg_path: Path, image_names: set[str]) -> None:
    text = svg_path.read_text(encoding="utf-8")
    for name in sorted(image_names, key=len, reverse=True):
        escaped = re.escape(name)
        text = re.sub(
            rf'href=(["\'])(?:\.\./images/|\./)?{escaped}\1',
            lambda m: f'href={m.group(1)}../images/{name}{m.group(1)}',
            text,
        )
    svg_path.write_text(text, encoding="utf-8")


def apply_template(project: Path, template_id: str) -> dict:
    entry = _catalog_entry(template_id)
    if entry.get("kind") != "deck":
        raise TemplateSelectionError("only curated kind: deck templates are supported")
    relative_source = entry.get("path")
    if not isinstance(relative_source, str):
        raise TemplateSelectionError("template catalog entry has no path")
    source = (SKILL_DIR / relative_source).resolve()
    deck_root = (SKILL_DIR / "templates" / "decks").resolve()
    if not _inside(source, deck_root) or not source.is_dir():
        raise TemplateSelectionError(f"unsafe or missing template directory: {source}")
    spec = source / "design_spec.md"
    if not spec.exists() or not re.search(r"(?m)^kind:\s*deck\s*$", spec.read_text(encoding="utf-8")):
        raise TemplateSelectionError("selected directory is not a registered deck template")

    templates_dir = project / "templates"
    images_dir = project / "images"
    templates_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    _remove_previous(project)

    managed: list[str] = []
    image_names = {p.name for p in source.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES}
    copied_svgs: list[Path] = []
    for item in source.rglob("*"):
        if not item.is_file():
            continue
        if item.suffix.lower() in IMAGE_SUFFIXES:
            target = images_dir / item.name
        else:
            target = templates_dir / item.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        managed.append(target.relative_to(project).as_posix())
        if target.suffix.lower() == ".svg":
            copied_svgs.append(target)

    for svg_path in copied_svgs:
        _rewrite_svg_images(svg_path, image_names)

    manifest = {
        "template_id": template_id,
        "template_name": entry.get("name_zh") or entry.get("name_en") or template_id,
        "source_path": relative_source,
        "applied_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "managed_files": managed,
    }
    manifest_path = templates_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", help="PPT Master project directory")
    parser.add_argument("--template-id", help="Override confirm_ui/result.json for testing")
    args = parser.parse_args()
    project = Path(args.project_dir).resolve()
    if not project.is_dir():
        raise SystemExit(f"project directory not found: {project}")
    try:
        template_id = _selected_id(project, args.template_id)
        result = apply_template(project, template_id)
    except TemplateSelectionError as exc:
        raise SystemExit(f"Template selection failed: {exc}") from exc
    print(json.dumps({"status": "applied", **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
