import pygame
import random
import sys
import os

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    """
    try:
        # PyInstaller creates a temporary folder and stores path in _MEIPASS.
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === ACCEPT WINNING_SCORE FROM COMMAND LINE ARGUMENT (DEFAULT = 100) ===
if len(sys.argv) > 1:
    try:
        WINNING_SCORE = int(sys.argv[1])
    except ValueError:
        WINNING_SCORE = 100
else:
    WINNING_SCORE = 100

# Base and maximum fruit speeds.
BASE_SPEED = 5
MAX_SPEED = BASE_SPEED * 5  # Maximum speed is 25.

# Speed at which the basket moves in automatic mode.
AUTO_SPEED = 100

# Initialize Pygame and its mixer for sound.
pygame.init()
pygame.mixer.init()

# Set the display mode to fullscreen (uses the entire screen).
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Catch the Falling Fruit!")

clock = pygame.time.Clock()

# === LOAD BACKGROUND IMAGE AND FADE IT DOWN ===
background = pygame.image.load(resource_path("background.webp"))
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# === COLORS ===
WHITE   = (255, 255, 255)
BLACK   = (0, 0, 0)
RED     = (255, 0, 0)
GREEN   = (0, 255, 0)
BLUE    = (0, 0, 255)
YELLOW  = (255, 255, 0)
ORANGE  = (255, 165, 0)
PURPLE  = (128, 0, 128)
colors  = [RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE]

# === SOUND FILES ===
happy_sound   = pygame.mixer.Sound(resource_path("happy.mp3"))
sad_sound     = pygame.mixer.Sound(resource_path("sad.mp3"))
winning_sound = pygame.mixer.Sound(resource_path("winning.mp3"))
winning_channel = None  # Channel on which winning_sound plays.

# === BASKET PROPERTIES ===
basket_width = 100
basket_height = 20
basket_y = HEIGHT - basket_height - 10  # Positioned near the bottom.
basket_rect = pygame.Rect(WIDTH // 2 - basket_width // 2, basket_y, basket_width, basket_height)

# === FRUIT PROPERTIES ===
# Fruits are double the original size (radius 40 instead of 20).
fruit_radius = 40
fruits = []  # List to hold falling fruits.

# === EXPLOSION EFFECTS ===
explosions = []  # Each explosion is stored as a dictionary.

# === SCORE & FONT ===
# Use "Comic Sans MS" in bold for a thicker, more playful look.
score_font = pygame.font.SysFont("Comic Sans MS", 80, bold=True)       # For score text (double size).
instruction_font = pygame.font.SysFont("Comic Sans MS", 60, bold=True)   # For instruction text.
win_font = pygame.font.SysFont("Comic Sans MS", 100, bold=True)          # For "YOU WIN" text.
score = 0

# === COLLISION & CAPTURE SETTINGS ===
COLLISION_OFFSET = 20  # Offset to trigger collision/sound slightly earlier.
CAPTURE_DELAY_FRAMES = 10  # Delay between playing the sound and starting explosion.

# === AUTOMATIC MODE SETTING ===
automatic_mode = False  # When True, the basket is controlled automatically.

# === GAME STATE ===
winning = False  # Indicates if the game is in a winning state.

# === MAIN GAME LOOP ===
running = True
while running:
    clock.tick(60)  # Run at 60 frames per second.

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                automatic_mode = not automatic_mode

    # --- Check for Winning Condition ---
    if score >= WINNING_SCORE and not winning:
        winning = True
        winning_channel = winning_sound.play()

    # --- Game Updates (when not in winning state) ---
    if not winning:
        # Update basket position.
        if automatic_mode:
            if fruits:
                target_fruit = max(fruits, key=lambda f: f['y'])
                target_x = target_fruit['x']
            else:
                target_x = basket_rect.centerx

            if basket_rect.centerx < target_x:
                basket_rect.x += min(AUTO_SPEED, target_x - basket_rect.centerx)
            elif basket_rect.centerx > target_x:
                basket_rect.x -= min(AUTO_SPEED, basket_rect.centerx - target_x)
        else:
            mouse_x, _ = pygame.mouse.get_pos()
            basket_rect.x = mouse_x - basket_width // 2

        if basket_rect.left < 0:
            basket_rect.left = 0
        if basket_rect.right > WIDTH:
            basket_rect.right = WIDTH

        # --- Spawn New Fruit ---
        spawn_probability = (1 + 0.4 * (score / WINNING_SCORE)) / 20.0
        if random.random() < spawn_probability:
            fruit_x = random.randint(fruit_radius, WIDTH - fruit_radius)
            fruit = {
                'x': fruit_x,
                'y': -fruit_radius,
                'radius': fruit_radius,
                'color': random.choice(colors)
            }
            fruits.append(fruit)

        # --- Update Fruit Positions and Check for Collisions ---
        effective_speed = BASE_SPEED + (MAX_SPEED - BASE_SPEED) * (score / WINNING_SCORE)
        for fruit in fruits[:]:
            if fruit.get("captured", False):
                fruit["delay"] -= 1
                if fruit["delay"] <= 0:
                    explosions.append({
                        'x': fruit['x'],
                        'y': fruit['y'],
                        'color': fruit['color'],
                        'radius': fruit['radius'],
                        'max_radius': fruit['radius'] * 3,
                        'growth': 4
                    })
                    fruits.remove(fruit)
                continue

            fruit['y'] += effective_speed

            if fruit['y'] - fruit['radius'] > HEIGHT:
                if score > 0:
                    score = max(score - 1, 0)
                    if score > 0:
                        sad_sound.play()
                fruits.remove(fruit)
                continue

            fruit_rect = pygame.Rect(
                fruit['x'] - fruit['radius'],
                fruit['y'] - fruit['radius'],
                fruit['radius'] * 2,
                fruit['radius'] * 2
            )
            collision_rect = basket_rect.copy()
            collision_rect.y -= COLLISION_OFFSET
            collision_rect.height += COLLISION_OFFSET

            if collision_rect.colliderect(fruit_rect) and not fruit.get("captured", False):
                fruit["captured"] = True
                fruit["delay"] = CAPTURE_DELAY_FRAMES
                score += 1
                happy_sound.play()
    else:
        # In winning state: do not update basket or spawn/move fruits.
        pass

    # --- Update Explosions ---
    for explosion in explosions[:]:
        explosion['radius'] += explosion['growth']
        if explosion['radius'] >= explosion['max_radius']:
            explosions.remove(explosion)

    # --- Check if Winning Sound Finished ---
    if winning and winning_channel is not None and not winning_channel.get_busy():
        score = 0
        winning = False
        fruits.clear()
        explosions.clear()

    # --- Drawing ---
    screen.blit(background, (0, 0))
    fade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    fade.fill((255, 255, 255, 80))
    screen.blit(fade, (0, 0))

    pygame.draw.rect(screen, BLACK, basket_rect)

    for fruit in fruits:
        pygame.draw.circle(screen, fruit['color'], (fruit['x'], fruit['y']), fruit['radius'])

    for explosion in explosions:
        pygame.draw.circle(screen, explosion['color'],
                           (explosion['x'], explosion['y']),
                           int(explosion['radius']), 3)

    score_text = score_font.render("Score: " + str(score), True, BLACK)
    screen.blit(score_text, (10, 10))

    # Instruction text now reflects the actual WINNING_SCORE.
    instruction_text = instruction_font.render(f"Catch {WINNING_SCORE} fruit!", True, BLACK)
    instruction_rect = instruction_text.get_rect(center=(WIDTH // 2, 30))
    screen.blit(instruction_text, instruction_rect)

    if winning:
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            win_text = win_font.render("YOU WIN", True, RED)
            text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(win_text, text_rect)

    pygame.display.flip()

pygame.quit()
sys.exit()
