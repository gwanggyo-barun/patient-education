# Multi-Agent Quality Pipeline — Evals

`reference/multi-agent-quality.md` 의 파이프라인 효과를 측정하는 eval suite.

## 두 가지 측정 방식 병용

### 1. Dogfooding (기본)

매 콘텐츠 생성 시 `_local/quality-logs/critique-YYYY-MM-DD.jsonl` 에 redacted 결과가 자동 누적된다 (`tools/quality_gate.py` 의 `log_critique`). 실제 작업 분포를 반영하는 가장 정직한 측정.

쿼리 예시:
```bash
# 지난 1주일 blocker 수
jq -s 'map(.specialists[].findings_count.blocker // 0) | add' \
   ~/clinic-content-system/_local/quality-logs/critique-*.jsonl
```

### 2. Synthetic fixture eval (재현 가능)

`evals/synthetic/` 의 가공된 fixture (실환자 데이터 금지) 로 multi-agent ON/OFF 비교. 재현 가능, 회귀 검증용.

```bash
cd ~/clinic-content-system
python3 evals/eval_runner.py run --mode multi-agent --kind decks
python3 evals/eval_runner.py run --mode baseline    --kind decks
python3 evals/eval_runner.py compare --kind decks
```

## Fixture 룰 (절대 룰)

- `evals/synthetic/` 에 **실환자 데이터 금지** — 이름·차트번호·생년월일·전화번호·실제 수치 패턴 전부.
- 가공 방법: 환자명은 `홍길동` / `김환자` 같은 일반 이름, 차트번호는 `[99001]`, 수치는 임상적으로 가능한 범위 내 랜덤. 실 패턴 추측 불가하게.
- fixture 자체는 repo 안에 commit 됨 — repo public 임을 의식하고 가공.

## 측정 metric

| metric | 의미 |
|---|---|
| `blocker_count_per_doc` | 콘텐츠 1건당 잡힌 blocker 수 (낮을수록 좋음) |
| `major_count_per_doc` | major 수 |
| `blocker_fix_rate` | blocker 중 1회 iteration 안에 fix 된 비율 |
| `avg_iterations` | Stage D-E 반복 횟수 평균 (1.0 = 한 번에 통과) |
| `time_to_pass` | Stage A 시작 ~ Stage F 통과까지 wall time |
| `false_positive_rate` | integrator 가 reject 한 finding 비율 (specialist 정밀도 측정) |

목표값:
- 기본 모드: `avg_iterations ≤ 1.3`, `blocker_count_per_doc ≤ 0.5`
- 극한 모드: `blocker_count_per_doc ≤ 0.1`, `false_positive_rate ≤ 30%`

## Directory

```
evals/
  README.md                  # this
  eval_runner.py             # 비교 실행
  gates/
    run_gate_evals.py        # handouts v2 게이트 결정론 회귀 (aboutness·visual-diff·tone, §7)
  synthetic/
    decks/                   # 가공된 decks fixture
    handouts/                # 가공된 handouts fixture
    lab-reports/             # 가공된 lab-reports fixture (실환자 X)
```

## 게이트 회귀 evals (결정론)

LLM 비교와 별개로, handouts v2 게이트(`shared/_image_gate`·`_visual_diff`·`_tone_score`)의
회귀를 fixture 로 고정한다 (`PRD/handout-visual-v2/04_PROJECT_SPEC.md` §7):

```bash
python3 evals/gates/run_gate_evals.py   # 전부 통과 시 exit 0 — CI 게이트로 사용 가능
```

## Caveat

- LLM 호출 비결정성: 같은 fixture 도 매 실행마다 약간 다른 산출물. 통계적 분포로 봐야 함.
- `eval_runner.py` 의 multi-agent 호출 부분은 호스트 환경마다 binding 이 다름 (Claude Code 는 Agent 도구, Codex 는 자체 도구). 본 runner 는 결정적 부분 (fixture load, metric 계산, 비교) 만 담당하고 실제 호출은 호스트 통합 지점을 따로 둔다.
