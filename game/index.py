# this file will house the fundamental game play logic of new space invaders python web app game

# from logging import _Level
import numbers
from pickle import TRUE
from re import S
from unittest import result
import pygame
import sys
import time
import os
import random
from pygame.locals import * #For useful variables
from spaceship import SpaceShip
from laser import Laser
from player import Player
from alien import Alien

# Initialize pygame
pygame.init()

# Set up the display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH /2 , SCREEN_HEIGHT))
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
class HeroShip(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, lives, health=100):
        super().__init__()
        self.image = pygame.image.load('assets/spaceship.png')
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = width
        self.height = height
        self.health = health
        self.lives = 3
        self.laser = []
        self.laser_cool_down = 0.5
        self.level = 0
        self.points = 0
        self.speed = 5

    def draw(self, screen):
        screen.blit(self.image, self.rect)


# creating new group for all space ships (hero & enemies)
spaceship = SpaceShip(100, SCREEN_HEIGHT - 100, 100)
spaceship_group = pygame.sprite.GroupSingle()
spaceship_group.add(spaceship) 

# creating new group for all lasers
laser_group = pygame.sprite.Group()

# Create hero ship once (not in the game loop!)
hero_ship = HeroShip(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100, 100, 100, 3, 100)
hero_group = pygame.sprite.GroupSingle()
hero_group.add(hero_ship)

# creating levels class OOP elements for game loop functionality
class Level (pygame.sprite.Sprite):
    def __init__(self, level_number):
        super().__init__()
        self.level_number = level_number
        self.lives = 5

    
    def show_level_up_message(self, screen, font, level_number):
        """Display animated level-up celebration"""
    # Create celebration overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(128)
    overlay.fill((0, 0, 0))
  
    
    # Level up text
    level_number = [[0,1,2,3,4,5,6,7,8,9,10,11,12]]
    font = "Ariel"
    level_text = font.render(f"LEVEL {level_number} COMPLETE!", True, (255, 255, 0))
    text_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))

    
    
    # Draw celebration elements
    screen.blit(overlay, (0, 0))
    screen.blit(level_text, text_rect)
    
    # Add particle effects, animations, etc.
    pygame.display.flip()
    pygame.time.wait(2000)  # Show for 2 seconds


# Game loop

if __name__ == "__main__":
    main()
    def main():
        print("game is starting...")
        Player.sprite = Player(SCREEN_WIDTH /2, SCREEN_HEIGHT, 5)
        player_group = pygame.sprite.GroupSingle(Player)
        clock = pygame.time.Clock()
        # running = True
        Level = [0,1,2,3,4,5,6,7,8,9,10,11,12]
        lives = 5
        current_level_index = 0
        # the player has 30 seconds/level to eliminate all the aliens
        time_seconds = 30 

        # New level function that resets level back to 0 when a new game commences
new_game = bool

def level ():
        if new_game == TRUE:
            print(f'New game started. Set level{0}')


        current_level_index = 0 
        # loosing lives game logic
        lives = [1,2,3,4,5]

        if lives < 1:
            print("Game Over! you've lost all your lives")
        
        # Handle continuous key presses
        keys = pygame.key.get_pressed()
        if keys[K_LEFT] and hero_ship.rect.left > 0:
            hero_ship.rect.x -= hero_ship.speed
        if keys[K_RIGHT] and hero_ship.rect.right < SCREEN_WIDTH:
            hero_ship.rect.x += hero_ship.speed
        if keys[K_UP] and hero_ship.rect.top > 0:
            hero_ship.rect.y -= hero_ship.speed
        if keys[K_DOWN] and hero_ship.rect.bottom < SCREEN_HEIGHT:
            hero_ship.rect.y += hero_ship.speed
        
        # Draw background
        screen.blit(nebula_bg, (0, 0)) 

        # Draw all game objects
        hero_group.draw(screen)
        spaceship_group.draw(screen)
        laser_group.draw(screen)

        # Update groups
        hero_group.update()
        spaceship_group.update()
        laser_group.update()

        # Update display
        pygame.display.flip()
        clock = pygame.time.Clock()
        clock.tick(60)

        # update ship damage rules

        spaceship_health = 100
        laser_damage = 10

        current_spaceship_health = spaceship_health - laser_damage

        print(current_spaceship_health)

    
        pygame.quit()
        sys.exit()

# custom exception defined
class StrictStartError(Exception):
    pass
# importing main function from game.py, needed to use a 'from module import function' to call fuction from outside of game loop
from game import main

if __name__ == "__main__":
    main()




hits = pygame.sprite.groupcollide(hero_bullets, Mystery_Ship, True, True)

for hit in hits:
    # When a mystery ship is destroyed
    key = Key(hit.rect.centerx, hit.rect.centery)
    all_sprites.add(key)
    
    hero_ship.has_key = True  # flag for later access
    print("🔑 Hero gained a Key!")

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False