# Loop Progress

Total passes planned: 5
Passes completed: 1

## Latest scores (1–10, target ≥8 each)
| Category | Score | Notes |
|----------|-------|-------|
| 1 Visual fidelity     | 7 | Solid pixel ships/enemies/bolts; cohesive palette. Drag: background nebulae are soft smooth blobs that break the pixel look |
| 2 Game feel / juice    | 7 | Graze popups, combo text, muzzle/particles present; can't fully judge motion from stills |
| 3 Feedback & clarity   | 8 | Score/Lives/Shield/combo all legible; clear hit feedback |
| 4 Lighting & FX        | 8 | FIXED: nebulae rebuilt as Bayer-dithered alpha-tiered pixel clouds (5x clean upscale) — now reads as deliberate pixel-art. Bolt glow good |
| 5 UI / menus / HUD     | 8 | FIXED: confusing red "GAME OVER" mid-game label renamed to "CORE 0 LY" danger marker. Top bar still slightly busy but no longer alarming/ambiguous |
| 6 Audio cohesion       | n/a | Not assessable from screenshots; score from code/runtime next pass |
| 7 Difficulty / pacing  | n/a | Not assessable from stills; needs a timed run |
| 8 Performance          | 8 | Headless run stable, exited clean |

## Pass log
### Pass 1 (2026-06-19) — VIABILITY TEST + baseline assessment
- Added SHOT_MODE instrumentation (headless capture of composed 800x600 frames at frames 90/180/300/450/620); guarded save_stats/save_high_score so automated runs don't pollute stats.txt.
- Confirmed the loop's core cycle works: instrument → run headless → capture → read/score frames.
- Did NOT yet make gameplay-improvement edits — this run was the test.
- Lowest categories to target next: #4 Lighting/FX (pixel-quantize nebulae), #5 UI/HUD (declutter top bar + fix the red label overlap), then assess #6/#7 with a timed run.

### Pass 1 (cont.) — improvements applied + verified
- make_nebula: replaced 16 soft translucent circles → low-res density field + 4x4 Bayer ordered dither into 4 alpha tiers, clean 5x nearest-neighbour upscale. Result verified in loop_shots: crisp stippled pixel cloud, no smooth gradient.
- draw_galaxy_progress: "GAME OVER" end-label → "CORE 0 LY" (clear danger/zero-distance marker; no longer reads as the game having ended).
- Verified: game launches clean headless, all 5 frames captured, ~2s load.
- New scores: #4 6→8, #5 6→8. Remaining below target/unknown: #6 Audio, #7 Difficulty/pacing (need timed-run assessment); #1 Visual fidelity (7) and #2 Game feel (7) are close.
- Next pass targets: #1/#2 (more juice — hit-stop tuning, impact particles), and assess #6/#7.
