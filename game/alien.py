import pygame, random

class Alien(pygame.sprite.Sprite):
    def __init__(self, type, x, y):
        super().__init__()
        self.type = type
        path = f"assets/alien_1.png, assets/alien_2.png, assets/alien_3.png"
        self.image = pygame.image.load(path)
        self.rect = self.image.get_rect(top_left = (x,y))

    def update(self, direction):
        self.rect.x += direction
        
    

