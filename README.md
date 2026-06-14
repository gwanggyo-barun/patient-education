# Clinic Content System

광교바른내과 통합 환자 콘텐츠 시스템 — **3가지 콘텐츠 타입을 단일 디자인 시스템·단일 빌드 파이프라인**으로 생산.

## 현재 상태 (2026-05 기준)

| 타입 | 디렉토리 | 포맷 | 현재 자료 수 |
|---|---|---|---|
| **decks** (16:9 슬라이드 12장) | `decks/{specialty}/{topic}/` | 1280×720 HTML + PDF | 30+ 주제 |
| **handouts** (A4 세로 1장) | `handouts/{specialty}/{slug}/` | A4 portrait HTML + PDF | 30+ 주제 |
| **lab-reports** (A4 세로 1장) | `lab-reports/{topic}/{hash10}/` | A4 portrait HTML + PDF | 환자 인스턴스 + 8종 재사용 템플릿 |

- **Source of Truth**: https://github.com/gwanggyo-barun/patient-education (public)
- **Live Pages**: https://gwanggyo-barun.github.io/patient-education/
- **Notion DB 3종 자동 라우팅**: `kind` 필드 기반 (📋 진료설명용 / 📨 환자유인물 / 🧪 환자검사결과)

## 빠른 시작

```bash
# 최초 1회 (새 머신)
gh auth status || gh auth login
git clone https://github.com/gwanggyo-barun/patient-education ~/clinic-content-system
cd ~/clinic-content-system && pip install -r requirements.txt
playwright install chromium

# 일상 작업
cd ~/clinic-content-system
git pull --rebase                     # 다른 머신 변경 받기
# (콘텐츠 작성 — 아래 표준 워크플로우 참조)
PYTHONIOENCODING=utf-8 python3 -m shared._validate_layout <path>  # 검증
python3 build.py                      # 로컬 빌드 (선택, CI도 자동)
git status --short                    # staged/untracked audit
git add <이번 작업 파일만 명시>       # 절대 git add . 금지
git diff --cached --name-only         # 내 파일만 staged 인지 확인
git commit -m "..."
git push
```

## 스킬 동기화 (Claude Code + Codex)

`~/clinic-content-system`이 main이고 tracked 변경이 없을 때:

```bash
cd ~/clinic-content-system
bash tools/sync_all_agents.sh     # origin/main + Claude plugin clone + Codex managed mirror
bash tools/verify_skill_sync.sh   # 4개 위치 HEAD/SKILL.md sha 확인
```

Codex mirror(`~/.codex/skills/clinic-content-system`)는 read-only 스킬 로딩 snapshot이다. 실제 편집·검증·빌드는 항상 `~/clinic-content-system`에서 한다.

산출물 (CI 자동):
- `output/{kind}/{slug}.pdf` — 환자 공유용 PDF
- `output/{kind}/{slug}-preview.png` — 데스크톱 풀스크린 미리보기
- GitHub Pages 자동 배포
- Notion DB 자동 행 upsert (`kind` → DB 라우팅)

## 새 콘텐츠 만들기

| 요청 키워드 | 디렉토리 | 가이드 |
|---|---|---|
| "환자 교육 슬라이드", "질환 안내 PPT", "12장 자료" | `decks/{specialty}/{topic}/` | `reference/content-template.md` + `patterns.md` |
| "유인물", "비치용 안내문", "A4 한 장" | `handouts/{specialty}/{slug}/` | `reference/patterns.md` (handout 변형) |
| "검사 결과지 인포그래픽", "결과지 시각화" | `lab-reports/{topic}/{hash10}/` | `reference/lab-templates.md` (8종 템플릿 활용) |

1. `reference/brand-design-system.md` 먼저 확인 (디자인 토큰 SoT)
2. `reference/content-template.md` 12장 표준 구성 참조 (decks)
3. `reference/patterns.md` 7가지 본문 패턴 참조
4. HTML 작성 → `_validate_layout` 통과 → `build.py` TARGETS 추가 → push
5. **lab-reports는 hash slug 필수** (개인정보 보호) — `reference/lab-templates.md` 절차 참조

## 핵심 원칙 (단일 진실의 원천: `SKILL.md`)

1. 모든 슬라이드/페이지는 4-region master grid (header / title-block / body / footer)
2. 본문은 7가지 패턴 중 하나 (Hero Number, Asymmetric Split, Density Grid 3×2/2×2, Comparison, Timeline, Checklist, Regimen Tile)
3. 컬러는 Navy `#003366` + Steel Blue `#5B9BD5` 두 가지만
4. 폰트는 Pretendard Variable 단일 (jsDelivr CDN)
5. 표지 외 슬라이드에 그라데이션 배경 금지
6. lab-reports는 hash slug + QR 제거 + noindex (개인정보 4중 보호)

## 디렉토리 구조

```
clinic-content-system/
├── SKILL.md                          # 진입점 (트리거 + 워크플로우 + 절대 규칙)
├── AGENTS.md                         # SKILL.md 핵심 규칙 압축판
├── README.md                         # 이 파일
├── build.py                          # 통합 빌드 스크립트 (Playwright + qrcode)
├── requirements.txt
│
├── shared/                           # 공유 자산
│   ├── design-tokens.css             # 색상/폰트/간격 토큰 (SoT)
│   ├── clinic-slides.css             # 16:9 슬라이드 마스터
│   ├── clinic-handout-a4.css         # A4 세로 마스터
│   ├── _build_helpers.py             # QR/OG/noindex 주입 헬퍼
│   ├── _notion_sync.py               # 3 DB 자동 라우팅 sync
│   ├── _validate_layout.py           # 레이아웃 검증기 (CI gate)
│   ├── _visual_audit.py              # Playwright 실제 렌더 검증
│   └── assets/                       # 로고 + 생성 이미지
│
├── reference/                        # 가이드 문서
│   ├── brand-design-system.md        # ★ 모든 콘텐츠 공유, 단일 진실의 원천
│   ├── patterns.md                   # 7가지 본문 패턴 + Closing
│   ├── content-template.md           # 12장 표준 구성 (decks)
│   ├── input-template.md             # 새 콘텐츠 요청 형식
│   ├── image-assets.md               # AI 이미지 생성·삽입 가이드
│   ├── lab-templates.md              # lab-report 재사용 템플릿 8종 사용법
│   ├── build.md                      # 빌드 환경 셋업
│   ├── migration.md                  # 기존 3개 스킬 통합 가이드
│   └── patterns.md
│
├── decks/                            # 16:9 슬라이드 자료
│   ├── cardio/                       # htn, chest-pain, OH, vasovagal 등
│   ├── endocrine/                    # 갑상선, 지질, 골다공증, 당뇨 등
│   ├── gi/                           # GERD, H.pylori, IBS, 위염, 변비 등
│   ├── pulmo/                        # 천식, OSA, PFT 등
│   ├── infectious/                   # LTBI, 대상포진, 인플루엔자
│   ├── derm/                         # 만성두드러기
│   ├── uro/                          # 미세혈뇨
│   ├── vaccines/                     # 폐렴구균
│   └── emergency/                    # CPR 직원교육
│
├── handouts/                         # A4 1장 유인물
│   ├── lifestyle/                    # 식이·운동 (당뇨/이상지질/저염/철결핍)
│   ├── endoscopy/                    # 내시경 준비·후관리·항혈전제
│   ├── screening/                    # 검진 준비, FIT 양성
│   ├── medication/                   # HTN, 철분제, SGLT2 주의사항
│   ├── results/                      # eGFR/단백뇨, 간효소, 갑상선
│   ├── imaging/                      # 복부초음파, 골밀도
│   ├── forms/                        # 진료 intake 양식
│   ├── emergency/                    # 응급카트, CPR 플로우차트
│   ├── gi/                           # 충수염 적색신호, 담낭폴립 추적
│   └── respiratory/                  # PFT 준비, 감기 재방문
│
├── lab-reports/                      # 환자 검사결과 (hash slug 보호)
│   ├── cbc/template/                 # 일반혈액검사
│   ├── hba1c/template/               # 당화혈색소
│   ├── thyroid-function/template/    # 갑상선
│   ├── liver-function/template/      # 간기능
│   ├── kidney-function/template/     # 신장기능
│   ├── tumor-markers/template/       # 종양표지자
│   ├── anemia-panel/template/        # 빈혈
│   ├── electrolytes/template/        # 전해질
│   ├── lipid-panel/sample/           # 지질 (sample template)
│   ├── diabetes-screening/           # 환자 인스턴스
│   ├── general-checkup/              # 환자 인스턴스
│   ├── cv-screening/                 # 환자 인스턴스
│   ├── comprehensive-summary/        # 환자 인스턴스
│   ├── bone-metabolism/              # 환자 인스턴스
│   └── urinalysis/                   # 환자 인스턴스
│
└── tools/
    ├── generate_image_asset.py       # OpenAI Image API → 로컬 PNG/WebP
    ├── sync_plugin_clone.sh          # Claude 플러그인 폴더 자동 동기화
    └── web_intake/                   # Streamlit PoC (환자 intake)
```

## 자세히 보기

- 전체 규칙·11가지 알려진 함정·시스템 구조: [`SKILL.md`](./SKILL.md)
- 디자인 시스템 SoT: [`reference/brand-design-system.md`](./reference/brand-design-system.md)
- HTML vs PPTX(legacy) 선택 기준: [`reference/skill-routing.md`](./reference/skill-routing.md)
- lab-report 템플릿 사용법: [`reference/lab-templates.md`](./reference/lab-templates.md)
- 환경 셋업 트러블슈팅: [`reference/build.md`](./reference/build.md)
