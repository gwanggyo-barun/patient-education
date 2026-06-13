"""Notion sync helper — upsert build artifacts into the appropriate clinic DB.

Routes by `kind` to one of three databases (per SKILL.md "Notion DB 라우팅"):
  - decks       → 📋 진료 설명용 자료 DB  (PPT slide-format teaching materials)
  - handouts    → 📨 환자 유인물 DB       (1-2 page non-patient handouts)
  - lab-reports → 🧪 환자 검사결과 DB     (patient-specific lab results)

Each DB has its own schema. lab-reports entries can either:
  (a) supply explicit patient_name/chart_no/exam_date/doctor fields, or
  (b) supply title in the legacy form "[1063] 김종혁 — 골 대사 검사 (2026-04-29)"
      — which is parsed for chart_no, patient_name, and note (date inferred to today_iso).

Reads NOTION_TOKEN from env. Caller decides whether to invoke
(skip when token absent). Uses stdlib only — no extra deps.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

NOTION_VERSION = "2022-06-28"

# Repo root (shared/_notion_sync.py → parent.parent).
_ROOT = Path(__file__).resolve().parent.parent


def git_last_modified_iso(path: str | Path, fallback_iso: str) -> str:
    """`최종수정일` = the date the material's content last changed in git.

    Returns YYYY-MM-DD of the most recent commit touching <path> (committer
    date), or `fallback_iso` (usually today) when the path has no git history
    yet — e.g. a brand-new, not-yet-committed material. This makes 최종수정일
    track real content edits instead of every build/sync run.
    """
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            cwd=str(_ROOT), capture_output=True, text=True, timeout=10,
        )
        d = out.stdout.strip()
        return d if d else fallback_iso
    except Exception:
        return fallback_iso


# --- Content-aware 최종수정일 (ignores CSS/layout-only commits) -------------
# A bulk layout-sweep commit touches every deck's <style>/markup but not the
# patient-facing meaning. We fingerprint only the *content* — visible text +
# the set of embedded image files — and walk git history to find the date that
# fingerprint last changed. So 최종수정일 reflects real content edits, not
# every restyle. (User request 2026-06-12.)

import hashlib  # noqa: E402

_STRIP_BLOCKS = (
    re.compile(r"<head\b.*?</head>", re.S | re.I),
    re.compile(r"<style\b.*?</style>", re.S | re.I),
    re.compile(r"<script\b.*?</script>", re.S | re.I),
    re.compile(r"<!--.*?-->", re.S),
)
_IMG_SRC_RE = re.compile(r"<img\b[^>]*?\bsrc\s*=\s*[\"']([^\"']+)[\"']", re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _content_fingerprint(html_text: str) -> str:
    """Hash of patient-facing content only: visible text + image basenames.

    Deliberately blind to CSS, class names, inline <style>, and HTML structure
    so that pure restyle/layout commits do not count as content changes.
    """
    import html as _html

    imgs = sorted({src.rsplit("/", 1)[-1] for src in _IMG_SRC_RE.findall(html_text)})
    body = html_text
    for rx in _STRIP_BLOCKS:
        body = rx.sub(" ", body)
    body = _TAG_RE.sub(" ", body)
    body = _WS_RE.sub(" ", _html.unescape(body)).strip()
    blob = body + "\n IMGS " + "|".join(imgs)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def content_last_modified_iso(file_rel_path: str, fallback_iso: str) -> str:
    """Date the material's *content* last changed in git (YYYY-MM-DD).

    Walks the file's commit history oldest→newest, hashing the content
    fingerprint of each revision, and returns the date of the most recent
    commit where the fingerprint differs from the prior one. Restyle-only
    commits are skipped. Falls back to the plain git date, then `fallback_iso`,
    if history can't be read.
    """
    try:
        log = subprocess.run(
            ["git", "log", "--format=%H %cs", "--", file_rel_path],
            cwd=str(_ROOT), capture_output=True, text=True, timeout=30,
        )
        lines = [ln for ln in log.stdout.splitlines() if ln.strip()]
        if not lines:
            return git_last_modified_iso(file_rel_path, fallback_iso)
        commits = [(ln.split(" ", 1)[0], ln.split(" ", 1)[1]) for ln in lines]
        prev_fp = None
        last_change = commits[-1][1]  # default: creation date (oldest commit)
        for h, d in reversed(commits):  # oldest → newest
            blob = subprocess.run(
                ["git", "show", f"{h}:{file_rel_path}"],
                cwd=str(_ROOT), capture_output=True, text=True, timeout=30,
            )
            if blob.returncode != 0:
                continue
            fp = _content_fingerprint(blob.stdout)
            if fp != prev_fp:
                last_change = d
                prev_fp = fp
        return last_change
    except Exception:
        return git_last_modified_iso(file_rel_path, fallback_iso)

# Database routing — see SKILL.md "Notion DB 라우팅" for the full mapping spec.
DBS = {
    "decks":       "a84f23489df54e8fbe34b9818d6109e5",  # 📋 진료 설명용 자료
    "handouts":    "920b48c92d674186a370afcaa81ce788",  # 📨 환자 유인물
    "lab-reports": "c150b47d523c45c09108ac716009c49b",  # 🧪 환자 검사결과
}

# 👤 환자 마스터 DB — same parent page as lab-reports DB. Each patient
# identified by chart_no (unique); lab-report rows link here via the
# DUAL "환자" relation so a patient page auto-accumulates every test
# they've ever had on the build pipeline.
PATIENT_DB_ID = "b7e56e3433ee4ed4a28f24621590d1af"

TITLE_PROPS = {
    "decks":       "자료명",
    "handouts":    "자료명",
    "lab-reports": "환자명",
}

# Legacy lab-report title parser: "[1063] 김종혁 — 골 대사 검사 (2026-04-29)"
# Captures: 1=chart_no, 2=patient_name, 3=note (optional)
_LAB_TITLE_RE = re.compile(r"^\[(\d+)\]\s*([^—\-]+?)(?:\s*[—\-]\s*(.+))?$")


def _normalize_notion_id(value: str | None) -> str:
    return (value or "").replace("-", "").lower()


def _page_is_trashed(page: dict) -> bool:
    return bool(
        page.get("in_trash")
        or page.get("archived")
        or page.get("is_archived")
    )


def _page_parent_matches(page: dict, db_id: str) -> bool:
    parent = page.get("parent", {})
    parent_id = parent.get("database_id") or parent.get("data_source_id")
    return _normalize_notion_id(parent_id) == _normalize_notion_id(db_id)


def _title_prop_text(page: dict, prop_name: str) -> str:
    prop = page.get("properties", {}).get(prop_name, {})
    return "".join(t.get("plain_text", "") for t in prop.get("title", []))


def _rich_text_prop_text(page: dict, prop_name: str) -> str:
    prop = page.get("properties", {}).get(prop_name, {})
    return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))


def _first_live_or_any(pages: list[dict]) -> dict | None:
    if not pages:
        return None
    return next((page for page in pages if not _page_is_trashed(page)), pages[0])


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


def _search_pages_by_title(title: str) -> list[dict]:
    body: dict = {
        "query": title,
        "filter": {"property": "object", "value": "page"},
        "page_size": 100,
    }
    pages: list[dict] = []
    while True:
        res = _api("POST", "/search", body)
        pages.extend(res.get("results", []))
        if not res.get("has_more"):
            return pages
        body["start_cursor"] = res["next_cursor"]


def _find_page_by_title(db_id: str, title_prop: str, title: str) -> dict | None:
    res = _api(
        "POST",
        f"/databases/{db_id}/query",
        {
            "filter": {"property": title_prop, "title": {"equals": title}},
            "page_size": 10,
        },
    )
    results = res.get("results", [])
    existing = _first_live_or_any(results)
    if existing:
        return existing

    matches = [
        page for page in _search_pages_by_title(title)
        if _page_parent_matches(page, db_id)
        and _title_prop_text(page, title_prop) == title
    ]
    return _first_live_or_any(matches)


def _find_patient_page_by_search(chart_no: str, patient_name: str) -> dict | None:
    matches = [
        page for page in _search_pages_by_title(patient_name)
        if _page_parent_matches(page, PATIENT_DB_ID)
        and _title_prop_text(page, "환자명") == patient_name
        and _rich_text_prop_text(page, "차트번호") == chart_no
    ]
    return _first_live_or_any(matches)


def _ensure_patient_page(chart_no: str, patient_name: str) -> str | None:
    """Find patient page by chart_no, or create one. Returns page_id.

    chart_no is the unique identifier (EMR chart number) — used for dedup so
    name typos / 표기 흔들림 don't fragment the patient. If a row already
    exists with this chart_no but a different 환자명, the existing 환자명 is
    updated to the latest passed in (assumption: latest build is most correct).
    """
    res = _api(
        "POST",
        f"/databases/{PATIENT_DB_ID}/query",
        {
            "filter": {"property": "차트번호", "rich_text": {"equals": chart_no}},
            "page_size": 10,
        },
    )
    results = res.get("results", [])
    if results:
        existing = _first_live_or_any(results)
        if existing is None or _page_is_trashed(existing):
            return None
        existing_id = existing["id"]
        existing_name = _title_prop_text(existing, "환자명")
        if patient_name and existing_name != patient_name:
            _api(
                "PATCH",
                f"/pages/{existing_id}",
                {
                    "properties": {
                        "환자명": {"title": [{"text": {"content": patient_name}}]}
                    }
                },
            )
        return existing_id

    deleted_or_missed = _find_patient_page_by_search(chart_no, patient_name)
    if deleted_or_missed:
        if _page_is_trashed(deleted_or_missed):
            return None
        return deleted_or_missed["id"]

    res = _api(
        "POST",
        "/pages",
        {
            "parent": {"database_id": PATIENT_DB_ID},
            "properties": {
                "환자명": {"title": [{"text": {"content": patient_name}}]},
                "차트번호": {"rich_text": [{"text": {"content": chart_no}}]},
            },
        },
    )
    return res["id"]


def _find_lab_report_existing(
    db_id: str, slug: str, search_title: str
) -> dict | None:
    """Find existing lab-report row using slug-based dedup.

    The slug is a SHA-256 hash of (chart_no, patient_name, topic) — stable
    across edits to note/title/patient_name formatting. It's embedded in
    every 파일링크 URL the build emits, so `url contains slug` reliably
    matches the same logical report even if the human-readable title or
    URL format changed between builds.

    Falls back to title equals for legacy entries created before slug-based
    dedup landed.
    """
    res = _api(
        "POST",
        f"/databases/{db_id}/query",
        {
            "filter": {"property": "파일링크", "url": {"contains": slug}},
            "page_size": 10,
        },
    )
    results = res.get("results", [])
    existing = _first_live_or_any(results)
    if existing:
        return existing
    return _find_page_by_title(db_id, "환자명", search_title)


def _clickable_links(html_url: str, pdf_url: str) -> list:
    """비고 컬럼용 — 한 번 클릭으로 열리는 HTML/PDF 링크."""
    return [
        {"type": "text", "text": {"content": "🌐 HTML 보기", "link": {"url": html_url}}},
        {"type": "text", "text": {"content": "\n"}},
        {"type": "text", "text": {"content": "📄 PDF 다운로드", "link": {"url": pdf_url}}},
    ]


def _parse_legacy_lab_title(title: str) -> tuple[str | None, str | None, str | None]:
    """Parse '[1063] 김종혁 — 골 대사 검사 (2026-04-29)' → (chart_no, patient_name, note).

    Returns (None, None, None) if title doesn't match expected legacy form.
    """
    m = _LAB_TITLE_RE.match(title.strip())
    if not m:
        return (None, None, None)
    chart_no, patient_name, note = m.group(1), m.group(2).strip(), m.group(3)
    return (chart_no, patient_name, note.strip() if note else None)


def _build_lab_report_props(
    *,
    patient_name: str,
    chart_no: str,
    exam_date: str | None,
    doctor: str | None,
    note: str | None,
    pdf_url: str,
    notes_rich: list,
    patient_page_id: str | None = None,
) -> tuple[dict, str]:
    """🧪 환자 검사결과 DB 속성 빌드. Returns (properties, search_title)."""
    if not (patient_name and chart_no):
        raise ValueError("lab-reports requires patient_name and chart_no")

    full_title = f"[{chart_no}] {patient_name}"
    if note:
        full_title = f"{full_title} — {note}"

    properties: dict = {
        "환자명": {"title": [{"text": {"content": full_title}}]},
        "차트번호": {"rich_text": [{"text": {"content": chart_no}}]},
        "자료종류": {"select": {"name": "검사결과"}},
        "파일형식": {"multi_select": [{"name": "PDF"}, {"name": "HTML"}]},
        "파일링크": {"url": pdf_url},
        "비고": {"rich_text": notes_rich},
    }
    if exam_date:
        properties["검사일"] = {"date": {"start": exam_date}}
    if doctor:
        properties["담당의"] = {"rich_text": [{"text": {"content": doctor}}]}
    if patient_page_id:
        properties["환자"] = {"relation": [{"id": patient_page_id}]}
    return properties, full_title


# ===========================================================================
# Patient hub auto-update (👤 환자 마스터 DB) — chart_no 기반 누적 조회 시스템
# ===========================================================================
# Each lab-report row links to a patient hub via "환자" relation. After every
# row create/update, the hub page's body is fully regenerated from all linked
# lab rows (sorted by exam_date desc), and its summary properties are patched
# from the latest row. Manual edits to the hub body are not preserved — this
# is the explicit design decision (전체 자동 SoT).
# Per Gotcha 11, patient names/chart numbers go into Notion page content only
# via Notion API properties — never into git logs or stderr prints.


def _list_patient_labs(patient_page_id: str) -> list[dict]:
    """Return all lab-report rows linked to this patient hub, exam_date desc."""
    res = _api(
        "POST",
        f"/databases/{DBS['lab-reports']}/query",
        {
            "filter": {
                "property": "환자",
                "relation": {"contains": patient_page_id},
            },
            "sorts": [{"property": "검사일", "direction": "descending"}],
            "page_size": 100,
        },
    )
    return res.get("results", [])


def _extract_lab_fields(lab: dict) -> dict:
    """Pull callout-relevant fields out of a lab-report row page object."""
    props = lab.get("properties", {})
    title = "".join(
        t.get("plain_text", "")
        for t in props.get("환자명", {}).get("title", [])
    )
    exam_date = (props.get("검사일", {}).get("date") or {}).get("start") or ""
    html_url = (props.get("HTML 링크", {}) or {}).get("url") or ""
    pdf_url = (
        (props.get("PDF 링크", {}) or {}).get("url")
        or (props.get("파일링크", {}) or {}).get("url")
        or ""
    )
    return {
        "title": title,
        "exam_date": exam_date,
        "html_url": html_url,
        "pdf_url": pdf_url,
    }


def _build_lab_callout_block(fields: dict) -> dict:
    """One lab row → callout block for hub body."""
    date_str = fields["exam_date"] or "(검사일 미정)"
    title = fields["title"] or "검사 결과"
    html_url = fields["html_url"]
    pdf_url = fields["pdf_url"]

    rich_text: list = [
        {
            "type": "text",
            "text": {"content": f"{date_str}  ·  "},
            "annotations": {"bold": True},
        },
        {"type": "text", "text": {"content": f"{title}\n"}},
    ]
    if html_url:
        rich_text.append(
            {"type": "text", "text": {"content": "🌐 HTML 보기", "link": {"url": html_url}}}
        )
    if html_url and pdf_url:
        rich_text.append({"type": "text", "text": {"content": "  ·  "}})
    if pdf_url:
        rich_text.append(
            {"type": "text", "text": {"content": "📄 PDF 다운로드", "link": {"url": pdf_url}}}
        )
    return {
        "object": "block",
        "type": "callout",
        "callout": {"icon": {"emoji": "🧪"}, "rich_text": rich_text},
    }


def _build_hub_index_blocks(labs: list[dict]) -> list[dict]:
    """Build the hub body children: heading + callout per lab."""
    blocks: list = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {"type": "text", "text": {"content": "📅 검사 이력 — 최신순"}}
                ],
            },
        }
    ]
    for lab in labs:
        blocks.append(_build_lab_callout_block(_extract_lab_fields(lab)))
    if not labs:
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "아직 등록된 검사 결과가 없습니다."}}
                    ],
                },
            }
        )
    return blocks


def _replace_page_children(page_id: str, new_blocks: list[dict]) -> None:
    """Wipe existing top-level children and append new ones.

    Notion API has no prepend; "전체 자동 SoT" 디자인이라 매번 통째 재작성.
    Max 100 children per PATCH call — chunk if larger.
    """
    res = _api("GET", f"/blocks/{page_id}/children?page_size=100", None)
    for block in res.get("results", []):
        try:
            _api("DELETE", f"/blocks/{block['id']}", None)
        except Exception:  # noqa: BLE001
            pass  # best-effort; orphaned archived blocks are harmless
    if new_blocks:
        for i in range(0, len(new_blocks), 100):
            _api(
                "PATCH",
                f"/blocks/{page_id}/children",
                {"children": new_blocks[i : i + 100]},
            )


def _refresh_patient_hub_props(patient_page_id: str, latest_lab: dict) -> None:
    """Patch 최근 검사일·요약·HTML on the hub from the newest lab row."""
    f = _extract_lab_fields(latest_lab)
    summary = f["title"]
    if " — " in summary:
        summary = summary.split(" — ", 1)[1]
    elif "] " in summary:
        summary = summary.split("] ", 1)[1]
    summary = summary[:200]

    patch_props: dict = {}
    if f["exam_date"]:
        patch_props["최근 검사일"] = {"date": {"start": f["exam_date"]}}
    if f["html_url"]:
        patch_props["최근 HTML 링크"] = {"url": f["html_url"]}
    if summary:
        patch_props["최근 검사요약"] = {"rich_text": [{"text": {"content": summary}}]}
    if patch_props:
        _api("PATCH", f"/pages/{patient_page_id}", {"properties": patch_props})


def _refresh_patient_hub(patient_page_id: str) -> None:
    """Full hub refresh — body rebuild + summary props. Best-effort."""
    try:
        labs = _list_patient_labs(patient_page_id)
        if not labs:
            return
        _replace_page_children(patient_page_id, _build_hub_index_blocks(labs))
        _refresh_patient_hub_props(patient_page_id, labs[0])
    except Exception as e:  # noqa: BLE001
        import sys as _sys
        # PII never enters stderr — class name only.
        print(
            f"⚠️  patient hub refresh failed ({type(e).__name__})",
            file=_sys.stderr,
        )


def _build_lab_report_body(
    html_url: str, pdf_url: str, patient_page_id: str | None
) -> list[dict]:
    """Lab-report row body — 자료 callout + (있으면) 환자 hub link callout."""
    blocks: list = [
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "icon": {"emoji": "📋"},
                "rich_text": [
                    {"type": "text", "text": {"content": "검사 자료 — "}},
                    {
                        "type": "text",
                        "text": {"content": "🌐 HTML 보기", "link": {"url": html_url}},
                    },
                    {"type": "text", "text": {"content": "  ·  "}},
                    {
                        "type": "text",
                        "text": {"content": "📄 PDF 다운로드", "link": {"url": pdf_url}},
                    },
                ],
            },
        }
    ]
    if patient_page_id:
        hub_url = f"https://www.notion.so/{patient_page_id.replace('-', '')}"
        blocks.append(
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "icon": {"emoji": "👤"},
                    "rich_text": [
                        {"type": "text", "text": {"content": "이 환자의 검사 이력 전체 보기 → "}},
                        {
                            "type": "text",
                            "text": {"content": "환자 마스터 페이지 열기", "link": {"url": hub_url}},
                        },
                    ],
                },
            }
        )
    return blocks


def _build_handout_props(
    *,
    title: str,
    category: str | None,
    audience: str | None,
    today_iso: str,
    version: str,
    status: str,
    notes_rich: list,
    pdf_url: str = "",
) -> tuple[dict, str]:
    """📨 환자 유인물 DB 속성 빌드. Returns (properties, search_title)."""
    properties: dict = {
        "자료명": {"title": [{"text": {"content": title}}]},
        "상태": {"select": {"name": status}},
        "파일형식": {"multi_select": [{"name": "PDF"}]},
        "버전": {"rich_text": [{"text": {"content": version}}]},
        "비고": {"rich_text": notes_rich},
        "최종수정일": {"date": {"start": today_iso}},
    }
    if pdf_url:
        # 사용자 요구 (2026-06-06): 링크 칸(파일링크)이 비면 안 됨
        properties["파일링크"] = {"url": pdf_url}
    if category:
        properties["카테고리"] = {"select": {"name": category}}
    if audience:
        properties["대상"] = {"select": {"name": audience}}
    return properties, title


def _build_deck_props(
    *,
    title: str,
    category: str | None,
    audience: str | None,
    disease: str | None,
    today_iso: str,
    version: str,
    status: str,
    notes_rich: list,
    pdf_url: str = "",
) -> tuple[dict, str]:
    """📋 진료 설명용 자료 DB 속성 빌드. Returns (properties, search_title)."""
    properties: dict = {
        "자료명": {"title": [{"text": {"content": title}}]},
        "상태": {"select": {"name": status}},
        "파일형식": {"multi_select": [{"name": "PDF"}]},
        "버전": {"rich_text": [{"text": {"content": version}}]},
        "비고": {"rich_text": notes_rich},
        "최종수정일": {"date": {"start": today_iso}},
    }
    if pdf_url:
        # 사용자 요구 (2026-06-06): 링크 칸(파일링크)이 비면 안 됨
        properties["파일링크"] = {"url": pdf_url}
    if category:
        properties["카테고리"] = {"select": {"name": category}}
    if audience:
        properties["대상"] = {"select": {"name": audience}}
    if disease:
        properties["세부 질환"] = {"rich_text": [{"text": {"content": disease}}]}
    return properties, title


def upsert(
    *,
    kind: str,
    html_url: str,
    pdf_url: str,
    today_iso: str,
    # decks/handouts 최종수정일 source — material's git last-commit date.
    # Falls back to today_iso when not provided (e.g. legacy callers).
    modified_iso: str | None = None,
    # decks / handouts
    title: str | None = None,
    category: str | None = None,
    audience: str | None = None,
    disease: str | None = None,
    # lab-reports (patient-specific)
    patient_name: str | None = None,
    chart_no: str | None = None,
    exam_date: str | None = None,
    doctor: str | None = None,
    note: str | None = None,
    slug: str | None = None,
    # common optional
    version: str = "v1.0",
    status: str = "✅ 사용중",
) -> tuple[str, str]:
    """Create or update a row in the appropriate DB based on `kind`.

    Returns (action, page_id) where action ∈ {"created", "updated"}.

    For lab-reports, if explicit patient_name/chart_no are missing, this
    function falls back to parsing the legacy `title` form
    "[1063] 김종혁 — 골 대사 검사" so existing TARGETS keep working.

    Dedup: lab-reports match by `slug` embedded in 파일링크 URL (stable
    across note/title edits); decks/handouts match by title equals.
    """
    if kind not in DBS:
        raise ValueError(f"Unknown kind: {kind!r}. Expected one of {list(DBS)}")

    db_id = DBS[kind]
    title_prop = TITLE_PROPS[kind]
    notes_rich = _clickable_links(html_url, pdf_url)
    if kind in ("decks", "handouts") and note:
        notes_rich.extend([
            {"type": "text", "text": {"content": "\n"}},
            {"type": "text", "text": {"content": note}},
        ])
    patient_page_id: str | None = None

    if kind == "lab-reports":
        # Legacy fallback: parse "[chart] name — note" out of title
        if (not patient_name or not chart_no) and title:
            p_chart, p_name, p_note = _parse_legacy_lab_title(title)
            chart_no = chart_no or p_chart
            patient_name = patient_name or p_name
            note = note or p_note
        # exam_date defaults to today if still unspecified
        exam_date = exam_date or today_iso
        properties, search_title = _build_lab_report_props(
            patient_name=patient_name or "",
            chart_no=chart_no or "",
            exam_date=exam_date,
            doctor=doctor,
            note=note,
            pdf_url=pdf_url,
            notes_rich=notes_rich,
            patient_page_id=patient_page_id,
        )
    elif kind == "handouts":
        if not title:
            raise ValueError("handouts requires title")
        properties, search_title = _build_handout_props(
            title=title, category=category, audience=audience,
            today_iso=modified_iso or today_iso, version=version, status=status,
            notes_rich=notes_rich, pdf_url=pdf_url,
        )
    else:  # decks
        if not title:
            raise ValueError("decks requires title")
        properties, search_title = _build_deck_props(
            title=title, category=category, audience=audience, disease=disease,
            today_iso=modified_iso or today_iso, version=version, status=status,
            notes_rich=notes_rich, pdf_url=pdf_url,
        )

    if kind == "lab-reports":
        # Slug-based dedup — survives note/title edits between rebuilds.
        # Fallback to slug derivation if caller didn't pass it (legacy callers).
        dedup_slug = slug or pdf_url.rsplit("/", 1)[-1].removesuffix(".pdf")
        existing_page = _find_lab_report_existing(db_id, dedup_slug, search_title)
    else:
        existing_page = _find_page_by_title(db_id, title_prop, search_title)

    if existing_page and _page_is_trashed(existing_page):
        return ("skipped_deleted", existing_page["id"])

    if kind == "lab-reports" and patient_name and chart_no:
        # Auto-link to 환자 마스터 DB — find by chart_no, create if missing.
        # Best-effort: lab-report upsert still proceeds if patient link fails.
        try:
            patient_page_id = _ensure_patient_page(chart_no, patient_name)
        except Exception as e:  # noqa: BLE001
            import sys as _sys
            # Never log chart_no, name, or full exception text — CI logs
            # on public repos are world-readable. Exception class only.
            print(
                f"⚠️  patient master link failed (chart=*** name=***) "
                f"({type(e).__name__})",
                file=_sys.stderr,
            )
        properties, search_title = _build_lab_report_props(
            patient_name=patient_name,
            chart_no=chart_no,
            exam_date=exam_date,
            doctor=doctor,
            note=note,
            pdf_url=pdf_url,
            notes_rich=notes_rich,
            patient_page_id=patient_page_id,
        )

    if existing_page:
        existing = existing_page["id"]
        _api("PATCH", f"/pages/{existing}", {"properties": properties})
        if kind == "lab-reports":
            # Backfill: if existing row has no body yet (e.g. created before
            # auto-body rollout), inject the standard 2-callout body now.
            # Best-effort — never fail the build on this.
            try:
                ch = _api(
                    "GET", f"/blocks/{existing}/children?page_size=1", None
                )
                if not ch.get("results"):
                    body = _build_lab_report_body(
                        html_url, pdf_url, patient_page_id
                    )
                    if body:
                        _api(
                            "PATCH",
                            f"/blocks/{existing}/children",
                            {"children": body},
                        )
            except Exception as e:  # noqa: BLE001
                import sys as _sys
                print(
                    f"⚠️  lab-report body backfill failed ({type(e).__name__})",
                    file=_sys.stderr,
                )
            # Refresh patient hub (body + summary props) — best-effort.
            if patient_page_id:
                _refresh_patient_hub(patient_page_id)
        return ("updated", existing)

    post_body: dict = {
        "parent": {"database_id": db_id},
        "properties": properties,
    }
    if kind == "lab-reports":
        body = _build_lab_report_body(html_url, pdf_url, patient_page_id)
        if body:
            post_body["children"] = body
    res = _api("POST", "/pages", post_body)
    new_id = res["id"]
    if kind == "lab-reports" and patient_page_id:
        _refresh_patient_hub(patient_page_id)
    return ("created", new_id)
