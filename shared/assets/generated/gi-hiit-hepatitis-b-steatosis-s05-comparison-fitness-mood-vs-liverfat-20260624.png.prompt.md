# HIIT·만성B형간염+지방간 — slide 05 raster visual (Comparison)

- Asset: `gi-hiit-hepatitis-b-steatosis-s05-comparison-fitness-mood-vs-liverfat-20260624.png`
- Tool: Codex CLI 0.142.0 `/imagen` (built-in image_gen), invoked directly (wrapper has a bug)
- Deck/slide: `decks/gi/hiit-hepatitis-b-steatosis` — slide 05 (결과②: 체력·기분(유의) vs 간지방(비유의))
- Slot: `.ai-visual ai-visual--focus ai-visual--fill ai-visual--diagram` (visual-focus right column, object-fit: contain)
- Slot ratio: strictly ~0.78:1 portrait, target ~760 x 900 px (zero crop)
- Visual intent: Comparison — two strong (significant) outcomes vs one weak/uncertain outcome

---

A simple comparison bar chart contrasting THREE outcomes by how clear the effect was.
BAR 1 = cardiorespiratory FITNESS (improved): a tall, solid, confident bar reaching high.
BAR 2 = emotional WELL-BEING / MOOD (improved): another tall, solid, confident bar reaching high.
BAR 3 = LIVER FAT (uncertain / non-significant): a short, faint / hollow / dashed-outline bar that
clearly reads as weak and inconclusive — e.g. a translucent low-opacity fill with a small uncertainty
whisker on top. It must read as "not established," NOT as a confident result.
The contrast is the whole message: two strong solid bars versus one weak / uncertain bar.

visual_type: Comparison / clean infographic bar chart, flat educational style.

palette: brand Navy #003366 and Steel Blue #5B9BD5 for the two strong (fitness, mood) solid bars; the
uncertain liver-fat bar is a faint / translucent steel outline (low opacity) so it reads as
weak / undetermined. Soft #f8fbff background; faint steel reference frames. NO red — this is an outcome
chart with no blood; red is reserved strictly for blood/bleeding imagery.

composition: three bars (two tall solid + one short/faint), centered, evenly filling the canvas; the bar
tops and the uncertainty whisker must NOT be clipped at the edges.

aspect ratio strictly 768 x 960 (portrait ~0.8:1), match the slot so object-fit:contain has zero crop.

constraints: ABSOLUTELY NO TEXT, NUMBERS, AXIS LABELS, OR PERCENT/UNIT SIGNS anywhere on the canvas —
no characters in any language. The labels ("체력 ↑", "기분 ↑", "간 지방 ?") and values are overlaid via
HTML Pretendard separately. Bars span the canvas evenly — no empty side panels.
