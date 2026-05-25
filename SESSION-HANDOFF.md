# 세션 인계 — 2026-05-25 (KST 23:15)

> 이 문서를 새 세션 시작 시 `Read /Users/chungjihwan/clinic-content-system/SESSION-HANDOFF.md` 또는 노션 페이지 링크로 전달하면, 진행 중 작업·룰·환경을 한 번에 복구할 수 있습니다.

---

## 🚨 절대 룰 (위반 시 즉시 사용자 불만)

1. **텔레그램 응답**: `<channel source="plugin:telegram:telegram">` 메시지에는 반드시 `mcp__plugin_telegram_telegram__reply` 도구로 회신. 텍스트 출력만 = 사용자 미수신.
2. **한국어 존댓말**: 반말("~할게", "~줘", "~돼?") 금지. "~하겠습니다", "~해주세요"로.
3. **장 휴장일 알람 차단**: KRX·NYSE 휴장일에는 알람 발송 X. `~/portfolio-auto/alarm_checker.py`의 `KRX_HOLIDAYS_2026`·`US_HOLIDAYS_2026` 참조.
4. **레이아웃 점검**: deck 생성 시 Playwright로 12 슬라이드 모두 overlap·overflow 점검 후 빌드. SKILL 기본.
5. **이미지 사용자 제공 우선**: ChatGPT 이미지 받으면 즉시 적절한 슬라이드에 배치. emoji·CSS 도형으로 대체 금지.
6. **PR 단위 commit**: 매 변경 후 `git add -A && git commit && git push` 자동. 특히 `~/clinic-content-system`, `~/portfolio-auto`, `~/soap-bot` 3개 repo.
7. **NOTION_TOKEN/credentials 절대 채팅에 붙여넣지 않기.**
8. **lab-reports 커밋 메시지**: 환자명/차트번호 금지.
9. **`07_Prompts/`**: gitignored, 외부 push 금지.
10. **SKILL.md SoT**: GitHub repo. 메모리는 개인 선호만.
11. **광교바른내과 연락 정보**: ⚠️ SoT는 `blocks/content/clinic-contact-footer.yaml` v03. 정확한 주소: **경기도 용인시 수지구 광교중앙로 298, 4층 402-404호 · 031-893-4560**. ❌ 절대 금지: "수원시 영통구"·"광교중앙로 145"·"아브뉴프랑"·"031-217-5878". sub-agent hallucination 사례 5/24-5/25 발생 → 일괄 수정 완료.

---

## 📌 진행 중·미완료 작업

### A. 5/25 논문 deck — #1·#2·#4 (사용자 미명시, 보류)
- #1 Lp(a) cardiovascular risk
- #2 Tirzepatide vs Semaglutide (SURMOUNT-5)
- #4 Vutrisiran ATTR-CM

→ 사용자가 명시적으로 요청하지 않으면 작업 보류.

### B. Trading Dashboard v6 옵션 (사용자 결정 대기)
- CAN SLIM 펀더멘털 통합
- MACD/RSI 인디케이터 추가
- 자동 알람 trigger
- Vercel 배포
- PWA 변환

→ 사용자 우선순위 결정 후 진행.

### C. 환자 설문 웹폼 (Akiflow에 등록만 됨)
- 작업 아직 시작 X. 환자 정보·증상·복약 등 사전 입력 form.

---

## ✅ 최근 완료 (5/20~5/25)

### 5/20-5/22
- Trading Dashboard v1→v5: Flask 백엔드 + Toss-style 프론트엔드 + Naver 차트 이미지 fallback + 127.0.0.1 보안 + TTL cache + holdings 기반 동적 메타 + 실시간 plPct 재계산
- 중복 LaunchAgent 5개 비활성화 (SSG/BTC/UFC/trading-triggers/trading-weekly)
- 5/21 Top 5 논문 deck 5개 (slide+PDF) + 노션 등록 + 텔레그램 발송
- IRP 정정: 미래에셋증권 (KB증권 X), 옵션 10 매수 완료

### 5/23-5/24
- 5/24 Top 5 deck v3 풀 quality 재작성 (Baxdrostat·트라마돌·SGLT2+GLP1·콩두류·RSV) + ChatGPT 이미지
- SKILL.md 사용자 디폴트 워크플로우 추가 (700+줄 quality·multi-agent·이미지 에셋)
- /goal 자동 적용, 30분 보고, Copyright & Asset Protection, PromptOps System
- PromptOps Phase 1 완성: 5 skills YAML + 5 tests + 4 brand-profiles + 38 reusable blocks + 3 templates + CI/CD + run_tests.py + 노션 Skills DB

### 5/25
- 5/25 #3 once-weekly-insulin deck (727줄, 12/12 zero clip)
- 5/25 #5 CPAP personalized CV deck (3.8MB PDF)
- KR + US 휴장일 알람 차단 (alarm_checker.py)
- 중1 키 성장 영양제 deck (753줄, 13 슬라이드) — 이미지 5개 적용 완료
  - Slide 03 anatomy·07 foodplate·08 GH curve·09 jump-sports·12 motivation
  - Slide 02·04·05 텍스트 겹침 fix (font·padding tightening)
- Notion deck DB 중복 정리 (인슐린·키성장 자동 sync row 유지, 제가 만든 dup 2개 workspace로 이동)
- 미용실 예약 Akiflow Inbox 등록 (5/26 마감)
- **🚨 광교바른내과 주소 일괄 정정** (sub-agent hallucination 사건):
  - SoT block `clinic-contact-footer.yaml` v03로 갱신 (정확한 주소·전화·forbidden_terms 가드)
  - 4개 blocks (bowel-prep·emergency·qr-mini·qr-block-standard) 정정
  - reference/copyright-protection.md 정정
  - 7개 deck (papers-20260524 5개 + papers-20260525 2개) closing-grid contact 제거 + qr-only 패턴
  - 7개 PDF 재빌드 + grep 검증 0건
  - 메모리 `feedback_clinic_contact_sot.md` 신설

---

## 🗂️ 주요 파일·디렉토리 SoT

| 경로 | 용도 |
|---|---|
| `~/clinic-content-system/SKILL.md` | 콘텐츠 생성 마스터 룰 (deck·handout·lab-report) |
| `~/clinic-content-system/reference/promptops-system.md` | PromptOps 1,111줄 풀 스펙 |
| `~/clinic-content-system/reference/copyright-protection.md` | 저작권·에셋 보호 룰 |
| `~/clinic-content-system/skills/*.yaml` | 5개 skill 정의 |
| `~/clinic-content-system/blocks/{safety,visual,content,data-viz}/` | 38개 재사용 블록 |
| `~/clinic-content-system/brand-profiles/` | 4개 (base·print·web·sns) |
| `~/clinic-content-system/templates/` | 3개 (deck-16x9·handout-a4·lab-report) |
| `~/clinic-content-system/tools/run_tests.py` | 596줄 테스트 러너 |
| `~/clinic-content-system/tools/build.py` | HTML→PDF 빌드 (Playwright) |
| `~/portfolio-auto/` | 자동화 GHA repo (evening 15:35·dawn 06:00·hourly alarm 등) |
| `~/portfolio-auto/holdings.json` | 포트폴리오 SoT (매매 시 즉시 갱신) |
| `~/portfolio-auto/watchlist.json` | 관심 종목 (미국 LITE·BE·CRCL 등) |
| `~/portfolio-auto/alarms.json` | 알람 trigger (매수 자동 추가·전량 매도 자동 제외) |
| `~/soap-bot/` | Vercel SOAP 챗봇 |
| `~/.claude/portfolio/naver_price.py` | 실시간 가격 조회 (`--portfolio` 옵션) |

---

## 🔑 자주 쓰는 Notion ID

| 페이지 | ID |
|---|---|
| 진료 설명용 자료 DB (deck) | `a84f23489df54e8fbe34b9818d6109e5` |
| 진료 설명용 자료 DB data source | `afaccb35-948f-45b4-9e9d-ec64ccbfe345` |
| Akiflow Inbox data source | `51331fb6-c123-4fec-a1a4-6a285ec42869` |
| 자산 포트폴리오 페이지 | `352b801424d6815b9fbbdeec261b16eb` |
| 스윙랩 트레이딩 저널 | `34db801424d681029a98c5f423658239` |
| PromptOps Skills DB | (sketched in promptops-system.md) |

---

## 🛠️ 자동화 cron·LaunchAgent

| 작업 | 시간(KST) | 위치 |
|---|---|---|
| Evening sync (홀딩스→노션) | 15:35 | GHA `~/portfolio-auto/.github/workflows/evening-sync.yml` |
| Dawn sync (미국 마감 후) | 06:00 | GHA `dawn-sync.yml` |
| Hourly alarm | 매시 30분 (장 중) | GHA `hourly-alarm.yml` |
| Daily report | 21:00 | GHA `daily-report.yml` |
| MLB Korean players | lineup 발표 시 + 경기 종료 5분 | GHA `mlb-lineup-finish.yml` |
| Thesis weekly·BTC RSI·US afterhours·PubMed·KBO·마일스톤·카메라·네이버 리뷰 | 각각 GHA | 5/13 추가 8건 |

→ 휴장일에는 hourly-alarm 자동 차단됨.

---

## 📊 투자 환경 스냅샷 (2026-05-25 기준)

- **현재 입장**: STAY (조정 종료 확정 신호까지 신규 매수 보류)
- **확신도 thesis**:
  - 피엔티(+200%·예외룰) → Minervini 익절 미적용
  - SK하이닉스·LS ELECTRIC (₩2M·예외) → 익절 미적용
  - AI 반도체·전력기기 확대 (정상 매매 적용)
- **분석 framework**:
  - Minervini Trend Template (주 프레임) + CAN SLIM 펀더멘털
  - 한국 개별종목 framework v1.0 (Mauboussin 역DCF + fractional Kelly + O'Neil 손절)
  - ETF/ISA framework v1.0 (Brinson·Bogle·Risk Parity)
- **현금 동적 차감**: 매수·매도 시 cash_available 즉시 갱신 (₩100M 고정 X)
- **OCO**: KRX tick 단위 라운딩 + 분할매도 주수 명시

---

## ✈️ 일정·이벤트

- **2026-07-29~08-02**: 가족 오사카 여행 (4박5일, OZ116/OZ113)
  - 호텔·USJ 사전 예약 필요
- **2026-06-15**: Claude 청구 정책 변경 (Agent SDK·Code 별도 크레딧 풀)
- **2026-06 초**: 맥미니 마이그레이션 도착 (Claude Code + LaunchAgent + MCP 1-2시간 이전)

---

## 📥 진행 트래커

- **노션 자산 포트폴리오** 매일 2회 갱신 (15:35·07:00, GHA 자동)
- **deck DB** 자동 sync row 사용 (build.py가 빌드 후 row 자동 등록·갱신)
- **Akiflow Inbox** Telegram → 노션 DB → Akiflow 동기화

---

## 📌 새 세션 시작 시 워크플로우

```
1. /memory  (또는 자동 로딩) — MEMORY.md 인덱스 확인
2. Read /Users/chungjihwan/clinic-content-system/SESSION-HANDOFF.md  ← 이 문서
3. 사용자 첫 메시지 확인 후 필요시 git pull (portfolio-auto·clinic-content-system·soap-bot)
4. 진행 중 작업 (위 "진행 중·미완료" 섹션) 우선 확인
```

---

## ❓ 자주 묻는 트러블슈팅

- **TradingView KRX 미지원**: 네이버 금융 이미지 차트로 fallback (`server.py` 참조)
- **macOS TCC permission denied**: Downloads 폴더 → `~/portfolio-auto/trading-dashboard`로 이전
- **Naver 가격 콤마 string**: `server.py to_num()` 함수에서 콤마 제거
- **빌드 후 PDF mtime 동일 이슈**: `stat -f %m` 기반 wait loop 사용

---

*마지막 업데이트: 2026-05-25 23:15 KST*
