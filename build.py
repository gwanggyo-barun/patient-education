"""Unified build script for clinic-content-system.

Builds three content types in a single run:
  - decks/        → 16:9 multi-slide patient education decks (1280x720 closing slide QR)
  - handouts/     → A4 portrait single-page clinic handouts (footer mini-QR)
  - lab-reports/  → A4 portrait single-page lab result infographics (footer mini-QR)

All targets share:
  - Common design tokens (shared/design-tokens.css)
  - Brand QR generation (Python qrcode SVG, navy #003366, inline-injected)
  - OG meta head registration (validated during build)
  - Notion DB sync (when NOTION_TOKEN env is set)

Output goes to output/{type}/{slug}.{pdf,png}
"""
from datetime import date
from pathlib import Path
import os
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

NOTION_ENABLED = bool(os.environ.get("NOTION_TOKEN"))
if NOTION_ENABLED:
    from _notion_sync import upsert as notion_upsert  # noqa: E402

OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
for sub in ("decks", "handouts", "lab-reports"):
    (OUT / sub).mkdir(exist_ok=True)

# Hosting base URL — change once here when GitHub Pages URL is finalized
BASE_URL = "https://gwanggyo-barun.github.io/patient-education"


# Each target dict carries everything needed to build + sync to Notion.
# Required: kind, slug, slug_path, html_path, qr_class, fmt
# Notion (optional but recommended): title, category, audience, disease
TARGETS = [
    # === 16:9 multi-slide decks ===
    {
        "kind": "decks", "slug": "gerd",
        "slug_path": "decks/gi/gerd/lifestyle/",
        "html_path": ROOT / "decks/gi/gerd/lifestyle/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "역류성 식도염 생활관리",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "GERD (역류성 식도염)",
    },
    {
        "kind": "decks", "slug": "hpylori",
        "slug_path": "decks/gi/h-pylori/eradication/",
        "html_path": ROOT / "decks/gi/h-pylori/eradication/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "헬리코박터 제균 치료 안내",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "H. pylori",
    },
    {
        "kind": "decks", "slug": "morning-htn",
        "slug_path": "decks/cardio/htn/morning/",
        "html_path": ROOT / "decks/cardio/htn/morning/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "아침 고혈압 환자 교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "고혈압 (HTN)",
    },
    {
        "kind": "decks", "slug": "oh-management-2026",
        "slug_path": "decks/cardio/orthostatic-hypotension/management-2026/",
        "html_path": ROOT / "decks/cardio/orthostatic-hypotension/management-2026/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "기립성 저혈압 관리 — JAMA 2026 리뷰",
        "category": "🩺 일반내과", "audience": "의료진", "disease": "기립성 저혈압",
    },
    {
        "kind": "decks", "slug": "endoscopy-cpr-training",
        "slug_path": "decks/emergency/endoscopy/cpr-training/",
        "html_path": ROOT / "decks/emergency/endoscopy/cpr-training/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "내시경실 심정지 응급 대응 직원 교육",
        "category": "🩺 일반내과", "audience": "의료진", "disease": "응급처치 (CPR)",
    },

    # === A4 portrait single-page handouts ===
    {
        "kind": "handouts", "slug": "colonoscopy",
        "slug_path": "handouts/gi/colonoscopy/",
        "html_path": ROOT / "handouts/gi/colonoscopy/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "대장내시경 전 준비 안내",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "대장내시경",
    },
    {
        "kind": "handouts", "slug": "cpr-flowchart",
        "slug_path": "handouts/emergency/cpr-flowchart/",
        "html_path": ROOT / "handouts/emergency/cpr-flowchart/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "내시경실 Code Blue 플로우차트",
        "category": "🩺 일반내과", "audience": "의료진", "disease": "응급처치 (CPR)",
    },
    {
        "kind": "handouts", "slug": "crash-cart-checklist",
        "slug_path": "handouts/emergency/crash-cart-checklist/",
        "html_path": ROOT / "handouts/emergency/crash-cart-checklist/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "응급카트 점검 체크리스트",
        "category": "🩺 일반내과", "audience": "의료진", "disease": "응급처치",
    },
    {
        "kind": "handouts", "slug": "crash-cart-map",
        "slug_path": "handouts/emergency/crash-cart-map/",
        "html_path": ROOT / "handouts/emergency/crash-cart-map/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "응급카트 약품·장비 위치 맵",
        "category": "🩺 일반내과", "audience": "의료진", "disease": "응급처치",
    },

    # === A4 portrait single-page lab reports ===
    {
        "kind": "lab-reports", "slug": "lipid-panel",
        "slug_path": "lab-reports/lipid-panel/sample/",
        "html_path": ROOT / "lab-reports/lipid-panel/sample/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "지질 패널 결과 안내",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "지질패널",
    },
]


def main() -> int:
    failures: list[str] = []
    notion_failures: list[str] = []
    today_iso = date.today().isoformat()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for t in TARGETS:
            kind, slug = t["kind"], t["slug"]
            slug_path, html_path = t["slug_path"], t["html_path"]
            qr_class, fmt = t["qr_class"], t["fmt"]

            if not html_path.exists():
                failures.append(f"{kind}/{slug}: source missing → {html_path}")
                continue

            target_url = f"{BASE_URL}/{slug_path}"
            html = html_path.read_text(encoding="utf-8")

            missing = check_og_meta(html, slug)
            if missing:
                failures.append(f"{kind}/{slug}: missing meta → {', '.join(missing)}")
                continue

            qr_svg = make_qr_svg(target_url)
            injected = inject_qr(html, qr_svg, target_class=qr_class)

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

            # Notion sync (best effort — never fails the build)
            if NOTION_ENABLED and "title" in t:
                pdf_url = f"{BASE_URL}/output/{kind}/{slug}.pdf"
                try:
                    action, page_id = notion_upsert(
                        title=t["title"],
                        category=t["category"],
                        audience=t["audience"],
                        disease=t["disease"],
                        html_url=target_url,
                        pdf_url=pdf_url,
                        today_iso=today_iso,
                    )
                    print(f"      Notion {action}: {page_id}")
                except Exception as e:  # noqa: BLE001
                    notion_failures.append(f"{kind}/{slug}: {e}")

        browser.close()

    print()
    print("=== Build artifacts ===")
    for f in sorted(OUT.rglob("*")):
        if f.is_file():
            rel = f.relative_to(OUT)
            print(f"  {rel}: {f.stat().st_size / 1024:.1f} KB")

    if NOTION_ENABLED:
        ok = len(TARGETS) - len(notion_failures)
        print()
        print(f"=== Notion sync: {ok}/{len(TARGETS)} ok ===")
        for line in notion_failures:
            print(f"  ⚠️  {line}", file=sys.stderr)
    else:
        print()
        print("=== Notion sync: SKIPPED (NOTION_TOKEN not set) ===")

    if failures:
        print()
        print("=== Failures ===", file=sys.stderr)
        for line in failures:
            print(f"  ✗ {line}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
