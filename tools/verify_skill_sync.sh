#!/usr/bin/env bash
# Verify that the clinic-content-system skill is in sync across:
#   1. origin/main (GitHub canonical)
#   2. ~/clinic-content-system (working repo)
#   3. Claude plugin clone (machine-local, found by remote URL)
#   4. ~/.codex/skills/clinic-content-system (Codex managed mirror)
#
# Exits 0 if all four show the same commit + SKILL.md hash, 1 otherwise.
# Read-only — safe to run any time, including with a dirty worktree.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
CODEX_MIRROR="$HOME/.codex/skills/clinic-content-system"
EXPECTED_REMOTE_FRAGMENT="gwanggyo-barun/patient-education"

if [ -t 1 ] && command -v tput >/dev/null 2>&1; then
    RED="$(tput setaf 1)"; GREEN="$(tput setaf 2)"; YELLOW="$(tput setaf 3)"; RESET="$(tput sgr0)"
else
    RED=""; GREEN=""; YELLOW=""; RESET=""
fi

short() { local s="${1:-}"; if [ -z "$s" ] || [ "$s" = "MISSING" ]; then echo "MISSING"; else echo "${s:0:7}"; fi; }

# Locate Claude plugin clone (searches the standard Claude data dirs for a
# directory named clinic-content-system whose git remote matches our repo)
find_plugin_clone() {
    local roots=()
    case "$(uname -s)" in
        Darwin*) roots+=("$HOME/Library/Application Support/Claude") ;;
        Linux*)  roots+=("$HOME/.config/Claude" "$HOME/.config/claude") ;;
        MINGW*|MSYS*|CYGWIN*)
            [ -n "${APPDATA:-}" ]      && roots+=("$APPDATA/Claude")
            [ -n "${LOCALAPPDATA:-}" ] && roots+=("$LOCALAPPDATA/Claude")
            ;;
    esac
    for root in "${roots[@]}"; do
        [ -d "$root" ] || continue
        while IFS= read -r dir; do
            [ -d "$dir/.git" ] || continue
            local remote
            remote="$(git -C "$dir" remote get-url origin 2>/dev/null || echo "")"
            case "$remote" in
                *"$EXPECTED_REMOTE_FRAGMENT"*) echo "$dir"; return 0 ;;
            esac
        done < <(find "$root" -type d -name "clinic-content-system" 2>/dev/null)
    done
    return 1
}

# --- Gather state ---
cd "$REPO"
git fetch origin --quiet 2>/dev/null || true

origin_sha="$(git rev-parse origin/main 2>/dev/null || echo "MISSING")"
origin_skill_sha=""
if [ "$origin_sha" != "MISSING" ]; then
    origin_skill_sha="$(git show "$origin_sha:SKILL.md" 2>/dev/null | shasum -a 256 | awk '{print $1}')"
fi

repo_sha="$(git rev-parse HEAD 2>/dev/null || echo "MISSING")"
repo_skill_sha=""
[ -f "$REPO/SKILL.md" ] && repo_skill_sha="$(shasum -a 256 "$REPO/SKILL.md" | awk '{print $1}')"

plugin_dir="$(find_plugin_clone || true)"
plugin_sha="MISSING"; plugin_skill_sha=""
if [ -n "$plugin_dir" ]; then
    plugin_sha="$(git -C "$plugin_dir" rev-parse HEAD 2>/dev/null || echo "MISSING")"
    [ -f "$plugin_dir/SKILL.md" ] && plugin_skill_sha="$(shasum -a 256 "$plugin_dir/SKILL.md" | awk '{print $1}')"
fi

mirror_sha="MISSING"; mirror_skill_sha=""
if [ -f "$CODEX_MIRROR/.sync-info" ]; then
    mirror_sha="$(awk -F= '/^synced_sha=/{print $2}' "$CODEX_MIRROR/.sync-info" 2>/dev/null || echo "MISSING")"
    [ -z "$mirror_sha" ] && mirror_sha="MISSING"
fi
[ -f "$CODEX_MIRROR/SKILL.md" ] && mirror_skill_sha="$(shasum -a 256 "$CODEX_MIRROR/SKILL.md" | awk '{print $1}')"

# --- Output table ---
plugin_label="${plugin_dir:-(plugin clone not found)}"
# Truncate long paths to 50 chars from the right for table readability
trunc() { local s="$1"; if [ "${#s}" -gt 50 ]; then echo "...${s: -47}"; else echo "$s"; fi; }

echo
printf "%-50s  %-9s  %s\n" "Location" "HEAD" "SKILL.md sha256 (short)"
printf -- "--------------------------------------------------  ---------  ------------------------\n"
printf "%-50s  %-9s  %s\n" "$(trunc "origin/main")"        "$(short "$origin_sha")"  "$(short "$origin_skill_sha")"
printf "%-50s  %-9s  %s\n" "$(trunc "$REPO")"              "$(short "$repo_sha")"    "$(short "$repo_skill_sha")"
printf "%-50s  %-9s  %s\n" "$(trunc "$plugin_label")"      "$(short "$plugin_sha")"  "$(short "$plugin_skill_sha")"
printf "%-50s  %-9s  %s\n" "$(trunc "$CODEX_MIRROR")"      "$(short "$mirror_sha")"  "$(short "$mirror_skill_sha")"

# --- Alignment check ---
echo
shas=("$origin_sha" "$repo_sha" "$plugin_sha" "$mirror_sha")
aligned=1
for s in "${shas[@]}"; do
    [ "$s" = "MISSING" ] && aligned=0
    [ "$s" != "$origin_sha" ] && aligned=0
done

if [ "$aligned" -eq 1 ]; then
    printf "%s✓ All 4 locations aligned at %s%s\n" "$GREEN" "$(short "$origin_sha")" "$RESET"
    exit 0
else
    printf "%s⚠ Locations not aligned.%s\n" "$YELLOW" "$RESET"
    echo "  → Resolve dirty state, then run: tools/sync_all_agents.sh"
    exit 1
fi
