import pygame
import random
import math
from pathlib import Path

pygame.init()
BASE_DIR = Path(__file__).resolve().parent
pygame.mixer.init()
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
pygame.mixer.music.load(str(BASE_DIR / "background_music.ogg"))
pygame.mixer.music.set_volume(0.25)
pygame.mixer.music.play(-1)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()
running = True


def make_pixel_sprite(rows, colors, scale):
    width = max(len(row) for row in rows)
    height = len(rows)
    sprite = pygame.Surface((width, height), pygame.SRCALPHA)

    for y, row in enumerate(rows):
        for x, pixel in enumerate(row):
            if pixel != ".":
                sprite.set_at((x, y), colors[pixel])

    return pygame.transform.scale(sprite, (width * scale, height * scale))


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
    global lives, player_hit_timer, screen_shake_timer, screen_shake_strength

    if player_hit_timer > 0:
        return

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

player_x = 400
player_y = 520
player_velocity_x = 0
player_velocity_y = 0
player_acceleration = 0.6
player_friction = 0.86
player_max_speed = 7

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
lives = 20

font = pygame.font.SysFont("monospace", 24)
big_64pixel_font = pygame.font.SysFont("monospace", 64)
medium_32_pixel_font = pygame.font.SysFont("monospace", 32)
special_font = pygame.font.SysFont("monospace", 54, bold=True)
while running:

    # --- CHECK / EVENTS ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- UPDATE ---
    difficulty_level = min(score // 100, 10)
    current_spawn_delay = max(20, 65 - difficulty_level * 5)
    enemies_per_spawn = 1 + min(difficulty_level // 3, 3)
    current_enemy_speed = enemy_speed + min(difficulty_level // 2, 4)
    current_enemy_bullet_speed = enemy_bullet_speed + min(difficulty_level // 3, 3)
    enemy_fire_roll = max(35, 160 - difficulty_level * 15)

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

    spawn_timer = spawn_timer + 1
    if spawn_timer >= current_spawn_delay:
        for i in range(enemies_per_spawn):
            enemy_x = random.randint(30, SCREEN_WIDTH - 30)
            enemy_y = -30 - i * 45
            enemy_type = random.randint(0, len(enemy_sprites) - 1)
            enemies.append([enemy_x, enemy_y, enemy_type])
        spawn_timer = 0

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
                points = 15 if laser[4] == "heavy" else 10
                score = score + points
                enemy_hit_sound.play()
                add_particles(enemy[0], enemy[1], powerup_colors.get(laser[4], (255, 220, 60)), 24, 4, 32, 4)
                add_particles(enemy[0], enemy[1], (255, 130, 55), 10, 5, 24, 3)
                add_score_popup("+" + str(points), enemy[0], enemy[1] - 12, powerup_colors.get(laser[4], (255, 255, 255)))
                screen_shake_timer = max(screen_shake_timer, 6)
                screen_shake_strength = max(screen_shake_strength, 3)
            else:
                surviving_enemies.append(enemy)
        enemies = surviving_enemies

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
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player_velocity_x = player_velocity_x - player_acceleration
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player_velocity_x = player_velocity_x + player_acceleration
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        player_velocity_y = player_velocity_y - player_acceleration
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        player_velocity_y = player_velocity_y + player_acceleration

    player_velocity_x = max(-player_max_speed, min(player_max_speed, player_velocity_x))
    player_velocity_y = max(-player_max_speed, min(player_max_speed, player_velocity_y))
    player_x = player_x + player_velocity_x
    player_y = player_y + player_velocity_y
    player_velocity_x = player_velocity_x * player_friction
    player_velocity_y = player_velocity_y * player_friction

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
    screen.fill((5, 5, 16))
    world_offset_x = 0
    world_offset_y = 0
    if screen_shake_timer > 0:
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
    pygame.display.flip()
    clock.tick(60)

pygame.mixer.music.stop()
game_over = True
while game_over:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = False

    screen.fill((0, 0, 0))

    over_text = big_64pixel_font.render("GAME OVER", True, (255, 50, 50))
    screen.blit(over_text, (100, 100))

    final_text = medium_32_pixel_font.render("FINAL SCORE: " + str(score), True, (255, 255, 255))
    screen.blit(final_text, (100, 300))

    quit_text = medium_32_pixel_font.render("CLOSE THE WINDOW TO EXIT", True, (150, 150, 150))
    screen.blit(quit_text, (100, 500))

    pygame.display.flip()
    clock.tick(30)
pygame.quit()
