# Clinic Content System

광교바른내과 환자 교육 슬라이드 덱 생성 시스템 (HTML + PDF, 16:9).

## 빠른 시작

```bash
# 1. 환경 셋업 (최초 1회)
pip install playwright --break-system-packages
playwright install chromium

# 2. 빌드
python build.py
```

산출물:
- `output/{slug}.pdf` — 환자 공유용 PDF (1280×720)
- `output/{slug}-preview.png` — 데스크톱 풀스크린 미리보기

## 새 덱 만들기

1. `decks/{specialty}/{topic}/{slug}/index.html` 생성
2. `reference/content-template.md`의 12장 표준 구성 참조
3. `reference/patterns.md`의 7가지 본문 패턴 참조
4. `build.py`의 `DECKS` 리스트에 새 항목 추가
5. `python build.py` 실행

## 디자인 시스템

색상·폰트·톤 일체는 **`reference/brand-design-system.md`**가 단일 진실의 원천.
이 시스템은 광교바른내과의 다른 스킬(`patient-handout-pdf`, `lab-report-infographic`,
`patient-education-pptx`)도 공유한다.

## 디렉토리 구조

```
clinic-content-system/
├── SKILL.md                       # 스킬 진입점, Claude가 자동 트리거할 때 읽음
├── README.md                      # 이 파일
├── build.py                       # Playwright 빌드 스크립트
│
├── shared/                        # 모든 덱이 공유하는 자산
│   ├── design-tokens.css          # 색상/폰트/간격 변수
│   ├── clinic-slides.css          # 슬라이드 마스터 + 7개 패턴 컴포넌트
│   └── assets/
│       └── clinic_logo.png
│
├── decks/                         # 콘텐츠
│   └── gi/
│       ├── gerd/lifestyle/index.html
│       └── h-pylori/eradication/index.html
│
└── reference/                     # 가이드 문서
    ├── brand-design-system.md     # ★ 모든 스킬 공유, 단일 진실의 원천
    ├── patterns.md                # 7가지 본문 패턴 HTML 가이드
    ├── content-template.md        # 12장 표준 구성
    ├── build.md                   # 빌드 환경 셋업
    └── migration.md               # 기존 3개 스킬 통합 가이드
```

## 핵심 원칙

1. **모든 슬라이드는 4-region master grid** (header / title-block / body / footer) — 위치 일관성 강제
2. **본문은 7가지 패턴 중 하나** — Hero Number, Asymmetric Split, Density Grid, Comparison, Timeline, Checklist, Regimen Tile
3. **컬러는 디자인 토큰만 사용** — Navy + Steel Blue 외 추가 금지
4. **폰트는 Pretendard Variable 단일** (PPTX 환경 fallback: Noto Sans KR)
5. **표지 외 슬라이드에 그라데이션 배경 금지**

## 검증된 덱

- ✅ `gi/gerd/lifestyle` — 역류성 식도염 생활관리 (12장)
- ✅ `gi/h-pylori/eradication` — H. pylori 제균 치료 (12장)

## 참고 문서

- 새 콘텐츠 만들기 전: `reference/brand-design-system.md` → `reference/content-template.md` → `reference/patterns.md`
- 빌드 환경 문제: `reference/build.md`
- 기존 PPTX 스킬 마이그레이션: `reference/migration.md`
