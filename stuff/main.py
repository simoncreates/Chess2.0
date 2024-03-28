import pygame
import pygame.draw
import json
import hashlib

# Load game data
with open('stuff/gamedata.json') as f:
    game_data = json.load(f)

# Game configuration
pawn_types = game_data["pawnTypes"]
SQUARE_AMOUNT = game_data["map"]["size"]
WINDOW_SIZE = [500, 500]
SQUARE_SIZE = WINDOW_SIZE[0] / SQUARE_AMOUNT[0]
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

pygame.init()
window = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption('Bauernschach')

def string_to_colorful_color(input_string):
    hash_object = hashlib.sha256(input_string.encode())
    hex_dig = hash_object.hexdigest()
    r_hash = int(hex_dig[0:2], 16)
    g_hash = int(hex_dig[2:4], 16)
    b_hash = int(hex_dig[4:6], 16)
    fixed_component_index = sum(bytearray(input_string.encode())) % 3
    colors = [r_hash, g_hash, b_hash]

    for i in range(3):
        if i == fixed_component_index:
            colors[i] = max(25, colors[i]) 
        else:
            colors[i] = min(255, max(0, colors[i]))  
    return tuple(colors)

def draw_board(window, players, pawn_types):
    window.fill(WHITE)
    for row in range(SQUARE_AMOUNT[0]):
        for col in range(SQUARE_AMOUNT[1]):
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(window, BLACK if (row + col) % 2 else WHITE, rect)

    for player in players:
        player_color = string_to_colorful_color(player['name'])
        for pawn in player['pawns']:
            row, col = pawn['position']
            pygame.draw.circle(window, player_color, (int(col * SQUARE_SIZE + SQUARE_SIZE / 2), int(row * SQUARE_SIZE + SQUARE_SIZE / 2)), int(SQUARE_SIZE // 4))
            draw_pawn(window, pawn, player_color, pawn_types)

def draw_shape(window, shape, position, size, color):
    x, y = position
    if shape == "triangle":
        pygame.draw.polygon(window, color, [(x, y - size // 2), (x - size // 2, y + size // 2), (x + size // 2, y + size // 2)])
    elif shape == "line":
        pygame.draw.line(window, color, (x - size // 2, y), (x + size // 2, y), 5)
    elif shape == "star":
        pygame.draw.circle(window, color, (x, y), size // 3)

def draw_pawn(window, pawn, player_color, pawn_types):
    row, col, pawn_type = pawn['position'][0], pawn['position'][1], pawn['type']
    x = int(col * SQUARE_SIZE + SQUARE_SIZE / 2)
    y = int(row * SQUARE_SIZE + SQUARE_SIZE / 2)
    base_color = player_color
    size = int(SQUARE_SIZE // 2)

    pygame.draw.circle(window, base_color, (x, y), size // 2)  # Base shape

    if pawn_type in pawn_types and "appearance" in pawn_types[pawn_type]:
        overlays = pawn_types[pawn_type]["appearance"].get("overlays", [])
        for overlay in overlays:
            shape = overlay["shape"]
            if overlay.get("color") == "relative":
                if "relativeColor" in overlay:
                    relative_color = overlay["relativeColor"]
                    overlay_color = (
                        min(255, max(0, base_color[0] + relative_color[0])),
                        min(255, max(0, base_color[1] + relative_color[1])),
                        min(255, max(0, base_color[2] + relative_color[2])),
                    )
                else:
                    overlay_color = base_color
            else:
                overlay_color = pygame.Color(*overlay.get("fixedColor", base_color))
            draw_shape(window, shape, (x, y), size, overlay_color)

def main():
    players = game_data["players"]
    current_turn = 0  # Index of the current player in the players list

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if players[current_turn]["type"] == "human":
                    print(f"Human player {players[current_turn]['name']} action handled.")
                    current_turn = (current_turn + 1) % len(players)
                    
        if players[current_turn]["type"] == "ai":
            print(f"AI player {players[current_turn]['name']}'s turn.")
            current_turn = (current_turn + 1) % len(players)

        draw_board(window, players, pawn_types)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
