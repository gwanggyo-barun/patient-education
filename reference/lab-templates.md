# Lab Report Templates — 환자 검사결과 재사용 템플릿

> 8종의 빈 lab-report 템플릿. 환자별 인스턴스를 만들 때 디렉토리 복사 → 값만 채워 사용한다.
> 템플릿은 `build.py` TARGETS에 등록되어 있지 않아 **GitHub Pages 라이브 배포되지 않는다**.

## 위치

```
lab-reports/
├── cbc/template/             # 일반혈액검사 (CBC)
├── hba1c/template/           # 당화혈색소 · 당뇨 평가
├── thyroid-function/template/ # 갑상선 기능 (TSH, fT4, fT3, anti-TPO)
├── liver-function/template/  # 간기능 (AST/ALT/GGT/빌리루빈)
├── kidney-function/template/ # 신장기능 (Cr/eGFR/BUN/uPCR)
├── tumor-markers/template/   # 종양표지자 (CEA/AFP/CA19-9/PSA 등)
├── anemia-panel/template/    # 빈혈 패널 (Fe/페리틴/B12/엽산)
└── electrolytes/template/    # 전해질 (Na/K/Cl/Ca/P/Mg)

# 기존 (이미 환자 인스턴스 다수)
├── lipid-panel/sample/       # 지질 패널 (template 역할)
├── diabetes-screening/       # 당뇨 종합 (HbA1c + 합병증)
├── general-checkup/          # 공단검진 통합
├── cv-screening/             # 심혈관 위험도
├── comprehensive-summary/    # 통합 요약
├── bone-metabolism/          # 골다공증 · Vit D · Ca/P
├── urinalysis/               # 소변검사
└── health-checkup/template/  # ⭐ 종합 건강검진 결과지 (혈액·소변·내시경·초음파·심전도·골밀도 통합, 1~3페이지 가변)
```

## health-checkup 가 다른 lab-reports topic 과 다른 점

단일 패널 (cbc / lipid-panel / thyroid-function 등) 은 하나의 검사 카테고리 1페이지가 표준. **health-checkup 은 환자별로 시행 검사 갯수가 달라 1~3페이지로 가변**한다.

| 항목 | 단일 패널 lab-reports | health-checkup |
|---|---|---|
| 페이지 수 | 1페이지 강제 | 1~3페이지 가변 |
| 모듈 구성 | 고정 (해당 패널 수치만) | 8 모듈 ON/OFF (시행 검사만) |
| 종합 판정 | 없음 (수치만) | §0 4영역 신호등 + 권장 사항 §9 |
| 영상검사 narrative | 없음 | 내시경·초음파 card 본문 가능 |
| 검사 항목 변동성 | 없음 | 매 환자 다름 |
| Stage A·D specialist | 5인 (clinical/patient/visual/data/privacy) | 7인 (+ **checkup-extraction**, **checkup-completeness**) |

`reference/quality-agents/checkup-extraction.md` 가 혼합 입력 추출 confidence 를, `reference/quality-agents/checkup-completeness.md` 가 모듈 누락·follow-up 일정·신호등 일관성을 점검.

자세한 모듈 ON/OFF 룰·페이지 분할 가이드는 `reference/checkup-result-workflow.md` + `reference/checkup-result-schema.md` + SKILL.md "건강검진 결과지 (health-checkup)" 섹션 참조.


## 환자 인스턴스 생성 절차

```bash
cd ~/clinic-content-system

# 1. hash slug 생성 (개인정보 보호 — Gotcha 11)
python3 -c "import sys; sys.path.insert(0,'shared'); from _build_helpers import lab_hash_slug; print(lab_hash_slug('차트번호','환자명','cbc'))"
# → 예: 8a3f1c9d2e

# 2. template → hash 디렉토리 복사
cp -r lab-reports/cbc/template lab-reports/cbc/8a3f1c9d2e

# 3. HTML 편집 — 다음 placeholder만 환자값으로 교체
#    - 「환자명」 → 실제 환자명
#    - (M/00) → (M/65) 같은 실제 성별/나이
#    - 차트번호 ◯◯◯◯ → 실제 차트번호
#    - YYYY-MM-DD → 실제 검사일
#    - 각 lab-row 값 + badge class (정상/--high/--low) 갱신
#    - 의미·해석 카드의 텍스트도 환자별로 수정

# 4. build.py TARGETS에 항목 추가
#    {
#      "kind": "lab-reports", "slug": "8a3f1c9d2e",
#      "slug_path": "lab-reports/cbc/8a3f1c9d2e/",
#      "html_path": ROOT / "lab-reports/cbc/8a3f1c9d2e/index.html",
#      "qr_class": "qr-mini__code", "fmt": "a4-portrait",
#      "patient_name": "홍길동", "chart_no": "12345",
#      "exam_date": "2026-05-13", "doctor": "정지환",
#      "note": "CBC — 경도 빈혈 추적",
#    }

# 5. 검증 + 빌드 + 푸시
PYTHONIOENCODING=utf-8 python3 -m shared._validate_layout lab-reports/cbc/8a3f1c9d2e/index.html
git add lab-reports/cbc/8a3f1c9d2e build.py
git commit -m "Add lab-report 8a3f1c9d2e (cbc)"   # 환자명/차트번호 절대 금지
git push
```

## 템플릿 구조 (8종 공통)

| 영역 | 내용 |
|---|---|
| **Header** | 로고 + `LAB REPORT · <PANEL_NAME>` eyebrow |
| **Title block** | `<패널명> 결과 안내` + 환자 메타 (placeholder) |
| **Stats row** (4) | 핵심 4가지 수치 — stat-cell--ok/--high/--low로 색상 |
| **Lab rows** | 6~10개 상세 항목 — lab-row__badge로 정상/이상 표시 |
| **Interpretation 2-col** | 좌: 의미 (accent card) · 우: 추적/감별 (card) |
| **Footer** | 클리닉 정보 + 면책 |

각 패널 특이사항:

- **CBC**: 빈혈 분류는 anemia-panel과 짝. 단순 추적이면 CBC, 원인 평가면 anemia-panel
- **HbA1c**: 당뇨 진단 기준 표를 본문에 명시 (≤5.6 정상 · 5.7-6.4 전단계 · ≥6.5 당뇨)
- **Thyroid**: 4패턴 감별표 포함 (정상/원발성 저하/항진/아임상성)
- **Liver**: AST/ALT 비 자동 해석 가이드 포함
- **Kidney**: CKD 5단계(G1-G5) 분류표 포함
- **Tumor markers**: "단독 진단 불가" 안내 카드 + 국가 5대암 검진 권장
- **Anemia panel**: 4패턴 감별 (철결핍성/만성질환성/거대적아구성/용혈)
- **Electrolytes**: 음이온 차 + 산-염기 평형 해석 가이드

## 디자인 일관성

모든 템플릿은 다음 표준 준수:
- viewport: `width=794` (A4 portrait 96dpi)
- noindex meta + OG meta 7종
- `../../../shared/design-tokens.css` + `clinic-handout-a4.css`
- 광교바른내과 footer (주소·전화·면책)
- `_validate_layout` 통과 (0 issues)

## 추가 패널 만들고 싶을 때

기존 8종에 없는 검사 (예: 응고검사, 류마티스 패널, 비타민D, IgE 등) 추가 시:
1. `lab-reports/{panel-slug}/template/index.html` 새로 생성
2. 기존 CBC template 복사해 schema만 바꾸는 게 가장 빠름
3. 이 문서 표에 한 줄 추가
4. `_validate_layout` 통과 확인
