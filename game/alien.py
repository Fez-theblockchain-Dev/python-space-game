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
    """
    Base alien class - Type 1 aliens move horizontally in formation.
    Use AlienDiagonal (type 2) and AlienDiver (type 3) for different movement patterns.
    """
    def __init__(self, type, speed, x, y):
        super().__init__()
        self.type = type
        self.health = 100  # default health for all aliens
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        path = os.path.join(project_root, f"assets/alien_{type}.png")
        self.image = pygame.image.load(path)
        self.rect = self.image.get_rect(center=(x, y))
        self.value = 100  # default value for all aliens
        self.speed = speed

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

    @staticmethod
    def get_alien_types():
        """Returns available alien type information"""
        return {
            1: {'file': 'alien_1.png', 'movement': 'horizontal', 'description': 'Standard formation alien'},
            2: {'file': 'alien_2.png', 'movement': 'diagonal', 'description': 'Diagonal movement alien'},
            3: {'file': 'alien_3.png', 'movement': 'dive', 'description': 'Diving alien (flipped, moves straight down)'}
        }


class AlienDiagonal(pygame.sprite.Sprite):
    """
    Type 2 alien - moves diagonally across the screen.
    Bounces off left/right edges while descending.
    """
    def __init__(self, speed, x, y, direction=1):
        super().__init__()
        self.type = 2
        self.health = 100
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        path = os.path.join(project_root, "assets/alien_2.png")
        self.image = pygame.image.load(path)
        self.rect = self.image.get_rect(center=(x, y))
        self.value = 150  # Higher value for harder alien
        self.speed = speed
        self.horizontal_direction = direction  # 1 = right, -1 = left
        self.vertical_speed = speed * 0.5  # Slower vertical descent
    
    def update(self, direction=None):
        """Move diagonally - bounces off walls while descending."""
        # Horizontal movement
        self.rect.x += self.horizontal_direction * self.speed
        
        # Bounce off edges
        if self.rect.left <= 0:
            self.rect.left = 0
            self.horizontal_direction = 1
        elif self.rect.right >= SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.horizontal_direction = -1
        
        # Vertical descent
        self.rect.y += self.vertical_speed
        
        # Remove if off screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()


class AlienDiver(pygame.sprite.Sprite):
    """
    Type 3 alien - flipped 180 degrees, dives straight down.
    Speed increases with game level.
    """
    def __init__(self, speed, x, y, level_multiplier=1):
        super().__init__()
        self.type = 3
        self.health = 100
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        path = os.path.join(project_root, "assets/alien_3.png")
        original_image = pygame.image.load(path)
        # Flip the image 180 degrees (both horizontally and vertically)
        self.image = pygame.transform.rotate(original_image, 180)
        self.rect = self.image.get_rect(center=(x, y))
        self.value = 200  # Highest value for hardest alien
        self.base_speed = speed
        self.level_multiplier = level_multiplier
        self.speed = speed * (1 + (level_multiplier * 0.3))  # Speed increases 30% per level
    
    def update(self, direction=None):
        """Move straight down at level-based speed."""
        self.rect.y += self.speed
        
        # Remove if off screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
    
    def set_level_speed(self, level):
        """Update speed based on current level."""
        self.level_multiplier = level
        self.speed = self.base_speed * (1 + (level * 0.3))


class MysteryShip(pygame.sprite.Sprite):
    """Mystery ship that flies across the screen for bonus points. Uses assets/mystery.png image."""
    def __init__(self, x, y, scale_size=(60, 50)):
        super().__init__()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        path = os.path.join(project_root, "assets/mystery.png")
        
        # Load and scale the mystery ship image
        if os.path.exists(path):
            original_image = pygame.image.load(path).convert_alpha()
            self.image = pygame.transform.scale(original_image, scale_size)
        else:
            # Fallback to a red rectangle if image doesn't exist
            self.image = pygame.Surface(scale_size, pygame.SRCALPHA)
            self.image.fill((255, 0, 0))  # Red color
            print(f"Warning: Could not load mystery ship image from {path}")
        
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = 150  # 3 hits to destroy (each hit does 50 damage)
        self.speed = 3
        self.value = 500
        self.direction = random.choice([-1, 1])  # Randomize direction: -1 = left, 1 = right
        self.hits_taken = 0  # Track number of hits for debugging

    def update(self, direction=None):
        """Move horizontally across screen."""
        # Use instance direction if none provided
        move_direction = direction if direction is not None else self.direction
        self.rect.x += move_direction * self.speed
        
        # Check if ship should be destroyed
        if self.health <= 0:
            self.kill()
            print("Mystery Ship Destroyed. Mystery treasure chest key has been claimed!")
        
        # Remove if off screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

    def take_damage(self, damage=50):
        """Apply damage to the mystery ship. Returns True if ship is destroyed."""
        self.hits_taken += 1
        self.health -= damage
        print(f"Mystery Ship hit! ({self.hits_taken}/3 hits) - Health: {self.health}/150")
        
        if self.health <= 0:
            print("Mystery Ship Destroyed! Key unlocked!")
            return True
        return False

