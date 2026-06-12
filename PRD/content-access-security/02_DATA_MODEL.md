# 02_DATA_MODEL — 콘텐츠 접근 보안 데이터 구조

## 관계도
```
ProtectedAsset (보호 자료 1건)
  ├─ kind ∈ ProtectedKinds(config: lab-reports, checkup-results…)
  ├─ has many → ShareLink (발급된 만료 링크/QR)
  │                └─ validated by → EdgeMiddleware
  └─ has one  → AccessPolicy (이름·환자번호 요구 여부, 만료 기본값)
ProtectedKinds(config)  ── 티어 확장 지점(새 종류 = 한 줄 추가)
SigningKey  ── HMAC 비밀(회전 가능) = 일괄 무력화 수단
AccessLog(선택) ── 열람 시각·결과(PII 최소)
```

## 엔티티
### ProtectedKinds (config) ★확장성 핵심
```jsonc
// 보호 티어에 들어갈 콘텐츠 종류. 검진결과 신설 시 여기 한 줄.
{ "protected_kinds": ["lab-reports", "checkup-results"],
  "default_ttl_hours": 24,
  "require_name_chartno": true }
```

### ProtectedAsset
| 필드 | 타입 | 설명 |
|------|------|------|
| slug_path | str | `lab-reports/{topic}/{hash}/` (기존 해시 슬러그 재사용) |
| kind | enum | protected_kinds 중 |
| chart_no_hash | str | 환자번호의 **해시**(평문 저장 금지) — 게이트 대조용 |
| name_norm | str | 이름 정규화 비교값(공백·자모) — 게이트 대조용(선택) |

### ShareLink
| 필드 | 타입 | 설명 |
|------|------|------|
| url | str | `https://{vercel}/{slug_path}?t={token}` |
| token | str | `base64url(payload).hmac` — payload={slug, exp, ver} |
| exp | epoch | 만료시각(발급+ttl) |
| qr_png | path | 같은 URL의 QR(있으면) |
| revoked | bool | 강제 만료 표시(or ver 불일치) |

### Token payload (서명)
```
{ "slug": "lab-reports/lipid/ab12cd34ef/", "exp": 1781300000, "ver": 3 }
signature = HMAC_SHA256(SigningKey_ver, payload)
```
- 검증: 서명 OK ∧ now<exp ∧ ver==현재 SigningKey 버전(회전 시 과거 토큰 일괄 무효).

### EdgeMiddleware (Vercel) 동작
```
요청 path가 protected_kinds 경로?  ──no──> 통과(공개)
        │yes
검증: 토큰 서명 OK ∧ 미만료 ∧ ver 일치 ?  ──no──> 410/만료 안내 (fail-closed)
        │yes
require_name_chartno?  ──no──> 자료 서빙(no-store·noindex)
        │yes
이름·환자번호 입력 일치(name_norm ∧ chart_no_hash)? + 시도 rate-limit ──no──> 재시도/차단
        │yes
자료 서빙 (Cache-Control: no-store, X-Robots-Tag: noindex)
```

## 불변식
- I1. protected_kinds 경로는 **유효 토큰 없이는 절대 서빙 안 됨**(fail-closed).
- I2. 환자번호는 **해시로만** 저장·비교(평문 0). 로그에 PII 평문 금지.
- I3. T0(공개) 자료는 이 게이트 비대상 — 기존 공개+noindex 유지.
- I4. SigningKey 회전 = 발급된 모든 토큰 즉시 무효(유출 대응).
- I5. 새 보호 종류 추가 = `protected_kinds`에 문자열 1개 + (해당 빌드가 chart_no_hash/name_norm 채움). 코드 변경 불필요.
