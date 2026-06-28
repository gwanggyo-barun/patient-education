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
import re
import sys

# Windows consoles default to cp949/cp1252 and raise UnicodeEncodeError when
# printing ✓ ✗ ⚠️ status glyphs. Force UTF-8 so Mac and Windows runs print
# identically (SKILL.md rule #1: cross-machine consistency).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT / "shared"))
from _build_helpers import (  # noqa: E402
    make_qr_svg,
    inject_qr,
    inject_qr_url_text,
    qr_mini_url_text,
    short_qr_url_text,
    inject_noindex_meta,
    render,
    check_og_meta,
    strip_qr_mini_block,
    load_asset_manifest,
    resolve_data_asset,
    collect_data_asset_keys,
)
from _validate_layout import (  # noqa: E402
    HANDOUT_VALIDATOR_JS,
    DECK_VALIDATOR_JS,
    CONTRAST_ADVISORY_JS,
    GRANDFATHERED_INTERNAL_GAP,
)

NOTION_ENABLED = bool(os.environ.get("NOTION_TOKEN"))
if NOTION_ENABLED:
    from _notion_sync import upsert as notion_upsert  # noqa: E402
    from _notion_sync import content_last_modified_iso  # noqa: E402

OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
for sub in ("decks", "handouts", "lab-reports"):
    (OUT / sub).mkdir(exist_ok=True)

# Hosting base URL — change once here when GitHub Pages URL is finalized
BASE_URL = "https://gwanggyo-barun.github.io/patient-education"
from targets import TARGETS, ACTIVE_STATUS, ARCHIVED_STATUS  # noqa: E402  (data SoT)


# Each target dict carries everything needed to build + sync to Notion.
# Required: kind, slug, slug_path, html_path, qr_class, fmt
# Notion (optional but recommended): title, category, audience, disease, status


from _validators import (  # noqa: E402  (build-time validators, monolith split)
    _check_qr_populated,
    _decode_qr_matches,
    _validate_css_paths,
    _sync_asset_manifest,
    _validate_data_assets,
    _validate_lab_report_no_webp,
    _validate_targets_routing,
)
def main() -> int:
    # Pre-flight: sync asset manifest before any HTML inspection so newly
    # added image files are auto-registered.
    _sync_asset_manifest()

    # Pre-flight: validate kind routing — fail fast on misclassified TARGETS
    routing_issues = _validate_targets_routing()
    if routing_issues:
        print("=== TARGETS routing errors (fix before build) ===", file=sys.stderr)
        for issue in routing_issues:
            print(f"  ✗ {issue}", file=sys.stderr)
        return 2

    # Pre-flight: every data-asset="key" must resolve in manifest + on disk
    asset_issues = _validate_data_assets()
    if asset_issues:
        print("=== data-asset errors (fix before build) ===", file=sys.stderr)
        for issue in asset_issues:
            print(f"  ✗ {issue}", file=sys.stderr)
        return 2

    # Pre-flight: lab-reports must not use WebP (PDF embed safety)
    webp_issues = _validate_lab_report_no_webp()
    if webp_issues:
        print("=== lab-report WebP errors (fix before build) ===", file=sys.stderr)
        for issue in webp_issues:
            print(f"  ✗ {issue}", file=sys.stderr)
        return 2

    # Pre-flight: verify CSS/asset paths resolve (catches 4-level vs 3-level bugs)
    css_issues = _validate_css_paths()
    if css_issues:
        print("=== CSS/asset path errors (fix before build) ===", file=sys.stderr)
        for issue in css_issues:
            print(f"  ✗ {issue}", file=sys.stderr)
        return 2

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

            # Resolve data-asset="key" → src + alt (idempotent; preserves the
            # data-asset attribute as source-of-truth for future rebuilds).
            html, asset_errs, asset_warns = resolve_data_asset(
                html, html_path, strict_review=False
            )
            if asset_errs:
                failures.append(f"{kind}/{slug}: data-asset → " + "; ".join(asset_errs))
                continue
            for w in asset_warns:
                print(f"  ⚠️  {kind}/{slug}: {w}", file=sys.stderr)

            missing = check_og_meta(html, slug)
            if missing:
                failures.append(f"{kind}/{slug}: missing meta → {', '.join(missing)}")
                continue

            if kind == "lab-reports":
                # Privacy: lab-reports name patients; printed QR + public URL
                # would let anyone scan the page and view personal results.
                # Strip the footer QR block + add noindex meta. robots.txt
                # disallows /lab-reports/ on the GH Pages side.
                injected = strip_qr_mini_block(html)
                injected = inject_noindex_meta(injected)
                if 'class="qr-mini"' in injected:
                    failures.append(
                        f"{kind}/{slug}: qr-mini block survived strip — "
                        f"check footer markup matches strip_qr_mini_block regex"
                    )
                    continue
            else:
                qr_svg = make_qr_svg(target_url)
                injected = inject_qr(html, qr_svg, target_class=qr_class)

                # Handout footer mini-QR: also render the page's short URL as a
                # small typeable text line next to the QR, so a patient who
                # can't scan can still type the address. Same URL the QR encodes
                # (scheme stripped for display). Idempotent across re-builds.
                if qr_class == "qr-mini__code":
                    injected = inject_qr_url_text(injected, target_url)

                # ── Build-time QR/URL integrity check (fail loudly) ──────────
                # There is a historical bug where the live mini-QR rendered
                # empty (SKILL.md Gotcha 3: the raw index.html kept an empty
                # <div class="qr-block__code"></div>). Assert the QR div is now
                # actually populated AND, for handout footers, that the
                # typeable URL line is present and matches the QR target.
                qr_errs = _check_qr_populated(
                    injected,
                    qr_class=qr_class,
                    target_url=target_url,
                    want_url_text=(qr_class == "qr-mini__code"),
                )
                if qr_errs:
                    failures.append(f"{kind}/{slug}: " + "; ".join(qr_errs))
                    continue

            # Write back to raw index.html so the live GH Pages copy stays in
            # sync with what we render to PDF (QR for decks/handouts, no QR
            # for lab-reports).
            html_path.write_text(injected, encoding="utf-8")
            build_file = html_path  # PDF builder uses the same file

            try:
                viewport = (
                    {"width": 1320, "height": 800}
                    if fmt == "deck-16x9"
                    else {"width": 820, "height": 1160}
                )
                ctx = browser.new_context(viewport=viewport)
                # Fail-fast: never hang forever. networkidle can stall indefinitely
                # if a page keeps any network activity (kz-002: a deck hung the local
                # build ~11min at 0% CPU). 45s cap → TimeoutError caught below, that
                # deck is recorded as a failure and the build continues.
                ctx.set_default_timeout(45000)
                page = ctx.new_page()
                page.goto(f"file://{build_file}")
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(1200)  # ensure Pretendard web font applied
                # Layout validation BEFORE rendering — catch overflows/overlaps.
                # ⭐ deck PDF는 print 미디어로 렌더되므로 검증도 print 로 (screen
                # 에서만 보면 print 폰트 메트릭 차이로 생기는 카드 겹침을 놓침).
                if fmt == "deck-16x9":
                    page.emulate_media(media="print")
                    page.wait_for_timeout(300)
                validator_js = DECK_VALIDATOR_JS if fmt == "deck-16x9" else HANDOUT_VALIDATOR_JS
                issues = page.evaluate(validator_js)
                # large_internal_gap 래칫: 유예 등록된 기존 덱에서는 이 종류만
                # 비차단 경고로 강등(나머지 종류는 그대로 차단). 새/수정 덱은
                # 강등 없음 → 완전 차단. (정본 목록 = _validate_layout.GRANDFATHERED_INTERNAL_GAP)
                try:
                    src_rel = str(html_path.relative_to(ROOT)).replace("\\", "/")
                except ValueError:
                    src_rel = ""
                if issues and src_rel in GRANDFATHERED_INTERNAL_GAP:
                    gf = [it for it in issues if it.get("kind") == "large_internal_gap"]
                    issues = [it for it in issues if it.get("kind") != "large_internal_gap"]
                    if gf:
                        print(f"  ⚠️  {kind}/{slug}: {len(gf)} grandfathered large_internal_gap "
                              f"(non-blocking, pre-existing 부채): {gf}", file=sys.stderr)
                if issues:
                    failures.append(f"{kind}/{slug}: layout issues → {issues}")
                    ctx.close()
                    continue
                # WCAG contrast ADVISORY (non-blocking, design-untouched).
                # Flags only SMALL visible text below 4.5:1 — large/bold/accent
                # text is exempt. Prints warnings to the build log; never fails
                # the build, never changes any color.
                try:
                    low_contrast = page.evaluate(CONTRAST_ADVISORY_JS)
                except Exception as exc:  # advisory must never break the build
                    low_contrast = []
                    print(f"  ⚠️  {kind}/{slug}: contrast advisory skipped ({exc})",
                          file=sys.stderr)
                for w in low_contrast:
                    print(
                        f"  ⚠️  low-contrast: '{w.get('snippet','')}' "
                        f"{w.get('ratio','?')}:1 (<4.5) — {w.get('selector','')}",
                        file=sys.stderr,
                    )
                # OPTIONAL QR decode (only if OpenCV is present — no new deps).
                # Screenshots the rendered handout QR and decodes it; if decode
                # succeeds and the payload doesn't match the URL we encoded, fail
                # loudly (a real mis-injection). If decode fails (rasterisation /
                # library quirk), just warn — we already asserted the <svg> is
                # non-empty above, so this is belt-and-suspenders only.
                if kind != "lab-reports" and qr_class == "qr-mini__code":
                    dec_err = _decode_qr_matches(page, qr_class, target_url)
                    if dec_err is True:
                        pass  # decoded and matched
                    elif isinstance(dec_err, str):
                        failures.append(f"{kind}/{slug}: {dec_err}")
                        ctx.close()
                        continue
                    # dec_err is None → decode unavailable/inconclusive → skip
                render(
                    page,
                    f"file://{build_file}",
                    out_pdf=OUT / kind / f"{slug}.pdf",
                    out_preview=OUT / kind / f"{slug}-preview.png",
                    fmt=fmt,
                )
                ctx.close()
                if kind == "lab-reports":
                    print(f"  ✓ {kind}/{slug}  →  no QR (privacy), noindex")
                else:
                    print(f"  ✓ {kind}/{slug}  →  QR: {target_url}")
            except Exception as e:
                # Render error/timeout (incl. 45s networkidle stall): record which
                # deck and keep going instead of hanging/crashing the whole build.
                failures.append(
                    f"{kind}/{slug}: render error/timeout → {type(e).__name__}: {str(e)[:120]}"
                )
                try:
                    ctx.close()
                except Exception:
                    pass
                continue
            finally:
                pass  # raw index.html keeps QR svg — desired for live site

            # Notion sync (best effort — never fails the build)
            # Routes by `kind` to one of three DBs (see SKILL.md "Notion DB 라우팅"):
            # - decks/handouts use {title, category, audience, [disease]}
            # - lab-reports use {patient_name, chart_no, exam_date, doctor, [note]}
            #   OR legacy title "[1063] 김종혁 — 골 대사 검사" (auto-parsed in _notion_sync)
            notion_sync = t.get("notion_sync", True)
            sync_eligible = notion_sync and (
                (
                    kind == "lab-reports" and ("patient_name" in t or "title" in t)
                ) or (
                    kind in ("decks", "handouts") and "title" in t
                )
            )
            if NOTION_ENABLED and sync_eligible:
                pdf_url = f"{BASE_URL}/output/{kind}/{slug}.pdf"
                # 최종수정일 = date the material's *content* (visible text +
                # images) last changed in git — CSS/layout-only commits are
                # ignored. Not today, so a rebuild/restyle doesn't restamp rows.
                modified_iso = (
                    content_last_modified_iso(
                        str(t["html_path"].relative_to(ROOT)), today_iso
                    )
                    if kind in ("decks", "handouts")
                    else None
                )
                try:
                    action, page_id = notion_upsert(
                        kind=kind,
                        slug=slug,  # lab-reports: dedup by slug-in-URL
                        html_url=target_url,
                        pdf_url=pdf_url,
                        today_iso=today_iso,
                        modified_iso=modified_iso,
                        version=t.get("version", "v1.0"),
                        status=t.get("status", ACTIVE_STATUS),
                        # decks / handouts
                        title=t.get("title"),
                        category=t.get("category"),
                        audience=t.get("audience"),
                        disease=t.get("disease"),
                        note=t.get("note"),
                        # lab-reports (explicit fields override legacy title parse)
                        patient_name=t.get("patient_name"),
                        chart_no=t.get("chart_no"),
                        exam_date=t.get("exam_date"),
                        doctor=t.get("doctor"),
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
        print("=== Failures (deploy continues for successful items) ===", file=sys.stderr)
        for line in failures:
            print(f"  ✗ {line}", file=sys.stderr)
            print(f"::error::build failure: {line}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
