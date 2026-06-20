"""Unified build script for clinic-content-system.

Builds three content types in a single run:
  - decks/        → 16:9 multi-slide patient education decks (1280x720 closing slide QR)
  - handouts/     → A4 portrait single-page clinic handouts (footer mini-QR)
  - lab-reports/  → A4 portrait single-page lab result infographics (footer mini-QR)

All targets share:
  - Common design tokens (shared/design-tokens.css)
  - Brand QR generation (Python qrcode SVG, navy #003366, inline-injected)
  - OG meta head registration (validated during build)
  - Notion DB sync (when NOTION_TOKEN env is set)

Output goes to output/{type}/{slug}.{pdf,png}
"""
from datetime import date
from pathlib import Path
import os
import re
import sys

# Windows consoles default to cp949/cp1252 and raise UnicodeEncodeError when
# printing ✓ ✗ ⚠️ status glyphs. Force UTF-8 so Mac and Windows runs print
# identically (SKILL.md rule #1: cross-machine consistency).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT / "shared"))
from _build_helpers import (  # noqa: E402
    make_qr_svg,
    inject_qr,
    inject_qr_url_text,
    qr_mini_url_text,
    short_qr_url_text,
    inject_noindex_meta,
    render,
    check_og_meta,
    strip_qr_mini_block,
    load_asset_manifest,
    resolve_data_asset,
    collect_data_asset_keys,
)
from _validate_layout import (  # noqa: E402
    HANDOUT_VALIDATOR_JS,
    DECK_VALIDATOR_JS,
    CONTRAST_ADVISORY_JS,
    GRANDFATHERED_INTERNAL_GAP,
)

NOTION_ENABLED = bool(os.environ.get("NOTION_TOKEN"))
if NOTION_ENABLED:
    from _notion_sync import upsert as notion_upsert  # noqa: E402
    from _notion_sync import content_last_modified_iso  # noqa: E402

OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
for sub in ("decks", "handouts", "lab-reports"):
    (OUT / sub).mkdir(exist_ok=True)

# Hosting base URL — change once here when GitHub Pages URL is finalized
BASE_URL = "https://gwanggyo-barun.github.io/patient-education"
ACTIVE_STATUS = "✅ 사용중"
ARCHIVED_STATUS = "⏸️ 보류"
VALID_NOTION_STATUSES = {
    ACTIVE_STATUS,
    "🔄 수정중",
    "📝 초안",
    ARCHIVED_STATUS,
}


# Each target dict carries everything needed to build + sync to Notion.
# Required: kind, slug, slug_path, html_path, qr_class, fmt
# Notion (optional but recommended): title, category, audience, disease, status
TARGETS = [
    # === 16:9 multi-slide decks ===
    {
        "kind": "decks", "slug": "roma-ovarian-risk",
        "slug_path": "decks/gyn/roma-ovarian-risk/",
        "html_path": ROOT / "decks/gyn/roma-ovarian-risk/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "ROMA 난소암 위험도 평가 검사",
        "category": "🌸 부인과", "audience": "환자/보호자", "disease": "난소암 위험도 평가 (ROMA)",
    },
    {
        "kind": "decks", "slug": "gerd",
        "slug_path": "decks/gi/gerd/lifestyle/",
        "html_path": ROOT / "decks/gi/gerd/lifestyle/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "역류성 식도염 생활관리",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "GERD (역류성 식도염)",
    },
    {
        "kind": "decks", "slug": "refractory-dyspepsia",
        "slug_path": "decks/gi/refractory-dyspepsia/",
        "html_path": ROOT / "decks/gi/refractory-dyspepsia/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "내시경 정상인데 끊으면 재발하는 쓰림 — 기능성·과민성 소화불량의 이해와 관리",
        "category": "🫁 위장관", "audience": "환자/보호자",
        "disease": "기능성 소화불량 · 역류 과민성 · 기능성 가슴쓰림 (DGBI / 난치성)",
    },
    {
        "kind": "decks", "slug": "hpylori",
        "slug_path": "decks/gi/h-pylori/eradication/",
        "html_path": ROOT / "decks/gi/h-pylori/eradication/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "헬리코박터 제균 치료 안내",
        "category": "🫁 위장관", "audience": "환자/보호자",
        "disease": "H. pylori 제균치료 / 약 복용법 / 부작용 / 제균 확인",
        "note": "구분: 제균 치료 전용. 감염 의미·내시경 소견·진단 개요는 별도 '진료설명 — 헬리코박터 파일로리 개요·진단 안내' 사용.",
    },
    {
        "kind": "decks", "slug": "masld-fatty-liver",
        "slug_path": "decks/gi/masld-fatty-liver/",
        "html_path": ROOT / "decks/gi/masld-fatty-liver/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "MASLD(대사이상 지방간) 환자 교육",
        "category": "🫁 위장관", "audience": "환자/보호자",
        "disease": "MASLD (대사이상 관련 지방간) · 대사·심장 위험 · 섬유화 단계 · FIB-4/간 탄성초음파",
    },
    {
        "kind": "decks", "slug": "morning-htn",
        "slug_path": "decks/cardio/htn/morning/",
        "html_path": ROOT / "decks/cardio/htn/morning/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "아침 고혈압 환자 교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "고혈압 (HTN)",
    },
    {
        "kind": "decks", "slug": "htn-2025-aha-acc",
        "slug_path": "decks/cardio/htn-2025-aha-acc/",
        "html_path": ROOT / "decks/cardio/htn-2025-aha-acc/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "2025 AHA/ACC 고혈압 가이드라인 — 목표 <130/80",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "고혈압 (HTN) · 2025 AHA/ACC Guideline",
    },
    {
        "kind": "decks", "slug": "oh-management-2026",
        "slug_path": "decks/cardio/orthostatic-hypotension/management-2026/",
        "html_path": ROOT / "decks/cardio/orthostatic-hypotension/management-2026/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "기립성 저혈압 관리 — JAMA 2026 리뷰",
        "category": "🩺 일반내과", "audience": "의료진", "disease": "기립성 저혈압",
    },
    {
        "kind": "decks", "slug": "endoscopy-cpr-training",
        "slug_path": "decks/emergency/endoscopy/cpr-training/",
        "html_path": ROOT / "decks/emergency/endoscopy/cpr-training/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "내시경실 심정지 응급 대응 직원 교육",
        "category": "🩺 일반내과", "audience": "의료진", "disease": "응급처치 (CPR)",
    },


    # === 2026-05-24 Top 5 논문 ===
    {
        "kind": "decks", "slug": "baxdrostat-baxhtn",
        "slug_path": "decks/general/papers-20260524/baxdrostat-baxhtn/",
        "html_path": ROOT / "decks/general/papers-20260524/baxdrostat-baxhtn/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "Baxdrostat — 알도스테론 합성효소 억제제 FDA 승인 (BaxHTN)",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "저항성 고혈압",
    },
    {
        "kind": "decks", "slug": "tramadol-bmj",
        "slug_path": "decks/general/papers-20260524/tramadol-bmj/",
        "html_path": ROOT / "decks/general/papers-20260524/tramadol-bmj/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "트라마돌 — 만성 통증 효과 미미·심혈관 위험 증가 (BMJ 메타분석)",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "만성 통증",
    },
    {
        "kind": "decks", "slug": "sglt2-glp1-combo",
        "slug_path": "decks/general/papers-20260524/sglt2-glp1-combo/",
        "html_path": ROOT / "decks/general/papers-20260524/sglt2-glp1-combo/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "SGLT-2i + GLP-1RA 병용 — 심혈관·신장 30% 개선",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "제2형 당뇨 (T2DM)",
    },
    {
        "kind": "decks", "slug": "teen-height-growth",
        "slug_path": "decks/general/teen-height-growth/",
        "html_path": ROOT / "decks/general/teen-height-growth/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "중1 남학생 키 성장 영양제 가이드 — 비타민D·칼슘·아연·HT042 + 수면·운동",
        "category": "🌿 생활습관·식이", "audience": "환자/보호자", "disease": "청소년 성장 (사춘기 성장급등)",
        "status": ARCHIVED_STATUS,
    },
    {
        "kind": "decks", "slug": "soy-legumes-htn",
        "slug_path": "decks/general/papers-20260524/soy-legumes-htn/",
        "html_path": ROOT / "decks/general/papers-20260524/soy-legumes-htn/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "콩·두류 섭취와 고혈압 — 최적 섭취량 정량화 (BMJ Nutrition)",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "고혈압 예방 식이",
    },
    {
        "kind": "decks", "slug": "rsv-realworld",
        "slug_path": "decks/general/papers-20260524/rsv-realworld/",
        "html_path": ROOT / "decks/general/papers-20260524/rsv-realworld/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "RSV 백신 — 실사용 근거 기반 가이드 (JAMA Internal Med)",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "RSV 백신",
    },


    # === 2026-05-25 Top 5 — 3번 & 5번 (병렬 에이전트 작성) ===
    {
        "kind": "decks", "slug": "once-weekly-insulin",
        "slug_path": "decks/general/papers-20260525/once-weekly-insulin/",
        "html_path": ROOT / "decks/general/papers-20260525/once-weekly-insulin/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "주1회 기저인슐린 (Efsitora·Icodec) 메타분석",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "제2형 당뇨 인슐린 요법",
    },
    {
        "kind": "decks", "slug": "cpap-personalized-cv",
        "slug_path": "decks/general/papers-20260525/cpap-personalized-cv/",
        "html_path": ROOT / "decks/general/papers-20260525/cpap-personalized-cv/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "CPAP 개인 맞춤 심혈관 효과 — Mount Sinai AI (SAVE 재분석)",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "수면무호흡 (OSA) · CPAP",
    },
    {
        "kind": "decks", "slug": "lp-a-cardiovascular-risk",
        "slug_path": "decks/general/papers-20260525/lp-a-cardiovascular-risk/",
        "html_path": ROOT / "decks/general/papers-20260525/lp-a-cardiovascular-risk/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "Lp(a)와 심혈관 위험 — 보편적 1회 선별 (2026 ACC/AHA 가이드라인)",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "Lp(a) · 이상지질혈증 · 심혈관 위험 보편 선별",
    },
    {
        "kind": "decks", "slug": "surmount5-tirzepatide-vs-semaglutide",
        "slug_path": "decks/general/papers-20260525/surmount5-tirzepatide-vs-semaglutide/",
        "html_path": ROOT / "decks/general/papers-20260525/surmount5-tirzepatide-vs-semaglutide/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "SURMOUNT-5 — 터제파타이드 vs 세마글루타이드 비만 직접 비교",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "비만 약물치료 · Tirzepatide · Semaglutide · 직접 비교 RCT",
    },
    {
        "kind": "decks", "slug": "vutrisiran-attr-cm-helios-b",
        "slug_path": "decks/general/papers-20260525/vutrisiran-attr-cm-helios-b/",
        "html_path": ROOT / "decks/general/papers-20260525/vutrisiran-attr-cm-helios-b/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "Vutrisiran ATTR-CM — HELIOS-B 3상",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "트랜스티레틴 아밀로이드 심근병증(ATTR-CM) · Vutrisiran · RNAi",
    },
    {
        "kind": "decks", "slug": "bepirovirsen-hbv-phase3",
        "slug_path": "decks/general/papers-20260528/bepirovirsen-hbv-phase3/",
        "html_path": ROOT / "decks/general/papers-20260528/bepirovirsen-hbv-phase3/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "베피로비르센 3상 — 만성 B형간염 기능적 완치",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "만성 B형간염 (CHB)",
    },
    {
        "kind": "decks", "slug": "acs-crc-screening-blood-test-2026",
        "slug_path": "decks/general/papers-20260530/acs-crc-screening-blood-test-2026/",
        "html_path": ROOT / "decks/general/papers-20260530/acs-crc-screening-blood-test-2026/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "ACS 2026 대장암 검진 가이드라인 — 혈액검사 신규 추가",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "대장암 검진 · 혈액 기반 cfDNA 검사",
    },
    {
        "kind": "decks", "slug": "finerenone-t1d-ckd-fine-one",
        "slug_path": "decks/general/papers-20260530/finerenone-t1d-ckd-fine-one/",
        "html_path": ROOT / "decks/general/papers-20260530/finerenone-t1d-ckd-fine-one/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "Finerenone in Type 1 Diabetes and CKD — FINE-ONE",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "제1형 당뇨병 · 만성콩팥병 · 알부민뇨",
    },
    {
        "kind": "decks", "slug": "easo-obesity-pharmacotherapy-2026",
        "slug_path": "decks/general/papers-20260530/easo-obesity-pharmacotherapy-2026/",
        "html_path": ROOT / "decks/general/papers-20260530/easo-obesity-pharmacotherapy-2026/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "EASO 2026 비만 약물치료 알고리즘 업데이트",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "비만 · GLP-1RA · GIP/GLP-1RA",
    },
    {
        "kind": "decks", "slug": "calcium-vitamin-d-fracture-falls-bmj",
        "slug_path": "decks/general/papers-20260530/calcium-vitamin-d-fracture-falls-bmj/",
        "html_path": ROOT / "decks/general/papers-20260530/calcium-vitamin-d-fracture-falls-bmj/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "BMJ 2026 칼슘·비타민 D 보충제와 골절·낙상 예방",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "골절 예방 · 낙상 예방 · 칼슘 · 비타민 D",
    },
    {
        "kind": "decks", "slug": "t1d-glp1-cardiorenal",
        "slug_path": "decks/general/papers-20260530/t1d-glp1-cardiorenal/",
        "html_path": ROOT / "decks/general/papers-20260530/t1d-glp1-cardiorenal/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "제1형 당뇨병 GLP-1RA — 심혈관·신장 사건 감소 (Nature Medicine 2026)",
        "category": "📰 논문 리뷰", "audience": "의료진", "disease": "제1형 당뇨병 · GLP-1RA · 심혈관·신장 보호 · target trial emulation",
    },

    # === A4 portrait single-page handouts ===
    {
        "kind": "handouts", "slug": "cpr-flowchart",
        "slug_path": "handouts/emergency/cpr-flowchart/",
        "html_path": ROOT / "handouts/emergency/cpr-flowchart/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "내시경실 Code Blue 플로우차트",
        "category": "🩺 일반내과", "audience": "의료진", "disease": "응급처치 (CPR)",
    },
    {
        "kind": "handouts", "slug": "crash-cart-checklist",
        "slug_path": "handouts/emergency/crash-cart-checklist/",
        "html_path": ROOT / "handouts/emergency/crash-cart-checklist/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "응급카트 점검 체크리스트",
        "category": "🩺 일반내과", "audience": "의료진", "disease": "응급처치",
    },
    {
        "kind": "handouts", "slug": "crash-cart-map",
        "slug_path": "handouts/emergency/crash-cart-map/",
        "html_path": ROOT / "handouts/emergency/crash-cart-map/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "응급카트 약품·장비 위치 맵",
        "category": "🩺 일반내과", "audience": "의료진", "disease": "응급처치",
    },

    # === A4 portrait single-page lab reports ===
    {
        "kind": "lab-reports", "slug": "lipid-panel",
        "slug_path": "lab-reports/lipid-panel/sample/",
        "html_path": ROOT / "lab-reports/lipid-panel/sample/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "지질 패널 결과 안내",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "지질패널",
    },
    {
        "kind": "lab-reports", "slug": "842acd69b8",
        "slug_path": "lab-reports/diabetes-screening/842acd69b8/",
        "html_path": ROOT / "lab-reports/diabetes-screening/842acd69b8/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "patient_name": "박형주", "chart_no": "23512",
        "exam_date": "2026-05-06", "doctor": "정지환",
        "note": "공단검진 — 당뇨 신규진단",
    },
    {
        # 16:9 설명 슬라이드를 환자 검사결과로 등록 (fmt=deck-16x9). 원장 확정 2026-06-20.
        "kind": "lab-reports", "slug": "55572cefba",
        "slug_path": "lab-reports/parkinson-meds/55572cefba/",
        "html_path": ROOT / "lab-reports/parkinson-meds/55572cefba/index.html",
        "qr_class": "qr-mini__code", "fmt": "deck-16x9",
        "patient_name": "맹복순", "chart_no": "24446",
        "exam_date": "2026-06-19", "doctor": "정지환",
        "note": "어지럼·전신 부종 설명 — 약물 관련 가능성 + 기립성 저혈압 (검사상 심·신·간·갑상선 정상)",
    },

    # === Migration: 29 new decks ===

    {
        "kind": "decks", "slug": "appendicitis-diverticulitis",
        "slug_path": "decks/gi/appendicitis-diverticulitis/",
        "html_path": ROOT / "decks/gi/appendicitis-diverticulitis/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "맹장염 / 급성 게실염",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "급성충수염 (Acute Appendicitis), 급성 게실염 (Acute Diverticulitis)",
    },
    {
        "kind": "decks", "slug": "bowel-prep-low-volume",
        "slug_path": "decks/gi/bowel-prep-low-volume/",
        "html_path": ROOT / "decks/gi/bowel-prep-low-volume/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "저용량 장정결 (1L PEG-ascorbate) — 4L PEG와 동등 이상",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "대장내시경 장정결 · 1L PEG-ascorbate · Ann Intern Med 2026",
    },
    {
        "kind": "decks", "slug": "atrophic-gastritis",
        "slug_path": "decks/gi/atrophic-gastritis/",
        "html_path": ROOT / "decks/gi/atrophic-gastritis/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "위축성위염 / 장상피화생",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "위축성위염 (Atrophic Gastritis), 장상피화생 (Intestinal Metaplasia)",
    },
    {
        "kind": "decks", "slug": "hypothyroidism",
        "slug_path": "decks/endocrine/hypothyroidism/",
        "html_path": ROOT / "decks/endocrine/hypothyroidism/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "갑상선기능저하증 환자교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "갑상선기능저하증 (Hypothyroidism)",
    },
    {
        "kind": "decks", "slug": "hyperthyroidism",
        "slug_path": "decks/endocrine/hyperthyroidism/",
        "html_path": ROOT / "decks/endocrine/hyperthyroidism/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "갑상선 기능항진증",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "갑상선기능항진증 (Hyperthyroidism)",
    },
    {
        "kind": "decks", "slug": "prediabetes-remission",
        "slug_path": "decks/endocrine/prediabetes-remission/",
        "html_path": ROOT / "decks/endocrine/prediabetes-remission/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "전당뇨 관해 — 심혈관 위험 절반으로",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "전당뇨 (Prediabetes) · 심혈관 위험 감소 · Lancet 2026",
    },
    {
        "kind": "decks", "slug": "chest-pain",
        "slug_path": "decks/cardio/chest-pain/",
        "html_path": ROOT / "decks/cardio/chest-pain/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "흉통 환자교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "흉통 (Chest Pain)",
    },
    {
        "kind": "decks", "slug": "abyss-betablocker-mi",
        "slug_path": "decks/cardio/abyss-betablocker-mi/",
        "html_path": ROOT / "decks/cardio/abyss-betablocker-mi/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "심근경색 후 베타차단제, 계속 vs 중단 — ABYSS 연구",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "심근경색 후 베타차단제 (ABYSS Trial · NEJM 2024)",
    },
    {
        "kind": "decks", "slug": "ltbi-overview",
        "slug_path": "decks/infectious/ltbi-overview/",
        "html_path": ROOT / "decks/infectious/ltbi-overview/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "잠복결핵 교육자료",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "잠복결핵감염 (Latent Tuberculosis Infection)",
    },
    {
        "kind": "decks", "slug": "hpylori-overview",
        "slug_path": "decks/gi/hpylori-overview/",
        "html_path": ROOT / "decks/gi/hpylori-overview/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "진료설명 — 헬리코박터 파일로리 개요·진단 안내",
        "category": "🫁 위장관", "audience": "환자/보호자",
        "disease": "H. pylori 개요 / 감염 의미 / 내시경 소견 / 진단검사 / 치료 필요성",
        "note": "병합본: 기존 '진료설명 — 헬리코박터 파일로리'와 '헬리코박터 파일로리 개요·진단 안내'의 중복을 하나로 정리. 제균 약 복용법·부작용은 별도 '헬리코박터 제균 치료 안내' 사용.",
    },
    {
        "kind": "decks", "slug": "dyslipidemia",
        "slug_path": "decks/endocrine/dyslipidemia/",
        "html_path": ROOT / "decks/endocrine/dyslipidemia/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "진료설명 — 고지혈증",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "이상지질혈증 (Dyslipidemia)",
    },
    {
        "kind": "decks", "slug": "diabetes-mellitus-type2",
        "slug_path": "decks/endocrine/diabetes-mellitus-type2/",
        "html_path": ROOT / "decks/endocrine/diabetes-mellitus-type2/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "제2형 당뇨병 환자 교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "제2형 당뇨병 (Type 2 Diabetes Mellitus)",
    },
    {
        "kind": "decks", "slug": "diabetes-first-visit",
        "slug_path": "decks/endocrine/diabetes-first-visit/",
        "html_path": ROOT / "decks/endocrine/diabetes-first-visit/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "당뇨 첫 외래 안내",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "제2형 당뇨병 신환 오리엔테이션 (Type 2 Diabetes First Visit)",
    },
    {
        "kind": "decks", "slug": "glp1-week-01-start",
        "slug_path": "decks/endocrine/glp1-weight-management/week-01-start/",
        "html_path": ROOT / "decks/endocrine/glp1-weight-management/week-01-start/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "마운자로·위고비 1회차 — 치료 시작 전 이해",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "비만 약물치료 · GLP-1/GIP-GLP-1 생활관리",
    },
    {
        "kind": "decks", "slug": "glp1-week-02-aerobic",
        "slug_path": "decks/endocrine/glp1-weight-management/week-02-aerobic/",
        "html_path": ROOT / "decks/endocrine/glp1-weight-management/week-02-aerobic/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "마운자로·위고비 2회차 — 걷기와 활동량",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "비만 약물치료 · 유산소 운동",
    },
    {
        "kind": "decks", "slug": "glp1-week-03-strength",
        "slug_path": "decks/endocrine/glp1-weight-management/week-03-strength/",
        "html_path": ROOT / "decks/endocrine/glp1-weight-management/week-03-strength/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "마운자로·위고비 3회차 — 근육 보존",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "비만 약물치료 · 근력운동 · 근육 보존",
    },
    {
        "kind": "decks", "slug": "glp1-week-04-nutrition",
        "slug_path": "decks/endocrine/glp1-weight-management/week-04-nutrition/",
        "html_path": ROOT / "decks/endocrine/glp1-weight-management/week-04-nutrition/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "마운자로·위고비 4회차 — 식단 기본",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "비만 약물치료 · 식단 · 단백질",
    },
    {
        "kind": "decks", "slug": "glp1-week-05-gi-effects",
        "slug_path": "decks/endocrine/glp1-weight-management/week-05-gi-effects/",
        "html_path": ROOT / "decks/endocrine/glp1-weight-management/week-05-gi-effects/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "마운자로·위고비 5회차 — 위장관 부작용 줄이기",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "비만 약물치료 · 오심 · 변비 · 탈수",
    },
    {
        "kind": "decks", "slug": "glp1-week-06-injection",
        "slug_path": "decks/endocrine/glp1-weight-management/week-06-injection/",
        "html_path": ROOT / "decks/endocrine/glp1-weight-management/week-06-injection/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "마운자로·위고비 6회차 — 주사·보관·놓쳤을 때",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "비만 약물치료 · 주사법 · 보관",
    },
    {
        "kind": "decks", "slug": "glp1-week-07-safety",
        "slug_path": "decks/endocrine/glp1-weight-management/week-07-safety/",
        "html_path": ROOT / "decks/endocrine/glp1-weight-management/week-07-safety/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "마운자로·위고비 7회차 — 위험 신호와 진료 연락",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "비만 약물치료 · 안전성 · Red flags",
    },
    {
        "kind": "decks", "slug": "glp1-week-08-maintenance",
        "slug_path": "decks/endocrine/glp1-weight-management/week-08-maintenance/",
        "html_path": ROOT / "decks/endocrine/glp1-weight-management/week-08-maintenance/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "마운자로·위고비 8회차 — 감량 이후 유지 전략",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "비만 약물치료 · 체중 유지 · 요요 예방",
    },
    {
        "kind": "decks", "slug": "gout",
        "slug_path": "decks/endocrine/gout/",
        "html_path": ROOT / "decks/endocrine/gout/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "통풍 환자 교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "통풍 (Gout)",
    },
    {
        "kind": "decks", "slug": "iron-deficiency-anemia",
        "slug_path": "decks/heme/iron-deficiency-anemia/",
        "html_path": ROOT / "decks/heme/iron-deficiency-anemia/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "철결핍성 빈혈 환자 교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "철결핍성 빈혈 (Iron Deficiency Anemia)",
    },
    {
        "kind": "decks", "slug": "pneumococcal",
        "slug_path": "decks/vaccines/pneumococcal/",
        "html_path": ROOT / "decks/vaccines/pneumococcal/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "폐렴구균 백신 환자설명",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "폐렴구균 백신 (Pneumococcal Vaccine)",
    },
    {
        "kind": "decks", "slug": "vasovagal-syncope",
        "slug_path": "decks/cardio/vasovagal-syncope/",
        "html_path": ROOT / "decks/cardio/vasovagal-syncope/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "미주신경성 실신",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "미주신경성 실신 (Vasovagal Syncope)",
    },
    {
        "kind": "decks", "slug": "microscopic-hematuria",
        "slug_path": "decks/uro/microscopic-hematuria/",
        "html_path": ROOT / "decks/uro/microscopic-hematuria/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "현미경적 혈뇨",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "현미경적 혈뇨 (Microscopic Hematuria)",
    },
    {
        "kind": "decks", "slug": "advanced-lipid-biomarkers",
        "slug_path": "decks/endocrine/advanced-lipid-biomarkers/",
        "html_path": ROOT / "decks/endocrine/advanced-lipid-biomarkers/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "고급 지질 바이오마커 환자교육",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "고급 지질 바이오마커 환자교육",
    },
    {
        "kind": "decks", "slug": "chronic-constipation",
        "slug_path": "decks/gi/chronic-constipation/",
        "html_path": ROOT / "decks/gi/chronic-constipation/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "만성변비 환자교육",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "만성변비 환자교육",
    },
    {
        "kind": "decks", "slug": "herpes-zoster",
        "slug_path": "decks/infectious/herpes-zoster/",
        "html_path": ROOT / "decks/infectious/herpes-zoster/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "대상포진 환자교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "대상포진 환자교육",
    },
    {
        "kind": "decks", "slug": "post-infectious-cough",
        "slug_path": "decks/pulmo/post-infectious-cough/",
        "html_path": ROOT / "decks/pulmo/post-infectious-cough/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "감염후기침 환자교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "감염후기침 환자교육",
    },
    {
        "kind": "decks", "slug": "osa",
        "slug_path": "decks/pulmo/osa/",
        "html_path": ROOT / "decks/pulmo/osa/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "폐쇄성 수면무호흡증 환자교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "폐쇄성 수면무호흡증 환자교육",
    },
    {
        "kind": "decks", "slug": "post-polypectomy",
        "slug_path": "decks/gi/post-polypectomy/",
        "html_path": ROOT / "decks/gi/post-polypectomy/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "용종절제술 후 관리",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "용종절제술 후 관리",
    },
    {
        "kind": "decks", "slug": "osteoporosis",
        "slug_path": "decks/endocrine/osteoporosis/",
        "html_path": ROOT / "decks/endocrine/osteoporosis/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "골다공증 환자교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "골다공증 환자교육",
    },
    {
        "kind": "decks", "slug": "influenza-antivirals",
        "slug_path": "decks/infectious/influenza-antivirals/",
        "html_path": ROOT / "decks/infectious/influenza-antivirals/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "인플루엔자 항바이러스제 비교",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "인플루엔자 항바이러스제 비교",
    },
    {
        "kind": "decks", "slug": "pft",
        "slug_path": "decks/pulmo/pft/",
        "html_path": ROOT / "decks/pulmo/pft/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "폐기능검사(PFT) 환자교육",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "폐기능검사(PFT) 환자교육",
    },
    {
        "kind": "decks", "slug": "pft-interpretation",
        "slug_path": "decks/pulmo/pft-interpretation/",
        "html_path": ROOT / "decks/pulmo/pft-interpretation/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "폐기능검사 결과 해석",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "폐기능검사 결과 해석",
    },
    {
        "kind": "decks", "slug": "ibs",
        "slug_path": "decks/gi/ibs/",
        "html_path": ROOT / "decks/gi/ibs/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "IBS 환자교육",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "IBS 환자교육",
    },
    {
        "kind": "decks", "slug": "antihypertensive-classes",
        "slug_path": "decks/cardio/antihypertensive-classes/",
        "html_path": ROOT / "decks/cardio/antihypertensive-classes/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "항고혈압제 클래스별 효력순위",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "항고혈압제 클래스별 효력순위",
    },
    {
        "kind": "decks", "slug": "pneumococcal-comparison",
        "slug_path": "decks/vaccines/pneumococcal-comparison/",
        "html_path": ROOT / "decks/vaccines/pneumococcal-comparison/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "폐렴구균백신 캡박시브 비교",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "폐렴구균백신 캡박시브 비교",
    },
    {
        "kind": "decks", "slug": "chronic-urticaria",
        "slug_path": "decks/derm/chronic-urticaria/",
        "html_path": ROOT / "decks/derm/chronic-urticaria/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "만성두드러기 교육자료",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "만성두드러기 교육자료",
    },
    {
        "kind": "decks", "slug": "acute-gastroenteritis-diet",
        "slug_path": "decks/gi/acute-gastroenteritis-diet/",
        "html_path": ROOT / "decks/gi/acute-gastroenteritis-diet/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "급성장염 식이관리",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "급성장염 식이관리",
    },
    {
        "kind": "decks", "slug": "asthma",
        "slug_path": "decks/pulmo/asthma/",
        "html_path": ROOT / "decks/pulmo/asthma/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "천식 환자교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "천식 환자교육",
    },
    {
        "kind": "decks", "slug": "eye-cardiovascular",
        "slug_path": "decks/cardio/eye-cardiovascular/",
        "html_path": ROOT / "decks/cardio/eye-cardiovascular/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "닥터눈",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "닥터눈",
    },
    {
        "kind": "decks", "slug": "ltbi-treatment",
        "slug_path": "decks/infectious/ltbi-treatment/",
        "html_path": ROOT / "decks/infectious/ltbi-treatment/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "진료설명 — 잠복결핵감염(LTBI) 치료",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "잠복결핵감염 (Latent Tuberculosis Infection)",
    },
    {
        "kind": "decks", "slug": "subacute-thyroiditis",
        "slug_path": "decks/endocrine/subacute-thyroiditis/",
        "html_path": ROOT / "decks/endocrine/subacute-thyroiditis/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "진료설명 — 아급성 갑상선염",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "아급성 갑상선염 (de Quervain's Thyroiditis)",
    },
    {
        "kind": "decks", "slug": "achieve3-oral-glp1",
        "slug_path": "decks/endocrine/achieve3-oral-glp1/",
        "html_path": ROOT / "decks/endocrine/achieve3-oral-glp1/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "ACHIEVE-3 — 먹는 GLP-1 직접비교 (오포글리프론 vs 세마글루타이드)",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "제2형 당뇨병 · 경구 GLP-1 (ACHIEVE-3)",
    },

    # === Migration: 14 new handouts ===

    {
        "kind": "handouts", "slug": "dyslipidemia-diet",
        "slug_path": "handouts/lifestyle/dyslipidemia-diet/",
        "html_path": ROOT / "handouts/lifestyle/dyslipidemia-diet/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "고지혈증 식단",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "이상지질혈증 (Dyslipidemia) — 식이요법",
    },
    {
        "kind": "handouts", "slug": "iron-deficiency-anemia-diet",
        "slug_path": "handouts/lifestyle/iron-deficiency-anemia-diet/",
        "html_path": ROOT / "handouts/lifestyle/iron-deficiency-anemia-diet/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "빈혈 식사 교육",
        "category": "💊 투약·생활습관", "audience": "환자/보호자", "disease": "철결핍성 빈혈 (Iron Deficiency Anemia) — 식이요법",
    },
    {
        "kind": "handouts", "slug": "diabetes-diet",
        "slug_path": "handouts/lifestyle/diabetes-diet/",
        "html_path": ROOT / "handouts/lifestyle/diabetes-diet/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "당뇨 환자를 위한 식이요법 가이드",
        "category": "🌿 생활습관·식이", "audience": "환자/보호자", "disease": "당뇨 환자를 위한 식이요법 가이드",
    },
    {
        "kind": "handouts", "slug": "ibs-fodmap-diet",
        "slug_path": "handouts/lifestyle/ibs-fodmap-diet/",
        "html_path": ROOT / "handouts/lifestyle/ibs-fodmap-diet/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "과민성장증후군(IBS) 식사 가이드 — 저FODMAP 3단계",
        "category": "🌿 생활습관·식이", "audience": "환자/보호자", "disease": "과민성장증후군 (IBS) — 저FODMAP 식이요법",
    },
    {
        "kind": "handouts", "slug": "hypertension-intake",
        "slug_path": "handouts/forms/hypertension-intake/",
        "html_path": ROOT / "handouts/forms/hypertension-intake/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "고혈압 초진 설문지",
        "category": "📝 동의서·서식", "audience": "환자/보호자", "disease": "고혈압 초진 설문지",
        "notion_sync": False,
    },
    {
        "kind": "handouts", "slug": "colonoscopy-prep",
        "slug_path": "handouts/endoscopy/colonoscopy-prep/",
        "html_path": ROOT / "handouts/endoscopy/colonoscopy-prep/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "대장내시경 준비 안내문",
        "category": "🏥 내시경 관련", "audience": "환자/보호자", "disease": "대장내시경 준비 안내문",
    },
    {
        "kind": "handouts", "slug": "egd-prep",
        "slug_path": "handouts/endoscopy/egd-prep/",
        "html_path": ROOT / "handouts/endoscopy/egd-prep/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "위내시경(EGD) 검사 준비 안내문",
        "category": "🏥 내시경 관련", "audience": "환자/보호자", "disease": "위내시경 검사 전 준비 · 금식 · GLP-1RA · 항혈전제",
    },
    {
        "kind": "handouts", "slug": "antithrombotic-pre-endoscopy",
        "slug_path": "handouts/endoscopy/antithrombotic-pre-endoscopy/",
        "html_path": ROOT / "handouts/endoscopy/antithrombotic-pre-endoscopy/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "항혈전제 복용자 내시경 전 상담표",
        "category": "🏥 내시경 관련", "audience": "환자/보호자", "disease": "항혈전제 복용자 내시경 전 상담",
    },
    {
        "kind": "handouts", "slug": "abdominal-ultrasound-prep",
        "slug_path": "handouts/imaging/abdominal-ultrasound-prep/",
        "html_path": ROOT / "handouts/imaging/abdominal-ultrasound-prep/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "복부초음파 전 준비 안내",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "복부초음파 검사 전 준비",
    },
    {
        "kind": "handouts", "slug": "gallbladder-polyp-followup",
        "slug_path": "handouts/gi/gallbladder-polyp-followup/",
        "html_path": ROOT / "handouts/gi/gallbladder-polyp-followup/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "담낭 폴립 추적 안내",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "담낭 폴립 추적·수술 상담 기준",
    },
    {
        "kind": "handouts", "slug": "bone-density-prep",
        "slug_path": "handouts/imaging/bone-density-prep/",
        "html_path": ROOT / "handouts/imaging/bone-density-prep/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "골밀도 검사 안내",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "골밀도 검사(DXA) 준비 안내",
    },
    {
        "kind": "handouts", "slug": "bone-density-room-guide",
        "slug_path": "handouts/imaging/bone-density-room-guide/",
        "html_path": ROOT / "handouts/imaging/bone-density-room-guide/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "골밀도 검사 진행 안내 (검사실 비치용)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "골밀도 검사(DXA) 검사실 자세·진행 가이드",
    },
    {
        "kind": "handouts", "slug": "pulmonary-function-test-prep",
        "slug_path": "handouts/respiratory/pulmonary-function-test-prep/",
        "html_path": ROOT / "handouts/respiratory/pulmonary-function-test-prep/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "폐기능 검사(PFT) 안내",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "폐기능 검사(PFT) 준비 안내",
        "version": "v1.1",
    },
    {
        "kind": "handouts", "slug": "cold-return-visit",
        "slug_path": "handouts/respiratory/cold-return-visit/",
        "html_path": ROOT / "handouts/respiratory/cold-return-visit/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "감기약 복용 중 다시 진료가 필요한 증상",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "감기 재진 경고 증상 · 부비동염 의심 증상",
    },
    {
        "kind": "handouts", "slug": "abdominal-pain-appendicitis-red-flags",
        "slug_path": "handouts/gi/abdominal-pain-appendicitis-red-flags/",
        "html_path": ROOT / "handouts/gi/abdominal-pain-appendicitis-red-flags/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "복통 감별진단: 맹장염을 놓치지 않기",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "복통 감별진단 · 급성충수염 경고 신호",
    },
    {
        "kind": "handouts", "slug": "blood-draw-prep",
        "slug_path": "handouts/screening/blood-draw-prep/",
        "html_path": ROOT / "handouts/screening/blood-draw-prep/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "채혈 전 준비 안내",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "채혈 전 준비",
    },
    {
        "kind": "handouts", "slug": "blood-draw-aftercare",
        "slug_path": "handouts/screening/blood-draw-aftercare/",
        "html_path": ROOT / "handouts/screening/blood-draw-aftercare/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "채혈 후 지혈 안내 (검사실 비치용)",
        "category": "🩺 일반내과", "audience": "환자/보호자",
        "disease": "채혈 후 지혈·멍 예방 — 검사실 비치용",
    },
    {
        "kind": "handouts", "slug": "urine-collection",
        "slug_path": "handouts/screening/urine-collection/",
        "html_path": ROOT / "handouts/screening/urine-collection/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "소변검사 채뇨 안내",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "소변검사 채뇨",
    },
    {
        "kind": "handouts", "slug": "urine-collection-restroom",
        "slug_path": "handouts/screening/urine-collection-restroom/",
        "html_path": ROOT / "handouts/screening/urine-collection-restroom/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "소변 검체 받는 방법 (화장실 비치용)",
        "category": "🩺 일반내과", "audience": "환자/보호자",
        "disease": "소변검사 채뇨 — 화장실 비치용",
    },
    {
        "kind": "handouts", "slug": "fit-collection",
        "slug_path": "handouts/screening/fit-collection/",
        "html_path": ROOT / "handouts/screening/fit-collection/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "FIT 대변검사 채취 방법",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "대변잠혈검사(FIT) 채취 방법",
    },
    {
        "kind": "handouts", "slug": "checkup-prep",
        "slug_path": "handouts/screening/checkup-prep/",
        "html_path": ROOT / "handouts/screening/checkup-prep/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "건강검진 전 준비사항",
        "category": "🏥 내시경 관련", "audience": "환자/보호자", "disease": "건강검진 전 준비사항",
    },
    {
        "kind": "handouts", "slug": "post-egd",
        "slug_path": "handouts/endoscopy/post-egd/",
        "html_path": ROOT / "handouts/endoscopy/post-egd/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "위내시경 후 주의사항",
        "category": "🩺 시술·처치 후", "audience": "환자/보호자", "disease": "위내시경 후 주의사항",
        "notion_sync": False,
    },
    {
        "kind": "handouts", "slug": "hypertension-low-salt",
        "slug_path": "handouts/lifestyle/hypertension-low-salt/",
        "html_path": ROOT / "handouts/lifestyle/hypertension-low-salt/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "고혈압 환자를 위한 저염식 가이드",
        "category": "🌿 생활습관·식이", "audience": "환자/보호자", "disease": "고혈압 환자를 위한 저염식 가이드",
    },
    {
        "kind": "handouts", "slug": "dyslipidemia-diet-exercise",
        "slug_path": "handouts/lifestyle/dyslipidemia-diet-exercise/",
        "html_path": ROOT / "handouts/lifestyle/dyslipidemia-diet-exercise/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "고지혈증 환자를 위한 식이·운동 가이드",
        "category": "🌿 생활습관·식이", "audience": "환자/보호자", "disease": "고지혈증 환자를 위한 식이·운동 가이드",
    },
    {
        "kind": "handouts", "slug": "post-colonoscopy",
        "slug_path": "handouts/endoscopy/post-colonoscopy/",
        "html_path": ROOT / "handouts/endoscopy/post-colonoscopy/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "대장내시경 후 주의사항",
        "category": "🩺 시술·처치 후", "audience": "환자/보호자", "disease": "대장내시경 후 주의사항",
        "notion_sync": False,
    },
    {
        "kind": "handouts", "slug": "post-polypectomy",
        "slug_path": "handouts/endoscopy/post-polypectomy/",
        "html_path": ROOT / "handouts/endoscopy/post-polypectomy/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "용종절제술 후 주의사항",
        "category": "🩺 시술·처치 후", "audience": "환자/보호자", "disease": "대장내시경 용종절제술 (Polypectomy) 후 주의사항",
    },
    {
        "kind": "handouts", "slug": "post-colonoscopy-clean",
        "slug_path": "handouts/endoscopy/post-colonoscopy-clean/",
        "html_path": ROOT / "handouts/endoscopy/post-colonoscopy-clean/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "대장내시경 후 주의사항 (용종 없음·절제 없음)",
        "category": "🩺 시술·처치 후", "audience": "환자/보호자", "disease": "용종 없음·절제 없는 대장내시경 후 주의사항",
    },
    {
        "kind": "handouts", "slug": "post-egd-clean",
        "slug_path": "handouts/endoscopy/post-egd-clean/",
        "html_path": ROOT / "handouts/endoscopy/post-egd-clean/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "위내시경 후 주의사항 (조직검사 없음)",
        "category": "🩺 시술·처치 후", "audience": "환자/보호자", "disease": "조직검사 없는 위내시경 후 주의사항",
    },
    {
        "kind": "handouts", "slug": "post-egd-biopsy",
        "slug_path": "handouts/endoscopy/post-egd-biopsy/",
        "html_path": ROOT / "handouts/endoscopy/post-egd-biopsy/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "위내시경 후 주의사항 (조직검사·CLO 검사)",
        "category": "🩺 시술·처치 후", "audience": "환자/보호자", "disease": "조직검사 또는 CLO 검사 한 위내시경 후 주의사항·H. pylori 안내",
    },
    {
        "kind": "handouts", "slug": "glp1ra-pre-procedure",
        "slug_path": "handouts/endoscopy/glp1ra-pre-procedure/",
        "html_path": ROOT / "handouts/endoscopy/glp1ra-pre-procedure/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "위고비·마운자로 사용 환자의 내시경·초음파 검사 안내",
        "category": "🏥 내시경 관련", "audience": "환자/보호자", "disease": "GLP-1 RA (위고비·마운자로) 사용 환자 검사 전 주의사항",
    },
    {
        "kind": "handouts", "slug": "liver-enzyme-fatty-liver",
        "slug_path": "handouts/results/liver-enzyme-fatty-liver/",
        "html_path": ROOT / "handouts/results/liver-enzyme-fatty-liver/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "간수치 상승·지방간 결과 안내",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "간수치 상승·지방간",
    },
    {
        "kind": "handouts", "slug": "egfr-proteinuria",
        "slug_path": "handouts/results/egfr-proteinuria/",
        "html_path": ROOT / "handouts/results/egfr-proteinuria/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "신장기능 eGFR·단백뇨 결과 안내",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "eGFR 감소·단백뇨",
    },
    {
        "kind": "handouts", "slug": "thyroid-function",
        "slug_path": "handouts/results/thyroid-function/",
        "html_path": ROOT / "handouts/results/thyroid-function/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "갑상선 기능검사 결과 안내",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "갑상선 기능검사",
    },
    {
        "kind": "handouts", "slug": "diabetes-intake",
        "slug_path": "handouts/forms/diabetes-intake/",
        "html_path": ROOT / "handouts/forms/diabetes-intake/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "당뇨병 초진 설문지",
        "category": "📝 동의서·서식", "audience": "환자/보호자", "disease": "당뇨병 초진 설문지",
        "notion_sync": False,
    },
    {
        "kind": "handouts", "slug": "fit-positive",
        "slug_path": "handouts/screening/fit-positive/",
        "html_path": ROOT / "handouts/screening/fit-positive/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "대변잠혈검사(FIT) 양성 안내문",
        "category": "🏥 내시경 관련", "audience": "환자/보호자", "disease": "대변잠혈검사(FIT) 양성 안내문",
    },
    {
        "kind": "handouts", "slug": "cvd-retinal-screening",
        "slug_path": "handouts/screening/cvd-retinal-screening/",
        "html_path": ROOT / "handouts/screening/cvd-retinal-screening/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "AI 망막 심혈관 위험 검사 안내",
        "category": "🩺 일반내과", "audience": "환자/보호자",
        "disease": "AI 망막 분석 심혈관 위험 검사 (CT·방사선 없이 90%+ 정확도, 70,000원, 실비 적용)",
    },
    {
        "kind": "handouts", "slug": "glp1-intake",
        "slug_path": "handouts/forms/glp1-intake/",
        "html_path": ROOT / "handouts/forms/glp1-intake/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "💉 GLP-1 수용체 작용제(마운자로/위고비) 초진 문진표",
        "category": "📝 동의서·서식", "audience": "환자/보호자", "disease": "💉 GLP-1 수용체 작용제(마운자로/위고비) 초진 문진표",
        "notion_sync": False,
    },
    {
        "kind": "handouts", "slug": "chronic-disease-intake",
        "slug_path": "handouts/forms/chronic-disease-intake/",
        "html_path": ROOT / "handouts/forms/chronic-disease-intake/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "만성질환 초진 설문지",
        "category": "📝 동의서·서식", "audience": "환자/보호자", "disease": "만성질환 초진 설문지",
    },
    {
        "kind": "handouts", "slug": "sglt2-precautions",
        "slug_path": "handouts/medication/sglt2-precautions/",
        "html_path": ROOT / "handouts/medication/sglt2-precautions/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "💊 SGLT2 억제제 신규 처방 주의사항 (포시가·자디앙·슈글렛)",
        "category": "💊 투약 안내", "audience": "환자/보호자",
        "disease": "SGLT2 억제제 (다파글리플로진·엠파글리플로진·이프라글리플로진) 신규 처방 안전 복용 가이드 — DKA·푸르니에괴저·SSTOP 룰",
    },
    {
        "kind": "handouts", "slug": "iron-supplement",
        "slug_path": "handouts/medication/iron-supplement/",
        "html_path": ROOT / "handouts/medication/iron-supplement/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "💊 철분제 복용 시 주의사항 (흡수 부스터·차단제·복약 가이드)",
        "category": "💊 투약 안내", "audience": "환자/보호자",
        "disease": "경구 철분제 복약 가이드 — 비타민 C 시너지·탄닌·칼슘·제산제 흡수 방해·격일 복용·페리틴 회복",
    },
    {
        "kind": "handouts", "slug": "creatine-guide",
        "slug_path": "handouts/lifestyle/creatine-guide/",
        "html_path": ROOT / "handouts/lifestyle/creatine-guide/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "크레아틴 복용 가이드 — 효과·부작용·복용 주의사항",
        "category": "🌿 생활습관·식이", "audience": "환자/보호자",
        "disease": "크레아틴 모노하이드레이트 보충제 — 운동 수행능력, 복용량, 신장 기능 검사 해석, 탈모 논란, 복용 전 상담 대상",
    },
    {
        "kind": "handouts", "slug": "thyroid-hormone-taking",
        "slug_path": "handouts/medication/thyroid-hormone-taking/",
        "html_path": ROOT / "handouts/medication/thyroid-hormone-taking/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "💊 갑상선 호르몬제 복용법 — 씬지로이드, 씬지록신 공복 복용 안내",
        "category": "💊 투약 안내", "audience": "환자/보호자",
        "disease": "갑상선 기능저하증 및 갑상선암 수술 후 레보티록신 복용 교육 — 아침 공복, 복용 후 30~60분 금식, 칼슘·철분·제산제 4시간 분리, 저녁 복용 연구 근거.",
    },
    {
        "kind": "handouts", "slug": "thyroid-nodule-followup",
        "slug_path": "handouts/endocrine/thyroid-nodule-followup/",
        "html_path": ROOT / "handouts/endocrine/thyroid-nodule-followup/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "갑상선 결절 추적 안내 — K-TIRADS와 세침흡인검사 기준",
        "category": "🩺 일반내과", "audience": "환자/보호자",
        "disease": "갑상선 결절 초음파 추적 — K-TIRADS 등급, 세침흡인검사(FNA) 크기 기준, Bethesda class별 추적 계획",
    },
    {
        "kind": "handouts", "slug": "hyperprolactinemia-protocol",
        "slug_path": "handouts/endocrine/hyperprolactinemia-protocol/",
        "html_path": ROOT / "handouts/endocrine/hyperprolactinemia-protocol/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "프로락틴 상승 시 진료 프로토콜",
        "category": "🩺 일반내과", "audience": "환자/보호자",
        "disease": "프로락틴 상승 환자 공통 안내 — 재검 조건, 약물·임신·갑상선·신장 기능 확인, 지속 상승 시 뇌하수체 평가 흐름",
    },
    {
        "kind": "handouts", "slug": "cgm-caresens365",
        "slug_path": "handouts/endocrine/cgm-caresens365/",
        "html_path": ROOT / "handouts/endocrine/cgm-caresens365/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "케어센스 365 연속혈당측정 안내 — 손가락 끝 한 방울로는 보이지 않는 것들",
        "category": "🩺 일반내과", "audience": "환자/보호자",
        "disease": "연속혈당측정 (CGM, CareSens 365) — 14일 블라인드(전문가) 모드 진단 검사, SMBG·HbA1c 한계, TIR, 비급여 안내",
    },
    {
        "kind": "handouts", "slug": "fasting-glucose",
        "slug_path": "handouts/endocrine/fasting-glucose/",
        "html_path": ROOT / "handouts/endocrine/fasting-glucose/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "아침 공복혈당이 높게 나오는 이유와 생활 관리",
        "category": "🌿 생활습관·식이", "audience": "환자/보호자",
        "disease": "아침 공복혈당 상승 환자 안내 — 밤사이 간의 포도당 생성과 새벽 현상(자연스러운 작용)이 주원인이며 소모기(저혈당 반동)는 드묾, 혈당을 올리는 생활 요인(체중·야식·운동부족·수면부족/코골이·스트레스·스테로이드), 효과가 큰 순서의 생활 관리(체중 5~10% 감량·저녁 식후 걷기·주 150분 운동·수면·야식↓·식이섬유·절주), 진료가 필요한 신호.",
    },
    {
        "kind": "handouts", "slug": "joint-supplements",
        "slug_path": "handouts/musculoskeletal/joint-supplements/",
        "html_path": ROOT / "handouts/musculoskeletal/joint-supplements/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "관절 영양제, 도움이 될까요? — 골관절염 환자 안내",
        "category": "🌿 생활습관·식이", "audience": "환자/보호자",
        "disease": "골관절염(퇴행성 관절염) 환자를 위한 관절 영양제 안내 — 영양제는 진통 효과가 약보다 약하나 위장·콩팥 부담이 적어 NSAID 못 쓰는 분께 시도 가치(만능 아님). 글루코사민·콘드로이틴(효과 엇갈림, 항응고제 주의)·MSM(근거 약함)·강황/커큐민(통증 도움 가능, 간·항응고제·담석·철분 주의)·보스웰리아(무난)·콜라겐/오메가3(관절 근거 약함) 비교, 안전 복용 4수칙, 영양제보다 확실한 체중감량·운동·바르는 소염제(디클로페낙 젤), 진료 신호.",
    },
    {
        "kind": "handouts", "slug": "nasal-spray-allergic-rhinitis",
        "slug_path": "handouts/medication/nasal-spray-allergic-rhinitis/",
        "html_path": ROOT / "handouts/medication/nasal-spray-allergic-rhinitis/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "💧 알러지 비염 코 스프레이, 이렇게 사용하세요 — 자세·각도·흡입·매일",
        "category": "💊 투약 안내", "audience": "환자/보호자",
        "disease": "알러지 비염 환자를 위한 비강 스테로이드 스프레이 사용 4단계 — 턱 살짝 당기기(턱 들기 금지), 같은 쪽 눈 방향으로 비스듬히 분사(비중격 회피), 분사 후 코로 살짝 흡입, 매일 1~2회 꾸준히. 효과는 1~2주 누적 후 발현, 안전성은 전신 흡수 < 1%.",
    },
    {
        "kind": "handouts", "slug": "htn-why-start",
        "slug_path": "handouts/medication/htn-why-start/",
        "html_path": ROOT / "handouts/medication/htn-why-start/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "💊 고혈압 약, 미루지 말아야 하는 이유 — 합병증 예방·감량 로드맵",
        "category": "💊 투약 안내", "audience": "환자/보호자",
        "disease": "고혈압 약물 치료의 목적(혈관 합병증 예방) 안내 — 운동·영양제·체중감량으로 약 시작을 미루려는 환자 대상. 5대 합병증 인포그래픽(뇌·눈·심장·대혈관·신장), 흔한 오해 vs 사실, 약 감량·중단 3단계 로드맵.",
    },
    {
        "kind": "handouts", "slug": "insulin-start",
        "slug_path": "handouts/medication/insulin-start/",
        "html_path": ROOT / "handouts/medication/insulin-start/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "💉 인슐린 주사 처음 시작하시는 분께 — 보관·소독·부위·회전·용량",
        "category": "💊 투약 안내", "audience": "환자/보호자",
        "disease": "당뇨 환자가 처음 인슐린 자가 주사를 시작할 때 알아야 할 5가지 — 냉장→상온 보관, 알코올 소독 후 완전 건조, 권장 주사 부위 4곳·배꼽 5cm 회피, 2~3cm 회전 룰, 10단위 시작 후 공복혈당 140 초과 3~4일 연속 시 +2단위 증량 규칙.",
    },
    {
        "kind": "handouts", "slug": "hand-eczema-steroid-potency",
        "slug_path": "handouts/medication/hand-eczema-steroid-potency/",
        "html_path": ROOT / "handouts/medication/hand-eczema-steroid-potency/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "손 습진 스테로이드 연고 효능 순서 — 역가별 선택·step-down",
        "category": "💊 투약 안내", "audience": "의료진",
        "disease": "손 습진(hand eczema) 외용제 선택 — 두꺼운 손바닥은 초강력·강력 국소 스테로이드를 짧게 충분히 사용하고 호전 후 중등도 제제로 step-down, TCI·알리트레티노인·보습·장갑 차단까지 한 장 요약.",
    },
    # === Migration: 11 new patient lab reports (2026-05-08) ===
    {
        "kind": "lab-reports", "slug": "13f629bf11",
        "slug_path": "lab-reports/bone-metabolism/13f629bf11/",
        "html_path": ROOT / "lab-reports/bone-metabolism/13f629bf11/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[1063] 김종혁 — 골 대사 검사 (2026-04-29)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "골다공증·골대사",
    },
    {
        "kind": "lab-reports", "slug": "53abb9a8c8",
        "slug_path": "lab-reports/bone-metabolism/53abb9a8c8/",
        "html_path": ROOT / "lab-reports/bone-metabolism/53abb9a8c8/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[4693] 김현아 — 골 대사 검사 (2026-04-28)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "골다공증·골대사",
    },
    {
        "kind": "lab-reports", "slug": "ea087af656",
        "slug_path": "lab-reports/comprehensive-summary/ea087af656/",
        "html_path": ROOT / "lab-reports/comprehensive-summary/ea087af656/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[12784] 오완영 — 종합 검진 요약 (2026-04-29)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "종합 검진",
    },
    {
        "kind": "lab-reports", "slug": "e33c38ae14",
        "slug_path": "lab-reports/comprehensive-summary/e33c38ae14/",
        "html_path": ROOT / "lab-reports/comprehensive-summary/e33c38ae14/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[12357] 정행년 — 종합 검진 요약 (2026-04-21)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "종합 검진",
    },
    {
        "kind": "lab-reports", "slug": "5e3ecd7635",
        "slug_path": "lab-reports/cv-screening/5e3ecd7635/",
        "html_path": ROOT / "lab-reports/cv-screening/5e3ecd7635/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[27474] 김양수 — 심혈관 위험 평가 (2026-04-21)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "심혈관 위험",
    },
    {
        "kind": "lab-reports", "slug": "f7aa074e4d",
        "slug_path": "lab-reports/cv-screening/f7aa074e4d/",
        "html_path": ROOT / "lab-reports/cv-screening/f7aa074e4d/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[11960] 안미흥 — 심혈관 위험 평가 (2026-04-28)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "심혈관 위험",
    },
    {
        "kind": "lab-reports", "slug": "6560324c10",
        "slug_path": "lab-reports/cv-screening/6560324c10/",
        "html_path": ROOT / "lab-reports/cv-screening/6560324c10/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[8223] 전상영 — 심혈관 위험 평가 (2026-04-28)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "심혈관 위험",
    },
    {
        "kind": "lab-reports", "slug": "0883646ddd",
        "slug_path": "lab-reports/cv-screening/0883646ddd/",
        "html_path": ROOT / "lab-reports/cv-screening/0883646ddd/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "심혈관 위험",
        "patient_name": "곽정옥", "chart_no": "435",
        "exam_date": "2026-05-09", "doctor": "정지환",
        "note": "Lp(a) 상승 — 적극적 LDL 관리 권고",
    },
    {
        "kind": "lab-reports", "slug": "8a614fd8f2",
        "slug_path": "lab-reports/cv-screening/8a614fd8f2/",
        "html_path": ROOT / "lab-reports/cv-screening/8a614fd8f2/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "심혈관 위험",
        "patient_name": "박성주", "chart_no": "29859",
        "exam_date": "2026-05-09", "doctor": "정지환",
        "note": "심근효소 정상 — 안정시 흉부 불편감은 비심장성. 고지혈(TC 264·LDL 144·TG 377) 적극 관리 권고",
    },
    {
        "kind": "lab-reports", "slug": "498a0b31ff",
        "slug_path": "lab-reports/diabetes-screening/498a0b31ff/",
        "html_path": ROOT / "lab-reports/diabetes-screening/498a0b31ff/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[2555] 김경태 — 당뇨 검진 결과 (2026-04-22)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "당뇨병",
    },
    {
        "kind": "lab-reports", "slug": "be7a11579c",
        "slug_path": "lab-reports/diabetes-followup/be7a11579c/",
        "html_path": ROOT / "lab-reports/diabetes-followup/be7a11579c/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "당뇨병",
        "patient_name": "김경태", "chart_no": "2555",
        "exam_date": "2026-05-26", "doctor": "정지환",
        "note": "추적 검사 (04-22 대비) — 공복혈당 208→143, HbA1c 8.6→7.8, TG 244→119 큰 호전. 소변당 3+·ALT 53 추가 관리",
    },
    {
        "kind": "lab-reports", "slug": "a8c908bd6d",
        "slug_path": "lab-reports/diabetes-screening/a8c908bd6d/",
        "html_path": ROOT / "lab-reports/diabetes-screening/a8c908bd6d/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[15870] 김양미 — 당뇨 검진 결과 (2026-04-29)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "당뇨병",
    },
    {
        "kind": "lab-reports", "slug": "771ba246e9",
        "slug_path": "lab-reports/diabetes-screening/771ba246e9/",
        "html_path": ROOT / "lab-reports/diabetes-screening/771ba246e9/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[13305] 이강성 — 당뇨 검진 결과 (2026-04-22)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "당뇨병",
    },
    {
        "kind": "lab-reports", "slug": "5d03e28e70",
        "slug_path": "lab-reports/urinalysis/5d03e28e70/",
        "html_path": ROOT / "lab-reports/urinalysis/5d03e28e70/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[1683] 윤종철 — 소변 검사 (2026-04-21)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "소변 검사 이상",
    },
    {
        # 신규 schema 예시 — explicit 환자 메타데이터 (lab-reports 권장 형식)
        "kind": "lab-reports", "slug": "969f64d2bc",
        "slug_path": "lab-reports/general-checkup/969f64d2bc/",
        "html_path": ROOT / "lab-reports/general-checkup/969f64d2bc/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "patient_name": "박순정", "chart_no": "17492",
        "exam_date": "2026-05-08", "doctor": "정지환",
        "note": "종합검사 — 콜레스테롤 경계역",
    },
    {
        "kind": "lab-reports", "slug": "b461390696",
        "slug_path": "lab-reports/general-checkup/b461390696/",
        "html_path": ROOT / "lab-reports/general-checkup/b461390696/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "고지혈·빈혈",
        "patient_name": "김은경", "chart_no": "29869",
        "exam_date": "2026-05-11", "doctor": "정지환",
        "note": "공단검진 — 심한 고지혈(TC 322·LDL 202·Lp(a) 94.8) 약물치료 권고 · 빈혈(Hb 9.5) 철결핍 확인 필요",
    },
    {
        "kind": "lab-reports", "slug": "58c4c71b86",
        "slug_path": "lab-reports/general-checkup/58c4c71b86/",
        "html_path": ROOT / "lab-reports/general-checkup/58c4c71b86/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "갑상선 기능저하",
        "patient_name": "김정원", "chart_no": "26",
        "exam_date": "2026-03-25", "doctor": "정지환",
        "note": "종합검사 — 갑상선 반절제술 후 TSH 6.15 경도상승, 신지로이드 25μg 시작 · 그 외 모두 정상 (암표지자 4종·고지혈·당뇨 정상)",
    },
    {
        "kind": "lab-reports", "slug": "d160ae37cb",
        "slug_path": "lab-reports/general-checkup/d160ae37cb/",
        "html_path": ROOT / "lab-reports/general-checkup/d160ae37cb/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "고지혈·당뇨전단계",
        "patient_name": "김영미", "chart_no": "28262",
        "exam_date": "2026-05-16", "doctor": "정지환",
        "note": "공단검진 — 고지혈(TC 261·LDL 200) 약물치료 권고 · 공복혈당 경계(111)·HbA1c 5.5% 정상 · hs-CRP 2.7 평균 위험 · Hct·Na·소변비중 동반 상승(탈수 양상) · 갑상선·암표지자 5종 모두 정상",
    },
    {
        "kind": "lab-reports", "slug": "19f7fad6a4",
        "slug_path": "lab-reports/comprehensive-summary/19f7fad6a4/",
        "html_path": ROOT / "lab-reports/comprehensive-summary/19f7fad6a4/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "종합 검진",
        "patient_name": "김수홍", "chart_no": "97",
        "exam_date": "2026-05-09", "doctor": "정지환",
        "note": "요산 8.6 ↑ (저퓨린 식이) · TSH 4.98 ↑ (불현성 갑상선 저하 — 추적)",
    },
    {
        "kind": "lab-reports", "slug": "0d8f6f8adf",
        "slug_path": "lab-reports/health-checkup/0d8f6f8adf/",
        "html_path": ROOT / "lab-reports/health-checkup/0d8f6f8adf/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "종합 건강검진",
        "patient_name": "검진가나", "chart_no": "DEMO01",
        "exam_date": "2026-05-14", "doctor": "정지환",
        "note": "DEMO 가공 환자 — 8 모듈 모두 활성, 2페이지 (혈액·소변·내시경·초음파·심전도·골밀도 통합) · H. pylori 제균 + LDL/HbA1c 경계 + 결절·골 follow-up",
    },

    # === Neurology — Migraine (2026-05-20) ===
    {
        "kind": "decks", "slug": "migraine-diagnosis",
        "slug_path": "decks/neurology/migraine/diagnosis/",
        "html_path": ROOT / "decks/neurology/migraine/diagnosis/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "편두통 — 위장 증상에 가려진 진짜 원인",
        "category": "🩺 일반내과", "audience": "환자/보호자",
        "disease": "편두통 (Migraine) — 소화불량·메스꺼움 주소 환자에서 의심해야 할 위장 표현 (전구기·gastroparesis·복부편두통·CVS 스펙트럼) · ICHD-3 진단기준 · 대한두통학회 2021",
    },
    {
        "kind": "handouts", "slug": "migraine",
        "slug_path": "handouts/neurology/migraine/",
        "html_path": ROOT / "handouts/neurology/migraine/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "편두통 — 위장 증상에 가려진 진짜 원인 (A4 1장)",
        "category": "🩺 일반내과", "audience": "환자/보호자",
        "disease": "편두통 (Migraine) — 위장 증상 동반 편두통의 4가지 양상, 의심 단서 6가지, ICHD-3 진단·치료·red flag 한 장 요약",
    },
    {
        "kind": "lab-reports", "slug": "19b619182b",
        "slug_path": "lab-reports/health-checkup/19b619182b/",
        "html_path": ROOT / "lab-reports/health-checkup/19b619182b/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "종합 건강검진",
        "patient_name": "정상각", "chart_no": "13713",
        "exam_date": "2026-05-22", "doctor": "정지환",
        "note": "공단검진+추가 — 간기능 ALT 249↑·갑상선 항진(TSH↓/fT4↑)·당뇨 고위험(HbA1c 6.1) 3건 동반 · 복부초음파·TRAb·간염표지자 즉시 권고",
    },
    {
        "kind": "lab-reports", "slug": "ca40e9a838",
        "slug_path": "lab-reports/igra-followup/ca40e9a838/",
        "html_path": ROOT / "lab-reports/igra-followup/ca40e9a838/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "잠복결핵·IGRA 추적",
        "patient_name": "이순열", "chart_no": "4798",
        "exam_date": "2026-05-21", "doctor": "정지환",
        "note": "잠복결핵 IGRA 2년 추적 — 0.487(Pos)→0.302(Neg) reversion · 두 값 모두 uncertainty zone(0.35~0.70) 내 측정 변동성으로 해석 · LTBI 진단 유지 (대한결핵학회 4판·WHO 2024·CDC)",
    },
]


def _check_qr_populated(
    html: str,
    *,
    qr_class: str,
    target_url: str,
    want_url_text: bool,
) -> list[str]:
    """Assert the injected QR block is non-empty (and URL text present).

    Guards against the historical empty-QR bug (SKILL.md Gotcha 3) where the
    raw index.html shipped an empty ``<div class="qr-block__code"></div>`` to
    the live site. Returns a list of error strings (empty = OK) so the caller
    can fail the build loudly.

    Checks:
      1. The target QR div actually contains an ``<svg …>`` element.
      2. (handout footers only) the typeable ``.qr-mini__url`` line exists and
         its text matches the QR target (scheme stripped).
    """
    errs: list[str] = []

    # 1. QR div non-empty: find <div class="...qr_class...">…</div> and require
    #    an <svg inside. Use a non-greedy capture up to the matching depth-0
    #    close is overkill here — the QR div has no nested divs, so stop at the
    #    first </div>.
    cls = re.escape(qr_class)
    m = re.search(
        rf'<div\s+class="(?:[^"]*\s)?{cls}(?:\s[^"]*)?"\s*>(.*?)</div>',
        html,
        re.DOTALL,
    )
    if not m:
        errs.append(f"QR div .{qr_class} not found in HTML")
    elif "<svg" not in m.group(1).lower():
        errs.append(
            f"empty QR — .{qr_class} has no <svg> (historical empty-QR bug, "
            f"SKILL.md Gotcha 3)"
        )

    # 2. Handout footer typeable URL line.
    if want_url_text:
        url_text = qr_mini_url_text(html)
        if not url_text:
            errs.append("missing typeable URL line (.qr-mini__url) in footer")
        else:
            want = short_qr_url_text(target_url)
            if url_text != want:
                errs.append(
                    f"URL text mismatch — footer shows '{url_text}' but QR "
                    f"encodes '{want}'"
                )

    return errs


def _decode_qr_matches(page, qr_class: str, target_url: str):
    """Best-effort: decode the rendered footer QR and check it equals target_url.

    Returns:
      - True  → decoded successfully AND payload matches target_url
      - str   → decoded successfully but payload MISMATCHES (build should fail)
      - None  → decode unavailable/inconclusive (OpenCV missing, no QR element,
                screenshot/raster failed, or detector found nothing) → skip

    Uses OpenCV's built-in QRCodeDetector if importable. No new dependency is
    added (cv2 is optional); if it is absent we simply return None.
    """
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return None
    try:
        # Screenshot the inner <svg> (not the bordered/rounded .qr-mini__code
        # box) so the detector sees a clean QR with quiet zone.
        loc = page.locator(f".{qr_class} svg").first
        if loc.count() == 0:
            loc = page.locator(f".{qr_class}").first
        if loc.count() == 0:
            return None
        png = loc.screenshot()
        arr = np.frombuffer(png, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        # Upscale + add a white quiet-zone border to help the detector.
        h, w = img.shape[:2]
        if max(h, w) < 600:
            scale = 600 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)),
                             interpolation=cv2.INTER_NEAREST)
        img = cv2.copyMakeBorder(img, 40, 40, 40, 40,
                                 cv2.BORDER_CONSTANT, value=255)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        detector = cv2.QRCodeDetector()
        data, _pts, _ = detector.detectAndDecode(img)
        if not data:
            return None  # detector found nothing → inconclusive, skip
        if data.strip() != target_url.strip():
            return (f"QR decode MISMATCH — encodes '{data.strip()}' "
                    f"but should be '{target_url}'")
        return True
    except Exception:
        return None  # any failure here is non-fatal (advisory belt-and-suspenders)


def _validate_css_paths() -> list[str]:
    """Verify each material's CSS path actually resolves to a real file.

    Catches the 4-level vs 3-level deep slug mismatch:
    - decks/cardio/chest-pain/ (3-level) needs ../../../shared/
    - decks/cardio/htn/morning/ (4-level) needs ../../../../shared/
    """
    import re
    issues: list[str] = []
    for t in TARGETS:
        html_path = t.get("html_path")
        if not html_path or not html_path.exists():
            continue
        text = html_path.read_text(encoding="utf-8")
        for m in re.finditer(r'(?:href|src)="(\.\./[^"]*?(?:shared|assets)/[^"]*)"', text):
            rel = m.group(1)
            target = (html_path.parent / rel).resolve()
            if not target.exists():
                issues.append(
                    f"{t['kind']}/{t['slug']}: '{rel}' resolves to missing {target}"
                )
                break  # one per file is enough
    return issues


_HANGUL_RE = __import__("re").compile(r"[가-힯]")
_LAB_HASH_RE = __import__("re").compile(r"^[0-9a-f]{10}$")


def _sync_asset_manifest() -> None:
    """Run shared/assets/manifest.json sync at build start. Best-effort —
    a missing tools/sync_manifest.py shouldn't break the build."""
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import sync_manifest  # noqa: E402
        sync_manifest.sync(verbose=False)
    except Exception as e:  # noqa: BLE001
        print(f"⚠️  asset manifest sync skipped: {e}", file=sys.stderr)


def _validate_data_assets() -> list[str]:
    """Pre-flight: every data-asset="key" referenced in a TARGETS HTML
    must resolve to a manifest entry whose file exists on disk. Catches
    typos before Playwright renders a broken-image page."""
    manifest = load_asset_manifest()
    issues: list[str] = []
    for t in TARGETS:
        html_path = t.get("html_path")
        if not html_path or not html_path.exists():
            continue
        text = html_path.read_text(encoding="utf-8")
        keys = collect_data_asset_keys(text)
        if not keys:
            continue
        if not manifest:
            issues.append(
                f"{t['kind']}/{t['slug']}: HTML uses data-asset but manifest "
                f"is empty — run tools/sync_manifest.py"
            )
            continue
        for key in keys:
            entry = manifest.get(key)
            if entry is None:
                # check aliases
                aliased = any(
                    key in (v.get("aliases") or []) for v in manifest.values()
                )
                if not aliased:
                    issues.append(
                        f"{t['kind']}/{t['slug']}: unknown data-asset='{key}' "
                        f"(not in manifest, no alias match)"
                    )
                    continue
                entry = next(
                    v for v in manifest.values() if key in (v.get("aliases") or [])
                )
            f = entry.get("file")
            if f and not (ROOT / "shared" / "assets" / f).exists():
                issues.append(
                    f"{t['kind']}/{t['slug']}: data-asset='{key}' → file "
                    f"missing on disk: shared/assets/{f}"
                )
    return issues


def _validate_lab_report_no_webp() -> list[str]:
    """Pre-flight: lab-reports must not embed WebP images — some PDF
    renderers (esp. older Chromium / pdfkit fallbacks) drop them, leaving
    blank rectangles on the printed page.  Allowed formats: png, jpg, svg."""
    manifest = load_asset_manifest()
    issues: list[str] = []
    for t in TARGETS:
        if t.get("kind") != "lab-reports":
            continue
        html_path = t.get("html_path")
        if not html_path or not html_path.exists():
            continue
        text = html_path.read_text(encoding="utf-8")
        # Direct <img src="…webp">
        for m in __import__("re").finditer(r'<img[^>]*src="([^"]+\.webp)"', text, __import__("re").IGNORECASE):
            issues.append(
                f"{t['kind']}/{t['slug']}: lab-report references WebP src "
                f"'{m.group(1)}' — use PNG/JPG/SVG (PDF embed safety)"
            )
        # data-asset → manifest lookup
        for key in collect_data_asset_keys(text):
            entry = manifest.get(key) or next(
                (v for v in manifest.values() if key in (v.get("aliases") or [])),
                None,
            )
            if entry and (entry.get("format") or "").lower() == "webp":
                issues.append(
                    f"{t['kind']}/{t['slug']}: data-asset='{key}' is WebP "
                    f"— lab-reports must use PNG/JPG/SVG"
                )
    return issues


def _validate_targets_routing() -> list[str]:
    """Validate every TARGETS entry — kind must match the slug_path prefix.

    This catches mis-routing at build time so a deck never ends up syncing to
    the handouts DB, and a lab-report never lands in the decks DB.

    Rules:
    - slug_path must start with the kind directory ('decks/', 'handouts/',
      'lab-reports/').
    - html_path must be inside that directory.
    - kind must be one of: decks | handouts | lab-reports.
    - lab-reports must declare patient_name + chart_no (or legacy title with
      [차트번호] prefix that _notion_sync.py can parse).
    - lab-reports slug + slug_path must NOT contain Korean Hangul characters
      (privacy guardrail — see Gotcha 11). Use lab_hash_slug() instead.
    """
    issues: list[str] = []
    valid_kinds = {"decks", "handouts", "lab-reports"}
    for i, t in enumerate(TARGETS):
        kind = t.get("kind", "")
        slug = t.get("slug", "")
        slug_path = t.get("slug_path", "")
        html_path = t.get("html_path")
        prefix = f"TARGETS[{i}] {kind}/{slug}"

        if kind not in valid_kinds:
            issues.append(f"{prefix}: invalid kind '{kind}' (must be one of {valid_kinds})")
            continue

        notion_sync = t.get("notion_sync", True)
        if not isinstance(notion_sync, bool):
            issues.append(f"{prefix}: notion_sync must be a boolean when present")

        if kind == "lab-reports" and "status" in t:
            issues.append(
                f"{prefix}: lab-reports DB has no status field; use "
                "notion_sync=False or remove the row manually"
            )

        status = t.get("status", ACTIVE_STATUS)
        if kind != "lab-reports" and status not in VALID_NOTION_STATUSES:
            valid = ", ".join(sorted(VALID_NOTION_STATUSES))
            issues.append(f"{prefix}: invalid status '{status}' (must be one of: {valid})")

        if not slug_path.startswith(f"{kind}/"):
            issues.append(f"{prefix}: slug_path '{slug_path}' does not start with kind '{kind}/'")

        if html_path and f"/{kind}/" not in str(html_path).replace("\\", "/"):
            issues.append(f"{prefix}: html_path '{html_path}' is not inside /{kind}/")

        # Privacy guardrail: lab-reports must use a hash slug, never a patient
        # name. Korean Hangul in slug or slug_path almost certainly means a
        # patient name leaked in. Compute via lab_hash_slug() in _build_helpers.
        if kind == "lab-reports":
            if _HANGUL_RE.search(slug) or _HANGUL_RE.search(slug_path):
                issues.append(
                    f"{prefix}: lab-reports slug/slug_path contains Korean characters "
                    f"— use lab_hash_slug(chart_no, patient_name, topic) instead "
                    f"(slug='{slug}', slug_path='{slug_path}')"
                )
            if "/sample/" not in slug_path and not _LAB_HASH_RE.match(slug):
                issues.append(
                    f"{prefix}: lab-reports slug must be 10 lowercase hex chars "
                    f"(got '{slug}')"
                )
            if "/sample/" not in slug_path and html_path and html_path.exists():
                text = html_path.read_text(encoding="utf-8")
                if "__HASH__" in text or "◯◯◯" in text or "「환자명」" in text:
                    issues.append(
                        f"{prefix}: placeholder remains in registered lab-report HTML"
                    )

        # lab-reports SHOULD declare patient meta — warn, don't fail
        # (sample data like /lab-reports/lipid-panel/sample/ is exempt)
        if kind == "lab-reports" and "/sample/" not in slug_path:
            has_explicit = t.get("patient_name") and t.get("chart_no")
            has_legacy = (t.get("title") or "").startswith("[")
            if not (has_explicit or has_legacy):
                # Print warning but don't add to issues (build proceeds)
                import sys
                print(
                    f"⚠️  {prefix}: lab-reports recommended fields missing "
                    f"(patient_name+chart_no or legacy '[chart_no] patient — note')",
                    file=sys.stderr,
                )
    return issues


def main() -> int:
    # Pre-flight: sync asset manifest before any HTML inspection so newly
    # added image files are auto-registered.
    _sync_asset_manifest()

    # Pre-flight: validate kind routing — fail fast on misclassified TARGETS
    routing_issues = _validate_targets_routing()
    if routing_issues:
        print("=== TARGETS routing errors (fix before build) ===", file=sys.stderr)
        for issue in routing_issues:
            print(f"  ✗ {issue}", file=sys.stderr)
        return 2

    # Pre-flight: every data-asset="key" must resolve in manifest + on disk
    asset_issues = _validate_data_assets()
    if asset_issues:
        print("=== data-asset errors (fix before build) ===", file=sys.stderr)
        for issue in asset_issues:
            print(f"  ✗ {issue}", file=sys.stderr)
        return 2

    # Pre-flight: lab-reports must not use WebP (PDF embed safety)
    webp_issues = _validate_lab_report_no_webp()
    if webp_issues:
        print("=== lab-report WebP errors (fix before build) ===", file=sys.stderr)
        for issue in webp_issues:
            print(f"  ✗ {issue}", file=sys.stderr)
        return 2

    # Pre-flight: verify CSS/asset paths resolve (catches 4-level vs 3-level bugs)
    css_issues = _validate_css_paths()
    if css_issues:
        print("=== CSS/asset path errors (fix before build) ===", file=sys.stderr)
        for issue in css_issues:
            print(f"  ✗ {issue}", file=sys.stderr)
        return 2

    failures: list[str] = []
    notion_failures: list[str] = []
    today_iso = date.today().isoformat()

    with sync_playwright() as p:
        browser = p.chromium.launch()

        for t in TARGETS:
            kind, slug = t["kind"], t["slug"]
            slug_path, html_path = t["slug_path"], t["html_path"]
            qr_class, fmt = t["qr_class"], t["fmt"]

            if not html_path.exists():
                failures.append(f"{kind}/{slug}: source missing → {html_path}")
                continue

            target_url = f"{BASE_URL}/{slug_path}"
            html = html_path.read_text(encoding="utf-8")

            # Resolve data-asset="key" → src + alt (idempotent; preserves the
            # data-asset attribute as source-of-truth for future rebuilds).
            html, asset_errs, asset_warns = resolve_data_asset(
                html, html_path, strict_review=False
            )
            if asset_errs:
                failures.append(f"{kind}/{slug}: data-asset → " + "; ".join(asset_errs))
                continue
            for w in asset_warns:
                print(f"  ⚠️  {kind}/{slug}: {w}", file=sys.stderr)

            missing = check_og_meta(html, slug)
            if missing:
                failures.append(f"{kind}/{slug}: missing meta → {', '.join(missing)}")
                continue

            if kind == "lab-reports":
                # Privacy: lab-reports name patients; printed QR + public URL
                # would let anyone scan the page and view personal results.
                # Strip the footer QR block + add noindex meta. robots.txt
                # disallows /lab-reports/ on the GH Pages side.
                injected = strip_qr_mini_block(html)
                injected = inject_noindex_meta(injected)
                if 'class="qr-mini"' in injected:
                    failures.append(
                        f"{kind}/{slug}: qr-mini block survived strip — "
                        f"check footer markup matches strip_qr_mini_block regex"
                    )
                    continue
            else:
                qr_svg = make_qr_svg(target_url)
                injected = inject_qr(html, qr_svg, target_class=qr_class)

                # Handout footer mini-QR: also render the page's short URL as a
                # small typeable text line next to the QR, so a patient who
                # can't scan can still type the address. Same URL the QR encodes
                # (scheme stripped for display). Idempotent across re-builds.
                if qr_class == "qr-mini__code":
                    injected = inject_qr_url_text(injected, target_url)

                # ── Build-time QR/URL integrity check (fail loudly) ──────────
                # There is a historical bug where the live mini-QR rendered
                # empty (SKILL.md Gotcha 3: the raw index.html kept an empty
                # <div class="qr-block__code"></div>). Assert the QR div is now
                # actually populated AND, for handout footers, that the
                # typeable URL line is present and matches the QR target.
                qr_errs = _check_qr_populated(
                    injected,
                    qr_class=qr_class,
                    target_url=target_url,
                    want_url_text=(qr_class == "qr-mini__code"),
                )
                if qr_errs:
                    failures.append(f"{kind}/{slug}: " + "; ".join(qr_errs))
                    continue

            # Write back to raw index.html so the live GH Pages copy stays in
            # sync with what we render to PDF (QR for decks/handouts, no QR
            # for lab-reports).
            html_path.write_text(injected, encoding="utf-8")
            build_file = html_path  # PDF builder uses the same file

            try:
                viewport = (
                    {"width": 1320, "height": 800}
                    if fmt == "deck-16x9"
                    else {"width": 820, "height": 1160}
                )
                ctx = browser.new_context(viewport=viewport)
                # Fail-fast: never hang forever. networkidle can stall indefinitely
                # if a page keeps any network activity (kz-002: a deck hung the local
                # build ~11min at 0% CPU). 45s cap → TimeoutError caught below, that
                # deck is recorded as a failure and the build continues.
                ctx.set_default_timeout(45000)
                page = ctx.new_page()
                page.goto(f"file://{build_file}")
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(1200)  # ensure Pretendard web font applied
                # Layout validation BEFORE rendering — catch overflows/overlaps.
                # ⭐ deck PDF는 print 미디어로 렌더되므로 검증도 print 로 (screen
                # 에서만 보면 print 폰트 메트릭 차이로 생기는 카드 겹침을 놓침).
                if fmt == "deck-16x9":
                    page.emulate_media(media="print")
                    page.wait_for_timeout(300)
                validator_js = DECK_VALIDATOR_JS if fmt == "deck-16x9" else HANDOUT_VALIDATOR_JS
                issues = page.evaluate(validator_js)
                # large_internal_gap 래칫: 유예 등록된 기존 덱에서는 이 종류만
                # 비차단 경고로 강등(나머지 종류는 그대로 차단). 새/수정 덱은
                # 강등 없음 → 완전 차단. (정본 목록 = _validate_layout.GRANDFATHERED_INTERNAL_GAP)
                try:
                    src_rel = str(html_path.relative_to(ROOT)).replace("\\", "/")
                except ValueError:
                    src_rel = ""
                if issues and src_rel in GRANDFATHERED_INTERNAL_GAP:
                    gf = [it for it in issues if it.get("kind") == "large_internal_gap"]
                    issues = [it for it in issues if it.get("kind") != "large_internal_gap"]
                    if gf:
                        print(f"  ⚠️  {kind}/{slug}: {len(gf)} grandfathered large_internal_gap "
                              f"(non-blocking, pre-existing 부채): {gf}", file=sys.stderr)
                if issues:
                    failures.append(f"{kind}/{slug}: layout issues → {issues}")
                    ctx.close()
                    continue
                # WCAG contrast ADVISORY (non-blocking, design-untouched).
                # Flags only SMALL visible text below 4.5:1 — large/bold/accent
                # text is exempt. Prints warnings to the build log; never fails
                # the build, never changes any color.
                try:
                    low_contrast = page.evaluate(CONTRAST_ADVISORY_JS)
                except Exception as exc:  # advisory must never break the build
                    low_contrast = []
                    print(f"  ⚠️  {kind}/{slug}: contrast advisory skipped ({exc})",
                          file=sys.stderr)
                for w in low_contrast:
                    print(
                        f"  ⚠️  low-contrast: '{w.get('snippet','')}' "
                        f"{w.get('ratio','?')}:1 (<4.5) — {w.get('selector','')}",
                        file=sys.stderr,
                    )
                # OPTIONAL QR decode (only if OpenCV is present — no new deps).
                # Screenshots the rendered handout QR and decodes it; if decode
                # succeeds and the payload doesn't match the URL we encoded, fail
                # loudly (a real mis-injection). If decode fails (rasterisation /
                # library quirk), just warn — we already asserted the <svg> is
                # non-empty above, so this is belt-and-suspenders only.
                if kind != "lab-reports" and qr_class == "qr-mini__code":
                    dec_err = _decode_qr_matches(page, qr_class, target_url)
                    if dec_err is True:
                        pass  # decoded and matched
                    elif isinstance(dec_err, str):
                        failures.append(f"{kind}/{slug}: {dec_err}")
                        ctx.close()
                        continue
                    # dec_err is None → decode unavailable/inconclusive → skip
                render(
                    page,
                    f"file://{build_file}",
                    out_pdf=OUT / kind / f"{slug}.pdf",
                    out_preview=OUT / kind / f"{slug}-preview.png",
                    fmt=fmt,
                )
                ctx.close()
                if kind == "lab-reports":
                    print(f"  ✓ {kind}/{slug}  →  no QR (privacy), noindex")
                else:
                    print(f"  ✓ {kind}/{slug}  →  QR: {target_url}")
            except Exception as e:
                # Render error/timeout (incl. 45s networkidle stall): record which
                # deck and keep going instead of hanging/crashing the whole build.
                failures.append(
                    f"{kind}/{slug}: render error/timeout → {type(e).__name__}: {str(e)[:120]}"
                )
                try:
                    ctx.close()
                except Exception:
                    pass
                continue
            finally:
                pass  # raw index.html keeps QR svg — desired for live site

            # Notion sync (best effort — never fails the build)
            # Routes by `kind` to one of three DBs (see SKILL.md "Notion DB 라우팅"):
            # - decks/handouts use {title, category, audience, [disease]}
            # - lab-reports use {patient_name, chart_no, exam_date, doctor, [note]}
            #   OR legacy title "[1063] 김종혁 — 골 대사 검사" (auto-parsed in _notion_sync)
            notion_sync = t.get("notion_sync", True)
            sync_eligible = notion_sync and (
                (
                    kind == "lab-reports" and ("patient_name" in t or "title" in t)
                ) or (
                    kind in ("decks", "handouts") and "title" in t
                )
            )
            if NOTION_ENABLED and sync_eligible:
                pdf_url = f"{BASE_URL}/output/{kind}/{slug}.pdf"
                # 최종수정일 = date the material's *content* (visible text +
                # images) last changed in git — CSS/layout-only commits are
                # ignored. Not today, so a rebuild/restyle doesn't restamp rows.
                modified_iso = (
                    content_last_modified_iso(
                        str(t["html_path"].relative_to(ROOT)), today_iso
                    )
                    if kind in ("decks", "handouts")
                    else None
                )
                try:
                    action, page_id = notion_upsert(
                        kind=kind,
                        slug=slug,  # lab-reports: dedup by slug-in-URL
                        html_url=target_url,
                        pdf_url=pdf_url,
                        today_iso=today_iso,
                        modified_iso=modified_iso,
                        version=t.get("version", "v1.0"),
                        status=t.get("status", ACTIVE_STATUS),
                        # decks / handouts
                        title=t.get("title"),
                        category=t.get("category"),
                        audience=t.get("audience"),
                        disease=t.get("disease"),
                        note=t.get("note"),
                        # lab-reports (explicit fields override legacy title parse)
                        patient_name=t.get("patient_name"),
                        chart_no=t.get("chart_no"),
                        exam_date=t.get("exam_date"),
                        doctor=t.get("doctor"),
                    )
                    print(f"      Notion {action}: {page_id}")
                except Exception as e:  # noqa: BLE001
                    notion_failures.append(f"{kind}/{slug}: {e}")

        browser.close()

    print()
    print("=== Build artifacts ===")
    for f in sorted(OUT.rglob("*")):
        if f.is_file():
            rel = f.relative_to(OUT)
            print(f"  {rel}: {f.stat().st_size / 1024:.1f} KB")

    if NOTION_ENABLED:
        ok = len(TARGETS) - len(notion_failures)
        print()
        print(f"=== Notion sync: {ok}/{len(TARGETS)} ok ===")
        for line in notion_failures:
            print(f"  ⚠️  {line}", file=sys.stderr)
    else:
        print()
        print("=== Notion sync: SKIPPED (NOTION_TOKEN not set) ===")

    if failures:
        print()
        print("=== Failures (deploy continues for successful items) ===", file=sys.stderr)
        for line in failures:
            print(f"  ✗ {line}", file=sys.stderr)
            print(f"::error::build failure: {line}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
