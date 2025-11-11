import pygame

# from game import spaceship

class Laser(pygame.sprite.Sprite):
    def __init__(self, position, speed, screen_height, false):
        super().__init__()
        self.image = pygame.Surface((4, 20))
        self.image.fill((243, 216, 63))
        self.rect = self.image.get_rect(center=position)
        self.speed = speed
        self.screen_y_axis = screen_height
        self.laser = False

    def destroy(self):
        if self.rect.y <= -50 or self.rect.y >= self.screen_y_axis + 50:
            self.kill()

    def update(self):
        self.rect.y += self.speed
        self.destroy()
        # Remove laser if it goes off screen
        if self.rect.bottom < 0:
            self.kill()