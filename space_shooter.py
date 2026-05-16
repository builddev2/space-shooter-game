import pygame
import random
import math
import os
import sys
from array import array
from datetime import datetime
from pathlib import Path

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


pygame.init()
BASE_DIR = Path(__file__).resolve().parent
HIGH_SCORE_FILE = BASE_DIR / "highscore.txt"
HIGH_SCORE_TIME_FILE = BASE_DIR / "highscore_time.txt"
pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1)
pygame.mixer.set_reserved(1)
weapon_sounds = {
    "single": pygame.mixer.Sound(str(BASE_DIR / "laser.wav")),
    "double": pygame.mixer.Sound(str(BASE_DIR / "laser_double.wav")),
    "spread": pygame.mixer.Sound(str(BASE_DIR / "laser_spread.wav")),
    "rapid": pygame.mixer.Sound(str(BASE_DIR / "laser_rapid.wav")),
    "heavy": pygame.mixer.Sound(str(BASE_DIR / "laser_heavy.wav")),
}
for sound in weapon_sounds.values():
    sound.set_volume(0.4)
enemy_hit_sound = pygame.mixer.Sound(str(BASE_DIR / "enemy_hit.wav"))
powerup_collect_sound = pygame.mixer.Sound(str(BASE_DIR / "powerup_collect.wav"))
player_hit_sound = pygame.mixer.Sound(str(BASE_DIR / "player_hit.wav"))
enemy_hit_sound.set_volume(0.35)
powerup_collect_sound.set_volume(0.45)
player_hit_sound.set_volume(0.45)
music_channel = pygame.mixer.Channel(0)
music_channel.set_volume(0.32)
current_music_name = ""
stage_music = [
    make_music_loop([(220, 0.16), (330, 0.16), (440, 0.16), (330, 0.16), (247, 0.16), (370, 0.16), (494, 0.16), (370, 0.16)], 0.30),
    make_music_loop([(196, 0.14), (294, 0.14), (392, 0.14), (494, 0.14), (392, 0.14), (294, 0.14), (262, 0.14), (330, 0.14)], 0.28),
    make_music_loop([(165, 0.18), (247, 0.12), (330, 0.18), (247, 0.12), (185, 0.18), (277, 0.12), (370, 0.18), (277, 0.12)], 0.31),
    make_music_loop([(147, 0.15), (220, 0.15), (294, 0.15), (440, 0.15), (330, 0.15), (247, 0.15), (196, 0.15), (294, 0.15)], 0.29),
    make_music_loop([(110, 0.20), (165, 0.10), (220, 0.20), (330, 0.10), (147, 0.20), (220, 0.10), (294, 0.20), (440, 0.10)], 0.34),
]
boss_music = [
    make_music_loop([(110, 0.10), (0, 0.04), (220, 0.10), (0, 0.04), (165, 0.10), (0, 0.04), (247, 0.10), (0, 0.04)], 0.38),
    make_music_loop([(130, 0.08), (196, 0.08), (262, 0.08), (330, 0.08), (262, 0.08), (196, 0.08), (130, 0.08), (98, 0.08)], 0.36),
    make_music_loop([(175, 0.12), (233, 0.06), (350, 0.12), (466, 0.06), (208, 0.12), (277, 0.06), (415, 0.12), (554, 0.06)], 0.34),
    make_music_loop([(82, 0.16), (123, 0.08), (165, 0.16), (247, 0.08), (98, 0.16), (147, 0.08), (196, 0.16), (294, 0.08)], 0.40),
    make_music_loop([(73, 0.09), (110, 0.09), (147, 0.09), (220, 0.09), (294, 0.09), (220, 0.09), (147, 0.09), (110, 0.09)], 0.42),
]

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TARGET_FPS = 60
DISPLAY_FLAGS = pygame.SCALED | pygame.DOUBLEBUF

try:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DISPLAY_FLAGS, vsync=1)
except TypeError:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DISPLAY_FLAGS)
pygame.display.set_caption("Space Shooter")
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN])
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
    with open(HIGH_SCORE_FILE, "w") as f:
        f.write(str(value))
    with open(HIGH_SCORE_TIME_FILE, "w") as f:
        f.write(score_time)


def restart_game():
    pygame.quit()
    os.execv(sys.executable, [sys.executable] + sys.argv)


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
    progress_rect = pygame.Rect(465, 12, 300, 22)
    distance_remaining = max(0, min(1, distance / max_galaxy_distance))
    progress_color = get_distance_color(distance)
    pygame.draw.rect(screen, (12, 16, 26), progress_rect, border_radius=8)
    pygame.draw.rect(screen, (95, 105, 125), progress_rect, 2, border_radius=8)
    pygame.draw.rect(
        screen,
        progress_color,
        (progress_rect.x + 3, progress_rect.y + 3, int((progress_rect.width - 6) * distance_remaining), progress_rect.height - 6),
        border_radius=6,
    )

    end_label = small_font.render("GAME OVER", True, (255, 120, 120))
    far_label = small_font.render("50,000 LY", True, (145, 165, 205))
    screen.blit(end_label, (progress_rect.x, progress_rect.y - 16))
    screen.blit(far_label, far_label.get_rect(topright=(progress_rect.right, progress_rect.y - 16)))

    distance_text = small_font.render("TO CENTER: " + format_distance(distance), True, (235, 240, 255))
    screen.blit(distance_text, (progress_rect.x, progress_rect.y + 28))

    map_rect = pygame.Rect(620, 95, 160, 185)
    pygame.draw.rect(screen, (8, 11, 22), map_rect, border_radius=8)
    pygame.draw.rect(screen, (75, 90, 120), map_rect, 2, border_radius=8)
    map_center = (map_rect.centerx, map_rect.y + 92)
    map_radius = 58

    for radius in [18, 36, 54]:
        pygame.draw.circle(screen, (28, 35, 55), map_center, radius, 1)

    pygame.draw.circle(screen, (245, 225, 130), (map_center[0], map_center[1] - map_radius), 5)
    sun_text = small_font.render("SUN N", True, (245, 225, 130))
    screen.blit(sun_text, (map_center[0] - 22, map_center[1] - map_radius - 20))
    reference_time_text = small_font.render("2026-05-15 16:30", True, (145, 165, 205))
    screen.blit(reference_time_text, (map_rect.x + 9, map_rect.bottom - 22))

    pygame.draw.circle(screen, (255, 255, 255), map_center, 8)
    pygame.draw.circle(screen, (0, 0, 0), map_center, 5)

    ship_radius = max(10, int(map_radius * max(0, min(1, distance / 28000))))
    ship_x = map_center[0] + math.cos(orbit_angle) * ship_radius
    ship_y = map_center[1] + math.sin(orbit_angle) * ship_radius
    pygame.draw.line(screen, (70, 95, 125), map_center, (ship_x, ship_y), 1)
    pygame.draw.circle(screen, progress_color, (int(ship_x), int(ship_y)), 5)

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
        line_rect = line_text.get_rect(right=SCREEN_WIDTH - 16, bottom=SCREEN_HEIGHT - 58 + i * 20)
        screen.blit(line_text, line_rect)


def draw_pause_play_button(paused):
    button_text = "PLAY" if paused else "PAUSE"
    mouse_pos = pygame.mouse.get_pos()
    button_color = (55, 145, 220) if pause_button.collidepoint(mouse_pos) else (28, 78, 135)
    if paused:
        button_color = (55, 175, 110) if pause_button.collidepoint(mouse_pos) else (35, 115, 75)

    pygame.draw.rect(screen, button_color, pause_button, border_radius=8)
    pygame.draw.rect(screen, (230, 240, 255), pause_button, 2, border_radius=8)
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
    screen.fill((5, 8, 18))
    for star in stars:
        pygame.draw.circle(screen, star[4], (int(star[0]), int(star[1])), star[3])

    title = medium_32_pixel_font.render("CHOOSE SHIP UPGRADE", True, (235, 245, 255))
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 48)))

    ship_preview = pygame.transform.scale(player_sprite, (player_sprite.get_width() * 2, player_sprite.get_height() * 2))
    ship_rect = ship_preview.get_rect(center=(SCREEN_WIDTH // 2, 190))
    screen.blit(ship_preview, ship_rect)
    pygame.draw.circle(screen, (60, 220, 255), ship_rect.center, 86, 2)
    pygame.draw.circle(screen, (255, 220, 80), (ship_rect.centerx, ship_rect.bottom - 8), 13)

    upgrade_cards = [
        ("guns", "GUNS", "+20% damage", "Level " + str(gun_upgrade_level)),
        ("shields", "SHIELDS", "+20 lives", "Level " + str(shield_upgrade_level)),
        ("engine", "ENGINE", "+15% move speed", "Level " + str(engine_upgrade_level)),
    ]
    mouse_pos = pygame.mouse.get_pos()
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

        pygame.draw.rect(screen, card_color, rect, border_radius=8)
        pygame.draw.rect(screen, accent, rect, 3, border_radius=8)
        card_title = font.render(title_text, True, accent)
        card_bonus = small_font.render(bonus_text, True, (235, 245, 255))
        card_level = small_font.render(level_text, True, (175, 195, 225))
        key_text = small_font.render("Press " + str(i + 1), True, (255, 255, 255))
        screen.blit(card_title, card_title.get_rect(center=(rect.centerx, rect.y + 34)))
        screen.blit(card_bonus, card_bonus.get_rect(center=(rect.centerx, rect.y + 70)))
        screen.blit(card_level, card_level.get_rect(center=(rect.centerx, rect.y + 98)))
        screen.blit(key_text, key_text.get_rect(center=(rect.centerx, rect.bottom - 24)))


def make_pixel_sprite(rows, colors, scale):
    width = max(len(row) for row in rows)
    height = len(rows)
    sprite = pygame.Surface((width, height), pygame.SRCALPHA)

    for y, row in enumerate(rows):
        for x, pixel in enumerate(row):
            if pixel != ".":
                sprite.set_at((x, y), colors[pixel])

    return pygame.transform.scale(sprite, (width * scale, height * scale)).convert_alpha()


def fire_player_weapon():
    nose_y = player_y - player_sprite.get_height() // 2

    if active_weapon == "double":
        lasers.append([player_x - 10, nose_y, 0, -laser_speed, "double"])
        lasers.append([player_x + 10, nose_y, 0, -laser_speed, "double"])
    elif active_weapon == "spread":
        lasers.append([player_x, nose_y, 0, -laser_speed, "spread"])
        lasers.append([player_x - 8, nose_y, -3, -laser_speed, "spread"])
        lasers.append([player_x + 8, nose_y, 3, -laser_speed, "spread"])
    elif active_weapon == "heavy":
        lasers.append([player_x, nose_y, 0, -laser_speed - 2, "heavy"])
    else:
        lasers.append([player_x, nose_y, 0, -laser_speed, active_weapon])

    weapon_sounds[active_weapon].play()


def add_particles(x, y, color, count, speed, life, size):
    for i in range(count):
        particles.append([
            x,
            y,
            random.uniform(-speed, speed),
            random.uniform(-speed, speed),
            random.randint(life // 2, life),
            color,
            random.randint(1, size),
        ])


def add_score_popup(text, x, y, color):
    score_popups.append([text, x, y, -1.2, 45, color])


def damage_player():
    global lives, player_hit_timer, screen_shake_timer, screen_shake_strength, shield_current

    if player_hit_timer > 0:
        return

    if shield_current > 0:
        shield_current = max(0, shield_current - 35)
    else:
        lives = lives - 1

    player_hit_timer = 45
    screen_shake_timer = 18
    screen_shake_strength = 8
    player_hit_sound.play()
    add_particles(player_x, player_y, (255, 70, 70), 18, 5, 30, 4)


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
    for i in range(-220, SCREEN_WIDTH + 260, 70):
        x = i + int(progress * 260)
        pygame.draw.polygon(
            overlay,
            (color[0], color[1], color[2], stripe_alpha),
            [(x, 0), (x + 34, 0), (x - 190, SCREEN_HEIGHT), (x - 224, SCREEN_HEIGHT)],
        )

    art_x = int(SCREEN_WIDTH * 0.68)
    art_y = int(SCREEN_HEIGHT * 0.45)
    glow_alpha = int(135 * fade)
    pygame.draw.circle(overlay, (color[0], color[1], color[2], glow_alpha), (art_x, art_y), 118)

    if weapon == "double":
        pygame.draw.rect(overlay, (230, 250, 255, int(235 * fade)), (art_x - 52, art_y - 78, 22, 155), border_radius=4)
        pygame.draw.rect(overlay, (230, 250, 255, int(235 * fade)), (art_x + 30, art_y - 78, 22, 155), border_radius=4)
        pygame.draw.line(overlay, (*color, int(255 * fade)), (art_x - 41, art_y - 102), (art_x - 41, art_y - 188), 8)
        pygame.draw.line(overlay, (*color, int(255 * fade)), (art_x + 41, art_y - 102), (art_x + 41, art_y - 188), 8)
        pygame.draw.rect(overlay, (70, 95, 130, int(230 * fade)), (art_x - 70, art_y + 52, 140, 28), border_radius=6)
    elif weapon == "spread":
        for angle in [-32, 0, 32]:
            end_x = art_x + math.sin(math.radians(angle)) * 155
            end_y = art_y - math.cos(math.radians(angle)) * 155
            pygame.draw.line(overlay, (*color, int(250 * fade)), (art_x, art_y + 58), (end_x, end_y), 9)
            pygame.draw.line(overlay, (255, 255, 255, int(235 * fade)), (art_x, art_y + 58), (end_x, end_y), 3)
        pygame.draw.arc(overlay, (*color, int(230 * fade)), (art_x - 88, art_y - 22, 176, 120), math.radians(205), math.radians(335), 8)
    elif weapon == "rapid":
        pygame.draw.rect(overlay, (225, 245, 230, int(230 * fade)), (art_x - 74, art_y - 22, 150, 42), border_radius=8)
        for i in range(6):
            barrel_x = art_x - 55 + i * 22
            pygame.draw.rect(overlay, (*color, int(250 * fade)), (barrel_x, art_y - 82, 10, 78), border_radius=3)
            pygame.draw.line(overlay, (255, 255, 255, int(220 * fade)), (barrel_x + 5, art_y - 95), (barrel_x + 5, art_y - 160 - i * 7), 3)
    elif weapon == "heavy":
        pygame.draw.polygon(
            overlay,
            (235, 235, 255, int(235 * fade)),
            [(art_x - 36, art_y + 80), (art_x + 36, art_y + 80), (art_x + 58, art_y - 85), (art_x - 58, art_y - 85)],
        )
        pygame.draw.rect(overlay, (*color, int(255 * fade)), (art_x - 16, art_y - 175, 32, 165), border_radius=5)
        pygame.draw.circle(overlay, (255, 255, 255, int(245 * fade)), (art_x, art_y - 190), 22)
        pygame.draw.line(overlay, (*color, int(235 * fade)), (art_x, art_y - 212), (art_x, 20), 14)

    callout_text = special_font.render(move_name, True, color)
    callout_shadow = special_font.render(move_name, True, (255, 255, 255))
    text_x = 48
    text_y = int(390 - math.sin(progress * math.pi) * 14)
    overlay.blit(callout_shadow, (text_x + 3, text_y + 3))
    overlay.blit(callout_text, (text_x, text_y))

    subtitle = font.render("SPECIAL WEAPON ONLINE", True, (230, 240, 255))
    overlay.blit(subtitle, (text_x + 8, text_y + 68))
    screen.blit(overlay, (0, 0))


def spawn_boss():
    global boss, enemies, enemy_bullets, spawn_timer

    stage = stages[current_stage]
    boss = {
        "x": SCREEN_WIDTH // 2,
        "y": -70,
        "target_y": 118,
        "hp": stage["boss_hp"],
        "max_hp": stage["boss_hp"],
        "stage": current_stage,
        "timer": 0,
        "vx": 3 + current_stage,
    }
    enemies = []
    enemy_bullets = []
    spawn_timer = 0
    play_music("boss_" + str(current_stage), boss_music[current_stage])


def fire_boss_attack(active_boss):
    stage_index = active_boss["stage"]
    timer = active_boss["timer"]
    boss_x = active_boss["x"]
    boss_y = active_boss["y"]

    if stage_index == 0 and timer % 42 == 0:
        for x_speed in [-3, -1, 1, 3]:
            enemy_bullets.append([boss_x, boss_y + 55, x_speed, 4])
    elif stage_index == 1 and timer % 28 == 0:
        for angle in range(25, 156, 26):
            x_speed = math.cos(math.radians(angle)) * 3.2
            y_speed = math.sin(math.radians(angle)) * 3.2
            enemy_bullets.append([boss_x, boss_y + 20, x_speed, y_speed])
    elif stage_index == 2:
        if timer % 38 == 0:
            for offset in [-52, 52]:
                dx = player_x - (boss_x + offset)
                dy = player_y - boss_y
                distance = max(1, math.hypot(dx, dy))
                enemy_bullets.append([boss_x + offset, boss_y + 34, dx / distance * 4, dy / distance * 4])
        if timer % 95 == 0:
            for x_speed in [-4, -2, 0, 2, 4]:
                enemy_bullets.append([boss_x, boss_y + 60, x_speed, 5])
    elif stage_index == 3:
        if timer % 16 == 0:
            lane_x = 90 + ((timer * 19) % (SCREEN_WIDTH - 180))
            enemy_bullets.append([lane_x, boss_y + 44, 0, 5.5])
        if timer % 70 == 0:
            for offset in [-70, 70]:
                enemy_bullets.append([boss_x + offset, boss_y + 40, -offset / 22, 4.2])
    elif stage_index == 4:
        if timer % 11 == 0:
            angle = timer * 10
            for extra in [0, 180]:
                x_speed = math.cos(math.radians(angle + extra)) * 3.5
                y_speed = 2.8 + math.sin(math.radians(angle + extra)) * 1.2
                enemy_bullets.append([boss_x, boss_y + 25, x_speed, y_speed])
        if timer % 75 == 0:
            for x_speed in [-5, -2.5, 0, 2.5, 5]:
                enemy_bullets.append([boss_x, boss_y + 58, x_speed, 4.8])


def update_boss():
    global boss

    if boss is None:
        return

    boss["timer"] = boss["timer"] + 1
    stage_index = boss["stage"]

    if boss["y"] < boss["target_y"]:
        boss["y"] = boss["y"] + 2
    elif stage_index == 0:
        boss["x"] = SCREEN_WIDTH // 2 + math.sin(boss["timer"] / 55) * 165
    elif stage_index == 1:
        boss["x"] = SCREEN_WIDTH // 2 + math.sin(boss["timer"] / 38) * 210
        boss["y"] = boss["target_y"] + math.sin(boss["timer"] / 52) * 24
    elif stage_index == 2:
        boss["x"] = SCREEN_WIDTH // 2 + math.sin(boss["timer"] / 70) * 120
    elif stage_index == 3:
        boss["x"] = boss["x"] + boss["vx"]
        if boss["x"] < 145 or boss["x"] > SCREEN_WIDTH - 145:
            boss["vx"] = boss["vx"] * -1
    elif stage_index == 4:
        boss["x"] = SCREEN_WIDTH // 2 + math.cos(boss["timer"] / 58) * 145
        boss["y"] = boss["target_y"] + math.sin(boss["timer"] / 45) * 34

    fire_boss_attack(boss)


def damage_boss(laser):
    global boss, score, stage_score, screen_shake_timer, screen_shake_strength

    damage = get_laser_damage(laser)
    boss["hp"] = boss["hp"] - damage
    score = score + 2
    stage_score = stage_score + 2
    enemy_hit_sound.play()
    add_particles(laser[0], laser[1], powerup_colors.get(laser[4], (255, 220, 60)), 8, 3, 18, 3)
    screen_shake_timer = max(screen_shake_timer, 4)
    screen_shake_strength = max(screen_shake_strength, 2)


def finish_boss():
    global boss, current_stage, stage_score, running, mission_complete, screen_shake_timer, screen_shake_strength, upgrade_screen
    global enemies, enemy_bullets, particles, score

    defeated_boss = stages[current_stage]["boss"]
    add_particles(boss["x"], boss["y"], (255, 210, 90), 80, 8, 60, 6)
    add_score_popup(defeated_boss + " DOWN", boss["x"], boss["y"], (255, 230, 120))
    score = score + 300 + current_stage * 100
    stage_score = 0
    current_stage = current_stage + 1
    boss = None
    enemies = []
    enemy_bullets = []
    screen_shake_timer = 28
    screen_shake_strength = 10

    if current_stage >= len(stages):
        mission_complete = True
        running = False
    else:
        upgrade_screen = True
        music_channel.stop()


def draw_stage_background(stage_index):
    base_color = stages[stage_index]["color"] if stage_index < len(stages) else (5, 5, 16)
    screen.fill(base_color)
    stripe_color = (
        min(255, base_color[0] + 18),
        min(255, base_color[1] + 18),
        min(255, base_color[2] + 26),
    )
    for y in range(-80, SCREEN_HEIGHT + 80, 120):
        offset = int((pygame.time.get_ticks() / 28 + stage_index * 45) % 120)
        pygame.draw.line(screen, stripe_color, (0, y + offset), (SCREEN_WIDTH, y + offset - 90), 1)


def draw_boss():
    if boss is None:
        return

    boss_sprite = boss_sprites[boss["stage"]]
    boss_rect = boss_sprite.get_rect(center=(boss["x"] + world_offset_x, boss["y"] + world_offset_y))
    screen.blit(boss_sprite, boss_rect)

    health_rect = pygame.Rect(170, 58, 460, 16)
    health_fill = max(0, boss["hp"] / boss["max_hp"])
    pygame.draw.rect(screen, (35, 10, 18), health_rect, border_radius=6)
    pygame.draw.rect(screen, (255, 80, 90), (health_rect.x, health_rect.y, int(health_rect.width * health_fill), health_rect.height), border_radius=6)
    pygame.draw.rect(screen, (255, 230, 230), health_rect, 2, border_radius=6)
    boss_text = small_font.render(stages[boss["stage"]]["boss"], True, (255, 230, 230))
    screen.blit(boss_text, boss_text.get_rect(center=(health_rect.centerx, health_rect.y - 10)))


def draw_stage_hud():
    stage = stages[current_stage] if current_stage < len(stages) else stages[-1]
    stage_text = small_font.render(stage["name"], True, (220, 235, 255))
    screen.blit(stage_text, (10, 130))
    if boss is None:
        progress_text = small_font.render("BOSS SIGNAL: " + str(min(stage_score, stage["goal"])) + "/" + str(stage["goal"]), True, (255, 220, 120))
        screen.blit(progress_text, (10, 150))
    else:
        fight_text = small_font.render("BOSS FIGHT", True, (255, 120, 120))
        screen.blit(fight_text, (10, 150))


player_sprite = make_pixel_sprite(
    [
        ".......W.......",
        "......WWW......",
        "......WCW......",
        ".....WCCCW.....",
        "....WCCCCCW....",
        "...WCCCCCCCW...",
        "..WCCCDCCCCCW..",
        ".WCCCDDDCCCCCW.",
        "WCCCDGGGDCCCCCW",
        "WCCCDGGGDCCCCCW",
        ".WCCCDDDCCCCCW.",
        "..WWCCCCCCCWW..",
        "....WAAAAAW....",
        "...WWAAAAAWW...",
        "...W..AAA..W...",
        "......AAA......",
    ],
    {
        "W": (235, 245, 255),
        "C": (40, 210, 235),
        "D": (18, 92, 170),
        "G": (95, 115, 145),
        "A": (255, 150, 30),
    },
    3,
)

enemy_sprites = [
    make_pixel_sprite(
        [
            "....RRRR....",
            "..RRMMMMRR..",
            ".RMMYYYYMMR.",
            "RMMYKKKKYMMR",
            "RMYKKGGKKYMR",
            "RMYKGGGGKYMR",
            ".RMYKKKKYMR.",
            "..RRYYYYRR..",
            "...RRAARR...",
            "....AAAA....",
        ],
        {
            "R": (210, 42, 62),
            "M": (92, 35, 115),
            "Y": (245, 198, 75),
            "K": (38, 30, 52),
            "G": (95, 240, 135),
            "A": (255, 118, 40),
        },
        3,
    ),
    make_pixel_sprite(
        [
            "....BBBB....",
            "..BBCCCCBB..",
            ".BCCWWWWCCB.",
            "BCCWPPPPWCCB",
            "BCWPPQQPPWCB",
            "BCWPPQQPPWCB",
            ".BCCWWWWCCB.",
            "..BBCCCCBB..",
            ".BB..AA..BB.",
            ".....AA.....",
        ],
        {
            "B": (45, 85, 215),
            "C": (62, 220, 245),
            "W": (235, 250, 255),
            "P": (80, 42, 130),
            "Q": (255, 60, 170),
            "A": (255, 126, 36),
        },
        3,
    ),
    make_pixel_sprite(
        [
            ".....SS.....",
            "...SSNNSS...",
            "..SNNVVNNS..",
            ".SNNVHHVNNS.",
            "SNNVHHHHVNNS",
            "SNNVHHHHVNNS",
            ".SNNVHHVNNS.",
            "..SSNVNSS..",
            "...SSLLSS...",
            "....LLLL....",
        ],
        {
            "S": (170, 175, 192),
            "N": (75, 78, 96),
            "V": (185, 55, 230),
            "H": (255, 78, 92),
            "L": (255, 164, 38),
        },
        3,
    ),
]

boss_sprites = [
    make_pixel_sprite(
        [
            ".......RRRRR.......",
            ".....RRMMMMMRR.....",
            "...RRMMYYYYYMMRR...",
            "..RMMYYKKKKKYYMMR..",
            ".RMMYKGGGGGGGKYMMR.",
            "RMMYKGGWWWWGGKYMMR",
            "RMMYKGWCCCCWGKYMMR",
            ".RMMYKGGWWGGKYMMR.",
            "..RRMMYKKKKKYMMRR..",
            "....RRRRAARRRR....",
            "......AAAAAAA......",
        ],
        {
            "R": (210, 48, 54),
            "M": (100, 35, 118),
            "Y": (240, 190, 70),
            "K": (30, 24, 42),
            "G": (80, 240, 140),
            "W": (235, 250, 255),
            "C": (70, 180, 255),
            "A": (255, 120, 35),
        },
        3,
    ),
    make_pixel_sprite(
        [
            ".......BBBBB.......",
            ".....BBCCCCCB......",
            "...BBCCWWWWWCCBB...",
            "..BCCWPPPPPPPWCCB..",
            ".BCCWPQQQQQQQPWCCB.",
            "BCCWPQRRRRRRQPWCCB",
            "BCCWPQRRRRRRQPWCCB",
            ".BCCWPQQQQQQQPWCCB.",
            "..BBCCWPPPPPWCCBB..",
            "....BBCCCCCCCBB....",
            "......BBBAABBB.....",
        ],
        {
            "B": (40, 85, 230),
            "C": (70, 220, 245),
            "W": (235, 250, 255),
            "P": (75, 40, 135),
            "Q": (255, 70, 180),
            "R": (255, 60, 60),
            "A": (255, 140, 40),
        },
        3,
    ),
    make_pixel_sprite(
        [
            "......SSSSSSS......",
            "....SSNNNNNNNSS....",
            "..SSNNVVVVVVVNNSS..",
            ".SNNVVHHHHHHHVVNNS.",
            "SNNVVHLLLLLLLHVVNNS",
            "SNNVVHLLWWWLLHVVNNS",
            "SNNVVHLLLLLLLHVVNNS",
            ".SNNVVHHHHHHHVVNNS.",
            "..SSNNVVVVVVVNNSS..",
            "....SSNNLLLNNSS....",
            "......LLLLLLL......",
        ],
        {
            "S": (185, 190, 205),
            "N": (65, 70, 90),
            "V": (175, 60, 230),
            "H": (255, 80, 95),
            "L": (255, 170, 45),
            "W": (235, 245, 255),
        },
        3,
    ),
    make_pixel_sprite(
        [
            ".......GGGGG.......",
            "....GGGDDDDDGGG....",
            "..GGDDOOOOOOODDGG..",
            ".GDDOOBBBBBBBOODDG.",
            "GDDOBBTTTTTTTBBODDG",
            "GDDOBBTWWWWWTTBODDG",
            "GDDOBBTTTTTTTBBODDG",
            ".GDDOOBBBBBBBOODDG.",
            "..GGDDOOOOOOODDGG..",
            "....GGGDDDDDGGG....",
            "......GGAAAAAG.....",
        ],
        {
            "G": (55, 210, 90),
            "D": (30, 85, 70),
            "O": (245, 190, 65),
            "B": (35, 38, 55),
            "T": (80, 255, 200),
            "W": (235, 250, 255),
            "A": (255, 135, 40),
        },
        3,
    ),
    make_pixel_sprite(
        [
            ".......PPPPP.......",
            "....PPPNNNNNPPP....",
            "..PPNNFFFFFFFNNPP..",
            ".PNNFFEEEEEEEFFNNP.",
            "PNNFFEKKKKKKKEFFNNP",
            "PNNFFEKWWWWWKEFFNNP",
            "PNNFFEKKKKKKKEFFNNP",
            ".PNNFFEEEEEEEFFNNP.",
            "..PPNNFFFFFFFNNPP..",
            "....PPPNNNNNPPP....",
            "......PPAAAAAPP....",
        ],
        {
            "P": (195, 70, 255),
            "N": (45, 38, 72),
            "F": (255, 90, 190),
            "E": (255, 230, 85),
            "K": (20, 20, 34),
            "W": (245, 250, 255),
            "A": (255, 105, 45),
        },
        3,
    ),
]

stages = [
    {"name": "Stage 1: Sky Patrol", "boss": "Carrier Fang", "goal": 120, "spawn_delay": 62, "speed": 0, "fire_roll": 170, "color": (5, 8, 24), "boss_hp": 180},
    {"name": "Stage 2: Crimson Orbit", "boss": "Red Wheel", "goal": 170, "spawn_delay": 54, "speed": 1, "fire_roll": 145, "color": (18, 5, 18), "boss_hp": 230},
    {"name": "Stage 3: Prism Gate", "boss": "Twin Prism", "goal": 230, "spawn_delay": 48, "speed": 1, "fire_roll": 125, "color": (6, 18, 26), "boss_hp": 285},
    {"name": "Stage 4: Green Monsoon", "boss": "Iron Monsoon", "goal": 300, "spawn_delay": 42, "speed": 2, "fire_roll": 105, "color": (5, 20, 14), "boss_hp": 350},
    {"name": "Stage 5: Event Horizon", "boss": "Singularity Crown", "goal": 380, "spawn_delay": 36, "speed": 3, "fire_roll": 85, "color": (12, 4, 22), "boss_hp": 430},
]

player_x = 400
player_y = 520
player_velocity_x = 0
player_velocity_y = 0
player_acceleration = 36
player_friction = 0.86
player_max_speed = 420

galaxy_distance = 26000.0
minimum_black_hole_distance = CRASH_DISTANCE_KILOMETERS / LIGHT_YEAR_KILOMETERS
max_galaxy_distance = 50000
radial_speed_ly_per_second = -120.0
orbit_speed_degrees_per_second = 35.0
orbit_angle = -math.pi / 2
black_hole_crash = False

stars = []
for i in range(140):
    star_x = random.randint(0, SCREEN_WIDTH)
    star_y = random.randint(0, SCREEN_HEIGHT)
    star_speed = random.choice([1, 1, 2, 3])
    star_size = 2 if star_speed == 3 else 1
    star_color = random.choice([(160, 175, 210), (210, 225, 255), (255, 255, 255)])
    stars.append([star_x, star_y, star_speed, star_size, star_color])

lasers = []
laser_speed = 10
fire_timer = 0
fire_delay = 12

powerups = []
powerup_speed = 2
powerup_timer = 0
powerup_spawn_delay = 420
active_weapon = "single"
weapon_timer = 0
weapon_duration = 600
weapon_types = ["double", "spread", "rapid", "heavy"]
powerup_colors = {
    "double": (60, 220, 255),
    "spread": (255, 210, 70),
    "rapid": (95, 255, 120),
    "heavy": (255, 95, 210),
}
powerup_labels = {
    "double": "D",
    "spread": "S",
    "rapid": "R",
    "heavy": "H",
}
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
score_popups = []
screen_shake_timer = 0
screen_shake_strength = 0
player_hit_timer = 0

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

font = pygame.font.SysFont("monospace", 24)
small_font = pygame.font.SysFont("monospace", 16)
big_64pixel_font = pygame.font.SysFont("monospace", 64)
medium_32_pixel_font = pygame.font.SysFont("monospace", 32)
special_font = pygame.font.SysFont("monospace", 54, bold=True)
paused = False
pause_button = pygame.Rect(350, 10, 100, 34)
upgrade_buttons = {
    "guns": pygame.Rect(70, 400, 200, 145),
    "shields": pygame.Rect(300, 400, 200, 145),
    "engine": pygame.Rect(530, 400, 200, 145),
}
play_music("stage_0", stage_music[0])
while running:

    # --- CHECK / EVENTS ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if upgrade_screen and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                apply_upgrade("guns")
            elif event.key == pygame.K_2:
                apply_upgrade("shields")
            elif event.key == pygame.K_3:
                apply_upgrade("engine")
        elif upgrade_screen and event.type == pygame.MOUSEBUTTONDOWN:
            for upgrade_name, button_rect in upgrade_buttons.items():
                if button_rect.collidepoint(event.pos):
                    apply_upgrade(upgrade_name)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            toggle_pause()
        elif event.type == pygame.MOUSEBUTTONDOWN and pause_button.collidepoint(event.pos):
            toggle_pause()

    # --- UPDATE ---
    if not paused and not upgrade_screen:
        seconds_passed = clock.get_time() / 1000
        stage = stages[current_stage]
        current_spawn_delay = stage["spawn_delay"]
        enemies_per_spawn = 1 + min(current_stage // 2, 2)
        current_enemy_speed = enemy_speed + stage["speed"]
        current_enemy_bullet_speed = enemy_bullet_speed + min(current_stage, 3)
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

        current_fire_delay = 5 if active_weapon == "rapid" else fire_delay

        fire_timer = fire_timer + 1
        if fire_timer >= current_fire_delay:
            fire_player_weapon()
            fire_timer = 0

        for star in stars:
            star[1] = star[1] + star[2]
            if star[1] > SCREEN_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, SCREEN_WIDTH)

        powerup_timer = powerup_timer + 1
        if powerup_timer >= powerup_spawn_delay:
            powerup_x = random.randint(40, SCREEN_WIDTH - 40)
            powerup_type = random.choice(weapon_types)
            powerups.append([powerup_x, -25, powerup_type])
            powerup_timer = 0

        new_powerups = []
        for powerup in powerups:
            powerup[1] = powerup[1] + powerup_speed
            if powerup[1] < SCREEN_HEIGHT + 30:
                new_powerups.append(powerup)
        powerups = new_powerups

        if boss is None and stage_score >= stage["goal"]:
            spawn_boss()
        elif boss is None:
            spawn_timer = spawn_timer + 1
            if spawn_timer >= current_spawn_delay:
                for i in range(enemies_per_spawn):
                    enemy_x = random.randint(30, SCREEN_WIDTH - 30)
                    enemy_y = -30 - i * 45
                    enemy_type = random.randint(0, len(enemy_sprites) - 1)
                    enemy_hp = 5 + current_stage * 2
                    enemies.append([enemy_x, enemy_y, enemy_type, enemy_hp])
                spawn_timer = 0

        update_boss()

        new_enemies = []
        for enemy in enemies:
            enemy[1] = enemy[1] + current_enemy_speed
            if enemy[1] > 20 and random.randint(1, enemy_fire_roll) == 1:
                enemy_sprite = enemy_sprites[enemy[2]]
                bullet_y = enemy[1] + enemy_sprite.get_height() // 2
                bullet_x_speed = random.choice([-3, -2, -1, 0, 1, 2, 3])
                enemy_bullets.append([enemy[0], bullet_y, bullet_x_speed, current_enemy_bullet_speed])
            if enemy[1] < SCREEN_HEIGHT + 40:
                new_enemies.append(enemy)
        enemies = new_enemies

        new_enemy_bullets = []
        for bullet in enemy_bullets:
            bullet[0] = bullet[0] + bullet[2]
            bullet[1] = bullet[1] + bullet[3]
            if -20 < bullet[0] < SCREEN_WIDTH + 20 and bullet[1] < SCREEN_HEIGHT + 20:
                new_enemy_bullets.append(bullet)
        enemy_bullets = new_enemy_bullets

        new_particles = []
        for particle in particles:
            particle[0] = particle[0] + particle[2]
            particle[1] = particle[1] + particle[3]
            particle[3] = particle[3] + 0.12
            particle[4] = particle[4] - 1
            if particle[4] > 0:
                new_particles.append(particle)
        particles = new_particles

        new_score_popups = []
        for popup in score_popups:
            popup[1] = popup[1] + random.uniform(-0.2, 0.2)
            popup[2] = popup[2] + popup[3]
            popup[4] = popup[4] - 1
            if popup[4] > 0:
                new_score_popups.append(popup)
        score_popups = new_score_popups

        surviving_lasers = []
        for laser in lasers:
            laser_width = 12 if laser[4] == "heavy" else 4
            laser_rect = pygame.Rect(laser[0] - laser_width // 2, laser[1], laser_width, 18)
            hit_something = False

            surviving_enemies = []
            for enemy in enemies:
                enemy_sprite = enemy_sprites[enemy[2]]
                enemy_rect = enemy_sprite.get_rect(center=(enemy[0], enemy[1])).inflate(-8, -8)
                if laser_rect.colliderect(enemy_rect):
                    hit_something = True
                    enemy[3] = enemy[3] - get_laser_damage(laser)
                    if enemy[3] <= 0:
                        points = 15 if laser[4] == "heavy" else 10
                        score = score + points
                        stage_score = stage_score + points
                        enemy_hit_sound.play()
                        add_particles(enemy[0], enemy[1], powerup_colors.get(laser[4], (255, 220, 60)), 24, 4, 32, 4)
                        add_particles(enemy[0], enemy[1], (255, 130, 55), 10, 5, 24, 3)
                        add_score_popup("+" + str(points), enemy[0], enemy[1] - 12, powerup_colors.get(laser[4], (255, 255, 255)))
                        screen_shake_timer = max(screen_shake_timer, 6)
                        screen_shake_strength = max(screen_shake_strength, 3)
                    else:
                        add_particles(enemy[0], enemy[1], powerup_colors.get(laser[4], (255, 220, 60)), 6, 2, 12, 2)
                        surviving_enemies.append(enemy)
                else:
                    surviving_enemies.append(enemy)
            enemies = surviving_enemies

            if boss is not None:
                boss_sprite = boss_sprites[boss["stage"]]
                boss_rect = boss_sprite.get_rect(center=(boss["x"], boss["y"])).inflate(-14, -10)
                if laser_rect.colliderect(boss_rect):
                    hit_something = True
                    damage_boss(laser)
                    if boss is not None and boss["hp"] <= 0:
                        finish_boss()

            if not hit_something or laser[4] == "heavy":
                surviving_lasers.append(laser)
        lasers = surviving_lasers

        player_rect = player_sprite.get_rect(center=(player_x, player_y)).inflate(-10, -6)

        surviving_powerups = []
        for powerup in powerups:
            powerup_rect = pygame.Rect(powerup[0] - 15, powerup[1] - 15, 30, 30)
            if player_rect.colliderect(powerup_rect):
                active_weapon = powerup[2]
                weapon_timer = weapon_duration
                fire_timer = current_fire_delay
                special_move_weapon = active_weapon
                special_move_timer = special_move_duration
                powerup_collect_sound.play()
                add_particles(powerup[0], powerup[1], powerup_colors[active_weapon], 28, 4, 36, 4)
                add_score_popup(active_weapon.upper(), powerup[0], powerup[1] - 18, powerup_colors[active_weapon])
                screen_shake_timer = max(screen_shake_timer, 8)
                screen_shake_strength = max(screen_shake_strength, 4)
            else:
                surviving_powerups.append(powerup)
        powerups = surviving_powerups

        surviving_enemies = []
        for enemy in enemies:
            enemy_sprite = enemy_sprites[enemy[2]]
            enemy_rect = enemy_sprite.get_rect(center=(enemy[0], enemy[1])).inflate(-8, -8)
            if player_rect.colliderect(enemy_rect):
                damage_player()
                add_particles(enemy[0], enemy[1], (255, 120, 60), 20, 5, 28, 4)
            else:
                surviving_enemies.append(enemy)
        enemies = surviving_enemies

        if boss is not None:
            boss_sprite = boss_sprites[boss["stage"]]
            boss_rect = boss_sprite.get_rect(center=(boss["x"], boss["y"])).inflate(-20, -12)
            if player_rect.colliderect(boss_rect):
                damage_player()
                add_particles(player_x, player_y, (255, 100, 120), 24, 5, 28, 4)

        surviving_enemy_bullets = []
        for bullet in enemy_bullets:
            bullet_rect = pygame.Rect(bullet[0] - 3, bullet[1], 6, 14)
            if player_rect.colliderect(bullet_rect):
                damage_player()
                add_particles(bullet[0], bullet[1], (255, 90, 120), 12, 4, 24, 3)
            else:
                surviving_enemy_bullets.append(bullet)
        enemy_bullets = surviving_enemy_bullets

        if lives <= 0: # 0 because we start with 10 lives so 10 trials for the whole game
            running = False

        new_lasers = []
        for laser in lasers:
            laser[0] = laser[0] + laser[2]
            laser[1] = laser[1] + laser[3]
            if -20 < laser[0] < SCREEN_WIDTH + 20 and laser[1] > -30:
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
            screen_shake_strength = 14
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

    for star in stars:
        pygame.draw.circle(screen, star[4], (int(star[0] + world_offset_x), int(star[1] + world_offset_y)), star[3])

    for laser in lasers:
        laser_color = powerup_colors.get(laser[4], (255, 255, 0))
        laser_width = 9 if laser[4] == "heavy" else 5
        laser_start = (laser[0] + world_offset_x, laser[1] + world_offset_y)
        laser_end = (laser[0] + laser[2] * 4 + world_offset_x, laser[1] - 18 + world_offset_y)
        pygame.draw.line(screen, (255, 255, 255), laser_start, laser_end, laser_width + 3)
        pygame.draw.line(screen, laser_color, laser_start, laser_end, laser_width)

    for bullet in enemy_bullets:
        bullet_start = (bullet[0] + world_offset_x, bullet[1] + world_offset_y)
        bullet_end = (bullet[0] + bullet[2] * 3 + world_offset_x, bullet[1] + 14 + world_offset_y)
        pygame.draw.line(screen, (255, 60, 90), bullet_start, bullet_end, 8)
        pygame.draw.line(screen, (255, 190, 210), bullet_start, bullet_end, 3)

    for enemy in enemies:
        enemy_sprite = enemy_sprites[enemy[2]]
        enemy_rect = enemy_sprite.get_rect(center=(enemy[0] + world_offset_x, enemy[1] + world_offset_y))
        screen.blit(enemy_sprite, enemy_rect)

    draw_boss()

    for powerup in powerups:
        powerup_color = powerup_colors[powerup[2]]
        pulse = 16 + int(math.sin(pygame.time.get_ticks() / 120) * 3)
        powerup_points = [
            (powerup[0] + world_offset_x, powerup[1] - pulse + world_offset_y),
            (powerup[0] + pulse + world_offset_x, powerup[1] + world_offset_y),
            (powerup[0] + world_offset_x, powerup[1] + pulse + world_offset_y),
            (powerup[0] - pulse + world_offset_x, powerup[1] + world_offset_y),
        ]
        pygame.draw.polygon(screen, powerup_color, powerup_points)
        pygame.draw.polygon(screen, (255, 255, 255), powerup_points, 2)
        powerup_text = font.render(powerup_labels[powerup[2]], True, (10, 10, 20))
        powerup_text_rect = powerup_text.get_rect(center=(powerup[0] + world_offset_x, powerup[1] + world_offset_y))
        screen.blit(powerup_text, powerup_text_rect)

    for particle in particles:
        pygame.draw.circle(
            screen,
            particle[5],
            (int(particle[0] + world_offset_x), int(particle[1] + world_offset_y)),
            particle[6],
        )

    engine_y = player_y + player_sprite.get_height() // 2 - 5
    engine_color = powerup_colors.get(active_weapon, (255, 150, 30))
    pygame.draw.circle(screen, engine_color, (int(player_x + world_offset_x), int(engine_y + world_offset_y)), 8)
    pygame.draw.circle(screen, (255, 230, 120), (int(player_x + world_offset_x), int(engine_y + world_offset_y)), 4)

    player_rect = player_sprite.get_rect(center=(player_x + world_offset_x, player_y + world_offset_y))
    screen.blit(player_sprite, player_rect)
    if player_hit_timer > 0 and player_hit_timer % 6 < 3:
        flash_surface = player_sprite.copy()
        flash_surface.fill((255, 80, 80, 140), special_flags=pygame.BLEND_RGBA_ADD)
        screen.blit(flash_surface, player_rect)

    for popup in score_popups:
        popup_text = font.render(popup[0], True, popup[5])
        popup_rect = popup_text.get_rect(center=(popup[1] + world_offset_x, popup[2] + world_offset_y))
        screen.blit(popup_text, popup_rect)

    draw_special_move(special_move_weapon, special_move_timer)

    score_text = font.render("Score: " + str(score), True, (255, 255, 255))
    screen.blit(score_text, (10, 10))
    lives_text = font.render("Lives: " + str(lives), True, (255, 255, 255))
    screen.blit(lives_text, (10, 40))
    if active_weapon != "single":
        seconds_left = weapon_timer // 60 + 1
        weapon_text = font.render("Weapon: " + active_weapon.upper() + " " + str(seconds_left), True, powerup_colors[active_weapon])
        screen.blit(weapon_text, (10, 70))

    shield_y = 102 if active_weapon != "single" else 72
    shield_rect = pygame.Rect(10, shield_y, 180, 12)
    shield_fill = 0 if shield_max <= 0 else max(0, min(1, shield_current / shield_max))
    pygame.draw.rect(screen, (10, 20, 34), shield_rect, border_radius=5)
    pygame.draw.rect(screen, (70, 220, 255), (shield_rect.x, shield_rect.y, int(shield_rect.width * shield_fill), shield_rect.height), border_radius=5)
    pygame.draw.rect(screen, (190, 230, 255), shield_rect, 1, border_radius=5)
    shield_text = small_font.render("Shield " + str(int(shield_current)) + "/" + str(int(shield_max)), True, (210, 235, 255))
    screen.blit(shield_text, (10, shield_y + 14))

    draw_stage_hud()
    draw_galaxy_progress(galaxy_distance, radial_speed_ly_per_second, orbit_speed_degrees_per_second, orbit_angle)

    if upgrade_screen:
        draw_upgrade_screen()

    if paused:
        pause_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pause_overlay.fill((0, 0, 0, 110))
        screen.blit(pause_overlay, (0, 0))
        paused_text = medium_32_pixel_font.render("PAUSED", True, (235, 245, 255))
        screen.blit(paused_text, paused_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

    if not upgrade_screen:
        draw_pause_play_button(paused)

    pygame.display.flip()
    clock.tick(TARGET_FPS)

music_channel.stop()
if score > high_score:
    high_score = score
    high_score_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_high_score(high_score, high_score_time)

game_over = True
show_replay_prompt = True
yes_button = pygame.Rect(160, 270, 200, 80)
no_button = pygame.Rect(440, 270, 200, 80)

while game_over:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = False
        if show_replay_prompt and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_y:
                restart_game()
            if event.key == pygame.K_n:
                show_replay_prompt = False
        if show_replay_prompt and event.type == pygame.MOUSEBUTTONDOWN:
            if yes_button.collidepoint(event.pos):
                restart_game()
            if no_button.collidepoint(event.pos):
                show_replay_prompt = False

    screen.fill((0, 0, 0))

    if show_replay_prompt:
        mouse_pos = pygame.mouse.get_pos()
        yes_color = (70, 190, 110) if yes_button.collidepoint(mouse_pos) else (40, 140, 80)
        no_color = (190, 70, 70) if no_button.collidepoint(mouse_pos) else (140, 40, 40)

        pygame.draw.rect(screen, yes_color, yes_button, border_radius=10)
        pygame.draw.rect(screen, no_color, no_button, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), yes_button, 3, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), no_button, 3, border_radius=10)

        yes_text = medium_32_pixel_font.render("YES", True, (255, 255, 255))
        no_text = medium_32_pixel_font.render("NO", True, (255, 255, 255))
        screen.blit(yes_text, yes_text.get_rect(center=yes_button.center))
        screen.blit(no_text, no_text.get_rect(center=no_button.center))
    else:
        if black_hole_crash:
            end_title = "BLACK HOLE CRASH"
        elif mission_complete:
            end_title = "MISSION COMPLETE"
        else:
            end_title = "GAME OVER"
        over_text = big_64pixel_font.render(end_title, True, (255, 50, 50))
        screen.blit(over_text, (100, 100))

        final_text = medium_32_pixel_font.render("FINAL SCORE: " + str(score), True, (255, 255, 255))
        screen.blit(final_text, (100, 300))

        high_score_text = medium_32_pixel_font.render("HIGH SCORE: " + str(high_score), True, (255, 220, 80))
        screen.blit(high_score_text, (100, 350))

        high_score_time_text = font.render("BEST SCORE TIME: " + high_score_time, True, (200, 220, 255))
        screen.blit(high_score_time_text, (100, 395))

        quit_text = medium_32_pixel_font.render("CLOSE THE WINDOW TO EXIT", True, (150, 150, 150))
        screen.blit(quit_text, (100, 500))

    pygame.display.flip()
    clock.tick(TARGET_FPS)
pygame.quit()
