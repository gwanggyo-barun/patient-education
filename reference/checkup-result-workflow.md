# Health Checkup Result Workflow

`lab-reports/health-checkup`은 환자별 시행 검사가 다른 종합검진 결과지를 만든다.
기본 목표는 A4 1장, 영상·기능검사까지 많으면 2장, 영상 narrative가 길 때만 3장이다.

## Intake

지원 입력:

- 의사가 적은 텍스트 요약
- 검사기관 PDF
- EMR/검사표 캡쳐 이미지
- 위/대장 내시경 소견, 조직검사 결과
- 상복부·갑상선·경동맥 초음파 판독
- 혈액검사, 소변검사, 신체계측, 심전도, 골밀도

처리 순서:

1. 모든 입력에서 시행 검사 inventory를 만든다.
2. `reference/checkup-result-schema.md`의 JSON으로 구조화한다.
3. `tools/checkup_schema_validate.py`로 JSON shape를 확인한다.
4. `lab-reports/health-checkup/template/` 또는 web intake renderer로 HTML을 만든다.
5. `python3 -m shared._validate_layout <html>`을 통과시킨다.
6. `build.py` TARGETS에 hash slug로 등록한다.

## Module Selection

항상 포함:

- 종합 판정
- 권장 사항·다음 단계

입력에 있을 때만 포함:

- 신체계측·생체징후
- 혈액검사
- 소변검사
- 위·대장 내시경
- 상복부·갑상선·경동맥 초음파
- 심전도
- 골밀도

시행하지 않은 검사를 “미시행”으로 길게 나열하지 않는다. 결과지는 시행한 검사만 카드화한다.

## Compression

- 정상 혈액 항목은 한 행으로 묶는다.
- 경계·이상·추적 필요 항목은 별도 행 또는 action item으로 분리한다.
- 페이지 1은 종합 판정, vitals, 혈액·소변 중심.
- 페이지 2는 내시경, 초음파, 심전도, 골밀도, action plan 중심.
- 3페이지는 내시경/초음파 narrative가 너무 길어 2페이지가 overflow 날 때만 쓴다.

## Quality Gates

Health-checkup에서는 기본 lab-reports specialist에 두 명을 추가한다.

- `checkup-extraction`: 입력 출처별 시행 검사 inventory와 수치/판독 추출 confidence 검토
- `checkup-completeness`: 모듈 누락, 신호등-본문 일관성, next-step 누락 검토

결정적 gate:

```bash
python3 tools/checkup_schema_validate.py <structured-json>
python3 -m shared._validate_layout <html>
python3 build.py
```

Privacy:

- 원본 PDF/캡쳐는 `_local/` 밖에 저장하지 않는다.
- public URL slug는 `lab_hash_slug(chart_no, patient_name, "health-checkup")`만 사용한다.
- OG title/description/image에 환자명·차트번호를 넣지 않는다.
- commit message에는 hash와 topic만 넣는다.
