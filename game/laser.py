import pygame
import index as index
import spaceship as spaceship


class Laser(pygame.sprite.Sprite):
    def __init__(self, position, speed):
        super().__init__()
        self.image = pygame.Surface((4, 20))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=position)
        self.speed = speed

    def hit_hero_ship(self):
        if self.rect.colliderect(index.hero_ship.rect):
            index.hero_ship.health -= 1
            return True
        else: return False 



   
        