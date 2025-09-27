import pygame
import sys
import os

pygame.init()

# --- Ustawienia katalogów ---
ASSETS_DIR = "images"
MAPS_DIR = "maps"
SOUNDS_DIR = "sounds"

# Parametry gry
tile_size = 40
clock = pygame.time.Clock()
player_speed = 3

# --- Tymczasowe okno, potrzebne dla convert_alpha() ---
pygame.display.set_mode((1, 1))

# --- Ładowanie grafik ---
def load_texture(name, size=None):
    path = os.path.join(ASSETS_DIR, name)
    img = pygame.image.load(path).convert_alpha()
    if size:
        img = pygame.transform.scale(img, size)
    return img

textures = {
    "0": load_texture("floor.png", (tile_size, tile_size)),
    "1": load_texture("wall.png", (tile_size, tile_size)),
    "D": load_texture("door.png", (tile_size, tile_size)),
}

player_size = 32
player_img = load_texture("player.png", (player_size, player_size))

# --- Ładowanie dźwięków ---
pygame.mixer.init()
pygame.mixer.music.load(os.path.join(SOUNDS_DIR, "bgm_montezuma.ogg"))
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1)  # pętla nieskończona

door_sound = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "door_open.wav"))
door_sound.set_volume(0.5)

# --- Wczytywanie mapy ---
def load_map(filename):
    with open(filename, "r") as f:
        lines = f.read().splitlines()
    return [list(line) for line in lines]

# --- Inicjalizacja poziomu ---
def start_level(level_index):
    global level_map, screen, player, map_width, map_height, doors

    filename = os.path.join(MAPS_DIR, f"map{level_index}.txt")
    if not os.path.exists(filename):
        print("🎉 Gratulacje, ukończyłeś wszystkie poziomy!")
        pygame.quit()
        sys.exit()

    level_map = load_map(filename)
    doors = []

    # Znajdź punkt startowy (S) i drzwi (D)
    start_x, start_y = None, None
    for row in range(len(level_map)):
        for col in range(len(level_map[row])):
            if level_map[row][col] == "S":
                start_x, start_y = col * tile_size, row * tile_size
                level_map[row][col] = "0"
            elif level_map[row][col] == "D":
                doors.append(pygame.Rect(col*tile_size, row*tile_size, tile_size, tile_size))

    if start_x is None or start_y is None:
        print(f"Błąd: brak punktu startowego (S) w {filename}")
        pygame.quit()
        sys.exit()

    # Okno gry - ustaw właściwy rozmiar
    map_width = len(level_map[0]) * tile_size
    map_height = len(level_map) * tile_size
    screen = pygame.display.set_mode((map_width, map_height))
    pygame.display.set_caption(f"Mapa 2D - poziom {level_index}")

    # Gracz - wycentrowany w tile
    offset = (tile_size - player_size) // 2
    player = pygame.Rect(start_x + offset, start_y + offset, player_size, player_size)

# --- Kolizje ---
def check_collision(rect):
    start_col = max(rect.left // tile_size, 0)
    end_col = min(rect.right // tile_size + 1, len(level_map[0]))
    start_row = max(rect.top // tile_size, 0)
    end_row = min(rect.bottom // tile_size + 1, len(level_map))

    for row in range(start_row, end_row):
        for col in range(start_col, end_col):
            if level_map[row][col] == "1":
                wall = pygame.Rect(col * tile_size, row * tile_size, tile_size, tile_size)
                if rect.colliderect(wall):
                    return True
    return False

# --- Start gry ---
current_level = 1
start_level(current_level)

# --- Pętla gry ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Ruch gracza
    keys = pygame.key.get_pressed()
    move_x = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * player_speed
    move_y = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * player_speed

    # Ruch w X
    new_rect = player.move(move_x, 0)
    if not check_collision(new_rect):
        player.x = new_rect.x

    # Ruch w Y
    new_rect = player.move(0, move_y)
    if not check_collision(new_rect):
        player.y = new_rect.y

    # Sprawdź drzwi
    for door in doors:
        if player.colliderect(door):
            door_sound.play()      # efekt dźwiękowy
            current_level += 1
            start_level(current_level)
            break

    # --- Rysowanie ---
    screen.fill((0, 0, 0))

    # Rysowanie mapy (bez drzwi)
    for row in range(len(level_map)):
        for col in range(len(level_map[row])):
            tile = level_map[row][col]
            if tile in textures and tile != "D":
                screen.blit(textures[tile], (col * tile_size, row * tile_size))

    # Rysowanie drzwi
    for door in doors:
        screen.blit(textures["D"], door)

    # Rysowanie gracza
    screen.blit(player_img, player)

    pygame.display.flip()
    clock.tick(30)
