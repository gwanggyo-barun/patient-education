#!/usr/bin/env python3
"""slide_screens.py — deck의 각 슬라이드를 1280x720 PNG로 개별 캡처 (푸시 전 전수 육안검수용).

사용자 룰 (2026-06-06): "최종 완성본을 스스로 페이지 하나하나 열어서
레이아웃 겹침 확인 후 커밋 푸시까지 완료" — integrator(Claude)는 푸시 전에
이 스크립트로 캡처한 슬라이드를 한 장씩 열어(Read) 겹침·잘림·이미지 크롭을
확인해야 한다. (_validate_layout 의 bbox 검사는 시각적 어색함을 못 잡는다)

Usage:
    python3 tools/slide_screens.py decks/endocrine/achieve3-oral-glp1/index.html [outdir]
기본 outdir: /tmp/slide-screens/{slug}/
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    html = Path(sys.argv[1]).resolve()
    if not html.exists():
        print(f"not found: {html}")
        return 1
    slug = html.parent.name
    outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(f"/tmp/slide-screens/{slug}")
    outdir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(html.as_uri())
        page.wait_for_timeout(1500)  # 폰트/이미지 로드
        slides = page.locator("section.slide")
        n = slides.count()
        for i in range(n):
            slides.nth(i).scroll_into_view_if_needed()
            page.wait_for_timeout(120)
            path = outdir / f"slide-{i+1:02d}.png"
            slides.nth(i).screenshot(path=str(path))
            print(path)
        browser.close()
    print(f"== {n} slides → {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
