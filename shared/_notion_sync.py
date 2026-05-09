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
import urllib.error
import urllib.request

NOTION_VERSION = "2022-06-28"

# Database routing — see SKILL.md "Notion DB 라우팅" for the full mapping spec.
DBS = {
    "decks":       "a84f23489df54e8fbe34b9818d6109e5",  # 📋 진료 설명용 자료
    "handouts":    "920b48c92d674186a370afcaa81ce788",  # 📨 환자 유인물
    "lab-reports": "c150b47d523c45c09108ac716009c49b",  # 🧪 환자 검사결과
}

TITLE_PROPS = {
    "decks":       "자료명",
    "handouts":    "자료명",
    "lab-reports": "환자명",
}

# Legacy lab-report title parser: "[1063] 김종혁 — 골 대사 검사 (2026-04-29)"
# Captures: 1=chart_no, 2=patient_name, 3=note (optional)
_LAB_TITLE_RE = re.compile(r"^\[(\d+)\]\s*([^—\-]+?)(?:\s*[—\-]\s*(.+))?$")


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


def _find_page_id_by_title(db_id: str, title_prop: str, title: str) -> str | None:
    res = _api(
        "POST",
        f"/databases/{db_id}/query",
        {
            "filter": {"property": title_prop, "title": {"equals": title}},
            "page_size": 1,
        },
    )
    results = res.get("results", [])
    return results[0]["id"] if results else None


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
    return properties, full_title


def _build_handout_props(
    *,
    title: str,
    category: str | None,
    audience: str | None,
    today_iso: str,
    version: str,
    status: str,
    notes_rich: list,
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
    # common optional
    version: str = "v1.0",
    status: str = "✅ 사용중",
) -> tuple[str, str]:
    """Create or update a row in the appropriate DB based on `kind`.

    Returns (action, page_id) where action ∈ {"created", "updated"}.

    For lab-reports, if explicit patient_name/chart_no are missing, this
    function falls back to parsing the legacy `title` form
    "[1063] 김종혁 — 골 대사 검사" so existing TARGETS keep working.
    """
    if kind not in DBS:
        raise ValueError(f"Unknown kind: {kind!r}. Expected one of {list(DBS)}")

    db_id = DBS[kind]
    title_prop = TITLE_PROPS[kind]
    notes_rich = _clickable_links(html_url, pdf_url)

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
        )
    elif kind == "handouts":
        if not title:
            raise ValueError("handouts requires title")
        properties, search_title = _build_handout_props(
            title=title, category=category, audience=audience,
            today_iso=today_iso, version=version, status=status,
            notes_rich=notes_rich,
        )
    else:  # decks
        if not title:
            raise ValueError("decks requires title")
        properties, search_title = _build_deck_props(
            title=title, category=category, audience=audience, disease=disease,
            today_iso=today_iso, version=version, status=status,
            notes_rich=notes_rich,
        )

    existing = _find_page_id_by_title(db_id, title_prop, search_title)
    if existing:
        _api("PATCH", f"/pages/{existing}", {"properties": properties})
        return ("updated", existing)

    res = _api(
        "POST",
        "/pages",
        {"parent": {"database_id": db_id}, "properties": properties},
    )
    return ("created", res["id"])
