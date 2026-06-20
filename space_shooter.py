import os
import pygame
import random
import math
from array import array
from datetime import datetime
from pathlib import Path

# Automated screenshot mode for the quality-rubric loop. Off during normal play.
# Run with: SHOT_MODE=1 SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 space_shooter.py
SHOT_MODE = os.environ.get("SHOT_MODE") == "1"
SHOT_FRAME = 0
SHOT_CAPTURE_FRAMES = (90, 180, 300, 450, 620)

SAMPLE_RATE = 22050
LIGHT_YEAR_KILOMETERS = 9461000000000
CRASH_DISTANCE_KILOMETERS = 0.0001


def make_music_loop(notes, volume):
    samples = array("h")
    for frequency, duration in notes:
        sample_count = int(SAMPLE_RATE * duration)
        for i in range(sample_count):
            if frequency <= 0:
                sample = 0
            else:
                fade = min(1, i / 240, (sample_count - i) / 240)
                wave = math.sin(2 * math.pi * frequency * i / SAMPLE_RATE)
                wave += 0.35 * math.sin(2 * math.pi * frequency * 2 * i / SAMPLE_RATE)
                sample = int(12500 * volume * wave * fade)
            samples.append(sample)
    return pygame.mixer.Sound(buffer=samples.tobytes())


# --- EDM / synthwave music engine ------------------------------------------
# The background tracks below are built as layered electronic loops: a
# four-on-the-floor kick, a driving sub-bass, and an arpeggiated synth lead.
# Each layer is rendered into a float mix buffer, summed, soft-clipped, then
# converted to int16. Inspired by the club-EDM / dark-synthwave space-shooter
# canon (WipEout, Hotline Miami, Rez). Pure math + array only (no numpy).
TWO_PI = 2 * math.pi


def _osc(phase, wave):
    # phase is in turns (0..1); returns a sample in [-1, 1].
    t = phase - math.floor(phase)
    if wave == "sine":
        return math.sin(TWO_PI * t)
    if wave == "saw":
        return 2.0 * t - 1.0
    if wave == "square":
        return 1.0 if t < 0.5 else -1.0
    if wave == "tri":
        return 4.0 * abs(t - 0.5) - 1.0
    return math.sin(TWO_PI * t)


def _add_voice(mix, start, freq, dur, wave, vol, attack=0.004, release=0.05, detune=0.0):
    # Mix one note into the float buffer with a click-free AR envelope.
    if freq <= 0 or vol <= 0:
        return
    count = int(SAMPLE_RATE * dur)
    atk = max(1, int(SAMPLE_RATE * attack))
    rel = max(1, int(SAMPLE_RATE * release))
    inc = freq / SAMPLE_RATE
    inc2 = (freq * (1.0 + detune)) / SAMPLE_RATE if detune else 0.0
    n = len(mix)
    for i in range(count):
        idx = start + i
        if idx >= n:
            break
        env = min(1.0, i / atk, (count - i) / rel)
        s = _osc(i * inc, wave)
        if detune:
            s = 0.6 * s + 0.4 * _osc(i * inc2, wave)
        mix[idx] += vol * env * s


def _add_kick(mix, start, vol=0.95):
    # Punchy four-on-the-floor kick: pitch drops ~150 -> 48 Hz with fast decay.
    dur = 0.18
    count = int(SAMPLE_RATE * dur)
    n = len(mix)
    phase = 0.0
    for i in range(count):
        idx = start + i
        if idx >= n:
            break
        frac = i / count
        freq = 48.0 + (150.0 - 48.0) * math.exp(-9.0 * frac)
        phase += freq / SAMPLE_RATE
        amp = math.exp(-7.0 * frac)
        mix[idx] += vol * amp * math.sin(TWO_PI * phase)


def _add_hat(mix, start, vol=0.18):
    # Short noisy-ish closed hat (square at high freq + quick decay) for groove.
    dur = 0.04
    count = int(SAMPLE_RATE * dur)
    n = len(mix)
    seed = (start * 1103515245 + 12345) & 0x7FFFFFFF
    for i in range(count):
        idx = start + i
        if idx >= n:
            break
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        noise = (seed / 0x3FFFFFFF) - 1.0
        amp = math.exp(-55.0 * (i / count))
        mix[idx] += vol * amp * noise


def build_track(bpm, bars, bass_steps, arp_steps, lead_wave="saw",
                bass_wave="square", volume=1.0, drums=True, hats=False,
                lead_vol=0.5, bass_vol=0.6):
    # 16 steps per bar (16th notes). bass_steps / arp_steps are frequency lists
    # (0 = rest); they tile to fill every bar. Returns a looping mixer Sound.
    steps_per_bar = 16
    total_steps = bars * steps_per_bar
    step_dur = 60.0 / bpm / 4.0  # one 16th note
    total_samples = int(SAMPLE_RATE * step_dur * total_steps) + 1
    mix = [0.0] * total_samples

    for step in range(total_steps):
        start = int(step * step_dur * SAMPLE_RATE)
        # Bass: sustain across the step for a driving sub feel.
        bf = bass_steps[step % len(bass_steps)] if bass_steps else 0
        if bf > 0:
            _add_voice(mix, start, bf, step_dur * 1.05, bass_wave, bass_vol,
                       attack=0.003, release=0.03, detune=0.004)
        # Arp / lead: shorter, brighter, plucky.
        af = arp_steps[step % len(arp_steps)] if arp_steps else 0
        if af > 0:
            _add_voice(mix, start, af, step_dur * 0.9, lead_wave, lead_vol,
                       attack=0.002, release=0.04, detune=0.01)
        # Drums.
        if drums and step % 4 == 0:
            _add_kick(mix, start)
        if hats and step % 4 == 2:
            _add_hat(mix, start)

    # Soft-clip and convert to int16.
    samples = array("h")
    for v in mix:
        v *= volume
        # tanh-ish soft clip to keep summed layers from harsh clipping.
        if v > 1.0 or v < -1.0:
            v = math.tanh(v)
        s = int(13500 * v)
        if s > 32767:
            s = 32767
        elif s < -32768:
            s = -32768
        samples.append(s)
    return pygame.mixer.Sound(buffer=samples.tobytes())


pygame.init()
BASE_DIR = Path(__file__).resolve().parent
HIGH_SCORE_FILE = BASE_DIR / "highscore.txt"
HIGH_SCORE_TIME_FILE = BASE_DIR / "highscore_time.txt"
STATS_FILE = BASE_DIR / "stats.txt"
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
pygame.mixer.set_reserved(1)
# Master volume scales every sound's effective output. Reduced 40% from full.
MASTER_VOLUME = 0.6
weapon_sounds = {
    "single": pygame.mixer.Sound(str(BASE_DIR / "laser.wav")),
    "double": pygame.mixer.Sound(str(BASE_DIR / "laser_double.wav")),
    "spread": pygame.mixer.Sound(str(BASE_DIR / "laser_spread.wav")),
    "rapid": pygame.mixer.Sound(str(BASE_DIR / "laser_rapid.wav")),
    "heavy": pygame.mixer.Sound(str(BASE_DIR / "laser_heavy.wav")),
}
for sound in weapon_sounds.values():
    sound.set_volume(0.4 * MASTER_VOLUME)
enemy_hit_sound = pygame.mixer.Sound(str(BASE_DIR / "enemy_hit.wav"))
powerup_collect_sound = pygame.mixer.Sound(str(BASE_DIR / "powerup_collect.wav"))
player_hit_sound = pygame.mixer.Sound(str(BASE_DIR / "player_hit.wav"))
enemy_hit_sound.set_volume(0.35 * MASTER_VOLUME)
powerup_collect_sound.set_volume(0.45 * MASTER_VOLUME)
player_hit_sound.set_volume(0.45 * MASTER_VOLUME)
graze_sound = make_music_loop([(1320, 0.03)], 0.4)
milestone_sound = make_music_loop([(523, 0.05), (659, 0.05), (784, 0.10)], 0.5)
warning_sound = make_music_loop([(196, 0.16), (0, 0.05), (196, 0.16)], 0.6)
new_record_sound = make_music_loop([(440, 0.07), (554, 0.07), (659, 0.07), (880, 0.16)], 0.55)
for cue_sound in (graze_sound, milestone_sound, warning_sound, new_record_sound):
    cue_sound.set_volume(MASTER_VOLUME)
music_channel = pygame.mixer.Channel(0)
music_channel.set_volume(0.32 * MASTER_VOLUME)
current_music_name = ""
# Note frequencies (Hz) used to spell the loop patterns below. _ is a rest.
_ = 0
A1, C2, D2, E2, F2, G2, A2, B2 = 55, 65, 73, 82, 87, 98, 110, 123
Bb2 = 117
C3, D3, E3, F3, G3, A3, Bb3, B3 = 131, 147, 165, 175, 196, 220, 233, 247
C4, D4, E4, F4, G4, A4, B4 = 262, 294, 330, 349, 392, 440, 494
C5, D5, E5, G5, A5 = 523, 587, 659, 784, 880

# Five distinct stage tracks, escalating in tempo and intensity. Each one's
# vibe: 1) bright house, 2) faster uplifting, 3) darker syncopated, 4) gritty
# driving synthwave, 5) relentless dark synth.
stage_music = [
    # Stage 1 - A minor, bright mid-tempo house. Inviting groove.
    build_track(
        bpm=112, bars=2,
        bass_steps=[A2, _, A2, _, A2, _, _, A2, F2, _, F2, _, G2, _, _, G2],
        arp_steps=[A4, C5, E5, C5, A4, C5, E5, C5, F4, A4, C5, A4, G4, B4, D5, B4],
        lead_wave="tri", bass_wave="square", lead_vol=0.42, bass_vol=0.55,
        hats=True, volume=0.95),
    # Stage 2 - C major, faster, brighter 16th arp.
    build_track(
        bpm=120, bars=2,
        bass_steps=[C2, _, C2, C2, _, C2, _, C2, G2, _, G2, _, A2, _, A2, _],
        arp_steps=[C5, E5, G5, E5, C5, E5, G5, A5, G5, E5, C5, E5, G4, B4, D5, B4],
        lead_wave="saw", bass_wave="square", lead_vol=0.40, bass_vol=0.55,
        hats=True, volume=0.95),
    # Stage 3 - D minor, darker, syncopated bass.
    build_track(
        bpm=126, bars=2,
        bass_steps=[D2, _, _, D2, D2, _, A1, _, F2, _, _, F2, E2, _, E2, _],
        arp_steps=[D5, A4, F4, A4, D5, F4, A4, C5, D5, A4, F4, D4, E4, G4, B3, A4],
        lead_wave="saw", bass_wave="saw", lead_vol=0.42, bass_vol=0.60,
        hats=True, volume=0.98),
    # Stage 4 - E minor, gritty driving synthwave.
    build_track(
        bpm=132, bars=2,
        bass_steps=[E2, E2, _, E2, E2, _, E2, _, C2, C2, _, C2, D2, D2, _, D2],
        arp_steps=[E5, B4, G4, B4, E5, G4, B4, E5, D5, A4, F4, A4, D5, F4, A4, D5],
        lead_wave="saw", bass_wave="saw", lead_vol=0.44, bass_vol=0.62,
        hats=True, volume=1.0),
    # Stage 5 - A minor (low), relentless dark synth. Dense and fast.
    build_track(
        bpm=138, bars=2,
        bass_steps=[A1, A1, A1, _, A1, A1, _, A1, F2, F2, _, F2, G2, G2, _, G2],
        arp_steps=[A4, E5, A5, E5, C5, G5, C5, E5, F4, C5, A4, C5, G4, D5, B4, D5],
        lead_wave="saw", bass_wave="saw", lead_vol=0.46, bass_vol=0.66,
        hats=True, volume=1.02),
]

# One shared boss theme used by every boss battle: fast, aggressive,
# four-on-the-floor dark-minor banger with a distorted square bass.
boss_music = build_track(
    bpm=150, bars=2,
    bass_steps=[D2, D2, D2, D2, D2, D2, D2, D2, Bb2, Bb2, Bb2, Bb2, A1, A1, A1, A1],
    arp_steps=[D5, _, F4, _, A4, _, D5, F4, A4, _, F4, _, D5, A4, F4, E5],
    lead_wave="saw", bass_wave="square", lead_vol=0.48, bass_vol=0.72,
    hats=True, volume=1.05)

# RES is the master render-resolution multiplier. The game is authored against a
# notional 800x600 design space; the actual logical canvas is RES times that, so
# the canvas upscales less to fill the window (crisper) and there is more room for
# the playfield. World-space pixel values below are written as <base> * RES so the
# relationship stays visible and RES = 1 restores the original look exactly.
RES = 2
SCREEN_WIDTH = 800 * RES
SCREEN_HEIGHT = 600 * RES
TARGET_FPS = 60
# NOTE: DOUBLEBUF is intentionally NOT set. This is a plain software window that
# present() fully repaints every frame (window.blit of the scaled canvas), so we
# don't need a back buffer. On macOS a double-buffered *software* window can stop
# presenting after display.flip(): the visible buffer freezes on a stale/partial
# frame while the Python loop keeps running and processing input (so movement and
# audio still work but the picture is stuck). Single-buffered avoids that stall.
WINDOW_FLAGS = pygame.RESIZABLE


def compute_initial_window_size():
    """Pick a launch window size that fills most of the desktop, keeping 4:3."""
    try:
        desktop_w, desktop_h = pygame.display.get_desktop_sizes()[0]
    except (AttributeError, IndexError, pygame.error):
        info = pygame.display.Info()
        desktop_w, desktop_h = info.current_w, info.current_h
    scale = min(desktop_w * 0.85 / SCREEN_WIDTH, desktop_h * 0.85 / SCREEN_HEIGHT)
    # The logical canvas is high-res (RES x), so downscaling it to fit the desktop
    # looks fine; only guard against an absurdly tiny launch window.
    scale = max(scale, 0.4)
    return int(SCREEN_WIDTH * scale), int(SCREEN_HEIGHT * scale)


def open_window(size):
    # NOTE: vsync is intentionally NOT requested. With the high-res canvas the
    # per-frame rescale is heavier, and on macOS a vsync-locked resizable window
    # can stall: the SDL/window-server stops refreshing the surface (frozen image)
    # even though the Python game loop keeps running and processing input. Frame
    # pacing is handled by clock.tick(TARGET_FPS) instead, so vsync isn't needed.
    return pygame.display.set_mode(size, WINDOW_FLAGS)


window = open_window(compute_initial_window_size())
pygame.display.set_caption("Space Shooter")
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.VIDEORESIZE])

# The game is always drawn to this fixed 800x600 logical canvas, then scaled up
# to fill the (resizable) window each frame in present().
screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

# Mapping from window pixels back to logical canvas coordinates, updated by present().
_view_scale = 1.0
_view_offset = (0, 0)


def present():
    """Scale the logical canvas into the window with aspect-correct letterboxing."""
    global _view_scale, _view_offset
    win_w, win_h = window.get_size()
    scale = min(win_w / SCREEN_WIDTH, win_h / SCREEN_HEIGHT)
    scaled_w = max(1, int(SCREEN_WIDTH * scale))
    scaled_h = max(1, int(SCREEN_HEIGHT * scale))
    offset_x = (win_w - scaled_w) // 2
    offset_y = (win_h - scaled_h) // 2
    _view_scale = scale
    _view_offset = (offset_x, offset_y)
    if offset_x or offset_y:
        window.fill((0, 0, 0))
    window.blit(pygame.transform.scale(screen, (scaled_w, scaled_h)), (offset_x, offset_y))
    pygame.display.flip()


def to_logical(pos):
    """Map a window-pixel position to logical 800x600 canvas coordinates."""
    return ((pos[0] - _view_offset[0]) / _view_scale, (pos[1] - _view_offset[1]) / _view_scale)


def logical_mouse_pos():
    return to_logical(pygame.mouse.get_pos())


def handle_window_resize(new_size):
    global window
    window = open_window((max(SCREEN_WIDTH // 2, new_size[0]), max(SCREEN_HEIGHT // 2, new_size[1])))
clock = pygame.time.Clock()
running = True


def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            return int(f.read())
    except (OSError, ValueError):
        return 0


def load_high_score_time():
    try:
        with open(HIGH_SCORE_TIME_FILE, "r") as f:
            return f.read()
    except OSError:
        return "Not saved yet"


def save_high_score(value, score_time):
    if SHOT_MODE:
        return
    with open(HIGH_SCORE_FILE, "w") as f:
        f.write(str(value))
    with open(HIGH_SCORE_TIME_FILE, "w") as f:
        f.write(score_time)


def load_stats():
    stats = {"best_combo": 0, "total_kills": 0, "total_runs": 0, "total_boss_kills": 0}
    try:
        with open(STATS_FILE, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    if key in stats:
                        stats[key] = int(value)
    except (OSError, ValueError):
        pass
    return stats


def save_stats():
    if SHOT_MODE:
        return
    with open(STATS_FILE, "w") as f:
        for key, value in lifetime_stats.items():
            f.write(key + "=" + str(value) + "\n")


def reset_run():
    global player_x, player_y, player_velocity_x, player_velocity_y
    global galaxy_distance, radial_speed_ly_per_second, orbit_speed_degrees_per_second, orbit_angle, black_hole_crash
    global lasers, fire_timer, powerups, powerup_timer, active_weapon, weapon_timer
    global special_move_weapon, special_move_timer, enemies, spawn_timer, enemy_bullets
    global particles, explosions, score_popups, shockwaves, screen_shake_timer, screen_shake_strength, player_hit_timer
    global score, lives, current_stage, stage_score, boss, mission_complete
    global gun_upgrade_level, shield_upgrade_level, engine_upgrade_level, shield_current, upgrade_screen, paused
    global combo_count, combo_timer, score_multiplier, best_combo_this_run, milestone_flash_timer
    global graze_count_this_run, graze_pulse_timer, graze_popup_cooldown
    global wave_timer, boss_warning_timer, hitstop_timer, muzzle_flash_timer, high_score_beaten
    global current_music_name, running

    player_x = 400
    player_y = 520
    player_velocity_x = 0
    player_velocity_y = 0
    galaxy_distance = 26000.0
    radial_speed_ly_per_second = -120.0
    orbit_speed_degrees_per_second = 35.0
    orbit_angle = -math.pi / 2
    black_hole_crash = False
    lasers = []
    fire_timer = 0
    powerups = []
    powerup_timer = 0
    active_weapon = "single"
    weapon_timer = 0
    special_move_weapon = ""
    special_move_timer = 0
    enemies = []
    spawn_timer = 0
    enemy_bullets = []
    particles = []
    explosions = []
    score_popups = []
    shockwaves = []
    screen_shake_timer = 0
    screen_shake_strength = 0
    player_hit_timer = 0
    score = 0
    lives = 20
    current_stage = 0
    stage_score = 0
    boss = None
    mission_complete = False
    gun_upgrade_level = 0
    shield_upgrade_level = 0
    engine_upgrade_level = 0
    shield_current = shield_max
    upgrade_screen = False
    paused = False
    combo_count = 0
    combo_timer = 0
    score_multiplier = 1
    best_combo_this_run = 0
    milestone_flash_timer = 0
    graze_count_this_run = 0
    graze_pulse_timer = 0
    graze_popup_cooldown = 0
    wave_timer = 0
    boss_warning_timer = 0
    hitstop_timer = 0
    muzzle_flash_timer = 0
    high_score_beaten = False
    running = True
    current_music_name = ""
    play_music("stage_0", stage_music[0])


def play_music(name, sound):
    global current_music_name

    if current_music_name == name:
        return

    current_music_name = name
    music_channel.stop()
    music_channel.play(sound, loops=-1)


def toggle_pause():
    global paused

    paused = not paused
    if paused:
        music_channel.pause()
    else:
        music_channel.unpause()


def mix_color(start_color, end_color, amount):
    amount = max(0, min(1, amount))
    return (
        int(start_color[0] + (end_color[0] - start_color[0]) * amount),
        int(start_color[1] + (end_color[1] - start_color[1]) * amount),
        int(start_color[2] + (end_color[2] - start_color[2]) * amount),
    )


def get_distance_color(distance):
    if distance <= 100:
        return (255, 255, 255)
    if distance <= 200:
        return mix_color((95, 0, 0), (255, 0, 0), (distance - 100) / 100)
    if distance <= 9300:
        return (255, 0, 0)
    if distance <= 18300:
        return mix_color((255, 0, 0), (255, 230, 0), (distance - 9300) / 9000)
    if distance <= 18600:
        return (255, 230, 0)
    if distance <= 28000:
        return mix_color((255, 230, 0), (0, 215, 80), (distance - 18600) / 9400)
    return (0, 90, 35)


def format_distance(distance):
    if distance < 1:
        kilometers = distance * LIGHT_YEAR_KILOMETERS
        meters = kilometers * 1000
        if kilometers >= 1000000000:
            return str(round(kilometers / 1000000000, 1)) + " billion km"
        if kilometers >= 1000000:
            return str(round(kilometers / 1000000, 1)) + " million km"
        if kilometers >= 1000:
            return str(round(kilometers / 1000, 1)) + " thousand km"
        if kilometers >= 100:
            return str(round(kilometers, 1)) + " km"
        if kilometers >= 10:
            return str(round(kilometers, 1)) + " km"
        if meters >= 100:
            return str(round(meters, 1)) + " m"
        if meters >= 10:
            return str(round(meters, 1)) + " m"
        return str(round(meters, 1)) + " m"
    return str(int(distance)) + " LY"


def get_close_center_speed_limit(distance):
    kilometers = distance * LIGHT_YEAR_KILOMETERS
    if kilometers >= 1000000000:
        return 800000000000 / LIGHT_YEAR_KILOMETERS
    if kilometers >= 1000000:
        return 80000000 / LIGHT_YEAR_KILOMETERS
    if kilometers >= 1000:
        return 80000 / LIGHT_YEAR_KILOMETERS
    if kilometers >= 100:
        return 80 / LIGHT_YEAR_KILOMETERS
    if kilometers >= 10:
        return 8 / LIGHT_YEAR_KILOMETERS
    if kilometers >= 0.1:
        return 0.8 / LIGHT_YEAR_KILOMETERS
    if kilometers >= 0.01:
        return 0.008 / LIGHT_YEAR_KILOMETERS
    return 0.0008 / LIGHT_YEAR_KILOMETERS


def format_radial_speed(speed, distance):
    if distance >= 1:
        return str(round(abs(speed), 1)) + " LY/S"

    kilometers_per_second = abs(speed) * LIGHT_YEAR_KILOMETERS
    if kilometers_per_second >= 1:
        return str(round(kilometers_per_second, 1)) + " KM/S"
    return str(round(kilometers_per_second * 1000, 1)) + " M/S"


def draw_galaxy_progress(distance, radial_speed, orbit_speed, orbit_angle):
    progress_rect = pygame.Rect(465 * RES, 12 * RES, 300 * RES, 22 * RES)
    distance_remaining = max(0, min(1, distance / max_galaxy_distance))
    progress_color = get_distance_color(distance)
    draw_pixel_panel(screen, progress_rect, (95, 105, 125), fill=(12, 16, 26))
    pygame.draw.rect(
        screen,
        progress_color,
        (progress_rect.x + 3 * RES, progress_rect.y + 3 * RES, int((progress_rect.width - 6 * RES) * distance_remaining), progress_rect.height - 6 * RES),
    )

    end_label = small_font.render("CORE 0 LY", True, (255, 120, 120))
    far_label = small_font.render("50,000 LY", True, (145, 165, 205))
    screen.blit(end_label, (progress_rect.x, progress_rect.y - 16 * RES))
    screen.blit(far_label, far_label.get_rect(topright=(progress_rect.right, progress_rect.y - 16 * RES)))

    distance_text = small_font.render("TO CENTER: " + format_distance(distance), True, (235, 240, 255))
    screen.blit(distance_text, (progress_rect.x, progress_rect.y + 28 * RES))

    map_rect = pygame.Rect(620 * RES, 95 * RES, 160 * RES, 185 * RES)
    draw_pixel_panel(screen, map_rect, (75, 90, 120), fill=(8, 11, 22))
    map_center = (map_rect.centerx, map_rect.y + 92 * RES)
    map_radius = 58 * RES

    for radius in [18 * RES, 36 * RES, 54 * RES]:
        pygame.draw.circle(screen, (28, 35, 55), map_center, radius, RES)

    pygame.draw.circle(screen, (245, 225, 130), (map_center[0], map_center[1] - map_radius), 5 * RES)
    sun_text = small_font.render("SUN N", True, (245, 225, 130))
    screen.blit(sun_text, (map_center[0] - 22 * RES, map_center[1] - map_radius - 20 * RES))
    reference_time_text = small_font.render("2026-05-15 16:30", True, (145, 165, 205))
    screen.blit(reference_time_text, (map_rect.x + 9 * RES, map_rect.bottom - 22 * RES))

    pygame.draw.circle(screen, (255, 255, 255), map_center, 8 * RES)
    pygame.draw.circle(screen, (0, 0, 0), map_center, 5 * RES)

    ship_radius = max(10 * RES, int(map_radius * max(0, min(1, distance / 28000))))
    ship_x = map_center[0] + math.cos(orbit_angle) * ship_radius
    ship_y = map_center[1] + math.sin(orbit_angle) * ship_radius
    pygame.draw.line(screen, (70, 95, 125), map_center, (ship_x, ship_y), RES)
    screen.fill(progress_color, (int(ship_x) - 2 * RES, int(ship_y) - 2 * RES, 5 * RES, 5 * RES))

    if radial_speed < -1:
        direction = "CLOSER"
    elif radial_speed > 1:
        direction = "FARTHER"
    else:
        direction = "ORBIT"

    speed_lines = [
        "SPEED " + format_radial_speed(radial_speed, distance),
        "DIR " + direction,
        "ORBIT " + str(int(orbit_speed)) + " DEG/S",
    ]
    for i, line in enumerate(speed_lines):
        line_text = small_font.render(line, True, (220, 235, 255))
        line_rect = line_text.get_rect(right=SCREEN_WIDTH - 16 * RES, bottom=SCREEN_HEIGHT - 58 * RES + i * 20 * RES)
        screen.blit(line_text, line_rect)


def draw_pause_play_button(paused):
    button_text = "PLAY" if paused else "PAUSE"
    mouse_pos = logical_mouse_pos()
    accent = (120, 190, 255)
    button_color = (55, 145, 220) if pause_button.collidepoint(mouse_pos) else (28, 78, 135)
    if paused:
        accent = (130, 235, 170)
        button_color = (55, 175, 110) if pause_button.collidepoint(mouse_pos) else (35, 115, 75)

    draw_pixel_panel(screen, pause_button, accent, fill=button_color)
    label = small_font.render(button_text, True, (255, 255, 255))
    screen.blit(label, label.get_rect(center=pause_button.center))


def get_gun_multiplier():
    return 1.2 ** gun_upgrade_level


def get_engine_multiplier():
    return 1.15 ** engine_upgrade_level


def get_laser_damage(laser):
    base_damage = 9 if laser[4] == "heavy" else 5
    return base_damage * get_gun_multiplier()


def apply_upgrade(upgrade_name):
    global gun_upgrade_level, shield_upgrade_level, engine_upgrade_level, lives, upgrade_screen

    if upgrade_name == "guns":
        gun_upgrade_level = gun_upgrade_level + 1
    elif upgrade_name == "shields":
        shield_upgrade_level = shield_upgrade_level + 1
        lives = lives + 20
    elif upgrade_name == "engine":
        engine_upgrade_level = engine_upgrade_level + 1

    upgrade_screen = False
    play_music("stage_" + str(current_stage), stage_music[current_stage])


def draw_upgrade_screen():
    screen.blit(stage_backgrounds[min(current_stage, len(stage_backgrounds) - 1)], (0, 0))
    draw_star_layers()

    draw_text_shadowed(medium_32_pixel_font, "CHOOSE SHIP UPGRADE", (235, 245, 255), center=(SCREEN_WIDTH // 2, 48 * RES))

    ship_rect = player_preview_sprite.get_rect(center=(SCREEN_WIDTH // 2, 190 * RES))
    blit_glow(ship_rect.centerx, ship_rect.centery, (60, 220, 255), 180)
    screen.blit(player_preview_sprite, ship_rect)

    bracket_rect = ship_rect.inflate(44 * RES, 44 * RES)
    bracket_color = (60, 220, 255)
    arm = 21 * RES
    thickness = 3 * RES
    pygame.draw.rect(screen, bracket_color, (bracket_rect.left, bracket_rect.top, arm, thickness))
    pygame.draw.rect(screen, bracket_color, (bracket_rect.left, bracket_rect.top, thickness, arm))
    pygame.draw.rect(screen, bracket_color, (bracket_rect.right - arm, bracket_rect.top, arm, thickness))
    pygame.draw.rect(screen, bracket_color, (bracket_rect.right - thickness, bracket_rect.top, thickness, arm))
    pygame.draw.rect(screen, bracket_color, (bracket_rect.left, bracket_rect.bottom - thickness, arm, thickness))
    pygame.draw.rect(screen, bracket_color, (bracket_rect.left, bracket_rect.bottom - arm, thickness, arm))
    pygame.draw.rect(screen, bracket_color, (bracket_rect.right - arm, bracket_rect.bottom - thickness, arm, thickness))
    pygame.draw.rect(screen, bracket_color, (bracket_rect.right - thickness, bracket_rect.bottom - arm, thickness, arm))

    upgrade_cards = [
        ("guns", "GUNS", "+20% damage", "Level " + str(gun_upgrade_level)),
        ("shields", "SHIELDS", "+20 lives", "Level " + str(shield_upgrade_level)),
        ("engine", "ENGINE", "+15% move speed", "Level " + str(engine_upgrade_level)),
    ]
    mouse_pos = logical_mouse_pos()
    for i, card in enumerate(upgrade_cards):
        upgrade_name, title_text, bonus_text, level_text = card
        rect = upgrade_buttons[upgrade_name]
        hover = rect.collidepoint(mouse_pos)
        card_color = (28, 66, 105) if hover else (14, 28, 54)
        accent = (255, 210, 70)
        if upgrade_name == "shields":
            accent = (70, 220, 255)
        elif upgrade_name == "engine":
            accent = (100, 255, 135)

        draw_pixel_panel(screen, rect, accent, fill=card_color)
        draw_text_shadowed(font, title_text, accent, center=(rect.centerx, rect.y + 34 * RES))
        draw_text_shadowed(small_font, bonus_text, (235, 245, 255), center=(rect.centerx, rect.y + 70 * RES))
        draw_text_shadowed(small_font, level_text, (175, 195, 225), center=(rect.centerx, rect.y + 98 * RES))
        draw_text_shadowed(small_font, "Press " + str(i + 1), (255, 255, 255), center=(rect.centerx, rect.bottom - 24 * RES))


OUTLINE_COLOR = (16, 14, 28)
TEXT_SHADOW_COLOR = (16, 14, 28)
HUD_FILL = (10, 14, 26)
HUD_BORDER = (90, 110, 150)
CRT_OVERLAY = True


def add_outline_rows(rows):
    width = max(len(row) for row in rows)
    padded = ["." * (width + 2)]
    for row in rows:
        padded.append("." + row.ljust(width, ".") + ".")
    padded.append("." * (width + 2))

    outlined = []
    for y, row in enumerate(padded):
        new_row = ""
        for x, pixel in enumerate(row):
            if pixel == ".":
                neighbors = [
                    padded[y - 1][x] if y > 0 else ".",
                    padded[y + 1][x] if y < len(padded) - 1 else ".",
                    row[x - 1] if x > 0 else ".",
                    row[x + 1] if x < len(row) - 1 else ".",
                ]
                if any(neighbor not in (".", "0") for neighbor in neighbors):
                    new_row += "0"
                    continue
            new_row += pixel
        outlined.append(new_row)
    return outlined


def make_pixel_sprite(rows, colors, scale, outline=True):
    if outline:
        rows = add_outline_rows(rows)
        colors = dict(colors)
        colors["0"] = OUTLINE_COLOR

    width = max(len(row) for row in rows)
    height = len(rows)
    sprite = pygame.Surface((width, height), pygame.SRCALPHA)

    for y, row in enumerate(rows):
        for x, pixel in enumerate(row):
            if pixel != ".":
                sprite.set_at((x, y), colors[pixel])

    return pygame.transform.scale(sprite, (width * scale, height * scale)).convert_alpha()


def mirror_rows(half_rows):
    return [row + row[::-1] for row in half_rows]


def make_flash_sprite(sprite, flash_color=(255, 80, 80, 140)):
    flash = sprite.copy()
    flash.fill(flash_color, special_flags=pygame.BLEND_RGBA_ADD)
    return flash


def hitbox_rect(center_x, center_y, size):
    return pygame.Rect(int(center_x - size[0] / 2), int(center_y - size[1] / 2), size[0], size[1])


GLOW_CACHE = {}


def make_glow(color, radius):
    base_radius = max(2, radius // 3)
    size = base_radius * 2 + 2
    surf = pygame.Surface((size, size))
    center = size // 2
    for factor, brightness in [(1.0, 0.10), (0.72, 0.2), (0.45, 0.36), (0.22, 0.6)]:
        ring_color = (int(color[0] * brightness), int(color[1] * brightness), int(color[2] * brightness))
        pygame.draw.circle(surf, ring_color, (center, center), max(1, int(base_radius * factor)))
    return pygame.transform.scale(surf, (size * 3, size * 3))


def get_glow(color, radius):
    key = (color, radius)
    if key not in GLOW_CACHE:
        GLOW_CACHE[key] = make_glow(color, radius)
    return GLOW_CACHE[key]


def blit_glow(x, y, color, radius):
    glow = get_glow(color, radius)
    screen.blit(glow, glow.get_rect(center=(int(x), int(y))), special_flags=pygame.BLEND_RGB_ADD)


def make_explosion_frames(base_size, scale):
    rng = random.Random(base_size * 7919)
    center = (base_size - 1) / 2
    max_radius = base_size / 2
    fire_ramp = [(255, 255, 255), (255, 230, 130), (255, 150, 40), (190, 60, 25)]
    smoke_color = (70, 60, 75)
    dark_smoke = (45, 38, 52)
    frames = []
    for frame_index in range(7):
        surf = pygame.Surface((base_size, base_size), pygame.SRCALPHA)
        if frame_index <= 2:
            radius = max_radius * (0.35 + 0.28 * frame_index)
            for y in range(base_size):
                for x in range(base_size):
                    distance = math.hypot(x - center, y - center)
                    if distance <= radius - rng.random() * 0.9:
                        ramp_position = distance / max(1, radius)
                        if ramp_position < 0.35 - 0.1 * frame_index:
                            surf.set_at((x, y), fire_ramp[0])
                        elif ramp_position < 0.62:
                            surf.set_at((x, y), fire_ramp[1])
                        elif ramp_position < 0.85:
                            surf.set_at((x, y), fire_ramp[2])
                        else:
                            surf.set_at((x, y), fire_ramp[3])
        elif frame_index <= 4:
            radius = max_radius * (0.92 + 0.08 * (frame_index - 3))
            for y in range(base_size):
                for x in range(base_size):
                    distance = math.hypot(x - center, y - center)
                    if radius - 2.2 <= distance <= radius - rng.random():
                        surf.set_at((x, y), fire_ramp[2] if rng.random() < 0.6 else fire_ramp[3])
            for _ in range(base_size):
                angle = rng.uniform(0, math.tau)
                throw = rng.uniform(0.4, 1.0) * max_radius
                ejecta_x = int(center + math.cos(angle) * throw)
                ejecta_y = int(center + math.sin(angle) * throw)
                if 0 <= ejecta_x < base_size and 0 <= ejecta_y < base_size:
                    surf.set_at((ejecta_x, ejecta_y), fire_ramp[1] if rng.random() < 0.4 else fire_ramp[2])
        else:
            speck_count = base_size * (2 if frame_index == 5 else 1)
            for _ in range(speck_count):
                angle = rng.uniform(0, math.tau)
                throw = rng.uniform(0.3, 1.0) * max_radius
                speck_x = int(center + math.cos(angle) * throw)
                speck_y = int(center + math.sin(angle) * throw)
                if 0 <= speck_x < base_size and 0 <= speck_y < base_size:
                    surf.set_at((speck_x, speck_y), smoke_color if rng.random() < 0.7 else dark_smoke)
        frames.append(pygame.transform.scale(surf, (base_size * scale, base_size * scale)).convert_alpha())
    return frames


# 4x4 ordered-dither matrix for quantizing nebula clouds into pixels.
NEBULA_BAYER = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


def make_nebula(color, seed):
    # Build a low-res density field of soft blobs, then ordered-dither it into
    # discrete alpha tiers so it upscales (nearest-neighbour) to a crisp,
    # stippled pixel cloud instead of a smooth translucent gradient.
    rng = random.Random(seed)
    low_w, low_h = SCREEN_WIDTH // 5, SCREEN_HEIGHT // 5
    surf = pygame.Surface((low_w, low_h), pygame.SRCALPHA)
    blobs = []
    for _ in range(13):
        blobs.append((
            rng.uniform(-15, low_w + 15),
            rng.uniform(-15, low_h + 15),
            rng.uniform(18, 52),
            rng.uniform(0.22, 0.7),
        ))
    for y in range(low_h):
        for x in range(low_w):
            density = 0.0
            for blob_x, blob_y, blob_radius, strength in blobs:
                d = math.hypot(x - blob_x, y - blob_y)
                if d < blob_radius:
                    falloff = 1.0 - d / blob_radius
                    density += strength * falloff * falloff
            if density <= 0.02:
                continue
            threshold = (NEBULA_BAYER[y % 4][x % 4] + 0.5) / 16.0
            level = density - threshold * 0.5
            if level <= 0:
                continue
            tier = min(3, int(level * 4))
            alpha = (tier + 1) * 13
            surf.set_at((x, y), (color[0], color[1], color[2], alpha))
    return pygame.transform.scale(surf, (SCREEN_WIDTH, SCREEN_HEIGHT))


def make_planet(base_diameter, palette, seed, ring_color=None):
    rng = random.Random(seed)
    surf_width = base_diameter * 2 if ring_color else base_diameter
    surf = pygame.Surface((surf_width, base_diameter), pygame.SRCALPHA)
    center_x = surf_width / 2 - 0.5
    center_y = base_diameter / 2 - 0.5
    radius = base_diameter / 2 - 0.5
    band_seeds = [rng.random() * 10 for _ in range(base_diameter)]
    for y in range(base_diameter):
        band = palette[1] if int(y * 0.45 + band_seeds[y]) % 2 == 0 else palette[2]
        for x in range(surf_width):
            distance = math.hypot(x - center_x, y - center_y)
            if distance <= radius:
                color = band
                if (x - center_x) + (y - center_y) > radius * 0.55:
                    color = palette[0]
                surf.set_at((x, y), color)
    if ring_color:
        ring_y = base_diameter // 2
        for x in range(surf_width):
            distance = abs(x - center_x)
            if radius + 1 < distance < radius * 2:
                surf.set_at((x, ring_y), ring_color)
                if rng.random() < 0.5:
                    surf.set_at((x, ring_y + (1 if x % 2 else -1)), ring_color)
    return pygame.transform.scale(surf, (surf_width * 6, base_diameter * 6))


def make_scanline_overlay():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for y in range(0, SCREEN_HEIGHT, 3 * RES):
        pygame.draw.line(overlay, (0, 0, 0, 26), (0, y), (SCREEN_WIDTH, y))
    for inset, alpha in [(0, 30), (8 * RES, 18), (16 * RES, 9)]:
        pygame.draw.rect(overlay, (0, 0, 0, alpha), (inset, inset, SCREEN_WIDTH - inset * 2, SCREEN_HEIGHT - inset * 2), 8 * RES)
    return overlay


def draw_pixel_panel(surface, rect, accent, fill=HUD_FILL):
    pygame.draw.rect(surface, fill, rect)
    pygame.draw.rect(surface, accent, rect, 2 * RES)
    for corner_x in (rect.left, rect.right - 3 * RES):
        for corner_y in (rect.top, rect.bottom - 3 * RES):
            pygame.draw.rect(surface, accent, (corner_x, corner_y, 3 * RES, 3 * RES))


def draw_segment_bar(surface, x, y, width, height, fraction, color, segments=12):
    fraction = max(0, min(1, fraction))
    pygame.draw.rect(surface, HUD_FILL, (x - 2 * RES, y - 2 * RES, width + 4 * RES, height + 4 * RES))
    pygame.draw.rect(surface, HUD_BORDER, (x - 2 * RES, y - 2 * RES, width + 4 * RES, height + 4 * RES), RES)
    cell_width = (width - (segments - 1) * 2 * RES) / segments
    filled = fraction * segments
    dim_color = (color[0] // 3, color[1] // 3, color[2] // 3)
    for i in range(segments):
        if i + 1 <= filled:
            cell_color = color
        elif i < filled:
            cell_color = dim_color
        else:
            continue
        pygame.draw.rect(surface, cell_color, (int(x + i * (cell_width + 2 * RES)), y, max(1, int(cell_width)), height))


def draw_text_shadowed(font_object, text, color, **anchor):
    shadow = font_object.render(text, True, TEXT_SHADOW_COLOR)
    text_surface = font_object.render(text, True, color)
    rect = text_surface.get_rect(**anchor)
    screen.blit(shadow, (rect.x + 2 * RES, rect.y + 2 * RES))
    screen.blit(text_surface, rect)
    return rect


def draw_star_layers(offset_x=0, offset_y=0):
    tick = pygame.time.get_ticks()
    for layer in star_layers:
        layer_offset_x = int(offset_x * layer["depth"])
        layer_offset_y = int(offset_y * layer["depth"])
        size = layer["size"]
        base_color, twinkle_color = layer["colors"]
        for star in layer["stars"]:
            color = twinkle_color if (tick // 180 + star[2]) % 7 == 0 else base_color
            screen.fill(color, (int(star[0]) + layer_offset_x, int(star[1]) + layer_offset_y, size, size))


def fire_player_weapon():
    global muzzle_flash_timer

    muzzle_flash_timer = 3
    nose_y = player_y - player_sprite.get_height() // 2

    if active_weapon == "double":
        lasers.append([player_x - 10 * RES, nose_y, 0, -laser_speed, "double"])
        lasers.append([player_x + 10 * RES, nose_y, 0, -laser_speed, "double"])
    elif active_weapon == "spread":
        lasers.append([player_x, nose_y, 0, -laser_speed, "spread"])
        lasers.append([player_x - 8 * RES, nose_y, -3 * RES, -laser_speed, "spread"])
        lasers.append([player_x + 8 * RES, nose_y, 3 * RES, -laser_speed, "spread"])
    elif active_weapon == "heavy":
        lasers.append([player_x, nose_y, 0, -laser_speed - 2 * RES, "heavy"])
    else:
        lasers.append([player_x, nose_y, 0, -laser_speed, active_weapon])

    weapon_sounds[active_weapon].play()


def add_particles(x, y, color, count, speed, life, size):
    # speed and size are pixel-space, so scale them with the render resolution;
    # count and life are quantities/frames and stay as-is.
    speed = speed * RES
    size = size * RES
    dark_color = mix_color(color, (20, 16, 30), 0.6)
    for i in range(max(1, int(count * 0.6))):
        particles.append([
            x,
            y,
            random.uniform(-speed, speed),
            random.uniform(-speed, speed),
            random.randint(life // 2, life),
            color,
            random.randint(1, size),
            dark_color,
        ])


def add_explosion(x, y, size_key):
    explosions.append([x, y, 0, size_key])


def add_score_popup(text, x, y, color, life=45):
    score_popups.append([text, x, y, -1.2 * RES, life, color])


def add_shockwave(x, y, max_radius, color):
    shockwaves.append([x, y, 6 * RES, max_radius, color])


def get_combo_multiplier(count):
    if count >= 55:
        return 6
    if count >= 35:
        return 5
    if count >= 20:
        return 4
    if count >= 10:
        return 3
    if count >= 5:
        return 2
    return 1


def bump_combo():
    global combo_count, combo_timer, score_multiplier, best_combo_this_run
    global milestone_flash_timer, hitstop_timer, screen_shake_timer, screen_shake_strength

    combo_count = combo_count + 1
    combo_timer = combo_window
    best_combo_this_run = max(best_combo_this_run, combo_count)
    new_multiplier = get_combo_multiplier(combo_count)
    if new_multiplier > score_multiplier:
        score_multiplier = new_multiplier
        milestone_flash_timer = 8
        hitstop_timer = max(hitstop_timer, 5)
        screen_shake_timer = max(screen_shake_timer, 10)
        screen_shake_strength = max(screen_shake_strength, 5 * RES)
        add_score_popup("x" + str(new_multiplier) + " COMBO!", SCREEN_WIDTH // 2, 240 * RES, combo_tier_colors[new_multiplier], 60)
        add_shockwave(player_x, player_y, 70 * RES, combo_tier_colors[new_multiplier])
        milestone_sound.play()


def register_kill(x, y, base_points):
    global hitstop_timer, high_score_beaten, milestone_flash_timer, screen_shake_timer, screen_shake_strength

    bump_combo()
    hitstop_timer = max(hitstop_timer, 2)
    lifetime_stats["total_kills"] = lifetime_stats["total_kills"] + 1
    points = base_points * score_multiplier
    if math.hypot(x - player_x, y - player_y) < 150 * RES:
        points = points + base_points // 2
        add_score_popup("CLOSE!", x, y - 34 * RES, (255, 160, 60))
    if not high_score_beaten and high_score > 0 and score + points > high_score:
        high_score_beaten = True
        add_score_popup("NEW HIGH SCORE!", SCREEN_WIDTH // 2, 200 * RES, (255, 230, 80), 90)
        new_record_sound.play()
        milestone_flash_timer = 10
        screen_shake_timer = max(screen_shake_timer, 12)
        screen_shake_strength = max(screen_shake_strength, 6 * RES)
    return points


def break_combo():
    global combo_count, combo_timer, score_multiplier

    if combo_count >= 5:
        add_score_popup("COMBO LOST", player_x, player_y - 40 * RES, (255, 90, 90))
    combo_count = 0
    combo_timer = 0
    score_multiplier = 1


def damage_player():
    global lives, player_hit_timer, screen_shake_timer, screen_shake_strength, shield_current

    if player_hit_timer > 0:
        return

    break_combo()
    if shield_current > 0:
        shield_current = max(0, shield_current - 35)
    else:
        lives = lives - 1

    player_hit_timer = 45
    screen_shake_timer = 18
    screen_shake_strength = 8 * RES
    player_hit_sound.play()
    add_particles(player_x, player_y, (255, 70, 70), 18, 5, 30, 4)
    add_explosion(player_x, player_y, "small")


def draw_special_move(weapon, timer):
    if timer <= 0:
        return

    progress = 1 - timer / special_move_duration
    fade = min(1, timer / 18)
    color = powerup_colors[weapon]
    move_name = special_move_names[weapon]
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    overlay.fill((0, 0, 0, int(86 * fade)))
    stripe_alpha = int(105 * fade)
    for i in range(-220 * RES, SCREEN_WIDTH + 260 * RES, 70 * RES):
        x = i + int(progress * 260 * RES)
        pygame.draw.polygon(
            overlay,
            (color[0], color[1], color[2], stripe_alpha),
            [(x, 0), (x + 34 * RES, 0), (x - 190 * RES, SCREEN_HEIGHT), (x - 224 * RES, SCREEN_HEIGHT)],
        )

    art_x = int(SCREEN_WIDTH * 0.68)
    art_y = int(SCREEN_HEIGHT * 0.45)
    glow_alpha = int(135 * fade)
    pygame.draw.circle(overlay, (color[0], color[1], color[2], glow_alpha), (art_x, art_y), 118 * RES)

    if weapon == "double":
        pygame.draw.rect(overlay, (230, 250, 255, int(235 * fade)), (art_x - 52 * RES, art_y - 78 * RES, 22 * RES, 155 * RES), border_radius=4 * RES)
        pygame.draw.rect(overlay, (230, 250, 255, int(235 * fade)), (art_x + 30 * RES, art_y - 78 * RES, 22 * RES, 155 * RES), border_radius=4 * RES)
        pygame.draw.line(overlay, (*color, int(255 * fade)), (art_x - 41 * RES, art_y - 102 * RES), (art_x - 41 * RES, art_y - 188 * RES), 8 * RES)
        pygame.draw.line(overlay, (*color, int(255 * fade)), (art_x + 41 * RES, art_y - 102 * RES), (art_x + 41 * RES, art_y - 188 * RES), 8 * RES)
        pygame.draw.rect(overlay, (70, 95, 130, int(230 * fade)), (art_x - 70 * RES, art_y + 52 * RES, 140 * RES, 28 * RES), border_radius=6 * RES)
    elif weapon == "spread":
        for angle in [-32, 0, 32]:
            end_x = art_x + math.sin(math.radians(angle)) * 155 * RES
            end_y = art_y - math.cos(math.radians(angle)) * 155 * RES
            pygame.draw.line(overlay, (*color, int(250 * fade)), (art_x, art_y + 58 * RES), (end_x, end_y), 9 * RES)
            pygame.draw.line(overlay, (255, 255, 255, int(235 * fade)), (art_x, art_y + 58 * RES), (end_x, end_y), 3 * RES)
        pygame.draw.arc(overlay, (*color, int(230 * fade)), (art_x - 88 * RES, art_y - 22 * RES, 176 * RES, 120 * RES), math.radians(205), math.radians(335), 8 * RES)
    elif weapon == "rapid":
        pygame.draw.rect(overlay, (225, 245, 230, int(230 * fade)), (art_x - 74 * RES, art_y - 22 * RES, 150 * RES, 42 * RES), border_radius=8 * RES)
        for i in range(6):
            barrel_x = art_x - 55 * RES + i * 22 * RES
            pygame.draw.rect(overlay, (*color, int(250 * fade)), (barrel_x, art_y - 82 * RES, 10 * RES, 78 * RES), border_radius=3 * RES)
            pygame.draw.line(overlay, (255, 255, 255, int(220 * fade)), (barrel_x + 5 * RES, art_y - 95 * RES), (barrel_x + 5 * RES, art_y - 160 * RES - i * 7 * RES), 3 * RES)
    elif weapon == "heavy":
        pygame.draw.polygon(
            overlay,
            (235, 235, 255, int(235 * fade)),
            [(art_x - 36 * RES, art_y + 80 * RES), (art_x + 36 * RES, art_y + 80 * RES), (art_x + 58 * RES, art_y - 85 * RES), (art_x - 58 * RES, art_y - 85 * RES)],
        )
        pygame.draw.rect(overlay, (*color, int(255 * fade)), (art_x - 16 * RES, art_y - 175 * RES, 32 * RES, 165 * RES), border_radius=5 * RES)
        pygame.draw.circle(overlay, (255, 255, 255, int(245 * fade)), (art_x, art_y - 190 * RES), 22 * RES)
        pygame.draw.line(overlay, (*color, int(235 * fade)), (art_x, art_y - 212 * RES), (art_x, 20 * RES), 14 * RES)

    callout_text = special_font.render(move_name, True, color)
    callout_shadow = special_font.render(move_name, True, (255, 255, 255))
    text_x = 48 * RES
    text_y = int(390 * RES - math.sin(progress * math.pi) * 14 * RES)
    overlay.blit(callout_shadow, (text_x + 3 * RES, text_y + 3 * RES))
    overlay.blit(callout_text, (text_x, text_y))

    subtitle = font.render("SPECIAL WEAPON ONLINE", True, (230, 240, 255))
    overlay.blit(subtitle, (text_x + 8 * RES, text_y + 68 * RES))
    screen.blit(overlay, (0, 0))
    blit_glow(art_x, art_y, color, 260)


def spawn_boss():
    global boss, enemies, enemy_bullets, spawn_timer

    stage = stages[current_stage]
    boss = {
        "x": SCREEN_WIDTH // 2,
        "y": -70 * RES,
        "target_y": 118 * RES,
        "hp": stage["boss_hp"],
        "max_hp": stage["boss_hp"],
        "stage": current_stage,
        "timer": 0,
        "vx": (3 + current_stage) * RES,
    }
    enemies = []
    enemy_bullets = []
    spawn_timer = 0
    play_music("boss", boss_music)


# --- Escape-path guarantee -------------------------------------------------
# Enemy fire must always leave at least one gap that is wide enough for the
# player AND reachable from where they currently are, so deaths come from
# misreading a pattern rather than from an impossible wall. Single aimed shots
# are intentionally kept (you must move to dodge); these helpers only ensure
# there is always somewhere safe to move TO.
#
# Half-width (world px) of the corridor we keep clear at the player's row.
# PLAYER_HITBOX (line ~1185) is in on-screen world px (~47 wide), bullets are
# 6 px wide, so this comfortably clears the hitbox plus a reaction margin.
SAFE_GAP_HALF = 48 * RES


def reachable_safe_x():
    # The always-reachable lane center: the player's own column, clamped so the
    # corridor stays fully on-screen. A descending bullet takes ~60-80 frames to
    # fall while the player moves ~14+ px/frame, so this column is trivially
    # holdable -- the gap it defines is reachable by construction.
    return max(SAFE_GAP_HALF, min(SCREEN_WIDTH - SAFE_GAP_HALF, player_x))


def carve_safe_gap(candidates, safe_x, gap_half=SAFE_GAP_HALF):
    # candidates: list of [x, y, vx, vy, flag] about to be fired in ONE volley.
    # Project each to the player's row and drop those that would land inside the
    # safe corridor, guaranteeing a reachable opening. Small N (4-6), per-volley.
    kept = []
    for b in candidates:
        if b[3] <= 0:                      # not descending -> can't wall the row
            kept.append(b)
            continue
        frames = (player_y - b[1]) / b[3]
        x_at_row = b[0] + b[2] * frames
        if abs(x_at_row - safe_x) > gap_half:
            kept.append(b)
    return kept


def corridor_blocked_if_added(new_bullet):
    # True if adding new_bullet would leave NO reachable corridor (>= player
    # width) anywhere in the span the player can cross before bullets arrive.
    # Used to make independent swarm enemies hold fire rather than seal the
    # player in. Scans enemy_bullets once, only on the rare fire-roll success.
    reach = int(SCREEN_WIDTH * 0.42)
    lo = max(0, player_x - reach)
    hi = min(SCREEN_WIDTH, player_x + reach)
    xs = []
    for b in enemy_bullets + [new_bullet]:
        if b[3] <= 0:
            continue
        frames = (player_y - b[1]) / b[3]
        x = b[0] + b[2] * frames
        if lo <= x <= hi:
            xs.append(x)
    xs.sort()
    edges = [lo] + xs + [hi]
    return all((edges[i + 1] - edges[i]) < 2 * SAFE_GAP_HALF
               for i in range(len(edges) - 1))


def fire_boss_attack(active_boss):
    stage_index = active_boss["stage"]
    timer = active_boss["timer"]
    boss_x = active_boss["x"]
    boss_y = active_boss["y"]

    if stage_index == 0 and timer % 42 == 0:
        shots = [[boss_x, boss_y + 55 * RES, x_speed * RES, 4 * RES, 0]
                 for x_speed in [-3, -1, 1, 3]]
        enemy_bullets.extend(carve_safe_gap(shots, reachable_safe_x()))
    elif stage_index == 1 and timer % 28 == 0:
        shots = []
        for angle in range(25, 156, 26):
            x_speed = math.cos(math.radians(angle)) * 3.2 * RES
            y_speed = math.sin(math.radians(angle)) * 3.2 * RES
            shots.append([boss_x, boss_y + 20 * RES, x_speed, y_speed, 0])
        enemy_bullets.extend(carve_safe_gap(shots, reachable_safe_x()))
    elif stage_index == 2:
        if timer % 38 == 0:
            # Aimed dual kept intact -- two single aimed bullets are dodgeable.
            for offset in [-52 * RES, 52 * RES]:
                dx = player_x - (boss_x + offset)
                dy = player_y - boss_y
                distance = max(1, math.hypot(dx, dy))
                enemy_bullets.append([boss_x + offset, boss_y + 34 * RES, dx / distance * 4 * RES, dy / distance * 4 * RES, 0])
        if timer % 95 == 0:
            shots = [[boss_x, boss_y + 60 * RES, x_speed * RES, 5 * RES, 0]
                     for x_speed in [-4, -2, 0, 2, 4]]
            enemy_bullets.extend(carve_safe_gap(shots, reachable_safe_x()))
    elif stage_index == 3:
        if timer % 16 == 0:
            # Single marching-lane bullet -- never a wall on its own.
            lane_x = 90 * RES + ((timer * 19 * RES) % (SCREEN_WIDTH - 180 * RES))
            enemy_bullets.append([lane_x, boss_y + 44 * RES, 0, 5.5 * RES, 0])
        if timer % 70 == 0:
            shots = [[boss_x + offset, boss_y + 40 * RES, -offset / 22, 4.2 * RES, 0]
                     for offset in [-70 * RES, 70 * RES]]
            enemy_bullets.extend(carve_safe_gap(shots, reachable_safe_x()))
    elif stage_index == 4:
        if timer % 11 == 0:
            # Rotating spiral arms -- inter-arm gaps are inherent.
            angle = timer * 10
            for extra in [0, 180]:
                x_speed = math.cos(math.radians(angle + extra)) * 3.5 * RES
                y_speed = (2.8 + math.sin(math.radians(angle + extra)) * 1.2) * RES
                enemy_bullets.append([boss_x, boss_y + 25 * RES, x_speed, y_speed, 0])
        if timer % 75 == 0:
            shots = [[boss_x, boss_y + 58 * RES, x_speed * RES, 4.8 * RES, 0]
                     for x_speed in [-5, -2.5, 0, 2.5, 5]]
            enemy_bullets.extend(carve_safe_gap(shots, reachable_safe_x()))


def update_boss():
    global boss, screen_shake_timer, screen_shake_strength

    if boss is None:
        return

    if "dying" in boss:
        boss["dying"] = boss["dying"] - 1
        if boss["dying"] % 6 == 0:
            blast_x = boss["x"] + random.randint(-60 * RES, 60 * RES)
            blast_y = boss["y"] + random.randint(-40 * RES, 40 * RES)
            add_particles(blast_x, blast_y, (255, 210, 90), 14, 5, 28, 4)
            add_explosion(blast_x, blast_y, "small")
            enemy_hit_sound.play()
            screen_shake_timer = max(screen_shake_timer, 6)
            screen_shake_strength = max(screen_shake_strength, 4 * RES)
        if boss["dying"] <= 0:
            finish_boss()
        return

    boss["timer"] = boss["timer"] + 1
    stage_index = boss["stage"]

    if boss["y"] < boss["target_y"]:
        boss["y"] = boss["y"] + 2 * RES
    elif stage_index == 0:
        boss["x"] = SCREEN_WIDTH // 2 + math.sin(boss["timer"] / 55) * 165 * RES
    elif stage_index == 1:
        boss["x"] = SCREEN_WIDTH // 2 + math.sin(boss["timer"] / 38) * 210 * RES
        boss["y"] = boss["target_y"] + math.sin(boss["timer"] / 52) * 24 * RES
    elif stage_index == 2:
        boss["x"] = SCREEN_WIDTH // 2 + math.sin(boss["timer"] / 70) * 120 * RES
    elif stage_index == 3:
        boss["x"] = boss["x"] + boss["vx"]
        if boss["x"] < 145 * RES or boss["x"] > SCREEN_WIDTH - 145 * RES:
            boss["vx"] = boss["vx"] * -1
    elif stage_index == 4:
        boss["x"] = SCREEN_WIDTH // 2 + math.cos(boss["timer"] / 58) * 145 * RES
        boss["y"] = boss["target_y"] + math.sin(boss["timer"] / 45) * 34 * RES

    fire_boss_attack(boss)


def damage_boss(laser):
    global boss, score, stage_score, screen_shake_timer, screen_shake_strength

    damage = get_laser_damage(laser)
    boss["hp"] = boss["hp"] - damage
    score = score + 2 * score_multiplier
    stage_score = stage_score + 2
    enemy_hit_sound.play()
    add_particles(laser[0], laser[1], powerup_colors.get(laser[4], (255, 220, 60)), 8, 3, 18, 3)
    screen_shake_timer = max(screen_shake_timer, 4)
    screen_shake_strength = max(screen_shake_strength, 2 * RES)


def finish_boss():
    global boss, current_stage, stage_score, running, mission_complete, screen_shake_timer, screen_shake_strength, upgrade_screen
    global enemies, enemy_bullets, particles, score

    defeated_boss = stages[current_stage]["boss"]
    boss_bonus = 300 + current_stage * 100
    add_particles(boss["x"], boss["y"], (255, 210, 90), 80, 8, 60, 6)
    add_explosion(boss["x"], boss["y"], "boss")
    add_shockwave(boss["x"], boss["y"], 160 * RES, (255, 210, 90))
    add_shockwave(boss["x"], boss["y"], 110 * RES, (255, 255, 255))
    add_score_popup(defeated_boss + " DOWN", boss["x"], boss["y"], (255, 230, 120), 75)
    add_score_popup("+" + str(boss_bonus), boss["x"], boss["y"] + 34 * RES, (255, 230, 120), 75)
    lifetime_stats["total_boss_kills"] = lifetime_stats["total_boss_kills"] + 1
    score = score + boss_bonus
    stage_score = 0
    current_stage = current_stage + 1
    boss = None
    enemies = []
    enemy_bullets = []
    screen_shake_timer = 28
    screen_shake_strength = 10 * RES

    if current_stage >= len(stages):
        mission_complete = True
        running = False
    else:
        upgrade_screen = True
        music_channel.stop()


def draw_stage_background(stage_index):
    screen.blit(stage_backgrounds[min(stage_index, len(stage_backgrounds) - 1)], (0, 0))


def draw_boss():
    if boss is None:
        return

    boss_frame = (boss["timer"] // 14) % 2
    boss_sprite = boss_sprites[boss["stage"]][boss_frame]
    boss_rect = boss_sprite.get_rect(center=(boss["x"] + world_offset_x, boss["y"] + world_offset_y))
    screen.blit(boss_sprite, boss_rect)
    if "dying" in boss and boss["dying"] % 6 < 3:
        screen.blit(boss_flash_sprites[boss["stage"]], boss_rect)

    draw_segment_bar(screen, 170 * RES, 58 * RES, 460 * RES, 16 * RES, max(0, boss["hp"] / boss["max_hp"]), (255, 80, 90), segments=24)
    draw_text_shadowed(small_font, stages[boss["stage"]]["boss"], (255, 230, 230), center=(400 * RES, 46 * RES))


def draw_stage_hud():
    stage = stages[current_stage] if current_stage < len(stages) else stages[-1]
    draw_text_shadowed(small_font, stage["name"], (220, 235, 255), topleft=(10 * RES, 130 * RES))
    if boss is None:
        draw_text_shadowed(small_font, "BOSS SIGNAL: " + str(min(stage_score, stage["goal"])) + "/" + str(stage["goal"]), (255, 220, 120), topleft=(10 * RES, 150 * RES))
    else:
        draw_text_shadowed(small_font, "BOSS FIGHT", (255, 120, 120), topleft=(10 * RES, 150 * RES))


# Hitboxes track the on-screen sprite size, not the world scale: body sprites grew
# by 4/3 (scale 3 -> 4) and the boss by 5/4 (scale 4 -> 5) under RES = 2.
PLAYER_HITBOX = (47, 56)
ENEMY_HITBOXES = [(37, 29), (37, 29), (37, 29), (29, 29)]
BOSS_HITBOX_LASER = (110, 65)
BOSS_HITBOX_BODY = (100, 58)

powerup_colors = {
    "double": (60, 220, 255),
    "spread": (255, 210, 70),
    "rapid": (95, 255, 120),
    "heavy": (255, 95, 210),
}

player_colors = {
    "W": (235, 245, 255),
    "L": (140, 235, 255),
    "C": (40, 170, 220),
    "D": (16, 80, 150),
    "G": (24, 110, 160),
    "A": (255, 150, 30),
}

player_rows_center = [
    "........W........",
    ".......WLW.......",
    ".......LCL.......",
    "......LLCLL......",
    "......LCCCL......",
    ".....LCGGGCL.....",
    ".....LCGWGCL.....",
    ".....LCGGGCL.....",
    "....LCCDDDCCL....",
    "....LCCCCCCCL....",
    "...LCCCCCCCCCL...",
    "..LCCDCCCCCDCCL..",
    ".LCCDDCCCCCDDCCL.",
    "LCCDD.DCCCD.DDCCL",
    "LCD...DDDDD...DCL",
    "LD....DAAAD....DL",
    "......DAAAD......",
    ".......AAA.......",
]

player_rows_left = player_rows_center[:11] + [
    "...DCDCCCCCDCCL..",
    "..DCDDCCCCCDDCCL.",
    ".DCDD.DCCCD.DDCCL",
    ".DD...DDDDD...DCL",
    ".D....DAAAD....DL",
    "......DAAAD......",
    ".......AAA.......",
]

player_rows_right = [row[::-1] for row in player_rows_left]

player_sprite = make_pixel_sprite(player_rows_center, player_colors, 4)
player_sprite_left = make_pixel_sprite(player_rows_left, player_colors, 4)
player_sprite_right = make_pixel_sprite(player_rows_right, player_colors, 4)
player_flash_center = make_flash_sprite(player_sprite)
player_flash_left = make_flash_sprite(player_sprite_left)
player_flash_right = make_flash_sprite(player_sprite_right)
player_preview_sprite = make_pixel_sprite(player_rows_center, player_colors, 11)

flame_rows_a = [
    ".WWW.",
    "YWWWY",
    "YYOYY",
    ".YOY.",
    ".ROR.",
    "..R..",
]
flame_rows_b = [
    "WWWWW",
    "YWWWY",
    ".YYY.",
    ".YOY.",
    "..R..",
    ".....",
]


def make_flame_frames(color):
    flame_palette = {
        "W": (255, 255, 255),
        "Y": mix_color(color, (255, 255, 255), 0.45),
        "O": color,
        "R": mix_color(color, (40, 10, 10), 0.45),
    }
    return (
        make_pixel_sprite(flame_rows_a, flame_palette, 4, outline=False),
        make_pixel_sprite(flame_rows_b, flame_palette, 4, outline=False),
    )


flame_frames = {"single": make_flame_frames((255, 150, 30))}
for weapon_name, weapon_color in powerup_colors.items():
    flame_frames[weapon_name] = make_flame_frames(weapon_color)

diver_colors = {
    "M": (210, 42, 62),
    "R": (120, 20, 40),
    "L": (255, 130, 120),
    "K": (35, 26, 46),
    "G": (95, 240, 135),
    "A": (255, 140, 40),
}
diver_rows_a = [
    "......MM......",
    ".....MLLM.....",
    "....MLLLLM....",
    "...MLKKKKLM...",
    "..MLKGGGGKLM..",
    ".MMLKGGGGKLMM.",
    "MM.RKKKKKKR.MM",
    "M..MRKKKKRM..M",
    "...MRRRRRRM...",
    "....MRAARM....",
    ".....AAAA.....",
    "......AA......",
]
diver_rows_b = diver_rows_a[:-2] + [
    "....AA..AA....",
    ".....AAAA.....",
]

weaver_colors = {
    "B": (30, 60, 160),
    "C": (62, 190, 235),
    "L": (160, 235, 255),
    "W": (235, 250, 255),
    "P": (70, 40, 120),
    "Q": (255, 60, 170),
    "A": (255, 140, 40),
}
weaver_rows_a = [
    ".....BLLB.....",
    "....BLWWLB....",
    "...BLLLLLLB...",
    ".BBCCCCCCCCBB.",
    "BCPPQQPPQQPPCB",
    ".BBCCCCCCCCBB.",
    "..BBBCCCCBBB..",
    "....BBBBBB....",
    "....BB..BB....",
    "....AA..AA....",
    ".....A..A.....",
]
weaver_rows_b = weaver_rows_a[:-2] + [
    "....A....A....",
    "....AA..AA....",
]

tank_colors = {
    "S": (170, 175, 192),
    "L": (220, 225, 238),
    "N": (75, 78, 96),
    "V": (165, 60, 220),
    "H": (255, 78, 92),
    "W": (235, 245, 255),
    "A": (255, 140, 40),
}
tank_rows_a = [
    "..NSSSSSSSSN..",
    ".NSLLSSSSLLSN.",
    "NSSVVVVVVVVSSN",
    "NSVVHHHHHHVVSN",
    "NSVHHWWWWHHVSN",
    "NSVVHHHHHHVVSN",
    "NSSVVVVVVVVSSN",
    ".NSSNNNNNNSSN.",
    "..NNSSSSSSNN..",
    "...NNLLLLNN...",
    "....AA..AA....",
    "...AAA..AAA...",
]
tank_rows_b = tank_rows_a[:-2] + [
    "...AAA..AAA...",
    "....AA..AA....",
]

kamikaze_colors = {
    "O": (255, 150, 40),
    "K": (60, 30, 20),
    "W": (255, 220, 120),
    "A": (255, 70, 30),
}
kamikaze_rows_a = [
    ".....OO.....",
    ".O..OKKO..O.",
    "..OOKWWKOO..",
    ".OKWWAAWWKO.",
    "OKWAAAAAAWKO",
    "OKWAAKKAAWKO",
    "OKWAAKKAAWKO",
    "OKWAAAAAAWKO",
    ".OKWWAAWWKO.",
    "..OOKWWKOO..",
    ".O..OKKO..O.",
    ".....OO.....",
]
kamikaze_rows_b = [
    "...O....O...",
    "....OKKO....",
] + kamikaze_rows_a[2:10] + [
    "....OKKO....",
    "...O....O...",
]

enemy_sprites = [
    (make_pixel_sprite(diver_rows_a, diver_colors, 4), make_pixel_sprite(diver_rows_b, diver_colors, 4)),
    (make_pixel_sprite(weaver_rows_a, weaver_colors, 4), make_pixel_sprite(weaver_rows_b, weaver_colors, 4)),
    (make_pixel_sprite(tank_rows_a, tank_colors, 4), make_pixel_sprite(tank_rows_b, tank_colors, 4)),
    (make_pixel_sprite(kamikaze_rows_a, kamikaze_colors, 4), make_pixel_sprite(kamikaze_rows_b, kamikaze_colors, 4)),
]
enemy_flash_sprites = tuple(make_flash_sprite(frame, (255, 60, 60, 130)) for frame in enemy_sprites[3])
# Bright white hit-flash per enemy type — popped briefly when an enemy is
# damaged but not destroyed, so tanky enemies visibly react to every shot.
enemy_hit_flash_sprites = [
    tuple(make_flash_sprite(frame, (255, 255, 255, 165)) for frame in frames)
    for frames in enemy_sprites
]

def make_boss_frames(half_rows, colors, pulse_keys):
    rows = mirror_rows(half_rows)
    frame_a = make_pixel_sprite(rows, colors, 5)
    colors_b = dict(colors)
    for key in pulse_keys:
        colors_b[key] = mix_color(colors[key], (255, 255, 255), 0.45)
    frame_b = make_pixel_sprite(rows, colors_b, 5)
    return (frame_a, frame_b)


carrier_half_rows = [
    ".............MM",
    "............MLL",
    "...........MLLL",
    "..........MLYYY",
    ".........MLYKKK",
    "........MLYKKKK",
    ".......MLYKGGKK",
    "......MLYKGGGGK",
    ".....MLYKKGGKKK",
    "....MLYKKKKKKKW",
    "...MLYKKKKKWKWK",
    "..MLYKKKKKKWKWK",
    ".MLLYKKKKKKKKKK",
    "MLLYYPPPPPPPPPP",
    "MLLYPPPPPPPPPPP",
    "..MLYPPPAAAPPPP",
    "....MLYPAAAPPPP",
    "......MMPPAAAPP",
]
carrier_colors = {
    "M": (210, 48, 62),
    "R": (130, 22, 40),
    "L": (255, 140, 130),
    "Y": (240, 190, 70),
    "K": (28, 22, 40),
    "G": (95, 240, 135),
    "W": (235, 245, 255),
    "P": (100, 35, 118),
    "A": (255, 130, 40),
}

wheel_half_rows = [
    "............BBB",
    "..........BCCCC",
    ".........BCCCCC",
    "........BCPPPPC",
    ".......BCPPPPPC",
    ".......BCPCPPPC",
    "......BCPPCPPPC",
    "......BCPPPCQQQ",
    "......BCCCCCQWQ",
    "......BCCCCCQWQ",
    "......BCPPPCQQQ",
    "......BCPPCPPPC",
    ".......BCPCPPPC",
    ".......BCPPPPPC",
    "........BCPPPPC",
    ".........BCCCCC",
    "..........BCCCC",
    "............BAA",
]
wheel_colors = {
    "B": (30, 60, 170),
    "C": (70, 200, 240),
    "P": (75, 40, 135),
    "Q": (255, 70, 180),
    "W": (235, 250, 255),
    "A": (255, 140, 40),
}

prism_half_rows = [
    ".......NN......",
    ".......NSN.....",
    "......NSSSN....",
    ".....NSVVVSN...",
    "....NSVVHVVSN..",
    "...NSVVHHHVVSN.",
    "..NSVVHHWHHVVSN",
    ".NSVVHHWWWHHVVS",
    "NSVVHHWWWWHHVSS",
    ".NSVVHHWWWHHVVS",
    "..NSVVHHWHHVVSN",
    "...NSVVHHHVVSN.",
    "....NSVVHVVSN..",
    ".....NSVVVSN...",
    "......NSSSN....",
    ".......NSN.....",
    ".......NAN.....",
    ".......AAA.....",
]
prism_colors = {
    "S": (185, 190, 205),
    "N": (65, 70, 90),
    "V": (175, 60, 230),
    "H": (255, 90, 160),
    "W": (245, 250, 255),
    "A": (255, 140, 40),
}

fortress_half_rows = [
    "..BBB.....BBB..",
    "..BTB.....BTB..",
    "..BBB.....BBB..",
    ".GGEGGGGGGGEGGG",
    "GLLLLLLLLLLLLLL",
    "GLEEEEEEEEEEEEE",
    "GLEOOOOOOOOOOOO",
    "GLEOBBBBBBBBBBB",
    "GLEOBTTTWTTTTBB",
    "GLEOBTTTTTTTTBB",
    "GLEOBBBBBBBBBBB",
    "GLEOOOOOOOOOOOO",
    "GLEEEEEEEEEEEEE",
    "GGLLLLLLLLLLLLL",
    ".GGEGGGGGGGEGGG",
    "...AA....AA....",
    "...AA....AA....",
    "....A.....A....",
]
fortress_colors = {
    "G": (60, 200, 95),
    "E": (24, 90, 55),
    "L": (160, 255, 170),
    "O": (245, 190, 65),
    "B": (35, 38, 55),
    "T": (80, 255, 200),
    "W": (235, 250, 255),
    "A": (255, 135, 40),
}

crown_half_rows = [
    ".P....P....P...",
    ".P....P....P...",
    ".PF...PF...PF..",
    ".PFP..PFP..PFP.",
    ".PFFP.PFFP.PFFP",
    "NPFFPNPFFPNPFFP",
    "NPPPPPPPPPPPPPP",
    "NPFEEEEEEEEEEEE",
    "NPFENNNNNNKKKKK",
    "NPFENNNNNEKKKKK",
    "NPFENNNNNEKKWKK",
    "NPFENNNNNEKKKKK",
    "NPFENNNNNNKKKKK",
    "NPFEEEEEEEEEEEE",
    "NPPPPPPPPPPPPPP",
    ".NPPFFFFFFFFFFF",
    "...NPPPAAAPPPPP",
    "......NPPAAAPPP",
]
crown_colors = {
    "P": (195, 70, 255),
    "N": (45, 38, 72),
    "F": (255, 90, 190),
    "E": (255, 230, 85),
    "K": (12, 10, 20),
    "W": (245, 250, 255),
    "A": (255, 105, 45),
}

boss_sprites = [
    make_boss_frames(carrier_half_rows, carrier_colors, ["G", "W"]),
    make_boss_frames(wheel_half_rows, wheel_colors, ["Q", "W"]),
    make_boss_frames(prism_half_rows, prism_colors, ["H", "W"]),
    make_boss_frames(fortress_half_rows, fortress_colors, ["T", "W"]),
    make_boss_frames(crown_half_rows, crown_colors, ["E", "W"]),
]
boss_flash_sprites = [make_flash_sprite(frames[0], (255, 255, 255, 90)) for frames in boss_sprites]

bolt_colors = {"single": (255, 255, 0)}
bolt_colors.update(powerup_colors)

bolt_rows_a = [".C.", "CWC", "CWC", "CWC", "CWC", ".C.", ".D."]
bolt_rows_b = [".W.", "CWC", "CCC", "CWC", "CCC", ".C.", ".D."]
heavy_bolt_rows_a = ["..C..", ".CWC.", "CWWWC", "CWWWC", "CWWWC", "CWWWC", ".CWC.", ".CDC.", "..D.."]
heavy_bolt_rows_b = ["..W..", ".CWC.", "CWWWC", "CWCWC", "CWWWC", "CWCWC", ".CWC.", ".CDC.", "..D.."]


def make_bolt_frames(color, heavy=False):
    bolt_palette = {"W": (255, 255, 255), "C": color, "D": mix_color(color, (20, 16, 40), 0.5)}
    rows_pair = (heavy_bolt_rows_a, heavy_bolt_rows_b) if heavy else (bolt_rows_a, bolt_rows_b)
    return tuple(make_pixel_sprite(rows, bolt_palette, 4) for rows in rows_pair)


bolt_sprites = {}
for weapon_name, weapon_color in bolt_colors.items():
    bolt_sprites[weapon_name] = make_bolt_frames(weapon_color, heavy=(weapon_name == "heavy"))

spread_bolt_sprites = {
    -1: tuple(pygame.transform.rotate(frame, 17) for frame in bolt_sprites["spread"]),
    1: tuple(pygame.transform.rotate(frame, -17) for frame in bolt_sprites["spread"]),
}

enemy_bullet_palette = {"R": (255, 60, 90), "P": (255, 150, 180), "W": (255, 240, 245)}
enemy_bullet_frames = (
    make_pixel_sprite([".RRR.", "RPPPR", "RPWPR", "RPPPR", ".RRR."], enemy_bullet_palette, 4),
    make_pixel_sprite([".RRR.", "RPWPR", "RWWWR", "RPWPR", ".RRR."], enemy_bullet_palette, 4),
)

muzzle_rows = [
    ["...C...", "...W...", ".C.W.C.", "CWWWWWC", ".C.W.C.", "...W...", "...C..."],
    ["..C..", ".CWC.", "CWWWC", ".CWC.", "..C.."],
    [".C.", "CWC", ".C."],
]


def make_muzzle_frames(color):
    muzzle_palette = {"W": (255, 255, 255), "C": color}
    return [make_pixel_sprite(rows, muzzle_palette, 4, outline=False) for rows in muzzle_rows]


muzzle_flash_sprites = {"single": make_muzzle_frames((255, 230, 120))}
for weapon_name, weapon_color in powerup_colors.items():
    muzzle_flash_sprites[weapon_name] = make_muzzle_frames(weapon_color)

powerup_glyphs = {
    "double": ["WW.", "W.W", "W.W", "W.W", "WW."],
    "spread": [".WW", "W..", ".W.", "..W", "WW."],
    "rapid": ["WW.", "W.W", "WW.", "W.W", "W.W"],
    "heavy": ["W.W", "W.W", "WWW", "W.W", "W.W"],
}


def make_powerup_frames(color, glyph):
    rows = []
    for y in range(11):
        row = ""
        for x in range(11):
            span = abs(x - 5) + abs(y - 5)
            if span > 5:
                row += "."
            elif span == 5:
                row += "M"
            elif x <= 5 and y <= 5 and span >= 3:
                row += "L"
            else:
                row += "F"
        rows.append(row)
    for glyph_y, glyph_row in enumerate(glyph):
        row = list(rows[3 + glyph_y])
        for glyph_x, glyph_pixel in enumerate(glyph_row):
            if glyph_pixel == "W":
                row[4 + glyph_x] = "K"
        rows[3 + glyph_y] = "".join(row)
    powerup_palette = {
        "M": mix_color(color, (20, 16, 40), 0.4),
        "L": mix_color(color, (255, 255, 255), 0.55),
        "F": color,
        "K": (16, 14, 28),
    }
    full = make_pixel_sprite(rows, powerup_palette, 4)
    width, height = full.get_size()
    frames = [full]
    for squash in (0.7, 0.35, 0.7):
        frames.append(pygame.transform.scale(full, (max(3, int(width * squash)), height)))
    return frames


powerup_sprites = {name: make_powerup_frames(powerup_colors[name], powerup_glyphs[name]) for name in powerup_glyphs}

explosion_frames = {
    "small": make_explosion_frames(12, 5),
    "large": make_explosion_frames(16, 7),
    "boss": make_explosion_frames(24, 8),
}

stages = [
    {"name": "Stage 1: Sky Patrol", "boss": "Carrier Fang", "goal": 120, "spawn_delay": 62, "speed": 0, "fire_roll": 170, "color": (5, 8, 24), "boss_hp": 180},
    {"name": "Stage 2: Crimson Orbit", "boss": "Red Wheel", "goal": 170, "spawn_delay": 54, "speed": 1, "fire_roll": 145, "color": (18, 5, 18), "boss_hp": 230},
    {"name": "Stage 3: Prism Gate", "boss": "Twin Prism", "goal": 230, "spawn_delay": 48, "speed": 1, "fire_roll": 125, "color": (6, 18, 26), "boss_hp": 285},
    {"name": "Stage 4: Green Monsoon", "boss": "Iron Monsoon", "goal": 300, "spawn_delay": 42, "speed": 2, "fire_roll": 105, "color": (5, 20, 14), "boss_hp": 350},
    {"name": "Stage 5: Event Horizon", "boss": "Singularity Crown", "goal": 380, "spawn_delay": 36, "speed": 3, "fire_roll": 85, "color": (12, 4, 22), "boss_hp": 430},
]

stage_accents = [(70, 110, 220), (220, 70, 130), (60, 180, 220), (70, 200, 120), (170, 70, 230)]
planet_palettes = [
    [(40, 60, 110), (90, 130, 200), (150, 190, 240)],
    [(95, 30, 30), (180, 80, 50), (230, 140, 90)],
    [(40, 70, 90), (90, 170, 200), (170, 230, 245)],
    [(25, 80, 45), (60, 150, 80), (120, 210, 130)],
    [(10, 8, 16), (30, 22, 44), (60, 45, 85)],
]
planet_positions = [(560 * RES, 80 * RES), (90 * RES, 110 * RES), (470 * RES, 60 * RES), (120 * RES, 70 * RES), (270 * RES, 60 * RES)]

stage_backgrounds = []
for stage_index, stage in enumerate(stages):
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    base_color = stage["color"]
    band_height = SCREEN_HEIGHT // 4
    for band in range(4):
        band_color = (
            min(255, base_color[0] + band * 3),
            min(255, base_color[1] + band * 3),
            min(255, base_color[2] + band * 4),
        )
        background.fill(band_color, (0, band * band_height, SCREEN_WIDTH, band_height))
    background.blit(make_nebula(stage_accents[stage_index], stage_index * 31 + 7), (0, 0))
    planet_ring_color = (255, 160, 60) if stage_index == 4 else None
    planet = make_planet((16 + stage_index * 2) * RES, planet_palettes[stage_index], stage_index * 13 + 3, planet_ring_color)
    background.blit(planet, planet_positions[stage_index])
    stage_backgrounds.append(background.convert())

game_over_background = stage_backgrounds[-1].copy()
game_over_dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
game_over_dim.fill((0, 0, 0))
game_over_dim.set_alpha(160)
game_over_background.blit(game_over_dim, (0, 0))

scanline_overlay = make_scanline_overlay()

# Red screen-edge flash drawn when the player takes damage — a full-screen
# hurt cue on top of the ship-flash and screen shake.
hurt_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)


def draw_hurt_vignette(intensity):
    if intensity <= 0:
        return
    hurt_overlay.fill((0, 0, 0, 0))
    bands = 50
    for i in range(bands):
        inset = i * 3 * RES
        if inset * 2 >= SCREEN_HEIGHT:
            break
        alpha = int(150 * intensity * (1 - i / bands) ** 2)
        if alpha <= 0:
            continue
        pygame.draw.rect(
            hurt_overlay,
            (205, 35, 45, alpha),
            (inset, inset, SCREEN_WIDTH - inset * 2, SCREEN_HEIGHT - inset * 2),
            3 * RES,
        )
    screen.blit(hurt_overlay, (0, 0))


milestone_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
milestone_overlay.fill((255, 255, 255))
pause_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
pause_overlay.fill((0, 0, 0))
pause_overlay.set_alpha(110)

vignette_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
for vignette_rect in [
    (0, 0, SCREEN_WIDTH, 26 * RES),
    (0, SCREEN_HEIGHT - 26 * RES, SCREEN_WIDTH, 26 * RES),
    (0, 0, 26 * RES, SCREEN_HEIGHT),
    (SCREEN_WIDTH - 26 * RES, 0, 26 * RES, SCREEN_HEIGHT),
]:
    pygame.draw.rect(vignette_overlay, (255, 30, 30, 65), vignette_rect)

player_x = 400 * RES
player_y = 520 * RES
player_velocity_x = 0
player_velocity_y = 0
player_acceleration = 36 * RES
player_friction = 0.86
player_max_speed = 420 * RES

galaxy_distance = 26000.0
minimum_black_hole_distance = CRASH_DISTANCE_KILOMETERS / LIGHT_YEAR_KILOMETERS
max_galaxy_distance = 50000
radial_speed_ly_per_second = -120.0
orbit_speed_degrees_per_second = 35.0
orbit_angle = -math.pi / 2
black_hole_crash = False

star_layers = []
for layer_speed, layer_count, layer_size, layer_colors, layer_depth in [
    (0.4 * RES, 70, 1 * RES, ((110, 120, 150), (80, 90, 115)), 0.3),
    (1.2 * RES, 50, 2 * RES, ((180, 195, 225), (140, 155, 190)), 0.6),
    (2.8 * RES, 30, 3 * RES, ((255, 255, 255), (150, 200, 255)), 1.0),
]:
    layer_stars = [
        [random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), random.randint(0, 6 * RES)]
        for _ in range(layer_count)
    ]
    star_layers.append({
        "speed": layer_speed,
        "size": layer_size,
        "colors": layer_colors,
        "depth": layer_depth,
        "stars": layer_stars,
    })

lasers = []
laser_speed = 10 * RES
fire_timer = 0
fire_delay = 12

powerups = []
powerup_speed = 2 * RES
powerup_timer = 0
powerup_spawn_delay = 420
active_weapon = "single"
weapon_timer = 0
weapon_duration = 600
weapon_types = ["double", "spread", "rapid", "heavy"]
special_move_names = {
    "double": "TWIN COMET",
    "spread": "STARFALL FAN",
    "rapid": "NEON BARRAGE",
    "heavy": "NOVA LANCE",
}
special_move_weapon = ""
special_move_timer = 0
special_move_duration = 90

enemies = []
enemy_speed = 1
spawn_timer = 0

enemy_bullets = []
enemy_bullet_speed = 4

particles = []
explosions = []
score_popups = []
shockwaves = []
screen_shake_timer = 0
screen_shake_strength = 0
player_hit_timer = 0
hitstop_timer = 0
muzzle_flash_timer = 0

combo_count = 0
combo_timer = 0
combo_window = 150
score_multiplier = 1
best_combo_this_run = 0
milestone_flash_timer = 0
combo_tier_colors = {
    1: (235, 245, 255),
    2: (255, 220, 80),
    3: (255, 140, 60),
    4: (255, 70, 160),
    5: (160, 90, 255),
    6: (90, 230, 255),
}
graze_count_this_run = 0
graze_pulse_timer = 0
graze_popup_cooldown = 0
wave_timer = 0
boss_warning_timer = 0
high_score_beaten = False
enemy_kill_points = [10, 10, 25, 20]
lifetime_stats = load_stats()

score = 0
high_score = load_high_score()
high_score_time = load_high_score_time()
lives = 20
current_stage = 0
stage_score = 0
boss = None
mission_complete = False
gun_upgrade_level = 0
shield_upgrade_level = 0
engine_upgrade_level = 0
shield_max = 100
shield_current = shield_max
upgrade_screen = False

font = pygame.font.SysFont("monospace", 24 * RES)
small_font = pygame.font.SysFont("monospace", 16 * RES)
big_64pixel_font = pygame.font.SysFont("monospace", 64 * RES)
medium_32_pixel_font = pygame.font.SysFont("monospace", 32 * RES)
special_font = pygame.font.SysFont("monospace", 54 * RES, bold=True)
paused = False
pause_button = pygame.Rect(350 * RES, 10 * RES, 100 * RES, 34 * RES)
upgrade_buttons = {
    "guns": pygame.Rect(70 * RES, 400 * RES, 200 * RES, 145 * RES),
    "shields": pygame.Rect(300 * RES, 400 * RES, 200 * RES, 145 * RES),
    "engine": pygame.Rect(530 * RES, 400 * RES, 200 * RES, 145 * RES),
}
play_music("stage_0", stage_music[0])
app_running = True
while app_running:
    while running:

        # --- CHECK / EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                handle_window_resize(event.size)
            elif upgrade_screen and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    apply_upgrade("guns")
                elif event.key == pygame.K_2:
                    apply_upgrade("shields")
                elif event.key == pygame.K_3:
                    apply_upgrade("engine")
            elif upgrade_screen and event.type == pygame.MOUSEBUTTONDOWN:
                for upgrade_name, button_rect in upgrade_buttons.items():
                    if button_rect.collidepoint(to_logical(event.pos)):
                        apply_upgrade(upgrade_name)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                toggle_pause()
            elif event.type == pygame.MOUSEBUTTONDOWN and pause_button.collidepoint(to_logical(event.pos)):
                toggle_pause()

        # --- UPDATE ---
        if hitstop_timer > 0 and not paused and not upgrade_screen:
            hitstop_timer = hitstop_timer - 1
        elif not paused and not upgrade_screen:
            seconds_passed = clock.get_time() / 1000
            stage = stages[current_stage]
            if boss is None and boss_warning_timer == 0:
                wave_timer = (wave_timer + 1) % 900
            in_lull = boss is None and boss_warning_timer == 0 and 600 <= wave_timer < 760
            if wave_timer < 600:
                current_spawn_delay = max(12, int(stage["spawn_delay"] * 0.72))
            else:
                current_spawn_delay = stage["spawn_delay"]
            enemies_per_spawn = 1 + min(current_stage // 2, 2)
            current_enemy_speed = (enemy_speed + stage["speed"]) * RES
            current_enemy_bullet_speed = (enemy_bullet_speed + min(current_stage, 3)) * RES
            enemy_fire_roll = stage["fire_roll"]

            if weapon_timer > 0:
                weapon_timer = weapon_timer - 1
            elif active_weapon != "single":
                active_weapon = "single"

            if player_hit_timer > 0:
                player_hit_timer = player_hit_timer - 1
            if screen_shake_timer > 0:
                screen_shake_timer = screen_shake_timer - 1
            if special_move_timer > 0:
                special_move_timer = special_move_timer - 1
            if milestone_flash_timer > 0:
                milestone_flash_timer = milestone_flash_timer - 1
            if muzzle_flash_timer > 0:
                muzzle_flash_timer = muzzle_flash_timer - 1
            if graze_pulse_timer > 0:
                graze_pulse_timer = graze_pulse_timer - 1
            if graze_popup_cooldown > 0:
                graze_popup_cooldown = graze_popup_cooldown - 1
            if combo_timer > 0:
                combo_timer = combo_timer - 1
                if combo_timer == 0:
                    break_combo()

            current_fire_delay = 5 if active_weapon == "rapid" else fire_delay

            fire_timer = fire_timer + 1
            if fire_timer >= current_fire_delay:
                fire_player_weapon()
                fire_timer = 0

            for layer in star_layers:
                for star in layer["stars"]:
                    star[1] = star[1] + layer["speed"]
                    if star[1] > SCREEN_HEIGHT:
                        star[1] = 0
                        star[0] = random.randint(0, SCREEN_WIDTH)

            powerup_timer = powerup_timer + 1
            if powerup_timer >= powerup_spawn_delay:
                powerup_x = random.randint(40 * RES, SCREEN_WIDTH - 40 * RES)
                powerup_type = random.choice(weapon_types)
                powerups.append([powerup_x, -25 * RES, powerup_type])
                powerup_timer = 0

            new_powerups = []
            for powerup in powerups:
                powerup[1] = powerup[1] + powerup_speed
                if powerup[1] < SCREEN_HEIGHT + 30 * RES:
                    new_powerups.append(powerup)
            powerups = new_powerups

            if boss is None and boss_warning_timer > 0:
                boss_warning_timer = boss_warning_timer - 1
                if boss_warning_timer == 90:
                    warning_sound.play()
                if boss_warning_timer == 0:
                    spawn_boss()
            elif boss is None and stage_score >= stage["goal"]:
                boss_warning_timer = 180
                warning_sound.play()
            elif boss is None and not in_lull:
                spawn_timer = spawn_timer + 1
                if spawn_timer >= current_spawn_delay:
                    for i in range(enemies_per_spawn):
                        enemy_x = random.randint(30 * RES, SCREEN_WIDTH - 30 * RES)
                        enemy_y = -30 * RES - i * 45 * RES
                        if current_stage == 0:
                            enemy_type = random.randint(0, 1)
                        elif random.random() < 0.13:
                            enemy_type = 3
                        else:
                            enemy_type = random.randint(0, 2)
                        enemy_hp = 5 + current_stage * 2
                        if enemy_type == 2:
                            enemy_hp = enemy_hp * 3
                        elif enemy_type == 3:
                            enemy_hp = 3
                        enemies.append([enemy_x, enemy_y, enemy_type, enemy_hp, 0, random.randint(0, 60), 0, 0])
                    spawn_timer = 0

            update_boss()

            new_enemies = []
            for enemy in enemies:
                enemy[5] = enemy[5] + 1
                if enemy[7] > 0:
                    enemy[7] = enemy[7] - 1
                if enemy[2] == 0:
                    if enemy[6] == 0 and enemy[1] > 130 * RES and abs(enemy[0] - player_x) < 90 * RES:
                        enemy[6] = 1
                        enemy[4] = max(-4 * RES, min(4 * RES, (player_x - enemy[0]) / 40))
                    if enemy[6] == 1:
                        enemy[0] = enemy[0] + enemy[4]
                        enemy[1] = enemy[1] + current_enemy_speed * 2.6
                        add_particles(enemy[0], enemy[1] - 14 * RES, (255, 150, 50), 2, 1, 10, 2)
                    else:
                        enemy[1] = enemy[1] + current_enemy_speed
                elif enemy[2] == 1:
                    enemy[0] = enemy[0] + math.sin(enemy[5] / 16) * 2.6 * RES
                    enemy[1] = enemy[1] + current_enemy_speed
                elif enemy[2] == 2:
                    enemy[1] = enemy[1] + current_enemy_speed * 0.55
                else:
                    if player_x > enemy[0]:
                        enemy[4] = min(3.5 * RES, enemy[4] + 0.18 * RES)
                    else:
                        enemy[4] = max(-3.5 * RES, enemy[4] - 0.18 * RES)
                    enemy[0] = enemy[0] + enemy[4]
                    enemy[1] = enemy[1] + current_enemy_speed * 1.7

                if enemy[1] > 20 * RES:
                    bullet_y = enemy[1] + enemy_sprites[enemy[2]][0].get_height() // 2
                    # Each shot is held if it would seal off the player's last
                    # reachable corridor, so independent swarm fire never walls
                    # the player in (aimed pressure is otherwise preserved).
                    if enemy[2] == 1 and random.randint(1, enemy_fire_roll + 40) == 1:
                        aim_x = player_x - enemy[0]
                        aim_y = player_y - bullet_y
                        aim_distance = max(1, math.hypot(aim_x, aim_y))
                        shot = [enemy[0], bullet_y, aim_x / aim_distance * current_enemy_bullet_speed, aim_y / aim_distance * current_enemy_bullet_speed, 0]
                        if not corridor_blocked_if_added(shot):
                            enemy_bullets.append(shot)
                    elif enemy[2] == 2 and random.randint(1, enemy_fire_roll) == 1:
                        left = [enemy[0], bullet_y, -1.5 * RES, current_enemy_bullet_speed, 0]
                        right = [enemy[0], bullet_y, 1.5 * RES, current_enemy_bullet_speed, 0]
                        if not corridor_blocked_if_added(left):
                            enemy_bullets.append(left)
                            enemy_bullets.append(right)
                    elif enemy[2] == 0 and enemy[6] == 0 and random.randint(1, enemy_fire_roll) == 1:
                        bullet_x_speed = random.choice([-3, -2, -1, 0, 1, 2, 3]) * RES
                        shot = [enemy[0], bullet_y, bullet_x_speed, current_enemy_bullet_speed, 0]
                        if not corridor_blocked_if_added(shot):
                            enemy_bullets.append(shot)
                if enemy[1] < SCREEN_HEIGHT + 40 * RES and -60 * RES < enemy[0] < SCREEN_WIDTH + 60 * RES:
                    new_enemies.append(enemy)
            enemies = new_enemies

            new_enemy_bullets = []
            for bullet in enemy_bullets:
                bullet[0] = bullet[0] + bullet[2]
                bullet[1] = bullet[1] + bullet[3]
                if -20 * RES < bullet[0] < SCREEN_WIDTH + 20 * RES and bullet[1] < SCREEN_HEIGHT + 20 * RES:
                    new_enemy_bullets.append(bullet)
            enemy_bullets = new_enemy_bullets

            # Engine exhaust trail — a continuous pixel plume behind the ship
            # for a sense of thrust. Emitted downward; particle gravity carries
            # it away and it fades from bright to dark over its short life.
            trail_color = powerup_colors.get(active_weapon, (255, 150, 30))
            trail_dark = mix_color(trail_color, (20, 16, 30), 0.6)
            trail_origin_y = player_y + player_sprite.get_height() // 2 - 2 * RES
            for _ in range(2):
                particles.append([
                    player_x + random.uniform(-3 * RES, 3 * RES),
                    trail_origin_y,
                    random.uniform(-0.5 * RES, 0.5 * RES),
                    random.uniform(1.8 * RES, 3.4 * RES),
                    random.randint(9, 15),
                    trail_color,
                    random.randint(1, 2 * RES),
                    trail_dark,
                ])

            new_particles = []
            for particle in particles:
                particle[0] = particle[0] + particle[2]
                particle[1] = particle[1] + particle[3]
                particle[3] = particle[3] + 0.12 * RES
                particle[4] = particle[4] - 1
                if particle[4] > 0:
                    new_particles.append(particle)
            particles = new_particles

            new_explosions = []
            for explosion in explosions:
                explosion[2] = explosion[2] + 1
                if explosion[2] < 21:
                    new_explosions.append(explosion)
            explosions = new_explosions

            new_shockwaves = []
            for shockwave in shockwaves:
                shockwave[2] = shockwave[2] + 7 * RES
                if shockwave[2] < shockwave[3]:
                    new_shockwaves.append(shockwave)
            shockwaves = new_shockwaves

            new_score_popups = []
            for popup in score_popups:
                popup[1] = popup[1] + random.uniform(-0.2 * RES, 0.2 * RES)
                popup[2] = popup[2] + popup[3]
                popup[4] = popup[4] - 1
                if popup[4] > 0:
                    new_score_popups.append(popup)
            score_popups = new_score_popups

            surviving_lasers = []
            for laser in lasers:
                laser_width = (12 if laser[4] == "heavy" else 4) * RES
                laser_rect = pygame.Rect(laser[0] - laser_width // 2, laser[1], laser_width, 18 * RES)
                hit_something = False

                surviving_enemies = []
                for enemy in enemies:
                    enemy_rect = hitbox_rect(enemy[0], enemy[1], ENEMY_HITBOXES[enemy[2]])
                    if laser_rect.colliderect(enemy_rect):
                        hit_something = True
                        enemy[3] = enemy[3] - get_laser_damage(laser)
                        if enemy[3] <= 0:
                            base_points = enemy_kill_points[enemy[2]]
                            if laser[4] == "heavy":
                                base_points = int(base_points * 1.5)
                            points = register_kill(enemy[0], enemy[1], base_points)
                            score = score + points
                            stage_score = stage_score + base_points
                            enemy_hit_sound.play()
                            add_explosion(enemy[0], enemy[1], "large" if enemy[2] == 2 else "small")
                            add_particles(enemy[0], enemy[1], powerup_colors.get(laser[4], (255, 220, 60)), 24, 4, 32, 4)
                            add_particles(enemy[0], enemy[1], (255, 130, 55), 10, 5, 24, 3)
                            add_shockwave(enemy[0], enemy[1], 34 * RES, powerup_colors.get(laser[4], (255, 220, 60)))
                            add_score_popup("+" + str(points), enemy[0], enemy[1] - 12 * RES, powerup_colors.get(laser[4], (255, 255, 255)))
                            screen_shake_timer = max(screen_shake_timer, 6)
                            screen_shake_strength = max(screen_shake_strength, 3 * RES)
                        else:
                            add_particles(enemy[0], enemy[1], powerup_colors.get(laser[4], (255, 220, 60)), 6, 2, 12, 2)
                            enemy[7] = 4
                            surviving_enemies.append(enemy)
                    else:
                        surviving_enemies.append(enemy)
                enemies = surviving_enemies

                if boss is not None and "dying" not in boss:
                    boss_rect = hitbox_rect(boss["x"], boss["y"], BOSS_HITBOX_LASER)
                    if laser_rect.colliderect(boss_rect):
                        hit_something = True
                        damage_boss(laser)
                        if boss["hp"] <= 0:
                            boss["dying"] = 75
                            hitstop_timer = max(hitstop_timer, 14)
                            add_shockwave(boss["x"], boss["y"], 160 * RES, (255, 210, 90))

                if not hit_something or laser[4] == "heavy":
                    surviving_lasers.append(laser)
            lasers = surviving_lasers

            player_rect = hitbox_rect(player_x, player_y, PLAYER_HITBOX)

            surviving_powerups = []
            for powerup in powerups:
                powerup_rect = pygame.Rect(powerup[0] - 15 * RES, powerup[1] - 15 * RES, 30 * RES, 30 * RES)
                if player_rect.colliderect(powerup_rect):
                    active_weapon = powerup[2]
                    weapon_timer = weapon_duration
                    fire_timer = current_fire_delay
                    special_move_weapon = active_weapon
                    special_move_timer = special_move_duration
                    powerup_collect_sound.play()
                    add_particles(powerup[0], powerup[1], powerup_colors[active_weapon], 28, 4, 36, 4)
                    add_score_popup(active_weapon.upper(), powerup[0], powerup[1] - 18 * RES, powerup_colors[active_weapon])
                    screen_shake_timer = max(screen_shake_timer, 8)
                    screen_shake_strength = max(screen_shake_strength, 4 * RES)
                else:
                    surviving_powerups.append(powerup)
            powerups = surviving_powerups

            surviving_enemies = []
            for enemy in enemies:
                enemy_rect = hitbox_rect(enemy[0], enemy[1], ENEMY_HITBOXES[enemy[2]])
                if player_rect.colliderect(enemy_rect):
                    damage_player()
                    add_particles(enemy[0], enemy[1], (255, 120, 60), 20, 5, 28, 4)
                    add_explosion(enemy[0], enemy[1], "small")
                else:
                    surviving_enemies.append(enemy)
            enemies = surviving_enemies

            if boss is not None and "dying" not in boss:
                boss_rect = hitbox_rect(boss["x"], boss["y"], BOSS_HITBOX_BODY)
                if player_rect.colliderect(boss_rect):
                    damage_player()
                    add_particles(player_x, player_y, (255, 100, 120), 24, 5, 28, 4)

            graze_rect = player_rect.inflate(34 * RES, 34 * RES)
            surviving_enemy_bullets = []
            for bullet in enemy_bullets:
                bullet_rect = pygame.Rect(bullet[0] - 3 * RES, bullet[1], 6 * RES, 14 * RES)
                if player_rect.colliderect(bullet_rect):
                    damage_player()
                    add_particles(bullet[0], bullet[1], (255, 90, 120), 12, 4, 24, 3)
                else:
                    if bullet[4] == 0 and player_hit_timer == 0 and graze_rect.colliderect(bullet_rect):
                        bullet[4] = 1
                        graze_count_this_run = graze_count_this_run + 1
                        score = score + 2 * score_multiplier
                        combo_timer = max(combo_timer, 90)
                        if graze_count_this_run % 3 == 0:
                            bump_combo()
                        graze_pulse_timer = 6
                        add_particles(bullet[0], bullet[1], (120, 230, 255), 4, 2, 14, 2)
                        if graze_popup_cooldown == 0:
                            add_score_popup("GRAZE +" + str(2 * score_multiplier), player_x, player_y - 44 * RES, (120, 230, 255))
                            graze_sound.play()
                            graze_popup_cooldown = 20
                    surviving_enemy_bullets.append(bullet)
            enemy_bullets = surviving_enemy_bullets

            if lives <= 0: # 0 because we start with 10 lives so 10 trials for the whole game
                running = False

            new_lasers = []
            for laser in lasers:
                laser[0] = laser[0] + laser[2]
                laser[1] = laser[1] + laser[3]
                if -20 * RES < laser[0] < SCREEN_WIDTH + 20 * RES and laser[1] > -30 * RES:
                    new_lasers.append(laser)
            lasers = new_lasers

            keys = pygame.key.get_pressed()
            frame_scale = seconds_passed * 60
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_velocity_x = player_velocity_x - player_acceleration * frame_scale
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_velocity_x = player_velocity_x + player_acceleration * frame_scale
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                player_velocity_y = player_velocity_y - player_acceleration * frame_scale
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                player_velocity_y = player_velocity_y + player_acceleration * frame_scale

            if keys[pygame.K_q]:
                radial_speed_ly_per_second = radial_speed_ly_per_second - 260 * seconds_passed
            if keys[pygame.K_e]:
                radial_speed_ly_per_second = radial_speed_ly_per_second + 260 * seconds_passed
            if keys[pygame.K_r]:
                radial_speed_ly_per_second = 0
            if keys[pygame.K_z]:
                orbit_speed_degrees_per_second = orbit_speed_degrees_per_second - 80 * seconds_passed
            if keys[pygame.K_x]:
                orbit_speed_degrees_per_second = orbit_speed_degrees_per_second + 80 * seconds_passed
            if keys[pygame.K_c]:
                orbit_speed_degrees_per_second = 0

            radial_speed_ly_per_second = max(-1200, min(1200, radial_speed_ly_per_second))
            if galaxy_distance < 1 and radial_speed_ly_per_second < 0:
                radial_speed_ly_per_second = max(radial_speed_ly_per_second, -get_close_center_speed_limit(galaxy_distance))
            orbit_speed_degrees_per_second = max(-180, min(180, orbit_speed_degrees_per_second))
            galaxy_distance = galaxy_distance + radial_speed_ly_per_second * seconds_passed
            galaxy_distance = max(minimum_black_hole_distance, min(max_galaxy_distance, galaxy_distance))
            if galaxy_distance <= minimum_black_hole_distance and radial_speed_ly_per_second < 0:
                black_hole_crash = True
                screen_shake_timer = 35
                screen_shake_strength = 14 * RES
                running = False
            orbit_angle = orbit_angle + math.radians(orbit_speed_degrees_per_second) * seconds_passed

            current_player_max_speed = player_max_speed * get_engine_multiplier()
            player_velocity_x = max(-current_player_max_speed, min(current_player_max_speed, player_velocity_x))
            player_velocity_y = max(-current_player_max_speed, min(current_player_max_speed, player_velocity_y))
            player_x = player_x + player_velocity_x * seconds_passed
            player_y = player_y + player_velocity_y * seconds_passed
            player_velocity_x = player_velocity_x * (player_friction ** frame_scale)
            player_velocity_y = player_velocity_y * (player_friction ** frame_scale)

            player_half_width = player_sprite.get_width() // 2
            player_half_height = player_sprite.get_height() // 2
            if player_x < player_half_width:
                player_x = player_half_width
                player_velocity_x = 0
            if player_x > SCREEN_WIDTH - player_half_width:
                player_x = SCREEN_WIDTH - player_half_width
                player_velocity_x = 0
            if player_y < 90:
                player_y = 90
                player_velocity_y = 0
            if player_y > SCREEN_HEIGHT - player_half_height:
                player_y = SCREEN_HEIGHT - player_half_height
                player_velocity_y = 0

        # --- DRAW ---
        draw_stage_background(current_stage)
        world_offset_x = 0
        world_offset_y = 0
        if screen_shake_timer > 0 and not paused:
            world_offset_x = random.randint(-screen_shake_strength, screen_shake_strength)
            world_offset_y = random.randint(-screen_shake_strength, screen_shake_strength)

        draw_star_layers(world_offset_x, world_offset_y)

        frame_tick = pygame.time.get_ticks()
        bolt_frame = (frame_tick // 66) % 2
        for laser in lasers:
            if laser[4] == "spread" and laser[2] != 0:
                bolt_sprite = spread_bolt_sprites[1 if laser[2] > 0 else -1][bolt_frame]
            else:
                bolt_sprite = bolt_sprites[laser[4]][bolt_frame]
            bolt_rect = bolt_sprite.get_rect(center=(laser[0] + world_offset_x, laser[1] + world_offset_y))
            screen.blit(bolt_sprite, bolt_rect)
            blit_glow(laser[0] + world_offset_x, laser[1] - 6 * RES + world_offset_y, bolt_colors[laser[4]], 16)

        orb_sprite = enemy_bullet_frames[(frame_tick // 100) % 2]
        for bullet in enemy_bullets:
            orb_rect = orb_sprite.get_rect(center=(bullet[0] + world_offset_x, bullet[1] + world_offset_y))
            screen.blit(orb_sprite, orb_rect)
            blit_glow(bullet[0] + world_offset_x, bullet[1] + world_offset_y, (255, 60, 90), 13)

        for enemy in enemies:
            enemy_frame = (enemy[5] // 8) % 2
            enemy_sprite = enemy_sprites[enemy[2]][enemy_frame]
            enemy_rect = enemy_sprite.get_rect(center=(enemy[0] + world_offset_x, enemy[1] + world_offset_y))
            screen.blit(enemy_sprite, enemy_rect)
            if enemy[2] == 3 and enemy[5] % 16 < 8:
                screen.blit(enemy_flash_sprites[enemy_frame], enemy_rect)
            if enemy[7] > 0:
                screen.blit(enemy_hit_flash_sprites[enemy[2]][enemy_frame], enemy_rect)

        draw_boss()

        for explosion in explosions:
            frame_set = explosion_frames[explosion[3]]
            frame = frame_set[min(len(frame_set) - 1, explosion[2] // 3)]
            screen.blit(frame, frame.get_rect(center=(explosion[0] + world_offset_x, explosion[1] + world_offset_y)))
            if explosion[2] < 9:
                blit_glow(explosion[0] + world_offset_x, explosion[1] + world_offset_y, (255, 160, 60), 40)

        spin_frame = (frame_tick // 120) % 4
        for powerup in powerups:
            blit_glow(powerup[0] + world_offset_x, powerup[1] + world_offset_y, powerup_colors[powerup[2]], 29)
            powerup_sprite = powerup_sprites[powerup[2]][spin_frame]
            powerup_rect = powerup_sprite.get_rect(center=(powerup[0] + world_offset_x, powerup[1] + world_offset_y))
            screen.blit(powerup_sprite, powerup_rect)

        for particle in particles:
            particle_color = particle[5] if particle[4] >= 8 else particle[7]
            screen.fill(
                particle_color,
                (
                    int(particle[0] + world_offset_x - particle[6]),
                    int(particle[1] + world_offset_y - particle[6]),
                    particle[6] * 2,
                    particle[6] * 2,
                ),
            )

        for shockwave in shockwaves:
            shockwave_radius = max(3 * RES, int(shockwave[2] // (3 * RES)) * (3 * RES))
            shockwave_center = (int(shockwave[0] + world_offset_x), int(shockwave[1] + world_offset_y))
            pygame.draw.circle(screen, shockwave[4], shockwave_center, shockwave_radius, 3 * RES)
            if shockwave_radius > 6 * RES:
                pygame.draw.circle(screen, (255, 255, 255), shockwave_center, shockwave_radius - 4 * RES, RES)

        if muzzle_flash_timer > 0:
            nose_x = int(player_x + world_offset_x)
            nose_y = int(player_y - player_sprite.get_height() // 2 + world_offset_y)
            flash_frames = muzzle_flash_sprites.get(active_weapon, muzzle_flash_sprites["single"])
            flash_sprite = flash_frames[max(0, 3 - muzzle_flash_timer)]
            screen.blit(flash_sprite, flash_sprite.get_rect(center=(nose_x, nose_y)))
            blit_glow(nose_x, nose_y, bolt_colors.get(active_weapon, (255, 230, 120)), 19)

        flame_pair = flame_frames.get(active_weapon, flame_frames["single"])
        flame_sprite = flame_pair[(frame_tick // 66) % 2]
        flame_x = int(player_x + world_offset_x)
        flame_y = int(player_y + player_sprite.get_height() // 2 - 4 * RES + world_offset_y)
        screen.blit(flame_sprite, flame_sprite.get_rect(midtop=(flame_x, flame_y)))
        blit_glow(flame_x, flame_y + 16, powerup_colors.get(active_weapon, (255, 150, 30)), 19)

        if player_velocity_x < -70:
            current_player_sprite = player_sprite_left
            current_player_flash = player_flash_left
        elif player_velocity_x > 70:
            current_player_sprite = player_sprite_right
            current_player_flash = player_flash_right
        else:
            current_player_sprite = player_sprite
            current_player_flash = player_flash_center
        player_rect = current_player_sprite.get_rect(center=(player_x + world_offset_x, player_y + world_offset_y))
        screen.blit(current_player_sprite, player_rect)
        if player_hit_timer > 0 and player_hit_timer % 6 < 3:
            screen.blit(current_player_flash, player_rect)
        if graze_pulse_timer > 0:
            pygame.draw.circle(screen, (120, 230, 255), (int(player_x + world_offset_x), int(player_y + world_offset_y)), 30 * RES, 2 * RES)

        for popup in score_popups:
            popup_shadow = font.render(popup[0], True, TEXT_SHADOW_COLOR)
            popup_text = font.render(popup[0], True, popup[5])
            popup_rect = popup_text.get_rect(center=(popup[1] + world_offset_x, popup[2] + world_offset_y))
            screen.blit(popup_shadow, (popup_rect.x + 2 * RES, popup_rect.y + 2 * RES))
            screen.blit(popup_text, popup_rect)

        draw_special_move(special_move_weapon, special_move_timer)

        draw_hurt_vignette(max(0, (player_hit_timer - 30) / 15))

        # Translucent backing panel so the left stat cluster reads as a unit
        # against the busy starfield, matching the right-side HUD panels.
        hud_panel_h = ((102 if active_weapon != "single" else 72) + 32) * RES
        hud_panel = pygame.Surface((198 * RES, hud_panel_h), pygame.SRCALPHA)
        hud_panel.fill((10, 14, 26, 145))
        screen.blit(hud_panel, (4 * RES, 4 * RES))
        hud_panel_rect = pygame.Rect(4 * RES, 4 * RES, 198 * RES, hud_panel_h)
        pygame.draw.rect(screen, (60, 80, 120), hud_panel_rect, 2 * RES)
        for corner_x in (hud_panel_rect.left, hud_panel_rect.right - 3 * RES):
            for corner_y in (hud_panel_rect.top, hud_panel_rect.bottom - 3 * RES):
                pygame.draw.rect(screen, (60, 80, 120), (corner_x, corner_y, 3 * RES, 3 * RES))

        score_color = (255, 230, 80) if high_score_beaten else (255, 255, 255)
        draw_text_shadowed(font, "Score: " + str(score), score_color, topleft=(10 * RES, 10 * RES))
        draw_text_shadowed(font, "Lives: " + str(lives), (255, 255, 255), topleft=(10 * RES, 40 * RES))
        if lives <= 5 and pygame.time.get_ticks() % 700 < 450:
            draw_text_shadowed(font, "DANGER", (255, 80, 80), topleft=(130 * RES, 40 * RES))
        if combo_count >= 2:
            combo_color = combo_tier_colors[score_multiplier]
            draw_text_shadowed(medium_32_pixel_font, "x" + str(score_multiplier), combo_color, topleft=(205 * RES, 6 * RES))
            draw_text_shadowed(small_font, str(combo_count) + " CHAIN", (220, 235, 255), topleft=(262 * RES, 16 * RES))
            draw_segment_bar(screen, 205 * RES, 42 * RES, 110 * RES, 8 * RES, combo_timer / combo_window, combo_color, segments=10)
        if boss is None and boss_warning_timer == 0 and 600 <= wave_timer < 760 and combo_count >= 5:
            if pygame.time.get_ticks() % 800 < 500:
                draw_text_shadowed(small_font, "HOLD THE COMBO", (255, 220, 80), topleft=(205 * RES, 56 * RES))
        if active_weapon != "single":
            seconds_left = weapon_timer // 60 + 1
            draw_text_shadowed(font, "Weapon: " + active_weapon.upper() + " " + str(seconds_left), powerup_colors[active_weapon], topleft=(10 * RES, 70 * RES))

        shield_y = (102 if active_weapon != "single" else 72) * RES
        shield_fill = 0 if shield_max <= 0 else max(0, min(1, shield_current / shield_max))
        draw_segment_bar(screen, 10 * RES, shield_y, 180 * RES, 12 * RES, shield_fill, (70, 220, 255), segments=12)
        draw_text_shadowed(small_font, "Shield " + str(int(shield_current)) + "/" + str(int(shield_max)), (210, 235, 255), topleft=(10 * RES, shield_y + 16 * RES))

        draw_stage_hud()
        draw_galaxy_progress(galaxy_distance, radial_speed_ly_per_second, orbit_speed_degrees_per_second, orbit_angle)

        if boss_warning_timer > 0:
            if boss_warning_timer % 30 < 18:
                draw_text_shadowed(medium_32_pixel_font, "!! " + stages[current_stage]["boss"].upper() + " APPROACHING !!", (255, 80, 80), center=(SCREEN_WIDTH // 2, 230 * RES))

        if lives <= 5:
            vignette_overlay.set_alpha(int(160 + 95 * math.sin(pygame.time.get_ticks() / 150)))
            screen.blit(vignette_overlay, (0, 0))

        if milestone_flash_timer > 0:
            milestone_overlay.set_alpha(int(60 * milestone_flash_timer / 8))
            screen.blit(milestone_overlay, (0, 0))

        if upgrade_screen:
            draw_upgrade_screen()

        if paused:
            screen.blit(pause_overlay, (0, 0))
            draw_text_shadowed(medium_32_pixel_font, "PAUSED", (235, 245, 255), center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        if not upgrade_screen:
            draw_pause_play_button(paused)

        if CRT_OVERLAY:
            screen.blit(scanline_overlay, (0, 0))

        if SHOT_MODE and not paused and not upgrade_screen:
            SHOT_FRAME = SHOT_FRAME + 1
            if SHOT_FRAME % 9 == 0:
                fire_player_weapon()
            if SHOT_FRAME in SHOT_CAPTURE_FRAMES:
                Path("loop_shots").mkdir(exist_ok=True)
                pygame.image.save(screen, "loop_shots/frame_%04d.png" % SHOT_FRAME)
            if SHOT_FRAME > SHOT_CAPTURE_FRAMES[-1]:
                running = False
                app_running = False

        present()
        clock.tick(TARGET_FPS)

    music_channel.stop()
    if score > high_score:
        high_score = score
        high_score_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_high_score(high_score, high_score_time)
    lifetime_stats["total_runs"] = lifetime_stats["total_runs"] + 1
    lifetime_stats["best_combo"] = max(lifetime_stats["best_combo"], best_combo_this_run)
    save_stats()

    game_over = True
    show_replay_prompt = True
    yes_button = pygame.Rect(160 * RES, 270 * RES, 200 * RES, 80 * RES)
    no_button = pygame.Rect(440 * RES, 270 * RES, 200 * RES, 80 * RES)

    while game_over:
        if SHOT_MODE:
            game_over = False
            app_running = False
            break
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = False
                app_running = False
            if event.type == pygame.VIDEORESIZE:
                handle_window_resize(event.size)
            if show_replay_prompt and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_y, pygame.K_r):
                    reset_run()
                    game_over = False
                if event.key == pygame.K_n:
                    show_replay_prompt = False
            if show_replay_prompt and event.type == pygame.MOUSEBUTTONDOWN:
                if yes_button.collidepoint(to_logical(event.pos)):
                    reset_run()
                    game_over = False
                if no_button.collidepoint(to_logical(event.pos)):
                    show_replay_prompt = False

        screen.blit(game_over_background, (0, 0))
        draw_star_layers()

        if show_replay_prompt:
            mouse_pos = logical_mouse_pos()
            yes_color = (70, 190, 110) if yes_button.collidepoint(mouse_pos) else (40, 140, 80)
            no_color = (190, 70, 70) if no_button.collidepoint(mouse_pos) else (140, 40, 40)

            draw_pixel_panel(screen, yes_button, (255, 255, 255), fill=yes_color)
            draw_pixel_panel(screen, no_button, (255, 255, 255), fill=no_color)

            draw_text_shadowed(medium_32_pixel_font, "YES", (255, 255, 255), center=yes_button.center)
            draw_text_shadowed(medium_32_pixel_font, "NO", (255, 255, 255), center=no_button.center)

            draw_text_shadowed(medium_32_pixel_font, "FLY AGAIN?", (235, 245, 255), center=(SCREEN_WIDTH // 2, 200 * RES))
            draw_text_shadowed(small_font, "R / Y - FLY AGAIN    N - QUIT", (180, 200, 230), center=(SCREEN_WIDTH // 2, 390 * RES))
        else:
            if black_hole_crash:
                end_title = "BLACK HOLE CRASH"
            elif mission_complete:
                end_title = "MISSION COMPLETE"
            else:
                end_title = "GAME OVER"
            draw_text_shadowed(big_64pixel_font, end_title, (255, 50, 50), topleft=(100 * RES, 100 * RES))

            stats_panel = pygame.Rect(80 * RES, 280 * RES, 640 * RES, 274 * RES)
            draw_pixel_panel(screen, stats_panel, HUD_BORDER)

            draw_text_shadowed(medium_32_pixel_font, "FINAL SCORE: " + str(score), (255, 255, 255), topleft=(100 * RES, 300 * RES))
            draw_text_shadowed(medium_32_pixel_font, "HIGH SCORE: " + str(high_score), (255, 220, 80), topleft=(100 * RES, 350 * RES))
            draw_text_shadowed(font, "BEST SCORE TIME: " + high_score_time, (200, 220, 255), topleft=(100 * RES, 395 * RES))
            draw_text_shadowed(font, "BEST COMBO: " + str(best_combo_this_run) + " CHAIN (x" + str(get_combo_multiplier(best_combo_this_run)) + ")    GRAZES: " + str(graze_count_this_run), (120, 230, 255), topleft=(100 * RES, 430 * RES))
            draw_text_shadowed(font, "ALL-TIME: " + str(lifetime_stats["total_kills"]) + " KILLS / " + str(lifetime_stats["total_boss_kills"]) + " BOSSES / " + str(lifetime_stats["total_runs"]) + " RUNS", (200, 220, 255), topleft=(100 * RES, 460 * RES))
            draw_text_shadowed(medium_32_pixel_font, "CLOSE THE WINDOW TO EXIT", (150, 150, 150), topleft=(100 * RES, 510 * RES))

        if CRT_OVERLAY:
            screen.blit(scanline_overlay, (0, 0))

        present()
        clock.tick(TARGET_FPS)
pygame.quit()
