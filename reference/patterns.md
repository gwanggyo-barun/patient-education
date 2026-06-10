# 본문 패턴 7종 가이드

> 모든 슬라이드는 동일한 4-region master grid (header / title-block / body / footer)를 따른다.
> 본문 영역(`.slide__body`)에만 패턴을 적용한다. 패턴은 슬라이드당 하나만 사용한다.

> **범위 메모.** "7종"은 본문 코어 패턴(§1–§7: Hero Number, Asymmetric Split, Density Grid, Density Grid 2×2, Comparison, Timeline, Checklist)을 가리킨다. 여기에 본문 변형인 §8 Regimen Tile, 마무리 전용 §9 Closing Slide를 더해 이 문서는 총 9개 블록을 정의한다. SKILL.md §"본문 패턴 7종"의 번호 매김(8 Regimen Tile 포함)과 본 문서가 일치한다.
>
> **모든 클래스는 `shared/clinic-slides.css`(정본 CSS)에 정의되어 있다.** 각 패턴마다 "핵심 클래스" 줄에 컨테이너·자식 클래스를 명시했다. 새 레이아웃이 필요하면 임의 클래스를 만들지 말고 먼저 정본 CSS에 추가한 뒤 이 문서를 갱신한다(§"새 패턴 추가 시"). 단, `decks/general/papers-*`(논문 리뷰 덱)은 환자 교육 덱과 별도 장르로, 자체 인라인 컴포넌트(`stat-card`·`review-card`·`tbl-row` 등)를 쓰며 본문 7종 패턴을 적용하지 않는다.

## 1. Hero Number

**적합한 콘텐츠**: 단일 핵심 숫자가 메시지를 압도하는 슬라이드 — 유병률, 위험 감소율, 5년 생존율, 성공률 등.

**핵심 클래스**: `pattern-hero-number`(컨테이너, grid 5fr:4fr) → `pattern-hero-number__numeric`(좌측) {`__value` `<em>`로 부분 강조, `__caption`} + `pattern-hero-number__detail`(우측, steel 좌측 보더) {`__detail-label` `__detail-text`}.

**레이아웃**: 좌 5 : 우 4 비대칭. 좌측에 거대한 숫자 + 캡션, 우측에 "Why it matters" 보충 설명.

```html
<div class="pattern-hero-number">
  <div class="pattern-hero-number__numeric">
    <div class="pattern-hero-number__value"><em>30</em>%</div>
    <div class="pattern-hero-number__caption">한국 성인 H. pylori 감염률 — 1998년 약 67%에서 지속 감소했지만 여전히 높은 수준입니다.</div>
  </div>
  <div class="pattern-hero-number__detail">
    <div class="pattern-hero-number__detail-label">Why eradication matters</div>
    <div class="pattern-hero-number__detail-text">
      H. pylori 감염은 위암 위험을 약 6배 높이며, WHO Group 1 발암물질로 분류됩니다.
    </div>
  </div>
</div>
```

**가이드**:
- 숫자 안에 `<em>` 태그를 부분 적용해 일부만 Steel Blue로 강조 가능
- 캡션은 1-2문장 이내
- 우측 detail은 3-4문장 이내, label은 영문 uppercase

## 2. Asymmetric Split

**적합한 콘텐츠**: 정의 + 보조 메트릭, 핵심 개념 + 통계, 주요 메시지 + 근거 데이터.

**핵심 클래스**: `pattern-split`(컨테이너, grid 11fr:9fr) → `pattern-split__primary` {`__statement` `<em>` 강조, `__supporting`} + `pattern-split__detail` {`pattern-split__metric` × 2 {`__metric-label` `__metric-value` `__metric-detail`}}. 우측에 일러스트를 넣을 때는 `pattern-split--with-visual` 변형(컬럼 비율·메트릭 패딩 축소) 사용.

**레이아웃**: 좌 11 : 우 9. 좌측에 큰 statement + 보조 본문, 우측에 metric card 2개.

```html
<div class="pattern-split">
  <div class="pattern-split__primary">
    <p class="pattern-split__statement">하부식도괄약근 기능 저하와 <em>복압 증가</em>가 만나는 지점에서 GERD는 시작됩니다.</p>
    <p class="pattern-split__supporting">
      정상적으로 닫혀있어야 할 식도-위 경계가 약해지면, 산성 위 내용물이 식도로 역류해 점막을 자극합니다.
    </p>
  </div>
  <div class="pattern-split__detail">
    <div class="pattern-split__metric">
      <div class="pattern-split__metric-label">Diagnostic threshold</div>
      <div class="pattern-split__metric-value">주 2회 이상</div>
      <div class="pattern-split__metric-detail">전형적 증상 빈도가 이 수준을 넘으면 임상 진단을 고려합니다.</div>
    </div>
    <div class="pattern-split__metric">
      <div class="pattern-split__metric-label">Long-term risk</div>
      <div class="pattern-split__metric-value">식도협착 · 바렛식도</div>
      <div class="pattern-split__metric-detail">방치 시 점막 변화와 협착 위험이 누적됩니다.</div>
    </div>
  </div>
</div>
```

**가이드**:
- statement는 1-2문장, em으로 핵심 단어를 Steel Blue 강조
- supporting은 3-4문장 이내
- metric card는 정확히 2개 권장 (3개도 가능하지만 빡빡)

## 3. Density Grid 3×2

**적합한 콘텐츠**: 6개 동등 위계 항목 — 증상, 위험 요인, 진단 방법, 적응증, 생활습관, Red Flags 등.

**핵심 클래스**: `pattern-grid pattern-grid--3`(3열 × 2행 = 6칸) + `tile`(반복) {`tile__index` `tile__title` `tile__body`}.

```html
<div class="pattern-grid pattern-grid--3">
  <div class="tile">
    <div class="tile__index">FACTOR · 01</div>
    <div class="tile__title">체중 · 복압</div>
    <div class="tile__body">비만, 복부 비만, 임신 — 복압이 올라가 위 내용물이 위로 밀려 올라옵니다.</div>
  </div>
  <!-- 5개 더 반복 (2행 × 3열) -->
</div>
```

**Tile 변형**:
- `tile` (기본) — 흰 배경, steel 좌측 보더
- `tile--accent` — 따뜻한 회색 배경, 강조 카드 (예: PREFERRED 옵션)
- `tile--alert` — 빨간 배경/보더 (Red Flag, 응급 상황)

**Mixed grid**: 한 grid 안에 일반 tile + alert tile 혼용 가능. 슬라이드 10(부작용)에서 일반 5개 + Red Flag 1개 같은 방식.

**grid 종류 (정본 CSS에 정의된 modifier)**:
- `pattern-grid--3` — 3열 × 2행 = **6칸** (이 패턴의 기본)
- `pattern-grid--2` — 2열 × 2행 = **4칸** (→ §4 Density Grid 2×2)
- `pattern-grid--2x4` — 4열 × 2행 = **8칸**. 항목이 8개로 동등할 때만 사용(예: 약물 분류 8종, 검사 항목 8가지). 6개 기본을 넘는 고밀도이므로 카드 본문을 1–2문장으로 더 압축하고 `_validate_layout`로 overflow 확인 필수.
- modifier 없이 `pattern-grid`만 쓰고 인라인 `grid-template-columns`로 열 수를 직접 지정하는 방식도 가능(§8 Regimen Tile이 그 예: 3열 1행).

**가이드**:
- 정확히 6개 항목 권장 (4개는 `--2`, 8개는 `--2x4`로 grid 종류 변경)
- 각 카드 본문 2-3문장 이내
- 인덱스 라벨은 `CATEGORY · NN` 형식 (영문 uppercase)

## 4. Density Grid 2×2

**적합한 콘텐츠**: 4개 핵심 규칙 또는 큰 위계 항목 — 복용 주의사항, 핵심 원칙, 검사 방법 4가지 등.
경고 메시지가 동반될 때 alert strip을 본문 하단에 추가 가능.

**핵심 클래스**: `pattern-grid pattern-grid--2`(2열 × 2행 = 4칸) + `tile` × 4. 하단 경고 추가 시 인라인 `grid-template-rows: 1fr 1fr auto;` + `alert-strip` {`alert-strip__label` `alert-strip__text`}.

```html
<div class="pattern-grid pattern-grid--2" style="grid-template-rows: 1fr 1fr auto;">
  <div class="tile">
    <div class="tile__index">RULE · 01</div>
    <div class="tile__title">정해진 시간에 복용</div>
    <div class="tile__body">PPI는 식사 30분 전, 항생제는 식사 직후 또는 함께.</div>
  </div>
  <!-- 3개 더 -->

  <div class="alert-strip">
    <span class="alert-strip__label">중요</span>
    <span class="alert-strip__text">심한 설사·발진·호흡곤란이 발생하면 즉시 약을 중단하고 내원하세요.</span>
  </div>
</div>
```

**가이드**:
- alert-strip을 추가할 때만 grid-template-rows에 `auto` 추가
- alert는 슬라이드당 1개

## 5. Comparison

**적합한 콘텐츠**: DO vs DON'T, 권장 vs 피하기, 옵션 A vs B.

**핵심 클래스**: `pattern-compare`(컨테이너, grid 1fr:1fr) → `compare-col compare-col--avoid`(좌, Navy 헤더) / `compare-col compare-col--prefer`(우, Steel 헤더). 각 컬럼: `compare-col__header` {`compare-col__marker`} + `compare-col__list`(li 항목, `::before` 마커는 avoid=`—` / prefer=`+` 자동).

**컬러 규칙 (디자인 시스템 §4.9)**: 좌측은 Navy, 우측은 Steel Blue. 환자 직관용 초록/빨강 사용 안 함.

```html
<div class="pattern-compare">
  <div class="compare-col compare-col--avoid">
    <div class="compare-col__header">
      <span class="compare-col__marker">−</span>
      피하기
    </div>
    <ul class="compare-col__list">
      <li>기름진 음식, 튀김류</li>
      <li>매운 음식, 강한 향신료</li>
      <!-- ... -->
    </ul>
  </div>
  <div class="compare-col compare-col--prefer">
    <div class="compare-col__header">
      <span class="compare-col__marker">+</span>
      권장
    </div>
    <ul class="compare-col__list">
      <li>천천히, 잘 씹어 먹기</li>
      <!-- ... -->
    </ul>
  </div>
</div>
```

**가이드**:
- 각 컬럼 5-7개 항목 권장
- 항목은 짧은 명사구 또는 짧은 문장 (한 줄에 들어갈 수준)
- 양쪽 컬럼 항목 수가 비슷해야 시각 균형

## 6. Timeline

**적합한 콘텐츠**: 진단 경로, 치료 일정, 시간 흐름, 단계별 프로세스 (정확히 4단계).

**핵심 클래스**: `pattern-timeline`(컨테이너, grid 4열) + `timeline-step` × 4 {`timeline-step__node`(번호 원형) `timeline-step__title` `timeline-step__body`}. 단계 사이 화살표(`→`)는 `.timeline-step:not(:last-child)::after`가 자동 렌더.

```html
<div class="pattern-timeline">
  <div class="timeline-step">
    <div class="timeline-step__node">1</div>
    <div class="timeline-step__title">치료 시작 · Day 1</div>
    <div class="timeline-step__body">처방받은 약물을 정해진 시간에 정확히 복용 시작.</div>
  </div>
  <!-- 3개 더 -->
</div>
```

**가이드**:
- 정확히 4단계 (3단계나 5단계는 패턴 변형 필요)
- 각 단계 제목은 짧게 (예: `치료 시작 · Day 1`)
- body는 1-2문장
- 노드 사이 화살표는 CSS가 자동으로 그림 (`::after`)

## 7. Checklist

**적합한 콘텐츠**: 환자 행동 항목 (보통 7가지), 핵심 요약, 일일 체크 리스트.

**핵심 클래스**: `pattern-checklist`(컨테이너, 2열 grid) + `check-item`(반복) {`check-item__num` `check-item__text`(`<strong>`으로 navy 강조)}.

```html
<div class="pattern-checklist">
  <div class="check-item">
    <div class="check-item__num">01</div>
    <div class="check-item__text">처방받은 약을 <strong>정해진 시간에 정확히</strong> 복용</div>
  </div>
  <!-- 6개 더 -->
  <div class="check-item" style="border-bottom: none;">
    <div class="check-item__num" style="color: var(--color-navy);">→</div>
    <div class="check-item__text" style="color: var(--color-slate);">매일 체크하면서 습관으로 만들어 보세요</div>
  </div>
</div>
```

**가이드**:
- 7가지 + 마지막 안내 1개 (총 8개) → 4행 × 2열 grid에 균형
- 항목 텍스트는 한 줄로 끝나야 좋음
- `<strong>` 태그로 핵심 단어를 navy 강조

## 8. Regimen Tile (약물 조합)

**적합한 콘텐츠**: 약물 처방 조합 — 1차 치료, 2차 치료, 표준 요법 등. tile 안에 약물명-용량-빈도 표시.

**핵심 클래스**: §3의 `pattern-grid` + `tile`을 재사용하되 `tile__regimen`(ul) {`tile__regimen-name` `tile__regimen-dose`} 리스트와 `tile__duration`(하단 steel 라인)을 추가. PREFERRED 옵션은 `tile--accent`. 가로 칸 수는 인라인 `grid-template-columns: repeat(3, 1fr)`로 지정(전용 modifier 없음).

```html
<div class="pattern-grid" style="grid-template-columns: repeat(3, 1fr); grid-template-rows: 1fr;">
  <div class="tile tile--accent">
    <div class="tile__index">OPTION · B · PREFERRED</div>
    <div class="tile__title">비스무트 사제요법</div>
    <ul class="tile__regimen">
      <li><span class="tile__regimen-name">PPI</span><span class="tile__regimen-dose">표준용량 · bid</span></li>
      <li><span class="tile__regimen-name">Bismuth</span><span class="tile__regimen-dose">300mg · qid</span></li>
      <li><span class="tile__regimen-name">Tetracycline</span><span class="tile__regimen-dose">500mg · qid</span></li>
      <li><span class="tile__regimen-name">Metronidazole</span><span class="tile__regimen-dose">500mg · tid</span></li>
    </ul>
    <div class="tile__duration">10 – 14 days</div>
  </div>
  <!-- 2-3개 더 -->
</div>
```

**가이드**:
- 가로 3개 권장 (그 이상은 약물 표가 좁아짐)
- 약물명은 영문, 용량은 숫자 + 단위 + 빈도(bid/tid/qid/qd)
- duration은 카드 하단에 steel 색상 라인 + 영문 표기
- PREFERRED 옵션은 `tile--accent` 적용



## 9. Closing Slide (마무리 슬라이드 + QR)

**적합한 콘텐츠**: 덱의 마지막 슬라이드. 클리닉 contact + QR 코드로 환자가 자료를 다시 볼 수 있게.

**핵심 클래스**: `slide--closing`(섹션 modifier) → 본문에 `closing-grid`(grid 2.4fr:1fr) → `contact-card`(closing-grid 안에서는 1열 세로 stack) {`contact-card__item` {`__label` `__value`}} + `qr-block` {`qr-block__code`(빈 div, 빌드가 SVG 주입) `qr-block__text` {`__label` `__heading` `__hint`}}.

**레이아웃**: 좌 2.4 : 우 1 비대칭. 좌측에 contact-card (Phone/Address/Specialty 세로 stack), 우측에 qr-block.

```html
<section class="slide slide--closing">
  <header class="slide__header">
    <img class="slide__logo" src="../../../../shared/assets/clinic_logo.png" alt="광교바른내과">
    <div class="slide__chapter">END OF DECK · <strong>THANK YOU</strong></div>
  </header>
  <div class="slide__title-block">
    <h2 class="slide__title">{메시지 1}<br><em>{메시지 2}</em></h2>
    <p class="slide__subtitle">{부제}</p>
  </div>
  <div class="slide__body">
    <div class="closing-grid">
      <div class="contact-card">
        <div class="contact-card__item">
          <div class="contact-card__label">Phone</div>
          <div class="contact-card__value">031-893-4560</div>
        </div>
        <div class="contact-card__item">
          <div class="contact-card__label">Address</div>
          <div class="contact-card__value">경기 용인 수지구<br>광교중앙로 298, 4층</div>
        </div>
        <div class="contact-card__item">
          <div class="contact-card__label">Specialty</div>
          <div class="contact-card__value">소화기내과 · 일반내과<br>5대암 검진</div>
        </div>
      </div>
      <div class="qr-block">
        <div class="qr-block__code"></div>
        <div class="qr-block__text">
          <div class="qr-block__label">SCAN TO REVISIT</div>
          <div class="qr-block__heading">집에서 다시 보기</div>
          <div class="qr-block__hint">QR을 스캔하면 핸드폰에서<br>같은 자료를 다시 볼 수 있어요</div>
        </div>
      </div>
    </div>
  </div>
  <footer class="slide__footer">
    <span class="slide__source">광교바른내과 · Gwanggyo Barun Internal Medicine</span>
    <span class="slide__page">N / N</span>
  </footer>
</section>
```

**가이드**:
- `.qr-block__code` 안은 빈 div로 둔다 — 빌드 스크립트가 Python qrcode로 SVG를 자동 생성해 인라인 삽입한다
- QR이 가리킬 URL은 HTML <head>의 `<meta property="og:url">`로 결정. build.py가 BASE_URL + slug_path로 자동 조립
- 클리닉 contact 정보(Phone/Address/Specialty)는 모든 덱에 동일. 변경 시 한 곳에서만 갱신
- `<em>` 태그로 타이틀의 핵심 단어 하나를 Steel Blue 강조

**OG 메타태그 표준 형식** (모든 덱 HTML <head>에 포함):

```html
<meta property="og:type" content="article">
<meta property="og:url" content="{BASE_URL}/{slug_path}">
<meta property="og:title" content="{주제} — 광교바른내과">
<meta property="og:description" content="{한 줄 부제}">
<meta property="og:image" content="{BASE_URL}/{slug_path}preview.png">
<meta property="og:site_name" content="광교바른내과">
<meta name="theme-color" content="#003366">
```

이 메타태그는 카톡 미리보기 카드에서 자동 사용된다. 환자에게 URL을 카톡으로 보내면 클리닉 로고와 제목이 카드 형태로 표시된다.

## 패턴 선택 가이드

콘텐츠 성격별 권장 패턴:

| 콘텐츠 | 권장 패턴 |
|--------|---------|
| 한국 유병률, 위암 위험 5배, 5년 생존율 90% | Hero Number |
| 질환 정의 + 진단 기준 메트릭 | Asymmetric Split |
| 증상 6가지, 진단 방법 6가지, 적응증 6가지 | Density Grid 3×2 |
| 핵심 규칙 4가지 + 응급 안내 | Density Grid 2×2 + alert |
| DO/DON'T, 권장/피하기, A 약물 vs B 약물 | Comparison |
| 진단 경로, 치료 일정, 시술 후 시간순 | Timeline |
| 환자 실천 7가지 | Checklist |
| 약물 조합 (1차/2차/3차 또는 옵션 A/B/C) | Regimen Tile |

## 새 패턴 추가 시

기존 7종으로 표현 안 되는 콘텐츠가 등장하면 새 패턴을 만든다. 절차:

1. 이 문서에 새 패턴 정의 추가 (HTML, 사용 가이드, 적합 콘텐츠)
2. `shared/clinic-slides.css`에 CSS 추가 (`.pattern-{name}` 클래스)
3. `brand-design-system.md`의 §7 패턴 표 갱신
4. SKILL.md의 패턴 매핑 표 갱신
