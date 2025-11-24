import pygame, sys
from player import Player
from config import SCREEN_HEIGHT, SCREEN_WIDTH

# obstacle (asteroid) class 
class Block(pygame.sprite.Sprite):
    def __init__(self,size,color,x,y):
        super().__init__()
        self.image = pygame.Surface(size,size)
        self.image.fill(color)
        player_sprite = Player(SCREEN_WIDTH  , SCREEN_HEIGHT, 5)
        self.player = pygame.sprite.GroupSingle(player_sprite)
        self.rect = self.image.get_rect(top_left = (x,y))

shape = [
  'xxxxxxx',
' xxxxxxxxx',
'xxxxxxxxxxx',
'xxxxxxxxxxx',
'xxxxxxxxxxx',
'xxx     xxx',
'xx       xx'
]