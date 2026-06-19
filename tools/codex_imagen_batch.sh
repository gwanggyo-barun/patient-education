#!/usr/bin/env bash
# codex_imagen_batch.sh — codex /imagen 이미지 N장을 **병렬 + CODEX_HOME 격리**로 생성.
#
# 왜: codex_imagen.sh 단독은 순차여야 안전했다 — codex가 생성 원본을 CODEX_HOME 하위
#   generated_images/ 에 떨구는데, 같은 CODEX_HOME(기본 ~/.codex)을 공유하면 병렬 시 서로
#   최신 파일을 집어가 뒤섞인다(2026-06-12 사고). 이 스크립트는 **작업마다 독립 임시 CODEX_HOME**
#   (실제 auth/config는 심링크)를 줘서 generated_images 충돌을 없애고 동시에 굽는다.
#
# Usage:
#   codex_imagen_batch.sh <prompt1>'|'<target1> <prompt2>'|'<target2> ...
#   codex_imagen_batch.sh --list <file>     # 파일: 줄당  <prompt_path>\t<target_path>
#
# Env:
#   CODEX_IMAGEN_CONCURRENCY (기본 4)  동시 실행 수
#   CODEX_IMAGEN_RETRIES / _BACKOFF / _MIN_BYTES  → codex_imagen.sh로 전달
#
# 종료코드: 전부 성공 0 / 일부 실패 7 (실패 목록 stderr) / 인자오류 2 / codex 없음 3
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SINGLE="$HERE/codex_imagen.sh"
REAL_CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
CONC="${CODEX_IMAGEN_CONCURRENCY:-4}"

command -v codex >/dev/null 2>&1 || { echo "ERROR: codex CLI not found" >&2; exit 3; }
[[ -f "$SINGLE" ]] || { echo "ERROR: codex_imagen.sh not found at $SINGLE" >&2; exit 2; }

# ── 작업 목록 파싱 ──
JOBS=()   # 각 원소 "prompt<TAB>target"
if [[ "${1:-}" == "--list" ]]; then
  [[ -f "${2:-}" ]] || { echo "ERROR: list file not found: ${2:-}" >&2; exit 2; }
  while IFS=$'\t' read -r p t; do
    [[ -z "$p" || -z "$t" ]] && continue
    JOBS+=("$p"$'\t'"$t")
  done < "$2"
else
  [[ $# -ge 1 ]] || { echo "Usage: $0 <prompt>'|'<target> ...   또는  --list <file>" >&2; exit 2; }
  for arg in "$@"; do
    p="${arg%%|*}"; t="${arg#*|}"
    [[ "$p" == "$arg" || -z "$p" || -z "$t" ]] && { echo "ERROR: bad job arg (need prompt'|'target): $arg" >&2; exit 2; }
    JOBS+=("$p"$'\t'"$t")
  done
fi
N=${#JOBS[@]}
[[ $N -ge 1 ]] || { echo "ERROR: no jobs" >&2; exit 2; }

# 중복 타깃 거부(Codex 검수 #7): 같은 target 을 두 job 이 동시에 rm/write 하면 경쟁한다.
dup_t=$(for job in "${JOBS[@]}"; do echo "${job#*$'\t'}"; done | sort | uniq -d | head -1)
[[ -n "$dup_t" ]] && { echo "ERROR: 중복 target — 병렬에서 경쟁함: $dup_t" >&2; exit 2; }

echo "[batch] $N job(s), concurrency=$CONC, real CODEX_HOME=$REAL_CODEX_HOME"

# ── 임시 CODEX_HOME 격리 디렉토리 (작업별) + 정리 trap ──
TMP_ROOT="$(mktemp -d -t codex-imagen-batch.XXXXXX)"
RESULT_DIR="$TMP_ROOT/_results"; mkdir -p "$RESULT_DIR"
cleanup(){ rm -rf "$TMP_ROOT" 2>/dev/null || true; }
trap cleanup EXIT

make_home(){  # $1=index → echoes isolated CODEX_HOME path
  local i="$1" h="$TMP_ROOT/home_$1"
  mkdir -p "$h"
  # creds/config만 심링크(읽기 위주, 복사 금지). features.json/config.json 은 심링크 금지 —
  # 각 job 의 codex_imagen.sh 가 `codex features enable` 로 write 하므로 실제 파일 공유 시 race
  # (Codex 검수 #3). 각 격리 홈이 자기 features.json 을 따로 쓰게 둔다. → generated_images 도 격리.
  for f in auth.json config.toml; do
    [[ -e "$REAL_CODEX_HOME/$f" ]] && ln -sf "$REAL_CODEX_HOME/$f" "$h/$f"
  done
  echo "$h"
}

run_job(){  # $1=index $2=prompt $3=target
  local i="$1" p="$2" t="$3" h
  h="$(make_home "$i")"
  if CODEX_HOME="$h" CODEX_IMAGEN_RETRIES="${CODEX_IMAGEN_RETRIES:-3}" \
       bash "$SINGLE" "$p" "$t" > "$RESULT_DIR/$i.log" 2>&1; then
    local sha; sha=$(shasum "$t" 2>/dev/null | awk '{print $1}')
    echo "OK"$'\t'"$t"$'\t'"$sha" > "$RESULT_DIR/$i.res"
  else
    echo "FAIL"$'\t'"$t"$'\t'"-" > "$RESULT_DIR/$i.res"
  fi
}

# ── 동시성 캡 병렬 실행 ──
# 슬롯 차면 폴링으로 대기 — `wait -n` 은 macOS 기본 bash 3.2 미지원이라 안 씀(Codex 검수 #5).
# `jobs -rp`(실행 중 PID)는 3.2 호환. 결과는 각 job 이 .res 파일로 명시 기록하므로 exit-status
# 수집에 의존하지 않는다.
idx=0
for job in "${JOBS[@]}"; do
  p="${job%%$'\t'*}"; t="${job#*$'\t'}"
  run_job "$idx" "$p" "$t" &
  idx=$((idx+1))
  while [[ $(jobs -rp | wc -l) -ge $CONC ]]; do sleep 0.5; done
done
wait

# ── 결과 집계 + sha 고유성(뒤섞임) 검증 ──
echo "[batch] ===== 결과 ====="
fails=0; shas=()
for i in $(seq 0 $((N-1))); do
  [[ -f "$RESULT_DIR/$i.res" ]] || { echo "  ? job $i: 결과 없음"; fails=$((fails+1)); continue; }
  IFS=$'\t' read -r st t sha < "$RESULT_DIR/$i.res"
  if [[ "$st" == "OK" ]]; then
    dim=$(python3 -c "from PIL import Image;import sys;print('%dx%d'%Image.open(sys.argv[1]).size)" "$t" 2>/dev/null || echo "?")
    echo "  ✅ $t  sha=${sha:0:12}  dim=$dim"
    shas+=("$sha")
  else
    echo "  ❌ $t  (로그: $RESULT_DIR/$i.log)"; sed -n '$p' "$RESULT_DIR/$i.log" 2>/dev/null | sed 's/^/      /'
    fails=$((fails+1))
  fi
done

# 고유성: 성공 sha 중 중복 있으면 격리 실패(뒤섞임)
dups=$(printf '%s\n' "${shas[@]:-}" | sort | uniq -d | grep -c . || true)
if [[ "${dups:-0}" -gt 0 ]]; then
  echo "[batch] ⚠️ sha 중복 발견 → CODEX_HOME 격리가 generated_images를 분리하지 못함(뒤섞임)." >&2
  echo "        → 격리 미지원 환경: CODEX_IMAGEN_CONCURRENCY=1 로 순차 실행 권장." >&2
  fails=$((fails+1))
else
  echo "[batch] sha 전부 고유 ✅ (격리 정상, 뒤섞임 0)"
fi

if [[ $fails -gt 0 ]]; then
  echo "[batch] DONE — 실패/경고 ${fails}건" >&2
  exit 7
fi
echo "[batch] DONE — 전부 성공 ($N장)"
