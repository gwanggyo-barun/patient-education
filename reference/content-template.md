# 12장 표준 콘텐츠 구성

> 새 환자 교육 자료를 만들 때 사용하는 12장 표준 구성. 콘텐츠 성격에 따라 슬라이드 순서나 패턴을 조정 가능하지만, 4-region master grid는 모든 슬라이드에 강제 적용된다.

## 표준 구성 표

| # | 슬라이드 | 패턴 | 챕터 라벨 |
|---|---------|------|----------|
| 01 | Cover | dark gradient | `PATIENT EDUCATION · {SPECIALTY}` |
| 02 | Overview / Hero stat | Hero Number | `CHAPTER 01 · OVERVIEW` |
| 03 | Definition / Pathophysiology | Asymmetric Split | `CHAPTER 01 · OVERVIEW` |
| 04 | Symptoms 또는 Diagnosis | Density Grid 3×2 | `CHAPTER 02 · SYMPTOMS` 또는 `· DIAGNOSIS` |
| 05 | Risk Factors / Indications | Density Grid 3×2 | `CHAPTER 03 · RISK FACTORS` 또는 `· INDICATIONS` |
| 06 | Treatment / First-line | Regimen Tile 또는 Density Grid | `CHAPTER 04 · FIRST-LINE` |
| 07 | Salvage / Comparison | Regimen Tile 또는 Comparison | `CHAPTER 05 · SALVAGE` 또는 `· DIET` |
| 08 | Schedule / Process | Timeline | `CHAPTER 06 · SCHEDULE` |
| 09 | Precautions | Density Grid 2×2 + alert | `CHAPTER 07 · PRECAUTIONS` |
| 10 | Side Effects 또는 Red Flags | Density Grid 3×2 (mixed) | `CHAPTER 08 · SIDE EFFECTS` 또는 `· RED FLAGS` |
| 11 | Action Checklist | Checklist (7가지) | `CHAPTER 09 · ACTION` |
| 12 | Closing | contact card | `END OF DECK · THANK YOU` |

## 콘텐츠 변형

### 만성질환 (예: 고혈압, 당뇨, 이상지질혈증)
- 06: 약물 치료 (Density Grid)
- 07: 식이/생활습관 (Comparison: 권장 vs 피하기)
- 08: 합병증 모니터링 일정 (Timeline)

### 감염 / 제균 치료 (예: H. pylori)
- 06: 1차 치료 약물 조합 (Regimen Tile)
- 07: 2차/3차 치료 (Regimen Tile)
- 08: 치료-재검사 일정 (Timeline)

### 시술 후 안내 (예: 내시경 후, 용종 절제 후)
- 02: 무엇을 했나 (Hero Number — 시술 시간/제거 개수)
- 06: 시술 후 시간별 주의사항 (Timeline)
- 07: 식이 안내 (Comparison)
- 08: 출혈/통증 자가 관리 (Density Grid 2×2 + alert)

### 검진 / 예방 (예: 5대암 검진)
- 02: 한국 발생률 (Hero Number)
- 04: 검사 종류 (Density Grid 3×2)
- 06: 권장 주기와 대상 (Density Grid 3×2)
- 08: 검진 당일 일정 (Timeline)

### 백신 안내 (예: 대상포진, 폐렴구균)
- 02: 대상자 수치 또는 예방 효과 (Hero Number)
- 03: 질환의 위험성 (Asymmetric Split)
- 06: 백신 종류 비교 (Comparison 또는 Regimen Tile)
- 08: 접종 후 시간별 주의 (Timeline)

## 슬라이드별 콘텐츠 작성 가이드

### Cover (1)
- **타이틀**: 주제 한 줄 + `<em>` 강조 부분 (예: "역류성 식도염<br><em>생활관리 안내</em>")
- **부제**: 한 줄 부연 (1-2 절)
- **챕터 라벨**: `PATIENT EDUCATION · {SPECIALTY}` (예: GASTROENTEROLOGY, CARDIOLOGY)
- **푸터 좌측**: 영문 약어 정의 (예: `GERD · Gastroesophageal Reflux Disease`)
- **푸터 우측**: `광교바른내과 {진료과}`

### Overview / Hero Stat (2)
- 한국 유병률, 위암 위험, 5년 생존율 등 한 가지 핵심 숫자
- 좌측 거대 숫자 + 캡션 (1-2문장)
- 우측 "Why it matters" 3-4문장
- 출처: 가이드라인 + 연도

### Definition (3)
- 핵심 정의를 한 문장 statement로 (em 강조 포함)
- supporting 본문 3-4문장
- 보조 metric 카드 2개 (Diagnostic threshold, Long-term risk 등)

### Symptoms / Diagnosis (4)
- 6항목 권장
- 각 항목 카드 인덱스: `TYPICAL · 01`, `INVASIVE · 01` 등 카테고리 구분
- 각 카드 본문 2-3문장

### Risk Factors / Indications (5)
- 6항목 (4-6 범위)
- 인덱스: `FACTOR · NN`, `STRONG · NN`, `CONDITIONAL · NN`
- 한국 보험 적용 여부 명시 가능

### Treatment / First-line (6)
- 약물 조합이라면 Regimen Tile (3개 옵션 가로 배열)
- 단일 치료 단계라면 Density Grid 2×2 (4개 본문 카드 + alert)
- "PREFERRED" 옵션은 `tile--accent`로 강조

### Comparison / Salvage (7)
- DO/DON'T 비교라면 Comparison (네이비/스틸)
- 2차/3차 치료라면 Regimen Tile

### Schedule / Process (8)
- 정확히 4단계
- 각 단계 제목: `{단계명} · {시점}` (예: `치료 시작 · Day 1`)
- 각 단계 body 1-2문장

### Precautions (9)
- 4개 핵심 규칙 (Density Grid 2×2)
- 응급 상황 안내는 alert-strip으로 카드 아래

### Side Effects / Red Flags (10)
- 6항목 (4 + 2 mixed grid 가능)
- 일반 부작용은 `tile`, 응급 신호는 `tile--alert`
- 인덱스 라벨: `COMMON · NN` vs `RED FLAG · NN`

### Action Checklist (11)
- 7개 항목 + 마지막 안내 1개 (총 8칸 → 4행×2열)
- 각 항목은 한 줄로 끝나는 명확한 행동
- `<strong>` 태그로 핵심 단어 navy 강조

### Closing (12)
- 큰 타이틀 (em 강조 포함, 예: "건강한 식도, <em>편안한 일상</em>")
- 본문은 `closing-grid` 패턴 (좌측 contact-card 세로 stack + 우측 qr-block)
- contact-card 3개 항목: Phone / Address / Specialty (모든 덱 공통, 변경 금지)
- qr-block의 `<div class="qr-block__code">`는 빈 div로 둔다 — 빌드 스크립트가 SVG QR을 자동 삽입
- 챕터 라벨: `END OF DECK · THANK YOU`
- 자세한 HTML 구조는 patterns.md §9 참조

## 의학적 정확성 체크리스트

콘텐츠 작성 시 반드시 확인:

- [ ] 한국 진료지침 또는 보험 기준 반영 (KCD, HIRA, NHI)
- [ ] 의학 용어 영문 병기 (GERD, H. pylori 등)
- [ ] 약물 용량은 한국 처방 가능 용량 기준
- [ ] 출처 명시 (가이드라인명 + 발행연도)
- [ ] 환자 친화적 어투 유지 (전문용어는 영문 병기로 보강)
- [ ] 응급 신호 (Red Flag) 명확하게 구분
- [ ] 자가 약물 중단·자가 진단 위험 안내 포함

## 슬라이드 수 조정

12장이 너무 많으면:
- 03 Definition 생략 (Overview에 포함)
- 09 Precautions와 11 Action Checklist 통합
- 10 Side Effects 생략 (간단한 콘텐츠일 때)

12장이 부족하면:
- 06과 07 사이에 약물별 상세 슬라이드 추가
- 08과 09 사이에 환자 사례 또는 FAQ 슬라이드 추가
- 11 다음에 가족·동거인 안내 슬라이드 추가

단, 어떤 경우든 4-region master grid는 절대 변형하지 않는다.
