# 04_PROJECT_SPEC — 구현 행동 규칙 (콘텐츠 접근 보안)

## 0. 원칙
- **Fail-closed**: 검증 못 하면 차단(절대 공개 누출 금지). 보호 경로 기본=잠금.
- **PII 최소**: 환자번호=해시 비교만, 평문 저장·로그·URL 금지. 이름은 정규화 비교값만.
- **민감도 분리 유지**: T0 공개자료(진료설명·유인물)는 건드리지 않는다(과잉인증 금지). T1만 보호.
- **확장성 우선**: 보호 대상은 `protected_kinds` config로만 늘린다(검진결과=한 줄). 하드코딩 금지.
- **SoT=repo**: 룰·미들웨어·발급도구는 repo 커밋(push)로 전파. 비밀(SigningKey)은 repo 금지 → Vercel env(트레이딩 대시보드 `DASHBOARD_PASSWORD` 패턴과 동일하게 env 보관).

## 1. 토큰·서명
- payload={slug, exp, ver} → `HMAC_SHA256(SigningKey_ver, payload)`. base64url.
- 검증: 서명 일치 ∧ now<exp ∧ ver==현행. 하나라도 실패=차단.
- SigningKey는 Vercel env(`PE_SIGNING_KEY_v{n}`). 회전 시 ver++ → 과거 토큰 일괄 무효.

## 2. 엣지 미들웨어(Vercel)
- 요청 path가 `protected_kinds`에 매칭될 때만 게이트. 아니면 통과.
- 응답 헤더: `Cache-Control: no-store`, `X-Robots-Tag: noindex,nofollow,noarchive`, `Referrer-Policy: no-referrer`.
- 만료/무효 = 410 + 친절한 "링크가 만료되었습니다, 진료실에 문의" 안내(자료 내용 노출 0).

## 3. 이름+환자번호 게이트(선택)
- 폼 입력 → `name_norm` 일치 ∧ `chart_no_hash` 일치. 시도 rate-limit(예: 5회/10분), 초과 차단.
- 짧은 세션쿠키(자료 단위, 만료=토큰 exp 이내). 환자번호 평문은 쿠키·로그 금지.

## 4. 발급 도구(원장용)
- 입력: 자료 slug + TTL(기본 config). 출력: 서명 링크 + QR(PNG).
- 1스텝(스킬 명령 또는 CLI). 진료 흐름 방해 0.

## 5. 빌드 연동
- 보호 kind 빌드 시 `chart_no_hash`·`name_norm` 메타 임베드(평문 금지). 기존 해시 슬러그 유지.
- T0 자료 빌드·라우팅·Notion 동기화는 무변경.

## 6. 안전장치·검증
- 배포 전 **스모크 테스트**: ①무토큰 접근=차단 ②만료 토큰=차단 ③정상 토큰=서빙 ④공개자료=정상 ⑤검색/캐시 헤더 확인. (미들웨어 오설정=공개 노출 사고 방지)
- 키 회전·revoke 절차 문서화. 유출 의심 보고 경로.

## 7. 안티패턴
- 보호 경로를 토큰 없이 서빙(공개 누출), 환자번호 평문 저장/로그/URL, SigningKey repo 커밋.
- T0 일반자료에 과잉 인증, 보호 대상 하드코딩(config 우회).
- "검증기 없이 배포" — fail-closed·스모크 미실시.

## 8. 확정 결정 (2026-06-12)
- **1차 인증 = 이름+환자번호 AND 만료링크 결합**(`require_name_chartno=true`, 둘 다 필수).
- **기본 TTL = 당일만**(발급일 23:59 KST 만료).
- **보호 호스팅 = 별도 Vercel 프로젝트**(기존 대시보드와 분리).
→ 구현은 이 3개 확정값 기준. P1=만료(당일)+서명, P2=이름·환자번호 결합 게이트, 별도 프로젝트로 배포.
