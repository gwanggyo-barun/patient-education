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
    inject_noindex_meta,
    render,
    check_og_meta,
    strip_qr_mini_block,
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
        "kind": "handouts", "slug": "urine-collection",
        "slug_path": "handouts/screening/urine-collection/",
        "html_path": ROOT / "handouts/screening/urine-collection/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "소변검사 채뇨 안내",
        "category": "🩺 일반내과", "audience": "환자/보호자", "disease": "소변검사 채뇨",
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
        "kind": "handouts", "slug": "htn-why-start",
        "slug_path": "handouts/medication/htn-why-start/",
        "html_path": ROOT / "handouts/medication/htn-why-start/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "💊 고혈압 약, 미루지 말아야 하는 이유 — 합병증 예방·감량 로드맵",
        "category": "💊 투약 안내", "audience": "환자/보호자",
        "disease": "고혈압 약물 치료의 목적(혈관 합병증 예방) 안내 — 운동·영양제·체중감량으로 약 시작을 미루려는 환자 대상. 5대 합병증 인포그래픽(뇌·눈·심장·대혈관·신장), 흔한 오해 vs 사실, 약 감량·중단 3단계 로드맵.",
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
        "kind": "lab-reports", "slug": "19f7fad6a4",
        "slug_path": "lab-reports/comprehensive-summary/19f7fad6a4/",
        "html_path": ROOT / "lab-reports/comprehensive-summary/19f7fad6a4/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "종합 검진",
        "patient_name": "김수홍", "chart_no": "97",
        "exam_date": "2026-05-09", "doctor": "정지환",
        "note": "요산 8.6 ↑ (저퓨린 식이) · TSH 4.98 ↑ (불현성 갑상선 저하 — 추적)",
    },
]


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
    # Pre-flight: validate kind routing — fail fast on misclassified TARGETS
    routing_issues = _validate_targets_routing()
    if routing_issues:
        print("=== TARGETS routing errors (fix before build) ===", file=sys.stderr)
        for issue in routing_issues:
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
                if kind == "lab-reports":
                    print(f"  ✓ {kind}/{slug}  →  no QR (privacy), noindex")
                else:
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
                        slug=slug,  # lab-reports: dedup by slug-in-URL
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
