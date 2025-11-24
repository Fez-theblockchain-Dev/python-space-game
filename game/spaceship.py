import pygame
import os

class SpaceShip(pygame.sprite.Sprite):
    def __init__(self, x, y, health=10):
        super().__init__()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.image = pygame.image.load(os.path.join(project_root, 'assets/spaceship.png'))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.health = health
        self.speed = 5
    
    def update(self):
        # Add any spaceship update logic here
        pass