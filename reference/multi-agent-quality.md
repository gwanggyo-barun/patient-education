# Multi-Agent Quality Pipeline — Integrator Spec

> 광교바른내과 환자 교육 콘텐츠 (`clinic-content-system`) 의 멀티 에이전트 품질 파이프라인 *상세 사양*.
> SKILL.md 의 "Multi-Agent Quality Pipeline" 섹션이 *trigger·요약*, 본 문서가 *상세 룰* 의 Source of Truth.

## 1. 파이프라인 단계

```
Stage A — Planning           (specialist 병렬, planning 모드)
   ↓
Stage B — Drafting           (integrator 만 파일 수정)
   ↓
Stage C — Deterministic gate (build.py + _validate_layout + _visual_audit)
   ↓
Stage D — Critique           (specialist 병렬, critique 모드)
   ↓
Stage E — Integrator revision (evidence 기반 fix)
   ↓
Stage F — Final verification + push
```

- Stage A 와 Stage D 만 specialist (LLM) 가동.
- Stage C 와 Stage F 의 검증은 *결정적 도구* (Python). LLM 호출 없음.
- Stage B 와 Stage E 는 *integrator (메인 호출 Claude)* 가 수행. specialist 의 산출물을 *참고* 하지만 *반드시 따르지 않는다* — 최종 결정권은 integrator.

## 2. 콘텐츠 타입별 specialist 라인업

기본 모드 (default — 일반 콘텐츠 작성 시 자동 가동):

| kind | Stage A · D specialist (병렬) |
|---|---|
| `decks` | clinical-accuracy + patient-readability + visual-design + **narrative-flow** = 4 |
| `handouts` | clinical-accuracy + patient-readability + visual-design + **density-hierarchy** = 4 |
| `lab-reports` (단일 패널) | clinical-accuracy + patient-readability + visual-design + **data-accuracy** + **privacy-ops** = 5 |
| `lab-reports` (`topic=health-checkup`) | 위 5인 + **checkup-extraction** + **checkup-completeness** = 7 (혼합 입력 추출·모듈 누락·follow-up·신호등 일관성) |

고품질 모드 (사용자가 "고품질" / "정확하게" 등 명시):

- 기본 + Stage D-E 2회차 cross-check 1회 추가 (총 2 iterations).

극한 모드 (사용자가 "최고 퀄리티" / "학회용" / "언론용" 등 명시):

- 기본 + 2회차 cross-check 1회 + 외부 가이드라인 search agent (clinical-accuracy 가 `[needs-verification]` 태그 단 항목에 한해 별도 search 호출). 총 3 iterations max.

빠른 모드는 없음 — 품질 보호가 본 파이프라인의 가치이므로 specialist skip 옵션 미제공. 단 `target_audience: "clinician"` 일 때 patient-readability 만 자동 skip.

## 3. 호출 환경 (Claude Code 기준)

integrator 가 specialist 를 호출할 때:

```
Agent(
  description: "Clinical accuracy critique for {topic}",
  subagent_type: "general-purpose",   # Claude Code 환경. Tools:* + in-process (worktree X). "claude" 타입은 FleetView 함대 에이전트 — worktree isolation 강제이므로 비-git cwd 에서 실패. Codex 등은 그쪽 best reasoning model.
  prompt: """
{specialist 의 reference/quality-agents/*.md 의 'Stage A' or 'Stage D' 섹션 텍스트}

## 입력 컨텍스트
stage: critique
kind: handouts
topic: gerd-lifestyle
doctor_input: |
  {원장님 한국어 원문}
html: |
  {작성된 HTML}
validate_layout_output: |
  {python3 -m shared._validate_layout 출력}
"""
)
```

병렬 호출은 *한 메시지 안 여러 Agent 호출* 로 가동 — Stage A/D 에서 모든 specialist 가 동시 시작.

### 모델 capability 룰

- **모델 ID 하드코딩 금지** — `model: "claude-opus-4-7"` 같은 명시 X. 사용 호스트의 default 또는 *available strongest reasoning model* 을 사용.
- vision 필요 specialist (visual-design, data-accuracy preview attach 시) 만 vision 지원 모델 필수. 모델이 vision 미지원이면 integrator 가 그 specialist 호출 자체를 skip.

## 4. Specialist 산출물 강제 스키마

모든 specialist 가 **반드시** 다음 JSON 으로 응답한다. integrator 는 JSON parse 실패하면 *retry 1회*, 그래도 실패면 그 specialist 의 critique 만 skip (다른 specialist 결과는 사용).

```json
{
  "agent": "clinical-accuracy",
  "stage": "planning" | "critique",
  "findings": [
    {
      "severity": "blocker" | "major" | "minor" | "nit",
      "affected_section": "slide 3 / Definition card 2",
      "evidence": "출처·근거 인용 (가이드라인 등). PII 인용 금지.",
      "fix_suggestion": "구체적 fix. PII 인용 금지.",
      "confidence": 0.0
    }
  ],
  "summary": "한 줄 요약. PII 인용 금지."
}
```

### Severity 의미 (모든 specialist 공통)

| 등급 | integrator 기본 반응 |
|---|---|
| `blocker` | 무조건 fix. push 차단. |
| `major` | 일반적으로 fix. evidence 약하거나 다른 specialist 와 충돌하면 reject 가능. |
| `minor` | integrator 판단. 시간 여유 있고 confidence 높으면 fix, 아니면 log 만 |
| `nit` | 기본 reject. 사용자가 fix 요청하면 fix. |

### 충돌 해소 우선순위 (specialist 끼리 의견 다를 때)

```
clinical-accuracy > patient-readability > visual-design > narrative-flow / density-hierarchy / data-accuracy > privacy-ops*

* privacy-ops 의 blocker 는 절대 우선 — push 차단 권한
```

예: clinical-accuracy 가 "이 한국 가이드라인 표현을 그대로 둬야 정확" 이라고 하고, patient-readability 가 "환자 못 알아듣는다" 라고 하면 → 둘 다 만족하는 fix (원문 표기 + 환자 풀이 괄호) 를 integrator 가 제안.

## 5. Integrator 룰 (메인 Claude 가 따른다)

### Stage A → Stage B 사이

1. Specialist 산출물 모두 모은 후 *통합 기획서 (한국어)* 작성 — 환자에게 어떤 핵심 메시지를, 어느 패턴으로, 어떤 강조를 줄지.
2. 통합 기획서를 사용자에게 *한 번* 보여주고 짧은 OK / 수정 요청 받음 (긴 자료일 때 — 핸드아웃 짧은 자료는 skip 가능).
3. HTML 작성 (기존 워크플로우 Step 2).

### Stage C (build) 가 fail 했을 때

- specialist 호출하지 않음. integrator 가 즉시 build error 읽고 fix → 재빌드.
- build pass 후에야 Stage D 호출.

### Stage D → Stage E 사이

1. Specialist 산출물 모두 수신.
2. PII redact 거쳐 `_local/quality-logs/critique-{date}.jsonl` 에 추가 (자세한 룰은 §6).
3. Severity sort: blocker → major → minor → nit.
4. blocker / major fix.
5. Stage D 재호출 (Stage F 직전 마지막 한 번).

### 반복 종료 조건

| 모드 | Stage D-E max iterations | 종료 조건 |
|---|---|---|
| 기본 | 1 | blocker 0 개 |
| 고품질 | 2 | blocker + major 0 개 |
| 극한 | 3 | blocker + major 0 개 + [needs-verification] 모두 해결 |

max 도달 후에도 blocker 남아있으면 *사용자에게 보고* 후 결정 받음 (push 강행 / 추가 수정 / 자료 보류).

### Stage F

1. `python3 -m shared._validate_layout` — 통과 확인
2. `python3 build.py` — preview.png 재생성
3. **A4 콘텐츠 (handouts / lab-reports) 는 preview.png 를 `Read` 도구로 직접 시각 확인** (메모리 룰)
4. lab-reports 한정: PII 한 번 더 검사 — slug hash 형식, og meta, 커밋 메시지
5. push (다른 세션 작업물 보호 — 명시적 stage 만)

## 6. Logging (PII redaction)

### 위치

- `_local/quality-logs/critique-{YYYY-MM-DD}.jsonl` — gitignored, repo 밖으로 안 나감
- `_local/quality-prompts/` / `_local/quality-runs/` — 실행 시 렌더된 specialist prompt 를 보관해야 할 때만 사용
- `_local/` 디렉토리는 `.gitignore` 에 등록

`reference/quality-agents/` 는 정적 prompt 템플릿 전용이다. doctor_input, 작성된 HTML, 검사 수치, 환자별 preview 경로가 합쳐진 실행 prompt 는 public repo 에 커밋될 수 있는 위치에 저장하지 않는다.

### Redaction 룰

저장 전 다음 패턴을 `[REDACTED]` 으로 치환:

| 패턴 | 정규식 / 휴리스틱 |
|---|---|
| 차트번호 | `\[(\d{4,6})\]` (예: `[12345]`) → `[REDACTED-CHART]` |
| 환자명 | TARGETS 항목의 `patient_name` 필드 값 일치 → `[REDACTED-NAME]` |
| 전화번호 | `\d{3}-\d{3,4}-\d{4}` → `[REDACTED-PHONE]` |
| 주민번호 | `\d{6}-\d{7}` → `[REDACTED-RRN]` |
| 생년월일 (8자리 + 한글 출생) | `(19|20)\d{2}[-./]?\d{2}[-./]?\d{2}` → `[REDACTED-DOB]` |
| 이메일 | `[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+` → `[REDACTED-EMAIL]` |

Redaction 은 `tools/quality_gate.py` 의 `redact_pii()` 함수가 수행.

### Schema

```json
{
  "timestamp": "2026-05-15T10:23:45+09:00",
  "topic_slug": "diabetes-screening",
  "kind": "lab-reports",
  "stage": "critique",
  "iteration": 1,
  "specialists": [
    {
      "agent": "data-accuracy",
      "findings_count": {"blocker": 1, "major": 0, "minor": 2, "nit": 0},
      "summary_redacted": "LDL 수치/색 불일치 1건 blocker, [REDACTED-CHART] eGFR 행에 next-step 누락 1건 minor."
    }
  ],
  "integrator_decision": {
    "fixed": 1,
    "rejected": 2,
    "deferred": 0
  }
}
```

Findings 본문 전체는 *저장하지 않음* — count + redacted summary 만. 본문이 필요하면 그 세션 안에서만 메모리에 보관.

## 7. 자주 잡히는 anti-pattern (integrator 가 사전 회피)

| 패턴 | 회피책 |
|---|---|
| Stage D 가 매번 같은 blocker 잡음 (예: HbA1c 풀이 누락) | Stage B 작성 시 자동으로 첫 등장 풀이 삽입 → 다음 critique 에서 안 잡힘 |
| Stage A 통합 기획서를 사용자에게 안 보여주고 바로 작성 → 사용자가 "방향이 달라" 후반에 reject → 전체 재작업 | 통합 기획서 한 번은 보여주기 (긴 자료) |
| specialist 산출물 JSON parse 실패 → critique 자체 무시 | retry 1회 후 그 specialist 만 skip, 다른 결과는 사용 |
| 충돌 항목 양쪽 다 reject → integrator 가 "어느 쪽도 안 만족" 결정 → 사용자 불만 | 충돌 해소 규칙 §4 적용, 양쪽 만족 안 되면 임상 우선 |
| max iteration 도달 후 blocker 남았는데 push 강행 | 사용자 보고 후 결정 받기 — 자동 강행 금지 |
| critique 로그에 환자명 박혀 _local/ 밖으로 유출 | `tools/quality_gate.py` 의 `redact_pii()` 통해서만 저장. 직접 write 금지 |

## 8. 모드 trigger 키워드 (참고 — integrator 가 사용자 메시지에서 추정)

| 모드 | 키워드 예시 |
|---|---|
| 기본 | (명시 없음) |
| 고품질 | "고품질로", "정확하게", "꼼꼼히", "퀄리티 신경 써서" |
| 극한 | "최고 퀄리티", "학회용", "언론용", "심사용", "외부 발표" |
| Clinician audience | "동료 의사용", "학회 발표", "원내 강의" — patient-readability skip |

## 9. 환경별 호환성

- **Claude Code**: 위 룰 그대로. `Agent` 도구 사용.
- **Codex (다른 머신)**: subagent / 도구 이름이 다를 수 있음. 본 문서 §3 의 호출 환경 부분만 그쪽 환경에 맞게 mental adapter. 산출물 JSON 스키마·severity·로깅 룰은 동일.
- **모델 변경**: 모델 ID 하드코딩 금지. 호스트 default 사용. 본 파이프라인은 모델 *capability* 에 의존 (강한 추론 + vision optional).

## 10. eval / 측정 (자세한 룰은 evals/README.md)

- 기본: dogfooding — 매 콘텐츠마다 `_local/quality-logs/` 누적
- 별도 eval: `evals/synthetic/` 의 가공된 fixture 로 multi-agent ON/OFF 비교
- 측정 metric: severity 분포, blocker fix rate, 평균 iteration 수, 시간·비용

## 11. 본 문서 vs SKILL.md

SKILL.md 가 짧은 trigger 와 link, 본 문서가 상세 룰. 정합성 룰:

- SKILL.md 룰 변경 시 본 문서 동기 갱신
- 본 문서만 변경되고 SKILL.md 미반영 → integrator 가 본 문서를 follow 안 할 수 있음
- 새 specialist 추가 시 `reference/quality-agents/` 에 파일 + 본 문서 §2 라인업 + SKILL.md 섹션 셋 다 갱신
