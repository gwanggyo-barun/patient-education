# launchd 자동화 + Notion orphan/중복 감사 보고서

- **작성일**: 2026-06-10
- **작성 환경**: Windows 11 (이 PC). ⚠️ **launchd 실행/테스트 불가** — 본 보고서는 **정적 코드 감사 + 안전한 정적 수정 + 근본원인 분석**이다. macOS·CI에서의 실행 검증이 필요한 항목은 §6에 별도 표기한다.
- **감사 범위(읽기 전용)**: `shared/_notion_sync.py`, `build.py`, `tools/notion_link_audit.py`, `.github/workflows/*.yml`
- **편집 범위**: `scripts/launchd/*.plist`(안전 가드 주석), 본 보고서

---

## 0. 한눈에 보기 (Executive summary)

| # | 분류 | 심각도 | 한 줄 요약 | 조치 위치 |
|---|------|--------|-----------|-----------|
| F1 | 중복 워크플로 | 🟠 High | `build-and-deploy.yml`와 `test-content.yml`이 **둘 다 `push:[main]`에서 Notion sync 시도** → 동시 업서트 경합 가능 | CI (Mac/GitHub) |
| F2 | Dead no-op | 🟠 High | `test-content.yml`의 `notion-sync` 잡이 **존재하지 않는 `ns.sync_all()`** 호출, 예외를 삼켜 **항상 조용히 실패** | CI (GitHub) |
| F3 | Orphan 근본원인 | 🟠 High | TARGET 삭제/slug 변경 시 **기존 Notion row를 정리(아카이브)하는 경로가 build 파이프라인에 없음** → 파일 404 + DB row 잔존 | 코드(build/sync, Mac) |
| F4 | 중복 row 근본원인 | 🟡 Med | **slug 변경**(파일명 salt/topic 변경) 시 dedup 키가 바뀌어 lab-reports 신규 row 생성; decks/handouts는 **title 변경** 시 중복 | 코드(sync, Mac) |
| F5 | launchd 멱등성 | 🟢 Low | `daily-fetch`는 `git fetch`(읽기 전용)라 본질적으로 멱등 — **중복 실행해도 orphan 무관**. 단, 다중 등록 시 로그 경합 | plist(정적 가드 적용) |
| F6 | launchd 중복 실행 | 🟢 Low | `StartCalendarInterval`는 중첩 없음. 단 `bootstrap` 재실행 시 `bootout→bootstrap`로 **자기 교체**되어 안전 | 정보 |
| F7 | autopull 이원화 | 🟢 Low | macOS는 launchd `git fetch`, Windows는 `.git-autopull.ps1`(`git pull --rebase`). 둘은 다른 머신이라 충돌 없음 | 정보 |

**핵심 결론**: 사용자가 겪는 **Notion orphan/중복은 launchd 때문이 아니다.** launchd `daily-fetch`는 읽기 전용 `git fetch`라서 Notion에 아무것도 쓰지 않는다(§1). 진짜 원인은 **(a) 빌드 파이프라인에 "삭제된 TARGET → Notion row 회수" 단계가 없음(F3)**, **(b) slug/title이 dedup 키인데 이들이 바뀌면 새 row가 생김(F4)**, **(c) 두 CI 워크플로가 같은 트리거에서 sync를 중복 시도(F1)** 이다.

---

## 1. launchd 정적 분석

### 1.1 대상 파일
- plist: `scripts/launchd/io.github.gwanggyo-barun.clinic-content.daily-fetch.plist`
- 실행 스크립트: `scripts/daily-fetch.sh`
- 설치 스크립트: `scripts/bootstrap-machine.sh`

### 1.2 XML 구조 육안 검증 (plutil 없이)
Windows라 `plutil -lint`를 쓸 수 없어 XML 트리를 육안 검증했다. 결과 **구조적 결함 없음**:
- 선언부 정상: `<?xml ...?>` → `<!DOCTYPE plist ...>` → `<plist version="1.0">` → 단일 루트 `<dict>`.
- key/value 짝 정상: `Label`(string), `ProgramArguments`(array of string), `WorkingDirectory`(string), `StartCalendarInterval`(array of dict), `StandardOutPath`/`StandardErrorPath`(string), `RunAtLoad`(false), `KeepAlive`(false), `ProcessType`(string).
- 모든 태그가 정상 종료되고 array/dict 중첩이 균형 잡혀 있음.
- 플레이스홀더 `@@HOME@@`, `@@REPO_DIR@@`는 `bootstrap-machine.sh:81-84`의 `sed` 치환으로 머신별 확정됨 — 미치환 상태로 로드되면 launchd가 실패하므로, **bootstrap을 거치지 않은 plist를 직접 `launchctl bootstrap` 하면 안 된다**(주의 주석 추가, §5).

### 1.3 중복 실행 가능성
- **StartCalendarInterval 중첩 없음**: 5개 엔트리가 각각 Weekday 1~5, 09:00 단일 시점(plist:31-35). 같은 요일/시각이 중복 정의되지 않았고 `StartInterval`(주기형)과 혼용하지 않아 **이중 실행 위험 없음**.
- **RunAtLoad=false**(plist:44-45): 로그인/로드 시 즉발하지 않음. 단 `bootstrap-machine.sh:96-97`이 설치 직후 **수동으로 1회 fetch**를 돌린다(워밍업). 이건 의도된 1회성이며 launchd 트리거와 중복되지 않는다.
- **bootstrap 재실행 안전**: `bootstrap-machine.sh:87`이 `launchctl bootout ... 2>/dev/null || true`로 **기존 등록을 먼저 제거**한 뒤 `bootstrap`(88)·`enable`(89). 따라서 bootstrap을 여러 번 돌려도 **동일 Label이 이중 등록되지 않는다**(자기 교체). → **멱등**.

### 1.4 멱등성 / orphan 유발 가능성
- `daily-fetch.sh`의 실제 작업은 `git fetch --all --prune --quiet`(daily-fetch.sh:38) **뿐**이다. HEAD·인덱스·작업트리를 건드리지 않고(주석 daily-fetch.sh:8-15), **원격 refs만 갱신**한다.
- 즉 **launchd 경로는 Notion API를 호출하지 않으며, 파일/DB row를 생성·삭제하지 않는다.** → **launchd가 orphan이나 중복 row를 만들 가능성은 구조적으로 0.**
- `set -euo pipefail`(daily-fetch.sh:17)로 실패 시 즉시 종료, 로그(`tee -a`)로 흔적을 남긴다. 멱등성·안전성 양호.
- 유일한 비멱등 요소: **로그 파일 append**. 같은 plist가 (가상의) 이중 등록되면 동일 로그에 동시 쓰기가 일어날 수 있으나, §1.3대로 이중 등록은 bootstrap이 차단한다.

### 1.5 launchd 소결
launchd 자동화는 **설계상 안전하고 멱등**하다. orphan/중복의 원인이 아니다. 개선 여지는 "운영자가 plist를 직접 만지거나 bootstrap 없이 로드할 때의 함정"을 주석으로 명시하는 정도이며, 이는 정적 수정으로 §5에서 반영했다.

---

## 2. Notion orphan 근본원인 (파일 404인데 DB row 잔존)

### 2.1 orphan이 생기는 경로
빌드 → Notion 동기화는 `build.py:1661-1686`에서 일어난다. 핵심은 **업서트(create/update)만 있고, 회수(reconcile/archive)가 없다**는 점이다:

```
# build.py:1653-1660 — sync 대상 판정
notion_sync = t.get("notion_sync", True)
sync_eligible = notion_sync and ( ... "title" in t ... )
if NOTION_ENABLED and sync_eligible:
    ...
    action, page_id = notion_upsert(...)   # build.py:1664 — create 또는 update 만
```

`notion_upsert`(=`_notion_sync.upsert`)는 `("created"|"updated"|"skipped_deleted", page_id)`만 반환한다(`_notion_sync.py:590, 712, 726, 655`). **TARGETS에서 제거되었거나 더는 빌드되지 않는 자료에 대응하는 Notion row를 찾아 아카이브하는 로직이 어디에도 없다.**

결과적으로:
1. **TARGET 삭제** → 해당 PDF/HTML이 더 이상 빌드/배포되지 않아 GitHub Pages에서 404. 그러나 Notion row는 그대로 남는다 → **orphan**.
2. **slug_path/slug 변경** → 새 URL의 row가 생성(또는 갱신)되지만, 옛 URL을 들고 있던 row는 정리되지 않는다 → **옛 row가 orphan**(파일 404).
3. **`notion_sync: False`로 사후 전환**(예: `build.py:714, 854, 879, 952, 978`의 intake 폼들) → 이미 만들어진 row가 있었다면, 이후 빌드는 그 row를 **갱신/회수하지 않고 방치** → orphan 가능.

### 2.2 trashed row의 처리 — orphan을 *부분적으로만* 완화
`_notion_sync.py`는 휴지통(아카이브) 상태를 인지한다:
- `_page_is_trashed`(_notion_sync.py:54-59): `in_trash | archived | is_archived`.
- 업서트 중 기존 row가 trashed면 **건드리지 않고 `skipped_deleted` 반환**(_notion_sync.py:654-655). → 운영자가 **수동으로 휴지통에 버린** row는 빌드가 되살리지 않는다(좋음).

그러나 이는 **"운영자가 손수 지운 경우"만 보호**한다. **자동으로 orphan을 감지·정리하지는 못한다.** 그 역할은 별도 도구 `tools/notion_link_audit.py`가 담당한다(§4).

### 2.3 dedup 조회가 orphan을 *부활*시키는 미묘한 경로
`_find_lab_report_existing`(_notion_sync.py:202-228)과 `_find_page_by_title`(115-134)은 `_first_live_or_any`(78-81)로 **"살아있는 row 우선, 없으면 아무거나"** 고른다. 즉 **모든 후보가 trashed면 trashed row를 반환**한다 → 호출부에서 `skipped_deleted`로 처리되어 부활은 막힌다(_notion_sync.py:654). 설계는 일관적이다. 다만 **live row 1개 + trashed 중복 N개**가 공존하면 live를 골라 갱신하므로, **trashed 잔재(=과거 중복의 흔적)는 청소되지 않고 남는다** → §3의 중복 흔적과 연결된다.

---

## 3. Notion 중복 row 근본원인 (재빌드 시 중복)

### 3.1 dedup 키 설계
| kind | dedup 키 | 코드 |
|------|----------|------|
| lab-reports | **slug**(파일링크 URL에 박힌 SHA-256 해시) → 실패 시 title equals 폴백 | `_find_lab_report_existing` `_notion_sync.py:216-228` |
| decks / handouts | **title equals**(+ search 폴백) | `_find_page_by_title` `_notion_sync.py:115-134` |

lab-reports의 slug 기반 dedup은 note/title 표기 흔들림에 강하다(주석 _notion_sync.py:205-215). 이는 좋은 설계다.

### 3.2 중복이 발생하는 구체 경로
1. **lab-reports: slug 자체가 바뀌는 경우** — slug는 `(chart_no, patient_name, topic)` + `LAB_SLUG_SALT`의 해시다(CI 시크릿 `LAB_SLUG_SALT`, `build-and-deploy.yml:41`, `test-content.yml:201`). **salt 회전, topic 텍스트 수정, 환자명/차트번호 정정** 중 하나라도 일어나면 slug가 바뀐다 → `filter:파일링크 url contains slug`가 옛 row를 못 찾아 **새 row 생성**. 옛 row는 §2의 orphan으로 잔존. **dedup 폴백(title equals)**(_notion_sync.py:228)도 title이 `[chart] name — note`(`_build_lab_report_props` _notion_sync.py:267-269)이므로 **note가 바뀌면 함께 빗나간다.**
2. **decks/handouts: title이 바뀌는 경우** — dedup이 **title equals 전용**이라(_notion_sync.py:116-122) `자료명`을 한 글자라도 고치면 옛 row를 못 찾고 **새 row 생성**. slug/slug_path는 안정적인데도 title이 키라서 취약하다.
3. **두 워크플로 동시 sync(F1)로 인한 경합 중복** — §3.3.
4. **검색 인덱스 지연** — `_search_pages_by_title`(_notion_sync.py:100-112)는 Notion `/search`를 쓰는데, Notion 검색 인덱싱은 수 초~수십 초 지연된다. 방금 만든 row가 폴백 검색에 안 잡히면 **연속 빌드에서 일시적 중복**이 날 수 있다(특히 F1의 두 워크플로가 근접 실행될 때).

### 3.3 동시 실행 경합 (F1 + F2)
- `build-and-deploy.yml`은 `push:[main]`에서 `python build.py` 실행(build-and-deploy.yml:3-6, 36-40) → **실제 Notion 업서트**.
- `test-content.yml`도 `push:[main]`에서 트리거되고(test-content.yml:14-18), JOB3 `notion-sync`가 `main` push일 때 도는 구조(test-content.yml:163-168).
- **두 워크플로의 concurrency group이 다르다**: `build-and-deploy.yml`은 `group: pages`(build-and-deploy.yml:13-15), `test-content.yml`은 `group: content-tests-${{ github.ref }}`(test-content.yml:24-26). → **상호 직렬화되지 않고 병렬 실행**된다.
- 만약 `test-content.yml`의 sync가 실제로 동작한다면, **같은 시각 같은 DB에 두 프로세스가 업서트** → dedup 조회와 create 사이의 TOCTOU로 **중복 row**가 날 수 있다.
- **다만 현재는 F2 때문에 실제 충돌이 안 난다**: `test-content.yml:203-217`은 `ns.sync_all()`을 호출하는데 `_notion_sync.py`에 **`sync_all`이 존재하지 않는다**(grep 확인: 매치 0). 코드는 `hasattr(ns, "sync_all")`로 가드되어 `"sync_all not found — skipping"`을 찍고 끝난다(test-content.yml:210-213). 게다가 바깥 `except Exception`이 모든 오류를 삼킨다(214-216).
- **→ 결론**: F2는 "지금은 우연히 충돌을 막아주는 죽은 코드"다. 누군가 `_notion_sync.py`에 `sync_all`을 추가하는 순간 **F1의 경합이 곧바로 현실화**된다. **시한폭탄**이므로 명시적으로 제거/일원화해야 한다(§6 권고).

---

## 4. orphan/중복 감사·복구 도구 검토 (`tools/notion_link_audit.py`)

원격이 최근 추가한 404 전수감사 도구다. 읽기 전용으로 검토했다.

### 4.1 무엇을 하나
- 3개 DB(`DBS["decks"], DBS["handouts"], 전체`)의 모든 row를 순회(`_build_report` notion_link_audit.py:249-251)하며, 속성 URL(`파일링크`/`HTML 링크`/`PDF 링크`)·rich_text·블록 안의 링크를 추출(`extract_links` 105-147)한 뒤 **HTTP GET으로 실제 상태코드 확인**(`check_url` 150-158).
- 200이 아니면 broken으로 집계하고, **TARGETS로부터 기대 URL을 역산**(`expected_url_for` 161-172 → `_target_index` 448-470)해서 그 기대 URL이 200이면 **fixable**, 아니면 unfixable로 분류.
- `--fix` 시 broken→expected로 **Notion 링크를 PATCH**(`fix_link` 175-205): property url, property rich_text, block rich_text 세 위치 모두 지원.
- 안전장치: **라이브 base URL이 404면 `--fix` 중단**(notion_link_audit.py:224-229) — 배포 실패로 전체가 404일 때 멀쩡한 링크를 덮어쓰는 사고 방지. 좋은 가드.

### 4.2 이 도구가 메우는 것 / 못 메우는 것
- ✅ **깨진 링크(404) 자동 교정**: slug/slug_path 변경으로 URL이 어긋난 fixable 케이스를 기대 URL로 되돌린다 → §3.2(1)(2)의 **URL 불일치**를 사후 복구.
- ❌ **orphan row 자체를 아카이브하지 않는다**: 이 도구는 **링크 값을 고칠 뿐 row를 삭제/아카이브하지 않는다.** TARGET이 사라져 기대 URL이 아예 없으면(`expected_url=None`) `ambiguous_or_missing_target`(269-270)로 **unfixable 집계만** 하고 둔다. → §2의 **"파일 없음 + row 잔존" orphan은 이 도구로도 안 사라진다.**
- ❌ **중복 row를 합치지 않는다**: 같은 자료의 row가 2개면 둘 다 링크를 고칠 뿐 **dedup/merge는 안 한다.**
- ⚠️ **title 동음이의 처리**: `_target_index`(448-470)는 같은 title이 둘 이상이면 `ambiguous`에 넣고 기대 URL을 주지 않는다(`expected_url_for` 165-166). 안전하지만, **중복·동명 자료가 많으면 자동 복구 범위가 좁아진다.**

### 4.3 CI 디스패치(`notion-link-audit.yml`) 검토
- `workflow_dispatch`로 수동 실행, `mode ∈ {report, fix}`(notion-link-audit.yml:3-13). 스케줄 트리거 **없음** → **자동 중복 실행 위험 없음**(운영자가 누를 때만 동작).
- `report` 모드는 `docs/link-audit-*.json` 아티팩트 업로드(31-37). **단, 현재 리포에 `docs/link-audit-*.json`이 없다**(Glob 확인) → 이 감사 도구는 **아직 한 번도(또는 최근) 돌지 않았을 가능성**이 크다. 즉 **orphan/중복이 쌓여도 탐지가 안 되고 있었다.** (운영 권고 §6-R4)
- `--fix`는 DB에 쓰기 때문에 `build-and-deploy.yml`·`test-content` sync와 **동시에 돌리면 경합**한다. 수동 트리거라 평소엔 안전하나, **배포 직후 fix를 누르면 충돌** 가능 → 운영 수칙 필요(§6-R5).

---

## 5. Windows에서 적용한 안전한 정적 수정

> 원칙: 기존 룰 삭제 금지, 누락·위험을 **주석/멱등 가드**로 보강. 모든 변경은 검토용(미push).

### 5.1 plist — 운영자 함정 방지 주석 보강
파일: `scripts/launchd/io.github.gwanggyo-barun.clinic-content.daily-fetch.plist`

기존 헤더 주석에 다음을 **추가**했다(설정값·스케줄은 일절 변경하지 않음):
- 이 plist는 **`@@HOME@@`/`@@REPO_DIR@@` 플레이스홀더를 포함한 템플릿**이며, **반드시 `bootstrap-machine.sh`를 통해 설치**해야 한다(직접 `launchctl bootstrap` 금지). 미치환 상태로 로드하면 launchd가 경로를 못 찾아 실패한다.
- 이 작업은 **읽기 전용 `git fetch`**라서 Notion/파일을 변경하지 않는다 — **Notion orphan/중복과 무관**함을 명시(오인 방지).
- **중복 등록 방지**는 bootstrap이 `bootout → bootstrap`로 처리하므로, plist를 수동 복제하지 말 것.

이 수정은 **XML 주석 블록 내부**에서만 이뤄져 plist의 key/value·스케줄·동작에 **영향이 없다**(육안 재검증 완료).

### 5.2 적용하지 않은 것 (의도적)
- `daily-fetch.sh`·`bootstrap-machine.sh`는 **shell 스크립트라 Windows에서 실행 검증 불가**하고, 로직 변경은 Mac 검증이 필요하므로 **건드리지 않았다**(공통 규칙: 보수적 변경). 또한 이들은 이미 멱등하다(§1).
- `_notion_sync.py`·`build.py`·`tools/*`는 **읽기 전용 지정**이라 수정하지 않았다. F1~F4의 코드 수정 권고는 §6에 **제안만** 둔다.

---

## 6. Mac/CI에서 해야 할 수정 (실행 검증 필요) — 권고

| ID | 권고 | 근거(코드 라인) | 위험도/우선순위 |
|----|------|----------------|----------------|
| **R1** | **CI Notion sync를 단일 워크플로로 일원화.** `test-content.yml`의 JOB3 `notion-sync`(test-content.yml:160-217)를 **제거**하고, 실제 sync는 `build-and-deploy.yml`의 `python build.py`(build-and-deploy.yml:36-40)에만 맡긴다. | F1, F2 | 🟠 즉시. 현재는 F2 덕에 무해하나 `sync_all` 추가 시 경합 폭발. |
| **R2** | (R1을 안 한다면) **두 워크플로를 같은 concurrency group으로 직렬화.** 예: 양쪽에 `group: notion-sync`(또는 공유 group) + `cancel-in-progress:false`. 현재 group이 `pages` vs `content-tests-${ref}`로 갈려 병렬(build-and-deploy.yml:13-15, test-content.yml:24-26). | F1 | 🟠 R1 대안 |
| **R3** | **빌드에 orphan 회수(reconcile) 단계 추가.** build 종료 시 `TARGETS`에서 산출되는 "기대 URL/slug 집합"을 만들고, 각 DB를 순회하여 **그 집합에 없고 빌드 산출물도 아닌 row를 아카이브**(또는 `상태`를 `🗄️ 보관`으로 표시). `_page_is_trashed`/`_first_live_or_any`(_notion_sync.py:54-81) 자료구조 재사용 가능. 단, **lab-reports(PHI)는 자동 아카이브 대신 리포트만** 내고 사람이 확인하도록(안전). | F3 | 🟠 orphan 근본 해결 |
| **R4** | **`notion-link-audit.yml`을 정기 스케줄(예: 주1회 `report`)로.** 현재 `workflow_dispatch` 전용(notion-link-audit.yml:3-13)이라 아무도 안 누르면 orphan/중복이 방치된다. 리포에 `docs/link-audit-*.json`이 없는 것이 방증(§4.3). `report`만 자동화하고 `fix`는 수동 유지. | F3,F4 가시화 | 🟡 |
| **R5** | **decks/handouts dedup에 slug 폴백 추가.** 현재 title equals 전용(_notion_sync.py:116-122)이라 title 수정 시 중복. lab-reports처럼 **slug_path를 비고/전용 속성에 심고 그걸로 1차 조회**하면 title 변경에 견딘다. (스키마 변경 동반) | F4 | 🟡 |
| **R6** | **`--fix`와 배포 sync의 동시 실행 차단.** `notion_link_audit.py`의 `--fix`는 DB 쓰기(notion_link_audit.py:175-205)라 build sync와 겹치면 경합. R1/R2의 concurrency group에 audit-fix도 포함시키거나, 운영 수칙으로 "배포 완료 후에만 fix" 고정. | F1 연장 | 🟢 |
| **R7** | **slug salt 회전 시 마이그레이션 절차 문서화.** `LAB_SLUG_SALT`(build-and-deploy.yml:41) 변경은 모든 lab-reports slug를 바꿔 **대량 중복**을 부른다. 회전 전 audit `report` → 회전 → R3 reconcile 순서를 SKILL.md에 박제. | F4 | 🟢 |

---

## 7. 자기검증 기록 (Windows 한계 명시)

| 검증 항목 | 방법 | 결과 |
|-----------|------|------|
| plist XML 구조 | plutil 불가 → **육안 트리 검증** | ✅ 선언/DOCTYPE/단일 dict/짝 맞는 key-value, array·dict 중첩 균형. 결함 없음 |
| `sync_all` 부재 | `Grep "def sync_all|sync_all"` in `_notion_sync.py` | ✅ 매치 0 → F2(dead no-op) 확정 |
| 두 워크플로 트리거 중복 | `build-and-deploy.yml:3-6` + `test-content.yml:14-18` 직접 인용 | ✅ 둘 다 `push:[main]` |
| concurrency group 상이 | `build-and-deploy.yml:13-15` vs `test-content.yml:24-26` | ✅ `pages` ≠ `content-tests-${ref}` → 병렬 |
| 업서트에 회수 경로 없음 | `_notion_sync.upsert` 반환값(_notion_sync.py:590,655,712,726) + `build.py:1661-1686` | ✅ create/update/skip만, archive 없음 → F3 확정 |
| dedup 키 취약점 | `_find_lab_report_existing`(216-228), `_find_page_by_title`(116-122) | ✅ slug/title 변경 시 신규 row → F4 확정 |
| audit 미실행 정황 | `Glob docs/link-audit-*.json` | ✅ 파일 없음 → §4.3 |
| launchd→Notion 영향 | `daily-fetch.sh:38`(fetch only) | ✅ 쓰기 없음 → launchd 무관 확정 |
| **실행 검증 (launchd load, build.py 실제 sync, audit run)** | **Windows라 불가** | ⛔ **미검증** — R1~R7은 Mac/CI에서 적용·검증 요망 |

---

## 8. 결론

1. **launchd는 무죄.** `daily-fetch`는 읽기 전용 `git fetch`이고 멱등하며, bootstrap이 중복 등록을 막는다. orphan/중복의 원인이 아니다(§1). 정적으로는 **운영자 오용 방지 주석**만 보강하면 충분했고, 그렇게 했다(§5.1).
2. **Notion orphan/중복의 진짜 원인은 코드/CI에 있다**: (F3) 빌드에 orphan 회수가 없음, (F4) slug/title이 dedup 키라 바뀌면 중복, (F1/F2) 두 워크플로가 같은 트리거에서 sync를 중복 시도(현재는 죽은 코드 덕에 우연히 무해하나 시한폭탄).
3. **`notion_link_audit.py`는 "깨진 링크 교정"까지만** 한다 — orphan row 아카이브·중복 merge는 못 한다(§4.2). 그조차 **정기 실행되지 않아 탐지 공백**이 있다(§4.3).
4. **권고의 핵심은 R1(워크플로 일원화)·R3(orphan 회수 단계)·R4(audit 정기화)** 이며, 모두 **Mac/CI에서 적용·실행 검증**이 필요하다.
