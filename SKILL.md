---
name: clinic-content-system
description: >
  광교바른내과 통합 환자 교육 콘텐츠 생성 스킬 (HTML + PDF). 세 가지 콘텐츠 타입을
  단일 디자인 시스템·단일 빌드 파이프라인으로 생산한다: (1) 16:9 멀티슬라이드 환자
  교육 덱, (2) A4 세로 1장 진료실 핸드아웃, (3) A4 세로 1장 검사 결과 인포그래픽.
  공통 인프라: Navy #003366 + Steel Blue #5B9BD5, Pretendard Variable, Python qrcode
  SVG 자동 QR 생성, OG meta 7개 head 등록. 사용자가 "환자 교육 슬라이드/PDF",
  "유인물 만들어줘", "주의사항 PDF", "비치용 안내문", "검사 결과지 인포그래픽",
  "결과지 시각화", "환자한테 보낼 자료", "카톡으로 보낼 자료" 등을 만들어 달라고
  할 때 트리거된다. 기존 patient-education-pptx, patient-handout-pdf,
  lab-report-infographic 세 스킬의 HTML 통합 후속 버전이며, PPTX가 명시적으로
  요구되지 않는 한 이 스킬을 우선 사용한다.
---

# Clinic Content System — Unified Patient Content (HTML + PDF)

## 콘텐츠 타입 3종

이 스킬은 광교바른내과 모든 환자 콘텐츠를 단일 디자인 시스템과 단일 빌드 파이프라인으로 생산한다:

| 타입 | 디렉터리 | 페이지 포맷 | 용도 | 마무리 QR 위치 |
|---|---|---|---|---|
| **decks** | `decks/{specialty}/{topic}/{slug}/` | 16:9 1280×720, 12장 | 진료실 환자 설명, 카톡 공유, 노션 임베드 | closing slide (`.qr-block__code`) |
| **handouts** | `handouts/{specialty}/{slug}/` | A4 세로, 1장 | 진료실 비치, 환자 인쇄물 | footer mini-QR (`.qr-mini__code`) |
| **lab-reports** | `lab-reports/{topic}/{slug}/` | A4 세로, 1장 | 검사 결과 시각화, 환자 설명 첨부 | footer mini-QR (`.qr-mini__code`) |

요청 키워드별 자동 라우팅:
- "환자 교육 슬라이드", "질환 안내 PPT", "12장 자료" → **decks/**
- "유인물", "비치용 안내문", "주의사항 PDF", "A4 한 장" → **handouts/**
- "검사 결과지 인포그래픽", "결과지 시각화", "혈액검사 PPT/PDF" → **lab-reports/**

## 출력물

세 가지 타입 모두 다음 용도를 단일 산출물로 만족한다:
1. **카톡/문자 공유용 PDF** — 환자에게 링크 또는 파일로 전송
2. **진료실 발표·필기용 PDF** — 굿노트로 불러와 펜으로 강조하며 설명
3. **노션 임베드용 HTML** — GitHub Pages 호스팅 후 클리닉 허브에 임베드

모든 슬라이드는 1280×720 (16:9) 고정 비율. 모바일 반응형은 설계 대상이 아니다.

## 디자인 시스템

색상·폰트·레이아웃·톤 일체는 `reference/brand-design-system.md`를 따른다.
**SKILL 사용 전 반드시 brand-design-system.md를 먼저 읽고 토큰을 확인한다.**

요약:
- 색상: Navy (#003366) 베이스 + Steel Blue (#5B9BD5) 단일 액센트
- 폰트: Pretendard Variable, weight 450/540 활용
- 라디우스: 8px / 16px만
- Hero 그라데이션은 표지 1장에만 적용

## 입력 형식

사용자는 다음과 같이 콘텐츠를 전달한다:

```
[주제명]
대상 환자: [예: 신환 / 재진 / 가족 / 일반]

1. 개요 / Overview
- 한국 유병률, 핵심 통계, 임상적 중요성

2. 정의 / Definition
- 질환의 정의, 주요 기전

3. 증상 또는 진단
- 6가지 정도

4. 위험 요인 / 적응증
- 6가지 정도

5. 치료 / 약물
- 1차, 2차, 3차 또는 약물 조합

6. 생활 관리 / 식이
- 권장 vs 피하기 또는 6가지 항목

7. 경고 증상 / Red Flag
- 즉시 내원이 필요한 경우 6가지

8. 환자 실천 7가지

[근거] ACG / KSGE / 대한 OO 학회 가이드라인
```

콘텐츠 양이 부족하면 Claude가 의학적으로 정확한 일반 정보를 보완 생성한다.
한국 진료 환경(보험 기준, KCD 코드, 한국 가이드라인)을 우선 반영한다.

## 생성 워크플로우

### Step 1 — 콘텐츠 분석 및 패턴 매핑

12장 표준 구성 (`reference/content-template.md` 참조):

| 슬라이드 | 패턴 | 비고 |
|---------|------|------|
| 1. Cover | dark gradient | 표지 |
| 2. Overview / Hero stat | Hero Number | 한국 유병률 등 핵심 숫자 |
| 3. Definition | Asymmetric Split | 정의 + 메트릭 카드 |
| 4. Symptoms / Diagnosis | Density Grid 3×2 | 6항목 |
| 5. Risk Factors / Indications | Density Grid 3×2 | 6항목 |
| 6. Treatment (first-line) | Regimen Tile 또는 Density Grid | 약물 조합 |
| 7. Treatment (salvage) 또는 Comparison | Regimen Tile 또는 Comparison | 2차 치료 또는 DO/DON'T |
| 8. Schedule / Process | Timeline | 4단계 |
| 9. Precautions | Density Grid 2×2 + alert strip | 4항목 + 경고 |
| 10. Side Effects / Red Flags | Density Grid 3×2 (mixed) | 일반 + alert tile 혼합 |
| 11. Action Checklist | Checklist | 7가지 |
| 12. Closing | closing-grid (contact + QR) | 클리닉 정보 + 다시 보기 QR (자동 생성) |

콘텐츠 성격에 따라 위 패턴을 변경 가능. 단, 4-region master grid (header / title-block / body / footer)는 모든 슬라이드에 강제 적용된다.

### Step 2 — HTML 생성

1. `decks/{specialty}/{topic}/{slug}/index.html` 경로에 새 파일 작성
   - 예: `decks/gi/gerd/lifestyle/index.html`, `decks/cardio/htn/lifestyle/index.html`
2. `shared/design-tokens.css`와 `shared/clinic-slides.css`를 link (상대 경로 4단계 위)
3. Pretendard Variable CDN 로드 (jsDelivr)
4. 12개 `<section class="slide">` 작성, 각각 4-region master grid + 본문 패턴 1개
5. 헤더: 좌측 로고(`shared/assets/clinic_logo.png`) + 우측 chapter eyebrow
6. 푸터: 좌측 출처 + 우측 페이지 번호 (NN / 12)
7. OG meta 태그 표준 7개 (`patterns.md §9` 참조): og:type, og:url, og:title, og:description, og:image, og:site_name, theme-color. og:url은 `{BASE_URL}/{slug_path}` 형식 (BASE_URL은 build.py 상수 참조)
8. 마무리 슬라이드의 `<div class="qr-block__code"></div>`는 빈 div로 둔다 — 빌드 스크립트가 Python qrcode로 SVG QR을 자동 생성해 인라인 삽입한다

### Step 3 — 빌드

빌드 명령어와 환경 셋업은 `reference/build.md` 참조. 핵심:

```bash
python build.py
```

산출물:
- `output/{slug}.pdf` — 환자 공유용 PDF (1280×720 페이지)
- `output/{slug}-preview.png` — 데스크톱 풀스크린 미리보기

### Step 4 — Notion DB 등록 (선택)

Notion 광교바른내과 클리닉 허브 DB에 다음 메타데이터로 행 추가:
- 제목, 분류 (소화기/순환기/내분비/일반), 대상 (환자용/직원용)
- 작성일, 가이드라인 출처, GitHub URL, 임베드 URL, 상태 (초안/검토중/공개)

## 본문 패턴 7종

상세 HTML 예시는 `reference/patterns.md` 참조:

1. **Hero Number** — 단일 거대 숫자 (좌 5 : 우 4 분할)
2. **Asymmetric Split** — 좌측 statement + 우측 metric cards (좌 11 : 우 9)
3. **Density Grid 3×2** — 6개 동등 카드
4. **Density Grid 2×2** — 4개 카드 (+ optional alert strip)
5. **Comparison** — 네이비 좌측 / 스틸 우측 컬럼
6. **Timeline** — 4단계 노드 + 화살표
7. **Checklist** — 7가지 액션 (2열 grid)
8. **Regimen Tile** — 약물 조합 표 (tile 안에 `tile__regimen` 리스트)

각 패턴의 적합 콘텐츠 유형, HTML 구조, 사용 예시는 `patterns.md`에 정의.

## 절대 규칙

1. **디자인 토큰 외 색상 추가 금지**. 녹색·파스텔·여러 액센트 색 사용 안 함
2. **표지 외 슬라이드에 그라데이션 배경 적용 금지**
3. **본문 패턴 7종 외 자유 레이아웃 금지** (필요시 `patterns.md`에 새 패턴 정의 후 사용)
4. **모든 슬라이드는 4-region master grid 준수** (header / title-block / body / footer 위치 동일)
5. **폰트는 Pretendard Variable 단일** (다른 폰트 추가 금지)
6. **로고는 텍스트가 아닌 PNG 이미지** (`shared/assets/clinic_logo.png`)
7. **의학 용어 영문 병기** (예: 역류성 식도염 (GERD))
8. **출처 명시** (푸터의 source 영역에 가이드라인명 + 연도)
9. **마무리 슬라이드는 closing-grid 패턴 강제** — contact-card + qr-block. QR은 빌드 시 자동 생성.
10. **OG 메타태그 7종 표준 포함** — 카톡 공유 미리보기 카드 자동 작동을 위해 필수.

## 검증

빌드 후 확인:
- 헤더 로고와 chapter eyebrow가 12장 모두 같은 위치인가
- 타이틀과 부제가 12장 모두 같은 위치인가
- 푸터의 출처 + 페이지 번호가 12장 모두 같은 위치인가
- 표지 외 슬라이드에 그라데이션 배경이 없는가
- 색상이 디자인 토큰 외 추가되지 않았는가
- Pretendard Variable이 정상 로드됐는가 (CDN 차단 환경 확인)


## 기존 덱 수정 워크플로우

생성된 덱은 PPTX와 달리 PowerPoint에서 직접 편집하는 방식이 아니다. HTML 소스를 수정하고 다시 빌드한다. 다음 두 가지 길 중 하나를 사용한다.

### 길 A — Claude에게 자연어로 수정 요청 (권장)

원장님이 자연어로 수정 사항을 지시하면 Claude가 해당 HTML 파일을 수정하고 다시 빌드한다. 이 방식의 장점은 디자인 시스템이 자동으로 보장된다는 점이다 — 카드 구조, 색상, 폰트, 위치가 그대로 유지되고 콘텐츠만 정확히 바뀐다.

수정 요청 예시:

```
"GERD 슬라이드 4번에서 '야간 흉통' 카드를 '야간 호흡곤란'으로 바꿔줘"
"슬라이드 7 약물 치료에서 P-CAB 카드를 PREFERRED로 표시해줘"
"슬라이드 11 체크리스트에 8번 항목으로 '식이섬유 충분히 섭취' 추가"
"표지 부제를 '진단부터 재검사까지 한눈에'로 바꿔줘"
"슬라이드 10 부작용에 '관절통' 카드 추가"
"슬라이드 6과 7의 순서를 바꿔줘"
"전체적으로 출처 라인을 ACG 2024 가이드라인으로 업데이트"
```

이런 요청을 받으면 Claude는:

1. 해당 덱의 `decks/{specialty}/{topic}/{slug}/index.html` 파일을 view 또는 read한다
2. 수정 사항이 디자인 시스템(`reference/brand-design-system.md`)을 위반하지 않는지 확인한다
3. `str_replace`로 정확한 부분만 수정한다 (전체 재작성하지 않는다)
4. `python build.py` 실행해서 새 PDF 생성
5. 변경된 슬라이드의 PDF 페이지를 추출해서 시각 검증
6. 결과 PDF와 변경 요약을 사용자에게 전달

수정 요청 시 권장 표현 형식:

- **위치 명시**: "슬라이드 N의 ..." 또는 "슬라이드 제목이 'XYZ'인 곳에서..."
- **변경 대상 명시**: 카드 인덱스(`FACTOR · 02`), 카드 제목, 본문 일부 등
- **변경 후 내용**: 정확히 어떤 텍스트로 또는 어떤 패턴으로

### 길 B — HTML 직접 편집

빠른 오타 수정이나 한두 단어 변경 시 사용자가 직접 HTML 파일을 편집할 수 있다. VSCode, Sublime, 또는 텍스트 에디터로 `decks/{specialty}/{topic}/{slug}/index.html`을 열고 텍스트만 수정한다.

```html
<!-- 이런 구조에서 -->
<div class="tile">
  <div class="tile__index">FACTOR · 01</div>      <!-- 라벨 (수정 가능) -->
  <div class="tile__title">체중 · 복압</div>        <!-- 제목 (수정 가능) -->
  <div class="tile__body">비만, 복부 비만...</div>  <!-- 본문 (수정 가능) -->
</div>
<!-- div class="..." 같은 태그는 건드리지 않는다 -->
```

수정 후:
```bash
python build.py
```

### 변경 추적 (권장)

덱 라이브러리는 git 저장소로 관리하시는 것을 권장한다:

```bash
git add decks/gi/gerd/lifestyle/
git commit -m "Update GERD: alarm symptoms revised per ACG 2024"
```

이렇게 하면 수정 이력이 자동 추적되고, 잘못 수정했을 때 `git checkout`으로 이전 버전으로 되돌릴 수 있다. PPTX 시절 `_v1`, `_v2`, `_final` 붙여가며 파일 관리하던 부담이 사라진다.

### 수정 시 주의

다음은 수정하지 않는다 (디자인 시스템이 깨진다):

- ❌ `<div class="tile">`의 클래스 이름 변경
- ❌ 슬라이드의 `<header>`, `.slide__title-block`, `.slide__body`, `<footer>` 구조 변경
- ❌ 색상 인라인 스타일 추가 (style 속성에 임의 색상 코드 입력)
- ❌ 새 폰트 link 추가
- ❌ 7가지 본문 패턴 외 자유 레이아웃 추가

이런 변경이 필요하면 먼저 `reference/brand-design-system.md`와 `reference/patterns.md`를 갱신한 다음 적용한다.

### 환자별 즉석 변경

진료실에서 특정 환자에게만 추가 강조나 메모가 필요한 경우, HTML 자체를 수정하지 않는다. 대신:

- 굿노트로 PDF 위에 펜으로 표시
- 또는 Markdown 메모를 별도 첨부

원본 덱은 일반적인 환자 교육용으로 유지한다.


## A4 세로 1장 콘텐츠 (handouts / lab-reports)

A4 세로 단일 페이지 콘텐츠는 16:9 덱과 다른 마스터 그리드를 사용한다. 자세한 컴포넌트 사양은 `shared/clinic-handout-a4.css` 참조.

### A4 페이지 마스터 (4-region grid)

```
.page (210mm × 297mm)
 ├─ .page__header        — 좌측 로고, 우측 eyebrow ("PATIENT HANDOUT · GASTROENTEROLOGY")
 ├─ .page__title-block   — 제목 + 부제
 ├─ .page__body          — 콘텐츠 영역 (flex column, gap 5mm)
 └─ .page__footer        — 좌측 클리닉 정보 + 면책 / 우측 mini QR (.qr-mini__code)
```

### 사용 가능한 컴포넌트

`shared/clinic-handout-a4.css`에 정의된 재사용 가능 블록:

- `.section-heading` — 좌측 Steel Blue 바 + Navy 제목 (12pt)
- `.card` (기본 / `--accent` 크림 / `--warning` 주황 / `--navy` 다크)
- `.checklist` — 번호 동그라미 + 텍스트 (타임라인·실천 항목)
- `.body-2col` — 2열 그리드 (권장 vs 금지, 의미 vs 권장 등)
- `.stats-row` + `.stat-cell` (`--ok`/`--high`/`--low`) — 검사 수치 한눈에
- `.lab-row` + `.lab-row__badge` — 항목별 결과/참고치/판정
- `.disclaimer` — footer 하단 작은 면책 문구

### A4 콘텐츠 작성 규칙

1. `handouts/{specialty}/{slug}/index.html` 또는 `lab-reports/{topic}/{slug}/index.html` 경로
2. CSS 링크 두 개: `../../../shared/design-tokens.css` + `../../../shared/clinic-handout-a4.css`
3. 로고 경로: `../../../shared/assets/clinic_logo.png`
4. **footer의 `<div class="qr-mini__code"></div>`는 빈 div로 둔다** — 빌드 스크립트가 자동 주입
5. OG meta 7개(og:type/url/title/description/image/site_name + theme-color) 모두 head에 작성. og:url은 `{BASE_URL}/{slug_path}/` 형식. **빌드 시 자동 검증된다.**
6. 1장 분량 강제: 콘텐츠가 넘치면 글자 크기 줄이지 말고 항목 수를 줄이거나 멀티슬라이드 deck로 전환 검토

### 통합 빌드

`build.py`의 `TARGETS` 리스트에 새 항목 추가:

```python
TARGETS = [
    # 기존 항목들...
    ("handouts", "{slug}", "handouts/{specialty}/{slug}/",
     ROOT / "handouts/{specialty}/{slug}/index.html",
     "qr-mini__code", "a4-portrait"),
]
```

`python build.py` 실행 시 4개 타깃(현재) 모두 일괄 빌드되며, 각 출력은:
- `output/decks/{slug}.{pdf,png}` — 16:9 덱
- `output/handouts/{slug}.{pdf,png}` — A4 핸드아웃
- `output/lab-reports/{slug}.{pdf,png}` — A4 랩리포트


## 디렉토리 구조

```
clinic-content-system/
├── SKILL.md                          # 이 파일
├── README.md
├── HANDOFF.md
├── build.py                          # 통합 빌드 (3개 타입 모두)
│
├── shared/                           # 모든 콘텐츠 공유
│   ├── design-tokens.css             # 색상/폰트/스페이싱 변수 (단일 진실)
│   ├── clinic-slides.css             # 16:9 덱 전용 컴포넌트
│   ├── clinic-handout-a4.css         # A4 1장 전용 컴포넌트
│   ├── _build_helpers.py             # QR SVG 생성, OG meta 검증 헬퍼
│   └── assets/
│       └── clinic_logo.png
│
├── decks/                            # 16:9 멀티슬라이드 덱
│   └── gi/
│       ├── gerd/lifestyle/index.html
│       └── h-pylori/eradication/index.html
│
├── handouts/                         # A4 1장 진료실 핸드아웃
│   └── gi/
│       └── colonoscopy/index.html
│
├── lab-reports/                      # A4 1장 검사 결과 인포그래픽
│   └── lipid-panel/sample/index.html
│
└── reference/
    ├── brand-design-system.md        # 단일 진실의 원천 (모든 스킬 공유)
    ├── patterns.md                   # 16:9 덱 7가지 본문 패턴
    ├── content-template.md           # 12장 표준 구성
    ├── input-template.md
    ├── build.md                      # 빌드 환경 셋업
    └── migration.md                  # 기존 PPTX 스킬에서 마이그레이션
```


## 참고 문서

- `reference/brand-design-system.md` — 색상/폰트/톤 단일 진실의 원천 (모든 스킬 공유)
- `reference/patterns.md` — 16:9 덱 7가지 본문 패턴의 HTML 사양과 사용 가이드
- `reference/content-template.md` — 16:9 덱 12장 표준 구성과 슬라이드별 콘텐츠 가이드
- `reference/build.md` — Playwright 빌드 환경 셋업과 명령어
- `reference/migration.md` — 기존 PPTX 스킬에서 마이그레이션 가이드
- `shared/clinic-handout-a4.css` — A4 1장 컴포넌트 사양 (handouts / lab-reports)
