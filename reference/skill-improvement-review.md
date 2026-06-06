# 스킬 자동 개선 리뷰 태스크 (다중 에이전트 · 통합 시스템 버전)

> **출처/이관**: 사용자가 맥북 데스크톱 앱에서 운영하던 루틴을 2026-06-06 텔레그램으로 전달 — Mac mini로 이관.
> **mini 적응 노트**: ① 스킬 베이스 경로는 맥북의 `~/Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/...` 대신 **이 repo (`~/clinic-content-system/`)가 Tier 1 본체** — SKILL.md·build.py·shared/가 SoT. wrapper/legacy 스킬이 mini에 없으면 해당 Tier는 "없음 — 스킵"으로 보고. ② `logs/improvement-log.jsonl`이 repo에 없으면 생성부터 제안. ③ 모델 규칙 "opus" = 현재 opus-4-8. ④ 보고는 텔레그램(chat_id 1592979427)으로, 승인 후에만 파일 수정 (원칙 유지).

## 원칙
- 모든 에이전트는 model: "opus" 사용 (사용자 명시 규칙)
- 병렬 에이전트는 한 메시지에 동시 호출, run_in_background: true
- 각 에이전트는 독립 판단. 프롬프트에 "다른 에이전트 결과를 참고하지 말고 독립 판단하라" 명시
- 사용자 승인 없이 스킬 파일 수정 금지

## 검토 대상 4개 스킬 (3-tier 구조)

| Tier | 스킬 | 역할 | 검토 깊이 |
|---|---|---|---|
| 1 (메인) | clinic-content-system/ | 통합 빌드 시스템 — decks/handouts/lab-reports 전부 여기서 실제 생성 | 전체 에이전트 적용 |
| 2 (wrapper) | patient-handout-pdf/, lab-report-infographic/ | entry point trigger only, clinic-content-system으로 위임 | trigger 정확도 + 위임 명확성만 검토 |
| 3 (legacy) | patient-education-pptx/ | PPTX 명시 요청 시만 사용 | 최근 사용 흔적 있을 때만 검토 |

로그 SoT:
- Tier 1·2의 모든 콘텐츠 생성 로그는 `clinic-content-system/logs/improvement-log.jsonl`에 통합 기록 (wrapper에서 위임 시에도 여기 기록)
- Tier 3 (pptx legacy)는 자기 자신의 logs/improvement-log.jsonl 사용
- 각 스킬의 logs/last-review-date.txt, `logs/originals/`도 유지

## Step 0 · 모드 결정
오늘 날짜 확인 (`date +%Y-%m-%d`, `date +%u`, `date +%d`, `date +%m`).
- 분기 모드 (1/4/7/10월 첫 금요일): 주간 6 + 월간 2 + 분기 1 = 9 에이전트
- 월간 모드 (그 외 달의 첫 금요일, 즉 day ≤ 7): 주간 6 + 월간 2 = 8 에이전트
- 주간 모드 (그 외 금요일): 6 에이전트

## Step 1 · 공통 사전 준비
확인할 파일: 통합 로그(improvement-log.jsonl), SKILL.md, HANDOFF.md/SESSION-HANDOFF.md, README.md, build.py, shared/(디자인 토큰), wrapper SKILL.md 2종, legacy 로그·SKILL.md, 각 logs/last-review-date.txt·logs/originals/.

스킵 조건: Tier 1·2 통합 로그에 지난 리뷰 이후 새 항목이 없고 Tier 3 legacy 로그도 새 항목이 없으면 → "새 로그 없음 — 리뷰 건너뜀" 보고 후 종료. (단, 월간/분기 모드일 때는 로그가 없어도 wrapper trigger 정확도 점검과 SKILL.md 간결화 검토는 진행 — 에이전트 5·6·8 일부)

## Step 2 · 병렬 에이전트 발사

### 🔍 에이전트 1 — 평가자 (Evaluator) · Explore
로그 기반 패턴 분석만, 수정안 금지. 통합 로그를 콘텐츠 타입(decks/handouts/lab-reports)별로 분리해 패턴 분석. 출력 JSON: by_type별 {top_issues, trend, critical} + legacy {top_issues, trend, usage_frequency, critical}.

### 💡 에이전트 2 — 제안자 (Proposer) · general-purpose
SKILL.md + HANDOFF + wrapper 2종 + legacy SKILL.md와 최근 30일 로그·diff-feedback을 분석해 구체적 수정 diff 초안. 우선순위 (a) 본체 (b) wrapper trigger description 정확도 (c) legacy는 사용 빈도 낮으면 무시 가능. 각 제안: 파일 경로 / 변경 전후 / 근거 로그 ID / 임팩트(1-5). 파일 수정 금지 — 초안만.

### ✅ 에이전트 3 — 검증자 (Verifier) · Explore
최근 산출물(타입별 최신 5개, legacy 3개)이 현재 규칙대로 나왔는지: 디자인 토큰(Navy #003366, Steel Blue #5B9BD5, Pretendard), QR 자동 생성(.qr-mini__code/.qr-block__code), OG meta 7개, 페이지 포맷(A4 세로/16:9 1280×720), footer 클리닉 정보+면책. 출력: ✅ 준수 / ❌ 위반(파일명+규칙) / ⚠️ 규칙 모호.

### 🗣️ 에이전트 4 — 반대자 (Devil's Advocate) · Explore
수정 제안에 반대할 근거 선정리: (1) 기존 규칙 충돌 (2) 특정 케이스 일반화 위험 (3) 과거 시도 이력 (4) 간결성 훼손 (5) wrapper에 본체 규칙 중복 안티패턴. 공격적으로 반박.

### ✂️ 에이전트 5 — 간결화 전문가 (Simplifier) · Explore
SKILL.md 비대화 감시: 본체(중복·죽은 규칙·병합 가능 규칙·description 길이), wrapper(본체 규칙 유입=위임 깨짐 — wrapper는 trigger+위임 한 줄+출력 위치만), legacy 비대화. 삭제 후보·병합 후보 구체 제시.

### 🏥 에이전트 6 — 환자 시뮬레이터 (Patient Simulator) · Explore
의학 지식 없는 60대 환자/보호자 페르소나로 최근 산출물(타입별 1-2개) 읽기: 어려운 용어 / 글씨·가독성 / 흐름 / "뭘 해야 하는지" 명확성 / 막히는 섹션 / 타입 간 톤 일관성. 구체 인용 지적.

### 🔄 에이전트 7 — 회귀 감시자 [월간] · Explore
지난 2-4주 SKILL.md 변경 이력(git log)과 이후 로그 교차 검증. wrapper trigger 충돌·위임 깨짐 의심. "지난달 X 변경 → 이번달 X 이슈" 인과 의심을 원인 가설과 함께 보고.

### 🔗 에이전트 8 — 크로스 스킬 조정자 [월간] · Explore
수평 비교: 3개 콘텐츠 타입 간 동일 개념 처리 차이(용어·색·글씨·footer), wrapper trigger 키워드 겹침/라우팅 모호성, legacy 좋은 패턴 이식, 타입 간 패턴 이식.

### 📊 에이전트 9 — 벤치마커 [분기] · general-purpose
동일 샘플 입력(타입별 1건 + 옛 pptx 입력 1건)을 3개월 전 SKILL.md 버전(git 임시 체크아웃 — 원본 디렉토리 금지, 임시 디렉토리 복사)과 현재 버전으로 각각 생성 → 시각·텍스트 비교 → ✅ 개선 / ⚠️ 미미(롤백 검토) / ❌ 악화(즉시 롤백). before/after 스크린샷 경로 포함 보고.

## Step 3 · 종합 및 충돌 해결
1. 합의점 매트릭스 (다수 에이전트 공통 지적 = 고신뢰)
2. 충돌점 (제안자 vs 반대자/검증자) → 각 주장 요약 후 판정
3. 우선순위 = 심각도 × 빈도 × 합의 수, 상위 5개. 본체 > wrapper
4. 환자 시뮬레이터 경고 별도 강조
5. wrapper 슬림성 위반 별도 강조 — 즉시 정리 후보

## Step 4 · 사용자 보고 (텔레그램)
형식: "스킬 자동 개선 리뷰 보고서 (YYYY-MM-DD) — [주간|월간|분기] 모드" / 📊 분석 요약(에이전트 N, 신규 로그 타입별 건수) / 🎯 고신뢰 개선 제안 Top 5 (Tier·파일·변경안·근거 에이전트·임팩트·리스크) / 🏥 환자 관점 경고 / 🪶 Wrapper 슬림성 / ⚔️ 주요 충돌점 / ✂️ 간결화 후보 / 🔄 회귀 의심 [월간] / 🔗 크로스 스킬 [월간] / 📊 벤치마크 [분기] / ✅ 요청: (1) 전체 승인 (2) 항목별 선택 (3) 반려.

## Step 5 · 승인 후 적용
승인 항목만 반영 + 커밋·푸시(스킬 SoT 룰). 각 스킬 logs/last-review-date.txt 갱신. 보류 항목은 다음 리뷰 재검토 목록에 기록.

## 주의사항
- 에이전트는 읽기 위주 (제안자·벤치마커만 general-purpose)
- 벤치마커는 임시 디렉토리 사용 — 스킬 디렉토리 직접 수정 금지
- 모든 에이전트 프롬프트에 "다른 에이전트 참고 금지, 독립 판단" 명시
- 6명 이상 동시 병렬 시 리소스 이슈 있으면 3+3 2웨이브 분할
- wrapper는 항상 슬림 유지 — 본체 규칙 복사 금지
- legacy pptx 사용 빈도 모니터링 — 6개월 이상 미사용 시 deprecation 검토 보고
