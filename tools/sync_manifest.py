"""Auto-sync shared/assets/manifest.json with the actual filesystem.

This is the single source of truth for the asset library. Called automatically
at the start of every build, and runnable standalone for ad-hoc updates.

Behavior (idempotent):
  - Scans shared/assets/** for image files (png, jpg, jpeg, webp, svg, gif).
  - For each file on disk:
      * If already in manifest → refresh `bytes`/`format`/`exists` only.
        Human-curated fields (alt_ko, tags, review_status, category, key
        override, generation_prompt, aliases) are preserved.
      * If new → add a skeleton entry with sensible defaults derived from
        the filename, marked `review_status: "pending"`.
  - For each manifest entry whose file no longer exists → set `exists: false`
    so asset_lint.py can flag it.

The manifest key defaults to the filename stem (no extension). Authors can
add a `"key": "explicit-key"` field to a manifest entry to expose a shorter,
stable handle for `data-asset=` references; renames then only need to touch
manifest, not every HTML file.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent.resolve()
ASSETS_DIR = ROOT / "shared" / "assets"
MANIFEST_PATH = ASSETS_DIR / "manifest.json"

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}

# Material dirs scanned to backfill alt_ko from existing <img alt="…"> tags
MATERIAL_DIRS = ("handouts", "decks", "lab-reports")

# Matches:  src="../../../shared/assets/...some-file.png" ... alt="..."
#       or: alt="..." ... src="../../../shared/assets/...some-file.png"
# Lazy + capped width to stay sane on multi-line tags.
_IMG_TAG_RE = re.compile(r"<img\b[^>]{0,800}>", re.IGNORECASE | re.DOTALL)
_SRC_RE = re.compile(r'src="([^"]*shared/assets/[^"]+)"', re.IGNORECASE)
_ALT_RE = re.compile(r'alt="([^"]*)"', re.IGNORECASE)

# Filename keyword → category. First match wins.
CATEGORY_RULES: list[tuple[str, str]] = [
    ("clinic_logo", "brand"),
    ("egd-", "endoscopy"),
    ("colonoscopy-", "endoscopy"),
    ("post-egd", "endoscopy"),
    ("post-colonoscopy", "endoscopy"),
    ("post-polypectomy", "endoscopy"),
    ("appendicitis", "gi-emergency"),
    ("abdominal-ultrasound", "ultrasound"),
    ("htn-", "cardio"),
    ("bone-density", "endocrine"),
    ("insulin", "endocrine"),
    ("dyslipidemia", "lipid"),
    ("iron-", "hematology"),
    ("blood-draw", "lab-blood"),
    ("urine-", "lab-urine"),
    ("pft-", "pulmonary"),
    ("nasal-spray", "ent"),
    ("sinusitis", "ent"),
]


def derive_category(stem: str) -> str:
    s = stem.lower()
    for needle, cat in CATEGORY_RULES:
        if needle in s:
            return cat
    return "uncategorized"


def derive_format_hint(stem: str) -> list[str]:
    """Best-effort hint for which content types an asset suits.
    Author overrides freely. Used by lint to warn (not block).
    """
    s = stem.lower()
    hints: list[str] = []
    if any(k in s for k in ("hero", "anatomy", "body-map", "rotation")):
        hints.extend(["deck", "handout"])
    if any(k in s for k in ("icons", "grid", "cards", "calendar", "clock")):
        hints.append("handout")
    if "logo" in s:
        hints.append("all")
    return hints or ["handout"]


def skeleton_entry(rel: str, abs_path: Path) -> dict[str, Any]:
    stem = abs_path.stem
    return {
        "file": rel,
        "format": abs_path.suffix.lstrip(".").lower(),
        "bytes": abs_path.stat().st_size,
        "exists": True,
        "category": derive_category(stem),
        "tags": [],
        "alt_ko": "",
        "review_status": "pending",
        "reviewed_by": None,
        "review_date": None,
        "use_in": derive_format_hint(stem),
        "aliases": [],
        "generation_prompt": None,
        "known_issues": None,
    }


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {"version": 1, "assets": {}}
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"⚠️  manifest.json is corrupt ({e}) — rebuilding from scratch", file=sys.stderr)
        return {"version": 1, "assets": {}}
    if "assets" not in data:
        data["assets"] = {}
    data.setdefault("version", 1)
    return data


def discover_files() -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for p in sorted(ASSETS_DIR.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in IMAGE_EXTS:
            continue
        if p.name.startswith("."):
            continue
        rel = p.relative_to(ASSETS_DIR).as_posix()
        out.append((rel, p))
    return out


def discover_alt_texts() -> dict[str, set[str]]:
    """Scan handouts/decks/lab-reports HTML for <img src="…shared/assets/…" alt="…">
    pairs. Returns {asset_rel_path: {alt_text_variants}}.

    Used to backfill the manifest's alt_ko field on first run so authors don't
    have to retype dozens of alt texts they already wrote.
    """
    found: dict[str, set[str]] = {}
    for mat in MATERIAL_DIRS:
        d = ROOT / mat
        if not d.exists():
            continue
        for html in d.rglob("*.html"):
            try:
                text = html.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for tag in _IMG_TAG_RE.findall(text):
                src_m = _SRC_RE.search(tag)
                if not src_m:
                    continue
                # Normalize: trim any leading "../" segments → leaves "shared/assets/foo"
                src = src_m.group(1)
                idx = src.find("shared/assets/")
                if idx < 0:
                    continue
                rel = src[idx + len("shared/assets/"):]
                if not rel:
                    continue
                alt_m = _ALT_RE.search(tag)
                alt = (alt_m.group(1).strip() if alt_m else "")
                if not alt:
                    continue
                found.setdefault(rel, set()).add(alt)
    return found


def backfill_alt(assets: dict[str, Any], verbose: bool = True) -> int:
    """Populate empty alt_ko fields from HTML evidence. Only fills when a
    single consistent alt text was seen — otherwise leaves blank with a note.
    """
    alt_map = discover_alt_texts()
    filled = 0
    for k, v in assets.items():
        if v.get("alt_ko"):
            continue
        f = v.get("file")
        if not f:
            continue
        alts = alt_map.get(f)
        if not alts:
            continue
        if len(alts) == 1:
            v["alt_ko"] = next(iter(alts))
            filled += 1
            if verbose:
                print(f"  alt_ko set:  {k}  → {v['alt_ko'][:60]}{'…' if len(v['alt_ko']) > 60 else ''}")
        else:
            v["known_issues"] = (
                f"multiple alt texts found in HTML — pick one: "
                + " | ".join(sorted(alts))
            )
            if verbose:
                print(f"  alt_ko AMBIG: {k}  ({len(alts)} variants — see known_issues)")
    return filled


def sync(verbose: bool = True) -> tuple[int, int, int]:
    """Sync manifest with disk. Returns (added, refreshed, missing) counts."""
    manifest = load_manifest()
    assets: dict[str, Any] = manifest["assets"]

    by_file: dict[str, str] = {}
    for k, v in assets.items():
        f = v.get("file")
        if f:
            by_file[f] = k

    on_disk_keys: set[str] = set()
    added = refreshed = 0

    for rel, abs_path in discover_files():
        existing_key = by_file.get(rel)
        if existing_key is not None:
            entry = assets[existing_key]
            entry["file"] = rel
            entry["format"] = abs_path.suffix.lstrip(".").lower()
            entry["bytes"] = abs_path.stat().st_size
            entry["exists"] = True
            on_disk_keys.add(existing_key)
            refreshed += 1
        else:
            key = abs_path.stem
            base_key, n = key, 2
            while key in assets:
                key = f"{base_key}-{n}"
                n += 1
            assets[key] = skeleton_entry(rel, abs_path)
            on_disk_keys.add(key)
            added += 1
            if verbose:
                print(f"  + {key}  ({rel})")

    missing = 0
    for k, v in assets.items():
        if k in on_disk_keys:
            continue
        if v.get("exists", True):
            v["exists"] = False
            missing += 1
            if verbose:
                print(f"  ! {k} no longer on disk → marked exists=false")

    # Backfill alt text from existing HTML (only fills empty alt_ko fields)
    filled = backfill_alt(assets, verbose=verbose)

    manifest["assets"] = dict(sorted(assets.items()))

    if verbose and filled:
        print(f"  alt_ko backfilled from HTML: {filled}")

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if verbose:
        total = len(manifest["assets"])
        print(f"manifest synced: {total} entries  (+{added} new, {refreshed} refreshed, {missing} missing)")

    return added, refreshed, missing


def main() -> int:
    sync(verbose=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
