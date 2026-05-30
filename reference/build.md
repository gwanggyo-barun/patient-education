# 빌드 가이드

## 환경 셋업

### 1. Python 환경

```bash
pip install playwright qrcode --break-system-packages
playwright install chromium
```

`qrcode`는 closing slide의 QR 코드 생성에 사용된다. 빌드 타임에 SVG로 만들어 HTML에 인라인 삽입하기 때문에 클라이언트 JS 의존성 없이 PDF에 안정적으로 들어간다.

### AI 이미지 자산

핸드아웃/검사 결과지에 그림을 넣을 때는 먼저 HTML/CSS 안에 실제 슬롯을 만든 뒤, 그 슬롯 치수에 맞춘 PNG/WebP/JPEG 또는 코드 네이티브 SVG를 `shared/assets/generated/`에 저장하고 HTML에서 참조한다. 제목 뒤 장식 이미지나 투명 배경 배너는 금지한다.

사진·질감·복잡한 해부 일러스트처럼 raster 생성이 필요할 때는 별도 Python SDK 없이 표준 라이브러리로 OpenAI Image API를 호출할 수 있다. 단순 절차/장비/행동 도식은 코드 네이티브 SVG로 생성할 수 있으며, 이 경우에도 같은 이름의 `.prompt.md`에 slot size/ratio, source text summary, visual intent, unique subject 를 남긴다.

```bash
export OPENAI_API_KEY="..."

python3 tools/generate_image_asset.py \
  --prompt "A clean patient-friendly medical illustration with empty space for HTML labels." \
  --output shared/assets/generated/example-handout-hero.png \
  --size 1536x1024 \
  --quality medium
```

세부 프롬프트/spec/HTML 삽입 패턴은 `reference/image-assets.md`를 따른다.

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

## 빌드 스크립트 (현재 schema)

`build.py`는 세 가지 콘텐츠 타입(decks/handouts/lab-reports)을 단일 TARGETS dict 리스트로 관리한다. **새 자료 추가는 이 리스트에 dict 한 항목을 append하는 것**.

```python
TARGETS = [
    # === 16:9 deck (12 slides) ===
    {
        "kind": "decks", "slug": "gerd",
        "slug_path": "decks/gi/gerd/lifestyle/",
        "html_path": ROOT / "decks/gi/gerd/lifestyle/index.html",
        "qr_class": "qr-block__code", "fmt": "deck-16x9",
        # Notion DB 동기용 (decks/handouts 필수)
        "title": "역류성 식도염 생활관리",
        "category": "🫁 위장관", "audience": "환자/보호자", "disease": "GERD",
        # 선택: 공유 페이지에서 숨기고 보관할 때
        "status": ARCHIVED_STATUS,
    },

    # === A4 handout (1 page) ===
    {
        "kind": "handouts", "slug": "egd-prep",
        "slug_path": "handouts/endoscopy/egd-prep/",
        "html_path": ROOT / "handouts/endoscopy/egd-prep/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        "title": "위내시경(EGD) 검사 준비 안내문",
        "category": "🏥 내시경 관련", "audience": "환자/보호자", "disease": "위내시경 준비",
    },

    # === A4 lab-report (1 page, 환자별) ===
    {
        "kind": "lab-reports", "slug": "<hash10>",        # lab_hash_slug() 결과
        "slug_path": "lab-reports/general-checkup/<hash10>/",
        "html_path": ROOT / "lab-reports/general-checkup/<hash10>/index.html",
        "qr_class": "qr-mini__code", "fmt": "a4-portrait",
        # 환자 메타 (lab-reports 필수, [차트번호] 환자명 자동 조합)
        "patient_name": "홍길동", "chart_no": "12345",
        "exam_date": "2026-05-13", "doctor": "정지환",
        "note": "종합검진 — 콜레스테롤 경계역",
    },
]
```

### Notion 공개/보관 제어

decks/handouts 항목은 기본적으로 Notion에 `✅ 사용중`으로 upsert된다. 자료를 지우지 않고 공유 페이지의 “사용중 자료만” 뷰에서 숨기려면 해당 항목에 `"status": ARCHIVED_STATUS`를 둔다. 행 자체를 휴지통에 보내고 다시 생성도 막아야 할 때는 모든 kind에서 `"notion_sync": False`를 사용한다. lab-reports DB에는 `상태` 속성이 없으므로 `status`를 쓰지 않는다.

이 설정은 Notion DB 표시만 제어한다. GitHub Pages 직접 URL 노출까지 중단하려면 source HTML이나 공개 인덱스 링크를 별도 정리해야 한다.

빌드 실행:
```bash
python3 build.py
```

빌드는 다음을 한 번에 수행:
1. **TARGETS 라우팅 검증** — `_validate_targets_routing()`이 `kind`와 `slug_path` 일치, Korean-slug(lab-reports) 차단
2. **CSS 경로 검증** — `_validate_css_paths()`가 3-level vs 4-level 깊이 mismatch 검출
3. **OG meta 검증** — `check_og_meta()`이 7종 메타태그 누락 검출
4. **lab-reports 개인정보 처리** — QR strip + noindex meta inject
5. **non-lab QR 주입** — `inject_qr()`이 빈 `<div class="qr-block__code">` 또는 `<div class="qr-mini__code">`에 SVG 삽입
6. **Playwright 레이아웃 validation** — 페이지 overflow / 푸터 침범 검출
7. **PDF + preview PNG 렌더** — `output/{kind}/{slug}.{pdf,png}`
8. **Notion DB upsert** (NOTION_TOKEN 있을 때만) — `kind`에 따라 3개 DB 중 하나로 라우팅

산출물:
- `output/{kind}/{slug}.pdf` — 환자 공유용
- `output/{kind}/{slug}-preview.png` — 데스크톱 풀스크린 미리보기

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

## 새 자료 만들기 단계 (deck/handout/lab-report 공통)

1. `{kind}/{specialty 또는 topic}/{slug}/index.html` 생성
   - decks: `decks/gi/gerd/lifestyle/index.html`을 템플릿으로 복사
   - handouts: 기존 핸드아웃 중 비슷한 카테고리 하나 복사
   - lab-reports: `lab-reports/{panel}/template/`을 복사, `lab_hash_slug()`로 slug 생성
2. content-template.md / patterns.md 참고해 본문 작성
3. `build.py`의 `TARGETS` 리스트에 dict 한 항목 append (위 스키마 참조)
4. `python3 -m shared._validate_layout <html_path>` 로 사전 검증
5. 이미지가 필요하면 `reference/image-assets.md`의 품질 우선 slot-first 순서를 따른다: 실제 slide/section 문구 기반 visual intent 작성 → 중복 subject/구도 없음 확인 → HTML/CSS 슬롯 확정 → 슬롯 치수 실측 → 그 비율로 이미지 생성 → `.prompt.md` 추적 → slot 비율 crop/resize → 다시 `_validate_layout`. 이미지 수량은 목표가 아니며, 무관하거나 가독성을 낮추는 이미지는 생략한다.
6. (선택) `python3 build.py` 로컬 빌드 — `output/{kind}/{slug}-preview.png` 시각 점검
7. `git add <명시 파일>` (절대 `.` 또는 `-A` 금지) → commit → push
8. CI(~80초)가 PDF 빌드 + GH Pages 배포 + Notion DB 자동 동기

사용자가 "검수 후 올려줘", "올려줘", "노션에 올려줘", "공유되게 해줘"라고 말하면 `push`까지 포함한다. `commit`에서 멈추면 GitHub Pages URL은 404가 날 수 있다. 사용자가 명시적으로 "푸시하지 마" 또는 "커밋만"이라고 한 경우에만 push를 생략한다.

## 검증 체크리스트

빌드 후 PDF를 열어서 확인:

- [ ] 12장 모두 헤더(로고 + chapter eyebrow) 위치 동일
- [ ] 12장 모두 타이틀 + 부제 위치 동일
- [ ] 12장 모두 푸터(출처 + 페이지 번호) 위치 동일
- [ ] 표지 외 슬라이드에 그라데이션 배경이 없음
- [ ] 색상이 디자인 토큰 외 추가되지 않음
- [ ] 이미지가 있으면 각 이미지의 subject 가 해당 슬라이드 본문과 직접 맞고, 같은 deck/series 안에서 파일/구도/subject 중복이 없음
- [ ] 이미지를 넣느라 본문 폰트·카드 간격·footer clearance 가 나빠지지 않음
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
