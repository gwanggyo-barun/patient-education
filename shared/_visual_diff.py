"""이미지 삽입 전/후 스냅샷 visual diff — 레이아웃 회귀 가드 (handouts v2 P3).

역할: Step 3.5.d 에서 이미지를 슬롯에 삽입하기 **직전**(before)과 **직후**(after)의
페이지 스냅샷 PNG 를 비교해, 의도한 슬롯 영역 밖에서 픽셀이 변했으면(=본문 밀림·겹침·
잘림·푸터 침범 같은 회귀) `regressed=True` 를 반환한다.
`shared._validate_layout` 통과와 **AND 게이트** — 둘 다 통과해야 이미지 채택
(둘 중 하나라도 실패 → 슬롯 크기/배치 보정 후 재검, 최대 2회 → 그래도 실패면 이미지 생략).

Usage:
    # 1) 삽입 전 스냅샷
    python3 -m shared._visual_diff capture <html_path> /tmp/before.png
    # 2) (이미지 삽입 편집)
    # 3) 삽입 후 스냅샷 + 비교 (슬롯 bbox 는 px, 캡처 viewport 좌표계)
    python3 -m shared._visual_diff capture <html_path> /tmp/after.png
    python3 -m shared._visual_diff compare /tmp/before.png /tmp/after.png \
        --slot-bbox X,Y,W,H [--slot-bbox X2,Y2,W2,H2 ...]

Returns exit 0 = no regression, 1 = regressed (빌드/채택 게이트용).
환경변수 HANDOUT_V2_GATES=0 이면 경고만 출력하고 exit 0.

## 회귀 판정 (초기값 — 전부 캘리브레이션 대상, 04_PROJECT_SPEC §6)
- 슬롯 bbox(+MARGIN_PX 여유) **안**의 변화 = 의도된 변화 → 마스킹.
- 마스크 밖 변화 픽셀 비율 > DIFF_T → regressed. (겹침/잘림은 0 허용이 원칙이라
  임계를 매우 낮게 시작한다. 안티앨리어싱 오탐은 PIXEL_TOL 로 흡수.)

## TODO (고급 캘리브레이션 — 기본 capture/compare 는 동작 검증 완료, evals/gates 참조)
- [ ] 멀티페이지 handout: .page 단위 캡처/비교 (현재 full-page 단일 스크린샷)
- [ ] 회귀 위치 리포트 고도화: 변화 클러스터의 bbox 를 묶어 "page 2 footer 근처" 식으로 출력
- [ ] 폰트 로딩 타이밍 오탐 마스킹 (Pretendard swap 전후 캡처 방지 — 현재 networkidle 대기만)
- [ ] DIFF_T / PIXEL_TOL / MARGIN_PX 캘리브레이션 (정상 삽입 N건 + 의도적 깨짐 N건 corpus)
- [ ] decks(1280×720)/lab-reports 지원은 P5 — 현재 handouts A4 우선
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent

# ── 임계 초기값 (캘리브레이션 대상) ─────────────────────────────────────────
DIFF_T = 0.002      # 마스크 밖 변화 픽셀 비율 허용 상한 (0.2% — 겹침/잘림 0 지향)
PIXEL_TOL = 12      # 채널당 픽셀값 차이 허용 (안티앨리어싱/JPEG 노이즈 흡수)
MARGIN_PX = 8       # 슬롯 bbox 주변 여유 마스크 (보더/그림자 변화 허용)

A4_VIEWPORT = {"width": 794, "height": 1123}


def capture(html_path: str | Path, out_png: str | Path) -> Path:
    """handout HTML 을 print 미디어로 렌더링해 full-page 스냅샷 PNG 저장."""
    from playwright.sync_api import sync_playwright

    html_path = Path(html_path).resolve()
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport=A4_VIEWPORT)
        page.emulate_media(media="print")
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts && document.fonts.ready")
        page.screenshot(path=str(out_png), full_page=True)
        browser.close()
    return out_png


def compare(before_png: str | Path, after_png: str | Path,
            slot_bboxes: list[tuple[int, int, int, int]] | None = None) -> dict:
    """before/after PNG 픽셀 비교. 슬롯 bbox(+여유) 는 마스킹하고 나머지 변화율 산출.

    Returns: {"regressed": bool, "diff_ratio": float, "changed_px": int,
              "size_changed": bool, "note": str}
    """
    from PIL import Image, ImageChops

    b = Image.open(before_png).convert("RGB")
    a = Image.open(after_png).convert("RGB")
    if b.size != a.size:
        # 페이지 높이 자체가 변함 = 본문 밀림/페이지 넘침 가능성 → 즉시 회귀로 본다.
        return {"regressed": True, "diff_ratio": 1.0, "changed_px": -1,
                "size_changed": True,
                "note": f"snapshot size changed {b.size} -> {a.size} (본문 밀림/오버플로 의심)"}

    diff = ImageChops.difference(b, a)
    px = diff.load()
    w, h = diff.size
    masks = []
    for (x, y, bw, bh) in (slot_bboxes or []):
        masks.append((max(0, x - MARGIN_PX), max(0, y - MARGIN_PX),
                      min(w, x + bw + MARGIN_PX), min(h, y + bh + MARGIN_PX)))

    changed = 0
    total = 0
    for yy in range(h):
        for xx in range(w):
            if any(mx0 <= xx < mx1 and my0 <= yy < my1 for (mx0, my0, mx1, my1) in masks):
                continue
            total += 1
            r, g, bl = px[xx, yy]
            if max(r, g, bl) > PIXEL_TOL:
                changed += 1
    ratio = (changed / total) if total else 0.0
    return {"regressed": ratio > DIFF_T, "diff_ratio": round(ratio, 6),
            "changed_px": changed, "size_changed": False,
            "note": f"masked slots={len(masks)}, DIFF_T={DIFF_T}"}


def _parse_bbox(s: str) -> tuple[int, int, int, int]:
    x, y, w, h = (int(v) for v in s.split(","))
    return (x, y, w, h)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, *rest = argv
    if cmd == "capture":
        if len(rest) < 2:
            print("❌ usage: capture <html_path> <out_png>")
            return 2
        html, out = rest[0], rest[1]
        if not Path(html).exists():
            print(f"❌ HTML 파일 없음: {html}")
            return 2
        p = capture(html, out)
        print(f"✓ snapshot saved: {p}")
        return 0
    if cmd == "compare":
        bboxes = []
        args = []
        it = iter(rest)
        for a in it:
            if a == "--slot-bbox":
                try:
                    bboxes.append(_parse_bbox(next(it)))
                except (StopIteration, ValueError):
                    print("❌ --slot-bbox 는 X,Y,W,H 정수 4개여야 함 (예: --slot-bbox 100,300,594,200)")
                    return 2
            else:
                args.append(a)
        if len(args) < 2:
            print("❌ usage: compare <before.png> <after.png> [--slot-bbox X,Y,W,H ...]")
            return 2
        for png in args[:2]:
            if not Path(png).exists():
                print(f"❌ 스냅샷 PNG 없음: {png}")
                return 2
        res = compare(args[0], args[1], bboxes)
        status = "❌ REGRESSED" if res["regressed"] else "✓ no regression"
        print(f"{status} — diff_ratio={res['diff_ratio']} ({res['note']})")
        if res["regressed"] and os.environ.get("HANDOUT_V2_GATES", "1") == "0":
            print("⚠️ HANDOUT_V2_GATES=0 — 게이트 비활성(관찰 모드), exit 0")
            return 0
        return 1 if res["regressed"] else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
