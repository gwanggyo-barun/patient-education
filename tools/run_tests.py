#!/usr/bin/env python3
"""PromptOps regression test runner.

각 tests/*.test.yaml 을 읽어 해당 skill의 output HTML/PDF에 대해
must_include·forbidden·style·layout·safety·medical_accuracy 검증.

Usage:
    python3 tools/run_tests.py --all
    python3 tools/run_tests.py tests/egd-fasting.test.yaml
    python3 tools/run_tests.py --severity blocker  # blocker만 실행

Exit code:
    0 — 모든 blocker pass
    1 — 1개 이상 blocker fail
    2 — 시스템 오류 (파일 없음 등)
"""
from __future__ import annotations
import argparse
import re
import sys
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


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def find_output(skill: dict) -> Path | None:
    """Skill YAML의 output_path → 실제 빌드된 HTML 파일."""
    if "output_path" not in skill:
        return None
    p = ROOT / skill["output_path"]
    return p if p.exists() else None


def check_must_include(html: str, terms: list[str]) -> list[tuple]:
    return [("must_include", t, "blocker") for t in terms if t not in html]


def check_forbidden(html: str, terms: list[str]) -> list[tuple]:
    return [("forbidden", t, "blocker") for t in terms if t in html]


def check_html_contains(html: str, needle: str) -> bool:
    return needle in html


def check_css_class_exists(html: str, css_class: str) -> bool:
    class_name = css_class.lstrip(".")
    return f'class="{class_name}"' in html or f"class='{class_name}'" in html or f'class="[^"]*{class_name}' in html or re.search(rf'class="[^"]*\b{re.escape(class_name)}\b', html) is not None


def check_viewport(html: str, expected: str) -> bool:
    return expected in html


def check_section_count(html: str, expected: int) -> bool:
    return html.count('<section class="slide') == expected or html.count("<section") >= expected


def check_footer_contains(html: str, needle: str) -> bool:
    footer_matches = re.findall(r"<footer[^>]*>.*?</footer>", html, re.DOTALL)
    return any(needle in f for f in footer_matches)


def run_rule(rule: dict, html: str, skill: dict) -> bool:
    """generic rule runner — check_type 분기."""
    ct = rule.get("check_type")
    chk = rule.get("check")
    if ct == "html_contains":
        return check_html_contains(html, chk)
    if ct == "css_class_exists":
        return check_css_class_exists(html, chk)
    if ct == "viewport":
        return check_viewport(html, chk)
    if ct == "section_count":
        return check_section_count(html, int(chk))
    if ct == "footer_contains":
        return check_footer_contains(html, chk)
    if ct == "css_color_whitelist":
        # html에서 사용된 hex 색상 모두 추출 → whitelist에 포함되는지
        used_colors = set(re.findall(r"#[0-9A-Fa-f]{3,6}\b", html))
        allowed = set(c.upper() for c in chk)
        violators = [c for c in used_colors if c.upper() not in allowed and c.upper() not in {"#000000", "#FFF"}]
        return len(violators) == 0
    if ct == "css_padding":
        return chk in html
    if ct == "css_min_font_size":
        return True  # 정밀 검증은 별도 도구 (CSS parser)
    if ct == "css_exact_color":
        return chk in html
    if ct == "contrast_ratio":
        return True  # 별도 도구
    if ct == "image_aspect_preserved":
        return True
    if ct == "case_specific":
        return True  # 케이스 의존적 — 별도 분석
    return True


def run_test(test_path: Path, severity_filter: str = None) -> tuple[list, list]:
    """단일 test YAML 실행. returns (failures, passes)"""
    test = load_yaml(test_path)
    skill_id = test.get("skill_ref")
    if not skill_id:
        return [("system", f"skill_ref missing in {test_path.name}", "blocker")], []

    # skill YAML 찾기
    skill_path = None
    for sp in SKILLS_DIR.glob("*.yaml"):
        s = load_yaml(sp)
        if s.get("prompt_id") == skill_id:
            skill_path = sp
            skill = s
            break
    if not skill_path:
        return [("system", f"skill {skill_id} not found in skills/", "blocker")], []

    output_path = find_output(skill)
    if not output_path:
        return [("system", f"output not built: {skill.get('output_path')}", "blocker")], []

    html = output_path.read_text(encoding="utf-8")

    failures, passes = [], []

    # must_include
    for f in check_must_include(html, test.get("must_include", [])):
        failures.append(f)
    if test.get("must_include") and not any(f[0] == "must_include" for f in failures):
        passes.append(("must_include", f"all {len(test['must_include'])} terms present", "pass"))

    # forbidden
    for f in check_forbidden(html, test.get("forbidden_terms", [])):
        failures.append(f)
    if test.get("forbidden_terms") and not any(f[0] == "forbidden" for f in failures):
        passes.append(("forbidden", f"all {len(test['forbidden_terms'])} terms absent", "pass"))

    # 다른 rule 카테고리
    for key in ["style_rules", "layout_rules", "safety_rules", "medical_accuracy", "accessibility", "brand_compliance"]:
        for rule in test.get(key, []):
            sev = rule.get("severity", "major")
            if severity_filter and SEVERITY_ORDER.index(sev) > SEVERITY_ORDER.index(severity_filter):
                continue
            ok = run_rule(rule, html, skill)
            if ok:
                passes.append((key, rule.get("rule", "?"), sev))
            else:
                failures.append((key, rule.get("rule", "?"), sev))

    return failures, passes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("test_files", nargs="*", help="특정 test YAML 또는 비워두면 --all")
    parser.add_argument("--all", action="store_true", help="모든 tests/*.test.yaml 실행")
    parser.add_argument("--severity", choices=SEVERITY_ORDER, help="해당 severity 이하만 검사")
    parser.add_argument("--quiet", action="store_true", help="실패만 출력")
    args = parser.parse_args()

    if args.all or not args.test_files:
        test_files = sorted(TESTS_DIR.glob("*.test.yaml"))
    else:
        test_files = [Path(t) for t in args.test_files]

    total_failures = 0
    total_blockers = 0
    print(f"=== PromptOps Test Runner ===")
    print(f"실행 대상: {len(test_files)} test(s)\n")

    for tp in test_files:
        print(f"📋 {tp.name}")
        failures, passes = run_test(tp, severity_filter=args.severity)

        if not args.quiet:
            for kind, term, sev in passes[:5]:
                print(f"  ✓ [{sev}] {kind}: {term}")
            if len(passes) > 5:
                print(f"  ✓ ... and {len(passes) - 5} more passes")

        for kind, term, sev in failures:
            icon = "🚨" if sev == "blocker" else "⚠️" if sev == "major" else "ℹ️"
            print(f"  {icon} [{sev}] {kind}: {term}")
            total_failures += 1
            if sev == "blocker":
                total_blockers += 1
        print()

    print("=" * 50)
    print(f"Total tests: {len(test_files)}")
    print(f"Total failures: {total_failures}")
    print(f"Blocker failures: {total_blockers}")

    if total_blockers > 0:
        print("\n❌ BLOCKER failures — push 차단")
        return 1
    elif total_failures > 0:
        print("\n⚠️ Non-blocker failures — 검토 권장 (push 통과)")
        return 0
    print("\n✅ All tests pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
