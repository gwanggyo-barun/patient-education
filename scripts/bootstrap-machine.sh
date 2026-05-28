#!/usr/bin/env bash
# Bootstrap a new mac for clinic-content-system work.
#
# Idempotent — safe to re-run anytime. Sets up:
#   1. Python deps (requirements.txt) + Playwright Chromium (PDF rendering).
#   2. macOS LaunchAgent that does a silent `git fetch` every weekday morning
#      so `git pull` at work-start is a no-op fast-forward instead of a
#      cold fetch over wifi (and surfaces upstream changes early in the
#      day rather than mid-task).
#
# Prerequisites — confirmed and listed but not installed by this script:
#   - git, gh (GitHub CLI), python3 (≥ 3.11). The script halts with a
#     clear message if any is missing.
#
# Usage:
#   cd ~/clinic-content-system
#   bash scripts/bootstrap-machine.sh
#
# To remove the daily-fetch LaunchAgent later:
#   launchctl bootout gui/$(id -u)/io.github.gwanggyo-barun.clinic-content.daily-fetch
#   rm ~/Library/LaunchAgents/io.github.gwanggyo-barun.clinic-content.daily-fetch.plist

set -euo pipefail

# --- Paths --------------------------------------------------------------- #

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LAUNCH_AGENT_LABEL="io.github.gwanggyo-barun.clinic-content.daily-fetch"
LAUNCH_AGENT_SRC="$REPO_DIR/scripts/launchd/$LAUNCH_AGENT_LABEL.plist"
LAUNCH_AGENT_DST="$HOME/Library/LaunchAgents/$LAUNCH_AGENT_LABEL.plist"
LOG_DIR="$HOME/Library/Logs/clinic-content-system"

# --- UI helpers ---------------------------------------------------------- #

say()  { printf "\033[1;34m▸\033[0m %s\n" "$*"; }
ok()   { printf "\033[1;32m✓\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m⚠\033[0m %s\n" "$*" >&2; }
die()  { printf "\033[1;31m✗\033[0m %s\n" "$*" >&2; exit 1; }

# --- Sanity checks ------------------------------------------------------- #

say "checking prerequisites"

[[ "$(uname -s)" == "Darwin" ]] || die "this script targets macOS only"

for cmd in git gh python3; do
  command -v "$cmd" >/dev/null 2>&1 \
    || die "missing required command: $cmd (install with brew install $cmd)"
done
ok "git $(git --version | awk '{print $3}'), gh $(gh --version | head -1 | awk '{print $3}'), python3 $(python3 --version | awk '{print $2}')"

[[ -d "$REPO_DIR/.git" ]] \
  || die "run this from inside a clinic-content-system clone (no .git found at $REPO_DIR)"

gh auth status >/dev/null 2>&1 \
  || die "gh CLI not authenticated — run: gh auth login"
ok "gh auth ok"

# --- Python deps --------------------------------------------------------- #

say "installing Python dependencies"
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet -r "$REPO_DIR/requirements.txt"
ok "pip install -r requirements.txt"

say "installing Playwright Chromium (for PDF rendering)"
python3 -m playwright install chromium >/dev/null
ok "playwright chromium ready"

# --- LaunchAgent: daily git fetch --------------------------------------- #

say "registering daily-fetch LaunchAgent (weekdays 09:00 local time)"

mkdir -p "$LOG_DIR"
mkdir -p "$(dirname "$LAUNCH_AGENT_DST")"

[[ -f "$LAUNCH_AGENT_SRC" ]] \
  || die "missing plist template: $LAUNCH_AGENT_SRC — repo may be incomplete"

# Substitute $HOME and repo path so the plist works on any machine.
sed \
  -e "s|@@HOME@@|$HOME|g" \
  -e "s|@@REPO_DIR@@|$REPO_DIR|g" \
  "$LAUNCH_AGENT_SRC" > "$LAUNCH_AGENT_DST"

# Reload — bootout the old one if present, then bootstrap the new one.
launchctl bootout "gui/$(id -u)/$LAUNCH_AGENT_LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$LAUNCH_AGENT_DST"
launchctl enable "gui/$(id -u)/$LAUNCH_AGENT_LABEL"

ok "LaunchAgent installed at $LAUNCH_AGENT_DST"
ok "logs: $LOG_DIR/daily-fetch.{log,err}"

# --- First fetch --------------------------------------------------------- #

say "running first fetch to warm the cache"
"$REPO_DIR/scripts/daily-fetch.sh" || warn "first fetch reported issues — see $LOG_DIR/daily-fetch.log"

# --- Done ---------------------------------------------------------------- #

cat <<EOF

──────────────────────────────────────────────
✓ bootstrap complete on $(hostname -s)

Next steps:
  • Start work: cd $REPO_DIR && git pull --rebase
  • Daily fetch: silent, weekdays 09:00 (logs in $LOG_DIR)
  • Build a page: python3 build.py
  • Asset library: shared/assets/README.md
──────────────────────────────────────────────
EOF
