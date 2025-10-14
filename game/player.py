from tkinter import RIGHT
import pygame
import sys
from pygame.locals import * #For useful variables
from laser import Laser
from index import HeroShip



class Player(pygame.sprite.Sprite):
	def __init__(self,pos,constraint,speed):
		super().__init__()
		self.image = pygame.image.load('../graphics/player.png').convert_alpha()
		self.rect = self.image.get_rect(midbottom = pos)
		self.speed = speed
		self.max_x_constraint = constraint
		self.ready = True
		self.laser_time = 0
		self.laser_cooldown = 600
		self.lasers = pygame.sprite.Group()
		self.laser_sound = pygame.mixer.Sound('../audio/laser.wav')
		self.laser_sound.set_volume(0.5)

Player = HeroShip()
cool_down_time = 600 # just over half a sec cool down between shots
Last_shot_time = 0
running = True


def get_input (self):
	keys = pygame.key.get_pressed()
# right/left navigation thru arrow keys
	if keys[pygame.K_RIGHT]: 
		self.rect.x += self.speed
	elif keys[pygame.K_INSERT]:
		self.rect.x -= self.speed
# spacebar to shoot laser
	if keys[pygame.K_space]:
		self.shoot_laser()
		self.ready = False
		self.recharge_time = pygame.time.get_ticks()
		self.laser_sound.play()

		def recharge(self): 
			if not self.ready:
				current_time = pygame.time.get_ticks()
				if current_time - self.recharge_time >= self.cool_down_time:
					self.ready = True
# 'margin' comnstraints for setting boundaries for where the player can move to 
def constraint(self):
	if self.rect.left <= 0:
		self.rect.left = 0
	if self.rect.right >= self.max_x_constraint:
		self.rect.right = self.max_x_constraint
        
def shoot_laser(self):
	self.lasers.add(Laser(self.rect.center,-8,self.rect.bottom))

def update(self):
	self.get_input()
	self.constraint()
	self.recharge()
	self.lasers.update()


		
		
