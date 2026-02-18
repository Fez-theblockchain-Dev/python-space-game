# this file will house the fundamental game play logic of new space invaders python web app game

import asyncio  # Required for Pygbag web deployment
import pygame
import sys
import time
import os
import random
import json
from pygame.locals import * #For useful variables
from typing import Any
from config import SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_BACKGROUND_THEME
from treasureChest import TreasureChest
from obstacle import Block, shape
from spaceship import SpaceShip
from laser import Laser
from alien import Alien, AlienDiagonal, AlienDiver, MysteryShip, check_alien_edges
from treasureChest import TreasureChest, Key
from button import Button
from player import Player
from mainMenu import theme_manager
from mainMenu import main_menu  # Entry point for web: menu -> play -> game

# Detect if running in browser (Pygbag/Emscripten)
IS_BROWSER = sys.platform == "emscripten"

# Add parent directory to path so we can import from backend_apis
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend_apis.gameEconomy import GameEconomy

# Debug logging configuration - only used on desktop
DEBUG_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cursor", "debug.log")
DEBUG_SESSION_ID = "debug-session"

#region agent log
def _agent_log(payload):
    """Write NDJSON debug log entry; skip in browser environment."""
    # Skip file logging in browser - no filesystem access
    if IS_BROWSER:
        return
    
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


# Get the directory of this script to handle paths correctly
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Window background space image
nebula_image = pygame.image.load(os.path.join(project_root, DEFAULT_BACKGROUND_THEME)).convert()
nebula_bg = pygame.transform.scale(nebula_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

# Font link
title_font = pygame.font.Font(os.path.join(project_root, 'assets/Fonts/hyperspace/Hyperspace Bold Italic.otf'), 36)
title_surface = title_font.render("Space Invaders", True, (255, 255, 255))
title_rect = title_surface.get_rect(centerx=SCREEN_WIDTH // 2, y=20)  # 20px from top

# General font for UI text (health, level messages, game over, etc.)
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
    # Each level has: 
    #   - rows/cols: alien_1 formation size
    #   - speed: base alien movement speed
    #   - diagonal_count: number of alien_2 (diagonal) aliens
    #   - diver_count: number of alien_3 (diver) aliens
    level_dict = {
        0: {"rows": 3, "cols": 8, "speed": 1, "diagonal_count": 0, "diver_count": 0},    # Level 0: Easy - only type 1
        1: {"rows": 4, "cols": 8, "speed": 2, "diagonal_count": 4, "diver_count": 0},    # Level 1: +4 diagonal aliens
        2: {"rows": 4, "cols": 9, "speed": 2, "diagonal_count": 6, "diver_count": 3},    # Level 2: +6 diagonal, +3 divers
        3: {"rows": 5, "cols": 9, "speed": 3, "diagonal_count": 8, "diver_count": 5},    # Level 3: +8 diagonal, +5 divers
        4: {"rows": 5, "cols": 10, "speed": 3, "diagonal_count": 10, "diver_count": 7},  # Level 4: +10 diagonal, +7 divers
        5: {"rows": 6, "cols": 10, "speed": 4, "diagonal_count": 12, "diver_count": 10}  # Level 5: +12 diagonal, +10 divers
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
        
        # Use config screen dimensions (compatible with web/Pygbag)
        print(f"Screen size: {SCREEN_WIDTH}x{SCREEN_HEIGHT}")
    

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
    
    @staticmethod
    def get_diagonal_count(level_index=None):
        """Get number of diagonal (type 2) aliens for a level"""
        config = Level.get_level_config(level_index)
        return config.get("diagonal_count", 0)
    
    @staticmethod
    def get_diver_count(level_index=None):
        """Get number of diver (type 3) aliens for a level"""
        config = Level.get_level_config(level_index)
        return config.get("diver_count", 0)
            

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

# alien collisions
alien = Alien(1, 2, 100, 100)  # Create an alien instance

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
        
        # Economy system setup
        self.economy = GameEconomy(initial_health=100)

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
        self.aliens = pygame.sprite.Group()  # Type 1: horizontal formation
        self.diagonal_aliens = pygame.sprite.Group()  # Type 2: diagonal movement
        self.diver_aliens = pygame.sprite.Group()  # Type 3: straight down dive
        self.alien_lasers = pygame.sprite.Group()
        self.alien_setup()  # Uses level config for predetermined alien counts
        self.alien_direction = 1
        
        # Mystery Ship and Treasure Chest setup
        self.mystery_ship = pygame.sprite.GroupSingle()
        self.treasure_chests = pygame.sprite.Group()
        self.keys = pygame.sprite.Group()
        self.mystery_ship_spawn_time = random.randint(400, 800)  # Frames until mystery ship spawns
        self.player_has_key = False
        self.mystery_bounty_end_time = 0
        self.mystery_bounty_duration_ms = 2500
        self._mystery_bounty_image = None
        
        # Level completion tracking
        self.level_just_completed = False
        self.level_complete_counter = 0
        self.level_bonus_earned = 0  # Track bonus coins earned for display

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
        
        # Pause button setup
        self.pause_button = Button(
            image=None,
            pos=(SCREEN_WIDTH - 200, 30),
            text_input="PAUSE",
            font=menu_button_font,
            base_color="#d7fcd4",
            hovering_color="White"
        )

        # Wallet button setup
        self.wallet_button = Button(
            image=None,
            pos=(SCREEN_WIDTH - 360, 30),
            text_input="WALLET",
            font=menu_button_font,
            base_color="#d7fcd4",
            hovering_color="White"
        )
        self.show_wallet_panel = False
        
        # Pause state
        self.is_paused = False
        
        # Mute button setup (speaker icon)
        self.is_muted = False
        self.mute_button_size = 30
        self.mute_button_pos = (SCREEN_WIDTH - 280, 30)
        self._create_speaker_icons()

        # Background theme setup
        self.current_theme = "PURPLE_NEBULA"  # Default theme
        self.backgrounds = {}
        self._load_backgrounds()

    def _create_speaker_icons(self):
        """Create speaker icons for mute/unmute button"""
        size = self.mute_button_size
        
        # Unmuted speaker icon (speaker with sound waves)
        self.speaker_unmuted = pygame.Surface((size, size), pygame.SRCALPHA)
        # Speaker body
        pygame.draw.polygon(self.speaker_unmuted, (215, 252, 212), [
            (4, 10), (10, 10), (18, 4), (18, 26), (10, 20), (4, 20)
        ])
        # Sound waves
        pygame.draw.arc(self.speaker_unmuted, (215, 252, 212), (16, 6, 10, 18), -1.0, 1.0, 2)
        pygame.draw.arc(self.speaker_unmuted, (215, 252, 212), (20, 3, 12, 24), -1.0, 1.0, 2)
        
        # Muted speaker icon (speaker with X)
        self.speaker_muted = pygame.Surface((size, size), pygame.SRCALPHA)
        # Speaker body (grayed out)
        pygame.draw.polygon(self.speaker_muted, (150, 150, 150), [
            (4, 10), (10, 10), (18, 4), (18, 26), (10, 20), (4, 20)
        ])
        # Red X for muted
        pygame.draw.line(self.speaker_muted, (255, 80, 80), (20, 8), (28, 22), 3)
        pygame.draw.line(self.speaker_muted, (255, 80, 80), (28, 8), (20, 22), 3)
        
        # Button rect for click detection
        self.mute_button_rect = pygame.Rect(
            self.mute_button_pos[0] - size // 2,
            self.mute_button_pos[1] - size // 2,
            size, size
        )

    def toggle_mute(self):
        """Toggle mute state for laser sound"""
        self.is_muted = not self.is_muted
        # Update player's laser sound
        if self.player.sprite.laser_sound:
            if self.is_muted:
                self.player.sprite.laser_sound.set_volume(0)
            else:
                self.player.sprite.laser_sound.set_volume(0.5)
        return self.is_muted

    def draw_mute_button(self, screen, mouse_pos=None):
        """Draw the mute/unmute button"""
        # Choose icon based on mute state
        icon = self.speaker_muted if self.is_muted else self.speaker_unmuted
        
        # Draw with hover effect
        icon_rect = icon.get_rect(center=self.mute_button_pos)
        
        # Highlight on hover
        if mouse_pos and self.mute_button_rect.collidepoint(mouse_pos):
            # Draw highlight circle behind icon
            pygame.draw.circle(screen, (100, 100, 100), self.mute_button_pos, self.mute_button_size // 2 + 4)
        
        screen.blit(icon, icon_rect)

    def check_mute_button_click(self, mouse_pos):
        """Check if mute button was clicked"""
        if self.mute_button_rect.collidepoint(mouse_pos):
            self.toggle_mute()
            return True
        return False

    def _load_backgrounds(self):
        """Load all available background themes"""
        # Flat black background
        black_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        black_bg.fill(BLACK)
        self.backgrounds["BLACK"] = black_bg
        
        # Purple nebula background (using config default)
        nebula_image = pygame.image.load(os.path.join(project_root, DEFAULT_BACKGROUND_THEME)).convert()
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
            "location": "game/main.py:collision_checks:entry",
            "message": "collision_checks_entry",
            "data": {
                "lives": self.lives,
                "aliens": len(self.aliens),
                "diagonal_aliens": len(self.diagonal_aliens),
                "diver_aliens": len(self.diver_aliens),
                "player_health": getattr(self.player.sprite, "health", None),
            },
        })
        #endregion

        # player lasers - use list() copy to safely remove sprites during iteration
        # (Pygbag/Emscripten crashes if sprite group is modified during iteration)
        if self.player.sprite.lasers:
            for laser in list[Laser](self.player.sprite.lasers):
                # obstacle collisions
                if pygame.sprite.spritecollide(laser, self.blocks, True):
                    laser.kill()
                    continue  # laser is gone, skip remaining checks
                
                # alien collisions - check all alien groups
                # Type 1: Standard formation aliens
                aliens_hit = pygame.sprite.spritecollide(laser, self.aliens, True)
                # Type 2: Diagonal aliens
                diagonal_hit = pygame.sprite.spritecollide(laser, self.diagonal_aliens, True)
                # Type 3: Diver aliens
                diver_hit = pygame.sprite.spritecollide(laser, self.diver_aliens, True)
                
                # Mystery Ship collision
                mystery_hit = pygame.sprite.spritecollide(laser, self.mystery_ship, False)
                if mystery_hit:
                    for mystery in mystery_hit:
                        is_destroyed = mystery.take_damage(50)  # 3 hits to destroy (50 damage × 3 = 150 health)
                        if is_destroyed:
                            self.score += mystery.value
                            self.economy.add_score(mystery.value)
                            self.economy.add_coins(mystery.value * 2)  # Double coins for mystery ship
                            self.mystery_bounty_end_time = pygame.time.get_ticks() + self.mystery_bounty_duration_ms
                            # Spawn treasure chest at mystery ship location
                            treasure = TreasureChest.spawn_from_mystery_ship(mystery.rect)
                            self.treasure_chests.add(treasure)
                            # Spawn a key that falls down for the player to collect
                            key = Key(mystery.rect.centerx + 50, mystery.rect.centery)
                            self.keys.add(key)
                            mystery.kill()
                            if self.explosion_sound:
                                self.explosion_sound.play()
                    laser.kill()
                    continue  # laser is gone, skip remaining checks
                
                all_hits = aliens_hit + diagonal_hit + diver_hit
                if all_hits:
                    for alien in all_hits:
                        self.score += alien.value
                        # Update economy: add score and coins (1 coin per alien value point)
                        self.economy.add_score(alien.value)
                        self.economy.add_coins(alien.value)
                    laser.kill()
                    if self.explosion_sound:
                        self.explosion_sound.play()
        
        # Player collision with keys
        for key in list(self.keys):
            if pygame.sprite.collide_rect(self.player.sprite, key):
                key.collect()
                self.player_has_key = True
        
        # Player collision with treasure chests
        for chest in list(self.treasure_chests):
            if pygame.sprite.collide_rect(self.player.sprite, chest):
                if chest.locked and self.player_has_key:
                    rewards = chest.unlock(has_key=True)
                    if rewards:
                        # Chest coins are already randomized in TreasureChest using config min/max values.
                        randomized_bonus = rewards.get('coins', 0)
                        if randomized_bonus > 0:
                            self.score += randomized_bonus
                            self.economy.add_coins(randomized_bonus)
                            # Persist chest rewards to wallet immediately on collection.
                            self.economy.save_session_coins()
                            self.economy.sync_wallet()
                        # Apply health packs if any
                        if rewards.get('health_packs', 0) > 0:
                            health_gain = rewards['health_packs'] * 10
                            self.player.sprite.health = min(100, self.player.sprite.health + health_gain)
                        self.player_has_key = False  # Consume the key
                        chest.kill()  # Remove chest after unlocking
                elif chest.locked and not self.player_has_key:
                    # Visual feedback that player needs a key (optional)
                    pass

        # direct alien collision with player (aliens touching player) - check all groups
        aliens_touching_player = pygame.sprite.spritecollide(self.player.sprite, self.aliens, True)
        diagonal_touching_player = pygame.sprite.spritecollide(self.player.sprite, self.diagonal_aliens, True)
        diver_touching_player = pygame.sprite.spritecollide(self.player.sprite, self.diver_aliens, True)
        aliens_touching_player = aliens_touching_player + diagonal_touching_player + diver_touching_player
        if aliens_touching_player:
            # if player/alien collide, decrement health by 25% for each collision
            for alien in aliens_touching_player:
                decrement_health(self.player.sprite, screen)

            # Update economy health based on player's actual health
            self.economy.update_health(int(self.player.sprite.health))

            #region agent log
            _agent_log({
                "runId": "pre-fix",
                "hypothesisId": "A",
                "location": "game/main.py:collision_checks:alien_player_collision",
                "message": "alien_player_collision",
                "data": {
                    "collisions": len(aliens_touching_player),
                    "player_health": self.player.sprite.health,
                    "health_percentage": self.player.sprite.health,
                },
            })
            #endregion

            if self.player.sprite.health <= 0:
                #region agent log
                _agent_log({
                    "runId": "pre-fix",
                    "hypothesisId": "A",
                    "location": "game/main.py:collision_checks:game_over",
                    "message": "player_out_of_health",
                    "data": {"health": self.player.sprite.health},
                })
                #endregion
                return False  # Signal game over

        #region agent log
        _agent_log({
            "runId": "pre-fix",
            "hypothesisId": "A",
            "location": "game/main.py:collision_checks:exit",
            "message": "collision_checks_exit",
            "data": {
                "lives": self.lives,
                "aliens": len(self.aliens),
                "diagonal_aliens": len(self.diagonal_aliens),
                "diver_aliens": len(self.diver_aliens),
            },
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
        """Setup aliens for current level with predetermined counts for each type."""
        # Get level-based configuration if not provided
        if rows is None:
            rows = Level.get_alien_rows()
        if cols is None:
            cols = Level.get_alien_cols()
        if speed is None:
            speed = Level.get_alien_speed()
        
        # Clear existing aliens from all groups
        self.aliens.empty()
        self.diagonal_aliens.empty()
        self.diver_aliens.empty()
        
        current_level = Level.current_level_index
        
        # Get predetermined counts for special aliens
        diagonal_count = Level.get_diagonal_count()
        diver_count = Level.get_diver_count()
        
        # Create Type 1 aliens in formation (rows x cols)
        for row_index in range(rows):
            for col_index in range(cols):
                x = col_index * x_distance + x_offset
                y = row_index * y_distance + y_offset
                alien_sprite = Alien(1, speed, x, y)
                self.aliens.add(alien_sprite)
        
        # Spawn predetermined number of Type 2 diagonal aliens
        # Position them spread across the top area, alternating left/right start
        for i in range(diagonal_count):
            # Spread diagonals evenly across screen width
            x = 50 + (i * (SCREEN_WIDTH - 100) // max(1, diagonal_count - 1)) if diagonal_count > 1 else SCREEN_WIDTH // 2
            y = -30 - (i * 40)  # Stagger entry from above screen
            direction = 1 if i % 2 == 0 else -1  # Alternate directions
            diagonal = AlienDiagonal(speed, x, y, direction=direction)
            self.diagonal_aliens.add(diagonal)
        
        # Spawn predetermined number of Type 3 diver aliens
        # Position them spread across top, staggered entry
        for i in range(diver_count):
            # Spread divers randomly but evenly across screen width
            section_width = (SCREEN_WIDTH - 100) // max(1, diver_count)
            x = 50 + (i * section_width) + random.randint(0, section_width // 2)
            y = -60 - (i * 50)  # Stagger entry more than diagonals
            diver = AlienDiver(speed, x, y, level_multiplier=current_level)
            self.diver_aliens.add(diver)

    def alien_position_checker(self):
        """Check if aliens hit edges and reverse direction"""
        for alien in self.aliens:
            if alien.rect.right >= SCREEN_WIDTH or alien.rect.left <= 0:
                self.alien_direction *= -1
                for a in self.aliens:
                    a.rect.y += 20  # Move down
                break

    def remove_offscreen_aliens(self):
        """Remove aliens that have moved below the screen (player survived by avoiding them)"""
        # Check Type 1 aliens (formation)
        for alien in list(self.aliens):
            if alien.rect.top > SCREEN_HEIGHT:
                alien.kill()
        
        # Check Type 2 aliens (diagonal)
        for alien in list(self.diagonal_aliens):
            if alien.rect.top > SCREEN_HEIGHT:
                alien.kill()
        
        # Check Type 3 aliens (diver)
        for alien in list(self.diver_aliens):
            if alien.rect.top > SCREEN_HEIGHT:
                alien.kill()

    def extra_alien_timer(self):
        """Handle extra alien spawning"""
        self.extra_spawn_time -= 1
        if self.extra_spawn_time <= 0:
            self.extra_spawn_time = random.randint(400, 800)
    
    def mystery_ship_timer(self):
        """Handle mystery ship spawning"""
        self.mystery_ship_spawn_time -= 1
        if self.mystery_ship_spawn_time <= 0 and not self.mystery_ship:
            # Spawn mystery ship from left or right side randomly
            side = random.choice(['left', 'right'])
            if side == 'left':
                x = -50
            else:
                x = SCREEN_WIDTH + 50
            mystery = MysteryShip(x, 50)
            mystery.direction = 1 if side == 'left' else -1
            self.mystery_ship.add(mystery)
            self.mystery_ship_spawn_time = random.randint(600, 1200)  # Reset timer

    def _load_mystery_bounty_image(self):
        """Load and cache center-screen bounty chest image."""
        if self._mystery_bounty_image is not None:
            return self._mystery_bounty_image

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        chest_path = os.path.join(project_root, "assets/treasure_chest.png")
        try:
            image = pygame.image.load(chest_path).convert_alpha()
            self._mystery_bounty_image = pygame.transform.scale(image, (180, 180))
        except (pygame.error, FileNotFoundError):
            fallback = pygame.Surface((180, 180), pygame.SRCALPHA)
            pygame.draw.rect(fallback, (218, 165, 32), (0, 0, 180, 180), border_radius=16)
            self._mystery_bounty_image = fallback
        return self._mystery_bounty_image
        

    def draw_mystery_bounty_overlay(self, screen):
        """Draw center-screen mystery bounty celebration for a short time."""
        now = pygame.time.get_ticks()
        if now >= self.mystery_bounty_end_time:
            return

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        screen.blit(overlay, (0, 0))

        chest_image = self._load_mystery_bounty_image().copy()
        pulse = 210 + int(45 * pygame.math.Vector2(0, 1).rotate(now * 0.25).y)
        chest_image.set_alpha(max(120, min(255, pulse)))
        chest_rect = chest_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(chest_image, chest_rect)

        title = self.font.render("MYSTERY BOUNTY!", True, (255, 230, 90))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 90))
        screen.blit(title, title_rect)

        subtitle = self.font.render("Treasure claimed after destroying the mystery ship!", True, (255, 255, 255))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(subtitle, subtitle_rect)

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
        """Display total gold coins (wallet balance + current session earnings)"""
        total_coins = self.economy.get_total_coins() + self.economy.session_coins_earned
        coins_text = self.font.render(f"Gold: {total_coins}", True, (255, 215, 0))  # Gold color
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
    
    def display_key_indicator(self):
        """Display key indicator if player has a key"""
        if self.player_has_key:
            key_text = self.font.render("🔑 KEY", True, (255, 215, 0))
            screen.blit(key_text, (10, 100))

    def draw_wallet_panel(self, screen):
        """Draw wallet details panel with player ID and balances."""
        if not self.show_wallet_panel:
            return

        wallet = self.economy.get_wallet_balance()
        wallet_id = spaceship.get_wallet_id() or "Not found"

        panel_width = 460
        panel_height = 230
        panel_x = SCREEN_WIDTH - panel_width - 20
        panel_y = 65
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((15, 20, 35, 220))
        screen.blit(panel_surface, panel_rect.topleft)
        pygame.draw.rect(screen, (100, 140, 220), panel_rect, 2, border_radius=8)

        line_y = panel_y + 16
        line_gap = 30
        wallet_lines = [
            "Player Wallet",
            f"Wallet ID: {wallet_id}",
            f"Gold Coins: {wallet.get('gold_coins', 0):,}",
            f"Health Packs: {wallet.get('health_packs', 0):,}",
            f"Total Earned Coins: {wallet.get('total_earned_coins', 0):,}",
            f"Session Coins: {self.economy.session_coins_earned:,}",
        ]

        for index, text in enumerate(wallet_lines):
            color = (255, 230, 90) if index == 0 else (255, 255, 255)
            rendered = self.font.render(text, True, color)
            screen.blit(rendered, (panel_x + 14, line_y))
            line_y += line_gap

    def toggle_pause(self):
        """Toggle game pause state and sync with economy"""
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            # Save game state to economy
            game_state = {
                "aliens_count": len(self.aliens),
                "player_pos": self.player.sprite.rect.center,
                "level": Level.current_level_index,
            }
            self.economy.pause_game(game_state)
        else:
            # Resume game
            self.economy.resume_game()
    
    def display_pause_screen(self, screen, mouse_pos=None):
        """Display pause overlay and menu"""
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Pause title
        pause_font = pygame.font.Font(os.path.join(project_root, 'assets/Fonts/hyperspace/Hyperspace Bold Italic.otf'), 60)
        pause_text = pause_font.render("PAUSED", True, (255, 255, 0))
        text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        screen.blit(pause_text, text_rect)
        
        # Instructions
        instruction_font = pygame.font.Font(os.path.join(project_root, 'assets/Fonts/hyperspace/Hyperspace Bold Italic.otf'), 24)
        
        resume_text = instruction_font.render("Press P or ESC to Resume", True, (255, 255, 255))
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(resume_text, resume_rect)
        
        quit_text = instruction_font.render("Press Q to Quit to Menu", True, (200, 200, 200))
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        screen.blit(quit_text, quit_rect)
        
        # Display session stats
        stats_y = SCREEN_HEIGHT // 2 + 100
        score_text = instruction_font.render(f"Score: {self.score}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, stats_y))
        screen.blit(score_text, score_rect)
        
        coins_text = instruction_font.render(f"Session Coins: {self.economy.session_coins_earned}", True, (255, 215, 0))
        coins_rect = coins_text.get_rect(center=(SCREEN_WIDTH // 2, stats_y + 30))
        screen.blit(coins_text, coins_rect)

    def all_aliens_destroyed(self):
        """Check if all alien types have been destroyed"""
        return len(self.aliens) == 0 and len(self.diagonal_aliens) == 0 and len(self.diver_aliens) == 0
    
    def victory_message(self):
        """Display victory message if all aliens destroyed and advance to next level"""
        if self.all_aliens_destroyed() and not self.level_just_completed:
            # Check if there are more levels
            max_level = max(Level.level_dict.keys())
            current_level = Level.current_level_index
            
            if current_level < max_level:
                # Mark level as completed
                self.level_just_completed = True
                self.level_complete_counter = 180  # Show message for ~3 seconds at 60 FPS
                
                # Award level completion bonus: 50 coins doubled each level
                # Level 0 = 50, Level 1 = 100, Level 2 = 200, etc.
                self.level_bonus_earned = 50 * (2 ** current_level)
                self.economy.add_coins(self.level_bonus_earned)

                # Health reward for clearing all aliens 
                # Restore 25 health points (capped at 100)
                health_reward = 25
                old_health = self.player.sprite.health
                self.player.sprite.health = min(100, self.player.sprite.health + health_reward)
                self.health_restored = self.player.sprite.health - old_health

                if self.lives < 3:
                    self.lives += 1

                # Save earned coins to wallet immediately so they persist
                self.economy.save_session_coins()
                
                # Advance to next level
                Level.increment_level()
                # Setup aliens for the new level
                self.alien_setup()  # Uses current level config automatically
                
        # Display level complete message if timer is active
        if self.level_just_completed:
            max_level = max(Level.level_dict.keys())
            if Level.current_level_index <= max_level:
                completed_level = Level.current_level_index
                starting_level = Level.current_level_index + 1
                level_text = self.font.render(f"LEVEL {completed_level} COMPLETE! LEVEL {starting_level} STARTING!", True, (255, 255, 0))
                text_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
                screen.blit(level_text, text_rect)
                
                # Display bonus coins earned
                bonus_text = self.font.render(f"+{self.level_bonus_earned} GOLD COIN BONUS!", True, (255, 215, 0))
                bonus_rect = bonus_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10))
                screen.blit(bonus_text, bonus_rect)

                # Display health restored
            if hasattr(self, 'health_restored') and self.health_restored > 0:
                health_text = self.font.render(f"+{self.health_restored} HEALTH RESTORED!", True, (0, 255, 0))
                health_rect = health_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
                screen.blit(health_text, health_rect)
            
            self.level_complete_counter -= 1
            if self.level_complete_counter <= 0:
                self.level_just_completed = False
                self.level_bonus_earned = 0  # Reset bonus after display
        elif self.all_aliens_destroyed():
            # All levels completed - final victory
            max_level = max(Level.level_dict.keys())
            if Level.current_level_index >= max_level:
                # Award final level bonus if not already awarded
                if self.level_bonus_earned == 0:
                    self.level_bonus_earned = 50 * (2 ** Level.current_level_index)
                    self.economy.add_coins(self.level_bonus_earned)
                    # Save earned coins to wallet immediately
                    self.economy.save_session_coins()
                
                victory_text = self.font.render("VICTORY! ALL LEVELS COMPLETE!", True, (255, 255, 0))
                text_rect = victory_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                screen.blit(victory_text, text_rect)
                
                # Display final bonus
                bonus_text = self.font.render(f"+{self.level_bonus_earned} BONUS COINS!", True, (255, 215, 0))
                bonus_rect = bonus_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
                screen.blit(bonus_text, bonus_rect)

    def run(self, screen, mouse_pos=None, mouse_clicked=False):
        """Main game loop update method"""
        self.player.update()
        
        # Update spaceship (for wallet data sync)
        spaceship_group.update()
        
        # Removed alien_lasers.update() - aliens don't shoot
        self.extra.update()
        
        # Update all alien types
        self.aliens.update(self.alien_direction)  # Type 1: horizontal formation
        self.diagonal_aliens.update()  # Type 2: diagonal movement
        self.diver_aliens.update()  # Type 3: straight down dive
        
        # Update mystery ship - use list() to avoid modifying group during iteration
        self.mystery_ship_timer()
        if self.mystery_ship:
            for mystery in list[MysteryShip](self.mystery_ship):
                mystery.update(getattr(mystery, 'direction', 1))
                # Remove if off screen
                if mystery.rect.right < 0 or mystery.rect.left > SCREEN_WIDTH:
                    mystery.kill()
                    continue

        # Update treasure chests and keys
        self.treasure_chests.update()
        self.keys.update()

        
        self.alien_position_checker()
        self.extra_alien_timer()
        self.remove_offscreen_aliens()  # Remove aliens that passed below the screen
        
        game_continues = self.collision_checks()
        if not game_continues:
            return False
        
        self.player.sprite.lasers.draw(screen)
        self.player.draw(screen)
        self.blocks.draw(screen)
        
        # Draw all alien types
        self.aliens.draw(screen)  # Type 1
        self.diagonal_aliens.draw(screen)  # Type 2
        self.diver_aliens.draw(screen)  # Type 3
        
        # Draw mystery ship
        self.mystery_ship.draw(screen)
        
        # Draw treasure chests and keys
        self.treasure_chests.draw(screen)
        self.keys.draw(screen)
        
        # Removed alien_lasers.draw() - aliens don't shoot
        self.extra.draw(screen)
        self.display_lives()
        self.display_score()
        self.display_coins()
        self.display_level()
        self.display_health()
        self.display_key_indicator()
        self.draw_mystery_bounty_overlay(screen)
        self.victory_message()
        
        # Draw player wallet ID (from SpaceShip class)
        spaceship.draw_wallet_id(screen)
        
        # Display and handle main menu button
        if mouse_pos:
            self.menu_button.change_color(mouse_pos)
            self.pause_button.change_color(mouse_pos)
            self.wallet_button.change_color(mouse_pos)
        self.menu_button.update(screen)
        self.pause_button.update(screen)
        self.wallet_button.update(screen)
        self.draw_mute_button(screen, mouse_pos)
        self.draw_wallet_panel(screen)
        
        # Check if menu button was clicked
        if mouse_clicked and mouse_pos:
            if self.menu_button.check_input(mouse_pos):
                return "menu"  # Signal to return to main menu
            if self.pause_button.check_input(mouse_pos):
                self.toggle_pause()
                return "paused"  # Signal game is paused
            if self.wallet_button.check_input(mouse_pos):
                self.show_wallet_panel = not self.show_wallet_panel
                if self.show_wallet_panel:
                    self.economy.sync_wallet()
            # Check mute button click
            self.check_mute_button_click(mouse_pos)
        
        # Sync economy score with game score
        self.economy.score = self.score
        
        return True


      

# main game loop init function
async def main():
    """Main game entry point - creates game instance and runs game loop (async for Pygbag)"""
    print("game is starting...")
    
    # Create game instance
    game = Game(None)
    
    # Apply the theme selected in main menu to the game
    menu_theme_name = theme_manager.get_current_theme_name()
    theme_mapping = {
        "Black": "BLACK",
        "Menu Background": "MENU_GRADIENT",
        "Purple Nebula": "PURPLE_NEBULA"
    }
    game_theme = theme_mapping.get(menu_theme_name, "PURPLE_NEBULA")
    game.set_background_theme(game_theme)
    print(f"Game using theme: {game_theme}")
    
    clock = pygame.time.Clock()
    running = True
    
    # Setup obstacles
    game.create_multiple_obstacles(*game.obstacle_x_positions, x_start=SCREEN_WIDTH / 15, y_start=480)

    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or (event.key == pygame.K_ESCAPE and not game.is_paused):
                    # Toggle pause with P key, or ESC to pause (not unpause)
                    game.toggle_pause()
                elif event.key == pygame.K_ESCAPE and game.is_paused:
                    # ESC while paused = resume
                    game.toggle_pause()
                elif event.key == pygame.K_q and game.is_paused:
                    # Q while paused = quit to menu
                    # Save session coins before quitting
                    game.economy.save_session_coins()
                    from mainMenu import main_menu
                    return await main_menu()
                elif event.key == pygame.K_m:
                    # M key to toggle mute
                    game.toggle_mute()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True

        # Draw background using current theme
        screen.blit(game.get_current_background(), (0, 0))
        # Renders the title of the game on the screen
        screen.blit(title_surface, title_rect)

        # Handle pause state
        if game.is_paused:
            # Still draw game state in background, then overlay pause screen
            game.player.draw(screen)
            game.blocks.draw(screen)
            game.aliens.draw(screen)
            game.diagonal_aliens.draw(screen)
            game.diver_aliens.draw(screen)
            game.display_score()
            game.display_coins()
            game.display_level()
            game.display_health()
            # Draw player wallet ID on pause screen
            spaceship.draw_wallet_id(screen)
            game.display_pause_screen(screen, mouse_pos)
            # Draw mute button on pause screen too
            game.draw_mute_button(screen, mouse_pos)
            # Handle mute button click while paused
            if mouse_clicked:
                game.check_mute_button_click(mouse_pos)
        else:
            # Run game update (handles all updates, collisions, and drawing)
            game_result = game.run(screen, mouse_pos, mouse_clicked)
            
            # Check if player wants to return to menu
            if game_result == "menu":
                from mainMenu import main_menu
                return await main_menu()
            
            # Check if pause button was clicked
            if game_result == "paused":
                pass  # Will be handled next frame when is_paused is True
            
            elif not game_result:
                # Game over screen - save coins before ending
                game.economy.save_session_coins()
                game_over_text = font.render("GAME OVER", True, (255, 0, 0))
                text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                screen.blit(game_over_text, text_rect)
                pygame.display.flip()
                await asyncio.sleep(3)  # Non-blocking wait (Pygbag compatible)
                running = False
        
        # Update display and control frame rate
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)  # Yield control to browser/event loop (required for Pygbag)

# custom exception defined
class StrictStartError(Exception):
    pass

# Entry point - start from main menu for full playable flow in DOM (Pygbag/Emscripten)
if __name__ == "__main__":
    asyncio.run(main_menu())





        