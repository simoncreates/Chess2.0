import pygame
import random

BOARD_SIZE = 8
SQUARE_SIZE = 75
WINDOW_SIZE = BOARD_SIZE * SQUARE_SIZE
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (100, 100, 100)
FPS = 30

# init pygame
pygame.init()

# create window
window = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption('Bauernschach')

pawn_types = {
    "standard": {
        "advance": 1,
        "capture": [(1, -1), (1, 1)]
    },
    "enhanced": {
        "advance": 1,
        "capture": [(1, -1), (1, 1)],
        "special": [(1, -1), (1, 1)]  
    }
}

def draw_board(window, player_pawns, ai_pawns, possible_moves=[]):
    window.fill(WHITE)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(window, BLACK if (row + col) % 2 else WHITE, rect)
            if (row, col) in player_pawns:
                pygame.draw.circle(window, RED, rect.center, SQUARE_SIZE // 5)
            elif (row, col) in ai_pawns:
                pygame.draw.circle(window, GREEN, rect.center, SQUARE_SIZE // 4)
            if (row, col) in possible_moves:
                pygame.draw.circle(window, GRAY, rect.center, SQUARE_SIZE // 8)


# check if move is valid
def is_move_valid(move, player_pawns, ai_pawns, is_player_turn):
    row, col = move
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        return False  
    if is_player_turn and move in player_pawns:
        return False 
    if not is_player_turn and move in ai_pawns:
        return False  
    return True

def update_state(tokens, move, won):
    if won:
        if move in tokens:
            tokens[move] += 1
        else:
            tokens[move] = 2  
    else:
        if move in tokens:
            tokens[move] -= 1  
            if tokens[move] <= 0:
                del tokens[move] 
        else:
            tokens[move] = -1

def get_possible_moves(pos, player_pawns, ai_pawns, is_player_turn):
    row, col, pawn_type, direction = pos  
    moves = []

    direction_moves = {
        0: (-1, 0), 
        2: (1, 0), 
        1: (0, 1), 
        3: (0, -1) 
    }
    
    move_row, move_col = direction_moves[direction]
    forward_pos = (row + move_row, col + move_col)
    if forward_pos not in player_pawns and forward_pos not in ai_pawns and 0 <= forward_pos[0] < BOARD_SIZE and 0 <= forward_pos[1] < BOARD_SIZE:
        moves.append(forward_pos)
    
    for d_col in [-1, 1]: 
        capture_pos = (row + move_row, col + d_col)
        if capture_pos in (ai_pawns if is_player_turn else player_pawns):
            moves.append(capture_pos)

    return moves

def reset_game():
    player_pawns = {(7, col, 1, 0) for col in range(BOARD_SIZE)} 
    ai_pawns = {(0, col, 1, 2) for col in range(BOARD_SIZE)}  
    selected_pawn = None
    possible_moves = []
    is_player_turn = True
    return player_pawns, ai_pawns, selected_pawn, possible_moves, is_player_turn



def make_ai_move(ai_pawns, player_pawns):
    print("pawns attempt to move")
    if ai_pawns:
        selected_pawn = random.choice(list(ai_pawns))
        possible_moves = get_possible_moves(selected_pawn, player_pawns, ai_pawns, is_player_turn=False)
        if possible_moves:
            print(f"possible moves:  {possible_moves}")
            print(f"AI selected pawn: {selected_pawn} with possible moves: {possible_moves}")
            ai_pawns.remove(selected_pawn)
            new_position = random.choice(possible_moves)
            ai_pawns.add(new_position)
            if new_position in player_pawns:
                print(f"AI captures player pawn at: {new_position}")
                player_pawns.remove(new_position)
        else:
            print("no possible moves")

def reset_game(player_pawns, ai_pawns, selected_pawn, possible_moves, is_player_turn):
    player_pawns = {(7, 2, 2, 0), (7, 3, 1, 0), (7, 4, 1, 0), (7, 1, 1, 0), (7, 0, 1, 0), (7, 5, 1, 0), (7, 6, 1, 0), (7, 7, 1, 0)} #x, y, type, dir (0=north, 2=south)
    ai_pawns = {(0, 2, 1, 2), (0, 3, 1, 2), (0, 4, 1, 2), (0, 1, 1, 2), (0, 0, 1, 2), (0, 5, 1, 2), (0, 6, 1, 2), (0, 7, 1, 2)}
    selected_pawn = None
    possible_moves = []
    is_player_turn = True
    return player_pawns, ai_pawns, selected_pawn, possible_moves, is_player_turn





def main():
    clock = pygame.time.Clock()
    player_pawns = {(7, 2), (7, 3), (7, 4), (7, 1), (7, 0), (7, 5), (7, 6), (7, 7)}
    ai_pawns = {(0, 2), (0, 3), (0, 4), (0, 1), (0, 0), (0, 5), (0, 6), (0, 7)}
    selected_pawn = None
    possible_moves = []
    is_player_turn = True
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Press 'R' to reset the game
                    player_pawns, ai_pawns, selected_pawn, possible_moves, is_player_turn = reset_game(player_pawns, ai_pawns, selected_pawn, possible_moves, is_player_turn)
            elif event.type == pygame.MOUSEBUTTONDOWN and is_player_turn:
                pos = pygame.mouse.get_pos()
                col = pos[0] // SQUARE_SIZE
                row = pos[1] // SQUARE_SIZE
                clicked_pos = (row, col)
                if selected_pawn and clicked_pos in possible_moves:
                    print(f"Player moves {selected_pawn} to {clicked_pos}")
                    is_player_turn = False
                    player_pawns.remove(selected_pawn)
                    player_pawns.add(clicked_pos)
                    # Check if an enemy pawn is captured
                    if clicked_pos in ai_pawns:
                        print(f"Player captures AI pawn at: {clicked_pos}")
                        ai_pawns.remove(clicked_pos)
                        is_player_turn = False
                        selected_pawn = None
                        possible_moves = []
                    else:
                        selected_pawn = None
                        possible_moves = []
                elif clicked_pos in player_pawns:
                    selected_pawn = clicked_pos
                    possible_moves = get_possible_moves(selected_pawn, player_pawns, ai_pawns, is_player_turn)

        # KI macht ihren Zug nach dem Spieler
        if not is_player_turn:
            print(f"Before AI Move: Player Pawns: {player_pawns}, AI Pawns: {ai_pawns}")
            make_ai_move(ai_pawns, player_pawns)
            print(f"After AI Move: Player Pawns: {player_pawns}, AI Pawns: {ai_pawns}")
            is_player_turn = True

        draw_board(window, player_pawns, ai_pawns, possible_moves)
        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()
