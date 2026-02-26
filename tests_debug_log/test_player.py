import unittest
from unittest.mock import Mock, patch, MagicMock
import pygame
import sys
import os

# Add the game directory to the path so we can import Player
# This is needed because player.py uses relative imports like "from laser import Laser"
game_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'game')
game_dir = os.path.abspath(game_dir)
if game_dir not in sys.path:
    sys.path.insert(0, game_dir)

from player import Player



class TestPlayerGetInput(unittest.TestCase):
    """Unit tests for Player.get_input() method"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Initialize pygame for testing (required for some pygame operations)
        pygame.init()
        
        # Create a mock surface for the player image
        mock_image = Mock()
        # Create a function that returns a real pygame.Rect when called with midbottom
        def get_rect(**kwargs):
            if 'midbottom' in kwargs:
                x, y = kwargs['midbottom']
                # Create a rect with midbottom at the specified position
                # Assuming a typical spaceship size (50x50)
                rect = pygame.Rect(x - 25, y - 50, 50, 50)
                return rect
            return pygame.Rect(100, 100, 50, 50)
        mock_image.get_rect = Mock(side_effect=get_rect)
        
        # Create a player instance with initial position and constraints
        with patch('pygame.image.load', return_value=mock_image):
            self.player = Player(pos=(400, 500), constraint=800, speed=5)
            # Ensure rect is a real pygame.Rect (not Mock) for proper boundary testing
            if not isinstance(self.player.rect, pygame.Rect):
                self.player.rect = pygame.Rect(100, 100, 50, 50)
            else:
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
        """Test that pressing UP arrow key moves player up (decreases y, since y=0 is at top)"""
        # Mock pygame.key.get_pressed to return UP key pressed
        def key_side_effect(key):
            return key == pygame.K_UP
        mock_keys = MagicMock()
        mock_keys.__getitem__ = Mock(side_effect=key_side_effect)
        mock_get_pressed.return_value = mock_keys
        
        initial_y = self.player.rect.y
        self.player.get_input()
        
        # Player should move up by speed amount (y decreases, since y=0 is at top)
        self.assertEqual(self.player.rect.y, initial_y - self.player.speed)
    
    @patch('pygame.key.get_pressed')
    def test_move_down(self, mock_get_pressed):
        """Test that pressing DOWN arrow key moves player down (increases y, since y=0 is at top)"""
        # Mock pygame.key.get_pressed to return DOWN key pressed
        def key_side_effect(key):
            return key == pygame.K_DOWN
        mock_keys = MagicMock()
        mock_keys.__getitem__ = Mock(side_effect=key_side_effect)
        mock_get_pressed.return_value = mock_keys
        
        initial_y = self.player.rect.y
        self.player.get_input()
        
        # Player should move down by speed amount (y increases, since y=0 is at top)
        self.assertEqual(self.player.rect.y, initial_y + self.player.speed)
    
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
    
    def test_top_boundary_constraint(self):
        """Test that player cannot move above the top of the screen"""
        from config import SCREEN_HEIGHT
        # Move player to top boundary
        self.player.rect.top = 0
        initial_top = self.player.rect.top
        
        # Try to move up (should stay at top)
        self.player.rect.top = -10
        self.player.constraint()
        
        # Player should be constrained to top of screen
        self.assertEqual(self.player.rect.top, 0)
    
    def test_bottom_boundary_constraint(self):
        """Test that player cannot move below the bottom of the screen"""
        from config import SCREEN_HEIGHT
        # Move player to bottom boundary
        self.player.rect.bottom = SCREEN_HEIGHT
        initial_bottom = self.player.rect.bottom
        
        # Try to move down (should stay at bottom)
        self.player.rect.bottom = SCREEN_HEIGHT + 10
        self.player.constraint()
        
        # Player should be constrained to bottom of screen
        self.assertEqual(self.player.rect.bottom, SCREEN_HEIGHT)


if __name__ == '__main__':
    unittest.main()
