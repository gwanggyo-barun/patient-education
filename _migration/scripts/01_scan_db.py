"""Phase 0 — Scan both Notion DBs and dump inventory.csv.

Outputs columns:
    page_id, db, title, category, audience, status, version, file_format,
    detail, last_modified, notion_url, attachment_block_ids
"""
from __future__ import annotations

import csv
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

NOTION_VERSION = "2022-06-28"


def _load_dotenv():
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()


DBS = [
    ("teaching", "a84f23489df54e8fbe34b9818d6109e5", "📋 진료 설명용 자료 DB"),
    ("handout",  "920b48c92d674186a370afcaa81ce788", "📨 환자 유인물 DB"),
]

OUT_CSV = Path(__file__).resolve().parent.parent / "inventory.csv"


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
        raise RuntimeError(f"Notion {method} {path} → {e.code}: {e.read().decode('utf-8', 'replace')}") from e


def query_db_all(db_id: str) -> list[dict]:
    pages, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = _api("POST", f"/databases/{db_id}/query", body)
        pages.extend(res["results"])
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
    return pages


def list_child_blocks(block_id: str) -> list[dict]:
    blocks, cursor = [], None
    while True:
        path = f"/blocks/{block_id}/children?page_size=100"
        if cursor:
            path += f"&start_cursor={cursor}"
        res = _api("GET", path)
        blocks.extend(res["results"])
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")
    return blocks


def find_attachment_blocks(page_id: str) -> list[tuple[str, str, str]]:
    """Return list of (block_id, file_name, file_type) for file/pdf blocks under the page."""
    out: list[tuple[str, str, str]] = []
    stack = [page_id]
    seen = set()
    while stack:
        bid = stack.pop()
        if bid in seen:
            continue
        seen.add(bid)
        try:
            children = list_child_blocks(bid)
        except RuntimeError:
            continue
        for blk in children:
            t = blk.get("type")
            if t in ("file", "pdf"):
                payload = blk.get(t, {})
                name = payload.get("name") or ""
                file_obj = payload.get("file") or payload.get("external") or {}
                file_url = file_obj.get("url", "")
                # Skip external links (not internal Notion files)
                kind = "internal" if "file" in payload else "external"
                out.append((blk["id"], name or file_url.split("/")[-1].split("?")[0], f"{t}:{kind}"))
            if blk.get("has_children"):
                stack.append(blk["id"])
    return out


def prop(props: dict, name: str, ptype: str):
    p = props.get(name)
    if not p:
        return ""
    if ptype == "title":
        return "".join(t.get("plain_text", "") for t in p.get("title", []))
    if ptype == "rich_text":
        return "".join(t.get("plain_text", "") for t in p.get("rich_text", []))
    if ptype == "select":
        return (p.get("select") or {}).get("name", "")
    if ptype == "multi_select":
        return ",".join(opt["name"] for opt in p.get("multi_select", []))
    if ptype == "date":
        return (p.get("date") or {}).get("start", "")
    return ""


def main():
    if "NOTION_TOKEN" not in os.environ:
        print("ERROR: NOTION_TOKEN env var not set", file=sys.stderr)
        sys.exit(2)

    rows = []
    for db_label, db_id, db_name in DBS:
        print(f"Scanning {db_name} ({db_id})…")
        pages = query_db_all(db_id)
        print(f"  → {len(pages)} pages")
        for pg in pages:
            pid = pg["id"]
            props = pg.get("properties", {})
            title = prop(props, "자료명", "title") or prop(props, "Name", "title")
            attachments = find_attachment_blocks(pid)
            rows.append({
                "page_id": pid,
                "db": db_label,
                "title": title,
                "category": prop(props, "카테고리", "select"),
                "audience": prop(props, "대상", "select"),
                "status": prop(props, "상태", "select"),
                "version": prop(props, "버전", "rich_text"),
                "file_format": prop(props, "파일형식", "multi_select"),
                "detail": prop(props, "세부 질환", "rich_text"),
                "last_modified": prop(props, "최종수정일", "date"),
                "notion_url": pg.get("url", ""),
                "attachment_count": len(attachments),
                "attachment_block_ids": "|".join(b[0] for b in attachments),
                "attachment_filenames": "|".join(b[1] for b in attachments),
                "attachment_types": "|".join(b[2] for b in attachments),
            })
            print(f"    · {title[:40]} — {len(attachments)} file(s)")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {OUT_CSV}")


if __name__ == "__main__":
    main()
