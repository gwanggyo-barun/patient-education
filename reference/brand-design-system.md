# 광교바른내과 브랜드 디자인 시스템

> **이 문서는 광교바른내과의 모든 환자 콘텐츠가 공유하는 단일 진실의 원천이다.**
> 새 콘텐츠를 만들거나 기존 자료를 갱신할 때 반드시 이 문서를 먼저 참조한다.

이 디자인 시스템은 다음 스킬들에서 동일하게 적용된다:

| 스킬 | 콘텐츠 타입 | 출력 형식 | 용도 |
|------|---------|---------|------|
| `clinic-content-system` (메인) | decks | HTML + PDF (16:9 1280×720) | 환자 교육 슬라이드 덱 (12장) |
| `clinic-content-system` (메인) | handouts | HTML + PDF (A4 세로 1장) | 진료실 비치·환자 인쇄 핸드아웃 |
| `clinic-content-system` (메인) | lab-reports | HTML + PDF (A4 세로 1장) | 검사 결과 인포그래픽 |
| `patient-handout-pdf` | redirector | (clinic-content-system 사용) | "유인물" 키워드 진입점 |
| `lab-report-infographic` | redirector | (clinic-content-system 사용) | "결과지 인포그래픽" 키워드 진입점 |
| `patient-education-pptx` (legacy) | PPTX | PPTX | PPTX가 명시적으로 필요한 경우만 |

세 가지 콘텐츠 타입(decks / handouts / lab-reports) 모두 동일한 디자인 토큰(`shared/design-tokens.css`)을 참조하며, 단일 빌드 파이프라인(`build.py`)으로 생산된다. 매체별 CSS만 분리되어 있다(`clinic-slides.css` for 16:9, `clinic-handout-a4.css` for A4 세로).

## 1. 디자인 철학 (Superhuman-inspired)

> Maximum confidence through minimum decoration.

- **단일 dramatic gesture**: 표지/hero 1장만 dark navy gradient. 나머지는 흰 캔버스
- **단일 액센트 컬러**: Steel Blue (#5B9BD5) 외 다른 색상 추가 금지
- **압축된 헤드라인**: 큰 타이틀은 line-height 0.96으로 압축, 본문은 1.5로 여유
- **비표준 폰트 weight**: Pretendard Variable의 450, 540 사용 (일반 400, 500과 미세하게 다름)
- **단 두 가지 radius**: 8px (작은 요소) / 16px (카드)
- **그림자 자제**: 깊이는 색상 대비와 보더로 표현

## 2. 컬러 팔레트

### Primary — Brand Navy
| Token | Hex | 용도 |
|-------|-----|------|
| `--color-navy` | `#003366` | 타이틀, 1차 마크, 비교 슬라이드 좌측 헤더 |
| `--color-navy-deep` | `#07193A` | Hero gradient의 가장 어두운 끝 |
| `--color-navy-mid` | `#1A2C4D` | Hero gradient 중간 톤 |

### Accent — Soft Steel Blue (유일한 액센트)
| Token | Hex | 용도 |
|-------|-----|------|
| `--color-steel` | `#5B9BD5` | 액센트, em 강조, 비교 슬라이드 우측 헤더 |
| `--color-steel-deep` | `#2C5F8D` | 액센트 press 상태 |
| `--color-sky` | `#BFE0FF` | 어두운 배경 위 highlight |

### Ink — 따뜻한 다크 텍스트
| Token | Hex | 용도 |
|-------|-----|------|
| `--color-ink` | `#1E293B` | 본문 텍스트 (밝은 배경) |
| `--color-ink-soft` | `#334155` | 보조 텍스트 |
| `--color-slate` | `#64748B` | 캡션, 라벨, 메타 |
| `--color-slate-soft` | `#94A3B8` | 미묘한 라벨 |

### Surfaces
| Token | Hex | 용도 |
|-------|-----|------|
| `--color-canvas` | `#FFFFFF` | 슬라이드 메인 캔버스 |
| `--color-canvas-warm` | `#FAFAF7` | 미묘한 따뜻한 흰색 (섹션 구분) |
| `--color-cream` | `#F4F1EB` | luxury 버튼 배경 |

### Borders
| Token | Hex | 용도 |
|-------|-----|------|
| `--color-border` | `#E2E8F0` | 기본 카드/구분선 |
| `--color-border-soft` | `#EDF2F7` | 미묘한 분리선 |
| `--color-border-strong` | `#CBD5E1` | 강조 보더 |

### Semantic — 매우 제한적 사용
| Token | Hex | 용도 |
|-------|-----|------|
| `--color-warning` | `#C2410C` | 주의 (절제된 오렌지) |
| `--color-warning-bg` | `#FFF7ED` | 주의 카드 배경 |
| `--color-danger` | `#B91C1C` | 진짜 위험 (Red Flag, 알람) |
| `--color-danger-bg` | `#FEF2F2` | 위험 카드 배경 |

> ⚠️ **녹색·파스텔·여러 액센트 색 사용 금지**. 의미적 의도 없이 색상 추가하지 않는다.

## 3. 타이포그래피

### 폰트 우선순위 (반드시 이 순서)

```
1차: Pretendard Variable (Pretendard Variable, Pretendard)
fallback: -apple-system, BlinkMacSystemFont, system-ui, sans-serif
2차 fallback (PPTX 환경): Noto Sans KR
```

**HTML/PDF 출력**: Pretendard Variable을 jsDelivr CDN으로 로드
```html
<link rel="stylesheet" as="style" crossorigin
  href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css" />
```

**PPTX 출력**: `fontFace: 'Pretendard'` 1차, fallback `'Noto Sans KR'`. 사용자 PC에 Pretendard가 설치돼 있지 않으면 fallback이 적용됨.

### 폰트 weight 가이드

| Weight | 용도 |
|--------|------|
| `300` (Light) | 큰 화살표·기호 같은 가벼운 장식 |
| `400` (Regular) | 일반 본문 |
| `450` | 본문의 미세 강조 (Pretendard Variable 전용) |
| `500` (Medium) | 보조 헤더 |
| `540` | Display 타이틀 (Pretendard Variable 전용) |
| `600` (Semibold) | 작은 라벨, 챕터 eyebrow |
| `700` (Bold) | 강조, 작은 텍스트 |
| `800` (Black) | Hero 거대 숫자, 배경 챕터 번호 |

### 크기 위계 (16:9 슬라이드 기준)

| Token | Size | 용도 |
|-------|------|------|
| `--text-display-xl` | 104px | Hero 거대 숫자 |
| `--text-display-lg` | 72px | 표지 타이틀 |
| `--text-display` | 48px | 일반 슬라이드 타이틀 |
| `--text-h1` | 36px | 큰 statement |
| `--text-h2` | 26px | 부제, 큰 metric value |
| `--text-h3` | 22px | 카드 타이틀 |
| `--text-body-lg` | 18px | 강조된 본문 |
| `--text-body` | 16px | 일반 본문 |
| `--text-sm` | 14px | 캡션 |
| `--text-xs` | 12px | 작은 라벨 |
| `--text-micro` | 11px | 챕터 eyebrow |

### Line height & Letter spacing

- **Display (큰 타이틀)**: line-height `0.96`, letter-spacing `-0.035em` (압축된 typographic block)
- **헤딩 (중간)**: line-height `1.10`, letter-spacing `-0.02em`
- **본문**: line-height `1.50`, letter-spacing `0` (여유로운 reading)
- **Eyebrow / 라벨**: letter-spacing `0.12em`, uppercase

## 4. 로고

**파일**: `clinic_logo.png` (가로:세로 = 3.33:1, 1531×460)

**위치 규칙**:
- 일반 슬라이드: 좌상단, height 32px
- 표지 슬라이드 (dark gradient): 좌상단, height 36px, `filter: brightness(0) invert(1)` (흰색)
- A4 1장 유인물: 우상단, 높이 약 0.54인치
- PPTX: 우상단 (표지는 좌상단 1개만, 디자인 시스템 4.3 참조)

## 5. 레이아웃 원칙

### Spacing (8px base)
4 / 8 / 12 / 16 / 20 / 24 / 28 / 32 / 40 / 48 / 56 / 64 / 80 / 96 px

### Radius (단 두 가지)
- `8px` — 작은 요소 (배지, 인라인 버튼)
- `16px` — 카드, 큰 컨테이너

### Slide geometry
- 가로:세로 비율: **16:9 고정** (1280×720)
- Padding: 좌우 72px / 상하 56px

### Master 4-region grid (모든 슬라이드 동일)
```
┌─ HEADER (logo + chapter eyebrow) ──── same position every slide
├─ TITLE BLOCK (title + subtitle) ───── same position every slide
├─ BODY (one of 7 patterns) ─────────── pattern-specific
└─ FOOTER (source + page) ──────────── same position every slide
```

## 6. 톤 & 보이스

### 영문 라벨 (eyebrow)
- 챕터: `CHAPTER 03 · RISK FACTORS`
- 카드 인덱스: `FACTOR · 02`, `RED FLAG · 06`, `OPTION · A`, `STRONG · 01`
- 메트릭 라벨: `WHY IT MATTERS`, `DIAGNOSTIC THRESHOLD`, `CANCER RISK REDUCTION`
- 출처: `근거 — ACG Clinical Guideline for GERD (2022)` (영문 + 한글 혼용)

### 한국어 본문
- 의학 용어는 영문 병기: `역류성 식도염 (GERD)`, `바렛식도 (Barrett's esophagus)`
- 환자 친화적 어투: "이런 증상이 있나요", "오늘부터 실천할 7가지"
- 권위적·명령조 회피, 그러나 응급 상황 안내는 명료하게: "즉시 진료가 필요한 경우"

### 알람·경고 표현
- 일반 주의: 카드 색상 / 라벨 변경 (`tile--accent`)
- 명확 경고: `tile--alert` + `RED FLAG · NN` 라벨
- 즉시 행동: `alert-strip` 컴포넌트 (붉은 좌측 보더 + "중요" 라벨)

## 7. 본문 패턴 7종

상세 사양과 HTML 예시는 `patterns.md` 참조. 요약:

| 패턴 | 적합한 콘텐츠 |
|------|--------------|
| **Hero Number** | 단일 핵심 숫자 (유병률, 위험 감소율) |
| **Asymmetric Split** | 정의 + 핵심 메트릭 |
| **Density Grid** (3×2 / 2×2) | 동등한 위계의 항목 나열 (증상, 원인, 적응증) |
| **Comparison** | DO/DON'T, 옵션 비교 (네이비 vs 스틸) |
| **Timeline** | 진단 경로, 치료 일정, 시간 흐름 |
| **Checklist** | 환자 행동 항목 (보통 7가지) |
| **Regimen Tile** | 약물 조합 (약물명 + 용량 + 빈도) |

## 8. 적용 체크리스트

새 콘텐츠 만들기 전 또는 기존 콘텐츠 갱신 시 확인:

- [ ] 색상은 정의된 토큰 7~8개 안에서만 사용했는가
- [ ] 폰트는 Pretendard Variable (또는 Noto Sans KR fallback)인가
- [ ] 표지 외 슬라이드에 그라데이션 배경을 추가하지 않았는가
- [ ] 모든 슬라이드의 로고/타이틀/푸터 위치가 동일한가
- [ ] 본문 패턴 7종 중 하나를 사용했는가
- [ ] 영문 eyebrow 라벨을 일관되게 사용했는가
- [ ] 출처를 푸터에 명시했는가

## 9. 디자인 시스템 변경 절차

이 디자인 시스템은 한 번 정착하면 자주 변경하지 않는다. 변경이 필요하면:

1. 이 문서를 먼저 갱신
2. `clinic-content-system/shared/design-tokens.css` 갱신 — 모든 콘텐츠가 CSS 변수로 참조하므로 빌드만 다시 돌리면 일괄 적용됨
3. 변경 사유와 영향 범위를 Notion 클리닉 허브에 기록

> Note: 옛 별도 스킬(patient-handout-pdf, lab-report-infographic, patient-education-pptx)은 이제 `clinic-content-system`의 진입점 redirector이므로 별도 토큰 동기화 불필요.
