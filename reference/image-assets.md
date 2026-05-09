# AI Image Assets

핸드아웃과 검사 결과지의 그림은 원장님이 ChatGPT 웹에서 생성해 고른 PNG/WebP를 제공하고, 에이전트가 파일 배치·HTML 삽입·레이아웃 검증을 맡는 흐름을 기본으로 한다. 필요할 때만 OpenAI Image API로 로컬에서 직접 생성한다.

PDF 빌드 시에는 일반 이미지 파일처럼 렌더링되므로 Playwright 빌드와 GitHub Pages 배포 흐름을 바꾸지 않는다.

## 원칙

1. 의료 설명의 정확한 문구, 수치, 라벨은 HTML 텍스트로 둔다.
2. 이미지 프롬프트에는 환자명, 차트번호, 생년월일, 원본 검사 PDF 등 PII를 넣지 않는다.
3. 이미지 안에는 한글·영문 텍스트를 넣지 않는다. 필요한 라벨은 `.ai-visual__pin` 또는 HTML 주변 텍스트로 얹는다.
4. 이미지 파일은 `shared/assets/generated/`에 저장한다.
5. API로 생성한 경우에는 같은 이름의 `.prompt.json`도 함께 커밋해 재생성 가능하게 둔다. ChatGPT 웹에서 만든 파일은 원본 프롬프트가 있으면 `.prompt.md`로 남긴다.

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
