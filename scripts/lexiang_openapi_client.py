#!/usr/bin/env python3
"""lexiang_openapi_client.py — lexiang OpenAPI client for the GZLab access layer.

Implements the stable interface contract from
references/gzlab-asset-retrieval.md §5 against the documented lexiang OpenAPI
(https://lexiang.tencent.com/wiki/api/):

  POST /cgi-bin/token                                   app credentials → Bearer (2h, cached)
  POST /cgi-bin/v1/kb/entries/search                    keyword + filters.properties[{id, keys}]
  GET  /cgi-bin/v1/kb/entries                           list children (space_id, parent_id)
  GET  /cgi-bin/v1/kb/entries/{id}                      detail incl. links.download (60 min)
  POST /cgi-bin/v1/kb/files/upload-params               step 1 of file upload → state
  PUT  <upload_url>                                     step 2: binary to Tencent COS
  POST /cgi-bin/v1/kb/entries?state=&space_id=          step 3: create file entry
  GET/PUT /cgi-bin/v1/kb/entries/{id}/properties/values custom property values
  POST /cgi-bin/v1/ai/search                            lexiang Agent semantic search

Config (environment variables — real values NEVER enter the repo):
  LEXIANG_APP_KEY, LEXIANG_APP_SECRET   app credentials (required)
  LEXIANG_STAFF_ID                      calling member account (x-staff-id; required
                                        for writes and AI search — the user identity
                                        whose permission is enforced, see
                                        references/gzlab-knowledge-base.md §3)
  LEXIANG_SPACE_ID                      default target space (falls back to the
                                        contract in templates/lexiang_properties.schema.json)
  LEXIANG_BASE_URL                      default https://lxapi.lexiangla.com
  LEXIANG_TOKEN_CACHE                   default ~/.gzlab_ppt/lexiang_token.json

Stdlib only (urllib) — no third-party dependencies.
CLI self-check:  python3 lexiang_openapi_client.py --check
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PROPERTIES_PATH = SKILL_DIR / "templates" / "lexiang_properties.schema.json"
DEFAULT_BASE_URL = "https://lxapi.lexiangla.com"
TOKEN_EXPIRY_MARGIN = 300  # refresh 5 min early

_EXT_BY_MIME = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
    "image/gif": ".gif", "image/bmp": ".bmp", "image/tiff": ".tiff",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "video/mp4": ".mp4", "video/quicktime": ".mov",
}


class LexiangError(RuntimeError):
    """API-level error. `status` is the HTTP code when available."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class LexiangPermissionError(LexiangError):
    """401/403 — the calling identity lacks permission; callers must NOT retry
    with elevated credentials (references/gzlab-knowledge-base.md §3 red line)."""


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

def load_contract() -> dict:
    return json.loads(PROPERTIES_PATH.read_text(encoding="utf-8"))


def load_config() -> dict:
    contract = load_contract()
    cfg = {
        "app_key": os.environ.get("LEXIANG_APP_KEY", "").strip(),
        "app_secret": os.environ.get("LEXIANG_APP_SECRET", "").strip(),
        "staff_id": os.environ.get("LEXIANG_STAFF_ID", "").strip(),
        "space_id": os.environ.get("LEXIANG_SPACE_ID", "").strip()
        or contract["space"]["space_id"],
        "base_url": os.environ.get("LEXIANG_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        "token_cache": Path(os.environ.get(
            "LEXIANG_TOKEN_CACHE",
            str(Path.home() / ".gzlab_ppt" / "lexiang_token.json"))),
    }
    return cfg


def require_config(cfg: dict, need_staff: bool = False) -> None:
    missing = [k for k in ("app_key", "app_secret") if not cfg.get(k)]
    if need_staff and not cfg.get("staff_id"):
        missing.append("staff_id (LEXIANG_STAFF_ID — the user identity for permission checks)")
    if missing:
        raise LexiangError(
            "missing lexiang config: " + ", ".join(missing) +
            " — set environment variables (see .env.example); never hard-code credentials")


# ---------------------------------------------------------------------------
# client
# ---------------------------------------------------------------------------

class LexiangClient:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or load_config()
        require_config(self.cfg)
        self._token: str | None = None
        self._token_exp: float = 0

    # -- token (2h validity, cached to disk) --------------------------------

    def token(self) -> str:
        now = time.time()
        if self._token and now < self._token_exp:
            return self._token
        cache = self.cfg["token_cache"]
        if cache.is_file():
            try:
                saved = json.loads(cache.read_text(encoding="utf-8"))
                if saved.get("access_token") and now < saved.get("expires_at", 0):
                    self._token, self._token_exp = saved["access_token"], saved["expires_at"]
                    return self._token
            except (OSError, json.JSONDecodeError):
                pass
        body = {
            "grant_type": "client_credentials",
            "app_key": self.cfg["app_key"],
            "app_secret": self.cfg["app_secret"],
        }
        resp = self._raw_request("POST", f"{self.cfg['base_url']}/cgi-bin/token", body)
        token = resp.get("access_token")
        if not token:
            raise LexiangError(f"token endpoint returned no access_token: {resp}")
        self._token = token
        self._token_exp = now + int(resp.get("expires_in", 7200)) - TOKEN_EXPIRY_MARGIN
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(
                {"access_token": token, "expires_at": self._token_exp}), encoding="utf-8")
        except OSError:
            pass  # caching is best-effort
        return token

    # -- raw HTTP ------------------------------------------------------------

    def _raw_request(self, method: str, url: str, body: dict | None = None,
                     headers: dict | None = None, binary: bytes | None = None) -> dict:
        data = binary if binary is not None else (
            json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None)
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json; charset=utf-8")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            if exc.code in (401, 403):
                raise LexiangPermissionError(
                    f"{exc.code} from {url}: {detail}", status=exc.code) from exc
            raise LexiangError(f"HTTP {exc.code} from {url}: {detail}", status=exc.code) from exc
        except urllib.error.URLError as exc:
            raise LexiangError(f"network error calling {url}: {exc.reason}") from exc
        if not payload:
            return {}
        try:
            return json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError:
            return {"_raw": payload.decode("utf-8", errors="replace")}

    def api(self, method: str, path: str, body: dict | None = None,
            query: dict | None = None, staff_id: str | None = None) -> dict:
        url = f"{self.cfg['base_url']}{path}"
        if query:
            url += "?" + urllib.parse.urlencode({k: v for k, v in query.items() if v is not None})
        headers = {"Authorization": f"Bearer {self.token()}"}
        if staff_id:
            headers["x-staff-id"] = staff_id
        return self._raw_request(method, url, body, headers)

    # -- contract wrappers (gzlab-asset-retrieval.md §5) ---------------------

    def search_entries(self, keyword: str, space_id: str,
                       properties: list[dict] | None = None,
                       limit: int = 20, page_token: str = "",
                       staff_id: str | None = None) -> dict:
        """POST /kb/entries/search — property filters are AND-combined;
        select/category keys are option key IDs (from the contract file).
        Requires a member identity (x-staff-id) — verified 2026-09-13:
        without StaffID the endpoint returns 403 "用户身份获取失败"."""
        body: dict = {"keyword": keyword, "space_id": space_id,
                      "limit": limit, "page_token": page_token}
        if properties:
            body["filters"] = {"properties": properties}
        staff = staff_id or self.cfg.get("staff_id")
        if not staff:
            raise LexiangError("search requires LEXIANG_STAFF_ID (x-staff-id)")
        return self.api("POST", "/cgi-bin/v1/kb/entries/search", body, staff_id=staff)

    def list_entries(self, space_id: str, parent_id: str | None = None,
                     limit: int = 100, page_token: str | None = None) -> dict:
        query: dict = {"space_id": space_id, "limit": limit}
        if parent_id:
            query["parent_id"] = parent_id
        if page_token:
            query["page_token"] = page_token
        return self.api("GET", "/cgi-bin/v1/kb/entries", query=query)

    def describe_entry(self, entry_id: str) -> dict:
        return self.api("GET", f"/cgi-bin/v1/kb/entries/{entry_id}")

    def download_entry(self, entry_id: str, dest_dir: Path) -> Path:
        """Detail → links.download (valid 60 min) → save file.
        Entry names may carry no extension — one is appended from the
        download response's Content-Type when missing."""
        detail = self.describe_entry(entry_id)
        data = detail.get("data") or {}
        url = (detail.get("links") or data.get("links") or {}).get("download")
        if not url:
            raise LexiangPermissionError(
                f"no download link for entry {entry_id} — non-uploadable source or no permission")
        name = (data.get("attributes") or {}).get("name") or f"{entry_id}.bin"
        dest_dir.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                disposition = resp.headers.get("Content-Disposition") or ""
                payload = resp.read()
        except urllib.error.URLError as exc:
            raise LexiangError(f"download failed for {name}: {exc}") from exc
        # Real filename lives in Content-Disposition (entry names may lack an
        # extension; COS serves application/octet-stream with the true name).
        cd_match = re.search(r"filename\*?=(?:utf-8''|\")?([^\";]+)", disposition)
        if cd_match and not Path(name).suffix:
            cd_name = urllib.parse.unquote(cd_match.group(1))
            if Path(cd_name).suffix:
                name = cd_name
        target = dest_dir / Path(name).name
        if not target.suffix:
            ext = _EXT_BY_MIME.get(content_type)
            if ext:
                target = target.with_suffix(ext)
        target.write_bytes(payload)
        return target

    def upload_file(self, file_path: Path, media_type: str = "file",
                    staff_id: str | None = None) -> str:
        """3-step upload → returns the state token for create_file_entry."""
        staff = staff_id or self.cfg.get("staff_id")
        if not staff:
            raise LexiangError("upload requires LEXIANG_STAFF_ID (x-staff-id)")
        resp = self.api("POST", "/cgi-bin/v1/kb/files/upload-params",
                        {"name": file_path.name, "media_type": media_type}, staff_id=staff)
        obj = resp.get("object") or {}
        upload_url, state = obj.get("upload_url"), obj.get("state")
        if not upload_url or not state:
            raise LexiangError(f"upload-params missing upload_url/state: {resp}")
        headers = dict(obj.get("headers") or {})
        token = (obj.get("auth") or {}).get("XCosSecurityToken")
        if token:
            headers["x-cos-security-token"] = token
        data = file_path.read_bytes()
        req = urllib.request.Request(upload_url, data=data, method="PUT")
        for k, v in headers.items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req, timeout=600) as resp2:
                resp2.read()
        except urllib.error.URLError as exc:
            raise LexiangError(f"COS upload failed for {file_path.name}: {exc}") from exc
        return state

    def create_file_entry(self, space_id: str, parent_id: str, name: str,
                          state: str, entry_type: str = "file",
                          staff_id: str | None = None) -> str:
        staff = staff_id or self.cfg.get("staff_id")
        if not staff:
            raise LexiangError("create entry requires LEXIANG_STAFF_ID (x-staff-id)")
        body = {"data": {"attributes": {"name": name, "entry_type": entry_type},
                         "relationships": {"parent_entry": {"data": {
                             "type": "kb_entry", "id": parent_id}}}}}
        resp = self.api("POST", "/cgi-bin/v1/kb/entries", body,
                        query={"state": state, "space_id": space_id}, staff_id=staff)
        entry_id = (resp.get("data") or {}).get("id")
        if not entry_id:
            raise LexiangError(f"create entry returned no id: {resp}")
        return entry_id

    def update_properties(self, entry_id: str, values: dict,
                          staff_id: str | None = None) -> dict:
        """values: {field_id: value} — text: str; select: label str;
        multi-select: [label, ...]; category: "path/child" string."""
        staff = staff_id or self.cfg.get("staff_id") or "system-bot"
        attributes = {fid: {"value": v} for fid, v in values.items()}
        return self.api("PUT", f"/cgi-bin/v1/kb/entries/{entry_id}/properties/values",
                        {"data": {"attributes": attributes}}, staff_id=staff)

    def get_properties(self, entry_id: str) -> dict:
        resp = self.api("GET", f"/cgi-bin/v1/kb/entries/{entry_id}/properties/values")
        return (resp.get("data") or {}).get("attributes") or {}

    def ai_search(self, query: str, staff_id: str | None = None,
                  limit: int = 10) -> dict:
        staff = staff_id or self.cfg.get("staff_id")
        if not staff:
            raise LexiangError("AI search requires LEXIANG_STAFF_ID (x-staff-id)")
        return self.api("POST", "/cgi-bin/v1/ai/search",
                        {"query": query, "limit": limit}, staff_id=staff)


# ---------------------------------------------------------------------------
# CLI self-check
# ---------------------------------------------------------------------------

def main() -> int:
    if "--check" not in sys.argv:
        print(__doc__)
        return 0
    try:
        cfg = load_config()
        require_config(cfg)
        client = LexiangClient(cfg)
        token = client.token()
        print(f"token OK (…{token[-6:]})")
        props = client.api("GET", "/cgi-bin/v1/kb/properties",
                           query={"source_type": "kb_space", "source_id": cfg["space_id"]})
        names = [p.get("attributes", {}).get("name") for p in props.get("data", [])]
        print(f"space {cfg['space_id']} properties: {names}")
        print("leixang OpenAPI check PASSED")
        return 0
    except LexiangError as exc:
        print(f"check FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
