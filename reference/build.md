# 빌드 가이드

## 환경 셋업

### 1. Python 환경

```bash
pip install playwright qrcode --break-system-packages
playwright install chromium
```

`qrcode`는 closing slide의 QR 코드 생성에 사용된다. 빌드 타임에 SVG로 만들어 HTML에 인라인 삽입하기 때문에 클라이언트 JS 의존성 없이 PDF에 안정적으로 들어간다.

### AI 이미지 자산

핸드아웃/검사 결과지에 AI 생성 그림을 넣을 때는 ChatGPT 웹에서 생성해 고른 PNG/WebP를 `shared/assets/generated/`에 저장하고 HTML에서 참조하는 흐름을 기본으로 한다.

자동 생성이 필요할 때는 별도 Python SDK 없이 표준 라이브러리로 OpenAI Image API를 호출할 수 있다.

```bash
export OPENAI_API_KEY="..."

python3 tools/generate_image_asset.py \
  --prompt "A clean patient-friendly medical illustration with empty space for HTML labels." \
  --output shared/assets/generated/example-handout-hero.png \
  --size 1536x1024 \
  --quality medium
```

세부 프롬프트/HTML 삽입 패턴은 `reference/image-assets.md`를 따른다.

### 호스팅 베이스 URL 설정

`build.py` 상단의 `BASE_URL` 상수를 GitHub Pages 또는 자체 호스팅 URL로 설정한다. 이 값은 모든 덱의 QR 코드와 OG 메타태그(`og:url`, `og:image`)에 사용된다.

```python
# build.py
BASE_URL = "https://gwanggyo-barun.github.io/patient-education"
```

호스팅 URL이 변경되면 이 한 줄만 수정하고 재빌드하면 모든 덱의 QR이 자동 갱신된다.

### 2. 디렉토리 구조

```
clinic-content-system/
├── SKILL.md
├── shared/
│   ├── design-tokens.css      # 색상/폰트/간격 변수 (단일 진실의 원천)
│   ├── clinic-slides.css      # 슬라이드 마스터 + 7개 패턴 컴포넌트
│   └── assets/
│       └── clinic_logo.png    # 광교바른내과 로고 (1531×460)
├── decks/
│   ├── gi/
│   │   ├── gerd/lifestyle/index.html
│   │   └── h-pylori/eradication/index.html
│   ├── cardio/
│   │   └── htn/lifestyle/index.html
│   └── ...
├── reference/
│   ├── brand-design-system.md
│   ├── patterns.md
│   ├── content-template.md
│   ├── build.md (이 파일)
│   └── migration.md
└── build.py                   # 빌드 스크립트
```

각 덱 HTML은 4단계 위 상대 경로로 shared 자산을 참조한다:
```html
<link rel="stylesheet" href="../../../../shared/design-tokens.css">
<link rel="stylesheet" href="../../../../shared/clinic-slides.css">
<img src="../../../../shared/assets/clinic_logo.png">
```

## 빌드 스크립트

`build.py`를 프로젝트 루트에 둔다:

```python
from playwright.sync_api import sync_playwright
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)

# 빌드할 덱 목록 (slug, HTML 경로)
DECKS = [
    ("gerd",     ROOT / "decks/gi/gerd/lifestyle/index.html"),
    ("hpylori",  ROOT / "decks/gi/h-pylori/eradication/index.html"),
    # 새 덱 추가 시 이 리스트에 한 줄 추가
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for slug, deck_path in DECKS:
        url = f"file://{deck_path}"

        # 데스크톱 풀스크린 미리보기 (검증용)
        ctx = browser.new_context(viewport={"width": 1320, "height": 800})
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.screenshot(path=str(OUT / f"{slug}-preview.png"), full_page=True)
        ctx.close()

        # 환자 공유용 PDF (1280x720 native)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(2000)
        page.emulate_media(media="print")
        page.pdf(path=str(OUT / f"{slug}.pdf"),
                 width="1280px", height="720px", print_background=True,
                 margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        ctx.close()

        print(f"  built: {slug}")
    browser.close()
```

실행:
```bash
python build.py
```

## 호스팅 (GitHub Pages)

1. GitHub 저장소 생성: `gwanggyo-barun/patient-education`
2. 프로젝트 전체를 push
3. Settings → Pages → Source: `main` 브랜치, `/` (root) 선택
4. URL: `https://gwanggyo-barun.github.io/patient-education/decks/gi/gerd/lifestyle/`
5. 환자에게 카톡으로 이 URL 전송, 또는 PDF 파일 첨부

## Notion 임베드

Notion 페이지에 Embed 블록 추가, GitHub Pages URL 입력:
```
https://gwanggyo-barun.github.io/patient-education/decks/gi/gerd/lifestyle/
```

12장 슬라이드가 노션 페이지 안에서 세로 스크롤로 표시된다.

## 새 덱 만들기 단계

1. `decks/{specialty}/{topic}/{slug}/index.html` 생성
2. `decks/gi/gerd/lifestyle/index.html`을 템플릿으로 복사
3. content-template.md의 12장 구성을 따라 본문 작성
4. patterns.md의 패턴 HTML을 복붙해서 콘텐츠만 교체
5. `build.py`의 DECKS 리스트에 한 줄 추가
6. `python build.py` 실행
7. `output/{slug}.pdf`와 `output/{slug}-preview.png` 검증
8. git push → GitHub Pages 자동 갱신

## 검증 체크리스트

빌드 후 PDF를 열어서 확인:

- [ ] 12장 모두 헤더(로고 + chapter eyebrow) 위치 동일
- [ ] 12장 모두 타이틀 + 부제 위치 동일
- [ ] 12장 모두 푸터(출처 + 페이지 번호) 위치 동일
- [ ] 표지 외 슬라이드에 그라데이션 배경이 없음
- [ ] 색상이 디자인 토큰 외 추가되지 않음
- [ ] Pretendard 폰트가 정상 로드됨 (CDN 차단 시 fallback 확인)
- [ ] 의학 용어 영문 병기됨
- [ ] 출처 명시됨

## 트러블슈팅

### 폰트가 깨져 보임 / 산세리프로 fallback됨
- jsDelivr CDN 접속 확인. 네트워크 차단된 환경이면 셀프호스팅 필요.
- Pretendard Variable을 `shared/fonts/`에 다운로드하고 `@font-face`로 로드.

### PDF에서 이미지가 안 나옴
- 로고 PNG 경로가 `file://` 절대 경로인지 확인
- `print_background=True` 옵션 누락 여부 확인

### 슬라이드가 한 페이지에 안 들어가고 잘림
- 콘텐츠 양 과다. 카드 텍스트 1-2문장씩 줄이기
- 타이틀이 길면 `<br>`로 줄바꿈

### 한 슬라이드가 두 페이지로 분할됨
- 카드 6개 그리드의 카드 본문이 너무 김. 각 카드 2-3문장 이내로
- `@media print`의 `page-break-after: always` 적용 확인
