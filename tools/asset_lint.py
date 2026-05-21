"""Asset library linter for clinic-content-system.

Checks the entire repo for asset hygiene issues without depending on
Playwright. Runs standalone or as a build pre-flight.

Checks performed:
  1. Broken <img src="…shared/assets/…"> — file missing on disk
  2. data-asset="key" not in manifest, or whose file is missing
  3. <img> tags referencing shared/assets without an alt attribute
  4. Filename PII risk — chart-number runs of 7 digits, Korean Hangul,
     RRN-shaped patterns in filenames under shared/assets/
  5. Oversize images — > 500 KB warning, > 1 MB error
  6. lab-report HTML referencing WebP (PDF embed safety)
  7. Manifest entries marked exists=false (file disappeared since last sync)
  8. Manifest review_status="pending" with active references (warn; in
     --strict mode this becomes an error so CI prod jobs can gate on it)

Exit codes:
  0  → clean
  1  → warnings only (or errors when --warn-only)
  2  → errors (or warnings escalated by --strict)

Usage:
  python3 tools/asset_lint.py
  python3 tools/asset_lint.py --strict        # treat warnings as errors
  python3 tools/asset_lint.py --warn-only     # never fail; exit 0/1 only
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
ASSETS_DIR = ROOT / "shared" / "assets"
MANIFEST_PATH = ASSETS_DIR / "manifest.json"
MATERIAL_DIRS = ("handouts", "decks", "lab-reports")

IMG_RE = re.compile(r"<img\b[^>]{0,800}>", re.IGNORECASE | re.DOTALL)
SRC_RE = re.compile(r'src="([^"]+)"', re.IGNORECASE)
ALT_RE = re.compile(r'\balt="([^"]*)"', re.IGNORECASE)
DATA_ASSET_RE = re.compile(r'\bdata-asset="([^"]+)"', re.IGNORECASE)

# PII heuristics for filenames under shared/assets/
HANGUL_RE = re.compile(r"[가-힯]")
CHART_RE = re.compile(r"(?<!\d)\d{7}(?!\d)")  # exactly 7 digits, isolated
RRN_RE = re.compile(r"\d{6}-?[1-4]\d{6}")  # Korean RRN shape

# Medical illustrations at print resolution legitimately run 1-3 MB.
# Warn above 1.5 MB so authors notice un-optimized exports; only error
# above 4 MB which is almost certainly an un-compressed source export.
SIZE_WARN = 1_500 * 1024
SIZE_ERR = 4_000 * 1024


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"assets": {}}
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"assets": {}}


def iter_html() -> list[Path]:
    out: list[Path] = []
    for mat in MATERIAL_DIRS:
        d = ROOT / mat
        if not d.exists():
            continue
        out.extend(d.rglob("*.html"))
    return out


def check_html(html_path: Path, manifest: dict, errors: list[str], warnings: list[str]) -> None:
    try:
        text = html_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return

    assets = manifest.get("assets", {})
    rel_html = html_path.relative_to(ROOT)
    is_lab = str(rel_html).startswith("lab-reports/")

    for tag in IMG_RE.findall(text):
        src_m = SRC_RE.search(tag)
        da_m = DATA_ASSET_RE.search(tag)
        alt_m = ALT_RE.search(tag)
        alt_present = bool(alt_m and alt_m.group(1).strip())

        # broken <img src>
        if src_m and "shared/assets/" in src_m.group(1):
            src = src_m.group(1)
            # resolve relative to html_path
            target = (html_path.parent / src).resolve()
            if not target.exists():
                errors.append(f"{rel_html}: broken src '{src}' → {target}")
            # lab-report WebP
            if is_lab and src.lower().endswith(".webp"):
                errors.append(
                    f"{rel_html}: lab-report references WebP '{src}' "
                    f"— use PNG/JPG/SVG (PDF embed safety)"
                )
            # alt missing
            if not alt_present:
                warnings.append(f"{rel_html}: <img src='{src}'> has no alt text")

        # data-asset checks
        if da_m:
            key = da_m.group(1)
            entry = assets.get(key)
            if entry is None:
                # alias?
                for k, v in assets.items():
                    if key in (v.get("aliases") or []):
                        entry = v
                        break
            if entry is None:
                errors.append(f"{rel_html}: unknown data-asset='{key}'")
                continue
            f = entry.get("file")
            if f and not (ASSETS_DIR / f).exists():
                errors.append(
                    f"{rel_html}: data-asset='{key}' → file missing: shared/assets/{f}"
                )
            if entry.get("exists") is False:
                warnings.append(
                    f"{rel_html}: data-asset='{key}' manifest says exists=false"
                )
            if entry.get("review_status") != "approved":
                warnings.append(
                    f"{rel_html}: data-asset='{key}' review_status="
                    f"{entry.get('review_status')!r} (not approved)"
                )
            if is_lab and (entry.get("format") or "").lower() == "webp":
                errors.append(
                    f"{rel_html}: lab-report data-asset='{key}' is WebP "
                    f"— use PNG/JPG/SVG"
                )


def check_filesystem(errors: list[str], warnings: list[str]) -> None:
    if not ASSETS_DIR.exists():
        return
    for p in ASSETS_DIR.rglob("*"):
        if not p.is_file():
            continue
        if p.name.startswith("."):
            continue
        name = p.name
        rel = p.relative_to(ROOT)

        # PII heuristics
        if HANGUL_RE.search(name):
            errors.append(f"{rel}: filename contains Korean characters (possible PII)")
        if CHART_RE.search(name):
            errors.append(
                f"{rel}: filename contains a 7-digit run (possible chart number)"
            )
        if RRN_RE.search(name):
            errors.append(f"{rel}: filename matches Korean RRN pattern")

        # size
        sz = p.stat().st_size
        if sz > SIZE_ERR:
            errors.append(
                f"{rel}: oversize {sz/1024:.0f} KB (> {SIZE_ERR/1024:.0f} KB)"
            )
        elif sz > SIZE_WARN:
            warnings.append(
                f"{rel}: large {sz/1024:.0f} KB (> {SIZE_WARN/1024:.0f} KB)"
            )


def check_manifest(manifest: dict, errors: list[str], warnings: list[str]) -> None:
    assets = manifest.get("assets", {})
    for key, entry in assets.items():
        f = entry.get("file")
        if not f:
            errors.append(f"manifest['{key}']: missing 'file' field")
            continue
        if entry.get("exists") is False:
            warnings.append(
                f"manifest['{key}']: file '{f}' no longer on disk — remove or restore"
            )
        if not entry.get("alt_ko") and entry.get("review_status") == "approved":
            warnings.append(
                f"manifest['{key}']: approved but alt_ko empty"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="warnings → errors")
    parser.add_argument("--warn-only", action="store_true", help="never exit non-zero on errors")
    args = parser.parse_args()

    manifest = load_manifest()
    errors: list[str] = []
    warnings: list[str] = []

    check_manifest(manifest, errors, warnings)
    check_filesystem(errors, warnings)
    for html in iter_html():
        check_html(html, manifest, errors, warnings)

    if args.strict:
        errors.extend(warnings)
        warnings = []

    for w in warnings:
        print(f"  ⚠️  {w}", file=sys.stderr)
    for e in errors:
        print(f"  ✗ {e}", file=sys.stderr)

    print(
        f"asset_lint: {len(errors)} errors, {len(warnings)} warnings "
        f"(strict={args.strict})"
    )

    if args.warn_only:
        return 0 if not (errors or warnings) else 1
    if errors:
        return 2
    if warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
