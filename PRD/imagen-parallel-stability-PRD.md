# PRD — codex_imagen 속도(병렬) · 안정성 개선

## 0. 한 줄
clinic 덱 이미지 생성(`tools/codex_imagen.sh`)을 **CODEX_HOME 격리 병렬**로 N장 동시 생성 + **재시도/백오프 + 비율·고유성 검증**으로 만들어, 4장 순차 8~12분 → 병렬 2~3분 + "조용한 실패/stale/뒤섞임" 0.

## 1. 배경 / 문제 (오늘 실측)
- 현 `codex_imagen.sh`는 **순차 전용**(헤더 경고): codex가 생성 원본을 **공유 폴더 `~/.codex/generated_images/`**에 떨궈, 병렬 시 서로 최신 파일을 집어가 뒤섞임(2026-06-12 ABYSS 사고).
- 2026-06-19 stale 픽스(타깃 rm + mtime 검증)는 들어갔으나, **속도(순차)·재시도 부재·비율 검증 부재**가 남음.
- 6/19 MASLD 덱: ①② 성공 후 ③/④가 back-to-back에서 튕김(레이트리밋 아님, codex가 디스크 미저장 간헐 현상 → wrapper exit 5). 단독 재시도하면 됨 → **재시도/백오프 + 병렬 격리**가 정답.

## 2. 목표 / 비목표
**목표**
1. **병렬 생성 + 격리**: 호출별 독립 CODEX_HOME → generated_images 충돌 0 → N장 동시.
2. **재시도/백오프**: 일시 실패(디스크 미저장/exit 5·6) 시 K회 백오프 재시도(즉시연타 금지).
3. **검증 강화**: 생성 이미지의 (a) 차원/비율이 프롬프트 `aspect ratio strictly WxH`와 근사 일치 (b) 배치 내 sha1 전부 고유(뒤섞임 탐지) (c) 최소 크기(>50KB, 코드-fallback 아님).
4. **기존 순차 경로·호출 시그니처 무파괴**(하위호환): `codex_imagen.sh <prompt> <target>` 그대로 동작.
**비목표**
- codex 자체/로그인 방식 변경, OpenAI 키 도입(불필요 — CLI 로그인으로 동작), 이미지 후처리 도입.

## 3. 설계
### A. `codex_imagen.sh` (단일, 하위호환 유지)
- **CODEX_HOME 존중**: 이미 env CODEX_HOME 있으면 그대로 사용(격리는 호출자가 주입). 없으면 기본.
- **재시도 루프**: 환경변수 `CODEX_IMAGEN_RETRIES`(기본 3), `CODEX_IMAGEN_BACKOFF`(기본 20s, 지수). 각 시도 = (타깃 rm) → codex /imagen → 존재+mtime+크기 검증. 실패 시 backoff 후 재시도. 전부 실패면 exit 5(정직).
- **비율 검증(옵션·경고)**: 프롬프트에서 `aspect ratio strictly (\d+)\s*[x:×]\s*(\d+)` 파싱 → 생성 PNG 차원 비율과 ±5% 비교, 어긋나면 stderr 경고(차단은 아님 — 일부 모델 clamp).
- **stale 차단 유지**: 타깃 rm + mtime≥호출시작.

### B. `codex_imagen_batch.sh` (신규 — 병렬+격리 오케스트레이터)
- 입력: `prompt1:target1 prompt2:target2 ...`(인자) 또는 `--list file`(줄당 `prompt\ttarget`).
- 각 작업마다 **임시 CODEX_HOME 생성**: `mktemp -d` → 실제 `~/.codex`의 `auth.json`·`config.toml`(있으면) **심링크**(creds 복사 금지) → 그 home에 codex가 generated_images를 따로 떨구게.
  - ⚠️ **선결 실증 필요**: codex가 generated_images를 CODEX_HOME 하위에 쓰는지 vs 항상 리터럴 ~/.codex인지 — 빌드 단계에서 테스트로 확인하고, 격리가 안 되면 폴백(작업별 생성 직후 즉시 고유파일명 캡처 + 동시성 1로 강등).
- **동시성 캡** `CODEX_IMAGEN_CONCURRENCY`(기본 4).
- 각 작업 = `CODEX_HOME=<tmp> codex_imagen.sh <prompt> <target>` 백그라운드.
- 전부 대기 → **배치 검증**: 각 타깃 존재 + sha1 수집 → **전부 고유**인지(중복=격리 실패) + 차원 로그.
- 임시 CODEX_HOME 정리(trap).
- 보고: per-target 성공/실패·sha·차원, 총 소요.

## 4. 수용 기준
1. `codex_imagen.sh <p> <t>` 단일 호출 = 기존과 동일 동작(하위호환), 실패 시 백오프 재시도 후 정직 실패.
2. `codex_imagen_batch.sh` 로 **2장 이상 동시 생성** → 결과물 **sha1 전부 고유**(뒤섞임 0), 각 비율 프롬프트와 근사 일치.
3. 격리 실증: CODEX_HOME 분리 시 generated_images 충돌 없음 확인(또는 폴백 동작 확인).
4. **실제 검증**: MASLD ④(미생성분) 포함 이미지들을 batch로 생성해 4/4 채움 + sha 고유 확인.
5. 기존 덱 빌드/순차 경로 무파괴.

## 5. 작업 순서
1. (실증) CODEX_HOME 격리 시 generated_images 위치 테스트.
2. codex_imagen.sh 개선(재시도·비율검증, 하위호환).
3. codex_imagen_batch.sh 신규.
4. **Codex 적대적 검수** → 반영.
5. 실제 병렬 생성 검증(MASLD 이미지).
6. SKILL/agent-orchestration 문서에 "병렬+격리 = batch 사용" 반영 + 레포 커밋.

## 6. 안전
- creds(auth.json)는 **심링크만**(복사 금지). 임시 CODEX_HOME는 trap으로 정리.
- 순차 단일 경로 무파괴(하위호환). 격리 실패 시 자동 폴백(동시성1).
- 레포 SoT: `tools/`·SKILL.md·reference/agent-orchestration.md. 단독 커밋.

---

## 7. 검증 결과 (2026-06-20 야간 자율작업 — Claude 빌드 → Codex 적대검수 → 반영 → 검증)
- **CODEX_HOME 격리 실증 ✅**: `CODEX_HOME=/tmp/cdxtest`(auth/config 심링크)로 codex 실행 시 codex가 그 홈을 정상 사용(전체 구조 생성). → 작업별 임시 홈 격리 = 병렬 가능.
- **🔴 ③④ 실패 진짜 원인 규명**: 레이트리밋·back-to-back 아님. codex 내장 `image_gen`이 "이미지는 대화에 생성하나 **원본 PNG 파일경로를 노출하지 않는** degraded 모드"로 전환됨 → wrapper가 복사할 원본이 없어 실패. codex 로그가 직접 보고("OPENAI_API_KEY 없어 fallback 불가"). 같은 날 ①②③는 경로노출 regime이라 성공 → **두 regime 공존**.
- **codex_imagen.sh 개선 ✅**(하위호환): 재시도/백오프 + stale(mtime) + 최소크기 + 비율경고 + **degraded 로그 감지 시 재시도 중단→폴백** + `CODEX_IMAGEN_ENGINE=auto|codex|gemini` 디스패치. 성공 로그 정리.
- **codex_imagen_batch.sh 신규 ✅**: 작업별 임시 CODEX_HOME 격리 병렬 + 동시성캡 + sha고유성 검증 + 중복타깃 거부. `wait -n`(bash3.2 미지원) 제거→폴링. features.json 심링크 제거(race 방지, Codex #3).
- **gemini_imagen_fallback.py 신규 ✅**: GEMINI_API_KEY로 image 모델 호출→inline bytes 저장. **폴백 배선 end-to-end 검증**(ENGINE=gemini 실행→헬퍼 호출→정직 실패까지 동작).
- **⚠️ 미완(키 의존, 사용자 결정 필요)**: 오늘 ④ 실생성 실패 — codex degraded + **현 Gemini 키 quota 0(429, OAuth파생키 image REST 미지원)**. 둘 다 막혀 어떤 엔진으로도 못 만듦. 해결: (a) AI Studio 정식 GEMINI_API_KEY 발급(권고, 키만 바꾸면 폴백 즉시 동작) (b) OPENAI_API_KEY(사용자 거부) (c) codex 경로노출 regime 복구 대기. → MASLD 덱은 3/4(④ 슬롯 비율 준비됨, 키 생기면 1줄로 채움).
- **Codex 적대검수 반영**: #1 프롬프트 CODEX_HOME 격리문구, #3 features.json race, #5 wait-n, #7 중복타깃, #8 비율파서, #9 로그누수, #10 degraded감지→폴백 — 전부 반영. (미반영: #6 원본경로 자기홈 검증, #2 사전 probe = 차기 개선.)
