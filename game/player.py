
import pygame
import sys
import os
from pygame.locals import * #For useful variables
from laser import Laser

# Get absolute paths for assets
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

class Player(pygame.sprite.Sprite):
	def __init__(self,pos,constraint,speed):
		super().__init__()
		self.image = pygame.image.load(os.path.join(project_root, 'assets/spaceship.png')).convert_alpha()
		self.rect = self.image.get_rect(midbottom = pos)
		self.speed = speed
		self.max_x_constraint = constraint
		self.ready = True
		self.laser_time = 0
		self.laser_cooldown = 600
		self.lasers = pygame.sprite.Group()
		try:
			self.laser_sound = pygame.mixer.Sound(os.path.join(project_root, 'audio/audio_laser.wav'))
			self.laser_sound.set_volume(0.5)
		except Exception as e:
			print(f"Warning: Could not load laser sound: {e}")
			self.laser_sound = None
		self.cool_down_time = 600
		self.recharge_time = 0
		self.health = 100  # Player health (0-100)

	def get_input(self):
		keys = pygame.key.get_pressed()
		# right/left/up/down navigation thru arrow keys
		if keys[pygame.K_RIGHT]: 
			self.rect.x += self.speed
		elif keys[pygame.K_LEFT]:
			self.rect.x -= self.speed
		elif keys[pygame.K_UP]:
			self.rect.y -= self.speed
		elif keys[pygame.K_DOWN]:
			self.rect.y += self.speed

		# spacebar to shoot laser
		if keys[pygame.K_SPACE]:
			if self.ready:
				self.shoot_laser()
				self.ready = False
				self.recharge_time = pygame.time.get_ticks()
				if self.laser_sound:
					self.laser_sound.play()

	def recharge(self): 
		if not self.ready:
			current_time = pygame.time.get_ticks()
			if current_time - self.recharge_time >= self.cool_down_time:
				self.ready = True
	
	# 'margin' constraints for setting boundaries for where the player can move to 
	def constraint(self):
		from config import SCREEN_HEIGHT
		# Left/Right boundaries
		if self.rect.left <= 0:
			self.rect.left = 0
		if self.rect.right >= self.max_x_constraint:
			self.rect.right = self.max_x_constraint
		# Top/Bottom boundaries
		if self.rect.top <= 0:
			self.rect.top = 0
		if self.rect.bottom >= SCREEN_HEIGHT:
			self.rect.bottom = SCREEN_HEIGHT
        
	def shoot_laser(self):
		from config import SCREEN_HEIGHT
		# Laser(position, speed, screen_height, false)
		laser = Laser(self.rect.center, -8, SCREEN_HEIGHT, False)
		self.lasers.add(laser)

	def update(self):
		self.get_input()
		self.constraint()
		self.recharge()
		self.lasers.update()

# conditional statements to control gameplay of player

# when player logs back into a game that was paused from earlier
is_logged_in = True
if is_logged_in:
  print("Welcome back!")


		
		
