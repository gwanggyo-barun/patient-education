# 기존 스킬 마이그레이션 가이드

> 이 문서는 광교바른내과의 기존 세 스킬(patient-education-pptx, patient-handout-pdf, lab-report-infographic)을 새 `clinic-content-system`의 디자인 시스템과 통일시키는 방법을 안내한다.

## 목표

세 가지 일관성 확보:
1. **컬러 팔레트** — Navy/Steel Blue 단일 시스템 (이미 거의 일치)
2. **폰트** — Pretendard Variable 1차, Noto Sans KR fallback
3. **톤 & 보이스** — 영문 라벨, 의학 용어 영문 병기, Superhuman 디자인 원칙

## 권장 마이그레이션 순서

각 스킬마다 영향도가 다르므로 순서대로 진행한다:

### Phase 1 — 디자인 시스템 문서 공유 (지금 완료)

`reference/brand-design-system.md`를 단일 진실의 원천으로 만들었다. 모든 스킬이 이 문서를 참조한다.

### Phase 2 — 폰트 통일 (가장 즉각적 효과)

세 스킬 모두 `Noto Sans KR` → `Pretendard` 1차로 변경.

#### patient-handout-pdf
```python
# A4 PDF 생성 시 폰트 지정 부분 변경
slide.addText("...", {
    fontFace: "Pretendard",  # 기존: "Noto Sans KR"
    # ... 나머지 옵션
})
```

WeasyPrint 사용 시 CSS:
```css
@font-face {
  font-family: 'Pretendard';
  src: url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
}
body { font-family: 'Pretendard', 'Noto Sans KR', sans-serif; }
```

#### patient-education-pptx (legacy)
```javascript
// PptxGenJS의 fontFace 옵션
slide.addText("...", {
  fontFace: "Pretendard",  // 기존: "Noto Sans KR"
  // ...
});
```

⚠️ **주의**: PPTX는 PowerPoint 사용자 PC에 폰트가 설치돼 있어야 표시된다. 클리닉 PC에 Pretendard 설치 필요. 미설치 시 자동으로 fallback 폰트로 표시되며, 디자인이 깨질 수 있다.

#### lab-report-infographic
출력 형식에 따라 위 두 가지 중 적용.

### Phase 3 — 컬러 토큰 동기화

세 스킬의 색상 정의가 모두 `brand-design-system.md`의 §2 팔레트와 일치하는지 확인. 이미 거의 동일하지만 다음 항목 점검:

- [ ] Primary Navy: `#003366` ✓
- [ ] Secondary Blue (Steel): `#5B9BD5` ✓
- [ ] Body Text: `#1E293B` ✓
- [ ] Slate Gray: `#64748B` ✓
- [ ] Card Border: `#E2E8F0` ✓
- [ ] Slide BG: 기존 `#F8FAFC` → **새 시스템 `#FAFAF7` (warm) 또는 `#FFFFFF`로 변경 권장**

### Phase 4 — 톤 통일 (점진적)

기존 스킬의 SKILL.md 또는 시스템 프롬프트에 추가:

```markdown
## 디자인 시스템 (필수 참조)

이 스킬의 디자인 톤·컬러·폰트는 `clinic-content-system/reference/brand-design-system.md`를 따른다.
새 콘텐츠 작성 전 반드시 해당 문서를 먼저 읽는다.

핵심 규칙:
- 컬러: Navy(#003366) + Steel Blue(#5B9BD5) 외 추가 금지
- 폰트: Pretendard 1차, Noto Sans KR fallback
- 영문 라벨 사용 (CHAPTER, FACTOR, RULE, PHASE 등)
- 의학 용어 영문 병기
- 출처 명시 (가이드라인 + 연도)
```

### Phase 5 — 점진적 폐기 (선택)

`patient-education-pptx`는 새 `clinic-content-system`이 출력 측면에서 상위 호환이다. 다음 시나리오에서만 PPTX 스킬 유지:

- 동료 의사가 PPTX 파일을 직접 편집해야 하는 경우
- 학회 발표용 템플릿이 PPTX 형식 강제일 때
- 외부 협업자에게 .pptx 파일 자체를 전달해야 할 때

이외의 모든 환자 교육 슬라이드는 `clinic-content-system`으로 전환한다.

## 스킬별 마이그레이션 체크리스트

### patient-handout-pdf

- [ ] `references/design-system.md`에서 Pretendard 폰트 추가 명시
- [ ] 빌드 코드에서 `fontFace: "Pretendard"`로 변경
- [ ] 테스트: 기존 유인물 한 장을 새 폰트로 재빌드해서 비교
- [ ] SKILL.md에 `clinic-content-system/reference/brand-design-system.md` 참조 명시

### lab-report-infographic

- [ ] 색상 토큰이 brand-design-system.md와 일치하는지 점검
- [ ] 폰트를 Pretendard로 통일
- [ ] 챕터 라벨, 인덱스 라벨을 영문 uppercase로 통일 (예: `LAB · LIVER`, `RANGE · NORMAL`)
- [ ] SKILL.md에 brand-design-system.md 참조 추가

### patient-education-pptx (legacy)

- [ ] Pretendard 폰트 적용 + Noto Sans KR fallback
- [ ] 컬러 토큰 동기화
- [ ] **장기적으로는 clinic-content-system으로 전환 권장**
- [ ] 점진적 폐기 시점은 6개월~1년 사용 후 결정

## 새 콘텐츠 만들 때 우선순위

원장님이 새 환자 교육 자료를 만들 때 다음 순서로 스킬 선택:

1. **환자 교육 슬라이드 덱** (12장 정도) → `clinic-content-system`
2. **A4 한 장 진료실 비치 유인물** → `patient-handout-pdf`
3. **검사 결과지 시각화** → `lab-report-infographic`
4. **PPTX 파일 자체가 필요한 경우** → `patient-education-pptx`

## 마이그레이션 진행 추적

Notion 클리닉 허브에 마이그레이션 상태 페이지 생성 권장:

| 스킬 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|------|---------|---------|---------|---------|---------|
| clinic-content-system | ✓ 완료 | ✓ | ✓ | ✓ | N/A (신규) |
| patient-handout-pdf | ✓ 완료 | □ 진행 중 | □ | □ | N/A |
| lab-report-infographic | ✓ 완료 | □ | □ | □ | N/A |
| patient-education-pptx | ✓ 완료 | □ | □ | □ | □ |

## 핵심 원칙

마이그레이션 중 흔들리지 말아야 할 원칙:

1. **단일 진실의 원천**: 모든 스킬은 `brand-design-system.md`를 참조한다. 색상/폰트를 임의로 추가·변경하지 않는다.
2. **점진적 전환**: 한 번에 모두 바꾸지 않는다. 새 콘텐츠 만들 때마다 새 시스템을 우선 사용하고, 기존 자료는 갱신 시점에 변환한다.
3. **하위 호환**: 기존 PPTX 파일들은 그대로 유지한다. 굳이 일괄 재생성하지 않는다 — 환자에게 이미 전달된 자료다.
4. **검증**: 각 스킬의 첫 마이그레이션 결과물은 반드시 시각 검증 (PDF/이미지로 출력해서 확인).
