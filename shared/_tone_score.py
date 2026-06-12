"""ToneScore — 브랜드 톤 일관성 점수 빌드 게이트 (handouts v2 P4).

색 팔레트·타이포·이미지 스타일이 광교바른내과 브랜드 토큰
(`reference/brand-design-system.md` / `shared/design-tokens.css` SoT)과 얼마나
일치하는지 0~100 점수를 산출한다. `score >= T_TONE` 미달이면 경고/차단.

구성 (가중치·임계 전부 초기값 — 캘리브레이션 대상, 04_PROJECT_SPEC §6):
  - palette (40점): 채택 이미지들의 도미넌트 컬러 vs 브랜드 팔레트 RGB 거리
  - typo    (30점): HTML 이 Pretendard 를 로드하고 비표준 font-family 를 안 쓰는지
  - image_style (30점): 이미지가 하우스 스타일(세미리얼·네이비/스틸블루 톤)인지
                        — **VLM 판정 필요. 결정론 코드로는 팔레트 근사만 가능 → 현재
                        에이전트가 --image-style-ok {0|1} 로 판정값을 주입한다 (stub).**

Usage:
    python3 -m shared._tone_score <html_path> [--image-style-ok 0|1] [--warn-only]

Returns exit 0 if score >= T_TONE (or --warn-only), 1 otherwise.
환경변수 HANDOUT_V2_GATES=0 이면 경고만 출력하고 exit 0.

## TODO (코드 완성 필요 — stub 명세)
- [x] design-tokens.css 를 파싱해 BRAND_PALETTE 자동 동기화 (실패 시 하드코딩 스냅샷 폴백)
      — 단, 토큰 *선정*(어떤 --color-* 가 "이미지 허용 팔레트"인가)은 여전히
      BRAND_PALETTE_TOKENS 화이트리스트가 정책 SoT. warning/danger 같은 시맨틱 색을
      전부 넣으면 게이트가 무력화되므로 자동 전수 수집은 의도적으로 안 한다 (TODO:
      reference/brand-design-system.md 에 "이미지 팔레트" 섹션 신설 후 그걸 파싱).
- [ ] 팔레트 거리: RGB 유클리드 → CIEDE2000 근사로 교체 + 화이트/뉴트럴 배경 제외 가중
- [ ] typo 검사: 렌더링된 computed font-family 검사(Playwright)로 강화 (현재 정적 HTML 스캔)
- [ ] image_style_ok 자동화: VLM 호출 또는 스타일 임베딩 비교 (현재 에이전트 판정 주입)
- [ ] 기존 대표 핸드아웃(bone-density-prep·colonoscopy-prep·insulin-start) corpus 로 T_TONE 캘리브레이션
- [ ] decks / lab-reports 확장 (P5)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
GENERATED_RE = re.compile(r"assets/generated/([\w.\-]+\.(?:png|webp|jpe?g))")

# ── 임계 (초기값 — 캘리브레이션 대상) ──────────────────────────────────────
T_TONE = 80           # 빌드 게이트 하한 (04_PROJECT_SPEC §6)
PALETTE_DIST_FULL = 40.0   # 평균 RGB 거리 ≤ 이 값이면 palette 만점
PALETTE_DIST_ZERO = 140.0  # 평균 RGB 거리 ≥ 이 값이면 palette 0점 (선형 보간)

# 이미지에 허용되는 브랜드 팔레트의 토큰 화이트리스트 (정책 SoT — 시맨틱 경고/위험색 제외).
# 실제 RGB 값은 shared/design-tokens.css 에서 자동 파싱해 동기화한다.
BRAND_PALETTE_TOKENS = [
    "navy", "navy-deep", "navy-mid",
    "steel", "steel-deep", "sky",
    "ink", "canvas", "canvas-warm",
]

# 하드코딩 스냅샷 — design-tokens.css 파싱 실패 시 폴백 (값은 2026-06 기준 토큰과 동일)
_BRAND_PALETTE_FALLBACK = [
    (0x00, 0x33, 0x66),  # navy
    (0x07, 0x19, 0x3A),  # navy-deep
    (0x1A, 0x2C, 0x4D),  # navy-mid
    (0x5B, 0x9B, 0xD5),  # steel
    (0x2C, 0x5F, 0x8D),  # steel-deep
    (0xBF, 0xE0, 0xFF),  # sky
    (0x1E, 0x29, 0x3B),  # ink
    (0xFF, 0xFF, 0xFF),  # canvas
    (0xFA, 0xFA, 0xF7),  # canvas-warm
]

DESIGN_TOKENS_CSS = ROOT / "shared" / "design-tokens.css"
_HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")


def _hex_to_rgb(h: str) -> tuple:
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def load_brand_palette(css_path: Path = DESIGN_TOKENS_CSS) -> list:
    """design-tokens.css 에서 BRAND_PALETTE_TOKENS 의 --color-{token} hex 를 파싱.

    토큰을 하나라도 못 찾으면 (파일 이동·토큰명 변경 등) 하드코딩 스냅샷으로
    폴백 — 게이트가 깨진 팔레트로 오판하는 것보다 낡은 스냅샷이 안전.
    """
    try:
        css = css_path.read_text(encoding="utf-8")
    except OSError:
        return list(_BRAND_PALETTE_FALLBACK)
    palette = []
    for token in BRAND_PALETTE_TOKENS:
        m = re.search(r"--color-" + re.escape(token) + r"\s*:\s*([^;]+);", css)
        hexm = _HEX_RE.search(m.group(1)) if m else None
        if not hexm:
            return list(_BRAND_PALETTE_FALLBACK)
        palette.append(_hex_to_rgb(hexm.group(1)))
    return palette


BRAND_PALETTE = load_brand_palette()


def palette_distance(image_path: Path, n_colors: int = 8) -> float:
    """이미지 도미넌트 컬러들의 브랜드 팔레트까지 평균 최단 RGB 거리 (낮을수록 좋음)."""
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    img.thumbnail((128, 128))
    pal = img.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT)
    palette = pal.getpalette()[: n_colors * 3]
    dom = [tuple(palette[i: i + 3]) for i in range(0, len(palette), 3)]
    dists = []
    for c in dom:
        d = min(((c[0] - b[0]) ** 2 + (c[1] - b[1]) ** 2 + (c[2] - b[2]) ** 2) ** 0.5
                for b in BRAND_PALETTE)
        dists.append(d)
    return sum(dists) / len(dists) if dists else 0.0


def check_typography(html_path: Path) -> bool:
    """HTML 이 Pretendard 를 로드하고, 인라인 font-family 가 브랜드 외 폰트를 안 쓰는지."""
    html = html_path.read_text(encoding="utf-8")
    if "Pretendard" not in html:
        return False
    # 인라인/스타일 블록의 비표준 폰트 (Pretendard 계열·시스템 폴백 외) 탐지
    for m in re.finditer(r"font-family\s*:\s*([^;}\"']+)", html):
        fam = m.group(1)
        if "Pretendard" not in fam and not re.search(
                r"sans-serif|monospace|inherit|var\(", fam):
            return False
    return True


def score(html_path: Path, image_style_ok: bool | None = None) -> dict:
    """ToneScore 산출. Returns {score, palette_dist, typo_ok, image_style_ok, images}."""
    html_path = Path(html_path)
    html = html_path.read_text(encoding="utf-8")
    gen_dir = ROOT / "shared" / "assets" / "generated"
    images = [gen_dir / m for m in GENERATED_RE.findall(html) if (gen_dir / m).exists()]

    # palette 40
    if images:
        avg = sum(palette_distance(p) for p in images) / len(images)
        frac = max(0.0, min(1.0, (PALETTE_DIST_ZERO - avg) / (PALETTE_DIST_ZERO - PALETTE_DIST_FULL)))
        palette_pts = 40.0 * frac
    else:
        avg = 0.0
        palette_pts = 40.0  # 이미지 없으면 팔레트 감점 없음

    # typo 30
    typo_ok = check_typography(html_path)
    typo_pts = 30.0 if typo_ok else 0.0

    # image_style 30 — VLM 판정 주입 (stub). 미주입 시 보수적으로 통과 처리하되 표기.
    if image_style_ok is None:
        style_pts, style_val = 30.0, "unjudged"
    else:
        style_pts, style_val = (30.0, True) if image_style_ok else (0.0, False)

    total = round(palette_pts + typo_pts + style_pts, 1)
    return {"score": total, "palette_dist": round(avg, 1), "typo_ok": typo_ok,
            "image_style_ok": style_val, "images": [p.name for p in images]}


def main(argv: list[str]) -> int:
    warn_only = "--warn-only" in argv
    argv = [a for a in argv if a != "--warn-only"]
    image_style_ok: bool | None = None
    args = []
    it = iter(argv)
    for a in it:
        if a == "--image-style-ok":
            image_style_ok = next(it) not in ("0", "false", "False")
        else:
            args.append(a)
    if not args:
        print(__doc__)
        return 2
    target = Path(args[0])
    if not target.is_file():
        print(f"❌ HTML 파일이 아님(없거나 디렉터리): {target}")
        return 2
    res = score(target, image_style_ok)
    ok = res["score"] >= T_TONE
    mark = "✓" if ok else "❌"
    print(f"{mark} ToneScore {res['score']}/100 (T_tone={T_TONE}) — "
          f"palette_dist={res['palette_dist']} typo_ok={res['typo_ok']} "
          f"image_style_ok={res['image_style_ok']} images={len(res['images'])}")
    if ok or warn_only:
        return 0
    if os.environ.get("HANDOUT_V2_GATES", "1") == "0":
        print("⚠️ HANDOUT_V2_GATES=0 — 게이트 비활성(관찰 모드), exit 0")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
