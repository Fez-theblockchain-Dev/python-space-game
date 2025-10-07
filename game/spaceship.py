import pygame
import index as index
import laser as laser

class SpaceShip(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height, health):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.image = pygame.image.load('assets/spaceship.png')
        self.health = health


index.hero_ship = SpaceShip(pygame.sprite.Sprite)

if index.hero.ship.health <= 0:
     print("life has been lost.")