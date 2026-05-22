# Asset Library

이 디렉터리는 슬라이드(`decks/`), 핸드아웃(`handouts/`), 검사결과(`lab-reports/`)에서
공통으로 쓰는 이미지 자산의 단일 출처입니다. `SKILL.md`에는 한 줄 포인터만 두고,
운영 규칙은 모두 이 문서에 있습니다.

## 구조

```
shared/assets/
  clinic_logo.png             # 의원 로고 (전 자료 공통)
  generated/                  # AI 생성 / 수작업 자산
  healthicons/                # Healthicons 벤더 SVG (자동 관리)
    LICENSE                   # MIT 라이선스 사본 (attribution)
    filled/<topic>/*.svg
    outline/<topic>/*.svg
  manifest.json               # 큐레이션 자산 메타데이터 (수동·자동 혼합)
  healthicons.manifest.json   # Healthicons 메타데이터 (전부 자동 생성)
  README.md                   # 이 문서
```

신규 카테고리 폴더(`medical/`, `lifestyle/`, `ui/` 등)는 자산이 의미적으로 그룹화
가능한 임계점에 도달했을 때만 추가합니다. 폴더 이주는 **manifest.json 안에서**
`aliases` 필드를 통해 점진적으로 처리합니다 — 기존 HTML을 깨뜨리지 않습니다.

## manifest.json — 단일 출처

`tools/sync_manifest.py` 가 디스크와 manifest를 양방향 동기화합니다.
`build.py` 가 매 빌드 시작 시 자동 실행하므로, 새 이미지를 디렉터리에 떨어뜨리면
**다음 빌드에서 자동으로 등록**됩니다.

### 엔트리 스키마

```jsonc
{
  "appendicitis-rebound-tenderness-20260511": {
    "file": "generated/appendicitis-rebound-tenderness-20260511.png",
    "format": "png",
    "bytes": 1473044,
    "exists": true,
    "category": "gi-emergency",
    "tags": ["abdomen", "physical-exam"],   // 자유 태그 (검색용)
    "alt_ko": "우측 하복부 통증과 반발 압통을 …",   // PDF/스크린리더 alt
    "review_status": "approved",            // pending | approved | retired
    "reviewed_by": "정지환",
    "review_date": "2026-05-21",
    "use_in": ["handout"],                  // deck | handout | lab-report | all
    "aliases": [],                          // 옛 키 → 현재 키로 fallback
    "generation_prompt": null,              // AI 생성 시 프롬프트 보존
    "known_issues": null                    // 임상/디자인 주의사항
  }
}
```

### 자동 갱신 대상 / 수동 큐레이션 대상

| 필드 | 누가 채우나 |
|------|----------|
| `file`, `format`, `bytes`, `exists` | sync_manifest.py 자동 |
| `category` | sync_manifest.py 추정 → 사람이 보정 |
| `alt_ko` | 기존 HTML에서 자동 백필 → 사람 검수 |
| `tags`, `use_in` | 사람 |
| `review_status`, `reviewed_by`, `review_date` | 사람 (임상 검수) |
| `aliases` | 사람 (파일명 변경 시) |
| `generation_prompt`, `known_issues` | 사람 |

## 사용 방법: `data-asset="key"` (권장)

### 새 HTML 작성 시

```html
<img data-asset="egd-prep-fasting-clock-20260513">
```

빌드 시 `_build_helpers.resolve_data_asset()` 가 다음을 수행합니다.

1. `manifest.json` 에서 `key` 조회 (없으면 `aliases` fallback).
2. `html_path` 기준 상대 경로로 `src=` 자동 계산 (3-level/4-level 디렉터리 문제 자동 해결).
3. `alt=` 가 비어 있으면 manifest의 `alt_ko` 자동 삽입.
4. `data-asset` 속성은 **그대로 유지** — 다음 빌드에서 다시 해석 가능 (재이름 안전).

빌드 후 HTML 예:

```html
<img data-asset="egd-prep-fasting-clock-20260513"
     src="../../../shared/assets/generated/egd-prep-fasting-clock-20260513.png"
     alt="금식 시계 — 위가 비어있어야 정확한 검사가 가능합니다">
```

### 레거시 호환

기존 `<img src="../../../shared/assets/...">` 코드는 그대로 작동합니다.
강제 이주는 하지 않습니다. 새 자료부터 `data-asset` 사용을 권장합니다.

### per-instance alt 오버라이드

특정 위치에서만 다른 alt 가 필요하면 그냥 직접 적습니다.

```html
<img data-asset="egd-prep-fasting-clock-20260513"
     alt="이 슬라이드에 맞춘 짧은 설명">
```

build 가 비어있지 않은 alt 는 건드리지 않습니다.

## 새 자산 추가 워크플로

1. 이미지 파일을 `shared/assets/generated/` (또는 적절한 카테고리 폴더)에 둠.
2. `python3 tools/sync_manifest.py` 실행 (또는 다음 build 까지 기다림).
3. `manifest.json` 신규 엔트리에서 `alt_ko`, `tags`, `review_status` 채우기.
4. HTML 에서 `<img data-asset="새-키">` 로 사용.
5. `python3 tools/asset_lint.py` 로 검증.

## 임상 검수 게이트

`review_status` 값:
- `pending` — 자동 생성 직후 기본값. **빌드는 통과 (경고)**, 프로덕션 lint(`--strict`)는 차단.
- `approved` — 의사가 임상·해부학적 정확성 확인 완료.
- `retired` — 더 이상 쓰지 않음. lint 가 경고. 시간 두고 제거.

CI prod job 에서는 `python3 tools/asset_lint.py --strict` 로 호출하여
`pending` 자산이 환자 자료에 섞이지 않도록 합니다.

## Healthicons (벤더된 의료 아이콘 라이브러리)

[Healthicons](https://github.com/resolvetosavelives/healthicons) (MIT,
Resolve to Save Lives / WHO 협업)을 **약 1,500개 SVG** 벤더링한 상태입니다.
시각적으로 가볍고(<10KB/icon) 임상 정확도가 사전 검증된 아이콘이라 슬라이드,
핸드아웃, 검사결과 모두에서 그대로 사용할 수 있습니다.

### 사용

큐레이션 자산과 똑같은 `data-asset` 패턴입니다.

```html
<img data-asset="hi-filled-heart-organ" class="icon-md">
<img data-asset="hi-outline-blood-pressure_monitor" alt="가정 혈압계 — 매일 같은 시간 측정">
```

- 키 네이밍: `hi-<style>-<name>` (style ∈ {`filled`, `outline`}).
  같은 name이 여러 topic에 존재할 때만 `hi-<style>-<topic>-<name>` 형태로 확장.
- 자주 쓰는 약 100개 아이콘은 한국어 alt가 시드되어 있음 (`tools/healthicons_alt_ko.json`).
  나머지는 use site에서 alt 직접 작성 권장 — 빈 alt 상태에서 빌드는 `data-asset='X'
  has no alt_ko in manifest` warning을 띄움.
- 매니페스트 자체는 `shared/assets/healthicons.manifest.json` 에 분리 보관 — PR diff
  깨끗하게, 큐레이션 풀과 검수 게이트를 분리.

### 갱신 / 재현

```bash
python3 tools/sync_healthicons.py          # 핀된 SHA로 sparse fetch + 매니페스트 재생성
python3 tools/sync_healthicons.py --check  # 매니페스트와 디스크 일치 검사 (write 없음)
```

`tools/sync_healthicons.py` 의 `HEALTHICONS_REF` 상수를 갱신하면 다음 sync 때 새
업스트림 SHA로 교체됩니다. 재현성을 위해 항상 **커밋 SHA**로 핀하며 `main` 같은
이동 ref는 피합니다.

### 한국어 alt 시드 추가

`tools/healthicons_alt_ko.json` 에 `"<manifest-key>": "<한글 alt>"` 추가 → 
`python3 tools/sync_healthicons.py` 실행.  존재하지 않는 키를 적으면 sync가 
경고(`⚠️ N seed alt key(s) not in manifest`)를 출력하므로 오타가 silent 되지 
않습니다.

### 큐레이션 manifest로 오버라이드

`shared/assets/manifest.json` 에 같은 키를 추가하면 해당 엔트리가 healthicons.manifest.json
보다 우선합니다.  현장에서 특정 아이콘의 alt나 category를 의원 컨벤션에 맞게
바꿔야 할 때 사용 — 단, **파일 자체를 교체하려면** healthicons 폴더 밖에 두고
`file` 필드를 그쪽으로 가리키게 해야 합니다 (다음 sync 가 healthicons/ 하위
파일을 덮어쓰기 때문).

## lab-reports 특수 규칙

- **WebP 금지** — 일부 PDF 렌더러에서 빈 사각형으로 출력됨. `png/jpg/svg` 만.
- `data-asset` 자산이 `format: "webp"` 이면 build pre-flight 차단.

## 파일명 규칙

- **금지** — 환자명(한글), 7자리 차트번호, 주민번호 패턴. `asset_lint.py` 가 차단.
- **권장** — `{토픽}-{서브토픽}-{버전}-{YYYYMMDD}.{ext}`.
  예: `egd-prep-fasting-clock-20260513.png`.
- 버전 이주 시 `manifest.json` 의 `aliases` 에 옛 키를 넣고 새 키로 교체.

## 빌드 통합 한 줄

`build.py main()` 의 pre-flight 체인:

1. `_sync_asset_manifest()` — 디스크 → manifest 동기화.
2. `_validate_targets_routing()` — 기존.
3. `_validate_data_assets()` — `data-asset` 키 전부 manifest 에 존재하고 파일이 디스크에 있는지.
4. `_validate_lab_report_no_webp()` — 검사결과 WebP 사용 차단.
5. `_validate_css_paths()` — 기존.

각 TARGETS 빌드 루프 안에서 `resolve_data_asset(html, html_path)` 가
`data-asset` → `src`/`alt` 치환을 수행한 뒤 QR 주입·렌더가 진행됩니다.

## 도구

| 명령 | 용도 |
|------|------|
| `python3 tools/sync_manifest.py` | 큐레이션 manifest ↔ 디스크 동기화 (build.py 가 자동 호출, healthicons/ 서브트리는 제외) |
| `python3 tools/sync_healthicons.py` | Healthicons upstream sparse fetch + healthicons.manifest.json 재생성 (수동 실행) |
| `python3 tools/sync_healthicons.py --check` | 벤더된 트리가 healthicons.manifest.json 과 일치하는지 검증 (write 없음) |
| `python3 tools/asset_lint.py` | 자산 위생 점검 (경고 1, 에러 2, 정상 0 exit) — 두 매니페스트 모두 검사 |
| `python3 tools/asset_lint.py --strict` | 경고를 에러로 승격 (CI prod 게이트용) |
| `python3 tools/asset_lint.py --warn-only` | 에러여도 0 반환 (정보용) |

## 알려진 제약

- 현재 `data-asset` 은 `<img>` 태그에만 적용됩니다. `<div style="background-image: url(...)">` 패턴은 레거시 `src` 방식 그대로 사용하세요.
- manifest 는 한 파일에 모든 자산을 담습니다. 200+ 자산을 넘으면 분할(`manifest/medical.json`, `manifest/lab.json` …) 을 검토합니다.
- 동일 stem 의 파일이 여러 폴더에 있으면 sync 가 `-2`, `-3` 접미사로 키를 자동 분리합니다. 명확한 키를 원하면 manifest 의 `key` 필드를 수동 설정하세요.
