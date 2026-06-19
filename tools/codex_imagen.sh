#!/usr/bin/env bash
# codex_imagen.sh — Claude(또는 다른 비-Codex 에이전트)가 Codex CLI의 /imagen을
# 헤드리스로 호출해 래스터 설명 이미지를 생성하는 cross-machine 래퍼.
#
# Usage: tools/codex_imagen.sh <prompt_file> <target_image_path>
#
# - prompt_file: §3.5.b 룰로 작성된 영문 프롬프트 (.prompt.md). strict ratio,
#   ABSOLUTELY NO TEXT 블록, full-bleed 문구 등은 호출 전에 프롬프트에 이미
#   포함되어 있어야 한다 — 이 스크립트는 전달만 한다.
# - target_image_path: 최종 저장 경로 (예: shared/assets/generated/xxx-20260606.png)
#
# 동작: codex CLI 존재/로그인 확인 → image_generation feature flag 자동 활성화 →
#       codex exec 로 /imagen 호출 (후처리 금지 가드 자동 첨부) → 파일 존재 +
#       SHA1 출력. 후처리(sips/ImageMagick/재인코딩)는 Codex 측에도 금지시킨다.
#
# 병렬: 이 단일 스크립트는 inherited CODEX_HOME 을 존중한다. 여러 장을 동시에 구우려면
#    codex_imagen_batch.sh 를 써라 — 작업별 임시 CODEX_HOME 격리로 generated_images 충돌
#    (2026-06-12 ABYSS 사고)을 없앤다. 같은 CODEX_HOME 으로 병렬 직접 호출은 금지.
#
# 엔진 (2026-06-20): CODEX_IMAGEN_ENGINE=auto(기본)|codex|gemini.
#    auto = codex /imagen 우선, codex가 "이미지는 만들지만 파일경로 미노출"(degraded) 또는
#    재시도 소진 시 Gemini 이미지 생성(tools/gemini_imagen_fallback.py)로 자동 폴백.
#    codex 내장 image_gen 이 파일경로를 노출하는 regime 이면 OpenAI 키 불필요(정상). 미노출
#    degraded regime 에서만 fallback 이 필요하다(2026-06-19 실측: 같은 날 두 regime 공존).
#
# Cross-machine: 어떤 머신이든 `codex` CLI + 로그인만 돼 있으면 동작한다.
# codex 가 없으면 exit 3 — 호출자(Claude)는 reference/agent-orchestration.md 의
# fallback 절차(이미지 생략 + "no image added: codex unavailable" 기록)를 따른다.

set -euo pipefail

PROMPT_FILE="${1:-}"
TARGET_PATH="${2:-}"

if [[ -z "$PROMPT_FILE" || -z "$TARGET_PATH" ]]; then
  echo "Usage: $0 <prompt_file> <target_image_path>" >&2
  exit 2
fi

if [[ ! -f "$PROMPT_FILE" ]]; then
  echo "ERROR: prompt file not found: $PROMPT_FILE" >&2
  exit 2
fi

# 1) codex CLI 존재 + 로그인 확인
if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: codex CLI not found — fallback: 이미지 생략 (agent-orchestration.md)" >&2
  exit 3
fi
if ! codex login status >/dev/null 2>&1; then
  echo "ERROR: codex CLI not logged in (run: codex login)" >&2
  exit 3
fi

# 2) image_generation feature flag 확인 + 자동 활성화
FLAG_STATE=$(codex features list 2>&1 | awk '/^image_generation/ {print $NF}' | head -n1)
if [[ "$FLAG_STATE" != "true" ]]; then
  echo "[codex_imagen] enabling image_generation feature flag..."
  codex features enable image_generation >/dev/null 2>&1
fi

# 3) 저장 디렉토리 준비
mkdir -p "$(dirname "$TARGET_PATH")"

# 4) 프롬프트 + 후처리 금지 가드
PROMPT_BODY=$(cat "$PROMPT_FILE")
CODEX_PROMPT=$(cat <<EOF
/imagen ${PROMPT_BODY}

저장 규칙 (반드시 준수):
- 생성된 원본 이미지 파일을 ${TARGET_PATH} 에 **그대로 복사**만 할 것
- sips, ImageMagick, Pillow, 그 외 어떤 후처리(크롭/리사이즈/재인코딩/알파 조작)도 **절대 금지**
- 생성 원본은 **현재 CODEX_HOME(${CODEX_HOME:-$HOME/.codex}) 하위 generated_images/** 에 떨어진다 — 반드시 그 폴더의 파일을 복사할 것(기본 ~/.codex 등 다른 홈 참조 금지: 병렬 격리가 깨진다). 원본과 저장 파일의 sha1 이 **반드시 일치**해야 함
- 복사 후 shasum 으로 두 파일 해시를 확인하여 출력할 것
EOF
)

# 엔진 선택
ENGINE="${CODEX_IMAGEN_ENGINE:-auto}"   # auto | codex | gemini
HERE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 4.5) 재시도/백오프 루프 (2026-06-20 속도·안정성 개선)
#   - 각 시도: 타깃 rm → codex /imagen → (존재 + mtime≥호출시작 + 최소크기) 검증.
#   - codex가 디스크에 새 렌더를 안 남기는 간헐 실패(exit 5류)·일시 오류를 백오프 재시도로 흡수.
#     (back-to-back 연타가 실패를 부르므로 즉시 재시도 금지 — 지수 백오프.)
#   - 전부 실패면 stale 재사용 없이 정직하게 exit 5.
#   - 병렬은 codex_imagen_batch.sh가 호출별 CODEX_HOME 격리로 처리(이 스크립트는 inherited CODEX_HOME 존중).
RETRIES="${CODEX_IMAGEN_RETRIES:-3}"
BACKOFF="${CODEX_IMAGEN_BACKOFF:-20}"
MIN_BYTES="${CODEX_IMAGEN_MIN_BYTES:-50000}"   # <50KB면 코드-fallback(단색도형) 의심 → 실패 취급

# 기대 비율 파싱(검증용, 경고 only): "aspect ratio strictly 1536 x 1024" 우선, 없으면 "strictly 3:2"
EXP_WH=$(grep -ioE 'aspect ratio strictly[^0-9]*[0-9]+[[:space:]]*[x:×][[:space:]]*[0-9]+' "$PROMPT_FILE" 2>/dev/null \
         | grep -oiE '[0-9]+[[:space:]]*[x:×][[:space:]]*[0-9]+' | head -1 | tr 'X×' 'x:' | tr -d ' ')
[[ -z "${EXP_WH:-}" ]] && EXP_WH=$(grep -ioE 'aspect ratio[^0-9]*[0-9]+[[:space:]]*:[[:space:]]*[0-9]+' "$PROMPT_FILE" 2>/dev/null \
         | grep -oiE '[0-9]+[[:space:]]*:[[:space:]]*[0-9]+' | head -1 | tr -d ' ')

# 생성 결과 검증(존재+mtime+크기) → 0 통과 / 1 실패. $1=호출시작시각
validate_target(){
  [[ -f "$TARGET_PATH" ]] || { echo "[codex_imagen] target not created" >&2; return 1; }
  local mt; mt=$(stat -f %m "$TARGET_PATH" 2>/dev/null || stat -c %Y "$TARGET_PATH" 2>/dev/null || echo 0)
  [[ "$mt" -ge "$1" ]] || { echo "[codex_imagen] stale (mtime $mt < call $1) — 옛 파일 재사용" >&2; return 1; }
  local sz; sz=$(wc -c < "$TARGET_PATH" | tr -d ' ')
  [[ "$sz" -ge "$MIN_BYTES" ]] || { echo "[codex_imagen] too small (${sz}B < ${MIN_BYTES}) — 코드-fallback 의심" >&2; return 1; }
  return 0
}

SUCCESS=0
DEGRADED=0   # codex image_gen이 "이미지는 만들지만 파일경로 미노출" 모드로 판정되면 1 → 재시도 무의미, 즉시 fallback

# ── codex 엔진 (engine=auto|codex) ──
if [[ "$ENGINE" == "auto" || "$ENGINE" == "codex" ]]; then
  attempt=0
  while [[ $attempt -lt $RETRIES ]]; do
    attempt=$((attempt+1))
    rm -f "$TARGET_PATH"
    CALL_T0=$(date +%s)
    LOG_FILE=$(mktemp -t codex-imagen-log.XXXXXX)
    echo "[codex_imagen] attempt ${attempt}/${RETRIES} — codex /imagen → ${TARGET_PATH} (CODEX_HOME=${CODEX_HOME:-~/.codex})"
    # </dev/null 필수: stdin 열린 파이프면 codex exec가 영원히 대기(2026-06-06 실측).
    codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
          "$CODEX_PROMPT" > "$LOG_FILE" 2>&1 </dev/null || \
          echo "[codex_imagen] attempt ${attempt}: codex exec returned nonzero" >&2

    if validate_target "$CALL_T0"; then SUCCESS=1; rm -f "$LOG_FILE"; break; fi

    # degraded 감지: codex가 "원본 PNG 파일 경로 미노출 / OPENAI_API_KEY 없어 fallback 불가" 류를 보고하면
    # 같은 조건 재시도는 계속 실패한다 → 즉시 루프 탈출해 fallback 엔진으로.
    if grep -qiE '경로를 노출하지|파일 경로|OPENAI_API_KEY|cannot (save|copy)|file path|API fallback' "$LOG_FILE" 2>/dev/null; then
      echo "[codex_imagen] ⚠️ degraded image_gen 감지(파일경로 미노출) — codex 재시도 중단, fallback 시도" >&2
      DEGRADED=1; rm -f "$LOG_FILE"; break
    fi
    if [[ $attempt -lt $RETRIES ]]; then
      echo "[codex_imagen] backoff ${BACKOFF}s before retry..." >&2
      sleep "$BACKOFF"; BACKOFF=$((BACKOFF*2))
    fi
    rm -f "$LOG_FILE"
  done
fi

# ── Gemini fallback (engine=auto+codex실패  또는  engine=gemini) ──
GEM_HELPER="$HERE_DIR/gemini_imagen_fallback.py"
if [[ $SUCCESS -eq 0 && ( "$ENGINE" == "gemini" || "$ENGINE" == "auto" ) ]]; then
  if [[ -f "$GEM_HELPER" ]]; then
    echo "[codex_imagen] → Gemini fallback (tools/gemini_imagen_fallback.py)" >&2
    rm -f "$TARGET_PATH"; CALL_T0=$(date +%s)
    if python3 "$GEM_HELPER" "$PROMPT_FILE" "$TARGET_PATH" >&2; then
      validate_target "$CALL_T0" && SUCCESS=1
    else
      echo "[codex_imagen] Gemini fallback 실패(키 quota/오류 — 로그 참조)" >&2
    fi
  else
    echo "[codex_imagen] Gemini fallback helper 없음: $GEM_HELPER" >&2
  fi
fi

if [[ $SUCCESS -eq 0 ]]; then
  echo "ERROR: codex_imagen 실패 — ${TARGET_PATH} (engine=$ENGINE, degraded=$DEGRADED). codex degraded면 작동하는 GEMINI/OPENAI 키 필요." >&2
  exit 5
fi

SIZE=$(wc -c < "$TARGET_PATH" | tr -d ' ')
SHA1=$(shasum "$TARGET_PATH" | awk '{print $1}')

# 6.6) 비율 sanity (경고 only — 일부 모델이 요청 비율을 clamp하므로 차단하진 않음)
if [[ -n "${EXP_WH:-}" ]] && command -v python3 >/dev/null 2>&1; then
  python3 - "$TARGET_PATH" "$EXP_WH" 2>/dev/null <<'PY' || true
import sys
try:
    from PIL import Image
    p, wh = sys.argv[1], sys.argv[2]
    ew, eh = (wh.replace('x',':').split(':') + ['1','1'])[:2]
    er = float(ew)/float(eh)
    w, h = Image.open(p).size
    ar = w/h
    if abs(ar-er)/er > 0.05:
        print(f"[codex_imagen] ⚠️ 비율 경고: 생성 {w}x{h}={ar:.3f} vs 프롬프트 {ew}x{eh}={er:.3f} (>5% 차이 — 모델 clamp 가능, 슬롯 비율 재확인 권장)", file=sys.stderr)
except Exception:
    pass
PY
fi

echo "[codex_imagen] SUCCESS  path=$TARGET_PATH  size=${SIZE}B  sha1=$SHA1"
