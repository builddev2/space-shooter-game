# Build Your Own Retro Space Shooter in Python!

**For young coders, age 8 and up**

---

## How to Use This Guide

This guide explains every line of code you will type — what it does, why it is there, and how it works. You will build your game one small piece at a time and test it after every step.

When you see a code block like this:

```python
x = 5
```

That means: type exactly that into your file. When you see `# explanation` after a line, that is a comment — Python ignores it, but it helps you remember what the line does. You do not have to type the comments, but it is good practice.

---

## Before You Start

### Install Python
Go to **python.org**, click Download, and install Python 3. Ask a grown-up to help if needed.

### Install Pygame
Open a terminal window (on Mac: search for "Terminal", on Windows: search for "Command Prompt") and type this, then press Enter:

```
pip install pygame
```

Wait until it finishes. You only need to do this once.

### Create Your File
Make a new file called `space_shooter.py` in the same folder as this instructions file. Open it in a code editor (VS Code works great, or even Notepad).

---

## What Is a Game, Really?

Before we write any code, you need to understand one big idea: **the game loop**.

A game is just a program that does three things over and over, very fast — like flipping through a cartoon flipbook:

```
EVERY SINGLE FRAME (about 60 times per second):
┌──────────────────────────────────────────┐
│  Step 1 — CHECK:  Did the player press   │
│           a key? Did anything collide?   │
│                                          │
│  Step 2 — UPDATE: Move things, add up   │
│           scores, remove destroyed items │
│                                          │
│  Step 3 — DRAW:   Paint everything      │
│           fresh onto the screen          │
└──────────────────────────────────────────┘
```

Every bit of code you write fits into one of those three steps. Keep this picture in your head the whole time.

---

## Part 1 — Setting Up Pygame

**What we are building:** The bare minimum to open a window, run the game loop, and close cleanly.

---

### Step 1.1 — Import the tools you need

At the very top of your file, type:

```python
import pygame
import random
```

**Why `import pygame`?**
Python does not know about games by default. `import` is how you load a toolbox of extra powers into your program. `pygame` is the toolbox for making games — it can draw shapes, detect keys, play sounds, and more.

**Why `import random`?**
Later you will need random numbers for enemy positions and stars. You are importing it now so it is ready when needed.

---

### Step 1.2 — Start Pygame up

```python
pygame.init()
```

**Why?**
`pygame.init()` is like pressing the "power on" button for the pygame toolbox. You must always call this before using any other pygame features. If you forget it, things will break in strange ways.

---

### Step 1.3 — Create the game window

```python
screen = pygame.display.set_mode((800, 600))
```

**Why?**
This creates the window where your game will appear. `(800, 600)` means 800 pixels wide and 600 pixels tall. The result is saved in a variable called `screen` — you will use `screen` every time you want to draw something.

**Note the double brackets:** The outer `()` are for the function call. The inner `()` create a "tuple" — a pair of numbers packaged together. Pygame expects width and height bundled this way.

```python
pygame.display.set_caption("Space Shooter")
```

**Why?**
This sets the text shown in the title bar of the window. Change `"Space Shooter"` to any name you like.

---

### Step 1.4 — Create a clock

```python
clock = pygame.time.Clock()
```

**Why?**
Without a clock, your game loop would run as fast as your computer can manage — maybe thousands of times per second on a fast computer and only hundreds on a slow one. This makes games run at different speeds on different machines. The clock lets us lock the speed to exactly 60 frames per second, so everyone gets the same experience.

---

### Step 1.5 — Create a "keep running" switch

```python
running = True
```

**Why?**
Your game loop will be a `while running:` loop. As long as `running` is `True`, the loop keeps going. When the player closes the window, you will set `running = False`, which stops the loop cleanly.

---

### Step 1.6 — Write the game loop

```python
while running:

    # --- CHECK / EVENTS ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- UPDATE ---
    # (nothing here yet)

    # --- DRAW ---
    screen.fill((0, 0, 0))
    pygame.display.flip()
    clock.tick(60)
```

Let's go through each line carefully:

**`while running:`**
This starts a loop that keeps repeating as long as `running` is `True`. Everything indented inside it runs once per frame.

**`for event in pygame.event.get():`**
Pygame collects a list of things that happened since the last frame — key presses, mouse clicks, window close requests. This line goes through that list one event at a time.

**`if event.type == pygame.QUIT:`**
`pygame.QUIT` is the event that fires when the player clicks the X button to close the window. This line checks: was this event a close request?

**`running = False`**
If the player clicked the X button, this sets `running` to `False`. On the next loop cycle, `while running:` will be `while False:`, which stops the loop.

**`screen.fill((0, 0, 0))`**
This paints the entire screen black. `(0, 0, 0)` is a colour written as three numbers: Red, Green, Blue — each between 0 and 255. `(0, 0, 0)` means no red, no green, no blue — black. You must do this every frame, otherwise old drawings stay on screen and everything smears.

**`pygame.display.flip()`**
Pygame draws to a hidden "back" screen so you never see half-drawn frames. `flip()` swaps the back screen with the visible one, showing everything at once. Without this line, nothing you draw will ever appear.

**`clock.tick(60)`**
Tells the clock to pause just long enough so that the loop runs at most 60 times per second. This keeps the game speed consistent.

---

### Step 1.7 — Quit cleanly

After the `while` loop (not inside it — at zero indentation):

```python
pygame.quit()
```

**Why?**
This shuts Pygame down properly when the loop ends. Without it, the program might hang or print error messages.

---

### Test it now!

Run your file. A black window should appear. Close it with the X button. If it works, great — you have the skeleton of a real game!

**Your file should look like this so far:**

```python
import pygame
import random

pygame.init()

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Space Shooter")

clock = pygame.time.Clock()
running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
```

---

## Part 2 — The Player's Spaceship

**What we are building:** A triangle shape the player can move left and right with the arrow keys.

---

### Step 2.1 — Understand coordinates

Your window is a grid of pixels. The top-left corner is position `(0, 0)`. X increases as you go **right**. Y increases as you go **down**.

```
(0,0) ────────────── (800,0)
  │                       │
  │    800 x 600 window   │
  │                       │
(0,600) ──────────── (800,600)
```

So the center-bottom of your window is around `(400, 570)`. Keep this in mind when placing your ship.

---

### Step 2.2 — Create player variables

Add these lines **before** the `while running:` loop:

```python
player_x = 400
player_y = 520
player_speed = 5
```

**Why `player_x` and `player_y`?**
These are the position of the player's ship. We store position in variables so we can change them every frame to move the ship. Starting at `(400, 520)` puts the ship near the bottom center.

**Why `player_speed = 5`?**
This controls how many pixels the ship moves per frame when an arrow key is held. 5 is a good starting value — try changing it later to feel the difference.

---

### Step 2.3 — Read held keys and move the ship

Inside the game loop, **after** the event `for` loop and **before** the draw section:

```python
    keys = pygame.key.get_pressed()

    if keys[pygame.K_LEFT]:
        player_x = player_x - player_speed

    if keys[pygame.K_RIGHT]:
        player_x = player_x + player_speed
```

**Why `pygame.key.get_pressed()`?**
The event loop (`for event in pygame.event.get()`) only fires once when a key is first pressed. But for movement, you want the ship to keep moving the whole time a key is held down. `get_pressed()` returns the live state of every key — is it down right now, this frame?

**Why `keys[pygame.K_LEFT]`?**
`keys` is like a big list. `pygame.K_LEFT` is the name for the left arrow key. `keys[pygame.K_LEFT]` gives you `True` if that key is currently held, or `False` if it is not. The `if` statement then moves the ship if the key is held.

**Why `player_x - player_speed` for left?**
Because X increases to the right. To go left, you decrease X. To go right, you increase X.

---

### Step 2.4 — Stop the ship from leaving the screen

Add these lines right after the movement code:

```python
    if player_x < 20:
        player_x = 20

    if player_x > 780:
        player_x = 780
```

**Why?**
Without these lines, the ship would fly off the edge of the window. These lines act like invisible walls. If the ship's X goes below 20, we snap it back to 20. If it goes above 780, we snap it back to 780. We use 20 and 780 (not 0 and 800) to leave a small margin so the wing tips do not clip the edge.

---

### Step 2.5 — Draw the ship as a triangle

Inside the draw section, **after** `screen.fill((0, 0, 0))` and **before** `pygame.display.flip()`:

```python
    ship_points = [
        (player_x, player_y - 20),
        (player_x - 20, player_y + 10),
        (player_x + 20, player_y + 10)
    ]
    pygame.draw.polygon(screen, (0, 255, 0), ship_points)
```

**Why a list of three points?**
A triangle has three corners. We describe each corner as an `(x, y)` position. All three positions are based on `player_x` and `player_y` (the ship's center), so when the variables change, the triangle automatically moves with them.

- `(player_x, player_y - 20)` — the **nose** of the ship, 20 pixels above center
- `(player_x - 20, player_y + 10)` — the **left wing tip**, 20 left and 10 below center
- `(player_x + 20, player_y + 10)` — the **right wing tip**, 20 right and 10 below center

**Why `(0, 255, 0)`?**
That is bright green. Red=0, Green=255 (max), Blue=0.

**Why `pygame.draw.polygon`?**
`polygon` draws a filled shape using a list of corner points. `screen` is where to draw. `(0, 255, 0)` is the colour. `ship_points` is our list of corners.

---

### Test it now!

Run your file. A green triangle should appear near the bottom center. Press the left and right arrow keys — the ship should move and stop at the edges.

---

## Part 3 — Starfield Background

**What we are building:** 100 tiny white dots randomly placed to look like stars in space.

---

### Step 3.1 — Create the list of stars

Add these lines **before** the `while running:` loop:

```python
stars = []

for i in range(100):
    star_x = random.randint(0, 800)
    star_y = random.randint(0, 600)
    stars.append([star_x, star_y])
```

**Why `stars = []`?**
This creates an empty list. A list is a container that can hold many items. We will store each star's position as an item in this list.

**Why `for i in range(100):`?**
This loop runs exactly 100 times — once for each star we want. `i` is a counter that goes from 0 to 99, but we do not actually use `i` here; we just need the loop to repeat 100 times.

**Why `random.randint(0, 800)`?**
`random.randint(a, b)` gives back a random whole number between `a` and `b`. So each star gets a random X position across the full width of the window.

**Why `stars.append([star_x, star_y])`?**
`append` adds a new item to the end of a list. We are adding `[star_x, star_y]` — a small list containing the star's X and Y. Using a list (not a tuple) means we can change the Y later to make stars scroll.

---

### Step 3.2 — Move the stars downward (scrolling effect)

Inside the **Update** section of the game loop:

```python
    for star in stars:
        star[1] = star[1] + 1
        if star[1] > 600:
            star[1] = 0
            star[0] = random.randint(0, 800)
```

**Why `for star in stars:`?**
This loops through every star in our list, one at a time. Each time through, `star` is one `[x, y]` pair.

**Why `star[1] = star[1] + 1`?**
`star[1]` is the Y value (index 1). Adding 1 each frame makes the star drift downward slowly — 1 pixel per frame.

**Why `if star[1] > 600:`?**
When a star drifts past the bottom of the screen (y > 600), we reset it to the top. We also give it a new random X position so it does not feel repetitive.

---

### Step 3.3 — Draw the stars

Inside the **Draw** section, **after** `screen.fill` but **before** drawing the ship:

```python
    for star in stars:
        pygame.draw.circle(screen, (255, 255, 255), (star[0], star[1]), 1)
```

**Why draw stars before the ship?**
Drawing order matters. Things drawn first appear behind things drawn later. Stars should be behind the ship, so we draw them first.

**Why `pygame.draw.circle`?**
A circle with radius 1 is a single pixel dot — perfect for a tiny star. `(255, 255, 255)` is white. `(star[0], star[1])` is the position. `1` is the radius.

---

### Test it now!

Run your file. You should see white stars slowly drifting downward behind your ship, making it feel like you are flying through space.

---

## Part 4 — Shooting Lasers

**What we are building:** Pressing SPACE fires a laser bolt that shoots upward from the ship. Many bolts can be on screen at the same time.

---

### Step 4.1 — Create the lasers list and speed

Add these lines before the game loop:

```python
lasers = []
laser_speed = 8
```

**Why a list?**
The player might fire many times quickly. Each laser travels independently. A list lets us track all of them at once — just like we did with stars.

**Why `laser_speed = 8`?**
Lasers should move faster than stars (1) and faster than the player ship (5) to feel satisfying. 8 pixels per frame is snappy.

---

### Step 4.2 — Fire a laser when SPACE is pressed

Inside the event loop (the `for event in pygame.event.get():` block), add:

```python
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                new_laser = [player_x, player_y - 20]
                lasers.append(new_laser)
```

**Why `pygame.KEYDOWN` and not `get_pressed()`?**
`KEYDOWN` fires exactly once when a key is first pushed down. This means each press fires exactly one laser. If we used `get_pressed()` instead, the laser would fire 60 times per second as long as SPACE was held — like a machine gun. One-at-a-time feels more classic and fair.

**Why `[player_x, player_y - 20]`?**
The laser starts at the tip of the ship's nose, which is 20 pixels above the center (`player_y - 20`). It would look wrong if the laser appeared below the ship.

---

### Step 4.3 — Move lasers upward and remove off-screen ones

Inside the **Update** section:

```python
    new_lasers = []
    for laser in lasers:
        laser[1] = laser[1] - laser_speed
        if laser[1] > 0:
            new_lasers.append(laser)
    lasers = new_lasers
```

**Why subtract `laser_speed`?**
Y increases downward, so to move upward you subtract. Subtracting 8 each frame makes the laser shoot up the screen quickly.

**Why build `new_lasers` instead of deleting from `lasers`?**
You cannot safely remove items from a list while you are looping through it with `for` — Python gets confused about which item comes next and skips some. The safe pattern is: loop through the old list, keep only the items you want in a new list, then replace the old list with the new one.

**Why `if laser[1] > 0:`?**
If the laser's Y is above the screen (less than 0), it has gone off the top and is wasted. We only add it to `new_lasers` if it is still on screen (`> 0`). This keeps the list from growing forever.

---

### Step 4.4 — Draw the lasers

Inside the **Draw** section:

```python
    for laser in lasers:
        pygame.draw.rect(screen, (255, 255, 0), (laser[0] - 2, laser[1], 4, 15))
```

**Why `pygame.draw.rect`?**
A laser bolt is a thin rectangle — a classic retro look. `rect` takes the surface to draw on, the colour, and a rectangle as `(x, y, width, height)`.

**Why `(255, 255, 0)`?**
That is bright yellow. Red=255, Green=255, Blue=0. Yellow lasers look classic.

**Why `laser[0] - 2`?**
The laser's X is the center of the bolt. The rectangle draws from its top-left corner. Subtracting 2 shifts it left by half the width (4 pixels wide, so half is 2), centering the bolt on the position.

**Why `4, 15`?**
4 pixels wide, 15 pixels tall — a thin vertical bar that looks like a laser bolt.

---

### Test it now!

Run your file. Press SPACE and yellow laser bolts should shoot upward from the nose of your ship!

---

## Part 5 — Enemy Ships

**What we are building:** Red enemy ships that randomly appear at the top of the screen and drift downward.

---

### Step 5.1 — Create the enemies list and variables

Before the game loop:

```python
enemies = []
enemy_speed = 2
spawn_timer = 0
```

**Why `enemy_speed = 2`?**
Enemies move slower than lasers (8) — they should feel like a creeping threat, not a bullet.

**Why `spawn_timer = 0`?**
We do not want a new enemy every single frame — that would be impossible to survive. Instead we will count frames and only spawn one when the timer reaches a certain number.

---

### Step 5.2 — Spawn enemies on a timer

Inside the **Update** section:

```python
    spawn_timer = spawn_timer + 1

    if spawn_timer >= 60:
        enemy_x = random.randint(20, 780)
        enemy_y = 0
        enemies.append([enemy_x, enemy_y])
        spawn_timer = 0
```

**Why add 1 to `spawn_timer` each frame?**
The game loop runs 60 times per second. So after 60 frames, one second has passed. By checking `>= 60` we spawn one enemy per second. Decrease 60 to spawn faster, increase it to spawn slower.

**Why `random.randint(20, 780)`?**
We want enemies to appear at a random X across the screen, but with a small margin from each edge so they are not half off screen.

**Why `enemy_y = 0`?**
Enemies start at the very top of the screen.

**Why `spawn_timer = 0`?**
After spawning an enemy, we reset the timer to 0 so it starts counting toward the next enemy again.

---

### Step 5.3 — Move enemies down and remove off-screen ones

Inside the **Update** section, right after the spawn code:

```python
    new_enemies = []
    for enemy in enemies:
        enemy[1] = enemy[1] + enemy_speed
        if enemy[1] < 620:
            new_enemies.append(enemy)
    enemies = new_enemies
```

**Why add `enemy_speed` to Y?**
Adding to Y moves downward (remember, Y increases going down).

**Why keep enemies only if `enemy[1] < 620`?**
If an enemy has drifted past 620 (just past the bottom edge of the 600-pixel-tall window), we drop it from the list. Keeping them forever would slowly slow down your game.

---

### Step 5.4 — Draw the enemies

Inside the **Draw** section:

```python
    for enemy in enemies:
        enemy_points = [
            (enemy[0], enemy[1] + 15),
            (enemy[0] - 18, enemy[1] - 10),
            (enemy[0] + 18, enemy[1] - 10)
        ]
        pygame.draw.polygon(screen, (255, 0, 0), enemy_points)
```

**Why a downward-pointing triangle?**
The player's ship points up. Enemies point down. This immediately tells the player which side is which, even without colour.

**Why `(255, 0, 0)`?**
Bright red. Red=255, Green=0, Blue=0. Classic enemy colour.

**Why these specific point offsets?**
- The tip points downward: `enemy[1] + 15` (15 pixels below center)
- The two back corners are above and to each side: `enemy[1] - 10` (10 pixels above center), `enemy[0] - 18` and `enemy[0] + 18`

Feel free to change the numbers to make your enemies look different.

---

### Test it now!

Run your file. Red triangles should appear at the top of the screen every second and drift downward. They will pass right through everything for now — collisions come next!

---

## Part 6 — Collisions

**What we are building:** Checking whether lasers hit enemies, and whether enemies hit the player.

---

### Step 6.1 — Understand hitboxes

We detect collisions using invisible rectangles called **hitboxes**. Even though the ship looks like a triangle, we treat it as a rectangle for collision checking. This is standard practice in games — it is fast and close enough.

```
pygame.Rect(x, y, width, height)
```

This creates a rectangle starting at `(x, y)` with the given width and height. Pygame can then check if two `Rect` objects overlap using `.colliderect()`.

---

### Step 6.2 — Add score and lives variables

Before the game loop:

```python
score = 0
lives = 3
```

---

### Step 6.3 — Check if lasers hit enemies

Inside the **Update** section, after moving enemies:

```python
    surviving_lasers = []
    for laser in lasers:
        laser_rect = pygame.Rect(laser[0] - 2, laser[1], 4, 15)
        hit_something = False

        surviving_enemies = []
        for enemy in enemies:
            enemy_rect = pygame.Rect(enemy[0] - 18, enemy[1] - 10, 36, 25)
            if laser_rect.colliderect(enemy_rect):
                hit_something = True
                score = score + 10
            else:
                surviving_enemies.append(enemy)
        enemies = surviving_enemies

        if not hit_something:
            surviving_lasers.append(laser)
    lasers = surviving_lasers
```

**Why loop through both lists?**
Each laser must be checked against every enemy. This is a "nested loop" — for each laser, we go through every enemy.

**Why `pygame.Rect(laser[0] - 2, laser[1], 4, 15)`?**
This creates a hitbox that matches the laser we draw. Same position, same size.

**Why `pygame.Rect(enemy[0] - 18, enemy[1] - 10, 36, 25)`?**
The enemy triangle spans from `enemy[0] - 18` to `enemy[0] + 18` (36 pixels wide) and from `enemy[1] - 10` to `enemy[1] + 15` (25 pixels tall). This hitbox covers the whole triangle.

**Why `hit_something = False`?**
We start assuming the laser did not hit anything. If it hits an enemy, we set this to `True`. At the end, we only keep the laser in the surviving list if `hit_something` is still `False`.

**Why `score = score + 10`?**
Each enemy destroyed adds 10 to the score.

---

### Step 6.4 — Check if enemies hit the player

Inside the **Update** section, after the laser-vs-enemy code:

```python
    player_rect = pygame.Rect(player_x - 20, player_y - 20, 40, 30)
    surviving_enemies = []
    for enemy in enemies:
        enemy_rect = pygame.Rect(enemy[0] - 18, enemy[1] - 10, 36, 25)
        if player_rect.colliderect(enemy_rect):
            lives = lives - 1
        else:
            surviving_enemies.append(enemy)
    enemies = surviving_enemies

    if lives <= 0:
        running = False
```

**Why `player_rect = pygame.Rect(player_x - 20, player_y - 20, 40, 30)`?**
This creates a hitbox centered on the player. 40 pixels wide and 30 pixels tall covers the triangle shape roughly.

**Why `lives = lives - 1`?**
Each time an enemy reaches the player, they lose a life.

**Why `running = False`?**
If the player is out of lives, the game should end. Setting `running = False` will stop the game loop after the current frame finishes.

---

### Test it now!

Run your file. Shoot the enemies — they should disappear and your score should go up. Let an enemy reach you — you should lose a life. Lose three lives and the game should close.

---

## Part 7 — Score and Lives on Screen

**What we are building:** Text in the top-left corner showing the current score and remaining lives.

---

### Step 7.1 — Create a font

Before the game loop:

```python
font = pygame.font.SysFont("monospace", 24)
```

**Why `SysFont`?**
`SysFont` loads a font that is already installed on your computer. `"monospace"` is a font where every letter is the same width — like an old computer terminal. It gives a very retro feel.

**Why size 24?**
24 is large enough to read easily but small enough to not take up much screen space. Try other sizes to see how they look.

---

### Step 7.2 — Draw the score and lives

Inside the **Draw** section, after drawing everything else:

```python
    score_text = font.render("SCORE: " + str(score), True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    lives_text = font.render("LIVES: " + str(lives), True, (255, 255, 255))
    screen.blit(lives_text, (10, 40))
```

**Why `font.render(...)`?**
Pygame does not draw text directly to the screen. Instead, `render` turns your text into an image (called a "surface"). You then draw that image onto the screen.

**Why `"SCORE: " + str(score)`?**
`score` is a number. You cannot join a number directly to a string with `+`. `str(score)` converts the number to text first. So if score is 30, this creates the string `"SCORE: 30"`.

**Why `True`?**
The second argument to `render` turns on "anti-aliasing" — smooth edges on the letters. For a more blocky, retro feel you can use `False` instead.

**Why `(255, 255, 255)`?**
White text shows up clearly on the black background.

**Why `screen.blit(...)`?**
`blit` draws one image onto another. Here we draw the text image onto the screen. `(10, 10)` is the top-left corner position of where the text appears.

**Why `(10, 40)` for lives?**
The score text is at Y=10. The font height is about 24 pixels. Placing the lives at Y=40 gives a small gap between the two lines.

---

### Test it now!

Run your file. You should see "SCORE: 0" and "LIVES: 3" in the top-left corner. Shoot enemies to watch the score rise. Get hit to watch lives drop.

---

## Part 8 — Game Over Screen

**What we are building:** When lives reach zero, show a "GAME OVER" screen instead of just closing.

---

### Step 8.1 — Create a big font

Before the game loop:

```python
big_font = pygame.font.SysFont("monospace", 64)
```

**Why size 64?**
Game over text should be dramatic and large. 64 pixels tall makes it stand out.

---

### Step 8.2 — Add the game over screen after the main loop

After the `while running:` loop ends (at zero indentation, before `pygame.quit()`):

```python
game_over = True
while game_over:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_over = False

    screen.fill((0, 0, 0))

    over_text = big_font.render("GAME OVER", True, (255, 50, 50))
    screen.blit(over_text, (180, 220))

    final_text = font.render("FINAL SCORE: " + str(score), True, (255, 255, 255))
    screen.blit(final_text, (290, 310))

    quit_text = font.render("CLOSE THE WINDOW TO EXIT", True, (150, 150, 150))
    screen.blit(quit_text, (185, 360))

    pygame.display.flip()
    clock.tick(30)
```

**Why another `while` loop?**
The game over screen needs to stay visible and respond to events (like clicking the X to close). A second loop does exactly that — it is just like the main game loop, but simpler.

**Why `(255, 50, 50)` for "GAME OVER"?**
A slightly red-tinted white reads as alarming and dramatic. Full red `(255, 0, 0)` would work too.

**Why `clock.tick(30)` instead of 60?**
The game over screen has nothing moving. 30 frames per second is plenty and uses less CPU.

**Why specific positions like `(180, 220)`?**
These numbers were chosen to roughly center the text on the 800×600 screen. To center text precisely, you can use `over_text.get_width()` to find the text's pixel width, then calculate: `x = (800 - over_text.get_width()) // 2`. Try it!

---

### Test it now!

Run your file, let the enemies kill you. After your last life, you should see the red "GAME OVER" screen with your final score. Close the window to exit.

---

## Part 9 — Polish and Extra Challenges

Your game is complete! Here are extra things to try. Each one teaches you something new.

---

### Challenge A — Flash the screen red when hit

When an enemy hits the player, fill the screen dark red for a few frames instead of black. This gives a "damage" feeling.

**Hint:** Create a variable `hit_flash = 0` before the game loop. When the player is hit, set `hit_flash = 10`. In the draw section:

```python
    if hit_flash > 0:
        screen.fill((80, 0, 0))
        hit_flash = hit_flash - 1
    else:
        screen.fill((0, 0, 0))
```

---

### Challenge B — Increase difficulty over time

Every time the score reaches a new hundred, increase the enemy speed and spawn rate.

**Hint:** After updating the score, add:

```python
    if score > 0 and score % 100 == 0:
        enemy_speed = enemy_speed + 0.5
```

`%` is the "remainder" operator. `score % 100 == 0` is `True` when score is exactly 100, 200, 300, etc.

---

### Challenge C — Make enemies zigzag

Give each enemy an X direction when it spawns. Change the enemy from a simple `[x, y]` list to `[x, y, direction]` where direction is `1` or `-1`. Each frame, add that direction to the enemy's X. When the enemy hits the edges, flip the direction.

**Hint when spawning:**

```python
        direction = random.choice([-1, 1])
        enemies.append([enemy_x, enemy_y, direction])
```

**Hint when moving:**

```python
        enemy[0] = enemy[0] + enemy[2]
        if enemy[0] < 10 or enemy[0] > 790:
            enemy[2] = enemy[2] * -1
```

Multiplying by `-1` flips positive to negative and negative to positive — reversing direction.

---

### Challenge D — Add sound effects

Save a `.wav` sound file in the same folder as your game. Then:

```python
pygame.mixer.init()
laser_sound = pygame.mixer.Sound("laser.wav")
```

Play it when you fire:

```python
laser_sound.play()
```

Search the internet for "free retro laser sound wav" to find files you can download.

---

### Challenge E — Save a high score

Use Python's file-reading tools to save and load the best score:

**To save:**
```python
with open("highscore.txt", "w") as f:
    f.write(str(score))
```

**To load at the start:**
```python
try:
    with open("highscore.txt", "r") as f:
        high_score = int(f.read())
except:
    high_score = 0
```

Then display `high_score` on the game over screen and update it if `score > high_score`.

---

## Complete Game Structure Map

Here is every section of your finished file in order. Use this as a checklist:

```
1.  import pygame
    import random

2.  pygame.init()

3.  screen = ...
    pygame.display.set_caption(...)
    clock = ...
    running = True

4.  Player variables  (player_x, player_y, player_speed)
5.  Stars list        (100 random [x, y] pairs)
6.  Lasers list       (lasers = [], laser_speed)
7.  Enemies list      (enemies = [], enemy_speed, spawn_timer)
8.  Score and lives   (score = 0, lives = 3)
9.  Fonts             (font, big_font)

10. while running:
        │
        ├── EVENT LOOP  (quit, KEYDOWN for space → append laser)
        │
        ├── HELD KEYS   (K_LEFT, K_RIGHT → move player)
        │
        ├── CLAMP       (keep player inside screen)
        │
        ├── UPDATE
        │     ├── Move stars down, wrap around top
        │     ├── Move lasers up, remove off-screen
        │     ├── Spawn enemies on timer
        │     ├── Move enemies down, remove off-screen
        │     ├── Laser vs enemy collisions → update score
        │     └── Enemy vs player collisions → update lives
        │
        ├── CHECK lives <= 0 → running = False
        │
        └── DRAW
              ├── screen.fill black (or red if hit_flash)
              ├── Draw stars
              ├── Draw lasers
              ├── Draw enemies
              ├── Draw player ship
              ├── Draw score text
              ├── Draw lives text
              ├── pygame.display.flip()
              └── clock.tick(60)

11. GAME OVER loop
        ├── EVENT LOOP (quit)
        ├── Draw black background
        ├── Draw "GAME OVER"
        ├── Draw final score
        ├── pygame.display.flip()
        └── clock.tick(30)

12. pygame.quit()
```

---

## When Things Go Wrong

**Black window appears then immediately closes:**
You probably have a Python error. Read the red text in the terminal carefully — it tells you exactly which line has the problem.

**Nothing draws on screen:**
Make sure `pygame.display.flip()` is inside the loop, at the end of every draw section. Also make sure all draw code is inside the `while running:` block.

**The game crashes with `IndexError` or `ValueError`:**
You might be accessing `enemy[2]` on an enemy that only has `[x, y]`. Check that all enemies were created with the right number of values.

**List size changes during iteration error:**
You are removing items while looping through the list directly. Use the "build a new surviving list" pattern from Part 4.

**Text does not appear:**
Make sure `font.render` is called every frame inside the loop — not once before the loop. And make sure you call `screen.blit` with the result.

**Ship moves too fast or too slow:**
Change `player_speed`. Higher = faster.

**Enemies are too easy or too hard:**
Change `enemy_speed` and the `spawn_timer` threshold.

---

## What You Have Learned

By finishing this game, you have learned the same ideas that real game developers use every day:

- The **game loop** — check, update, draw
- **Variables** to track position, speed, score, and lives
- **Lists** to manage many objects at the same time
- **Loops** to move and draw every item in a list
- **Conditionals** (`if`) to react to keypresses and collisions
- **Hitboxes** and collision detection with `pygame.Rect`
- **Text rendering** to display scores on screen

The only difference between this game and a professional game is the size of the team. The thinking is exactly the same. 

**What to try next:**
- Add a second enemy type that moves differently
- Add a "shield" power-up that occasionally falls from the top
- Add a boss enemy that takes multiple hits
- Try making a completely different game — a platformer, a racing game, or a puzzle game — using these same ideas
