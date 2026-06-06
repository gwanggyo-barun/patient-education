"""Layout validator for handouts / lab-reports / decks.

Run AFTER writing HTML, BEFORE building/committing.
Detects overflow, footer overlap, content escaping the page bounding box.

Usage:
    python -m shared._validate_layout <html_path>      # validates a single file
    python -m shared._validate_layout                  # validates all TARGETS in build.py

Returns exit code 0 if clean, 1 if issues found (suitable for CI gate).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent

# A4 portrait at 96dpi: 210mm × 297mm = 794 × 1123 px
A4_VIEWPORT = {"width": 794, "height": 1123}
# 16:9 deck: 1280 × 720
DECK_VIEWPORT = {"width": 1280, "height": 720}

# JS that walks the DOM and returns layout issues. Same shape for both kinds.
HANDOUT_VALIDATOR_JS = r"""
(() => {
  const issues = [];
  const pages = [...document.querySelectorAll('.page')];
  if (pages.length === 0) {
    issues.push({kind: 'no_page_div', detail: 'document has no .page element'});
    return issues;
  }
  pages.forEach((p, idx) => {
    const pn = idx + 1;
    const pr = p.getBoundingClientRect();
    if (p.scrollHeight > p.clientHeight + 1) {
      issues.push({page: pn, kind: 'page_overflow', detail: `${p.scrollHeight - p.clientHeight}px`});
    }
    const footer = p.querySelector('.page__footer');
    const body = p.querySelector('.page__body');
    if (!footer || !body) {
      issues.push({page: pn, kind: 'missing_region', detail: !footer ? 'no .page__footer' : 'no .page__body'});
      return;
    }
    const fr = footer.getBoundingClientRect();
    const sections = [...body.querySelectorAll(':scope > section')];
    sections.forEach((s, sIdx) => {
      const sr = s.getBoundingClientRect();
      if (sr.bottom > fr.top + 1) {
        issues.push({
          page: pn, kind: 'section_overlaps_footer',
          section: sIdx + 1,
          overlap_px: Math.round(sr.bottom - fr.top),
        });
      }
    });
    const cards = [...p.querySelectorAll('.card, .tile, .lab-row, .stat-cell, .checklist__item')];
    cards.forEach((c) => {
      const cr = c.getBoundingClientRect();
      if (cr.bottom > pr.bottom + 1) {
        issues.push({page: pn, kind: 'element_below_page', detail: `${Math.round(cr.bottom - pr.bottom)}px`, sample: c.className});
      }
      if (cr.right > pr.right + 1) {
        issues.push({page: pn, kind: 'element_right_of_page', detail: `${Math.round(cr.right - pr.right)}px`, sample: c.className});
      }
    });
  });
  return issues;
})()
"""

DECK_VALIDATOR_JS = r"""
(() => {
  const issues = [];
  const slides = [...document.querySelectorAll('.slide')];
  if (slides.length === 0) {
    issues.push({kind: 'no_slide_div', detail: 'document has no .slide element'});
    return issues;
  }
  // Note: .slide has overflow:hidden by design (1280×720 fixed frame), so
  // scrollHeight check would false-positive on decorative absolute-positioned
  // elements like .slide__bg-num. Use per-content-element overflow detection.
  slides.forEach((s, idx) => {
    const sn = idx + 1;
    const sr = s.getBoundingClientRect();
    const cards = [...s.querySelectorAll('.tile, .card, .pattern-grid > *, .alert-row, .slide__title, .slide__body > *')];
    cards.forEach((c) => {
      // Skip decorative absolute elements (background numbers, watermarks)
      if (c.classList.contains('slide__bg-num')) return;
      const cr = c.getBoundingClientRect();
      if (cr.bottom > sr.bottom + 1) {
        issues.push({slide: sn, kind: 'element_below_slide', detail: `${Math.round(cr.bottom - sr.bottom)}px`, sample: c.className});
      }
      if (cr.right > sr.right + 1) {
        issues.push({slide: sn, kind: 'element_right_of_slide', detail: `${Math.round(cr.right - sr.right)}px`, sample: c.className});
      }
    });

    // 2026-06-06 (사용자 검수): body 내용이 footer를 덮거나(overlap) footer
    // 위로 과한 여백(underfill)을 남기는지 검사. 둘 다 슬라이드 박스 '안'에서
    // 일어나 위의 element-overflow 체크로는 안 잡혔다.
    const body = s.querySelector('.slide__body');
    const footer = s.querySelector('.slide__footer');
    if (body && footer) {
      const fr = footer.getBoundingClientRect();
      const slideH = sr.height || 720;
      // 전체 출혈(full-bleed) 이미지·배경 비주얼은 footer 아래까지 깔리도록
      // 설계된 것이므로 제외 (footer 가 그 위에 z-index 로 올라앉음). 진짜
      // 겹침은 텍스트/표/카드가 footer 를 침범하는 경우다.
      const IMG_TAGS = new Set(['IMG','FIGURE','PICTURE','CANVAS','SVG','VIDEO']);
      const isVisual = (el) => {
        if (IMG_TAGS.has(el.tagName)) return true;
        const cn = (typeof el.className === 'string' ? el.className : '');
        return /__visual|bg-image|ai-visual|hero-img|full-bleed|-image\b|__img/.test(cn);
      };
      let maxBottom = 0, deepest = '';
      body.querySelectorAll('*').forEach((c) => {
        if (c.classList.contains('slide__bg-num')) return;
        const cs = getComputedStyle(c);
        if (cs.position === 'absolute' || cs.position === 'fixed') return; // 장식 핀 제외
        if (isVisual(c)) return;                 // 풀블리드 이미지/배경 제외
        if (c.closest && c.closest('figure, .bg-image-split__visual')) return; // 비주얼 컨테이너 내부도 제외
        const r = c.getBoundingClientRect();
        if (r.height > 0 && r.bottom > maxBottom) { maxBottom = r.bottom; deepest = c.className; }
      });
      if (maxBottom > 0) {
        const gap = fr.top - maxBottom;            // 음수 = footer 침범
        const gapPct = (gap / slideH) * 100;
        if (gap < -3) {
          issues.push({slide: sn, kind: 'body_overlaps_footer', detail: `${Math.round(-gap)}px`, sample: String(deepest).slice(0,40)});
        } else if (gapPct > 9) {
          issues.push({slide: sn, kind: 'body_underfills', detail: `${Math.round(gap)}px (${gapPct.toFixed(0)}%)`, sample: String(deepest).slice(0,40)});
        }
      }
    }
  });
  return issues;
})()
"""


def validate_html_file(html_path: Path, kind: str = "auto") -> list[dict]:
    """Validate a single HTML file. kind: 'handout' | 'deck' | 'auto' (sniff)."""
    if kind == "auto":
        text = html_path.read_text(encoding="utf-8")
        path_parts = set(html_path.resolve().parts)
        if "clinic-handout-a4.css" in text or "lab-reports" in path_parts or "handouts" in path_parts:
            kind = "handout"
        else:
            kind = "deck"

    viewport = A4_VIEWPORT if kind == "handout" else DECK_VIEWPORT
    js = HANDOUT_VALIDATOR_JS if kind == "handout" else DECK_VALIDATOR_JS

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport=viewport)
        page.goto(html_path.resolve().as_uri())
        page.wait_for_load_state("networkidle")
        issues = page.evaluate(js)
        browser.close()
    return issues


def main():
    targets: list[Path] = []
    if len(sys.argv) > 1:
        targets = [Path(arg).resolve() for arg in sys.argv[1:]]
    else:
        # Walk handouts/, lab-reports/, decks/ for index.html files
        for sub in ("handouts", "lab-reports", "decks"):
            d = ROOT / sub
            if d.exists():
                targets.extend(sorted(d.rglob("index.html")))

    if not targets:
        print("no HTML targets found")
        sys.exit(0)

    total_issues = 0
    for t in targets:
        rel = t.relative_to(ROOT) if t.is_relative_to(ROOT) else t
        issues = validate_html_file(t)
        if issues:
            total_issues += len(issues)
            print(f"\n❌ {rel}  ({len(issues)} issues)")
            for it in issues:
                print(f"   · {json.dumps(it, ensure_ascii=False)}")
        else:
            print(f"✓ {rel}")

    print(f"\n{'-' * 60}")
    if total_issues:
        print(f"FAIL: {total_issues} layout issue(s) across {len(targets)} files")
        sys.exit(1)
    else:
        print(f"OK: {len(targets)} files, no layout issues")
        sys.exit(0)


if __name__ == "__main__":
    main()
