import pygame
import os
import random
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TREASURE_CHEST_MIN_COINS, TREASURE_CHEST_MAX_COINS,
    TRESURE_CHEST_HEALTH_PACK_CHANCE, TREASURE_CHEST_MIN_HEALTH_PACK, TREASURE_CHEST_MAX_HEALTH_PACK
)


class TreasureChest(pygame.sprite.Sprite):
    """
    TreasureChest that can be unlocked with a Key for bonus rewards.
    Spawns after defeating a MysteryShip.
    """
    def __init__(self, x, y, scale_size=(80, 80)):
        super().__init__()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        # Load treasure chest image
        path = os.path.join(project_root, "assets/treasure_chest.png")
        if os.path.exists(path):
            original_image = pygame.image.load(path).convert_alpha()
            # Scale the image to a reasonable game size
            self.image = pygame.transform.scale(original_image, scale_size)
        else:
            # Fallback to a colored rectangle if image doesn't exist
            self.image = pygame.Surface((40, 40))
            self.image.fill((218, 165, 32))  # Gold color
        
        self.rect = self.image.get_rect(center=(x, y))
        self.locked = True
        self.value = random.randint(TREASURE_CHEST_MIN_COINS, TREASURE_CHEST_MAX_COINS)
        self.health_pack_chance = TRESURE_CHEST_HEALTH_PACK_CHANCE
        self.health_packs = random.randint(TREASURE_CHEST_MIN_HEALTH_PACK, TREASURE_CHEST_MAX_HEALTH_PACK) if random.random() < self.health_pack_chance else 0
        
        # Spawn animation properties
        self.spawn_time = pygame.time.get_ticks()
        self.spawn_animation_duration = 1000  # 1 second spawn animation
        self.is_spawning = True
        self.alpha = 0  # Start invisible for fade-in effect
        self.fall_speed = 2  # Speed at which chest falls down
        self.target_y = y  # Final resting position
        self.rect.y = y - 100  # Start above target position

    def unlock(self, has_key=True):
        """Unlock the treasure chest if player has a key."""
        if self.locked and has_key:
            self.locked = False
            self.is_spawning = False  # Stop any spawn animation
            print("🎉 Treasure Chest unlocked! Reward granted!")
            return self.get_rewards()
        return None
    
    @classmethod
    def spawn_from_mystery_ship(cls, mystery_ship_rect):
        """
        Factory method to create a TreasureChest at the MysteryShip's position.
        Called when a MysteryShip is destroyed.
        """
        x = mystery_ship_rect.centerx
        y = mystery_ship_rect.centery
        print("💎 A Treasure Chest has appeared from the Mystery Ship!")
        return cls(x, y)

    def get_rewards(self):
        """Return the rewards from the treasure chest."""
        if not self.locked:
            rewards = {
                'coins': self.value,
                'health_packs': self.health_packs
            }
            return rewards
        return None

    def update(self):
        """Update treasure chest state with spawn animation."""
        if self.is_spawning:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.spawn_time
            
            # Fade in effect
            if elapsed < self.spawn_animation_duration:
                self.alpha = min(255, int((elapsed / self.spawn_animation_duration) * 255))
                self.image.set_alpha(self.alpha)
            else:
                self.alpha = 255
                self.image.set_alpha(255)
            
            # Fall down to target position
            if self.rect.centery < self.target_y:
                self.rect.y += self.fall_speed
                if self.rect.centery >= self.target_y:
                    self.rect.centery = self.target_y
                    self.is_spawning = False
        
        # Floating animation when idle (locked and not spawning)
        if not self.is_spawning and self.locked:
            # Gentle float effect
            float_offset = int(3 * pygame.math.Vector2(0, 1).rotate(pygame.time.get_ticks() * 0.1).y)
            self.rect.centery = self.target_y + float_offset
        
        # Remove if off screen (fell through)
        if self.rect.top > SCREEN_HEIGHT:
            self.kill() 


class Key(pygame.sprite.Sprite):
    """
    Key item that drops from MysteryShip and unlocks TreasureChests.
    Appears on screen for 3 seconds after MysteryShip is destroyed.
    """
    def __init__(self, x, y):
        super().__init__()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        # Load key image
        path = os.path.join(project_root, "assets/key.png")
        if os.path.exists(path):
            self.image = pygame.image.load(path).convert_alpha()
        else:
            # Fallback to a colored rectangle if image doesn't exist
            self.image = pygame.Surface((20, 30))
            self.image.fill((255, 215, 0))  # Gold color
        
        self.rect = self.image.get_rect(center=(x, y))
        self.collected = False
        self.fall_speed = 2
        
        # Timer for 3-second visibility after MysteryShip is destroyed
        self.spawn_time = pygame.time.get_ticks()
        self.display_duration = 3000  # 3 seconds in milliseconds
        self.is_active = True

    @classmethod
    def spawn_from_mystery_ship(cls, mystery_ship_rect):
        """
        Factory method to create a Key at the MysteryShip's position.
        Called when a MysteryShip is destroyed.
        """
        x = mystery_ship_rect.centerx
        y = mystery_ship_rect.centery
        print("🔑 A Key has dropped from the Mystery Ship!")
        return cls(x, y)

    def update(self):
        """Key falls down after spawning and disappears after 3 seconds."""
        if not self.collected and self.is_active:
            # Check if 3 seconds have passed since spawn
            current_time = pygame.time.get_ticks()
            if current_time - self.spawn_time >= self.display_duration:
                self.is_active = False
                self.kill()
                print("🔑 Key disappeared!")
                return
            
            # Fall down movement
            self.rect.y += self.fall_speed
            
            # Remove if off screen
            if self.rect.top > SCREEN_HEIGHT:
                self.kill()

    def collect(self):
        """Mark key as collected."""
        self.collected = True
        self.kill()
        print("🔑 Key collected!")
        return True
