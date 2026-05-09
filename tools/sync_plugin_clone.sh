#!/usr/bin/env bash
# Sync the Claude skill plugin folder(s) on this machine to origin/main.
#
# Why this exists: the canonical working dir is `~/clinic-content-system/`,
# but Claude actually loads SKILL.md from a per-machine plugin folder under
# `~/Library/Application Support/Claude/.../skills/clinic-content-system/`.
# That folder is itself a clone of this repo, so it can drift behind origin
# whenever a SKILL.md / reference / shared CSS change lands. Run this script
# after major skill changes are pushed (or on a fresh machine) to bring the
# plugin clone(s) up to date without re-installing the plugin.
#
# Usage:
#   bash tools/sync_plugin_clone.sh
#
# Safe to run repeatedly. Only touches clones whose git remote matches the
# patient-education repo. macOS-focused; on other OSes, adjust ROOT below.

set -euo pipefail

EXPECTED_REMOTE_FRAGMENT="gwanggyo-barun/patient-education"
ROOT="$HOME/Library/Application Support/Claude"

if [ ! -d "$ROOT" ]; then
    echo "Claude support dir not found at: $ROOT" >&2
    echo "(macOS path. On Windows/Linux, locate the Claude data dir manually.)" >&2
    exit 1
fi

found_any=0

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

if [ "$found_any" -eq 0 ]; then
    echo "No matching clinic-content-system clones found under $ROOT"
    echo "(no remote pointing at $EXPECTED_REMOTE_FRAGMENT, or plugin not installed yet)"
    exit 0
fi
