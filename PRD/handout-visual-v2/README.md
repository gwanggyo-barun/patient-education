# 핸드아웃 스킬 v2 — 비주얼·레이아웃·톤 하드닝 (기획서)

> 광교바른내과 환자설명 핸드아웃 생성 스킬(`clinic-content-system/handouts`) 업데이트 PRD.
> 생성: 2026-06-12 (show-me-the-prd 인터뷰 기반) · SoT=이 repo.

## 한 줄
환자가 **글이 아니라 그림으로 이해**하도록 — 겉도는 이미지·생성 불안정·레이아웃 깨짐·톤 비일관을 **자동 게이트로 강제**하는 v2.

## 문서
| 파일 | 내용 |
|------|------|
| [01_PRD.md](01_PRD.md) | 문제(P1~P4)·목표·요구사항·성공지표 |
| [02_DATA_MODEL.md](02_DATA_MODEL.md) | ImageIntent·AboutnessVerdict·LayoutCheck·ToneScore 등 파이프라인 엔티티 |
| [03_PHASES.md](03_PHASES.md) | Phase 1(aboutness)→2(안정생성)→3(레이아웃가드)→4(톤)→5(확장) |
| [04_PROJECT_SPEC.md](04_PROJECT_SPEC.md) | 스킬 행동 규칙·게이트·보고포맷·안티패턴 |

## 핵심 페인포인트(사용자, 2026-06-12)
1. 이미지가 본문을 못 아우르고 **겉돔** → ImageIntent + aboutness 게이트(P1, Phase1 키스톤)
2. 이미지 **생성 불안정** → 재시도·후보비교·fallback(P2)
3. **레이아웃 깨짐** → 삽입 전/후 visual diff + validator AND 게이트(P3)
4. **톤·디자인 비일관** → ToneScore 빌드 게이트(P4)

## 다음 단계
- Phase 1부터 `SKILL.md` Step 3.5 + `reference/image-assets.md` + `shared/` 코드에 게이트 구현 → commit/push.
- 임계값(T_about·T_tone·diff)은 초기값 후 사람 스팟체크로 캘리브레이션.
- 승인 시 `/goal` 등으로 Phase 1 구현 착수 가능.
