# Agent Orchestration — Claude ↔ Codex 자동 왕복 (v2, 2026-06-06)

> 이 문서는 **어떤 에이전트가 작업을 주도하든 Step 3.5 이미지 생성과 (옵트인) 병렬 드래프팅이
> 사람 개입 없이 끝까지 진행**되도록 하는 cross-agent 오케스트레이션 사양이다.
> SKILL.md §생성 워크플로우 / §Step 3.5 가 트리거·요약, 본 문서가 상세 룰의 SoT.

## 1. 배경 — 왜 필요한가

`$imagegen` 은 **Codex CLI 내장 기능**이다. 기존 워크플로우는 "Codex 가 슬롯을 설계하고
`$imagegen` 을 직접 호출한다"고 적혀 있어, **Claude 가 주도하는 세션에서는 이미지 생성
시점에 사람이 Codex 로 갈아타야 하는 수동 단계**가 끼어 있었다. 2026-06-06 부터는
Claude 가 `tools/codex_imagen.sh` 로 Codex CLI 를 헤드리스 호출해 같은 일을 자동으로 한다.

역할 분담 원칙 (변하지 않는 것):
- **integrator(주도 에이전트) = 콘텐츠·임상 정확성·최종 결정권.** Multi-Agent Quality
  Pipeline(Stage A~F)의 구조와 specialist 라인업은 그대로다.
- 이미지의 **슬롯 설계·후보 식별·프롬프트 작성 책임도 integrator** 에게 있다 (§3.5.a/b 룰
  전부 적용). Codex 는 "프롬프트 → 래스터 PNG" 변환기로만 쓴다 (위임 모드 제외, §4).

## 2. Driver 감지 — 실행 경로 결정 테이블

세션 시작 또는 Step 3.5 진입 시 integrator 가 다음을 확인한다:

```bash
command -v codex >/dev/null && codex login status >/dev/null 2>&1 && echo CODEX_OK
```

| 주도 에이전트 | codex CLI 상태 | Step 3.5 이미지 생성 경로 |
|---|---|---|
| **Codex** | (자기 자신) | built-in `$imagegen` 직접 호출 (기존 그대로) |
| **Claude** | CODEX_OK | **`tools/codex_imagen.sh <prompt.md> <target.png>` 자동 호출** ← v2 신규 기본값 |
| **Claude** | codex 없음/미로그인 | 이미지 생략 + 각 후보에 `no image added: codex unavailable` 기록. 슬롯 HTML 은 남기지 않는다 (빈 프레임 금지) |

- 경로 선택은 **자동**이다. 사용자에게 "Codex 로 만들까요?" 같은 질문을 하지 않는다.
- exit 3 (codex 없음) → fallback 행. exit 4/5 (생성 실패) → 프롬프트 보강 후 1회 재시도,
  그래도 실패하면 그 이미지만 생략하고 기록한다. 이미지 실패가 자료 전체 push 를 막지 않는다.

## 3. Claude-driver 의 Step 3.5 실행 절차 (표준)

1. §3.5.a 후보 식별 + 내용 적합성 게이트 5줄 작성 (기존 룰 그대로)
2. HTML 슬롯 먼저 + `_validate_layout` 통과 + 슬롯 실측 (§3.5.b — strict ratio, 추정 금지)
3. 이미지별 영문 프롬프트 작성 → `{대상 디렉토리}/{이름}.prompt.md` 로 저장
   (ABSOLUTELY NO TEXT 블록, full-bleed 문구, PII 금지 — 기존 룰 전부 포함해서)
4. 이미지 생성 (2026-06-20 개선):
   - **1장**: `bash tools/codex_imagen.sh <prompt.md> shared/assets/generated/{slug}-{purpose}-YYYYMMDD.png`
     (자동 재시도/백오프 + stale·최소크기·비율 검증 내장)
   - **여러 장 = 병렬+격리**: `bash tools/codex_imagen_batch.sh <p1>'|'<t1> <p2>'|'<t2> ...`
     (또는 `--list <file>`: 줄당 `prompt<TAB>target`). 작업별 임시 CODEX_HOME 격리로 동시 생성
     (`~/.codex/generated_images` 충돌 없음) + sha 고유성 자동 검증. 더 이상 순차 강제 아님.
   - **엔진/폴백**: `CODEX_IMAGEN_ENGINE=auto`(기본). codex 내장 image_gen 이 "이미지는 만들지만
     파일경로 미노출"(degraded) 이면 자동으로 Gemini 폴백(`tools/gemini_imagen_fallback.py`).
     ⚠️ Gemini 폴백은 **이미지 REST quota 있는 정식 GEMINI_API_KEY(AI Studio 발급)** 필요 —
     OAuth 파생 키(AQ.…)는 quota 0(429). 둘 다 막히면 정직하게 exit 5(가짜 이미지 없음).
5. 생성본 Read 로 육안 검수 (구도·여백·텍스트 혼입 여부) → 슬롯 비율 어긋나면 재생성
   (레이아웃을 이미지에 맞추지 않는다)
6. HTML 삽입 → 재빌드·재검증 → push (기존 Step 4)

## 4. (옵트인) Codex 위임 모드 — "품앗이"

기본은 §3 (Claude 가 프롬프트까지 작성). 사용자가 **"품앗이"**, **"병렬로"**, **"외주 돌려"**
라고 명시했을 때만 다음 위임을 허용한다:

- **이미지 프롬프트 위임**: Claude 는 슬롯 실측값 + visual intent 한 줄만 주고, 영문
  프롬프트 작성을 Codex 에 위임 (`codex exec` 프롬프트에 §3.5.b 룰 요약 동봉 필수).
- **병렬 HTML 드래프팅**: 다수 deck/handout 일괄 작업 시 슬라이드/자료 단위로
  `codex exec` 워커에 분배. 단:
  - 워커 산출물은 **초안** — integrator(Claude)가 4-region grid·패턴·브랜드 토큰 준수를
    검수하고 Stage C/D 게이트는 평소대로 전부 통과시켜야 한다.
  - 임상 수치·약물 용량·가이드라인 인용이 들어가는 슬라이드는 위임 금지 (integrator 직접).
  - git 조작(add/commit/push)은 워커에게 절대 위임하지 않는다 — SKILL.md §6 git 룰은
    integrator 단독 책임.

## 5. 환경별 주의사항

- **헤드리스/원격 세션** (텔레그램 브리지 등): AskUserQuestion 류 인터랙티브 도구가 닿지
  않으므로 질문 단계는 생략하고 판단 근거를 결과 보고에 적는다.
- **이미지 생성 시간**: 장당 1~3분. 3장 이상이면 진행 보고(30분 룰)와 별개로 "n/총 생성
  완료" 중간 보고 1회.
- **Codex mirror 동기화**: 본 문서·SKILL.md 변경 후 `bash tools/sync_all_agents.sh` —
  Codex 가 주도하는 세션도 같은 룰 snapshot 을 읽게 한다.
- **비용**: codex exec 호출은 OpenAI 측 토큰을 쓴다. 대량(10장+) 생성 전에는 사용자에게
  장수만 한 줄 고지한다 (확인 대기는 불필요, 고지만).

## 6. 검증된 사실 (2026-06-06, Mac mini)

- `codex login status` → ChatGPT 계정, `codex exec` 헤드리스 정상 (model gpt-5.5)
- `codex features list` → `image_generation stable true` (이미 활성)
- git repo 밖 실행 시 `--skip-git-repo-check` 필요 — 래퍼에 포함됨
- bun 설치 머신 주의: bun 으로 codex 업그레이드 시 네이티브 바이너리 심링크가 node
  래퍼로 롤백됨 → `env: node` 오류가 나면 darwin-arm64 바이너리로 재심링크
