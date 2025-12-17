import unittest
from unittest.mock import Mock, patch, MagicMock
import pygame
import sys
import os

# Add the game directory to the path so we can import Player
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'game'))

from player import Player


class TestPlayerGetInput(unittest.TestCase):
    """Unit tests for Player.get_input() method"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Initialize pygame for testing (required for some pygame operations)
        pygame.init()
        
        # Create a mock surface for the player image
        mock_image = Mock()
        mock_image.get_rect = Mock(return_value=Mock(x=100, y=100, center=(150, 150)))
        
        # Create a player instance with initial position and constraints
        with patch('pygame.image.load', return_value=mock_image):
            self.player = Player(pos=(400, 500), constraint=800, speed=5)
            # Set initial position for testing
            self.player.rect.x = 100
            self.player.rect.y = 100
    
    def tearDown(self):
        """Clean up after each test method"""
        pygame.quit()
    
    @patch('pygame.key.get_pressed')
    def test_move_right(self, mock_get_pressed):
        """Test that pressing RIGHT arrow key moves player to the right"""
        # Mock pygame.key.get_pressed to return RIGHT key pressed
        def key_side_effect(key):
            return key == pygame.K_RIGHT
        mock_keys = MagicMock()
        mock_keys.__getitem__ = Mock(side_effect=key_side_effect)
        mock_get_pressed.return_value = mock_keys
        
        initial_x = self.player.rect.x
        self.player.get_input()
        
        # Player should move right by speed amount
        self.assertEqual(self.player.rect.x, initial_x + self.player.speed)
    
    @patch('pygame.key.get_pressed')
    def test_move_left(self, mock_get_pressed):
        """Test that pressing LEFT arrow key moves player to the left"""
        # Mock pygame.key.get_pressed to return LEFT key pressed
        def key_side_effect(key):
            return key == pygame.K_LEFT
        mock_keys = MagicMock()
        mock_keys.__getitem__ = Mock(side_effect=key_side_effect)
        mock_get_pressed.return_value = mock_keys
        
        initial_x = self.player.rect.x
        self.player.get_input()
        
        # Player should move left by speed amount
        self.assertEqual(self.player.rect.x, initial_x - self.player.speed)
    
    @patch('pygame.key.get_pressed')
    def test_move_up(self, mock_get_pressed):
        """Test that pressing UP arrow key moves player up (increases y)"""
        # Mock pygame.key.get_pressed to return UP key pressed
        def key_side_effect(key):
            return key == pygame.K_UP
        mock_keys = MagicMock()
        mock_keys.__getitem__ = Mock(side_effect=key_side_effect)
        mock_get_pressed.return_value = mock_keys
        
        initial_y = self.player.rect.y
        self.player.get_input()
        
        # Player should move up by speed amount (y increases)
        self.assertEqual(self.player.rect.y, initial_y + self.player.speed)
    
    @patch('pygame.key.get_pressed')
    def test_move_down(self, mock_get_pressed):
        """Test that pressing DOWN arrow key moves player down (decreases y)"""
        # Mock pygame.key.get_pressed to return DOWN key pressed
        def key_side_effect(key):
            return key == pygame.K_DOWN
        mock_keys = MagicMock()
        mock_keys.__getitem__ = Mock(side_effect=key_side_effect)
        mock_get_pressed.return_value = mock_keys
        
        initial_y = self.player.rect.y
        self.player.get_input()
        
        # Player should move down by speed amount (y decreases)
        self.assertEqual(self.player.rect.y, initial_y - self.player.speed)
    
    @patch('pygame.key.get_pressed')
    def test_no_key_pressed(self, mock_get_pressed):
        """Test that when no arrow keys are pressed, player does not move"""
        # Mock pygame.key.get_pressed to return no keys pressed
        mock_keys = MagicMock()
        mock_keys.__getitem__ = Mock(return_value=False)
        mock_get_pressed.return_value = mock_keys
        
        initial_x = self.player.rect.x
        initial_y = self.player.rect.y
        self.player.get_input()
        
        # Player should not move when no keys are pressed (no else clause)
        self.assertEqual(self.player.rect.x, initial_x)
        self.assertEqual(self.player.rect.y, initial_y)
    
    @patch('pygame.key.get_pressed')
    def test_priority_right_over_left(self, mock_get_pressed):
        """Test that RIGHT key takes priority over LEFT when both are pressed"""
        # Mock pygame.key.get_pressed to return both RIGHT and LEFT pressed
        # Since it's an if-elif chain, RIGHT should be processed first
        def key_side_effect(key):
            return key in [pygame.K_RIGHT, pygame.K_LEFT]
        mock_keys = MagicMock()
        mock_keys.__getitem__ = Mock(side_effect=key_side_effect)
        mock_get_pressed.return_value = mock_keys
        
        initial_x = self.player.rect.x
        self.player.get_input()
        
        # Should move right (first condition in if-elif chain)
        self.assertEqual(self.player.rect.x, initial_x + self.player.speed)
    
    @patch('pygame.key.get_pressed')
    def test_multiple_calls_accumulate_movement(self, mock_get_pressed):
        """Test that multiple calls to get_input accumulate movement"""
        # Mock pygame.key.get_pressed to return RIGHT key pressed
        mock_keys = MagicMock()
        mock_keys.__getitem__ = Mock(side_effect=lambda key: key == pygame.K_RIGHT)
        mock_get_pressed.return_value = mock_keys
        
        initial_x = self.player.rect.x
        # Call get_input multiple times
        self.player.get_input()
        self.player.get_input()
        self.player.get_input()
        
        # Player should have moved right by speed * 3
        self.assertEqual(self.player.rect.x, initial_x + (self.player.speed * 3))


if __name__ == '__main__':
    unittest.main()
