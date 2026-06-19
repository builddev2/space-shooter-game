# Loop Progress

Total passes planned: 5
Passes completed: 2

## Latest scores (1–10, target ≥8 each)
| Category | Score | Notes |
|----------|-------|-------|
| 1 Visual fidelity     | 8 | Pass 2: added continuous engine exhaust trail (warm pixel plume behind ship) — frame now reads dynamic, not static. Cohesive palette, dithered nebula |
| 2 Game feel / juice    | 8 | Pass 2: thrust trail adds motion juice on top of existing hitstop/shake/muzzle/particles/graze. Verified plume + explosion burst in stills |
| 3 Feedback & clarity   | 8 | Score/Lives/Shield/combo all legible; clear hit feedback |
| 4 Lighting & FX        | 8 | FIXED: nebulae rebuilt as Bayer-dithered alpha-tiered pixel clouds (5x clean upscale) — now reads as deliberate pixel-art. Bolt glow good |
| 5 UI / menus / HUD     | 8 | FIXED: confusing red "GAME OVER" mid-game label renamed to "CORE 0 LY" danger marker. Top bar still slightly busy but no longer alarming/ambiguous |
| 6 Audio cohesion       | 7* | *provisional. Code shows SFX mapped to shoot/hit/explosion/powerup + procedural music, but mix/balance CANNOT be verified headless (dummy audio driver). Needs a real audio-on playtest by the user |
| 7 Difficulty / pacing  | 7* | *provisional. Code has stages, wave_timer lulls, scaling spawn delays, boss warnings — structurally sound, but actual feel CANNOT be verified without a real playthrough |
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

### Pass 2 (2026-06-19) — engine exhaust trail (juice)
- Added a continuous engine exhaust trail: emits 2 downward pixel particles/frame from the ship's tail in the active-weapon flame color, fading bright→dark over ~9-15 frames (reuses existing particle system + gravity). Verified plume visible in loop_shots.
- Scores: #1 Visual fidelity 7→8, #2 Game feel 7→8. Visual rubric categories (#1-#5, #8) now all ≥8.
- HONEST LIMIT: #6 Audio and #7 Difficulty/pacing are 7* provisional — they cannot be self-certified headless. The loop should NOT declare "all ≥8 / done" on my assessment alone; these two need a real audio-on playtest by the user. Loop continues.
- Next pass targets: a remaining visual-polish item (e.g. parallax depth in star/nebula layers or bolt impact sparks), since #6/#7 are gated on human verification, not code.
