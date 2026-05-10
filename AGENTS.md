# AGENTS.md — Clinic Content System

> 이 레포에서 작업하는 모든 에이전트(Codex, Claude Code, 기타 AI 코딩 도구)가 따라야 할 규칙.
> **Source of Truth는 [`SKILL.md`](./SKILL.md)** — 이 파일은 그 핵심 규칙의 압축판이며, SKILL.md와 충돌 시 SKILL.md가 우선한다.

---

## 🔒 무조건 규칙 — Cross-Machine Consistency (최우선)

원장님은 머신 2~3개를 사용한다. **모든 변경은 머신이 바뀌어도 동일한 결과가 나오도록 작성해야 한다. 절대 예외 없음.**

| # | 규칙 |
|---|---|
| 1 | `~/clinic-content-system/`에서만 작업. 스킬 플러그인 폴더(`~/Library/Application Support/Claude/...`) 직접 편집 금지 |
| 2 | 머신 종속 절대경로 금지 (`C:\Users\...`, `/Users/도현/...`). `~/`, `Path(__file__).parent`, 환경변수만 사용 |
| 3 | 시크릿은 환경변수 / GitHub Secret만. 코드에 박지 말 것 |
| 4 | fresh clone에서 `gh auth → git clone → pip install -r requirements.txt`만으로 빌드되어야 함 |
| 5 | **변경 전 `git pull --rebase`, 변경 후 즉시 `git add . && git commit && git push`** — 사용자가 따로 지시하지 않아도 자동 수행 |
| 6 | `output/` 디렉토리 커밋 금지 (.gitignore 등록됨) |
| 7 | 새 의존성 추가 시 `requirements.txt` 갱신 |

**한 작업 = (pull) → 작업 → (push)** 이게 깨지면 다른 머신에서 작업이 사라지거나 충돌난다.

---

## 📦 콘텐츠 타입 3종 + Notion DB 라우팅

`build.py`의 TARGETS 항목 `kind` 필드가 3개 DB 중 하나로 자동 라우팅한다. 매핑은 [`shared/_notion_sync.py`](./shared/_notion_sync.py)의 `DBS` dict가 SoT.

| `kind` | 디렉토리 | 포맷 | Notion DB | DB ID | Title 속성 | 환자별? |
|---|---|---|---|---|---|---|
| `decks` | `decks/{specialty}/{topic}/{slug}/` | 16:9 1280×720, 12장 | 📋 진료 설명용 자료 | `a84f23489df54e8fbe34b9818d6109e5` | `자료명` | ❌ |
| `handouts` | `handouts/{specialty}/{slug}/` | A4 세로 1장 | 📨 환자 유인물 | `920b48c92d674186a370afcaa81ce788` | `자료명` | ❌ |
| `lab-reports` | `lab-reports/{topic}/{slug}/` | A4 세로 1장 | 🧪 환자 검사결과 | `c150b47d523c45c09108ac716009c49b` | `환자명` | ✅ |

### 분류 정의 (원장님 정의 — 변경 금지)
- **decks**: 진료 시 사용할 PPT 슬라이드 형태 자료
- **handouts**: 1~2장짜리 비환자 정보 공유용 — 카테고리 6종 (`🏥 내시경 관련` / `💊 투약 안내` / `🩺 시술·처치 후` / `🌿 생활습관·식이` / `🚨 증상별 안내` / `📝 동의서·서식`), audience 3종 (`환자/보호자` / `직원용` / `공용`)
- **lab-reports**: 환자 혈액검사 결과, 개인 설명용 결과지

### lab-reports 필수 메타데이터
`build.py` TARGETS 항목에 다음 필드 필수 (slug 는 `lab_hash_slug` 로 생성한 hash, 환자명 직접 사용 금지 — privacy):
```python
{
    "kind": "lab-reports", "slug": "<hash10>",  # python lab_hash_slug(chart_no, patient_name, topic)
    "slug_path": "lab-reports/general-checkup/<hash10>/",
    "html_path": ROOT / "lab-reports/general-checkup/<hash10>/index.html",
    "qr_class": "qr-mini__code", "fmt": "a4-portrait",
    "patient_name": "<환자명>",     # 필수 — Notion 카드 매칭용
    "chart_no": "<차트번호>",       # 필수
    "exam_date": "2026-05-08",      # 선택
    "doctor": "정지환",             # 선택
    "note": "종합검사 — 콜레스테롤 경계역",  # 선택
},
```
→ 노션 제목 자동 생성: `[<차트번호>] <환자명> — <note>`

Legacy 제목(`[<차트번호>] <환자명> — <검사명> (YYYY-MM-DD)`)도 `_notion_sync.py`가 자동 파싱.

---

## 🖼️ A4 레이아웃 검증 — 필수 2단계

A4 콘텐츠(handouts / lab-reports)는 본문이 넘쳐도 자동으로 다음 페이지로 안 넘어가고 **footer를 침범한다.** 두 단계 검증 필수:

### 1단계 — 자동 검증 (`_validate_layout`)
```bash
python -m shared._validate_layout <html_path>   # 단일
python -m shared._validate_layout               # 전체
```
검출 항목 (모두 0이어야 통과): `page_overflow`, `section_overlaps_footer`, `element_below_page` / `element_right_of_page`, `slide_overflow` (deck).

### 2단계 — 시각 확인
```bash
python build.py
# → output/{kind}/{slug}-preview.png 생성
# → 이미지 뷰어 또는 IDE preview로 PNG 직접 확인
```
**`ls output/`만으로 "파일 생겼으니 OK" 처리하지 말 것** — 검증기가 못 잡는 시각적 어색함이 있을 수 있다.

### 분량 룰 (handouts + lab-reports 공통)
1. 1페이지 우선 시도
2. 콘텐츠 부족 → 보강해서 1페이지 유지
3. 약간 넘침 → 항목 컴팩트화 (3-card → 통합 1-card)
4. 진짜 무리 → 2페이지로 확장 (**절대 폰트 줄이지 말 것**)

경험칙: lab-row 최대 10행, 해석 2-col bullet 카드당 3개, stats-row 4 cells 고정.

---

## 🔄 표준 워크플로우

```bash
cd ~/clinic-content-system
git pull --rebase                                # ① 다른 머신 변경분 받기
# ② HTML 작성 (decks/handouts/lab-reports 중 하나)
# ③ build.py TARGETS에 dict 항목 추가 (kind별 메타 포함)
python -m shared._validate_layout                # ④ 레이아웃 검증
python build.py                                  # ⑤ 로컬 빌드 (선택)
# → output/{kind}/{slug}-preview.png 시각 확인
git add . && git commit -m "Add {topic}" && git push   # ⑥ 자동 푸시
```

CI(GitHub Actions, ~80초)가 자동 처리:
- Playwright Chromium PDF 빌드
- GitHub Pages 배포 → `https://gwanggyo-barun.github.io/patient-education/{slug_path}/`
- `kind`에 따라 자동 라우팅된 Notion DB에 행 upsert (HTML/PDF 링크 포함)

---

## ⛔ 절대 하지 말 것

- ❌ 스킬 플러그인 폴더(`~/Library/Application Support/Claude/.../skills/clinic-content-system/`) 직접 편집
- ❌ `output/` 디렉토리 수동 편집 또는 커밋
- ❌ 머신 종속 절대경로 하드코딩
- ❌ 시크릿 토큰을 코드에 직접 작성
- ❌ A4 콘텐츠 빌드 후 preview PNG 시각 확인 생략
- ❌ `git pull --rebase` 없이 push (충돌 시 작업 손실 위험)
- ❌ 글자 크기 줄여서 한 페이지에 억지로 끼워넣기 (→ 항목 수 축소가 옳음)

---

## 📚 추가 참고

- 전체 규칙·디자인 시스템·컴포넌트 사양: [`SKILL.md`](./SKILL.md)
- 디자인 토큰 SoT: [`reference/brand-design-system.md`](./reference/brand-design-system.md)
- 7가지 본문 패턴: [`reference/patterns.md`](./reference/patterns.md)
- 12장 표준 구성: [`reference/content-template.md`](./reference/content-template.md)
- Notion sync 구현: [`shared/_notion_sync.py`](./shared/_notion_sync.py)
- 레이아웃 검증기 구현: [`shared/_validate_layout.py`](./shared/_validate_layout.py)
- 라이브 자원: GitHub Pages https://gwanggyo-barun.github.io/patient-education/, Actions https://github.com/gwanggyo-barun/patient-education/actions
