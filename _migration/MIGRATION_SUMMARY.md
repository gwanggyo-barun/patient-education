# 진료 교육자료 마이그레이션 — 종합 작업 리포트

**기간**: 2026-05-07 ~ 2026-05-09
**최종 상태**: ✅ 모든 단계 완료

## 📊 최종 현황

| 분류 | 자료 수 | 라이브 |
|---|---|---|
| 📋 진료 설명용 (decks, 16:9) | 34 | ✅ HTTP 200 |
| 📨 환자 유인물 (handouts, A4) | 18 | ✅ HTTP 200 |
| 🧪 환자 검사결과 (lab-reports, A4) | 14 | ✅ HTTP 200 |
| **합계** | **66** | **66/66** |

## 🔧 시스템 보강 (영구 정착)

### Notion 3-DB 자동 라우팅
build.py 의 kind 필드 기반:
- `decks` → 📋 진료 설명용 자료 DB (`a84f23489d...`)
- `handouts` → 📨 환자 유인물 DB (`920b48c92d...`)
- `lab-reports` → 🧪 환자 검사결과 DB (`c150b47d52...`)

`build.py` 의 `_validate_targets_routing()` 가 빌드 전 자동 검증 — 잘못 분류 시 빌드 실패.

### 디자인 시스템
- `SKILL.md` Alert 룰, 검증 워크플로우, 1페이지 기본 룰
- `shared/_validate_layout.py` 자동 검증 (overflow / footer overlap / 페이지 밖)
- `shared/_build_helpers.py` inject_qr — multi-class div 지원
- 모바일 viewport meta (decks 1280, handouts/lab-reports 794)

## 📦 레거시 정리
- 옛 PDF 첨부 자료들 → 📦 레거시 자료 아카이브 페이지로 통합
- 환자별 개인화 자료 (옛) 도 archive 로 이동
- 진료 설명용 DB 의 36 misclassified rows 정리 (handouts/lab-reports 자료가 잘못 들어왔던 것)

## 🌐 라이브 사이트
- 인덱스: [https://gwanggyo-barun.github.io/patient-education/](https://gwanggyo-barun.github.io/patient-education/) — 66 자료 한눈에 + 모바일 안내
- 카테고리별 직접 URL: `/decks/{cat}/{slug}/`, `/handouts/{cat}/{slug}/`, `/lab-reports/{kind}/{slug}/`

## 📌 노션 메인 페이지 구조 (정돈됨)
- 📋 진료 설명용 자료 DB
- 🧪 환자 검사결과 인포그래픽
- 📨 환자 유인물 / 한장 안내문
- 📦 레거시 자료 아카이브 (참고용)

## 🟡 사용자 직접 검수 필요
[review_queue.md](review_queue.md) — 66 자료 체크박스 + 라이브 URL.
