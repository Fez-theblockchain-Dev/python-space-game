import pygame, sys
from player import Player

# obstacle (asteroid) class 
class GAME:
    def __init__(self):
        player_sprite = Player(SCREEN_WIDTH / 2 , SCREEN_HEIGHT / 2 , 5)
        self.player = pygame.sprite.GroupSingle(player_sprite)