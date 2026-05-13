"""Core pipeline for the lab-report intake web app.

Flow:
  1. user uploads a lab-result PDF + emphasis text + patient metadata
  2. PDF pages are rasterized to PNGs (PyMuPDF)
  3. OpenAI gpt-4o-vision extracts structured data (4 key stats, 7 detail rows,
     3 meaning bullets, 3 recommendation bullets) — biased by emphasis text
  4. structured data + metadata fill a Jinja template → A4 portrait HTML
  5. Playwright renders the HTML to PDF (+ preview PNG)
  6. (optional) Notion upsert via existing _notion_sync.upsert — patient master
     page is auto-linked through the same path build.py uses, so the row shows
     up under the patient's 검사결과 relation automatically.

The output mirrors the clinic-content-system lab-reports convention so the
generated HTML can be committed to lab-reports/{topic}/{hash}/index.html and
picked up by the regular GH Pages build with no extra work.
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]  # clinic-content-system/
sys.path.insert(0, str(ROOT / "shared"))
from _build_helpers import (  # noqa: E402
    lab_hash_slug,
    inject_noindex_meta,
    render as pw_render,
)
from _validate_layout import HANDOUT_VALIDATOR_JS  # noqa: E402

BASE_URL = "https://gwanggyo-barun.github.io/patient-education"

# Claude vision model — Sonnet 4.5 is strong for Korean medical extraction
# + structured JSON output, cheaper than Opus, and fast enough for the
# 15-30s interactive UX target.
ANTHROPIC_MODEL = "claude-sonnet-4-5"

# Path to clinic-content-system SKILL.md — injected (with prompt caching)
# as system prompt so the model already knows the lab-report conventions,
# design tokens, validators, and section structure.
SKILL_MD_PATH = ROOT / "SKILL.md"

# Topic → human-readable eyebrow label shown in header
TOPIC_LABELS = {
    "general-checkup": "GENERAL CHECKUP",
    "comprehensive-summary": "COMPREHENSIVE SUMMARY",
    "lipid-panel": "LIPID PANEL",
    "diabetes-screening": "DIABETES SCREENING",
    "cv-screening": "CV SCREENING",
    "bone-metabolism": "BONE METABOLISM",
    "urinalysis": "URINALYSIS",
    "thyroid": "THYROID PANEL",
}

# Default report title per topic — overridable from caller
DEFAULT_TITLES = {
    "general-checkup": "종합검사 결과 안내",
    "comprehensive-summary": "종합 검진 결과 요약",
    "lipid-panel": "지질 검사 결과 안내",
    "diabetes-screening": "당뇨 검진 결과 안내",
    "cv-screening": "심혈관 위험 평가 결과",
    "bone-metabolism": "골 대사 검사 결과",
    "urinalysis": "소변 검사 결과 안내",
    "thyroid": "갑상선 기능검사 결과",
}


@dataclass
class PatientMeta:
    name: str
    chart_no: str
    exam_date: str  # YYYY-MM-DD
    doctor: str = "정지환"
    age_sex: str = ""  # filled in by AI from PDF if empty


@dataclass
class IntakeResult:
    slug: str
    topic: str
    html_path: Path
    pdf_path: Path
    preview_path: Path
    extracted: dict = field(default_factory=dict)
    notion_action: str | None = None
    notion_page_id: str | None = None


# --------------------------------------------------------------------------- #
# Step 1-2: PDF rasterization
# --------------------------------------------------------------------------- #

def pdf_to_images(pdf_bytes: bytes, dpi: int = 144) -> list[bytes]:
    """Convert each PDF page to a PNG byte string.

    dpi=144 (~2x of default 72) is enough resolution for gpt-4o-vision to
    OCR small lab table numbers without bloating tokens too much.
    """
    images: list[bytes] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        zoom = dpi / 72
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            images.append(pix.tobytes("png"))
    finally:
        doc.close()
    return images


# --------------------------------------------------------------------------- #
# Step 3: GPT-4o vision structured extraction
# --------------------------------------------------------------------------- #

EXTRACTION_SYSTEM = """\
당신은 광교바른내과의 검사결과 인포그래픽 자료 작성 전문가입니다. 환자가 검사실에서
받아 가는 A4 1장 결과지에 들어갈 내용을 추출하고 요약합니다.

원칙:
- 의학적 사실은 PDF에 적힌 값을 그대로 신뢰합니다 (창의적 해석 금지).
- 강조점(emphasis)이 주어지면 그 방향으로 우선순위를 잡습니다.
- 한국어로 출력합니다.
- 환자가 한 번에 이해할 수 있게 핵심만 추립니다.
- 의학적 단정은 피하고 "정상 / 경계 / 주의" 같은 표현을 사용합니다.

출력은 반드시 JSON 형식이며 다음 스키마를 따릅니다:
{
  "report_title": "결과지 제목 (예: '종합검사 결과 안내')",
  "eyebrow_label": "헤더 라벨 (예: 'GENERAL CHECKUP')",
  "og_description": "OG meta description, 1줄 요약 (60자 이내)",
  "age_sex": "F/53 또는 M/47 형식 — PDF에서 추출 불가시 빈 문자열",
  "stats": [
    {"label": "총콜레스테롤", "value": "209", "unit": "mg/dL · 경계역",
     "status": "high|ok|alert|warn 중 하나"}
    // 정확히 4개. 가장 임상적으로 중요한 핵심 수치.
  ],
  "details": [
    {"label": "지질 (TC / LDL / HDL / TG)",
     "value": "209 / 127 / 62 / 96",
     "range": "<200 / <130 / 40~60 / <150",
     "badge": "경계|정상|주의|이상 중 하나",
     "badge_class": "high|alert|warn 또는 빈 문자열 (정상일 때)"}
    // 5~7행. 검사 카테고리별로 묶어 한 줄에. 정상 항목은 묶어서 1줄.
  ],
  "meanings": [
    "환자에게 결과의 핵심 의미를 알려주는 문장. <strong>강조</strong> 가능. 8.5pt에 맞춰 짧게."
    // 정확히 3개.
  ],
  "recommendations": [
    "<strong>식이</strong> — 구체적 행동"
    // 정확히 3개. 식이/운동/추적 같은 카테고리 구분.
  ]
}
"""

EXTRACTION_USER_TEMPLATE = """\
환자: {patient_name} (차트번호 {chart_no}, 검사일 {exam_date})
검사 카테고리: {topic}

[강조점 — 의사가 환자에게 전달하고 싶은 핵심 메시지]
{emphasis}

위 검사 PDF 이미지를 분석해서 JSON으로 구조화해주세요. 강조점이 있으면 그 방향으로
stats/details/meanings/recommendations 의 우선순위를 잡되, PDF에 적힌 수치는 그대로
정확히 옮깁니다. 강조점이 비어있다면 PDF에서 가장 임상적으로 중요한 항목을 우선합니다.
"""


def _load_skill_md() -> str:
    """Lazy-load SKILL.md as a cacheable system prompt block (once per process).

    Returns empty string if the file is missing — caller treats that as "no
    extra conventions context" and falls back to EXTRACTION_SYSTEM alone.
    """
    try:
        return SKILL_MD_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _user_content_text(meta: PatientMeta, topic: str, emphasis: str) -> str:
    return EXTRACTION_USER_TEMPLATE.format(
        patient_name=meta.name,
        chart_no=meta.chart_no,
        exam_date=meta.exam_date,
        topic=topic,
        emphasis=emphasis.strip() or "(없음 — PDF에서 임상적 우선순위로 추출)",
    )


def _parse_json_block(text: str) -> dict:
    """Robust JSON extraction — handle plain JSON, fenced code blocks, prose wrapping."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in model response (first 200 chars): {text[:200]}")
    return json.loads(text[start : end + 1])


def _extract_via_anthropic(
    images: list[bytes], meta: PatientMeta, topic: str, emphasis: str
) -> dict:
    """Claude Sonnet 4.5 with SKILL.md cached system prompt + vision input.

    SKILL.md (~15K tokens) sits in the first system block with
    cache_control=ephemeral, so the first call pays full input cost but
    subsequent calls within the 5-min cache window only pay ~10% for that
    portion. EXTRACTION_SYSTEM (JSON schema spec) goes uncached in a second
    block because it's small and may evolve.
    """
    import anthropic

    client = anthropic.Anthropic()

    user_content: list[dict] = []
    for img_bytes in images:
        b64 = base64.b64encode(img_bytes).decode("ascii")
        user_content.append(
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": b64},
            }
        )
    user_content.append({"type": "text", "text": _user_content_text(meta, topic, emphasis)})

    skill_md = _load_skill_md()
    system_blocks: list[dict] = []
    if skill_md:
        system_blocks.append(
            {
                "type": "text",
                "text": (
                    "다음은 광교바른내과 clinic-content-system 의 SKILL.md 입니다 "
                    "(콘텐츠 컨벤션·디자인 토큰·검증 규칙·lab-reports 운영 원칙). "
                    "검사결과 인포그래픽 데이터 추출 시 이 컨벤션을 따릅니다.\n\n"
                    + skill_md
                ),
                "cache_control": {"type": "ephemeral"},
            }
        )
    system_blocks.append({"type": "text", "text": EXTRACTION_SYSTEM})

    resp = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system_blocks,
        messages=[{"role": "user", "content": user_content}],
        temperature=0.2,
    )

    # Anthropic returns a list of content blocks; the text response is the
    # first text block. usage telemetry includes cache hit/miss counters
    # which the caller can log if needed.
    text_parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
    if not text_parts:
        raise RuntimeError("Anthropic response had no text blocks")
    result = _parse_json_block(text_parts[0])
    result.setdefault("__usage__", {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "cache_creation_input_tokens": getattr(resp.usage, "cache_creation_input_tokens", 0),
        "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", 0),
    })
    return result


def _extract_via_openai(
    images: list[bytes], meta: PatientMeta, topic: str, emphasis: str
) -> dict:
    """OpenAI gpt-4o fallback — kept for environments without ANTHROPIC_API_KEY."""
    from openai import OpenAI

    client = OpenAI()
    content: list[dict] = [{"type": "text", "text": _user_content_text(meta, topic, emphasis)}]
    for img_bytes in images:
        b64 = base64.b64encode(img_bytes).decode("ascii")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            }
        )

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": content},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return json.loads(resp.choices[0].message.content)


def extract_structured(
    images: list[bytes], meta: PatientMeta, topic: str, emphasis: str
) -> dict:
    """Extract structured lab-report data from PDF images.

    Backend selection:
    - ANTHROPIC_API_KEY set → Claude Sonnet 4.5 with SKILL.md system prompt
      (preferred — consistent with clinic-content-system, prompt caching).
    - else OPENAI_API_KEY set → gpt-4o (legacy fallback).
    - else RuntimeError.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return _extract_via_anthropic(images, meta, topic, emphasis)
    if os.environ.get("OPENAI_API_KEY"):
        return _extract_via_openai(images, meta, topic, emphasis)
    raise RuntimeError(
        "Neither ANTHROPIC_API_KEY nor OPENAI_API_KEY is set — "
        "source ~/clinic-content-system/_migration/.env before calling intake."
    )


# --------------------------------------------------------------------------- #
# Step 4-5: HTML render + Playwright PDF
# --------------------------------------------------------------------------- #

def render_html(
    extracted: dict, meta: PatientMeta, topic: str, slug: str, *, base_url: str = BASE_URL
) -> str:
    env = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("lab_report.html.j2")
    age_sex = extracted.get("age_sex") or meta.age_sex or ""
    report_title = extracted.get("report_title") or DEFAULT_TITLES.get(
        topic, "검사 결과 안내"
    )
    eyebrow_label = extracted.get("eyebrow_label") or TOPIC_LABELS.get(
        topic, topic.upper().replace("-", " ")
    )
    og_description = (
        extracted.get("og_description")
        or f"{report_title} — {meta.name} · {meta.exam_date}"
    )

    html = template.render(
        base_url=base_url,
        slug=slug,
        topic=topic,
        report_title=report_title,
        eyebrow_label=eyebrow_label,
        og_description=og_description,
        patient_name=meta.name,
        chart_no=meta.chart_no,
        exam_date=meta.exam_date,
        doctor=meta.doctor,
        age_sex=age_sex,
        stats=extracted.get("stats", []),
        details=extracted.get("details", []),
        meanings=extracted.get("meanings", []),
        recommendations=extracted.get("recommendations", []),
    )
    # lab-reports privacy: ensure noindex (template already has it, but
    # inject_noindex_meta is idempotent — defense in depth)
    return inject_noindex_meta(html)


def build_pdf(html_path: Path, out_pdf: Path, out_preview: Path) -> dict:
    """Render the saved HTML to A4 PDF + preview PNG via Playwright.

    Runs the same HANDOUT_VALIDATOR_JS that build.py uses so overflow /
    bbox issues are caught before the user gets a broken layout.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            ctx = browser.new_context(viewport={"width": 820, "height": 1160})
            page = ctx.new_page()
            page.goto(f"file://{html_path}")
            page.wait_for_load_state("networkidle")
            issues = page.evaluate(HANDOUT_VALIDATOR_JS)
            pw_render(
                page,
                f"file://{html_path}",
                out_pdf=out_pdf,
                out_preview=out_preview,
                fmt="a4-portrait",
            )
            ctx.close()
        finally:
            browser.close()
    return {"layout_issues": issues}


# --------------------------------------------------------------------------- #
# Step 6: Notion sync (optional)
# --------------------------------------------------------------------------- #

def register_notion(
    *,
    meta: PatientMeta,
    topic: str,
    slug: str,
    note: str,
    base_url: str = BASE_URL,
) -> tuple[str, str]:
    """Upsert a row in 🧪 환자 검사결과 DB; patient master page is auto-linked."""
    from _notion_sync import upsert  # imported here to avoid hard dep when Notion off

    return upsert(
        kind="lab-reports",
        slug=slug,
        html_url=f"{base_url}/lab-reports/{topic}/{slug}/",
        pdf_url=f"{base_url}/output/lab-reports/{slug}.pdf",
        today_iso=meta.exam_date,
        patient_name=meta.name,
        chart_no=meta.chart_no,
        exam_date=meta.exam_date,
        doctor=meta.doctor,
        note=note,
    )


# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #

def run_intake(
    *,
    pdf_bytes: bytes,
    meta: PatientMeta,
    topic: str,
    emphasis: str,
    register_to_notion: bool = False,
) -> IntakeResult:
    if not topic:
        raise ValueError("topic is required (e.g. 'general-checkup')")
    if not meta.name or not meta.chart_no:
        raise ValueError("patient name and chart_no are required")

    images = pdf_to_images(pdf_bytes)
    if not images:
        raise ValueError("PDF has no pages")

    extracted = extract_structured(images, meta, topic, emphasis)

    slug = lab_hash_slug(meta.chart_no, meta.name, topic)

    html_dir = ROOT / "lab-reports" / topic / slug
    html_dir.mkdir(parents=True, exist_ok=True)
    html_path = html_dir / "index.html"
    html_path.write_text(render_html(extracted, meta, topic, slug), encoding="utf-8")

    out_dir = ROOT / "output" / "lab-reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{slug}.pdf"
    preview_path = out_dir / f"{slug}-preview.png"
    build_info = build_pdf(html_path, pdf_path, preview_path)

    result = IntakeResult(
        slug=slug,
        topic=topic,
        html_path=html_path,
        pdf_path=pdf_path,
        preview_path=preview_path,
        extracted=extracted,
    )

    if register_to_notion and os.environ.get("NOTION_TOKEN"):
        note = emphasis.strip().splitlines()[0][:200] if emphasis.strip() else (
            extracted.get("og_description") or ""
        )
        action, page_id = register_notion(
            meta=meta, topic=topic, slug=slug, note=note
        )
        result.notion_action = action
        result.notion_page_id = page_id

    if build_info.get("layout_issues"):
        # Surface to caller; UI can decide to show warning
        result.extracted["__layout_issues__"] = build_info["layout_issues"]

    return result
