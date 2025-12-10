import pygame, random, os
from config import SCREEN_WIDTH, SCREEN_HEIGHT


aliens = pygame.sprite.Group()

def check_alien_edges(alien_group, direction):
    """Check if any alien hits screen edge. Returns reversed direction if edge hit, otherwise returns same direction."""
    edge_hit = False
    for alien in alien_group:
        if alien.rect.left <= 0 or alien.rect.right >= SCREEN_WIDTH:
            edge_hit = True
            break
    
    if edge_hit:
        return -direction  # Reverse direction
    return direction  # Keep same direction

class Alien(pygame.sprite.Sprite):
    def __init__(self, type, speed, x, y):
        super().__init__()
        self.type = type
        self.health = 100 # default health for all aliens
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        path = os.path.join(project_root, f"assets/alien_{type}.png")
        self.image = pygame.image.load(path)
        self.rect = self.image.get_rect(center = (x, y))
        self.value = 100 # default value for all aliens
        self.speed = speed 

# function to remove the alien from game once it leaves the screen
    def update(self, direction=None):
        """Update alien position. If direction is provided, move horizontally."""
        if direction is not None:
            # Move horizontally
            self.rect.x += direction * self.speed
        else:
            # Default vertical movement (for backward compatibility)
            self.rect.y += 2 
            if self.rect.top > SCREEN_HEIGHT:
                self.kill()


    def update_horizontal(self, direction):
        """Move alien horizontally. Returns True if alien hits screen edge."""
        self.rect.x += direction * self.speed
        
        # Check if alien hits left or right edge
        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            return True  # Signal that edge was hit
        return False

    # Spawn timer variables
    SPAWN_INTERVAL = 2000  # milliseconds
    last_spawn_time = pygame.time.get_ticks()


    def alien_type(self):
        self.type_1 = 'alien_1.png'
        self.type_2 = 'alien_2.png'
        self.type_3 = 'alien_3.png'

    class Myster_Ship(pygame.sprite.Sprite):
        def __init__(self, x, y):
            super().__init__()
            self.mystery_ship = 'mystery_ship.png'
            self.image = pygame.image.load(self.mystery_ship)
            self.rect = self.image.get_rect(top_left = (x,y))
            self.health = 250

            if self.health <= 0:
                self.kill() and print("Mystery Ship Destroyed. Mystery treasure chest key has been claimed!")
    
    def update(self, direction):
        self.rect.x += direction

# variables for Key class
key = random.randint(1, 100)


class Key(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("assets/key.png").convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))

class TreasureBox(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("assets/treasure_box.png").convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.locked = True

        def unlock(self):
            self.locked = False
            print("🎉 Mystery Treasure Box unlocked! Reward granted!")


    
         
        
    

