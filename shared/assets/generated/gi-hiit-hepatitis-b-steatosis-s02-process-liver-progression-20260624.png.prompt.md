# HIIT·만성B형간염+지방간 — slide 02 raster visual (Process)

- Asset: `gi-hiit-hepatitis-b-steatosis-s02-process-liver-progression-20260624.png`
- Tool: Codex CLI 0.142.0 `/imagen` (built-in image_gen), invoked directly (wrapper has a bug)
- Deck/slide: `decks/gi/hiit-hepatitis-b-steatosis` — slide 02 (왜 중요한가: 정상간→지방간→염증/섬유화)
- Slot: `.ai-visual ai-visual--focus ai-visual--fill ai-visual--diagram` (visual-focus right column, object-fit: contain)
- Slot ratio: strictly ~0.78:1 portrait, target ~760 x 900 px (zero crop)
- Visual intent: Process — chronic-hepatitis-B liver worsening when fat is added

---

A 3-stage PROCESS medical illustration of how a chronic-hepatitis-B liver worsens when fat is added.
STAGE 1 = a healthy liver cross-section: smooth, evenly textured tissue with clear small blood vessels.
STAGE 2 = the SAME liver with fatty change — many round pale fat droplets accumulating inside the liver
cells (hepatic steatosis), the tissue looking pale and swollen.
STAGE 3 = inflammation + early fibrosis — the fatty, virus-affected liver now with inflamed patches and
pale fibrous strands / scar bands beginning to stiffen the tissue. Include a few small navy/steel virus
particles dotted in the tissue to signal the chronic-B-virus context.
Show clear directional arrows indicating the worsening progression between the three stages.

visual_type: Process / mechanism medical illustration, clean educational cross-section style.

palette: §20 ANATOMICAL COLOR RULE — liver TISSUE and BLOOD/vessels are rendered in realistic warm red /
red-brown (this is organ tissue, blood is red). The accumulating FAT droplets are a pale warm yellow /
cream. Brand Navy #003366 + Steel Blue #5B9BD5 are reserved for the soft #f8fbff background, outlines,
directional arrows, and any virus-particle accents ONLY. Do NOT tint the liver tissue navy/steel.

composition: 3 stages, evenly distributed, all roughly equal size, centered, filling the canvas. Arrow
tips and all three liver panels MUST NOT be clipped at the edges. A portrait layout stacking the 3
stages top-to-bottom with downward arrows reads well for this slot — keep zero edge clipping either way.

aspect ratio strictly 768 x 960 (portrait ~0.8:1), match the slot so object-fit:contain has zero crop.

constraints: ABSOLUTELY NO TEXT — no letters, numbers, words, labels, or captions in any language
anywhere on the canvas. Korean stage labels ("정상 간", "지방간", "염증·섬유화") are overlaid via HTML
Pretendard separately. No empty side panels — illustration spans the entire canvas evenly.
