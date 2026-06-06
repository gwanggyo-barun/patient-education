# 세션 인계 — 2026-06-06 (KST 17:40) · 직전판 2026-05-29

> 이 문서를 새 세션 시작 시 `Read ~/clinic-content-system/SESSION-HANDOFF.md` 또는 노션 페이지 링크로 전달하면, 진행 중 작업·룰·환경을 한 번에 복구할 수 있습니다. (주 작업 호스트는 Mac mini로 이전됨 — 경로 `/Users/jihwan/...`)

---

## 🆕 2026-06-06 업데이트 (Mac mini 마라톤 세션)

1. **🚨 연락처 SoT 정정 — `blocks/content/clinic-contact-footer.yaml` v04**: 부원장 진료로 **평일(월–금) 전일 운영** (08:30–18:30 · 토 08:30–13:30). 원장 개인 휴무(수 오후)와 병원 휴진을 혼동한 v03의 "수요일 오후 휴진" 표기는 **금지** — 6/6 원장 직접 확인. 아래 절대 룰 11번의 v03 언급은 v04로 대체됨.
2. **슬라이드 스킬 v2 (SKILL.md)**: ① deck당 이미지 4–6장이 내용의 핵심 축 ② 텍스트는 절대 이미지에 굽지 않고 HTML 오버레이 ③ 스타일 = semi-realistic (플랫 벡터 금지, `reference/image-assets.md` STYLE 블록) ④ slot-first: HTML 슬롯 실측 후 비율 맞춰 생성 ⑤ Step 3.8 페이지별 Playwright 시각 QA + 자동 commit·push ⑥ Notion 동기화 시 "파일링크" 칸 필수 (`shared/_notion_sync.py` pdf_url). 벤치마크 산출물: `decks/endocrine/achieve3-oral-glp1/` (e28fafd).
3. **Claude↔Codex 오케스트레이션**: `reference/agent-orchestration.md` + `tools/codex_imagen.sh` (codex /imagen 헤드리스 래퍼 — `</dev/null` 필수, imagen 시간당 rate limit 존재, 생성 간 75초+ 간격). `tools/slide_screens.py` = per-slide 캡처.
4. **멀티엔진 리서치 가동**: Claude + Codex(gpt-5.5) + Gemini CLI(울트라 OAuth, `GEMINI_CLI_TRUST_WORKSPACE=true gemini -p`) + Perplexity Sonar API(`~/.claude/.perplexity_api_key`, Pro 무료크레딧 폐지됨—충전식). 1호전: IBS 식단 (Codex 1위). TODO: 딥리서치 스킬 repo화 (pplx는 sonar-deep-research 모델로).
5. **IBS 저FODMAP A4 핸드아웃 신규**: `handouts/lifestyle/ibs-fodmap-diet/` — 4엔진 리서치 통합본, imagen 이미지 4장 중심 구성 (v2 룰 첫 핸드아웃 적용).
6. **사진 자동 컬링 v1**: 별도 repo `minyunpapa/family-media-pipeline` — 통덤프→연사 클러스터→품질 채점→XMP 별점. 1,076장 실전 1차 통과 (★5 299장/228초).
7. **클라우드 루틴**: 논문Top5 v2(06:00) · 아침브리핑 v2(06:05) · KBO 결과 리포트(23:00, etcRecords+wRC+) — 모두 6/7 첫 자동실행 검증 필요. 야구 시즌 성적 인용 시 wRC+ 필수(statiz).
8. **할일 컨벤션 재확인**: 할일 → Notion "📥 Akiflow Inbox" DB (To-do 캘린더 아님!), 일정 → 구글캘린더.
9. **🆕 덱 황금비율 디자인 룰 (6/6 저녁, 사용자 컨펌 + 코덱스 감수)**: `reference/deck-design-proportions.md` 신설(SoT) + SKILL Gotcha 19. 비주얼-포커스 박스 폰트 0.58~0.78rem→15~17px, 박스 세로중앙 대칭여백, 거터 28~32px. `_validate_layout`에 `box_underfill`(하단공백 비대칭)·`font_too_small`(<15px)·`content_image_gutter`(<24px) 자동 차단 추가 + Step 3.8 한장한장 스크린샷 전수검수 강화. EASO/BMJ/FINE-ONE/ACS 4덱 적용 완료.
   - **⚠️ 미완 — 라이브러리 전체 스윕 TODO**: 신규 검증기가 기존 덱 ~20개(achieve3·bepirovirsen 포함)에서 같은 잠복 문제(작은폰트·언더필·푸터겹침) 적발. build.py는 `::error` 주석만 내고 `return 0`(deploy 계속)이라 CI는 안 깨지지만, 점진적으로 황금비율 룰로 일괄 수정 필요. `python3 shared/_validate_layout.py` 가 대상 목록.

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

### A0. 🆕 논문 슬라이드 일괄 제작 (5/28 요청, 대상 확인 대기)
- 사용자: "제공해준 논문 다 슬라이드 만들어서 보내줘"
- 어떤 논문 세트인지 불명확 → 사용자에게 확인 요청함 (미응답)
- 후보 배치 A(고혈압/심혈관 5건: 저항성고혈압 BP·환경오염 HTN·2026 ACC/AHA 지질 가이드라인·단일정제 3제 병합·노인 BP 궤적) / 배치 B(혼합 5건) / 5/25 보류분(#1 Lp(a)·#2 SURMOUNT-5·#4 Vutrisiran)
- → 사용자가 세트 지정하면 멀티에이전트 deck 제작 시작

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

### D. 🟢 추가 투입 검토 (5/28 장 확인 후 결정)
- ISA ₩20M 추가 납입 → S&P500 추가 매수 (연간 한도 소진)
- 현대중공업 ₩10M 본계좌 thesis 진입 (CAN SLIM 7/7, TT 8/8)
- 코미코 pullback 시 진입 검토 (CAN SLIM 6.5/7, 무상증자 신주상장 6/15)

---

## ✅ 최근 완료 (5/20~5/29)

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

### 5/27
- **ISA 리밸런싱 실행**: 4종 ETF 전량 매도 → TIGER 미국S&P500 100% (794주, 평단 ₩27,361)
- **MetLife 변액보험 펀드 변경**: 5종 균등(각20%) → 미국주식 60% + 한국가치주식 40%
- **LS ELECTRIC 추매 19주** @₩264,250 (본계좌, 총 43주, 평단 ₩246,521)
- **삼성전자 추매 1주** @₩315,000 (UPM, 총 36주)
- **미국 비중**: 5.5% → 13.7% (+8.2%p)
- **5분봉 실시간 분석 스크립트** 신규 구축: `~/.claude/portfolio/intraday_5min.py`
  - 네이버 1분봉 API → 5분봉 집계 + ORB/VWAP/RSI/MACD/볼린저/진입판정
- **종목 분석 4건**: 삼현(AVOID 60/100) · 삼성SDI(WAIT 69/100) · 코미코(BUY후보 6.5/7) · 현대중공업(STRONG BUY 7/7)
- 코덱스 데스크톱 연결하기 Akiflow 등록

### 5/28-5/29
- **🚨 관심종목 SoT 버그 수정** (사용자 "어제 피드백 반영 안 됐어" 불만):
  - 원인: 5/27 `watchlist.json` 직접 편집 → 매일 18:00 `sync_watchlist.py`(LaunchAgent `com.claude.stock-briefing`)가 `interest_tickers.json` 기준으로 덮어써서 제거한 6종목 부활
  - 수정: `~/Library/Application Support/stock-briefing/interest_tickers.json`(진짜 SoT)에서 6종 제거+현대중공업 추가 → `python3 sync_watchlist.py` 실행
  - **추가 발견**: holdings.json이 2개 분리. `~/.claude/portfolio/holdings.json`(로컬 스크립트용)이 5/20에 멈춤 → portfolio-auto(5/27) 최신본 cp로 동기화. 앞으로 매매 시 양쪽 다 갱신 필수
  - 메모리 신설: `feedback_watchlist_sot.md`
- **알람 정리** (5/27~28): 관심종목 6종(에코프로머티·유일로보틱스·한화비전·삼성전기·LG이노텍·에코프로머티) alarm 제거 + 현대중공업 3건(720K/665K/766K) + SK하이닉스 목표 ₩400만 + 삼성전자 목표 ₩80만 + LS ELECTRIC 긴급 4건(250K/245K/229K손절/265K회복)
- **관심종목 최종 7개**: HPSP·코미코·HS효성첨단소재·두산에너빌리티·동진쎄미켐·삼현·현대중공업
- **시놀로지 NAS 원격접속 셋업 완료** (사용자 개인): 로컬 IP 직접접속(192.168.68.62) + 포트포워딩(5001/80/443) + Let's Encrypt 인증서 발급(jhjwhmhy.synology.me) + DS비디오 인증서 에러 해결 + QuickConnect 중계 탈피. 도메인 접속 jhjwhmhy.synology.me:5001
- **캘린더 등록 5건**: 헤어컷 6/3 11시 / 아이패드수리 6/3 14시 / 투자살롱 AFW 이선엽 6/18 18시 / 투자살롱 KB 이은택 6/22 18:30 / (오사카 여행 기존)
- **기타 브리핑**: SSG 최용준 투수(2021 2차 10라운드 KIA, 재기스토리) / 벤딕트 차량용 충전기 비교(더볼트 기본·PLUS·PRO·코어·미니) / 애플스토어 용산 없음(공식 6곳) / USJ 퀵패스 전략(닌텐도 정리권·해리포터 자유입장·파트너호텔 얼리입장)
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

## 📊 투자 환경 스냅샷 (2026-05-29 기준)

- **현재 입장**: 🟢 분할 진입 모드 (5/26 전환)
  - 1차 투입 완료: ISA 리밸런싱 + MetLife 변경 + LS ELEC·삼성전자 추매
  - 2차: ₩20~25M (사용자 "내일 장 보고 결정", 미실행)
  - 예비 현금 ₩93M (cash_available)
- **🚨 LS ELECTRIC 모니터링 (5/28 200MA 이탈)**:
  - 5/28 종가 ₩246,500 (-5.74%) → 200MA(₩250K) 하향 이탈
  - 평단 ₩246,521 = 사실상 본전. 전력설비 섹터 전반 -20~28% 조정 중
  - 알람: ₩250K(이탈경고)/₩245K(19주 정리 검토)/₩229K(-7% 전량손절)/₩265K(50MA 회복)
  - 펀더멘털 견조(1Q 최대실적·수주 5.6조) → 보유 유지, ₩245K 이하 마감 시 오늘 매수분(19주) 정리 검토
- **5/27 실행 완료**:
  - ISA: 4종 매도 → S&P500 100% 전환 (794주) ✅
  - MetLife: 미국주식 60% + 한국가치주식 40% ✅
  - LS ELECTRIC: 19주 추매 @₩264,250 (총 43주) ✅
  - 삼성전자: 1주 추매 @₩315,000 (UPM, 총 36주) ✅
- **검토 중 (미실행)**:
  - ISA ₩20M 추가 납입 → S&P500 추가 매수 (연간 한도 소진)
  - 현대중공업 ₩10M 본계좌 thesis 진입 (5/28 ₩704K로 -5.4%, pullback 진입 기회 접근)
  - 코미코 pullback 시 진입 검토 (무상증자 신주상장 6/15)
  - IRP: 옵션 10 현행 유지
- **목표가 알람**: SK하이닉스 ₩400만 / 삼성전자 ₩80만 (사용자 설정)
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

*마지막 업데이트: 2026-05-29 00:25 KST*
