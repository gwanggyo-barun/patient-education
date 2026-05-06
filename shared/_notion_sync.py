"""Notion sync helper — upsert build artifacts into the patient-education DB.

Reads NOTION_TOKEN from env. Caller decides whether to invoke (skip when token absent).
Uses stdlib only (no extra deps in requirements.txt).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

NOTION_VERSION = "2022-06-28"
DB_ID = "a84f23489df54e8fbe34b9818d6109e5"  # 📋 진료 설명용 자료 DB


def _api(method: str, path: str, body: dict | None = None) -> dict:
    token = os.environ["NOTION_TOKEN"]
    url = f"https://api.notion.com/v1{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion {method} {path} → {e.code}: {err_body}") from e


def _find_page_id_by_title(title: str) -> str | None:
    res = _api(
        "POST",
        f"/databases/{DB_ID}/query",
        {
            "filter": {"property": "자료명", "title": {"equals": title}},
            "page_size": 1,
        },
    )
    results = res.get("results", [])
    return results[0]["id"] if results else None


def upsert(
    *,
    title: str,
    category: str,
    audience: str,
    disease: str,
    html_url: str,
    pdf_url: str,
    today_iso: str,
    version: str = "v1.0",
    status: str = "✅ 사용중",
) -> tuple[str, str]:
    """Create or update a row in the DB. Returns (action, page_id)."""
    notes = f"🌐 HTML: {html_url}\n📄 PDF: {pdf_url}"
    properties = {
        "자료명": {"title": [{"text": {"content": title}}]},
        "카테고리": {"select": {"name": category}},
        "대상": {"select": {"name": audience}},
        "상태": {"select": {"name": status}},
        "파일형식": {"multi_select": [{"name": "PDF"}]},
        "세부 질환": {"rich_text": [{"text": {"content": disease}}]},
        "버전": {"rich_text": [{"text": {"content": version}}]},
        "비고": {"rich_text": [{"text": {"content": notes}}]},
        "최종수정일": {"date": {"start": today_iso}},
    }

    existing = _find_page_id_by_title(title)
    if existing:
        _api("PATCH", f"/pages/{existing}", {"properties": properties})
        return ("updated", existing)

    res = _api(
        "POST",
        "/pages",
        {"parent": {"database_id": DB_ID}, "properties": properties},
    )
    return ("created", res["id"])
