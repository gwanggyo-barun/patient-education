#!/usr/bin/env bash
# Silent daily git fetch for clinic-content-system.
#
# Invoked by the LaunchAgent at io.github.gwanggyo-barun.clinic-content.daily-fetch
# on weekdays at 09:00 local time. Safe to run manually too:
#   bash scripts/daily-fetch.sh
#
# Why fetch (not pull):
#   - `git pull` on a dirty working tree blows up. The user may have an
#     in-progress edit at 09:00, so we never touch HEAD or the index.
#   - `git fetch` is read-only; it just refreshes origin/* refs so the
#     next `git pull --rebase` (the user does this at work-start per
#     SKILL.md) is a no-op fast-forward against locally-cached objects.
#   - This also surfaces conflicts earlier: a noisy fetch log warns
#     "main is N commits ahead" before you start editing, not after.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$HOME/Library/Logs/clinic-content-system"
LOG_FILE="$LOG_DIR/daily-fetch.log"

mkdir -p "$LOG_DIR"

ts() { date "+%Y-%m-%d %H:%M:%S"; }

log() {
  # tee-style: append to log + write to stdout (so LaunchAgent's
  # StandardOutPath captures the same thing).
  local msg="[$(ts)] $*"
  printf "%s\n" "$msg" | tee -a "$LOG_FILE"
}

cd "$REPO_DIR" || { log "✗ repo not found: $REPO_DIR"; exit 1; }

log "fetch start (branch=$(git rev-parse --abbrev-ref HEAD))"

if ! git fetch --all --prune --quiet; then
  log "✗ git fetch failed (network? auth? credentials? gh auth status?)"
  exit 1
fi

# Show how stale the working branch is, if applicable.
upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
if [[ -n "$upstream" ]]; then
  ahead_behind=$(git rev-list --left-right --count "@{u}...HEAD" 2>/dev/null || echo "0\t0")
  behind=$(echo "$ahead_behind" | cut -f1)
  ahead=$(echo "$ahead_behind" | cut -f2)
  if [[ "$behind" -gt 0 ]]; then
    log "→ local is $behind commit(s) behind $upstream — run 'git pull --rebase' before next work session"
  elif [[ "$ahead" -gt 0 ]]; then
    log "→ local is $ahead commit(s) ahead of $upstream (unpushed work)"
  else
    log "→ up to date with $upstream"
  fi
fi

log "fetch done"
