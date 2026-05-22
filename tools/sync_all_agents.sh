#!/usr/bin/env bash
# Sync the clinic-content-system skill across Claude and Codex on this machine.
#
# Flow:
#   [A] dirty guard on working repo
#   [B] git fetch + ff-only pull from origin/main
#   [C] Claude plugin clone sync (delegates to sync_plugin_clone.sh)
#   [D] Codex managed mirror update (whitelist rsync to ~/.codex/skills/clinic-content-system)
#   [E] write mirror metadata (.sync-info, MIRROR-NOTICE.md)
#   [F] verify (delegates to verify_skill_sync.sh)
#
# Safety:
#   - dirty (modified tracked files) aborts immediately — never touches other sessions' work.
#   - pull is --ff-only — non-fast-forward aborts; user must rebase/resolve manually.
#   - rsync uses a strict whitelist — output/, decks/, handouts/, lab-reports/, .git/,
#     _migration/, patient data, generated assets are NEVER copied to the mirror.
#   - Codex mirror is only a skill-loading/reference snapshot; real work stays in $REPO.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
CODEX_MIRROR="$HOME/.codex/skills/clinic-content-system"
EXPECTED_REMOTE_FRAGMENT="gwanggyo-barun/patient-education"

# tput-based colors with TTY fallback
if [ -t 1 ] && command -v tput >/dev/null 2>&1; then
    RED="$(tput setaf 1)"; GREEN="$(tput setaf 2)"; YELLOW="$(tput setaf 3)"; RESET="$(tput sgr0)"
else
    RED=""; GREEN=""; YELLOW=""; RESET=""
fi
ok()   { printf "%s✓ %s%s\n" "$GREEN"  "$*" "$RESET"; }
warn() { printf "%s⚠ %s%s\n" "$YELLOW" "$*" "$RESET"; }
err()  { printf "%s✗ %s%s\n" "$RED"    "$*" "$RESET" >&2; }

# Guard: correct repo
cd "$REPO"
remote_url="$(git remote get-url origin 2>/dev/null || echo "")"
case "$remote_url" in
    *"$EXPECTED_REMOTE_FRAGMENT"*) ;;
    *) err "Not the expected repo. origin = $remote_url"; exit 1 ;;
esac

# Guard: this script syncs the canonical main branch only.
branch="$(git branch --show-current 2>/dev/null || echo "")"
if [ "$branch" != "main" ]; then
    err "sync_all_agents.sh must run from main, but current branch is '$branch'."
    err "Switch to main after your work is merged/pushed, then re-run."
    exit 1
fi

# [A] dirty guard — only modified tracked files block, untracked files OK
echo
echo "== [A] Working repo dirty check =="
if ! git diff --quiet HEAD -- 2>/dev/null; then
    err "DIRTY tracked changes in $REPO — aborting."
    git status --short
    echo
    err "Commit/stash these first, then re-run."
    exit 1
fi
ok "No modified tracked files."

# [B] fetch + ff-only pull
echo
echo "== [B] origin sync (fetch + ff-only pull) =="
git fetch origin
local_sha="$(git rev-parse HEAD)"
origin_sha="$(git rev-parse origin/main)"
if [ "$local_sha" = "$origin_sha" ]; then
    ok "Already at origin/main ($origin_sha)."
elif git merge-base --is-ancestor HEAD origin/main; then
    echo "Fast-forwarding $local_sha → $origin_sha"
    git pull --ff-only origin main
    ok "Pulled to $(git rev-parse HEAD)."
else
    err "Local has commits not in origin/main (non-fast-forward). Aborting."
    err "Resolve manually (push, rebase, or reset). Then re-run."
    exit 1
fi

# [C] Claude plugin clone sync
echo
echo "== [C] Claude plugin clone sync =="
bash "$REPO/tools/sync_plugin_clone.sh"

# [D] Codex managed mirror
echo
echo "== [D] Codex managed mirror update =="
mkdir -p "$CODEX_MIRROR"

# Refuse if target is a symlink (legacy from rejected symlink approach)
if [ -L "$CODEX_MIRROR" ]; then
    err "$CODEX_MIRROR is a symlink — remove it manually before running. (We use a managed copy now, not a symlink.)"
    exit 1
fi

# Whitelist rsync: include patterns are anchored to source root with leading slash;
# trailing /** recurses; final --exclude='*' catches everything else.
# Excludes for .sync-info / MIRROR-NOTICE.md protect them from --delete on subsequent runs.
rsync -a --delete --prune-empty-dirs \
    --exclude='/.sync-info' \
    --exclude='/MIRROR-NOTICE.md' \
    --include='/SKILL.md' \
    --include='/AGENTS.md' \
    --include='/README.md' \
    --include='/build.py' \
    --include='/reference/' \
    --include='/reference/**' \
    --include='/shared/' \
    --include='/shared/*.css' \
    --include='/shared/*.py' \
    --include='/shared/assets/' \
    --include='/shared/assets/clinic_logo.png' \
    --include='/tools/' \
    --include='/tools/sync_plugin_clone.sh' \
    --include='/tools/generate_image_asset.py' \
    --exclude='*' \
    "$REPO/" "$CODEX_MIRROR/"

# [E] metadata
synced_sha="$(git rev-parse HEAD)"
synced_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

if [ -f "$CODEX_MIRROR/AGENTS.md" ]; then
    agents_tmp="$CODEX_MIRROR/AGENTS.md.tmp"
    cat > "$agents_tmp" <<EOF
# AGENTS.md — Codex Managed Mirror

This directory is a **read-only skill-loading snapshot** generated from
\`$REPO\` by \`tools/sync_all_agents.sh\`.

Do not edit files here. All real editing, validation, builds, commits, and
pushes must happen in \`$REPO\`.

The source AGENTS.md content follows for reference.

---

EOF
    cat "$REPO/AGENTS.md" >> "$agents_tmp"
    mv "$agents_tmp" "$CODEX_MIRROR/AGENTS.md"
fi

cat > "$CODEX_MIRROR/.sync-info" <<EOF
synced_at=$synced_at
synced_sha=$synced_sha
source_repo=$REPO
EOF

cat > "$CODEX_MIRROR/MIRROR-NOTICE.md" <<EOF
# ⚠️ Managed Mirror — Do Not Edit

This directory is a **read-only mirror** of \`$REPO\`, populated by
\`tools/sync_all_agents.sh\` (whitelist-based rsync).

Edits here are wiped on next sync. All real editing happens in \`$REPO\`.

- Last synced: ${synced_at} (UTC)
- Source commit: ${synced_sha}

What lives here: SKILL.md, AGENTS.md, README.md, build.py, reference/,
shared/*.{css,py}, shared/assets/clinic_logo.png,
tools/sync_plugin_clone.sh, tools/generate_image_asset.py.

What does NOT live here (by design): .git/, output/, decks/, handouts/, lab-reports/,
_migration/, evals/, tools/web_intake/, generated assets, patient data, secrets.
EOF

ok "Codex mirror updated → $synced_sha"

# [F] verify
echo
echo "== [F] verify =="
bash "$REPO/tools/verify_skill_sync.sh"
