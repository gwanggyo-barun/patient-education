# 스킬 라우팅 — HTML(clinic-content-system) vs PPTX(legacy) 선택 기준

> **목적**: 새 환자 교육 자료를 만들 때 "어느 스킬로 만들지"를 한 장에서 결정하기 위한 의사결정 노트.
> **단일 진실의 원천(SoT)**: 콘텐츠/디자인 룰 자체는 `SKILL.md` + `reference/brand-design-system.md`.
> 이 문서는 그 위에서 **출력 매체(HTML 통합 vs .pptx) 선택**만 다룬다.
> 관련 historical 기록: [`reference/migration.md`](./migration.md) (2026-05-09 마이그레이션 완료, 기록 보존용).

---

## 1. 기본 원칙 — HTML 우선 (default)

**새 콘텐츠는 기본적으로 `clinic-content-system`(HTML + PDF)으로 만든다.**

`clinic-content-system`은 기존 세 스킬(patient-education-pptx, patient-handout-pdf, lab-report-infographic)의 HTML 통합 후속 버전이다. 출력 측면에서 PPTX의 상위 호환이며, 다음 이점이 있다:

- 단일 디자인 토큰(`shared/design-tokens.css`) + 단일 빌드 파이프라인(`build.py`)으로 일관성 자동 보장
- 자동 QR 생성(Python `qrcode` SVG) + OG meta 7개 head 등록 → 노션/카톡 공유 최적화
- 버전 관리가 git 기반 (PPTX 시절 `_v1`/`_v2`/`_final` 파일 난립 부담 없음, `git checkout`으로 롤백)
- 폰트 렌더링이 환경 비의존 (PPTX는 사용자 PC에 Pretendard 미설치 시 fallback으로 디자인 깨질 위험)

---

## 2. PPTX(legacy)를 쓰는 경우 — .pptx가 *명시적으로* 필요할 때만

`patient-education-pptx`(legacy) 스킬은 **PowerPoint(.pptx) 파일 자체가 산출물로 명시적으로 요구되는 경우에만** 사용한다. 구체적 시나리오:

| # | 시나리오 | 이유 |
|---|---------|------|
| 1 | **동료 의사가 직접 편집**해야 하는 자료 | 받는 의사가 PowerPoint에서 텍스트/슬라이드를 직접 고쳐야 함 → 편집 가능한 .pptx 필요 |
| 2 | **학회 발표용 템플릿**이 .pptx 형식 강제일 때 | 학회/세미나 제출 양식이 PowerPoint 포맷을 요구 |
| 3 | **외부 협업자에게 .pptx 파일 자체**를 전달 | 상대가 HTML/PDF가 아닌 원본 .pptx 파일을 요청 |
| 4 | 사용자가 `"PPTX로"`, `"PowerPoint 파일로"`, `".pptx 파일"` 등을 **명시적으로 요청** | 명시적 포맷 지정은 사용자 의도로 존중 |

위 4가지 중 하나에도 해당하지 않으면 → **`clinic-content-system`(HTML)으로 만들고**, 필요 시 그 사실을 사용자에게 안내한다.

> ⚠️ **애매하면 HTML.** "환자한테 보여줄 PPT"처럼 *최종 포맷이 아니라 용도*만 말한 경우는 PPTX 강제가 아니다 → HTML 우선. .pptx 산출물 자체가 목적일 때만 legacy로 간다.

---

## 3. 한눈에 보는 결정 트리

```
새 환자 교육 자료 요청
        │
        ▼
.pptx 파일 자체가 산출물로 필요한가?
(동료 의사 직접 편집 · 학회 .pptx 템플릿 ·
 외부에 .pptx 전달 · 사용자가 "PPTX로" 명시)
        │
   ┌────┴─────┐
  예          아니오
   │            │
   ▼            ▼
patient-     clinic-content-system (HTML + PDF)  ← 기본값
education-        │
pptx (legacy)    ├─ "환자 교육 슬라이드/12장 덱"  → decks/{specialty}/{topic}/
                 ├─ "유인물/비치용/A4 한 장"       → handouts/{specialty}/{slug}/
                 └─ "검사 결과지 인포그래픽/결과지" → lab-reports/{topic}/{hash10}/
```

HTML 분기 안에서 **어떤 콘텐츠 타입**(deck / handout / lab-report)을 고를지는 README "새 콘텐츠 만들기" 표와 `SKILL.md`를 따른다. 이 문서는 그 *상위*의 매체 선택만 담당한다.

---

## 4. 공통 사항 (HTML / PPTX 무관)

- **디자인 토큰은 동일**: Navy `#003366` + Steel Blue `#5B9BD5`, Pretendard 1차 / Noto Sans KR fallback, 영문 라벨, 의학 용어 영문 병기(medical term in English). PPTX도 `reference/brand-design-system.md`를 SoT로 따른다 (legacy 스킬 SKILL.md의 "디자인 시스템" 절 참조).
- **PPTX 색상값 주의**: PptxGenJS는 `#` 없이 `"003366"` 형식 사용 (HTML CSS는 `#003366`).
- **기존 PPTX 자료는 그대로 보존**: 환자에게 이미 전달된 .pptx를 일괄 재생성할 필요 없음. 갱신 시점에 .pptx 강제가 아니면 HTML로 전환 권장.

---

## 5. 스킬 정의 파일 위치 메모 (운영 참고)

| 스킬 | SKILL.md 정의 위치 | 비고 |
|------|-------------------|------|
| `clinic-content-system` (메인) | 이 repo `SKILL.md` | dev clone = SoT. 룰 변경은 여기서 + git push |
| `patient-handout-pdf` (redirector) | 플러그인 | "유인물" 진입점, clinic-content-system으로 위임 |
| `lab-report-infographic` (redirector) | 플러그인 | "결과지 인포그래픽" 진입점, 위임 |
| `patient-education-pptx` (legacy) | **플러그인 전용** (`%APPDATA%\Claude\...\skills-plugin\...\patient-education-pptx\SKILL.md`) | dev clone에 정의 파일 **없음** |

> ⚠️ **PPTX 스킬은 dev clone에 정의 파일이 없고 플러그인 런타임 경로에만 존재한다.**
> repo의 메타 룰(SKILL.md §"메타 룰")상 `%APPDATA%\Claude\...` 같은 머신 종속 위치는 룰의 SoT로 삼지 않는다.
> 따라서 **PPTX 라우팅의 SoT는 (플러그인 SKILL.md가 아니라) 이 문서 + `reference/migration.md`**다.
> 플러그인 SKILL.md의 description/우선순위 안내 문구를 바꿔야 한다면, 플러그인 마켓플레이스 소스에서 갱신해야 하며 이 repo 편집만으로는 반영되지 않는다.
