# PromptOps System — 광교바른내과 의료 콘텐츠 자산 시스템

> 2026-05-25 사용자 명시. 단순 프롬프트 저장이 아닌 **재사용·버전관리·브랜드 일관성·회귀 테스트·교차 모델 사용·Notion/YAML 변환 가능**한 구조화된 의료 콘텐츠 자산 시스템.

## 1. SYSTEM ARCHITECTURE

### 6-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       Skill                             │
│  (entry point — kind + topic + audience 지정)          │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│                     Template                            │
│  (12장 deck / A4 handout / lab-report 등 layout 골격)  │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Reusable Blocks                        │
│  (fasting-warning · anticoagulant · brand-color 등)     │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│                       Tests                             │
│  (must_include · forbidden · safety_rules 자동 검증)   │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│                       Assets                            │
│  (이미지·SVG·로고·QR — provenance 추적)                │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Output Archive                         │
│  (PDF·HTML·PNG — 버전 관리 + Notion DB sync)           │
└─────────────────────────────────────────────────────────┘
```

### 각 레이어 역할

| 레이어 | 역할 | 디렉터리 | 변경 빈도 |
|---|---|---|---|
| **Skill** | 사용자 의도 → 콘텐츠 종류 라우팅 | `skills/*.yaml` | 분기 |
| **Template** | 12장 구성·1장 layout·footer 등 골격 | `templates/*.yaml` | 월 |
| **Reusable Blocks** | 공통 텍스트·CSS·이미지·QR 패턴 | `blocks/*.yaml` | 주 |
| **Tests** | 자동 검증 룰 (clinical accuracy 포함) | `tests/*.yaml` | 분기 |
| **Assets** | 이미지·SVG·로고·icon | `assets/generated/` | 일 |
| **Output Archive** | 생산된 PDF·HTML 보관 | `output/` + Git | 일 |

### 의존성 그래프

- Skill은 1개 Template + N개 Reusable Blocks + N개 Tests 참조
- Template은 N개 Reusable Blocks 참조
- Tests는 다른 layer에 의존하지 않음 (독립 검증)
- Assets는 Skill·Template·Blocks 어디서나 참조 가능

---

## 2. MASTER YAML SCHEMA

### Production-grade Skill YAML 스키마

```yaml
# skills/egd-fasting.yaml
prompt_id: GBIM-skill-egd-fasting-v03      # globally unique
title: 위내시경 금식 안내                    # 한국어 표시명
category: endoscopy                          # 카테고리 트리 §3
subcategory: pre-procedure                   # 하위 카테고리
persona: clinician-internal-medicine         # 사용자 페르소나
task_type: handout                           # deck / handout / lab-report
output_format: a4-portrait                   # a4-portrait / 16x9 / 1080x1080
expected_length:
  pages: 1
  word_count_range: [180, 350]               # 한국어 글자 수
  slide_count: null                          # deck 시 12
tags:                                        # §4 태그
  - a4
  - patient-friendly
  - korean
  - print-ready
  - infographic
  - no-text-in-image
brand_profile: gwanggyo-bareun-print-v1      # §7
image_constraints:
  style: flat-medical
  palette: [navy-003366, steel-blue-5B9BD5]
  no_text: true
  aspect_ratio: strict-measured              # 슬롯 측정 후 결정
  min_dpi: 300                               # 인쇄용
temperature: 0.3                             # 의료 콘텐츠 보수
model_family:                                # 교차 모델 우선순위
  primary: claude-opus-4-7
  fallback: claude-sonnet-4-6
  alt_provider: gpt-4o
reusable_blocks:                             # §5 참조 블록
  - fasting-warning-standard
  - sedation-aftercare-standard
  - anticoagulant-warning
  - clinic-contact-footer
  - brand-color-palette
test_inputs:                                 # §6 테스트 입력 샘플
  - case_id: T01-routine
    patient_age: 55
    sedation: true
    anticoagulant: false
  - case_id: T02-anticoagulant
    patient_age: 70
    sedation: true
    anticoagulant: true
expected_outputs:                            # §6 기대 출력
  - case_id: T01-routine
    must_include:
      - "8시간 금식"
      - "물 한 모금 가능"
      - "검사 당일 보호자 동반"
    forbidden_terms:
      - "12시간 금식"
      - "물 절대 금지"
safety_level: high                           # low / medium / high / critical
version: v03                                 # SemVer-like
created_at: 2026-05-13T09:00:00+09:00
updated_at: 2026-05-25T12:00:00+09:00
authors:
  - 정지환                                    # 의사
  - claude-opus-4-7                          # AI co-author
license: GBIM-internal-v1                    # §LICENSE
notion_sync:
  enabled: true
  db_id: 920b48c92d674186a370afcaa81ce788    # handouts DB
  category_select: "🏥 내시경 관련"
```

### 필드별 설명

| 필드 | 타입 | 설명 |
|---|---|---|
| `prompt_id` | string | `GBIM-{layer}-{slug}-{version}` 전역 고유 |
| `title` | string | 한국어 표시명 |
| `category` | string | §3 카테고리 트리 leaf |
| `subcategory` | string | 카테고리 하위 |
| `persona` | string | `clinician-*` / `patient-*` / `staff-*` |
| `task_type` | enum | `deck` / `handout` / `lab-report` / `banner` / `pptx-export` |
| `output_format` | enum | `a4-portrait` / `16x9` / `1080x1080` / `web-1920` |
| `expected_length` | object | pages·word_count·slide_count |
| `tags` | array | §4 표준 태그 |
| `brand_profile` | string | §7 브랜드 프로필 ID |
| `image_constraints` | object | 이미지 스타일·팔레트·DPI·비율 |
| `temperature` | float | LLM 온도 (의료는 0.2-0.4) |
| `model_family` | object | primary·fallback·alt_provider |
| `reusable_blocks` | array | §5 참조 블록 ID 리스트 |
| `test_inputs` | array | §6 테스트 케이스 입력 |
| `expected_outputs` | array | §6 케이스별 must_include·forbidden |
| `safety_level` | enum | `low` / `medium` / `high` / `critical` |
| `version` | string | `v01`, `v02`, ... (SemVer-like) |
| `created_at` · `updated_at` | ISO-8601 | 자동 갱신 |
| `authors` | array | 의사 + AI 모델 명시 |
| `license` | string | §저작권 LICENSE 참조 |
| `notion_sync` | object | DB 자동 sync 활성·DB ID |

---

## 3. CATEGORY SYSTEM

### 의료 콘텐츠 카테고리 트리

```
clinic
├── general
│   ├── intake-forms
│   ├── consent-forms
│   └── clinic-overview
├── imaging
│   ├── ct
│   ├── mri
│   ├── ultrasound
│   │   ├── abdominal
│   │   ├── thyroid
│   │   ├── carotid
│   │   └── cardiac
│   ├── xray
│   └── dxa
├── endoscopy
│   ├── pre-procedure        # 금식·약 중단·교육
│   ├── procedure-day        # 당일 안내·동의
│   ├── post-procedure       # 회복·식이·운전 금지
│   └── biopsy
├── patient-education
│   ├── chronic-disease      # 만성질환 (HTN·DM·CKD)
│   ├── acute-illness        # 급성질환 (URI·gastroenteritis)
│   ├── prevention           # 예방 (백신·암검진)
│   ├── lifestyle            # 생활습관
│   └── medication-info      # 약물 안내
├── nutrition
│   ├── diet-counseling      # 식단 상담
│   ├── ibs-fodmap
│   ├── dash-diet
│   ├── diabetic-meal
│   └── weight-management
├── injections
│   ├── glp-1                # GLP-1 주사 교육
│   ├── insulin              # 인슐린 시작·교환
│   ├── vaccines
│   └── b12
├── operations               # 의원 운영
│   ├── schedule             # 휴진·시간 변경
│   ├── pricing              # 비급여 가격
│   ├── staff-training       # 직원 교육
│   └── emergency            # 응급 대응 (CPR 등)
├── finance                  # 비용·보험
│   ├── nhi-coverage         # 건강보험
│   ├── private-insurance    # 실손보험
│   └── non-covered-services # 비급여
├── photography              # 환자 사진 (피부·구강 등)
│   ├── consent
│   └── workflow
└── paper-reviews            # 논문 리뷰
    ├── daily-top5
    ├── thematic
    └── guideline-update
```

### Subcategory 명명 규칙

- 한 단어 또는 hyphen 두 단어 (`pre-procedure`)
- 동사형보다 명사형 (`fasting-guide` not `tell-fasting`)
- 환자 친화어 X, 의학 용어 OK (`ibs-fodmap` not `장-관리`)

### Notion select option 매핑

각 leaf는 Notion DB의 `카테고리` select option과 1:1 매핑:
- `endoscopy/pre-procedure` → `🏥 내시경 관련`
- `nutrition/diet-counseling` → `🌿 생활습관·식이`
- `paper-reviews/daily-top5` → `📰 논문 리뷰`

---

## 4. TAGGING CONVENTION

### 표준 태그 분류

#### Layout / Format
- `a4` · `a4-portrait` · `a4-landscape`
- `16x9` · `deck-16x9`
- `1080x1080` · `sns-card`
- `web-banner` · `web-1920`
- `2-page` · `multi-page`

#### Style
- `flat-vector` · `medical-illustration`
- `infographic` · `data-viz`
- `minimalist` · `text-heavy`
- `pretendard-font`
- `navy-steel-palette`

#### Audience
- `patient-friendly` · `physician-only` · `nurse-readable`
- `senior-readable` (큰 폰트·간단 어휘) · `pediatric`
- `family-readable`

#### Locale
- `korean` · `english` · `bilingual`
- `kor-formal` (존댓말) · `kor-informal`

#### Content Constraints
- `no-text-in-image` (HTML overlay 전용)
- `print-ready` (300 DPI 인쇄용)
- `web-only` (스크린)
- `qr-included` · `qr-mini`
- `redacted-pii` (lab-reports)

#### Safety / Compliance
- `safety-high` · `safety-critical`
- `requires-physician-review`
- `has-warning-block`
- `medication-info` (약물 명시)

#### Process
- `draft` · `reviewed` · `approved` · `published` · `archived`
- `ai-assisted` · `ai-only` · `human-only`
- `regression-tested`

### 태그 적용 규칙

- 모든 Skill에 **최소 5개 태그** (layout 1 + style 1 + audience 1 + locale 1 + process 1)
- 다중 audience 가능 (`patient-friendly` + `senior-readable`)
- 태그 추가는 본 문서 update + repo commit 필수 (다른 머신 동기화)

---

## 5. REUSABLE BLOCK SYSTEM

### 블록 명명 규칙

`{domain}-{purpose}-{variant}.yaml`

예: `fasting-warning-standard.yaml`, `anticoagulant-warning-egd.yaml`

### 표준 블록 카탈로그

#### 의료 안전 경고 블록
- `fasting-warning-standard` — 일반 금식 (8시간)
- `fasting-warning-deep-sedation` — 깊은 진정 (12시간)
- `anticoagulant-warning-standard` — 항응고제 일반
- `anticoagulant-warning-noac` — DOAC 특화
- `sedation-aftercare-standard` — 진정 후 24h 운전 금지
- `pregnancy-x-warning` — 임신 금기
- `lactation-caution` — 수유 주의

#### 시각 요소 블록
- `brand-color-palette` — Navy + Steel Blue 표준 토큰
- `pretendard-font-stack` — Pretendard CDN
- `qr-block-standard` — closing slide QR 144×144
- `qr-mini-footer` — handout footer 24×24
- `clinic-logo-header` — 좌상 로고 + chapter
- `slide-footer-standard` — 출처 + 페이지 번호

#### 콘텐츠 블록
- `clinic-contact-footer` — 광교바른내과 주소·연락처
- `take-home-4-cards` — 12장 deck closing 4 카드
- `red-flag-grid-6` — 응급 증상 6가지 alert tile
- `lifestyle-grid-6` — 생활관리 6가지 tile
- `medication-table-template` — 약물 비교 표

#### 데이터 시각화 블록
- `dose-response-bar-template` — bar chart (비례 검증 포함)
- `kaplan-meier-template` — survival curve
- `forest-plot-template` — meta-analysis forest plot
- `before-after-comparison`

### Block YAML 예시

```yaml
# blocks/fasting-warning-standard.yaml
block_id: fasting-warning-standard
version: v02
applies_to:
  - endoscopy/pre-procedure
  - imaging/ultrasound/abdominal
content:
  ko: |
    ⚠️ 검사 8시간 전부터 금식
    - 물 한 모금까지 가능 (검사 2시간 전까지)
    - 껌·사탕·담배 금지
    - 평소 약은 의사 지시에 따라
  en: |
    ⚠️ Fast for 8 hours before procedure
    - Small sips of water OK up to 2 hours before
    - No gum, candy, smoking
    - Medications per physician
visual_constraints:
  border: "4px solid #f59e0b"
  background: "#fff9e6"
  icon: "⚠️"
safety_check:
  must_include_korean:
    - "8시간 금식"
    - "물"
  forbidden_terms:
    - "12시간"      # deep sedation 시 별도 블록 사용
```

### Inheritance & Override

- 블록은 부모-자식 상속 가능: `fasting-warning-deep-sedation` extends `fasting-warning-standard`
- override 룰: 자식이 부모의 `content.ko` 전체 교체 (부분 override 금지 — 의료 안전)
- `visual_constraints` 는 부분 override 가능 (색상·border 조정)

---

## 6. REGRESSION TEST SYSTEM

### 테스트 구조

```yaml
# tests/egd-fasting-handout.test.yaml
test_id: egd-fasting-handout-v03
skill_ref: GBIM-skill-egd-fasting-v03
must_include:                       # 출력에 반드시 포함
  - "8시간"
  - "금식"
  - "물 한 모금"
  - "보호자 동반"
  - "광교바른내과"
forbidden_terms:                    # 출력에 절대 없어야 함
  - "12시간 금식"
  - "물 절대 금지"
  - "임의로 약 중단"
  - "의사 상의 없이"
style_rules:                        # 디자인 검증
  - rule: "Pretendard Variable 폰트 사용"
    check: "grep 'pretendardvariable' index.html"
  - rule: "Navy + Steel Blue 팔레트만"
    check: "no other hex colors in CSS"
  - rule: "QR mini footer 포함"
    check: "exists .qr-mini__code"
layout_rules:                       # 레이아웃 검증
  - rule: "A4 1페이지 (210×297mm)"
    check: "viewport=794"
  - rule: "Footer에 광교바른내과 + 출처"
    check: "footer contains '광교바른내과'"
  - rule: "본문 padding 14mm"
    check: "CSS padding: 14mm"
safety_rules:                       # 의료 안전성 검증 (critical)
  - rule: "항응고제 환자 별도 안내 X"
    check: "deep_sedation flag → 별도 블록 사용 강제"
    severity: blocker
  - rule: "임신 가능성 안내"
    check: "if female 15-50 → '임신 가능성 확인' 포함"
    severity: major
medical_accuracy:                   # 의학적 정확성
  - rule: "수술 전 항응고제 중단 시점 명시"
    check: "warfarin → '5일 전', DOAC → '24-48시간 전'"
    severity: major
  - rule: "용량·단위 정확"
    check: "약물 용량은 항상 단위 명시 (mg / g / mL)"
    severity: blocker
accessibility:                      # 접근성
  - rule: "본문 텍스트 최소 10pt"
    check: "font-size >= 10pt"
  - rule: "색상 대비 4.5:1 이상"
    check: "contrast ratio check"
brand_compliance:
  - rule: "로고 자르기·왜곡 금지"
    check: "logo aspect ratio preserved"
  - rule: "Navy #003366 정확 사용"
    check: "no other navy shade"
```

### 자동 검증 도구

```python
# tools/run_tests.py
def run_test(test_yaml_path, output_html_path):
    test = load_yaml(test_yaml_path)
    html = read(output_html_path)

    failures = []

    # 1. must_include
    for term in test.get("must_include", []):
        if term not in html:
            failures.append(("must_include", term, "blocker"))

    # 2. forbidden_terms
    for term in test.get("forbidden_terms", []):
        if term in html:
            failures.append(("forbidden", term, "blocker"))

    # 3. style_rules (regex/grep)
    for rule in test.get("style_rules", []):
        if not check_rule(rule, html):
            failures.append(("style", rule["rule"], "major"))

    # 4. safety_rules (medical critical)
    for rule in test.get("safety_rules", []):
        if not check_rule(rule, html):
            failures.append(("safety", rule["rule"], rule.get("severity", "blocker")))

    # 5. medical_accuracy
    for rule in test.get("medical_accuracy", []):
        if not check_rule(rule, html):
            failures.append(("medical", rule["rule"], rule.get("severity", "major")))

    return failures
```

### Severity 처리

- `blocker` → 빌드 실패, push 차단
- `major` → 경고 로그, 빌드 통과 (사용자 검토 후 commit 가능)
- `minor` → 정보 로그만
- `nit` → 보고만

### CI/CD 통합

`.github/workflows/test-content.yml`:

```yaml
name: Content Regression Tests
on: [pull_request, push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 build.py
      - run: python3 tools/run_tests.py --all
      - name: Fail on blocker
        run: |
          if [ $(grep -c "blocker" test-results.log) -gt 0 ]; then
            exit 1
          fi
```

---

## 7. BRAND PROFILE SYSTEM

### Brand Profile YAML

```yaml
# brand-profiles/gwanggyo-bareun-v1.yaml
brand_id: gwanggyo-bareun-v1
display_name: 광교바른내과 (Gwanggyo Bareun Internal Medicine)
version: v1
effective_date: 2026-01-01

palette:
  primary:
    navy: "#003366"
    steel_blue: "#5B9BD5"
  neutral:
    white: "#FFFFFF"
    light_gray: "#F4F6F8"
    canvas_warm: "#FAF7F2"
    border: "#E5E8EB"
    ink: "#1c2025"
    ink_soft: "#4e5968"
    muted: "#8b95a1"
  accent:
    success: "#15803D"
    warning: "#F97316"
    danger: "#EF4444"
  reserved:
    # 사용 금지 색상 (브랜드 외 hex)
    - "#FF0000"   # 순빨강 X
    - "#0000FF"   # 순파랑 X

typography:
  primary: Pretendard Variable
  cdn: "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css"
  weights:
    regular: 450
    medium: 540
    bold: 700
    black: 900
  scale:
    h1: 32px
    h2: 24px
    h3: 18px
    body: 14px
    body_lg: 16px
    caption: 11px
  letter_spacing:
    tight: -0.02em
    snug: -0.01em
    normal: 0
    mega: -0.04em

spacing:
  base_unit: 4px
  scale: [0, 4, 8, 12, 16, 24, 32, 48, 64, 80, 120]  # space-0 ~ space-10

radius:
  none: 0
  sm: 4px
  md: 8px
  lg: 16px
  pill: 9999px

illustration_style:
  type: flat-medical
  preferred: vector  # SVG > raster
  no_3d: true
  no_skeuomorphism: true
  background: white-with-soft-gradient
  shadows: soft-only

icon_style:
  set: lucide-or-custom-svg
  stroke_width: 2px
  size_scale: [16, 20, 24, 32, 48]
  color: inherit-text  # currentColor

accessibility:
  min_contrast: 4.5:1
  min_font_size_print: 10pt
  min_font_size_screen: 13px
  alt_text_required: true

variants:                    # 미디어별 파생
  - id: gwanggyo-bareun-print-v1
    inherits: gwanggyo-bareun-v1
    overrides:
      typography.scale.body: 12pt
      radius.lg: 12px
  - id: gwanggyo-bareun-web-v1
    inherits: gwanggyo-bareun-v1
    overrides:
      shadows: soft-with-elevation
  - id: gwanggyo-bareun-sns-v1
    inherits: gwanggyo-bareun-v1
    overrides:
      palette.primary.navy: "#001f44"   # SNS 대비 강화
```

### Variant 선택 룰

- `task_type == handout/lab-report` → `gwanggyo-bareun-print-v1`
- `task_type == deck` 게다가 web embed 우선 → `gwanggyo-bareun-web-v1`
- `task_type == banner` 또는 SNS card → `gwanggyo-bareun-sns-v1`

---

## 8. NOTION DATABASE DESIGN

### 추가 DB 설계 — PromptOps Skills DB

기존 3개 DB(decks·handouts·lab-reports) 외에 **Skill 자체** 관리용 DB 추가:

```
📋 PromptOps Skills DB
Page IDs: (신규 생성 필요)

Properties:
- 자료명 (title) — Skill 표시명
- prompt_id (text) — GBIM-skill-* 전역 ID
- 카테고리 (select) — clinic·imaging·endoscopy·...
- subcategory (text)
- 페르소나 (select) — clinician-internal-medicine·patient-friendly·...
- task_type (select) — deck·handout·lab-report·banner
- output_format (select) — a4-portrait·16x9·1080x1080·web-1920
- 태그 (multi_select) — §4 표준 태그
- 브랜드 프로필 (relation) → Brand Profiles DB
- safety_level (select) — low·medium·high·critical
- 버전 (text) — v01·v02·...
- 상태 (select) — draft·reviewed·approved·published·archived
- 모델 (multi_select) — claude-opus·claude-sonnet·gpt-4o·gemini
- 마지막 테스트 (date)
- 테스트 결과 (select) — pass·fail-blocker·fail-major
- reusable_blocks (multi_select)
- YAML URL (url) → GitHub raw file
- 생성일 (date) — created_at
- 수정일 (date) — updated_at
- 작성자 (people)
- AI 작성자 (text) — model name + session
- 노션 sync (checkbox)
- 비고 (rich_text)
```

### Filtering Strategy

| View | Filter | 용도 |
|---|---|---|
| 📂 전체 | (none) | 카탈로그 |
| ✅ 사용중 | 상태 == approved/published | 실무 자료 |
| 🚧 작업중 | 상태 == draft/reviewed | 진행 중 |
| 🚨 안전 위험 | safety_level == critical | 의사 검토 |
| 🤖 AI-only | 작성자 contains AI | AI 비중 추적 |
| 📅 최근 7일 | 수정일 >= now()-7d | 신규·변경 |
| 🩺 카테고리별 | groupBy 카테고리 | board view |

### Automation Ideas

- Skill YAML push 시 GitHub Action → Notion DB row upsert
- 테스트 실패 시 노션 row "테스트 결과" 자동 fail-blocker로 변경 + 슬랙 알림
- 매주 일요일 archive 후보 자동 발견 (상태=draft AND updated_at < 30일)

---

## 9. FILE STRUCTURE

### Recommended Repository Layout

```
~/clinic-content-system/
├── README.md
├── SKILL.md                              # 본 SoT (skill·workflow rules)
├── build.py                              # Playwright PDF·PNG 빌드
├── requirements.txt
│
├── skills/                               # § Skill YAML
│   ├── egd-fasting.yaml
│   ├── colonoscopy-prep.yaml
│   ├── ibs-fodmap-education.yaml
│   ├── glp1-injection-education.yaml
│   ├── abdominal-us-fasting.yaml
│   └── ...
│
├── templates/                            # § Template YAML
│   ├── deck-16x9-12slides.yaml
│   ├── handout-a4-single.yaml
│   ├── handout-a4-2page.yaml
│   ├── lab-report-a4.yaml
│   └── banner-web-1920.yaml
│
├── blocks/                               # § Reusable Blocks
│   ├── safety/
│   │   ├── fasting-warning-standard.yaml
│   │   ├── anticoagulant-warning.yaml
│   │   └── sedation-aftercare.yaml
│   ├── visual/
│   │   ├── brand-color-palette.yaml
│   │   ├── qr-block-standard.yaml
│   │   └── clinic-logo-header.yaml
│   ├── content/
│   │   ├── clinic-contact-footer.yaml
│   │   ├── take-home-4-cards.yaml
│   │   └── red-flag-grid-6.yaml
│   └── data-viz/
│       ├── dose-response-bar.yaml
│       └── kaplan-meier.yaml
│
├── tests/                                # § Regression Tests
│   ├── egd-fasting-handout.test.yaml
│   ├── colonoscopy-prep.test.yaml
│   ├── shared/
│   │   ├── brand-compliance.test.yaml
│   │   └── medical-accuracy-common.test.yaml
│   └── snapshots/                        # 기대 출력 스냅샷
│       ├── egd-fasting-T01.html
│       └── ...
│
├── brand-profiles/                       # § Brand Profile YAML
│   ├── gwanggyo-bareun-v1.yaml
│   ├── gwanggyo-bareun-print-v1.yaml
│   └── gwanggyo-bareun-sns-v1.yaml
│
├── decks/                                # 실제 HTML (Skill 출력)
│   ├── cardio/...
│   ├── general/papers-20260524/...
│   └── endocrine/...
│
├── handouts/
├── lab-reports/
│
├── shared/                               # 공통 CSS·헬퍼
│   ├── design-tokens.css
│   ├── clinic-slides.css
│   ├── clinic-handout-a4.css
│   ├── assets/
│   │   ├── clinic_logo.png
│   │   └── generated/
│   ├── _build_helpers.py
│   ├── _notion_sync.py
│   ├── _validate_layout.py
│   └── _visual_audit.py
│
├── reference/                            # § 디테일 문서
│   ├── brand-design-system.md
│   ├── patterns.md
│   ├── image-assets.md
│   ├── multi-agent-quality.md
│   ├── promptops-system.md               # 본 문서
│   ├── copyright-protection.md
│   └── content-template.md
│
├── output/                               # 빌드 산출물 (.gitignore)
│   ├── decks/
│   ├── handouts/
│   └── lab-reports/
│
├── archive/                              # 옛 버전 보관 (.gitignore)
│   └── 2025/
│       ├── decks/
│       └── handouts/
│
├── tools/                                # 자동화 스크립트
│   ├── run_tests.py
│   ├── sync_all_agents.sh
│   ├── sync_plugin_clone.sh
│   ├── pack_for_share.sh
│   ├── sync_to_nas.sh
│   ├── Watch-Export.ps1
│   └── verify_skill_sync.sh
│
├── _local/                               # 머신 종속 (gitignored)
│   ├── quality-logs/
│   ├── quality-prompts/
│   └── .env
│
└── evals/                                # 회귀 검증
    ├── README.md
    ├── synthetic/
    └── eval_runner.py
```

### .gitignore 주요 항목

```
output/
archive/
_local/
07_Prompts/
*.editable.svg
.DS_Store
__pycache__/
.env
```

---

## 10. REAL EXAMPLES (5개)

### 10-1. 위내시경 금식 안내

```yaml
# skills/egd-fasting.yaml
prompt_id: GBIM-skill-egd-fasting-v03
title: 위내시경 금식 안내
category: endoscopy
subcategory: pre-procedure
persona: patient-friendly
task_type: handout
output_format: a4-portrait
expected_length:
  pages: 1
  word_count_range: [180, 280]
tags: [a4, patient-friendly, korean, print-ready, infographic, no-text-in-image, safety-high, qr-mini]
brand_profile: gwanggyo-bareun-print-v1
image_constraints:
  style: flat-medical
  palette: [navy-003366, steel-blue-5B9BD5, warning-F97316]
  no_text: true
  aspect_ratio: strict-measured
  min_dpi: 300
temperature: 0.2
model_family:
  primary: claude-opus-4-7
  fallback: claude-sonnet-4-6
reusable_blocks:
  - fasting-warning-standard
  - sedation-aftercare-standard
  - anticoagulant-warning-standard
  - clinic-contact-footer
  - brand-color-palette
  - qr-mini-footer
test_inputs:
  - case_id: T01-routine
    patient_age: 55
    sedation: true
    anticoagulant: false
  - case_id: T02-anticoagulant
    patient_age: 70
    sedation: true
    anticoagulant: true
  - case_id: T03-no-sedation
    patient_age: 45
    sedation: false
expected_outputs:
  - case_id: T01-routine
    must_include: ["8시간 금식", "물 한 모금 가능", "보호자 동반"]
    forbidden_terms: ["12시간 금식", "임의로 약 중단"]
  - case_id: T02-anticoagulant
    must_include: ["항응고제", "주치의 상의", "warfarin 5일 전"]
safety_level: high
version: v03
license: GBIM-internal-v1
```

**테스트** `tests/egd-fasting.test.yaml`:
```yaml
must_include: ["8시간", "금식", "물 한 모금", "광교바른내과"]
forbidden_terms: ["12시간 금식", "물 절대 금지", "임의로 약 중단"]
safety_rules:
  - rule: "항응고제 환자 별도 안내"
    severity: blocker
```

---

### 10-2. 대장내시경 장정결 안내

```yaml
# skills/colonoscopy-prep.yaml
prompt_id: GBIM-skill-colonoscopy-prep-v04
title: 대장내시경 장정결 안내
category: endoscopy
subcategory: pre-procedure
task_type: handout
output_format: a4-portrait
expected_length:
  pages: 1
  word_count_range: [220, 350]
tags: [a4, patient-friendly, korean, print-ready, infographic, safety-high, has-warning-block]
brand_profile: gwanggyo-bareun-print-v1
reusable_blocks:
  - fasting-warning-deep-sedation        # 깊은 진정용
  - bowel-prep-schedule-2day
  - bowel-prep-fluids-allowed
  - bowel-prep-stool-clarity-check
  - anticoagulant-warning-standard
  - clinic-contact-footer
test_inputs:
  - case_id: T01-pm-procedure
    procedure_time: PM
    patient_age: 60
  - case_id: T02-am-procedure
    procedure_time: AM
    patient_age: 65
expected_outputs:
  - case_id: T01-pm-procedure
    must_include: ["전날 저녁 6시", "맑은 물 같은 변", "노란 액체"]
    forbidden_terms: ["검은 변", "고형 변 OK"]
safety_level: high
version: v04
```

---

### 10-3. IBS 식단 교육 (FODMAP)

```yaml
# skills/ibs-fodmap-education.yaml
prompt_id: GBIM-skill-ibs-fodmap-v02
title: 과민성장증후군 (IBS) FODMAP 식단 교육
category: nutrition
subcategory: ibs-fodmap
task_type: deck
output_format: 16x9
expected_length:
  slide_count: 12
tags: [16x9, patient-friendly, korean, deck-16x9, infographic, medication-info]
brand_profile: gwanggyo-bareun-web-v1
reusable_blocks:
  - brand-color-palette
  - take-home-4-cards
  - fodmap-food-grid-high
  - fodmap-food-grid-low
  - elimination-reintroduction-timeline
test_inputs:
  - case_id: T01-mixed-ibs
    subtype: mixed
    severity: moderate
  - case_id: T02-diarrhea-predominant
    subtype: ibs-d
    severity: severe
expected_outputs:
  - case_id: T01-mixed-ibs
    must_include: ["3단계", "elimination", "reintroduction", "Monash University"]
    forbidden_terms: ["완치 가능", "평생 모든 음식 금지"]
safety_level: medium
version: v02
```

---

### 10-4. 복부초음파 금식 안내

```yaml
# skills/abdominal-us-fasting.yaml
prompt_id: GBIM-skill-abdominal-us-fasting-v01
title: 복부초음파 금식 안내
category: imaging
subcategory: ultrasound/abdominal
task_type: handout
output_format: a4-portrait
expected_length:
  pages: 1
tags: [a4, patient-friendly, korean, print-ready, infographic]
brand_profile: gwanggyo-bareun-print-v1
reusable_blocks:
  - fasting-warning-standard          # 8h
  - water-allowed-up-to-2h
  - smoking-no-gum-warning
  - clinic-contact-footer
test_inputs:
  - case_id: T01-morning
    procedure_time: AM
  - case_id: T02-afternoon
    procedure_time: PM
expected_outputs:
  - case_id: T01-morning
    must_include: ["전날 저녁 9시", "물 가능", "검사 2시간 전까지"]
    forbidden_terms: ["껌·사탕 OK"]
safety_level: medium
version: v01
```

---

### 10-5. GLP-1 주사 교육

```yaml
# skills/glp1-injection-education.yaml
prompt_id: GBIM-skill-glp1-injection-v02
title: GLP-1 주사 (오젬픽·위고비·맙젠다) 자가 주사 교육
category: injections
subcategory: glp-1
task_type: deck
output_format: 16x9
expected_length:
  slide_count: 12
tags: [16x9, patient-friendly, korean, deck-16x9, infographic, medication-info, safety-high]
brand_profile: gwanggyo-bareun-web-v1
image_constraints:
  no_text: true
  required_anatomy: ["injection-site-abdomen", "injection-site-thigh"]
reusable_blocks:
  - brand-color-palette
  - glp1-injection-sites-anatomy
  - glp1-titration-schedule
  - glp1-side-effects-grid
  - glp1-storage-rules
  - clinic-contact-footer
  - emergency-warning-block
test_inputs:
  - case_id: T01-first-time
    patient_first_injection: true
    drug: semaglutide
  - case_id: T02-switching
    patient_first_injection: false
    drug: tirzepatide
    previous_drug: liraglutide
expected_outputs:
  - case_id: T01-first-time
    must_include: ["복부", "허벅지", "90도", "주 1회"]
    forbidden_terms: ["근육 주사", "동일 부위 매번 같은 곳"]
  - case_id: T02-switching
    must_include: ["전환", "새 약 시작 용량"]
    forbidden_terms: ["이전 약 용량 그대로"]
safety_level: high
version: v02
```

---

## 11. FUTURE EXPANSION

### Phase 1 — Foundation (현재 ~ 2026 Q3)

- [x] 본 PromptOps 시스템 설계 (2026-05-25)
- [ ] 5개 Skill YAML 실제 생성 + 테스트 통과 (다음 단계)
- [ ] 표준 블록 카탈로그 30+ 작성
- [ ] Brand Profile 3종 YAML 변환
- [ ] tools/run_tests.py 구현
- [ ] CI/CD GitHub Actions 통합

### Phase 2 — Cross-Model Support (2026 Q3-Q4)

- [ ] **Claude·GPT·Gemini 교차 호출 어댑터**
  - prompt YAML → 모델별 API 페이로드 자동 변환
  - 모델별 token 비용·latency 추적
- [ ] **Agent Workflow**
  - Stage A planning (4 specialist 병렬)
  - Stage D critique (4 specialist 병렬)
  - Stage F final verification
  - 모두 `tools/agent_pipeline.py`로 표준화
- [ ] **Auto prompt generation**
  - 기존 HTML deck → reverse engineer YAML
  - GPT/Claude로 새 prompt 자동 생성 + 검증

### Phase 3 — Scale & Automation (2027)

- [ ] **Batch infographic generation**
  - 1일 50+ deck 자동 생산 (RSS 논문 feed → Skill 적용)
  - LaunchAgent/Cron + Claude API
- [ ] **API integration**
  - 외부 EMR·진료·예약 시스템과 콘텐츠 자동 동기화
  - 환자별 맞춤 자료 자동 생성
- [ ] **CI/CD style prompt testing**
  - Pull request마다 모든 Skill regression test
  - 실패 시 자동 알림
- [ ] **Prompt version control**
  - Git tag 기반 SemVer
  - rollback 한 명령
  - A/B 테스트 (v02 vs v03 효과 측정)

### Phase 4 — Advanced (2027+)

- [ ] **Multi-tenant**: 다른 의원 브랜드 분리 적용 (광교바른내과 외)
- [ ] **외부 LLM 의료 검증**: 의대 교수·전문의 reviewer pool 연동
- [ ] **PromptOps SaaS**: 다른 의원에 시스템 라이선스 제공
- [ ] **Voice → Slide**: 진료실 녹음 → Slide 자동 생성 (Whisper + LLM)
- [ ] **Patient-facing app**: 진료 후 환자가 모바일로 받아보는 맞춤 자료

---

## 부록 A — 마이그레이션 가이드 (기존 → PromptOps)

기존 자료를 PromptOps 체계로 옮기는 단계:

1. **카테고리·서브카테고리 분류** (§3 트리)
2. **태그 부여** (§4)
3. **YAML 스키마 생성** (§2)
4. **재사용 블록 식별** (§5) — 중복되는 부분 추출
5. **Regression test 작성** (§6)
6. **브랜드 프로필 매칭** (§7)
7. **Notion DB row 생성** (§8)
8. **테스트 통과 후 archive 처리**

매주 2-3개씩 점진적 마이그레이션 권장. 1년 안에 모든 자료 PromptOps 체계로 통합.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) for 광교바른내과 — 2026-05-25
