# antithrombotic — AF cardioembolism (LAA clot → brain) raster visual

- Asset: `antithrombotic-af-cardioembolism-20260621.png`
- Source generated image: `~/.codex/generated_images/019eea66-52aa-7e41-88c8-718f979804c9/ig_0d9996cb5649c6f7016a37e923088c819188948e4fe6c934b5.png`
- Tool: built-in image_gen (Codex), invoked via `codex exec`
- Deck/slide: `decks/cardio/antithrombotic-therapy/overview` — slide 15 (심방세동은 항응고제)
- Slot: `.ai-visual ai-visual--focus ai-visual--fill` (visual-focus right column)
- Slot size: 505 x 284 px (measured)
- Strict ratio: 16:9 (1.78:1)
- Source text summary: 심방세동에서 심장(좌심방이) 안에 생긴 혈전이 떨어져 나가 뇌혈관을 막아 뇌졸중을 일으킨다
- Visual intent: Mechanism — 좌심방이 혈전 → 색전 이동 → 뇌동맥 폐색을 한 장으로 보여 "아스피린이 아니라 항응고제" 메시지 강화
- Unique subject: heart cross-section with a clot in the left atrial appendage, an embolus travelling along a vessel up to a brain where it lodges in a cerebral artery
- Processing: source 1672x941 (≈16:9) → center-cropped to 16:9, resized 1600x900 px (LANCZOS)
- Palette note: navy #003366 + steel #5B9BD5 heart/vessels/brain; muted clinical red ONLY for clot / travelling embolus
- Negative constraints: no embedded text/labels/numbers, no logos, no patient-identifying details, direction implied by vessel + embolus position (no written arrows), fills canvas edge-to-edge
