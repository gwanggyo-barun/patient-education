"""Shared build utilities for clinic-content-system.

Used by build.py for decks, handouts, and lab-reports — single source for:
  - QR SVG generation (Python qrcode, brand navy color, inline-safe)
  - QR injection into HTML (replace empty .qr-block__code or .qr-mini__code)
  - Playwright render helpers (preview PNG + PDF, multiple page formats)
  - OG meta block standardization
  - lab-reports privacy: hash slugs + QR strip + noindex meta
  - Asset manifest + data-asset="key" → src/alt resolution
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

import qrcode
import qrcode.image.svg


BRAND_NAVY = "#003366"


# --------------------------------------------------------------------------- #
# QR
# --------------------------------------------------------------------------- #

def make_qr_svg(url: str, dark_color: str = BRAND_NAVY) -> str:
    """Generate inline SVG QR code for the given URL.

    Returns SVG string with XML declaration stripped (safe to inline in HTML).
    """
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(image_factory=factory)
    buf = BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode("utf-8")
    svg = svg.replace('fill="#000000"', f'fill="{dark_color}"')
    svg = svg.replace('stroke="#000000"', f'stroke="{dark_color}"')
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    return svg


def inject_qr(html: str, qr_svg: str, *, target_class: str = "qr-block__code") -> str:
    """Replace the first empty <div> whose class list contains target_class.

    Multi-class divs (e.g. ``<div class="qr-block__code takehome-side__qr">``)
    are matched too — the original class list is preserved, only the SVG is
    inserted inside.

    Supports two target classes:
      - "qr-block__code"  → 16:9 deck closing slide
      - "qr-mini__code"   → A4 handout / lab-report footer mini-QR
    """
    # Match <div class="...{target_class}..."></div> regardless of other classes
    # Group 1 captures the full opening tag so we can reuse it verbatim.
    cls_pattern = rf'(?:[^"\s]+\s+)*{re.escape(target_class)}(?:\s+[^"]+)*'
    pattern = rf'(<div class="{cls_pattern}">)\s*</div>'
    return re.sub(pattern, rf'\1{qr_svg}</div>', html, count=1)


# Matches the URL text line inside the footer mini-QR block (handouts).
# Used to detect an existing line (idempotent re-build) and to validate
# presence. Captures the inner text so we can compare against the live URL.
_QR_MINI_URL_RE = re.compile(
    r'<div\s+class="qr-mini__url"[^>]*>(.*?)</div>',
    re.DOTALL,
)


def short_qr_url_text(url: str) -> str:
    """Display form of a QR URL for the typeable text line under the mini-QR.

    Strips the ``https://`` / ``http://`` scheme (browsers re-add it) so the
    line stays short and unobtrusive, while still being something a patient who
    cannot scan can type verbatim. Trailing slash is kept — it mirrors the QR
    target exactly so both routes land on the same GitHub Pages directory.
    """
    return re.sub(r'^https?://', '', url.strip())


def inject_qr_url_text(html: str, url: str) -> str:
    """Inject (or refresh) the typeable short-URL line inside the footer.

    For handouts only. Renders a small ``<div class="qr-mini__url">…</div>``
    inside the ``.qr-mini`` block so a patient who can't scan the QR can read
    and type the address. The accompanying CSS positions it unobtrusively at
    the bottom of the footer, next to the QR, WITHOUT changing the footer's
    flow height (it is absolutely positioned) — this keeps all existing dense
    handouts from overflowing their single A4 page.

    Idempotent: an existing ``qr-mini__url`` line is replaced with the current
    URL (so URL drift across re-builds self-corrects). If the handout has no
    ``.qr-mini`` block the HTML is returned unchanged.

    The encoded text is the same URL the QR encodes (scheme stripped for the
    visible line) — see ``short_qr_url_text``.
    """
    display = short_qr_url_text(url)
    line = f'<div class="qr-mini__url">{display}</div>'

    # Already has a url line → replace its contents in place (idempotent).
    if _QR_MINI_URL_RE.search(html):
        return _QR_MINI_URL_RE.sub(line, html, count=1)

    # Preferred: insert right after the qr-mini__label line (preserve indent).
    label_re = re.compile(
        r'(^[ \t]*)(<div\s+class="qr-mini__label"[^>]*>.*?</div>)',
        re.MULTILINE | re.DOTALL,
    )
    m = label_re.search(html)
    if m:
        indent = m.group(1)
        return html[: m.end()] + f'\n{indent}{line}' + html[m.end():]

    # No label but a qr-mini block exists (class may carry extra attrs like
    # aria-label) → append just before the block's closing </div>. Find the
    # opening tag, then the matching close before </footer>.
    open_re = re.compile(r'<div\s+class="(?:[^"]*\s)?qr-mini(?:\s[^"]*)?"[^>]*>')
    om = open_re.search(html)
    if om:
        close_re = re.compile(r'</div>\s*</footer>')
        cm = close_re.search(html, om.end())
        if cm:
            return html[: cm.start()] + f'\n      {line}\n    ' + html[cm.start():]

    # No mini-QR block at all (e.g. lab-report already stripped) → no-op.
    return html


def qr_mini_url_text(html: str) -> str | None:
    """Return the text inside ``.qr-mini__url`` if present, else None."""
    m = _QR_MINI_URL_RE.search(html)
    return m.group(1).strip() if m else None


# --------------------------------------------------------------------------- #
# Playwright render
# --------------------------------------------------------------------------- #

PageFormat = Literal["deck-16x9", "a4-portrait"]


def render(
    page,
    url: str,
    out_pdf: Path,
    out_preview: Path,
    fmt: PageFormat,
    wait_ms: int = 1500,
) -> None:
    """Render an HTML URL to PDF + preview PNG, sized per format."""
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(wait_ms)

    # Preview PNG (full page screenshot)
    page.screenshot(path=str(out_preview), full_page=True)

    # PDF — page size depends on format
    page.emulate_media(media="print")
    if fmt == "deck-16x9":
        page.pdf(
            path=str(out_pdf),
            width="1280px",
            height="720px",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
    elif fmt == "a4-portrait":
        page.pdf(
            path=str(out_pdf),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
    else:
        raise ValueError(f"Unknown format: {fmt}")


# --------------------------------------------------------------------------- #
# OG meta validation (sanity check during build)
# --------------------------------------------------------------------------- #

OG_REQUIRED = (
    "og:type", "og:url", "og:title", "og:description",
    "og:image", "og:site_name",
)
THEME_COLOR_REQUIRED = "theme-color"


def check_og_meta(html: str, slug: str) -> list[str]:
    """Return list of missing required meta tags (empty list = all present)."""
    missing: list[str] = []
    for prop in OG_REQUIRED:
        if not re.search(rf'<meta\s+property="{re.escape(prop)}"', html):
            missing.append(prop)
    if not re.search(rf'<meta\s+name="{re.escape(THEME_COLOR_REQUIRED)}"', html):
        missing.append(THEME_COLOR_REQUIRED)
    return missing


# --------------------------------------------------------------------------- #
# lab-reports privacy: hash slugs + QR strip + noindex
# --------------------------------------------------------------------------- #

def lab_hash_slug(chart_no: str, patient_name: str, topic: str) -> str:
    """Deterministic 10-char hex slug for a lab-report URL.

    Same (chart_no, patient_name, topic) always yields the same slug, so
    re-builds and Notion upserts stay stable. Topic is the second segment of
    slug_path (e.g. "diabetes-screening"), which keeps URLs grouped without
    leaking identity.

    Set ``LAB_SLUG_SALT`` env var to inject a server-side secret salt.
    Without the salt, the inputs (chart_no range, name, 8-topic enum) are
    brute-forceable in under an hour on commodity GPU. Migrating existing
    slugs requires re-running build.py + updating Notion 파일링크 URLs.
    """
    if not chart_no or not patient_name:
        raise ValueError("lab_hash_slug requires non-empty chart_no and patient_name")
    salt = os.environ.get("LAB_SLUG_SALT", "")
    seed_parts = [chart_no.strip(), patient_name.strip(), topic]
    if salt:
        seed_parts.insert(0, salt)
    seed = ":".join(seed_parts)
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:10]


_QR_MINI_BLOCK_RE = re.compile(
    r'\s*<div\s+class="qr-mini">.*?</div>\s*</div>',
    re.DOTALL,
)


def strip_qr_mini_block(html: str) -> str:
    """Remove the entire footer mini-QR aside (`<div class="qr-mini">…</div>`).

    Used for lab-reports where rendering a QR pointing to a public URL would
    expose patient-specific content via the printed PDF. Idempotent — already
    stripped HTML is returned unchanged.
    """
    return _QR_MINI_BLOCK_RE.sub("", html, count=1)


_NOINDEX_META = '<meta name="robots" content="noindex,nofollow,noarchive">'


def inject_noindex_meta(html: str) -> str:
    """Insert `<meta name="robots" content="noindex,nofollow,noarchive">`.

    Combined with /robots.txt this hides lab-report URLs from search engines.
    The noarchive directive also blocks Google's cached-copy view.

    Behaviour:
      - no existing robots meta → insert canonical after <head>
      - existing weak meta (missing noarchive) → replace with canonical
      - existing canonical (already has noarchive) → no-op
    """
    existing = re.search(r'<meta\s+name="robots"[^>]*>', html, re.IGNORECASE)
    if existing:
        if "noarchive" in existing.group(0).lower():
            return html
        return html.replace(existing.group(0), _NOINDEX_META, 1)
    return re.sub(
        r'(<head[^>]*>)',
        rf'\1\n  {_NOINDEX_META}',
        html,
        count=1,
    )


# --------------------------------------------------------------------------- #
# Asset manifest + data-asset resolution
# --------------------------------------------------------------------------- #

# Root of the repo, computed once. _build_helpers.py lives in shared/ so the
# parent is the repo root.
_HELPERS_ROOT = Path(__file__).parent.parent.resolve()
_MANIFEST_PATH = _HELPERS_ROOT / "shared" / "assets" / "manifest.json"
_HEALTHICONS_MANIFEST_PATH = _HELPERS_ROOT / "shared" / "assets" / "healthicons.manifest.json"
_ASSETS_DIR = _HELPERS_ROOT / "shared" / "assets"

# Cache loaded once per process — manifest doesn't change during a build.
_MANIFEST_CACHE: dict[str, Any] | None = None


def _load_manifest_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data.get("assets", {}) or {}


def load_asset_manifest(*, refresh: bool = False) -> dict[str, Any]:
    """Return the merged asset manifest as a dict {key: entry}. Cached per
    process.

    Merges two sources:
      - shared/assets/healthicons.manifest.json — vendored icon library
        (auto-generated by tools/sync_healthicons.py; lower precedence).
      - shared/assets/manifest.json — curated, hand-edited assets
        (higher precedence; wins on key collision so authors can override
        a vendored icon's metadata if needed).

    Returns an empty dict if both files are missing — callers should treat
    that as "no asset registry yet" (data-asset references will fail
    pre-flight in that case, which is the intended behaviour).
    """
    global _MANIFEST_CACHE
    if _MANIFEST_CACHE is not None and not refresh:
        return _MANIFEST_CACHE
    merged: dict[str, Any] = {}
    merged.update(_load_manifest_file(_HEALTHICONS_MANIFEST_PATH))
    merged.update(_load_manifest_file(_MANIFEST_PATH))
    _MANIFEST_CACHE = merged
    return _MANIFEST_CACHE


# Matches a full <img …> tag that carries data-asset="…".
# Captures: (full_tag, key)
_DATA_ASSET_IMG_RE = re.compile(
    r'<img\b([^>]*?)\bdata-asset="([^"]+)"([^>]*?)/?>',
    re.IGNORECASE | re.DOTALL,
)


def _replace_or_append_attr(attrs: str, name: str, value: str) -> str:
    """Set attribute `name="value"` on an attribute string. Replaces if
    present, appends with a leading space otherwise. Returns the new string."""
    pat = re.compile(rf'\b{re.escape(name)}="[^"]*"', re.IGNORECASE)
    new = f'{name}="{value}"'
    if pat.search(attrs):
        return pat.sub(new, attrs, count=1)
    sep = "" if attrs.endswith(" ") or attrs == "" else " "
    return attrs + sep + new


def resolve_data_asset(
    html: str,
    html_path: Path,
    *,
    strict_review: bool = False,
) -> tuple[str, list[str], list[str]]:
    """Rewrite `<img data-asset="key">` tags to embed the resolved src + alt.

    The data-asset attribute is preserved as the source of truth — src/alt
    act as a build-cached resolution layer. A subsequent rebuild re-derives
    src/alt from the manifest, so renames/alt-text edits propagate cleanly.

    For each match:
      - look up `key` in the manifest
      - compute correct `../../…/shared/assets/…` path from `html_path.parent`
      - inject/refresh `src="…"`
      - inject/refresh `alt="…"` only if the tag doesn't already have a
        non-empty alt (authors can override per-instance)

    Returns (new_html, errors, warnings):
      - errors: hard failures — unknown key, missing file → build should fail
      - warnings: review_status != "approved", file marked exists=false,
        manifest empty → build proceeds, logs warning. `strict_review=True`
        upgrades pending review_status to a hard error (use in CI prod jobs).
    """
    manifest = load_asset_manifest()
    errors: list[str] = []
    warnings: list[str] = []

    def replace(m: re.Match[str]) -> str:
        attrs_before = m.group(1) or ""
        key = m.group(2)
        attrs_after = m.group(3) or ""
        attrs = (attrs_before + attrs_after).strip()

        entry = manifest.get(key)
        # Also try resolving via aliases (manifest entry can declare
        # `"aliases": ["old-name"]` so renames don't break authored HTML).
        if entry is None:
            for k, v in manifest.items():
                if key in (v.get("aliases") or []):
                    entry = v
                    key = k  # normalize to canonical key for logging
                    break

        if entry is None:
            errors.append(f"{html_path.name}: data-asset='{key}' not in manifest")
            return m.group(0)

        file_rel = entry.get("file")
        if not file_rel:
            errors.append(f"{html_path.name}: data-asset='{key}' has no 'file' field")
            return m.group(0)

        asset_abs = _ASSETS_DIR / file_rel
        if not asset_abs.exists():
            errors.append(
                f"{html_path.name}: data-asset='{key}' → file missing on disk: {file_rel}"
            )
            return m.group(0)

        if entry.get("exists") is False:
            warnings.append(
                f"{html_path.name}: data-asset='{key}' marked exists=false in manifest"
            )

        review = entry.get("review_status", "pending")
        if review != "approved":
            msg = f"{html_path.name}: data-asset='{key}' review_status={review!r}"
            if strict_review:
                errors.append(msg + " (strict mode: refusing to ship)")
                return m.group(0)
            warnings.append(msg)

        rel_src = os.path.relpath(asset_abs, html_path.parent).replace(os.sep, "/")

        # Canonical attribute order for stable, idempotent rewrites:
        # data-asset → src → alt → (everything else preserved as-is).
        # Strip data-asset from `attrs` (already captured) before we re-prefix.
        attrs = re.sub(r'\s*\bdata-asset="[^"]*"', "", attrs).strip()
        new_attrs = _replace_or_append_attr("", "data-asset", key)
        new_attrs = _replace_or_append_attr(new_attrs, "src", rel_src)
        if attrs:
            # Drop any old src= from preserved attrs (we just wrote the new one)
            attrs = re.sub(r'\s*\bsrc="[^"]*"', "", attrs).strip()
            if attrs:
                new_attrs = new_attrs + " " + attrs

        # alt: only fill if missing or empty. Authors can override per-instance.
        alt_match = re.search(r'\balt="([^"]*)"', new_attrs, re.IGNORECASE)
        existing_alt = (alt_match.group(1).strip() if alt_match else "")
        if not existing_alt:
            alt_ko = (entry.get("alt_ko") or "").strip()
            if alt_ko:
                new_attrs = _replace_or_append_attr(new_attrs, "alt", alt_ko)
            else:
                warnings.append(
                    f"{html_path.name}: data-asset='{key}' has no alt_ko in manifest"
                )

        # Keep data-asset attribute as SoT for the next build/edit cycle.
        # _replace_or_append_attr already preserved it (since it was in `attrs`).
        # Reassemble. Use self-closing because original tag style varies.
        # We normalize to <img attrs/> to keep output deterministic.
        new_attrs = re.sub(r"\s+", " ", new_attrs).strip()
        return f"<img {new_attrs}>"

    new_html = _DATA_ASSET_IMG_RE.sub(replace, html)
    return new_html, errors, warnings


def collect_data_asset_keys(html: str) -> list[str]:
    """Return all data-asset keys referenced in the given HTML. Used by
    pre-flight validators and lint."""
    return [m.group(2) for m in _DATA_ASSET_IMG_RE.finditer(html)]
