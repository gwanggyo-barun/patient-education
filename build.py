"""Unified build script for clinic-content-system.

Builds three content types in a single run:
  - decks/        → 16:9 multi-slide patient education decks (1280x720 closing slide QR)
  - handouts/     → A4 portrait single-page clinic handouts (footer mini-QR)
  - lab-reports/  → A4 portrait single-page lab result infographics (footer mini-QR)

All targets share:
  - Common design tokens (shared/design-tokens.css)
  - Brand QR generation (Python qrcode SVG, navy #003366, inline-injected)
  - OG meta head registration (validated during build)

Output goes to output/{type}/{slug}.{pdf,png}
"""
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT / "shared"))
from _build_helpers import (  # noqa: E402
    make_qr_svg,
    inject_qr,
    render,
    check_og_meta,
)

OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
for sub in ("decks", "handouts", "lab-reports"):
    (OUT / sub).mkdir(exist_ok=True)

# Hosting base URL — change once here when GitHub Pages URL is finalized
BASE_URL = "https://gwanggyo-barun.github.io/patient-education"


# Format: (kind, slug, slug_path, html_path, qr_target_class, render_format)
TARGETS = [
    # === 16:9 multi-slide decks ===
    ("decks", "gerd",    "decks/gi/gerd/lifestyle/",
     ROOT / "decks/gi/gerd/lifestyle/index.html",
     "qr-block__code", "deck-16x9"),

    ("decks", "hpylori", "decks/gi/h-pylori/eradication/",
     ROOT / "decks/gi/h-pylori/eradication/index.html",
     "qr-block__code", "deck-16x9"),

    ("decks", "morning-htn", "decks/cardio/htn/morning/",
     ROOT / "decks/cardio/htn/morning/index.html",
     "qr-block__code", "deck-16x9"),

    ("decks", "oh-management-2026", "decks/cardio/orthostatic-hypotension/management-2026/",
     ROOT / "decks/cardio/orthostatic-hypotension/management-2026/index.html",
     "qr-block__code", "deck-16x9"),

    ("decks", "endoscopy-cpr-training", "decks/emergency/endoscopy/cpr-training/",
     ROOT / "decks/emergency/endoscopy/cpr-training/index.html",
     "qr-block__code", "deck-16x9"),

    # === A4 portrait single-page handouts ===
    ("handouts", "colonoscopy", "handouts/gi/colonoscopy/",
     ROOT / "handouts/gi/colonoscopy/index.html",
     "qr-mini__code", "a4-portrait"),

    ("handouts", "cpr-flowchart", "handouts/emergency/cpr-flowchart/",
     ROOT / "handouts/emergency/cpr-flowchart/index.html",
     "qr-mini__code", "a4-portrait"),

    ("handouts", "crash-cart-checklist", "handouts/emergency/crash-cart-checklist/",
     ROOT / "handouts/emergency/crash-cart-checklist/index.html",
     "qr-mini__code", "a4-portrait"),

    ("handouts", "crash-cart-map", "handouts/emergency/crash-cart-map/",
     ROOT / "handouts/emergency/crash-cart-map/index.html",
     "qr-mini__code", "a4-portrait"),

    # === A4 portrait single-page lab reports ===
    ("lab-reports", "lipid-panel", "lab-reports/lipid-panel/sample/",
     ROOT / "lab-reports/lipid-panel/sample/index.html",
     "qr-mini__code", "a4-portrait"),
]


def main() -> int:
    failures: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for kind, slug, slug_path, html_path, qr_class, fmt in TARGETS:
            if not html_path.exists():
                failures.append(f"{kind}/{slug}: source missing → {html_path}")
                continue

            target_url = f"{BASE_URL}/{slug_path}"
            html = html_path.read_text(encoding="utf-8")

            # Sanity check: OG meta in head
            missing = check_og_meta(html, slug)
            if missing:
                failures.append(f"{kind}/{slug}: missing meta → {', '.join(missing)}")
                continue

            # 1. Generate QR SVG and inject
            qr_svg = make_qr_svg(target_url)
            injected = inject_qr(html, qr_svg, target_class=qr_class)

            # 2. Write build HTML next to source so relative paths still resolve
            build_file = html_path.parent / "_build.html"
            build_file.write_text(injected, encoding="utf-8")

            try:
                viewport = (
                    {"width": 1320, "height": 800}
                    if fmt == "deck-16x9"
                    else {"width": 820, "height": 1160}
                )
                ctx = browser.new_context(viewport=viewport)
                page = ctx.new_page()
                render(
                    page,
                    f"file://{build_file}",
                    out_pdf=OUT / kind / f"{slug}.pdf",
                    out_preview=OUT / kind / f"{slug}-preview.png",
                    fmt=fmt,
                )
                ctx.close()
                print(f"  ✓ {kind}/{slug}  →  QR: {target_url}")
            finally:
                build_file.unlink(missing_ok=True)

        browser.close()

    print()
    print("=== Build artifacts ===")
    for f in sorted(OUT.rglob("*")):
        if f.is_file():
            rel = f.relative_to(OUT)
            print(f"  {rel}: {f.stat().st_size / 1024:.1f} KB")

    if failures:
        print()
        print("=== Failures ===", file=sys.stderr)
        for line in failures:
            print(f"  ✗ {line}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
