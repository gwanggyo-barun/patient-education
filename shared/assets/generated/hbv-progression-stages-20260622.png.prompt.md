# hbv — 자연경과 4단계 raster visual

- Asset: `hbv-progression-stages-20260622.png`
- Tool: built-in image_gen (Codex), invoked via `tools/codex_imagen_batch.sh` (--list, CODEX_HOME-isolated)
- Deck/slide: `decks/gi/chronic-hepatitis-b/overview` — slide 04 (자연경과 4단계)
- Slot: `.ai-visual ai-visual--focus ai-visual--fill` (visual-focus right column)
- Slot ratio: strict 16:9 (object-fit: cover), width ≥500px
- Source text summary: 치료하지 않으면 간이 서서히 굳고 일부는 간암으로 진행
- Visual intent: Comparison — 정상→염증→섬유화→간경변→간암 진행을 한눈에
- Unique subject: four equal liver cross-section panels (healthy→inflamed→fibrotic→cirrhotic with small tumor), centers x=12.5/37.5/62.5/87.5%
- Palette note: §20 anatomical color rule — liver tissue and blood/vessels realistic warm red/red-brown; navy #003366 + steel blue #5B9BD5 reserved for background, outlines, equipment, and virus-particle accents only
- Negative constraints: no embedded text/labels/numbers, no logos, no patient-identifying details; fills canvas edge-to-edge
