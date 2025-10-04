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
player_space_ship = pygame.image.load('') # need too add image path here for player ship

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
nebula_image = pygame.image.load('assets/512x512_purple_nebula_1.png').convert()
nebula_bg = pygame.transform.scale(nebula_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# HeroShip class definition
class HeroShip:
    def __init__(self, x, y, width, height, lives, health=100):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.health = health
        self.lives = 3
        self.laser = []
        self.laser_cool_down = 0.5
        self.level = 0
        self.points = 0
        self.speed = 5
        # Create a simple colored rectangle instead of loading an image
        self.image = pygame.Surface((width, height))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
    
    def draw(self, screen):
        screen.blit(self.image, self.rect)


# creating new group for all space ships (hero & enemies)
spaceship = HeroShip(50, 0, 100, 100, 3, 100)
spaceship_group = pygame.sprite.GroupSingle()
spaceship_group.add(spaceship) 


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
        spaceship_group.draw(screen)

        # redraw window with new components
        hero_ship = HeroShip(50, 0, 100, 100, 3, 100)
        hero_ship.draw(screen)


        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

# custom exception defined
class StrictStartError(Exception):
    pass


if __name__ == "__main__":
    main()



