#!/usr/bin/env bash
# [kz-015] pre-push 훅 설치. core.hooksPath 는 clone 에 전파되지 않으므로 각 clone 에서 1회 실행.
#   설치 위치의 단일 SoT = `git rev-parse --git-path hooks` (git 이 실제로 훅을 실행하는 그 경로).
#   이 값은 core.hooksPath(상대·절대·tilde `~` 포함)와 linked-worktree 의 .git-파일을 모두 정확히
#   해소한다 → "설치했다고 믿지만 안 도는" fail-open(특히 tilde hooksPath)을 구조적으로 제거.
#   실행 위치가 repo 밖(전역/공유 hooks)이면 자동 설치하지 않고 정확한 위치를 알려주고 중단.
#   기존(비-kz-015) pre-push 훅이 있으면 덮어쓰지 않고 중단(수동 병합 유도).
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"
src="$repo_root/hooks/pre-push"
[ -f "$src" ] || { echo "✗ 원본 없음: $src" >&2; exit 1; }

# git 이 실제로 pre-push 를 실행하는 디렉토리(hooksPath·tilde·worktree 전부 해소) → 절대경로화.
hooks_dir_raw="$(git rev-parse --git-path hooks)"
hooks_dir="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$hooks_dir_raw")"
repo_real="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$repo_root")"

case "$hooks_dir/" in
  "$repo_real"/*) : ;;   # repo 안 → 자동 설치 OK
  *)
    echo "⚠️ git 이 훅을 실행하는 위치가 repo 밖입니다(core.hooksPath 전역 설정 등):" >&2
    echo "     $hooks_dir" >&2
    echo "   다른 repo 에 영향 줄 수 있어 자동 설치하지 않습니다." >&2
    echo "   수동 설치: cp '$src' '$hooks_dir/pre-push' && chmod +x '$hooks_dir/pre-push'" >&2
    exit 1 ;;
esac

dst="$hooks_dir/pre-push"
if [ -e "$dst" ] && ! grep -q "kz-015" "$dst" 2>/dev/null; then
  echo "⚠️ 기존 pre-push 훅이 있고 kz-015 훅이 아닙니다: $dst" >&2
  echo "   덮어쓰지 않습니다 — 수동 병합하세요." >&2
  exit 1
fi

mkdir -p "$hooks_dir"
cp "$src" "$dst"
chmod +x "$dst"
echo "✅ pre-push 훅 설치 완료: $dst"
echo "   (검증: git push --dry-run 로 게이트 동작 확인 가능)"
