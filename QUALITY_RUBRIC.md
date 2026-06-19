# Quality Rubric — "Top-10 feel" while staying bit/pixel-art

Each category scored 1–10. Target: every category ≥ 8 before the loop stops.
Graphics improvements must STAY within a pixel-art / retro aesthetic
(low internal resolution upscaled with nearest-neighbor, limited palette, no smooth gradients/AA that break the bit look).

| # | Category            | What "8+" looks like |
|---|---------------------|----------------------|
| 1 | Visual fidelity     | Crisp pixel sprites, cohesive limited palette, readable silhouettes, intentional internal-resolution upscaling |
| 2 | Game feel / juice   | Screen shake, hit-stop, knockback, particles, muzzle flashes — tuned, not noisy |
| 3 | Feedback & clarity  | Player always knows what hit them, what they hit, HP/score/state legible at a glance |
| 4 | Lighting & FX       | Glow/bloom faked in palette, parallax depth, layered backgrounds — without breaking pixel style |
| 5 | UI / menus / HUD    | Pixel-consistent font, clean layout, transitions, pause/game-over polish |
| 6 | Audio cohesion      | SFX mapped to every key event, balanced mix, music that fits the action |
| 7 | Difficulty / pacing | Ramp that escalates fairly, readable telegraphs, no dead air or unfair spikes |
| 8 | Performance         | Stable frame rate with all FX on; no stutter from particle/spawn spikes |

## Hard constraints
- Do NOT abandon pixel-art style for "HD" smooth graphics. Higher *internal* resolution + nearest-neighbor scaling is OK; anti-aliased vector art is NOT.
- Every pass must keep the game runnable (`python3 space_shooter.py` launches without error).
- No regressions: a category that was ≥8 must not drop below 8.
