# AI Image Assets

decks, handouts, lab-reports 의 인포그래픽은 두 단계로 운영된다:

- **Phase 1 (슬롯 설계 + `$imagegen` 래스터 생성)**: 초안 HTML 이 빌드·검증 통과한 직후, Codex 가 슬라이드/섹션을 훑어 인포그래픽 후보를 식별하고, 실제 HTML 슬롯을 만든 뒤 슬롯 크기에 맞춘 영문 프롬프트를 작성해 built-in `$imagegen`을 호출한다.
- **Phase 2 (배치 & 최종화)**: 생성된 PNG/WebP/JPEG 선택본을 `shared/assets/generated/` 에 저장하고, 적절한 `.ai-visual` 또는 자료별 figure/frame 으로 HTML 에 삽입한 다음 재빌드·검증·푸시한다.

## ⛔ 이미지 생성 절대 순서 (Layout-First) — 건너뛰기 금지

> 2026-06-12 사용자 재확인. **이미지를 먼저 만들어 놓고 레이아웃을 거기에 맞추지 않는다.**
> 레이아웃을 완성한 뒤, 어디에 이미지를 넣을지 계획하고, **그 슬롯의 실측 크기에 맞춰** 이미지를
> 생성한다. 이 순서를 지켜야 이미지 비율·크기가 깨지는 일이 최소화된다.

1. **레이아웃 완성 먼저** — HTML/CSS 초안을 `build.py` + `_validate_layout` 통과까지 끝낸다.
   이 시점에서야 슬롯 위치·크기가 확정된다.
2. **이미지 위치·개수 계획** — 어느 슬라이드/섹션에 이미지를 넣을지, 몇 장 넣을지(§0.a 적합성
   게이트 통과분만)를 먼저 정한다. 빈 슬롯을 실제 HTML 에 배치한다.
3. **슬롯 실측** — 배치한 슬롯의 실제 폭·높이(mm/px)와 strict ratio 를 잰다(§0, 추정 금지).
4. **그 크기에 맞춰 생성** — 실측 ratio/픽셀을 프롬프트에 명시해 `$imagegen` 으로 생성한다.
   결과가 슬롯과 어긋나면 이미지를 crop/재생성하지, **레이아웃을 이미지에 끌려가게 바꾸지 않는다.**
5. **배치 → 검증 → preview 육안 → push** (Phase 2).

⛔ **deck 완료 게이트**: deck 은 §0.a 게이트를 통과하는 이미지 후보가 4개 이상이면 **이미지 4~6장을
삽입하기 전까지 "완성"으로 보고하지 않는다.** 텍스트만으로 빌드가 통과해도 그것은 *초안*이다.
적합 후보가 4개 미만일 때만 텍스트 덱으로 마감하되, **"이미지 N장만 삽입(적합 후보 N개), 나머지
생략 사유: …"** 를 완료 보고에 반드시 남긴다. (계기: 2026-06-12 ABYSS 덱이 이미지 0장으로 마감됨.)

판단 기준:
- **품질·가독성 우선**: 이미지 개수를 채우지 않는다. 삽입 후 텍스트가 작아지거나 정보 위계가 흐려지면 만들지 않는다.
- **공통 방식**: decks, handouts, lab-reports 모두 레이아웃 슬롯 먼저 → 슬롯 실측 → built-in `$imagegen` PNG/WebP/JPEG 래스터 생성 → preview 검수 순서를 따른다.
- **handouts / lab-reports**: 보통 0~2개지만, 각 이미지가 다른 교육 포인트를 설명하고 레이아웃이 유지되면 여러 개도 허용한다. lab-reports 는 환자 PII 없는 검사 원리·해부·결과 이해 보조 이미지로 제한한다.
- **decks**: ⚠️ 2026-06-06 사용자 룰 — **deck당 4~6장, 이미지가 전체 내용의 핵심 시각 축**. Definition, Mechanism, Process, Action, Comparison 슬라이드에서 적합성 게이트를 통과하는 unique subject 4~6개를 설계한다. 텍스트는 절대 이미지에 굽지 않고 HTML 오버레이(.ai-visual__pin, 라벨 grid)로 얹는다. 적합 subject가 4개 미만이면 억지로 채우지 말고 사유를 보고에 남긴다.

PDF 빌드 시 이미지는 일반 파일로 렌더링되므로 Playwright 빌드와 GitHub Pages 배포 흐름을 바꾸지 않는다.

## 원칙

1. 의료 설명의 정확한 문구, 수치, 라벨은 HTML 텍스트로 둔다.
2. 이미지 프롬프트에는 환자명, 차트번호, 생년월일, 원본 검사 PDF 등 PII를 넣지 않는다.
3. 이미지 안에는 한글·영문 텍스트를 넣지 않는다. 필요한 라벨은 `.ai-visual__pin` 또는 HTML 주변 텍스트로 얹는다.
4. decks/handouts/lab-reports 보강용 새 설명 이미지는 기본적으로 built-in `$imagegen`으로 생성한 PNG/WebP/JPEG 래스터 자산이어야 한다. 코드 네이티브 SVG icon strip, healthicon 묶음, 작은 pictogram row 는 어떤 콘텐츠 타입에서도 이미지 보강으로 인정하지 않는다.
5. `$imagegen` 기본 생성 폴더의 원본은 삭제하지 않고, 선택본만 `shared/assets/generated/`에 복사한다.
6. 파일명은 `{topic-slug}-{purpose}-YYYYMMDD.{png|webp|jpg}`처럼 주제와 용도가 드러나게 짓는다.
7. 원본 프롬프트는 같은 이름의 `.prompt.md`로 남긴다. API/CLI로 생성한 경우에는 `.prompt.json`도 허용한다.
8. **이미지 생성은 반드시 slot-first**: HTML/CSS 슬롯을 먼저 만들고, 실제 슬롯 폭·높이와 비율을 잰 뒤 그 값으로 프롬프트를 작성한다. 이미지 파일을 먼저 만든 뒤 CSS로 억지로 맞추는 흐름은 금지한다.
9. 기존 자료 보강 작업에서는 로고/QR을 제외한 의미 있는 이미지가 하나라도 이미 있고 새 이미지가 같은 정보를 반복하면 스킵한다. 이미지가 없는 자료만 자동 slot-first 이미지 대상으로 삼되, 내용에 직접 맞는 visual intent 가 없으면 생략한다.
10. **내용 직접 연결**: prompt subject 는 해당 slide/section 의 제목·핵심 문장·표/카드 내용에서 온 구체적 개념이어야 한다. "clinic background", "medical icon strip", "organ-themed infographic"처럼 어디에나 붙일 수 있는 이미지는 실패다.
11. **제목 장식 금지**: title block 뒤에 투명 배경처럼 깔리는 이미지, 장식용 organ banner, 페이지 구조를 거의 바꾸지 않는 분위기 이미지는 실패다. 본문 이해를 돕는 전용 슬롯 또는 섹션 옆 figure 로 배치한다.
12. **SVG strip 금지**: 작은 code-native SVG context strip 을 만들어 넣고 "이미지 추가"로 간주하지 않는다. 수치 그래프, QR, 로고, 기존 SVG 아이콘 시스템처럼 deterministic vector가 본질인 경우만 예외다.
13. **중복 금지**: 같은 파일 재사용 금지. 파일명만 다른 동일 구도, 같은 generic strip, 같은 subject 반복도 중복으로 본다. deck/series 검수에서 `placements == unique_assets`, reused count 0 이 되어야 한다.
14. **불확실하면 생략**: 정확히 맞는 그림을 만들 수 없으면 이미지를 넣지 않는다. 이미지 생략은 실패가 아니지만 무관한 이미지는 실패다.

## Phase 1 — 인포그래픽 슬롯 설계 + `$imagegen` 래스터 생성

### 언제 트리거되는가

`build.py` 와 `python3 -m shared._validate_layout` 가 둘 다 통과한 직후. 텍스트와 레이아웃이 일단 확정된 지점에서만 슬롯을 만든다 — 그 전에 만들면 슬롯 위치가 바뀔 수 있어 무의미. **레이아웃 확정 후에야 정확한 슬롯 폭/높이 측정 가능**.

### 0. 슬롯 측정 — 필수 첫 단계 (Strict Ratio 우선)

⚠️ **일반 라운드 비율(4:3, 16:9, 1:1) 사용 금지.** 항상 실제 figure 슬롯의 폭/높이를 mm 단위로 측정해서 strict ratio를 산출하고 그대로 프롬프트에 명시한다. 2026-05-23 cvd-retinal-screening 사례 후 정식 룰화 (SKILL.md Known Gotchas §12).

⚠️ **순서 금지 사항**: `$imagegen`을 먼저 호출한 뒤 그 결과물에 맞춰 레이아웃을 바꾸지 않는다. 먼저 HTML에 슬롯을 배치하고 `_validate_layout` 또는 Playwright screenshot으로 슬롯이 실제 자료 안에서 성립하는지 확인한 다음 이미지를 생성한다. 생성 결과가 슬롯과 어긋나면 이미지를 crop/resize하거나 재생성하고, 레이아웃을 이미지에 끌려가게 바꾸지 않는다.

deck 의 `.ai-visual--split` / `.ai-visual--strip` 슬롯처럼 고정 프레임에 들어가는 생성 이미지는 **레이아웃 슬롯에 맞춘 full-bleed 구도**로 만든다. 프롬프트에 “fill the entire frame edge to edge, no blank side gutters, no centered small vignette”를 명시하고, 선택본은 슬롯 비율에 맞춰 crop/fit 저장한 뒤 `.ai-visual--fill`을 붙인다. 해부도처럼 전체 보존이 더 중요한 경우에만 contain 배치를 쓰고, 그때도 좌우 여백이 눈에 띄지 않는지 preview로 확인한다.

> 🔴 **NO-CROP 최우선 (2026-06-19 원장 검수, ROMA 덱)**: 위 full-bleed cover-crop은 **가장자리에 의미가 없는 ambient 이미지에만** 쓴다. **다이어그램류(흐름·분기·비교·프로세스·단계·아이콘 행 등 Mechanism/Process/Comparison)는 cover-crop 금지** — 화살표·분기·끝 객체가 잘려 정보가 사라진다. 이때 기본은 **슬롯 비율 = 생성 이미지 비율을 처음부터 정확히 일치 + `object-fit: contain`(잘림 0)**. 비율을 일치시키면 contain이라도 레터박스가 없다. 즉 strip(가로로 넓은 고정 비율)에 3:1 이미지를 욱여넣어 cover로 자르는 흐름을 폐기하고, **슬롯 aspect-ratio를 이미지 콘텐츠가 다 들어오는 비율로 잡고 그 비율로 생성**한다. preview에서 가장자리 콘텐츠가 조금이라도 잘리면 FAIL → 재생성 또는 슬롯 비율 조정. (SKILL.md §15 "잘림 0 NO-CROP 규칙" 참조 — 그쪽이 SoT.)

### 0.a. 내용 적합성 게이트 — 수량보다 먼저

슬롯을 만들기 전에 다음 5줄을 먼저 적는다. 한 줄이라도 못 채우면 이미지 후보가 아니다.

```text
slide_or_section:
source_text_summary:
visual_intent:
unique_subject:
why_this_improves_readability:
```

- `source_text_summary`는 실제 슬라이드/섹션 문구를 요약한다.
- `visual_intent`는 Anatomy / Mechanism / Process / Equipment / Action / Comparison 중 하나로 시작한다.
- `unique_subject`는 같은 deck/series 안에서 반복되지 않아야 한다.
- "분위기", "의료 느낌", "카드 장식", "배경 보강"이 주된 이유면 탈락이다.
- title block 뒤에 깔리는 장식 이미지나 투명 배경 이미지는 탈락이다.
- 작은 SVG icon strip, context strip, healthicon row 로 충분하다고 판단되면 탈락이다.
- 이미지가 들어가면서 본문 폰트, 카드 간격, footer clearance 가 나빠지면 탈락이다.

### 0.a.1. handouts v2 — ImageIntent 의무화 (2026-06-12, SoT=`PRD/handout-visual-v2/`)

**handouts 는 위 5줄 게이트를 통과한 후보를 기계검증 가능한 `ImageIntent` 로 승격해 사이드카로 남기는 것까지가 의무다.** 채택 이미지(또는 명시적 생략 슬롯)마다 `shared/assets/generated/{topic-slug}-{slot-key}-YYYYMMDD.intent.json` 작성:

| 필드 | 내용 |
|---|---|
| `explains` | **이 이미지가 설명할 본문 문장/표/체크리스트 정확히 1개** — 본문에 대응 문장이 없으면 "겉도는 이미지", 만들지 않는다 |
| `visual_type` | Anatomy / Mechanism / Process / Equipment / Action / Comparison 중 하나 — **그 외면 슬롯 생성 금지**(텍스트 레이아웃 개선으로 대체). SVG icon/context strip 은 visual_type 에 미포함 |
| `must_show[]` | 이미지에 반드시 보여야 할 요소 ≥1 — aboutness 검증의 채점 기준 |
| `prompt_en` | 슬롯 실측 비율(§0)을 명시한 영문 프롬프트 |
| `candidates[]` | 생성 후보별 `file` / `gen_path` / `verdict`(aboutness 교차검증 결과) |
| `adopted` / `skipped_reason` | 채택 1장 또는 null+생략 사유 (빈 슬롯 HTML 잔존 금지) |

전체 스키마·예시 = `shared/_image_gate.py` docstring. 검증: `python3 -m shared._image_gate <html_path>` (intent 누락·스키마 위반·미달 채택 = exit 1 차단). decks / lab-reports 확장은 P5 — 그 전까지는 위 0.a 5줄 게이트만 적용.

#### 슬롯 폭 표준 (A4 핸드아웃 / 검사결과지)

페이지 14mm padding 기준:

| 슬롯 타입 | 폭 (mm) | 산출 |
|---|---|---|
| 본문 풀폭 (single column) | **182mm** | 210 − 14×2 |
| `body-2col` 좌/우 각 | **88mm** | (182 − gap 6mm) / 2 |
| `body-3col` 각 | **58mm** | (182 − gap 4mm×2) / 3 |

#### 슬롯 폭 표준 (deck slide, 1280×720)

좌우 padding 80px 기준:

| 슬롯 타입 | 폭 (px) | 산출 |
|---|---|---|
| 본문 풀폭 | **1120px** | 1280 − 80×2 |
| `body-2col` 좌/우 각 | **536px** | (1120 − gap 48px) / 2 |

#### 높이

해당 figure에 명시한 `height` 그대로 사용 (예: `height:62mm` → 62mm). HTML 작성 후 figure에 정해진 값을 보고 결정. **추정 금지, 측정 필수**.

#### 비율·픽셀 산출

```
ratio = slot_width_mm / slot_height_mm    (소수점 둘째 자리)
px_w  = slot_width_mm  × 12               (300 DPI 인쇄)
px_h  = slot_height_mm × 12
```

예시:

| 슬롯 폭 × 높이 | ratio | 권장 px |
|---|---|---|
| 182mm × 50mm | **3.64 → `3.6:1`** | **2200 × 610** |
| 182mm × 40mm | **4.55 → `4.5:1`** | **2200 × 490** |
| 182mm × 62mm | **2.94 → `3:1`** | **2200 × 740** |
| 88mm × 78mm | **1.13:1** | **1300 × 1150** |
| 88mm × 88mm | 1:1 | 1100 × 1100 |
| 58mm × 58mm | 1:1 | 800 × 800 |

### 0.b. Multi-column 정렬 룰 (다단계 흐름도, 비교 매트릭스)

N-column 시각(4단계 흐름, 3개 결과 등)은 **각 요소의 중심 좌표를 % 단위로 프롬프트에 명시**한다. HTML 라벨 grid의 column 중심과 정확히 일치해야 정렬이 깨지지 않는다 (Known Gotchas §13).

| N | 중심 위치 (%) |
|---|---|
| 2 | 25 · 75 |
| 3 | 16.7 · 50 · 83.3 |
| 4 | **12.5 · 37.5 · 62.5 · 87.5** |
| 5 | 10 · 30 · 50 · 70 · 90 |

세로 분포(y 좌표)도 동일 공식.

대응하는 HTML: figure와 라벨 grid 둘 다 동일 `max-width` + `margin:0 auto` 가운데 정렬. column 폭이 같아야 매칭.

```html
<figure class="ai-visual" style="height:62mm; max-width:118mm; margin:0 auto; padding:0; ...">
  <img src="..." style="width:100%; height:100%; object-fit:contain;">
</figure>
<div style="display:grid; grid-template-columns: repeat(4, 1fr); max-width:118mm; margin:0 auto;">
  <div>① 라벨1</div><div>② 라벨2</div><div>③ 라벨3</div><div>④ 라벨4</div>
</div>
```

### 0.c. 텍스트 처리 — HTML Pretendard 오버레이만 (이미지에 굽지 말 것)

이미지 안에 한글·영문 텍스트를 굽는 것 절대 금지 (Known Gotchas §14):
- ❌ 폰트 불일치 (이미지 폰트 vs HTML Pretendard) → 자료 일관성 깨짐
- ❌ 저해상도에서 흐림, 가독성 ↓
- ❌ 수정·오타 → 이미지 재생성 필요
- ✅ HTML 오버레이: 폰트 일관성, 즉시 수정 반영, 정렬 정확

모든 프롬프트의 마지막 블록에 다음 강제 문구 포함:

```text
ABSOLUTELY NO TEXT:
Do NOT include any letters, numbers, words, labels, captions, 
or any characters in any language (Korean, English, Chinese, etc.) 
anywhere on the canvas. Pure visual only.
HTML will overlay Korean labels using Pretendard font separately.
```

### 후보 식별 — 6 카테고리

각 슬라이드/섹션을 다음 6 카테고리에 매핑한다.

| 카테고리 | 대상 슬라이드/섹션 | 적합 예시 |
|---|---|---|
| **Anatomy (해부도)** | Definition · Asymmetric Split · 첫 본문 슬라이드 | 갑상선·간·대장·심장·관절·갑상선 단면 |
| **Mechanism (기전)** | Definition · Risk Factors | 인슐린 저항성·역류 메커니즘·콜레스테롤 침착·동맥 협착 |
| **Process (절차/타임라인)** | Timeline · Schedule | 내시경 준비 단계·약 복용 시점·정기 검사 주기 |
| **Equipment (장비/도구)** | Hero · Asymmetric Split | CGM 부착 모습·혈압계·내시경·DXA 장비·인슐린 펜 |
| **Action (자세/행동)** | Lifestyle · Density Grid · Checklist | 식판 모델·운동 자세·금연·인슐린 자가 주사·올바른 양치 |
| **Comparison (비교)** | Comparison · DO/DON'T | 정상 vs 비정상 조직·올바른 자세 vs 잘못된 자세 |

**스킵해야 하는 슬롯**: Hero Number 단독, Regimen Tile 약물 조합표, 7-Checklist 액션 카드, alert strip — 이미지가 들어가면 오히려 어수선해진다.

**선정 가이드**: handouts / lab-reports → 대개 0~2개지만, 서로 다른 교육 포인트를 설명하는 전용 이미지 섹션이면 여러 개도 가능하다. 12장 deck → 이해를 크게 돕는 만큼만. 세 타입 모두 같은 slot-first + `$imagegen` raster 방식으로 만들며, 수량이 아니라 slide/section 별 visual intent, 이미지 품질, 중복 없음이 기준이다.

### `$imagegen` 생성·저장 절차

1. 내용 적합성 게이트를 통과한 후보만 남긴다.
2. 후보마다 실제 슬롯을 먼저 만든다. 슬롯은 fixed width/height 또는 aspect-ratio로 안정화하며, 좋은 선례(`bone-density-prep`, `colonoscopy-prep`, `nasal-spray-allergic-rhinitis`, `insulin-start`)처럼 이미지가 자료의 주요 설명 섹션이 되게 한다.
3. 같은 deck/series 안의 기존 이미지 파일·프롬프트와 비교해 중복 subject/구도가 아닌지 확인한다.
4. 슬롯 실측값으로 영문 프롬프트를 작성한다. 텍스트·숫자·PII는 이미지에 넣지 않는다.
5. `$imagegen` 기본 내장 모드로 후보별 1장씩 생성한다. decks/handouts/lab-reports 보강에서는 코드 네이티브 SVG를 `$imagegen` 대체물로 쓰지 않는다. 서로 다른 이미지를 하나의 프롬프트에 묶지 않는다.
   - ⚠️ **`tools/codex_imagen.sh` 는 순차 호출만** (2026-06-12 ABYSS 작업 중 실측): 여러 장을 동시(병렬)로 돌리면 Codex 공유 출력폴더(`~/.codex/generated_images/`)에서 레이스가 나 **두 타깃이 같은 이미지를 집어가 중복**이 된다. 4장이면 4번 순차 실행하고, 끝나면 `shasum`으로 전부 고유한지 반드시 확인한다.
6. 생성 이미지를 확인하고, 선택본을 `shared/assets/generated/`에 저장한다.
7. 같은 이름의 `.prompt.md`에 slide/section, source text summary, visual intent, unique subject, slot size/ratio, negative constraints 를 저장한다.
8. HTML 라벨·캡션·핀을 얹고, `_validate_layout` + preview PNG 육안 확인까지 끝낸다. preview가 작은 아이콘 행이나 얇은 strip처럼 보이면 실패로 보고 재생성한다.

### handouts v2 — 안정 생성 루프 + aboutness 교차검증 (2026-06-12)

handouts 는 위 절차의 5~8단계를 다음 게이트 루프로 강화한다 (SKILL.md §3.5.e 가 정본):

**안정 생성 루프 (P2)**
1. 슬롯당 **후보 2~3장** 생성 (후보별 별도 호출). 호출 실패 시 같은 경로 **재시도 ≥2**.
2. 경로 자체가 죽으면 **fallback 체인**: `tools/codex_imagen.sh` ↔ built-in `$imagegen` (driver 반대 경로 1회 전환) → 둘 다 불가면 **명시적 생략 + `skipped_reason`** (`no image added: <사유>`). 사용 경로는 intent.json `candidates[].gen_path` 에 기록 — 무엇이 왜 실패했는지 재현 가능해야 한다.

**aboutness 교차검증 (P1)** — 후보마다 VLM 이 이미지 실물을 직접 보고 판정:
```text
이 이미지가 "{explains}" 를 실제로 묘사하는가?
{must_show[]} 각 요소가 화면에 보이는가?
→ depicts_intent(Y/N) · aboutness(0~100) · quality(0~100) · 근거
```
- **quality 체크 항목**: 한글(또는 어떤 언어든) 텍스트 혼입 = 즉시 탈락(`korean_text_in_image`), 해부학적/구도 왜곡, 저해상도·블러.
- **채택 = `depicts_intent ∧ aboutness ≥ T_about(70) ∧ quality OK` 후보 중 `aboutness × quality` 최고 1장.**
- 전 후보 미달 → must_show 를 구체화해 재생성 1회 → 그래도 미달이면 생략+사유. 임계는 초기값·캘리브레이션 대상.
- 판정은 intent.json `candidates[].verdict` 에 기록하고 `python3 -m shared._image_gate` 로 정합성 검증.

**레이아웃 회귀 가드 (P3)** — 삽입 전/후 `shared/_visual_diff` 스냅샷 비교 + `_validate_layout` **AND 게이트**. 실패 시 슬롯 보정 후 재검(최대 2회) → 그래도 실패면 생략+복원. 상세는 SKILL.md §3.5.d/§3.5.e.

### 영문 프롬프트 기본 골격 (Strict Ratio · 빈 사이드 패널 금지 · 텍스트 0)

`$imagegen`은 한국어 의료 프롬프트보다 구조화된 영문 프롬프트를 더 안정적으로 따른다. 항상 영문으로 작성하고, **§0 슬롯 측정에서 산출한 strict ratio와 픽셀을 그대로 채워 사용**한다.

```text
Create a {style descriptor — e.g., "clean medical illustration",
"large patient-facing process sequence"},
aspect ratio strictly {W}:{H} ({px_w} x {px_h} pixels), white background.

{LAYOUT / COMPOSITION SPEC}
- Describe exact regions ("Left 55% of width", "Right 45% of width")
- For multi-step visuals, specify full scene regions in % per §0.b
- Specify subject orientation, view angle, scene composition
- Subject must depict this slide/section's concrete source text, not a generic medical background.

STYLE:
Rich semi-realistic medical illustration {kind} — soft volumetric shading,
translucent glossy anatomical structures, gentle depth and dimensionality,
detailed equipment/people rendering when the scene calls for it,
premium hospital aesthetic. Cool blue tonal palette anchored on
navy #003366 and steel blue #5B9BD5 (tints/shades of these allowed),
soft white-to-light-blue gradient background.

⚠️ 2026-06-06 사용자 확정: **플랫 벡터/아이콘 스타일 금지** — 기존 자산
(bone-density-room-guide, acs-crc-cfdna-biology 등)과 같은 입체감 있는
세미리얼 일러스트가 하우스 스타일이다. 새 이미지는 이 스타일을 따른다.

⚠️ **v2 P4 (2026-06-12)**: 위 STYLE 단락이 **브랜드 스타일 디스크립터 표준 문구**다 —
모든 `$imagegen`/`codex_imagen` 프롬프트에 **항상 그대로 삽입**한다(자료 간 이미지 톤
통일 장치). 색·토큰 SoT 는 `reference/brand-design-system.md`. 누락·임의 변형 시
`shared/_tone_score.py` ToneScore(`image_style_ok`) 감점 대상.

CRITICAL CONSTRAINTS:
- Illustration must SPAN THE ENTIRE CANVAS evenly — no empty side panels, 
  no centered cluster with empty margins on left/right or top/bottom.
- All depicted elements must use the full available canvas dimensions.
- For deck split/strip slots, compose as full-bleed artwork for the exact slot ratio.
- Avoid a small centered vignette, icon island, postcard border, or blank gutters.
- Avoid generic stethoscope, hospital corridor, abstract DNA, floating organs, or repeated motif unless that exact object is the slide subject.
{any additional constraints specific to this image}

ABSOLUTELY NO TEXT:
Do NOT include any letters, numbers, words, labels, captions, 
or any characters in any language (Korean, English, Chinese, etc.) 
anywhere on the canvas. Pure visual only.
HTML will overlay Korean labels using Pretendard font separately.
```

토큰 치환 가이드 (값은 슬롯 실측 결과로 채움):

| 토큰 | 채우는 방법 |
|---|---|
| `{style descriptor}` | 콘텐츠 형식: `"clean medical banner illustration"`, `"large patient-facing process sequence"`, `"side-by-side comparison diagram"` 등 |
| `{W}:{H}` | §0.b 비율 산출 결과. 예: `3.6:1`, `1.13:1`, `1:1` |
| `{px_w} x {px_h}` | §0.b 픽셀 산출 결과. 예: `2200 x 610`, `1300 x 1150` |
| `{kind}` | decks → `deck slide infographic` · handouts → `A4 portrait handout infographic` · lab-reports → `A4 portrait result-page infographic` |
| `{LAYOUT}` | Anatomy → 단일 중앙 / Process → N-column 균등 / Comparison → 좌우 split / Equipment → 장비 풀폭 |

### 카테고리별 채워진 프롬프트 템플릿

⚠️ **다음 옛 템플릿은 일반 비율을 사용한다.** 새 작업에서는 **§0 슬롯 측정 → 새 골격(위 §영문 프롬프트 기본 골격)에 strict ratio 채우기** 방식을 우선 사용한다. 아래 템플릿은 카테고리별 "어떤 시각이 적합한가"의 참고용으로만 보고, 비율·픽셀 부분은 반드시 슬롯 실측값으로 덮어쓴다.

복사 → subject 한 줄만 갈아 끼우면 쓸 수 있는 완성형. (소문자 마침표 형식 유지.)

**Anatomy — 갑상선·간·대장·심장·관절 등 장기 해부도**

```text
Create a clean, patient-friendly medical illustration for a Korean clinic deck slide.
Subject: anatomy of the {organ name}, {brief shape/landmark descriptor},
with a simplified cross-section showing relative position of neighboring structures.
Style: premium hospital patient education infographic, warm white background,
restrained navy (#003366) and steel-blue (#5B9BD5) accents, soft shadows,
isometric 3/4 view.
Composition: subject centered, with generous whitespace on left and right for HTML label pins.
Do not include any text, letters, numbers, logos, watermarks, or patient information.
Aspect ratio: 4:3.
```

**Mechanism — 기전 단면도 (역류·인슐린 저항성·동맥 침착 등)**

```text
Create a clean, patient-friendly medical illustration for a Korean clinic deck slide.
Subject: a simplified cutaway cross-section illustrating {mechanism in one English clause,
e.g., "stomach acid refluxing past a weakened lower esophageal sphincter"}.
Style: premium hospital patient education infographic, warm white background,
restrained navy (#003366) and steel-blue (#5B9BD5) accents, soft shadows,
cutaway cross-section view.
Composition: subject centered, with generous whitespace on left and right for HTML label pins.
Do not include any text, letters, numbers, logos, watermarks, or patient information.
Aspect ratio: 4:3.
```

**Process — 절차 타임라인 (내시경 준비·약 복용 시점 등)**

```text
Create a clean, patient-friendly medical illustration for a Korean clinic deck slide.
Subject: a four-step horizontal process illustration of {process name, e.g., "colonoscopy preparation"},
showing four sequential scenes left-to-right: {step 1}, {step 2}, {step 3}, {step 4}.
Style: premium hospital patient education infographic, warm white background,
restrained navy (#003366) and steel-blue (#5B9BD5) accents, soft shadows,
side view, left-to-right reading order.
Composition: four scenes evenly spaced, with generous whitespace above and below for HTML labels.
Do not include any text, letters, numbers, logos, watermarks, or patient information.
Aspect ratio: 16:9.
```

**Equipment — CGM·혈압계·내시경·DXA 등 장비**

```text
Create a clean, patient-friendly medical illustration for a Korean clinic deck slide.
Subject: {equipment name, e.g., "a continuous glucose monitor (CGM) sensor attached to the upper arm"},
shown on a friendly adult patient in casual clothing, focusing on the device and attachment site.
Style: premium hospital patient education infographic, warm white background,
restrained navy (#003366) and steel-blue (#5B9BD5) accents, soft shadows,
isometric 3/4 view.
Composition: subject centered, with generous whitespace on left and right for HTML label pins.
Do not include any text, letters, numbers, logos, watermarks, or patient information.
Aspect ratio: 4:3.
```

**Action — 식판·운동 자세·자가 주사 등 행동**

```text
Create a clean, patient-friendly medical illustration for a Korean clinic A4 portrait handout.
Subject: {action description, e.g., "a balanced Korean meal plate following the diabetes plate model,
with half non-starchy vegetables, a quarter whole grains, and a quarter lean protein"}.
Style: premium hospital patient education infographic, warm white background,
restrained navy (#003366) and steel-blue (#5B9BD5) accents, soft shadows,
overhead top-down view.
Composition: subject centered horizontally near the top, with generous whitespace
at top and bottom for caption and pins.
Do not include any text, letters, numbers, logos, watermarks, or patient information.
Aspect ratio: 16:9.
```

**Comparison — 정상 vs 비정상 / 올바른 자세 vs 잘못된 자세**

```text
Create a clean, patient-friendly medical illustration for a Korean clinic deck slide.
Subject: a side-by-side comparison of {left subject, e.g., "a healthy normal artery"}
on the left and {right subject, e.g., "an artery narrowed by cholesterol plaque"} on the right.
Style: premium hospital patient education infographic, warm white background,
restrained navy (#003366) and steel-blue (#5B9BD5) accents, soft shadows,
cutaway cross-section view.
Composition: two subjects evenly spaced, with a clear vertical center divider area
and whitespace below each for HTML labels.
Do not include any text, letters, numbers, logos, watermarks, or patient information.
Aspect ratio: 16:9.
```

### 파일명 컨벤션 (제안 시 함께 통보)

`shared/assets/generated/{topic-slug}-{slot-key}.png`

- `topic-slug`: 자료 슬러그 그대로 (예: `thyroid-nodule`, `colonoscopy-prep`).
- `slot-key`: 슬라이드/섹션을 식별할 짧은 케밥 (예: `anatomy`, `prep-timeline`, `plate-model`, `before-after`). 슬라이드 번호는 권장 X — 슬라이드가 재배열돼도 이름이 살아남게.
- 확장자: 사용자가 PNG 로 받으면 `.png`, WebP 로 받으면 `.webp` (변환하지 않음).

### 사용자에게 출력하는 형식 (블록 단위 반복)

빌드 통과 메시지 직후 한 번에 정리:

```
📸 인포그래픽 제안 — {topic-slug}

문서 초안이 빌드·검증을 통과했습니다. 다음 위치에 인포그래픽을 추가하면 이해도가 크게 올라갑니다.
아래 프롬프트로 Codex가 `$imagegen`을 직접 호출한다.
받는 즉시 알맞은 슬롯에 배치하고 재빌드·푸시합니다.

────────────────────────
### 1. {위치 — 예: 슬라이드 3 / Definition} — {주제 한국어}
**Source text summary**: {실제 슬라이드/섹션 문구 요약}
**왜**: {한 줄 — 텍스트로 설명하기 어려운 이유}
**카테고리**: {Anatomy / Mechanism / Process / Equipment / Action / Comparison}
**Unique subject**: {같은 deck/series 안에서 반복되지 않는 구체 subject}
**슬롯**: `.ai-visual--{hero|portrait|compact|contain}` — **{폭mm} × {높이mm}** → **strict ratio {W}:{H}** ({px_w} × {px_h} px)
**저장 파일명**: `shared/assets/generated/{topic-slug}-{slot-key}.png`

$imagegen 프롬프트:
​```text
{슬롯 실측값으로 채운 영문 프롬프트 — §영문 프롬프트 기본 골격 참조}
​```
────────────────────────
### 2. ...
```

각 항목은 위치 / source text summary / 왜 / 카테고리 / unique subject / 슬롯+ratio / 파일명 + `$imagegen` 영문 프롬프트를 항상 포함한다.

---

## Phase 2 — 생성 이미지 배치 & 최종화

`$imagegen` 결과가 생성되면 다음을 자동 수행:

1. 선택한 PNG/WebP/JPEG 를 **제안 시 정한 파일명 그대로** `shared/assets/generated/{topic-slug}-{slot-key}.{ext}` 에 저장한다. `$imagegen` 기본 생성 폴더의 원본은 삭제하지 않는다.
2. 같은 이름의 `.prompt.md` 에 원본 프롬프트와 함께 slide/section, source text summary, visual intent, unique subject, slot size/ratio, negative constraints 를 저장한다.
3. 해당 슬라이드/섹션 HTML 의 placeholder 위치(또는 텍스트 카드 자리)에 `.ai-visual` 컴포넌트 삽입 — 변형(`--hero` / `--portrait` / `--compact` / `--contain`)은 Phase 1 에서 정한 슬롯 그대로.
4. 이미지 안에 텍스트가 끼어 들어왔으면 다시 생성 요청 (라벨은 모두 HTML).
5. `python3 -m shared._validate_layout <html_path>` 재실행 → `OK` 확인.
6. 중복/무관 이미지 audit: 배치 수와 unique asset 수가 같아야 하며, 각 asset 의 prompt subject 가 해당 slide/section source text 와 직접 맞아야 한다.
7. `python3 build.py` 재실행 → `output/{kind}/{slug}-preview.png` 로 시각 점검 (이미지가 슬롯을 잘 채우는지, 텍스트 가독성을 해치지 않는지, 화이트 백그라운드가 페이지 배경과 자연스럽게 이어지는지).
8. git status audit → 명시적 add → 단독 commit → push → Notion DB upsert 자동.

---

## 기본 워크플로우: `$imagegen` 직접 생성

1. HTML에 이미지 슬롯을 만든다.
2. 슬롯 실측값으로 영문 프롬프트를 작성한다.
3. Codex가 built-in `$imagegen`을 호출한다.
4. 가장 좋은 컷을 `shared/assets/generated/`에 저장하고, `.ai-visual` 또는 자료별 figure/frame 컴포넌트로 배치한다.
5. `python3 -m shared._validate_layout <html_path>`와 `python3 build.py` 또는 대상별 시각 확인을 수행한다.

$imagegen 프롬프트 예시:

```text
Create a clean, patient-friendly medical illustration for an A4 Korean clinic handout.
Subject: colonoscopy preparation, clear liquids, medication packet, calendar, and bathroom route.
Style: premium hospital patient education infographic, accurate but non-scary, warm white background, restrained navy/steel-blue/green accents.
Composition: leave clear empty areas for HTML labels and captions.
Do not include any text, letters, numbers, logos, watermarks, patient names, chart numbers, or personal information.
```

## 선택 워크플로우: API/CLI로 생성

사용자가 명시적으로 CLI/API 경로를 요구하거나 `$imagegen` 기본 도구가 실패했을 때만 사용한다. API 과금/한도는 별도다.

```bash
export OPENAI_API_KEY="..."

python3 tools/generate_image_asset.py \
  --prompt "A friendly colonoscopy preparation scene: calendar, clear liquids, medication packet, bathroom route, simplified clean medical infographic composition with empty areas for HTML labels." \
  --output shared/assets/generated/colonoscopy-prep-hero.png \
  --size 1536x1024 \
  --quality medium
```

기본 모델은 `gpt-image-1.5`이며, 필요하면 환경변수나 옵션으로 바꾼다.

```bash
OPENAI_IMAGE_MODEL=gpt-image-1 python3 tools/generate_image_asset.py ...
python3 tools/generate_image_asset.py --model gpt-image-1-mini ...
```

API를 호출하지 않고 최종 프롬프트만 확인:

```bash
python3 tools/generate_image_asset.py \
  --prompt "Thyroid ultrasound exam with a simplified thyroid anatomy inset." \
  --output shared/assets/generated/thyroid-ultrasound.png \
  --dry-run
```

## HTML 삽입

3-level deep 자료(`handouts/lifestyle/slug/index.html`, `lab-reports/topic/slug/index.html`)는 `../../../shared/...`를 쓴다.

```html
<figure class="ai-visual ai-visual--hero">
  <img
    class="ai-visual__image"
    src="../../../shared/assets/generated/colonoscopy-prep-hero.png"
    alt="대장내시경 준비 과정을 설명하는 부드러운 의료 일러스트"
  >
  <figcaption class="ai-visual__caption">검사 준비는 식사 조절, 장정결제, 수분 섭취 순서로 진행합니다.</figcaption>
  <span class="ai-visual__pin" style="left: 11mm; top: 10mm;">식사 조절</span>
  <span class="ai-visual__pin" style="right: 10mm; top: 15mm;">수분 섭취</span>
</figure>
```

4-level deep 자료는 `../../../../shared/...`를 쓴다.

## CSS 컴포넌트

- `.ai-visual` — 기본 이미지 프레임
- `.ai-visual--hero` — A4 상단 넓은 설명 이미지
- `.ai-visual--portrait` — 세로 그림용
- `.ai-visual--compact` — 작은 보조 그림
- `.ai-visual--contain` — 이미지 전체가 잘리지 않게 contain 배치
- `.ai-visual--fill` — 슬롯 전체를 채우는 generated deck image용 cover 배치
- `.ai-visual__caption` — 이미지 위 캡션
- `.ai-visual__pin` — HTML 라벨 칩

## 검증

```bash
python3 -m shared._validate_layout handouts/endoscopy/colonoscopy-prep/index.html
python3 build.py
```

`build.py`는 HTML 안의 `../../../shared/assets/generated/...` 경로가 실제 파일로 존재하는지 사전 검증한다.
이미지가 깨지면 PDF 생성 전에 CSS/asset path error로 실패해야 정상이다.

**handouts v2 추가 게이트** (기본 ON, `HANDOUT_V2_GATES=0` = 관찰 모드 — SKILL.md §검증 워크플로우 참조):

```bash
python3 -m shared._image_gate handouts/{specialty}/{slug}/index.html     # ImageIntent + aboutness 불변식
python3 -m shared._visual_diff capture <html> /tmp/before.png            # 삽입 전 스냅샷
python3 -m shared._visual_diff compare /tmp/before.png /tmp/after.png --slot-bbox X,Y,W,H
python3 -m shared._tone_score handouts/{specialty}/{slug}/index.html     # ToneScore ≥ 80
```
