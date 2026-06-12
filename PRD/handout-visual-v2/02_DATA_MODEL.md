# 02_DATA_MODEL — 핸드아웃 v2 비주얼 파이프라인 데이터 구조

> 앱 DB가 아니라 **빌드 파이프라인의 데이터 엔티티/스키마**. 기존 `build.py`·`_validate_layout`·PromptOps YAML과 정합.

## 관계도
```
Handout(자료 1건)
  ├─ has many → ImageSlot (본문 안 figure 슬롯)
  │                ├─ has one → ImageIntent   (이 슬롯이 설명할 본문 1개 + 비주얼 타입)
  │                ├─ has many→ ImageCandidate (생성 후보 N장)
  │                │                └─ has one → AboutnessVerdict (VLM 교차검증 결과)
  │                └─ has one → AdoptedImage   (채택 1장 or null=생략+사유)
  ├─ has one  → LayoutCheck   (삽입 전/후 visual diff + validator 결과)
  └─ has one  → ToneScore     (브랜드 일관성 점수)
```

## 엔티티

### Handout
| 필드 | 타입 | 설명 |
|------|------|------|
| slug_path | str | `handouts/{category}/{topic}/` (기존 라우팅 키) |
| topic | str | 질환·검사 주제 |
| html_path | path | 빌드 산출 HTML |
| status | enum | draft / images_pending / verified / published |
| build_report | obj | 아래 LayoutCheck·ToneScore·이미지 요약 집계 |

### ImageSlot
| 필드 | 타입 | 설명 |
|------|------|------|
| id | str | 슬롯 식별자(예: `.ai-visual-1`) |
| w_mm,h_mm,aspect | num | 실측 슬롯 크기(레이아웃 확정 후) |
| intent_ref | ImageIntent | 이 슬롯이 설명할 대상 |

### ImageIntent  ★v2 신규 — P1(겉도는 이미지) 해결의 핵심
| 필드 | 타입 | 설명 |
|------|------|------|
| explains | str | **이 이미지가 설명할 본문 문장/표/체크리스트 1개**(필수, 자유서술) |
| visual_type | enum | Anatomy / Mechanism / Process / Equipment / Action / Comparison (그 외=슬롯 생성 금지) |
| must_show | str[] | 이미지에 반드시 보여야 할 요소(검증 기준) |
| prompt_en | str | 슬롯 비율 명시한 영문 imagegen 프롬프트 |

### ImageCandidate / AboutnessVerdict  ★v2 신규 — P2(불안정성)·P1
| 필드 | 타입 | 설명 |
|------|------|------|
| file | path | 생성 후보 |
| gen_path | enum | $imagegen / codex_imagen / fallback |
| verdict.depicts_intent | bool | VLM: 이미지가 `explains`/`must_show`를 실제로 묘사하는가 |
| verdict.aboutness | num(0~100) | 관련성 점수(임계 ≥ T_about) |
| verdict.quality | num | 해상도·왜곡·한글텍스트혼입(금지) 등 품질 |
| verdict.reasons | str[] | 통과/탈락 근거 |

### AdoptedImage
| 필드 | 타입 | 설명 |
|------|------|------|
| candidate_ref | id | 채택 후보(없으면 null) |
| skipped_reason | str | 생략 시 사유(예: "적합 visual_type 없음", "aboutness<T") |

### LayoutCheck  ★v2 강화 — P3(깨짐)
| 필드 | 타입 | 설명 |
|------|------|------|
| validator | obj | `_validate_layout` 결과(box_underfill·box_content_overflow·body_overlaps_footer·body_underfills·sparse_box…) |
| before_png / after_png | path | 이미지 삽입 전/후 스냅샷 |
| visual_diff | obj | 회귀 지표(겹침·잘림·여백 변화). regressed=bool |
| passed | bool | validator∧¬regressed |

### ToneScore  ★v2 신규 — P4(일관성)
| 필드 | 타입 | 설명 |
|------|------|------|
| palette_dist | num | brand 토큰 색과의 거리 |
| typo_ok | bool | 폰트(Pretendard)·스케일 준수 |
| image_style_ok | bool | 이미지 스타일(브랜드 가이드) 일치 |
| score | num(0~100) | 가중 합(임계 ≥ T_tone) |

## 불변식(Invariant)
- I1. `AdoptedImage`는 `AboutnessVerdict.depicts_intent==true ∧ aboutness≥T_about`일 때만 존재. 아니면 `skipped_reason` 필수.
- I2. `Handout.status=published`는 모든 슬롯이 (채택∨명시적 생략) ∧ `LayoutCheck.passed` ∧ `ToneScore.score≥T_tone`.
- I3. 이미지 내 한글 텍스트 금지(기존 룰) — quality 검증에 포함.
- I4. SVG icon/context strip은 이미지 보강으로 불인정(기존 §15) — visual_type에 미포함.
