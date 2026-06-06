# Layout Sweep Report

Date: 2026-06-07

Scope:
- Excluded decks touched since 2026-06-06 by `git log --since=2026-06-06 --name-only --pretty=format: | sort -u`.
- Targeted existing `decks/**/index.html` files with validator violations outside that exclusion list.
- Medical text, numeric data, drug names, and shared blocks were not intentionally changed.

## Summary

- Target decks: 60
- Validator pass after current sweep: 32
- Validator still failing: 28
- Commit: not created, per instruction.
- Screenshot visual audit: not completed. `tools/slide_screens.py` should be run after the gate passes so screenshots do not document known-failing layouts as acceptable.

## Validation Gate

Run:

```bash
bash docs/layout-sweep-gate.sh
```

Current result: fails because 28 target decks still have validator issues.

## Completed Pattern Fixes

Applied deck-local CSS only:
- Compact deck frame: smaller vertical slide padding, smaller title/footer spacing.
- Legacy hero/split/timeline/checklist/compare patterns: adjusted spacing, line-height, and minimum fill behavior.
- Closing QR blocks: compacted QR sizing and closing layout.
- Visual-focus gutter: raised local grid gap to match the 28-32px design rule.
- Paper-review components: compacted table rows, metric cards, split notes, and image captions.
- GLP injection deck: adjusted GLP-specific grid/card fill behavior.

## Passing Decks

- decks/heme/iron-deficiency-anemia/index.html
- decks/neurology/migraine/diagnosis/index.html
- decks/gi/ibs/index.html
- decks/gi/bowel-prep-low-volume/index.html
- decks/gi/gerd/lifestyle/index.html
- decks/gi/hpylori-overview/index.html
- decks/gi/h-pylori/eradication/index.html
- decks/gi/chronic-constipation/index.html
- decks/gi/acute-gastroenteritis-diet/index.html
- decks/gi/post-polypectomy/index.html
- decks/gi/appendicitis-diverticulitis/index.html
- decks/pulmo/post-infectious-cough/index.html
- decks/pulmo/osa/index.html
- decks/pulmo/pft-interpretation/index.html
- decks/cardio/chest-pain/index.html
- decks/cardio/eye-cardiovascular/index.html
- decks/cardio/htn-2025-aha-acc/index.html
- decks/cardio/vasovagal-syncope/index.html
- decks/cardio/antihypertensive-classes/index.html
- decks/emergency/endoscopy/cpr-training/index.html
- decks/endocrine/diabetes-first-visit/index.html
- decks/endocrine/hyperthyroidism/index.html
- decks/endocrine/osteoporosis/index.html
- decks/endocrine/hypothyroidism/index.html
- decks/endocrine/gout/index.html
- decks/endocrine/diabetes-mellitus-type2/index.html
- decks/infectious/ltbi-overview/index.html
- decks/infectious/herpes-zoster/index.html
- decks/infectious/influenza-antivirals/index.html
- decks/vaccines/pneumococcal/index.html
- decks/injections/glp1-injection/index.html
- decks/uro/microscopic-hematuria/index.html

## Remaining Issues

The following decks still require deck-specific layout work:

- decks/gi/atrophic-gastritis/index.html: `body_underfills`
- decks/general/papers-20260524/baxdrostat-baxhtn/index.html: `body_overlaps_footer`, `body_underfills`
- decks/general/papers-20260524/soy-legumes-htn/index.html: `body_overlaps_footer`, `body_underfills`
- decks/general/papers-20260524/tramadol-bmj/index.html: `body_overlaps_footer`
- decks/general/papers-20260524/rsv-realworld/index.html: `body_overlaps_footer`
- decks/general/papers-20260524/sglt2-glp1-combo/index.html: `body_overlaps_footer`, `body_underfills`, `box_content_overflow`
- decks/general/papers-20260525/once-weekly-insulin/index.html: `body_overlaps_footer`, `element_below_slide`
- decks/general/papers-20260525/cpap-personalized-cv/index.html: `body_underfills`, `font_too_small`
- decks/general/teen-height-growth/index.html: `body_underfills`
- decks/pulmo/asthma/index.html: `body_overlaps_footer`
- decks/pulmo/pft/index.html: `body_overlaps_footer`
- decks/cardio/orthostatic-hypotension/management-2026/index.html: `body_underfills`
- decks/cardio/htn/morning/index.html: `body_underfills`
- decks/endocrine/dyslipidemia/index.html: `body_underfills`
- decks/endocrine/glp1-weight-management/week-06-injection/index.html: `body_overlaps_footer`
- decks/endocrine/glp1-weight-management/week-02-aerobic/index.html: `body_overlaps_footer`
- decks/endocrine/glp1-weight-management/week-03-strength/index.html: `body_overlaps_footer`
- decks/endocrine/glp1-weight-management/week-04-nutrition/index.html: `body_overlaps_footer`
- decks/endocrine/glp1-weight-management/week-07-safety/index.html: `body_overlaps_footer`
- decks/endocrine/glp1-weight-management/week-01-start/index.html: `body_overlaps_footer`
- decks/endocrine/glp1-weight-management/week-05-gi-effects/index.html: `body_overlaps_footer`
- decks/endocrine/glp1-weight-management/week-08-maintenance/index.html: `body_overlaps_footer`
- decks/endocrine/prediabetes-remission/index.html: `body_underfills`
- decks/endocrine/subacute-thyroiditis/index.html: `body_underfills`
- decks/endocrine/advanced-lipid-biomarkers/index.html: `body_underfills`
- decks/derm/chronic-urticaria/index.html: `body_overlaps_footer`
- decks/infectious/ltbi-treatment/index.html: `body_underfills`
- decks/vaccines/pneumococcal-comparison/index.html: `body_overlaps_footer`

## Screenshot Paths

No final screenshot set was accepted. After all targets pass:

```bash
python3 tools/slide_screens.py <deck>/index.html /tmp/slide-screens/<deck-slug>
```

Record each reviewed directory here before commit.

## Round 2

Date: 2026-06-07

Scope: fixed the 28 remaining decks listed in `/tmp/sweep-remaining.md`. Changes were deck-local CSS/layout overrides only; medical copy, values, drug names, shared blocks, and validator scripts were not changed.

Validation:
- `PYTHONIOENCODING=utf-8 python3 shared/_validate_layout.py <deck-path>` passed for all 28 Round 2 decks.
- `bash docs/layout-sweep-gate.sh` exited 0.

Per-deck fixes:
- `decks/gi/atrophic-gastritis/index.html`: `body_underfills` -> expanded and vertically balanced Kimura legend cards on slide 5.
- `decks/general/papers-20260524/baxdrostat-baxhtn/index.html`: `body_overlaps_footer`, `body_underfills` -> compacted slide 3 split list/note and expanded slide 5 table row fill.
- `decks/general/papers-20260524/soy-legumes-htn/index.html`: `body_overlaps_footer`, `body_underfills` -> resized slide 3 portion visual/labels and expanded slide 5 table row fill.
- `decks/general/papers-20260524/tramadol-bmj/index.html`: `body_overlaps_footer` -> compacted slide 7 danger split note.
- `decks/general/papers-20260524/rsv-realworld/index.html`: `body_overlaps_footer` -> compacted slide 3 split list/note.
- `decks/general/papers-20260524/sglt2-glp1-combo/index.html`: `body_overlaps_footer`, `body_underfills`, `box_content_overflow` -> compacted slide 3 split content, added slide 5 table row slack/fill, and balanced slide 10 split notes.
- `decks/general/papers-20260525/once-weekly-insulin/index.html`: `body_overlaps_footer`, `element_below_slide` -> compacted slide 7 mechanism cards and converted slide 12 closing QR from stretched to content-height layout.
- `decks/general/papers-20260525/cpap-personalized-cv/index.html`: `body_underfills`, `font_too_small` -> lowered slide 3 caption and raised slide 11 table-note font to validator minimum.
- `decks/general/teen-height-growth/index.html`: `body_underfills` -> balanced priority cards, tile bodies, diet/sport banners, mistake cards, and step cards across slides 5, 6, 7, 9, 10, and 11.
- `decks/pulmo/asthma/index.html`: `body_overlaps_footer` -> compacted slide 7 grid tiles and slide 9 split metric block.
- `decks/pulmo/pft/index.html`: `body_overlaps_footer` -> compacted slide 4 split metric block.
- `decks/cardio/orthostatic-hypotension/management-2026/index.html`: `body_underfills` -> expanded slide 12 take-home list/item fill.
- `decks/cardio/htn/morning/index.html`: `body_underfills` -> expanded slide 6 alert strip fill.
- `decks/endocrine/dyslipidemia/index.html`: `body_underfills` -> expanded slide 5 target-row fill without crossing footer.
- `decks/endocrine/glp1-weight-management/week-01-start/index.html`: `body_overlaps_footer` -> converted slide 6 closing QR from stretched to content-height layout and reduced QR footprint.
- `decks/endocrine/glp1-weight-management/week-02-aerobic/index.html`: `body_overlaps_footer` -> same closing QR fix.
- `decks/endocrine/glp1-weight-management/week-03-strength/index.html`: `body_overlaps_footer` -> same closing QR fix.
- `decks/endocrine/glp1-weight-management/week-04-nutrition/index.html`: `body_overlaps_footer` -> same closing QR fix.
- `decks/endocrine/glp1-weight-management/week-05-gi-effects/index.html`: `body_overlaps_footer` -> same closing QR fix.
- `decks/endocrine/glp1-weight-management/week-06-injection/index.html`: `body_overlaps_footer` -> same closing QR fix.
- `decks/endocrine/glp1-weight-management/week-07-safety/index.html`: `body_overlaps_footer` -> same closing QR fix.
- `decks/endocrine/glp1-weight-management/week-08-maintenance/index.html`: `body_overlaps_footer` -> same closing QR fix.
- `decks/endocrine/prediabetes-remission/index.html`: `body_underfills` -> balanced slide 5 heart-rate rows.
- `decks/endocrine/subacute-thyroiditis/index.html`: `body_underfills` -> expanded and centered slide 3 split metric stack.
- `decks/endocrine/advanced-lipid-biomarkers/index.html`: `body_underfills` -> balanced slide 7 risk rows.
- `decks/derm/chronic-urticaria/index.html`: `body_overlaps_footer` -> compacted slide 6 UAS7 table/note and set bounded vertical fill.
- `decks/infectious/ltbi-treatment/index.html`: `body_underfills` -> expanded slide 3 regimen table rows and slide 5 alert strip fill.
- `decks/vaccines/pneumococcal-comparison/index.html`: `body_overlaps_footer` -> compacted slide 4 tri-column vaccine cards/lists.

Remaining unresolved issues: none.
