"""Quality Gate — Multi-Agent Quality Pipeline 의 결정적 검증 + PII redaction 도우미.

본 모듈은 integrator (메인 Claude) 가 Stage C/D/F 에서 호출하는 결정적 보조 함수 모음:
- run_deterministic_gate(): build.py 사전 검증 + _validate_layout + _visual_audit 묶음
- redact_pii(): critique 로그 저장 전 PII 패턴 치환
- log_critique(): _local/quality-logs/critique-YYYY-MM-DD.jsonl 에 추가 (redacted)

reference/multi-agent-quality.md 가 본 모듈의 사양 SoT. 룰 변경 시 본 모듈도 갱신.

실제 LLM 호출은 integrator 가 Agent 도구로 수행하며 본 모듈은 *결정적 부분만* 담당한다.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent  # ~/clinic-content-system/
LOG_DIR = ROOT / "_local" / "quality-logs"
KST = timezone(timedelta(hours=9))


# ---------------------------------------------------------------------------
# Deterministic gate
# ---------------------------------------------------------------------------


@dataclass
class GateResult:
    passed: bool
    steps: list[dict[str, Any]] = field(default_factory=list)

    def to_context(self) -> str:
        """integrator 가 Stage D specialist 호출 시 컨텍스트로 전달할 텍스트."""
        lines = [f"deterministic_gate: {'PASS' if self.passed else 'FAIL'}"]
        for step in self.steps:
            lines.append(
                f"  [{step['name']}] rc={step['returncode']} ({step.get('summary', '')})"
            )
            if step.get("output_tail"):
                lines.append("    " + step["output_tail"].replace("\n", "\n    "))
        return "\n".join(lines)


def _run(cmd: list[str], cwd: Path = ROOT) -> dict[str, Any]:
    proc = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, check=False
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    tail_lines = out.strip().splitlines()[-12:]
    return {
        "name": " ".join(cmd[:3]),
        "returncode": proc.returncode,
        "summary": "ok" if proc.returncode == 0 else "fail",
        "output_tail": "\n".join(tail_lines),
    }


def run_deterministic_gate(
    html_path: str | None = None,
    skip_build: bool = False,
    skip_visual_audit: bool = True,  # visual_audit 는 네트워크 필요 — push 후 별도 실행이 기본
) -> GateResult:
    """Stage C/F 에서 호출. build + validate_layout + (optional) visual_audit 묶음.

    Args:
        html_path: 단일 파일 검증만 하고 싶을 때. None 이면 전체.
        skip_build: HTML 만 작성하고 build.py 는 별도 호출할 때 True.
        skip_visual_audit: 기본 True. 라이브 push 후 별도 검증 권장.
    """
    steps: list[dict[str, Any]] = []
    passed = True

    if html_path:
        step = _run([sys.executable, "-m", "shared._validate_layout", html_path])
    else:
        step = _run([sys.executable, "-m", "shared._validate_layout"])
    steps.append(step)
    if step["returncode"] != 0:
        passed = False

    if passed and not skip_build:
        step = _run([sys.executable, "build.py"])
        steps.append(step)
        if step["returncode"] != 0:
            passed = False

    if passed and not skip_visual_audit:
        step = _run([sys.executable, "-m", "shared._visual_audit"])
        steps.append(step)
        if step["returncode"] != 0:
            passed = False

    return GateResult(passed=passed, steps=steps)


# ---------------------------------------------------------------------------
# PII redaction
# ---------------------------------------------------------------------------


PII_PATTERNS = [
    (re.compile(r"\[(\d{4,6})\]"), "[REDACTED-CHART]"),
    (re.compile(r"\d{3}-\d{3,4}-\d{4}"), "[REDACTED-PHONE]"),
    (re.compile(r"\d{6}-\d{7}"), "[REDACTED-RRN]"),
    (re.compile(r"(?:19|20)\d{2}[-./]?\d{2}[-./]?\d{2}"), "[REDACTED-DOB]"),
    (re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"), "[REDACTED-EMAIL]"),
]


def redact_pii(
    text: str, patient_names: list[str] | None = None
) -> str:
    """Critique 산출물 텍스트의 PII 패턴을 [REDACTED-*] 로 치환.

    Args:
        text: redact 대상 문자열
        patient_names: 추가로 치환할 환자명 리스트 (TARGETS 의 patient_name 필드)
    """
    redacted = text
    for pattern, repl in PII_PATTERNS:
        redacted = pattern.sub(repl, redacted)
    if patient_names:
        for name in patient_names:
            if name and len(name) >= 2:
                redacted = redacted.replace(name, "[REDACTED-NAME]")
    return redacted


def redact_findings_summary(
    summary: str, patient_names: list[str] | None = None
) -> str:
    """Specialist summary 문자열을 redact."""
    return redact_pii(summary, patient_names=patient_names)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def log_critique(
    topic_slug: str,
    kind: str,
    stage: str,
    iteration: int,
    specialists: list[dict[str, Any]],
    integrator_decision: dict[str, int],
    patient_names: list[str] | None = None,
) -> Path:
    """Critique 라운드 결과를 _local/quality-logs/ 에 한 줄 append.

    Findings 본문 자체는 저장하지 않음. severity counts + redacted summary 만.

    Args:
        topic_slug: 콘텐츠 슬러그
        kind: decks / handouts / lab-reports
        stage: 보통 "critique"
        iteration: 1, 2, 3 ...
        specialists: 각 specialist 의 {"agent", "findings_count", "summary"} 리스트
        integrator_decision: {"fixed": N, "rejected": N, "deferred": N}
        patient_names: redaction 보조 (lab-reports 한정)
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(KST).date().isoformat()
    log_path = LOG_DIR / f"critique-{today}.jsonl"

    redacted_specialists = []
    for spec in specialists:
        redacted_specialists.append(
            {
                "agent": spec["agent"],
                "findings_count": spec.get("findings_count", {}),
                "summary_redacted": redact_findings_summary(
                    spec.get("summary", ""), patient_names=patient_names
                ),
            }
        )

    entry = {
        "timestamp": datetime.now(KST).isoformat(),
        "topic_slug": topic_slug,
        "kind": kind,
        "stage": stage,
        "iteration": iteration,
        "specialists": redacted_specialists,
        "integrator_decision": integrator_decision,
    }

    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return log_path


# ---------------------------------------------------------------------------
# Specialist roster (mirror of reference/multi-agent-quality.md §2)
# ---------------------------------------------------------------------------


SPECIALIST_ROSTER: dict[str, list[str]] = {
    "decks": [
        "clinical-accuracy",
        "patient-readability",
        "visual-design",
        "narrative-flow",
    ],
    "handouts": [
        "clinical-accuracy",
        "patient-readability",
        "visual-design",
        "density-hierarchy",
    ],
    "lab-reports": [
        "clinical-accuracy",
        "patient-readability",
        "visual-design",
        "data-accuracy",
        "privacy-ops",
    ],
}


def roster_for(
    kind: str,
    topic: str | None = None,
    target_audience: str = "patient",
) -> list[str]:
    """주어진 kind/topic 에 호출할 specialist 목록.

    Args:
        kind: decks / handouts / lab-reports
        topic: optional topic slug. lab-reports/health-checkup 에서 extra specialist 추가.
        target_audience: 'clinician' 이면 patient-readability skip.
    """
    base = list(SPECIALIST_ROSTER.get(kind, []))
    if kind == "lab-reports" and topic == "health-checkup":
        base.append("checkup-completeness")
    if target_audience == "clinician" and "patient-readability" in base:
        base.remove("patient-readability")
    return base


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_help() -> None:
    print(
        "usage:\n"
        "  python3 tools/quality_gate.py gate [<html_path>]\n"
        "      run deterministic gate (validate_layout [+ build])\n"
        "  python3 tools/quality_gate.py redact <text>\n"
        "      print redacted version of <text>\n"
        "  python3 tools/quality_gate.py roster <kind> [<topic>] [clinician]\n"
        "      print specialist roster for kind/topic\n"
    )


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        _print_help()
        return 0

    cmd = argv[0]
    if cmd == "gate":
        html_path = argv[1] if len(argv) > 1 else None
        result = run_deterministic_gate(html_path=html_path, skip_build=False)
        print(result.to_context())
        return 0 if result.passed else 1
    if cmd == "redact":
        text = " ".join(argv[1:])
        print(redact_pii(text))
        return 0
    if cmd == "roster":
        kind = argv[1]
        topic = None
        audience = "patient"
        for arg in argv[2:]:
            if arg == "clinician":
                audience = "clinician"
            else:
                topic = arg
        print("\n".join(roster_for(kind, topic=topic, target_audience=audience)))
        return 0

    _print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
