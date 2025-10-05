import pygame

class SpaceShip(pygame.sprite.Sprite):
    def init(self, Screen_width, Screen_height):
        super().__init__()
        self.screen_width = Screen_width
        self.screen_height = Screen_height
        self.image = pygame.image.load('assets/spaceship.png')
       