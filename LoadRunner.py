import pygame
import sys
import os

pygame.init()

os.environ['SDL_VIDEO_CENTERED'] = '1'

# --- Directories ---
ASSETS_DIR = "images"
PLAYER_DIR = os.path.join(ASSETS_DIR, "player")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
MAPS_DIR = "maps"
SOUNDS_DIR = "sounds"

# Game parameters
tile_size = 40
clock = pygame.time.Clock()
player_speed = 3
hud_height = tile_size * 2  # miejsce na HUD

# Temporary window for convert_alpha()
pygame.display.set_mode((1, 1))

# --- Load textures ---
def load_texture(path, size=None):
    img = pygame.image.load(path).convert_alpha()
    if size:
        img = pygame.transform.scale(img, size)
    return img

textures = {
    "0": load_texture(os.path.join(ICONS_DIR, "floor.png"), (tile_size, tile_size)),
    "1": load_texture(os.path.join(ICONS_DIR, "wall.png"), (tile_size, tile_size)),
    "D": load_texture(os.path.join(ICONS_DIR, "door.png"), (tile_size, tile_size)),
    "L": load_texture(os.path.join(ICONS_DIR, "ladder1.png"), (tile_size, tile_size)),
}

# --- Player animations ---
player_size = 32
required_sprites = [
    "idle_right.png", "idle_left.png", "idle_up.png", "idle_down.png",
    "walk1_right.png", "walk2_right.png", "walk3_right.png",
    "walk1_left.png", "walk2_left.png", "walk3_left.png",
    "walk1_up.png", "walk2_up.png", "walk3_up.png",
    "walk1_down.png", "walk2_down.png", "walk3_down.png",
]

missing = [f for f in required_sprites if not os.path.exists(os.path.join(PLAYER_DIR, f))]
if missing:
    print("❌ Missing player sprite files:")
    for f in missing:
        print("   -", f)
    pygame.quit()
    sys.exit()

def load_player_sprite(name):
    return load_texture(os.path.join(PLAYER_DIR, name), (player_size, player_size))

player_animations = {
    "right": [load_player_sprite(f"walk{i}_right.png") for i in range(1, 4)],
    "left": [load_player_sprite(f"walk{i}_left.png") for i in range(1, 4)],
    "up": [load_player_sprite(f"walk{i}_up.png") for i in range(1, 4)],
    "down": [load_player_sprite(f"walk{i}_down.png") for i in range(1, 4)],
}

player_idle = {
    "right": load_player_sprite("idle_right.png"),
    "left": load_player_sprite("idle_left.png"),
    "up": load_player_sprite("idle_up.png"),
    "down": load_player_sprite("idle_down.png"),
}

player_direction = "down"
player_frame = 0
player_anim_timer = 0
player_anim_speed = 150

# --- HUD variables ---
player_lives = 3
player_keys = 0
heart_img = load_texture(os.path.join(ICONS_DIR, "heart.png"), (tile_size, tile_size))

def draw_hud():
    # Szare tło pod HUD
    pygame.draw.rect(screen, (50, 50, 50), (0, 0, map_width, hud_height))
    # Draw lives
    for i in range(player_lives):
        screen.blit(heart_img, (10 + i * (tile_size + 5), 10))
    # Draw keys
    font = pygame.font.Font(None, 32)
    text = font.render(f"Keys: {player_keys}", True, (255, 255, 255))
    screen.blit(text, (10, 10 + tile_size + 5))

# --- Sounds ---
pygame.mixer.init()
pygame.mixer.music.load(os.path.join(SOUNDS_DIR, "background_sound_1.wav"))
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)

door_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "door_open.wav"))
door_sound.set_volume(0.5)

# --- Map loading ---
def load_map(filename):
    with open(filename, "r") as f:
        lines = f.read().splitlines()
    return [list(line) for line in lines]

def start_level(level_index):
    global level_map, screen, player, map_width, map_height, doors

    filename = os.path.join(MAPS_DIR, f"map{level_index}.txt")
    if not os.path.exists(filename):
        print("🎉 Congratulations, you finished all levels!")
        pygame.quit()
        sys.exit()

    level_map = load_map(filename)
    doors = []

    start_x, start_y = None, None
    for row in range(len(level_map)):
        for col in range(len(level_map[row])):
            if level_map[row][col] == "S":
                start_x, start_y = col * tile_size, row * tile_size
                level_map[row][col] = "0"
            elif level_map[row][col] == "D":
                doors.append(pygame.Rect(col*tile_size, row*tile_size + hud_height, tile_size, tile_size))

    if start_x is None or start_y is None:
        print(f"Error: no start point (S) in {filename}")
        pygame.quit()
        sys.exit()

    map_width = len(level_map[0]) * tile_size
    map_height = len(level_map) * tile_size + hud_height
    screen = pygame.display.set_mode((map_width, map_height))
    pygame.display.set_caption(f"Load Runner 2D Map - level {level_index}")

    offset = (tile_size - player_size) // 2
    player = pygame.Rect(start_x + offset, start_y + offset + hud_height, player_size, player_size)

# --- Collisions ---
def check_collision(rect):
    start_col = max(rect.left // tile_size, 0)
    end_col = min(rect.right // tile_size + 1, len(level_map[0]))
    start_row = max((rect.top - hud_height) // tile_size, 0)
    end_row = min((rect.bottom - hud_height) // tile_size + 1, len(level_map))

    for row in range(start_row, end_row):
        for col in range(start_col, end_col):
            if level_map[row][col] == "1":
                wall = pygame.Rect(col * tile_size, row * tile_size + hud_height, tile_size, tile_size)
                if rect.colliderect(wall):
                    return True
    return False

# --- Game start ---
current_level = 1
start_level(current_level)

# --- Game loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    move_x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * player_speed
    move_y = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * player_speed

    # Update direction
    if move_x > 0:
        player_direction = "right"
    elif move_x < 0:
        player_direction = "left"
    elif move_y < 0:
        player_direction = "up"
    elif move_y > 0:
        player_direction = "down"

    # Move X
    new_rect = player.move(move_x, 0)
    if not check_collision(new_rect):
        player.x = new_rect.x

    # Move Y
    new_rect = player.move(0, move_y)
    if not check_collision(new_rect):
        player.y = new_rect.y

    # Doors
    for door in doors:
        if player.colliderect(door):
            door_sound.play()
            current_level += 1
            start_level(current_level)
            break

    # --- Animation ---
    moving = (move_x != 0 or move_y != 0)
    if moving:
        now = pygame.time.get_ticks()
        if now - player_anim_timer > player_anim_speed:
            player_anim_timer = now
            player_frame = (player_frame + 1) % len(player_animations[player_direction])
        player_img = player_animations[player_direction][player_frame]
    else:
        player_img = player_idle[player_direction]

    # --- Drawing ---
    screen.fill((0, 0, 0))

    # Draw map
    for row in range(len(level_map)):
        for col in range(len(level_map[row])):
            tile = level_map[row][col]
            if tile in textures and tile != "D":
                screen.blit(textures[tile], (col * tile_size, row * tile_size + hud_height))

    # Draw doors
    for door in doors:
        screen.blit(textures["D"], door)

    # Draw player
    screen.blit(player_img, player)

    # --- Draw HUD ---
    draw_hud()

    pygame.display.flip()
    clock.tick(30)
