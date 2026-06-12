"""handouts v2 게이트 회귀 evals — 04_PROJECT_SPEC §7 (aboutness / visual-diff / tone).

LLM 파이프라인 비교(eval_runner.py)와 달리 **완전 결정론** 회귀 테스트:
게이트 모듈(shared/_image_gate, _visual_diff, _tone_score)이 "잡아야 할 것을
계속 잡는지"를 fixture 로 고정한다. CI/수동 어느 쪽에서든 그대로 실행 가능.

케이스:
  ① aboutness — 의도와 무관한 이미지(aboutness<T_about)를 채택한 intent 가
     image gate 에서 FAIL 하는지 + malformed intent(adopted=dict 등)가
     트레이스백 없이 스키마 오류로 graceful FAIL 하는지 (2026-06-12 결함 회귀 가드).
  ② visual-diff — 일부러 깨진 레이아웃(슬롯 밖 픽셀 변화·페이지 높이 변화)이
     compare() 에서 regressed=True 로 차단되는지 / 정상 삽입(슬롯 안 변화만)은
     무회귀로 통과하는지.
  ③ tone — 브랜드 외 색(레드/그린 계열) 이미지가 ToneScore palette 점수에서
     감점되어 T_tone 미달로 떨어지는지 / 브랜드 팔레트 이미지는 통과하는지.

Usage:
    python3 evals/gates/run_gate_evals.py        # 전체 실행, 전부 통과 시 exit 0

fixture 는 실행 시 tempdir 에 생성·정리한다 (③ 의 generated 이미지는
shared/assets/generated/ 에 `eval-gate-` 접두사로 잠깐 만들었다 지움 —
score() 가 그 폴더만 보기 때문. 실패해도 finally 로 반드시 정리).
실환자 데이터 없음 (evals/README.md 절대 룰 준수).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
GENERATED_DIR = ROOT / "shared" / "assets" / "generated"

PASS, FAIL = "✓", "❌"
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"  {PASS if ok else FAIL} {name}" + (f" — {detail}" if detail else ""))


def run_image_gate(intent_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "shared._image_gate", str(intent_path)],
        capture_output=True, text=True, cwd=str(ROOT),
    )


# ─────────────────────────────────────────────────────────────────────────────
# ① aboutness — 탈락 intent 가 게이트 FAIL + malformed graceful
# ─────────────────────────────────────────────────────────────────────────────

def eval_aboutness(tmp: Path) -> None:
    print("① aboutness 게이트 (image gate)")

    # 1) aboutness 55 < T_about 70 인데 채택 → I1 위반으로 FAIL 해야 함
    low = {
        "slot_id": ".ai-visual-1",
        "slot_mm": [182, 50],
        "explains": "장정결제 복용 순서 (합성 fixture — 실환자 아님)",
        "visual_type": "Process",
        "must_show": ["장정결제 복용 시간"],
        "prompt_en": "wide 16:5 process diagram, navy/steel palette",
        "candidates": [{
            "file": "eval-gate-unrelated.png", "gen_path": "codex_imagen",
            "verdict": {"depicts_intent": False, "aboutness": 55, "quality": 85,
                        "korean_text_in_image": False,
                        "reasons": ["의도(장정결)와 무관한 일반 병원 풍경"]},
        }],
        "adopted": "eval-gate-unrelated.png",
        "skipped_reason": None,
    }
    p = tmp / "low-aboutness.intent.json"
    p.write_text(json.dumps(low, ensure_ascii=False), encoding="utf-8")
    r = run_image_gate(p)
    check("aboutness<T_about 채택 intent → gate FAIL (exit 1)",
          r.returncode == 1 and "I1 위반" in r.stdout,
          f"exit={r.returncode}")

    # 2) 같은 후보를 정직하게 생략(adopted=null+사유) → 통과해야 함
    ok = dict(low, adopted=None, skipped_reason="aboutness 55 < T_about — 적합 이미지 생성 실패, 슬롯 생략")
    p2 = tmp / "skipped-ok.intent.json"
    p2.write_text(json.dumps(ok, ensure_ascii=False), encoding="utf-8")
    r2 = run_image_gate(p2)
    check("동일 후보를 생략+사유 기록 → gate OK (exit 0)", r2.returncode == 0, f"exit={r2.returncode}")

    # 3) malformed (adopted 가 dict) → 트레이스백 없이 스키마 오류로 FAIL (결함 회귀 가드)
    bad = dict(low, adopted={"file": "eval-gate-unrelated.png"})
    p3 = tmp / "malformed-adopted.intent.json"
    p3.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    r3 = run_image_gate(p3)
    check("malformed adopted(dict) → graceful 스키마 오류 (no traceback)",
          r3.returncode == 1 and "스키마 오류" in r3.stdout and "Traceback" not in r3.stderr,
          f"exit={r3.returncode}")


# ─────────────────────────────────────────────────────────────────────────────
# ② visual-diff — 깨진 레이아웃 차단
# ─────────────────────────────────────────────────────────────────────────────

def eval_visual_diff(tmp: Path) -> None:
    print("② visual-diff 회귀 가드 (compare)")
    from PIL import Image, ImageDraw

    from shared._visual_diff import compare

    W, H = 794, 1123                       # A4 viewport
    SLOT = (100, 300, 594, 200)            # x, y, w, h

    before = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(before)
    for y in range(80, 280, 30):           # 본문 텍스트 블록 흉내
        d.rectangle([60, y, 730, y + 14], fill=(30, 41, 59))
    d.rectangle([60, 1060, 730, 1090], fill=(0, 51, 102))  # footer
    bp = tmp / "before.png"
    before.save(bp)

    # 정상 삽입: 슬롯 안에만 이미지 → 무회귀여야 함
    good = before.copy()
    ImageDraw.Draw(good).rectangle(
        [SLOT[0], SLOT[1], SLOT[0] + SLOT[2], SLOT[1] + SLOT[3]], fill=(91, 155, 213))
    gp = tmp / "after-good.png"
    good.save(gp)
    r = compare(bp, gp, [SLOT])
    check("정상 삽입(슬롯 안 변화만) → regressed=False",
          r["regressed"] is False, f"diff_ratio={r['diff_ratio']}")

    # 깨진 레이아웃: 슬롯 밖(본문/footer 영역) 픽셀 변화 → 회귀로 차단해야 함
    broken = good.copy()
    db = ImageDraw.Draw(broken)
    for y in range(700, 1000, 30):         # 본문 밀림 흉내 — 슬롯 밖 새 블록
        db.rectangle([60, y, 730, y + 14], fill=(30, 41, 59))
    kp = tmp / "after-broken.png"
    broken.save(kp)
    r2 = compare(bp, kp, [SLOT])
    check("슬롯 밖 변화(본문 밀림) → regressed=True",
          r2["regressed"] is True, f"diff_ratio={r2['diff_ratio']}")

    # 페이지 높이 변화(오버플로) → 즉시 회귀
    taller = Image.new("RGB", (W, H + 200), (255, 255, 255))
    taller.paste(good, (0, 0))
    tp = tmp / "after-taller.png"
    taller.save(tp)
    r3 = compare(bp, tp, [SLOT])
    check("스냅샷 높이 변화(오버플로 의심) → regressed=True",
          r3["regressed"] is True and r3["size_changed"] is True, r3["note"])


# ─────────────────────────────────────────────────────────────────────────────
# ③ tone — 브랜드 외 색 감점
# ─────────────────────────────────────────────────────────────────────────────

def eval_tone(tmp: Path) -> None:
    print("③ ToneScore 브랜드 톤 게이트")
    from PIL import Image

    from shared._tone_score import T_TONE, score

    on_brand = GENERATED_DIR / "eval-gate-onbrand.png"
    off_brand = GENERATED_DIR / "eval-gate-offbrand.png"
    try:
        # 브랜드 팔레트(네이비/스틸/화이트) 이미지
        img = Image.new("RGB", (300, 200), (255, 255, 255))
        img.paste(Image.new("RGB", (150, 200), (0, 51, 102)), (0, 0))      # navy
        img.paste(Image.new("RGB", (75, 200), (91, 155, 213)), (150, 0))   # steel
        img.save(on_brand)
        # 브랜드 외 색 (선명한 레드/그린/옐로) 이미지
        img2 = Image.new("RGB", (300, 200), (220, 30, 30))
        img2.paste(Image.new("RGB", (150, 200), (30, 200, 60)), (0, 0))
        img2.paste(Image.new("RGB", (75, 200), (250, 220, 40)), (150, 0))
        img2.save(off_brand)

        html_tpl = (
            "<!doctype html><html><head><style>"
            "body{{font-family:'Pretendard Variable',Pretendard,sans-serif}}"
            "</style></head><body><div class='page'>"
            "<img src='assets/generated/{name}' alt='합성 eval fixture'>"
            "</div></body></html>"
        )
        hp_on = tmp / "onbrand.html"
        hp_on.write_text(html_tpl.format(name=on_brand.name), encoding="utf-8")
        hp_off = tmp / "offbrand.html"
        hp_off.write_text(html_tpl.format(name=off_brand.name), encoding="utf-8")

        s_on = score(hp_on)
        check(f"브랜드 팔레트 이미지 → ToneScore {s_on['score']} ≥ T_tone {T_TONE}",
              s_on["score"] >= T_TONE, f"palette_dist={s_on['palette_dist']}")
        s_off = score(hp_off)
        check(f"브랜드 외 색 이미지 → ToneScore {s_off['score']} < T_tone {T_TONE} (감점)",
              s_off["score"] < T_TONE, f"palette_dist={s_off['palette_dist']}")
        check("감점이 palette 축에서 발생 (palette_dist 차이 유의)",
              s_off["palette_dist"] > s_on["palette_dist"] + 40,
              f"{s_on['palette_dist']} → {s_off['palette_dist']}")
    finally:
        for f in (on_brand, off_brand):
            try:
                f.unlink()
            except OSError:
                pass


# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    print("handouts v2 게이트 회귀 evals (04_PROJECT_SPEC §7)\n")
    with tempfile.TemporaryDirectory(prefix="gate-evals-") as td:
        tmp = Path(td)
        eval_aboutness(tmp)
        eval_visual_diff(tmp)
        eval_tone(tmp)
    failed = [n for n, ok, _ in results if not ok]
    print()
    if failed:
        print(f"{FAIL} gate evals FAIL — {len(failed)}/{len(results)}: {failed}")
        return 1
    print(f"{PASS} gate evals OK — {len(results)}/{len(results)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
