# web_intake — 검사결과 자료 셀프 생성 웹앱

직원·부원장이 환자 검사 PDF·캡쳐 이미지·검사 텍스트를 입력하고 강조점을 적으면,
광교바른내과 표준 스타일의 검사 결과 HTML/PDF가 자동 생성되는 로컬
Streamlit 앱이다. 같은 환자의 검사는 👤 환자 마스터 페이지에 자동으로
누적된다 (`_notion_sync._ensure_patient_page` 경로).

## 설치 (한 번만)

```bash
pip3 install --user -r ~/clinic-content-system/tools/web_intake/requirements.txt
python3 -m playwright install chromium   # 첫 실행 시
```

## 실행

```bash
cd ~/clinic-content-system
set -a && source _migration/.env && set +a   # ANTHROPIC_API_KEY + NOTION_TOKEN 로드
python3 -m streamlit run tools/web_intake/app.py
```

`ANTHROPIC_API_KEY`가 있으면 Anthropic vision + `SKILL.md` 캐시된 system prompt가 사용됩니다 (권장 — clinic-content-system 컨벤션 자동 반영). `ANTHROPIC_API_KEY`가 없고 `OPENAI_API_KEY`만 있으면 OpenAI vision으로 자동 fallback. 모델 alias는 필요하면 `ANTHROPIC_MODEL` / `OPENAI_MODEL` 환경변수로 고정합니다.

브라우저가 자동으로 열림 (보통 http://localhost:8501).

## 사용 흐름

1. **환자 정보** (사이드바): 이름, 차트번호, 검사일, 담당의
2. **검사 카테고리** 선택 (general-checkup, lipid-panel, …)
3. **강조점 / 의사 코멘트** 입력 — 결과지 콘텐츠 우선순위를 결정
4. **검사결과 텍스트** 입력 또는 **PDF/캡쳐 이미지** 업로드 (여러 개 OK)
5. **생성하기** 클릭 → 15~30초 후 결과 표시:
   - 📸 미리보기 PNG
   - 🔍 vision 모델이 추출한 구조화 데이터 (JSON)
   - 📁 PDF 다운로드 + Notion 등록 상태

`Notion DB 자동 등록`을 켜두면 🧪 환자 검사결과 DB에 row가 생기고
같은 chart_no의 환자 마스터 페이지에 자동으로 연결된다 (build.py와
동일한 코드 경로).

## GH Pages 배포 (선택)

웹앱은 로컬 PDF + Notion 등록까지만 한다. GH Pages에 공식 배포하려면:

1. `build.py`의 `TARGETS` 리스트 끝에 새 dict 추가 (slug/slug_path/html_path/qr_class/fmt + patient_name/chart_no/exam_date/doctor/note)
2. `git status --short`로 기존 staged 항목 확인
3. 새 HTML 파일과 `build.py`만 명시적으로 `git add <file>`
4. `git diff --cached --name-only`로 staged 범위를 재확인한 뒤 commit/push
5. GH Actions가 ~1분 20초 안에 빌드 + Pages 배포 + Notion 카드 URL 자동 갱신

## 데이터 흐름

```
PDF / 캡쳐 이미지 / 텍스트
  → PyMuPDF rasterize (PNG @ 144dpi) + text source merge
  → Anthropic vision (SKILL.md cached system prompt → JSON)
       │  OpenAI vision fallback if ANTHROPIC_API_KEY missing
  → Jinja2 template (health-checkup 은 전용 1~2페이지 renderer)
  → Playwright A4 portrait render (PDF + preview.png)
  → (옵션) Notion upsert via _notion_sync.upsert
      → _ensure_patient_page(chart_no, name) — 환자 마스터 자동 생성/매칭
      → row의 `환자` relation 자동 채움 → 환자 페이지에 누적
```

## 보안 고려사항

- **PDF 내용은 Claude API (또는 OpenAI fallback)로 전송됩니다.** 환자명·차트번호·검사값이
  포함되므로 공용 API 키 사용 시 비식별화를 고려하세요 (이름 마스킹 등). Anthropic의
  Zero Data Retention 정책 + workspace 설정을 기본 신뢰합니다.
- **로컬 전용 PoC**: Streamlit이 0.0.0.0이 아닌 localhost에 바인딩되므로 같은
  머신에서만 접속 가능. 외부 공개 시 Cloudflare Access / 매직 링크 인증 + 한국
  리전 호스팅 + audit log 필수.
- **민감정보 로그 금지**: 에러 추적 시 PDF 내용·환자 식별자가 로그에 남지
  않도록 주의.

## 다음 발전 방향

- [ ] Edit-loop: 생성 결과 HTML을 사용자가 인라인으로 수정 → 재렌더
- [ ] build.py TARGETS 자동 추가 + git commit/push 버튼
- [ ] 매직 링크 인증으로 외부 공개 (Vercel + 한국 리전)
- [x] 모델 alias 환경변수 지원 (`ANTHROPIC_MODEL`, `OPENAI_MODEL`)
- [x] PDF 자체 외에 EMR 텍스트 입력도 지원
