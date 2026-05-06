# 새 콘텐츠 요청 입력 템플릿

> 원장님이 Claude에 새 환자 교육 자료를 요청할 때 사용하는 입력 템플릿.
> 이 템플릿대로 입력하면 Claude가 `clinic-content-system` 스킬을 자동 트리거하고
> 12장짜리 덱을 생성한다.

## 표준 입력 형식

```
[주제명]을 환자 교육 슬라이드로 만들어줘. clinic-content-system 스킬 사용.

대상 환자: [신환 / 재진 / 가족 / 일반]
진료과: [GASTROENTEROLOGY / CARDIOLOGY / ENDOCRINOLOGY / GENERAL INTERNAL MEDICINE]
slug: [예: gerd, h-pylori, htn, dm-type2]
specialty 폴더: [예: gi, cardio, endo, general]

1. Overview / 핵심 통계
- 한국 유병률: ~%
- 주요 위험성: ...

2. Definition / Pathophysiology
- 정의: ...
- 핵심 기전: ...

3. Symptoms 또는 Diagnosis (6항목)
- ...
- ...

4. Risk Factors / Indications (6항목)
- ...
- ...

5. Treatment / First-line
[약물 조합이라면 약물명 + 용량 + 빈도]
[단순 치료 단계라면 4가지 핵심 규칙]

6. Salvage / Comparison
[2차 치료 또는 DO/DON'T 비교]

7. Schedule (4단계)
- Day 1: ...
- Day N: ...
- ...

8. Precautions (4가지 + 응급 알림)
- 규칙 1: ...
- ...
- 응급 알림: ...

9. Side Effects 또는 Red Flags (6가지, mixed 가능)
- 일반: ...
- Red Flag: ...

10. Action Checklist (7가지)
- ...
- ...

근거: [가이드라인명 + 발행연도]
```

## 사용 예시 1 — 만성질환 (고혈압)

```
고혈압 생활관리를 환자 교육 슬라이드로 만들어줘. clinic-content-system 스킬 사용.

대상 환자: 신환
진료과: CARDIOLOGY
slug: htn-lifestyle
specialty 폴더: cardio

1. Overview
- 한국 성인 고혈압 유병률: 약 30% (30세 이상)
- 사망 기여 1위 원인: 심혈관질환

2. Definition
- 수축기 ≥ 140 또는 이완기 ≥ 90 mmHg
- 가정혈압 기준은 ≥ 135/85

3. 진단 방법 (6가지)
- 진료실 혈압 측정
- 가정혈압 측정 (HBPM)
- 24시간 활동혈압 측정 (ABPM)
- ...

4. 위험 요인 (6가지)
- 비만, 과음, 흡연, 고염분 섭취, 운동부족, 스트레스

5. 약물 치료
- 1차: ACEI/ARB (HCT 병합 가능)
- 1차: CCB
- 1차: 저용량 thiazide

6. 식이/생활 비교
- 권장: 저염식 (소금 < 5g/일), 채소·과일, 저지방 유제품
- 피하기: 가공식품, 패스트푸드, 과음, 흡연

7. 모니터링 일정
- Day 1: 처방 시작
- Week 2: 혈압 재확인 + 부작용 점검
- Week 4: 용량 조절 검토
- Month 3: 표적 도달 평가

8. 약물 복용 주의 (4가지 + 응급)
- 정해진 시간 복용
- 임의 중단 금지
- ...
- 응급: 흉통·실신·심한 두통 → 즉시 119

9. 부작용 (6가지, mixed)
- 일반: 어지러움, 부종, 마른 기침, 피로
- Red Flag: 혈관부종, 신기능 악화

10. 체크리스트 (7가지)
- 매일 같은 시간 가정혈압 측정
- ...

근거: 2022 KSH/대한고혈압학회 진료지침; 2023 ESH Guidelines
```

## 사용 예시 2 — 시술 후 안내 (위 내시경 후)

```
위 내시경 후 주의사항을 환자 교육 슬라이드로 만들어줘. clinic-content-system 스킬 사용.

대상 환자: 검진 후 환자
진료과: GASTROENTEROLOGY
slug: post-egd
specialty 폴더: gi

1. Overview
- 위·식도 검진 시술 (EGD)
- 평균 시술 시간: 5-10분
- 회복 시간: 15-30분 (수면 내시경 시 1-2시간)

2. 시술 직후 주의 (4가지)
- 마취 깰 때까지 보호자 동반
- ...

3. 음식 섭취 시간순 (Timeline 4단계)
- 즉시: 금식
- 30분 후: 미지근한 물 한 모금
- 1시간 후: 부드러운 죽
- 4시간 후: 일반식

4. 권장 vs 피하기 (Comparison)
- 권장: 미지근한 음식, 부드러운 식감
- 피하기: 뜨거운 음식, 매운 음식, 단단한 음식, 술

5. 흔한 일시 증상 (4가지)
- 인후 불편감
- 복부 팽만
- 트림
- 가벼운 메스꺼움

6. 응급 신호 (Red Flag, 6가지)
- 검은변 또는 토혈
- 심한 복통 (점점 악화)
- 고열 38°C 이상
- 호흡곤란
- 가슴 통증
- 토혈

7. 체크리스트 (7가지)
- 시술 당일 운전 금지 (수면 내시경)
- ...

근거: ESGE Position Statement on Post-EGD Care 2023
```

## 짧은 입력으로도 가능

콘텐츠가 부족하거나 시간이 없을 때, 다음과 같이 짧게 요청해도 Claude가 일반 의학 정보로 보완 생성한다:

```
대상포진 백신 안내를 clinic-content-system 스킬로 만들어줘.
대상자, 효과, 부작용, 접종 일정 중심으로.
```

이 경우 Claude는:
- 한국 KDCA·국가예방접종 기준 적용
- 2가지 백신(Zostavax / Shingrix) 비교 자동 포함
- 일반적인 부작용/주의사항 포함
- 보험 적용 여부 명시

## 결과물 검토 후 재요청

Claude의 첫 산출물에서 수정이 필요하면 구체적으로 지시:

```
3번 슬라이드(증상)에서 "야간 흉통" 카드를 "야간 호흡곤란"으로 바꿔줘.
나머지는 그대로.
```

```
6번 슬라이드(약물)에서 P-CAB 카드를 PREFERRED로 표시하고
표준 삼제요법 카드는 일반 tile로 바꿔줘.
```

## 빌드까지 한 번에

```
헬리코박터 제균을 clinic-content-system으로 만들고 PDF까지 빌드해줘.
```

이 경우 Claude가:
1. HTML 작성
2. `build.py`의 DECKS 리스트에 추가
3. `python build.py` 실행
4. 결과 PDF 경로 안내
