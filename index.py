# this file will house the fundamental game play logic of new space invaders python web app game

import pygame
import sys
import time
import os
import random
from pygame.locals import *

# Initialize pygame
pygame.init()

# Set up the display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Game loop
def main():
    clock = pygame.time.Clock()
    running = True
# new nested function inside of main game loop function to change the background color/pictures on game play window
    def redraw_window():
        pygame.display.update()
        
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
        
        # Fill screen with black
        screen.fill(BLACK)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()





if __name__ == "__main__":
    main()
