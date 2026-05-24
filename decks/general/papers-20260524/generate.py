"""5/24 Top 5 논문 12장 slide deck generator.

Uses shared/clinic-slides.css + design-tokens.css for consistent typography·colors.
Output: 5 × index.html under decks/general/papers-20260524/{slug}/
"""
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

PAPERS = [
    {
        "slug": "baxdrostat-baxhtn",
        "title": "Baxdrostat,<br><em>알도스테론을 막는 새 무기</em>",
        "subtitle": "BaxHTN Phase 3 (NEJM) · FDA approval 2026.05.18 — 저항성 고혈압의 5번째 카드",
        "chapter": "CARDIOLOGY · HYPERTENSION",
        "source": "BaxHTN Phase 3 · NEJM · FDA 2026.05.18",
        "importance": 5,
        "tldr": "표준 다약제로 조절 안 되던 저항성 고혈압 환자에서 baxdrostat 2 mg 12주 투여 시 SBP −15.7 mmHg (위약 대비 −9.8 mmHg 추가). 알도스테론 합성효소(CYP11B2)를 선택적으로 차단하는 1st-in-class 신약.",
        "background": "고혈압의 5–10%는 3제 이상 약물 사용에도 조절 안 되는 저항성 고혈압. 알도스테론 과다는 핵심 기전 중 하나지만 스피로노락톤은 부작용(여성형 유방·고칼륨)이 많다. baxdrostat는 코르티솔 합성효소(CYP11B1) 영향 없이 알도스테론 합성효소(CYP11B2)만 100배 이상 선택적으로 차단.",
        "design": "BaxHTN — 다국가 무작위 위약대조 Phase 3. 표준 3제 이상 사용에도 SBP ≥130 mmHg인 성인 ~750명. baxdrostat 1 mg / 2 mg / 위약 12주.",
        "result1_title": "혈압 강하 효과",
        "result1_items": [
            ("2 mg", "SBP −15.7 mmHg (위약 대비 −9.8 mmHg)"),
            ("1 mg", "SBP −14.5 mmHg (위약 대비 −8.7 mmHg)"),
            ("DBP", "유의미한 동시 감소"),
            ("효과 발현", "4주째 의미 있는 차이 시작"),
        ],
        "result2_title": "기전·약리학적 특성",
        "result2_items": [
            ("타겟", "CYP11B2 (알도스테론 합성효소)"),
            ("선택성", "CYP11B1 대비 100배+"),
            ("코르티솔", "영향 없음 (스피로노락톤 대비 장점)"),
            ("투여", "1일 1회 경구"),
        ],
        "subgroup_title": "Subgroup 분석",
        "subgroup_items": [
            "흑인 환자에서도 일관된 효과",
            "당뇨·CKD 동반 환자에서 유의한 강하",
            "65세 이상 노인 효과 유지",
            "여성·남성 차이 미미",
        ],
        "safety_title": "안전성 — 모니터링 필수",
        "safety_items": [
            ("고칼륨", "5% 내외, 대부분 경증"),
            ("저나트륨", "드물게 보고"),
            ("코르티솔 결핍", "임상적으로 거의 없음 (선택성)"),
            ("간기능", "유의미한 이상 X"),
        ],
        "apply_who_title": "어떤 환자에게",
        "apply_who_items": [
            "ARB/ACEI + CCB + 이뇨제 3제에도 SBP ≥130/85 미달성",
            "스피로노락톤 부작용(여성형 유방·고칼륨)으로 중단한 환자",
            "원발성 알도스테론증 의심군 (PAC/PRA ratio 고려)",
            "당뇨·CKD 동반 저항성 고혈압",
        ],
        "apply_how_title": "처방 시 주의",
        "apply_how_items": [
            "시작 용량 1 mg, 4주 후 2 mg 증량 가능",
            "ARB·ACEI·이뇨제와 병용 시 칼륨 모니터 (시작 2주·4주·8주)",
            "기존 스피로노락톤 중단 후 시작",
            "임신·수유부 금기",
        ],
        "limits_title": "한계와 주의사항",
        "limits_items": [
            "12주 단기 결과 — 장기(>1년) 심혈관 endpoint 자료 부족",
            "한국 도입 시기·보험 적용 미정 (FDA 승인 직후, 6월 미국 출시)",
            "기존 약 대비 비용 우위 미상",
            "원발성 알도스테론증과의 우선순위 명확화 필요",
        ],
        "takehome_lines": [
            "표준 다약제로 안 잡히던 저항성 고혈압의 새 옵션",
            "알도스테론 합성효소 선택적 억제 → 스피로노락톤 부작용 회피",
            "칼륨 모니터링(2·4·8주) 필수",
            "한국 도입까지는 시간 — 환자 기대 관리 + 기존 치료 최적화",
        ],
        "qr_target": "decks/general/papers-20260524/baxdrostat-baxhtn/",
    },
    {
        "slug": "tramadol-bmj",
        "title": "트라마돌,<br><em>이제 1차 약제에서 빼야 할 때</em>",
        "subtitle": "BMJ Meta-analysis 2026.05 — 만성 통증 효과 미미·심혈관 위험 증가",
        "chapter": "PAIN · GERIATRICS",
        "source": "BMJ Meta-analysis 2026.05",
        "importance": 5,
        "tldr": "만성 통증에서 트라마돌의 통증 감소 효과는 MCID(임상적 의미 있는 최소 차이)에 못 미치는 미미한 수준. 반면 심혈관 사건·골절·저나트륨 등 중대 부작용은 의미 있게 증가. 위험이 효과를 능가한다는 결론.",
        "background": "트라마돌은 '약한 오피오이드'로 인식되어 NSAID 부작용 회피·노인·심장약 복용자에게 흔히 처방. 그러나 세로토닌·노르에피네프린 재흡수 억제·SNRI 양면성·CYP2D6 변이성으로 약리학적으로 복잡하다. 최근 대규모 메타분석으로 위험-이익 재평가 필요.",
        "design": "BMJ 게재 systematic review·meta-analysis. 만성 통증(척추·관절·신경병성 등) RCT 다수 통합. 통증 감소(VAS·NRS)·기능·삶의 질·안전성 endpoint.",
        "result1_title": "통증 효과 — 미미",
        "result1_items": [
            ("VAS 감소", "위약 대비 약 −7 mm (MCID 10 mm 미만)"),
            ("기능 개선", "통계적 유의하나 임상적 의의 미약"),
            ("삶의 질", "위약 대비 차이 거의 없음"),
            ("MCID 도달률", "낮음"),
        ],
        "result2_title": "안전성 — 위험 증가",
        "result2_items": [
            ("심혈관 사건", "유의미한 증가"),
            ("골절·낙상", "노인에서 위험 ↑"),
            ("저나트륨", "SIADH 유사 작용"),
            ("세로토닌 증후군", "SSRI·SNRI 병용 시 위험"),
            ("의존성", "기존 인식보다 높음"),
        ],
        "subgroup_title": "고위험군",
        "subgroup_items": [
            "65세 이상 노인 — 골절·낙상 ↑",
            "심혈관 질환자 — MACE 위험 ↑",
            "SSRI·SNRI 복용자 — 세로토닌 증후군",
            "CYP2D6 ultra-rapid metabolizer — 호흡억제",
        ],
        "safety_title": "임상 영향력",
        "safety_items": [
            ("울트라셋·트라마셋", "복합제 처방 재검토"),
            ("저용량 = 안전 가설", "근거 약함"),
            ("'NSAID 대안' 가설", "위험-이익 역전"),
            ("의존·금단", "장기 복용 시 발생 가능"),
        ],
        "apply_who_title": "재검토 대상 환자",
        "apply_who_items": [
            "만성 비암성 통증으로 트라마돌 장기 복용 중",
            "노인·심혈관 위험군에서 1차 약제로 처방된 경우",
            "SSRI·SNRI 병용 환자",
            "신장 기능 저하·간기능 저하 환자",
        ],
        "apply_how_title": "대안 전략",
        "apply_how_items": [
            "1차: 비약물 (운동·인지치료·물리치료)",
            "2차: 위장·신장 평가 후 NSAID 단기",
            "신경병성 통증: 가바펜틴·둘록세틴",
            "심한 통증: 필요 시 전문의 의뢰 — 강한 오피오이드보다 다학제 접근",
        ],
        "limits_title": "한계와 주의사항",
        "limits_items": [
            "포함된 RCT 이질성 (지속기간·용량·환자군 차이)",
            "단기(<12주) 위주, 장기 효과 자료 부족",
            "개인차 — CYP2D6 다형성으로 반응 다양",
            "급성 통증·암성 통증에는 별도 권고",
        ],
        "takehome_lines": [
            "트라마돌은 만성 통증 1차 약제에서 빼야 한다",
            "특히 노인·심혈관 위험군·SSRI 복용자에서 위험-이익 역전",
            "비약물 + NSAID(평가 후) + 신경병성은 가바펜틴/둘록세틴",
            "기존 환자 — 점진적 감량 + 대안 마련 후 중단",
        ],
        "qr_target": "decks/general/papers-20260524/tramadol-bmj/",
    },
    {
        "slug": "sglt2-glp1-combo",
        "title": "SGLT-2i + GLP-1RA,<br><em>병용이 답이다</em>",
        "subtitle": "Cardiovascular Diabetology 메타분석 (>100만 명) — MACE·신장 30% 개선",
        "chapter": "ENDOCRINOLOGY · CARDIOLOGY",
        "source": "Cardiovascular Diabetology · 18 코호트 메타분석",
        "importance": 5,
        "tldr": "제2형 당뇨 환자에서 SGLT-2i와 GLP-1RA 병용 시 MACE·중대 신장 사건이 단독요법 대비 약 30% 감소. HbA1c·체중·혈압도 추가 개선. ASCVD·CKD 동반 당뇨에서 병용을 적극 고려할 강한 근거.",
        "background": "ADA 2024·KDA 2023은 ASCVD·HFpEF·CKD 동반 당뇨에서 SGLT-2i 또는 GLP-1RA 우선 권고. 단독 시 효과 명확하나 '둘 다 쓰면 어떤가'는 임상시험 부재. 18개 대규모 코호트(100만+) 메타분석으로 답.",
        "design": "Systematic review·meta-analysis. T2DM 환자 18개 real-world 코호트 통합. SGLT-2i + GLP-1RA 병용군 vs 각 단독군 비교. MACE·신장 endpoint·혈당·체중·혈압.",
        "result1_title": "심혈관·신장 결과",
        "result1_items": [
            ("MACE 감소", "−30% (HR ~0.70)"),
            ("심부전 입원", "−25–35%"),
            ("중대 신장 사건", "−30–35%"),
            ("전체 사망", "−20% 내외"),
        ],
        "result2_title": "대사적 추가 개선",
        "result2_items": [
            ("HbA1c", "추가 −0.5–0.8%"),
            ("체중", "추가 −2–4 kg"),
            ("수축기혈압", "추가 −3–5 mmHg"),
            ("알부민뇨", "유의 감소"),
        ],
        "subgroup_title": "적응증별 일관성",
        "subgroup_items": [
            "ASCVD 동반 — 효과 가장 큼",
            "CKD eGFR 30–60 — 신장 보호 명확",
            "HF (HFrEF·HFpEF) — 입원 감소",
            "고도비만 (BMI ≥35) — 체중·혈당 큰 폭 개선",
        ],
        "safety_title": "안전성·실용성",
        "safety_items": [
            ("저혈당", "두 약제 모두 위험 낮음"),
            ("DKA", "SGLT-2i 단독과 동일 수준"),
            ("위장관 부작용", "GLP-1RA 시작 시 일시적"),
            ("비뇨생식기 감염", "SGLT-2i 관련 감독"),
        ],
        "apply_who_title": "병용 1순위 환자",
        "apply_who_items": [
            "ASCVD 동반 T2DM",
            "CKD (eGFR 30–60) 동반 T2DM",
            "HFpEF·HFrEF 동반 T2DM",
            "비만 + HbA1c 8% 이상",
        ],
        "apply_how_title": "단계적 추가 전략",
        "apply_how_items": [
            "기존 SGLT-2i 환자 — GLP-1RA(주사·경구) 추가",
            "기존 GLP-1RA 환자 — SGLT-2i 추가",
            "Metformin + 둘 다 → 3제 병용 가능",
            "비용·보험·환자 순응도 점검 (특히 주사제)",
        ],
        "limits_title": "한계와 주의사항",
        "limits_items": [
            "관찰연구 메타 — RCT 인과성보다 약함",
            "코호트별 약물·용량 이질성",
            "한국 보험 — 동시 인정 여부 약제별 확인",
            "비용 부담 — 본인부담 ₩10–30만/월 예상",
        ],
        "takehome_lines": [
            "ASCVD·CKD·HF 동반 당뇨는 SGLT-2i + GLP-1RA 둘 다 검토",
            "MACE·신장 30% 추가 감소 — 매우 큰 임상적 이득",
            "Metformin 기반 + 둘 추가로 표준 진료 update",
            "비용·보험·순응도 점검 후 단계적 추가",
        ],
        "qr_target": "decks/general/papers-20260524/sglt2-glp1-combo/",
    },
    {
        "slug": "soy-legumes-htn",
        "title": "콩과 두류,<br><em>고혈압 예방의 정량적 처방</em>",
        "subtitle": "BMJ Nutrition, Prevention & Health 2026.05 — 최적 섭취량 정량화",
        "chapter": "NUTRITION · PREVENTIVE MEDICINE",
        "source": "BMJ Nutrition, Prevention & Health 2026.05",
        "importance": 4,
        "tldr": "식이 콩(soy)·두류(legumes) 섭취가 많을수록 고혈압 발생 위험 감소. 최적 섭취량 정량화: 두류 ≈170 g/일, 콩 60–80 g/일. DASH·지중해식 권고에 보강 근거 — 비용·부작용 거의 없는 1차 진료 개입.",
        "background": "DASH·지중해식 → 고혈압 예방 효과는 알려졌으나 '얼마나 먹어야 하는가'는 모호. 콩 단백·이소플라본·식이섬유·마그네슘·칼륨이 혈압 강하 기전. 메타분석으로 dose-response 정량화.",
        "design": "Systematic review·meta-analysis · 다수 cohort. 식이 빈도 설문 + 고혈압 발생률 추적. Dose-response 모델로 최적 섭취량 도출.",
        "result1_title": "정량화된 최적 섭취량",
        "result1_items": [
            ("두류 (콩과 식물)", "≈170 g/일"),
            ("콩 (대두·메주콩)", "60–80 g/일"),
            ("혈압 감소 (관찰)", "SBP −2~4 mmHg"),
            ("고혈압 발생 위험", "최적 섭취군에서 −15–20%"),
        ],
        "result2_title": "기전 — 무엇이 작용하나",
        "result2_items": [
            ("칼륨", "Na 배설 ↑"),
            ("마그네슘", "혈관 평활근 이완"),
            ("이소플라본", "혈관내피 NO 생성"),
            ("식이섬유", "체중·혈당·인슐린 저항성 개선"),
            ("식물성 단백질", "동물성 대체 시 LDL ↓"),
        ],
        "subgroup_title": "효과가 큰 군",
        "subgroup_items": [
            "전고혈압 (SBP 120–129) — 진행 억제",
            "비만·대사증후군 환자",
            "노인 (식이섬유 부족군)",
            "당뇨 동반자",
        ],
        "safety_title": "주의사항 — 거의 없음",
        "safety_items": [
            ("일반인", "안전, 상한 없음"),
            ("신부전 (CKD G4-5)", "칼륨·인 제한 필요"),
            ("갑상선 — 콩 이소플라본 영향", "갑상선약 흡수 시간차 두기"),
            ("가스·복부 팽만", "점진적 증량 권고"),
        ],
        "apply_who_title": "환자 상담 대상",
        "apply_who_items": [
            "전고혈압·1단계 고혈압 (약물 시작 전)",
            "대사증후군·당뇨 동반",
            "비만·체중 감량 목표",
            "심혈관 위험군 식이 보강",
        ],
        "apply_how_title": "구체적 처방 (실용)",
        "apply_how_items": [
            "두류 한 끼 한 컵(≈170 g) — 콩·렌틸·병아리콩 번갈아",
            "콩 60–80 g/일 = 두부 1/3모·콩나물 한 줌·두유 200 mL",
            "쌀 일부를 잡곡(콩·렌틸)으로 대체",
            "주 5일 이상 꾸준한 섭취 권고",
        ],
        "limits_title": "한계와 주의사항",
        "limits_items": [
            "관찰연구 — 인과성 단정 불가",
            "식이 설문의 회상 bias",
            "한국인 콩 섭취 (전통식) 풍부 → 추가 이득 폭 미상",
            "단독 개입보다 DASH·운동·체중 패키지가 효과 큼",
        ],
        "takehome_lines": [
            "고혈압 예방·관리에 콩·두류 적극 권장 — 비용·부작용 거의 X",
            "두류 한 끼 한 컵(≈170 g) + 콩 60–80 g/일 구체 처방",
            "전고혈압 단계에서 약물 시작 전 식이 개입 1순위",
            "신부전·갑상선약 환자는 개인 맞춤 조정",
        ],
        "qr_target": "decks/general/papers-20260524/soy-legumes-htn/",
    },
    {
        "slug": "rsv-realworld",
        "title": "RSV 백신,<br><em>실사용 데이터로 가이드 재정비</em>",
        "subtitle": "JAMA Internal Medicine 2026.05 — 60세+ 성인 RSV 백신 real-world 효과 분석",
        "chapter": "VACCINOLOGY · INFECTIOUS DISEASE",
        "source": "JAMA Internal Medicine Vol 186 No 5 (2026.05)",
        "importance": 4,
        "tldr": "60세 이상 성인 RSV 백신의 임상시험 효과(80–90%) vs 실사용 효과 격차 분석. 입원 예방 60–80% 수준으로 일관 유지. 75세+·만성 심폐질환·면역저하 우선 권고 보강. 가을 시즌 대비 환자 상담 자료.",
        "background": "RSV 백신(Arexvy·Abrysvo·mRESVIA) — 임상시험 효과 80–90%, 60세+ 권고. 그러나 실사용에서 효과 유지 여부·부작용 빈도·고위험군 정의는 추가 자료 필요. JAMA Internal Med real-world 분석으로 update.",
        "design": "Real-world cohort + case-control. 미국·EU 등 다국 데이터. 60세+ RSV 백신 접종 vs 미접종 비교. 효과·이상반응·고위험군 정의 재평가.",
        "result1_title": "실사용 효과",
        "result1_items": [
            ("RSV 입원 예방", "60–80% (RCT 80–90%와 격차)"),
            ("외래 RSV 감염", "효과 변동성 큼"),
            ("효과 지속", "1년 후에도 유지"),
            ("부스터 필요성", "2년차 자료 진행 중"),
        ],
        "result2_title": "이상반응 — 안전성",
        "result2_items": [
            ("국소 (주사 부위)", "30–60% — 경증, 1–2일"),
            ("전신 (피로·근육통)", "20–40% — 일시적"),
            ("길랑-바레 증후군", "백만 명 당 1–9 예 — 매우 드묾"),
            ("심막염·심근염", "신호 약함 (계속 추적)"),
        ],
        "subgroup_title": "우선 접종 대상 — 보강",
        "subgroup_items": [
            "75세 이상 — 입원·중증 위험 가장 큼",
            "만성 심부전·COPD·천식 중등도 이상",
            "면역저하 (장기이식·항암·고용량 스테로이드)",
            "장기요양시설 거주자",
        ],
        "safety_title": "한국 임상 실무",
        "safety_items": [
            ("국내 도입", "Arexvy(GSK)·Abrysvo(Pfizer) 일부 시행"),
            ("보험·비용", "비급여, 1회 ~₩20–30만"),
            ("인플루엔자·코로나 동시 접종", "안전성 OK"),
            ("재접종 간격", "1회 vs 매년 — 미확정"),
        ],
        "apply_who_title": "어떤 환자에 권고하나",
        "apply_who_items": [
            "75세 이상 — 강한 권고",
            "60–74세 + 만성 심폐질환 — 권고",
            "60–74세 일반 건강 — 환자 선호 기반 결정",
            "면역저하자 — 의사 판단·비용 안내",
        ],
        "apply_how_title": "환자 상담 포인트",
        "apply_how_items": [
            "가을(9–10월) 접종 권고 — 겨울 시즌 대비",
            "인플루엔자·폐렴구균 백신과 동시·근접 시행 가능",
            "주사 부위 통증·피로 1–2일 동반 안내",
            "비급여 비용 사전 안내, 본인 결정 존중",
        ],
        "limits_title": "한계와 주의사항",
        "limits_items": [
            "Real-world cohort — selection bias 가능",
            "RSV 진단 자체의 부정확성 (검사 빈도)",
            "한국인 데이터 부족 — 외삽 필요",
            "장기 효과·부스터 자료 미완성",
        ],
        "takehome_lines": [
            "RSV 백신 실사용 효과 일관 유지 — 입원 60–80% 예방",
            "75세+·만성 심폐질환·면역저하 우선 권고 (실사용 보강)",
            "가을 시즌 인플루엔자·폐렴구균 백신과 함께 안내",
            "비급여 ₩20–30만 안내 + 환자 선호 기반 결정",
        ],
        "qr_target": "decks/general/papers-20260524/rsv-realworld/",
    },
]


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1280">
  <title>{title_plain} — 광교바른내과</title>

  <meta property="og:type" content="article">
  <meta property="og:url" content="https://gwanggyo-barun.github.io/patient-education/{qr_target}">
  <meta property="og:title" content="{title_plain} — 광교바른내과">
  <meta property="og:description" content="{subtitle}">
  <meta property="og:image" content="https://gwanggyo-barun.github.io/patient-education/{qr_target}preview.png">
  <meta property="og:site_name" content="광교바른내과">
  <meta name="theme-color" content="#003366">

  <link rel="stylesheet" as="style" crossorigin
    href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css" />

  <link rel="stylesheet" href="../../../../shared/design-tokens.css">
  <link rel="stylesheet" href="../../../../shared/clinic-slides.css">

  <style>
    .slide__bg-num {{ display: none !important; }}
    .paper-meta-card {{ background: var(--color-canvas-warm); border-left: 4px solid var(--color-accent); padding: var(--space-4) var(--space-5); border-radius: var(--radius-md); margin-top: var(--space-4); }}
    .paper-meta-card strong {{ color: var(--color-navy); }}
    .data-row {{ display: grid; grid-template-columns: 220px 1fr; gap: var(--space-3); padding: var(--space-3) 0; border-bottom: 1px solid var(--color-border); }}
    .data-row:last-child {{ border-bottom: 0; }}
    .data-row__label {{ font-weight: 700; color: var(--color-navy); }}
    .data-row__value {{ color: var(--color-ink); }}
    .item-list {{ list-style: none; padding: 0; margin: 0; }}
    .item-list li {{ padding: var(--space-3) 0; border-bottom: 1px solid var(--color-border); display: flex; gap: var(--space-3); align-items: flex-start; }}
    .item-list li::before {{ content: "▸"; color: var(--color-accent); font-weight: 700; flex-shrink: 0; }}
    .stars {{ color: var(--color-accent); letter-spacing: 0.1em; font-size: 1.2em; }}
    .takehome-list li {{ background: var(--color-canvas-warm); padding: var(--space-4) var(--space-5); margin-bottom: var(--space-3); border-radius: var(--radius-md); border-left: 4px solid var(--color-navy); }}
    .takehome-list li::before {{ display: none; }}
  </style>
</head>
<body>

<div class="deck">

  <!-- SLIDE 01 · COVER -->
  <section class="slide slide--cover">
    <header class="slide__header">
      <img class="slide__logo" src="../../../../shared/assets/clinic_logo.png" alt="광교바른내과">
      <div class="slide__chapter"><strong>PATIENT EDUCATION</strong> · {chapter}</div>
    </header>
    <div class="slide__title-block">
      <h1 class="slide__title">{title}</h1>
      <p class="slide__subtitle">{subtitle}</p>
    </div>
    <footer class="slide__footer">
      <span class="slide__source">{source}</span>
      <span class="slide__importance"><span class="stars">{stars}</span></span>
    </footer>
  </section>

  <!-- SLIDE 02 · TL;DR -->
  <section class="slide">
    <header class="slide__header"><div class="slide__chapter">02 · TL;DR</div></header>
    <div class="slide__title-block"><h2 class="slide__title">핵심 한 문단</h2></div>
    <div class="slide__body">
      <p style="font-size: 1.35em; line-height: 1.6; color: var(--color-ink);">{tldr}</p>
    </div>
  </section>

  <!-- SLIDE 03 · BACKGROUND -->
  <section class="slide">
    <header class="slide__header"><div class="slide__chapter">03 · 배경</div></header>
    <div class="slide__title-block"><h2 class="slide__title">왜 이 연구가 중요한가</h2></div>
    <div class="slide__body">
      <p style="font-size: 1.15em; line-height: 1.7;">{background}</p>
    </div>
  </section>

  <!-- SLIDE 04 · STUDY DESIGN -->
  <section class="slide">
    <header class="slide__header"><div class="slide__chapter">04 · 연구 디자인</div></header>
    <div class="slide__title-block"><h2 class="slide__title">방법론</h2></div>
    <div class="slide__body">
      <p style="font-size: 1.1em; line-height: 1.7;">{design}</p>
    </div>
  </section>

  <!-- SLIDE 05 · RESULT 1 -->
  <section class="slide">
    <header class="slide__header"><div class="slide__chapter">05 · 주요 결과 ①</div></header>
    <div class="slide__title-block"><h2 class="slide__title">{result1_title}</h2></div>
    <div class="slide__body">
      <div class="data-rows">
        {result1_rows}
      </div>
    </div>
  </section>

  <!-- SLIDE 06 · RESULT 2 -->
  <section class="slide">
    <header class="slide__header"><div class="slide__chapter">06 · 주요 결과 ②</div></header>
    <div class="slide__title-block"><h2 class="slide__title">{result2_title}</h2></div>
    <div class="slide__body">
      <div class="data-rows">
        {result2_rows}
      </div>
    </div>
  </section>

  <!-- SLIDE 07 · SUBGROUP -->
  <section class="slide">
    <header class="slide__header"><div class="slide__chapter">07 · Subgroup</div></header>
    <div class="slide__title-block"><h2 class="slide__title">{subgroup_title}</h2></div>
    <div class="slide__body">
      <ul class="item-list">
        {subgroup_items}
      </ul>
    </div>
  </section>

  <!-- SLIDE 08 · SAFETY -->
  <section class="slide">
    <header class="slide__header"><div class="slide__chapter">08 · 안전성·실무</div></header>
    <div class="slide__title-block"><h2 class="slide__title">{safety_title}</h2></div>
    <div class="slide__body">
      <div class="data-rows">
        {safety_rows}
      </div>
    </div>
  </section>

  <!-- SLIDE 09 · APPLY WHO -->
  <section class="slide">
    <header class="slide__header"><div class="slide__chapter">09 · 임상 적용 ①</div></header>
    <div class="slide__title-block"><h2 class="slide__title">{apply_who_title}</h2></div>
    <div class="slide__body">
      <ul class="item-list">
        {apply_who_items}
      </ul>
    </div>
  </section>

  <!-- SLIDE 10 · APPLY HOW -->
  <section class="slide">
    <header class="slide__header"><div class="slide__chapter">10 · 임상 적용 ②</div></header>
    <div class="slide__title-block"><h2 class="slide__title">{apply_how_title}</h2></div>
    <div class="slide__body">
      <ul class="item-list">
        {apply_how_items}
      </ul>
    </div>
  </section>

  <!-- SLIDE 11 · LIMITS -->
  <section class="slide">
    <header class="slide__header"><div class="slide__chapter">11 · 한계</div></header>
    <div class="slide__title-block"><h2 class="slide__title">{limits_title}</h2></div>
    <div class="slide__body">
      <ul class="item-list">
        {limits_items}
      </ul>
    </div>
  </section>

  <!-- SLIDE 12 · TAKE-HOME -->
  <section class="slide slide--closing">
    <header class="slide__header">
      <img class="slide__logo" src="../../../../shared/assets/clinic_logo.png" alt="광교바른내과">
      <div class="slide__chapter">12 · TAKE-HOME</div>
    </header>
    <div class="slide__title-block">
      <h2 class="slide__title">1차 진료 Take-home</h2>
    </div>
    <div class="slide__body">
      <ul class="item-list takehome-list">
        {takehome_items}
      </ul>
    </div>
    <footer class="slide__footer">
      <div class="qr-block">
        <div class="qr-block__code"></div>
        <div class="qr-block__caption">광교바른내과 · {source}</div>
      </div>
    </footer>
  </section>

</div>

</body>
</html>
"""


def html_escape_minimal(s: str) -> str:
    return s.replace("&", "&amp;")


def render(paper: dict) -> str:
    def data_rows(items):
        return "\n        ".join(
            f'<div class="data-row"><div class="data-row__label">{html_escape_minimal(k)}</div><div class="data-row__value">{html_escape_minimal(v)}</div></div>'
            for k, v in items
        )

    def list_items(items):
        return "\n        ".join(
            f"<li>{html_escape_minimal(i)}</li>" for i in items
        )

    title_plain = paper["title"].replace("<br>", " ").replace("<em>", "").replace("</em>", "")
    stars = "★" * paper["importance"] + "☆" * (5 - paper["importance"])

    return HTML_TEMPLATE.format(
        title=paper["title"],
        title_plain=title_plain,
        subtitle=paper["subtitle"],
        chapter=paper["chapter"],
        source=paper["source"],
        stars=stars,
        tldr=paper["tldr"],
        background=paper["background"],
        design=paper["design"],
        result1_title=paper["result1_title"],
        result1_rows=data_rows(paper["result1_items"]),
        result2_title=paper["result2_title"],
        result2_rows=data_rows(paper["result2_items"]),
        subgroup_title=paper["subgroup_title"],
        subgroup_items=list_items(paper["subgroup_items"]),
        safety_title=paper["safety_title"],
        safety_rows=data_rows(paper["safety_items"]),
        apply_who_title=paper["apply_who_title"],
        apply_who_items=list_items(paper["apply_who_items"]),
        apply_how_title=paper["apply_how_title"],
        apply_how_items=list_items(paper["apply_how_items"]),
        limits_title=paper["limits_title"],
        limits_items=list_items(paper["limits_items"]),
        takehome_items=list_items(paper["takehome_lines"]),
        qr_target=paper["qr_target"],
    )


def main():
    for paper in PAPERS:
        out_dir = ROOT / paper["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        html_path = out_dir / "index.html"
        html_path.write_text(render(paper), encoding="utf-8")
        print(f"✓ {paper['slug']}: {html_path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
