# this file will house the fundamental game play logic of new space invaders python web app game

# from logging import _Level
from _typeshed import Self
from cgi import print_arguments
from ctypes import resize
from nt import kill
import numbers
# from pickle import TRUE
from re import S
import string
import symbol
from turtle import screensize
from unittest import result
import pygame
import sys
import time
import os
import random
from pygame.locals import * #For useful variables
from spaceship import SpaceShip
from laser import Laser
from alien import Alien
import tkinter as tk
import font 
from level import Level




# Initialize pygame
pygame.init()

# Set up the display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH /2 , SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")

# Colors
YELLOW = (255, 255, 100) #Yellow for alien_ships
RED = (255, 0, 0) #red for laser
ROYAL_BLUE = (65, 105, 225) 

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
    # Class variable to track current level index across instances
    current_level_index = 0
    level_array = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    
    def __init__(self, level_number = None):
        super().__init__()
        self.level_number = level_number if level_number is not None else Level.current_level_index
        self.lives = 5

    
    def show_level_up_message(self, screen, font):
        """Display animated level-up celebration"""
        # Create celebration overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
      
        # responsive screen size handeling
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        print(f"Screen size:{screen_width}x{screen_height}")
        root.destroy()
    

    def get_current_level(self, new_game = False):
        """Get current level index, reset to 0 if new game, otherwise return last level"""
        if new_game:
            Level.current_level_index = 0
            return Level.current_level_index
        else:
            return Level.current_level_index
    
    def increment_level(self):
        """Move to next level if available"""
        if Level.current_level_index < len(Level.level_array) - 1:
            Level.current_level_index += 1
        return Level.current_level_index
            

    
    
    # Level up text
    current_level = Level.level_array[Level.current_level_index]
    level_text = font.render(f"LEVEL {current_level} COMPLETE!", True, (255, 255, 0))
    text_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    
    # Draw celebration elements

    screen.blit(overlay, (0, 0))
    level_text and text_rect = True
    screen.blit(level_text, text_rect)
    pygame.display.set_mode((400, 400)),pygame.RESIZABLE
    
    # conditional statement to handle the logic of when level_text & text_rect will render on screen
    total_aliens = 5 
    if total_aliens == 0:
        print(f"Congrats! you've beaten all the enemies & now reached level {Level.current_level_index}")

    # Add particle effects, animations, etc.
    pygame.display.flip()
    pygame.time.wait(2000)  # Show for 2 seconds

    # alien 'collisions' w/ laser logic

def collision_checks(self):
		# player lasers 
    if self.player.sprite.lasers:
        for laser in self.player.sprite.lasers:
        # obstacle collisions
            if pygame.sprite.spritecollide(laser,self.blocks,True):
                laser.kill()
            
            

				# alien collisions
laser = Laser() #setting laser variable to the Laser class that I have in the it's respective file
alien = Alien(1, 2, 100, 100)  # Create an alien instance

# Initialize score and create aliens group
score = 0
aliens_group = pygame.sprite.Group()

aliens_hit = pygame.sprite.spritecollide(laser, aliens_group, True)
if aliens_hit:
    for alien in aliens_hit:
        score += alien.value
        laser.kill()
        # explosion_sound.play()  # Uncomment when sound is available


# Game loop

player = HeroShip

if __name__ == "__main__":
    main()
    def main():
        print("game is starting...")
        player.sprite = player(SCREEN_WIDTH /2, SCREEN_HEIGHT, 5)
        player_group = pygame.sprite.GroupSingle(player)
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
        if new_game (True):
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
        print (current_spaceship_health)

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

# new 'Key' class that will hold the object that appears on the players screen when the mystery_ship is destroyed
class Key:
    def mystery_ship_destroyed(self, x, y,):
        if self.mystery_ship_alive is False:
            return 'mystery ship has been destroyed'
        else:
            return None
        

# hits = pygame.sprite.groupcollide(hero_bullets, Mystery_Ship, True, True)
hits = []
for hit in hits:
    # When a mystery ship is destroyed
    key = symbol(hit.rect.centerx, hit.rect.centery)
    sprite.add(key)

    sprite = laser 

    
    hero_ship.has_key = True  # flag for later access
    print("Hero gained a Key!🔑")

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                    quit()
                    
            
try:
    from pygame.locals import QUIT
except ImportError:
    print("Could not import QUIT from pygame.locals. Check if pygame is installed.")

from collections import deque





    


