# Synthetic Eval Fixtures

`evals/eval_runner.py` 가 가동하는 multi-agent vs baseline 비교 fixture.

## ⛔ 절대 룰 — 실환자 데이터 금지

이 디렉토리는 **public repo** 안에 있다. 다음은 절대 들어가면 안 됨:

- 실 환자명 (홍길동·김환자 같은 일반명만)
- 실 차트번호 (`[99001]`, `[99002]` 같은 9 로 시작하는 placeholder)
- 실 생년월일·전화번호·주소·이메일
- 실 검사 수치 패턴 — 환자 1명의 lab 패턴을 그대로 복사 금지. 임상적으로 가능한 범위 내 *합성* 값 사용

위반 시 `clinic-content-system/lab-reports` 의 hash slug + noindex + robots.txt 보호망 *밖* 에 환자 자료가 노출된다.

## Fixture JSON 스키마

각 파일은 `evals/synthetic/{kind}/{slug}.json`:

```json
{
  "topic": "diabetes-screening-routine",
  "kind": "lab-reports",
  "doctor_input": "60대 여성 환자, HbA1c 6.8, 공복혈당 130, 콜레스테롤 230 ...",
  "target_audience": "patient",
  "expected_blockers": [
    "LDL 정상범위 표시 오류 가능성",
    "공복혈당 단위 누락 시 blocker"
  ],
  "expected_majors": [
    "용어 풀이 누락 — HbA1c"
  ],
  "notes": "환자명·차트번호 등 식별자 없음. 수치 패턴은 임상적으로 가능한 범위 내 합성."
}
```

- `expected_blockers` / `expected_majors`: ground truth — specialist 가 잡으면 true positive, 못 잡으면 false negative
- `doctor_input` 의 환자명·차트번호는 일반 placeholder 만

## 초기 fixture 구성 권장 (다음 세션에서 채움)

- decks 5개: HTN / DM / GERD / 갑상선결절 / 빈혈 — 각각 흐름 issue 1-2개 의도 삽입
- handouts 5개: 내시경 준비 / 갑상선약 / 대장폴립 추적 / 식이 / 운동 — 1페이지 압박 case 포함
- lab-reports 5개: 지질 / 당대사 / 갑상선 / 신기능 / 빈혈 — 색상 코딩 오류 의도 삽입 case 포함

총 15 fixture × multi-agent + baseline 각 1회 = 30 run.

## 합성 데이터 생성 가이드

| 항목 | 합성 방법 |
|---|---|
| 환자명 | `홍길동`, `김환자`, `이임상`, `박표준` (실재 흔하지 않은 한국 성+이름 조합) |
| 차트번호 | `[99XXX]` (9 로 시작, repo public 노출 자체로 의미 없는 번호대) |
| 생년월일 | 사용 자체를 권장 안 함. 필요시 `1955-XX-XX` 등 일자 부분 X |
| 전화 | `010-0000-0000` placeholder |
| 검사 수치 | 임상적으로 가능한 범위 내, 단 진짜 환자 한 명의 패턴 복사 X |
| 검사 일자 | `2026-XX-XX` 또는 `최근 검사` 텍스트 |

가공 후 fixture 작성자가 자체 검수: 식별 정보 0 인지 grep / 정규식 확인.
