import pygame

class Laser(pygame.sprite.Sprite):
    def __init__(self, position, speed):
        super().__init__()
        self.image = pygame.Surface((4, 20))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=position)
        self.speed = speed

    def update(self):
        self.rect.y -= self.speed
        # Remove laser if it goes off screen
        if self.rect.bottom < 0:
            self.kill()