#!/usr/bin/env python3
"""Audit and repair broken Notion links to GitHub Pages artifacts.

Dry-run by default:
    python3 tools/notion_link_audit.py --report

Write fixes only when explicitly requested:
    python3 tools/notion_link_audit.py --fix
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Iterator
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "shared"))

try:
    from build import BASE_URL, TARGETS  # noqa: E402
except ModuleNotFoundError:
    # CI(workflow_dispatch)는 빌드 의존성(playwright/qrcode)을 설치하지 않는다.
    # build.py는 상수(BASE_URL/TARGETS) 접근에만 필요하므로 빌드 전용 모듈을 스텁으로 대체.
    import types

    for _name in ("playwright", "playwright.sync_api", "qrcode", "qrcode.image", "qrcode.image.svg"):
        _mod = sys.modules.setdefault(_name, types.ModuleType(_name))
        if _name == "playwright.sync_api" and not hasattr(_mod, "sync_playwright"):
            _mod.sync_playwright = None
    from build import BASE_URL, TARGETS  # noqa: E402

from _notion_sync import DBS, NOTION_VERSION  # noqa: E402

REPORT_PATH = ROOT / "docs/link-audit-20260607.json"
REQUEST_INTERVAL_SEC = 0.34
TIMEOUT_SEC = 30
REDACTED_LAB_REPORT_TITLE = "[lab-report redacted]"
DATA_SOURCE_IDS = {
    "a84f23489df54e8fbe34b9818d6109e5": "afaccb35-948f-45b4-9e9d-ec64ccbfe345",
}

_TOKEN: str | None = None
_LAST_REQUEST_AT = 0.0
_TARGET_INDEX: dict[str, dict[str, str | None]] | None = None
_AMBIGUOUS_TITLES: set[str] | None = None


@dataclass
class LinkRecord:
    page_id: str
    page_title: str
    kind: str
    url: str
    db_id: str = ""
    content_kind: str | None = None
    location: str = ""
    property_name: str | None = None
    block_id: str | None = None
    block_type: str | None = None
    rich_text_index: int | None = None
    reason: str | None = None
    expected_url: str | None = None
    status_code: int | None = None
    fixed: bool = False
    fix_error: str | None = None
    raw: dict = field(default_factory=dict, repr=False, compare=False)


def get_token() -> str:
    token = os.environ.get("NOTION_TOKEN", "").strip()
    if token:
        return token
    try:
        return subprocess.check_output(
            ["security", "find-generic-password", "-s", "NOTION_TOKEN", "-w"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=10,
        ).strip()
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        raise RuntimeError("NOTION_TOKEN is not set and macOS Keychain lookup failed") from exc


def iter_db_rows(db_id: str) -> Iterator[dict]:
    body: dict = {"page_size": 100}
    while True:
        res = _notion_request("POST", f"/databases/{db_id}/query", body)
        for page in res.get("results", []):
            yield page
        if not res.get("has_more"):
            return
        body["start_cursor"] = res.get("next_cursor")


def extract_links(page: dict, page_blocks: list) -> list[LinkRecord]:
    title = _page_title(page)
    page_id = page["id"]
    parent = page.get("parent", {}) or {}
    db_id = parent.get("database_id") or parent.get("data_source_id") or ""
    content_kind = _kind_for_db(db_id)
    records: list[LinkRecord] = []

    for prop_name, prop in (page.get("properties", {}) or {}).items():
        if prop.get("type") == "url" and prop.get("url") and prop_name in {"파일링크", "HTML 링크", "PDF 링크"}:
            records.append(
                LinkRecord(
                    page_id=page_id,
                    page_title=title,
                    kind="HTML링크" if prop_name == "HTML 링크" else "파일링크",
                    url=prop["url"],
                    db_id=db_id,
                    content_kind=content_kind,
                    location="property_url",
                    property_name=prop_name,
                )
            )
        if prop.get("type") == "rich_text":
            for i, text in enumerate(prop.get("rich_text", [])):
                record_kind = _link_kind_from_rich_text(text)
                if record_kind:
                    records.append(
                        LinkRecord(
                            page_id=page_id,
                            page_title=title,
                            kind=record_kind,
                            url=text["text"]["link"]["url"],
                            db_id=db_id,
                            content_kind=content_kind,
                            location="property_rich_text",
                            property_name=prop_name,
                            rich_text_index=i,
                        )
                    )

    for block in page_blocks:
        records.extend(_extract_block_links(page_id, title, db_id, content_kind, block))
    return records


def check_url(url: str) -> int:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "clinic-link-audit/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as res:
            return res.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except urllib.error.URLError:
        return 0


def expected_url_for(page_title: str, kind: str) -> str | None:
    index, ambiguous = _target_index()
    if page_title in ambiguous:
        return None
    target = index.get(page_title)
    if not target:
        return None
    if kind in {"HTML링크", "body_html"}:
        return target["html_url"]
    if kind in {"파일링크", "body_pdf"}:
        return target["pdf_url"]
    return None


def fix_link(page_id: str, record: LinkRecord, new_url: str, dry_run: bool) -> bool:
    if dry_run:
        return False
    if record.location == "property_url" and record.property_name:
        _notion_request(
            "PATCH",
            f"/pages/{page_id}",
            {"properties": {record.property_name: {"url": new_url}}},
        )
        return True
    if record.location == "property_rich_text" and record.property_name:
        page = _notion_request("GET", f"/pages/{page_id}")
        prop = (page.get("properties", {}) or {}).get(record.property_name, {})
        rich_text = prop.get("rich_text", [])
        if _replace_rich_text_link(rich_text, record, new_url):
            _notion_request(
                "PATCH",
                f"/pages/{page_id}",
                {"properties": {record.property_name: {"rich_text": rich_text}}},
            )
            return True
        raise RuntimeError("matching rich_text link not found")
    if record.location == "block_rich_text" and record.block_id and record.block_type:
        block = _notion_request("GET", f"/blocks/{record.block_id}")
        payload = block.get(record.block_type, {})
        rich_text = payload.get("rich_text", [])
        if _replace_rich_text_link(rich_text, record, new_url):
            _notion_request("PATCH", f"/blocks/{record.block_id}", {record.block_type: {"rich_text": rich_text}})
            return True
        raise RuntimeError("matching block rich_text link not found")
    raise RuntimeError(f"unsupported link location: {record.location}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Notion DB links for broken GitHub Pages URLs.")
    parser.add_argument("--report", action="store_true", help="write docs/link-audit-20260607.json")
    parser.add_argument("--fix", action="store_true", help="patch fixable Notion links")
    args = parser.parse_args()
    if not args.report and not args.fix:
        args.report = True

    try:
        token = get_token()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    global _TOKEN
    _TOKEN = token

    base_status = check_url(BASE_URL + "/")
    if args.fix and base_status == 404:
        report = _build_report(base_status=base_status, dry_run=False, fix_blocked_reason="live base URL is 404")
        _write_report(report)
        print(f"fix aborted: live base URL is 404; report written to {REPORT_PATH.relative_to(ROOT)}")
        return 2

    report = _build_report(base_status=base_status, dry_run=not args.fix, fix_blocked_reason=None)
    if args.fix:
        _apply_fixes(report)
        report = _build_report(base_status=base_status, dry_run=False, fix_blocked_reason=None)
    _write_report(report)
    stats = report["summary"]
    print(
        "link audit complete: "
        f"total={stats['total']} ok={stats['ok']} broken={stats['broken']} "
        f"fixable={stats['fixable']} unfixable={stats['unfixable']} "
        f"report={REPORT_PATH.relative_to(ROOT)}"
    )
    return 0


def _build_report(*, base_status: int, dry_run: bool, fix_blocked_reason: str | None) -> dict:
    details = []
    stats = {"total": 0, "ok": 0, "broken": 0, "fixable": 0, "unfixable": 0}
    db_ids = list(dict.fromkeys([DBS["decks"], DBS["handouts"], *DBS.values()]))
    for db_id in db_ids:
        for page in iter_db_rows(db_id):
            blocks = _get_all_blocks(page["id"])
            for record in extract_links(page, blocks):
                record.expected_url = expected_url_for(record.page_title, record.kind)
                record.status_code = check_url(record.url)
                is_ok = record.status_code == 200
                if is_ok:
                    stats["ok"] += 1
                else:
                    stats["broken"] += 1
                    if record.expected_url:
                        expected_status = check_url(record.expected_url)
                        if expected_status == 200:
                            stats["fixable"] += 1
                        else:
                            stats["unfixable"] += 1
                            record.reason = f"expected_url_status_{expected_status}"
                    else:
                        stats["unfixable"] += 1
                        record.reason = "ambiguous_or_missing_target"
                stats["total"] += 1
                details.append(_record_for_report(record, ok=is_ok))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "live_base_url": BASE_URL,
        "live_base_status": base_status,
        "fix_blocked_reason": fix_blocked_reason,
        "summary": stats,
        "details": details,
    }


def _apply_fixes(report: dict) -> None:
    for row in report["details"]:
        if row["ok"] or not row.get("expected_url") or row.get("expected_status") != 200:
            continue
        record = LinkRecord(**{k: v for k, v in row["record"].items() if k in LinkRecord.__dataclass_fields__})
        try:
            row["fixed"] = fix_link(record.page_id, record, row["expected_url"], dry_run=False)
        except Exception as exc:  # noqa: BLE001
            row["fixed"] = False
            row["fix_error"] = type(exc).__name__


def _record_for_report(record: LinkRecord, *, ok: bool) -> dict:
    data = asdict(record)
    data.pop("raw", None)
    title_redacted = record.content_kind == "lab-reports"
    page_title = REDACTED_LAB_REPORT_TITLE if title_redacted else record.page_title
    if title_redacted:
        data["page_title"] = page_title
    expected_status = check_url(record.expected_url) if record.expected_url and not ok else None
    return {
        "page_id": record.page_id,
        "page_title": page_title,
        "page_title_redacted": title_redacted,
        "content_kind": record.content_kind,
        "link_kind": record.kind,
        "location": record.location,
        "property_name": record.property_name,
        "block_id": record.block_id,
        "before_url": record.url,
        "status_code": record.status_code,
        "ok": ok,
        "expected_url": record.expected_url,
        "expected_status": expected_status,
        "fixable": (not ok) and bool(record.expected_url) and expected_status == 200,
        "unfixable_reason": None if ok or (record.expected_url and expected_status == 200) else record.reason,
        "record": data,
    }


def _write_report(report: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _notion_request(method: str, path: str, body: dict | None = None) -> dict:
    if _TOKEN is None:
        raise RuntimeError("Notion session is not initialized")
    global _LAST_REQUEST_AT
    elapsed = time.monotonic() - _LAST_REQUEST_AT
    if elapsed < REQUEST_INTERVAL_SEC:
        time.sleep(REQUEST_INTERVAL_SEC - elapsed)
    url = f"https://api.notion.com/v1{path}"
    for attempt in range(6):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {_TOKEN}")
        req.add_header("Notion-Version", NOTION_VERSION)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as res:
                _LAST_REQUEST_AT = time.monotonic()
                raw = res.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            _LAST_REQUEST_AT = time.monotonic()
            if exc.code == 429:
                time.sleep(float(exc.headers.get("Retry-After", "1")) + attempt)
                continue
            if exc.code == 404 and method == "POST" and path.startswith("/databases/") and path.endswith("/query"):
                db_id = path.split("/")[2]
                data_source_id = DATA_SOURCE_IDS.get(db_id.replace("-", "").lower())
                if data_source_id:
                    return _notion_request(method, f"/data_sources/{data_source_id}/query", body)
            raise RuntimeError(f"Notion {method} {path} failed with HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            _LAST_REQUEST_AT = time.monotonic()
            raise RuntimeError(f"Notion {method} {path} failed: {type(exc).__name__}") from exc
    raise RuntimeError(f"Notion {method} {path} failed after 429 retries")


def _get_all_blocks(page_id: str) -> list[dict]:
    blocks: list[dict] = []
    cursor = None
    while True:
        suffix = "?page_size=100"
        if cursor:
            suffix += "&start_cursor=" + urllib.parse.quote(cursor)
        res = _notion_request("GET", f"/blocks/{page_id}/children{suffix}")
        for block in res.get("results", []):
            blocks.append(block)
            if block.get("has_children"):
                block["children"] = _get_all_blocks(block["id"])
        if not res.get("has_more"):
            return blocks
        cursor = res.get("next_cursor")


def _extract_block_links(page_id: str, title: str, db_id: str, content_kind: str | None, block: dict) -> list[LinkRecord]:
    records: list[LinkRecord] = []
    block_type = block.get("type")
    payload = block.get(block_type, {}) if block_type else {}
    for i, text in enumerate(payload.get("rich_text", [])):
        record_kind = _link_kind_from_rich_text(text)
        if record_kind:
            records.append(
                LinkRecord(
                    page_id=page_id,
                    page_title=title,
                    kind=record_kind,
                    url=text["text"]["link"]["url"],
                    db_id=db_id,
                    content_kind=content_kind,
                    location="block_rich_text",
                    block_id=block.get("id"),
                    block_type=block_type,
                    rich_text_index=i,
                )
            )
    for child in block.get("children", []):
        records.extend(_extract_block_links(page_id, title, db_id, content_kind, child))
    return records


def _link_kind_from_rich_text(text: dict) -> str | None:
    link = (((text.get("text") or {}).get("link") or {}).get("url"))
    content = (text.get("plain_text") or (text.get("text") or {}).get("content") or "").strip()
    if not link:
        return None
    if "HTML 보기" in content:
        return "body_html"
    if "PDF 다운로드" in content:
        return "body_pdf"
    return None


def _replace_rich_text_link(rich_text: list, record: LinkRecord, new_url: str) -> bool:
    if record.rich_text_index is not None and record.rich_text_index < len(rich_text):
        text = rich_text[record.rich_text_index]
        if (((text.get("text") or {}).get("link") or {}).get("url")) == record.url:
            text["text"]["link"]["url"] = new_url
            return True
    for text in rich_text:
        if (((text.get("text") or {}).get("link") or {}).get("url")) == record.url:
            link_kind = _link_kind_from_rich_text(text)
            if link_kind == record.kind:
                text["text"]["link"]["url"] = new_url
                return True
    return False


def _page_title(page: dict) -> str:
    for prop in (page.get("properties", {}) or {}).values():
        if prop.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in prop.get("title", []))
    return ""


def _kind_for_db(db_id: str) -> str | None:
    normalized = db_id.replace("-", "").lower()
    for kind, candidate in DBS.items():
        if candidate.replace("-", "").lower() == normalized:
            return kind
    for db_candidate, data_source_candidate in DATA_SOURCE_IDS.items():
        if data_source_candidate.replace("-", "").lower() == normalized:
            return _kind_for_db(db_candidate)
    return None


def _target_index() -> tuple[dict[str, dict[str, str | None]], set[str]]:
    global _TARGET_INDEX, _AMBIGUOUS_TITLES
    if _TARGET_INDEX is not None and _AMBIGUOUS_TITLES is not None:
        return _TARGET_INDEX, _AMBIGUOUS_TITLES
    index: dict[str, dict[str, str | None]] = {}
    ambiguous: set[str] = set()
    for target in TARGETS:
        if target.get("notion_sync", True) is False:
            continue
        title = _target_title(target)
        if not title:
            continue
        item = {
            "content_kind": target["kind"],
            "html_url": f"{BASE_URL}/{target['slug_path']}",
            "pdf_url": f"{BASE_URL}/output/{target['kind']}/{target['slug']}.pdf",
        }
        if title in index and index[title] != item:
            ambiguous.add(title)
        index[title] = item
    _TARGET_INDEX = index
    _AMBIGUOUS_TITLES = ambiguous
    return index, ambiguous


def _target_title(target: dict) -> str | None:
    if target["kind"] == "lab-reports":
        patient_name = target.get("patient_name")
        chart_no = target.get("chart_no")
        if patient_name and chart_no:
            title = f"[{chart_no}] {patient_name}"
            if target.get("note"):
                title = f"{title} — {target['note']}"
            return title
    return target.get("title")


if __name__ == "__main__":
    raise SystemExit(main())
