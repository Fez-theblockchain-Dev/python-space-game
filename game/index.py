# this file will house the fundamental game play logic of new space invaders python web app game

import pygame
import sys
import time
import os
import random
from pygame.locals import * #For useful variables
from typing import Any
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from obstacle import Block, shape
from spaceship import SpaceShip
from laser import Laser
from alien import Alien, check_alien_edges
import tkinter as tk
from button import Button
from player import Player
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gameEconomy import game_economy







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
    
    def current_level(self, arr):
        return (Level.current_level_index)

    # alien 'collisions' w/ laser logic

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
        x_start = (0,0)
        y_start = (0,100)

        # Economy system setup
        self.economy = game_economy(initial_health=100)

        # health and score setup
        self.lives = 3
        try:
            self.live_surf = pygame.image.load(os.path.join(project_root, 'graphics/player.png')).convert_alpha()
            self.live_x_start_pos = SCREEN_WIDTH - (self.live_surf.get_size()[0] * 2 + 20)
        except:
            self.live_surf = None
            self.live_x_start_pos = SCREEN_WIDTH - 100
        self.score = 0
        self.font = pygame.font.Font(os.path.join(project_root, 'assets/Fonts/hyperspace/Hyperspace Bold Italic.otf'), 20)

        # Obstacle setup
        self.shape = shape
        self.block_size = 6
        self.blocks = pygame.sprite.Group()
        self.obstacle_amount = 4
        self.obstacle_x_positions = [num * (SCREEN_WIDTH / self.obstacle_amount) for num in range(self.obstacle_amount)]
        # Create obstacles - will be implemented in create_multiple_obstacles method
        # self.create_multiple_obstacles(*self.obstacle_x_positions, x_start=SCREEN_WIDTH / 15, y_start=480)

        # Alien setup
        self.aliens = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()
        # self.alien_setup(rows = 6, cols = 8)
        self.alien_direction = 1

        # Extra setup
        self.extra = pygame.sprite.GroupSingle()
        self.extra_spawn_time = random.randint(40,80)

        # Audio setup - handle missing files gracefully
        try:
            music = pygame.mixer.Sound(os.path.join(project_root, 'audio/music.wav'))
            music.set_volume(0.2)
            music.play(loops = -1)
        except:
            pass
        try:
            self.laser_sound = pygame.mixer.Sound(os.path.join(project_root, 'audio/laser.wav'))
            self.laser_sound.set_volume(0.5)
        except:
            self.laser_sound = None
        try:
            self.explosion_sound = pygame.mixer.Sound(os.path.join(project_root, 'audio/explosion.wav'))
            self.explosion_sound.set_volume(0.3)
        except:
            self.explosion_sound = None

    def collision_checks(self):
        # player lasers 
        if self.player.sprite.lasers:
            for laser in self.player.sprite.lasers:
                # obstacle collisions
                if pygame.sprite.spritecollide(laser, self.blocks, True):
                    laser.kill()
                
                # alien collisions
                aliens_hit = pygame.sprite.spritecollide(laser, self.aliens, True)
                if aliens_hit:
                    for alien in aliens_hit:
                        self.score += alien.value
                        # Update economy: add score and coins (1 coin per alien value point)
                        self.economy.add_score(alien.value)
                        self.economy.add_coins(alien.value)
                    laser.kill()
                    if self.explosion_sound:
                        self.explosion_sound.play()
        
        # direct alien collision with player (aliens touching player)
        aliens_touching_player = pygame.sprite.spritecollide(self.player.sprite, self.aliens, True)
        if aliens_touching_player:
            # Remove all aliens that touched the player
            for alien in aliens_touching_player:
                if self.explosion_sound:
                    self.explosion_sound.play()
            self.lives -= 1
            # Update economy health based on lives (each life = 33.33 health points)
            health_percentage = (self.lives / 3.0) * 100
            self.economy.update_health(int(health_percentage))
            if self.lives <= 0:
                return False  # Signal game over
        
        return True  # Game continues

    def create_obstacle(self, x_start, y_start, offset_x):
        for row_index, row in enumerate(self.shape):
            for col_index, col in enumerate(row):
                if col == 'x':
                    x = x_start + col_index * self.block_size + offset_x
                    y = y_start + row_index * self.block_size
                    block = Block(self.block_size, (241, 79, 80), x, y)
                    self.blocks.add(block)

    def create_multiple_obstacles(self, *offset, x_start, y_start):
        for offset_x in offset:
            self.create_obstacle(x_start, y_start, offset_x)

    def alien_setup(self, rows, cols, x_distance=60, y_distance=48, x_offset=70, y_offset=100):
        for row_index in range(rows):
            for col_index in range(cols):
                x = col_index * x_distance + x_offset
                y = row_index * y_distance + y_offset
                alien_sprite = Alien(1, 2, x, y)
                self.aliens.add(alien_sprite)

    def alien_position_checker(self):
        """Check if aliens hit edges and reverse direction"""
        for alien in self.aliens:
            if alien.rect.right >= SCREEN_WIDTH or alien.rect.left <= 0:
                self.alien_direction *= -1
                for a in self.aliens:
                    a.rect.y += 20  # Move down
                break

    def extra_alien_timer(self):
        """Handle extra alien spawning"""
        self.extra_spawn_time -= 1
        if self.extra_spawn_time <= 0:
            self.extra_spawn_time = random.randint(400, 800)

    def display_lives(self):
        """Display player lives"""
        if self.live_surf:
            for live_index in range(self.lives):
                x = self.live_x_start_pos + (live_index * (self.live_surf.get_size()[0] + 10))
                screen.blit(self.live_surf, (x, 8))

    def display_score(self):
        """Display current score"""
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))
    
    def display_coins(self):
        """Display current coins/gold"""
        coins_text = self.font.render(f"Coins: {self.economy.coins}", True, (255, 215, 0))  # Gold color
        screen.blit(coins_text, (10, 40))

    def victory_message(self):
        """Display victory message if all aliens destroyed"""
        if len(self.aliens) == 0:
            victory_text = self.font.render("VICTORY!", True, (255, 255, 0))
            text_rect = victory_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(victory_text, text_rect)

    def run(self, screen):
        """Main game loop update method"""
        self.player.update()
        
        # Removed alien_lasers.update() - aliens don't shoot
        self.extra.update()
        
        self.aliens.update(self.alien_direction)
        self.alien_position_checker()
        self.extra_alien_timer()
        game_continues = self.collision_checks()
        if not game_continues:
            return False
        
        self.player.sprite.lasers.draw(screen)
        self.player.draw(screen)
        self.blocks.draw(screen)
        self.aliens.draw(screen)
        # Removed alien_lasers.draw() - aliens don't shoot
        self.extra.draw(screen)
        self.display_lives()
        self.display_score()
        self.display_coins()
        self.victory_message()
        
        # Sync economy score with game score
        self.economy.score = self.score
        
        return True


def main():
    print("game is starting...")
    clock = pygame.time.Clock()
    running = True
    
    # Create game instance
    game = Game()
    
    # Setup initial aliens
    game.alien_setup(rows=3, cols=8)
    
    # Setup obstacles
    game.create_multiple_obstacles(*game.obstacle_x_positions, x_start=SCREEN_WIDTH / 15, y_start=480)

    # Game loop
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Draw background
        screen.blit(nebula_bg, (0, 0)) 

        # Run game update (handles all updates, collisions, and drawing)
        game_continues = game.run(screen)
        if not game_continues:
            # Game over screen
            game_over_text = font.render("GAME OVER", True, (255, 0, 0))
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(game_over_text, text_rect)
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False
        
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





        