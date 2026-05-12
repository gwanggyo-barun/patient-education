"""End-to-end smoke test for tools/web_intake without calling OpenAI.

Patches `extract_structured` to return a fixed JSON (modeled on the real
박순정 결과지) so the rest of the pipeline — Jinja render, Playwright A4
PDF, Notion upsert + 환자 마스터 relation — can be exercised offline.

Uses a synthetic patient ([TEST] 환자_웹앱검증 / 99999) so production rows
aren't polluted. Archives the Notion row + patient page on success.
"""
from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(ROOT / "tools" / "web_intake"))

from intake import PatientMeta, run_intake  # noqa: E402
from _notion_sync import _api, _ensure_patient_page, PATIENT_DB_ID  # noqa: E402


MOCK_EXTRACTED = {
    "report_title": "종합검사 결과 안내",
    "eyebrow_label": "GENERAL CHECKUP",
    "og_description": "[TEST] 환자_웹앱검증 — 종합검사 결과 한 장 요약",
    "age_sex": "F/53",
    "stats": [
        {"label": "총콜레스테롤", "value": "209", "unit": "mg/dL · 경계역", "status": "high"},
        {"label": "당화혈색소 (HbA1c)", "value": "5.5", "unit": "% · 정상", "status": "ok"},
        {"label": "신장기능 (eGFR)", "value": "113", "unit": "mL/min · 우수", "status": "ok"},
        {"label": "갑상선 (TSH)", "value": "1.42", "unit": "μIU/mL · 정상", "status": "ok"},
    ],
    "details": [
        {"label": "지질 (TC / LDL / HDL / TG)", "value": "209 / 127 / 62 / 96",
         "range": "<200 / <130 / 40~60 / <150", "badge": "경계", "badge_class": "high"},
        {"label": "혈당 / 당화혈색소", "value": "97 / 5.5",
         "range": "<100 mg/dL · ≤5.6%", "badge": "정상", "badge_class": ""},
        {"label": "간기능 (AST/ALT/ALP/γ-GT)", "value": "19 / 23 / 60 / 17",
         "range": "정상 범위", "badge": "정상", "badge_class": ""},
        {"label": "신장 (Cr / eGFR / BUN)", "value": "0.48 / 113 / 15.3",
         "range": "eGFR > 59 우수", "badge": "정상", "badge_class": ""},
        {"label": "전해질·CBC·갑상선", "value": "Na 140·K 4.4 · Hb 13.2·WBC 5.7 · TSH 1.42",
         "range": "모두 정상", "badge": "정상", "badge_class": ""},
        {"label": "B/C형 간염 · 염증", "value": "HBs Ab+ 19.8 / HCV(-) · CRP 0.06",
         "range": "B형 면역 ✓ · 정상", "badge": "정상", "badge_class": ""},
    ],
    "meanings": [
        "<strong>전반적으로 매우 양호</strong> — 간·신장·혈당·갑상선·CBC·소변 모두 정상",
        "<strong>총콜레스테롤 209 (경계역)</strong> — LDL 127·HDL 62는 안전, 식이·운동으로 관리 가능",
        "<strong>B형간염 항체 양성</strong> — 면역력 보유 (감염 없음)",
    ],
    "recommendations": [
        "<strong>식이</strong> — 포화지방 줄이고 등푸른 생선·견과류·식이섬유 늘리기",
        "<strong>운동</strong> — 주 150분 이상 유산소 + 근력 운동",
        "<strong>1년 후 재검</strong> — 지질 패널 재확인 (필요 시 6개월 후)",
    ],
}


def main() -> int:
    assert os.environ.get("NOTION_TOKEN"), "source _migration/.env first"

    # Use an existing rendered PDF as input bytes — fitz only needs valid PDF.
    sample_pdf = ROOT / "output" / "lab-reports" / "969f64d2bc.pdf"
    pdf_bytes = sample_pdf.read_bytes()

    meta = PatientMeta(
        name="[TEST] 환자_웹앱검증",
        chart_no="99999",
        exam_date=date.today().isoformat(),
        doctor="정지환",
    )

    with patch("intake.extract_structured", return_value=MOCK_EXTRACTED):
        result = run_intake(
            pdf_bytes=pdf_bytes,
            meta=meta,
            topic="general-checkup",
            emphasis="총콜레스테롤 209 경계역, 식이·운동 관리 강조",
            register_to_notion=True,
        )

    print(f"slug:         {result.slug}")
    print(f"html_path:    {result.html_path}")
    print(f"pdf_path:     {result.pdf_path} ({result.pdf_path.stat().st_size//1024} KB)")
    print(f"preview_path: {result.preview_path} ({result.preview_path.stat().st_size//1024} KB)")
    print(f"notion:       {result.notion_action} {result.notion_page_id}")

    assert result.html_path.exists()
    assert result.pdf_path.exists()
    assert result.pdf_path.stat().st_size > 100_000, "PDF too small — render likely failed"

    # Patient master page should now contain this test row in 검사결과.
    # Notion is eventually consistent — give the relation index a few seconds
    # to catch up before asserting (verified ~3s is enough in dev).
    if result.notion_page_id:
        import time
        time.sleep(4)
        patient_pid = _ensure_patient_page("99999", "[TEST] 환자_웹앱검증")
        page = _api("GET", f"/pages/{patient_pid}", None)
        rel = page.get("properties", {}).get("검사결과", {}).get("relation", [])
        print(f"patient master 검사결과 relation count: {len(rel)}")
        assert any(r["id"].replace("-", "") == result.notion_page_id.replace("-", "")
                   for r in rel), "lab-report row not linked from patient master"
        print("✅ patient master correctly linked to lab-report row")

        # Cleanup: archive both the lab-report row and the test patient
        _api("PATCH", f"/pages/{result.notion_page_id}", {"archived": True})
        _api("PATCH", f"/pages/{patient_pid}", {"archived": True})
        print(f"cleanup: archived lab-report row {result.notion_page_id} + patient {patient_pid}")

    # Cleanup local artifacts
    result.html_path.unlink(missing_ok=True)
    if result.html_path.parent.exists() and not any(result.html_path.parent.iterdir()):
        result.html_path.parent.rmdir()
    result.pdf_path.unlink(missing_ok=True)
    result.preview_path.unlink(missing_ok=True)
    print("cleanup: local artifacts removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
