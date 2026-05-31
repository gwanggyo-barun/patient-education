"""Generate 2026-05-30 clinical paper review slide decks."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parent.resolve()
REL = "../../../../"
BASE_URL = "https://gwanggyo-barun.github.io/patient-education"


CSS = """
    .slide__bg-num { display: none !important; }
    .slide__subtitle { max-width: 1080px; }
    .stars { color: #f59e0b; letter-spacing: 0.12em; font-size: 1.15em; }
    .slide--cover .slide__subtitle { max-width: 1060px; }

    .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); height: 100%; }
    .stat-card { border-radius: var(--radius-lg); border: 1px solid var(--color-border); padding: var(--space-5); display: flex; flex-direction: column; justify-content: center; gap: var(--space-3); background: var(--color-canvas); min-height: 0; }
    .stat-card--navy { background: var(--color-navy); color: var(--color-canvas); border-color: var(--color-navy); }
    .stat-card--steel { background: #eef4fb; border-color: var(--color-steel); }
    .stat-card--good { background: #ecfdf5; border-color: #10b981; }
    .stat-card--warn { background: #fff7ed; border-color: #f59e0b; }
    .stat-card--danger { background: #fef2f2; border-color: #fca5a5; }
    .stat-card__label { font-size: 0.82rem; font-weight: var(--weight-bold); color: var(--color-steel); letter-spacing: 0.07em; text-transform: uppercase; }
    .stat-card--navy .stat-card__label { color: var(--color-sky); }
    .stat-card__value { font-size: 2.65rem; font-weight: var(--weight-black); color: var(--color-navy); line-height: 1; letter-spacing: var(--tracking-tight); }
    .stat-card--navy .stat-card__value { color: var(--color-canvas); }
    .stat-card--good .stat-card__value { color: #047857; }
    .stat-card--warn .stat-card__value { color: #b45309; }
    .stat-card--danger .stat-card__value { color: #b91c1c; }
    .stat-card__body { font-size: 1rem; line-height: 1.45; color: var(--color-ink); }
    .stat-card--navy .stat-card__body { color: rgba(255,255,255,0.9); }

    .note { margin-top: var(--space-4); padding: var(--space-4) var(--space-5); border-radius: var(--radius-lg); background: var(--color-canvas-warm); border-left: 5px solid var(--color-steel); font-size: 1rem; line-height: 1.5; color: var(--color-ink); }
    .note strong { color: var(--color-navy); }
    .note--good { background: #ecfdf5; border-left-color: #10b981; }
    .note--warn { background: #fff7ed; border-left-color: #f59e0b; }
    .note--danger { background: #fef2f2; border-left-color: #ef4444; }

    .split { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-6); height: 100%; }
    .split-col { min-height: 0; display: flex; flex-direction: column; }
    .split-col__title { font-size: 1.28rem; font-weight: var(--weight-bold); color: var(--color-navy); margin-bottom: var(--space-3); line-height: 1.2; }
    .line-list { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 0; }
    .line-list li { padding: 9px 0; border-bottom: 1px solid var(--color-border-soft); font-size: 0.98rem; line-height: 1.35; }
    .line-list li strong { color: var(--color-navy); }
    .line-list li:last-child { border-bottom: 0; }

    .card-grid { display: grid; gap: var(--space-3); height: 100%; }
    .card-grid--2 { grid-template-columns: repeat(2, 1fr); }
    .card-grid--3 { grid-template-columns: repeat(3, 1fr); }
    .card-grid--6 { grid-template-columns: repeat(3, 1fr); grid-template-rows: repeat(2, 1fr); }
    .review-card { border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-canvas); padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-2); min-height: 0; overflow: hidden; }
    .review-card--navy { background: var(--color-navy); border-color: var(--color-navy); color: var(--color-canvas); }
    .review-card--steel { background: #eef4fb; border-color: var(--color-steel); }
    .review-card--good { background: #ecfdf5; border-color: #10b981; }
    .review-card--warn { background: #fff7ed; border-color: #f59e0b; }
    .review-card--danger { background: #fef2f2; border-color: #fca5a5; }
    .review-card__kicker { font-size: 0.72rem; font-weight: var(--weight-bold); color: var(--color-steel); letter-spacing: 0.08em; text-transform: uppercase; }
    .review-card__title { font-size: 1.08rem; font-weight: var(--weight-bold); color: var(--color-navy); line-height: 1.22; }
    .review-card--navy .review-card__title { color: var(--color-canvas); }
    .review-card--good .review-card__title { color: #047857; }
    .review-card--warn .review-card__title { color: #b45309; }
    .review-card--danger .review-card__title { color: #b91c1c; }
    .review-card__body { font-size: 0.88rem; line-height: 1.42; color: var(--color-ink); }
    .review-card--navy .review-card__body { color: rgba(255,255,255,0.9); }
    .review-card__metric { margin-top: auto; font-size: 1.7rem; font-weight: var(--weight-black); color: var(--color-steel); line-height: 1; letter-spacing: var(--tracking-tight); }

    .table-wrap { display: flex; flex-direction: column; gap: 7px; height: 100%; justify-content: center; }
    .tbl-row { display: grid; gap: var(--space-3); align-items: center; padding: 9px var(--space-4); border-radius: var(--radius-lg); border: 1px solid var(--color-border); background: var(--color-canvas); }
    .tbl-row--4 { grid-template-columns: 1.1fr 1fr 1fr 1.35fr; }
    .tbl-row--5 { grid-template-columns: 1.05fr 0.9fr 0.9fr 0.9fr 1.25fr; }
    .tbl-row--head { background: var(--color-navy); border-color: var(--color-navy); color: var(--color-canvas); font-weight: var(--weight-bold); }
    .tbl-row--good { background: #ecfdf5; border-color: #10b981; }
    .tbl-row--warn { background: #fff7ed; border-color: #f59e0b; }
    .tbl-row--danger { background: #fef2f2; border-color: #fca5a5; }
    .tbl-cell { font-size: 0.88rem; line-height: 1.32; color: var(--color-ink); }
    .tbl-row--head .tbl-cell { color: var(--color-canvas); font-size: 0.82rem; }
    .tbl-cell strong { color: var(--color-navy); }
    .tbl-row--head .tbl-cell strong { color: var(--color-canvas); }

    .timeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-3); height: 100%; }
    .step { background: var(--color-canvas); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-2); }
    .step--good { background: #ecfdf5; border-color: #10b981; }
    .step--warn { background: #fff7ed; border-color: #f59e0b; }
    .step--danger { background: #fef2f2; border-color: #fca5a5; }
    .step__num { font-size: 1.6rem; font-weight: var(--weight-black); color: var(--color-steel); line-height: 1; }
    .step__title { font-size: 1.02rem; font-weight: var(--weight-bold); color: var(--color-navy); line-height: 1.25; }
    .step__body { font-size: 0.86rem; line-height: 1.42; color: var(--color-ink); }

    .bar-wrap { display: grid; grid-template-columns: 1.05fr 0.95fr; gap: var(--space-5); height: 100%; align-items: stretch; }
    .bars { background: var(--color-canvas); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-5); display: flex; flex-direction: column; justify-content: center; gap: var(--space-3); }
    .bar-row { display: grid; grid-template-columns: 150px 1fr 90px; gap: var(--space-3); align-items: center; }
    .bar-row__label { font-size: 0.9rem; font-weight: var(--weight-bold); color: var(--color-navy); line-height: 1.2; }
    .bar-track { height: 28px; background: #e5e7eb; border-radius: 14px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 14px; background: linear-gradient(90deg, var(--color-steel), var(--color-navy)); }
    .bar-fill--good { background: linear-gradient(90deg, #10b981, #047857); }
    .bar-fill--warn { background: linear-gradient(90deg, #fbbf24, #b45309); }
    .bar-fill--danger { background: linear-gradient(90deg, #fca5a5, #b91c1c); }
    .bar-row__value { font-size: 1rem; font-weight: var(--weight-black); color: var(--color-navy); text-align: right; }

    .flow { display: grid; grid-template-columns: repeat(5, 1fr); gap: var(--space-3); height: 100%; align-items: stretch; }
    .flow-card { background: var(--color-canvas); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-4); display: flex; flex-direction: column; gap: var(--space-2); justify-content: center; }
    .flow-card--good { background: #ecfdf5; border-color: #10b981; }
    .flow-card--warn { background: #fff7ed; border-color: #f59e0b; }
    .flow-card--danger { background: #fef2f2; border-color: #fca5a5; }
    .flow-card__label { font-size: 0.72rem; font-weight: var(--weight-bold); color: var(--color-steel); letter-spacing: 0.08em; text-transform: uppercase; }
    .flow-card__title { font-size: 1rem; font-weight: var(--weight-bold); color: var(--color-navy); line-height: 1.22; }
    .flow-card__body { font-size: 0.82rem; line-height: 1.36; color: var(--color-ink); }

    .takehome-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-3); height: 100%; }
    .takehome-card { background: var(--color-navy); color: var(--color-canvas); border-radius: var(--radius-lg); padding: var(--space-4); display: flex; gap: var(--space-3); align-items: flex-start; min-height: 0; }
    .takehome-card__num { color: var(--color-steel); font-size: 2rem; line-height: 1; font-weight: var(--weight-black); min-width: 42px; }
    .takehome-card__text { font-size: 0.95rem; line-height: 1.42; font-weight: var(--weight-540); }
    .takehome-card__text strong { color: var(--color-sky); }

    .slide--closing .slide__body { gap: var(--space-3); justify-content: space-between; }
    .closing-grid { display: grid; grid-template-columns: 2.15fr 1fr; gap: var(--space-3); align-items: stretch; }
    .closing-contact { background: var(--color-canvas-warm); border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-4); display: flex; flex-direction: column; justify-content: center; gap: 4px; }
    .closing-contact__label { font-size: 0.72rem; color: var(--color-steel); font-weight: var(--weight-bold); letter-spacing: 0.08em; text-transform: uppercase; }
    .closing-contact__title { font-size: 1.08rem; color: var(--color-navy); font-weight: var(--weight-bold); }
    .closing-contact__body { font-size: 0.82rem; line-height: 1.38; color: var(--color-ink-soft); }
    .qr-block { border: 1px solid var(--color-border); border-radius: var(--radius-lg); padding: var(--space-3); display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 6px; background: var(--color-canvas); }
    .qr-block__code { width: 86px; height: 86px; display: flex; align-items: center; justify-content: center; }
    .qr-block__code svg { width: 86px !important; height: 86px !important; }
    .qr-block__caption { font-size: 0.68rem; color: var(--color-slate); line-height: 1.2; text-align: center; }
"""


def star_text(n: int) -> str:
    return "★" * n


def head(deck: dict) -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=1280">
  <title>{deck["plain_title"]} — 광교바른내과</title>
  <meta property="og:type" content="article">
  <meta property="og:url" content="{BASE_URL}/decks/general/papers-20260530/{deck["slug"]}/">
  <meta property="og:title" content="{deck["plain_title"]} — 광교바른내과">
  <meta property="og:description" content="{deck["description"]}">
  <meta property="og:image" content="{BASE_URL}/decks/general/papers-20260530/{deck["slug"]}/preview.png">
  <meta property="og:site_name" content="광교바른내과">
  <meta name="theme-color" content="#003366">
  <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css" />
  <script src="https://cdn.jsdelivr.net/npm/qrcodejs/qrcode.min.js"></script>
  <link rel="stylesheet" href="{REL}shared/design-tokens.css">
  <link rel="stylesheet" href="{REL}shared/clinic-slides.css">
  <style>{CSS}
  </style>
</head>
<body>
<div class="deck">
"""


def end() -> str:
    return """
</div>
</body>
</html>
"""


def header(chapter: str) -> str:
    return f"""
    <header class="slide__header">
      <img class="slide__logo" src="{REL}shared/assets/clinic_logo.png" alt="광교바른내과">
      <div class="slide__chapter">{chapter}</div>
    </header>"""


def footer(source: str, idx: int, total: int) -> str:
    return f"""
    <footer class="slide__footer">
      <span class="slide__source">{source}</span>
      <span class="slide__page">{idx:02d} / {total:02d}</span>
    </footer>"""


def title_block(title: str, subtitle: str) -> str:
    return f"""
    <div class="slide__title-block">
      <h2 class="slide__title">{title}</h2>
      <p class="slide__subtitle">{subtitle}</p>
    </div>"""


def cover(deck: dict, total: int) -> str:
    return f"""
  <section class="slide slide--cover">
{header(f"<strong>PAPER REVIEW</strong> · {deck['chapter']}")}
    <div class="slide__title-block">
      <h1 class="slide__title">{deck["title"]}</h1>
      <p class="slide__subtitle">{deck["subtitle"]}</p>
    </div>
    <footer class="slide__footer">
      <span class="slide__source">{deck["source"]}</span>
      <span class="slide__page"><span class="stars">{star_text(deck["importance"])}</span></span>
    </footer>
  </section>
"""


def slide_shell(slide: dict, body: str, idx: int, total: int) -> str:
    return f"""
  <section class="slide">
{header(slide["chapter"])}
{title_block(slide["title"], slide["subtitle"])}
    <div class="slide__body">
{body}
    </div>
{footer(slide["source"], idx, total)}
  </section>
"""


def stats(slide: dict) -> str:
    cards = []
    for item in slide["stats"]:
        cards.append(f"""
        <div class="stat-card stat-card--{item.get("tone", "steel")}">
          <div class="stat-card__label">{item["label"]}</div>
          <div class="stat-card__value">{item["value"]}</div>
          <div class="stat-card__body">{item["body"]}</div>
        </div>""")
    note = f'<div class="note note--{slide.get("note_tone", "steel")}">{slide["note"]}</div>' if slide.get("note") else ""
    return f"""
      <div class="stat-grid">
{''.join(cards)}
      </div>
      {note}"""


def cards(slide: dict) -> str:
    count = len(slide["cards"])
    grid_class = "card-grid--6" if count >= 5 else ("card-grid--3" if count == 3 else "card-grid--2")
    rendered = []
    for i, item in enumerate(slide["cards"], start=1):
        metric = f'<div class="review-card__metric">{item["metric"]}</div>' if item.get("metric") else ""
        rendered.append(f"""
        <div class="review-card review-card--{item.get("tone", "steel")}">
          <div class="review-card__kicker">{item.get("kicker", f"{i:02d}")}</div>
          <div class="review-card__title">{item["title"]}</div>
          <div class="review-card__body">{item["body"]}</div>
          {metric}
        </div>""")
    note = f'<div class="note note--{slide.get("note_tone", "steel")}">{slide["note"]}</div>' if slide.get("note") else ""
    return f"""
      <div class="card-grid {grid_class}">
{''.join(rendered)}
      </div>
      {note}"""


def split(slide: dict) -> str:
    def col(data: dict) -> str:
        lis = "".join(f"<li>{item}</li>" for item in data["items"])
        return f"""
        <div class="split-col">
          <h3 class="split-col__title">{data["title"]}</h3>
          <ul class="line-list">{lis}</ul>
        </div>"""

    note = f'<div class="note note--{slide.get("note_tone", "steel")}">{slide["note"]}</div>' if slide.get("note") else ""
    return f"""
      <div class="split">
{col(slide["left"])}
{col(slide["right"])}
      </div>
      {note}"""


def table(slide: dict) -> str:
    cols = len(slide["columns"])
    row_class = "tbl-row--5" if cols == 5 else "tbl-row--4"
    head_cells = "".join(f'<div class="tbl-cell">{c}</div>' for c in slide["columns"])
    rows = [f'<div class="tbl-row {row_class} tbl-row--head">{head_cells}</div>']
    for row in slide["rows"]:
        cells = "".join(f'<div class="tbl-cell">{c}</div>' for c in row["cells"])
        rows.append(f'<div class="tbl-row {row_class} tbl-row--{row.get("tone", "plain")}">{cells}</div>')
    return f"""
      <div class="table-wrap">
{''.join(rows)}
      </div>"""


def timeline(slide: dict) -> str:
    rendered = []
    for i, item in enumerate(slide["steps"], start=1):
        rendered.append(f"""
        <div class="step step--{item.get("tone", "steel")}">
          <div class="step__num">{i:02d}</div>
          <div class="step__title">{item["title"]}</div>
          <div class="step__body">{item["body"]}</div>
        </div>""")
    note = f'<div class="note note--{slide.get("note_tone", "steel")}">{slide["note"]}</div>' if slide.get("note") else ""
    return f"""
      <div class="timeline">
{''.join(rendered)}
      </div>
      {note}"""


def bars(slide: dict) -> str:
    rendered = []
    for item in slide["bars"]:
        rendered.append(f"""
          <div class="bar-row">
            <div class="bar-row__label">{item["label"]}</div>
            <div class="bar-track"><div class="bar-fill bar-fill--{item.get("tone", "steel")}" style="width:{item["width"]}%"></div></div>
            <div class="bar-row__value">{item["value"]}</div>
          </div>""")
    side = cards({"cards": slide["side"]})
    return f"""
      <div class="bar-wrap">
        <div class="bars">
{''.join(rendered)}
        </div>
        <div>{side}</div>
      </div>"""


def flow(slide: dict) -> str:
    rendered = []
    for i, item in enumerate(slide["steps"], start=1):
        rendered.append(f"""
        <div class="flow-card flow-card--{item.get("tone", "steel")}">
          <div class="flow-card__label">{item.get("label", f"STEP {i:02d}")}</div>
          <div class="flow-card__title">{item["title"]}</div>
          <div class="flow-card__body">{item["body"]}</div>
        </div>""")
    note = f'<div class="note note--{slide.get("note_tone", "steel")}">{slide["note"]}</div>' if slide.get("note") else ""
    return f"""
      <div class="flow">
{''.join(rendered)}
      </div>
      {note}"""


def takehome(slide: dict) -> str:
    items = []
    for i, line in enumerate(slide["items"], start=1):
        items.append(f"""
        <div class="takehome-card">
          <div class="takehome-card__num">{i:02d}</div>
          <div class="takehome-card__text">{line}</div>
        </div>""")
    return f"""
      <div class="takehome-grid">
{''.join(items)}
      </div>"""


def closing(deck: dict, slide: dict, idx: int, total: int) -> str:
    return f"""
  <section class="slide slide--closing">
{header(slide["chapter"])}
{title_block(slide["title"], slide["subtitle"])}
    <div class="slide__body">
{takehome(slide)}
      <div class="closing-grid">
        <div class="closing-contact">
          <div class="closing-contact__label">CLINIC NOTE</div>
          <div class="closing-contact__title">광교바른내과 · 의료진 논문 리뷰</div>
          <div class="closing-contact__body">{slide["clinic_note"]}</div>
        </div>
        <div class="qr-block">
          <div class="qr-block__code"></div>
          <div class="qr-block__caption">온라인 슬라이드<br>QR 스캔</div>
        </div>
      </div>
    </div>
{footer(slide["source"], idx, total)}
  </section>
"""


RENDERERS = {
    "stats": stats,
    "cards": cards,
    "split": split,
    "table": table,
    "timeline": timeline,
    "bars": bars,
    "flow": flow,
}


DECKS = [
    {
        "slug": "acs-crc-screening-blood-test-2026",
        "plain_title": "ACS 2026 대장암 검진 가이드라인 — 혈액검사 신규 추가",
        "title": "ACS 2026 대장암 검진 업데이트,<br><em>혈액검사는 어디에 놓을 것인가</em>",
        "subtitle": "CA: A Cancer Journal for Clinicians 2026.05.27 — 혈액 기반 cfDNA 검사가 처음 포함. 단, 기존 선호 검사를 거부하거나 완료하지 않는 환자에게 쓰는 보조 선택지.",
        "description": "ACS 2026 대장암 검진 업데이트. Shield 등 혈액 기반 cfDNA 검사는 선호 검사 거부·미완료 환자의 보조 선택지이며, FIT·분변분자검사·내시경은 계속 핵심이다.",
        "chapter": "GASTROENTEROLOGY · CANCER SCREENING",
        "source": "ACS guideline update 2026-05-27 · CA Cancer J Clin · Shield/ECLIPSE NEJM 2024",
        "importance": 5,
        "slides": [
            {
                "type": "stats", "chapter": "CHAPTER 01 · <strong>TL;DR</strong>",
                "title": "한 문장으로: 혈액검사는 '거부군 구조용' 옵션",
                "subtitle": "검진 시작·종료 원칙은 그대로, 선택지는 넓어졌지만 우선순위는 바뀌지 않았다.",
                "source": "ACS press release 2026-05-27 · CA Cancer J Clin 2026",
                "stats": [
                    {"label": "START", "value": "45세", "body": "평균위험 성인은 45세부터 정기 검진 시작. 2018 권고 유지.", "tone": "navy"},
                    {"label": "CONTINUE", "value": "75세", "body": "기대여명 10년 이상이면 75세까지 지속. 76-85세는 개별화.", "tone": "steel"},
                    {"label": "BLOOD TEST", "value": "2차 선택", "body": "선호 검사 거부·미완료 환자에게만 권고. first-line 아님.", "tone": "warn"},
                ],
                "note": "<strong>진료실 메시지 — </strong>대장내시경이나 FIT를 계속 거부하는 환자에게 '검진 공백'을 줄이는 근거가 생겼다. 그러나 혈액검사는 진행성 선종·초기암 검출력이 낮아 예방 효과가 제한된다.",
                "note_tone": "warn",
            },
            {
                "type": "cards", "chapter": "CHAPTER 02 · <strong>WHAT CHANGED</strong>",
                "title": "2026 업데이트의 실제 변경점",
                "subtitle": "새 검사를 추가했지만, 검사 선택의 기본 구조는 유지된다.",
                "source": "ACS guideline update 2026-05-27",
                "cards": [
                    {"title": "혈액 기반 cfDNA", "body": "Shield 등 종양 DNA 기반 혈액검사가 가이드라인에 처음 포함. 진료실 채혈로 시행 가능.", "metric": "NEW", "tone": "warn"},
                    {"title": "mt-sRNA stool", "body": "ColoSense 계열 다표적 분변 RNA 검사 신규 포함. 3년 간격.", "metric": "3년", "tone": "steel"},
                    {"title": "ng-mt-sDNA", "body": "차세대 Cologuard 계열 다표적 분변 DNA 검사 업데이트. 3년 간격.", "metric": "3년", "tone": "good"},
                    {"title": "기존 FIT 유지", "body": "고감도 FIT는 매년 시행하는 핵심 비침습 검사로 계속 권고.", "metric": "매년", "tone": "navy"},
                    {"title": "내시경 유지", "body": "대장내시경은 10년 간격, CT colonography와 sigmoidoscopy는 5년 간격.", "metric": "10년", "tone": "steel"},
                    {"title": "양성 후 내시경", "body": "분변·혈액 검사 양성은 검진 완료가 아니다. 적시 대장내시경이 필수.", "metric": "≤6개월", "tone": "danger"},
                ],
            },
            {
                "type": "split", "chapter": "CHAPTER 03 · <strong>UNCHANGED</strong>",
                "title": "바뀌지 않은 핵심 권고",
                "subtitle": "새 검사가 들어왔지만, 검진의 목표는 '암 발견'이 아니라 '암 예방'까지 포함한다.",
                "source": "ACS recommendations for average-risk adults",
                "left": {"title": "대상과 연령", "items": [
                    "<strong>평균위험군</strong> — 증상 없음, CRC/선종 과거력 없음, IBD·유전증후군 없음",
                    "<strong>45세 시작</strong> — 젊은 대장암 증가 추세를 반영한 기존 권고 유지",
                    "<strong>75세까지</strong> — 건강하고 기대여명 10년 이상이면 계속",
                    "<strong>76-85세</strong> — 선호, 전신상태, 이전 검진력으로 개별 결정",
                    "<strong>85세 초과</strong> — 정기 검진 중단",
                ]},
                "right": {"title": "검사 우선순위", "items": [
                    "<strong>Visual exam</strong> — 대장내시경, CT colonography, sigmoidoscopy",
                    "<strong>Stool test</strong> — FIT/gFOBT 매년, mt-sDNA/mt-sRNA 3년",
                    "<strong>Blood test</strong> — 선호 검사 거부·미완료 시 차선책",
                    "<strong>Positive test</strong> — 반드시 진단 대장내시경으로 완결",
                    "<strong>High-risk</strong> — 평균위험 가이드와 별도 경로",
                ]},
                "note": "<strong>첫 상담 문장 — </strong>'가장 좋은 검사는 환자가 실제로 끝까지 완료하는 검사입니다. 다만 예방력은 검사마다 다릅니다.'",
                "note_tone": "good",
            },
            {
                "type": "stats", "chapter": "CHAPTER 04 · <strong>WHY IT MATTERS</strong>",
                "title": "왜 ACS가 선택지를 넓혔나",
                "subtitle": "대장암은 예방 가능한 암이지만, 검진 미완료자가 여전히 많다.",
                "source": "ACS press release 2026-05-27 · NCI Shield review 2024",
                "stats": [
                    {"label": "UNSCREENED", "value": "2,000만+", "body": "미국에서 권고대로 검진받지 않은 적격 성인 규모.", "tone": "danger"},
                    {"label": "SURVIVAL", "value": ">90%", "body": "조기 발견 시 미국 5년 생존율. 늦으면 급격히 악화.", "tone": "good"},
                    {"label": "BARRIER", "value": "준비·대변·진정", "body": "내시경 준비, 분변검체 거부, 시간·교통 장벽이 검진 공백을 만든다.", "tone": "steel"},
                ],
                "note": "<strong>혈액검사의 역할 — </strong>검사 성능이 최고라서가 아니라, '아무 검사도 안 하는 환자'를 검진 경로 안으로 끌어들이기 위한 선택지다.",
                "note_tone": "warn",
            },
            {
                "type": "cards", "chapter": "CHAPTER 06 · <strong>BLOOD TEST BIOLOGY</strong>",
                "title": "Shield 혈액검사는 무엇을 보나",
                "subtitle": "혈액 속 cell-free DNA에서 종양 관련 변화를 찾는 방식이다.",
                "source": "FDA Shield P230009 · NCI Cancer Currents 2024",
                "cards": [
                    {"title": "cfDNA", "body": "종양 또는 전암성 병변에서 유래할 수 있는 cell-free DNA를 혈장 내에서 분석.", "tone": "steel"},
                    {"title": "Mutation", "body": "암세포에서 생긴 somatic mutation 신호를 탐지.", "tone": "navy"},
                    {"title": "Methylation", "body": "염기서열을 바꾸지 않는 epigenomic alteration도 함께 평가.", "tone": "good"},
                    {"title": "Fragmentation", "body": "DNA 절편 패턴을 조합해 양성/음성 결과를 생성.", "tone": "steel"},
                    {"title": "No bowel prep", "body": "장정결, 식이 제한, 진정이 필요 없다는 접근성 장점.", "tone": "good"},
                    {"title": "No polyp removal", "body": "양성이라도 병변 위치를 모르며, 폴립 제거는 불가능.", "tone": "danger"},
                ],
            },
            {
                "type": "bars", "chapter": "CHAPTER 07 · <strong>PERFORMANCE</strong>",
                "title": "성능: 암은 잡지만, 전암 병변은 많이 놓친다",
                "subtitle": "ECLIPSE 연구의 핵심 수치를 환자 설명용으로 단순화한다.",
                "source": "ECLIPSE study · NEJM 2024;390:973-983 · NCI 2024",
                "bars": [
                    {"label": "대장암 민감도", "value": "83%", "width": 83, "tone": "good"},
                    {"label": "진행성 전암 병변", "value": "13%", "width": 13, "tone": "danger"},
                    {"label": "특이도", "value": "90%", "width": 90, "tone": "steel"},
                    {"label": "위양성", "value": "~10%", "width": 10, "tone": "warn"},
                ],
                "side": [
                    {"title": "강점", "body": "대장암 검출 민감도는 기존 일부 비침습 검사와 비교 가능한 수준.", "tone": "good"},
                    {"title": "약점", "body": "진행성 선종·전암 병변 민감도가 낮아 '예방 검사'로는 한계가 크다.", "tone": "danger"},
                ],
            },
            {
                "type": "split", "chapter": "CHAPTER 08 · <strong>WHY NOT FIRST-LINE</strong>",
                "title": "왜 first-line으로 권하지 않는가",
                "subtitle": "대장암 검진의 이상적 목표는 암이 되기 전에 선종을 제거하는 것이다.",
                "source": "ACS 2026 update · ECLIPSE NEJM 2024",
                "left": {"title": "대장내시경 / FIT의 장점", "items": [
                    "<strong>내시경</strong> — 병변 확인과 제거를 같은 날 수행",
                    "<strong>FIT</strong> — 반복 시행 시 사망률 감소 근거가 강함",
                    "<strong>분변 분자검사</strong> — 전암 병변 검출력이 혈액검사보다 우수",
                    "<strong>양성 위치 확인</strong> — 내시경으로 바로 진단·치료 연결",
                ]},
                "right": {"title": "혈액검사의 제한", "items": [
                    "<strong>전암 병변 민감도 13%</strong> — 예방 목적에는 취약",
                    "<strong>초기암 낮은 검출 우려</strong> — stage I 검출이 상대적으로 약함",
                    "<strong>양성 후 내시경 필요</strong> — 결국 장정결·내시경 장벽을 다시 만남",
                    "<strong>반복 간격·장기 효과</strong> — 사망률 감소 효과는 추적 근거 필요",
                ]},
                "note": "<strong>환자 설명 — </strong>'피검사가 편한 것은 맞지만, 대장내시경처럼 용종을 떼어 암을 예방하는 검사는 아닙니다.'",
                "note_tone": "danger",
            },
            {
                "type": "cards", "chapter": "CHAPTER 09 · <strong>WHO</strong>",
                "title": "혈액검사를 고려할 수 있는 환자",
                "subtitle": "평균위험군 중에서도 기존 선호 검사를 실제로 완료하지 못하는 사람이다.",
                "source": "ACS 2026 guideline update",
                "cards": [
                    {"title": "내시경 장정결 거부", "body": "반복 상담에도 장정결·진정·동행 문제로 내시경을 계속 미루는 평균위험군.", "tone": "warn"},
                    {"title": "분변검체 거부", "body": "FIT/분변분자검사를 설명해도 채취 자체를 거부하거나 매번 미제출.", "tone": "warn"},
                    {"title": "검진 공백 장기화", "body": "45세 이상인데 검진 이력이 없거나 10년 이상 공백.", "tone": "danger"},
                    {"title": "높은 접근성 필요", "body": "진료실 채혈이 현실적으로 유일하게 완료 가능한 선택지.", "tone": "steel"},
                    {"title": "평균위험군", "body": "증상·빈혈·혈변·체중감소·IBD·가족력 고위험이 없는 경우.", "tone": "good"},
                    {"title": "고위험군 제외", "body": "증상 있거나 고위험이면 선별검사가 아니라 진단 대장내시경 경로.", "tone": "navy"},
                ],
            },
            {
                "type": "flow", "chapter": "CHAPTER 10 · <strong>OFFICE FLOW</strong>",
                "title": "1차 진료 상담 흐름",
                "subtitle": "검사 선택은 환자 선호를 반영하되, 예방 효과 차이를 숨기지 않는다.",
                "source": "ACS 2026 update · clinic implementation draft",
                "steps": [
                    {"label": "SCREEN", "title": "위험도 확인", "body": "증상, 가족력, IBD, 과거 선종/암, 빈혈을 먼저 배제.", "tone": "navy"},
                    {"label": "OFFER", "title": "선호 검사 제안", "body": "내시경 또는 분변검사를 먼저 설명하고 선택하게 함.", "tone": "good"},
                    {"label": "BARRIER", "title": "미완료 이유 확인", "body": "장정결, 대변 채취, 비용, 시간, 두려움을 구체화.", "tone": "steel"},
                    {"label": "RESCUE", "title": "혈액검사 논의", "body": "기존 검사를 거부하거나 미완료할 때 차선책으로 제안.", "tone": "warn"},
                    {"label": "CLOSE", "title": "양성 후 내시경 동의", "body": "양성 시 6개월 이내 대장내시경 필요를 사전 동의.", "tone": "danger"},
                ],
            },
            {
                "type": "timeline", "chapter": "CHAPTER 11 · <strong>POSITIVE RESULT</strong>",
                "title": "양성 결과는 검진 완료가 아니다",
                "subtitle": "양성 후 대장내시경 누락은 선별검사의 가장 큰 실패 지점이다.",
                "source": "ACS 2026 update · NCI Shield review",
                "steps": [
                    {"title": "결과 설명", "body": "양성은 암 확진이 아니라 암/전암 병변 가능성. 불안을 낮추되 지연 금지.", "tone": "warn"},
                    {"title": "내시경 예약", "body": "가능하면 6개월 이내. 일정·장정결·항혈전제 조정까지 한 번에 계획.", "tone": "danger"},
                    {"title": "검사 완결", "body": "내시경에서 병변 확인, 조직검사 또는 용종절제 시행.", "tone": "good"},
                    {"title": "추적 간격", "body": "내시경 소견과 병리 결과에 따라 다음 검진 간격 재설정.", "tone": "steel"},
                ],
                "note": "<strong>기록 문구 — </strong>'혈액/분변 선별검사 양성 시 진단 대장내시경 필요성 및 미시행 위험 설명함.'",
                "note_tone": "warn",
            },
            {
                "type": "cards", "chapter": "CHAPTER 12 · <strong>NEGATIVE RESULT</strong>",
                "title": "음성 결과도 '끝'이 아니다",
                "subtitle": "혈액검사는 특히 전암 병변을 놓칠 수 있으므로 반복 검진 계획을 남겨야 한다.",
                "source": "FDA Shield P230009 · ACS 2026 update",
                "cards": [
                    {"title": "음성은 보장 아님", "body": "FDA도 음성 결과가 대장암 부재를 보장하지 않는다고 명시한다.", "tone": "warn"},
                    {"title": "증상 발생 시 진단 경로", "body": "혈변, 철결핍빈혈, 체중감소, 배변습관 변화는 음성과 무관하게 평가.", "tone": "danger"},
                    {"title": "반복 검진 계획", "body": "혈액검사 후 다음 검진 간격은 지침·보험·검사 라벨에 맞춰 추적.", "tone": "steel"},
                    {"title": "선호 검사 재상담", "body": "다음 방문에서 FIT 또는 내시경 전환을 계속 논의.", "tone": "good"},
                ],
                "note": "<strong>상담 문장 — </strong>'이번 피검사가 음성이어도 용종을 다 보는 검사가 아니므로, 정기 검진 계획을 계속 가져가야 합니다.'",
                "note_tone": "warn",
            },
            {
                "type": "table", "chapter": "CHAPTER 13 · <strong>COMPARISON</strong>",
                "title": "검사별 설명 포인트",
                "subtitle": "환자에게 한 표로 설명하면 선택과 사전 동의가 쉬워진다.",
                "source": "ACS 2026 update · NCI 2024 Shield review",
                "columns": ["검사", "간격", "장점", "주의점"],
                "rows": [
                    {"cells": ["<strong>대장내시경</strong>", "10년", "진단+용종제거, 예방 효과 최강", "장정결·진정·천공/출혈 위험"], "tone": "good"},
                    {"cells": ["<strong>FIT/gFOBT</strong>", "매년", "저렴, 집에서 시행, 반복 근거 강함", "매년 제출해야 함, 양성이면 내시경"], "tone": "steel"},
                    {"cells": ["<strong>mt-sDNA/RNA</strong>", "3년", "분자표지자 포함, 비침습", "비용·위양성·양성 후 내시경"], "tone": "steel"},
                    {"cells": ["<strong>CT colonography</strong>", "5년", "진정 없음, 구조 확인", "장정결 필요, 용종 제거 불가"], "tone": "warn"},
                    {"cells": ["<strong>혈액 cfDNA</strong>", "라벨/보험 확인", "채혈로 접근성 높음", "전암 병변 검출 낮음, first-line 아님"], "tone": "danger"},
                ],
            },
            {
                "type": "split", "chapter": "CHAPTER 14 · <strong>KOREA CLINIC</strong>",
                "title": "한국 1차 진료 적용",
                "subtitle": "국내 검진 체계와 보험 현실은 다르지만, 상담 원칙은 바로 쓸 수 있다.",
                "source": "ACS 2026 update · clinic implementation draft",
                "left": {"title": "바로 적용할 점", "items": [
                    "<strong>45세 이상 미검진자</strong>에게 검진 여부를 매년 확인",
                    "<strong>대장내시경·FIT</strong>를 먼저 제안하고 완료를 추적",
                    "<strong>거부 이유</strong>를 EMR에 남기고 장벽별 대안 제시",
                    "<strong>혈액검사</strong>는 국내 허가·보험·검사 가능 여부 확인 후 차선책으로 설명",
                ]},
                "right": {"title": "환자 설명 스크립트", "items": [
                    "<strong>최선</strong> — '용종 제거까지 가능한 대장내시경이 가장 예방력이 큽니다.'",
                    "<strong>대안</strong> — '내시경이 어렵다면 매년 FIT도 좋은 선택입니다.'",
                    "<strong>구조</strong> — '둘 다 어렵다면 피검사라도 검진 공백을 줄일 수 있습니다.'",
                    "<strong>한계</strong> — '다만 피검사는 작은 용종을 많이 놓칩니다.'",
                ]},
                "note": "<strong>주의 — </strong>혈액 기반 검사가 국내에서 동일하게 사용 가능한지, 비용·보험·검사명은 실제 도입 상황을 별도 확인해야 한다.",
                "note_tone": "warn",
            },
            {
                "type": "cards", "chapter": "CHAPTER 15 · <strong>PITFALLS</strong>",
                "title": "피해야 할 상담 실수",
                "subtitle": "편의성을 강조하다가 예방력과 후속 내시경 필요성을 흐리면 안 된다.",
                "source": "ACS 2026 update · ECLIPSE NEJM 2024",
                "cards": [
                    {"title": "피검사 = 내시경 대체", "body": "잘못. 대장내시경처럼 용종 제거를 통한 예방 기능이 없다.", "tone": "danger"},
                    {"title": "음성이면 안심", "body": "잘못. 전암 병변 민감도가 낮고 음성은 질병 부재 보장이 아니다.", "tone": "warn"},
                    {"title": "고위험군에도 선별", "body": "잘못. 증상·빈혈·고위험 병력은 진단 내시경 경로다.", "tone": "danger"},
                    {"title": "양성 후 지연", "body": "가장 위험. 양성 결과 설명과 동시에 내시경 예약 프로세스를 열어야 한다.", "tone": "warn"},
                    {"title": "비용 미설명", "body": "보험·본인부담·검사 가능성을 확인하지 않으면 완료율이 떨어진다.", "tone": "steel"},
                    {"title": "검진 간격 누락", "body": "검사 후 다음 계획을 EMR에 남기지 않으면 반복 검진이 끊긴다.", "tone": "steel"},
                ],
            },
            {
                "type": "closing", "chapter": "CHAPTER 16 · <strong>TAKE HOME</strong>",
                "title": "진료실 결론",
                "subtitle": "혈액검사는 대장암 검진을 대체하지 않고, 미검진자를 검진 경로로 끌어들이는 보조 도구다.",
                "source": "ACS 2026 update · Shield/ECLIPSE NEJM 2024 · FDA P230009",
                "clinic_note": "이 자료는 의료진 상담용 요약입니다. 국내 도입 검사명, 허가 범위, 보험 적용은 실제 처방·검사 의뢰 전 별도 확인이 필요합니다.",
                "items": [
                    "<strong>first-line은 유지</strong> — FIT·분변분자검사·대장내시경이 핵심이다.",
                    "<strong>혈액검사는 rescue option</strong> — 기존 선호 검사를 거부하거나 완료하지 않는 평균위험군에게 설명한다.",
                    "<strong>한계는 반드시 말하기</strong> — 대장암 민감도는 약 83%지만 진행성 전암 병변 민감도는 약 13%다.",
                    "<strong>양성 후 내시경</strong> — 분변·혈액 검사 양성은 대장내시경까지 해야 검진이 완결된다.",
                ],
            },
        ],
    },
    {
        "slug": "finerenone-t1d-ckd-fine-one",
        "plain_title": "Finerenone in Type 1 Diabetes and CKD — FINE-ONE",
        "title": "1형 당뇨 CKD에서 Finerenone,<br><em>알부민뇨를 낮춘 첫 3상 신호</em>",
        "subtitle": "NEJM 2026.03 — FINE-ONE phase 3. T1D + CKD + UACR 200-5000 mg/g에서 6개월 UACR 위약 대비 25% 추가 감소.",
        "description": "FINE-ONE phase 3: 1형 당뇨병 CKD 성인에서 finerenone이 UACR을 유의하게 낮췄고 고칼륨혈증 모니터링이 핵심이다.",
        "chapter": "ENDOCRINOLOGY · NEPHROLOGY",
        "source": "Heerspink HJL et al. NEJM 2026;394:947-957 · DOI 10.1056/NEJMoa2512854",
        "importance": 4,
        "slides": [
            {
                "type": "stats", "chapter": "CHAPTER 01 · <strong>TL;DR</strong>",
                "title": "한 문단·세 숫자로 요약",
                "subtitle": "T2D CKD 근거가 T1D 알부민뇨 환자로 확장되는 첫 phase 3 근거다.",
                "source": "NEJM 2026;394:947-957",
                "stats": [
                    {"label": "RANDOMIZED", "value": "242명", "body": "T1D + CKD + UACR 200-5000 mg/g, ACEi/ARB 복용 중.", "tone": "navy"},
                    {"label": "PRIMARY", "value": "25%", "body": "6개월 UACR 위약 대비 추가 감소. geometric mean ratio 0.75.", "tone": "good"},
                    {"label": "SAFETY", "value": "10.1%", "body": "고칼륨혈증: finerenone 10.1% vs placebo 3.3%.", "tone": "warn"},
                ],
                "note": "<strong>핵심 메시지 — </strong>UACR surrogate endpoint는 명확히 좋아졌다. 단, hard renal/CV outcome을 입증한 연구는 아니며 칼륨·eGFR 모니터링을 전제로 해석해야 한다.",
                "note_tone": "warn",
            },
            {
                "type": "split", "chapter": "CHAPTER 02 · <strong>UNMET NEED</strong>",
                "title": "왜 중요한가: T1D CKD의 옵션 부족",
                "subtitle": "제1형 당뇨병의 신장질환은 젊은 나이부터 장기 위험을 만든다.",
                "source": "NEJM editorial 2026 · FINE-ONE background",
                "left": {"title": "기존 표준", "items": [
                    "<strong>혈당 조절</strong> — A1c 목표 개별화, 저혈당 피하기",
                    "<strong>혈압 조절</strong> — RAAS blockade 중심",
                    "<strong>ACEi/ARB</strong> — 알부민뇨 동반 CKD의 기본축",
                    "<strong>SGLT2i</strong> — T1D에서는 DKA 위험과 허가 제한 때문에 일반 표준으로 보기 어렵다",
                ]},
                "right": {"title": "남는 문제", "items": [
                    "<strong>잔여 알부민뇨</strong> — ACEi/ARB에도 진행 위험 지속",
                    "<strong>심혈관 위험</strong> — CKD 자체가 독립 위험인자",
                    "<strong>근거 공백</strong> — T2D에서 입증된 약제가 T1D에는 거의 시험되지 않음",
                    "<strong>치료 피로</strong> — 장기 추적·검사 순응도가 관건",
                ]},
            },
            {
                "type": "cards", "chapter": "CHAPTER 03 · <strong>TRIAL DESIGN</strong>",
                "title": "FINE-ONE 설계",
                "subtitle": "hard outcome trial이 아니라, 6개월 UACR 변화를 1차 평가변수로 둔 registration trial이다.",
                "source": "NEJM 2026 FINE-ONE methods",
                "cards": [
                    {"title": "Population", "body": "성인 T1D + CKD. eGFR 25-&lt;90 mL/min/1.73m².", "tone": "steel"},
                    {"title": "Albuminuria", "body": "UACR 200-&lt;5000 mg/g. 이미 의미 있는 알부민뇨가 있는 군.", "tone": "warn"},
                    {"title": "Background therapy", "body": "ACE inhibitor 또는 ARB 복용 중인 환자.", "tone": "good"},
                    {"title": "Intervention", "body": "Finerenone 10 mg 또는 20 mg/day, eGFR 기반 시작.", "tone": "navy"},
                    {"title": "Comparator", "body": "Matching placebo, double-blind randomization.", "tone": "steel"},
                    {"title": "Primary outcome", "body": "6개월 동안 UACR relative change.", "tone": "good"},
                ],
            },
            {
                "type": "bars", "chapter": "CHAPTER 04 · <strong>PRIMARY ENDPOINT</strong>",
                "title": "UACR: finerenone이 더 크게 낮췄다",
                "subtitle": "절대값보다 상대 변화와 위약 대비 차이를 기억하면 된다.",
                "source": "NEJM 2026 FINE-ONE results",
                "bars": [
                    {"label": "Finerenone", "value": "−34%", "width": 66, "tone": "good"},
                    {"label": "Placebo", "value": "−12%", "width": 88, "tone": "steel"},
                    {"label": "Vs placebo", "value": "−25%", "width": 75, "tone": "good"},
                    {"label": "P value", "value": "&lt;0.001", "width": 95, "tone": "navy"},
                ],
                "side": [
                    {"title": "Baseline to 6 months", "body": "Finerenone: median UACR 574.6 → 373.5. Placebo: 506.4 → 475.6.", "tone": "good"},
                    {"title": "해석", "body": "알부민뇨 감소는 장기 신장위험 감소와 연결되지만, 본 연구 자체는 장기 outcome을 직접 증명하지 않는다.", "tone": "warn"},
                ],
            },
            {
                "type": "table", "chapter": "CHAPTER 05 · <strong>SAFETY</strong>",
                "title": "안전성: 고칼륨혈증과 초기 eGFR dip",
                "subtitle": "비슷한 계열의 해석 원칙: 효과는 기대하되, 칼륨은 반드시 본다.",
                "source": "NEJM 2026 FINE-ONE safety",
                "columns": ["항목", "Finerenone", "Placebo", "실무 해석"],
                "rows": [
                    {"cells": ["<strong>고칼륨혈증</strong>", "10.1%", "3.3%", "가장 흔한 이상반응. 시작 전·초기 추적 K 확인"], "tone": "warn"},
                    {"cells": ["<strong>고칼륨 중단</strong>", "1.7%", "0%", "대부분 관리 가능했으나 중단 사례 존재"], "tone": "warn"},
                    {"cells": ["<strong>eGFR 변화</strong>", "−5.6", "−2.7", "초기 dip. washout 기간에 baseline 접근"], "tone": "steel"},
                    {"cells": ["<strong>치료 중단</strong>", "6.7%", "8.2%", "전체 중단은 위약과 유사"], "tone": "good"},
                ],
            },
            {
                "type": "cards", "chapter": "CHAPTER 06 · <strong>MECHANISM</strong>",
                "title": "Finerenone의 위치",
                "subtitle": "비스테로이드성 mineralocorticoid receptor antagonist로 염증·섬유화 축을 겨냥한다.",
                "source": "FINE-ONE rationale · FIDELIO/FIGARO background",
                "cards": [
                    {"title": "MR blockade", "body": "Mineralocorticoid receptor 과활성을 막아 신장 염증·섬유화 신호를 줄인다.", "tone": "navy"},
                    {"title": "Nonsteroidal", "body": "Spironolactone과 달리 비스테로이드성 구조. T2D CKD에서 outcome 근거 축적.", "tone": "steel"},
                    {"title": "Albuminuria", "body": "사구체 손상 신호를 낮추는 방향. UACR는 치료 반응 추적에 적합.", "tone": "good"},
                    {"title": "Potassium", "body": "RAAS blockade와 병용될 때 고칼륨 위험이 올라가므로 모니터링 필수.", "tone": "warn"},
                ],
            },
            {
                "type": "timeline", "chapter": "CHAPTER 07 · <strong>MONITORING</strong>",
                "title": "진료실 모니터링 흐름",
                "subtitle": "허가·보험 적용 전이라도, 적용 후보를 생각할 때 필요한 안전 프레임이다.",
                "source": "Finerenone label principles · FINE-ONE safety",
                "steps": [
                    {"title": "Baseline", "body": "K, eGFR, UACR, 혈압, ACEi/ARB 용량 확인. K 높으면 시작 보류.", "tone": "navy"},
                    {"title": "4주", "body": "K/eGFR 재확인. 칼륨 상승 시 용량 조절·식이·병용약 검토.", "tone": "warn"},
                    {"title": "3개월", "body": "UACR 추적. 혈압·탈수·NSAID 사용 점검.", "tone": "steel"},
                    {"title": "6개월", "body": "UACR 반응과 안정성으로 지속 여부 판단.", "tone": "good"},
                ],
            },
            {
                "type": "cards", "chapter": "CHAPTER 08 · <strong>WHO</strong>",
                "title": "적용을 고려할 환자상",
                "subtitle": "지금은 '가이드라인 즉시 변경'보다 후보군을 식별하는 단계로 보는 것이 안전하다.",
                "source": "FINE-ONE inclusion criteria",
                "cards": [
                    {"title": "T1D + CKD", "body": "제1형 당뇨병이 명확하고 CKD가 동반된 성인.", "tone": "navy"},
                    {"title": "UACR ≥200", "body": "의미 있는 알부민뇨가 반복 확인된 환자.", "tone": "warn"},
                    {"title": "eGFR 25-90", "body": "연구 포함 범위. 말기 CKD·투석 전 단계는 별도 판단.", "tone": "steel"},
                    {"title": "ACEi/ARB 사용", "body": "RAAS blockade 최적화 후에도 잔여 알부민뇨가 남는 경우.", "tone": "good"},
                    {"title": "칼륨 안정", "body": "고칼륨 병력·식이·병용약 위험을 견딜 수 있어야 함.", "tone": "warn"},
                    {"title": "추적 가능", "body": "초기 K/eGFR 추적에 순응 가능한 환자.", "tone": "good"},
                ],
            },
            {
                "type": "split", "chapter": "CHAPTER 09 · <strong>INTERPRETATION</strong>",
                "title": "무엇을 말할 수 있고, 무엇은 아직인가",
                "subtitle": "알부민뇨 감소는 강한 신호지만 장기 endpoint는 아직 직접 증명 전이다.",
                "source": "NEJM 2026 FINE-ONE · NEJM editorial 2026",
                "left": {"title": "말할 수 있는 것", "items": [
                    "<strong>UACR 감소</strong> — 위약보다 통계적으로 명확",
                    "<strong>T1D 근거</strong> — T2D 외 영역으로 확장되는 첫 3상 결과",
                    "<strong>안전성</strong> — 고칼륨은 증가하지만 중단은 소수",
                    "<strong>실무 준비</strong> — 후보군·모니터링 체계를 만들 근거",
                ]},
                "right": {"title": "아직 말하기 이른 것", "items": [
                    "<strong>ESKD 감소</strong> — 본 연구에서 직접 증명 아님",
                    "<strong>MACE 감소</strong> — T1D hard CV outcome 근거는 부족",
                    "<strong>모든 T1D 적용</strong> — 알부민뇨 없는 환자에 일반화 불가",
                    "<strong>SGLT2i 대체</strong> — 약리·위험·허가 이슈가 달라 단순 대체 불가",
                ]},
                "note": "<strong>표현 — </strong>'신장 보호 효과가 입증됐다'보다 '알부민뇨를 의미 있게 낮췄고 장기 신장 보호 가능성을 뒷받침한다'가 정확하다.",
                "note_tone": "warn",
            },
            {
                "type": "table", "chapter": "CHAPTER 10 · <strong>COUNSELING</strong>",
                "title": "환자 설명 문장",
                "subtitle": "기대 효과와 검사 부담을 동시에 말해야 순응도가 생긴다.",
                "source": "Clinic counseling draft based on FINE-ONE",
                "columns": ["상황", "설명", "확인", "기록"],
                "rows": [
                    {"cells": ["<strong>시작 전</strong>", "소변 단백을 줄이는 약", "K/eGFR/UACR", "ACEi/ARB 복용 확인"], "tone": "steel"},
                    {"cells": ["<strong>효과</strong>", "6개월에 소변 단백 감소 기대", "UACR 추적", "장기 outcome은 추적 필요"], "tone": "good"},
                    {"cells": ["<strong>위험</strong>", "칼륨 상승 가능", "근력저하·부정맥 증상", "고칼륨 교육"], "tone": "warn"},
                    {"cells": ["<strong>생활</strong>", "저염·혈압·탈수 회피", "NSAID/보충제 확인", "병용약 점검"], "tone": "steel"},
                ],
            },
            {
                "type": "cards", "chapter": "CHAPTER 11 · <strong>LIMITATIONS</strong>",
                "title": "한계와 향후 가이드라인 전망",
                "subtitle": "관심은 높지만, 처방 기준은 허가·보험·장기 결과를 기다려야 한다.",
                "source": "NEJM 2026 FINE-ONE · KDIGO 2026 draft context",
                "cards": [
                    {"title": "짧은 기간", "body": "double-blind 치료 6개월. 장기 신장·심혈관 endpoint 확인 필요.", "tone": "warn"},
                    {"title": "선별된 환자", "body": "UACR 200-5000 mg/g, eGFR 25-90, ACEi/ARB 사용군.", "tone": "steel"},
                    {"title": "Surrogate endpoint", "body": "UACR는 강력한 marker지만 환자중심 결과는 아님.", "tone": "warn"},
                    {"title": "고칼륨 모니터링", "body": "추적 검사를 할 수 없는 환경에서는 안전성이 떨어진다.", "tone": "danger"},
                    {"title": "가이드라인 반영 가능성", "body": "T1D + 알부민뇨 CKD에서 추가 옵션으로 논의될 가능성.", "tone": "good"},
                    {"title": "국내 적용", "body": "허가 적응증과 급여는 별도 확인 필요.", "tone": "steel"},
                ],
            },
            {
                "type": "closing", "chapter": "CHAPTER 12 · <strong>TAKE HOME</strong>",
                "title": "진료실 결론",
                "subtitle": "FINE-ONE은 T1D CKD 치료 공백에 들어온 의미 있는 신호다.",
                "source": "NEJM 2026;394:947-957",
                "clinic_note": "국내 허가·급여 범위와 potassium monitoring protocol은 실제 처방 전 확인이 필요합니다.",
                "items": [
                    "<strong>대상은 좁다</strong> — T1D + CKD + UACR 200-5000 mg/g + ACEi/ARB 사용군.",
                    "<strong>효과는 UACR</strong> — 6개월 위약 대비 25% 추가 감소, hard outcome은 아직 직접 증명 전.",
                    "<strong>고칼륨이 핵심</strong> — 시작 전과 초기 K/eGFR 모니터링 없이는 쓰기 어렵다.",
                    "<strong>가이드라인 후보</strong> — T1D 알부민뇨 CKD의 add-on option으로 부상 가능.",
                ],
            },
        ],
    },
    {
        "slug": "easo-obesity-pharmacotherapy-2026",
        "plain_title": "EASO 2026 비만 약물치료 알고리즘 업데이트",
        "title": "EASO 2026 비만 약물 알고리즘,<br><em>감량 목표와 합병증으로 고른다</em>",
        "subtitle": "Nature Medicine 2026.05 — SURMOUNT-5 등 새 RCT 근거 반영. Tirzepatide와 semaglutide의 역할을 목표 체중감량·합병증 기준으로 재정렬.",
        "description": "EASO 2026 비만 약물치료 업데이트. Tirzepatide는 큰 체중감량 목표에서 근거가 더 강해졌고, semaglutide는 MASH fibrosis 등 특정 합병증 근거가 중요하다.",
        "chapter": "OBESITY · ENDOCRINOLOGY",
        "source": "Ciudin et al. Nature Medicine 2026 · EASO living framework update",
        "importance": 5,
        "slides": [
            {
                "type": "stats", "chapter": "CHAPTER 01 · <strong>TL;DR</strong>",
                "title": "한 문단·세 숫자로 요약",
                "subtitle": "이제 비만약 선택은 '어느 약이 더 세냐'가 아니라 '목표와 합병증이 무엇인가'다.",
                "source": "Nature Medicine 2026 · EASO update · SURMOUNT-5 NEJM 2025",
                "stats": [
                    {"label": "EVIDENCE BASE", "value": "62 RCT", "body": "2025.11.21까지의 새 근거를 반영한 living guidance 업데이트.", "tone": "navy"},
                    {"label": "SURMOUNT-5", "value": "20.2% vs 13.7%", "body": "Tirzepatide vs semaglutide 72주 평균 체중감량.", "tone": "good"},
                    {"label": "MASH FIBROSIS", "value": "Semaglutide", "body": "2026 업데이트에서 fibrosis stage improvement 근거는 semaglutide가 더 강함.", "tone": "steel"},
                ],
                "note": "<strong>중요한 단서 — </strong>EASO는 알고리즘을 universal ranking이나 처방 순서로 읽지 말라고 명시했다. 환자 특성, 선호, 비용, 안전성을 함께 본다.",
                "note_tone": "warn",
            },
            {
                "type": "cards", "chapter": "CHAPTER 02 · <strong>WHAT CHANGED</strong>",
                "title": "2026 업데이트에서 달라진 포인트",
                "subtitle": "체중감량 주목표와 MASH 영역에서 근거 분리가 더 선명해졌다.",
                "source": "EASO press release 2026-05-12 · Nature Medicine 2026",
                "cards": [
                    {"title": "Tirzepatide 우위 명확화", "body": "합병증 없는 비만에서 체중감량 자체가 주목표일 때 근거가 더 강해졌다.", "tone": "good"},
                    {"title": "SURMOUNT-5 반영", "body": "직접 비교 RCT로 tirzepatide의 평균 감량 폭과 목표 달성률 우위 확인.", "tone": "navy"},
                    {"title": "MASH update", "body": "MASH remission은 semaglutide 또는 tirzepatide, fibrosis stage improvement는 semaglutide 근거가 더 강함.", "tone": "steel"},
                    {"title": "Not a ranking", "body": "알고리즘은 처방 순서표가 아니라 합병증-목표 기반 의사결정 도구.", "tone": "warn"},
                    {"title": "Safety domain 예정", "body": "향후 업데이트에서 중단율·이상반응 등 benefit-risk 영역이 강화될 전망.", "tone": "steel"},
                    {"title": "Living guidance", "body": "새 약제·경구제·장기 outcome이 나오면 계속 바뀌는 구조.", "tone": "good"},
                ],
            },
            {
                "type": "bars", "chapter": "CHAPTER 03 · <strong>SURMOUNT-5</strong>",
                "title": "직접 비교: tirzepatide가 평균 감량 폭에서 우위",
                "subtitle": "환자에게 '몇 kg'보다 '목표 감량률 달성 가능성'으로 설명하면 명확하다.",
                "source": "Aronne et al. NEJM 2025;393:26-36 · Lilly release 2025-05-11",
                "bars": [
                    {"label": "평균 감량 Tirzepatide", "value": "−20.2%", "width": 81, "tone": "good"},
                    {"label": "평균 감량 Semaglutide", "value": "−13.7%", "width": 55, "tone": "steel"},
                    {"label": "≥20% 달성 Tirzepatide", "value": "48.4%", "width": 48, "tone": "good"},
                    {"label": "≥20% 달성 Semaglutide", "value": "27.3%", "width": 27, "tone": "steel"},
                ],
                "side": [
                    {"title": "해석", "body": "평균 차이 6.5%p. BMI 35 이상 또는 20% 이상 감량이 필요한 군에서 임상적으로 크다.", "tone": "good"},
                    {"title": "주의", "body": "Open-label trial이며 안전성 비교에 powered 된 연구는 아니다.", "tone": "warn"},
                ],
            },
            {
                "type": "flow", "chapter": "CHAPTER 04 · <strong>TARGET-FIRST</strong>",
                "title": "목표 감량률로 먼저 나누기",
                "subtitle": "환자에게 먼저 물을 질문은 '얼마나 빼야 합병증이 좋아지는가'다.",
                "source": "EASO 2026 framework · SURMOUNT-5",
                "steps": [
                    {"label": "5-10%", "title": "초기 대사 개선", "body": "혈당·혈압·지질 개선 목적. 생활요법+약물 선택 폭 넓음.", "tone": "steel"},
                    {"label": "10-15%", "title": "Semaglutide zone", "body": "GLP-1RA 단독으로 충분한 목표. CV 보호 근거도 고려.", "tone": "good"},
                    {"label": "15-20%", "title": "공유 의사결정", "body": "tirzepatide 우선 검토. 비용·부작용·선호도 함께 평가.", "tone": "warn"},
                    {"label": "≥20%", "title": "Tirzepatide zone", "body": "고도비만·OSA·큰 기계적 부담이 있으면 우선 고려.", "tone": "good"},
                    {"label": "Bariatric", "title": "수술/다학제", "body": "약물만으로 부족한 BMI·합병증은 수술 포함 평가.", "tone": "navy"},
                ],
            },
            {
                "type": "table", "chapter": "CHAPTER 05 · <strong>COMPLICATIONS</strong>",
                "title": "합병증별 약물 선택 프레임",
                "subtitle": "체중감량률만 보지 말고, 어떤 합병증을 함께 치료하려는지 본다.",
                "source": "EASO 2026 update · Nature Medicine",
                "columns": ["합병증/목표", "Tirzepatide", "Semaglutide", "실무 포인트"],
                "rows": [
                    {"cells": ["<strong>체중감량 주목표</strong>", "근거 더 강함", "강함", "큰 감량 필요 시 tirzepatide 우선 검토"], "tone": "good"},
                    {"cells": ["<strong>심혈관 보호</strong>", "outcome 진행 중/제한", "SELECT 등 근거", "ASCVD 동반이면 semaglutide 근거가 강점"], "tone": "steel"},
                    {"cells": ["<strong>OSA + 비만</strong>", "강점", "자료 제한", "기계적 감량 효과가 중요"], "tone": "good"},
                    {"cells": ["<strong>MASH remission</strong>", "가능", "가능", "둘 다 고려 가능"], "tone": "steel"},
                    {"cells": ["<strong>MASH fibrosis</strong>", "덜 성숙", "근거 더 강함", "fibrosis 개선 목표면 semaglutide 쪽 근거 확인"], "tone": "warn"},
                ],
            },
            {
                "type": "split", "chapter": "CHAPTER 06 · <strong>NOT A RANKING</strong>",
                "title": "알고리즘을 '순위표'로 읽지 않는다",
                "subtitle": "EASO가 직접 강조한 부분이다. 환자별 맥락이 처방을 바꾼다.",
                "source": "EASO 2026 press release",
                "left": {"title": "순위표가 아닌 이유", "items": [
                    "<strong>직접 비교는 일부</strong> — 많은 비교는 NMA와 별도 RCT 기반",
                    "<strong>합병증별 endpoint</strong> — 체중, MACE, OSA, MASH가 서로 다름",
                    "<strong>부작용과 중단율</strong> — efficacy만으로 결정 불가",
                    "<strong>가격·접근성</strong> — 실제 치료 지속 가능성을 좌우",
                ]},
                "right": {"title": "진료실에서 묻는 질문", "items": [
                    "<strong>목표 감량률</strong> — 10%, 15%, 20% 중 어디인가",
                    "<strong>동반질환</strong> — T2D, ASCVD, OSA, MASH, 관절염",
                    "<strong>이전 경험</strong> — GLP-1RA 부작용·중단 이력",
                    "<strong>비용/선호</strong> — 주사제 수용성과 장기 비용",
                ]},
                "note": "<strong>상담 문장 — </strong>'더 잘 빠지는 약' 하나로 끝내지 말고, 목표와 동반질환에 맞는 약을 고른다.",
                "note_tone": "good",
            },
            {
                "type": "timeline", "chapter": "CHAPTER 07 · <strong>FIRST VISIT</strong>",
                "title": "비만약 첫 상담 4단계",
                "subtitle": "약제명을 고르기 전에 목표와 위험을 고정한다.",
                "source": "EASO 2026 framework · clinic algorithm draft",
                "steps": [
                    {"title": "Baseline phenotype", "body": "BMI, 허리둘레, 혈압, A1c, 지질, 간수치, 수면무호흡 증상.", "tone": "navy"},
                    {"title": "Target setting", "body": "3개월·6개월·12개월 목표 감량률과 합병증 목표를 수치화.", "tone": "good"},
                    {"title": "Drug fit", "body": "tirzepatide/semaglutide/기타 약물, 금기, 비용, 선호도 검토.", "tone": "steel"},
                    {"title": "Follow-up rule", "body": "용량 증량, 위장관 부작용, 근손실 예방, 중단 기준을 사전 설명.", "tone": "warn"},
                ],
            },
            {
                "type": "cards", "chapter": "CHAPTER 08 · <strong>SAFETY</strong>",
                "title": "효과만큼 중요한 지속 가능성",
                "subtitle": "감량 폭이 커도 중단하면 만성질환 치료가 아니다.",
                "source": "SURMOUNT-5 NEJM 2025 · EASO 2026 update",
                "cards": [
                    {"title": "위장관 부작용", "body": "오심·구토·변비·설사. 증량 속도와 식사 패턴 조정이 핵심.", "tone": "warn"},
                    {"title": "담낭/췌장", "body": "담석·췌장염 증상 교육. 심한 지속 복통은 즉시 평가.", "tone": "danger"},
                    {"title": "근손실", "body": "단백질·저항운동 없으면 체중은 줄어도 기능은 떨어질 수 있음.", "tone": "steel"},
                    {"title": "비용", "body": "장기 지속 비용을 시작 전에 확인. 중단 후 재증가 가능성 설명.", "tone": "warn"},
                    {"title": "금기", "body": "MTC/MEN2 병력, 임신 계획, 중증 위장관 질환 등 확인.", "tone": "danger"},
                    {"title": "추적", "body": "체중·허리둘레·A1c·간수치·증상 지표를 같은 방식으로 반복 측정.", "tone": "good"},
                ],
            },
            {
                "type": "split", "chapter": "CHAPTER 09 · <strong>DRUG SELECTION</strong>",
                "title": "Tirzepatide vs Semaglutide: 실무적 분기",
                "subtitle": "공식 권고를 과장하지 않고, 근거의 강점을 진료실 언어로 바꾼다.",
                "source": "EASO 2026 update · SURMOUNT-5 NEJM 2025",
                "left": {"title": "Tirzepatide를 먼저 떠올릴 때", "items": [
                    "<strong>≥20% 감량 목표</strong> 또는 BMI 35 이상 고도비만",
                    "<strong>OSA·관절부하</strong> 등 기계적 체중 부담이 핵심",
                    "<strong>기존 GLP-1RA 반응 부족</strong> 또는 목표 미달",
                    "<strong>큰 허리둘레 감소</strong>가 필요한 대사위험군",
                ]},
                "right": {"title": "Semaglutide가 더 설득력 있을 때", "items": [
                    "<strong>10-15% 목표</strong>로 충분한 환자",
                    "<strong>ASCVD 위험</strong>에서 CV outcome 근거를 중시",
                    "<strong>MASH fibrosis</strong> 개선 근거를 우선 고려",
                    "<strong>약제 접근성·비용</strong>에서 현실성이 높은 경우",
                ]},
                "note": "<strong>중립 문장 — </strong>'체중 감량 폭은 tirzepatide가 더 크지만, 심혈관·간질환 등 목표에 따라 semaglutide 근거가 더 중요할 수 있습니다.'",
                "note_tone": "steel",
            },
            {
                "type": "table", "chapter": "CHAPTER 10 · <strong>KOREA CLINIC</strong>",
                "title": "한국 외래에서 바로 쓰는 선택표",
                "subtitle": "환자 질문은 대개 '삭센다/위고비/마운자로 중 뭐가 좋나'로 들어온다.",
                "source": "Clinic implementation draft based on EASO 2026",
                "columns": ["환자상", "우선 질문", "약물 방향", "추적 지표"],
                "rows": [
                    {"cells": ["<strong>BMI 30-34</strong>", "목표 10-15%?", "semaglutide 또는 tirzepatide", "체중·허리·A1c"], "tone": "steel"},
                    {"cells": ["<strong>BMI ≥35</strong>", "20% 이상 필요?", "tirzepatide 우선 검토", "OSA·관절·지방간"], "tone": "good"},
                    {"cells": ["<strong>ASCVD 동반</strong>", "CV 보호가 핵심?", "semaglutide 근거 강조", "MACE risk·BP·LDL"], "tone": "steel"},
                    {"cells": ["<strong>MASH/fibrosis</strong>", "섬유화 개선 목표?", "semaglutide 근거 확인", "FIB-4·FibroScan·ALT"], "tone": "warn"},
                    {"cells": ["<strong>비용 민감</strong>", "지속 가능?", "저비용 약제/생활요법 병행", "중단 위험·재증가"], "tone": "warn"},
                ],
            },
            {
                "type": "cards", "chapter": "CHAPTER 11 · <strong>PITFALLS</strong>",
                "title": "피해야 할 설명",
                "subtitle": "약물 선택을 단순 경쟁 구도로 만들면 장기 치료 설계가 깨진다.",
                "source": "EASO 2026 update",
                "cards": [
                    {"title": "무조건 tirzepatide", "body": "체중감량 우위는 명확하지만, 모든 합병증에서 universal first-line이라는 뜻은 아니다.", "tone": "danger"},
                    {"title": "Semaglutide는 약하다", "body": "ASCVD outcome과 MASH fibrosis 영역에서 중요한 근거가 있다.", "tone": "warn"},
                    {"title": "목표 없는 시작", "body": "몇 % 감량을 목표로 하는지 정하지 않으면 약제 평가가 불가능.", "tone": "warn"},
                    {"title": "부작용 늦게 설명", "body": "오심·변비·담낭·췌장 증상은 시작 전 교육해야 중단을 줄인다.", "tone": "steel"},
                    {"title": "운동 생략", "body": "근손실 예방 없이는 체중감량의 질이 떨어진다.", "tone": "steel"},
                    {"title": "중단 계획 없음", "body": "비만은 만성질환. 중단 후 재증가와 유지 전략을 사전에 논의.", "tone": "good"},
                ],
            },
            {
                "type": "closing", "chapter": "CHAPTER 12 · <strong>TAKE HOME</strong>",
                "title": "진료실 결론",
                "subtitle": "2026 EASO 업데이트의 핵심은 약제 서열이 아니라 목표 기반 선택이다.",
                "source": "Nature Medicine 2026 · EASO 2026 update · SURMOUNT-5 NEJM 2025",
                "clinic_note": "국내 허가, 공급, 급여, 약가는 시점에 따라 바뀔 수 있어 실제 처방 전 최신 정보를 확인해야 합니다.",
                "items": [
                    "<strong>큰 감량 목표</strong> — ≥20% 감량이 필요하면 tirzepatide 근거가 가장 설득력 있다.",
                    "<strong>합병증 목표</strong> — ASCVD·MASH fibrosis 등은 semaglutide 근거가 선택을 바꿀 수 있다.",
                    "<strong>알고리즘은 순위표가 아니다</strong> — 환자 특성·선호·비용·부작용을 함께 본다.",
                    "<strong>장기 치료로 설명</strong> — 증량, 부작용, 근손실 예방, 중단 후 유지까지 시작 전에 말한다.",
                ],
            },
        ],
    },
    {
        "slug": "calcium-vitamin-d-fracture-falls-bmj",
        "plain_title": "BMJ 2026 칼슘·비타민 D 보충제와 골절·낙상 예방",
        "title": "칼슘·비타민 D 보충제,<br><em>일괄 처방을 멈춰야 할 때</em>",
        "subtitle": "BMJ 2026.05 systematic review & meta-analysis — 69 RCT, 153,902명. 일반 성인·지역사회 고령자에서 골절·낙상 예방 효과는 임상적으로 미미.",
        "description": "BMJ 2026 메타분석: 칼슘, 비타민 D 또는 병합 보충제는 대부분의 일반 성인에서 골절·낙상 예방 효과가 작거나 없다. 결핍·시설거주 등 고위험군은 별도 평가.",
        "chapter": "GERIATRICS · PREVENTIVE MEDICINE",
        "source": "Massé et al. BMJ 2026;393:e088050 · DOI 10.1136/bmj-2025-088050",
        "importance": 4,
        "slides": [
            {
                "type": "stats", "chapter": "CHAPTER 01 · <strong>TL;DR</strong>",
                "title": "한 문단·세 숫자로 요약",
                "subtitle": "보충제 자동 권고보다 결핍 확인, 식이 평가, 낙상 예방이 먼저다.",
                "source": "BMJ 2026;393:e088050",
                "stats": [
                    {"label": "TRIALS", "value": "69 RCT", "body": "칼슘·비타민 D·병합 보충제를 placebo/no treatment와 비교.", "tone": "navy"},
                    {"label": "PARTICIPANTS", "value": "153,902명", "body": "대부분 일반 성인·지역사회 거주 고령자 근거가 중심.", "tone": "steel"},
                    {"label": "EFFECT", "value": "Little / none", "body": "골절·낙상 예방 효과가 대부분 임상적으로 의미 있게 보이지 않음.", "tone": "warn"},
                ],
                "note": "<strong>진료실 메시지 — </strong>'뼈에 좋으니 일단 드세요'가 아니라, 결핍·식이 부족·골다공증 치료 동반 여부를 확인한 뒤 처방한다.",
                "note_tone": "warn",
            },
            {
                "type": "split", "chapter": "CHAPTER 02 · <strong>WHY REASSESS</strong>",
                "title": "왜 다시 봐야 하나",
                "subtitle": "외래에서 보충제는 흔하지만, 환자가 기대하는 효과는 과장되어 있다.",
                "source": "BMJ 2026 meta-analysis background",
                "left": {"title": "기존 관행", "items": [
                    "<strong>50대 이상</strong>이면 칼슘·비타민 D를 자동 권고",
                    "<strong>골절 예방</strong>과 낙상 예방을 한 묶음으로 설명",
                    "<strong>검사 없이</strong> 복용 시작 후 장기 지속",
                    "<strong>골다공증 약</strong>과 보충제 권고가 혼재",
                ]},
                "right": {"title": "문제점", "items": [
                    "<strong>결핍군과 비결핍군</strong>이 섞여 근거 해석이 흐림",
                    "<strong>낙상</strong>은 근력·균형·약물·환경 요인이 더 큼",
                    "<strong>보충제 복용</strong>이 운동·식이 개입을 대체할 수 있음",
                    "<strong>신장결석·위장관 불편</strong> 등 부담도 존재",
                ]},
            },
            {
                "type": "cards", "chapter": "CHAPTER 03 · <strong>EVIDENCE MAP</strong>",
                "title": "무엇을 비교했나",
                "subtitle": "칼슘 단독, 비타민 D 단독, 병합요법을 분리해 보았다.",
                "source": "BMJ 2026;393:e088050",
                "cards": [
                    {"title": "Calcium alone", "body": "칼슘 단독 보충이 전체 골절·고관절 골절을 의미 있게 줄인다는 근거는 약함.", "tone": "warn"},
                    {"title": "Vitamin D alone", "body": "비결핍 일반 성인에서 낙상·골절 예방 효과가 일관되지 않음.", "tone": "warn"},
                    {"title": "Calcium + Vitamin D", "body": "병합도 대부분 결과에서 little to no effect. 특정 고위험군 가능성은 별도.", "tone": "steel"},
                    {"title": "Community-dwelling", "body": "지역사회 거주 일반 고령자에서는 자동 보충 이득이 작음.", "tone": "danger"},
                    {"title": "Institutional / deficient", "body": "요양시설, 영양불량, 심한 결핍은 일반화 금지. 개별 평가.", "tone": "good"},
                    {"title": "Falls", "body": "낙상은 보충제보다 근력, 균형, 시야, 약물 조정, 환경 개선이 핵심.", "tone": "navy"},
                ],
            },
            {
                "type": "table", "chapter": "CHAPTER 04 · <strong>WHO STILL NEEDS</strong>",
                "title": "그래도 보충제가 필요한 경우",
                "subtitle": "결론은 '전면 금지'가 아니라 '무차별 권고 중단'이다.",
                "source": "BMJ 2026 meta-analysis · osteoporosis practice context",
                "columns": ["환자군", "칼슘", "비타민 D", "실무 포인트"],
                "rows": [
                    {"cells": ["<strong>명확한 결핍</strong>", "식이 우선+필요시", "보충 적응", "25(OH)D, 식이 섭취, 원인 평가"], "tone": "good"},
                    {"cells": ["<strong>요양시설/영양불량</strong>", "고려", "고려", "일반 community-dwelling 근거와 분리"], "tone": "good"},
                    {"cells": ["<strong>골다공증 약 복용</strong>", "권장 섭취량 확보", "권장 섭취량 확보", "약물 RCT의 보조요법 맥락"], "tone": "steel"},
                    {"cells": ["<strong>비결핍 일반 고령자</strong>", "자동 권고 X", "자동 권고 X", "식이·운동·낙상 예방 우선"], "tone": "warn"},
                    {"cells": ["<strong>신장결석/CKD</strong>", "주의", "개별화", "칼슘·인·PTH·약물 상호작용 확인"], "tone": "danger"},
                ],
            },
            {
                "type": "timeline", "chapter": "CHAPTER 05 · <strong>ASSESS FIRST</strong>",
                "title": "처방 전 4단계 평가",
                "subtitle": "보충제보다 먼저 환자의 실제 위험을 분해한다.",
                "source": "Clinic implementation draft based on BMJ 2026",
                "steps": [
                    {"title": "Fracture risk", "body": "FRAX, 골절력, DEXA, 스테로이드, 부모 고관절골절.", "tone": "navy"},
                    {"title": "Diet", "body": "유제품·두부·멸치·채소 등 식이 칼슘 섭취량 추정.", "tone": "steel"},
                    {"title": "Vitamin D", "body": "결핍 위험, 햇빛 노출, 25(OH)D 측정 필요성 판단.", "tone": "warn"},
                    {"title": "Fall risk", "body": "근력, 균형, 시야, 수면제/벤조/항고혈압제, 집안 환경.", "tone": "good"},
                ],
            },
            {
                "type": "cards", "chapter": "CHAPTER 06 · <strong>WHAT WORKS BETTER</strong>",
                "title": "골절·낙상 예방의 우선순위",
                "subtitle": "낙상을 줄이는 개입은 보충제보다 행동과 환경에 가깝다.",
                "source": "Geriatric fall prevention principles · BMJ 2026 context",
                "cards": [
                    {"title": "저항운동", "body": "하지 근력과 균형을 높이는 운동. 주 2-3회가 실질적 낙상 예방.", "tone": "good"},
                    {"title": "균형훈련", "body": "한발서기, 보행훈련, Tai chi 등. 낙상 공포까지 줄인다.", "tone": "good"},
                    {"title": "약물 정리", "body": "수면제, 벤조디아제핀, 항콜린제, 과도한 혈압약 조정.", "tone": "warn"},
                    {"title": "시력·발", "body": "백내장, 다초점렌즈, 발 변형·신발 문제 확인.", "tone": "steel"},
                    {"title": "환경", "body": "러그, 욕실, 조명, 문턱, 계단 손잡이. 집에서 넘어지는 것을 줄인다.", "tone": "steel"},
                    {"title": "골다공증 치료", "body": "고위험군은 보충제가 아니라 항골흡수/골형성 약물 평가가 핵심.", "tone": "navy"},
                ],
            },
            {
                "type": "split", "chapter": "CHAPTER 07 · <strong>COUNSELING</strong>",
                "title": "환자 상담 문장",
                "subtitle": "이미 복용 중인 환자에게는 '끊으세요'보다 평가 후 조정이 안전하다.",
                "source": "Clinic counseling draft based on BMJ 2026",
                "left": {"title": "새로 시작하려는 환자", "items": [
                    "<strong>'검사 없이 자동으로'</strong> 시작할 필요는 없습니다.",
                    "<strong>식사로 충분한지</strong> 먼저 보겠습니다.",
                    "<strong>낙상 예방</strong>은 운동·약물정리·환경개선이 더 중요합니다.",
                    "<strong>결핍이 있으면</strong> 그때 용량과 기간을 정하겠습니다.",
                ]},
                "right": {"title": "이미 복용 중인 환자", "items": [
                    "<strong>복용 이유</strong> — 결핍, 골다공증 약, 단순 예방인지 확인",
                    "<strong>부작용</strong> — 변비, 위장불편, 결석력, CKD 확인",
                    "<strong>식이 섭취</strong> — 총 칼슘량이 과하지 않은지 계산",
                    "<strong>중단/감량</strong> — 고위험군이면 임의 중단 말고 계획적으로 조정",
                ]},
                "note": "<strong>핵심 — </strong>보충제 상담을 DEXA, FRAX, 낙상평가, 운동 처방으로 연결한다.",
                "note_tone": "good",
            },
            {
                "type": "table", "chapter": "CHAPTER 08 · <strong>ORDER SET</strong>",
                "title": "외래 처방·검사 세트 재정리",
                "subtitle": "자동 처방보다 평가 기반 처방으로 바꾼다.",
                "source": "Clinic implementation draft",
                "columns": ["상황", "검사/평가", "처방", "추적"],
                "rows": [
                    {"cells": ["<strong>일반 50대</strong>", "식이·운동·위험평가", "자동 보충 X", "건강검진/DEXA 적응증"], "tone": "warn"},
                    {"cells": ["<strong>골다공증</strong>", "DEXA·FRAX·Ca/P/VitD", "치료제+권장섭취량", "골밀도·순응도"], "tone": "good"},
                    {"cells": ["<strong>낙상 병력</strong>", "보행·약물·시력·환경", "운동·약물정리", "1-3개월 재평가"], "tone": "good"},
                    {"cells": ["<strong>결핍 의심</strong>", "25(OH)D", "목표 기간 보충", "재검 후 유지량"], "tone": "steel"},
                    {"cells": ["<strong>CKD/결석</strong>", "eGFR·Ca/P/PTH", "개별화", "신장내과 협의 고려"], "tone": "danger"},
                ],
            },
            {
                "type": "cards", "chapter": "CHAPTER 09 · <strong>PITFALLS</strong>",
                "title": "흔한 오해 정리",
                "subtitle": "보충제의 낮은 위해성 때문에 효과까지 과대평가되기 쉽다.",
                "source": "BMJ 2026 meta-analysis",
                "cards": [
                    {"title": "비타민 D는 낙상을 줄인다", "body": "비결핍 일반 성인에서는 일관된 낙상 감소를 기대하기 어렵다.", "tone": "warn"},
                    {"title": "칼슘은 많을수록 좋다", "body": "총 섭취량 과다, 변비, 결석, CKD 위험을 고려해야 한다.", "tone": "danger"},
                    {"title": "보충제가 골다공증 치료", "body": "고위험 골다공증은 항골다공증 약물 평가가 중심이다.", "tone": "navy"},
                    {"title": "검사 없이 평생 복용", "body": "복용 이유와 종료 조건이 없는 보충제는 약물 목록만 늘린다.", "tone": "warn"},
                ],
            },
            {
                "type": "split", "chapter": "CHAPTER 10 · <strong>CLINIC POLICY</strong>",
                "title": "진료실 정책으로 바꾸기",
                "subtitle": "자료 하나의 결론보다 실제 처방 습관을 바꾸는 것이 중요하다.",
                "source": "BMJ 2026 meta-analysis · clinic implementation draft",
                "left": {"title": "줄일 것", "items": [
                    "<strong>무증상·비결핍</strong> 일반 고령자 자동 처방",
                    "<strong>검사 없는</strong> 고용량 비타민 D 장기 처방",
                    "<strong>칼슘 중복</strong> — 종합비타민+칼슘제+식이 과다",
                    "<strong>낙상 예방을 보충제로 대체</strong>하는 설명",
                ]},
                "right": {"title": "늘릴 것", "items": [
                    "<strong>식이 칼슘 평가</strong> — 음식으로 먼저 채우기",
                    "<strong>25(OH)D 선별</strong> — 위험군 중심 측정",
                    "<strong>DEXA/FRAX</strong> — 골절위험 기반 치료 결정",
                    "<strong>운동 처방</strong> — 저항운동+균형훈련을 구체화",
                ]},
            },
            {
                "type": "cards", "chapter": "CHAPTER 11 · <strong>LIMITATIONS</strong>",
                "title": "해석의 한계",
                "subtitle": "모든 환자에게 보충제가 무의미하다는 뜻은 아니다.",
                "source": "BMJ 2026 meta-analysis · rapid responses context",
                "cards": [
                    {"title": "이질적 연구", "body": "연령, 거주 형태, baseline vitamin D, 용량, 순응도가 다양하다.", "tone": "steel"},
                    {"title": "결핍군 부족", "body": "심한 결핍, 영양불량, 시설거주 환자에 일반화하면 안 된다.", "tone": "warn"},
                    {"title": "복합 치료 맥락", "body": "골다공증 약물 trial에서는 칼슘·비타민 D가 배경요법으로 포함되는 경우가 많다.", "tone": "steel"},
                    {"title": "개별 목표", "body": "골절 예방이 아니라 결핍 교정, 골연화증 예방 등 다른 목표가 있을 수 있다.", "tone": "good"},
                ],
                "note": "<strong>정확한 결론 — </strong>대부분의 비결핍 일반 고령자에게 '골절·낙상 예방 목적의 일괄 보충'은 재고해야 한다.",
                "note_tone": "warn",
            },
            {
                "type": "closing", "chapter": "CHAPTER 12 · <strong>TAKE HOME</strong>",
                "title": "진료실 결론",
                "subtitle": "보충제를 없애는 것이 아니라, 자동 처방을 평가 기반 처방으로 바꾼다.",
                "source": "BMJ 2026;393:e088050",
                "clinic_note": "이 자료는 일반 외래 상담용 근거 요약입니다. 결핍, 요양시설 거주, 골다공증 약물치료, CKD 등은 개별 판단이 필요합니다.",
                "items": [
                    "<strong>일반 고령자 자동 권고 X</strong> — 골절·낙상 예방 효과는 대체로 작거나 없다.",
                    "<strong>결핍과 고위험군은 별도</strong> — 25(OH)D, 식이, 거주 형태, 골다공증 치료 여부를 본다.",
                    "<strong>낙상 예방은 운동·환경·약물정리</strong> — 보충제가 중심이 아니다.",
                    "<strong>처방 이유를 남긴다</strong> — 시작 이유, 목표, 기간, 재평가 시점을 EMR에 기록한다.",
                ],
            },
        ],
    },
]


def render_deck(deck: dict) -> str:
    total = 1 + len(deck["slides"])
    parts = [head(deck), cover(deck, total)]
    for idx, slide in enumerate(deck["slides"], start=2):
        if slide["type"] == "closing":
            parts.append(closing(deck, slide, idx, total))
        else:
            body = RENDERERS[slide["type"]](slide)
            parts.append(slide_shell(slide, body, idx, total))
    parts.append(end())
    return "".join(parts)


def main() -> None:
    for deck in DECKS:
        out_dir = ROOT / deck["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(render_deck(deck), encoding="utf-8")
        print(f"wrote {out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
