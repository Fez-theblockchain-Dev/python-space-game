# this file will house the fundamental game play logic of new space invaders python web app game

import pygame
import sys
import time
import os
import random
import json
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
from gameEconomy import game_economy, PlayerWallet

DEBUG_LOG_PATH = "/Users/ramez/Desktop/ramezdev/python-space-game/.cursor/debug.log"
DEBUG_SESSION_ID = "debug-session"

#region agent log
def _agent_log(payload):
    """Write NDJSON debug log entry; keep failures silent for gameplay."""
    try:
        os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
        base = {
            "sessionId": DEBUG_SESSION_ID,
            "timestamp": int(time.time() * 1000),
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps({**base, **payload}) + "\n")
    except Exception:
        pass
#endregion



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

# health group variables/function

def decrement_health(player, screen):
    """
    Decrements player health by 25% and displays the health bar on screen.
    
    Args:
        player: The Player sprite object
        screen: The pygame screen surface to draw on
    """
    # Decrement health by 25%
    player.health = max(0, player.health - 25)
    
    # Health bar dimensions and position (centered at top)
    bar_width = 200
    bar_height = 20
    bar_x = (SCREEN_WIDTH - bar_width) // 2  # Center horizontally
    bar_y = 10  # Position at top of screen
    
    # Draw health bar background (red)
    background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(screen, (255, 0, 0), background_rect)
    
    # Draw health bar fill (green, proportional to health)
    health_width = int((player.health / 100) * bar_width)
    health_rect = pygame.Rect(bar_x, bar_y, health_width, bar_height)
    pygame.draw.rect(screen, (0, 255, 0), health_rect)
    
    # Draw health bar border
    pygame.draw.rect(screen, (255, 255, 255), background_rect, 2)
    
    # Display health percentage text (centered above bar)
    health_text = font.render(f"Health: {player.health}%", True, (255, 255, 255))
    text_rect = health_text.get_rect(center=(SCREEN_WIDTH // 2, bar_y - 15))
    screen.blit(health_text, text_rect)

# creating levels class OOP elements for game loop functionality
class Level (pygame.sprite.Sprite):
    # Class variable to track current level index across instances
    current_level_index = 0
    
    # Level dictionary with progressive difficulty
    # Each level has: rows (alien rows), cols (alien columns), speed (alien movement speed)
    level_dict = {
        0: {"rows": 3, "cols": 8, "speed": 1},   # Level 0: Easy - 3 rows, 8 cols, speed 1
        1: {"rows": 4, "cols": 8, "speed": 2},   # Level 1: Medium - 4 rows, 8 cols, speed 2
        2: {"rows": 4, "cols": 9, "speed": 2},   # Level 2: Medium-Hard - 4 rows, 9 cols, speed 2
        3: {"rows": 5, "cols": 9, "speed": 3},   # Level 3: Hard - 5 rows, 9 cols, speed 3
        4: {"rows": 5, "cols": 10, "speed": 3},  # Level 4: Very Hard - 5 rows, 10 cols, speed 3
        5: {"rows": 6, "cols": 10, "speed": 4}   # Level 5: Extreme - 6 rows, 10 cols, speed 4
    }
    
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
        max_level = max(Level.level_dict.keys())
        if Level.current_level_index < max_level:
            Level.current_level_index += 1
        return Level.current_level_index
    
    @staticmethod
    def get_level_config(level_index=None):
        """Get configuration for a specific level or current level"""
        if level_index is None:
            level_index = Level.current_level_index
        return Level.level_dict.get(level_index, Level.level_dict[0])  # Default to level 0 if invalid
    
    @staticmethod
    def get_alien_rows(level_index=None):
        """Get number of alien rows for a level"""
        config = Level.get_level_config(level_index)
        return config["rows"]
    
    @staticmethod
    def get_alien_cols(level_index=None):
        """Get number of alien columns for a level"""
        config = Level.get_level_config(level_index)
        return config["cols"]
    
    @staticmethod
    def get_alien_speed(level_index=None):
        """Get alien movement speed for a level"""
        config = Level.get_level_config(level_index)
        return config["speed"]
            

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
    def __init__(self, game):
        # def run(self, screen, mouse_pos=None, mouse_clicked=False):
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
        self.alien_setup(rows = 6, cols = 8)
        self.alien_direction = 1
        
        # Level completion tracking
        self.level_just_completed = False
        self.level_complete_counter = 0

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
        
        # Main menu button setup
        menu_button_font = pygame.font.Font(os.path.join(project_root, 'assets/Fonts/hyperspace/Hyperspace Bold Italic.otf'), 30)
        self.menu_button = Button(
            image=None,
            pos=(SCREEN_WIDTH - 100, 30),
            text_input="MENU",
            font=menu_button_font,
            base_color="#d7fcd4",
            hovering_color="White"
        )

        # Background theme setup
        self.current_theme = "PURPLE_NEBULA"  # Default theme
        self.backgrounds = {}
        self._load_backgrounds()

    def _load_backgrounds(self):
        """Load all available background themes"""
        # Flat black background
        black_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        black_bg.fill(BLACK)
        self.backgrounds["BLACK"] = black_bg
        
        # Purple nebula background
        nebula_image = pygame.image.load(os.path.join(project_root, 'assets/512x512_purple_nebula_1.png')).convert()
        nebula_bg = pygame.transform.scale(nebula_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.backgrounds["PURPLE_NEBULA"] = nebula_bg
        
        # Main menu background (purple gradient)
        menu_bg_path = os.path.join(project_root, 'assets/main_menu_background.png')
        if os.path.exists(menu_bg_path):
            try:
                menu_bg_img = pygame.image.load(menu_bg_path).convert()
                menu_bg = pygame.transform.scale(menu_bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.backgrounds["MENU_GRADIENT"] = menu_bg
            except pygame.error:
                print(f"Warning: Could not load {menu_bg_path}")
                # Fallback to black if menu background can't be loaded
                self.backgrounds["MENU_GRADIENT"] = black_bg
        else:
            # Fallback to black if file doesn't exist
            self.backgrounds["MENU_GRADIENT"] = black_bg

    def set_background_theme(self, theme_name):
        """Set the background theme for gameplay"""
        if theme_name in self.backgrounds:
            self.current_theme = theme_name
            return True
        return False

    def get_current_background(self):
        """Get the current background surface"""
        return self.backgrounds.get(self.current_theme, self.backgrounds["BLACK"])

    def cycle_background_theme(self):
        """Cycle to the next available background theme"""
        themes = list(self.backgrounds.keys())
        if themes:
            current_index = themes.index(self.current_theme) if self.current_theme in themes else 0
            next_index = (current_index + 1) % len(themes)
            self.current_theme = themes[next_index]
            return self.current_theme
        return None

    def collision_checks(self):
        #region agent log
        _agent_log({
            "runId": "pre-fix",
            "hypothesisId": "A",
            "location": "game/index.py:collision_checks:entry",
            "message": "collision_checks_entry",
            "data": {
                "lives": self.lives,
                "aliens": len(self.aliens),
                "player_health": getattr(self.player.sprite, "health", None),
            },
        })
        #endregion

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
            # if player/alien collide, take one player life for each time a collision occurs
            for alien in aliens_touching_player:
                self.lives -= 1  # decrement a life by 1 (5 lives before losing game)
                decrement_health(self.player.sprite, screen)

            # Update economy health based on lives (each life = 33.33 health points)
            health_percentage = (self.lives / 3.0) * 100
            self.economy.update_health(int(health_percentage))

            #region agent log
            _agent_log({
                "runId": "pre-fix",
                "hypothesisId": "A",
                "location": "game/index.py:collision_checks:alien_player_collision",
                "message": "alien_player_collision",
                "data": {
                    "collisions": len(aliens_touching_player),
                    "lives_after": self.lives,
                    "health_percentage": health_percentage,
                },
            })
            #endregion

            if self.lives <= 0:
                #region agent log
                _agent_log({
                    "runId": "pre-fix",
                    "hypothesisId": "A",
                    "location": "game/index.py:collision_checks:game_over",
                    "message": "player_out_of_lives",
                    "data": {"lives": self.lives},
                })
                #endregion
                return False  # Signal game over

        #region agent log
        _agent_log({
            "runId": "pre-fix",
            "hypothesisId": "A",
            "location": "game/index.py:collision_checks:exit",
            "message": "collision_checks_exit",
            "data": {"lives": self.lives, "aliens": len(self.aliens)},
        })
        #endregion
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

    def alien_setup(self, rows=None, cols=None, speed=None, x_distance=60, y_distance=48, x_offset=70, y_offset=100):
        """Setup aliens for current level. If rows/cols/speed not provided, uses current level config."""
        # Get level-based configuration if not provided
        if rows is None:
            rows = Level.get_alien_rows()
        if cols is None:
            cols = Level.get_alien_cols()
        if speed is None:
            speed = Level.get_alien_speed()
        
        for row_index in range(rows):
            for col_index in range(cols):
                x = col_index * x_distance + x_offset
                y = row_index * y_distance + y_offset
                alien_sprite = Alien(1, speed, x, y)
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
        coins_text = self.font.render(f"Coins: {self.economy.get_total_coins()}", True, (255, 215, 0))  # Gold color
        screen.blit(coins_text, (10, 40))
    
    def display_level(self):
        """Display current level"""
        level_text = self.font.render(f"Level: {Level.current_level_index + 1}", True, (255, 255, 255))
        screen.blit(level_text, (10, 70))

    def display_health(self):
        """Display player health bar"""
        # Health bar dimensions and position (centered at top)
        bar_width = 200
        bar_height = 20
        bar_x = (SCREEN_WIDTH - bar_width) // 2  # Center horizontally
        bar_y = 10  # Position at top of screen
        
        # Draw health bar background (red)
        background_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(screen, (255, 0, 0), background_rect)
        
        # Draw health bar fill (green, proportional to health)
        health_width = int((self.player.sprite.health / 100) * bar_width)
        health_rect = pygame.Rect(bar_x, bar_y, health_width, bar_height)
        pygame.draw.rect(screen, (0, 255, 0), health_rect)
        
        # Draw health bar border
        pygame.draw.rect(screen, (255, 255, 255), background_rect, 2)
        
        # Display health percentage text
        health_text = self.font.render(f"Health: {self.player.sprite.health}%", True, (255, 255, 255))
        text_rect = health_text.get_rect(center=(SCREEN_WIDTH // 2, bar_y - 15))
        screen.blit(health_text, text_rect)

    def victory_message(self):
        """Display victory message if all aliens destroyed and advance to next level"""
        if len(self.aliens) == 0 and not self.level_just_completed:
            # Check if there are more levels
            max_level = max(Level.level_dict.keys())
            current_level = Level.current_level_index
            
            if current_level < max_level:
                # Mark level as completed
                self.level_just_completed = True
                self.level_complete_counter = 180  # Show message for ~3 seconds at 60 FPS
                
                # Advance to next level
                Level.increment_level()
                # Setup aliens for the new level
                self.alien_setup()  # Uses current level config automatically
                
        # Display level complete message if timer is active
        if self.level_just_completed:
            max_level = max(Level.level_dict.keys())
            if Level.current_level_index <= max_level:
                completed_level = Level.current_level_index + 1
                starting_level = Level.current_level_index + 1
                level_text = self.font.render(f"LEVEL {completed_level} COMPLETE! LEVEL {starting_level} STARTING!", True, (255, 255, 0))
                text_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
                screen.blit(level_text, text_rect)
            
            self.level_complete_counter -= 1
            if self.level_complete_counter <= 0:
                self.level_just_completed = False
        elif len(self.aliens) == 0:
            # All levels completed - final victory
            max_level = max(Level.level_dict.keys())
            if Level.current_level_index >= max_level:
                victory_text = self.font.render("VICTORY! ALL LEVELS COMPLETE!", True, (255, 255, 0))
                text_rect = victory_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                screen.blit(victory_text, text_rect)

    def run(self, screen, mouse_pos=None, mouse_clicked=False):
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
        self.display_level()
        self.display_health()
        self.victory_message()
        
        # Display and handle main menu button
        if mouse_pos:
            self.menu_button.change_color(mouse_pos)
        self.menu_button.update(screen)
        
        # Check if menu button was clicked
        if mouse_clicked and mouse_pos:
            if self.menu_button.check_input(mouse_pos):
                return "menu"  # Signal to return to main menu
        
        # Sync economy score with game score
        self.economy.score = self.score
        
        return True


      
    print("game is starting...")
    clock = pygame.time.Clock()
    running = True
    

    
    # Setup initial aliens using level 0 configuration
    alien_setup = game.alien_setup()  
    
    # Setup obstacles
    game.create_multiple_obstacles(game.obstacle_x_positions, x_start=SCREEN_WIDTH / 15, y_start=480)  # pyright: ignore[reportUndefinedVariable]

    # Game loop
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True

        # Draw background using current theme
        screen.blit(game.get_current_background(), (0, 0)) 

        # Run game update (handles all updates, collisions, and drawing)
        game_result = game.run(screen, mouse_pos, mouse_clicked)
        
        # Check if player wants to return to menu
        def menu_redirect(self, screen):
            if game_result == "Lose":
                return main_menu() 
        
        if not game_result:
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

    # Game loop ended - return to caller (main menu or exit)
    # Don't quit pygame here as main menu may still be running

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





        