"""Phase 4 — Generate build.py TARGETS dict entries from inventory_classified.csv.

Output: Python source snippets ready to paste into build.py TARGETS list.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CSV_IN = ROOT / "_migration" / "inventory_classified.csv"


def gen_entry(row: dict) -> str:
    kind = row["target_kind"]
    if kind not in ("decks", "handouts", "lab-reports"):
        return ""
    slug = row["slug"]
    cat = row["category_dir"]
    slug_path = f"{kind}/{cat}/{slug}/" if cat else f"{kind}/{slug}/"
    qr_class = "qr-block__code" if kind == "decks" else "qr-mini__code"
    fmt = "deck-16x9" if kind == "decks" else "a4-portrait"

    title = row["title"].strip()
    category = row["category"].strip()
    audience = row["audience"].strip()
    disease = row["detail"].strip() or title

    return (
        "    {\n"
        f'        "kind": "{kind}", "slug": "{slug}",\n'
        f'        "slug_path": "{slug_path}",\n'
        f'        "html_path": ROOT / "{slug_path}index.html",\n'
        f'        "qr_class": "{qr_class}", "fmt": "{fmt}",\n'
        f'        "title": "{title}",\n'
        f'        "category": "{category}", "audience": "{audience}", "disease": "{disease}",\n'
        "    },"
    )


def main():
    rows = list(csv.DictReader(CSV_IN.open(encoding="utf-8")))
    targets_decks = []
    targets_handouts = []
    targets_lab = []
    for r in rows:
        kind = r["target_kind"]
        entry = gen_entry(r)
        if not entry:
            continue
        if kind == "decks":
            targets_decks.append(entry)
        elif kind == "handouts":
            targets_handouts.append(entry)
        elif kind == "lab-reports":
            targets_lab.append(entry)

    out = []
    if targets_decks:
        out.append(f"    # === Migration: {len(targets_decks)} new decks ===\n")
        out.extend(targets_decks)
    if targets_handouts:
        out.append(f"\n    # === Migration: {len(targets_handouts)} new handouts ===\n")
        out.extend(targets_handouts)
    if targets_lab:
        out.append(f"\n    # === Migration: {len(targets_lab)} new lab-reports ===\n")
        out.extend(targets_lab)

    text = "\n".join(out)
    out_file = ROOT / "_migration" / "build_targets_snippet.py"
    out_file.write_text(text, encoding="utf-8")
    print(f"Wrote {out_file}")
    print(f"  Decks: {len(targets_decks)}, Handouts: {len(targets_handouts)}, Lab: {len(targets_lab)}")
    print(f"  Total: {len(targets_decks) + len(targets_handouts) + len(targets_lab)}")


if __name__ == "__main__":
    main()
