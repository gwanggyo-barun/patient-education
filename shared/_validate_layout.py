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

# ── large_internal_gap 래칫 (2026-06-14, 원장 검수) ──────────────────────────
# 새 검사 large_internal_gap 은 BLOCKING 이다 (≥140px 빈 띠 = 추한 갭, 차단).
# 전수검사 결과 같은 안티패턴을 가진 기존 덱 7종이 이미 존재한다(아래). 이들을
# 지금 일괄 수정하면 무관한 덱을 건드리게 되므로(원장 지시: "don't auto-fix
# unrelated decks"), 기존 부채로 '유예 등록(grandfather)'해 CI 를 막지 않게 한다.
# ⚠️ 새 덱/수정 덱은 유예 대상이 아니다 — large_internal_gap 은 완전 차단된다.
# 유예된 덱을 손볼 때 이 갭도 같이 고치고, 고친 항목은 이 목록에서 제거할 것.
# (refractory-dyspepsia 는 이번에 고쳤으므로 목록에 없다 = 완전 게이트됨.)
GRANDFATHERED_INTERNAL_GAP = {
    "decks/cardio/htn-2025-aha-acc/index.html",
    "decks/emergency/endoscopy/cpr-training/index.html",
    "decks/endocrine/prediabetes-remission/index.html",
    "decks/general/papers-20260525/vutrisiran-attr-cm-helios-b/index.html",
    "decks/gi/bowel-prep-low-volume/index.html",
    "decks/gi/h-pylori/eradication/index.html",
    "decks/vaccines/pneumococcal-comparison/index.html",
}

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
      // ⚠️ 타임라인 카드(timeline-step/step-card)·.tile 은 body-fill(BOXSEL) 측정에서 제외한다.
      // 새 표준에서 카드 내용은 '중앙 정렬'이고, 이미지 짝(visual-focus) 슬라이드에선 카드 열이
      // 이미지보다 짧다 — 이미지가 하단을 채우는데도(이미지는 figure라 측정 제외) 카드 바닥이
      // footer 위 100px+ 라 거짓 body_underfills 가 난다. (timeline 카드 넘침은 아래 per-box 루프가 잡음.)
      const BOXSEL = '.stat-card,.review-card,.step,.flow-card,.tbl-row,.takehome-card,.note,.bars,.closing-contact,.qr-block,.line-list li';
      let maxBottom = 0, deepest = '';
      s.querySelectorAll(BOXSEL).forEach((c) => {
        if (c.closest && c.closest('figure, .bg-image-split__visual, .ai-visual, .slide__footer, .pattern-timeline')) return;
        const cs = getComputedStyle(c);
        if (cs.position === 'absolute' || cs.position === 'fixed') return;
        const r = c.getBoundingClientRect();
        if (r.height > 6 && r.bottom > maxBottom) { maxBottom = r.bottom; deepest = (typeof c.className==='string'?c.className:''); }
      });
      // 텍스트 leaf 폴백 (박스 없는 슬라이드)
      // ⚠️ 2026-06-14: 폴백은 본문 콘텐츠의 '최상단(minTop)'도 함께 잰다.
      // 새 표준(Gotcha 21)에서 짧은 카드/리스트는 박스 안에서 '세로 중앙정렬'
      // 되므로 위·아래에 대칭 여백이 남는다 — 이건 의도된 중앙정렬이지 언더필이
      // 아니다. 아래에서 (위 여백 ≈ 아래 여백)이면 body_underfills 를 면제한다.
      let minTop = Infinity;
      if (maxBottom === 0) {
        const bodyTop = body.getBoundingClientRect().top;
        body.querySelectorAll('*').forEach((c) => {
          if (c.children.length > 0 || !c.textContent.trim()) return;
          if (c.closest && c.closest('figure, .ai-visual, .slide__footer, .pattern-timeline')) return;
          const r = c.getBoundingClientRect();
          if (r.height <= 0) return;
          if (r.bottom > maxBottom) { maxBottom = r.bottom; deepest = (c.parentElement&&typeof c.parentElement.className==='string')?c.parentElement.className:''; }
          if (r.top < minTop) minTop = r.top;
        });
      }
      if (maxBottom > 0) {
        const gap = fr.top - maxBottom;            // 음수 = footer 침범, 0~3 = 닿음
        // 본문 콘텐츠 위쪽 빈공간(body 상단 ~ 첫 콘텐츠). 폴백에서만 측정됨.
        const topGap = (minTop !== Infinity) ? (minTop - body.getBoundingClientRect().top) : 0;
        // footer.top 은 푸터 '상단 경계선'이고 실제 텍스트는 그 아래 padding-top
        // (16px)+border 만큼 떨어져 있다. 따라서 박스 하단이 footer.top 에 닿는
        // (gap 0) 건 구조상 정상(텍스트와 17px 여유)이고, 박스가 그 경계선을
        // 실제로 가로지를 때(gap < -3)만 진짜 침범이다. 잘려 넘치는 텍스트는
        // 아래 box_content_overflow 가 따로 잡는다.
        if (gap < -3) {
          issues.push({slide: sn, kind: 'body_overlaps_footer', detail: `gap ${Math.round(gap)}px (crosses footer line)`, sample: String(deepest).slice(0,40)});
        } else if (gap > 72) {
          // 본문 최하단~푸터 여백이 72px 초과 = 언더필 (24~56 적정, <16 과밀).
          // 단, 콘텐츠가 세로 중앙정렬되어 위쪽에도 비슷한 여백(top ≳ bottom*0.6)이
          // 있으면 의도된 중앙정렬이므로 면제 (Gotcha 21 fix false-positive 회피).
          const centered = topGap >= gap * 0.6;
          // visual-focus 슬라이드: 옆 이미지가 푸터 근처까지 세로를 채우면(텍스트 열보다
          // 길다) 텍스트 열이 중앙정렬로 짧아도 빈 슬라이드가 아니다 → 면제.
          let imgFills = false;
          if (body.classList.contains('slide__body--visual-focus')) {
            const fig = s.querySelector('figure.ai-visual, .ai-visual, .paper-visual');
            // 이미지가 텍스트 열만큼(또는 그 이상) 아래로 내려가 본문 세로를 채우면
            // (figr.bottom ≥ 텍스트 maxBottom) 텍스트 열이 짧아도 빈 슬라이드가 아니다.
            if (fig) { const figr = fig.getBoundingClientRect(); if (figr.bottom >= maxBottom - 4) imgFills = true; }
          }
          if (!centered && !imgFills) {
            issues.push({slide: sn, kind: 'body_underfills', detail: `${Math.round(gap)}px`, sample: String(deepest).slice(0,40)});
          }
        }
      }

      // 2026-06-06 황금비율 룰 (reference/deck-design-proportions.md):
      // ① box_underfill: 박스 하단 빈공간 >28px AND >25% (px+비율 병행)
      // ② font_too_small: 박스/표 본문 <15px 차단
      // ③ content_image_gutter: 콘텐츠 열↔이미지 <24px 차단
      const cssNum = (el, prop) => parseFloat(getComputedStyle(el)[prop]) || 0;
      // ① + ② : 콘텐츠 박스 순회
      s.querySelectorAll('.stat-card,.review-card,.step,.flow-card,.tbl-row:not(.tbl-row--head),.line-list li,.timeline-step,.step-card').forEach((box) => {
        const br = box.getBoundingClientRect();
        if (br.height < 40) return;
        // 타임라인 카드(timeline-step/step-card)는 grid stretch + 의도적 중앙정렬이라
        // 짧은 내용이면 자연히 위·아래 여백이 생긴다 → overflow 만 잡고
        // font_too_small / box_underfill / sparse_box 는 면제(사용자 룰: 의도적 중앙정렬 false positive 회피).
        const boxCl0 = (typeof box.className==='string'?box.className:'');
        const isTLcard = /timeline-step|step-card/.test(boxCl0);
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
          if (!isTLcard && fs > 0 && fs < 15 && !/value|metric|__num|stars|kicker|label|eyebrow/.test(cls)) {
            issues.push({slide: sn, kind: 'font_too_small', detail: `${fs.toFixed(1)}px`, sample: cls.slice(0,30) || t.tagName});
          }
        });
        const padBottom = cssNum(box, 'paddingBottom');
        const padTop = cssNum(box, 'paddingTop');
        const emptyBottom = br.bottom - cb - padBottom;      // 패딩 제외 하단 빈공간
        const emptyTop = ct - br.top - padTop;               // 패딩 제외 상단 빈공간
        // 언더필 = 비대칭(내용이 위로 몰림): 하단 공백이 28px↑이고, 상단보다 24px↑ 더 큼.
        // 세로 중앙정렬(상·하단 공백 비슷)은 대칭이므로 통과.
        if (!isTLcard && emptyBottom > 28 && (emptyBottom - emptyTop) > 24) {
          issues.push({slide: sn, kind: 'box_underfill', detail: `bottom ${Math.round(emptyBottom)}px vs top ${Math.round(emptyTop)}px`, sample: (typeof box.className==='string'?box.className:'').split(' ')[0]});
        }
        // sparse_box (코덱스 2차): 대칭이어도 박스가 콘텐츠보다 과하게 큼.
        // inner_fill = 보이는 내용높이 / 박스 내부높이. <0.55 면 경고(작은 박스·라벨류 제외).
        const innerH = box.clientHeight - padTop - padBottom;
        const contentH = cb - ct;
        if (innerH > 90 && contentH > 0) {
          const innerFill = contentH / innerH;
          const cl = (typeof box.className==='string'?box.className:'');
          if (!isTLcard) {
            // 큰 숫자 메트릭 카드(stat-card)는 값이 짧아 자연히 낮으므로 더 관대(0.40)
            // 코덱스 권고 카드 목표 0.50~0.68 → 0.48 미만만 경고(0.51 등 경계 통과), stat 0.40
            const floor = /stat-card/.test(cl) ? 0.40 : 0.48;
            if (innerFill < floor) {
              issues.push({slide: sn, kind: 'sparse_box', detail: `fill ${(innerFill*100).toFixed(0)}% (box ${Math.round(box.clientHeight)}px)`, sample: cl.split(' ')[0]});
            }
          }
        }
      });
      // ④ large_internal_gap (2026-06-14, 원장 검수): 카드/타일/행/리스트-아이템
      // 컨테이너 '안'에서, 늘어난 박스를 채우려고 콘텐츠를 양끝으로 밀어 생긴
      // 큰 빈 세로 띠를 잡는다. margin-top:auto / justify-content·align-content:
      // space-between/space-around 의 전형적 증상 — 연속한 보이는 자식 사이
      // 또는 (단일 그룹일 때) 그룹 위/아래에 GAP_T 초과의 빈 공간이 생긴다.
      // 박스 자체가 콘텐츠보다 큰 sparse_box 와 달리, 이건 '한 박스 내부에서
      // 콘텐츠 덩어리들이 서로 멀리 떨어진' 경우를 직접 짚는다.
      // 임계값 튜닝 (2026-06-14 전수검사): 라이브러리 표준 .tile 레이아웃은
      // 88~117px 의 자연스러운 카드 여백을 정상적으로 만든다(전 자료 분포의 최빈값
      // 89px). dyspepsia 의 추한 빈 띠는 162~302px 였다. 따라서 140px 를 컷오프로
      // 두면 정상 카드 간격은 모두 통과하고, 추한 띠(≥145px)만 잡힌다.
      const GAP_T = 140;  // px
      const GAPSEL = '.tile,.card,.myth-tile,.lsm-item,.dt-row,.check-item,.stats3-cell,.split__left,.split__right,.flow-card,.step,.step-card,.review-card,.stat-card';
      s.querySelectorAll(GAPSEL).forEach((box) => {
        const cs = getComputedStyle(box);
        if (cs.display === 'none') return;
        const br = box.getBoundingClientRect();
        if (br.height < 60) return;
        // 타임라인 카드는 의도적 중앙정렬(위·아래 대칭 여백) → 면제.
        const bcl = (typeof box.className==='string'?box.className:'');
        if (/timeline-step|step-card/.test(bcl)) return;
        // 박스 안 '보이는 콘텐츠'의 세로 구간들을 모아, 연속 구간 사이 빈 띠를 본다.
        // (텍스트/이미지 leaf 의 top~bottom 구간을 1px 단위로 합집합)
        const padTop2 = parseFloat(cs.paddingTop) || 0;
        const padBot2 = parseFloat(cs.paddingBottom) || 0;
        const innerTop = br.top + padTop2, innerBot = br.bottom - padBot2;
        const spans = [];
        box.querySelectorAll('*').forEach((t) => {
          if (t.children.length > 0) return;          // leaf 만
          if (!t.textContent.trim() && !/IMG|SVG|CANVAS|PICTURE/.test(t.tagName)) return;
          const cs2 = getComputedStyle(t);
          if (cs2.display === 'none' || cs2.visibility === 'hidden') return;
          const r = t.getBoundingClientRect();
          if (r.height <= 0 || r.width <= 0) return;
          spans.push([Math.max(r.top, innerTop), Math.min(r.bottom, innerBot)]);
        });
        if (spans.length === 0) return;
        spans.sort((a,b) => a[0]-b[0]);
        // 연속 구간 사이 최대 빈 띠
        let worst = 0, prevBot = spans[0][1];
        for (let i = 1; i < spans.length; i++) {
          const g = spans[i][0] - prevBot;
          if (g > worst) worst = g;
          if (spans[i][1] > prevBot) prevBot = spans[i][1];
        }
        if (worst > GAP_T) {
          issues.push({slide: sn, kind: 'large_internal_gap', detail: `${Math.round(worst)}px between children`, sample: bcl.split(' ')[0]});
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


# ---------------------------------------------------------------------------
# WCAG CONTRAST ADVISORY (non-blocking, design-untouched)
# ---------------------------------------------------------------------------
# Walks every visible text node, reads its computed color + the effective
# (first non-transparent ancestor) background, and computes the WCAG 2.x
# contrast ratio. Returns ONLY violations for small text below 4.5:1.
#
# This is ADVISORY: build.py prints these as ⚠️ warnings and never fails the
# build. No color is changed. Large text (≥24px, or ≥18.66px AND bold) only
# needs 3:1 and is intentionally NOT collected here, so navy titles, big stat
# numbers, and accent-colored headings stay exempt and unflagged.
CONTRAST_ADVISORY_JS = r"""
(() => {
  const warnings = [];

  const parseRGB = (s) => {
    if (!s) return null;
    const m = s.match(/rgba?\(([^)]+)\)/i);
    if (!m) return null;
    const parts = m[1].split(',').map(x => parseFloat(x.trim()));
    const [r, g, b] = parts;
    const a = parts.length > 3 ? parts[3] : 1;
    return {r, g, b, a};
  };

  // Effective background = first ancestor with a non-transparent bg color,
  // alpha-composited onto white (paper). Good enough for flat handout cards.
  const effectiveBg = (el) => {
    let node = el;
    const stack = [];
    while (node && node.nodeType === 1) {
      const bg = parseRGB(getComputedStyle(node).backgroundColor);
      if (bg && bg.a > 0) { stack.push(bg); if (bg.a >= 1) break; }
      node = node.parentElement;
    }
    // Composite from bottom (white paper) up.
    let base = {r: 255, g: 255, b: 255};
    for (let i = stack.length - 1; i >= 0; i--) {
      const c = stack[i], a = c.a;
      base = {
        r: c.r * a + base.r * (1 - a),
        g: c.g * a + base.g * (1 - a),
        b: c.b * a + base.b * (1 - a),
      };
    }
    return base;
  };

  const lin = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  const lum = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const ratio = (a, b) => { const L1 = lum(a), L2 = lum(b); const hi = Math.max(L1, L2), lo = Math.min(L1, L2); return (hi + 0.05) / (lo + 0.05); };

  const isVisible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };

  const seen = new Set();
  // Walk text-bearing leaf-ish elements.
  document.querySelectorAll('body *').forEach((el) => {
    // Only elements that directly hold visible text (a direct text child).
    let txt = '';
    for (const n of el.childNodes) {
      if (n.nodeType === 3 && n.textContent.trim()) txt += n.textContent;
    }
    txt = txt.trim();
    if (!txt) return;
    if (!isVisible(el)) return;

    const cs = getComputedStyle(el);
    const fg = parseRGB(cs.color);
    if (!fg || fg.a === 0) return;
    const bg = effectiveBg(el);
    // Composite foreground over its background if the text color itself has alpha.
    const fgComposited = fg.a < 1
      ? {r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a)}
      : fg;

    const fontPx = parseFloat(cs.fontSize) || 16;
    const weight = parseInt(cs.fontWeight, 10) || 400;
    const isBold = weight >= 700;
    // WCAG "large text": ≥24px, or ≥18.66px AND bold.
    const isLarge = fontPx >= 24 || (fontPx >= 18.66 && isBold);
    if (isLarge) return;   // large text exempt (only needs 3:1) — not collected

    const cr = ratio(fgComposited, bg);
    if (cr < 4.5) {
      // Build a short, stable selector for the offending node.
      let sel = el.tagName.toLowerCase();
      if (el.id) sel += '#' + el.id;
      else if (typeof el.className === 'string' && el.className.trim()) {
        sel += '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.');
      }
      const snippet = txt.replace(/\s+/g, ' ').slice(0, 32);
      const key = sel + '|' + cr.toFixed(2) + '|' + snippet;
      if (seen.has(key)) return;
      seen.add(key);
      warnings.push({
        selector: sel,
        ratio: cr.toFixed(1),
        font_px: Math.round(fontPx),
        snippet: snippet,
      });
    }
  });
  return warnings;
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
    grandfathered_total = 0
    for t in targets:
        rel = t.relative_to(ROOT) if t.is_relative_to(ROOT) else t
        rel_str = str(rel).replace("\\", "/")
        issues = validate_html_file(t)
        # large_internal_gap 래칫: 유예 등록된 기존 덱에서는 이 종류만 비차단
        # 경고로 강등(다른 종류는 그대로 차단). 새/수정 덱은 강등 없음 → 완전 차단.
        grandfathered = []
        if rel_str in GRANDFATHERED_INTERNAL_GAP:
            kept = []
            for it in issues:
                if it.get("kind") == "large_internal_gap":
                    grandfathered.append(it)
                else:
                    kept.append(it)
            issues = kept
        if issues:
            total_issues += len(issues)
            print(f"\n❌ {rel}  ({len(issues)} issues)")
            for it in issues:
                print(f"   · {json.dumps(it, ensure_ascii=False)}")
        else:
            print(f"✓ {rel}")
        if grandfathered:
            grandfathered_total += len(grandfathered)
            print(f"   ⚠️  (grandfathered, non-blocking) {len(grandfathered)} large_internal_gap — pre-existing 부채, 추후 수정 대상:")
            for it in grandfathered:
                print(f"      · {json.dumps(it, ensure_ascii=False)}")

    print(f"\n{'-' * 60}")
    if grandfathered_total:
        print(f"NOTE: {grandfathered_total} grandfathered large_internal_gap warning(s) in pre-existing decks (non-blocking — see GRANDFATHERED_INTERNAL_GAP)")
    if total_issues:
        print(f"FAIL: {total_issues} layout issue(s) across {len(targets)} files")
        sys.exit(1)
    else:
        print(f"OK: {len(targets)} files, no blocking layout issues")
        sys.exit(0)


if __name__ == "__main__":
    main()
