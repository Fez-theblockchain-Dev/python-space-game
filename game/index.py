# this file will house the fundamental game play logic of new space invaders python web app game

import pygame
import sys
import time
import os
import random
from pygame.locals import * #For useful variables
from typing import Any
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from spaceship import SpaceShip
from laser import Laser
from alien import Alien, check_alien_edges
import tkinter as tk
from button import Button
from player import Player







# Initialize pygame
pygame.init()


# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders")

# Colors
YELLOW = (255, 255, 100) #Yellow for alien_ships
RED = (255, 0, 0) #red for laser
ROYAL_BLUE = (65, 105, 225) 
BLACK = (0, 0, 0) #screen overlay to create multiple screens illusion

screen.fill('black')
# Get the directory of this script to handle paths correctly
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Window background space image
nebula_image = pygame.image.load(os.path.join(project_root, 'assets/512x512_purple_nebula_1.png')).convert()
nebula_bg = pygame.transform.scale(nebula_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Font link
font = pygame.font.Font(os.path.join(project_root, 'assets/Fonts/hyperspace/Hyperspace Bold Italic.otf'), 20)

# HeroShip class definition
class HeroShip(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, lives,level, health=100, ):
        super().__init__()
        self.image = pygame.image.load(os.path.join(project_root, 'assets/spaceship.png'))
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
        pygame.init(self)
        """Get current level index, reset to 0 if new game, otherwise return last level"""
        if new_game:
            Level.current_level_index = 0
            return Level.current_level_index
        else:
            return Level.current_level_index
    
    @staticmethod
    def increment_level():
        """Move to next level if available"""
        if Level.current_level_index < len(Level.level_array) - 1:
            Level.current_level_index += 1
        return Level.current_level_index
            




    #function for screen messages
    def screen_msg(self, arr): 
        # Draw celebration elements
        level_text = font.render(f"LEVEL {arr} COMPLETE!", True, (255, 255, 0))
        text_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        screen.blit(level_text, text_rect)   
        if level_text:
            print(f"Currently on Lvl: {arr}")

    pygame.display.set_mode((400, 400), pygame.RESIZABLE)
    
    # conditional statement to handle the logic of when level_text & text_rect will render on screen
       # Level up text 
    
    def current_level(self, arr):
        return (Level.current_level_index)
    level_text = font.render(f"LEVEL {current_level} COMPLETE!", True, (255, 255, 0))
    text_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    total_aliens = 5 
    if total_aliens == 0:
        print(f"Congrats! you've beaten all the enemies & now reached level {arr.add}")

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
            
            
from laser import Laser
# alien collisions
alien = Alien(1, 2, 100, 100)  # Create an alien instance
laser_audio_path = os.path.join(project_root, "audio/audio_laser.wav")

def shoot_laser(self):
    if self.laser == True: #if laser is fired, play the laser audio
        laser_sound = pygame.mixer.Sound(laser_audio_path)
        laser_sound.play()

# Initialize score and create aliens group
score = 0
aliens_group = pygame.sprite.Group()

# Create some aliens to display
for row in range(3):
    for col in range(8):
        x = 100 + col * 80
        y = 50 + row * 60
        alien = Alien(1, 2, x, y)
        aliens_group.add(alien)


# Game loop setup

class Game:
    
    def __init__(self):
        # Player setup
        player_sprite = Player((SCREEN_WIDTH / 2, SCREEN_HEIGHT), SCREEN_WIDTH, 5)
        self.player = pygame.sprite.GroupSingle(player_sprite)

        # health and score setup
        self.lives = 3
        self.live_surf = pygame.image.load('../graphics/player.png').convert_alpha()
        self.live_x_start_pos = SCREEN_WIDTH - (self.live_surf.get_size()[0] * 2 + 20)
        self.score = 0
        self.font = pygame.font.Font('assets/Fonts/hyperspace/Hyperspace Bold Italic.otf', 20)

        # Obstacle setup - commented out as obstacle class not fully defined
        self.shape = Block.shape
        self.block_size = 6
        self.blocks = pygame.sprite.Group()
        self.obstacle_amount = 4
        self.obstacle_x_positions = [num * (SCREEN_WIDTH / self.obstacle_amount) for num in range(self.obstacle_amount)]
        self.create_multiple_obstacles(*self.obstacle_x_positions, x_start = SCREEN_WIDTH / 15, y_start = 480)

        # Alien setup
        self.aliens = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()
        # self.alien_setup(rows = 6, cols = 8)
        self.alien_direction = 1

        # Extra setup
        self.extra = pygame.sprite.GroupSingle()
        self.extra_spawn_time = random.randint(40,80)

        music = pygame.mixer.Sound('../audio/music.wav')
        music.set_volume(0.2)
        music.play(loops = -1)
        self.laser_sound = pygame.mixer.Sound('../audio/laser.wav')
        self.laser_sound.set_volume(0.5)
        self.explosion_sound = pygame.mixer.Sound('../audio/explosion.wav')
        self.explosion_sound.set_volume(0.3)


def main():
    print("game is starting...")
    clock = pygame.time.Clock()
    running = True
    Level = [0,1,2,3,4,5,6,7,8,9,10,11,12]
    lives = 5
    current_level_index = 0
    # the player has 30 seconds/level to eliminate all the aliens
    time_limit = 30 
    new_game = False


    # Game loop
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:
                    # Create a new laser at the hero ship's position, moving upward
                    laser = Laser(
                        position=(hero_ship.rect.centerx, hero_ship.rect.top),
                        speed=-8,  # Negative speed moves upward
                        screen_height=SCREEN_HEIGHT,
                        false=False
                    )
                    laser_group.add(laser)

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

        # Check for collisions between lasers and aliens
        aliens_hit = pygame.sprite.groupcollide(laser_group, aliens_group, True, True)
        if aliens_hit:
            for laser, hit_aliens in aliens_hit.items():
                for alien in hit_aliens:
                    score += alien.value

        # Draw all game objects
        hero_group.draw(screen)
        spaceship_group.draw(screen)
        laser_group.draw(screen)
        aliens_group.draw(screen)

        # Update groups
        hero_group.update()
        spaceship_group.update()
        laser_group.update()
        aliens_group.update(1)  # Pass direction for alien movement
        
        # Display score
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
        
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

# new 'Key' class that will hold the object that appears on the players screen when the mystery_ship is destroyed
class Key:
    def mystery_ship_destroyed(self, x, y,):
        if self.mystery_ship_alive is False:
            return 'mystery ship has been destroyed'
        else:
            return None
    
    
    # Key functionality can be added later
    hero_ship.has_key = True  # flag for later access
    print("Hero gained a Key!🔑")
                    
            
try:
    from pygame.locals import QUIT
except ImportError:
    print("Could not import QUIT from pygame.locals. Check if pygame is installed.")

from collections import deque


# These functions and code blocks are part of the Game class and should be moved there
# when the Game class is fully implemented. Commented out for now to avoid errors.

# x_start = int()
# y_start = int()



def create_obstacle(self, x_start, y_start, offset_x):
    for row_index, row in enumerate[Any](self.shape):
        for col_index,col in enumerate[Any](row):
            if col == 'x':
                x = x_start + col_index * self.block_size + offset_x
                y = y_start + row_index * self.block_size
                block = create_obstacle.Block(self.block_size,(241,79,80),x,y)
                self.blocks.add(block)


def create_multiple_obstacles(self,*offset,x_start,y_start):
		for offset_x in offset:
			self.create_obstacle(x_start,y_start,offset_x)

def alien_setup(self,rows,cols, x_distance = 60, y_distance = 48, x_offset = 70, y_offset = 100):
    for row_index, row in enumerate[Any](self.shape):
        for col_index, col in enumerate[Any](rows):
            x = cols_index * x_distance + x_offset
            y = row_index * y_distance + y_offset
            alien_sprite = Alien('red',x,y)
            self.aliens.add(alien_sprite)



if aliens_hit:
    for alien in aliens_hit:
        self.score += alien.value
    laser.kill()
    self.explosion_sound.play()

    aliens_hit = False
    


# if self.alien_lasers:
#     for laser in self.alien_lasers:
#         if pygame.sprite.spritecollide(laser,self.blocks,True):
#             laser.kill()


if pygame.sprite.spritecollide(self,laser,player,False):
    laser.kill()
    self.lives -= 1
    if self.lives <= 0:
        pygame.quit()
        sys.exit()

if self.aliens:
    for aliens in self.aliens:
        pygame.sprite.spritecollide(alien,self.blocks, True)




def run(self):
    self.player.update()
    
    self.alien_lasers.update()
    self.extra.update()
    
    self.aliens.update(self.alien_direction)
    self.alien_position_checker()
    self.extra_alien_timer()
    self.collision_checks()
    
    self.player.sprite.lasers.draw(screen)
    self.player.draw(screen)
    self.blocks.draw(screen)
    self.aliens.draw(screen)
    self.alien_lasers.draw(screen)
    self.extra.draw(screen)
    self.display_lives()
    self.display_score()
    self.victory_message()


        