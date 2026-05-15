---
name: clinic-content-system
description: >
  광교바른내과 통합 환자 교육 콘텐츠 생성 스킬 (HTML + PDF). 세 가지 콘텐츠 타입을
  단일 디자인 시스템·단일 빌드 파이프라인으로 생산한다: (1) 16:9 멀티슬라이드 환자
  교육 덱, (2) A4 세로 1장 진료실 핸드아웃, (3) A4 세로 1장 검사 결과 인포그래픽.
  공통 인프라: Navy #003366 + Steel Blue #5B9BD5, Pretendard Variable, Python qrcode
  SVG 자동 QR 생성, OG meta 7개 head 등록. 사용자가 "환자 교육 슬라이드/PDF",
  "유인물 만들어줘", "주의사항 PDF", "비치용 안내문", "검사 결과지 인포그래픽",
  "결과지 시각화", "환자한테 보낼 자료", "카톡으로 보낼 자료" 등을 만들어 달라고
  할 때 트리거된다. 기존 patient-education-pptx, patient-handout-pdf,
  lab-report-infographic 세 스킬의 HTML 통합 후속 버전이며, PPTX가 명시적으로
  요구되지 않는 한 이 스킬을 우선 사용한다.
---

# Clinic Content System — Unified Patient Content (HTML + PDF)

## 🔒 무조건 규칙 — Cross-Machine Consistency (최우선)

**원장님은 머신 2~3개를 사용한다. 이 스킬의 모든 업데이트(SKILL.md, build.py, `_notion_sync.py`, reference/, shared/, 모든 콘텐츠 파일 포함)는 머신이 바뀌어도 동일한 결과가 나오도록 작성해야 한다. 절대 예외 없음.**

### 모든 변경에 적용되는 체크리스트

1. ✅ **표준 워킹 디렉토리 `~/clinic-content-system/`에서만 작업** — 플러그인 폴더 직접 편집 금지
2. ✅ **머신 종속 경로 하드코딩 금지** — `C:\Users\user\...`, `/Users/도현/...` 같은 절대 경로 금지. `~/`, `Path(__file__).parent`, 환경변수 사용
3. ✅ **시크릿은 환경변수 / GitHub Secret으로** — `NOTION_TOKEN` 같은 토큰을 코드에 직접 쓰지 않음
4. ✅ **fresh clone에서 동작 검증** — 새 머신에서 README의 3개 명령(`gh auth` → `git clone` → `pip install -r requirements.txt`)만으로 빌드되어야 함
5. ✅ **변경 전 `git pull --rebase`, 변경 후 즉시 명시적 stage → commit → push** — 다른 머신과의 충돌 방지 + 즉시 전파. 한 작업 = (pull) - 작업 - (push)
6. ⭐ **한 대화창에서 만든 변경은 단독 commit으로만 push, 다른 작업과 절대 묶지 않음** — 다음 순서를 절대 건너뛰지 않는다.
   - **(0)** 작업 시작 직후 `git status --short` 로 시작 상태 캡처. 이때 보이는 `A `/`M `/`D ` 표시 staged 항목은 모두 **다른 대화창의 잔재** (내가 아직 만지지 않음).
   - **(1)** `git add .` / `git add -A` / `git add <디렉토리>` 절대 금지. **이번 작업에서 만든/수정한 파일만 한 줄씩 명시적으로 add**.
   - **(2)** commit 명령 직전 다시 `git status --short` → staged 영역에 (0) 에서 본 항목 또는 내 작업 외 `A `/`M `/`D ` 가 있으면 **즉시 `git restore --staged <path>`** 로 unstage. **`git add ... && git commit ...` 한 줄로 체이닝 금지** — 사이에 audit 단계가 강제로 들어가야 한다. untracked (`??`) 는 그대로 둔다.
   - **(3)** unstage 후 `git status --short` 한 번 더 → 정확히 내 작업 파일만 staged 인지 눈으로 확인 → 그제서야 `git commit`.
   - **(4)** push 후 `git log -1 --stat` 로 실제 들어간 파일 확인 → 의도와 다르면 즉시 사용자에게 보고.
   - **이유**: 원장님은 머신·대화창 여러 개에서 동시에 다른 자료를 진행한다. git index 는 워킹 디렉터리 단위로 공유되므로, **다른 대화창이 `git add` 만 해두고 떠난 staged 항목은 내 다음 commit 에 그대로 따라간다** — `git add SKILL.md` 만 호출해도 미완성 파일이 묶여 push 된다. 2026-05-11 한 세션에서 두 번 연속 발생 (htn-why-start, appendicitis-red-flags) 후 정식 규칙화.
7. ✅ **`output/` 디렉토리 커밋 금지** — `.gitignore`에 등록됨, CI가 매번 새로 빌드
8. ✅ **새 의존성 추가 시 `requirements.txt` 갱신** — pip install로만 끝내면 다른 머신에서 ImportError

### Claude가 이 스킬을 사용할 때의 규칙

- 사용자가 SKILL.md, build.py, _notion_sync.py 등 스킬 파일 변경을 요청하면 **반드시 위 체크리스트 전부 통과시켜야 한다**
- **변경 시작 전 `git pull --rebase` 필수** — 다른 머신에서의 변경을 먼저 받기. 충돌 안 나는 게 정상
- **변경 작업 끝에 commit + push 자동 수행** (사용자 추가 지시 없어도). 사유: 머신 간 일관성 확보가 본 스킬의 무조건 규칙
- decks/handouts 추가 시 동일 — 커밋 메시지에 주제 명시
- **lab-reports 커밋 메시지에는 환자명/차트번호 절대 금지** — repo 가 public 이라 git log 가 노출됨. `Add lab-report 842acd69b8 (diabetes-screening)` 처럼 hash 만 쓴다 ([Gotcha 11] 참조)

### 다른 머신에서 SKILL 업데이트 받기 (수신 측 절차)

이 SKILL.md / `reference/` / `shared/` / `tools/` 변경은 GitHub origin/main 에 push되지만, Claude 가 실제로 로드하는 것은 **각 머신의 플러그인 폴더 안 SKILL.md** 다. 플러그인 폴더는 그 자체로 patient-education 의 git clone 이며 자동 업데이트되지 않으므로, push 한 머신 외 다른 머신에서는 다음 두 곳을 모두 pull 해야 최신 SKILL 이 로드된다.

**터미널이 있으면 (macOS / Linux / Windows Git Bash):**
```bash
# 1. 워킹 디렉토리 (작업용)
cd ~/clinic-content-system && git pull --rebase

# 2. 플러그인 폴더 (Claude 가 SKILL.md 로드하는 위치)
bash ~/clinic-content-system/tools/sync_plugin_clone.sh
```

**터미널 없이 데스크톱 클로드 코드만 쓰는 경우 (예: Windows 데스크톱)**: 그냥 채팅창에 한국어로 **"다른 머신에서 작업했어. 동기화해줘"** 또는 **"clinic-content-system 동기화"** 라고 말하면 클로드가 위 두 명령어를 자동으로 실행한다. (Claude Code 의 Bash 도구가 OS 별 셸을 알아서 사용 — Windows 는 Git Bash, macOS·Linux 는 bash.)

`tools/sync_plugin_clone.sh` 는 OS 별 Claude 데이터 디렉토리 (macOS `~/Library/Application Support/Claude`, Linux `~/.config/Claude`, Windows `%APPDATA%/Claude`) 아래에서 patient-education 리모트를 가진 clone 을 모두 자동 탐색해 `git pull --rebase`. 플러그인 재설치 없이 SKILL 업데이트만 받을 때 사용. 플러그인 폴더 UUID 는 머신마다 다르므로 스크립트가 알아서 찾는다.

새 머신 첫 세팅 직후에도 한 번 돌려두면 안전하다 (마켓플레이스 캐시가 옛 버전이면 즉시 최신화됨).

### 어겼을 때의 결과

- 머신 A에서 추가한 새 워크플로우가 머신 B에서 동작 안 함
- 머신 종속 path/token으로 인한 CI 빌드 실패
- SKILL.md 갱신 후 다른 머신에서 옛 SKILL이 로드되어 잘못된 워크플로우 실행
- 환자 자료가 한 머신에만 존재 → 다른 머신에서는 사라진 듯 보임
- pull 안 하고 push해서 rebase 충돌 → 작업 손실 위험

---

## 📚 알려진 함정 (Known Gotchas) — 어떤 머신에서도 같은 실수를 하지 않도록

이 섹션은 과거에 실제로 발생해서 라이브 사이트를 깨뜨렸던 버그들을 정리한다. 같은 패턴 반복 금지.

### 1. CSS/asset 경로의 깊이 (`../` 개수)는 슬러그 깊이에 따라 달라진다

자료마다 디렉터리 깊이가 다르므로 `<link href="../../...">` 의 `../` 개수가 자료마다 다르다.
- **3-level deep** 자료 (`decks/cardio/chest-pain/`, `handouts/lifestyle/x/`, `lab-reports/kind/x/`) → `../../../shared/`
- **4-level deep** 자료 (`decks/cardio/htn/morning/`, `decks/gi/h-pylori/eradication/` 등) → `../../../../shared/`

**절대 일괄 sed 로 모든 자료의 `../` 개수를 바꾸지 말 것.** 슬러그 깊이를 따라가야 한다.

자동 검증: `build.py` 의 `_validate_css_paths()` 가 빌드 전 모든 자료의 CSS/이미지 경로가 실제 file system 에 존재하는지 검증한다. 잘못된 경로 → 빌드 fail.

### 2. `inject_qr()` 는 multi-class div 도 지원해야 한다

자료별로 custom 클래스 (`<div class="qr-block__code takehome-side__qr">`) 가 있으므로, `inject_qr` 는 정확한 단일 클래스 매칭이 아니라 클래스 list 안에 target_class 가 포함되는지 검사한다 (`shared/_build_helpers.py`).

### 3. `build.py` 는 raw HTML 의 QR div 도 갱신해야 한다

옛 패턴은 `_build.html` 임시 파일만 만들어 PDF 빌드 후 unlink. 결과: 라이브 GH Pages 의 raw HTML 에는 빈 `<div class="qr-block__code"></div>` 가 그대로 → 라이브에서 QR 안 보임.

현 패턴: `inject_qr` 결과를 raw `index.html` 에 직접 overwrite. SVG 가 deterministic 이라 매 빌드마다 같은 결과 → git diff drift 0.

### 4. 모바일 viewport 는 fixed-width 로 (CSS zoom 사용 금지)

표준 패턴:
- decks: `<meta name="viewport" content="width=1280">`
- handouts/lab-reports: `<meta name="viewport" content="width=794">`

모바일 브라우저가 자동 fit-to-width + 핀치줌 정상 작동.

⚠️ **CSS `zoom` 또는 `transform: scale()` 모바일 미디어 쿼리 사용 금지.** iOS Safari + 카카오톡 인앱 브라우저에서 핀치줌 차단되고 잘림이 더 심해진다 (실측 결과).

### 5. Notion DB 는 `kind` 로 자동 라우팅 (3 DB 분리)

| `kind` | DB | 분류 정의 |
|---|---|---|
| `decks` | 📋 진료 설명용 자료 (`a84f23489d...`) | 진료 시 환자에게 설명할 슬라이드. 환자별 X. |
| `handouts` | 📨 환자 유인물 (`920b48c92d...`) | 한 장 안내문. 환자별 X. |
| `lab-reports` | 🧪 환자 검사결과 (`c150b47d52...`) | 환자 개인 검사결과. 페이지 제목에 환자명+차트번호 필수. |

`build.py` 의 `_validate_targets_routing()` 가 빌드 전 자동 검증. `slug_path` 가 `kind/` 로 시작 안 하면 빌드 fail.

자료를 잘못된 DB 에 sync 하면 옛 sync 결과 + 신규 sync 결과로 중복·misclass 행이 쌓인다 (한 번 발생함, 37 행 정리해서 복구).

### 6. lab-reports 는 환자명+차트번호 필수

DB 행 제목이 `[차트번호] 환자명` 또는 `[차트번호] 환자명 — 부연` 형식. `_notion_sync.py` 가 자동 파싱하거나 explicit `patient_name`/`chart_no` 필드 사용.

**dedup 키는 슬러그(파일링크 URL 안의 hash)** — 타이틀 아님. 같은 lab-report TARGETS 항목의 `note`/`patient_name` 표기를 편집하고 다시 빌드해도 슬러그가 같으면 동일 row 가 PATCH 된다 (중복 row 안 만들어짐). 한 번 깨졌던 적 있음 (2026-05-11 박성주 29859, title equals 만 보다가 note 편집되면 새 row 생성됨). decks/handouts 는 타이틀 안정 식별자라 그대로 title equals 매칭.

### 7. Notion API 는 페이지 본문 prepend (맨 위 삽입) 직접 지원 X

새 콜아웃을 페이지 본문 맨 위에 삽입하려면 모든 children block 을 가져온 뒤 다시 작성해야 한다 (replace_content). 단순 PATCH /children 은 항상 끝에 append.

### 8. NOTION_TOKEN 은 절대 채팅에 붙여넣지 않는다

대화 로그에 영구 저장됨. 안전한 방법:
- 로컬: `~/clinic-content-system/_migration/.env` 파일에만 저장 (.gitignore 등록됨)
- CI: GitHub Secret 으로만
- 노출 시 즉시 https://www.notion.so/my-integrations 에서 재발급

### 9. page_id prefix 8자 매칭은 충돌한다

다운로드·매칭 시 page_id 의 8자 접두사 (`343b8014` 같은) 는 자료 17개와 매칭됨. **항상 32자 전체 사용** (다운로드 파일명·매핑 키 등).

### 10. 자동 검증의 한계

`_validate_layout` (bbox) + HTTP 200 만 확인하면 시각적 깨짐 (CSS 미로드, font 안 보임 등) 못 잡는다. **`shared/_visual_audit.py`** 가 라이브 URL 을 Playwright 로 실제 렌더링해서 검증. CI 또는 push 후 수동 실행.

```bash
python -m shared._visual_audit              # all 66 materials
python -m shared._visual_audit --kind=decks # decks only
```

### 11. lab-reports 개인정보 보호 — hash slug + QR 제거 + noindex

GH Pages 는 전체 공개 호스팅이라 lab-reports 의 환자명을 URL slug 로 쓰면 외부에서 패턴 추측만으로 검사 결과 노출 가능. **lab-reports 만** 다음 3중 보호:

1. **Hash slug** — `slug` / `slug_path` 의 환자명 자리에 결정적 SHA-256 hex(10자) 사용. `_build_helpers.lab_hash_slug(chart_no, patient_name, topic)` 호출. 같은 입력이면 매번 같은 hash 라 재빌드해도 URL drift 0. 노션 카드는 `chart_no + 환자명` 으로 매칭하므로 카드 1개에 새 URL 만 덮어씀.
2. **QR 제거** — `build.py` 가 `kind == "lab-reports"` 일 때 `make_qr_svg`/`inject_qr` 대신 `strip_qr_mini_block(html)` 으로 footer `<div class="qr-mini">…</div>` 통째 제거. PDF 인쇄물에서 URL 누출 차단.
3. **noindex + robots.txt** — `inject_noindex_meta` 가 head 에 `<meta name="robots" content="noindex,nofollow,noarchive">` 자동 주입 + 루트 `robots.txt` 가 `/lab-reports/` Disallow. 검색엔진 인덱싱 차단.
4. **빌드 단계 Korean-slug 차단** — `_validate_targets_routing()` 가 lab-reports entry 의 `slug` / `slug_path` 에 한글(가-힣)이 있으면 빌드 fail. 머신 동기화 깜빡하고 환자명 slug 로 만들어도 CI 가 push 단계에서 막음.

새 lab-report 추가 절차:
```
1. chart_no + patient_name + topic 결정
2. python -c "import sys; sys.path.insert(0,'shared'); from _build_helpers import lab_hash_slug; print(lab_hash_slug('차트번호','환자명','topic'))"
3. lab-reports/{topic}/{hash}/index.html 작성 — qr-mini block 안 넣어도 됨 (있어도 build 가 strip)
4. TARGETS 항목 추가: slug=hash, slug_path=lab-reports/{topic}/{hash}/, html_path=ROOT/.../index.html, patient_name+chart_no 명시
5. 커밋·푸시
```

**남는 위험**: git history 에 옛 환자명 디렉토리 자취가 남는다 (public repo 인 경우 이슈). 완전 제거하려면 `git filter-repo` 또는 BFG 사용 + force-push 필요 — 별도 작업.

---

## 🚀 배포 워크플로우 — 모든 머신 공통 (반드시 먼저 읽기)

**Source of Truth**: https://github.com/gwanggyo-barun/patient-education (public)

이 스킬의 **실제 콘텐츠와 빌드 파이프라인**은 위 GitHub 레포에 있다. 스킬 플러그인 폴더(`~/Library/Application Support/Claude/.../skills/clinic-content-system/`)는 머신마다 버전이 다르고 플러그인 업데이트 시 갈아엎힐 수 있으므로, **콘텐츠 작성·수정·빌드는 절대 플러그인 폴더에서 하지 말 것**.

### 표준 워킹 디렉토리 (모든 머신)

```
~/clinic-content-system/
```

이 경로에 GitHub 레포를 clone한 사본이 있어야 한다. 모든 작업(HTML 작성, build.py 수정, 커밋, 푸시)은 여기서 수행.

### 새 머신 1회 세팅 (3개 명령)

```bash
gh auth status || gh auth login                                    # GitHub 인증 (gh CLI 필요)
git clone https://github.com/gwanggyo-barun/patient-education ~/clinic-content-system
cd ~/clinic-content-system && pip install -r requirements.txt      # 로컬 빌드용 (CI만 쓸거면 생략 가능)
```

이게 끝. 별도 환경변수·시크릿 설정 불필요 (`NOTION_TOKEN`은 레포 GitHub Secret으로 등록되어 있어 CI가 알아서 사용).

### 일상 콘텐츠 작성 워크플로우

1. `cd ~/clinic-content-system` (스킬 트리거되면 Claude가 여기로 이동)
2. `git pull` (다른 머신에서 푸시한 것 받기)
3. 새 HTML 작성 — `decks/{specialty}/{topic}/{slug}/index.html` 또는 `handouts/...` 또는 `lab-reports/...`
4. `build.py`의 `TARGETS` 리스트에 새 항목 추가 (kind, slug, slug_path, html_path, qr_class, fmt, **+ Notion 메타: title, category, audience, disease**)
5. (선택) 로컬 검증: `python build.py` — Playwright 설치되어 있다면
6. **`git add . && git commit -m "Add {topic}" && git push`**
7. CI(GitHub Actions)가 ~1분 20초에 자동 처리:
   - PDF 빌드 (Playwright Chromium)
   - GitHub Pages 배포 (HTML + PDF 라이브)
   - Notion DB 자동 행 upsert (📋 진료 설명용 자료 DB)

### 라이브 URL

| 자원 | URL |
|---|---|
| Pages 호스팅 | https://gwanggyo-barun.github.io/patient-education/ |
| Notion DB (📋 진료 설명용 자료) | https://www.notion.so/a84f23489df54e8fbe34b9818d6109e5 |
| GitHub Actions | https://github.com/gwanggyo-barun/patient-education/actions |

### 절대 규칙

- ❌ **스킬 플러그인 폴더에서 작업 금지** — 거기서의 변경은 다른 머신에 전파 안 됨
- ❌ **`output/` 디렉토리 수동 편집 금지** — CI가 매번 새로 빌드함 (.gitignore에 등록됨)
- ✅ **항상 `~/clinic-content-system/`에서 작업**
- ✅ **푸시 후 1-2분 안에 라이브 반영** (Pages CDN + Notion API)
- ✅ **Notion 비고 컬럼의 "🌐 HTML 보기" / "📄 PDF 다운로드" 클릭 → 즉시 열림**

---

## 콘텐츠 타입 3종

이 스킬은 광교바른내과 모든 환자 콘텐츠를 단일 디자인 시스템과 단일 빌드 파이프라인으로 생산한다:

| 타입 | 디렉터리 | 페이지 포맷 | 용도 | 마무리 QR 위치 |
|---|---|---|---|---|
| **decks** | `decks/{specialty}/{topic}/{slug}/` | 16:9 1280×720, 12장 | 진료실 환자 설명, 카톡 공유, 노션 임베드 | closing slide (`.qr-block__code`) |
| **handouts** | `handouts/{specialty}/{slug}/` | A4 세로, 1장 | 진료실 비치, 환자 인쇄물 | footer mini-QR (`.qr-mini__code`) |
| **lab-reports** | `lab-reports/{topic}/{hash10}/` | A4 세로, 1장 | 검사 결과 시각화, 환자 설명 첨부 | **QR 없음 (개인정보 보호)** |

요청 키워드별 자동 라우팅:
- "환자 교육 슬라이드", "질환 안내 PPT", "12장 자료" → **decks/**
- "유인물", "비치용 안내문", "주의사항 PDF", "A4 한 장" → **handouts/**
- "검사 결과지 인포그래픽", "결과지 시각화", "혈액검사 PPT/PDF" → **lab-reports/**

## Notion DB 라우팅 — 콘텐츠 타입별 3개 DB

광교바른내과 노션에는 **3개의 분리된 DB**가 있고, 각 콘텐츠 타입은 정확히 한 DB에 자동 라우팅된다 (`build.py`의 `kind` 필드 기반).

### 분류 정의 (원장님 정의 — 변경 금지)

| 콘텐츠 타입 | 분류 정의 | 환자별? |
|---|---|---|
| **진료설명용 자료** (decks) | 진료 시 사용할 PPT 슬라이드 형태의 자료. 환자별이 아닌 일반 교육용 라이브러리. | ❌ |
| **검사결과** (lab-reports) | 환자의 혈액검사 결과 관련, 개인 설명용 결과지. **노션 페이지에 환자 이름 + 차트번호 필수 기록**. | ✅ |
| **유인물** (handouts) | 한 장 혹은 두 장짜리 세로/가로의 간략한 정보 공유용 자료. 검사결과 없음 → 특정 환자 국한 X. | ❌ |

### Notion DB ID 매핑

| `kind` | DB | DB ID | Data Source ID | Title 속성 |
|---|---|---|---|---|
| `decks` | 📋 진료 설명용 자료 | `a84f23489df54e8fbe34b9818d6109e5` | (다중 데이터소스) | `자료명` |
| `handouts` | 📨 환자 유인물 | `920b48c92d674186a370afcaa81ce788` | `004eba40-f13b-404f-a045-c9eb82f31609` | `자료명` |
| `lab-reports` | 🧪 환자 검사결과 | `c150b47d523c45c09108ac716009c49b` | `4923d400-64ce-419f-8408-ef6a42e18d62` | `환자명` |

### lab-reports 필수/선택 메타데이터

**필수**: `patient_name`, `chart_no` — 둘이 합쳐 노션 제목 `[차트번호] 환자명` 자동 생성
**선택**: `exam_date` (검사일 ISO), `doctor` (담당의), `note` (환자명 뒤 부연 — 예: `종합검사 — 콜레스테롤 경계역`)

> **Backward compat**: 기존 lab-reports TARGETS가 `title: "[<차트번호>] <환자명> — <검사명> (YYYY-MM-DD)"` 형식을 사용하면 `_notion_sync.py`가 자동으로 chart_no/patient_name/note를 파싱한다. 신규 항목은 explicit 필드 사용 권장.

### handouts → 📨 환자 유인물 DB 카테고리

`category` 값은 Notion DB select option과 일치시킨다:
- `🏥 내시경 관련` / `💊 투약 안내` / `🩺 시술·처치 후` / `🌿 생활습관·식이` / `🚨 증상별 안내` / `📝 동의서·서식`
- `🫁 위장관` / `🩺 일반내과` / `💊 투약·생활습관`

`audience`: `환자/보호자` / `직원용` / `공용`

### "원클릭" = git push

빌드 + 노션 등록 + Pages 배포 모두 한 번의 `git push`로 자동 실행:

1. 로컬에서 HTML 작성 + `build.py` TARGETS 추가
2. `git pull --rebase && git add . && git commit -m "Add lab-report 969f64d2bc (general-checkup)" && git push`
   (lab-reports 커밋 메시지는 hash slug 만 — 환자명/차트번호 금지, [Gotcha 11])
3. CI(GitHub Actions, ~80초 안에 완료):
   - Playwright PDF 빌드
   - GitHub Pages 배포 → `https://gwanggyo-barun.github.io/patient-education/lab-reports/general-checkup/969f64d2bc/` (hash slug)
   - **kind에 따라 자동 라우팅 → 해당 DB에 행 upsert**
4. 노션에서 환자 페이지 클릭 → 🌐 HTML / 📄 PDF 링크 한 번에 열림 (lab-reports 는 PDF 만, HTML 도 noindex)

## 출력물

세 가지 타입 모두 다음 용도를 단일 산출물로 만족한다:
1. **카톡/문자 공유용 PDF** — 환자에게 링크 또는 파일로 전송
2. **진료실 발표·필기용 PDF** — 굿노트로 불러와 펜으로 강조하며 설명
3. **노션 임베드용 HTML** — GitHub Pages 호스팅 후 클리닉 허브에 임베드

모든 슬라이드는 1280×720 (16:9) 고정 비율. 모바일 반응형은 설계 대상이 아니다.

## 디자인 시스템

색상·폰트·레이아웃·톤 일체는 `reference/brand-design-system.md`를 따른다.
**SKILL 사용 전 반드시 brand-design-system.md를 먼저 읽고 토큰을 확인한다.**

요약:
- 색상: Navy (#003366) 베이스 + Steel Blue (#5B9BD5) 단일 액센트
- 폰트: Pretendard Variable, weight 450/540 활용
- 라디우스: 8px / 16px만
- Hero 그라데이션은 표지 1장에만 적용

## 입력 형식

사용자는 다음과 같이 콘텐츠를 전달한다:

```
[주제명]
대상 환자: [예: 신환 / 재진 / 가족 / 일반]

1. 개요 / Overview
- 한국 유병률, 핵심 통계, 임상적 중요성

2. 정의 / Definition
- 질환의 정의, 주요 기전

3. 증상 또는 진단
- 6가지 정도

4. 위험 요인 / 적응증
- 6가지 정도

5. 치료 / 약물
- 1차, 2차, 3차 또는 약물 조합

6. 생활 관리 / 식이
- 권장 vs 피하기 또는 6가지 항목

7. 경고 증상 / Red Flag
- 즉시 내원이 필요한 경우 6가지

8. 환자 실천 7가지

[근거] ACG / KSGE / 대한 OO 학회 가이드라인
```

콘텐츠 양이 부족하면 Claude가 의학적으로 정확한 일반 정보를 보완 생성한다.
한국 진료 환경(보험 기준, KCD 코드, 한국 가이드라인)을 우선 반영한다.

## 🤖 Multi-Agent Quality Pipeline (필수)

모든 콘텐츠 작성은 **3-stage 멀티 에이전트 파이프라인** 으로 진행한다. 상세 사양은 [`reference/multi-agent-quality.md`](reference/multi-agent-quality.md) — 본 섹션은 trigger·요약.

### 파이프라인 흐름

```
Stage A — Planning            (specialist 병렬, planning 모드)
   ↓
Stage B — Drafting            (integrator 만 파일 수정)
   ↓
Stage C — Deterministic gate  (build.py + _validate_layout + _visual_audit)
   ↓
Stage D — Critique            (specialist 병렬, critique 모드)
   ↓
Stage E — Integrator revision (evidence 기반 fix)
   ↓
Stage F — Final verification + push
```

Stage A·D 만 LLM specialist, Stage C·F 는 결정적 도구, Stage B·E 는 integrator (메인 호출 Claude).

### 콘텐츠 타입별 specialist 라인업 (기본 모드)

| kind | specialist (병렬) |
|---|---|
| `decks` | clinical-accuracy + patient-readability + visual-design + **narrative-flow** = 4 |
| `handouts` | clinical-accuracy + patient-readability + visual-design + **density-hierarchy** = 4 |
| `lab-reports` | clinical-accuracy + patient-readability + visual-design + **data-accuracy** + **privacy-ops** = 5 |

각 specialist 의 상세 프롬프트는 `reference/quality-agents/{name}.md`.

### 모드 (사용자 메시지에서 추정)

| 모드 | trigger 키워드 | Stage D-E max iteration |
|---|---|---|
| 기본 | (명시 없음) | 1 |
| 고품질 | "고품질", "정확하게", "꼼꼼히" | 2 |
| 극한 | "최고 퀄리티", "학회용", "언론용", "심사용" | 3 |

빠른 모드는 없음. `target_audience: "clinician"` 일 때만 patient-readability 자동 skip.

### 모델 호출 룰

- 모델 ID 하드코딩 금지. 호스트 default 또는 *available strongest reasoning model* 사용
- Claude Code 환경: `Agent` 도구 `subagent_type: "general-purpose"` (모델 inherit, Tools: *). `subagent_type: "claude"` 는 FleetView 함대 에이전트 — worktree isolation 강제 → 비-git cwd (예: `/Users/chungjihwan/Documents`) 에서 호출 시 즉시 실패하므로 specialist 호출에 부적합
- 다른 환경 (Codex 등): 그쪽 best reasoning model
- vision 필요 specialist (visual-design) 는 vision 모델 필수 — 미지원이면 그 specialist 자체 skip

### Specialist 산출물 (강제 JSON 스키마)

```json
{
  "agent": "...",
  "stage": "planning" | "critique",
  "findings": [
    {
      "severity": "blocker" | "major" | "minor" | "nit",
      "affected_section": "...",
      "evidence": "...",
      "fix_suggestion": "...",
      "confidence": 0.0
    }
  ],
  "summary": "..."
}
```

Severity 반응:
- `blocker` → 무조건 fix, push 차단
- `major` → 일반적으로 fix (evidence 약하면 reject 가능)
- `minor` → integrator 판단
- `nit` → 기본 reject

충돌 해소 우선순위: **clinical-accuracy > patient-readability > visual-design > 타입별 specialist**. `privacy-ops` 의 blocker 는 절대 우선 (push 차단 권한).

### Logging (PII redact)

매 라운드 critique 결과를 `_local/quality-logs/critique-YYYY-MM-DD.jsonl` 에 *redacted summary + counts 만* 저장 (gitignored). Findings 본문은 저장 안 함. 자세한 redaction 룰은 `reference/multi-agent-quality.md §6`.

도우미: [`tools/quality_gate.py`](tools/quality_gate.py)
- `redact_pii(text)` — 환자명·차트번호·전화번호 등 `[REDACTED-*]` 치환
- `run_deterministic_gate()` — build + validate_layout 묶음 (Stage C/F)
- `roster_for(kind, target_audience)` — kind 별 specialist 목록

### 생성 워크플로우와의 통합

아래 "생성 워크플로우" 의 Step 1 직전·Step 3 직후에 멀티 에이전트 stage 가 끼인다:

```
[Stage A — Planning specialist 병렬 호출] ← integrator 가 Step 1 시작 전 호출
   ↓
Step 1 콘텐츠 분석 (integrator)
Step 2 HTML 작성 (integrator)
Step 3 build + validate_layout + (lab-reports 한정) _visual_audit  ← Stage C
   ↓
[Stage D — Critique specialist 병렬 호출] ← Step 3.5 또는 Step 4 직전
   ↓
[Stage E — integrator fix (blocker / major 우선)]
   ↓
Step 3.5 인포그래픽 자동 제안 (decks / handouts 만)
Step 4 git push (커밋 시 다른 세션 작업물 보호 — 명시적 stage 만)
```

`lab-reports` 는 Step 3.5 가 없으므로 Stage D-E → Step 4 직진.

### eval

- **Dogfooding**: `_local/quality-logs/` 자동 누적 — 실제 작업 분포 측정
- **Synthetic**: `evals/synthetic/` (실환자 데이터 금지) + `python evals/eval_runner.py` — 회귀 검증
- 상세: [`evals/README.md`](evals/README.md)

---

## 생성 워크플로우

**전체 흐름 (decks / handouts)** — 텍스트 초안만 만들고 끝내지 않는다. 다음 2-pass 사이클로 진행한다:

1. **Pass 1 — 초안 빌드** (Step 1 → 2 → 3): 콘텐츠 분석, HTML 작성, 빌드+레이아웃 검증까지. 텍스트와 배치가 일단 확정되는 지점.
2. **인터미션 — 인포그래픽 자동 제안** (Step 3.5): Claude 가 슬라이드/섹션을 훑어 어디에 어떤 인포그래픽이 들어가면 이해도가 올라갈지 판단해, ChatGPT 웹 이미지 생성에 그대로 붙여넣을 영문 프롬프트를 사용자에게 자동으로 제시한다. 사용자가 이미지를 생성해 채팅창에 다시 공유한다.
3. **Pass 2 — 이미지 배치 & 최종화** (Step 3.5 후반 → 4): 받은 이미지를 알맞은 슬롯에 배치 → 재빌드·재검증 → git push (Pages 배포 + Notion DB upsert 자동).

**lab-reports 는 1-pass**. 검사 결과지는 정확한 수치·이름·항목명 시각화가 중심이라 일반 인포그래픽이 들어갈 슬롯이 거의 없다. Step 3.5 를 건너뛰고 Step 1 → 2 → 3 → 4 로 직진한다.

### Step 1 — 콘텐츠 분석 및 패턴 매핑

12장 표준 구성 (`reference/content-template.md` 참조):

| 슬라이드 | 패턴 | 비고 |
|---------|------|------|
| 1. Cover | dark gradient | 표지 |
| 2. Overview / Hero stat | Hero Number | 한국 유병률 등 핵심 숫자 |
| 3. Definition | Asymmetric Split | 정의 + 메트릭 카드 |
| 4. Symptoms / Diagnosis | Density Grid 3×2 | 6항목 |
| 5. Risk Factors / Indications | Density Grid 3×2 | 6항목 |
| 6. Treatment (first-line) | Regimen Tile 또는 Density Grid | 약물 조합 |
| 7. Treatment (salvage) 또는 Comparison | Regimen Tile 또는 Comparison | 2차 치료 또는 DO/DON'T |
| 8. Schedule / Process | Timeline | 4단계 |
| 9. Precautions | Density Grid 2×2 + alert strip | 4항목 + 경고 |
| 10. Side Effects / Red Flags | Density Grid 3×2 (mixed) | 일반 + alert tile 혼합 |
| 11. Action Checklist | Checklist | 7가지 |
| 12. Closing | closing-grid (contact + QR) | 클리닉 정보 + 다시 보기 QR (자동 생성) |

콘텐츠 성격에 따라 위 패턴을 변경 가능. 단, 4-region master grid (header / title-block / body / footer)는 모든 슬라이드에 강제 적용된다.

### Step 2 — HTML 생성

1. `decks/{specialty}/{topic}/{slug}/index.html` 경로에 새 파일 작성
   - 예: `decks/gi/gerd/lifestyle/index.html`, `decks/cardio/htn/lifestyle/index.html`
2. `shared/design-tokens.css`와 `shared/clinic-slides.css`를 link (상대 경로 4단계 위)
3. Pretendard Variable CDN 로드 (jsDelivr)
4. 12개 `<section class="slide">` 작성, 각각 4-region master grid + 본문 패턴 1개
5. 헤더: 좌측 로고(`shared/assets/clinic_logo.png`) + 우측 chapter eyebrow
6. 푸터: 좌측 출처 + 우측 페이지 번호 (NN / 12)
7. OG meta 태그 표준 7개 (`patterns.md §9` 참조): og:type, og:url, og:title, og:description, og:image, og:site_name, theme-color. og:url은 `{BASE_URL}/{slug_path}` 형식 (BASE_URL은 build.py 상수 참조)
8. 마무리 슬라이드의 `<div class="qr-block__code"></div>`는 빈 div로 둔다 — 빌드 스크립트가 Python qrcode로 SVG QR을 자동 생성해 인라인 삽입한다

### Step 3 — 빌드

빌드 명령어와 환경 셋업은 `reference/build.md` 참조. 핵심:

```bash
python build.py
```

산출물:
- `output/{slug}.pdf` — 환자 공유용 PDF (1280×720 페이지)
- `output/{slug}-preview.png` — 데스크톱 풀스크린 미리보기

### Step 3.5 — 인포그래픽 자동 제안 (decks / handouts 전용, lab-reports 제외)

**언제**: 초안 HTML + `build.py` + `_validate_layout` 가 통과한 직후. 텍스트와 레이아웃이 일단 확정된 지점에서 한 번 멈춘다.

**왜**: 환자 교육 자료는 인포그래픽이 들어가면 이해도가 크게 올라간다. 그러나 *어디에 어떤 그림이 들어가야 효과적인지*는 콘텐츠를 다 본 뒤에야 판단할 수 있어, 빌드 후에 후보를 골라 사용자에게 제안한다. 사용자는 받은 영문 프롬프트로 ChatGPT 웹에서 이미지를 생성해 채팅창에 다시 공유하고, Claude 가 알아서 슬롯에 배치한다.

**lab-reports 제외**: 검사 결과지는 정확한 수치·이름 시각화가 핵심 → Step 3.5 건너뛰고 바로 Step 4.

#### 3.5.a — 인포그래픽 후보 식별

작성한 각 슬라이드/섹션을 다음 6 카테고리에 매핑한다. 해당하면 후보, 아니면 패스.

| 카테고리 | 대상 슬라이드/섹션 | 예시 주제 |
|---|---|---|
| **해부도 (Anatomy)** | Definition · Asymmetric Split · 첫 본문 슬라이드 | 갑상선·간·대장·심장·관절 단면 |
| **기전 (Mechanism)** | Definition · Risk Factors | 인슐린 저항성·역류 메커니즘·콜레스테롤 침착 |
| **절차/타임라인 (Process)** | Timeline · Schedule | 내시경 준비 단계·약 복용 시점·정기 검사 주기 |
| **장비/도구 (Equipment)** | Hero · Asymmetric Split | CGM 부착·혈압계·내시경·DXA 장비 |
| **자세/행동 (Action)** | Lifestyle · Density Grid · Checklist | 식판 모델·운동 자세·금연·인슐린 자가 주사 |
| **비교 (Comparison)** | Comparison · DO/DON'T | 정상 vs 비정상 조직·올바른 자세 vs 잘못된 자세 |

**스킵 조건** (이미지가 오히려 노이즈): 순수 숫자(Hero Number 단독), 약물 조합표(Regimen Tile), 7가지 액션 Checklist, 경고 alert strip.

**수량 가이드**: 한 자료당 최소 1개, 보통 2–3개 후보. 12장 deck 도 4개 초과 권장 X (자료가 어수선해짐). 1장 handout 은 1–2개.

#### 3.5.b — 영문 프롬프트 작성 규칙

ChatGPT 웹 / DALL-E 는 한국어 의료 프롬프트를 잘 못 따른다 → **영문**으로 작성한다. 다음 골격을 그대로 채워 출력 (사용자가 복붙해 그대로 쓰도록 ```` ```text ```` 코드블록으로 묶음):

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

채우는 값:

| 토큰 | 값 |
|---|---|
| `{kind}` | `deck slide` (decks) / `A4 portrait handout` (handouts) |
| `{ratio}` | deck Hero/Asymmetric → `4:3` · deck Density 슬롯 → `3:2` · handout hero (가로) → `16:9` · handout 보조 (사각) → `1:1` |
| `{view_angle}` | 해부도/장비 → `isometric 3/4 view` · 자세/행동 → `front view` · 식판/오버헤드 → `overhead top-down view` · 절차 → `side view` |
| `{position}` | Asymmetric Split 우측 → `centered` · Hero → `slightly off-center` · Density 슬롯 → `centered` |
| `{whitespace_zone}` | Asymmetric → `on left and right` · Hero → `above and below` · Density → `on all sides` |

카테고리별 상세 프롬프트 템플릿은 `reference/image-assets.md §Phase 1` 참조.

#### 3.5.c — 사용자에게 제시하는 출력 형식

빌드 통과 메시지 직후, 다음 형식으로 채팅창에 한 번에 정리해 전달한다:

```
📸 인포그래픽 제안 — {topic-slug}

문서 초안이 빌드·검증을 통과했습니다. 다음 위치에 인포그래픽을 추가하면 이해도가 크게 올라갑니다. ChatGPT 웹에서 각 프롬프트로 이미지를 생성하신 뒤 채팅창에 공유해 주십시오. 받는 즉시 알맞은 슬롯에 배치하고 재빌드·푸시합니다.

────────────────────────
### 1. 슬라이드 3 / Definition — 갑상선 해부도
**왜**: 갑상선 위치와 모양은 텍스트만으로 설명하기 어렵다. 한 장의 그림이 가장 빠르다.
**슬롯**: `.ai-visual--hero` (Asymmetric Split 우측, 4:3)
**저장 파일명**: `shared/assets/generated/thyroid-nodule-anatomy.png`

ChatGPT 웹에 복붙:
​```text
Create a clean, patient-friendly medical illustration for a Korean clinic deck slide.
Subject: anatomy of the thyroid gland, butterfly-shaped, located in front of the trachea,
with a simplified neck cross-section showing the relative position of larynx and esophagus.
Style: premium hospital patient education infographic, warm white background,
restrained navy (#003366) and steel-blue (#5B9BD5) accents, soft shadows,
isometric 3/4 view.
Composition: subject centered, with generous whitespace on left and right for HTML label pins.
Do not include any text, letters, numbers, logos, watermarks, or patient information.
Aspect ratio: 4:3.
​```

────────────────────────
### 2. 슬라이드 8 / Schedule — 검사 준비 타임라인 일러스트
...
```

각 항목은 (1) 위치 (2) 왜 필요한지 한 줄 (3) 슬롯 클래스 + aspect ratio (4) 미리 정한 저장 파일명 (5) 복붙용 프롬프트 — 다섯 가지를 항상 포함한다.

#### 3.5.d — 이미지 수령 후 처리 (Pass 2 시작)

사용자가 이미지를 채팅창에 공유하면:

1. 받은 PNG/WebP/JPEG 를 **제안 시 알려준 파일명 그대로** `shared/assets/generated/{topic-slug}-{slot-key}.png` 에 저장. 이름 임의 변경 금지 (재배치·재생성 추적 위해).
2. 해당 슬라이드/섹션 HTML 의 placeholder (또는 텍스트 카드) 위치에 `.ai-visual` 컴포넌트 삽입. 컴포넌트 변형(`--hero` / `--portrait` / `--compact` / `--contain`)은 3.5.b 에서 정한 슬롯 그대로.
3. `python3 -m shared._validate_layout <html_path>` 재실행 → `OK` 확인.
4. `python3 build.py` 재실행 → PDF/PNG 갱신, `output/{kind}/{slug}-preview.png` 로 시각 점검.
5. Step 4 (git commit + push) 로 진행.

상세 컴포넌트·삽입 예시는 `reference/image-assets.md §HTML 삽입` 참조. 이미지 안에는 텍스트를 절대 넣지 않으며, 라벨·캡션은 모두 HTML `figcaption` / `.ai-visual__pin` 으로 얹는다.

### Step 4 — git push (Pages 배포 + Notion DB upsert 자동)

**원클릭 배포**: Pass 2 까지 끝났으면 git 한 번으로 라이브 사이트 반영 + Notion DB 행 자동 등록까지 모두 처리된다.

```bash
git pull --rebase                           # 다른 머신 변경 먼저 받기
git status --short                           # staged 영역 audit (다른 대화창 잔재 확인)
git add <내가 만든·수정한 파일만 명시적으로>     # 절대 git add . 금지
git status --short                           # 다시 확인 후
git commit -m "Add {topic} ({slug})"
git push
git log -1 --stat                            # 의도한 파일만 들어갔는지 검증
```

CI(GitHub Actions, ~80초):
- Playwright Chromium 으로 최종 PDF 빌드 (인포그래픽 포함)
- GitHub Pages 배포 → `https://gwanggyo-barun.github.io/patient-education/{kind}/{slug_path}/`
- `kind` 에 따라 자동 라우팅 → 해당 Notion DB 에 행 upsert (제목·분류·대상·작성일·HTML/PDF 링크)

Notion DB 매핑은 §"Notion DB 라우팅" 표를 따른다. lab-reports 커밋 메시지에는 환자명·차트번호 금지 — hash slug 만 (`Add lab-report 842acd69b8 (diabetes-screening)`).

## 본문 패턴 7종

상세 HTML 예시는 `reference/patterns.md` 참조:

1. **Hero Number** — 단일 거대 숫자 (좌 5 : 우 4 분할)
2. **Asymmetric Split** — 좌측 statement + 우측 metric cards (좌 11 : 우 9)
3. **Density Grid 3×2** — 6개 동등 카드
4. **Density Grid 2×2** — 4개 카드 (+ optional alert strip)
5. **Comparison** — 네이비 좌측 / 스틸 우측 컬럼
6. **Timeline** — 4단계 노드 + 화살표
7. **Checklist** — 7가지 액션 (2열 grid)
8. **Regimen Tile** — 약물 조합 표 (tile 안에 `tile__regimen` 리스트)

각 패턴의 적합 콘텐츠 유형, HTML 구조, 사용 예시는 `patterns.md`에 정의.

## 검증 워크플로우 (필수 — 빌드/배포 전 반드시 실행)

콘텐츠 작성·수정 후 반드시 레이아웃 검증을 거친다. 자동 검증 도구가 다음을 잡아낸다:

- **page overflow** — `.page` 가 클립되어 콘텐츠가 잘림 (특히 핸드아웃 297mm 초과)
- **section ↔ footer overlap** — body 마지막 섹션이 footer 영역으로 침범 (인쇄 시 텍스트 겹침)
- **element below/right of page** — 카드·타일·표 행이 페이지 bbox 밖으로 나감
- **slide overflow** — deck 슬라이드가 1280×720 안에 안 들어감

### 실행 명령

```bash
# 단일 파일 검증
python -m shared._validate_layout handouts/lifestyle/hypertension-low-salt/index.html

# 전체 검증 (decks/ + handouts/ + lab-reports/ 모든 index.html)
python -m shared._validate_layout
```

exit code 0 → 통과, 1 → 실패 (CI gate에 그대로 사용 가능).

### 자동화 (CI 통합 권장)

`build.py`가 PDF 빌드 전에 `_validate_layout.py`를 호출하도록 통합되어 있다.
- 검증 실패 시 빌드 중단 → push 후 GitHub Actions에서 fail
- 로컬 작업 시에도 push 전 위 명령으로 한 번 돌려보면 시간 절약

### 검증 실패 시 대응

| 이슈 | 원인 | 해결 |
|---|---|---|
| `section_overlaps_footer` | body 콘텐츠가 grid 1fr 영역을 넘음 | 섹션 내 카드 항목 줄이기 / 식단·표 카드 통합 / 다음 페이지로 분할 |
| `page_overflow` | A4 297mm를 콘텐츠가 직접 넘김 | 1페이지 가정을 버리고 2페이지로 분할 |
| `element_below_page` | 특정 카드 padding/font 과다 | 그 카드 항목 수 줄이거나 폰트 행간 조정 |
| `slide_overflow` (deck) | 12장 표준에 안 맞는 콘텐츠 | 슬라이드 분할 또는 카드 수 줄임 |

**원칙**: 글자 크기를 줄여 억지로 끼워넣지 않는다. 콘텐츠를 분리하거나 페이지를 추가한다.

---

## 절대 규칙

1. **디자인 토큰 외 색상 추가 금지**. 녹색·파스텔·여러 액센트 색 사용 안 함
2. **표지 외 슬라이드에 그라데이션 배경 적용 금지**
3. **본문 패턴 7종 외 자유 레이아웃 금지** (필요시 `patterns.md`에 새 패턴 정의 후 사용)
4. **모든 슬라이드는 4-region master grid 준수** (header / title-block / body / footer 위치 동일)
5. **폰트는 Pretendard Variable 단일** (다른 폰트 추가 금지)
6. **로고는 텍스트가 아닌 PNG 이미지** (`shared/assets/clinic_logo.png`)
7. **의학 용어 영문 병기** (예: 역류성 식도염 (GERD))
8. **출처 명시** (푸터의 source 영역에 가이드라인명 + 연도)
9. **마무리 슬라이드는 closing-grid 패턴 강제** — contact-card + qr-block. QR은 빌드 시 자동 생성.
10. **OG 메타태그 7종 표준 포함** — 카톡 공유 미리보기 카드 자동 작동을 위해 필수.

## Alert(붉은 강조) 사용 룰

디자인 컨셉은 Navy + Steel Blue 베이스. 붉은 alert(`tile--alert`, `alert-row`, `alert-strip`, `card--warning`)는 **소량 액센트**로만 쓴다. 과용하면 "응급실 게시판" 처럼 보여 Navy 베이스 톤이 흐려진다.

**룰**:
- **한 슬라이드 안에서 alert tile은 0개 또는 최대 2개**. 6개 모두 alert 같은 패턴은 금지.
- **한 deck 에서 alert 비중 ≤ 15%** (12 슬라이드 기준 alert-heavy 슬라이드 1-2개 이하).
- **여러 항목이 모두 critical 인 경우 (예: 6대 fatal causes)**: 카드는 기본 tile로 두고, 슬라이드 제목·subtitle·chapter eyebrow에서 위급함을 표현. 카드까지 모두 alert로 도색하지 않는다.
- **alert-stack 패턴**은 "응급 신호 / 즉시 119" 같은 명시적 emergency 슬라이드에서만 1회 사용. 슬라이드 안에 alert-row 5개 이상 늘어놓지 않는다 (3-4개로 압축).
- **handout / lab-report**도 동일 — `card--warning` 1-2개 + 나머지 기본 카드. DO/DON'T 의 DON'T 한쪽만 warning 톤이 표준.
- **잘된 예시**: chest-pain deck slide 4 — "즉시 응급실 가야 하는 6대 치명적 원인" 제목으로 위급 표현, 6 카드는 Navy 라벨 + 흰 배경 기본 tile.

## 검증

빌드 후 확인:
- 헤더 로고와 chapter eyebrow가 12장 모두 같은 위치인가
- 타이틀과 부제가 12장 모두 같은 위치인가
- 푸터의 출처 + 페이지 번호가 12장 모두 같은 위치인가
- 표지 외 슬라이드에 그라데이션 배경이 없는가
- 색상이 디자인 토큰 외 추가되지 않았는가
- Pretendard Variable이 정상 로드됐는가 (CDN 차단 환경 확인)


## 기존 덱 수정 워크플로우

생성된 덱은 PPTX와 달리 PowerPoint에서 직접 편집하는 방식이 아니다. HTML 소스를 수정하고 다시 빌드한다. 다음 두 가지 길 중 하나를 사용한다.

### 길 A — Claude에게 자연어로 수정 요청 (권장)

원장님이 자연어로 수정 사항을 지시하면 Claude가 해당 HTML 파일을 수정하고 다시 빌드한다. 이 방식의 장점은 디자인 시스템이 자동으로 보장된다는 점이다 — 카드 구조, 색상, 폰트, 위치가 그대로 유지되고 콘텐츠만 정확히 바뀐다.

수정 요청 예시:

```
"GERD 슬라이드 4번에서 '야간 흉통' 카드를 '야간 호흡곤란'으로 바꿔줘"
"슬라이드 7 약물 치료에서 P-CAB 카드를 PREFERRED로 표시해줘"
"슬라이드 11 체크리스트에 8번 항목으로 '식이섬유 충분히 섭취' 추가"
"표지 부제를 '진단부터 재검사까지 한눈에'로 바꿔줘"
"슬라이드 10 부작용에 '관절통' 카드 추가"
"슬라이드 6과 7의 순서를 바꿔줘"
"전체적으로 출처 라인을 ACG 2024 가이드라인으로 업데이트"
```

이런 요청을 받으면 Claude는:

1. 해당 덱의 `decks/{specialty}/{topic}/{slug}/index.html` 파일을 view 또는 read한다
2. 수정 사항이 디자인 시스템(`reference/brand-design-system.md`)을 위반하지 않는지 확인한다
3. `str_replace`로 정확한 부분만 수정한다 (전체 재작성하지 않는다)
4. `python build.py` 실행해서 새 PDF 생성
5. 변경된 슬라이드의 PDF 페이지를 추출해서 시각 검증
6. 결과 PDF와 변경 요약을 사용자에게 전달

수정 요청 시 권장 표현 형식:

- **위치 명시**: "슬라이드 N의 ..." 또는 "슬라이드 제목이 'XYZ'인 곳에서..."
- **변경 대상 명시**: 카드 인덱스(`FACTOR · 02`), 카드 제목, 본문 일부 등
- **변경 후 내용**: 정확히 어떤 텍스트로 또는 어떤 패턴으로

### 길 B — HTML 직접 편집

빠른 오타 수정이나 한두 단어 변경 시 사용자가 직접 HTML 파일을 편집할 수 있다. VSCode, Sublime, 또는 텍스트 에디터로 `decks/{specialty}/{topic}/{slug}/index.html`을 열고 텍스트만 수정한다.

```html
<!-- 이런 구조에서 -->
<div class="tile">
  <div class="tile__index">FACTOR · 01</div>      <!-- 라벨 (수정 가능) -->
  <div class="tile__title">체중 · 복압</div>        <!-- 제목 (수정 가능) -->
  <div class="tile__body">비만, 복부 비만...</div>  <!-- 본문 (수정 가능) -->
</div>
<!-- div class="..." 같은 태그는 건드리지 않는다 -->
```

수정 후:
```bash
python build.py
```

### 변경 추적 (권장)

덱 라이브러리는 git 저장소로 관리하시는 것을 권장한다:

```bash
git add decks/gi/gerd/lifestyle/
git commit -m "Update GERD: alarm symptoms revised per ACG 2024"
```

이렇게 하면 수정 이력이 자동 추적되고, 잘못 수정했을 때 `git checkout`으로 이전 버전으로 되돌릴 수 있다. PPTX 시절 `_v1`, `_v2`, `_final` 붙여가며 파일 관리하던 부담이 사라진다.

### 수정 시 주의

다음은 수정하지 않는다 (디자인 시스템이 깨진다):

- ❌ `<div class="tile">`의 클래스 이름 변경
- ❌ 슬라이드의 `<header>`, `.slide__title-block`, `.slide__body`, `<footer>` 구조 변경
- ❌ 색상 인라인 스타일 추가 (style 속성에 임의 색상 코드 입력)
- ❌ 새 폰트 link 추가
- ❌ 7가지 본문 패턴 외 자유 레이아웃 추가

이런 변경이 필요하면 먼저 `reference/brand-design-system.md`와 `reference/patterns.md`를 갱신한 다음 적용한다.

### 환자별 즉석 변경

진료실에서 특정 환자에게만 추가 강조나 메모가 필요한 경우, HTML 자체를 수정하지 않는다. 대신:

- 굿노트로 PDF 위에 펜으로 표시
- 또는 Markdown 메모를 별도 첨부

원본 덱은 일반적인 환자 교육용으로 유지한다.


## A4 세로 1장 콘텐츠 (handouts / lab-reports)

A4 세로 단일 페이지 콘텐츠는 16:9 덱과 다른 마스터 그리드를 사용한다. 자세한 컴포넌트 사양은 `shared/clinic-handout-a4.css` 참조.

### A4 페이지 마스터 (4-region grid)

```
.page (210mm × 297mm)
 ├─ .page__header        — 좌측 로고, 우측 eyebrow ("PATIENT HANDOUT · GASTROENTEROLOGY")
 ├─ .page__title-block   — 제목 + 부제
 ├─ .page__body          — 콘텐츠 영역 (flex column, gap 5mm)
 └─ .page__footer        — 좌측 클리닉 정보 + 면책 / 우측 mini QR (.qr-mini__code)
```

### 사용 가능한 컴포넌트

`shared/clinic-handout-a4.css`에 정의된 재사용 가능 블록:

- `.section-heading` — 좌측 Steel Blue 바 + Navy 제목 (12pt)
- `.card` (기본 / `--accent` 크림 / `--warning` 주황 / `--navy` 다크)
- `.checklist` — 번호 동그라미 + 텍스트 (타임라인·실천 항목)
- `.body-2col` — 2열 그리드 (권장 vs 금지, 의미 vs 권장 등)
- `.ai-visual` + `--hero`/`--portrait`/`--compact` — OpenAI 생성 이미지 삽입 프레임
- `.stats-row` + `.stat-cell` (`--ok`/`--high`/`--low`) — 검사 수치 한눈에
- `.lab-row` + `.lab-row__badge` — 항목별 결과/참고치/판정
- `.disclaimer` — footer 하단 작은 면책 문구

### A4 콘텐츠 작성 규칙

1. `handouts/{specialty}/{slug}/index.html` 또는 `lab-reports/{topic}/{hash10}/index.html` 경로 (lab-reports 는 환자명 대신 hash, [Gotcha 11] 참조)
2. CSS 링크 두 개: `../../../shared/design-tokens.css` + `../../../shared/clinic-handout-a4.css`
3. 로고 경로: `../../../shared/assets/clinic_logo.png`
4. **handouts**: footer의 `<div class="qr-mini__code"></div>`는 빈 div로 둔다 — 빌드 스크립트가 자동 주입
   **lab-reports**: footer 의 `<div class="qr-mini">…</div>` 통째 생략 가능 (있어도 build 가 strip). QR 없는 footer 는 좌측 클리닉 정보만 표시.
5. OG meta 7개(og:type/url/title/description/image/site_name + theme-color) 모두 head에 작성. og:url은 `{BASE_URL}/{slug_path}/` 형식. **빌드 시 자동 검증된다.**

### AI 이미지 자산 사용

핸드아웃/검사 결과지 퀄리티 보강이 필요하면 **원장님이 ChatGPT 웹에서 생성해 고른 이미지**를 제공하고, 에이전트가 파일 배치·HTML 삽입·레이아웃 검증을 맡는 흐름을 기본으로 한다. API 직접 생성은 자동 대량 생성이 필요할 때만 선택한다.

표준 처리 순서:

1. 전달받은 PNG/WebP/JPEG를 `shared/assets/generated/{topic-slug}.png`처럼 의미 있는 파일명으로 저장
2. HTML에는 `.ai-visual` / `.ai-visual--hero` / `.ai-visual--portrait` / `.ai-visual--compact` 중 가장 맞는 프레임으로 삽입
3. 이미지 안의 글자는 쓰지 않고, 라벨·캡션·설명은 HTML 텍스트로 배치
4. `python3 -m shared._validate_layout <html_path>` 실행
5. 필요 시 `python3 build.py` 후 `output/{kind}/{slug}-preview.png`를 직접 확인

HTML 예시:

```html
<figure class="ai-visual ai-visual--hero">
  <img class="ai-visual__image" src="../../../shared/assets/generated/thyroid-ultrasound.png" alt="갑상선 초음파 검사 설명 일러스트">
  <figcaption class="ai-visual__caption">라벨과 설명은 HTML 텍스트로 얹는다</figcaption>
</figure>
```

규칙: 이미지 프롬프트나 파일명에 환자명/차트번호/생년월일/원본 검사 PDF를 넣지 않는다. 이미지 안의 한글 텍스트는 피하고, 모든 라벨은 HTML로 처리한다. 자세한 절차는 `reference/image-assets.md`.

로컬 API 생성이 필요한 경우:

```bash
python3 tools/generate_image_asset.py \
  --prompt "A friendly thyroid ultrasound exam illustration with a simplified thyroid anatomy inset and empty areas for HTML labels." \
  --output shared/assets/generated/thyroid-ultrasound.png \
  --size 1536x1024 \
  --quality medium
```

### 페이지 분량 결정 (handouts + lab-reports 공통 — 무조건 1페이지 기본)

**🔑 절대 원칙 — 핸드아웃·검사결과 페이지 모두 동일**:

1. **기본은 무조건 1페이지.** 핸드아웃이든 검사결과 페이지든 1페이지를 우선 시도.
2. **1페이지에 무리하게 욱여넣지 말 것.** 글자 크기를 줄이거나 카드 padding을 짜내서 한 장에 끼워 넣는 행동 금지.
3. **텍스트 겹침은 절대 금지.** body 섹션이 footer 영역으로 침범하거나 카드끼리 겹치면 즉시 콘텐츠 조정.
4. **1페이지가 정말 무리일 때만 2페이지로 확장.** 무조건 2페이지 만들지 않는다. 콘텐츠가 1페이지 안에 안전하게 들어가지 않을 때만 확장.
5. **2페이지 확장 시에도 적절히 배치.** 1페이지에 핵심, 2페이지에 상세 — 각 페이지가 시각적으로 균형 있어야.

**의사결정 트리**:

```
[콘텐츠 작성 후 검증]
        ↓
1페이지에 다 들어가는가? (검증기 OK + 시각적 여백 한쪽 쏠림 없음)
        ↓
   ┌─ YES → 1페이지로 확정 (표준 케이스)
   │
   └─ NO ┐
         ↓
      어떤 종류의 NO인가?
        ├─ 콘텐츠가 부족해서 빈 여백 큼
        │  → 콘텐츠 보강 (핵심 수치, 기전, 예시 추가) → 1페이지 유지
        │
        ├─ 콘텐츠 약간 많아서 살짝 overflow / footer 겹침
        │  → 항목 1-2개 컴팩트화 (3-card → 통합 1-card 등) → 1페이지 유지
        │  → 폰트 줄여서 끼워넣지 말 것
        │
        └─ 콘텐츠가 진짜 많아서 1페이지로는 무리
           → 2페이지로 확장 (1장: 핵심 / 2장: 상세)
           → 단, 폰트는 12pt 이상 유지
           → 두 페이지 모두 균형 있게 배치 (1페이지만 가득, 2페이지 텅텅 X)
```

**검증 룰**: 작성 후 `python -m shared._validate_layout <html_path>` → `OK` 받기 전에는 끝나지 않은 작업이다. 검증기가 잡는 issue:
- `section_overlaps_footer` → 1페이지 안에서 항목 줄이거나 2페이지로 확장
- `page_overflow` → 콘텐츠 분할 (절대 폰트 줄이지 말 것)
- `element_below_page` / `element_right_of_page` → 카드 padding 또는 항목 수 조정

### 여백·균형 룰

1. **여백 한쪽 쏠림 금지**: body 영역이 vertical로 골고루 채워져야 한다. 위쪽으로 콘텐츠가 몰리고 footer 위가 텅 비는 결과를 피한다. CSS가 `justify-content: space-between` + 섹션 `flex: 1`로 균등 분배하도록 설정되어 있으나, 콘텐츠 자체가 부족하면 시각적으로 비어 보일 수 있으므로 콘텐츠 양을 우선 보강.
2. **카드별 정보 밀도**: 카드 1개당 본문 텍스트 최소 3줄 또는 리스트 4항목 이상. 한 줄짜리 카드는 피하고, 어쩔 수 없이 짧다면 카드 안에 부가 정보(단위·예시·근거)를 함께 표시.
3. **2열 레이아웃의 균형**: `.body-2col`을 쓸 때 좌우 카드 항목 수가 ±1 이내여야 한다 (5 vs 5, 6 vs 5 OK / 5 vs 2 NG).
4. **섹션 간 위계**: 첫 섹션은 핵심 수치/타깃 카드, 마지막 섹션은 실천 팁 또는 경고. 중간에 main content (DO/DON'T, 체크리스트, 표).

### 2페이지 핸드아웃 작성법

콘텐츠가 정말 많아서 2페이지 가는 경우:

```html
<body>
  <div class="page">
    <!-- 1페이지: header + title + body(핵심) + footer(QR 포함) -->
  </div>
  <div class="page">
    <!-- 2페이지: header(약식) + body(상세) + footer(축약, QR 생략 또는 1페이지에만) -->
  </div>
</body>
```

- 두 페이지 모두 같은 CSS 사용 (자동 page-break)
- QR 코드는 1페이지 footer에만 (한 번 스캔으로 충분)
- 2페이지 footer는 출처/면책만 짧게
- 2페이지 분량은 1페이지의 60-100% 사이가 적정 (너무 짧으면 1페이지 보강이 답)

### 콘텐츠 부족할 때 보강 패턴

저염식·식이 가이드 같은 자료는 `핵심 수치 한 줄 + DO/DON'T 5×5` 만으론 1장이 비어 보인다. 다음을 보강:

- **핵심 수치를 stats-row로 확장**: 단일 숫자 → 3-4개 통계 (목표값 / 현재 한국인 평균 / 감소량 / 효과)
- **식품 mg/kcal 수치**: "젓갈 피하기" → "젓갈 1큰술 = 1,200mg Na (일일 60%)"
- **실천 시나리오**: 아침/점심/저녁 식단 예시
- **체크리스트 추가**: 외식 시 7가지 체크포인트
- **시각적 비교**: navy card vs warning card 대비 강조

### 통합 빌드

`build.py`의 `TARGETS` 리스트에 새 항목 추가:

```python
TARGETS = [
    # 기존 항목들...
    ("handouts", "{slug}", "handouts/{specialty}/{slug}/",
     ROOT / "handouts/{specialty}/{slug}/index.html",
     "qr-mini__code", "a4-portrait"),
]
```

`python build.py` 실행 시 4개 타깃(현재) 모두 일괄 빌드되며, 각 출력은:
- `output/decks/{slug}.{pdf,png}` — 16:9 덱
- `output/handouts/{slug}.{pdf,png}` — A4 핸드아웃
- `output/lab-reports/{slug}.{pdf,png}` — A4 랩리포트


## 디렉토리 구조

```
clinic-content-system/
├── SKILL.md                          # 이 파일
├── README.md
├── HANDOFF.md
├── build.py                          # 통합 빌드 (3개 타입 모두)
│
├── shared/                           # 모든 콘텐츠 공유
│   ├── design-tokens.css             # 색상/폰트/스페이싱 변수 (단일 진실)
│   ├── clinic-slides.css             # 16:9 덱 전용 컴포넌트
│   ├── clinic-handout-a4.css         # A4 1장 전용 컴포넌트
│   ├── _build_helpers.py             # QR SVG 생성, OG meta 검증 헬퍼
│   └── assets/
│       └── clinic_logo.png
│
├── decks/                            # 16:9 멀티슬라이드 덱
│   └── gi/
│       ├── gerd/lifestyle/index.html
│       └── h-pylori/eradication/index.html
│
├── handouts/                         # A4 1장 진료실 핸드아웃
│   └── gi/
│       └── colonoscopy/index.html
│
├── lab-reports/                      # A4 1장 검사 결과 인포그래픽
│   └── lipid-panel/sample/index.html
│
└── reference/
    ├── brand-design-system.md        # 단일 진실의 원천 (모든 스킬 공유)
    ├── patterns.md                   # 16:9 덱 7가지 본문 패턴
    ├── content-template.md           # 12장 표준 구성
    ├── input-template.md
    ├── build.md                      # 빌드 환경 셋업
    └── migration.md                  # 기존 PPTX 스킬에서 마이그레이션
```


## 참고 문서

- `reference/brand-design-system.md` — 색상/폰트/톤 단일 진실의 원천 (모든 스킬 공유)
- `reference/patterns.md` — 16:9 덱 7가지 본문 패턴의 HTML 사양과 사용 가이드
- `reference/content-template.md` — 16:9 덱 12장 표준 구성과 슬라이드별 콘텐츠 가이드
- `reference/build.md` — Playwright 빌드 환경 셋업과 명령어
- `reference/migration.md` — 기존 PPTX 스킬에서 마이그레이션 가이드
- `shared/clinic-handout-a4.css` — A4 1장 컴포넌트 사양 (handouts / lab-reports)
