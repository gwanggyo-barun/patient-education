"""Shared build utilities for clinic-content-system.

Used by build.py for decks, handouts, and lab-reports — single source for:
  - QR SVG generation (Python qrcode, brand navy color, inline-safe)
  - QR injection into HTML (replace empty .qr-block__code or .qr-mini__code)
  - Playwright render helpers (preview PNG + PDF, multiple page formats)
  - OG meta block standardization
"""
from __future__ import annotations
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
