import json
import os
import sys

import pygame
from config import resource_path, BACKEND_API_URL
from web_http import fetch_json, kick_off_background_json

IS_BROWSER = sys.platform == "emscripten"


class SpaceShip(pygame.sprite.Sprite):
    def __init__(self, x, y, health=10):
        super().__init__()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.image = pygame.image.load(resource_path("assets", "spaceship.png"))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.health = health
        self.speed = 5

        # Wallet tracking: desktop reads player_id.json; browser uses
        # localStorage (populated by the fallback load_shared_player_id in
        # __main__.py so all modules agree on the same UUID).
        self.player_wallet_id = (
            self.load_browser_player_id() if IS_BROWSER else self.load_player_id(project_root)
        )
        self.gold_coins = 0
        self.wallet_last_fetched = 0
        self.wallet_fetch_interval = 5000  # Fetch wallet every 5 seconds (milliseconds)
        # Guard so we only have one in-flight background refresh at a time.
        self.wallet_refresh_inflight = False

        # Font for rendering wallet ID
        font_path = resource_path("assets", "Fonts", "hyperspace", "Hyperspace Bold.otf")
        try:
            self.wallet_font = pygame.font.Font(font_path, 14)
        except Exception:
            self.wallet_font = pygame.font.SysFont("arial", 14)

        # Initial wallet fetch.  Using the background variant means a cold
        # DNS lookup on api.spacecowboys.dev (or an undeployed backend) can
        # never freeze the pygbag canvas at game start -- the render loop
        # keeps drawing with gold_coins=0 and the response patches it in
        # when it lands.  On desktop, kick_off_background_json short-circuits
        # to a synchronous call when no asyncio loop is running, so the init
        # path stays unchanged there.
        self.refresh_wallet_background()

    def load_player_id(self, project_root):
        """Load the player's wallet ID from player_id.json."""
        player_id_path = os.path.join(project_root, "player_id.json")
        try:
            with open(player_id_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data.get("player_id", None)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def load_browser_player_id(self):
        """Read the player's wallet ID from browser localStorage, if any."""
        try:
            from platform import window  # type: ignore[import-not-found]
            stored = window.localStorage.getItem("player_id")
            if stored and stored != "null":
                return str(stored)
        except Exception as exc:
            print(f"[SpaceShip] localStorage player_id read failed: {exc}")
        return None

    def apply_wallet_payload(self, data):
        """Callback invoked by the background refresh with parsed JSON."""
        self.wallet_refresh_inflight = False
        if data and isinstance(data, dict):
            try:
                self.gold_coins = int(data.get("gold_coins", 0) or 0)
            except (TypeError, ValueError):
                pass

    def fetch_wallet_data(self):
        """Blocking fetch used at init time (desktop) or as a fallback.

        This path briefly blocks, which is acceptable before the game loop
        starts.  The per-frame refresh in :meth:`update` goes through
        :func:`kick_off_background_json` instead so the canvas never stalls.
        """
        if not self.player_wallet_id:
            return

        url = f"{BACKEND_API_URL}/api/wallet/{self.player_wallet_id}"
        data = fetch_json(url, timeout=2.0)
        if data and isinstance(data, dict):
            self.gold_coins = int(data.get("gold_coins", 0) or 0)

    def refresh_wallet_background(self):
        """Kick off a non-blocking wallet refresh; harmless if one is already in flight."""
        if not self.player_wallet_id or self.wallet_refresh_inflight:
            return
        url = f"{BACKEND_API_URL}/api/wallet/{self.player_wallet_id}"
        self.wallet_refresh_inflight = True
        scheduled = kick_off_background_json(
            "GET", url, on_result=self.apply_wallet_payload, timeout=3.0
        )
        if not scheduled:
            # Fall back to sync call; mirror flag so we don't leak the guard.
            self.wallet_refresh_inflight = False
            self.fetch_wallet_data()

    def update(self):
        """Update spaceship state, including periodic wallet data refresh.

        The refresh runs on an asyncio background task so a slow backend
        can never freeze the render loop.  The next frame keeps drawing
        with the last known ``gold_coins`` value until the response lands.
        """
        current_time = pygame.time.get_ticks()

        if current_time - self.wallet_last_fetched >= self.wallet_fetch_interval:
            self.wallet_last_fetched = current_time
            self.refresh_wallet_background()

    def draw_wallet_id(self, screen):
        """Render the player's wallet ID on screen with a background rect."""
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
        """Get the current gold coins balance from past matches."""
        return self.gold_coins

    def get_wallet_id(self):
        """Get the player's wallet ID."""
        return self.player_wallet_id