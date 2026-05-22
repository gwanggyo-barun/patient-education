"""Validate health-checkup structured JSON before HTML rendering.

Usage:
  python3 tools/checkup_schema_validate.py path/to/checkup.json

This is intentionally small and dependency-free. It catches the mistakes that
most often break the health-checkup renderer: missing module inventory, unknown
status values, action-plan omissions, and source warnings shaped incorrectly.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

VALID_STATUS = {"ok", "warn", "alert", "normal", "low", "high", "borderline", ""}


def _as_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key, [])
    return value if isinstance(value, list) else []


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def validate(data: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    if not _as_list(data, "performed_tests"):
        issues.append("performed_tests must list every source-mentioned exam")

    overall = _as_list(data, "overall")
    if not 1 <= len(overall) <= 4:
        issues.append("overall must contain 1-4 verdict cells")
    for i, cell in enumerate(overall, 1):
        if not isinstance(cell, dict):
            issues.append(f"overall[{i}] must be an object")
            continue
        if not (cell.get("area") or cell.get("label")):
            issues.append(f"overall[{i}] missing area/label")
        if _status(cell.get("status")) not in VALID_STATUS:
            issues.append(f"overall[{i}] has invalid status: {cell.get('status')}")
        if not (cell.get("summary") or cell.get("unit")):
            issues.append(f"overall[{i}] missing patient-facing summary")

    for group in ("vitals", "labs", "urinalysis"):
        for i, row in enumerate(_as_list(data, group), 1):
            if not isinstance(row, dict):
                issues.append(f"{group}[{i}] must be an object")
                continue
            for required in ("label", "value"):
                if not row.get(required):
                    issues.append(f"{group}[{i}] missing {required}")
            if _status(row.get("status")) not in VALID_STATUS:
                issues.append(f"{group}[{i}] has invalid status: {row.get('status')}")

    for group in ("endoscopy", "ultrasound"):
        for i, block in enumerate(_as_list(data, group), 1):
            if not isinstance(block, dict):
                issues.append(f"{group}[{i}] must be an object")
                continue
            if not block.get("title"):
                issues.append(f"{group}[{i}] missing title")
            items = block.get("items")
            if not isinstance(items, list) or not items:
                issues.append(f"{group}[{i}] must have non-empty items[]")

    ekg = data.get("ekg")
    if ekg and not isinstance(ekg, dict):
        issues.append("ekg must be an object when present")
    elif isinstance(ekg, dict):
        if not ekg.get("title"):
            issues.append("ekg missing title")
        if ekg.get("items") and not isinstance(ekg["items"], list):
            issues.append("ekg.items must be a list")

    bmd = data.get("bmd")
    if bmd and not isinstance(bmd, dict):
        issues.append("bmd must be an object when present")
    elif isinstance(bmd, dict):
        if not (bmd.get("lumbar") or bmd.get("femoral")):
            issues.append("bmd must include lumbar or femoral when present")

    action_plan = _as_list(data, "action_plan")
    if not action_plan:
        issues.append("action_plan must include at least one next-step item")
    for i, rec in enumerate(action_plan[:5], 1):
        if not isinstance(rec, dict):
            issues.append(f"action_plan[{i}] must be an object")
            continue
        if not rec.get("title") or not rec.get("text"):
            issues.append(f"action_plan[{i}] missing title/text")

    source_warnings = data.get("source_warnings", [])
    if source_warnings and not isinstance(source_warnings, list):
        issues.append("source_warnings must be a list when present")

    return issues


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python3 tools/checkup_schema_validate.py path/to/checkup.json")
        return 2
    path = Path(argv[0])
    data = json.loads(path.read_text(encoding="utf-8"))
    if "structured_json" in data and isinstance(data["structured_json"], dict):
        data = data["structured_json"]
    issues = validate(data)
    if issues:
        print(f"FAIL: {path}")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
