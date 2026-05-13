"""End-to-end test for tools/web_intake with the **real** Anthropic vision call.

Unlike _migration/test_web_intake_e2e.py (which mocks the LLM), this script
actually pays for a Claude Sonnet 4.5 vision call to verify the full happy
path: SKILL.md system prompt with prompt caching → vision OCR of a real lab
PDF → structured JSON → Jinja render → Playwright A4 PDF → Notion upsert
→ patient master relation accumulates.

Uses a synthetic patient ([TEST] 실vision검증 / 88888) so production rows
aren't polluted. Archives all created Notion artifacts on success.

Run once after migrating intake.py to the Anthropic backend.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(ROOT / "tools" / "web_intake"))

from intake import PatientMeta, run_intake  # noqa: E402
from _notion_sync import _api, _ensure_patient_page  # noqa: E402


def main() -> int:
    assert os.environ.get("NOTION_TOKEN"), "source _migration/.env first"
    assert os.environ.get("ANTHROPIC_API_KEY"), "ANTHROPIC_API_KEY required"

    sample_pdf = ROOT / "output" / "lab-reports" / "969f64d2bc.pdf"
    assert sample_pdf.exists(), f"sample PDF missing: {sample_pdf}"
    pdf_bytes = sample_pdf.read_bytes()
    print(f"input PDF: {sample_pdf.name} ({len(pdf_bytes)//1024} KB)")

    meta = PatientMeta(
        name="[TEST] 실vision검증",
        chart_no="88888",
        exam_date=date.today().isoformat(),
        doctor="정지환",
    )

    print(f"calling Claude Sonnet 4.5 vision (this takes ~15-25s)...")
    t0 = time.time()
    result = run_intake(
        pdf_bytes=pdf_bytes,
        meta=meta,
        topic="general-checkup",
        emphasis=(
            "총콜레스테롤 209로 경계역, 식이·운동 관리 강조. "
            "HbA1c 5.5/eGFR 113/TSH 1.42는 모두 정상이라 안심 메시지 같이 전달."
        ),
        register_to_notion=True,
    )
    elapsed = time.time() - t0
    print(f"vision call complete in {elapsed:.1f}s")

    # ───────── Assertions on structured output ─────────
    usage = result.extracted.get("__usage__", {})
    print(
        f"usage: input={usage.get('input_tokens')} "
        f"cache_create={usage.get('cache_creation_input_tokens')} "
        f"cache_read={usage.get('cache_read_input_tokens')} "
        f"output={usage.get('output_tokens')}"
    )

    stats = result.extracted.get("stats", [])
    details = result.extracted.get("details", [])
    meanings = result.extracted.get("meanings", [])
    recs = result.extracted.get("recommendations", [])
    print(f"extracted shape: stats={len(stats)} details={len(details)} "
          f"meanings={len(meanings)} recs={len(recs)}")
    assert len(stats) == 4, f"expected 4 stats, got {len(stats)}"
    assert 5 <= len(details) <= 7, f"expected 5-7 details, got {len(details)}"
    assert len(meanings) == 3, f"expected 3 meanings, got {len(meanings)}"
    assert len(recs) == 3, f"expected 3 recs, got {len(recs)}"
    # Each stat must have label/value/status
    for s in stats:
        assert "label" in s and "value" in s and "status" in s, f"bad stat: {s}"
        assert s["status"] in {"ok", "high", "alert", "warn"}, f"bad status: {s['status']}"
    # 총콜레스테롤 should be extracted (강조점 + PDF에 분명 있음)
    chol_in_stats = any("콜레스테롤" in s.get("label", "") for s in stats)
    chol_in_details = any("콜레스테롤" in d.get("label", "") or
                          "지질" in d.get("label", "") for d in details)
    assert chol_in_stats or chol_in_details, "콜레스테롤 not surfaced anywhere"
    print(f"✅ structured JSON shape valid + 콜레스테롤 surfaced")

    # ───────── Files ─────────
    print(f"slug: {result.slug}")
    print(f"pdf:  {result.pdf_path} ({result.pdf_path.stat().st_size//1024} KB)")
    print(f"png:  {result.preview_path} ({result.preview_path.stat().st_size//1024} KB)")
    assert result.pdf_path.stat().st_size > 100_000, "PDF too small"

    # ───────── Notion: row + patient relation ─────────
    print(f"notion: {result.notion_action} {result.notion_page_id}")
    assert result.notion_page_id, "notion upsert returned no page_id"

    time.sleep(4)  # eventual consistency
    patient_pid = _ensure_patient_page("88888", "[TEST] 실vision검증")
    page = _api("GET", f"/pages/{patient_pid}", None)
    rel = page.get("properties", {}).get("검사결과", {}).get("relation", [])
    print(f"patient master 검사결과 relation count: {len(rel)}")
    assert any(
        r["id"].replace("-", "") == result.notion_page_id.replace("-", "")
        for r in rel
    ), "lab-report row not linked from patient master"
    print("✅ patient master correctly linked")

    # ───────── Cleanup ─────────
    _api("PATCH", f"/pages/{result.notion_page_id}", {"archived": True})
    _api("PATCH", f"/pages/{patient_pid}", {"archived": True})
    print(f"cleanup: archived row + patient page")

    result.html_path.unlink(missing_ok=True)
    if result.html_path.parent.exists() and not any(result.html_path.parent.iterdir()):
        result.html_path.parent.rmdir()
    result.pdf_path.unlink(missing_ok=True)
    result.preview_path.unlink(missing_ok=True)
    print("cleanup: local artifacts removed")

    # ───────── Dump extracted JSON for human review (without artifacts) ─────────
    print()
    print("=== extracted JSON (for human review) ===")
    review = {k: v for k, v in result.extracted.items() if k != "__usage__"}
    print(json.dumps(review, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
