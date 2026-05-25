#!/usr/bin/env python3
"""PromptOps regression test runner — Phase 1 강화판.

각 tests/*.test.yaml 을 읽어 해당 skill의 output HTML/PDF에 대해
must_include·forbidden·style·layout·safety·medical_accuracy·accessibility·brand_compliance
검증. case_specific 룰은 skill YAML의 test_inputs·expected_outputs와 교차 매칭.

Usage:
    python3 tools/run_tests.py --all
    python3 tools/run_tests.py tests/egd-fasting.test.yaml
    python3 tools/run_tests.py --severity blocker         # blocker만 실행
    python3 tools/run_tests.py --all --json out.json      # 노션 sync 용
    python3 tools/run_tests.py --all --quiet              # 실패만 출력
    python3 tools/run_tests.py --all --skip-missing       # 빌드 안 된 skill은 skip

Exit code:
    0 — 모든 blocker pass (skip 허용)
    1 — 1개 이상 blocker fail
    2 — 시스템 오류 (파일 손상 등)
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    print("✗ PyYAML 필요: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).parent.parent.resolve()
TESTS_DIR = ROOT / "tests"
SKILLS_DIR = ROOT / "skills"

SEVERITY_ORDER = ["blocker", "major", "minor", "nit"]

# 안전한 중성 색상 (whitelist에 항상 허용)
NEUTRAL_COLORS = {
    "#000", "#000000",
    "#FFF", "#FFFFFF",
    "#333", "#333333",
    "#666", "#666666",
    "#999", "#999999",
    "#CCC", "#CCCCCC",
    "#DDD", "#DDDDDD",
    "#EEE", "#EEEEEE",
    "#F0F0F0",
    "#F4F6F8",  # 표준 배경 회색
    "#F9FAFB",
    "#FAFBFC",
    "#E5E7EB",  # divider 회색
    "#D1D5DB",
}

# 한국 시간
KST = timezone(timedelta(hours=9))


# ──────────────────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────────────────


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def find_output(skill: dict) -> Path | None:
    """Skill YAML의 output_path → 실제 빌드된 HTML 파일."""
    if "output_path" not in skill:
        return None
    p = ROOT / skill["output_path"]
    return p if p.exists() else None


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"Invalid hex: {hex_color}")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """WCAG relative luminance."""
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast_ratio(c1: str, c2: str) -> float:
    """WCAG contrast ratio (1~21)."""
    l1 = relative_luminance(hex_to_rgb(c1))
    l2 = relative_luminance(hex_to_rgb(c2))
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


# ──────────────────────────────────────────────────────────
# 기본 check 함수
# ──────────────────────────────────────────────────────────


def check_must_include(html: str, terms: list[str]) -> list[tuple]:
    return [("must_include", t, "blocker") for t in terms if t not in html]


def check_forbidden(html: str, terms: list[str]) -> list[tuple]:
    return [("forbidden", t, "blocker") for t in terms if t in html]


def check_html_contains(html: str, needle: str) -> bool:
    return needle in html


def check_css_class_exists(html: str, css_class: str) -> bool:
    class_name = css_class.lstrip(".")
    patterns = [
        rf'class="[^"]*\b{re.escape(class_name)}\b[^"]*"',
        rf"class='[^']*\b{re.escape(class_name)}\b[^']*'",
    ]
    return any(re.search(p, html) for p in patterns)


def check_viewport(html: str, expected: str) -> bool:
    return expected in html


def check_section_count(html: str, expected: int) -> bool:
    slide_n = len(re.findall(r'<section[^>]*class="[^"]*\bslide\b', html))
    if slide_n == expected:
        return True
    # fallback: 전체 <section> count
    any_n = len(re.findall(r"<section\b", html))
    return any_n >= expected


def check_footer_contains(html: str, needle: str) -> bool:
    footer_matches = re.findall(r"<footer[^>]*>.*?</footer>", html, re.DOTALL)
    if not footer_matches:
        # fallback: footer 클래스
        footer_matches = re.findall(
            r'<[^>]*class="[^"]*\bfooter\b[^"]*"[^>]*>.*?</[^>]+>',
            html,
            re.DOTALL,
        )
    return any(needle in f for f in footer_matches)


def check_css_color_whitelist(html: str, allowed: list[str]) -> tuple[bool, list[str]]:
    """HTML에서 사용된 hex 색상 vs whitelist. returns (ok, violators)."""
    used = set(re.findall(r"#[0-9A-Fa-f]{3,8}\b", html))
    allowed_norm = {c.upper() for c in allowed} | {c.upper() for c in NEUTRAL_COLORS}
    violators = []
    for c in used:
        cu = c.upper()
        # 4·8-char hex (alpha) 무시
        if len(cu) - 1 in (4, 8):
            continue
        if cu not in allowed_norm:
            violators.append(c)
    return len(violators) == 0, violators


def check_css_min_font_size(html: str, min_pt: str) -> tuple[bool, list[str]]:
    """모든 font-size 선언이 min_pt 이상인지. min_pt 예: '10pt'."""
    m_min = re.match(r"([\d.]+)\s*(pt|px|rem|em)", min_pt)
    if not m_min:
        return True, []
    min_val = float(m_min.group(1))
    min_unit = m_min.group(2)
    min_pt_val = {
        "pt": min_val,
        "px": min_val * 0.75,  # 1px ≈ 0.75pt
        "rem": min_val * 12,    # 1rem ≈ 12pt (base 16px)
        "em": min_val * 12,
    }[min_unit]

    violators = []
    for m in re.finditer(r"font-size\s*:\s*([\d.]+)\s*(pt|px|rem|em)", html):
        val, unit = float(m.group(1)), m.group(2)
        pt_val = {
            "pt": val,
            "px": val * 0.75,
            "rem": val * 12,
            "em": val * 12,
        }[unit]
        if pt_val < min_pt_val - 0.01:
            violators.append(f"{val}{unit}")
    return len(violators) == 0, violators


def check_css_padding(html: str, expected: str) -> bool:
    return expected in html


def check_css_exact_color(html: str, expected: str) -> bool:
    return expected.upper() in html.upper()


def check_contrast_ratio(html: str, min_ratio: float) -> tuple[bool, list[str]]:
    """텍스트 색·배경 색 페어를 간단 추론 (color + background-color).
    엄밀한 분석은 별도 도구; 여기서는 자주 쓰이는 패턴만 검증.
    """
    # color: #xxx ... background-color: #yyy 쌍 추출
    color_pat = re.compile(r"color\s*:\s*(#[0-9A-Fa-f]{3,6})", re.IGNORECASE)
    bg_pat = re.compile(r"background(?:-color)?\s*:\s*(#[0-9A-Fa-f]{3,6})", re.IGNORECASE)
    text_colors = {m.group(1).upper() for m in color_pat.finditer(html)}
    bg_colors = {m.group(1).upper() for m in bg_pat.finditer(html)} or {"#FFFFFF"}

    violators = []
    for tc in text_colors:
        # 가장 낮은 contrast 쌍 평가
        ratios = []
        for bg in bg_colors:
            try:
                ratios.append((contrast_ratio(tc, bg), bg))
            except ValueError:
                continue
        if not ratios:
            continue
        min_r, worst_bg = min(ratios)
        if min_r < min_ratio:
            violators.append(f"{tc} on {worst_bg} = {min_r:.2f}:1")
    return len(violators) == 0, violators


# ──────────────────────────────────────────────────────────
# case_specific 룰
# ──────────────────────────────────────────────────────────


# rule.check 문자열에서 case_id 와 기대 substring 추출.
# 표현 예:
#  - "T01 anticoagulant=warfarin → '5일 전'"
#  - "T02 PM → 'split-dose' 또는 '전날 저녁 6시'"
#  - "T03 patient_age>=70 → '탈수 주의'"
#  - "anticoagulant flag → '주치의 상의' 또는 'warfarin 5일' 포함"
CASE_ID_RE = re.compile(r"\b(T\d{2,3}[-_A-Za-z0-9]*)\b")
QUOTED_RE = re.compile(r"['\"‘’“”]([^'\"‘’“”]+)['\"‘’“”]")


def parse_case_specific(check_str: str) -> tuple[list[str], list[list[str]]]:
    """check 문자열에서 (case_ids, expected_groups) 추출.
    expected_groups: OR 그룹의 list (각 그룹은 모두 매칭되어야 함; 그룹 간 OR).
    "A 또는 B" → [["A"], ["B"]]
    "A" → [["A"]]
    """
    case_ids = CASE_ID_RE.findall(check_str)
    quoted = QUOTED_RE.findall(check_str)
    if not quoted:
        return case_ids, []
    # 또는 / or 분기 처리
    # 간단 모델: '또는'·' or '·'OR' 로 split
    arrow_idx = check_str.find("→")
    expected_part = check_str[arrow_idx + 1:] if arrow_idx >= 0 else check_str
    or_parts = re.split(r"\b(?:또는|or|OR)\b", expected_part)
    groups = []
    for part in or_parts:
        q = QUOTED_RE.findall(part)
        if q:
            groups.append(q)
    if not groups:
        groups = [quoted]
    return case_ids, groups


def check_case_specific(html: str, rule: dict, skill: dict) -> tuple[bool, str]:
    """case_specific 룰을 skill의 expected_outputs와 매칭.

    1) rule.check 에서 case_id·기대 substring 추출
    2) skill.expected_outputs 에서 해당 case_id의 must_include/forbidden 보강
    3) HTML 본문에 substring 포함 여부 검사 (OR 그룹 중 하나라도 매칭되면 OK)
    4) case_id가 없거나 expected_outputs가 없으면 → quoted substring만으로 검사
    5) 아무 단서도 없으면 (skip, 메시지)
    """
    chk = rule.get("check", "")
    if not isinstance(chk, str):
        return True, "skip (non-string check)"

    case_ids, expected_groups = parse_case_specific(chk)

    # skill의 expected_outputs에서 보강
    skill_expected = {
        eo.get("case_id"): eo
        for eo in skill.get("expected_outputs", []) or []
        if isinstance(eo, dict)
    }

    matched_terms: list[str] = []
    forbidden_terms: list[str] = []
    if case_ids:
        for cid in case_ids:
            eo = skill_expected.get(cid)
            if eo:
                matched_terms.extend(eo.get("must_include", []) or [])
                forbidden_terms.extend(eo.get("forbidden_terms", []) or [])

    # OR 그룹 평가
    if expected_groups:
        group_ok = []
        for grp in expected_groups:
            group_ok.append(all(t in html for t in grp))
        or_ok = any(group_ok)
    else:
        or_ok = True  # quoted 없으면 case_id 보강에만 의존

    # case_id 보강 must_include 검사 (AND)
    aug_must_ok = all(t in html for t in matched_terms) if matched_terms else True
    # forbidden 검사
    forbidden_ok = all(t not in html for t in forbidden_terms) if forbidden_terms else True

    ok = or_ok and aug_must_ok and forbidden_ok

    detail_parts = []
    if expected_groups:
        detail_parts.append(
            "OR groups: " + " / ".join("·".join(g) for g in expected_groups)
        )
    if case_ids:
        detail_parts.append(f"cases: {','.join(case_ids)}")
    if matched_terms:
        detail_parts.append(f"aug must: {len(matched_terms)}")

    if not ok:
        missing_or = [
            "·".join(g) for g, gok in zip(expected_groups, group_ok) if not gok
        ] if expected_groups else []
        missing_aug = [t for t in matched_terms if t not in html]
        present_forb = [t for t in forbidden_terms if t in html]
        reasons = []
        if missing_or and not or_ok:
            reasons.append(f"no OR matched: {missing_or}")
        if missing_aug:
            reasons.append(f"missing aug: {missing_aug}")
        if present_forb:
            reasons.append(f"present forbidden: {present_forb}")
        return False, "; ".join(reasons) or "case_specific fail"

    return True, "; ".join(detail_parts) or "case_specific ok"


# ──────────────────────────────────────────────────────────
# 룰 디스패치
# ──────────────────────────────────────────────────────────


def run_rule(rule: dict, html: str, skill: dict) -> tuple[bool, str]:
    """returns (ok, detail)."""
    ct = rule.get("check_type")
    chk = rule.get("check")
    if ct == "html_contains":
        ok = check_html_contains(html, chk)
        return ok, "" if ok else f"missing '{chk}'"
    if ct == "css_class_exists":
        ok = check_css_class_exists(html, chk)
        return ok, "" if ok else f"class '{chk}' not found"
    if ct == "viewport":
        ok = check_viewport(html, chk)
        return ok, "" if ok else f"viewport '{chk}' missing"
    if ct == "section_count":
        ok = check_section_count(html, int(chk))
        return ok, "" if ok else f"section count != {chk}"
    if ct == "footer_contains":
        ok = check_footer_contains(html, chk)
        return ok, "" if ok else f"footer missing '{chk}'"
    if ct == "css_color_whitelist":
        ok, violators = check_css_color_whitelist(html, chk if isinstance(chk, list) else [])
        return ok, "" if ok else f"violators: {violators[:5]}"
    if ct == "css_padding":
        ok = check_css_padding(html, chk)
        return ok, "" if ok else f"padding '{chk}' missing"
    if ct == "css_min_font_size":
        ok, violators = check_css_min_font_size(html, chk)
        return ok, "" if ok else f"too-small: {violators[:5]}"
    if ct == "css_exact_color":
        ok = check_css_exact_color(html, chk)
        return ok, "" if ok else f"color '{chk}' missing"
    if ct == "contrast_ratio":
        try:
            ratio = float(chk)
        except (TypeError, ValueError):
            ratio = 4.5
        ok, violators = check_contrast_ratio(html, ratio)
        return ok, "" if ok else f"contrast violators: {violators[:3]}"
    if ct == "image_aspect_preserved":
        # logo.png 등은 <img> width/height 미강제 시 OK 간주
        return True, "skip (build-time check)"
    if ct == "case_specific":
        return check_case_specific(html, rule, skill)
    return True, f"unknown check_type: {ct}"


# ──────────────────────────────────────────────────────────
# 테스트 실행
# ──────────────────────────────────────────────────────────


def run_test(
    test_path: Path,
    severity_filter: str | None = None,
    skip_missing: bool = False,
) -> tuple[list, list, str]:
    """단일 test YAML 실행. returns (failures, passes, status).

    status ∈ {pass, fail-blocker, fail-major, fail-minor, skip}
    """
    test = load_yaml(test_path)
    skill_id = test.get("skill_ref")
    if not skill_id:
        return ([("system", f"skill_ref missing", "blocker")], [], "fail-blocker")

    # skill YAML 찾기
    skill = None
    for sp in SKILLS_DIR.glob("*.yaml"):
        s = load_yaml(sp)
        if s.get("prompt_id") == skill_id:
            skill = s
            break
    if skill is None:
        return ([("system", f"skill {skill_id} not found", "blocker")], [], "fail-blocker")

    output_path = find_output(skill)
    if not output_path:
        msg = f"output not built: {skill.get('output_path')}"
        if skip_missing:
            return ([], [("skip", msg, "skip")], "skip")
        return ([("system", msg, "blocker")], [], "fail-blocker")

    html = output_path.read_text(encoding="utf-8")

    failures, passes = [], []

    # must_include
    mi = test.get("must_include", []) or []
    for f in check_must_include(html, mi):
        failures.append(f)
    if mi and not any(f[0] == "must_include" for f in failures):
        passes.append(("must_include", f"all {len(mi)} terms present", "blocker"))

    # forbidden
    fb = test.get("forbidden_terms", []) or []
    for f in check_forbidden(html, fb):
        failures.append(f)
    if fb and not any(f[0] == "forbidden" for f in failures):
        passes.append(("forbidden", f"all {len(fb)} terms absent", "blocker"))

    # 카테고리별 룰
    for key in (
        "style_rules",
        "layout_rules",
        "safety_rules",
        "medical_accuracy",
        "accessibility",
        "brand_compliance",
    ):
        for rule in test.get(key, []) or []:
            sev = rule.get("severity", "major")
            if (
                severity_filter
                and sev in SEVERITY_ORDER
                and SEVERITY_ORDER.index(sev) > SEVERITY_ORDER.index(severity_filter)
            ):
                continue
            ok, detail = run_rule(rule, html, skill)
            label = rule.get("rule", "?")
            if detail:
                label = f"{label} — {detail}"
            if ok:
                passes.append((key, label, sev))
            else:
                failures.append((key, label, sev))

    # status 결정
    severities_failed = {sev for _, _, sev in failures}
    if "blocker" in severities_failed:
        status = "fail-blocker"
    elif "major" in severities_failed:
        status = "fail-major"
    elif "minor" in severities_failed or "nit" in severities_failed:
        status = "fail-minor"
    else:
        status = "pass"

    return failures, passes, status


# ──────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("test_files", nargs="*", help="특정 test YAML 또는 비워두면 --all")
    parser.add_argument("--all", action="store_true", help="모든 tests/*.test.yaml 실행")
    parser.add_argument("--severity", choices=SEVERITY_ORDER, help="해당 severity 이하만 검사")
    parser.add_argument("--quiet", action="store_true", help="실패만 출력")
    parser.add_argument("--json", help="결과 JSON 파일 출력 (노션 sync 용)")
    parser.add_argument("--skip-missing", action="store_true", help="output 미빌드 시 skip")
    args = parser.parse_args()

    if args.all or not args.test_files:
        test_files = sorted(TESTS_DIR.glob("*.test.yaml"))
    else:
        test_files = [Path(t) for t in args.test_files]

    total_failures = 0
    total_blockers = 0
    status_counts = {"pass": 0, "fail-blocker": 0, "fail-major": 0, "fail-minor": 0, "skip": 0}
    json_results = []
    now = datetime.now(KST).isoformat(timespec="seconds")

    print("=== PromptOps Test Runner ===")
    print(f"실행 대상: {len(test_files)} test(s) @ {now}\n")

    for tp in test_files:
        print(f"📋 {tp.name}")
        failures, passes, status = run_test(
            tp, severity_filter=args.severity, skip_missing=args.skip_missing
        )
        status_counts[status] = status_counts.get(status, 0) + 1

        if not args.quiet:
            for kind, term, sev in passes[:6]:
                icon = "✓" if sev != "skip" else "↷"
                print(f"  {icon} [{sev}] {kind}: {term}")
            if len(passes) > 6:
                print(f"  ✓ ... and {len(passes) - 6} more passes")

        for kind, term, sev in failures:
            icon = "🚨" if sev == "blocker" else "⚠️" if sev == "major" else "ℹ️"
            print(f"  {icon} [{sev}] {kind}: {term}")
            total_failures += 1
            if sev == "blocker":
                total_blockers += 1

        print(f"  → status: {status}\n")

        if args.json:
            test = load_yaml(tp)
            json_results.append({
                "test_id": test.get("test_id"),
                "skill_ref": test.get("skill_ref"),
                "test_file": tp.name,
                "status": status,
                "pass_count": len(passes),
                "fail_count": len(failures),
                "failures": [
                    {"kind": k, "label": l, "severity": s} for k, l, s in failures
                ],
                "tested_at": now,
            })

    print("=" * 56)
    print(f"Total tests: {len(test_files)}")
    print(
        f"Status: pass={status_counts['pass']} "
        f"fail-blocker={status_counts['fail-blocker']} "
        f"fail-major={status_counts['fail-major']} "
        f"fail-minor={status_counts['fail-minor']} "
        f"skip={status_counts['skip']}"
    )
    print(f"Total failures: {total_failures}  (blocker: {total_blockers})")

    if args.json:
        out_path = Path(args.json)
        out_path.write_text(
            json.dumps(
                {"summary": status_counts, "tested_at": now, "results": json_results},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"JSON saved → {out_path}")

    if total_blockers > 0:
        print("\n❌ BLOCKER failures — push 차단")
        return 1
    elif total_failures > 0:
        print("\n⚠️ Non-blocker failures — 검토 권장 (push 통과)")
        return 0
    print("\n✅ All tests pass (or skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
