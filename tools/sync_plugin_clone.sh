#!/usr/bin/env bash
# Sync the Claude skill plugin folder(s) on this machine to origin/main.
#
# Why this exists: the canonical working dir is `~/clinic-content-system/`,
# but Claude actually loads SKILL.md from a per-machine plugin folder under
# the OS-specific Claude data dir. That folder is itself a clone of this
# repo, so it can drift behind origin whenever a SKILL.md / reference /
# shared CSS change lands. Run this script after major skill changes are
# pushed (or on a fresh machine) to bring the plugin clone(s) up to date
# without re-installing the plugin.
#
# Usage:
#   bash tools/sync_plugin_clone.sh
#
# Cross-platform: macOS / Linux / Windows (Git Bash). Safe to run repeatedly.
# Only touches clones whose git remote matches the patient-education repo.

set -euo pipefail

EXPECTED_REMOTE_FRAGMENT="gwanggyo-barun/patient-education"

# Detect Claude data dir per-OS. All three are scanned recursively for any
# clinic-content-system clone, so plugin reshuffles between channels still
# get picked up.
CANDIDATE_ROOTS=()
case "$(uname -s)" in
    Darwin*)
        CANDIDATE_ROOTS+=("$HOME/Library/Application Support/Claude")
        ;;
    Linux*)
        CANDIDATE_ROOTS+=("$HOME/.config/Claude" "$HOME/.config/claude")
        ;;
    MINGW*|MSYS*|CYGWIN*)
        # Windows via Git Bash (Claude Code's default shell on Windows).
        # APPDATA → C:\Users\<u>\AppData\Roaming, LOCALAPPDATA → ...\Local.
        [ -n "${APPDATA:-}" ]      && CANDIDATE_ROOTS+=("$APPDATA/Claude")
        [ -n "${LOCALAPPDATA:-}" ] && CANDIDATE_ROOTS+=("$LOCALAPPDATA/Claude")
        # Fallback if env not exported (rare): construct from $HOME.
        CANDIDATE_ROOTS+=("$HOME/AppData/Roaming/Claude" "$HOME/AppData/Local/Claude")
        ;;
    *)
        echo "Unsupported OS: $(uname -s) — adjust CANDIDATE_ROOTS in this script." >&2
        exit 1
        ;;
esac

# Pick the first candidate that exists, but keep scanning all valid ones
# (a machine can host both Stable + Insider editions side by side).
ROOTS=()
for r in "${CANDIDATE_ROOTS[@]}"; do
    [ -d "$r" ] && ROOTS+=("$r")
done

if [ ${#ROOTS[@]} -eq 0 ]; then
    echo "No Claude data dir found — skipping plugin clone sync (nothing to update on this machine)." >&2
    echo "Tried:" >&2
    for r in "${CANDIDATE_ROOTS[@]}"; do echo "  $r" >&2; done
    # exit 0 (skip), not 1: 데스크톱 Claude 플러그인이 없는 머신(예: 헤드리스 Mac mini의
    # CLI 전용 환경)에서도 sync_all_agents.sh 가 [D] Codex mirror 단계로 진행해야 한다.
    # 2026-06-06 mini에서 실측: exit 1 이 set -e 체인을 끊어 Codex mirror 가 안 만들어짐.
    exit 0
fi

found_any=0

for ROOT in "${ROOTS[@]}"; do
    while IFS= read -r dir; do
        [ -n "$dir" ] || continue
        [ -d "$dir/.git" ] || continue
        remote=$(git -C "$dir" remote get-url origin 2>/dev/null || echo "")
        case "$remote" in
            *"$EXPECTED_REMOTE_FRAGMENT"*) ;;
            *) continue ;;
        esac

        found_any=1
        echo ""
        echo "== Syncing $dir =="
        before=$(git -C "$dir" rev-parse --short HEAD)
        git -C "$dir" fetch origin
        git -C "$dir" pull --rebase origin main
        after=$(git -C "$dir" rev-parse --short HEAD)
        if [ "$before" = "$after" ]; then
            echo "Already at $after"
        else
            echo "Updated: $before -> $after"
        fi
    done < <(find "$ROOT" -type d -name "clinic-content-system" 2>/dev/null)
done

if [ "$found_any" -eq 0 ]; then
    echo "No matching clinic-content-system clones found under:"
    for r in "${ROOTS[@]}"; do echo "  $r"; done
    echo "(no remote pointing at $EXPECTED_REMOTE_FRAGMENT, or plugin not installed yet)"
    exit 0
fi
