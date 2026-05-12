# AI Image Assets

decks 와 handouts 의 인포그래픽은 두 단계로 운영된다:

- **Phase 1 (자동 제안)**: 초안 HTML 이 빌드·검증 통과한 직후, Claude 가 슬라이드/섹션을 훑어 인포그래픽 후보를 식별하고 ChatGPT 웹용 영문 프롬프트를 사용자에게 자동으로 제시한다. 사용자는 받은 프롬프트로 이미지를 생성한 뒤 채팅창에 공유한다.
- **Phase 2 (배치 & 최종화)**: 사용자가 공유한 PNG/WebP/JPEG 를 `shared/assets/generated/` 에 저장하고, 적절한 `.ai-visual` 변형으로 HTML 에 삽입한 다음 재빌드·검증·푸시한다.

lab-reports 는 Phase 1·2 를 건너뛴다 (검사 결과지는 정확한 수치 시각화 중심).

PDF 빌드 시 이미지는 일반 파일로 렌더링되므로 Playwright 빌드와 GitHub Pages 배포 흐름을 바꾸지 않는다.

## 원칙

1. 의료 설명의 정확한 문구, 수치, 라벨은 HTML 텍스트로 둔다.
2. 이미지 프롬프트에는 환자명, 차트번호, 생년월일, 원본 검사 PDF 등 PII를 넣지 않는다.
3. 이미지 안에는 한글·영문 텍스트를 넣지 않는다. 필요한 라벨은 `.ai-visual__pin` 또는 HTML 주변 텍스트로 얹는다.
4. 이미지 파일은 `shared/assets/generated/`에 저장한다.
5. API로 생성한 경우에는 같은 이름의 `.prompt.json`도 함께 커밋해 재생성 가능하게 둔다. ChatGPT 웹에서 만든 파일은 원본 프롬프트가 있으면 `.prompt.md`로 남긴다.

## Phase 1 — 인포그래픽 자동 제안 (decks / handouts)

### 언제 트리거되는가

`build.py` 와 `python3 -m shared._validate_layout` 가 둘 다 통과한 직후. 텍스트와 레이아웃이 일단 확정된 지점에서만 제안한다 — 그 전에 제안하면 슬롯 위치가 바뀔 수 있어 무의미.

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

**수량 가이드**: 12장 deck → 2–4개 / 1장 handout → 1–2개. 12장 deck 도 4개 초과 권장 X.

### 영문 프롬프트 기본 골격

ChatGPT 웹 / DALL-E 는 한국어 의료 프롬프트를 잘 못 따른다. 항상 다음 골격을 영문으로 채워 출력한다:

```text
Create a clean, patient-friendly medical illustration for a Korean clinic {kind}.
Subject: {one-line subject description in English}.
Style: premium hospital patient education infographic, warm white background,
restrained navy (#003366) and steel-blue (#5B9BD5) accents, soft shadows,
{view_angle}.
Composition: subject {position}, with generous whitespace {whitespace_zone} for HTML label pins.
Do not include any text, letters, numbers, logos, watermarks, or patient information.
Aspect ratio: {ratio}.
```

토큰 치환 표:

| 토큰 | 값 |
|---|---|
| `{kind}` | decks → `deck slide` · handouts → `A4 portrait handout` |
| `{ratio}` | deck Hero/Asymmetric 우측 → `4:3` · deck Density 슬롯 → `3:2` · handout hero (가로) → `16:9` · handout 보조 (사각) → `1:1` · handout 세로 인물/장비 → `3:4` |
| `{view_angle}` | Anatomy/Equipment → `isometric 3/4 view` · Action/자세 → `front view` · 식판/식단 → `overhead top-down view` · Timeline/Process → `side view, left-to-right reading order` · Mechanism → `cutaway cross-section view` |
| `{position}` | Asymmetric Split 우측 → `centered` · Hero (전면) → `slightly off-center` · Density 슬롯 → `centered` · A4 hero → `centered horizontally near the top` |
| `{whitespace_zone}` | Asymmetric → `on left and right` · Hero → `above and below` · Density → `on all sides` · A4 hero → `at top and bottom for caption and pins` |

### 카테고리별 채워진 프롬프트 템플릿

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
각 프롬프트로 ChatGPT 웹에서 이미지를 생성하신 뒤 채팅창에 공유해 주십시오.
받는 즉시 알맞은 슬롯에 배치하고 재빌드·푸시합니다.

────────────────────────
### 1. {위치 — 예: 슬라이드 3 / Definition} — {주제 한국어}
**왜**: {한 줄 — 텍스트로 설명하기 어려운 이유}
**카테고리**: {Anatomy / Mechanism / Process / Equipment / Action / Comparison}
**슬롯**: `.ai-visual--{hero|portrait|compact|contain}` ({ratio})
**저장 파일명**: `shared/assets/generated/{topic-slug}-{slot-key}.png`

ChatGPT 웹에 복붙:
​```text
{영문 프롬프트}
​```
────────────────────────
### 2. ...
```

각 항목 5요소 (위치 / 왜 / 카테고리 / 슬롯+ratio / 파일명) + 복붙용 영문 프롬프트를 항상 포함한다.

---

## Phase 2 — 이미지 수령 후 배치 & 최종화

사용자가 이미지를 채팅창에 공유하면 다음을 자동 수행:

1. 받은 PNG/WebP/JPEG 를 **제안 시 알려준 파일명 그대로** `shared/assets/generated/{topic-slug}-{slot-key}.{ext}` 에 저장. 이름 임의 변경 금지.
2. ChatGPT 원본 프롬프트가 보존되어 있으면 같은 이름의 `.prompt.md` 도 함께 저장 (재생성 추적).
3. 해당 슬라이드/섹션 HTML 의 placeholder 위치(또는 텍스트 카드 자리)에 `.ai-visual` 컴포넌트 삽입 — 변형(`--hero` / `--portrait` / `--compact` / `--contain`)은 Phase 1 에서 정한 슬롯 그대로.
4. 이미지 안에 텍스트가 끼어 들어왔으면 다시 생성 요청 (라벨은 모두 HTML).
5. `python3 -m shared._validate_layout <html_path>` 재실행 → `OK` 확인.
6. `python3 build.py` 재실행 → `output/{kind}/{slug}-preview.png` 로 시각 점검 (이미지가 슬롯을 잘 채우는지, 화이트 백그라운드가 페이지 배경과 자연스럽게 이어지는지).
7. git status audit → 명시적 add → 단독 commit → push → Notion DB upsert 자동.

---

## 기본 워크플로우: ChatGPT 웹 이미지 제공

1. ChatGPT 웹에서 이미지를 생성한다.
2. 가장 좋은 컷을 PNG/WebP로 저장한다.
3. 에이전트에게 이미지 파일 경로 또는 업로드 이미지를 전달하며 삽입할 HTML을 지정한다.
4. 에이전트는 이미지를 `shared/assets/generated/`에 복사하고, `.ai-visual` 컴포넌트로 효율적으로 배치한다.
5. 에이전트는 `python3 -m shared._validate_layout <html_path>`와 `python3 build.py` 또는 대상별 시각 확인을 수행한다.

ChatGPT 웹 프롬프트 예시:

```text
Create a clean, patient-friendly medical illustration for an A4 Korean clinic handout.
Subject: colonoscopy preparation, clear liquids, medication packet, calendar, and bathroom route.
Style: premium hospital patient education infographic, accurate but non-scary, warm white background, restrained navy/steel-blue/green accents.
Composition: leave clear empty areas for HTML labels and captions.
Do not include any text, letters, numbers, logos, watermarks, patient names, chart numbers, or personal information.
```

## 선택 워크플로우: API로 생성

로컬 파이프라인 안에서 자동 생성해야 할 때만 사용한다. ChatGPT 구독 한도와 API 과금/한도는 별도다.

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
OPENAI_IMAGE_MODEL=gpt-image-1 python tools/generate_image_asset.py ...
python tools/generate_image_asset.py --model gpt-image-1-mini ...
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
- `.ai-visual__caption` — 이미지 위 캡션
- `.ai-visual__pin` — HTML 라벨 칩

## 검증

```bash
python3 -m shared._validate_layout handouts/endoscopy/colonoscopy-prep/index.html
python3 build.py
```

`build.py`는 HTML 안의 `../../../shared/assets/generated/...` 경로가 실제 파일로 존재하는지 사전 검증한다.
이미지가 깨지면 PDF 생성 전에 CSS/asset path error로 실패해야 정상이다.
