# this file will house the fundamental game play logic of new space invaders python web app game

# from logging import _Level
import numbers
from re import S
from unittest import result
import pygame
import sys
import time
import os
import random
from pygame.locals import *

# os.path import to safely load assets to window from dif folder
img_path = os.path.join("assets", "images", "player.png")
player_img = pygame.image.load('') # need too add image path here for player ship

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
    levels = [0,1,2,3,4,5,6,7,8,9,10,11,12]
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
        
        # sleep for 1 second
        time.sleep(1)
        # print the levels and lives
        print(levels)
        print(lives)
    
    pygame.quit()
    sys.exit()

# custom exception defined
class StrictStartError(Exception):
    pass


if __name__ == "__main__":
    main()



