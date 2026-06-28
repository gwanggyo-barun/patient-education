#!/usr/bin/env python3
"""Brand color-token compliance checker for clinic-content-system.

Enforces the design system rule (brand-design-system.md §2, §8):
  "색상은 정의된 토큰 7~8개 안에서만 사용한다."

Two violation classes:
  E-CVAR : a `var(--c-...)` reference. The real token names are `--color-...`
           (defined in shared/design-tokens.css). `--c-*` tokens DO NOT EXIST,
           so they silently fall back to a hardcoded hex and the element is
           decoupled from the design SoT (brand color changes won't propagate).
  E-HEX  : a raw hex color literal that is NOT a brand token value and not an
           allowed neutral (white/black). These are off-brand colors (e.g. the
           old rainbow body-map) or hardcoded copies of brand hexes that should
           be `var(--color-*)` so they track the SoT.

Allowed without flagging:
  - brand token hex values parsed live from design-tokens.css
  - pure white / black / transparent
  - hex inside the footer QR <svg> path (generated, navy brand fill)
  - <meta name="theme-color"> (brand navy; HTML attr can't take a CSS var)

Usage:
  python3 -m shared._check_tokens <path-or-dir> [more ...]
  python3 -m shared._check_tokens            # defaults to decks/ handouts/ lab-reports/
Exit code 0 = clean, 1 = violations (so build.py / CI can gate on it).
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS_CSS = os.path.join(ROOT, "shared", "design-tokens.css")

HEX_RE = re.compile(r"#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?\b")
CVAR_RE = re.compile(r"var\(\s*--c-[a-z0-9-]+", re.I)
NEUTRALS = {"#fff", "#ffffff", "#000", "#000000"}


def _norm(h):
    h = h.lower()
    if len(h) == 4:  # #abc -> #aabbcc
        h = "#" + "".join(c * 2 for c in h[1:])
    return h


def brand_hexes():
    """Live-parse allowed hex values from design-tokens.css (--color-* + greys)."""
    allowed = set(NEUTRALS)
    try:
        css = open(TOKENS_CSS, encoding="utf-8").read()
    except OSError:
        return allowed
    for m in re.finditer(r"--[a-z0-9-]+:\s*(#[0-9A-Fa-f]{3,6})", css):
        allowed.add(_norm(m.group(1)))
    return allowed


def _strip_allowed_contexts(html):
    """Blank out regions where raw hex is legitimately unavoidable so they
    don't trip E-HEX: the QR <svg> block and the theme-color meta tag."""
    html = re.sub(r"<svg\b.*?</svg>", " ", html, flags=re.I | re.S)
    html = re.sub(r'<meta[^>]*theme-color[^>]*>', " ", html, flags=re.I)
    return html


def check_file(path, allowed):
    issues = []
    raw = open(path, encoding="utf-8").read()
    # E-CVAR: scan raw (line numbers meaningful)
    for i, line in enumerate(raw.splitlines(), 1):
        if CVAR_RE.search(line):
            for tok in CVAR_RE.findall(line):
                issues.append((i, "E-CVAR", tok + ")",
                               "존재하지 않는 토큰 — var(--color-*) 로 교체"))
    # E-HEX: scan with allowed contexts stripped
    scrubbed = _strip_allowed_contexts(raw)
    scrubbed_lines = scrubbed.splitlines()
    for i, line in enumerate(scrubbed_lines, 1):
        for h in HEX_RE.findall(line):
            if _norm(h) not in allowed:
                issues.append((i, "E-HEX", h,
                               "비브랜드 색 — var(--color-*) 토큰 사용"))
    return issues


def iter_targets(args):
    paths = args or [os.path.join(ROOT, d) for d in ("decks", "handouts", "lab-reports")]
    for p in paths:
        if os.path.isdir(p):
            for dirpath, _, files in os.walk(p):
                for f in files:
                    if f == "index.html":
                        yield os.path.join(dirpath, f)
        elif p.endswith(".html") and os.path.exists(p):
            yield p


def main(argv):
    allowed = brand_hexes()
    total_files = 0
    bad_files = 0
    total_issues = 0
    for path in sorted(iter_targets(argv)):
        total_files += 1
        issues = check_file(path, allowed)
        if not issues:
            continue
        bad_files += 1
        total_issues += len(issues)
        rel = os.path.relpath(path, ROOT)
        print(f"\n✗ {rel}")
        for ln, code, tok, hint in issues[:40]:
            print(f"    {code} L{ln}: {tok}  — {hint}")
        if len(issues) > 40:
            print(f"    … +{len(issues) - 40} more")
    print("\n" + "-" * 60)
    if total_issues:
        print(f"FAIL: {total_issues} color-token violations in {bad_files}/{total_files} files")
        print(f"(allowed brand hexes: {len(allowed)} parsed from design-tokens.css)")
        return 1
    print(f"OK: {total_files} files, brand color tokens clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
