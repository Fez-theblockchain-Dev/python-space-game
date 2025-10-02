# this file will house the fundamental game play logic of new space invaders python web app game

import pygame
import sys
import time
import os
import random
from pygame.locals import *

# os.path import to safely load assets to window from dif folder
img_path = os.path.join("assets", "images", "player.png")
player_img = pygame.image.load(img_path)

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

# Window background space image
nebula_image = pygame.image.load('512x512_purple_nebula_1.png').convert()
nebula_bg = pygame.transform.scale(nebula_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Game loop
def main():
    clock = pygame.time.Clock()
    running = True
    level = 0
    lives = 5

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
        
        # Draw background
        screen.blit(nebula_bg, (0, 0))
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()





if __name__ == "__main__":
    main()
