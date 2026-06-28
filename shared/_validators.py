"""Build-time validators — extracted from build.py 2026-06-28 (monolith split).

All gate the build using the TARGETS manifest; imported back into build.py's main().
Excluded from the published site via the deploy workflow's --exclude='*.py'.
"""
import re  # noqa: F401  (re.escape/finditer/search used below)
import sys  # used by _sync_asset_manifest / validators for status output
from targets import TARGETS, ACTIVE_STATUS, ARCHIVED_STATUS, ROOT
from _build_helpers import load_asset_manifest, collect_data_asset_keys

VALID_NOTION_STATUSES = {
    ACTIVE_STATUS,
    "🔄 수정중",
    "📝 초안",
    ARCHIVED_STATUS,
}


def _check_qr_populated(
    html: str,
    *,
    qr_class: str,
    target_url: str,
    want_url_text: bool,
) -> list[str]:
    """Assert the injected QR block is non-empty (and URL text present).

    Guards against the historical empty-QR bug (SKILL.md Gotcha 3) where the
    raw index.html shipped an empty ``<div class="qr-block__code"></div>`` to
    the live site. Returns a list of error strings (empty = OK) so the caller
    can fail the build loudly.

    Checks:
      1. The target QR div actually contains an ``<svg …>`` element.
      2. (handout footers only) the typeable ``.qr-mini__url`` line exists and
         its text matches the QR target (scheme stripped).
    """
    errs: list[str] = []

    # 1. QR div non-empty: find <div class="...qr_class...">…</div> and require
    #    an <svg inside. Use a non-greedy capture up to the matching depth-0
    #    close is overkill here — the QR div has no nested divs, so stop at the
    #    first </div>.
    cls = re.escape(qr_class)
    m = re.search(
        rf'<div\s+class="(?:[^"]*\s)?{cls}(?:\s[^"]*)?"\s*>(.*?)</div>',
        html,
        re.DOTALL,
    )
    if not m:
        errs.append(f"QR div .{qr_class} not found in HTML")
    elif "<svg" not in m.group(1).lower():
        errs.append(
            f"empty QR — .{qr_class} has no <svg> (historical empty-QR bug, "
            f"SKILL.md Gotcha 3)"
        )

    # 2. Handout footer typeable URL line.
    if want_url_text:
        url_text = qr_mini_url_text(html)
        if not url_text:
            errs.append("missing typeable URL line (.qr-mini__url) in footer")
        else:
            want = short_qr_url_text(target_url)
            if url_text != want:
                errs.append(
                    f"URL text mismatch — footer shows '{url_text}' but QR "
                    f"encodes '{want}'"
                )

    return errs


def _decode_qr_matches(page, qr_class: str, target_url: str):
    """Best-effort: decode the rendered footer QR and check it equals target_url.

    Returns:
      - True  → decoded successfully AND payload matches target_url
      - str   → decoded successfully but payload MISMATCHES (build should fail)
      - None  → decode unavailable/inconclusive (OpenCV missing, no QR element,
                screenshot/raster failed, or detector found nothing) → skip

    Uses OpenCV's built-in QRCodeDetector if importable. No new dependency is
    added (cv2 is optional); if it is absent we simply return None.
    """
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return None
    try:
        # Screenshot the inner <svg> (not the bordered/rounded .qr-mini__code
        # box) so the detector sees a clean QR with quiet zone.
        loc = page.locator(f".{qr_class} svg").first
        if loc.count() == 0:
            loc = page.locator(f".{qr_class}").first
        if loc.count() == 0:
            return None
        png = loc.screenshot()
        arr = np.frombuffer(png, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        # Upscale + add a white quiet-zone border to help the detector.
        h, w = img.shape[:2]
        if max(h, w) < 600:
            scale = 600 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)),
                             interpolation=cv2.INTER_NEAREST)
        img = cv2.copyMakeBorder(img, 40, 40, 40, 40,
                                 cv2.BORDER_CONSTANT, value=255)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        detector = cv2.QRCodeDetector()
        data, _pts, _ = detector.detectAndDecode(img)
        if not data:
            return None  # detector found nothing → inconclusive, skip
        if data.strip() != target_url.strip():
            return (f"QR decode MISMATCH — encodes '{data.strip()}' "
                    f"but should be '{target_url}'")
        return True
    except Exception:
        return None  # any failure here is non-fatal (advisory belt-and-suspenders)


def _validate_css_paths() -> list[str]:
    """Verify each material's CSS path actually resolves to a real file.

    Catches the 4-level vs 3-level deep slug mismatch:
    - decks/cardio/chest-pain/ (3-level) needs ../../../shared/
    - decks/cardio/htn/morning/ (4-level) needs ../../../../shared/
    """
    import re
    issues: list[str] = []
    for t in TARGETS:
        html_path = t.get("html_path")
        if not html_path or not html_path.exists():
            continue
        text = html_path.read_text(encoding="utf-8")
        for m in re.finditer(r'(?:href|src)="(\.\./[^"]*?(?:shared|assets)/[^"]*)"', text):
            rel = m.group(1)
            target = (html_path.parent / rel).resolve()
            if not target.exists():
                issues.append(
                    f"{t['kind']}/{t['slug']}: '{rel}' resolves to missing {target}"
                )
                break  # one per file is enough
    return issues


_HANGUL_RE = __import__("re").compile(r"[가-힯]")
_LAB_HASH_RE = __import__("re").compile(r"^[0-9a-f]{10}$")


def _sync_asset_manifest() -> None:
    """Run shared/assets/manifest.json sync at build start. Best-effort —
    a missing tools/sync_manifest.py shouldn't break the build."""
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import sync_manifest  # noqa: E402
        sync_manifest.sync(verbose=False)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  asset manifest sync skipped: {e}", file=sys.stderr)


def _validate_data_assets() -> list[str]:
    """Pre-flight: every data-asset="key" referenced in a TARGETS HTML
    must resolve to a manifest entry whose file exists on disk. Catches
    typos before Playwright renders a broken-image page."""
    manifest = load_asset_manifest()
    issues: list[str] = []
    for t in TARGETS:
        html_path = t.get("html_path")
        if not html_path or not html_path.exists():
            continue
        text = html_path.read_text(encoding="utf-8")
        keys = collect_data_asset_keys(text)
        if not keys:
            continue
        if not manifest:
            issues.append(
                f"{t['kind']}/{t['slug']}: HTML uses data-asset but manifest "
                f"is empty — run tools/sync_manifest.py"
            )
            continue
        for key in keys:
            entry = manifest.get(key)
            if entry is None:
                # check aliases
                aliased = any(
                    key in (v.get("aliases") or []) for v in manifest.values()
                )
                if not aliased:
                    issues.append(
                        f"{t['kind']}/{t['slug']}: unknown data-asset='{key}' "
                        f"(not in manifest, no alias match)"
                    )
                    continue
                entry = next(
                    v for v in manifest.values() if key in (v.get("aliases") or [])
                )
            f = entry.get("file")
            if f and not (ROOT / "shared" / "assets" / f).exists():
                issues.append(
                    f"{t['kind']}/{t['slug']}: data-asset='{key}' → file "
                    f"missing on disk: shared/assets/{f}"
                )
    return issues


def _validate_lab_report_no_webp() -> list[str]:
    """Pre-flight: lab-reports must not embed WebP images — some PDF
    renderers (esp. older Chromium / pdfkit fallbacks) drop them, leaving
    blank rectangles on the printed page.  Allowed formats: png, jpg, svg."""
    manifest = load_asset_manifest()
    issues: list[str] = []
    for t in TARGETS:
        if t.get("kind") != "lab-reports":
            continue
        html_path = t.get("html_path")
        if not html_path or not html_path.exists():
            continue
        text = html_path.read_text(encoding="utf-8")
        # Direct <img src="…webp">
        for m in __import__("re").finditer(r'<img[^>]*src="([^"]+\.webp)"', text, __import__("re").IGNORECASE):
            issues.append(
                f"{t['kind']}/{t['slug']}: lab-report references WebP src "
                f"'{m.group(1)}' — use PNG/JPG/SVG (PDF embed safety)"
            )
        # data-asset → manifest lookup
        for key in collect_data_asset_keys(text):
            entry = manifest.get(key) or next(
                (v for v in manifest.values() if key in (v.get("aliases") or [])),
                None,
            )
            if entry and (entry.get("format") or "").lower() == "webp":
                issues.append(
                    f"{t['kind']}/{t['slug']}: data-asset='{key}' is WebP "
                    f"— lab-reports must use PNG/JPG/SVG"
                )
    return issues


def _validate_targets_routing() -> list[str]:
    """Validate every TARGETS entry — kind must match the slug_path prefix.

    This catches mis-routing at build time so a deck never ends up syncing to
    the handouts DB, and a lab-report never lands in the decks DB.

    Rules:
    - slug_path must start with the kind directory ('decks/', 'handouts/',
      'lab-reports/').
    - html_path must be inside that directory.
    - kind must be one of: decks | handouts | lab-reports.
    - lab-reports must declare patient_name + chart_no (or legacy title with
      [차트번호] prefix that _notion_sync.py can parse).
    - lab-reports slug + slug_path must NOT contain Korean Hangul characters
      (privacy guardrail — see Gotcha 11). Use lab_hash_slug() instead.
    """
    issues: list[str] = []
    valid_kinds = {"decks", "handouts", "lab-reports"}
    for i, t in enumerate(TARGETS):
        kind = t.get("kind", "")
        slug = t.get("slug", "")
        slug_path = t.get("slug_path", "")
        html_path = t.get("html_path")
        prefix = f"TARGETS[{i}] {kind}/{slug}"

        if kind not in valid_kinds:
            issues.append(f"{prefix}: invalid kind '{kind}' (must be one of {valid_kinds})")
            continue

        notion_sync = t.get("notion_sync", True)
        if not isinstance(notion_sync, bool):
            issues.append(f"{prefix}: notion_sync must be a boolean when present")

        if kind == "lab-reports" and "status" in t:
            issues.append(
                f"{prefix}: lab-reports DB has no status field; use "
                "notion_sync=False or remove the row manually"
            )

        status = t.get("status", ACTIVE_STATUS)
        if kind != "lab-reports" and status not in VALID_NOTION_STATUSES:
            valid = ", ".join(sorted(VALID_NOTION_STATUSES))
            issues.append(f"{prefix}: invalid status '{status}' (must be one of: {valid})")

        if not slug_path.startswith(f"{kind}/"):
            issues.append(f"{prefix}: slug_path '{slug_path}' does not start with kind '{kind}/'")

        if html_path and f"/{kind}/" not in str(html_path).replace("\\", "/"):
            issues.append(f"{prefix}: html_path '{html_path}' is not inside /{kind}/")

        # Privacy guardrail: lab-reports must use a hash slug, never a patient
        # name. Korean Hangul in slug or slug_path almost certainly means a
        # patient name leaked in. Compute via lab_hash_slug() in _build_helpers.
        if kind == "lab-reports":
            if _HANGUL_RE.search(slug) or _HANGUL_RE.search(slug_path):
                issues.append(
                    f"{prefix}: lab-reports slug/slug_path contains Korean characters "
                    f"— use lab_hash_slug(chart_no, patient_name, topic) instead "
                    f"(slug='{slug}', slug_path='{slug_path}')"
                )
            if "/sample/" not in slug_path and not _LAB_HASH_RE.match(slug):
                issues.append(
                    f"{prefix}: lab-reports slug must be 10 lowercase hex chars "
                    f"(got '{slug}')"
                )
            if "/sample/" not in slug_path and html_path and html_path.exists():
                text = html_path.read_text(encoding="utf-8")
                if "__HASH__" in text or "◯◯◯" in text or "「환자명」" in text:
                    issues.append(
                        f"{prefix}: placeholder remains in registered lab-report HTML"
                    )

        # lab-reports SHOULD declare patient meta — warn, don't fail
        # (sample data like /lab-reports/lipid-panel/sample/ is exempt)
        if kind == "lab-reports" and "/sample/" not in slug_path:
            has_explicit = t.get("patient_name") and t.get("chart_no")
            has_legacy = (t.get("title") or "").startswith("[")
            if not (has_explicit or has_legacy):
                # Print warning but don't add to issues (build proceeds)
                import sys
                print(
                    f"⚠️  {prefix}: lab-reports recommended fields missing "
                    f"(patient_name+chart_no or legacy '[chart_no] patient — note')",
                    file=sys.stderr,
                )
    return issues


