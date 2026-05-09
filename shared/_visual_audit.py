"""Live visual audit — render every TARGETS material on the production URL,
verify CSS actually loaded, font applied, and element sizes are correct.

Catches issues that the bbox-only `_validate_layout.py` misses:
- CSS @import / link broken even though the file exists at build time
- 4-level vs 3-level deep slug path mismatch on production
- Custom CSS swallowing the global stylesheet rules
- Pretendard font failing to load (CDN block)

Usage:
    python -m shared._visual_audit              # check all TARGETS
    python -m shared._visual_audit --kind=decks # decks only

Returns exit 0 if all clean, 1 if any failure (suitable for CI gate).
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT_PUB = "https://gwanggyo-barun.github.io/patient-education"
ROOT = Path(__file__).resolve().parent.parent


def _load_targets():
    """Re-import build.TARGETS without running main()."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "shared"))
    import importlib.util
    spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TARGETS


AUDIT_JS = r"""
(() => {
  const sheets = [...document.styleSheets];
  let loaded = 0, externalTotal = 0;
  for (const s of sheets) {
    try {
      const rules = s.cssRules.length;
      if (rules > 0) loaded++;
      if (s.href) externalTotal++;
    } catch {}
  }
  const body = document.body;
  const bodyStyle = getComputedStyle(body);
  const sel = document.querySelector('.slide, .page');
  const rect = sel ? sel.getBoundingClientRect() : null;
  const elCount = document.querySelectorAll('.slide').length || document.querySelectorAll('.page').length;
  return {
    sheetsLoaded: loaded,
    sheetsTotal: sheets.length,
    elementSize: rect ? `${Math.round(rect.width)}x${Math.round(rect.height)}` : 'none',
    elementCount: elCount,
    bodyFont: bodyStyle.fontFamily,
  };
})()
"""


def audit_one(page, url: str, kind: str) -> list[str]:
    issues: list[str] = []
    try:
        page.goto(url, timeout=30000, wait_until="networkidle")
    except Exception as e:
        return [f"load failed: {e}"]
    data = page.evaluate(AUDIT_JS)
    if data["sheetsLoaded"] < data["sheetsTotal"]:
        issues.append(f"CSS partial: {data['sheetsLoaded']}/{data['sheetsTotal']} sheets active")
    if data["elementCount"] == 0:
        issues.append("no .slide/.page elements")
    if "Pretendard" not in data["bodyFont"]:
        issues.append(f"font wrong: {data['bodyFont'][:40]}")
    if kind == "decks" and data["elementSize"] != "none":
        try:
            w, _ = data["elementSize"].split("x")
            if int(w) < 1000:
                issues.append(f"slide too small: {data['elementSize']}")
        except Exception:
            pass
    return issues


def main():
    targets = _load_targets()
    kind_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--kind="):
            kind_filter = arg.split("=", 1)[1]
    if kind_filter:
        targets = [t for t in targets if t["kind"] == kind_filter]

    print(f"Visual audit: {len(targets)} live URLs (production)…")
    failures: list[tuple[str, list[str]]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for i, t in enumerate(targets, 1):
            url = f"{ROOT_PUB}/{t['slug_path']}"
            kind = t["kind"]
            viewport = (
                {"width": 1320, "height": 800} if kind == "decks"
                else {"width": 820, "height": 1160}
            )
            ctx = browser.new_context(viewport=viewport)
            page = ctx.new_page()
            issues = audit_one(page, url, kind)
            if issues:
                failures.append((t["slug_path"], issues))
                print(f"  ✗ {t['slug_path']}: {', '.join(issues)}")
            ctx.close()
            if i % 10 == 0:
                print(f"    progress {i}/{len(targets)}")
        browser.close()

    if failures:
        print(f"\nFAIL: {len(failures)} of {len(targets)} materials")
        sys.exit(1)
    print(f"\nOK: all {len(targets)} materials render correctly")
    sys.exit(0)


if __name__ == "__main__":
    main()
