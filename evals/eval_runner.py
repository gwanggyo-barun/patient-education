"""Eval runner — multi-agent vs baseline 비교 (synthetic fixtures only).

본 runner 는 *결정적 부분* (fixture load, metric 계산, 비교 보고) 만 담당하고,
실제 LLM 호출은 호스트 환경별 통합 지점에서 별도 수행한다. (Claude Code 환경에서는
integrator 가 Agent 도구로 specialist 를 호출하며, 본 runner 는 결과 JSON 만 받아 metric 계산.)

사용:
  python evals/eval_runner.py --mode multi-agent --kind decks
  python evals/eval_runner.py --mode baseline    --kind handouts
  python evals/eval_runner.py --compare          --kind decks
  python evals/eval_runner.py --list-fixtures

산출:
  evals/results/{mode}-{kind}-{timestamp}.jsonl  — run 결과
  evals/results/compare-{kind}-{timestamp}.md   — 비교 보고서
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "evals"
SYNTHETIC_DIR = EVAL_DIR / "synthetic"
RESULTS_DIR = EVAL_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Fixture load
# ---------------------------------------------------------------------------


def list_fixtures(kind: str | None = None) -> list[Path]:
    """synthetic/{kind}/*.json 또는 모든 kind 의 fixture path 리스트."""
    if kind:
        dirs = [SYNTHETIC_DIR / kind]
    else:
        dirs = [SYNTHETIC_DIR / k for k in ("decks", "handouts", "lab-reports")]
    out: list[Path] = []
    for d in dirs:
        if d.exists():
            out.extend(sorted(d.glob("*.json")))
    return out


def load_fixture(path: Path) -> dict:
    """Fixture JSON 로드. 기대 스키마:
    {
      "topic": "...",
      "kind": "decks" | "handouts" | "lab-reports",
      "doctor_input": "...",
      "expected_blockers": ["...short identifiers..."],  # optional ground truth
      "notes": "..."
    }
    """
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Metric 계산
# ---------------------------------------------------------------------------


def compute_metrics(run_records: list[dict]) -> dict:
    """run record 리스트로부터 aggregate metric 계산.

    record 스키마:
    {
      "fixture_id": "...",
      "iterations": 1,
      "wall_seconds": 47.2,
      "specialist_findings": [
        {"agent": "clinical-accuracy", "findings_count": {"blocker": 1, "major": 0, "minor": 2, "nit": 0}},
        ...
      ],
      "integrator_decisions": {"fixed": 3, "rejected": 1, "deferred": 0}
    }
    """
    if not run_records:
        return {"sample_size": 0}

    blocker_counts = []
    major_counts = []
    iterations = []
    walls = []
    fp_count = 0
    total_findings = 0

    for rec in run_records:
        agg = Counter()
        for spec in rec.get("specialist_findings", []):
            for sev, n in spec.get("findings_count", {}).items():
                agg[sev] += n
                total_findings += n
        blocker_counts.append(agg["blocker"])
        major_counts.append(agg["major"])
        iterations.append(rec.get("iterations", 1))
        walls.append(rec.get("wall_seconds", 0.0))
        fp_count += rec.get("integrator_decisions", {}).get("rejected", 0)

    return {
        "sample_size": len(run_records),
        "blocker_per_doc_mean": statistics.mean(blocker_counts),
        "blocker_per_doc_p90": _percentile(blocker_counts, 0.9),
        "major_per_doc_mean": statistics.mean(major_counts),
        "avg_iterations": statistics.mean(iterations),
        "avg_wall_seconds": statistics.mean(walls),
        "false_positive_rate": (fp_count / total_findings) if total_findings else 0.0,
    }


def _percentile(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    k = max(0, min(len(s) - 1, int(round(q * (len(s) - 1)))))
    return s[k]


# ---------------------------------------------------------------------------
# 비교 보고
# ---------------------------------------------------------------------------


def compare(baseline: dict, multi_agent: dict) -> str:
    """두 metric dict 를 받아 마크다운 비교 보고서 문자열 생성."""
    def fmt(v):
        if isinstance(v, float):
            return f"{v:.3f}"
        return str(v)

    keys = [
        "sample_size",
        "blocker_per_doc_mean",
        "blocker_per_doc_p90",
        "major_per_doc_mean",
        "avg_iterations",
        "avg_wall_seconds",
        "false_positive_rate",
    ]
    lines = ["# Multi-Agent Quality Pipeline — Eval Compare", ""]
    lines.append(f"_Generated: {datetime.now().isoformat(timespec='seconds')}_")
    lines.append("")
    lines.append("| metric | baseline | multi-agent | Δ |")
    lines.append("|---|---|---|---|")
    for k in keys:
        b = baseline.get(k, "—")
        m = multi_agent.get(k, "—")
        delta = (
            f"{(m - b):+.3f}"
            if isinstance(b, (int, float)) and isinstance(m, (int, float))
            else "—"
        )
        lines.append(f"| {k} | {fmt(b)} | {fmt(m)} | {delta} |")
    lines.append("")
    lines.append("## 해석")
    lines.append("- `blocker_per_doc_mean` 감소 = 멀티 에이전트가 blocker 를 사전에 잡아 push 직전 자료의 잔존 risk 감소.")
    lines.append("- `avg_iterations` 가 1.x 면 자동 수정 루프가 정착, 2 초과면 specialist 가 같은 issue 를 매번 잡는 패턴 — Stage B 작성 시 사전 회피 룰 추가 필요.")
    lines.append("- `false_positive_rate` 가 30% 초과면 specialist 프롬프트 정밀도 부족 — `reference/quality-agents/*.md` 의 severity 기준 명시 강화.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def save_results(mode: str, kind: str, records: list[dict]) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = RESULTS_DIR / f"{mode}-{kind}-{ts}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path


def load_latest(mode: str, kind: str) -> list[dict]:
    matches = sorted(RESULTS_DIR.glob(f"{mode}-{kind}-*.jsonl"))
    if not matches:
        return []
    latest = matches[-1]
    return [json.loads(line) for line in latest.read_text(encoding="utf-8").splitlines()]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_list_fixtures(args) -> int:
    for p in list_fixtures(args.kind):
        print(p.relative_to(ROOT))
    return 0


def cmd_run(args) -> int:
    """실제 LLM 호출은 호스트 환경별 통합 지점에서 수행하고 records 를 본 runner 에 전달.
    여기서는 stub — 통합 지점 binding 이 없을 때 0 record 만 저장.
    """
    fixtures = list_fixtures(args.kind)
    print(f"loaded {len(fixtures)} fixtures from synthetic/{args.kind or 'all'}")
    print(
        "NOTE: actual LLM calls are made by the host integrator (Claude Code Agent or "
        "Codex equivalent). This runner only persists records.\n"
        "Provide records via stdin (one JSON per line) or implement the host binding."
    )
    records: list[dict] = []
    if not sys.stdin.isatty():
        for line in sys.stdin:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    out = save_results(args.mode, args.kind or "all", records)
    metrics = compute_metrics(records)
    print(f"saved: {out.relative_to(ROOT)}")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


def cmd_compare(args) -> int:
    baseline_recs = load_latest("baseline", args.kind or "all")
    ma_recs = load_latest("multi-agent", args.kind or "all")
    if not baseline_recs or not ma_recs:
        print("need both baseline-*.jsonl and multi-agent-*.jsonl in evals/results/")
        return 1
    baseline = compute_metrics(baseline_recs)
    ma = compute_metrics(ma_recs)
    report = compare(baseline, ma)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = RESULTS_DIR / f"compare-{args.kind or 'all'}-{ts}.md"
    out.write_text(report, encoding="utf-8")
    print(f"saved: {out.relative_to(ROOT)}")
    print()
    print(report)
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list-fixtures")
    p_list.add_argument("--kind", choices=["decks", "handouts", "lab-reports"])
    p_list.set_defaults(func=cmd_list_fixtures)

    p_run = sub.add_parser("run")
    p_run.add_argument("--mode", choices=["baseline", "multi-agent"], required=True)
    p_run.add_argument("--kind", choices=["decks", "handouts", "lab-reports"])
    p_run.set_defaults(func=cmd_run)

    p_cmp = sub.add_parser("compare")
    p_cmp.add_argument("--kind", choices=["decks", "handouts", "lab-reports"])
    p_cmp.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
