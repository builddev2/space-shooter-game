import pygame
import random
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
player_speed = 5

stars = []
for i in range(100):
    star_x = random.randint(0, SCREEN_WIDTH)
    star_y = random.randint(0, SCREEN_HEIGHT)
    stars.append([star_x, star_y])

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

enemies = []
enemy_speed = 1
spawn_timer = 0

enemy_bullets = []
enemy_bullet_speed = 4

score = 0
lives = 20

font = pygame.font.SysFont("monospace", 24)
big_64pixel_font = pygame.font.SysFont("monospace", 64)
medium_32_pixel_font = pygame.font.SysFont("monospace", 32)
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

    current_fire_delay = 5 if active_weapon == "rapid" else fire_delay

    fire_timer = fire_timer + 1
    if fire_timer >= current_fire_delay:
        fire_player_weapon()
        fire_timer = 0

    for star in stars:
        star[1] = star[1] + 1
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
                score = score + 10
            else:
                surviving_enemies.append(enemy)
        enemies = surviving_enemies

        if not hit_something:
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
        else:
            surviving_powerups.append(powerup)
    powerups = surviving_powerups

    surviving_enemies = []
    for enemy in enemies:
        enemy_sprite = enemy_sprites[enemy[2]]
        enemy_rect = enemy_sprite.get_rect(center=(enemy[0], enemy[1])).inflate(-8, -8)
        if player_rect.colliderect(enemy_rect):
            lives = lives - 1
        else:
            surviving_enemies.append(enemy)
    enemies = surviving_enemies

    surviving_enemy_bullets = []
    for bullet in enemy_bullets:
        bullet_rect = pygame.Rect(bullet[0] - 3, bullet[1], 6, 14)
        if player_rect.colliderect(bullet_rect):
            lives = lives - 1
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
    if keys[pygame.K_LEFT]:
        player_x = player_x - player_speed
    if keys[pygame.K_RIGHT]:
        player_x = player_x + player_speed

    player_half_width = player_sprite.get_width() // 2
    if player_x < player_half_width:
        player_x = player_half_width
    if player_x > SCREEN_WIDTH - player_half_width:
        player_x = SCREEN_WIDTH - player_half_width

    # --- DRAW ---
    screen.fill((5, 5, 16))

    for star in stars:
        pygame.draw.circle(screen, (220, 230, 255), (star[0], star[1]), 1)

    for laser in lasers:
        laser_color = powerup_colors.get(laser[4], (255, 255, 0))
        laser_width = 9 if laser[4] == "heavy" else 5
        laser_end_x = laser[0] + laser[2] * 4
        laser_end_y = laser[1] - 18
        pygame.draw.line(screen, (255, 255, 255), (laser[0], laser[1]), (laser_end_x, laser_end_y), laser_width + 3)
        pygame.draw.line(screen, laser_color, (laser[0], laser[1]), (laser_end_x, laser_end_y), laser_width)

    for bullet in enemy_bullets:
        bullet_end_x = bullet[0] + bullet[2] * 3
        bullet_end_y = bullet[1] + 14
        pygame.draw.line(screen, (255, 60, 90), (bullet[0], bullet[1]), (bullet_end_x, bullet_end_y), 8)
        pygame.draw.line(screen, (255, 190, 210), (bullet[0], bullet[1]), (bullet_end_x, bullet_end_y), 3)

    for enemy in enemies:
        enemy_sprite = enemy_sprites[enemy[2]]
        enemy_rect = enemy_sprite.get_rect(center=(enemy[0], enemy[1]))
        screen.blit(enemy_sprite, enemy_rect)

    for powerup in powerups:
        powerup_color = powerup_colors[powerup[2]]
        powerup_points = [
            (powerup[0], powerup[1] - 16),
            (powerup[0] + 16, powerup[1]),
            (powerup[0], powerup[1] + 16),
            (powerup[0] - 16, powerup[1]),
        ]
        pygame.draw.polygon(screen, powerup_color, powerup_points)
        pygame.draw.polygon(screen, (255, 255, 255), powerup_points, 2)
        powerup_text = font.render(powerup_labels[powerup[2]], True, (10, 10, 20))
        powerup_text_rect = powerup_text.get_rect(center=(powerup[0], powerup[1]))
        screen.blit(powerup_text, powerup_text_rect)

    player_rect = player_sprite.get_rect(center=(player_x, player_y))
    screen.blit(player_sprite, player_rect)
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
