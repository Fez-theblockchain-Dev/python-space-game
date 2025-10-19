import pygame, random

from game.index import hero_ship


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

    class Myster_Ship(pygame.sprite.Sprite):
        def __init__(self, x, y):
            super().__init__()
            self.mystery_ship = 'mystery_ship.png'
            self.image = pygame.image.load(self.mystery_ship)
            self.rect = self.image.get_rect(top_left = (x,y))
            self.health = 250

            if self.health <= 0:
                self.kill() and print("Mystery Ship Destroyed. Mystery treasure chest key has been claimed!")
    
    def update(self, direction):
        self.rect.x += direction

# variables for Key class
key = random.randint(1, 100)


class Key(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("assets/key.png").convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))

class TreasureBox(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load("assets/treasure_box.png").convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.locked = True

        def unlock(self):
            self.locked = False
            print("🎉 Mystery Treasure Box unlocked! Reward granted!")


    
         
        
    

