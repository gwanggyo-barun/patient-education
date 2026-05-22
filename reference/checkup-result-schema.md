# Health Checkup Result Schema

`lab-reports/health-checkup`은 텍스트, PDF, 캡쳐 이미지가 섞인 종합검진 입력을 먼저
표준 JSON으로 정리한 뒤 HTML을 만든다. 원본을 바로 HTML로 옮기지 않는다.

## 필수 원칙

- 입력에 실제로 나온 검사만 포함한다. 시행하지 않은 검사는 추정 금지.
- 수치·단위·판독명·검사일은 원본 그대로 옮긴다.
- 불명확한 판독은 만들지 말고 `source_warnings`에 남긴다.
- 환자명·차트번호는 title block과 `build.py` metadata에만 둔다. OG meta와 본문 해석 카드에 반복하지 않는다.
- `status` 값은 `ok`, `warn`, `alert` 중 하나를 기본으로 쓴다.

## JSON Schema

```json
{
  "report_title": "종합 건강검진 결과 안내",
  "og_description": "환자 식별자 없는 60자 이내 요약",
  "age_sex": "M/55",
  "performed_tests": ["혈액검사", "소변검사", "위내시경", "대장내시경", "갑상선초음파"],
  "overall": [
    {"area": "대사·심혈관", "status": "warn", "value": "주의", "summary": "LDL·혈압 경계"}
  ],
  "vitals": [
    {"label": "BMI", "value": "26.4", "unit": "kg/m² · 과체중", "status": "warn"}
  ],
  "labs": [
    {
      "label": "지질 (TC / LDL / HDL / TG)",
      "value": "215 / 142 / 48 / 158",
      "range": "<200 / <130 / ≥40 / <150",
      "badge": "경계",
      "status": "warn"
    }
  ],
  "urinalysis": [
    {"label": "단백 · 잠혈 · 당", "value": "trace · − · −", "range": "단백 trace 외 음성", "badge": "경계", "status": "warn"}
  ],
  "endoscopy": [
    {"title": "위내시경 — H. pylori (+)", "items": ["만성 위축성 위염", "제균 치료 후 4주 뒤 박멸 확인"]}
  ],
  "ultrasound": [
    {"title": "갑상선 초음파", "items": ["우엽 0.4cm TIRADS 3", "12개월 후 추적"]}
  ],
  "ekg": {"title": "정상 동율동", "items": ["심박수 72 bpm", "ST-T 변화 없음"], "status": "ok"},
  "bmd": {
    "lumbar": {"label": "요추", "value": "-1.6", "unit": "T-score · 골감소증", "status": "warn"},
    "femoral": {"label": "대퇴 경부", "value": "-1.1", "unit": "T-score · 정상 경계", "status": "ok"},
    "note": "비타민 D·칼슘·체중부하 운동, 2년 후 재검"
  },
  "action_plan": [
    {"title": "최우선 권고", "text": "H. pylori 제균 치료 후 4주 뒤 박멸 확인"}
  ],
  "source_warnings": []
}
```

검증:

```bash
python3 tools/checkup_schema_validate.py evals/synthetic/lab-reports/health-checkup-mixed.json
```
