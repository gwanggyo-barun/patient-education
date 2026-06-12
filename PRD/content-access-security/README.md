# 환자 콘텐츠 링크/QR 접근 보안 (기획서)

> 진료설명·유인물·검사결과 공유 링크/QR에 **민감도별 접근 통제**를 추가하는 PRD.
> 생성: 2026-06-12 (show-me-the-prd) · SoT=이 repo · **승인 방향: 옵션 C + 검진결과 확장 대비**

## 한 줄
PII 없는 일반 교육자료는 가볍게(공개+noindex) 두고, **환자명·차트번호가 든 검사결과는 만료 서명링크 + (선택)이름·환자번호 로그인 + 추측불가 URL로 진짜 잠근다.** 향후 **검진결과 페이지도 config 한 줄로 같은 보호**에 편입.

## 문서
| 파일 | 내용 |
|------|------|
| [01_PRD.md](01_PRD.md) | 문제·위협모델·옵션 C(2티어)·요구사항·지표 |
| [02_DATA_MODEL.md](02_DATA_MODEL.md) | ProtectedKinds(config)·ShareLink·토큰·엣지 미들웨어 흐름 |
| [03_PHASES.md](03_PHASES.md) | P0 즉시강화→P1 만료링크(MVP)→P2 이름·번호게이트→P3 검진결과확장·무력화 |
| [04_PROJECT_SPEC.md](04_PROJECT_SPEC.md) | fail-closed·PII최소·확장성·발급도구·스모크테스트 규칙 |

## 핵심 설계
- **T0 공개**(진료설명 decks·유인물 handouts) = GitHub Pages 유지.
- **T1 보호**(검사결과 lab-reports + 향후 검진결과) = Vercel 엣지 미들웨어 = 만료 서명링크 + 이름·환자번호 + 해시URL + no-store/noindex.
- **확장성**: `protected_kinds` config에 `checkup-results` 추가만으로 검진결과 보호 적용.
- **유출 대응**: SigningKey 회전 = 발급 토큰 일괄 무효.

## 확정 결정 (2026-06-12 사용자)
1. **1차 인증 = 이름+환자번호 + 만료링크 결합** (둘 다 요구, `require_name_chartno=true`)
2. **기본 만료 = 당일만** (`default_ttl`=발급일 23:59 KST 만료, 자정 경과 시 차단)
3. **보호 호스팅 = 별도 Vercel 프로젝트** (기존 트레이딩 대시보드와 분리)
