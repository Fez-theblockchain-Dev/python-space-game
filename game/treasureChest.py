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
    def __init__(self, x, y):
        super().__init__()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        # Load treasure chest image
        path = os.path.join(project_root, "assets/treasure_chest.jpg")
        if os.path.exists(path):
            self.image = pygame.image.load(path).convert_alpha()
        else:
            # Fallback to a colored rectangle if image doesn't exist
            self.image = pygame.Surface((40, 40))
            self.image.fill((218, 165, 32))  # Gold color
        
        self.rect = self.image.get_rect(center=(x, y))
        self.locked = True
        self.value = random.randint(TREASURE_CHEST_MIN_COINS, TREASURE_CHEST_MAX_COINS)
        self.health_pack_chance = TRESURE_CHEST_HEALTH_PACK_CHANCE
        self.health_packs = random.randint(TREASURE_CHEST_MIN_HEALTH_PACK, TREASURE_CHEST_MAX_HEALTH_PACK) if random.random() < self.health_pack_chance else 0

    def unlock(self, has_key=True):
        """Unlock the treasure chest if player has a key."""
        if self.locked and has_key:
            self.locked = False
            print("🎉 Treasure Chest unlocked! Reward granted!")
            return self.get_rewards()
        return None

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
        """Update treasure chest state."""
        # Can add floating animation or effects here
        pass


class Key(pygame.sprite.Sprite):
    """
    Key item that drops from MysteryShip and unlocks TreasureChests.
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

    def update(self):
        """Key falls down after spawning."""
        if not self.collected:
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
