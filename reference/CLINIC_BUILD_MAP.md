# Clinic Content System — Build Map & Refactor Safety

> 목적: `build.py`(2079줄)·`shared/` 헬퍼·디자인 토큰을 **심볼 단위로 안전 리팩터**하기 위한 지도.
> "무엇이 어디에 있고, 무엇을 건드리면 어디가 영향받나"를 한 장에. (Serena 라이브 세션에선
> 여기 심볼명으로 find-references → 정밀 편집. 생성 2026-06-28, 구조 바뀌면 갱신.)

## 1. 빌드 파이프라인 (build.py `main()` @1782)

1. **TARGETS 순회**(@81) — 모든 자료의 manifest(`kind`/`slug`/`slug_path`/`html_path`/`url`/`notion_sync`…).
   173개 자료가 여기 1건씩. 새 자료 추가 = 여기 dict 1개 추가.
2. **render**(`shared/_build_helpers.render` @155) — HTML 로드 → QR SVG 주입(`make_qr_svg`/`inject_qr`)
   → QR URL 텍스트(`inject_qr_url_text`) → OG meta 점검(`check_og_meta`) → lab-reports는 noindex
   (`inject_noindex_meta`)·QR mini 제거(`strip_qr_mini_block`) → PDF(Playwright) + preview PNG.
3. **빌드 전 검증**(차단): `_validate_css_paths`(@1576) · `_validate_data_assets`(@1616) ·
   `_validate_lab_report_no_webp`(@1661) · `_validate_targets_routing`(@1694) · `_check_qr_populated`(@1470).
   ※ 색 토큰 검증(`_check_tokens`)·레이아웃(`_validate_layout`)은 **CI(test-content.yml)**에서 별도 실행.
4. **Notion upsert**(`shared/_notion_sync.upsert` @build 2024) — `kind`로 3개 DB 라우팅
   (📋 진료설명 decks / 📨 환자유인물 handouts / 🧪 검사결과 lab-reports). `notion_sync:False`면 스킵.

## 2. 파일·심볼 인덱스

### build.py (오케스트레이터)
| 줄 | 심볼 | 역할 |
|---|---|---|
| 81 | `TARGETS` | ⚠️★ 전 자료 manifest(추가/이동의 단일 지점) |
| 1470 | `_check_qr_populated` | QR가 실제 채워졌는지 |
| 1525 | `_decode_qr_matches` | QR 디코드=URL 일치 검증 |
| 1576 | `_validate_css_paths` | CSS/이미지 경로 존재(빌드 차단) |
| 1605 | `_sync_asset_manifest` / 1616 `_validate_data_assets` | 데이터 자산 매니페스트 |
| 1661 | `_validate_lab_report_no_webp` | 결과지 webp 금지 |
| 1694 | `_validate_targets_routing` | slug_path가 kind/로 시작(라우팅 정합) |
| 1782 | `main()` | 파이프라인 전체 |

### shared/ (실제 로직 모듈 — 모놀리스 해체 시 여기가 경계)
| 모듈 | 핵심 심볼 | 역할 |
|---|---|---|
| `_build_helpers.py` | `render`·`make_qr_svg`·`inject_qr`·`inject_qr_url_text`·`lab_hash_slug`·`inject_noindex_meta`·`strip_qr_mini_block`·`resolve_data_asset`·`load_asset_manifest` | 렌더·QR·lab 해시slug·자산 해석 |
| `_notion_sync.py` | `upsert`·`content_last_modified_iso` | kind→3 DB 라우팅 upsert |
| `_validate_layout.py` | (CLI) | bbox 레이아웃 검증(CI 차단) — 색만 바뀌면 영향 없음, 줄바꿈/간격 바뀌면 재검 필수 |
| `_check_tokens.py` | (CLI) | ⚠️ 색 토큰 린터(var(--c-*)·비브랜드 hex) — CI hard gate |
| `_image_gate.py` | ImageIntent·aboutness 채택 게이트(handout v2) |
| `_tone_score.py` | 브랜드 톤 점수 게이트(handout v2) |
| `_visual_audit.py` | 라이브 URL 렌더 실검증(CSS 로드·폰트·크기) |
| `_visual_diff.py` | 이미지 삽입 전/후 회귀 가드 |

### 디자인 시스템 (색·폰트·레이아웃의 단일 출처)
| 파일 | 무엇 |
|---|---|
| `shared/design-tokens.css` | ⚠️★ 모든 `--color-*`/`--text-*`/`--space-*`/`--radius-*` 토큰 정의(SoT). 색 바꾸면 전 자료 일괄 반영 |
| `shared/clinic-slides.css` | 16:9 슬라이드 마스터 + 7패턴 컴포넌트. body에 한글 keep-all 줄바꿈 |
| `shared/clinic-handout-a4.css` | A4 핸드아웃/결과지 마스터. body에 keep-all |
| `reference/brand-design-system.md` | 디자인 규칙 SoT(색 §2/2.1·타이포·줄바꿈 §3·패턴 §7) |
| `SKILL.md` | 스킬 규칙(색 토큰·줄바꿈 강제 명문화) |

## 3. "X 바꾸면 어디가 영향받나" (safe-refactor 가드)

- **색/토큰 변경** → `design-tokens.css` 한 곳. 단 토큰 *이름* 바꾸면 → 173 HTML + shared CSS에서
  `var(--color-X)` 전부 찾아 교체(Serena find-references / `grep -rn "var(--color-X)"`). 끝에 `_check_tokens` 통과.
- **CSS 클래스 rename**(예: `.tile`) → 173 HTML + clinic-*.css 전수. grep/Serena로 사용처 확인 후.
- **TARGETS 스키마 변경**(필드 추가/이름변경) → `main()` 소비부 + `_validate_targets_routing` +
  `_notion_sync.upsert`가 읽는 키 함께 수정.
- **render/QR 시그니처 변경**(`_build_helpers.render`) → `main()` 호출부 + 모든 호출 인자. QR 주입은
  `qr-block__code` 클래스 의존(HTML과 결합).
- **Notion 라우팅**(`_notion_sync.upsert`) → `kind` 값(decks/handouts/lab-reports)·DB id와 결합.
  결과지(lab) title 파싱 규칙([차트번호] prefix) 깨지 말 것.
- **레이아웃에 영향 주는 변경**(폰트·간격·줄바꿈) → 반드시 `_validate_layout.py` 전체 재실행(색만이면 불요).
  ⚠️ keep-all/text-wrap은 빽빽한 슬라이드 footer 넘침 유발 이력 — brand-design-system.md §3 참고.

## 4. Serena 활용(다음 세션)

clinic-content-system을 Serena 프로젝트로 활성화 → 위 ⚠️★ 심볼(`TARGETS`·`render`·`upsert`·
`_check_tokens`·디자인 토큰)에 `find_referencing_symbols`로 영향처 전수 → 정밀 편집 → `_check_tokens`
+ `_validate_layout` 통과 확인. **모놀리스 해체**(build.py→모듈)는 §2 shared 경계를 심볼 단위로 분리.
