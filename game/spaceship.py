import pygame

class SpaceShip(pygame.sprite.Sprite):
    def __init__(self, x, y, health=10):
        super().__init__()
        self.image = pygame.image.load('assets/spaceship.png')
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.health = health
        self.speed = 5
    
    def update(self):
        # Add any spaceship update logic here
        pass