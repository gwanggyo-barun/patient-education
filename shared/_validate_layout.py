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

# Windows consoles default to cp949/cp1252 and raise UnicodeEncodeError when
# printing ✓ ❌ status glyphs. Force UTF-8 so Mac and Windows runs print
# identically (SKILL.md rule #1: cross-machine consistency).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

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
      // '보이는 콘텐츠 박스'(배경/테두리 있는 카드·행·패널)의 최하단을 본다.
      // 투명 full-height 래퍼(table-wrap 등)에 속지 않고, 채워진 패널(bars·step)이
      // 푸터까지 닿으면 underfill 아님 / 투명하게 떠 있는 행이면 underfill 로 잡힘.
      // 실제 '콘텐츠' 최하단을 본다. split-col 같은 투명 full-height 래퍼는
      // 배경/테두리가 없어 푸터까지 닿아도 시각적으로 안 채워진다 → 측정에서
      // 빼고, 대신 그 안의 실제 콘텐츠(line-list li 등)를 본다. (BMJ s3 사례:
      // 래퍼는 푸터까지 닿지만 리스트는 60%에서 끝나 underfill 을 놓쳤다.)
      // ⚠️ li 는 마지막 항목이 border-bottom:none 이라도 '보이는 텍스트'이므로
      // paint 여부로 거르지 말 것 — 거르면 실제로 채웠는데 false underfill 난다.
      const BOXSEL = '.stat-card,.review-card,.step,.flow-card,.tbl-row,.takehome-card,.note,.bars,.closing-contact,.qr-block,.line-list li';
      let maxBottom = 0, deepest = '';
      s.querySelectorAll(BOXSEL).forEach((c) => {
        if (c.closest && c.closest('figure, .bg-image-split__visual, .ai-visual, .slide__footer')) return;
        const cs = getComputedStyle(c);
        if (cs.position === 'absolute' || cs.position === 'fixed') return;
        const r = c.getBoundingClientRect();
        if (r.height > 6 && r.bottom > maxBottom) { maxBottom = r.bottom; deepest = (typeof c.className==='string'?c.className:''); }
      });
      // 텍스트 leaf 폴백 (박스 없는 슬라이드)
      if (maxBottom === 0) {
        body.querySelectorAll('*').forEach((c) => {
          if (c.children.length > 0 || !c.textContent.trim()) return;
          if (c.closest && c.closest('figure, .ai-visual, .slide__footer')) return;
          const r = c.getBoundingClientRect();
          if (r.height > 0 && r.bottom > maxBottom) { maxBottom = r.bottom; deepest = (c.parentElement&&typeof c.parentElement.className==='string')?c.parentElement.className:''; }
        });
      }
      if (maxBottom > 0) {
        const gap = fr.top - maxBottom;            // 음수 = footer 침범, 0~3 = 닿음
        // footer.top 은 푸터 '상단 경계선'이고 실제 텍스트는 그 아래 padding-top
        // (16px)+border 만큼 떨어져 있다. 따라서 박스 하단이 footer.top 에 닿는
        // (gap 0) 건 구조상 정상(텍스트와 17px 여유)이고, 박스가 그 경계선을
        // 실제로 가로지를 때(gap < -3)만 진짜 침범이다. 잘려 넘치는 텍스트는
        // 아래 box_content_overflow 가 따로 잡는다.
        if (gap < -3) {
          issues.push({slide: sn, kind: 'body_overlaps_footer', detail: `gap ${Math.round(gap)}px (crosses footer line)`, sample: String(deepest).slice(0,40)});
        } else if (gap > 72) {
          // 본문 최하단~푸터 여백이 72px 초과 = 언더필 (24~56 적정, <16 과밀)
          issues.push({slide: sn, kind: 'body_underfills', detail: `${Math.round(gap)}px`, sample: String(deepest).slice(0,40)});
        }
      }

      // 2026-06-06 황금비율 룰 (reference/deck-design-proportions.md):
      // ① box_underfill: 박스 하단 빈공간 >28px AND >25% (px+비율 병행)
      // ② font_too_small: 박스/표 본문 <15px 차단
      // ③ content_image_gutter: 콘텐츠 열↔이미지 <24px 차단
      const cssNum = (el, prop) => parseFloat(getComputedStyle(el)[prop]) || 0;
      // ① + ② : 콘텐츠 박스 순회
      s.querySelectorAll('.stat-card,.review-card,.step,.flow-card,.tbl-row:not(.tbl-row--head),.line-list li').forEach((box) => {
        const br = box.getBoundingClientRect();
        if (br.height < 40) return;
        // ⓐ 박스 내용 넘침/꽉낌: scrollHeight 가 clientHeight 에 너무 근접하면
        // PDF 래스터라이저의 폰트 메트릭 차이로 실제 PDF 에서 넘쳐 이웃 카드와
        // 겹친다(슬라이드2 사례 — getBoundingClientRect 1px 여유였는데 PDF 겹침).
        // 따라서 최소 4px 여유를 요구한다.
        const slack = box.clientHeight - box.scrollHeight;   // 양수 = 여유, 음수 = 넘침
        // 음수 slack = 내용이 박스보다 큼. overflow:hidden 이어도 텍스트가 잘려
        // 사라지거나(내용 손실) PDF 에서 footer/이웃으로 삐져나가므로 항상 차단.
        if (slack < 0) {
          issues.push({slide: sn, kind: 'box_content_overflow', detail: `overflow ${-slack}px`, sample: (typeof box.className==='string'?box.className:'').split(' ')[0]});
        }
        // 박스 내부 텍스트 최상단/최하단
        let cb = br.top, ct = br.bottom;
        box.querySelectorAll('*').forEach((t) => {
          if (t.children.length) return;
          if (!t.textContent.trim()) return;
          const r = t.getBoundingClientRect();
          if (r.bottom > cb) cb = r.bottom;
          if (r.top < ct) ct = r.top;
          // 폰트 하한 (값 텍스트/숫자 메트릭 제외: 큰 숫자는 짧아 OK)
          const fs = cssNum(t, 'fontSize');
          const cls = (typeof t.className === 'string') ? t.className : '';
          // 큰 숫자/메트릭과 대문자 마이크로 라벨(kicker·label·eyebrow·num)은 본문 하한 면제
          if (fs > 0 && fs < 15 && !/value|metric|__num|stars|kicker|label|eyebrow/.test(cls)) {
            issues.push({slide: sn, kind: 'font_too_small', detail: `${fs.toFixed(1)}px`, sample: cls.slice(0,30) || t.tagName});
          }
        });
        const padBottom = cssNum(box, 'paddingBottom');
        const padTop = cssNum(box, 'paddingTop');
        const emptyBottom = br.bottom - cb - padBottom;      // 패딩 제외 하단 빈공간
        const emptyTop = ct - br.top - padTop;               // 패딩 제외 상단 빈공간
        // 언더필 = 비대칭(내용이 위로 몰림): 하단 공백이 28px↑이고, 상단보다 24px↑ 더 큼.
        // 세로 중앙정렬(상·하단 공백 비슷)은 대칭이므로 통과.
        if (emptyBottom > 28 && (emptyBottom - emptyTop) > 24) {
          issues.push({slide: sn, kind: 'box_underfill', detail: `bottom ${Math.round(emptyBottom)}px vs top ${Math.round(emptyTop)}px`, sample: (typeof box.className==='string'?box.className:'').split(' ')[0]});
        }
        // sparse_box (코덱스 2차): 대칭이어도 박스가 콘텐츠보다 과하게 큼.
        // inner_fill = 보이는 내용높이 / 박스 내부높이. <0.55 면 경고(작은 박스·라벨류 제외).
        const innerH = box.clientHeight - padTop - padBottom;
        const contentH = cb - ct;
        if (innerH > 90 && contentH > 0) {
          const innerFill = contentH / innerH;
          // 큰 숫자 메트릭 카드(stat-card)는 값이 짧아 자연히 낮으므로 더 관대(0.40)
          const cl = (typeof box.className==='string'?box.className:'');
          // 코덱스 권고 카드 목표 0.50~0.68 → 0.48 미만만 경고(0.51 등 경계 통과), stat 0.40
          const floor = /stat-card/.test(cl) ? 0.40 : 0.48;
          if (innerFill < floor) {
            issues.push({slide: sn, kind: 'sparse_box', detail: `fill ${(innerFill*100).toFixed(0)}% (box ${Math.round(box.clientHeight)}px)`, sample: cl.split(' ')[0]});
          }
        }
      });
      // ③ content_image_gutter: visual-focus 2열에서 좌측 콘텐츠 우측 끝 ↔ 이미지 좌측
      const vf = s.querySelector('.slide__body--visual-focus');
      if (vf) {
        const img = s.querySelector('.paper-visual, figure.ai-visual');
        if (img) {
          const ir = img.getBoundingClientRect();
          let maxRight = 0;
          vf.querySelectorAll('.stat-card,.review-card,.step,.flow-card,.tbl-row,.bars,.line-list,.split-col,.note').forEach((el) => {
            if (img.contains(el)) return;
            const r = el.getBoundingClientRect();
            if (r.left < ir.left && r.right > maxRight && r.right <= ir.left + 2) maxRight = r.right;
          });
          if (maxRight > 0) {
            const gutter = ir.left - maxRight;
            if (gutter < 24) issues.push({slide: sn, kind: 'content_image_gutter', detail: `${Math.round(gutter)}px`, sample: 'visual-focus'});
          }
        }
      }
    }
    // ⓓ 형제 박스끼리 실제 겹침 (카드↔카드 충돌) — 2026-06-06 슬라이드2 사례.
    // print 미디어에서 콘텐츠가 넘쳐 이웃 카드와 박스가 물리적으로 겹치는 경우.
    const SIB = '.stat-card,.review-card,.step,.flow-card,.tbl-row,.takehome-card,.note';
    const sibs = [...s.querySelectorAll(SIB)].map(e => ({e, r: e.getBoundingClientRect()})).filter(x => x.r.width > 4 && x.r.height > 4);
    for (let i = 0; i < sibs.length; i++) {
      for (let j = i + 1; j < sibs.length; j++) {
        const A = sibs[i], B = sibs[j];
        if (A.e.contains(B.e) || B.e.contains(A.e)) continue;
        const ox = Math.min(A.r.right, B.r.right) - Math.max(A.r.left, B.r.left);
        const oy = Math.min(A.r.bottom, B.r.bottom) - Math.max(A.r.top, B.r.top);
        if (ox > 2 && oy > 2) {
          issues.push({slide: sn, kind: 'sibling_box_overlap', detail: `${Math.round(ox)}x${Math.round(oy)}px`, sample: (typeof A.e.className==='string'?A.e.className:'').split(' ')[0]});
        }
      }
    }
  });
  // 동일 (slide,kind) 중복 제거
  const seen = new Set(), uniq = [];
  issues.forEach((it) => { const k = it.slide+'|'+it.kind+'|'+(it.sample||''); if (!seen.has(k)) { seen.add(k); uniq.push(it); } });
  return uniq;
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
        # ⭐ 2026-06-06: PDF는 print 미디어로 렌더되므로 검증도 print 로 맞춘다.
        # screen 미디어에서만 보면 print 의 미세 폰트 메트릭 차이로 생기는
        # 카드 겹침(슬라이드2 사례)을 놓친다.
        if kind == "deck":
            page.emulate_media(media="print")
            page.wait_for_timeout(300)
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
