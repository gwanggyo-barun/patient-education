"""Streamlit web app for staff/부원장 self-service lab-report generation.

Run with:
    set -a && source ~/clinic-content-system/_migration/.env && set +a
    # Local-only (recommended):
    python3 -m streamlit run ~/clinic-content-system/tools/web_intake/app.py \
        --server.address=127.0.0.1
    # LAN-shared: REQUIRES INTAKE_PASSWORD env var, never expose to open internet.

The .env must define OPENAI_API_KEY (vision extraction) and, optionally,
NOTION_TOKEN (auto-register the row in 🧪 환자 검사결과 DB so it also shows
up under the patient's 👤 환자 마스터 page).

Security: this app accepts patient PDFs and writes to the tracked lab-reports/
tree. Without auth, anyone on the LAN can submit PHI and burn API keys.
Set INTAKE_PASSWORD in env to require a shared secret before the UI loads.
"""
from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from intake import (  # noqa: E402
    DEFAULT_TITLES,
    IntakeSource,
    PatientMeta,
    TOPIC_LABELS,
    run_intake,
)

st.set_page_config(page_title="검사결과 자료 생성", page_icon="🧪", layout="wide")


def _require_password() -> bool:
    """Gate the app behind INTAKE_PASSWORD shared secret if set.

    Returns True when access is granted, False when the password prompt is
    being shown (caller should st.stop()). If INTAKE_PASSWORD is unset, shows
    a visible warning but allows entry — appropriate only for localhost runs.
    """
    expected = os.environ.get("INTAKE_PASSWORD")
    if not expected:
        st.warning(
            "⚠️ INTAKE_PASSWORD 환경변수가 비어 있습니다. "
            "현재 인증 없이 접근 가능한 상태입니다. "
            "`--server.address=127.0.0.1` 로컬 전용 실행을 권장합니다."
        )
        return True
    if st.session_state.get("_intake_auth_ok"):
        return True
    pwd = st.text_input("🔒 접근 비밀번호", type="password", key="_intake_pwd_input")
    if not pwd:
        st.info("이 앱은 환자 PDF를 처리합니다. 관리자가 공유한 비밀번호를 입력하세요.")
        return False
    if pwd != expected:
        st.error("비밀번호가 일치하지 않습니다.")
        return False
    st.session_state["_intake_auth_ok"] = True
    st.rerun()
    return False


if not _require_password():
    st.stop()

st.title("🧪 검사결과 자료 셀프 생성")
st.caption(
    "환자 검사 PDF·캡쳐 이미지·텍스트를 입력하면, 광교바른내과 표준 스타일의 "
    "검사 결과 HTML/PDF를 생성합니다. 같은 환자의 검사는 👤 환자 마스터 페이지에 "
    "자동 누적됩니다."
)

# ───────────────────────── Sidebar: 환자 메타 ─────────────────────────
with st.sidebar:
    st.header("환자 정보")
    patient_name = st.text_input("환자명 *", placeholder="홍길동")
    chart_no = st.text_input("차트번호 *", placeholder="12345")
    exam_date = st.date_input("검사일", value=date.today())
    doctor = st.text_input("담당의", value="정지환")
    age_sex_hint = st.text_input(
        "성별/나이 (선택, 비우면 PDF에서 자동 추출)",
        placeholder="F/53",
    )
    st.divider()
    register_notion = st.toggle(
        "Notion DB 자동 등록",
        value=True,
        help="🧪 환자 검사결과 DB에 row 생성 + 👤 환자 마스터 페이지에 자동 연결",
    )

# ───────────────────────── Main: 검사 정보 + 업로드 ─────────────────────────
col_left, col_right = st.columns([1, 1])

with col_left:
    topic = st.selectbox(
        "검사 카테고리 *",
        options=list(TOPIC_LABELS.keys()),
        format_func=lambda t: f"{t} — {DEFAULT_TITLES.get(t, '')}",
    )
    emphasis = st.text_area(
        "강조점 / 의사 코멘트",
        height=160,
        placeholder=(
            "예시:\n"
            "- 총콜레스테롤 264로 적극 관리 필요\n"
            "- LDL 144 — 약물치료 고려\n"
            "- 환자에게 식이·운동 계획 강조"
        ),
        help="결과지 콘텐츠의 우선순위를 결정합니다. 비워두면 PDF에서 가장 임상적으로 중요한 항목 위주로 추출됩니다.",
    )
    source_text = st.text_area(
        "검사결과 텍스트 / EMR 복사 내용",
        height=180,
        placeholder=(
            "예시:\n"
            "위내시경: H. pylori 양성, 위축성 위염\n"
            "갑상선초음파: 우엽 0.4cm TIRADS 3\n"
            "혈액: LDL 142, HbA1c 6.0"
        ),
        help="PDF/캡쳐가 없거나, 이미지에서 잘 안 보이는 내용을 보강할 때 입력합니다.",
    )

with col_right:
    uploaded_files = st.file_uploader(
        "검사결과 PDF / 캡쳐 이미지",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )
    st.info(
        "💡 검사센터/EMR에서 받은 원본 PDF 또는 캡쳐 이미지를 여러 개 올릴 수 있습니다. "
        "텍스트만 입력해도 생성 가능합니다."
    )

st.divider()

# ───────────────────────── Submit ─────────────────────────
if st.button("📄 생성하기", type="primary", use_container_width=True):
    if not patient_name or not chart_no:
        st.error("환자명과 차트번호를 입력해주세요.")
    elif not uploaded_files and not source_text.strip():
        st.error("검사결과 PDF/캡쳐 이미지 또는 텍스트를 입력해주세요.")
    elif not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        st.error(
            "ANTHROPIC_API_KEY 또는 OPENAI_API_KEY 환경변수가 설정되지 않았습니다. "
            "터미널에서 `source _migration/.env` 후 streamlit을 다시 실행하세요."
        )
    else:
        meta = PatientMeta(
            name=patient_name.strip(),
            chart_no=chart_no.strip(),
            exam_date=exam_date.isoformat(),
            doctor=doctor.strip() or "정지환",
            age_sex=age_sex_hint.strip(),
        )
        with st.spinner("자료 분석 → 인포그래픽 생성 중… (15~30초)"):
            try:
                result = run_intake(
                    sources=[
                        IntakeSource(
                            filename=f.name,
                            content=f.getvalue(),
                            media_type=f.type or "",
                        )
                        for f in uploaded_files
                    ],
                    meta=meta,
                    topic=topic,
                    emphasis=emphasis,
                    source_text=source_text,
                    register_to_notion=register_notion,
                )
            except Exception as e:  # noqa: BLE001
                st.exception(e)
                st.stop()

        st.success(f"✅ 생성 완료 — slug `{result.slug}`")

        # ───── Result tabs ─────
        tab_preview, tab_json, tab_files = st.tabs(
            ["📸 미리보기", "🔍 추출 데이터", "📁 파일·Notion"]
        )

        with tab_preview:
            st.image(str(result.preview_path), use_container_width=True)

        with tab_json:
            issues = result.extracted.pop("__layout_issues__", None)
            if issues:
                st.warning(
                    f"레이아웃 경고 ({len(issues)}건) — overflow나 잘림 가능성:"
                )
                st.json(issues)
            st.json(result.extracted)

        with tab_files:
            with open(result.pdf_path, "rb") as f:
                st.download_button(
                    "📥 PDF 다운로드",
                    data=f.read(),
                    file_name=f"{patient_name}_{topic}_{exam_date.isoformat()}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            st.code(
                f"HTML: {result.html_path.relative_to(Path.home())}\n"
                f"PDF:  {result.pdf_path.relative_to(Path.home())}\n"
                f"미리보기: {result.preview_path.relative_to(Path.home())}",
                language="text",
            )
            if result.notion_action:
                st.success(
                    f"📋 Notion {result.notion_action}: "
                    f"https://www.notion.so/{result.notion_page_id.replace('-', '')}"
                )
                st.caption(
                    "환자 마스터 페이지의 검사결과 relation에 자동으로 연결되었습니다."
                )
            elif register_notion and not os.environ.get("NOTION_TOKEN"):
                st.info(
                    "NOTION_TOKEN 미설정 — 로컬 PDF만 생성. "
                    "`source _migration/.env` 후 재실행하면 자동 등록됩니다."
                )
            st.markdown(
                "**다음 단계 (GH Pages 배포):**\n"
                "1. `build.py`의 `TARGETS` 끝에 이 자료 dict 추가 "
                f"(`slug='{result.slug}'`, `slug_path='lab-reports/{result.topic}/{result.slug}/'`)\n"
                "2. `git status --short`로 기존 staged 항목 확인\n"
                "3. 새 HTML 파일과 `build.py`만 명시적으로 `git add <file>`\n"
                "4. `git diff --cached --name-only` 확인 후 commit/push\n"
                "5. GH Actions가 ~1분 20초 후 GH Pages에 배포 — Notion 카드 링크 자동 갱신"
            )
