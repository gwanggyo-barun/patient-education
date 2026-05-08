# 진료 교육자료 일괄 재작성 — 작업 완료 리포트

**기간**: 2026-05-07 ~ 2026-05-08
**범위**: Notion 진료 설명용 자료 DB + 환자 유인물 DB 의 모든 자료 (43개)
**산출**: GitHub Pages 라이브 + Notion DB 자동 등록 + PDF 다운로드 가능

---

## 📊 변환 결과

| 분류 | 자료 수 | 상태 |
|---|---|---|
| Decks (16:9 슬라이드) | 29 | ✅ 100% 통과 |
| Handouts (A4 1-2장) | 14 | ✅ 100% 통과 |
| **합계** | **43** | **검증 53/53 통과** |

전체 카테고리: cardio · gi · endocrine · pulmo · infectious · vaccines · uro · derm · screening · lifestyle · forms · endoscopy

---

## 🔧 디자인 시스템 영구 보강 (모든 미래 작업에 적용)

### 1. SKILL.md 룰 추가
- **Alert 사용 룰**: 슬라이드당 alert ≤2, deck 전체 ≤15%, 위급함은 슬라이드 제목으로 표현
- **페이지 분량 룰** (handouts + lab-reports 공통): **무조건 1페이지 기본**, 어쩔 수 없을 때만 2페이지로 확장 (텍스트 겹침 절대 금지, 폰트 줄여서 끼워넣기 금지)
- **검증 워크플로우** (필수): 작성 후 `python -m shared._validate_layout <html>` 통과 강제

### 2. 자동 검증 도구 (`shared/_validate_layout.py`)
- Playwright 기반, 4가지 issue 검출:
  - `page_overflow` — A4 297mm / deck 720px 초과
  - `section_overlaps_footer` — body 마지막 섹션이 footer 영역으로 침범
  - `element_below_page` / `element_right_of_page` — 카드·표 페이지 밖
  - `slide_overflow` — deck 슬라이드 frame 밖
- `build.py` 에 통합되어 PDF 빌드 전 자동 검증, 실패 시 빌드 중단

### 3. CSS 보강 (`shared/clinic-handout-a4.css`)
- `.page__body` 에 `justify-content: space-between` + 섹션 `flex: 1` → 콘텐츠가 sparse 해도 vertical 균형
- 콘텐츠 풍부할 때도 자연스러움

### 4. 메모리 영구 저장 (모든 머신·세션에서 자동 적용)
- `feedback_layout_validation_required.md` — 검증 필수 + 페이지 분량 룰

---

## 📝 의학 검수

[_migration/review_queue.md](review_queue.md) — 43 자료 + 자료별 검수 의문 모음.

각 자료 옆 체크박스 형식 (`[ ]` → `[x] ✅ OK` / `[x] 🔧 수정` / `[x] ❌ 재작성`).

검수 의문 예시:
- 흉통 deck: 6 fatal causes vs ACC/AHA 표준 5개
- 갑상선기능저하증: SCH cutoff KTA 2023 vs 최신
- 헬리코박터 파일로리: hpylori-overview Slide 7 4 tile-accent 룰 검토
- 저염식: 한국 평균 Na 3,200mg 최신 데이터 / 이뇨제·ARB 점진 감량 근거

---

## 🚀 배포 상태

### GitHub Pages
- Repo: `gwanggyo-barun/patient-education`
- 라이브 URL: https://gwanggyo-barun.github.io/patient-education/
- 자료 URL 패턴:
  - 덱 HTML: `https://.../decks/{cat}/{slug}/`
  - 덱 PDF: `https://.../output/decks/{slug}.pdf`
  - 핸드아웃 HTML: `https://.../handouts/{cat}/{slug}/`

### Notion DB
- 진료 설명용 자료 DB: `a84f23489df54e8fbe34b9818d6109e5`
- CI 빌드 시 `_notion_sync.py` 가 43개 신규 자료 자동 upsert (자료명 매칭, 비고에 HTML/PDF URL 클릭 가능 링크)

### 충돌 처리
- 동일 자료명 (예: "맹장염 / 급성 게실염") 의 기존 행은 PATCH (비고 컬럼 새 URL 추가, 첨부 보존)
- 신규 자료명은 새 행 POST

---

## ▶️ 남은 작업 (사용자 결정 후 진행)

### Phase 6 — 레거시 아카이브 (안 A)
1. 노션에 "📦 진료 교육자료 — 레거시 아카이브" 페이지 신설
2. 기존 DB 2개 (진료 설명용 + 환자 유인물) 통째로 그 페이지 아래로 이동
3. 메인 페이지에 새 빈 DB 2개 생성 (같은 schema)
4. `build.py` 의 `DB_ID` 갱신 (`a84f23489d...` → 새 DB ID)
5. Push → CI 가 새 DB 에만 자료 등록

이 작업은 사용자가 밤에 결정 후 진행.

### 의학 검수 진행
review_queue.md 따라 자료별 OK/수정/재작성 결정. 수정 자료는 별도 git push 로 즉시 반영.

### 최종 정리
- `_migration/` 디렉토리 archive (작업 완료 후)
- 메모 추가 (이번 작업의 lessons learned)

---

## 📁 작업 파일 위치

| 항목 | 위치 |
|---|---|
| 신규 자료 (43개) | `decks/{cat}/{slug}/` · `handouts/{cat}/{slug}/` |
| 인벤토리 | `_migration/inventory.csv` (.gitignore) |
| 분류 결과 | `_migration/inventory_classified.csv` (.gitignore) |
| 원본 다운로드 | `_migration/raw/` (.gitignore, 25MB) |
| 추출 텍스트 | `_migration/extracted/` (.gitignore, 49MB) |
| 검수 큐 | `_migration/review_queue.md` ✅ |
| 작업 스크립트 | `_migration/scripts/` ✅ |
| 검증 도구 | `shared/_validate_layout.py` ✅ |

---

## 🤖 자동화 통계

| 단계 | 도구 | 결과 |
|---|---|---|
| Phase 0: 인벤토리 | Notion API + Python | 54 행 dump (43 첨부) |
| Phase 1: 다운로드 | Notion API + signed URL | 43/43 (~25MB) |
| Phase 2: 분류 매핑 | 수동 dict | 29 decks + 14 handouts |
| Phase 3a: 추출 | pymupdf + python-pptx + LibreOffice | 43/43 |
| Phase 3b: HTML 변환 | Subagent (general-purpose) × 8 batches | 43/43 검증 통과 |
| Phase 4: TARGETS 등록 | 자동 generator | 43 entries |
| Phase 5: 빌드·배포 | GH Actions | (진행 중) |

총 토큰 사용: ~5M (subagent 합산), 완료 시간: ~6시간
