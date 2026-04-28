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
    path = os.path.join(*parts).replace("\\", "/")
    if sys.platform == "emscripten":
        # Browser/APK layout can vary by loaderhome:
        # - /data/data/<bundle>/assets
        # - /data/data/<bundle>
        # Probe common relative candidates so asset loading is resilient.
        normalized = path.lstrip("./")
        candidates = [normalized]
        candidates.append(f"assets/{normalized}")
        if normalized.startswith("assets/"):
            candidates.append(normalized[len("assets/"):])
        # Keep ordering stable while removing duplicates.
        seen = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            try:
                if os.path.exists(candidate):
                    return candidate
            except Exception:
                # In browser runtimes, probing may fail before FS mount.
                pass
        return normalized
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
# IMPORTANT: pygbag hardcodes http://localhost:8000/archives/repo/ as the
# pygame-wheel source whenever the browser origin matches `http://localhost:8*`
# (see pygbag/support/cross/aio/pep0723.py ~line 233). On this project port
# 8000 is already occupied by the Django dev server, so that hardcoded URL
# 404s, blocks pygame from installing, and leaves the canvas stuck on the
# purple CSS body forever. Using a port OUTSIDE the 8xxx range sidesteps the
# heuristic so pygbag downloads pygame directly from pygame-web.github.io.
PYGBAG_PORT = 9666

# ============================================
# PRODUCTION / DEPLOYMENT URLS
# ============================================
# The pygbag browser build is hosted on Vercel at this domain.
VERCEL_DOMAIN_NAME = "https://spacecowboys.dev/"

# Canonical origin (no trailing slash) for the static pygbag frontend.
FRONTEND_ORIGIN = VERCEL_DOMAIN_NAME.rstrip("/")

# The FastAPI backend (server.py) lives on a subdomain so that CORS, cookies
# and Vercel routing stay clean.  Override via the GAME_BACKEND_URL env var
# when running a local FastAPI server or a staging backend.
PRODUCTION_BACKEND_URL = "https://api.spacecowboys.dev"
# Local backend lives on the same port as the pygbag dev server so the game
# has a single entry point during development: http://localhost:9666.
LOCAL_BACKEND_URL = f"http://localhost:{PYGBAG_PORT}"


def running_in_browser() -> bool:
    """True when executed inside the pygbag/Emscripten runtime."""
    return sys.platform == "emscripten"


def detect_browser_origin() -> str:
    """Return the current browser page origin (scheme://host[:port]) or ""."""
    if not running_in_browser():
        return ""
    try:
        from platform import window  # type: ignore[import-not-found]
        origin = getattr(window.location, "origin", None)
        if origin:
            return str(origin).rstrip("/")
    except Exception:
        pass
    return ""


def get_backend_api_url() -> str:
    """Resolve the backend base URL for the current runtime.

    Priority order:
      1. GAME_BACKEND_URL env var (desktop dev / CI overrides).
      2. If running in the browser and the page is served from a
         spacecowboys.dev host, use https://api.spacecowboys.dev.
      3. If running in the browser but on an unknown host (e.g. a preview
         deploy), fall back to the same origin under /api so reverse-proxy
         setups still work.
      4. Desktop default: ``http://localhost:9666`` (the pygbag port).
    """
    override = os.getenv("GAME_BACKEND_URL")
    if override:
        return override.rstrip("/")

    if running_in_browser():
        origin = detect_browser_origin()
        host = origin.rsplit("://", 1)[-1] if origin else ""
        if host.endswith("spacecowboys.dev"):
            return PRODUCTION_BACKEND_URL
        if origin:
            return origin
        return PRODUCTION_BACKEND_URL

    return LOCAL_BACKEND_URL


BACKEND_API_URL = get_backend_api_url()