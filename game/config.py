# this config file wil centrally store the imports for the game to avoid circular imports

import os
import sys

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720


def resource_path(*parts: str) -> str:
    """
    Resolve asset paths for both desktop and Pygbag browser.
    In browser, CWD is appdir/assets (loaderhome); assets/ subpath resolves to
    assets/assets/ in the APK (e.g. assets/spaceship.png -> assets/assets/spaceship.png).
    """
    path = os.path.join(*parts)
    if sys.platform == "emscripten":
        # Browser: use forward slashes, relative to CWD (game root)
        return path.replace("\\", "/")
    # Desktop: resolve relative to config file (game dir)
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, path)

# Free currency (earned through gameplay)
INITIAL_COINS = 0
INITIAL_GEMS = 0

# Premium currency (purchased with real money)
INITIAL_PREMIUM_CURRENCY = 0

# Currency conversion rates
COINS_TO_GEMS_RATE = 100  # 100 coins = 1 gem
GEMS_TO_PREMIUM_RATE = 10  # 10 gems = 1 premium currency

# ============================================
# REWARD SYSTEM
# ============================================
# Base rewards
COINS_PER_ALIEN_KILL = 10
COINS_PER_LEVEL_COMPLETE = 50
COINS_PER_BONUS_SHIP = 100

# Treasure chest rewards
TREASURE_CHEST_MIN_COINS = 1000
TREASURE_CHEST_MAX_COINS = 50000
TRESURE_CHEST_HEALTH_PACK_CHANCE = .3 # 1/3 chance of receiving health pack from treasure chest 
TREASURE_CHEST_MIN_HEALTH_PACK = 1
TREASURE_CHEST_MAX_HEALTH_PACK = 5

# ============================================
# BACKGROUND THEMES
# ============================================
# Base game directory for runtime assets.
GAME_DIR = os.path.dirname(os.path.abspath(__file__))

# Default background theme path (use resource_path for browser compatibility).
DEFAULT_BACKGROUND_THEME = resource_path("assets", "512x512_purple_nebula_1.png")

# Server constants/paths
GAME_BUILD_PATH = os.path.join(os.path.dirname(__file__), "build", "web")
PYGBAG_PORT = 8666
