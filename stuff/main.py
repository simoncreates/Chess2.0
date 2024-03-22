import pygame
import sys
from pygame.locals import *
import time

# Initialize Pygame
pygame.init()

# Grid Settings
grid_size = (8, 8)  # Example grid size
square_size = 50  # Pixel size of a grid square
screen_size = (grid_size[0] * square_size, grid_size[1] * square_size)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

# Screen
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption('Grid Game')

# Game Variables
pieces = {(2, 2): 'human', (5, 5): 'bot'}  # Example starting positions
last_moved = {}  # Tracks last move time of pieces

# Main Game Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == MOUSEBUTTONDOWN:
            # Determine grid position
            mx, my = pygame.mouse.get_pos()
            grid_pos = mx // square_size, my // square_size
            
            # Check if a piece was selected and move it if the delay has passed
            if grid_pos in pieces:
                pieces[grid_pos] = 'moving'
                last_moved[grid_pos] = time.time()

    # Update Game State
    now = time.time()
    for pos in list(pieces.keys()):
        if pieces[pos] == 'moving' and now - last_moved[pos] >= 2:  # 2 seconds delay
            # Example move logic: Move right if possible
            new_pos = (pos[0] + 1 if pos[0] + 1 < grid_size[0] else pos[0], pos[1])
            pieces[new_pos] = pieces.pop(pos)

    # Drawing
    screen.fill(BLACK)
    for y in range(grid_size[1]):
        for x in range(grid_size[0]):
            rect = pygame.Rect(x * square_size, y * square_size, square_size, square_size)
            pygame.draw.rect(screen, WHITE, rect, 1)
            if (x, y) in pieces:
                color = BLUE if pieces[(x, y)] == 'human' else WHITE
                pygame.draw.circle(screen, color, (x * square_size + square_size // 2, y * square_size + square_size // 2), square_size // 4)

    pygame.display.flip()
    pygame.time.wait(50)  # Frame delay to reduce CPU usage
