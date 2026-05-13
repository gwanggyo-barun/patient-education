"""Shared build utilities for clinic-content-system.

Used by build.py for decks, handouts, and lab-reports — single source for:
  - QR SVG generation (Python qrcode, brand navy color, inline-safe)
  - QR injection into HTML (replace empty .qr-block__code or .qr-mini__code)
  - Playwright render helpers (preview PNG + PDF, multiple page formats)
  - OG meta block standardization
  - lab-reports privacy: hash slugs + QR strip + noindex meta
"""
from __future__ import annotations
import hashlib
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Literal

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
