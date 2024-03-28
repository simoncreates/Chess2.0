import pygame
import pygame.draw
import pygame.font
import json
import hashlib
import random


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

global possible_moves, selected_pawn
possible_moves = []
selected_pawn = None

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

def draw_board(window, players, pawn_types, current_turn):
    window.fill(WHITE)
    for row in range(SQUARE_AMOUNT[0]):
        for col in range(SQUARE_AMOUNT[1]):
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(window, BLACK if (row + col) % 2 else WHITE, rect)

    for player in players:
        show_cooldown = (player['id'] == current_turn + 1)  # Assuming player ID starts from 1 and matches with turn index
        player_color = string_to_colorful_color(player['name'])
        for pawn in player['pawns']:
            row, col = pawn['position']
            draw_pawn(window, pawn, player_color, pawn_types, show_cooldown)
    
    for move in possible_moves:
        move_y, move_x = move
        center_position = (int(move_x * SQUARE_SIZE + SQUARE_SIZE / 2), int(move_y * SQUARE_SIZE + SQUARE_SIZE / 2))
        pygame.draw.circle(window, (0, 255, 0), center_position, int(SQUARE_SIZE // 8))
    
    current_player_color = string_to_colorful_color(players[current_turn]['name'])
    indicator_size = (50, 50)
    pygame.draw.rect(window, current_player_color, pygame.Rect(10, 10, indicator_size[0], indicator_size[1]))


def draw_shape(window, shape, position, size, color):
    x, y = position
    if shape == "triangle":
        pygame.draw.polygon(window, color, [(x, y - size // 2), (x - size // 2, y + size // 2), (x + size // 2, y + size // 2)])
    elif shape == "line":
        pygame.draw.line(window, color, (x - size // 2, y), (x + size // 2, y), 5)
    elif shape == "star":
        pygame.draw.circle(window, color, (x, y), size // 3)

def draw_pawn(window, pawn, player_color, pawn_types, show_cooldown):
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
    
    if show_cooldown and 'downtime' in pawn and pawn['downtime'] > 0:
        pygame.font.init()  
        font = pygame.font.SysFont('Arial', 12)
        cooldown_text = font.render(str(pawn['downtime']), True, (0, 0, 0))  
        text_x = x + size // 2 - cooldown_text.get_width() // 2
        text_y = y + size // 2 - cooldown_text.get_height() // 2     
        background_rect = cooldown_text.get_rect(x=text_x-2, y=text_y-2) 
        pygame.draw.rect(window, (255, 255, 255), background_rect, 0) 
        window.blit(cooldown_text, (text_x, text_y))

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

        if 0 <= new_x < SQUARE_AMOUNT[1] and 0 <= new_y < SQUARE_AMOUNT[0]:  # Ensure within bounds
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
            elif move_type == 3:
                #like rookor queen
                direction_x = 1 if dx > 0 else -1 if dx < 0 else 0
                direction_y = 1 if dy > 0 else -1 if dy < 0 else 0

                step_x, step_y = x, y
                while True:
                    step_x += direction_x
                    step_y += direction_y

                    # Stop if out of bounds
                    if not (0 <= step_x < SQUARE_AMOUNT[1] and 0 <= step_y < SQUARE_AMOUNT[0]):
                        break

                    next_pos = (step_y, step_x)
                    
                    # Stop if reaching a friendly piece
                    if next_pos in friendly_positions:
                        break
                    
                    possible_moves.append(next_pos)

                    # Stop if reaching an enemy piece - can capture
                    if next_pos in enemy_positions:
                        break

                    # Stop if the move has reached its maximum distance relative to its start
                    if (abs(step_x - x) == abs(dx) and dx != 0) or (abs(step_y - y) == abs(dy) and dy != 0):
                        break
    return possible_moves

def can_move(players, current_turn):
    # Check if there's any pawn with 0 downtime
    return any(pawn['downtime'] == 0 for pawn in players[current_turn]['pawns'])

def start_turn(players, current_turn):
    for pawn in players[current_turn]['pawns']:
        if pawn['downtime'] > 0:
            pawn['downtime'] -= 1


def execute_move(pawn, new_y, new_x, players, current_turn):
    pawn['position'] = [new_y, new_x]
    
    # Set the pawn's downtime according to its cooldownTime
    pawn['downtime'] = pawn_types[pawn['type']].get('cooldownTime', 0) 

    enemy_player_indices = [i for i in range(len(players)) if i != current_turn]
    for enemy_index in enemy_player_indices:
        enemy_player = players[enemy_index]
        enemy_player['pawns'] = [p for p in enemy_player['pawns'] if p['position'] != [new_y, new_x]]
    
    print(f"Moved pawn to {new_x}, {new_y}. Pawn now cooling down for {pawn['downtime']} turns.")



def human_turn(players, event, current_turn):
    global possible_moves, selected_pawn

    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:  # Left click
            click_position = get_click_position(event)
            if click_position:
                _, _, grid_x, grid_y = click_position
                
                # If a pawn is already selected, check if the click is on one of the possible moves
                if selected_pawn and (grid_y, grid_x) in possible_moves:
                    execute_move(selected_pawn, grid_y, grid_x, players, current_turn)
                    possible_moves = []  # Clear possible moves after the move is made
                    selected_pawn = None  # Clear selected pawn after the move
                    
                    # Only end the turn if no more pawns can move
                    if not any(p['downtime'] == 0 for p in players[current_turn]['pawns']):
                        print("No more moves left. End of turn.")
                        return True
                    else:
                        print("Another move is possible.")
                        return False
                    
                # No pawn is currently selected, or the click wasn't on a possible move
                selected_pawn = None  # Reset selected pawn if a new click occurs
                for pawn in players[current_turn]['pawns']:
                    pawn_y, pawn_x = pawn['position']
                    if [grid_y, grid_x] == [pawn_y, pawn_x] and pawn['downtime'] == 0:
                        # Select the pawn and calculate possible moves
                        selected_pawn = pawn
                        possible_moves = calculate_possible_moves(pawn, players, pawn_types, current_turn)
                        print(f"Pawn at {grid_x}, {grid_y}, with type: {pawn['type']} selected.")
                        return False  # Do not end turn; allow for move selection

                # Click was not on a pawn or a valid move; clear selection and possible moves
                if not possible_moves:
                    print("No valid action; select a pawn or one of its moves.")
                    selected_pawn = None

        elif event.button == 3:  # Right click to end turn
            possible_moves = []
            selected_pawn = None
            print("Skipping to next player's turn.")
            return True  # End the player's turn immediately

    return False
def initialize_game():
    max_players = 4
    min_players = 2
    max_pawns_per_player = 5
    min_pawns_per_player = 1
    pawn_types = ["knight", "archer", "soldier", "mage"]

    players = []
    player_names = ["Simon", "Dönermann Ali", "AI1", "AI2"]  

    num_players = random.randint(min_players, max_players)
    for player_id in range(1, num_players + 1):
        player = {
            "id": player_id,
            "name": player_names[player_id - 1],
            "type": "ai" if player_id > 2 else "human", 
            "pawns": []
        }

        num_pawns = random.randint(min_pawns_per_player, max_pawns_per_player)
        for _ in range(num_pawns):
            pawn_type = random.choice(pawn_types)
            pawn_position = [random.randint(0, SQUARE_AMOUNT[0] - 1), random.randint(0, SQUARE_AMOUNT[1] - 1)]
            
            # Ensure unique positions for pawns within the same player
            while pawn_position in [pawn['position'] for pawn in player['pawns']]:
                pawn_position = [random.randint(0, SQUARE_AMOUNT[0] - 1), random.randint(0, SQUARE_AMOUNT[1] - 1)]

            pawn = {
                "position": pawn_position,
                "type": pawn_type,
                "health": 100,  # Example health, adjust as needed
                "downtime": 0   # Assuming no downtime initially
            }
            player["pawns"].append(pawn)
        players.append(player)

    # Example obstacles, could also randomize this part
    obstacles = [[2, 3], [4, 5], [6, 7]]

    return {"map": {"size": SQUARE_AMOUNT, "obstacles": obstacles}, "players": players, "pawnTypes": pawn_types}

def validate_movement_patterns(pawn_types):
    for pawn_type, attributes in pawn_types.items():
        for dx, dy, move_type, _ in attributes['movementPatterns']:
            if move_type == 3:
                if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                    raise ValueError(f"Invalid movement pattern for type {pawn_type}: [{dx}, {dy}] must be diagonal or straight.")

validate_movement_patterns(pawn_types)

def main():
    global possible_moves  
    game_data = initialize_game()
    players = game_data["players"]
    current_turn = 0

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        start_turn(players, current_turn)  

        for event in events:
            if players[current_turn]["type"] == "human":
                turn_ended = human_turn(players, event, current_turn)
                if turn_ended:
                    possible_moves = []
                    current_turn = (current_turn + 1) % len(players)
                    continue 

        # AI player's turn logic
        if players[current_turn]["type"] == "ai":
            print(f"AI player {players[current_turn]['name']}'s turn.")
            current_turn = (current_turn + 1) % len(players)

        draw_board(window, players, pawn_types, current_turn)
        pygame.display.flip()

    pygame.quit()




if __name__ == '__main__':
    main()
