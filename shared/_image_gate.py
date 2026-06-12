"""ImageIntent 메타 검증기 + aboutness 채택 게이트 (handouts v2 — PRD/handout-visual-v2).

역할 (결정론 파트만):
  이미지 슬롯마다 에이전트가 작성하는 `.intent.json` 사이드카가
  (1) 스키마를 충족하는지 (explains / visual_type / must_show / prompt_en 필수)
  (2) 채택 불변식 I1 을 만족하는지
      — AdoptedImage 는 `depicts_intent==true AND aboutness>=T_ABOUT AND quality_ok` 일 때만 존재,
        아니면 `skipped_reason` 필수 (02_DATA_MODEL.md §불변식)
  를 검증한다. **aboutness 점수 산출 자체는 VLM(에이전트가 Read 도구로 이미지를 직접 보고 판정)이
  수행하고, 그 결과를 candidates[].verdict 에 기록한다 — 이 모듈은 기록의 정합성만 게이트한다.**

사이드카 위치/이름: 채택 이미지와 같은 폴더, 같은 베이스네임
  `shared/assets/generated/{topic-slug}-{slot-key}-YYYYMMDD.intent.json`
  (기존 `.prompt.md` 사이드카와 나란히. 슬롯이 '명시적 생략'으로 끝나도 intent.json 은 남긴다.)

스키마 (02_DATA_MODEL.md ImageIntent/ImageCandidate/AboutnessVerdict/AdoptedImage):
{
  "slot_id": ".ai-visual-1",            # HTML 슬롯 식별자
  "slot_mm": [182, 50],                  # 실측 [폭, 높이] (mm; deck 은 px 허용)
  "explains": "이 이미지가 설명할 본문 문장/표/체크리스트 1개 (자유서술, 필수)",
  "visual_type": "Process",              # VISUAL_TYPES 중 하나 — 그 외면 슬롯 자체가 무효
  "must_show": ["장정결제 복용", "..."],  # 이미지에 반드시 보여야 할 요소 (≥1)
  "prompt_en": "...",                    # 슬롯 비율 명시한 영문 프롬프트
  "candidates": [
    {"file": "....jpg", "gen_path": "codex_imagen",   # codex_imagen|$imagegen|fallback
     "verdict": {"depicts_intent": true, "aboutness": 88, "quality": 90,
                  "korean_text_in_image": false, "reasons": ["..."]}}
  ],
  "adopted": "....jpg" | null,           # 채택 1장 (candidates[].file 중 하나) 또는 null
  "skipped_reason": null | "적합 visual_type 없음 / aboutness<T_about / 생성 실패 ..."
}

Usage:
    python3 -m shared._image_gate <intent.json> [<intent.json> ...]
    python3 -m shared._image_gate <html_path>      # HTML 이 참조하는 generated 이미지의 intent 일괄 검증
    python3 -m shared._image_gate --t-about 70 ...

Returns exit 0 if all gates pass, 1 otherwise (CI/빌드 게이트용).

롤아웃: 환경변수 HANDOUT_V2_GATES=0 이면 경고만 출력하고 exit 0 (단계적 롤아웃,
기본은 ON). decks / lab-reports 확장은 P5 — 현재는 handouts 에서만 의무.

하위호환 (grandfathering): 이 게이트는 **2026-06-12 이후 새로 만들거나 수정한
이미지 슬롯**에 적용한다. 레거시 핸드아웃의 기존 이미지(intent.json 없는 자산)는
그 자료를 손대지 않는 한 검사 대상이 아니다 — HTML 전체를 넘기면 레거시 자산도
"사이드카 없음"으로 잡히므로, 레거시 자료 재작업이 아니면 신규 intent.json 경로를
직접 넘겨 검사한다. 전 자산 백필은 캘리브레이션 단계 과제 (TODO).
"""
from __future__ import annotations

import json
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
GENERATED_DIR = ROOT / "shared" / "assets" / "generated"

# ── 게이트 임계 (초기값 — 캘리브레이션 대상, 04_PROJECT_SPEC §6) ──────────────
T_ABOUT = 70          # aboutness 0~100, 이 미만이면 채택 금지 (사람 스팟체크로 조정)
T_QUALITY = 60        # quality 0~100 하한 (왜곡·저해상도 게이트, 캘리브레이션 대상)

VISUAL_TYPES = {"Anatomy", "Mechanism", "Process", "Equipment", "Action", "Comparison"}
GEN_PATHS = {"codex_imagen", "$imagegen", "fallback"}


def _typename(x) -> str:
    """오류 메시지용 타입 표기 (예: dict, list, int)."""
    return type(x).__name__


def validate_intent(d, path: str = "") -> list[str]:
    """ImageIntent 스키마 검증. 위반 메시지 리스트 반환 (빈 리스트 = 통과).

    방어적 타입검증: 에이전트가 쓴 intent.json 이 스키마를 어겨도 (필드가
    dict/list/숫자 등 엉뚱한 타입이어도) 트레이스백 없이 메시지로 graceful fail.
    """
    tag = f"[{path}] " if path else ""
    if not isinstance(d, dict):
        return [f"{tag}스키마 오류: intent.json 루트가 object 가 아님 ({_typename(d)}) — ImageIntent dict 필수"]
    errs: list[str] = []
    if not (isinstance(d.get("explains"), str) and d["explains"].strip()):
        errs.append(f"{tag}explains 누락 — 이 이미지가 설명할 본문 1개를 반드시 명시")
    vt = d.get("visual_type")
    if not isinstance(vt, str) or vt not in VISUAL_TYPES:
        errs.append(f"{tag}visual_type {vt!r} 무효 — {sorted(VISUAL_TYPES)} 중 하나(str)여야 함 "
                    "(적합 타입이 없으면 슬롯을 만들지 말 것)")
    ms = d.get("must_show")
    if not (isinstance(ms, list) and len(ms) >= 1 and all(isinstance(x, str) and x.strip() for x in ms)):
        errs.append(f"{tag}must_show 는 1개 이상의 비어있지 않은 문자열 리스트여야 함 "
                    f"(현재: {_typename(ms)})")
    if not (isinstance(d.get("prompt_en"), str) and d["prompt_en"].strip()):
        errs.append(f"{tag}prompt_en 누락 — 슬롯 실측 비율을 명시한 영문 프롬프트 필수")
    return errs


def validate_adoption(d, t_about: int = T_ABOUT, path: str = "") -> list[str]:
    """채택 불변식 I1 + quality 게이트 검증.

    방어적 타입검증: adopted 는 str|null, candidates 는 list[dict],
    candidates[].file 은 str, verdict 는 dict — 어기면 스키마 오류 메시지로
    graceful fail (절대 raw 예외로 죽지 않음).
    """
    tag = f"[{path}] " if path else ""
    if not isinstance(d, dict):
        return [f"{tag}스키마 오류: intent.json 루트가 object 가 아님 ({_typename(d)}) — ImageIntent dict 필수"]
    errs: list[str] = []
    adopted = d.get("adopted")

    raw_candidates = d.get("candidates", [])
    if not isinstance(raw_candidates, list):
        errs.append(f"{tag}스키마 오류: candidates 는 list[dict] 여야 함 (현재: {_typename(raw_candidates)})")
        raw_candidates = []
    candidates: dict = {}
    for i, c in enumerate(raw_candidates):
        if not isinstance(c, dict):
            errs.append(f"{tag}스키마 오류: candidates[{i}] 가 object 가 아님 ({_typename(c)}) — ImageCandidate dict 필수")
            continue
        fname = c.get("file")
        if not (isinstance(fname, str) and fname.strip()):
            errs.append(f"{tag}스키마 오류: candidates[{i}].file 은 비어있지 않은 str 이어야 함 (현재: {fname!r})")
            continue
        candidates[fname] = c

    for fname, c in candidates.items():
        gp = c.get("gen_path")
        if not isinstance(gp, str) or gp not in GEN_PATHS:
            errs.append(f"{tag}candidate '{fname}' gen_path {gp!r} 무효 ({sorted(GEN_PATHS)})")
        v = c.get("verdict")
        if v is not None and not isinstance(v, dict):
            errs.append(f"{tag}스키마 오류: candidate '{fname}' verdict 는 object 여야 함 (현재: {_typename(v)})")
            v = {}
        v = v or {}
        if not isinstance(v.get("aboutness"), (int, float)) or isinstance(v.get("aboutness"), bool):
            errs.append(f"{tag}candidate '{fname}' verdict.aboutness(0~100) 누락 — VLM 교차검증 미수행")

    if adopted is None:
        sr = d.get("skipped_reason")
        if not (isinstance(sr, str) and sr.strip()):
            errs.append(f"{tag}adopted=null 인데 skipped_reason 누락 — 생략 시 사유 필수"
                        + (f" (현재 타입: {_typename(sr)})" if sr is not None else ""))
        return errs

    if not isinstance(adopted, str):
        errs.append(f"{tag}스키마 오류: adopted 는 candidates[].file 의 str 또는 null 이어야 함 "
                    f"(현재: {_typename(adopted)}) — 02_DATA_MODEL.md AdoptedImage 참조")
        return errs

    c = candidates.get(adopted)
    if c is None:
        errs.append(f"{tag}adopted '{adopted}' 가 candidates 에 없음")
        return errs
    v = c.get("verdict")
    v = v if isinstance(v, dict) else {}
    if v.get("depicts_intent") is not True:
        errs.append(f"{tag}I1 위반: adopted '{adopted}' depicts_intent != true")
    ab = v.get("aboutness")
    if not (isinstance(ab, (int, float)) and not isinstance(ab, bool) and ab >= t_about):
        errs.append(f"{tag}I1 위반: adopted '{adopted}' aboutness {ab!r} < T_about {t_about}")
    q = v.get("quality")
    if not (isinstance(q, (int, float)) and not isinstance(q, bool) and q >= T_QUALITY):
        errs.append(f"{tag}quality 게이트: adopted '{adopted}' quality {q!r} < {T_QUALITY}")
    if v.get("korean_text_in_image") is not False:
        errs.append(f"{tag}quality 게이트: adopted '{adopted}' korean_text_in_image 가 false 로 확인되지 않음 "
                    "(이미지 내 한글 텍스트 금지 — SKILL.md Gotcha 14)")
    try:
        missing = not (GENERATED_DIR / adopted).exists() and not Path(adopted).exists()
    except (OSError, ValueError):  # null byte 등 경로로 쓸 수 없는 문자열
        missing = True
    if missing:
        errs.append(f"{tag}adopted 파일이 shared/assets/generated/ 에 없음: {adopted}")
    return errs


def intents_for_html(html_path: Path) -> list[Path]:
    """HTML 이 참조하는 generated 이미지들의 .intent.json 사이드카 경로를 수집."""
    html = html_path.read_text(encoding="utf-8")
    out: list[Path] = []
    for m in re.finditer(r"assets/generated/([\w.\-]+\.(?:png|webp|jpe?g))", html):
        sidecar = GENERATED_DIR / (Path(m.group(1)).stem + ".intent.json")
        if sidecar not in out:
            out.append(sidecar)
    return out


def run_gate(paths: list[Path], t_about: int = T_ABOUT) -> int:
    all_errs: list[str] = []
    checked = 0
    for p in paths:
        if not p.exists():
            all_errs.append(f"[{p.name}] intent.json 사이드카 없음 — ImageIntent 의무화 위반 (handouts v2)")
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            all_errs.append(f"[{p.name}] JSON 파싱 실패: {e}")
            continue
        checked += 1
        try:
            if not isinstance(d, dict):
                # 루트 타입 오류는 한 번만 보고 (두 검증기 모두 같은 메시지를 내므로)
                all_errs += validate_intent(d, p.name)
                continue
            all_errs += validate_intent(d, p.name)
            all_errs += validate_adoption(d, t_about, p.name)
        except Exception as e:  # 최후 안전망 — malformed 입력에 절대 트레이스백으로 죽지 않음
            all_errs.append(f"[{p.name}] 스키마 오류: intent 검증 중 내부 오류 ({_typename(e)}: {e}) "
                            "— 02_DATA_MODEL.md ImageIntent 스키마 확인")
    if all_errs:
        print(f"❌ image gate FAIL — {len(all_errs)} issue(s) / {checked} intent(s):")
        for e in all_errs:
            print(f"  • {e}")
        if os.environ.get("HANDOUT_V2_GATES", "1") == "0":
            print("⚠️ HANDOUT_V2_GATES=0 — 게이트 비활성(관찰 모드), exit 0")
            return 0
        return 1
    print(f"✓ image gate OK — {checked} intent(s), T_about={t_about}")
    return 0


def main(argv: list[str]) -> int:
    t_about = T_ABOUT
    args = []
    it = iter(argv)
    for a in it:
        if a == "--t-about":
            try:
                t_about = int(next(it))
            except (StopIteration, ValueError):
                print("❌ --t-about 뒤에 정수 임계값이 필요함 (예: --t-about 70)")
                return 2
        else:
            args.append(a)
    if not args:
        print(__doc__)
        return 2
    paths: list[Path] = []
    for a in args:
        p = Path(a)
        if p.suffix == ".html":
            if not p.exists():
                print(f"❌ HTML 파일 없음: {p}")
                return 2
            paths += intents_for_html(p)
        else:
            paths.append(p)
    return run_gate(paths, t_about)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
