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
global possible_moves
possible_moves=[]

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
    
    for move in possible_moves:
        move_y, move_x = move  # Corrected to ensure consistency
        center_position = (int(move_x * SQUARE_SIZE + SQUARE_SIZE / 2), int(move_y * SQUARE_SIZE + SQUARE_SIZE / 2))
        pygame.draw.circle(window, (0, 255, 0), center_position, int(SQUARE_SIZE // 8))


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

def get_click_position(event):
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
        pixel_x, pixel_y = event.pos
        grid_x = pixel_x // SQUARE_SIZE
        grid_y = pixel_y // SQUARE_SIZE
        return pixel_x, pixel_y, grid_x, grid_y
    else:
        return None
    
def calculate_possible_moves(pawn, players, pawn_types, current_turn):
    possible_moves = []
    y, x = pawn['position']  # Assuming position is stored as [y, x]
    pawn_type_rules = pawn_types[pawn['type']]['movementPatterns']

    friendly_positions = [tuple(p['position']) for p in players[current_turn]['pawns']]
    enemy_positions = [tuple(p['position']) for player in players if player != players[current_turn] for p in player['pawns']]

    for dx, dy, move_type, _ in pawn_type_rules:
        new_x = x + dx
        new_y = y + dy

        if 0 <= new_x < SQUARE_AMOUNT[1] and 0 <= new_y < SQUARE_AMOUNT[0]: 
            new_pos = (new_y, new_x)

            if move_type == 0:
                #can move when there is no friendly pawn
                if new_pos not in friendly_positions:
                    possible_moves.append(new_pos)
            elif move_type == 1:
                #Can only move if unoccupied
                if new_pos not in friendly_positions and new_pos not in enemy_positions:
                    possible_moves.append(new_pos)
            elif move_type == 2:
                #Can only move if occupied by an enemy pawn
                if new_pos in enemy_positions:
                    possible_moves.append(new_pos)
    return possible_moves



#[x, y, type, move_type]
#x, y is the position relative to the pawn, that it can move to
#type can be (0= can go there if an enemy pawn is there or not. if going there while an enemy pawn is there it will be removed. 
#1, can only move if there is no enemy pawn, 
#2, can only move, if there is an enemy pawn, 
#3 means that this pawns acts like a rook or a queen. that means, if relative x or y is on a straight line or diagonal of the pawn, it can move to every spot until the relative point is reached, but can be blocked by your own or enemy pawns. enemy pawns can be taken like in normal chess)
#move_type defines, how the pawn moves to that place. if move type if 0 it moves like a knight in a normal chess games, so this move is able to skip other enemys. if the move type is 
#1 and the relative x y position is on a diagonal or straight line from the pawns origin, it can only go there, if there is no obstruction in the way like enemy pawns or your own.




def human_turn(players, event, current_turn):
    global possible_moves

    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:  # Left click
            click_position = get_click_position(event)
            if click_position:
                _, _, grid_x, grid_y = get_click_position(event)
                for pawn in players[current_turn]['pawns']:
                    pawn_y, pawn_x = pawn['position']
                    if [grid_y, grid_x] == [pawn_y, pawn_x]:  # Ensure comparison is consistent
                        # Proceed with move calculation
                        possible_moves = calculate_possible_moves(pawn, players, pawn_types, current_turn)
                        print(f"Pawn at {grid_x}, {grid_y} with no cooldown was clicked.")
                        return False
                    elif pawn['position'] == [grid_y, grid_x]:
                        print(f"Pawn at {grid_x}, {grid_y} clicked but it's still cooling down.")
                        possible_moves = []  # Clear as action can't be taken
                # If no pawn clicked or another pawn's cooldown is active
                if not possible_moves:
                    print("No pawn was clicked or pawn can't move.")
        elif event.button == 3:  # Right click to end turn
            possible_moves = []
            print("Skipping to next player's turn.")
            return True

    return False


def main():
    global possible_moves  # Use the global declaration to modify the global variable
    players = game_data["players"]
    current_turn = 0

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            # Handle the human player's turn
            if players[current_turn]["type"] == "human":
                turn_ended = human_turn(players, event, current_turn)
                if turn_ended:
                    # Reset possible moves when the turn ends
                    possible_moves = []
                    # Move to the next player's turn
                    current_turn = (current_turn + 1) % len(players)

        # AI player's turn logic should be outside the event loop
        # This way, it doesn't depend on events to proceed
        if players[current_turn]["type"] == "ai":
            print(f"AI player {players[current_turn]['name']}'s turn.")
            # Here you would implement AI actions
            # After AI actions are done, proceed to the next player
            current_turn = (current_turn + 1) % len(players)
            # Assuming AI's turn ends immediately for simplicity

        draw_board(window, players, pawn_types)
        pygame.display.flip()

    pygame.quit()



if __name__ == '__main__':
    main()
