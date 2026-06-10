# Notion 동기화 운영 가이드 (sync · reconcile · salt rotation)

- **작성일**: 2026-06-10
- **근거**: `docs/launchd-notion-audit-20260610.md` (F1~F4 / R1~R7)
- **대상 코드**: `build.py`, `shared/_notion_sync.py`, `tools/notion_link_audit.py`,
  `.github/workflows/{build-and-deploy,test-content,notion-link-audit}.yml`

이 문서는 환자 교육 콘텐츠가 Notion 3개 DB(decks / handouts / lab-reports)에
등록·갱신·정리되는 전체 흐름과, orphan(파일 404 + row 잔존)·중복 row를 막기 위한
운영 수칙을 정리한다.

---

## 1. 동기화는 한 곳에서만 — `build-and-deploy.yml`

`main` push 시 Notion 업서트는 **`build-and-deploy.yml`의 `python build.py`가 단독으로**
수행한다(SoT 일원화, R1). `test-content.yml`에는 더 이상 Notion sync 잡이 없다.

- ❌ **재도입 금지**: 과거 `test-content.yml`에 있던 `notion-sync` 잡은 (a) 존재하지
  않는 `_notion_sync.sync_all()`을 부르는 죽은 코드(F2)였고, (b) `build-and-deploy`와
  concurrency group이 달라(`pages` vs `content-tests-${ref}`) 같은 push에서 병렬
  업서트 → dedup 조회와 create 사이 TOCTOU로 **중복 row**를 만들 수 있었다(F1).
- Notion sync를 또 추가해야 한다면, 반드시 `build-and-deploy`의 흐름 안에 넣거나
  같은 concurrency group으로 직렬화할 것.

---

## 2. 중복 방지 — dedup 키 모델

| kind | 1차 키 | 폴백 | 코드 |
|------|--------|------|------|
| lab-reports | 파일링크 URL 안의 **slug**(SHA-256, `LAB_SLUG_SALT`) `contains` | 환자명(title) equals | `_find_lab_report_existing` |
| decks / handouts | **자료명(title)** equals | **파일링크 URL** equals (= `…/output/{kind}/{slug}.pdf`) | `_find_deck_handout_existing` |

- decks/handouts의 URL 폴백(R5)은 **추가(additive)** 동작이다. 자료명이 그대로면 1차
  키에서 끝나고 폴백 쿼리는 나가지 않는다. **자료명을 수정**했을 때만 폴백이 작동해
  안정적인 파일링크 URL(slug 기반)로 기존 row를 찾아 **갱신**한다 → 중복 생성 방지.
  스키마 변경이 필요 없다(파일링크는 2026-06-06 이후 모든 deck/handout row에 채워짐).
- slug 자체가 바뀌면(아래 §4의 salt 회전, 또는 slug_path 변경) URL 키도 빗나가
  신규 row가 생긴다. 이 경우 옛 row는 §3의 reconcile로 정리한다.

---

## 3. Orphan 정리 — `tools/notion_link_audit.py --reconcile`

**orphan** = 파일링크 PDF(`{BASE_URL}/output/{kind}/{slug}.pdf`)가 **하드 404**인데
Notion row는 남아 있는 상태. TARGET 삭제 또는 slug 변경이 원인(F3).

```bash
# 1) 무엇이 orphan인지만 본다 (Notion에 아무것도 쓰지 않음 — 항상 먼저 실행)
python3 tools/notion_link_audit.py --reconcile

# 2) 검토 후, decks/handouts 의 확정 orphan만 아카이브 (휴지통 이동, 복구 가능)
python3 tools/notion_link_audit.py --reconcile-archive
```

안전 모델(의도적으로 보수적):

- **파일링크가 `…/output/{kind}/` 로 시작하는 빌드 관리 row만** 후보. 수동 등록 row나
  다른 링크는 절대 건드리지 않는다.
- 아카이브 조건은 **하드 404 + 현재 TARGETS 기대집합에 부재** 둘 다. 200(여전히
  라이브)·0/5xx(일시 오류)는 리포트만 하고 아카이브하지 않는다.
- **lab-reports는 PHI라 자동 아카이브 안 함.** `--reconcile-archive` 를 줘도
  lab-reports orphan은 **page_id(+ 해시 slug URL, 환자명 없음)** 로만 리포트되고,
  사람이 Notion에서 직접 검토·아카이브한다. (콘솔/리포트에 환자명·title 미출력)
- **mass-archive 가드**: 라이브 base URL이 200이 아니면(배포 실패 등) 모든 row가
  404처럼 보이므로 아카이브를 **전면 비활성화**하고 리포트만 낸다(종료코드 2).
- 리포트는 `docs/notion-reconcile-<UTC날짜>.json` 에 기록되고 `.gitignore`로 git에서
  제외된다(PHI 보호). CI에서는 아티팩트로 업로드된다.

> ⚠️ `--reconcile-archive` 실제 실행과 라이브 반영은 **원장 검토 후**. 먼저
> `--reconcile` 리포트를 공유해 "무엇을 아카이브할지" 목록을 확인받는다.

정기 탐지(R4): `notion-link-audit.yml`이 **매주 월 00:00 UTC(09:00 KST)** 에
`report` 모드로 자동 실행된다. 쓰기 모드(`fix` / `reconcile-archive`)는 수동
`workflow_dispatch` 전용이다.

---

## 4. `LAB_SLUG_SALT` 회전 절차 (⚠️ 대량 중복 위험)

lab-report slug = `hash(chart_no, patient_name, topic, LAB_SLUG_SALT)`. **salt를
바꾸면 모든 lab-report의 slug → 파일링크 URL이 통째로 바뀐다.** 그 결과:

- 다음 빌드의 slug 기반 dedup이 옛 row를 못 찾아 **모든 lab-report에 신규 row 생성**
  (대량 중복), 그리고 재배포 후 옛 URL은 404가 되어 옛 row는 전부 **orphan**.
- 이미 환자에게 공유한 링크(옛 URL)도 전부 404가 된다.

**그래서 salt는 꼭 필요할 때만 회전한다.** 회전이 불가피하면 다음 순서를 지킨다:

1. **(전)** 베이스라인 스냅샷: `--report` 와 `--reconcile` 를 돌려 현재 상태와
   lab-reports row 수를 기록.
2. **회전**: GitHub repo secret `LAB_SLUG_SALT` 와 로컬 시크릿(macOS Keychain 등)을
   **동일 값**으로 교체. (둘이 어긋나면 로컬·CI 빌드가 서로 다른 slug를 만든다.)
3. **전체 재빌드/배포**: `build-and-deploy` 실행 → 새 slug로 모든 lab-report HTML/PDF
   재생성 + 새 row 생성. 배포가 라이브로 반영될 때까지 대기.
4. **(후)** 옛 row 정리: 이제 옛 URL이 404 → `--reconcile` 로 lab-reports orphan
   목록(page_id)을 뽑아 **사람이 Notion에서 수동 아카이브**(PHI라 자동 금지).
   필요하면 환자 마스터 페이지의 누적 이력과 대조.
5. decks/handouts는 `LAB_SLUG_SALT` 와 무관(salt를 안 쓰는 slug)하므로 영향 없음.
6. 활성 링크 재전송: 옛 URL을 받은 환자에게 새 링크를 다시 보낸다. 가능하면
   진료·발송이 적은 시간대에 회전한다.

절대 금지: **회전과 동시에 `--fix` / `--reconcile-archive` 를 돌리지 말 것**(§5).

---

## 5. 동시 실행 수칙 (R6)

- `notion-link-audit.yml` 은 자기 자신과 직렬화된다(concurrency group `notion-write`,
  `cancel-in-progress: false`) → `fix` / `reconcile-archive` 두 실행이 겹쳐 같은 DB를
  경합하지 않는다. 진행 중인 쓰기는 중간에 취소되지 않고 끝까지 수행된다.
- 단, 이 group은 `build-and-deploy.yml` 의 `python build.py` sync까지 직렬화하지는
  **못한다**(그 워크플로는 Pages 배포 때문에 group `pages` 를 가져야 함).
  → **운영 수칙**: 배포(`build-and-deploy`)가 도는 동안에는 `fix` /
  `reconcile-archive` 를 dispatch하지 말 것. 배포 완료(라이브 반영) 후에 실행한다.
  (mass-archive 가드가 최악은 막지만, 경합 자체는 수칙으로 피한다.)

---

## 6. 명령 빠른 참조

```bash
# 로컬 빌드 무결성 확인 (Notion 미접속 — sync SKIP)
NOTION_TOKEN= python3 build.py

# 깨진 링크 census (dry-run)
python3 tools/notion_link_audit.py --report
# 깨진 링크 자동 교정 (배포 완료 후에만)
python3 tools/notion_link_audit.py --fix

# orphan 목록 (dry-run, Notion 미변경)
python3 tools/notion_link_audit.py --reconcile
# decks/handouts orphan 아카이브 (lab-reports는 리포트만; 원장 검토 후)
python3 tools/notion_link_audit.py --reconcile-archive
```
