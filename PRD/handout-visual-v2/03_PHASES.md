# 03_PHASES — 핸드아웃 v2 단계별 계획

> 각 Phase는 독립 배포 가능. handouts에 먼저 적용 → decks/lab-reports로 확장. 룰은 repo 커밋(push)로 전파.

## Phase 1 — MVP: 이미지 aboutness 게이트 (P1 직격)
**목표**: "겉도는 이미지" 0건. 이미지가 본문을 실제로 설명할 때만 채택.
- [ ] `ImageIntent` 스키마 도입 — 슬롯마다 `explains`/`visual_type`/`must_show`/`prompt_en` 명시(Step 3.5에 강제 필드).
- [ ] **aboutness 교차검증** 단계: 생성 이미지를 VLM에 "이 이미지가 [explains/must_show]를 묘사하는가? 0~100 + 근거"로 질의 → 임계 미달이면 재생성/생략.
- [ ] 완료 보고에 슬롯별 intent·aboutness 점수 표기.
- [ ] 가드: 적합 `visual_type` 없으면 슬롯 생성 금지(텍스트 레이아웃 개선으로 대체) — 기존 §15 룰을 코드 게이트화.
**완료 기준**: 핸드아웃 1건에서 채택 이미지 전부 게이트 통과, 미달은 사유 기록.

## Phase 2 — 안정 생성 루프 (P2)
**목표**: "불안정→생략"을 "안정→채택"으로.
- [ ] imagegen 호출 재시도(≥2) + 후보 2~3장 생성 → aboutness×quality 최고 1장 채택.
- [ ] fallback 체인 명문화: codex_imagen → $imagegen → 명시 생략+사유. 경로/실패를 build_report에 기록.
- [ ] quality 체크 자동화: 한글텍스트 혼입 금지·왜곡·저해상도 탐지(VLM/규칙).
**완료 기준**: 생성 실패 시 자동 재시도·후보비교 동작, 성공률 상승 로그.

## Phase 3 — 레이아웃 회귀 가드 (P3)
**목표**: 이미지 삽입 후 깨짐 0.
- [ ] 삽입 **전/후 스냅샷**(Playwright) → visual diff(겹침·잘림·푸터침범·여백변화) 자동 비교.
- [ ] `_validate_layout` 강화 체크와 AND 게이트 — 둘 다 통과해야 채택. 깨지면 슬롯 크기/배치 자동 보정 후 재검.
- [ ] Step 3.8 전수 육안검수를 **회귀 diff가 가리키는 페이지 우선**으로 보조(육안은 유지).
**완료 기준**: 의도된 시각 회귀를 자동 차단, 오탐 임계 튜닝 완료.

## Phase 4 — 톤·디자인 일관성 스코어 (P4)
**목표**: 자료 간 시각 일관성 측정·강제.
- [ ] `ToneScore`: 색 팔레트 거리·폰트/스케일·이미지 스타일을 brand 토큰과 대조해 점수화.
- [ ] 빌드 게이트에 임계 추가(미달 경고/차단), 완료 보고에 점수.
- [ ] 이미지 스타일 일관성: imagegen 프롬프트에 브랜드 스타일 디스크립터 표준 삽입.
**완료 기준**: 신규 핸드아웃이 톤 임계 통과, 기존 대표자료와 시각 일관.

## Phase 5 — 확장 (decks/lab-reports)
- [ ] Phase 1~4 게이트를 decks(4~6장 룰과 결합)·lab-reports(PII 제한)로 확대.
- [ ] 회귀 테스트(evals)에 aboutness·visual-diff·tone 케이스 추가.

## 의존성
P1 → (P2, P3 병렬 가능) → P4 → P5. P1이 키스톤(intent 스키마가 P2/P3/P4의 입력).
