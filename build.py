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
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT / "shared"))
from _build_helpers import (  # noqa: E402
    make_qr_svg,
    inject_qr,
    render,
    check_og_meta,
)
from _validate_layout import HANDOUT_VALIDATOR_JS, DECK_VALIDATOR_JS  # noqa: E402

NOTION_ENABLED = bool(os.environ.get("NOTION_TOKEN"))
if NOTION_ENABLED:
    from _notion_sync import upsert as notion_upsert  # noqa: E402

OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
for sub in ("decks", "handouts", "lab-reports"):
    (OUT / sub).mkdir(exist_ok=True)

# Hosting base URL — change once here when GitHub Pages URL is finalized
BASE_URL = "https://gwanggyo-barun.github.io/patient-education"


# Each target dict carries everything needed to build + sync to Notion.
# Required: kind, slug, slug_path, html_path, qr_class, fmt
# Notion (optional but recommended): title, category, audience, disease
TARGETS = [
    # === 16:9 multi-slide decks ===
    {
        "kind": "decks", "slug": "gerd",
        "slug_path": "decks/gi/gerd/lifestyle/",
        "html_path": ROOT / "decks/gi/gerd/lifestyle/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "역류성 식도염 생활관리",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "GERD (역류성 식도염)",
    },
    {
        "kind": "decks", "slug": "hpylori",
        "slug_path": "decks/gi/h-pylori/eradication/",
        "html_path": ROOT / "decks/gi/h-pylori/eradication/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "헬리코박터 제균 치료 안내",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "H. pylori",
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

    # === A4 portrait single-page handouts ===
    {
        "kind": "handouts", "slug": "colonoscopy",
        "slug_path": "handouts/gi/colonoscopy/",
        "html_path": ROOT / "handouts/gi/colonoscopy/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "대장내시경 전 준비 안내",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "대장내시경",
    },
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
        "kind": "lab-reports", "slug": "박형주",
        "slug_path": "lab-reports/diabetes-screening/박형주/",
        "html_path": ROOT / "lab-reports/diabetes-screening/박형주/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "박형주 공단검진 결과 (2026-05-06)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "당뇨 신규진단",
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
        "kind": "decks", "slug": "chest-pain",
        "slug_path": "decks/cardio/chest-pain/",
        "html_path": ROOT / "decks/cardio/chest-pain/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        "title": "흉통 환자교육",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "흉통 (Chest Pain)",
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
        "title": "진료설명 — 헬리코박터 파일로리",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "헬리코박터 파일로리 (Helicobacter pylori)",
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
        "kind": "handouts", "slug": "hypertension-intake",
        "slug_path": "handouts/forms/hypertension-intake/",
        "html_path": ROOT / "handouts/forms/hypertension-intake/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "고혈압 초진 설문지",
        "category": "📝 동의서·서식", "audience": "환자/보호자", "disease": "고혈압 초진 설문지",
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
    },
    {
        "kind": "handouts", "slug": "diabetes-intake",
        "slug_path": "handouts/forms/diabetes-intake/",
        "html_path": ROOT / "handouts/forms/diabetes-intake/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "당뇨병 초진 설문지",
        "category": "📝 동의서·서식", "audience": "환자/보호자", "disease": "당뇨병 초진 설문지",
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
        "kind": "handouts", "slug": "glp1-intake",
        "slug_path": "handouts/forms/glp1-intake/",
        "html_path": ROOT / "handouts/forms/glp1-intake/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "💉 GLP-1 수용체 작용제(마운자로/위고비) 초진 문진표",
        "category": "📝 동의서·서식", "audience": "환자/보호자", "disease": "💉 GLP-1 수용체 작용제(마운자로/위고비) 초진 문진표",
    },
    {
        "kind": "handouts", "slug": "chronic-disease-intake",
        "slug_path": "handouts/forms/chronic-disease-intake/",
        "html_path": ROOT / "handouts/forms/chronic-disease-intake/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "만성질환 초진 설문지",
        "category": "📝 동의서·서식", "audience": "환자/보호자", "disease": "만성질환 초진 설문지",
    },
    # === Migration: 11 new patient lab reports (2026-05-08) ===
    {
        "kind": "lab-reports", "slug": "김종혁",
        "slug_path": "lab-reports/bone-metabolism/김종혁/",
        "html_path": ROOT / "lab-reports/bone-metabolism/김종혁/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[1063] 김종혁 — 골 대사 검사 (2026-04-29)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "골다공증·골대사",
    },
    {
        "kind": "lab-reports", "slug": "김현아",
        "slug_path": "lab-reports/bone-metabolism/김현아/",
        "html_path": ROOT / "lab-reports/bone-metabolism/김현아/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[4693] 김현아 — 골 대사 검사 (2026-04-28)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "골다공증·골대사",
    },
    {
        "kind": "lab-reports", "slug": "오완영",
        "slug_path": "lab-reports/comprehensive-summary/오완영/",
        "html_path": ROOT / "lab-reports/comprehensive-summary/오완영/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[12784] 오완영 — 종합 검진 요약 (2026-04-29)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "종합 검진",
    },
    {
        "kind": "lab-reports", "slug": "정행년",
        "slug_path": "lab-reports/comprehensive-summary/정행년/",
        "html_path": ROOT / "lab-reports/comprehensive-summary/정행년/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[12357] 정행년 — 종합 검진 요약 (2026-04-21)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "종합 검진",
    },
    {
        "kind": "lab-reports", "slug": "김양수",
        "slug_path": "lab-reports/cv-screening/김양수/",
        "html_path": ROOT / "lab-reports/cv-screening/김양수/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[27474] 김양수 — 심혈관 위험 평가 (2026-04-21)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "심혈관 위험",
    },
    {
        "kind": "lab-reports", "slug": "안미흥",
        "slug_path": "lab-reports/cv-screening/안미흥/",
        "html_path": ROOT / "lab-reports/cv-screening/안미흥/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[11960] 안미흥 — 심혈관 위험 평가 (2026-04-28)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "심혈관 위험",
    },
    {
        "kind": "lab-reports", "slug": "전상영",
        "slug_path": "lab-reports/cv-screening/전상영/",
        "html_path": ROOT / "lab-reports/cv-screening/전상영/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[8223] 전상영 — 심혈관 위험 평가 (2026-04-28)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "심혈관 위험",
    },
    {
        "kind": "lab-reports", "slug": "김경태",
        "slug_path": "lab-reports/diabetes-screening/김경태/",
        "html_path": ROOT / "lab-reports/diabetes-screening/김경태/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[2555] 김경태 — 당뇨 검진 결과 (2026-04-22)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "당뇨병",
    },
    {
        "kind": "lab-reports", "slug": "김양미",
        "slug_path": "lab-reports/diabetes-screening/김양미/",
        "html_path": ROOT / "lab-reports/diabetes-screening/김양미/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[15870] 김양미 — 당뇨 검진 결과 (2026-04-29)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "당뇨병",
    },
    {
        "kind": "lab-reports", "slug": "이강성",
        "slug_path": "lab-reports/diabetes-screening/이강성/",
        "html_path": ROOT / "lab-reports/diabetes-screening/이강성/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[13305] 이강성 — 당뇨 검진 결과 (2026-04-22)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "당뇨병",
    },
    {
        "kind": "lab-reports", "slug": "윤종철",
        "slug_path": "lab-reports/urinalysis/윤종철/",
        "html_path": ROOT / "lab-reports/urinalysis/윤종철/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "[1683] 윤종철 — 소변 검사 (2026-04-21)",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "소변 검사 이상",
    },
    {
        # 신규 schema 예시 — explicit 환자 메타데이터 (lab-reports 권장 형식)
        "kind": "lab-reports", "slug": "박순정",
        "slug_path": "lab-reports/general-checkup/박순정/",
        "html_path": ROOT / "lab-reports/general-checkup/박순정/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "patient_name": "박순정", "chart_no": "17492",
        "exam_date": "2026-05-08", "doctor": "정지환",
        "note": "종합검사 — 콜레스테롤 경계역",
    },
]


def main() -> int:
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

            missing = check_og_meta(html, slug)
            if missing:
                failures.append(f"{kind}/{slug}: missing meta → {', '.join(missing)}")
                continue

            qr_svg = make_qr_svg(target_url)
            injected = inject_qr(html, qr_svg, target_class=qr_class)

            # Write QR-injected HTML to the raw index.html so the live site
            # (GH Pages) also gets the QR — not only the PDF.
            html_path.write_text(injected, encoding="utf-8")
            build_file = html_path  # PDF builder uses the same file

            try:
                viewport = (
                    {"width": 1320, "height": 800}
                    if fmt == "deck-16x9"
                    else {"width": 820, "height": 1160}
                )
                ctx = browser.new_context(viewport=viewport)
                page = ctx.new_page()
                page.goto(f"file://{build_file}")
                page.wait_for_load_state("networkidle")
                # Layout validation BEFORE rendering — catch overflows/overlaps
                validator_js = DECK_VALIDATOR_JS if fmt == "deck-16x9" else HANDOUT_VALIDATOR_JS
                issues = page.evaluate(validator_js)
                if issues:
                    failures.append(f"{kind}/{slug}: layout issues → {issues}")
                    ctx.close()
                    continue
                render(
                    page,
                    f"file://{build_file}",
                    out_pdf=OUT / kind / f"{slug}.pdf",
                    out_preview=OUT / kind / f"{slug}-preview.png",
                    fmt=fmt,
                )
                ctx.close()
                print(f"  ✓ {kind}/{slug}  →  QR: {target_url}")
            finally:
                pass  # raw index.html keeps QR svg — desired for live site

            # Notion sync (best effort — never fails the build)
            # Routes by `kind` to one of three DBs (see SKILL.md "Notion DB 라우팅"):
            # - decks/handouts use {title, category, audience, [disease]}
            # - lab-reports use {patient_name, chart_no, exam_date, doctor, [note]}
            #   OR legacy title "[1063] 김종혁 — 골 대사 검사" (auto-parsed in _notion_sync)
            sync_eligible = (
                kind == "lab-reports" and ("patient_name" in t or "title" in t)
            ) or (
                kind in ("decks", "handouts") and "title" in t
            )
            if NOTION_ENABLED and sync_eligible:
                pdf_url = f"{BASE_URL}/output/{kind}/{slug}.pdf"
                try:
                    action, page_id = notion_upsert(
                        kind=kind,
                        html_url=target_url,
                        pdf_url=pdf_url,
                        today_iso=today_iso,
                        # decks / handouts
                        title=t.get("title"),
                        category=t.get("category"),
                        audience=t.get("audience"),
                        disease=t.get("disease"),
                        # lab-reports (explicit fields override legacy title parse)
                        patient_name=t.get("patient_name"),
                        chart_no=t.get("chart_no"),
                        exam_date=t.get("exam_date"),
                        doctor=t.get("doctor"),
                        note=t.get("note"),
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
        print("=== Failures ===", file=sys.stderr)
        for line in failures:
            print(f"  ✗ {line}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
