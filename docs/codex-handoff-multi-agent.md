# Codex Handoff — Multi-Agent Quality Pipeline

> 이 문서는 Claude Code 세션이 추가한 **Multi-Agent Quality Pipeline** 변경을 Codex (또는 다른 AI 코딩 도구) 세션이 cold-start로 이어받을 수 있도록 작성한 핸드오프.
>
> Source of Truth: [`SKILL.md`](../SKILL.md) §"Multi-Agent Quality Pipeline" + [`reference/multi-agent-quality.md`](../reference/multi-agent-quality.md). 본 문서는 그 변경을 *Codex 관점*에서 재구성한 안내일 뿐, 룰 자체는 SKILL.md / multi-agent-quality.md 가 우선.

---

## 1. TL;DR

`clinic-content-system` 의 콘텐츠 작성 워크플로우에 **3-stage 멀티 에이전트 품질 파이프라인** 이 들어갔다. integrator 1명 + specialist 다수 (kind별 4~5명) 가 병렬로 planning → drafting → critique 를 돌린다. Codex 가 이 repo 에서 콘텐츠를 만들 때도 *같은 산출물 스키마·severity·로깅 룰* 을 따라야 한다 — specialist 호출 도구 이름만 환경에 맞게 mental adapter.

이전에 Codex 가 review 한 의견 (model ID 하드코딩 금지, critique 로그는 `_local/` gitignored + redaction, layout validation 은 결정적 도구 유지, lab-reports 에 privacy-ops 추가) 은 **이미 반영** 됨.

---

## 2. 변경된 commit 2개

| commit | 날짜 | 요약 |
|---|---|---|
| `3effb90` | 2026-05-15 00:19 | Add multi-agent quality pipeline (7 specialists + orchestrator + gate) |
| `13ff189` | 2026-05-15 23:48 | Switch specialist subagent_type from claude to general-purpose |

`13ff189` 는 Claude Code 환경 전용 fix (FleetView `claude` 함대 에이전트가 worktree isolation 을 강제하여 비-git cwd 에서 실패 → `general-purpose` 로 전환). Codex 환경에는 직접 적용되지 않지만, SKILL.md / multi-agent-quality.md 의 §"호출 환경" 텍스트가 같이 갱신된 것을 인지하면 됨.

---

## 3. 신규/갱신된 핵심 파일

```
SKILL.md                              §"🤖 Multi-Agent Quality Pipeline" 신설 (line 349~)
reference/multi-agent-quality.md      상세 SoT — 11 섹션 (pipeline / specialist 라인업 / 호출 환경 / JSON 스키마 / severity / 충돌 해소 / logging / anti-pattern / 모드 trigger / 호환성 / eval)
reference/quality-agents/             7 specialist 프롬프트
  ├── clinical-accuracy.md
  ├── patient-readability.md
  ├── visual-design.md
  ├── narrative-flow.md         (decks 전용)
  ├── density-hierarchy.md      (handouts 전용)
  ├── data-accuracy.md          (lab-reports 전용)
  └── privacy-ops.md            (lab-reports 전용 — push 차단 권한 보유)
tools/quality_gate.py                 redact_pii() / run_deterministic_gate() / log_critique() / roster_for()
evals/                                synthetic eval scaffold — host-binding-agnostic runner
.gitignore                            _local/ 추가 (critique 로그 위치), evals/results/ 추가
```

---

## 4. Codex 가 이 repo 에서 콘텐츠를 만들 때

`reference/multi-agent-quality.md` §9 "환경별 호환성" 이 SoT. 요점:

1. **Specialist 호출 도구만 환경에 맞게 mental adapter.**
   - Claude Code: `Agent(subagent_type="general-purpose", ...)` 한 메시지 안 여러 호출 = 병렬
   - Codex: 그쪽 환경의 sub-agent / parallel tool call 메커니즘 사용. 도구 이름이 달라도 *역할* 은 동일 (specialist prompt 그대로 + 컨텍스트 주입 + JSON 응답 수신)
2. **모델은 호스트 default 또는 available strongest reasoning model.** 모델 ID 하드코딩 금지.
3. **vision specialist (`visual-design`)** 는 vision 지원 모델 필수. 미지원이면 그 specialist 만 skip — 다른 specialist 는 진행.
4. **산출물 JSON 스키마·severity 의미·충돌 해소 우선순위·logging redaction 룰은 환경 무관 동일.**
5. **결정적 gate (Stage C / F)** 는 LLM 호출 없이 그대로 사용: `python -m shared._validate_layout`, `python build.py`, lab-reports 한정 `_visual_audit`.

### 콘텐츠 타입별 specialist 라인업

| kind | Stage A / D specialist (병렬) | 개수 |
|---|---|---|
| `decks` | clinical-accuracy + patient-readability + visual-design + narrative-flow | 4 |
| `handouts` | clinical-accuracy + patient-readability + visual-design + density-hierarchy | 4 |
| `lab-reports` | clinical-accuracy + patient-readability + visual-design + data-accuracy + **privacy-ops** | 5 |

`target_audience: "clinician"` 일 때만 `patient-readability` 자동 skip (학회·동료의사 자료).

### 모드 (사용자 메시지에서 추정)

| 모드 | trigger 키워드 | Stage D-E max iteration |
|---|---|---|
| 기본 | (명시 없음) | 1 |
| 고품질 | "고품질", "정확하게", "꼼꼼히" | 2 |
| 극한 | "최고 퀄리티", "학회용", "언론용", "심사용" | 3 |

빠른 모드 없음. specialist skip 옵션 미제공.

---

## 5. 변경되지 *않은* 것 (안심하고 그대로 따르면 됨)

- Notion DB 라우팅 3개 (`decks` / `handouts` / `lab-reports`) — `shared/_notion_sync.py` `DBS` dict 그대로
- A4 레이아웃 검증 2단계 (`_validate_layout` 자동 + preview PNG 시각 확인)
- Cross-Machine Consistency 7원칙 (AGENTS.md §"🔒 무조건 규칙") — 워킹 디렉토리 `~/clinic-content-system/`, push 자동화 등
- lab-reports privacy 4중 보호 (hash slug / QR 제거 / noindex / 커밋 메시지 환자명 금지)
- 빌드 파이프라인 (`build.py` + GitHub Actions ~80초)
- 표준 워크플로우 (pull --rebase → 작성 → validate → build → push)

**Multi-agent pipeline 은 기존 워크플로우 *위에 추가* 된 레이어** — 기존 룰을 덮지 않는다.

---

## 6. 정합성 검증 (Codex 가 작업 시작 전 1회)

```bash
cd ~/clinic-content-system

# (a) Pipeline 사양 핵심 4 파일 존재 확인
ls reference/multi-agent-quality.md \
   reference/quality-agents/{clinical-accuracy,patient-readability,visual-design,narrative-flow,density-hierarchy,data-accuracy,privacy-ops}.md \
   tools/quality_gate.py

# (b) Quality gate 도우미 동작 확인
python -c "from tools.quality_gate import redact_pii, roster_for; \
print(roster_for('lab-reports', 'patient')); \
print(redact_pii('환자명 김OO 차트번호 [12345] 연락처 010-1234-5678'))"

# (c) SKILL.md 와 multi-agent-quality.md 의 specialist 라인업 일치 확인
grep -A 5 'kind | specialist' SKILL.md
grep -A 5 'kind | Stage A · D specialist' reference/multi-agent-quality.md

# (d) _local/ gitignore 확인 (critique 로그가 push 되면 안 됨)
grep -E '^_local/?$|^_local/quality-logs' .gitignore
```

위 4개가 모두 정상이면 Codex 환경에서 pipeline 활용 준비 완료.

---

## 7. 자주 잡히는 anti-pattern (multi-agent-quality.md §7 요약)

| 패턴 | 회피책 |
|---|---|
| Stage D 가 매번 같은 blocker (예: HbA1c 풀이 누락) | Stage B 작성 시 자동으로 첫 등장 풀이 삽입 |
| Stage A 통합 기획서 사용자 확인 skip → 후반 reject → 전체 재작업 | 통합 기획서 한 번은 사용자에게 보여주기 (긴 자료) |
| specialist JSON parse 실패 → critique 자체 무시 | retry 1회 후 그 specialist 만 skip, 나머지는 사용 |
| 충돌 항목 양쪽 다 reject | 충돌 해소 우선순위 적용 (clinical > readability > visual > 타입별), 양쪽 만족 안 되면 임상 우선 |
| max iteration 후 blocker 남아도 push 강행 | **사용자 보고 후 결정** — 자동 강행 금지. `privacy-ops` blocker 면 절대 push 금지 |
| critique 로그에 환자명 박혀 `_local/` 밖 유출 | `tools/quality_gate.py::redact_pii()` 통해서만 저장. raw write 금지 |

---

## 8. 다른 세션 작업물 보호 (Cross-Session Rule)

이 repo 는 Claude Code + Codex 가 병행 작업할 수 있다. 다른 세션의 *미커밋* 파일·orphaned TARGETS·local-only commits 를 봐도:

- 건드리지 않는다 (revert / 삭제 / force push 금지)
- 본인 task 만 commit + push
- 본인 push 가 CI fail 해도 그게 다른 세션의 unfinished work 때문이면 그대로 둠 — 그쪽이 완성해서 push 하면 자연 해결
- "어떻게 도와줘?" 가 와도 즉시 다른 세션 파일 수정 안 함. 사용자 판단 먼저

자세한 규칙: AGENTS.md §"⛔ 절대 하지 말 것" + Claude Code memory `feedback_parallel_agents_no_interference.md`.

---

## 9. 열려있는 질문 / 다음 단계

- **Eval runner** (`evals/eval_runner.py`) 는 host-binding-agnostic 으로 작성됐지만 Codex 환경에서 실제 실행 검증 미완. 첫 Codex 가동 시 dogfooding 결과 `_local/quality-logs/` 누적 모니터링 권장.
- **Stage A 통합 기획서 (한국어)** 를 어느 길이의 자료부터 사용자에게 노출할지 - 현재 룰은 "긴 자료 한 번" 으로 모호. dogfooding 누적되면 임계값 조정 후보.
- **모드 trigger 정확도** — 현재 사용자 메시지 키워드 추정 방식. False positive (사용자가 "정확하게" 라는 단어를 다른 문맥에서) 가 누적되면 명시적 flag 도입 검토.
- **새 specialist 추가 시 갱신 위치 3곳** — `reference/quality-agents/` 파일 + `reference/multi-agent-quality.md` §2 라인업 + `SKILL.md` §"Multi-Agent Quality Pipeline" 표. 누락 시 integrator 가 따라가지 않을 수 있음.

---

## 10. 참고 링크

- 통합 룰 (Claude Code + Codex 공통): [`../AGENTS.md`](../AGENTS.md)
- 콘텐츠 작성 전체 SoT: [`../SKILL.md`](../SKILL.md)
- Multi-agent 상세 사양: [`../reference/multi-agent-quality.md`](../reference/multi-agent-quality.md)
- Specialist 프롬프트: [`../reference/quality-agents/`](../reference/quality-agents/)
- Quality gate 도우미: [`../tools/quality_gate.py`](../tools/quality_gate.py)
- Eval scaffold: [`../evals/README.md`](../evals/README.md)
