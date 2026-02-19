# this config file wil centrally store the imports for the game to avoid circular imports

import os
# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

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
# Default background theme (relative path from project root)
DEFAULT_BACKGROUND_THEME = "assets/512x512_purple_nebula_1.png"

# Server constants/paths
GAME_BUILD_PATH = os.path.join(os.path.dirname(__file__), "build", "web")
