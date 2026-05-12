"""One-shot backfill: link existing 🧪 환자 검사결과 rows to 👤 환자 마스터 pages.

Scans every row in the lab-reports DB, extracts (chart_no, patient_name) from
the title "[chart] name — note" (or from the 차트번호 column when present),
calls _ensure_patient_page() to find-or-create the patient page, then PATCHes
the row's 환자 relation property.

Idempotent: rows already linked are skipped. Rows whose title doesn't match
the standard "[chart] name" pattern (legacy malformed entries) are reported
and skipped — manual cleanup if needed.

Run once after the relation property is added. Future builds populate the
relation automatically via _notion_sync.upsert().
"""
import os
import re
import sys
from pathlib import Path

# Resolve shared/ module from repo root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared"))

from _notion_sync import _api, DBS, _ensure_patient_page  # noqa: E402


LAB_TITLE_RE = re.compile(r"^\[(\d+)\]\s*([^—\-]+?)(?:\s*[—\-]\s*(.+))?$")


def _extract_text(rich: list) -> str:
    return "".join(t.get("plain_text", "") for t in rich)


def main() -> int:
    db_id = DBS["lab-reports"]

    rows: list[dict] = []
    cursor: str | None = None
    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = _api("POST", f"/databases/{db_id}/query", body)
        rows.extend(res.get("results", []))
        if not res.get("has_more"):
            break
        cursor = res.get("next_cursor")

    print(f"Found {len(rows)} lab-report rows")

    linked = 0
    already = 0
    skipped = 0

    for row in rows:
        props = row.get("properties", {})
        title_rich = props.get("환자명", {}).get("title", [])
        title_text = _extract_text(title_rich).strip()
        chart_rich = props.get("차트번호", {}).get("rich_text", [])
        chart_no = _extract_text(chart_rich).strip()
        existing_rel = props.get("환자", {}).get("relation", [])

        m = LAB_TITLE_RE.match(title_text)
        if not m:
            print(f"  skip (unparseable title): {title_text!r}")
            skipped += 1
            continue

        chart_no = chart_no or m.group(1)
        patient_name = m.group(2).strip()

        if not chart_no.isdigit() or not patient_name:
            print(f"  skip (no chart/name): {title_text!r}")
            skipped += 1
            continue

        if existing_rel:
            already += 1
            continue

        patient_page_id = _ensure_patient_page(chart_no, patient_name)
        _api(
            "PATCH",
            f"/pages/{row['id']}",
            {
                "properties": {
                    "환자": {"relation": [{"id": patient_page_id}]},
                }
            },
        )
        print(f"  linked: [{chart_no}] {patient_name} → {patient_page_id}")
        linked += 1

    print()
    print(f"=== Backfill complete: {linked} linked, {already} already linked, {skipped} skipped ===")
    return 0


if __name__ == "__main__":
    if not os.environ.get("NOTION_TOKEN"):
        sys.exit("NOTION_TOKEN env var required. source _migration/.env first.")
    raise SystemExit(main())
