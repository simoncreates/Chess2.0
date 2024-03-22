import pygame
import random
from game_config import *
from game_utils import draw_board

class Game:
    def __init__(self):
        self.pawns = self.initialize_pawns()
        self.is_player_turn = True
        self.selected_pawn = None
        self.possible_moves = []
        self.clock = pygame.time.Clock()

    def initialize_pawns(self):
        pawns = []
        for i in range(BOARD_SIZE):
            pawns.append({'position': (7, i), 'type': 0, 'health': 100, 'move_speed': 2, 'owner': 'player'})
            pawns.append({'position': (0, i), 'type': 0, 'health': 100, 'move_speed': 2, 'owner': 'enemy'})
        for _ in range(5):
            row, col = random.choice([(r, c) for r in range(2, BOARD_SIZE - 2) for c in range(BOARD_SIZE)])
            pawns.append({'position': (row, col), 'type': 1, 'health': 150, 'move_speed': 1, 'owner': random.choice(['player', 'enemy'])})
        return pawns

    
    def get_possible_moves(self, pawn_pos):
        moves = []
        row, col = pawn_pos
        direction = -1 if self.is_player_turn else 1
        forward_pos = (row + direction, col)
        if forward_pos not in self.player_pawns and forward_pos not in self.enemy_pawns and 0 <= forward_pos[0] < BOARD_SIZE:
            moves.append(forward_pos)
        for delta_col in [-1, 1]:
            capture_pos = (row + direction, col + delta_col)
            if capture_pos in (self.enemy_pawns if self.is_player_turn else self.player_pawns):
                moves.append(capture_pos)
        return moves

    def get_pawn_at_position(self, position):
        for pawn in self.pawns:
            if pawn['position'] == position:
                return pawn
        return None
        

    def make_move(self, pawn, new_pos):
        attacking_pawn = self.get_pawn_at_position(new_pos)
        if attacking_pawn:
            # If there's an attacking pawn, set its health to 0 (effectively 'capturing' it)
            attacking_pawn['health'] = 0
        pawn['position'] = new_pos
        self.remove_pawns_with_no_health()
        self.switch_turns()

    def remove_pawns_with_no_health(self):
        self.pawns = [pawn for pawn in self.pawns if pawn['health'] > 0]

    def ai_make_move(self):
        # Simplified AI move logic for demonstration
        ai_pawns = [pawn for pawn in self.pawns if pawn['owner'] == 'enemy' and pawn['type'] == 0]
        if ai_pawns:
            pawn = random.choice(ai_pawns)
            possible_moves = self.get_possible_moves(pawn['position'])
            if possible_moves:
                new_pos = random.choice(possible_moves)
                self.make_move(pawn, new_pos)


    def ai_make_move(self):
        ai_pawn, ai_new_pos = random.choice(list(self.get_ai_moves().items()))
        self.make_move(ai_pawn, ai_new_pos)

    def get_ai_moves(self):
        ai_moves = {}
        for pawn in self.enemy_pawns:
            possible_moves = self.get_possible_moves(pawn)
            if possible_moves:
                ai_moves[pawn] = random.choice(possible_moves)
        return ai_moves

    def switch_turns(self):
        self.is_player_turn = not self.is_player_turn
        self.selected_pawn = None
        self.possible_moves = []

    def run(self):
        pygame.init()
        window = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
        pygame.display.set_caption('Bauernschach')
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.is_player_turn:
                    pos = pygame.mouse.get_pos()
                    col = pos[0] // SQUARE_SIZE
                    row = pos[1] // SQUARE_SIZE
                    clicked_pos = (row, col)
                    if self.selected_pawn:
                        if clicked_pos in self.possible_moves:
                            self.make_move(self.selected_pawn, clicked_pos)
                        elif clicked_pos in self.player_pawns:
                            # Allow selecting another pawn
                            self.selected_pawn = clicked_pos
                            self.possible_moves = self.get_possible_moves(clicked_pos)
                        else:
                            # Deselect the current pawn if clicked outside of possible moves
                            self.selected_pawn = None
                            self.possible_moves = []
                    elif clicked_pos in self.player_pawns:
                        self.selected_pawn = clicked_pos
                        self.possible_moves = self.get_possible_moves(clicked_pos)

            if not self.is_player_turn:
                self.ai_make_move()

            turn_indicator = 'player' if self.is_player_turn else 'enemy'
            draw_board(window, self.player_pawns, self.enemy_pawns, self.special_pawns, self.possible_moves, turn_indicator)
            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()