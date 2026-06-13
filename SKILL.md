---
name: clinic-content-system
description: >
  광교바른내과 통합 환자 교육 콘텐츠 생성 스킬 (HTML + PDF). 세 가지 콘텐츠 타입을
  단일 디자인 시스템·단일 빌드 파이프라인으로 생산한다: (1) 16:9 멀티슬라이드 환자
  교육 덱, (2) A4 세로 1장 진료실 핸드아웃, (3) A4 세로 1장 검사 결과 인포그래픽.
  공통 인프라: Navy #003366 + Steel Blue #5B9BD5, Pretendard Variable, Python qrcode
  SVG 자동 QR 생성, OG meta 7개 head 등록. 사용자가 "환자 교육 슬라이드/PDF",
  "유인물 만들어줘", "주의사항 PDF", "비치용 안내문", "검사 결과지 인포그래픽",
  "결과지 시각화", "종합검진 결과지", "건강검진 결과", "검진 결과지",
  "위/대장 내시경 + 초음파 + 혈액검사 종합", "경동맥/갑상선/상복부 초음파 결과",
  "심전도/골밀도 포함 검진 결과", "텍스트/PDF/캡쳐로 검사결과지 생성",
  "환자한테 보낼 자료", "카톡으로 보낼 자료" 등을 만들어 달라고
  할 때 트리거된다. 특히 `lab-reports/health-checkup` 모드는 환자별로 시행
  검사가 다른 종합 건강검진 결과지를 1~3페이지 HTML/PDF로 만든다.
  기존 patient-education-pptx, patient-handout-pdf,
  lab-report-infographic 세 스킬의 HTML 통합 후속 버전이며, PPTX가 명시적으로
  요구되지 않는 한 이 스킬을 우선 사용한다.
---

# Clinic Content System — Unified Patient Content (HTML + PDF)

> **📌 정비 노트 — 2026-06-10**: 문서 staleness 정리 라운드. ① 강화된 deck 검증기 규칙(본문 폰트 ≥15px·`body_underfills`>72px·`box_underfill`·`sparse_box`)을 § 검증 워크플로우에 명문화 ② 의료 표기 통일 SoT [`reference/medical-notation-style.md`](reference/medical-notation-style.md) 참조 추가(≥…이상→`≥`, `6.5 %`→`6.5%`, 정량 "X% 감소"→`X% ↓`, `UACR`/지표 `ACR`→`uACR`) ③ Notion DB 자동 등록(Phase 4)이 `build.py`+CI 에서 이미 동작함을 명시(= 완료) ④ 레거시 PPTX 스킬과의 우선순위 한 줄 명확화. 룰 삭제 없이 보강·통합만. (편집 범위: SKILL.md 단독)

## ⭐ 메타 룰 — 스킬 자체의 업데이트는 항상 이 repo 안에 저장 (최우선의 최우선)

**스킬·시스템 룰/사양/워크플로우의 단일 진실의 원천(SoT)은 이 GitHub repo 안의 다음 파일들이다.**

- `SKILL.md` — 핵심 룰·워크플로우·메타 룰
- `reference/*.md` — 상세 가이드 (image-assets, patterns, brand-design-system 등)
- `tools/*.py` — 자동화 도구
- `shared/*.py|*.css` — 공유 헬퍼

**금지**: 머신 종속 위치(예: macOS의 `~/.claude/projects/.../memory/`, Windows의 `%APPDATA%\Claude\...`, 로컬 dotfile 등)에 스킬 룰/사양을 SoT로 저장하지 말 것. 그렇게 하면:
- 다른 머신의 Claude는 그 룰을 영원히 모름 (메모리는 머신별 격리)
- Codex 등 **다른 에이전트는 그 룰을 영원히 모름** (메모리는 Claude 전용)
- repo의 SKILL.md가 옛 룰이면 다른 곳에서 옛 룰로 동작 → 분기 행동

**적용**: 사용자가 "스킬 업데이트해줘" / "이 룰 추가해줘" / "이렇게 바꿔줘" 요청하면 → **첫 행동은 이 repo 안 파일 편집 + git commit + push**. 다른 머신·에이전트는 `git pull --rebase`로 룰을 받는다. 메모리에는 요약/포인터/사용자 개인 선호만 (예: "이 사용자는 이런 톤을 선호한다") — 시스템 룰의 SoT는 항상 repo.

**예외**: 사용자 개인 선호(톤, 호출명, 우선순위 등 사용자 자체의 속성)는 메모리에 두는 게 맞음 — 다른 머신에서도 같은 사용자라 같은 선호 적용. 단 "스킬이 어떻게 동작해야 한다"는 시스템 룰은 무조건 repo.

이 룰은 향후 모든 스킬 업데이트 요청에 자동 적용. 사용자가 매번 알려줄 필요 없음.

---

## 🔒 무조건 규칙 — Cross-Machine Consistency (최우선)

**원장님은 머신 2~3개를 사용한다. 이 스킬의 모든 업데이트(SKILL.md, build.py, `_notion_sync.py`, reference/, shared/, 모든 콘텐츠 파일 포함)는 머신이 바뀌어도 동일한 결과가 나오도록 작성해야 한다. 절대 예외 없음.**

### 모든 변경에 적용되는 체크리스트

1. ✅ **표준 워킹 디렉토리 `~/clinic-content-system/`에서만 작업** — 플러그인 폴더 직접 편집 금지
2. ✅ **머신 종속 경로 하드코딩 금지** — `C:\Users\user\...`, `/Users/도현/...` 같은 절대 경로 금지. `~/`, `Path(__file__).parent`, 환경변수 사용
3. ✅ **시크릿은 환경변수 / GitHub Secret으로** — `NOTION_TOKEN` 같은 토큰을 코드에 직접 쓰지 않음
4. ✅ **fresh clone에서 동작 검증** — 새 머신에서 README의 3개 명령(`gh auth` → `git clone` → `pip install -r requirements.txt`)만으로 빌드되어야 함
5. ✅ **변경 전 `git pull --rebase`, 변경 후 명시적 stage → audit → commit/push 가능한 상태로 정리** — 다른 머신과의 충돌 방지 + 즉시 전파. 한 작업 = (pull) - 작업 - (push 준비)
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
- **변경 작업 끝에는 명시적 stage/audit 후 commit/push 또는 사용자 승인 요청까지 처리**. 호스트 정책이 자동 commit/push를 금지하면 변경 범위와 검증 결과를 요약하고 승인을 받는다.
- decks/handouts 추가 시 동일 — 커밋 메시지에 주제 명시
- **사용자가 슬라이드/자료를 만들고 "검수 후 올려줘", "올려줘", "노션에 올려줘", "공유되게 해줘"처럼 배포 의도를 말하면 `commit`에서 멈추지 말고 `git push origin main`까지 완료한다.** 이 repo에서 "올리기"는 GitHub Pages 404를 없애기 위한 push까지 포함한다. 단, 사용자가 명시적으로 "푸시하지 마", "커밋만"이라고 했거나, staged 영역에 내 작업 외 파일이 있어 분리 불가능하거나, push가 보호/인증/충돌로 실패하면 즉시 보고하고 필요한 확인을 받는다.
- **lab-reports 커밋 메시지에는 환자명/차트번호 절대 금지** — repo 가 public 이라 git log 가 노출됨. `Add lab-report 842acd69b8 (diabetes-screening)` 처럼 hash 만 쓴다 ([Gotcha 11] 참조)

### 다른 머신에서 SKILL 업데이트 받기 (수신 측 절차)

이 SKILL.md / `reference/` / `shared/` / `tools/` 변경은 GitHub origin/main 에 push되지만, Claude 와 Codex 가 실제로 로드하는 스킬 snapshot 은 각 머신마다 따로 존재한다. push 한 머신 외 다른 머신에서는 **작업 repo + Claude plugin clone + Codex managed mirror** 를 맞춰야 최신 SKILL 이 로드된다.

**터미널이 있으면 (macOS / Linux / Windows Git Bash):**
```bash
# 권장: main + clean 상태에서 한 번에 동기화
cd ~/clinic-content-system
bash tools/sync_all_agents.sh

# 상태만 확인할 때
bash tools/verify_skill_sync.sh
```

`tools/sync_all_agents.sh` 는 dirty tracked change 가 있거나 main 이 아니면 중단한다. 성공 시:
1. `origin/main` 을 fetch + ff-only pull
2. Claude plugin clone 동기화
3. `~/.codex/skills/clinic-content-system` 을 whitelist rsync 로 갱신
4. 4개 위치(origin/main, 작업 repo, Claude plugin clone, Codex mirror)의 HEAD/SKILL.md sha 출력

Codex mirror 는 **스킬 로딩/참조용 read-only snapshot** 이다. 실제 HTML 편집·검증·빌드·커밋은 항상 `~/clinic-content-system/` 에서 한다. symlink 는 사용하지 않는다.

**Claude plugin clone만 수동 동기화해야 할 때:**
```bash
bash ~/clinic-content-system/tools/sync_plugin_clone.sh
```

**터미널 없이 데스크톱 클로드 코드만 쓰는 경우 (예: Windows 데스크톱)**: 그냥 채팅창에 한국어로 **"다른 머신에서 작업했어. 동기화해줘"** 또는 **"clinic-content-system 동기화"** 라고 말하면 클로드가 동기화 명령을 실행한다. (Claude Code 의 Bash 도구가 OS 별 셸을 알아서 사용 — Windows 는 Git Bash, macOS·Linux 는 bash.)

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
python3 -m shared._visual_audit              # all 66 materials
python3 -m shared._visual_audit --kind=decks # decks only
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
2. python3 -c "import sys; sys.path.insert(0,'shared'); from _build_helpers import lab_hash_slug; print(lab_hash_slug('차트번호','환자명','topic'))"
3. lab-reports/{topic}/{hash}/index.html 작성 — qr-mini block 안 넣어도 됨 (있어도 build 가 strip)
4. TARGETS 항목 추가: slug=hash, slug_path=lab-reports/{topic}/{hash}/, html_path=ROOT/.../index.html, patient_name+chart_no 명시
5. 커밋·푸시
```

**남는 위험**: git history 에 옛 환자명 디렉토리 자취가 남는다 (public repo 인 경우 이슈). 완전 제거하려면 `git filter-repo` 또는 BFG 사용 + force-push 필요 — 별도 작업.

### 12. 이미지 슬롯 비율 mismatch — 일반 비율(4:3, 16:9, 1:1) 추천 금지, 슬롯 실측 strict ratio 사용

ChatGPT/DALL-E에 일반 라운드 비율로 이미지를 만들어 받으면, 실제 figure 슬롯 비율과 어긋나서 양옆이나 위아래에 어색한 여백이 생긴다. 이를 CSS `max-width` 강제, `padding` 0 override 같은 hack으로 끼워맞추는 건 미봉책. 매번 다시 발생한다.

**올바른 절차** (§3.5.b 참조):
1. HTML 확정 후 슬롯 폭/높이 mm 측정 (handouts 본문 폭 = 182mm, body-2col = 88mm 등)
2. `ratio = width / height` 소수 둘째 자리까지 산출
3. 프롬프트에 `aspect ratio strictly W:H (px_w x px_h pixels)` 명시
4. `Illustration must SPAN THE ENTIRE CANVAS evenly — no empty side panels` 강제 문구 포함

발견 시점: 2026-05-23 `handouts/screening/cvd-retinal-screening` 작업 중. Flow 4단계 이미지를 `3:1` 일반 비율로 요청했는데 GPT가 `1.78:1`(16:9)에 가깝게 생성. 결국 figure max-width 118mm로 줄여 가운데 정렬하는 hack으로 해결. 정식 룰화.

### 13. Multi-column 비주얼 — 아이콘 위치와 HTML 라벨 grid 정렬 보장

N-column 흐름도/매트릭스(4단계 흐름, 3개 결과 등)의 경우, 이미지 안 아이콘 중심이 HTML 라벨 grid의 column 중심과 정확히 일치해야 시각적 정렬이 깨지지 않는다.

**프롬프트** (§3.5.b.4 참조):
```
4 circular icons of EQUAL SIZE evenly distributed across the canvas width.
Icon CENTER positions must be precisely at:
  • x = 12.5%, x = 37.5%, x = 62.5%, x = 87.5%
```

**HTML**: figure와 라벨 grid 둘 다 동일 `max-width` + `margin:0 auto`로 가운데 정렬. column 폭이 같아야 매칭.

```html
<figure class="ai-visual" style="max-width:118mm; margin:0 auto; ...">…</figure>
<div style="display:grid; grid-template-columns: repeat(4, 1fr); max-width:118mm; margin:0 auto;">…</div>
```

### 14. 이미지에 한글 텍스트 굽지 말 것 — HTML Pretendard 오버레이만

GPT가 생성한 이미지 안 한글 텍스트는 (1) 폰트가 Pretendard 아니라 자료 일관성 깨짐 (2) 저해상도에서 흐림 (3) 오타·수정 시 이미지 재생성 필요. 모든 한글 라벨/캡션/번호는 HTML로 처리.

**프롬프트 마지막 블록 필수**:
```
ABSOLUTELY NO TEXT:
Do NOT include any letters, numbers, words, labels, captions, 
or any characters in any language anywhere on the canvas.
HTML will overlay Korean labels using Pretendard font separately.
```

라벨 배치 옵션: (1) 이미지 아래 grid, (2) 이미지 위 `.ai-visual__pin` absolute, (3) `body-2col` 우측 카드 (일석이조 패턴).

### 15. 이미지 생성 순서 — layout slot 먼저, imagegen raster는 그 다음

핸드아웃/검사결과지/덱에 이미지를 추가할 때는 **절대 이미지를 먼저 만들고 나중에 끼워 맞추지 않는다.** 순서는 항상 다음과 같다.

0. 기존 좋은 이미지 활용 사례를 먼저 비교한다. 슬라이드·핸드아웃·검사 설명 모두 같은 품질 기준을 적용하며, 최소 2개 이상: `handouts/imaging/bone-density-prep`, `handouts/endoscopy/colonoscopy-prep`, `handouts/medication/nasal-spray-allergic-rhinitis`, `handouts/medication/insulin-start`, `handouts/lifestyle/creatine-guide`, `handouts/lifestyle/dyslipidemia-diet`.
1. HTML 레이아웃을 먼저 확정하고, 실제 이미지 슬롯을 만든다. 슬롯은 `.ai-visual` 계열 또는 동급의 큰 figure 영역이어야 하며 `width`, `height`, `aspect-ratio`, `max-width` 중 하나 이상으로 크기가 안정되어야 한다.
2. Playwright 또는 CSS 실측으로 슬롯의 실제 폭·높이를 mm/px 단위로 확인한다.
3. 그 슬롯 비율을 프롬프트에 `aspect ratio strictly W:H (px_w x px_h pixels)`로 명시한 뒤 **built-in `$imagegen`으로 PNG/WebP/JPEG 래스터 이미지를 생성한다.**
4. 생성 결과는 필요하면 슬롯 비율로 crop/resize한 뒤 `shared/assets/generated/`에 저장한다.
5. HTML에 이미지를 배치한 뒤 `_validate_layout`와 preview PNG 육안 검수로 겹침·잘림·여백·그림 자체의 퀄리티를 확인한다.

⛔ **deck 완료 게이트 (2026-06-12, ABYSS 0장 마감 사건 계기)**: 덱은 텍스트만으로 빌드가 통과해도 *초안*이다. §0.a 적합성 게이트를 통과하는 이미지 후보가 4개 이상이면 **이미지 4~6장을 슬롯-우선으로 삽입하기 전까지 "완성"으로 보고하지 않는다.** 적합 후보가 4개 미만일 때만 텍스트 덱으로 마감하되 "이미지 N장 삽입 / 나머지 생략 사유"를 완료 보고에 남긴다. 상세는 `reference/image-assets.md` 최상단 "⛔ 이미지 생성 절대 순서" 참조.

특히 Notion DB나 build target 전체를 대상으로 기존 자료에 이미지를 보강할 때는 **이미지 개수를 채우는 것이 목표가 아니다.** 가독성과 슬라이드/문서 퀄리티가 올라가는 경우에만 추가한다. 로고/QR을 제외한 의미 있는 이미지가 이미 있고 새 이미지가 같은 정보를 반복하면 스킵한다. 이미지가 없는 자료도 내용에 직접 맞는 Anatomy/Mechanism/Process/Equipment/Action/Comparison 후보가 없으면 텍스트 레이아웃을 개선하고 이미지는 넣지 않는다.

슬라이드·핸드아웃·검사 설명 자료 보강에서는 제목 배경, 투명 장식, 범용 장기 배너처럼 구조만 유지하고 분위기만 더하는 이미지를 금지한다. 먼저 본문 안에 `.ai-visual` 또는 자료별 고정 figure 슬롯을 만들고, 그 슬롯이 설명할 문장·표·체크리스트를 정한 뒤 `$imagegen`으로 래스터 이미지를 생성한다. 필요하면 한 장이 아니라 여러 장을 넣어도 되지만, 각 이미지는 서로 다른 행동·절차·장비·비교 포인트를 설명해야 하며 같은 구도나 generic strip 반복은 실패다.

**중요 실패 사례**: decks/handouts/lab-reports 어디에서든 작은 code-native SVG icon strip 또는 context strip을 만들어 넣고 "이미지 추가"로 간주하는 것은 금지한다. 이런 strip은 `imagegen` 래스터 설명 이미지의 대체물이 아니며, 골밀도 검사·대장내시경 준비·비강 스프레이·인슐린 시작 자료 수준의 환자 이해도와 시각 품질을 만들지 못하면 실패다. 코드 네이티브 SVG는 수치 그래프, 단순 로고/아이콘, manifest asset, QR처럼 deterministic vector가 본질인 경우에만 쓴다.

### 16. 이미지 내용 적합성 + 중복 금지

생성 이미지는 장식이 아니라 설명 도구다. 다음을 모두 만족하지 못하면 **생성하지 않거나 제거**한다.

1. **슬라이드/섹션 본문과 직접 연결**: 프롬프트의 subject가 해당 슬라이드/섹션의 제목·핵심 문장·표/카드 내용에서 온 구체적 개념이어야 한다. "medical infographic", "clinic background", "organ-themed banner" 같은 범용 이미지는 실패로 본다.
2. **가독성 향상**: 이미지가 텍스트를 대체하거나 압축해 이해를 돕는 경우에만 사용한다. 제목 뒤 장식, 투명 배경, 분위기용 배너, 작은 SVG icon strip은 가독성 향상으로 보지 않는다. 이미지를 넣느라 본문이 작아지거나 카드 간격이 무너지면 이미지를 버린다.
3. **중복 이미지 금지**: 같은 파일을 재사용하지 않는다. 파일명만 바꾼 동일 구도, 같은 generic strip, 같은 장기 배경 반복도 중복이다. deck/series 검수 시 `placements == unique_assets` 이어야 하고 reused count 는 0 이어야 한다.
4. **프롬프트 추적**: 생성본 옆의 `.prompt.md`에는 slide 번호, slide title, source text summary, visual intent, unique subject, slot size/ratio, negative constraints 를 남긴다.
5. **불확실하면 생략**: 정확히 맞는 그림을 만들 수 없으면 "no image added: reason"으로 기록하고 텍스트 위계·표·아이콘·여백을 개선한다. 이미지 수량 부족은 실패가 아니지만, 무관한 이미지는 실패다.

> ⛔ **v2 게이트화 (2026-06-12)**: 위 1·2·5 항은 handouts 에서 더 이상 주관 판단에 맡기지 않는다 — 슬롯마다 `ImageIntent`(설명할 본문 1개 + visual_type + must_show) 의무 + 생성 이미지의 **aboutness 교차검증**(VLM 0~100, T_about=70 미달 채택 금지)으로 강제하고, `shared/_image_gate.py` 가 기록 정합성을 차단 게이트한다. 상세 절차는 §3.5.a(ImageIntent)·§3.5.e(채택 게이트).

### 20. 박스 안 "핵심 문구 + 설명"은 한 묶음 — 떼어 놓지 말 것 (2026-06-13 진료설명 리뷰)

카드/박스 안의 **제목(핵심 문구)과 바로 아래 작은 설명 글씨는 하나의 의미 단위**다. 이 둘을 `justify-content: space-between` 이나 `.tile__body { margin-top:auto }` 로 박스의 위·아래 끝까지 벌리면, 둘 사이에 큰 빈 여백이 생겨 "제목 따로, 설명 따로"로 읽힌다 (hpylori-overview slides 2·3·5·6·7 사용자 지적: "네모 박스 안의 중심 문구랑 아래 작은 글씨들 사이 여백이 너무 많다").

규칙:
1. **묶음은 타이트하게, 박스 안에서 가운데로** — `.tile`·`.timeline-step` 등 카드는 `justify-content: center`, 본문은 `margin-top:auto` **금지**(간격은 박스 `gap` 8~12px 하나로). ⚠️ **deck-local 로 적용한다 — shared 기본값을 바꾸지 말 것.** `shared/clinic-slides.css` 의 `.tile__body{margin-top:auto}`(본문 바닥 고정으로 채움)를 전역으로 제거하면, 기존 '내용 짧음 + 타일 키 큼' deck 들이 일제히 `body_underfills` **회귀**를 낸다(2026-06-13 `pneumococcal-comparison` s5·s6 확인 → 즉시 revert). 따라서 deck 생성·수정 시 그 deck 안에서만 override 한다. hpylori-overview 가 참조 구현.
2. **§18 의 `space-between` 는 "독립 항목"용** — 표의 행, 나란한 카드들처럼 *서로 다른 항목*을 분배할 때만 쓴다. **한 박스 안의 제목↔설명에는 절대 쓰지 않는다** (이게 §18 과 본 항의 경계).
3. **footer 언더필(`body_underfills`)과 충돌하면 — 제목·설명을 떼지 말고 "박스"를 채운다.** 짧은 콘텐츠를 가운데로 모으면 박스 위·아래에 여백이 남아 `body_underfills` 가 뜬다. 해법: ① 카드는 `min-height`(또는 stretch)로 세로를 채우고 그 **안에서** 콘텐츠를 가운데 정렬, ② hero 숫자 등 단독 강조 요소는 **폰트를 키워** 컬럼을 채움, ③ split 의 metric 2박스는 `flex:1 1 0` 등높이로 컬럼을 채우고 박스 안은 `justify-content:center`. 즉 **"박스는 채우되, 묶음은 박스 가운데"** — "박스 가운데 배치" 와 "footer 까지 채움"을 동시에 만족시킨다.
4. **timeline 화살표**: 카드 사이 간격(`--space-7`) 정중앙에 `right: calc(-1*var(--space-7)); width: var(--space-7); text-align:center` 로 놓고 **steel 색·540 weight** (옅은 border-strong 회색 → 또렷한 steel 로).

deck-local override 예: `decks/gi/hpylori-overview/index.html` 의 `box-spacing fix 2026-06-13` 블록(slide 2 hero 확대+캡션 묶음, 3·11 metric 등높이, 5 timeline `min-height`+가운데, 6·7 tile 가운데+제목 확대).

### 19. deck 폰트·박스·여백은 황금비율 룰을 따른다 (2026-06-06 사용자 컨펌, 코덱스 감수)

비주얼-포커스(좌측 박스 + 우측 큰 이미지) 레이아웃에서 ① 박스가 이미지 높이에 stretch되며 내용이 위로 몰려 아래 30~64% 빈 비대칭 여백 ② 폰트 0.58~0.78rem 과소 ③ 박스가 이미지에 바짝 붙어 겹쳐 보임 — 세 문제를 모듈러 타입 스케일 + 황금비율로 해결한다. **상세 수치는 `reference/deck-design-proportions.md`가 SoT.**

핵심: 박스 본문 16~17px(하한 15)·제목 20~22px·표셀 15~16px(0.58~0.78rem 강제축소 폐기) / 박스 늘릴 땐 `justify-content:center`로 여백 대칭(위몰림 금지), 기본은 내용기반 높이 / 본문:이미지 콘텐츠 의존 분할(표·6카드는 콘텐츠 ≥520px, 기본 0.72:1) + 거터 28~32px / 카드 radius 8~12·border 중심 / 한글 좌측정렬.

**v2 보강 (코덱스 2차 감수):** ① 박스 내용 넘침 금지(`box_content_overflow`, scrollHeight>clientHeight) — 긴 비교값은 폰트 축소보다 라벨/값 분리 ② "대칭이면 OK 아님 — 박스가 콘텐츠 무게와 맞아야". **inner_fill(내용/박스)** ≥55 A방치 / 40~55 B확대(폰트 아닌 패딩·행간·막대·아이콘) / 28~40 C박스축소+중앙배치 / <28 D재설계. 순서 B→C→D ③ 표 4행↑ space-between(행간상한), 2~3행 금지(박스=내용+48~72px) ④ 막대 두께14~20·행44~56·채움50~70% ⑤ 카드2개 높이상한 220~260px·full-height stretch 금지. `_validate_layout`이 `box_underfill`·`box_content_overflow`·`font_too_small`·`content_image_gutter`·`body_underfills`(보이는박스 기준)·`sparse_box`(대칭이나 inner_fill<55%)를 차단/경고. **검증기 통과 ≠ 시각 통과 — Step 3.8 PNG 한장씩 전수 육안 필수.**

### 18. deck 슬라이드는 '보기 좋게' 꽉 채우고, 박스 안 텍스트는 정렬을 맞춘다 (2026-06-06 사용자 지적)

사용자 검수에서 발견된 두 부류의 실패 — 둘 다 _validate_layout 의 신규 체크(`body_overlaps_footer`/`body_underfills`)로 자동 감지된다:

1. **푸터 침범**: stats3 원·visual-strip·closing-grid 등 큰 블록이 본문 높이를 넘겨 footer(출처·페이지번호)를 덮음. → 블록 크기(원 지름·strip height·카드 padding)를 줄여 본문이 footer 위에서 끝나게 한다. 측정: 슬라이드별 `footer.top − 본문최하단 ≥ 0`.
2. **언더필 + 과소 폰트**: 표(table-wrap)·목록(pattern-compare) 등 텍스트 컴포넌트가 `justify-content:center`로 가운데 몰리고 폰트가 작아 위아래 여백이 큼. → ① `justify-content: space-between`/`flex-start`로 펴고 ② 폰트를 키운다(표 셀 ~1rem, 목록 항목 ~1.05rem, 제목 ~1.2rem 수준) ③ 행/항목 padding·line-height를 늘려 슬라이드를 **'꽉'이 아니라 '보기 좋게'** 채운다(footer 위 여백 슬라이드 높이의 9% 이내). ⚠️ **단 `space-between` 은 "독립 항목(표 행·나란한 카드)" 분배에만** — 한 박스 안의 제목↔설명 묶음을 떼는 데 쓰면 안 된다(→ [Gotcha 20]).

**박스 활용 + 정렬**: 텍스트는 가능하면 박스(card/col/tile) 안에 담고, 박스 안에서 라벨·본문의 시작점(좌측 정렬)과 줄간격을 일관되게 맞춘다. 같은 행의 여러 박스는 등높이로(`align-items: stretch` 또는 `height:100%`) 만들어 구분선이 수직이 되게 한다([Gotcha 17]도 같은 맥락).

deck-local override 예: `bepirovirsen-hbv-phase3/index.html` 의 `.slide:nth-of-type(N)` 블록(slide 2·7·8·9·12 교정).

### 17. 수치용 lab-row 를 텍스트 목록 표에 재사용 금지 (2026-06-06 사용자 지적)

`clinic-handout-a4.css`의 `.lab-row` 는 **검사 수치 표** 전용이다 — `lab-row__value { text-align: right }` + 열폭 `1.4fr 0.7fr 1fr auto` (분류 넓게, 수치 좁게)가 숫자 비교에 최적화돼 있다. 이걸 음식 목록·문장형 셀에 그대로 쓰면 **value 가 우측으로 쏠리고 줄바꿈이 삐뚤빼뚤**해진다 (IBS 신호등 표 사고 — 사용자 즉시 지적).

룰: 셀 내용이 숫자/짧은 값이 아니라 **목록·문장이면** deck/handout 로컬 CSS 로 스코프 오버라이드를 만들어 ① `text-align: left` ② 내용 길이에 맞는 열폭 재배분(라벨 좁게, 본문 넓게) ③ `line-height ≥1.4` 를 적용한다. 예: `handouts/lifestyle/ibs-fodmap-diet`의 `.ibs-food-table`.

---

## 🚀 배포 워크플로우 — 모든 머신 공통 (반드시 먼저 읽기)

**Source of Truth**: https://github.com/gwanggyo-barun/patient-education (public)

이 스킬의 **실제 콘텐츠와 빌드 파이프라인**은 위 GitHub 레포에 있다. 스킬 플러그인 폴더(`~/Library/Application Support/Claude/.../skills/clinic-content-system/`)는 머신마다 버전이 다르고 플러그인 업데이트 시 갈아엎힐 수 있으므로, **콘텐츠 작성·수정·빌드는 절대 플러그인 폴더에서 하지 말 것**.

### 표준 워킹 디렉토리 (모든 머신)

```
~/clinic-content-system/
```

이 경로에 GitHub 레포를 clone한 사본이 있어야 한다. 모든 작업(HTML 작성, build.py 수정, 커밋, 푸시)은 여기서 수행.

### 새 머신 1회 세팅 (한 줄 bootstrap)

```bash
gh auth status || gh auth login
git clone https://github.com/gwanggyo-barun/patient-education ~/clinic-content-system
cd ~/clinic-content-system && bash scripts/bootstrap-machine.sh
```

`bootstrap-machine.sh` 가 자동 수행:

1. **Python 의존성** — `pip install -r requirements.txt`
2. **Playwright Chromium** — PDF 렌더링용
3. **매일 fetch LaunchAgent 등록** — 평일 09:00 background `git fetch` (silent). `git pull --rebase` 가 cold network round-trip 없이 즉시 fast-forward 되도록 캐시 워밍 + upstream 변경 조기 가시화. plist 는 `scripts/launchd/io.github.gwanggyo-barun.clinic-content.daily-fetch.plist`, 로그는 `~/Library/Logs/clinic-content-system/daily-fetch.{log,err}`
4. **첫 fetch** — bootstrap 직후 한 번 실행해 캐시 채움

별도 환경변수·시크릿 설정 불필요 (`NOTION_TOKEN`은 레포 GitHub Secret으로 등록되어 있어 CI가 알아서 사용).

**제거 방법** (필요 시):

```bash
launchctl bootout gui/$(id -u)/io.github.gwanggyo-barun.clinic-content.daily-fetch
rm ~/Library/LaunchAgents/io.github.gwanggyo-barun.clinic-content.daily-fetch.plist
```

### 일상 콘텐츠 작성 워크플로우

1. `cd ~/clinic-content-system` (스킬 트리거되면 Claude가 여기로 이동)
2. `git pull` (다른 머신에서 푸시한 것 받기)
3. 새 HTML 작성 — `decks/{specialty}/{topic}/{slug}/index.html` 또는 `handouts/...` 또는 `lab-reports/...`
4. `build.py`의 `TARGETS` 리스트에 새 항목 추가 (kind, slug, slug_path, html_path, qr_class, fmt, **+ Notion 메타: title, category, audience, disease, status**)
5. (선택) 로컬 검증: `python3 build.py` — Playwright 설치되어 있다면
6. `git status --short`로 staged/untracked 상태 audit → 이번 작업 파일만 `git add <file>`로 명시 stage → `git diff --cached --name-only` 재확인 → `git commit` → `git push`
7. CI(GitHub Actions)가 ~1분 20초에 자동 처리:
   - PDF 빌드 (Playwright Chromium)
   - GitHub Pages 배포 (HTML + PDF 라이브)
   - Notion DB 자동 행 upsert (📋 진료 설명용 자료 DB) — ⚠️ `파일링크`(PDF URL) 칸 필수 채움 (2026-06-06 사용자 룰, decks/handouts 빌더에 반영; 빈 칸 발견 시 버그)

### 콘텐츠 삭제 / 보관 / 공유페이지 숨김

Notion에서 행을 직접 휴지통으로 보내면 다음 `build.py` sync 때 `_notion_sync.py`가 같은 DB 안의 같은 제목/환자검사 행을 search로 다시 확인한다. 휴지통 상태(`in_trash`/`archived`)가 감지되면 `skipped_deleted`로 처리하고 새 행을 만들지 않는다.

자료를 삭제하지 않고 공유페이지에서만 숨길 때는 공개/보관 의도를 `build.py`에 기록한다.

```python
{
    "kind": "decks", "slug": "example",
    ...
    "status": ARCHIVED_STATUS,  # Notion 상태 = ⏸️ 보류
}
```

- decks/handouts의 기본값은 `ACTIVE_STATUS` (`✅ 사용중`)이다.
- decks/handouts에서 `status: ARCHIVED_STATUS`는 자료와 링크는 보존하지만 Notion 상태를 `⏸️ 보류`로 유지한다. 공유 페이지의 “사용중 자료만” 뷰에서 숨길 때 이 값을 쓴다.
- `notion_sync: False`는 모든 kind에서 해당 TARGETS 항목을 Notion에 생성/갱신하지 않는다. Notion search로도 삭제 상태를 찾을 수 없는 항목까지 완전히 끊을 때 쓴다.
- lab-reports DB에는 `상태` 속성이 없으므로 `status`를 쓰지 않는다. 필요하면 `notion_sync: False`로 sync를 끄고 행은 수동 정리한다.
- GitHub Pages의 직접 URL까지 없애려면 source HTML 또는 공개 인덱스 카드도 별도 정리해야 한다. Notion 상태는 Notion 공유 페이지 표시만 제어한다.

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

> **레거시 PPTX 스킬과의 관계**: 새 환자 콘텐츠는 **이 스킬(clinic-content-system, HTML+PDF)을 우선** 사용한다. 레거시 `patient-education-pptx` 는 `.pptx` 파일 자체가 명시적으로 필요한 경우(동료 의사 직접 편집·학회 발표 템플릿·외부 협업자에게 .pptx 전달)에만 사용한다.

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

> ✅ **Phase 4 (Notion DB 자동 등록) = 완료.** 노션 행 upsert 는 이미 운영 중이다 — `build.py` 가 `_notion_sync.upsert()` 를 호출하고, `kind` 로 3개 DB 에 자동 라우팅하며, GitHub Actions CI 에 `NOTION_TOKEN` secret 이 등록되어 매 push 마다 자동 실행된다(로컬은 `NOTION_TOKEN` env 설정 시에만). 따라서 별도 수동 노션 생성은 **불필요** — `git push` 한 번이 빌드+Pages 배포+노션 upsert 를 모두 끝낸다(원클릭). 수동 커넥터 작업은 CI 실패/secret 누락 시의 fallback 으로만.

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
2. `git pull --rebase` 후 이번 작업 파일과 `build.py`만 명시적으로 `git add <file>` → `git diff --cached --name-only` audit → `git commit -m "Add {kind} {slug}"` → `git push`
   (lab-reports 커밋 메시지는 hash slug 만 — 환자명/차트번호 금지, [Gotcha 11])
3. CI(GitHub Actions):
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

## 🏥 클리닉 연락처 (SoT — 모든 자료 공통, 머신 무관)

모든 자료의 마무리 슬라이드(decks) · 푸터(handouts / lab-reports) `contact-card` 는
아래 값을 **글자 그대로** 사용한다. 새로 타이핑하지 말고 여기서 복사한다. 이 블록이
유일한 출처(SoT)이며, 값이 바뀌면 **이 표만 고친 뒤 기존 자료를 일괄 갱신**한다. 이
SKILL.md 는 공유 repo(origin/main)에 있으므로 commit·push 하면 모든 머신이 `git pull`
로 동일하게 받는다.

⚠️ **1차 SoT는 `blocks/content/clinic-contact-footer.yaml` (v04)** — 아래 표는 그 요약. 충돌 시 yaml이 이긴다.

| 항목 | 값 |
|---|---|
| 의원명 | 광교바른내과 |
| **진료시간** | **평일(월–금) 08:30~18:30 (점심 13:00~14:00) · 토 08:30~13:30** · 일·공휴일 휴진 |
| 주소 | 경기도 용인시 수지구 광교중앙로 298, 4층 402-404호 |
| 전화 | 031-893-4560 |
| 진료과 | 소화기내과 · 일반내과 · 5대암 검진 |

표준 마크업 — decks closing-grid (한 줄형):
```html
<div class="contact-card__main">평일 08:30~18:30 · 토 08:30~13:30</div>
```
handouts / lab-reports 푸터 (줄바꿈형)도 허용:
```html
<div class="contact-card__value">평일 08:30~18:30<br>토요일 08:30~13:30</div>
```

⚠️ **금지(과거 오류)**: ①`평일 09:00 ~ 18:30` / `토 09:00 ~ 14:00` (2026-05 4개 덱에서 정정) ②**`수요일 오후 휴진` 표기 — 수요일 오후는 부원장 진료로 병원 정상 운영** (2026-06-06 원장 직접 확인; 원장 개인 휴무와 병원 운영시간을 혼동한 v03 yaml·5/29 인계 페이지가 출처였음 — 환자 자료에 절대 사용 금지) ③수원시 영통구·광교중앙로 145·아브뉴프랑·031-217-5878 (옛 오류 주소·전화).

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

## 🚨 사용자 디폴트 워크플로우 (2026-05-24 명시·강제)

**사용자가 "빠르게·간단히·대충" 등 명시하지 않은 한, 모든 deck/handout/lab-report 작성은 다음 워크플로우를 디폴트로 적용한다.** 한 번에 quality 끌어올려 재작업을 줄이는 것이 목표.

### 한 번에 제대로 만드는 5단계

1. **SKILL.md + reference/ 정독 우선** — 워크플로우 시작 전 본 문서 + `reference/multi-agent-quality.md` + `reference/image-assets.md` + `reference/patterns.md` + `reference/agent-orchestration.md` 필수 확인. 단순 generator 또는 5분 작성 금지.

2. **기존 high-quality deck 패턴 학습** — `decks/cardio/htn-2025-aha-acc/index.html` (718줄), `decks/infectious/herpes-zoster/index.html` (785줄) 등 700+줄급 풍부한 deck 한 개 정독해 inline CSS·layout 다양성·정보 밀도 베이스라인 확보.

3. **멀티 에이전트 quality pipeline 호출** — 본 문서 §Multi-Agent Quality Pipeline의 4명 specialist (`clinical-accuracy + patient-readability + visual-design + narrative-flow`) 병렬 호출 필수. Stage A planning + Stage D critique 모두 실행. 모드는 **고품질 (max iteration 2)** 기본.

4. **이미지 자산 적극 활용 (3가지 옵션)**:
   - (a) `shared/assets/generated/` 정독해 **paper 내용과 정확히 매칭되는** 자산만 사용. 키워드만으로 무관 슬라이드 끼워넣기 절대 금지.
   - (b) 매칭 자산 없으면 §3.5.b 룰대로 HTML 슬롯을 만들고 영문 프롬프트 작성 → `$imagegen`으로 직접 생성 → `shared/assets/generated/`에 복사 → 정확한 슬롯 배치.
   - (c) 데이터 시각화(MCID bar, dose-response curve 등)는 **막대 폭이 실제 수치에 비례**해야 함 — 비례 안 맞으면 critique blocker.

5. **풀 quality HTML 작성**: 700+줄 목표, 12장 표준 + 슬라이드별 **다른 layout** (pattern-stats3 / pattern-table / pattern-split / pattern-grid / pattern-timeline / pattern-checklist / mech-flow / takehome-grid 등). 같은 layout은 deck당 **2회 이하**.

### 재작업 유발 금지 사항 (과거 실제 사례)

- ❌ Generator script로 모든 slide 동일 layout 자동 생성 (2026-05-24 v1 작업 — 사용자 컴플레인)
- ❌ 이미지를 키워드 기반 무관 슬라이드에 끼워넣기 (htn-complications를 알도스테론 기전 슬라이드에 — 2026-05-24)
- ❌ 데이터 시각화 막대 폭이 수치에 비례하지 않음 (tramadol MCID bar — 2026-05-24)
- ❌ Trial N·국가 등 핵심 사실 vague 처리 ("약 750명", "한국 미참여" 검증 안 함)
- ❌ TL;DR에 정량 숫자 대신 추상 기호 (↑↑) 사용
- ❌ `pattern-checklist` 같은 layout deck당 3회 이상 반복
- ❌ Mechanism 슬라이드가 efficacy 결과 슬라이드 뒤에 위치 (논문 review 정석은 기전 → 결과)

### /goal 자동 적용 (2026-05-24 사용자 명시 · 2026-05-25 강화)

**모든 deck/handout/lab-report 작성은 자동으로 `/goal` 모드로 진행한다.**

#### 핵심 룰 (2026-05-25 강화)
사용자가 명시적으로 `/goal`을 입력하지 않아도:
- **응답 한 사이클 안에 가능한 모든 단계 일괄 처리** — 작성·빌드·발송·git push·노션 update 모두 끝까지
- 사용자 응답 기다리지 않고 다음 단계 즉시 진행
- 빌드 → critique → 수정 → 재빌드 → 발송 한 사이클 안에 완결
- 멀티 deck 작업 시 deck 하나 완성 즉시 발송 (모아서 X) + 다음 deck 즉시 시작
- 응답 한계에 도달하면 자동으로 백그라운드 빌드 trigger + 다음 deck 작성 + 사용자 응답 시 즉시 다음 deck

#### 대량 작업 (deck 5개 등) 처리 원칙
사용자가 "5개 deck 모두 만들어" 같은 대량 작업 명령 시:
1. **첫 응답에 시작** — 첫 deck 작성·빌드·발송 모두 즉시 처리
2. **사용자 응답 도착 시 다음 deck 즉시** — 한 응답에 1 deck 끝내고 다음 deck 시작 알림
3. **중단 없이 5개까지** — 사용자 추가 명령 없어도 자동 진행
4. **각 deck 완성 직후 PDF 발송** — 모아서 X, 발송 후 다음 작성

#### 시스템 한계 솔직 안내
- ⚠️ **Claude는 응답 사이에 작업하지 않는다** — 시스템 호출 모델. 사용자 응답이 올 때만 호출됨
- ⚠️ 사용자가 자다가 5시간 응답 안 하면 그 5시간 동안 작업 못 함
- ✅ **그러나 호출되면 즉시 끝까지** — 응답이 오면 다음 단계 자동 진행 (사용자 추가 명령 불필요)
- ✅ 사용자 응답이 "고마워" 같은 짧은 거여도 다음 deck 진행
- 진짜 응답 사이 자동화 필요 시: LaunchAgent + Claude API 별도 구축 (외부 시스템)

이는 본 SKILL.md §사용자 디폴트 워크플로우의 일부.

### 진행 보고 룰 (2026-05-24 사용자 명시)

장시간 작업 (deck 5개 동시 작성 등 1시간+) 시 **30분마다 간략한 진행 상황을 텔레그램으로 보고**한다. 형식:

```
🛠️ [HH:MM] 진행 보고
- 완료: deck A·B (이미지 적용 + critique 통과)
- 진행: deck C HTML 작성 중 (~50%)
- 남은: deck D·E + 최종 빌드 + 발송
- 예상 완료: HH:MM
```

사용자가 작업이 진행 중인지 멈췄는지 알 수 있게. 30분 간격 strict.

### 메모리 vs SKILL.md 구분 (다른 머신에서도 적용)

- 시스템 룰 (워크플로우·디자인 시스템·검증 룰) → **본 SKILL.md** (모든 머신 동기화)
- 사용자 개인 선호 (톤·호출명·우선순위) → Claude 메모리 (`~/.claude/.../memory/`)
- 본 디폴트 워크플로우는 **시스템 룰**이라 SKILL.md에 SoT. 다른 머신은 `bash tools/sync_all_agents.sh` 또는 채팅 "동기화" 명령으로 즉시 받음.

---

## 🧠 PromptOps System (2026-05-25 사용자 명시)

콘텐츠 자산을 **재사용·버전관리·브랜드 일관성·회귀 테스트·교차 모델 사용**가능한 시스템으로 운영. 디테일은 [`reference/promptops-system.md`](reference/promptops-system.md) (11개 섹션 — Architecture·YAML Schema·Category Tree·Tags·Reusable Blocks·Tests·Brand Profile·Notion DB·File Structure·Real Examples·Future Expansion).

### 6-Layer Architecture
`Skill → Template → Reusable Blocks → Tests → Assets → Output Archive`

### 핵심 룰
- 모든 새 Skill은 `skills/*.yaml` Master Schema 따름 (§2)
- 재사용 블록 식별·추출 의무 (§5) — 중복 콘텐츠 발견 시 block 분리
- Regression test 필수 (§6) — `must_include`·`forbidden_terms`·`safety_rules`
- Brand Profile YAML 적용 (§7) — `gwanggyo-bareun-print/web/sns-v1`
- 교차 모델 우선순위: Claude Opus > Sonnet > GPT-4o > Gemini

### Phase 1 진행 사항 (현재)
- [x] 본 시스템 설계 완료
- [ ] 5개 Skill YAML 실제 생성 + 테스트
- [ ] 표준 블록 카탈로그 30+
- [ ] Brand Profile 3종 YAML 변환
- [ ] CI/CD 통합

---

## 🔐 Copyright & Asset Protection (2026-05-25 사용자 명시·강제)

광교바른내과 디자인 자산의 저작권 보호·재배포 방지·provenance 관리를 위한 정책. 디테일은 [`reference/copyright-protection.md`](reference/copyright-protection.md). 본 섹션은 핵심 룰·요약.

### 원칙

1. **품질·가독성 절대 우선** — 디자인 품질 저하·환자 가독성 저하·과도한 DRM 금지
2. **현실적 의원급 기준** — Mac+Windows 혼합 환경, Google Drive/NAS 백업 가능
3. **SVG 벡터 워크플로우 유지** — flatten은 외부 배포 export 전용
4. **provenance 우선** — DRM보다 출처·이력 추적이 핵심

### 1. SVG 메타데이터 자동 삽입 (build 단계)

모든 export SVG에 다음 metadata 자동 삽입 (`shared/_build_helpers.inject_copyright_metadata()`):

```xml
<metadata>
  © 2026 Gwanggyo Bareun Internal Medicine.
  Asset-ID: GBIM-{KIND}-{SLUG}-{FMT}
  Version: v{NN}
  Created: {YYYY-MM-DD}
  AI-Assisted: {Yes|No}
  License: Patient education only. Unauthorized redistribution prohibited.
</metadata>
```

- Asset-ID 규칙: `GBIM-{decks|handouts|labreports}-{slug}-{a4|16x9}` 대문자 케밥
- AI-Assisted: Claude/ChatGPT/SD 등 AI 도구 사용 시 Yes (Codex Skill 등 포함)

### 2. Invisible Ownership Mark (PDF/PNG)

배포용 PDF·PNG 하단 4~8px 영역에 자동 삽입:
- 텍스트: `© 2026 광교바른내과 · 무단 수정/재배포 금지` (영문 옵션: `© 2026 Gwanggyo Bareun Internal Medicine · No unauthorized redistribution`)
- 색상: `rgba(0,0,0,0.30)` 회색 (opacity 30%)
- 크기: 8~10px Pretendard
- 위치: 하단 footer 안쪽 또는 footer 미사용 영역

⚠️ **절대 금지**: 중앙 watermark, 환자 가독성 방해, 대각선 워터마크. lab-reports는 가독성 우선 — ownership mark는 footer micro-text로만.

### 3. Master File 보호 구조

```
~/clinic-content-system/
├── 01_Master_SVG/          # 원본 SVG (외부 전달 금지)
│   ├── decks/
│   ├── handouts/
│   └── lab-reports/
├── 02_Export_Print/        # PDF 300DPI (인쇄용)
├── 03_Export_Web/          # WebP/PNG 1920px (웹용)
├── 04_Export_SNS/          # 1080×1080 PNG (SNS 카드)
├── 05_Export_EMR/          # EMR 임베드용 PDF/WebP
├── 06_Export_Kiosk/        # 진료실 키오스크용
├── 07_Prompts/             # AI prompt 보관 (외부 X)
└── 08_LICENSE/             # LICENSE 템플릿
```

- `01_Master_SVG/` 직접 공유 절대 금지
- 외부 전달은 `02~06_Export_*/`의 flatten 파일만
- editable source 제공은 명시 계약 시만
- 파일명 규칙: `GBIM_{topic}_{kind}_{fmt}_v{NN}.{ext}` (예: `GBIM_EGD_Fasting_A4_Print_v03.pdf`)
- ❌ `FINAL_final_v2.svg` 같은 파일명 금지 — v01/v02 체계 강제

### 4. Export 정책 (용도별 분리)

| 용도 | 폴더 | 포맷 | 크기 | DPI | Metadata |
|---|---|---|---|---|---|
| print | `02_Export_Print/` | PDF | A4 또는 16:9 | 300 | Asset-ID·license 풀버전 |
| web | `03_Export_Web/` | WebP | 1920px | 144 | metadata |
| sns | `04_Export_SNS/` | PNG | 1080×1080 | 144 | invisible footer mark |
| emr | `05_Export_EMR/` | PDF | A4 | 200 | metadata |
| kiosk | `06_Export_Kiosk/` | PNG | 1920×1080 | 144 | metadata |

파일명 예시:
- `GBIM_EGD_Fasting_A4_Print_v03.pdf`
- `GBIM_EGD_Fasting_Web_1920_v03.webp`
- `GBIM_EGD_Fasting_SNS_1080_v03.png`
- `GBIM_EGD_Fasting_EMR_A4_v03.pdf`

### 5. LICENSE 자동 동봉

외부 공유 ZIP 생성 시 `tools/pack_for_share.sh`가 자동으로 `LICENSE_KR.txt` + `LICENSE_EN.txt` 동봉.

**LICENSE_KR.txt** (요약):
```
광교바른내과 환자 교육 자료 라이선스

허용:
- 환자 교육 목적 사용
- 진료실 내부 배포·출력
- 환자 직접 전달 (카톡·이메일 포함)

금지:
- 상업적 재판매
- 2차 수정·재가공
- 로고·출처 제거
- 외부 기관·SNS 공식 계정 배포 (사전 승인 필요)
- editable SVG 외부 전달

문의: 광교바른내과 (gwanggyo-barun.github.io)
```

**LICENSE_EN.txt**: 동일 내용 영문판.

### 6. Prompt Provenance (AI 생성 이미지)

AI 도구 사용한 이미지마다 `07_Prompts/{asset-id}_prompt_v{NN}.json` 저장:

```json
{
  "asset_id": "GBIM-handouts-egd-fasting",
  "version": "v03",
  "created": "2026-05-25",
  "model": "ChatGPT GPT-4o (image)",
  "original_prompt": "Clean flat modern medical illustration...",
  "negative_prompt": "no text, no labels...",
  "aspect_ratio": "4:3",
  "export_resolution": "1600x1200",
  "iterations": 3,
  "final_path": "shared/assets/generated/egd-fasting-clock-20260513.png"
}
```

저장 위치: 내부 전용 (`.gitignore`로 외부 push 차단 옵션 검토). 단 metadata 추적용 SHA-256 hash는 SVG metadata에 포함 가능.

### 7. AI-Assisted 표시 정책

- 내부 master SVG metadata: `AI-Assisted: Yes` 유지
- 환자용 최종 PDF/PNG **표면**: 노출 금지 (가독성·신뢰성 보호)
- metadata 레벨만 유지 — 분쟁 시 출처 입증 가능

### 8. Notion 자산 DB 확장 (3 DB 모두)

기존 property에 추가:

| Property | Type | 설명 |
|---|---|---|
| Asset ID | text | `GBIM-{kind}-{slug}-{fmt}` |
| License Type | select | `환자교육-내부` / `환자교육-공개` / `상업 X` / `MIT-with-attribution` |
| External Shared | checkbox | 외부 공유 여부 |
| Master Protected | checkbox | master SVG 보호 정책 적용 |
| AI Assisted | checkbox | AI 도구 사용 여부 |
| Prompt Stored | checkbox | prompt JSON 보관 여부 |
| Export Preset | multi-select | `print` / `web` / `sns` / `emr` / `kiosk` |
| Copyright Embedded | checkbox | metadata·invisible mark 적용 |
| Last Export Date | date | 마지막 export 일자 |

`_notion_sync.py` 자동으로 upsert 시 채움.

### 9. 자동화 (Mac/Windows 혼합)

- **Mac Hazel**: `02_Export_*/` 폴더 watch → 신규 파일 시 NAS rsync 자동 백업
- **Mac Automator**: SVG export 시 metadata 자동 삽입 (build.py 호출)
- **Windows PowerShell**: `tools/Watch-Export.ps1` Hazel 대체
- **Synology Hyper Backup**: `01_Master_SVG/` 매일 야간 백업, 30일 보관
- **rsync**: `tools/sync_to_nas.sh` cron 야간 실행

### 10. 재배포 방지 전략 (현실적)

| 채널 | 정책 |
|---|---|
| editable SVG | 외부 공유 금지 (계약 시만) |
| SNS 게시 | flattened PNG (`04_Export_SNS/`) 우선 |
| 웹사이트 | SVG optimize + metadata 유지 |
| 인쇄 | PDF (`02_Export_Print/`) 300DPI + invisible mark |
| EMR 임베드 | PDF (`05_Export_EMR/`) 200DPI |
| AI prompt | 내부 전용 (`07_Prompts/`), 외부 전달 X |
| 환자 카톡 | PDF/PNG flatten, 메타데이터 유지 |

⚠️ **과도한 DRM 금지** — 환자 접근성·진료실 운영 효율 우선. 분쟁은 metadata·git history로 입증.

### 11. 기존 스킬 대비 변경점 요약

| 영역 | 변경 전 | 변경 후 |
|---|---|---|
| metadata | 없음 | SVG/PDF 자동 삽입 |
| ownership mark | 없음 | invisible footer 자동 |
| 폴더 구조 | output/ 단일 | 01~08 분리 |
| 파일명 | 자유 | `GBIM_*_v{NN}` 규칙 |
| AI prompt | 휘발 | JSON 보관 |
| LICENSE | 없음 | KR/EN 자동 동봉 |
| Notion DB | 기본 | 9 property 추가 |
| 자동화 | 수동 | Hazel·PowerShell·rsync |

---

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
| `lab-reports` (단일 패널) | clinical-accuracy + patient-readability + visual-design + **data-accuracy** + **privacy-ops** = 5 |
| `lab-reports` (`topic=health-checkup`) | 위 5인 + **checkup-extraction** + **checkup-completeness** = 7 (혼합 입력 추출·모듈 누락·follow-up·신호등 일관성 추가 점검) |

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
- `$imagegen` 이 필요한데 주도 에이전트가 Claude 인 경우: `tools/codex_imagen.sh` 로 Codex CLI 를 자동 호출 (driver 감지·fallback·위임 모드는 `reference/agent-orchestration.md`)

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
- `run_deterministic_gate()` — validate_layout 기본, 옵션으로 build/visual audit 포함 (Stage C/F)
- `roster_for(kind, topic, target_audience)` — kind/topic 별 specialist 목록

실행 시 렌더된 specialist prompt (doctor_input, HTML, 검사 수치, preview 경로가 합쳐진 프롬프트) 를 파일로 남겨야 할 경우 **반드시 `_local/quality-prompts/` 또는 `_local/quality-runs/` 아래에만 저장**한다. `reference/quality-agents/` 는 정적 템플릿 전용이며 환자별 입력을 넣지 않는다.

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
Step 3.5 인포그래픽 슬롯 설계 + `$imagegen` 생성 (decks / handouts / lab-reports)
Step 3.8 ⚠️ 푸시 전 전수 육안검수 (2026-06-06 사용자 룰, 강화) — `python3 tools/slide_screens.py <html>` 로 **모든 슬라이드를 한 장씩 캡처해 Read 도구로 한 장 한 장 전부 직접 열어본다** (요약/대표 몇 장만 보는 것 금지). bbox 검사(_validate_layout)만으로 끝내지 않는다. _validate_layout 은 이제 `body_overlaps_footer`(본문이 푸터 침범)·`body_underfills`(푸터 위 9%↑ 빈 여백)도 잡으므로 **먼저 통과시킨 뒤** 육안검수한다. 각 슬라이드에서 확인: ① 푸터/페이지번호 가림 없음 ② 본문이 슬라이드를 보기 좋게 채움(언더필·과여백 없음) ③ 이미지 크롭·라벨 정렬 ④ **박스 안 텍스트 정렬·여백 균형** ([Gotcha 18]). 문제 발견 시 수정→재캡처→재검수. 통과 후에만 Step 4 진행하며, 사용자 추가 지시 없이 커밋·푸시까지 완료한다. **handouts v2**: §3.5.e 의 visual diff 가 회귀를 가리킨 페이지가 있으면 그 페이지부터 우선 육안 확인한다(전수 검수 자체는 유지 — diff 는 우선순위 보조이지 대체가 아니다).
Step 4 git push (커밋 시 다른 세션 작업물 보호 — 명시적 stage 만)
```

`lab-reports` 도 이미지가 필요하면 Step 3.5 를 같은 방식으로 적용한다. 단, 환자 PII·원본 검사 PDF·환자 식별 텍스트는 이미지 프롬프트와 파일명에 절대 넣지 않고, 검사 원리·해부·결과 이해 보조처럼 안전한 설명 이미지로 제한한다.

### eval

- **Dogfooding**: `_local/quality-logs/` 자동 누적 — 실제 작업 분포 측정
- **Synthetic**: `evals/synthetic/` (실환자 데이터 금지) + `python3 evals/eval_runner.py` — 회귀 검증
- 상세: [`evals/README.md`](evals/README.md)

---

## 생성 워크플로우

**전체 흐름 (decks / handouts / lab-reports)** — 텍스트 초안만 만들고 끝내지 않는다. 다음 2-pass 사이클로 진행한다:

1. **Pass 1 — 초안 빌드** (Step 1 → 2 → 3): 콘텐츠 분석, HTML 작성, 빌드+레이아웃 검증까지. 텍스트와 배치가 일단 확정되는 지점.
2. **인터미션 — 인포그래픽 슬롯 설계 + 이미지 생성** (Step 3.5): 주도 에이전트(integrator)가 슬라이드/섹션을 훑어 어디에 어떤 인포그래픽이 들어가면 이해도가 올라갈지 판단하고, HTML 안에 실제 슬롯을 만든 뒤, 슬롯 크기에 맞춘 영문 프롬프트로 이미지를 생성한다. **생성 경로는 driver 자동 감지** — Codex 주도면 built-in `$imagegen` 직접 호출, Claude 주도면 `tools/codex_imagen.sh`로 Codex CLI를 헤드리스 자동 호출(사람 개입 없음), 어느 쪽도 불가하면 이미지 생략+기록 (상세: `reference/agent-orchestration.md`).
3. **Pass 2 — 이미지 배치 & 최종화** (Step 3.5 후반 → 4): 생성 이미지를 `shared/assets/generated/`에 복사, HTML에 삽입, 라벨은 HTML 텍스트로 얹기 → 재빌드·재검증 → git push (Pages 배포 + Notion DB upsert 자동).

**이미지 판단 기준**:
- **품질·가독성 우선**: 이미지 수를 채우지 않는다. 이미지가 슬라이드/문서 이해도를 실제로 높이고 텍스트 위계를 해치지 않을 때만 사용한다.
- **공통 방식**: decks, handouts, lab-reports 모두 레이아웃 슬롯을 먼저 만들고, 슬롯을 실측한 뒤, built-in `$imagegen`으로 PNG/WebP/JPEG 래스터 설명 이미지를 생성한다. 작은 SVG icon/context strip 은 세 타입 모두에서 이미지 보강으로 인정하지 않는다.
- **handouts / lab-reports**: 보통 0~2개지만, 각 이미지가 서로 다른 교육 포인트를 설명하고 레이아웃이 유지되면 여러 개도 허용한다. 검사결과지는 PII 없는 해부·기전·검사 원리·안전 확인 이미지로 제한한다.
- **decks**: ⚠️ **2026-06-06 사용자 룰 — deck당 이미지 4~6장, 이미지가 전체 내용의 핵심 시각 축이어야 한다** (텍스트의 보조 장식이 아니라 이미지 중심 설계). 후보는 정의·기전·절차·행동/비교 슬라이드에서 찾고, 각 이미지는 §3.5.a 0.a 적합성 게이트(내용 직결·unique subject·가독성 향상)를 전부 통과해야 한다. 텍스트·라벨·숫자는 절대 이미지에 굽지 않고 **HTML 오버레이/인접 grid**(.ai-visual__pin, 라벨 grid — Gotcha 13 정렬 룰)로 얹는다. 적합한 subject가 4개 미만이면 억지로 채우지 말고 사유를 완료 보고에 명시한다.
- 생략은 실패가 아니다(handouts/lab-reports 기준). 내용에 직접 맞는 visual intent 가 없거나 레이아웃이 나빠지면 이미지를 생략하고 텍스트·표·아이콘·여백으로 가독성을 높인다 — 단 decks 는 위 4~6장 룰이 우선.

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

### Step 2.5 — 아이콘 패스 (decks / handouts / lab-reports / checkup 공통)

**언제**: Step 2 HTML 초안 완성 직후, Step 3 빌드 직전. Step 3.5 인포그래픽보다 먼저 — 일러스트는 큰 그림 1-3개고, 아이콘은 카드·헤더·리스트·셀 보조 시각화라 보완 관계.

**왜**: 텍스트만 있는 카드·헤딩은 시각적 무게가 부족하다. Healthicons 1,482개 (한국어 alt 시드 1,068개 / 72%) 가 벤더링되어 있어 `<img data-asset="hi-filled-{name}">` 한 줄로 의료 SVG 아이콘을 끼울 수 있다. 빌드가 `src`·`alt`·디렉토리 깊이 모두 자동 처리.

#### 2.5.a — kind별 추천 슬롯·카테고리

| kind | 슬롯 | 추천 카테고리 (filled-style 기준 검색 키워드) |
|------|------|------|
| **decks** | chapter eyebrow 옆 (specialty 표시) | `hi-specialties` (cardiology, endocrinology, gastroenterology, hematology, opthalmology, …) |
| | 데이터 카드 좌상단 (measurement) | `hi-devices` (blood-pressure_monitor, thermometer, weight, pulse-oximeter), `hi-body` (heart-organ, lungs, kidneys) |
| | DO/DON'T 비교 셀 | `hi-symbols` (ok, not-ok, positive, negative), `hi-emotions` (happy, sad, neutral) |
| | 챕터 마무리 / takeaway | `hi-symbols` (heart, health, smoking-cessation, social-distancing) |
| **handouts** | 헤드라인 옆 (condition/symptom) | `hi-conditions` (headache, diarrhea, allergies), `hi-body` |
| | 단계별 시퀀스 (Step 1·2·3) | `hi-objects` (calendar, bandage-adhesive), `hi-devices`, `hi-exercise` |
| | 주의 박스 (CAUTION strip) | `hi-symbols` (alert, alert-triangle, hazardous, stop) |
| | 식사 가이드 그리드 | `hi-nutrition` (fruits, vegetables, dairy, sugar-free, sodium-free, alcohol-cessation, unhealthy-food) |
| | 운동·금연 권고 | `hi-exercise` (walking, running, weights), `hi-symbols` (smoking-cessation) |
| **lab-reports / checkup** | 검사 항목 헤더 | `hi-body` (kidneys/liver/heart-organ/lungs/thyroid), `hi-specialties` |
| | 정상·경계·이상 status 셀 | `hi-symbols` (positive/negative/ok/not-ok/alert) |
| | 권장사항 푸터 (운동·식이·금연·정기 검사) | `hi-exercise`, `hi-nutrition`, `hi-symbols` (smoking-cessation, calendar-quarantine) |

#### 2.5.b — 키 검색 명령

```bash
# 카테고리별 키 훑기 (예: body)
python3 -c "import json; m=json.load(open('shared/assets/healthicons.manifest.json')); [print(f'  {k:50} {v[\"alt_ko\"]}') for k,v in sorted(m['assets'].items()) if v['category']=='hi-body' and v['tags'][0]=='filled']"

# 키워드 검색 (예: 'pressure' 포함된 키)
python3 -c "import json; m=json.load(open('shared/assets/healthicons.manifest.json')); [print(f'  {k:50} {v[\"alt_ko\"]}') for k,v in sorted(m['assets'].items()) if 'pressure' in k and v['tags'][0]=='filled']"
```

운영 매뉴얼·전체 카테고리 분포는 `shared/assets/README.md § Healthicons` 참조.

#### 2.5.c — 삽입 패턴

```html
<!-- 시드 alt 있는 키 (1,068개) — alt 자동 -->
<img data-asset="hi-filled-heart-organ" class="icon-md">

<!-- outline 스타일 (filled 시드 자동 fallback) -->
<img data-asset="hi-outline-blood-pressure_monitor" class="icon-sm">

<!-- 시드 alt 없는 키 — use-site 에서 alt 직접 -->
<img data-asset="hi-filled-mosquito-collection" alt="모기 채집 — 매개체 감시">
```

#### 2.5.d — 스킵 조건 / 수량 가이드

스킵: 같은 슬롯에 일러스트(Step 3.5) 예정 / 텍스트가 이미 self-evident (Hero Number 단독) / lab-report 환자 동적 수치 셀 (아이콘이 시선 분산).

수량: decks 12장당 6-10 아이콘 (한 슬라이드 0-1개), handout A4 1장 5-8 아이콘, lab-report 검사 항목 수 × 1-2 아이콘.

### Step 3 — 빌드

빌드 명령어와 환경 셋업은 `reference/build.md` 참조. 핵심:

```bash
python3 build.py
```

산출물:
- `output/{slug}.pdf` — 환자 공유용 PDF (1280×720 페이지)
- `output/{slug}-preview.png` — 데스크톱 풀스크린 미리보기

### Step 3.5 — 인포그래픽 슬롯 설계 + `$imagegen` 래스터 생성

**언제**: 초안 HTML + `build.py` + `_validate_layout` 가 통과한 직후. 텍스트와 레이아웃이 일단 확정된 지점에서 한 번 멈춘다 — **레이아웃 확정 후에야 정확한 슬롯 폭/높이 측정 가능** (§3.5.b 참조).

**왜**: 환자 교육 자료는 인포그래픽이 들어가면 이해도가 크게 올라간다. 그러나 *어디에 어떤 그림이 들어가야 효과적인지*는 콘텐츠를 다 본 뒤에야 판단할 수 있어, 빌드 후 후보를 고르고 HTML 슬롯을 만든 다음 `$imagegen`으로 직접 생성한다.

**실행 경로 (driver 자동 감지 — 2026-06-06 v2)**: Codex 주도 세션이면 built-in `$imagegen` 직접 호출(기존). **Claude 주도 세션이면 `bash tools/codex_imagen.sh <prompt.md> <target.png>` 로 Codex CLI를 헤드리스 자동 호출** — 슬롯 설계·후보 식별·프롬프트 작성 책임은 그대로 integrator(Claude)에게 있고, Codex는 프롬프트→래스터 변환만 한다. codex CLI 없음/미로그인이면 이미지를 생략하고 `no image added: codex unavailable` 기록(빈 슬롯 HTML은 남기지 않음). 위임(품앗이) 모드·실패 처리·환경별 주의는 `reference/agent-orchestration.md` 참조.

**⛔ handouts v2 이미지 게이트 (2026-06-12, SoT=`PRD/handout-visual-v2/`)**: handouts 는 Step 3.5 전 과정에 다음 4중 게이트가 **의무**다 — ① 슬롯마다 `ImageIntent` 작성(§3.5.a — explains·visual_type·must_show·prompt_en, 적합 visual_type 없으면 슬롯 생성 금지) ② 생성 후보 전부 **aboutness 교차검증**(§3.5.e — 미달이면 채택 금지) ③ 삽입 전/후 스냅샷 **visual diff + `_validate_layout` AND 게이트**(§3.5.e) ④ 빌드 시 **ToneScore ≥ T_tone**(§검증 워크플로우). 게이트는 기본 ON이며 환경변수 `HANDOUT_V2_GATES=0`으로만 관찰 모드 전환 가능. **decks / lab-reports 확장은 P5(후속)** — 그 전까지 decks/lab-reports 는 기존 §3.5.a 0.a 적합성 게이트대로 운용한다.

**판단 기준**:
- 이미지는 수량 목표가 아니라 가독성 개선 수단이다. 삽입 후 본문이 작아지거나 정보 구조가 흐려지면 만들지 않는다.
- **decks / handouts / lab-reports 공통**: 이미지 활용 방식은 동일하다. 레이아웃 슬롯을 먼저 만들고, 슬롯을 실측한 뒤, built-in `$imagegen`으로 PNG/WebP/JPEG 래스터 설명 이미지를 생성한다. 작은 SVG icon/context strip, healthicon 묶음, 단순 아이콘 행은 어떤 콘텐츠 타입에서도 이미지 보강으로 인정하지 않는다.
- **handouts / lab-reports**: 보통 0~2개지만, A4 안에서 여백·가독성이 유지되고 각 이미지가 다른 포인트를 설명하면 여러 개도 허용한다. handout은 기전·행동·비교·안전 확인, lab-report는 검사 원리·장기 모식도·결과 이해 보조처럼 PII가 없는 이미지로 제한한다.
- **decks**: Definition, Mechanism, Process, Action, Comparison 중 내용상 그림이 가장 강한 슬라이드에만 배치한다. 최소 개수는 없다.
- 이미지 안에는 글자를 굽지 않는다. 라벨·캡션·숫자·주의 문구는 HTML Pretendard 텍스트로 배치한다.

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

**선정 가이드**: handouts / lab-reports 는 대개 0~2개, **decks 는 4~6장 (2026-06-06 사용자 룰 — 이미지가 핵심 축)**. A4 자료라도 서로 다른 행동·절차·장비·비교 포인트를 전용 이미지 섹션으로 나누면 여러 개를 넣을 수 있다. visual intent 와 이미지 품질 게이트는 수량 룰과 무관하게 전부 적용 — 각 후보는 슬라이드/섹션 제목·핵심 문장과 직접 연결되어야 하며, 같은 deck/series 안에서 같은 구도·같은 subject 를 반복하지 않는다. 라벨·텍스트는 HTML 로만 (이미지에 굽기 금지).

**ImageIntent 의무화 (handouts v2 — 슬롯을 만들기 전에 작성)**: handouts 는 이미지 슬롯마다 다음 4필드를 가진 `ImageIntent` 를 먼저 작성하고, 같은 베이스네임의 사이드카 `shared/assets/generated/{topic-slug}-{slot-key}-YYYYMMDD.intent.json` 으로 남긴다 (스키마·예시는 `shared/_image_gate.py` docstring = SoT):

- `explains` — **이 이미지가 설명할 본문 문장/표/체크리스트 정확히 1개** (자유서술, 필수). 본문에 대응 문장이 없으면 그 이미지는 "겉도는 이미지"다 — 만들지 않는다.
- `visual_type` — Anatomy / Mechanism / Process / Equipment / Action / Comparison 중 하나. **이 6개에 들어맞지 않으면 슬롯 자체를 만들지 말고** 텍스트 위계·표·여백 개선으로 대체한다 (기존 §15/§16 룰의 코드 게이트화).
- `must_show[]` — 이미지에 반드시 보여야 할 요소 ≥1개 (aboutness 검증 기준이 된다).
- `prompt_en` — 슬롯 실측 비율을 명시한 영문 프롬프트 (§3.5.b).

intent 없는 생성·채택은 게이트 위반이다: `python3 -m shared._image_gate <html_path>` 가 HTML 이 참조하는 generated 이미지의 intent 존재·스키마·채택 불변식을 검증한다(빌드/푸시 전 필수, exit 1 = 차단). 슬롯을 명시적으로 생략한 경우에도 intent.json 에 `adopted: null + skipped_reason` 으로 남긴다.

#### 3.5.a.1 — `$imagegen` 생성·저장 절차

0. 좋은 선례를 먼저 연다: 골밀도 검사, 대장내시경 준비, 비강 스프레이, 인슐린 시작, 크레아틴, 이상지질혈증 식단 중 최소 2개를 preview로 확인한다.
1. HTML에 먼저 `.ai-visual` 또는 자료별 fixed figure/frame 슬롯을 만든다. 슬롯 폭/높이는 mm 또는 px로 고정하고, 작은 장식 strip이 아니라 자료의 주요 교육 섹션이 되게 한다.
2. 슬롯 실측값으로 영문 프롬프트를 작성한다. deck 의 split/strip 이미지처럼 고정 프레임에 들어가면 full-bleed 구도를 요구하고, “fill the entire frame edge to edge, no blank side gutters, no centered small vignette”를 명시한다. PII, 제품명, 브랜드명, 이미지 내부 텍스트는 금지한다.
3. 이미지별 별도 프롬프트로 생성한다(batch 금지). **handouts 는 슬롯당 후보 2~3장 생성이 기본**이고, 호출이 실패하면 같은 경로로 **≥2회 재시도** 후 fallback 체인을 따른다 — `tools/codex_imagen.sh` ↔ built-in `$imagegen` (driver 반대 경로로 1회 전환) → 둘 다 불가하면 **명시적 생략 + intent.json 에 `skipped_reason` 기록** (`no image added: <사유>`, 빈 슬롯 HTML 잔존 금지). 후보별 사용 경로(`gen_path`)와 실패 이력은 intent.json `candidates[]` 에 남긴다. decks/handouts/lab-reports 보강에서 코드 네이티브 SVG는 `$imagegen` 대체물로 쓰지 않는다. (`codex_imagen.sh` 는 순차 호출만 — `reference/image-assets.md` §생성·저장 절차 ⚠️ 레이스 주의.)
4. **handouts: 후보 전부를 §3.5.e aboutness 교차검증에 올리고, 게이트 통과 후보 중 `aboutness × quality` 최고 1장만** 선택본으로 `shared/assets/generated/{topic-slug}-{purpose}-YYYYMMDD.{png|webp|jpg}`에 저장한다. 전 후보 미달이면 프롬프트 보강(must_show 구체화) 후 재생성 1회 → 그래도 미달이면 생략+사유. `$imagegen` 원본은 삭제하지 않는다. deck split/strip 슬롯은 슬롯 비율로 crop/fit 저장해 좌우 여백이 남지 않게 한다.
5. HTML에 `<figure class="ai-visual">` 또는 자료별 figure/frame 으로 삽입하고, 필요한 설명은 `.ai-visual__caption`, `.ai-visual__pin`, 또는 `figcaption`으로 얹는다. 슬롯을 꽉 채워야 하는 generated deck image에는 `.ai-visual--fill`을 함께 붙인다.
6. `python3 -m shared._validate_layout <html_path>` → `python3 build.py` 또는 단일 타깃 빌드 → preview PNG 육안 확인까지 완료한다.
7. preview가 좋은 선례 대비 작은 아이콘 행, 얇은 strip, 장식 배너처럼 보이면 실패로 보고 재생성·재배치한다.

#### 3.5.b — 영문 프롬프트 작성 규칙 (슬롯 실측 우선)

⚠️ **일반 비율 추천 금지** (`4:3`, `16:9`, `1:1` 등 라운드 비율). 모든 이미지 프롬프트는 **HTML 작성 후 실제 슬롯의 폭/높이를 mm 단위로 측정**한 다음, 그 정확한 비율과 픽셀을 strict하게 명시한다. 라운드 비율이 슬롯과 어긋나면 양옆/위아래에 어색한 여백이 생기고, 결국 CSS hack(`max-width` 강제, `padding` 줄임)으로 끼워맞춰야 한다. 2026-05-23 cvd-retinal-screening 핸드아웃에서 한 번 발생 후 정식 룰화.

##### 3.5.b.1 — 슬롯 폭 측정 (필수)

A4 핸드아웃 (handouts / lab-reports) — 페이지 14mm padding 기준:
- **본문 폭 (풀폭) = 182mm** (= 210 − 14×2)
- **body-2col 좌/우 = 88mm** 각 (= (182 − gap 6mm) / 2)
- **body-3col 각 = 58mm** (= (182 − gap 4mm×2) / 3)

deck slide (decks) — 1280×720 기준 (좌우 padding 80px):
- **본문 폭 = 1120px**
- **body-2col 좌/우 = 536px** 각

높이는 해당 figure에 명시한 `height` (예: `height:62mm`) 그대로 사용. **HTML이 확정된 후에 측정**한다 — 추정 금지.

##### 3.5.b.2 — 비율·픽셀 산출

```
ratio = slot_width_mm / slot_height_mm    (소수점 둘째 자리)
px_w  = slot_width_mm  × 12               (300 DPI 인쇄 품질)
px_h  = slot_height_mm × 12
```

예시:
| 슬롯 폭 × 높이 | ratio | 권장 px |
|---|---|---|
| 182mm × 50mm | **3.64:1** → 프롬프트엔 `3.6:1` | 2200 × 610 |
| 182mm × 40mm | **4.55:1** → `4.5:1` | 2200 × 490 |
| 88mm × 78mm | **1.13:1** | 1300 × 1150 |
| 88mm × 88mm | 1:1 | 1100 × 1100 |
| 58mm × 58mm | 1:1 | 800 × 800 |

##### 3.5.b.3 — 새 프롬프트 골격

```text
Create a {style descriptor}, 
aspect ratio strictly {W}:{H} ({px_w} x {px_h} pixels), white background.

{LAYOUT / COMPOSITION SPEC — describe exact regions, icon positions with %, sizes}

STYLE:
Clean flat modern medical {kind}, premium hospital aesthetic,
strict palette: navy #003366 and steel blue #5B9BD5 only,
white background, soft gradients allowed.

CRITICAL CONSTRAINTS:
- Illustration must SPAN THE ENTIRE CANVAS evenly — no empty side panels, 
  no centered cluster with empty margins on left/right or top/bottom.
- All depicted elements must use the full available canvas dimensions.
{additional constraints — N-column positions if applicable}

ABSOLUTELY NO TEXT:
Do NOT include any letters, numbers, words, labels, captions, 
or any characters in any language (Korean, English, Chinese, etc.) 
anywhere on the canvas. Pure visual only.
HTML will overlay Korean labels using Pretendard font separately.
```

⚠️ **STYLE 블록 = 브랜드 스타일 디스크립터 표준 (v2 P4 — 모든 프롬프트에 항상 삽입)**: 위 골격의 STYLE 단락은 자료 간 이미지 톤 통일 장치다. 실제 문구는 `reference/image-assets.md` §영문 프롬프트 기본 골격의 **세미리얼 하우스 스타일 디스크립터** (rich semi-realistic, navy `#003366` + steel blue `#5B9BD5` 팔레트 — 플랫 벡터/아이콘 스타일 금지, 2026-06-06 사용자 확정)를 그대로 쓰고, 색·토큰의 SoT 는 `reference/brand-design-system.md` 다. 디스크립터를 빼먹거나 임의 변형하면 ToneScore `image_style_ok` 감점 대상.

##### 3.5.b.4 — N-column / N-row 시각 (다단계 흐름도, 비교 매트릭스, N개 결과)

균등 분포가 필요한 비주얼은 **각 요소의 중심 좌표를 % 단위로 명시**한다. HTML 라벨 grid와 매칭해 자동 정렬 보장.

| N | 중심 위치 (%) |
|---|---|
| 2 | 25 · 75 |
| 3 | 16.7 · 50 · 83.3 |
| 4 | 12.5 · 37.5 · 62.5 · 87.5 |
| 5 | 10 · 30 · 50 · 70 · 90 |

세로 분포(y 좌표)도 동일 공식.

프롬프트 예 (4-column flow):

```text
4 circular icons of EQUAL SIZE evenly distributed across the canvas width.
Icon CENTER positions must be precisely at:
  • x = 12.5%, x = 37.5%, x = 62.5%, x = 87.5%
All 4 icons vertically centered at y = 50%.
Icon diameter: approximately 60% of canvas height.
```

대응하는 HTML (이미지 바로 아래 캡션 grid):
```html
<figure class="ai-visual" style="height:62mm; max-width:118mm; margin:0 auto; padding:0; ...">
  <img src="..." style="width:100%; height:100%; object-fit:contain;">
</figure>
<div style="display:grid; grid-template-columns: repeat(4, 1fr); max-width:118mm; margin:0 auto;">
  <div>① 라벨1</div><div>② 라벨2</div><div>③ 라벨3</div><div>④ 라벨4</div>
</div>
```
`max-width`가 figure와 캡션 grid 둘 다 같아야 4 column 중심이 4 아이콘 중심과 정확히 매칭.

##### 3.5.b.5 — 한글 라벨은 HTML 오버레이 (Pretendard) — 이미지에 굽지 말 것

이미지에 텍스트(특히 한글)를 굽는 것 절대 금지:
- ❌ 폰트 불일치 (이미지 안 폰트 vs HTML Pretendard) → 자료 일관성 깨짐
- ❌ 가독성 저하 (저해상도에서 흐림)
- ❌ 수정 불가 (이미지 새로 생성해야)
- ✅ HTML로 오버레이: 폰트 일관성, 수정 즉시 반영, 정렬 정확

라벨 위치 옵션:
- **이미지 바로 아래 grid** — 가장 simple. N-col 흐름도/매트릭스에 권장. figure max-width와 grid max-width 일치 필수
- **이미지 위 absolute pin** — `.ai-visual__pin` 활용. 해부도에 라벨 핀 박을 때
- **우측 별도 card** — `body-2col` 우측에 체크리스트 카드 (일석이조 패턴)

##### 3.5.b.6 — lab-reports 도 같은 방식으로 적용

검사 결과지·검사 설명 자료도 이미지가 필요하면 decks/handouts 와 같은 Step 3.5 룰을 적용한다. 단 정확한 수치 시각화와 개인정보 보호가 핵심이므로 일반 인포그래픽 남용은 금지하고, 환자명·차트번호·생년월일·원본 검사 PDF·식별 가능한 수치를 이미지 프롬프트와 파일명에 넣지 않는다.

##### 3.5.b.7 — 카테고리별 보조 토큰 (선택)

`reference/image-assets.md §Phase 1`에 카테고리(해부도·기전·절차·장비·자세·비교)별 상세 프롬프트 템플릿 보강. 슬롯 실측값을 그 템플릿에 채워 사용.

#### 3.5.c — `$imagegen` 실행 기록 형식

빌드 통과 직후, 사용자에게 다시 이미지를 만들어오라고 맡기지 않는다. Codex가 다음 형식으로 내부 판단을 정리하고 곧바로 `$imagegen`을 호출한다. 중간 보고가 필요하면 위치·왜·파일명·프롬프트만 짧게 공유한다.

```
📸 인포그래픽 생성 — {topic-slug}

문서 초안이 빌드·검증을 통과했습니다. 다음 위치에 인포그래픽 슬롯을 만들고, 슬롯 크기에 맞춘 프롬프트로 `$imagegen`을 호출합니다.

────────────────────────
### 1. 슬라이드 3 / Definition — 갑상선 해부도
**왜**: 갑상선 위치와 모양은 텍스트만으로 설명하기 어렵다. 한 장의 그림이 가장 빠르다.
**슬롯**: `.ai-visual--hero` (Asymmetric Split 우측, 4:3)
**저장 파일명**: `shared/assets/generated/thyroid-nodule-anatomy.png`

$imagegen 프롬프트:
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

각 항목은 (1) 위치 (2) source slide text summary (3) 왜 필요한지 한 줄 (4) unique subject + 중복 아님을 확인한 근거 (5) 슬롯 클래스 + aspect ratio (6) 미리 정한 저장 파일명 (7) `$imagegen` 프롬프트 — 일곱 가지를 항상 포함한다.

#### 3.5.d — 생성 이미지 배치 처리 (Pass 2 시작)

`$imagegen` 결과가 생성되면:

1. 선택한 PNG/WebP/JPEG 를 **제안 시 정한 파일명 그대로** `shared/assets/generated/{topic-slug}-{slot-key}.png` 에 복사한다. `$imagegen` 기본 생성 폴더의 원본은 삭제하지 않는다. (handouts: 같은 베이스네임의 `.intent.json` 사이드카에 후보·verdict·채택 기록 완료 상태여야 한다 — §3.5.a.)
2. **(handouts 필수) 삽입 전 스냅샷**: `python3 -m shared._visual_diff capture <html_path> /tmp/{slug}-before.png` — 이미지가 들어가기 직전의 확정 레이아웃을 기준선으로 잡는다.
3. 해당 슬라이드/섹션 HTML 의 placeholder (또는 텍스트 카드) 위치에 `.ai-visual` 컴포넌트 삽입. 컴포넌트 변형(`--hero` / `--portrait` / `--compact` / `--contain`)은 3.5.b 에서 정한 슬롯 그대로.
4. **(handouts 필수) 삽입 후 스냅샷 + 회귀 diff**: after 캡처 후 `python3 -m shared._visual_diff compare before.png after.png --slot-bbox X,Y,W,H` — 슬롯 영역 밖 변화(본문 밀림·겹침·잘림·푸터 침범)가 잡히면 회귀다. §3.5.e AND 게이트로 처리.
5. `python3 -m shared._validate_layout <html_path>` 재실행 → `OK` 확인. (handouts: visual diff 와 **둘 다** 통과해야 채택 — §3.5.e.)
6. `python3 build.py` 재실행 → PDF/PNG 갱신, `output/{kind}/{slug}-preview.png` 로 시각 점검. (handouts: `python3 -m shared._tone_score <html_path>` 로 ToneScore ≥ T_tone 확인 — §검증 워크플로우.)
7. Step 4 (git commit + push) 로 진행.

상세 컴포넌트·삽입 예시는 `reference/image-assets.md §HTML 삽입` 참조. 이미지 안에는 텍스트를 절대 넣지 않으며, 라벨·캡션은 모두 HTML `figcaption` / `.ai-visual__pin` 으로 얹는다.

#### 3.5.e — handouts v2 채택 게이트: aboutness 교차검증 + 레이아웃 회귀 가드 (2026-06-12)

**1) aboutness 교차검증 (P1 — "겉도는 이미지" 원천차단)**

생성 후보마다, 검증 주체(VLM)가 후보 이미지를 **Read 도구로 직접 열어 보고** intent 와 대조 판정한다. 프롬프트를 쓴 에이전트의 자기 채점이 아니라 *이미지 실물 vs intent* 교차검증이다:

> "이 이미지가 `{explains}` 를 실제로 묘사하는가? `{must_show[]}` 각 요소가 보이는가?
> `depicts_intent`(Y/N) · `aboutness`(0~100) · `quality`(0~100: 해상도·왜곡·한글텍스트 혼입 여부) · 근거를 판정하라."

판정 결과는 intent.json `candidates[].verdict` 에 기록하고, **채택 조건(하드 게이트)**:

- 채택 ⇔ `depicts_intent == true ∧ aboutness ≥ T_about(70, 초기값·캘리브레이션 대상) ∧ quality OK(한글텍스트 0 · 왜곡 없음 · 저해상도 아님)`
- 미달 = 재생성 1회(프롬프트의 must_show 구체화) → 그래도 미달이면 **빈 슬롯을 남기지 말고 슬롯 제거 + `skipped_reason` 기록**.
- **"이미지 개수 채우기" 금지**(기존 §15/§16): generic·장식·같은 정보 반복·SVG strip 은 aboutness 와 무관하게 보강 불인정.
- 기록 정합성은 `python3 -m shared._image_gate <html_path>` 가 결정론 검증한다 (intent 누락·불변식 위반 = exit 1 차단).

**2) 레이아웃 회귀 가드 (P3 — AND 게이트)**

이미지 채택 = `visual diff 무회귀 ∧ _validate_layout OK` **둘 다** 통과. 하나라도 실패하면:

1. 슬롯 크기/배치 자동 보정 (figure height·max-width 조정, 라벨 grid 재정렬) 후 **재검 (최대 2회)**.
2. 2회 보정 후에도 실패 → 이미지 생략 + `skipped_reason: "layout regression"` 기록, 레이아웃은 삽입 전 상태로 복원.
3. diff 회귀 임계(슬롯 밖 변화 0.2%·겹침/잘림 0 허용)는 `shared/_visual_diff.py` 상수 = 초기값·캘리브레이션 대상.

Step 3.8 전수 육안검수는 그대로 유지하되, **diff 가 가리키는 페이지를 우선 확인**한다.

**3) 완료 보고 포맷 (P1~P4 집계 — handouts 완료 시 이 형식으로 사용자에게 요약)**

```
✅ {topic} 핸드아웃 — verified
🖼 이미지: N장 채택 / M장 생략
  • slot1 [Process] aboutness 88 — "{explains}"
  • slot2 생략 — 적합 visual_type 없음
📐 레이아웃: 0 깨짐 (validator pass, diff regress 0)
🎨 톤: 92/100
```

검증기 통과만으로 "완성" 보고 금지 — aboutness·diff·톤 게이트 결과가 이 포맷에 전부 들어가야 완료다.

### Step 4 — git push (Pages 배포 + Notion DB upsert 자동)

**원클릭 배포**: Pass 2 까지 끝났으면 git 한 번으로 라이브 사이트 반영 + Notion DB 행 자동 등록까지 모두 처리된다.

원클릭 원칙:
- 로컬 `NOTION_TOKEN`이 없어도 수동 Notion 생성으로 우회하지 않는다. 기본 경로는 `git push` → GitHub Actions → Pages 배포 + Notion upsert다.
- 수동 Notion 커넥터 생성/수정은 CI가 실패했거나 `NOTION_TOKEN` secret 누락이 확인된 경우의 fallback으로만 사용하고, 그 사실을 사용자에게 보고한다.
- HTML/PDF 링크는 CI가 배포한 GitHub Pages URL을 기준으로 한다.

```bash
git pull --rebase                           # 다른 머신 변경 먼저 받기
git status --short                           # staged 영역 audit (다른 대화창 잔재 확인)
git add <내가 만든·수정한 파일만 명시적으로>     # 절대 git add . 금지
git status --short                           # 다시 확인 후
git commit -m "Add {topic} ({slug})"
git push
git log -1 --stat                            # 의도한 파일만 들어갔는지 검증
```

CI(GitHub Actions):
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

**A4 (handouts / lab-reports) 공통 체크:**
- **page overflow** — `.page` 가 클립되어 콘텐츠가 잘림 (특히 핸드아웃 297mm 초과)
- **section ↔ footer overlap** — body 마지막 섹션이 footer 영역으로 침범 (인쇄 시 텍스트 겹침)
- **element below/right of page** — 카드·타일·표 행이 페이지 bbox 밖으로 나감

**deck (1280×720) 전용 강화 체크 (2026-06-06 추가, `shared/_validate_layout.py` DECK 경로):**
deck 은 위 overflow 검사 외에 황금비율·모듈러 스케일 룰([Gotcha 19], **SoT = [`reference/deck-design-proportions.md`](reference/deck-design-proportions.md) §6**)을 자동 강제한다. ⚠️ 검증·캡처는 PDF 와 동일한 `print` 미디어 + Pretendard 폰트 로딩 대기로 수행한다(screen 미디어로는 print 의 미세 폰트 메트릭 차이로 생기는 카드 겹침을 놓침).

- **slide overflow** — deck 슬라이드가 1280×720 안에 안 들어감
- **`font_too_small`** — 박스/표 **본문 폰트가 15px 미만이면 차단** (노안 환자 가독성 하한; kicker·label·value 는 면제). 0.58~0.78rem 강제 축소는 폐기됨 — 본문 16~17px·표셀 15~16px 가 기준.
- **`body_underfills`** — 본문 최하단~푸터 상단 여백이 **72px 초과**(보이는 박스 기준)면 언더필 경고. 적정 24~56px, 16px 미만은 과밀.
- **`box_underfill`** — 박스 하단 빈 공간이 상단보다 비대칭으로 큼(하단 >28px AND 상단보다 >24px). 위로 몰린 내용 → `justify-content:center` 또는 박스 높이를 내용에 맞춤.
- **`box_content_overflow`** — 박스 내용이 `scrollHeight > clientHeight`로 실제 잘림. 긴 비교값은 폰트 축소가 아니라 라벨/값 분리로 해결.
- **`sparse_box`** — 대칭이어도 박스가 콘텐츠보다 과하게 큼(`inner_fill` < 0.48, stat 카드는 < 0.40 — **경고**). 처리 우선순위 B(콘텐츠 확대)→C(박스 축소+중앙배치)→D(재설계). 임계 수치 전체는 SoT §4 표 참조.
- **`content_image_gutter`** / **`sibling_box_overlap`** — 본문↔이미지 거터 24px 미만, 형제 카드 물리 겹침.

> ⚠️ **검증기 통과 ≠ 시각 통과.** deck 은 Step 3.8 에서 `python3 tools/slide_screens.py <html>` 로 **모든 슬라이드 PNG 를 한 장씩 전수 육안검수**해야 끝난다(요약 몇 장만 보는 것 금지). bbox·픽셀 검증으로 못 잡는 박스 대칭·희소 박스·라벨 정렬을 사람이 확인한다.

### 실행 명령

```bash
# 단일 파일 검증
python3 -m shared._validate_layout handouts/lifestyle/hypertension-low-salt/index.html

# 전체 검증 (decks/ + handouts/ + lab-reports/ 모든 index.html)
python3 -m shared._validate_layout
```

exit code 0 → 통과, 1 → 실패 (CI gate에 그대로 사용 가능).

### handouts v2 게이트 — 이미지·레이아웃·톤 (2026-06-12, SoT=`PRD/handout-visual-v2/`)

handouts 는 `_validate_layout` 외에 다음 3개 게이트를 빌드/푸시 전에 통과해야 한다 (전부 exit 0/1, 기본 ON — `HANDOUT_V2_GATES=0` 일 때만 관찰 모드):

```bash
# ① ImageIntent + aboutness 채택 불변식 (intent 누락·미달 채택 차단) — §3.5.a / §3.5.e
python3 -m shared._image_gate handouts/{specialty}/{slug}/index.html

# ② 이미지 삽입 전/후 visual diff (슬롯 밖 변화 = 회귀) — §3.5.d / §3.5.e
python3 -m shared._visual_diff capture <html> /tmp/before.png   # 삽입 전
python3 -m shared._visual_diff compare /tmp/before.png /tmp/after.png --slot-bbox X,Y,W,H

# ③ ToneScore — 색 팔레트·Pretendard·이미지 스타일 vs brand 토큰 (T_tone=80)
python3 -m shared._tone_score handouts/{specialty}/{slug}/index.html
```

- **AND 게이트**: 이미지 채택은 ②diff 무회귀 ∧ `_validate_layout` OK 둘 다 필요 (§3.5.e). ③ToneScore 는 빌드 게이트 — 미달이면 색·폰트·이미지 스타일을 brand 토큰으로 교정 후 재산출.
- 임계 초기값: `T_about=70` · `T_tone=80` · diff 슬롯 밖 변화 0.2%(겹침/잘림 0 허용) — **전부 캘리브레이션 대상**, 사람 스팟체크로 조정하며 상수 SoT 는 각 `shared/_*.py` 모듈.
- `_tone_score` 의 `image_style_ok` 는 VLM 판정 주입형 stub — 판정 전이면 `unjudged` 로 표기되니 완료 보고에 그대로 안 옮기고 직접 판정해 `--image-style-ok` 로 주입한다.
- **레거시 하위호환**: 게이트는 **이번 작업에서 새로 만들거나 수정한 이미지 슬롯**에 적용한다. 기존 핸드아웃의 2026-06-12 이전 이미지(intent.json 없는 자산)는 grandfathered — 그 자료를 손대지 않는 한 게이트 실행 대상이 아니며, 손댈 때 해당 슬롯만 intent 백필한다. 전 자산 일괄 백필은 캘리브레이션 단계 과제.
- **P5(후속)**: 이 3개 게이트의 decks / lab-reports 확장 + evals 회귀 케이스(aboutness 탈락·의도 깨짐 차단·브랜드 외 색 감점) 추가. 그 전까지 decks/lab-reports 는 기존 검증기·육안 워크플로우 그대로 (하위호환).

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
| `font_too_small` (deck) | 본문 폰트 <15px 강제 축소 | 폰트 키우기 — 표셀 15~16px·본문 16~17px (콘텐츠 줄여 공간 확보, 폰트 축소 금지) |
| `body_underfills` (deck) | 푸터 위 >72px 빈 여백 | `space-between`/패딩·행간으로 펴기, 콘텐츠 보강 (SoT §4) |
| `box_underfill` / `sparse_box` (deck) | 박스가 콘텐츠보다 과대 | 박스 높이를 내용에 맞춤 또는 `justify-content:center`, B→C→D 순서 |

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
9. **마무리 슬라이드는 closing-grid 패턴 강제** — contact-card + qr-block. QR은 빌드 시 자동 생성. **contact-card 값(진료시간·주소·전화)은 반드시 § 클리닉 연락처(SoT) 표에서 복사** — 직접 타이핑 금지.
10. **OG 메타태그 7종 표준 포함** — 카톡 공유 미리보기 카드 자동 작동을 위해 필수.
11. **의료 표기 통일 — SoT = [`reference/medical-notation-style.md`](reference/medical-notation-style.md)** (원장 결정 2026-06-07). 모든 신규/수정 콘텐츠에 적용:
    - 수치 기준은 부등호로만 — `≥`/`≤`/`<`/`>` + "이상/이하" 텍스트 **중복 금지** (O `uACR ≥30 mg/g` · X `uACR ≥30 mg/g 이상`). 단 자연어 "65세 이상" 등 비수치 서술은 유지.
    - 수치–단위 공백: `6.5%` (not `6.5 %`); `mg/dL` 등 슬래시 단위만 한 칸 띄움.
    - 정량 "감소"는 `↓` 화살표 — `LDL 15~20% ↓`, `위험 56% ↓` (문장 동사형 "…를 50% 감소시킵니다"는 텍스트 유지).
    - 소변 알부민/크레아티닌 비는 **`uACR`** (소문자 u + 대문자 ACR)로 통일 — `UACR`·지표 의미의 `ACR` 금지. **예외**: 학회/기관 고유명(ACR 2020·ACR/EULAR 등)은 그대로 둔다.

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
4. `python3 -m shared._validate_layout <html>` 통과 후 `python3 build.py` 실행해서 새 PDF 생성 — deck 강화 검증기(`font_too_small`·`body_underfills`·`box_underfill`·`sparse_box`, § 검증 워크플로우)도 함께 통과시킨다
5. 변경된 슬라이드를 시각 검증 — Step 3.8 룰대로 `python3 tools/slide_screens.py <html>` 로 영향받은 슬라이드 PNG 를 직접 육안 확인(검증기 통과 ≠ 시각 통과)
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
python3 build.py
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

핸드아웃/검사 결과지/슬라이드 덱의 AI 이미지는 **가독성과 설명력을 높일 때만** 배치한다. 기본값은 "필요한 만큼"이며 최소 이미지 개수는 없다. 원장님이 별도 이미지를 제공한 경우에는 그 이미지를 우선 검토하되, 제공 이미지도 현재 슬라이드/섹션 내용과 직접 맞지 않으면 쓰지 않는다.

이미지 활용 방식은 세 콘텐츠 타입 모두 동일하다. 먼저 레이아웃 슬롯을 만들고, 실제 슬롯 치수를 재고, built-in `$imagegen`으로 PNG/WebP/JPEG 래스터 설명 이미지를 생성한다. 작은 code-native SVG icon/context strip, healthicon 묶음, 단순 아이콘 행은 슬라이드·핸드아웃·검사 설명 어디에서도 이미지 보강으로 인정하지 않는다.

표준 처리 순서:

1. 해당 슬라이드/섹션의 제목·핵심 문장·표/카드 내용을 읽고, 이미지가 설명할 **구체적 subject**를 먼저 적는다. subject 를 못 적으면 이미지를 만들지 않는다.
2. 같은 deck/series 안의 기존 이미지 파일·프롬프트를 확인해 같은 subject, 같은 구도, 같은 generic strip 이 없는지 확인한다.
3. HTML 레이아웃 안에 이미지 슬롯을 먼저 만든다 (`.ai-visual` / `.ai-visual--hero` / `.ai-visual--portrait` / `.ai-visual--compact`, 또는 자료별 custom fixed-size frame).
4. 슬롯 폭/높이를 실측해 영문 프롬프트를 작성하고 `$imagegen`으로 생성한다. deck split/strip 슬롯은 full-bleed 구도와 “no blank side gutters”를 명시한다. 이미지 내부 텍스트, PII, 브랜드명은 금지한다.
5. 선택한 PNG/WebP/JPEG를 `shared/assets/generated/{topic-slug}-{purpose}-YYYYMMDD.png`처럼 의미 있는 파일명으로 복사하고, 같은 이름의 `.prompt.md`에 slide/section, source text summary, visual intent, unique subject, negative constraints 를 남긴다. deck split/strip 슬롯은 슬롯 비율로 crop/fit 저장하고 `.ai-visual--fill`로 배치한다. `$imagegen` 기본 생성 폴더의 원본은 삭제하지 않는다.
6. 이미지 안의 글자는 쓰지 않고, 라벨·캡션·설명은 HTML 텍스트로 배치한다.
7. `python3 -m shared._validate_layout <html_path>` 실행
8. 필요 시 `python3 build.py` 후 `output/{kind}/{slug}-preview.png`를 직접 확인

HTML 예시:

```html
<figure class="ai-visual ai-visual--hero">
  <img class="ai-visual__image" src="../../../shared/assets/generated/thyroid-ultrasound.png" alt="갑상선 초음파 검사 설명 일러스트">
  <figcaption class="ai-visual__caption">라벨과 설명은 HTML 텍스트로 얹는다</figcaption>
</figure>
```

규칙: 이미지 프롬프트나 파일명에 환자명/차트번호/생년월일/원본 검사 PDF를 넣지 않는다. 이미지 안의 한글·영문 텍스트는 피하고, 모든 라벨은 HTML로 처리한다. 무관한 범용 의료 배경, 파일만 다른 중복 이미지, 내용을 압박하는 장식 이미지는 금지한다. 자세한 절차는 `reference/image-assets.md`.

**자산 라이브러리 (권장)**: 신규 자료는 `<img data-asset="key">` 한 줄로 작성하면 `build.py` 가 `manifest.json` 을 보고 `src`·`alt` 를 자동 채운다. 디렉터리 깊이(`../../../`) 계산·alt 텍스트 통일·재이름 propagation 모두 자동. 새 이미지 추가 시 `tools/sync_manifest.py` 가 자동 등록한다. 운영 규칙·검수 게이트·`tools/asset_lint.py` 사용법은 **`shared/assets/README.md`** 참조.

**Healthicons (벤더된 의료 SVG 아이콘 ~1,500개)**: 큐레이션 자산과 같은 `data-asset` 패턴을 그대로 쓰면 된다. 키는 `hi-<style>-<name>` (style ∈ `filled`/`outline`). 약 1,000개는 한국어 alt 가 시드되어 있고, 나머지는 use site 에서 `alt="..."` 직접 지정 권장. 예시:

```html
<img data-asset="hi-filled-heart-organ" class="icon-md">                <!-- alt="심장" 자동 -->
<img data-asset="hi-outline-blood-pressure_monitor" class="icon-md">    <!-- alt="혈압계" 자동 (filled→outline fallback) -->
<img data-asset="hi-filled-syringe-vaccine" alt="독감 예방접종 안내">      <!-- use-site override -->
```

신규 시드 추가는 `tools/healthicons_alt_ko.json` 에 `"<key>": "<한글>"` 한 줄 더 후 `python3 tools/sync_healthicons.py` 재실행. 카테고리 분포·운영·갱신 절차는 **`shared/assets/README.md` § Healthicons** 참조.

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

**검증 룰**: 작성 후 `python3 -m shared._validate_layout <html_path>` → `OK` 받기 전에는 끝나지 않은 작업이다. 검증기가 잡는 issue:
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

`python3 build.py` 실행 시 4개 타깃(현재) 모두 일괄 빌드되며, 각 출력은:
- `output/decks/{slug}.{pdf,png}` — 16:9 덱
- `output/handouts/{slug}.{pdf,png}` — A4 핸드아웃
- `output/lab-reports/{slug}.{pdf,png}` — A4 랩리포트


## 건강검진 결과지 (lab-reports / topic = health-checkup)

종합 건강검진은 환자마다 시행 검사 갯수가 달라 단일 패널 lab-reports (cbc / lipid-panel 등) 의 "1페이지 강제" 룰을 따르지 못한다. **`lab-reports/health-checkup/` topic 은 1~3페이지 가변** 으로 별도 룰을 적용한다.

### 트리거

원장님 또는 직원이 다음과 같이 요청할 때:
- "종합검진 결과지", "건강검진 결과", "검진 결과지"
- 동시에 여러 검사 (혈액 + 내시경 + 초음파 + 심전도 + 골밀도 등) 공유
- 텍스트 + PDF + 사진 혼합 입력

→ `lab-reports/health-checkup/{hash10}/index.html` 로 인스턴스 생성.

### 입력 형태 (모두 지원)

| 형태 | 처리 |
|---|---|
| **텍스트** (의사 정리 소견) | 가장 신뢰도 높음. 직접 본문 작성 |
| **PDF** (외부 검진센터 결과지) | PyMuPDF 144dpi 래스터 → vision-capable model 추출 → 본문 |
| **사진/캡쳐** (모니터·종이) | 동일하게 vision 처리 |
| **혼합** (한 환자에 여러 소스) | 가장 흔한 케이스. 영역별로 소스 매핑 후 통합 |

별도 OCR 라이브러리 추가 없이 `tools/web_intake/intake.py` 의 기존 vision 파이프라인 재사용.

스키마와 작업 절차:
- `reference/checkup-result-schema.md` — 표준 JSON schema
- `reference/checkup-result-workflow.md` — 입력 inventory → JSON → HTML → 검증 절차
- `tools/checkup_schema_validate.py` — 구조화 JSON 결정적 검증

### 모듈 구성 (8 모듈, ON/OFF)

| § | 모듈 | 컴포넌트 | 항상/선택 |
|---|---|---|---|
| §0 | **종합 판정 (Overall Verdict)** | `.stats-row` × 4 `.stat-cell` (신호등 색) | ✅ 항상 |
| §1 | 신체계측·생체징후 (Vitals) | `.stats-row` × 4 (키/체중·BMI·허리·BP) | 🔘 선택 |
| §2 | 혈액검사 (Blood) | `.lab-row` 표 5~7행 (영역끼리 묶기) | 🔘 선택 |
| §3 | 소변검사 (Urinalysis) | compact `.lab-row` 1~2행 | 🔘 선택 |
| §4 | 위·대장 내시경 (Endoscopy) | `.body-2col` × 2 `.card` (둘 다 했으면) / 단일 card (하나만) | 🔘 선택 |
| §5 | 초음파 (Ultrasound) | 단일 `.card` 안에 시행 부위 (상복부·갑상선·경동맥) bullet | 🔘 선택 |
| §6 | 심전도 (EKG) | 단일 compact `.card` | 🔘 선택 |
| §7 | 골밀도 (DXA) | `.stat-cell` × 2 (요추·대퇴) + 해석 | 🔘 선택 |
| §9 | **권장 사항·다음 단계 (Action Plan)** | `.checklist` 5항목 (즉시치료·생활습관·재검·전문과·경고) | ✅ 항상 |

§6 + §7 을 `.body-2col` 로 한 섹션에 묶어 2페이지 공간 절약 가능 (sample 참조).

### 신호등 색 매핑

§0 종합 판정의 각 영역 `.stat-cell`:
- `.stat-cell--ok` (녹색) — 정상
- `.stat-cell--low` (주황) — 주의·경계
- `.stat-cell--high` (빨강) — 이상·즉시 조치

영역 권장 4개: **대사·심혈관 / 위장 (내시경) / 갑상선·간 / 골·근골격**. 환자별로 영역명 조정 가능 (호흡기·신경계 등 추가).

### 페이지 분할 가이드

- **1페이지** (검사 3~4개 받은 환자) — §0 + §1 + §2 + §3 + §9 압축
- **2페이지** (전체 검사 받은 환자) — Page 1: §0~§3, Page 2: §4~§7 + §9
- **3페이지** (영상 narrative 매우 풍부) — Page 1: §0~§3, Page 2: §4 (내시경 상세), Page 3: §5~§7 + §9

`shared/_validate_layout` 가 `.page` 마다 자동 검증하므로 페이지 수 직접 선언 불필요. overflow 발생 시 다음 페이지로 자동 확장하는 게 아니라 작성자가 분할해야 함 (build.py 도 작성된 `.page` 갯수만큼 PDF 페이지 생성).

### 템플릿 사용

```bash
cd ~/clinic-content-system

# 1. 환자 hash slug 생성
python3 -c "import sys; sys.path.insert(0,'shared'); from _build_helpers import lab_hash_slug; print(lab_hash_slug('차트번호','환자명','health-checkup'))"
# → 예: 0d8f6f8adf

# 2. template 복사
cp -r lab-reports/health-checkup/template lab-reports/health-checkup/{hash}

# 3. index.html 편집
#    - subtitle: 환자명·차트번호·검사일·담당의·시행 검사 N종
#    - §0 신호등 4영역: ok/low/high 색 + 한 줄 요약
#    - 시행하지 않은 모듈 <section> 통째 삭제
#    - 시행한 모듈은 placeholder ◯ 값을 실제 값으로 교체
#    - lab-row badge class (정상/--high/--low) 갱신
#    - 입력 추출 정확도 + 종합 판정 신호등 ↔ 본문 일관성 자체 점검

# 4. 구조화 JSON을 따로 저장했다면 schema 검증
python3 tools/checkup_schema_validate.py _local/checkup-json/{hash}.json

# 5. _validate_layout 통과 확인
python3 -m shared._validate_layout lab-reports/health-checkup/{hash}/index.html

# 6. build.py TARGETS 추가
```

`build.py` TARGETS 등록 예시:

```python
{
    "kind": "lab-reports", "slug": "0d8f6f8adf",
    "slug_path": "lab-reports/health-checkup/0d8f6f8adf/",
    "html_path": ROOT / "lab-reports/health-checkup/0d8f6f8adf/index.html",
    "qr_class": "qr-mini__code", "fmt": "a4-portrait",
    "category": "🔬 건강검진·암검진", "audience": "환자/보호자", "disease": "종합 건강검진",
    "patient_name": "환자명", "chart_no": "차트번호",
    "exam_date": "YYYY-MM-DD", "doctor": "정지환",
    "note": "검사 N종 — 핵심 소견 + follow-up 한 줄 요약",
},
```

### Multi-agent 흐름 (health-checkup 한정)

Stage A · D 에 **checkup-extraction + checkup-completeness specialist 2명 추가** (총 7인 병렬). 점검 영역:
1. 혼합 입력 추출 — PDF·캡쳐·텍스트 source별 시행 검사 inventory와 confidence
2. 모듈 완전성 — 입력에 언급된 검사가 결과지에 모두 반영
3. follow-up 일정 — 각 이상·경계 소견에 next-step 명시
4. §0 신호등 ↔ 본문 일관성
5. §9 checklist 5 카테고리 균형 (즉시치료/생활습관/재검/전문과/경고)
6. 페이지 분할 균형

상세: `reference/quality-agents/checkup-extraction.md`, `reference/quality-agents/checkup-completeness.md`.

### 샘플

가공 환자 `lab-reports/health-checkup/0d8f6f8adf/` — 8 모듈 모두 활성, 2페이지. 디자인 시연 + 검증 통과 케이스 reference.


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
- `reference/medical-notation-style.md` — 의료 콘텐츠 표기 통일 규칙 (부등호·단위 공백·`↓`·`uACR` 등, 원장 결정 2026-06-07)
- `reference/deck-design-proportions.md` — deck 황금비율·모듈러 스케일·검증기 임계 수치 SoT (§6)
- `reference/migration.md` — 기존 PPTX 스킬에서 마이그레이션 가이드
- `shared/clinic-handout-a4.css` — A4 1장 컴포넌트 사양 (handouts / lab-reports)
