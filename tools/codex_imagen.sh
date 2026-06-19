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
# ⚠️ 순차 호출만 (2026-06-12 ABYSS 작업 중 실측): 이 스크립트를 여러 장에 대해 동시(병렬)로
#    돌리지 말 것. Codex 가 생성 원본을 공유 폴더(~/.codex/generated_images/)에 떨구는데,
#    병렬 실행 시 두 프로세스가 같은 최신 파일을 집어가 타깃이 중복된다. 4장이면 4번 순차
#    실행하고 끝나면 shasum 으로 전부 고유한지 확인한다.
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
- 생성 원본(~/.codex/generated_images/ 하위)과 저장 파일의 sha1 해시가 **반드시 일치**해야 함
- 복사 후 shasum 으로 두 파일 해시를 확인하여 출력할 것
EOF
)

# 4.5) 재생성 전 기존 타깃 제거 (2026-06-19 원장 검수, ROMA 덱)
#   버그: 타깃이 이미 있으면 codex가 새 렌더를 못 만든 경우에도 옛 파일을 재사용/유지해
#   stale 이미지가 SUCCESS 로 통과했다(아래 6) 존재검증이 '파일 있음'만 봤기 때문).
#   타깃을 먼저 비우면 codex 가 새로 못 만들 때 정직하게 exit 5 로 실패한다.
rm -f "$TARGET_PATH"
CALL_T0=$(date +%s)

# 5) codex exec 호출 (이미지 생성은 수 분 걸릴 수 있음)
LOG_FILE=$(mktemp -t codex-imagen-log.XXXXXX)
echo "[codex_imagen] calling codex /imagen — target: $TARGET_PATH"
echo "[codex_imagen] log: $LOG_FILE"

# </dev/null 필수: stdin이 열린 파이프면 codex exec가 "Reading additional input
# from stdin..."에서 영원히 대기한다 (2026-06-06 헤드리스 스모크 테스트에서 실측).
if ! codex exec \
    --skip-git-repo-check \
    --dangerously-bypass-approvals-and-sandbox \
    "$CODEX_PROMPT" > "$LOG_FILE" 2>&1 </dev/null; then
  echo "ERROR: codex exec failed. log tail:" >&2
  tail -30 "$LOG_FILE" >&2
  exit 4
fi

# 6) 결과 검증
if [[ ! -f "$TARGET_PATH" ]]; then
  echo "ERROR: target file not created: $TARGET_PATH" >&2
  tail -30 "$LOG_FILE" >&2
  exit 5
fi

# 6.5) 새 렌더 검증 (2026-06-19): 호출 시작(CALL_T0) 이후 생성/수정된 파일이어야 한다.
#   codex 가 옛 파일을 재사용했다면 mtime 이 호출 이전이므로 stale 로 판정해 실패시킨다.
MTIME=$(stat -f %m "$TARGET_PATH" 2>/dev/null || stat -c %Y "$TARGET_PATH" 2>/dev/null || echo 0)
if [[ "$MTIME" -lt "$CALL_T0" ]]; then
  echo "ERROR: target not freshly generated (mtime $MTIME < call $CALL_T0) — likely stale reuse, not a new render." >&2
  tail -30 "$LOG_FILE" >&2
  exit 6
fi

SIZE=$(wc -c < "$TARGET_PATH" | tr -d ' ')
SHA1=$(shasum "$TARGET_PATH" | awk '{print $1}')
echo "[codex_imagen] SUCCESS  path=$TARGET_PATH  size=${SIZE}B  sha1=$SHA1"
