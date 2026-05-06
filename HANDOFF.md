# 광교바른내과 콘텐츠 시스템 — 인계 문서

> 다음 세션 시작 시 이 문서를 첨부하고 "이어서 진행해줘"라고 요청하세요.
> 메모리 시스템과 합쳐져서 정확한 컨텍스트가 복원됩니다.
>
> **작성일**: 2026-05-03
> **이전 세션 종료 시점**: 작업 A(가이드 문서 갱신) 완료, 작업 B(Notion API 자동 등록) 대기

---

## 📌 한 줄 요약

광교바른내과 환자 교육 콘텐츠를 위한 단일 디자인 시스템이 4개 스킬에 걸쳐 정착됐고, 새 HTML 시스템(`clinic-content-system`)으로 GERD/H. pylori 두 덱이 검증 완료됐습니다. 다음은 **Notion API 자동 등록**(4단계)입니다.

---

## ✅ 지금까지 완료된 작업

### 1단계 — 디자인 시스템 정립
- Superhuman 디자인 원칙을 클리닉 브랜드(Navy/Steel Blue)에 적용
- Pretendard Variable 단일 폰트 (weight 450/540 활용)
- 7가지 본문 패턴 정의 (Hero Number / Asymmetric Split / Density Grid 3×2, 2×2 / Comparison / Timeline / Checklist / Regimen Tile)
- 4-region master grid (header / title-block / body / footer) — 모든 슬라이드 동일 위치 강제
- 단일 진실의 원천: `clinic-content-system/reference/brand-design-system.md`

### 2단계 — 두 덱 검증 완료
- `decks/gi/gerd/lifestyle/` — 역류성 식도염 생활관리 12장
- `decks/gi/h-pylori/eradication/` — H. pylori 제균 치료 12장
- 두 덱 모두 16:9 (1280×720) 단일 PDF 출력 — 카톡 공유 + 진료실 굿노트 + 노션 임베드 모두 만족

### 3단계 — QR + OG 메타 자동화 (직전 사이클)
- 마무리 슬라이드에 자기 URL을 가리키는 QR 코드 자동 삽입 (Python qrcode → SVG 인라인)
- HTML <head>에 OG 메타태그 7종 표준화 (카톡 미리보기 카드 자동 작동)
- BASE_URL은 build.py 한 곳에서 정의 → 호스팅 URL 변경 시 한 줄만 수정

### 디자인 시스템 통일 (네 스킬 모두)
- `clinic-content-system` (신규 메인) + 기존 3개 스킬에 디자인 시스템 참조 섹션 추가
- 폰트(Pretendard 1차 + Noto Sans KR fallback), 컬러(Navy/Steel), 배경색(#FAFAF7) 100% 일치
- patient-education-pptx는 "(legacy)" 표시 + "PPTX 명시적 요청 시에만 사용" 안내

### 작업 A — 가이드 문서 갱신 (이번 세션 마지막에 완료)
- `SKILL.md` — closing 슬라이드 행 갱신, Step 2에 OG + QR placeholder 안내 추가, 절대 규칙 9·10 추가
- `patterns.md` — §9 Closing Slide 섹션 신규 추가 (HTML 예시, OG 메타 표준 형식 포함)
- `content-template.md` — Closing 슬라이드 가이드 갱신 (closing-grid 패턴 명시)

---

## 🎯 다음 세션에서 진행할 작업 — 4단계 Notion API 자동 등록

### 목표
새 슬라이드 덱이 빌드될 때마다 광교바른내과 클리닉 허브의 **`📋 진료 설명용 자료 DB`**에 자동으로 행 추가. 임베드 URL과 PDF 다운로드 링크가 자동으로 채워지도록.

### Notion 인프라 정보 (이번 세션에서 확인 완료)

| 항목 | 값 |
|------|-----|
| 클리닉 허브 메인 페이지 | `32db8014-24d6-81ac-9fb4-d834598f45f0` |
| 진료 교육자료 (공유) 페이지 | `32fb8014-24d6-8195-888a-db795c84358e` |
| **타깃 DB**: 진료 설명용 자료 DB | `a84f23489df54e8fbe34b9818d6109e5` |
| Data source ID | `collection://afaccb35-948f-45b4-9e9d-ec64ccbfe345` |

### DB 스키마

| 컬럼 | 타입 | 옵션 |
|------|------|------|
| 자료명 | title | (자유 텍스트) |
| 카테고리 | select | 🫁 위장관 / 🫀 간·담도·췌장 / 🩺 일반내과 / 🔬 건강검진·암검진 / 💊 투약·생활습관 / 📝 동의서·안내문 |
| 대상 | select | 환자/보호자 / 의료진 / 공용 |
| 상태 | select | ✅ 사용중 / 🔄 수정중 / 📝 초안 / ⏸️ 보류 |
| 최종수정일 | date | (ISO-8601) |
| 버전 | text | 예: v1.0 |
| 파일형식 | multi_select | PPTX / PDF |
| 세부 질환 | text | 예: GERD, H. pylori |
| 비고 | text | (자유 텍스트 — URL 등) |

### 4단계 작업 순서

**Phase 1: 자동 등록 코드 작성**
1. `clinic-content-system/build.py`에 Notion 등록 함수 추가
2. 각 덱의 HTML <head>에서 OG 메타데이터(og:title, og:description) 파싱
3. slug → 카테고리 매핑 테이블 (예: `gi/*` → 🫁 위장관, `cardio/*` → 🩺 일반내과)
4. 빌드 후 Notion API로 행 추가/갱신

**Phase 2: 메타데이터 매핑**
- 자료명 ← og:title (`"역류성 식도염 생활관리 — 광교바른내과"`에서 클리닉명 제거)
- 카테고리 ← specialty 폴더 매핑
- 대상 ← 기본값 "환자/보호자" (또는 SKILL.md frontmatter에서 명시)
- 상태 ← 기본값 "📝 초안" (수동 검토 후 사용중으로 변경)
- 최종수정일 ← 빌드 시점 (datetime.now())
- 버전 ← Git commit 해시 또는 수동 지정
- 파일형식 ← `["PDF"]` (clinic-content-system은 HTML+PDF지만 DB 옵션은 PPTX/PDF만 있음)
- 세부 질환 ← og:title에서 추출 또는 frontmatter
- 비고 ← `{BASE_URL}/{slug_path}` (호스팅 URL)

**Phase 3: 인증 처리**
- Notion API 토큰 발급 (Settings → Integrations → New integration)
- 토큰을 .env 또는 환경변수로 관리 (절대 git에 commit 금지)
- 통합(integration)을 진료 설명용 자료 DB에 연결 (DB 우상단 ··· → Connections)

**Phase 4: 갱신 vs 신규 처리**
- 같은 slug가 이미 있으면 행 갱신 (최종수정일 + 버전 업데이트)
- 없으면 신규 행 추가
- 매칭 키: 비고 컬럼의 URL 또는 자료명

### 필요한 결정 사항 (다음 세션에서 받아야 할 것)
1. **Notion API 토큰 제공 방식** — 환경변수? .env 파일? 1Password 등?
2. **기존 DB 행 처리** — 새 자동 등록과 충돌 안 하도록 신규 자료만 등록할지, 기존 자료도 마이그레이션할지
3. **GitHub Pages 호스팅 셋업 시점** — 4단계 전에 호스팅 먼저? 아니면 placeholder URL로 등록 먼저?

---

## 📂 핵심 파일 경로

### outputs (이미 원장님께 전달됨)
- `clinic-content-system.zip` — 메인 스킬 패키지 (3단계 + 작업 A 적용본)
- `GERD.pdf`, `HPylori.pdf` — 검증된 두 덱
- `patient-education-pptx-skill.zip`, `patient-handout-pdf-skill.zip`, `lab-report-infographic-skill.zip` — 디자인 통일된 기존 스킬
- `all-three-skills-updated.zip` — 위 셋 통합본

### 스킬 내부 구조
```
clinic-content-system/
├── SKILL.md                        # 진입점 (트리거 키워드 + 워크플로우 + 절대 규칙 10개)
├── README.md                       # 빠른 시작 가이드
├── build.py                        # Playwright + Python qrcode 빌드 스크립트
├── shared/
│   ├── design-tokens.css           # 색상/폰트 토큰 단일 진실의 원천
│   ├── clinic-slides.css           # 슬라이드 마스터 + 7개 패턴 + qr-block + alert-strip
│   └── assets/clinic_logo.png
├── decks/gi/
│   ├── gerd/lifestyle/index.html
│   └── h-pylori/eradication/index.html
└── reference/
    ├── brand-design-system.md      ★ 모든 스킬 공유, 단일 진실의 원천
    ├── patterns.md                 # 9개 섹션 (7개 본문 패턴 + Closing + 패턴 선택 가이드)
    ├── content-template.md         # 12장 표준 구성
    ├── input-template.md           # 새 콘텐츠 요청 형식 + 사용 예시 2개
    ├── build.md                    # Playwright 환경 셋업
    └── migration.md                # 기존 3개 스킬 통합 가이드
```

---

## 🎨 디자인 시스템 핵심 (한눈에)

- **컬러**: Navy `#003366` 베이스 + Steel Blue `#5B9BD5` 단일 액센트. 다른 색 추가 금지
- **폰트**: Pretendard Variable (weight 450/540 활용) — Noto Sans KR fallback
- **라디우스**: `8px` (작은 요소) / `16px` (카드) — 단 두 가지만
- **배경색**: `#FFFFFF` (캔버스) / `#FAFAF7` (warm white, 섹션 구분)
- **본문 폰트 크기**: 16px (body) / 18px (body-lg) / 22px (h3) / 26px (h2) / 36-72-104px (display 계열)
- **그라데이션**: 표지/Hero 슬라이드 1장에만. 본문 슬라이드는 흰 캔버스 유지
- **그림자**: 최소화. 깊이는 색상 대비와 보더로 표현

---

## 🔑 7가지 본문 패턴 + 1 (마무리)

| 패턴 | 적합 콘텐츠 | 예시 |
|------|-----------|------|
| Hero Number | 단일 핵심 숫자 | 한국 유병률 30%, 위암 위험 6배 |
| Asymmetric Split | 정의 + 메트릭 | "GERD란" + 진단 임계값 카드 |
| Density Grid 3×2 | 6개 동등 항목 | 증상 6개, 위험 요인 6개 |
| Density Grid 2×2 | 4개 핵심 + alert | 복용 주의사항 4가지 + 응급 |
| Comparison | 양자 비교 (네이비/스틸) | DO vs DON'T, 권장 vs 피하기 |
| Timeline | 4단계 흐름 | 진단 경로, 치료 일정 |
| Checklist | 7가지 액션 | 환자 실천 7가지 |
| Regimen Tile | 약물 조합 | 1차/2차/3차 치료, 표준 vs 비스무트 사제 |
| **Closing** (신규) | 마무리 + QR | contact-card + qr-block 좌우 분할 |

---

## ⚙️ 빌드 워크플로우

```bash
# 환경 셋업 (최초 1회)
pip install playwright qrcode --break-system-packages
playwright install chromium

# 빌드
cd clinic-content-system
python build.py
# → output/{slug}.pdf, output/{slug}-preview.png 생성
```

`build.py`의 `BASE_URL` 상수가 호스팅 URL의 단일 진실의 원천. GitHub Pages URL 확정 시 이 한 줄만 변경하면 모든 덱의 QR이 자동으로 새 URL을 가리킴.

---

## 💡 다음 세션 시작 멘트 예시

```
이 인계 문서 보고 이어서 진행해줘. 4단계 Notion API 자동 등록 시작하자.
Notion 토큰은 [방식]으로 전달할게.
```

또는

```
지난번에 만들던 광교바른내과 clinic-content-system 이어서 진행.
이 인계 문서 첨부했으니 컨텍스트 복원 후 4단계 Notion API 자동 등록 진행해줘.
```

Claude의 메모리 시스템에 핵심 정보(Notion 페이지 ID, DB 스키마, 디자인 시스템 요점)가 저장되어 있어 이 인계 문서와 합쳐지면 정확한 컨텍스트가 복원됩니다.
