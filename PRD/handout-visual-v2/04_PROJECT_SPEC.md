# 04_PROJECT_SPEC — 스킬 행동 규칙 (AI 구현 가이드)

> 이 PRD를 구현하는 에이전트가 지켜야 할 규칙. 기존 `SKILL.md`·`AGENTS.md`·`reference/*`와 정합되게 **편집·커밋**한다(룰 SoT=repo).

## 0. 구현 원칙
- **SoT는 repo**: 룰 변경은 SKILL.md/`reference/image-assets.md`/`shared/` 코드 편집 + commit + push. 메모리엔 포인터·사용자 톤 선호만.
- **하위호환 우선**: handouts 경로에 먼저. decks/lab-reports·Notion 라우팅·build.py 기존 동작 깨지 않기. 게이트는 기본 ON이되 환경변수로 단계적 롤아웃 가능하게.
- **사람 개입 0 기본**: 생성·검증·보정·커밋·푸시 자동. 실패(생성 불가·게이트 반복 미달)만 사용자 에스컬레이션.
- **결정론**: 같은 입력→같은 슬롯/검증. 후보 이미지·검증 결과는 build_report에 남겨 재현·디버그 가능.

## 1. Step 3.5 (이미지) 변경 — aboutness 우선
1. 레이아웃 확정 후 슬롯 실측(기존).
2. 슬롯마다 **`ImageIntent` 작성 필수**: `explains`(설명할 본문 1개) + `visual_type`(Anatomy/Mechanism/Process/Equipment/Action/Comparison 중) + `must_show[]`. 적합 visual_type 없으면 **슬롯 만들지 말고** 텍스트/표/여백으로 가독성 개선.
3. 프롬프트는 슬롯 비율 명시 + must_show 반영. 후보 2~3장 생성(재시도 포함).
4. 각 후보 **aboutness 교차검증**(VLM): `depicts_intent`·`aboutness(0~100)`·`quality`·근거. 임계 미달이면 재생성 1회 → 그래도 미달이면 생략+사유.
5. 채택 1장만 슬롯에 배치.

## 2. 이미지 채택 게이트(하드)
- 채택 ⇔ `depicts_intent==true ∧ aboutness≥T_about ∧ quality OK(한글텍스트 0·왜곡 없음)`.
- 미달 = 빈 슬롯 남기지 말고 제거 + `skipped_reason` 기록.
- **"이미지 개수 채우기" 금지**(기존 §15): 같은 정보 반복·generic·장식 이미지·SVG strip은 보강 불인정.

## 3. 레이아웃 회귀 가드
- 이미지 삽입 **전/후 스냅샷** → visual diff. `_validate_layout` 강화 체크와 **AND**. 둘 중 하나라도 실패면 슬롯 크기·배치 자동 보정 후 재검(최대 N회), 그래도 실패면 이미지 생략.
- Step 3.8 전수 육안검수는 유지하되 diff가 가리키는 페이지를 우선 확인.

## 4. 톤·일관성
- 빌드 시 `ToneScore`(색·폰트·이미지스타일 vs brand 토큰). 임계 미달 경고/차단.
- imagegen 프롬프트에 **브랜드 스타일 디스크립터 표준 문구**를 항상 삽입(자료 간 이미지 톤 통일). 디스크립터 SoT=`reference/brand-design-system.md`.

## 5. 보고 포맷(완료 시)
```
✅ {topic} 핸드아웃 — verified
🖼 이미지: N장 채택 / M장 생략
  • slot1 [Process] aboutness 88 — "{explains}"
  • slot2 생략 — 적합 visual_type 없음
📐 레이아웃: 0 깨짐 (validator pass, diff regress 0)
🎨 톤: 92/100
```

## 6. 게이트 임계(초기값, 캘리브레이션 대상)
- `T_about` = 70 (초기), 사람 스팟체크로 조정.
- visual diff 회귀 임계: 겹침/잘림 0 허용, 여백 변화 N% 이내.
- `T_tone` = 80 (초기).

## 7. 테스트(evals)
- aboutness: 의도와 무관한 이미지 샘플이 게이트에서 탈락하는지.
- visual-diff: 일부러 깨진 레이아웃이 차단되는지.
- tone: 브랜드 외 색/폰트가 감점되는지.
- 회귀: 기존 대표 핸드아웃(bone-density-prep·colonoscopy-prep·insulin-start 등) 재빌드 시 품질 유지.

## 8. 안티패턴(하지 말 것)
- 빈 슬롯 HTML 잔존, generic/장식 이미지 채택, SVG strip을 이미지로 간주.
- 검증기 통과만으로 "완성" 보고(시각/aboutness 게이트 누락).
- 룰을 메모리에만 적고 repo 미반영.
