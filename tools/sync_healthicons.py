"""Vendor Healthicons SVGs into shared/assets/healthicons/ and emit
shared/assets/healthicons.manifest.json.

Healthicons (https://github.com/resolvetosavelives/healthicons) is a CC-MIT
icon library curated by Resolve to Save Lives in collaboration with WHO. We
vendor a subset (public/icons/svg) into the repo so that:
  - Pages PDF rendering needs no external network during Playwright runs.
  - The set is reproducible by SHA pin, not by upstream's latest main.
  - The asset library treats them like any other entry — same resolver,
    same lint, same data-asset="key" pattern in HTML.

Manifest separation:
  - shared/assets/manifest.json — authored / curated assets (hand-edited).
  - shared/assets/healthicons.manifest.json — this file. Auto-generated.
    Hand-edits would be wiped on the next sync. Use the seed translation
    file (tools/healthicons_alt_ko.json) to inject Korean alt text into
    selected keys instead.

Idempotent: re-running with the same HEALTHICONS_REF produces an
identical tree.  Bump HEALTHICONS_REF below to refresh the vendored copy.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


# --- Pinning ----------------------------------------------------------- #

HEALTHICONS_REPO = "https://github.com/resolvetosavelives/healthicons.git"
HEALTHICONS_REF = "891ace7addf4deb7a8b1ce8292d5906064fab36a"  # 2026-05-22 main
HEALTHICONS_RAW = "https://raw.githubusercontent.com/resolvetosavelives/healthicons"


# --- Paths ------------------------------------------------------------- #

ROOT = Path(__file__).parent.parent.resolve()
ASSETS_DIR = ROOT / "shared" / "assets"
VENDOR_DIR = ASSETS_DIR / "healthicons"
MANIFEST_PATH = ASSETS_DIR / "healthicons.manifest.json"
SEED_ALT_PATH = ROOT / "tools" / "healthicons_alt_ko.json"
WORKDIR = Path("/tmp/healthicons-vendor")

# Healthicons folder in upstream — we only want this subtree.
UPSTREAM_SVG_DIR = "public/icons/svg"

# Style variants to keep. The upstream also ships `*-24px` variants optimized
# for pixel-snapped 24×24 UI chrome; patient-education materials render icons
# at 64-200px where the primary `filled`/`outline` versions look better, so
# we skip the 24px subset to halve disk + manifest size.
ALLOWED_STYLES = {"filled", "outline"}


# --- Shell helpers ----------------------------------------------------- #

def _run(cmd: list[str], cwd: Path | None = None, capture: bool = False) -> str:
    """Run a command, raise on non-zero, return stdout when capture=True."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=True,
    )
    return (result.stdout or "") if capture else ""


# --- Clone / vendor ---------------------------------------------------- #

def fetch_upstream(ref: str) -> Path:
    """Sparse-fetch only public/icons/svg at the pinned SHA into WORKDIR.

    Uses git's uploadpack.allowReachableSHA1InWant (enabled on GitHub) to
    avoid downloading history.  Treesame WORKDIR is reused across runs.
    """
    needs_fresh = not WORKDIR.exists() or not (WORKDIR / ".git").exists()
    if needs_fresh:
        if WORKDIR.exists():
            shutil.rmtree(WORKDIR)
        WORKDIR.mkdir(parents=True)
        _run(["git", "init", "-q"], cwd=WORKDIR)
        _run(["git", "remote", "add", "origin", HEALTHICONS_REPO], cwd=WORKDIR)
        _run(["git", "sparse-checkout", "init", "--cone"], cwd=WORKDIR)
        _run(["git", "sparse-checkout", "set", UPSTREAM_SVG_DIR], cwd=WORKDIR)

    _run(
        ["git", "fetch", "--depth", "1", "--filter=blob:none", "origin", ref],
        cwd=WORKDIR,
    )
    _run(["git", "checkout", "FETCH_HEAD"], cwd=WORKDIR)

    upstream = WORKDIR / UPSTREAM_SVG_DIR
    if not upstream.exists():
        raise RuntimeError(
            f"upstream subtree missing after fetch: {upstream} — "
            f"upstream may have restructured; bump HEALTHICONS_REF or "
            f"adjust UPSTREAM_SVG_DIR"
        )
    return upstream


def upstream_commit_date(ref: str) -> str:
    """ISO date of the pinned commit. Stable across re-runs with the same SHA."""
    iso = _run(["git", "log", "-1", "--format=%cI", ref], cwd=WORKDIR, capture=True).strip()
    return iso[:10] if iso else date.today().isoformat()


def vendor_svgs(upstream: Path) -> tuple[int, int]:
    """Copy SVGs from upstream into VENDOR_DIR, pruning files that no longer
    exist upstream. Returns (copied, pruned).

    Layout mirrored from upstream: <style>/<topic>/<name>.svg.
    """
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)

    # Collect what should exist after sync.
    desired: set[Path] = set()
    copied = 0
    for src in sorted(upstream.rglob("*.svg")):
        if src.name.startswith("."):
            continue
        rel = src.relative_to(upstream)
        if rel.parts[0] not in ALLOWED_STYLES:
            continue
        dst = VENDOR_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Cheap dedup: skip rewriting if size+mtime would imply no change.
        if dst.exists() and dst.stat().st_size == src.stat().st_size:
            try:
                if dst.read_bytes() == src.read_bytes():
                    desired.add(dst.resolve())
                    continue
            except OSError:
                pass
        shutil.copy2(src, dst)
        desired.add(dst.resolve())
        copied += 1

    # Prune files in VENDOR_DIR that aren't in upstream anymore (keep LICENSE).
    pruned = 0
    for p in list(VENDOR_DIR.rglob("*")):
        if not p.is_file():
            continue
        if p.name == "LICENSE":
            continue
        if p.suffix.lower() != ".svg":
            continue
        if p.resolve() not in desired:
            p.unlink()
            pruned += 1

    # Clean up now-empty directories.
    for d in sorted(VENDOR_DIR.rglob("*"), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()

    return copied, pruned


def fetch_license(ref: str) -> bool:
    """Pull the upstream LICENSE into VENDOR_DIR/LICENSE.  Returns True
    when fetched fresh (or content changed), False on identical no-op."""
    url = f"{HEALTHICONS_RAW}/{ref}/LICENSE"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:  # noqa: S310 — pinned GitHub URL
            body = resp.read()
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️  LICENSE fetch failed ({e}) — skipping", file=sys.stderr)
        return False
    dst = VENDOR_DIR / "LICENSE"
    if dst.exists() and dst.read_bytes() == body:
        return False
    dst.write_bytes(body)
    return True


# --- Manifest emission ------------------------------------------------- #

def _scan_collisions(upstream: Path) -> dict[tuple[str, str], set[str]]:
    """Return {(style, name): {topics}} so we can decide whether to use
    the short key `hi-<style>-<name>` or the topic-disambiguated
    `hi-<style>-<topic>-<name>` form."""
    collisions: dict[tuple[str, str], set[str]] = {}
    for svg in upstream.rglob("*.svg"):
        rel = svg.relative_to(upstream).parts
        if len(rel) < 3:
            continue
        style, topic, name_with_ext = rel[0], rel[1], rel[-1]
        if style not in ALLOWED_STYLES:
            continue
        name = name_with_ext[:-4]
        collisions.setdefault((style, name), set()).add(topic)
    return collisions


def _key_for(style: str, topic: str, name: str,
             collisions: dict[tuple[str, str], set[str]]) -> str:
    topics = collisions.get((style, name), {topic})
    if len(topics) <= 1:
        return f"hi-{style}-{name}"
    return f"hi-{style}-{topic}-{name}"


def load_seed_alt() -> dict[str, str]:
    if not SEED_ALT_PATH.exists():
        return {}
    try:
        return json.loads(SEED_ALT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  ⚠️  seed alt file is invalid JSON ({e}) — ignoring", file=sys.stderr)
        return {}


def build_manifest(upstream: Path, ref: str, commit_date: str) -> dict[str, Any]:
    """Walk vendored healthicons/, emit a manifest dict ready to dump."""
    collisions = _scan_collisions(upstream)
    seed_alt = load_seed_alt()

    assets: dict[str, Any] = {}
    for svg in sorted(VENDOR_DIR.rglob("*.svg")):
        rel = svg.relative_to(ASSETS_DIR).as_posix()  # "healthicons/filled/body/heart.svg"
        rel_in_hi = svg.relative_to(VENDOR_DIR).parts  # ("filled", "body", "heart.svg")
        if len(rel_in_hi) < 3:
            continue
        style, topic, name_with_ext = rel_in_hi[0], rel_in_hi[1], rel_in_hi[-1]
        name = name_with_ext[:-4]
        key = _key_for(style, topic, name, collisions)
        alt_ko = (seed_alt.get(key) or "").strip()
        assets[key] = {
            "file": rel,
            "format": "svg",
            "bytes": svg.stat().st_size,
            "exists": True,
            "category": f"hi-{topic}",
            "tags": [style, topic],
            "alt_ko": alt_ko,
            "review_status": "approved",
            "reviewed_by": "healthicons-import",
            "review_date": commit_date,
            "use_in": ["deck", "handout", "lab-report"],
            "aliases": [],
            "generation_prompt": None,
            "known_issues": None,
            "healthicons": {
                "style": style,
                "topic": topic,
                "name": name,
                "ref": ref,
            },
        }

    return {
        "version": 1,
        "source": "https://github.com/resolvetosavelives/healthicons",
        "license": "MIT",
        "ref": ref,
        "ref_date": commit_date,
        "assets": dict(sorted(assets.items())),
    }


def write_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# --- Entry point ------------------------------------------------------- #

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Vendor Healthicons SVGs + emit manifest"
    )
    parser.add_argument(
        "--ref",
        default=HEALTHICONS_REF,
        help=f"Healthicons commit SHA to pin (default: {HEALTHICONS_REF[:10]}…)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the vendored tree matches the manifest (no writes)",
    )
    args = parser.parse_args()

    if args.check:
        if not MANIFEST_PATH.exists():
            print("✗ healthicons.manifest.json missing — run without --check", file=sys.stderr)
            return 2
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        missing: list[str] = []
        for key, entry in manifest.get("assets", {}).items():
            f = entry.get("file", "")
            if not (ASSETS_DIR / f).exists():
                missing.append(f"{key} → shared/assets/{f}")
        if missing:
            print(f"✗ {len(missing)} manifest entries point to missing files:", file=sys.stderr)
            for m in missing[:10]:
                print(f"    {m}", file=sys.stderr)
            return 2
        print(f"✓ healthicons manifest matches disk ({len(manifest.get('assets', {}))} entries)")
        return 0

    print(f"healthicons sync: ref={args.ref[:10]}…")
    upstream = fetch_upstream(args.ref)
    commit_date = upstream_commit_date(args.ref)
    print(f"  upstream date: {commit_date}")

    copied, pruned = vendor_svgs(upstream)
    license_changed = fetch_license(args.ref)
    print(f"  svgs: +{copied} copied, -{pruned} pruned"
          f"{' · LICENSE updated' if license_changed else ''}")

    manifest = build_manifest(upstream, args.ref, commit_date)
    write_manifest(manifest)
    seeded = sum(1 for v in manifest["assets"].values() if v["alt_ko"])
    print(
        f"  manifest: {len(manifest['assets'])} entries "
        f"({seeded} with seed alt_ko)"
    )

    # Surface seed entries that don't map to a real manifest key so typos
    # in healthicons_alt_ko.json don't silently no-op forever.
    seed_alt = load_seed_alt()
    asset_keys = set(manifest["assets"].keys())
    stale = [
        k for k in seed_alt
        if k.startswith("hi-") and k not in asset_keys
    ]
    if stale:
        print(
            f"  ⚠️  {len(stale)} seed alt key(s) not in manifest — fix or remove:",
            file=sys.stderr,
        )
        for k in stale:
            print(f"      - {k}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
