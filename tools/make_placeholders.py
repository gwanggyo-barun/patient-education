"""Temporary placeholder images for blood-draw-aftercare and urine-collection-restroom.

Replace these files with real photos/illustrations later — the HTML img src paths
will pick up the new files automatically.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "shared" / "assets" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = (0, 51, 102)
STEEL = (91, 155, 213)
CREAM = (244, 241, 235)
INK = (30, 41, 59)
SLATE = (100, 116, 139)
DANGER_BG = (254, 242, 242)
BRUISE = (108, 60, 95)
WARM = (250, 250, 247)

def font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def placeholder(path: Path, w: int, h: int, bg, label: str, sublabel: str = "") -> None:
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w - 1, h - 1), outline=(226, 232, 240), width=2)
    f1 = font(int(h * 0.07))
    f2 = font(int(h * 0.045))
    f3 = font(int(h * 0.035))
    # central placeholder mark
    d.text((w // 2, int(h * 0.42)), "[ 이미지 자리 ]", fill=SLATE, anchor="mm", font=f3)
    d.text((w // 2, int(h * 0.55)), label, fill=NAVY, anchor="mm", font=f1)
    if sublabel:
        d.text((w // 2, int(h * 0.70)), sublabel, fill=SLATE, anchor="mm", font=f2)
    img.save(path, quality=92)
    print(f"  wrote {path.relative_to(ROOT)}  ({path.stat().st_size // 1024} KB)")

# Blood draw — bruise photo placeholder (warmer reddish hue to hint at content)
placeholder(
    OUT / "blood-draw-bruise.jpg",
    900, 700, (252, 235, 232),
    "채혈 후 멍 사진",
    "지혈 부족으로 생긴 멍 — 사진 교체 필요",
)

# Blood draw — pressure pose
placeholder(
    OUT / "blood-draw-pressure.png",
    900, 700, WARM,
    "올바른 압박 자세",
    "팔 펴고 손가락으로 5분 누르기 — 일러스트 교체 필요",
)

# Urine — cup holding
placeholder(
    OUT / "urine-cup-position.png",
    900, 700, WARM,
    "컵에 받는 자세",
    "컵 안쪽 닿지 않게 — 일러스트 교체 필요",
)

# Urine — shelf position
placeholder(
    OUT / "urine-shelf-spot.png",
    900, 700, WARM,
    "검체 두는 자리",
    "표시된 선반 위 — 실제 검사실 사진 교체 필요",
)

print("Placeholders written.")
