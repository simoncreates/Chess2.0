import pygame
import pygame.draw
import pygame.font
import json
import hashlib
import random
import tensorflow as tf
from tensorflow.keras import layers, models
import numpy as np
import itertools
import matplotlib.pyplot as plt
tf.keras.backend.clear_session()

def create_model(input_shape, num_actions):
    if num_actions <= 1:
        raise ValueError("num_actions must be greater than 1 for softmax. For binary decisions, consider using sigmoid.")
    model = models.Sequential([
        layers.Input(shape=input_shape),
        layers.Dense(64, activation='relu'),
        layers.Dense(32, activation='relu'),
        layers.Dense(num_actions, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='categorical_crossentropy')
    return model



try:
    with open('stuff/gamedata.json') as f:
        game_data = json.load(f)
except FileNotFoundError:
    print("Error: The file 'stuff/gamedata.json' was not found.")
    exit(1)
except json.JSONDecodeError:
    print("Error: There was an issue decoding 'stuff/gamedata.json'. Check if the file is valid JSON.")
    exit(1)

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






def get_game_state_input(players, current_turn, SQUARE_AMOUNT):
    """
    Prepare the neural network input from the game state.
    
    Parameters:
    - players: List of player objects containing pawn positions.
    - current_turn: Integer representing the current player's turn.
    - SQUARE_AMOUNT: Tuple representing the board size (width, height).
    
    Returns:
    - Numpy array representing the neural network input.
    """
    # Initialize an empty state representation
    state = np.zeros((SQUARE_AMOUNT[0], SQUARE_AMOUNT[1], 1), dtype=np.float32)
    
    # Mark positions of the current player's knights and enemy knights
    for player in players:
        for pawn in player['pawns']:
            if pawn['type'] == 'knight':
                x, y = pawn['position']
                state[y, x, 0] = 1.0 if player['id'] == current_turn + 1 else -1.0
                
    # Flatten the state to match the neural network's input shape
    return state.flatten()

def make_decision(model, game_state_input, possible_moves):
    predictions = model.predict(np.expand_dims(game_state_input, axis=0))[0]
    num_possible_moves = len(possible_moves)
    
    if num_possible_moves == 0:
        return 'skip'  # or another appropriate action for no moves available

    # Ensure we do not exceed the model's output size
    predictions = predictions[:num_possible_moves]

    move_index = np.argmax(predictions)
    selected_move = possible_moves[move_index]
    print(f"selected move: {selected_move}")
    return selected_move



def ai_turn(player, model, game_data):
    print(f"AI turn for player {player['name']} with model {model}")
    global possible_moves
    # Generate possible moves for all pawns.
    possible_moves = []
    for pawn in player['pawns']:
        moves_for_pawn = calculate_possible_moves(pawn, game_data['players'], game_data['pawnTypes'], game_data['current_turn'])
        for move in moves_for_pawn:
            possible_moves.append((pawn, move[0], move[1]))
    print(f"Possible moves calculated: {possible_moves}")

    # Get the current state input for the AI.
    state_input = get_game_state_input(game_data['players'], game_data['current_turn'], SQUARE_AMOUNT)
    print(f"State input for AI: {state_input.shape}")

    # Make a decision and execute the move or skip.
    decision = make_decision(model, state_input, possible_moves)
    print(f"AI decision: {decision}")
    if decision != 'skip':
        execute_move(decision, game_data['players'], game_data['current_turn'])
    else:
        print("AI decided to skip the turn.")


def check_game_over(players):
    # Example condition: check if any player has no pawns left
    return any(len(player['pawns']) == 0 for player in players)

def evaluate_and_select_top_ais(ais, scores):
    # Assume `scores` is a list of the same length as `ais` with each AI's score
    # Sort the AIs by their score in descending order and select the top half
    top_ais_indices = np.argsort(scores)[::-1][:len(ais)//2]
    return [ais[i] for i in top_ais_indices]

def reproduce_ais(top_ais):
    new_generation = []
    # Duplicate each top AI once, and then mutate
    for ai in top_ais:
        new_ai = create_model(input_shape=(SQUARE_AMOUNT[0] * SQUARE_AMOUNT[1],), num_actions=len(possible_moves) + 1)
        new_ai.set_weights(ai.get_weights())  # copy weights
        mutate_model(new_ai)  # mutate weights slightly
        new_generation.append(new_ai)
        # Add the original unmutated version too
        new_generation.append(ai)
    return new_generation

def mutate_model(model, mutation_rate=0.1):
    weights = model.get_weights()
    new_weights = []
    for weight in weights:
        if len(weight.shape) == 2:  # for Dense layers
            mutation_mask = np.random.rand(*weight.shape) < mutation_rate
            weight += np.random.normal(size=weight.shape) * mutation_mask
        new_weights.append(weight)
    model.set_weights(new_weights)


def play_game(ai_1, ai_2, game_data, score_board):
    global window  # Ensure 'window' is accessible, defined globally or passed as an argument
    
    move_history = []  # Track all moves
    game_draw = False  # Flag to indicate if the game ends in a draw

    print("Starting a new game.")
    game_data['current_turn'] = 0

    while not check_game_over(game_data['players']):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return  # Stop playing if the window is closed

        current_player_id = game_data['current_turn'] % 2
        print(f"Turn {game_data['current_turn']}: Player {current_player_id + 1}'s move.")
        current_ai_model = ai_1 if current_player_id == 0 else ai_2
        ai_turn(game_data['players'][current_player_id], current_ai_model, game_data)

        # Convert game state to a hashable form to track repetitions
        current_move = [(pawn['position'], pawn['type']) for pawn in game_data['players'][current_player_id]['pawns']]
        move_history.append(tuple(current_move))

        if move_history.count(tuple(current_move)) >= 4:  # Check for the fourth repetition
            print("Game ends in a draw due to repetition.")
            game_draw = True
            break

        draw_board(window, game_data['players'], pawn_types, game_data['current_turn'])  # Draw the current game state
        pygame.display.flip()  # Update the display with the new drawing

        game_data['current_turn'] += 1
    
    if game_draw:
        # Update scores for a draw
        score_board['ai_1'] += 0.5
        score_board['ai_2'] += 0.5
    else:
        print("Game over.")

    return game_draw




def evolve_ais(ais):
    # Evaluate AIs and sort by performance
    sorted_ais = sorted(ais, key=lambda ai: ai['score'], reverse=True)
    
    # Select the top half of AIs
    survivors = sorted_ais[:len(sorted_ais)//2]
    
    # Create the new generation of AIs by duplicating and mutating the survivors
    new_generation = []
    for survivor in survivors:
        for _ in range(2):  # Duplicate each survivor
            new_ai = create_model(input_shape=(SQUARE_AMOUNT[0] * SQUARE_AMOUNT[1],), num_actions=len(possible_moves))
            new_ai.set_weights(survivor.get_weights())  # Copy weights
            # Introduce mutations, this function needs to be implemented
            mutate_model(new_ai)
            new_generation.append(new_ai)
    
    return new_generation

def train_ais(game_data, num_ais=50, generations=10):
    # Assuming SQUARE_AMOUNT is defined elsewhere in your code
    SQUARE_AMOUNT = (8, 8)  # Example for a chess board, update as necessary

    # Initialization code for create_model, initialize_ai_game, and reproduce_ais goes here
    # Placeholder for the actual AI model creation function
    def create_model(input_shape, num_actions):
        pass

    # Placeholder for the game initialization function
    def initialize_ai_game():
        pass

    # Placeholder for the function to reproduce AIs for the next generation
    def reproduce_ais(top_ais):
        pass

    # Assuming a maximum of 50 actions
    max_possible_actions = 50  # Adjust based on your game's logic
    ais = [create_model(input_shape=(SQUARE_AMOUNT[0] * SQUARE_AMOUNT[1],), num_actions=max_possible_actions) for _ in range(num_ais)]

    # Initialize scores and best_scores list
    scores = np.zeros(num_ais)
    best_scores = []  # Track best score per generation
    score_board = np.zeros((num_ais, num_ais))  # Initialize a scoreboard

    for generation in range(generations):
        print(f"Starting generation {generation + 1}")
        scores.fill(0)  # Reset scores each generation
        score_board.fill(0)  # Reset scoreboard each generation

        # Play each AI against each other AI
        for i, model_1 in enumerate(ais):
            for j, model_2 in enumerate(ais):
                if i != j:
                    game_data = initialize_ai_game()  # Reset game_data for each match
                    print(f"Playing game {i} vs {j}")
                    # Update play_game to include score_board as an argument
                    play_game(model_1, model_2, game_data, score_board)

                    # Implement your scoring logic here based on game_data outcome
                    # Example updates to the scores and scoreboard
                    # scores[i] += determine_score(game_data, model_1)
                    # scores[j] += determine_score(game_data, model_2)
                    # score_board[i][j] = determine_score(game_data, model_1) # Example update

        # Implement your AI selection and reproduction logic here
        top_ais_indices = scores.argsort()[-num_ais//2:]
        best_scores.append(scores[top_ais_indices[-1]])
        top_ais = [ais[i] for i in top_ais_indices]

        ais = reproduce_ais(top_ais)
        print(f"Generation {generation + 1} trained. Best score: {best_scores[-1]}")
        print("Scoreboard for the generation:")
        print(score_board)  # Print the scoreboard for the current generation

    # Plot the best scores over generations
    plt.plot(best_scores)
    plt.xlabel('Generation')
    plt.ylabel('Best Score')
    plt.title('Best AI Score Over Generations')
    plt.show()

    return ais










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
        player_color = string_to_colorful_color(player['name'])
        for pawn in player['pawns']:
            row, col = pawn['position']
            draw_pawn(window, pawn, player_color, pawn_types)
    for move in possible_moves:
        _, move_y, move_x = move  # Adjusted to unpack the full structure of each 'move'
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
    y, x = pawn['position'] 
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

def execute_move(decision, players, current_turn):
    print(f"Executing move: {decision} for players at turn {current_turn}")
    pawn, new_y, new_x = decision
    # Update the pawn's position
    pawn['position'] = [new_y, new_x]
    print(f"Updated pawn position to {new_x}, {new_y}.")

    # Remove any enemy pawn at the new position
    enemy_player_indices = [i for i in range(len(players)) if i != current_turn]
    for enemy_index in enemy_player_indices:
        enemy_player = players[enemy_index]
        enemy_player['pawns'] = [p for p in enemy_player['pawns'] if p['position'] != [new_y, new_x]]
    print("Move executed.")




def human_turn(players, event, current_turn):
    global possible_moves, selected_pawn

    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:  
            click_position = get_click_position(event)
            if click_position:
                _, _, grid_x, grid_y = click_position

                if selected_pawn and (grid_y, grid_x) in possible_moves:
                    execute_move(selected_pawn, grid_y, grid_x, players, current_turn)
                    selected_pawn = None 
                    return False  

                else:
                    # Try to select another pawn
                    for pawn in players[current_turn]['pawns']:
                        pawn_y, pawn_x = pawn['position']
                        if [grid_y, grid_x] == [pawn_y, pawn_x]:
                            selected_pawn = pawn
                            possible_moves = calculate_possible_moves(pawn, players, pawn_types, current_turn)
                            print(f"Pawn at {grid_x}, {grid_y}, with type: {pawn['type']} selected.")
                            return False

                    # If no pawn is selected, reset the selection
                    selected_pawn = None
                    possible_moves = []
                    print("Select a pawn.")
                    return False

        elif event.button == 3:  
            # End the player's turn
            possible_moves = []
            selected_pawn = None
            print("Ending player's turn.")
            return True

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

def initialize_ai_game():
    pawn_types_list = ["knight"]  # Assuming we're only using knights for this setup
    players = []

    # Setup for two AI players
    for player_id in range(1, 3):
        player = {
            "id": player_id,
            "name": f"AI {player_id}",
            "type": "ai",
            "pawns": []
        }

        # Add three knights for each player
        for _ in range(3):
            pawn_position = [random.randint(0, SQUARE_AMOUNT[0] - 1), random.randint(0, SQUARE_AMOUNT[1] - 1)]
            
            # Ensure unique positions for pawns within the same player
            while pawn_position in [pawn['position'] for pawn in player['pawns']]:
                pawn_position = [random.randint(0, SQUARE_AMOUNT[0] - 1), random.randint(0, SQUARE_AMOUNT[1] - 1)]

            pawn = {
                "position": pawn_position,
                "type": random.choice(pawn_types_list),
                "health": 100,  # Example health, adjust as needed
            }
            player["pawns"].append(pawn)
        players.append(player)

    # Obstacles are optional and can be randomly placed as well
    obstacles = [[random.randint(0, SQUARE_AMOUNT[0] - 1), random.randint(0, SQUARE_AMOUNT[1] - 1)] for _ in range(5)]

    return {"map": {"size": SQUARE_AMOUNT, "obstacles": obstacles}, "players": players, "pawnTypes": pawn_types}


def validate_movement_patterns(pawn_types):
    for pawn_type, attributes in pawn_types.items():
        for dx, dy, move_type, _ in attributes['movementPatterns']:
            if move_type == 3:
                if not (dx == 0 or dy == 0 or abs(dx) == abs(dy)):
                    raise ValueError(f"Invalid movement pattern for type {pawn_type}: [{dx}, {dy}] must be diagonal or straight.")

validate_movement_patterns(pawn_types)

def main():
    global possible_moves, selected_pawn
    
    # Train the AI models before the game starts
    game_data = initialize_ai_game()  # Use the AI-specific initialization
    trained_ais = train_ais(game_data)  # Train the AIs

    # You can now select an AI from the trained AIs to play in the game
    selected_ai = trained_ais[0]  # Select the first AI for demonstration purposes

    current_turn = 0
    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        for event in events:
            if players[current_turn]["type"] == "human":
                turn_ended = human_turn(players, event, current_turn)
                if turn_ended:
                    possible_moves = []
                    current_turn = (current_turn + 1) % len(players)
                    continue
            elif players[current_turn]["type"] == "ai":
                ai_turn(players[current_turn], selected_ai, game_data)  # AI takes its turn
                current_turn = (current_turn + 1) % len(players)
                
        draw_board(window, players, pawn_types, current_turn)
        pygame.display.flip()

    pygame.quit()





if __name__ == '__main__':
    main()
