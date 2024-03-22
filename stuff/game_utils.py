import pygame
from game_config import *

def draw_board(window, player_pawns, enemy_pawns, special_pawns, possible_moves, turn_indicator):
    window.fill(WHITE)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(window, BLACK if (row + col) % 2 else WHITE, rect)
            pawn_pos = (row, col)
            if pawn_pos in player_pawns:
                pygame.draw.circle(window, player_pawns[pawn_pos], rect.center, SQUARE_SIZE // 4)
            elif pawn_pos in enemy_pawns:
                pygame.draw.circle(window, enemy_pawns[pawn_pos], rect.center, SQUARE_SIZE // 4)
            elif pawn_pos in special_pawns:
                pygame.draw.circle(window, special_pawns[pawn_pos], rect.center, SQUARE_SIZE // 4)
            if pawn_pos in possible_moves:
                pygame.draw.circle(window, GRAY, rect.center, SQUARE_SIZE // 8)

    pygame.draw.rect(window, RED if turn_indicator == 'player' else GREEN, (0, 0, WINDOW_SIZE, 10))

