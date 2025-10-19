import pygame, random

class Alien(pygame.sprite.Sprite):
    def __init__(self, type, x, y):
        super().__init__()
        self.type = type
        self.health = 100 # default health for all aliens
        path = f"assets/alien_{type}.png"
        self.image = pygame.image.load(path)
        self.rect = self.image.get_rect(top_left = (x,y))
        self.value = 100 # default value for all aliens
    
    def alien_type(self):
        self.type_1 = 'alien_1.png'
        self.type_2 = 'alien_2.png'
        self.type_3 = 'alien_3.png'
    
    def update(self, direction):
        self.rect.x += direction
         
        
    

