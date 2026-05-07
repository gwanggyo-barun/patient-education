"""Phase 2 — Classify each inventory row into target_kind/category_dir/slug.

Outputs inventory_classified.csv with extra columns:
    target_kind   = decks | handouts | lab-reports | SKIP
    category_dir  = gi/cardio/endocrine/...
    slug          = url-safe English slug
    target_path   = decks/{cat}/{slug}/  (full target dir)
    conflict      = if slug clashes with existing build.py TARGETS
    note          = any caveat worth flagging
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_IN = ROOT / "inventory.csv"
CSV_OUT = ROOT / "inventory_classified.csv"

# Existing slugs in build.py — must NOT collide
EXISTING_DECKS = {"gerd", "hpylori", "morning-htn", "oh-management-2026", "endoscopy-cpr-training"}
EXISTING_HANDOUTS = {"colonoscopy", "cpr-flowchart", "crash-cart-checklist", "crash-cart-map"}
EXISTING_LAB = {"lipid-panel"}

# Page-id-prefix → (kind, category, slug, [optional note])
# Hand-curated mapping: 31 teaching + 12 handout = 43 rows
MAPPING: dict[str, tuple[str, str, str, str]] = {
    # ===== Teaching DB (31 rows with attachments) =====
    "335b8014-24d6-811c-a890-d9c13f590ee7": ("decks", "gi", "appendicitis-diverticulitis", ""),
    "335b8014-24d6-81eb-9f2f-d4dddc5368aa": ("decks", "gi", "atrophic-gastritis", ""),
    "336b8014-24d6-8100-ae88-e349ac023241": ("decks", "endocrine", "hypothyroidism", ""),
    "336b8014-24d6-8113-b5a4-d8e7ea26a162": ("handouts", "lifestyle", "dyslipidemia-diet", ""),
    "336b8014-24d6-8130-abf1-fc7fcae5b836": ("decks", "endocrine", "hyperthyroidism", ""),
    "336b8014-24d6-8140-b964-df3da52f3145": ("decks", "cardio", "chest-pain", ""),
    "336b8014-24d6-8175-9bea-dba644961397": ("handouts", "lifestyle", "iron-deficiency-anemia-diet", ""),
    "336b8014-24d6-8176-8777-fa7badeb1393": ("decks", "infectious", "ltbi-overview", ""),
    "336b8014-24d6-818e-8e46-c7ddaa3cfe31": ("decks", "gi", "hpylori-overview", "Conflict: 'hpylori' is auto-build (제균 치료). Renamed to 'hpylori-overview' (전반 진료설명)."),
    "336b8014-24d6-81a1-b538-c6fd20b53a04": ("decks", "endocrine", "dyslipidemia", ""),
    "336b8014-24d6-81c9-accd-dd3b347e7be4": ("decks", "vaccines", "pneumococcal", ""),
    "336b8014-24d6-81e4-88a6-dace03783f8e": ("decks", "cardio", "vasovagal-syncope", ""),
    "336b8014-24d6-81f7-ad15-ebcd09c1f799": ("decks", "uro", "microscopic-hematuria", ""),
    "343b8014-24d6-8100-8b61-c4ee4f6ba862": ("decks", "endocrine", "advanced-lipid-biomarkers", ""),
    "343b8014-24d6-810b-a175-eabc0476c717": ("decks", "gi", "chronic-constipation", ""),
    "343b8014-24d6-8152-97de-d22db56df5a4": ("decks", "infectious", "herpes-zoster", ""),
    "343b8014-24d6-8156-b8e6-f7c5a938835c": ("decks", "pulmo", "post-infectious-cough", ""),
    "343b8014-24d6-816b-bab0-ec4164760463": ("decks", "pulmo", "osa", ""),
    "343b8014-24d6-8170-a823-c94ab1db6210": ("decks", "gi", "post-polypectomy", ""),
    "343b8014-24d6-8173-9b39-e46a4a2bd57b": ("decks", "endocrine", "osteoporosis", ""),
    "343b8014-24d6-81aa-aa45-c1f4c42d2942": ("decks", "infectious", "influenza-antivirals", ""),
    "343b8014-24d6-81b1-a7e1-c1453853c4f5": ("decks", "pulmo", "pft", ""),
    "343b8014-24d6-81b1-beb1-cb31aa9e1ed4": ("decks", "gi", "ibs", ""),
    "343b8014-24d6-81ba-802b-e2c202272dbc": ("decks", "cardio", "antihypertensive-classes", ""),
    "343b8014-24d6-81bb-a2ed-fdfefd16caf4": ("decks", "vaccines", "pneumococcal-comparison", ""),
    "343b8014-24d6-81de-bf56-df50c2d63d2e": ("decks", "derm", "chronic-urticaria", ""),
    "343b8014-24d6-81e1-ab32-f3fb8262d78a": ("decks", "gi", "acute-gastroenteritis-diet", ""),
    "343b8014-24d6-81f5-8943-dd50fa081a57": ("decks", "pulmo", "asthma", ""),
    "343b8014-24d6-81fc-a56c-d477bc47ee01": ("decks", "cardio", "eye-cardiovascular", "닥터눈: 눈·심혈관 건강 통합 자료"),
    "344b8014-24d6-8197-9eda-ce728da95b98": ("decks", "infectious", "ltbi-treatment", ""),
    "344b8014-24d6-81c6-9111-ce9f6bb755a1": ("decks", "endocrine", "subacute-thyroiditis", ""),

    # ===== Handout DB (12 rows) =====
    "341b8014-24d6-8115-86c9-c488dd001a93": ("handouts", "lifestyle", "diabetes-diet", ""),
    "341b8014-24d6-813f-80d5-f9cb1fa730a4": ("handouts", "forms", "hypertension-intake", ""),
    "341b8014-24d6-8171-a015-fcedcf4f5b5d": ("handouts", "endoscopy", "colonoscopy-prep", "Auto-build 'colonoscopy' covers same topic; consider merge — flagged"),
    "341b8014-24d6-8183-8a2d-c64a65b4d2f9": ("handouts", "screening", "checkup-prep", ""),
    "341b8014-24d6-8187-b711-cda817a6a88e": ("handouts", "endoscopy", "post-egd", ""),
    "341b8014-24d6-818f-9cf0-c8e7fce9b1fe": ("handouts", "lifestyle", "hypertension-low-salt", ""),
    "341b8014-24d6-8194-98d4-fe13ee29cdc1": ("handouts", "lifestyle", "dyslipidemia-diet-exercise", ""),
    "341b8014-24d6-81b2-998a-cf216c4e8fc3": ("handouts", "endoscopy", "post-colonoscopy", ""),
    "341b8014-24d6-81e9-a2bd-d4b5738396ad": ("handouts", "forms", "diabetes-intake", ""),
    "342b8014-24d6-819b-8a77-e408629962d7": ("handouts", "screening", "fit-positive", ""),
    "343b8014-24d6-8156-9033-cfce2b3cb86f": ("handouts", "forms", "glp1-intake", ""),
    "34ab8014-24d6-8105-ad10-e0b09bff9013": ("handouts", "forms", "chronic-disease-intake", ""),
}


def main():
    rows_in = list(csv.DictReader(CSV_IN.open(encoding="utf-8")))
    rows_out = []
    skipped = 0
    for r in rows_in:
        pid = r["page_id"]
        if r["attachment_count"] == "0":
            r.update({
                "target_kind": "SKIP",
                "category_dir": "",
                "slug": "",
                "target_path": "",
                "conflict": "",
                "note": "이미 자동빌드된 행 (첨부 0)",
            })
            skipped += 1
        elif pid in MAPPING:
            kind, cat, slug, note = MAPPING[pid]
            existing = (
                EXISTING_DECKS if kind == "decks"
                else EXISTING_HANDOUTS if kind == "handouts"
                else EXISTING_LAB
            )
            conflict = "YES" if slug in existing else ""
            r.update({
                "target_kind": kind,
                "category_dir": cat,
                "slug": slug,
                "target_path": f"{kind}/{cat}/{slug}/" if cat else f"{kind}/{slug}/",
                "conflict": conflict,
                "note": note,
            })
        else:
            r.update({
                "target_kind": "UNMAPPED",
                "category_dir": "",
                "slug": "",
                "target_path": "",
                "conflict": "",
                "note": "MAPPING dict에 없음 — 추가 필요",
            })

        rows_out.append(r)

    fieldnames = list(rows_out[0].keys())
    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows_out)

    # Summary
    by_kind: dict[str, int] = {}
    for r in rows_out:
        by_kind[r["target_kind"]] = by_kind.get(r["target_kind"], 0) + 1
    print(f"Wrote {CSV_OUT} ({len(rows_out)} rows)")
    print("By kind:", by_kind)
    conflicts = [r for r in rows_out if r.get("conflict") == "YES"]
    if conflicts:
        print(f"⚠️ {len(conflicts)} slug conflicts:")
        for r in conflicts:
            print(f"  · {r['title']} → {r['target_path']}")
    notes = [r for r in rows_out if r.get("note") and r["target_kind"] not in ("SKIP",)]
    if notes:
        print(f"\nℹ️ {len(notes)} rows with notes:")
        for r in notes:
            print(f"  · {r['title']}: {r['note']}")


if __name__ == "__main__":
    main()
