import pygame
import os
import json
import urllib.request
import urllib.error

class SpaceShip(pygame.sprite.Sprite):
    # API endpoint for wallet data
    API_BASE_URL = "http://localhost:8000"
    
    def __init__(self, x, y, health=10):
        super().__init__()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.image = pygame.image.load(os.path.join(project_root, 'assets/spaceship.png'))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.health = health
        self.speed = 5
        
        # Wallet tracking
        self.player_wallet_id = self._load_player_id(project_root)
        self.gold_coins = 0
        self.wallet_last_fetched = 0
        self.wallet_fetch_interval = 5000  # Fetch wallet every 5 seconds (milliseconds)
        
        # Font for rendering wallet ID
        font_path = os.path.join(project_root, 'assets/Fonts/hyperspace/Hyperspace Bold.otf')
        try:
            self.wallet_font = pygame.font.Font(font_path, 14)
        except:
            self.wallet_font = pygame.font.SysFont('arial', 14)
        
        # Initial wallet fetch
        self._fetch_wallet_data()
    
    def _load_player_id(self, project_root):
        """Load the player's wallet ID from player_id.json"""
        player_id_path = os.path.join(project_root, 'player_id.json')
        try:
            with open(player_id_path, 'r') as f:
                data = json.load(f)
                return data.get('player_id', None)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load player_id.json: {e}")
            return None
    
    def _fetch_wallet_data(self):
        """Fetch wallet data from the backend API to get gold_coins from past matches"""
        if not self.player_wallet_id:
            return
        
        try:
            url = f"{self.API_BASE_URL}/api/wallet/{self.player_wallet_id}"
            req = urllib.request.Request(url, method='GET')
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.gold_coins = data.get('gold_coins', 0)
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
            # Silently fail - API might not be running
            pass
    
    def update(self):
        """Update spaceship state, including periodic wallet data refresh"""
        current_time = pygame.time.get_ticks()
        
        # Periodically fetch wallet data to keep gold_coins in sync
        if current_time - self.wallet_last_fetched >= self.wallet_fetch_interval:
            self._fetch_wallet_data()
            self.wallet_last_fetched = current_time
    
    def draw_wallet_id(self, screen):
        """Render the player's wallet ID on screen with a background rect"""
        if not self.player_wallet_id:
            return
        
        # Truncate wallet ID for display (show first 8 and last 4 characters)
        display_id = f"{self.player_wallet_id[:8]}...{self.player_wallet_id[-4:]}"
        wallet_text = f"Wallet: {display_id}"
        
        # Render the text
        text_surface = self.wallet_font.render(wallet_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        
        # Position at bottom-left of screen with padding
        padding = 10
        text_rect.bottomleft = (padding, screen.get_height() - padding)
        
        # Create background rect with slight transparency
        bg_rect = text_rect.inflate(16, 8)  # Add padding around text
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill((30, 30, 50, 200))  # Dark blue with transparency
        
        # Draw background and text
        screen.blit(bg_surface, bg_rect.topleft)
        pygame.draw.rect(screen, (100, 100, 150), bg_rect, 2)  # Border
        screen.blit(text_surface, text_rect)
    
    def get_gold_coins(self):
        """Get the current gold coins balance from past matches"""
        return self.gold_coins
    
    def get_wallet_id(self):
        """Get the player's wallet ID"""
        return self.player_wallet_id