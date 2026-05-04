"""
Game Economy Module

This module provides:
- Local game economy management (score, health, in-game session state)
- Backend API client for wallet sync and purchases
- Player ID management
- Browser (Pygbag) compatibility for web deployment
"""
import uuid
import os
import json
import webbrowser
import sys
from typing import Optional
from dataclasses import dataclass
# Detect if running in browser (Pygbag/Emscripten)
IS_BROWSER = sys.platform == "emscripten"

# Conditional import for HTTP requests
if not IS_BROWSER:
    import requests  # Only available on desktop

# ============================================================================
# Configuration
# ============================================================================

PLAYER_ID_FILE = "player_id.json"


def default_backend_url() -> str:
    """Pick a sane backend base URL based on the runtime.

    * Env var ``GAME_BACKEND_URL`` always wins (for staging / tests).
    * In the browser, if the page is served from spacecowboys.dev, talk to
      ``https://api.spacecowboys.dev``.  Otherwise fall back to the page's
      own origin so reverse-proxy setups keep working.
    * On desktop, default to ``http://localhost:9666`` so the FastAPI
      dev server and the pygbag dev server share a single entry point.
    """
    override = os.getenv("GAME_BACKEND_URL")
    if override:
        return override.rstrip("/")

    if IS_BROWSER:
        try:
            from platform import window  # type: ignore[import-not-found]
            host = str(getattr(window.location, "hostname", "") or "")
            origin = str(getattr(window.location, "origin", "") or "").rstrip("/")
            if host.endswith("spacecowboys.dev"):
                return "https://api.spacecowboys.dev"
            if origin:
                return origin
        except Exception:
            pass
        return "https://api.spacecowboys.dev"

    return "http://localhost:9666"


BACKEND_URL = default_backend_url()
trans_id = None


# ============================================================================
# Player ID Management
# ============================================================================

def generate_player_id(player_id=None) -> str:
    """Generate a new unique player ID, or retrieve/create one if player_id is not provided."""
    if player_id is None:
        return get_or_create_player_id()
    return str(uuid.uuid4())


def get_or_create_player_id() -> str:
    """Get existing player ID or create a new one and save it.
    
    Uses localStorage in browser, file system on desktop.
    """
    if IS_BROWSER:
        # Use browser localStorage for persistence
        try:
            from platform import window
            stored_id = window.localStorage.getItem("player_id")
            if stored_id and stored_id != "null":
                return stored_id
            # Generate and store new ID
            new_id = generate_player_id()
            window.localStorage.setItem("player_id", new_id)
            return new_id
        except Exception as e:
            print(f"Browser localStorage error: {e}")
            # Fallback to session-only ID
            return generate_player_id()
    else:
        # Desktop: use file-based storage
        if os.path.exists(PLAYER_ID_FILE):
            try:
                with open(PLAYER_ID_FILE, 'r') as f:
                    data = json.load(f)
                    player_id = data.get('player_id')
                    if player_id:
                        return player_id
            except (json.JSONDecodeError, KeyError):
                pass

        player_id = generate_player_id()
        save_player_id(player_id)
        return player_id


def save_player_id(player_id: str):
    """Save player ID to persistent storage.
    
    Uses localStorage in browser, file system on desktop.
    """
    if IS_BROWSER:
        try:
            from platform import window
            window.localStorage.setItem("player_id", player_id)
        except Exception as e:
            print(f"Browser localStorage save error: {e}")
    else:
        with open(PLAYER_ID_FILE, 'w') as f:
            json.dump({'player_id': player_id}, f)


# Initialize player ID on module load
player_id = get_or_create_player_id()


def get_player_id() -> str:
    """Get the current player's ID."""
    return player_id


# ============================================================================
# Backend API Client
# ============================================================================

@dataclass
class WalletBalance:
    """Wallet balance from backend."""
    gold_coins: int
    health_packs: int
    gems: int
    total_earned_coins: int
    total_earned_health_packs: int
    total_spent_usd: float


@dataclass
class PurchaseSession:
    """Payment session for in-app purchase."""
    success: bool
    checkout_url: Optional[str] = None
    session_id: Optional[str] = None
    session_data: Optional[str] = None
    merchant_reference: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Package:
    """Purchasable package info."""
    id: str
    name: str
    price_usd: float
    gold_coins: int
    health_packs: int


class BackendClient:
    """Client for communicating with the game backend API.
    
    Supports both desktop (requests library) and browser (JavaScript fetch) environments.
    """
    
    def __init__(self, base_url: str = None, player_uuid: str = None):
        self.base_url = (base_url or BACKEND_URL).rstrip('/')
        self.player_uuid = player_uuid or get_player_id()
        self.cached_wallet: Optional[WalletBalance] = None
        self.pending_requests = []  # For async browser requests
    
    def request(self, method: str, endpoint: str, **kwargs) -> Optional[dict]:
        """Make an HTTP request to the backend.
        
        Uses requests library on desktop, JavaScript fetch in browser.
        """
        url = f"{self.base_url}{endpoint}"
        
        if IS_BROWSER:
            return self.browser_request_sync(method, url, **kwargs)
        else:
            return self.desktop_request(method, url, **kwargs)
    
    def desktop_request(self, method: str, url: str, **kwargs) -> Optional[dict]:
        """Desktop HTTP request using requests library."""
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Backend request failed: {e}")
            return None
    
    def browser_request_sync(self, method: str, url: str, **kwargs) -> Optional[dict]:
        """Browser HTTP request using JavaScript fetch (synchronous wrapper).
        
        Note: In browser, we use a synchronous XMLHttpRequest for compatibility
        with the existing synchronous API. For better performance, consider
        using async methods.
        """
        try:
            from platform import window
            
            # Create XMLHttpRequest for synchronous call
            xhr = window.XMLHttpRequest.new()
            xhr.open(method, url, False)  # False = synchronous
            
            # Set headers for JSON
            xhr.setRequestHeader("Content-Type", "application/json")
            
            # Prepare body if present
            body = None
            if "json" in kwargs:
                body = json.dumps(kwargs["json"])
            
            # Send request
            if body:
                xhr.send(body)
            else:
                xhr.send()
            
            # Check response
            if xhr.status >= 200 and xhr.status < 300:
                response_text = xhr.responseText
                if response_text:
                    return json.loads(response_text)
            else:
                print(f"Browser request failed with status: {xhr.status}")
            
            return None
        except Exception as e:
            print(f"Browser request error: {e}")
            return None
    
    def get_wallet(self, force_refresh: bool = False) -> Optional[WalletBalance]:
        """
        Get wallet balance from backend.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            WalletBalance or None if request failed
        """
        if not force_refresh and self.cached_wallet:
            return self.cached_wallet
        
        data = self.request("GET", f"/api/wallet/{self.player_uuid}")
        
        if data:
            self.cached_wallet = WalletBalance(
                gold_coins=data.get("gold_coins", 0),
                health_packs=data.get("health_packs", 0),
                gems=data.get("gems", 0),
                total_earned_coins=data.get("total_earned_coins", 0),
                total_earned_health_packs=data.get("total_earned_health_packs", 0),
                total_spent_usd=data.get("total_spent_usd", 0.0),
            )
            return self.cached_wallet
        
        return None
    
    def get_packages(self) -> list[Package]:
        """Get available purchase packages."""
        data = self.request("GET", "/api/packages")
        
        if data:
            return [
                Package(
                    id=p["id"],
                    name=p["name"],
                    price_usd=p["price_usd"],
                    gold_coins=p["gold_coins"],
                    health_packs=p["health_packs"],
                )
                for p in data
            ]
        
        return []
    
    def create_purchase_session(
        self,
        package_id: str,
        use_payment_link: bool = True,
        email: Optional[str] = None,
    ) -> PurchaseSession:
        """
        Create a payment session for a package purchase.
        
        Args:
            package_id: ID of the package to purchase (e.g., "gold_100")
            use_payment_link: If True, returns a shareable payment link
            email: Optional email for receipt
            
        Returns:
            PurchaseSession with checkout details
        """
        data = self.request(
            "POST",
            "/api/payment/create-session",
            json={
                "player_uuid": self.player_uuid,
                "package_id": package_id,
                "use_payment_link": use_payment_link,
                "email": email,
            }
        )
        
        if data:
            return PurchaseSession(
                success=data.get("success", False),
                checkout_url=data.get("checkout_url"),
                session_id=data.get("session_id"),
                session_data=data.get("session_data"),
                merchant_reference=data.get("merchant_reference"),
                error=data.get("error"),
            )
        
        return PurchaseSession(success=False, error="Failed to connect to backend")
    
    def initiate_purchase(self, package_id: str, email: Optional[str] = None) -> bool:
        """
        Initiate a purchase and open the checkout page in browser.
        
        Args:
            package_id: ID of the package to purchase
            email: Optional email for receipt
            
        Returns:
            True if checkout was opened successfully
        """
        session = self.create_purchase_session(
            package_id=package_id,
            use_payment_link=True,
            email=email,
        )
        
        if session.success and session.checkout_url:
            if IS_BROWSER:
                # In browser, use JavaScript to open URL in new tab
                try:
                    from platform import window
                    window.open(session.checkout_url, "_blank")
                    return True
                except Exception as e:
                    print(f"Failed to open checkout URL in browser: {e}")
                    return False
            else:
                # On desktop, use webbrowser module
                webbrowser.open(session.checkout_url)
                return True
        
        print(f"Failed to initiate purchase: {session.error}")
        return False
    
    def spend_coins(self, amount: int) -> bool:
        """
        Spend gold coins on the backend.
        
        Args:
            amount: Number of coins to spend
            
        Returns:
            True if successful
        """
        data = self.request(
            "POST",
            "/api/wallet/spend",
            json={
                "player_uuid": self.player_uuid,
                "amount": amount,
            }
        )
        
        if data and data.get("success"):
            # Invalidate cache
            self.cached_wallet = None
            return True
        
        return False
    
    def use_health_pack(self) -> bool:
        """
        Use a health pack on the backend.
        
        Returns:
            True if successful
        """
        data = self.request(
            "POST",
            "/api/wallet/use-health-pack",
            json={"player_uuid": self.player_uuid}
        )
        
        if data and data.get("success"):
            self.cached_wallet = None
            return True
        
        return False
    
    def add_earned_coins(self, amount: int) -> dict:
        """
        Add earned coins from gameplay to the backend wallet.
        
        Args:
            amount: Number of coins earned during gameplay
            
        Returns:
            Dict with success status, coins_added, and new_balance
        """
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        
        data = self.request(
            "POST",
            "/api/wallet/add-earned-coins",
            json={
                "player_uuid": self.player_uuid,
                "amount": amount,
            }
        )
        
        if data and data.get("success"):
            self.cached_wallet = None  # Invalidate cache
            return {
                "success": True,
                "coins_added": data.get("coins_added", amount),
                "new_balance": data.get("new_balance", 0),
            }
        
        return {"success": False, "error": "Failed to add coins to wallet"}
    
    def get_transaction_history(self, limit: int = 20) -> list[dict]:
        """Get recent transaction history."""
        global trans_id
        data = self.request(
            "GET",
            f"/api/payment/transactions/{self.player_uuid}?limit={limit}"
        )
        trans_id = self.request("GET")
        
        return data if data else []
    
    def sync_wallet(self, local_wallet: dict | None = None) -> Optional[WalletBalance]:
        """Push local wallet state to the backend and pull the merged result.

        If *local_wallet* is provided the backend merges it (max-wins) with
        the stored wallet and returns the result.  Otherwise falls back to a
        plain GET refresh.
        """
        if local_wallet:
            payload = {
                "player_uuid": self.player_uuid,
                "gold_coins": int(local_wallet.get("gold_coins", 0)),
                "health_packs": int(local_wallet.get("health_packs", 0)),
                "gems": int(local_wallet.get("gems", 0)),
                "total_earned_coins": int(local_wallet.get("total_earned_coins", 0)),
                "session_coins_earned": int(local_wallet.get("session_coins_earned", 0)),
            }
            data = self.request("POST", "/api/wallet/sync", json=payload)
            if data:
                wallet_data = data.get("wallet", data)
                self.cached_wallet = WalletBalance(
                    gold_coins=wallet_data.get("gold_coins", 0),
                    health_packs=wallet_data.get("health_packs", 0),
                    gems=wallet_data.get("gems", 0),
                    total_earned_coins=wallet_data.get("total_earned_coins", 0),
                    total_earned_health_packs=wallet_data.get("total_earned_health_packs", 0),
                    total_spent_usd=wallet_data.get("total_spent_usd", 0.0),
                )
                return self.cached_wallet
        return self.get_wallet(force_refresh=True)


# ============================================================================
# Game Economy (Local Session State)
# ============================================================================

class GameEconomy:
    """
    Manages the local game session economy.
    
    This class handles:
    - In-game score tracking
    - Health management
    - Session-level coin tracking
    - Backend synchronization via BackendClient
    """
    
    def __init__(self, initial_health: int = 100, backend_url: str = None, ):
        self.backend = BackendClient(base_url=backend_url)
        self.score = 0
        self.health = initial_health
        self.max_health = initial_health
        self.session_coins_earned = 0  # Coins earned this session
        self.save_session_earnings = True

        # Pause/resume state
        self.is_paused = False
        self.paused_state = None  # Stores game state when paused

        # Prizes/achievements for this session
        self.potential_prizes = {
            "New Avatar": False,
            "Gold Coins": False,
            "Faster Bullet": False,
        }

        # Avatar store catalog: id -> {name, price, image_file, description}
        self.avatar_catalog = {
            "default": {
                "name": "Classic Ship",
                "price": 0,
                "image_file": "assets/spaceship.png",
                "description": "The original spaceship",
            },
            "alien_hunter": {
                "name": "Alien Hunter",
                "price": 2.99,
                "image_file": "assets/alien_hunter_avatar.png",
                "description": "A battle-worn cruiser feared by aliens",
            },
            "neon_falcon": {
                "name": "Neon Falcon",
                "price": 2.99,
                "image_file": "assets/neon_falcon_avatar.png",
                "description": "Sleek neon-lit interceptor",
            },
            "star_phoenix": {
                "name": "Star Phoenix",
                "price": 2.99,
                "image_file": "assets/star_phoenix_avatar.png",
                "description": "Legendary phoenix-class warship",
            },
            "shadow_viper": {
                "name": "Shadow Viper",
                "price": 2.99,
                "image_file": "assets/shadow_viper_avatar.png",
                "description": "Stealth fighter with dark energy shields",
            },
            "cosmic_dragon": {
                "name": "Cosmic Dragon",
                "price": 2.99,
                "image_file": "assets/cosmic_dragon_avatar.png",
                "description": "Mythical dragon-forged flagship",
            },
        }

        # "default" is always owned; additional avatars are added on purchase
        self.owned_avatars: set[str] = {"default"}
        self.active_avatar: str = "default"

        # Sync with backend on init
        self.synced_wallet: Optional[WalletBalance] = None
        self.sync_wallet()
    
    @property
    def player_id(self) -> str:
        """Get the player's unique ID."""
        return self.backend.player_uuid
    
    @property
    def coins(self) -> int:
        """Get total coins (from backend wallet)."""
        if self.synced_wallet:
            return self.synced_wallet.gold_coins
        return 0

    # This method leverages the existing coins
    # property which already fetches the gold_coins
    # from the backend wallet.

    def get_total_coins(self) -> int:
        """Get total coins from the player's wallet."""
        return self.coins
    
    def add_coins(self, amount: int):
        """
        Add coins to the current session's earned coins.
        
        Called during gameplay when player earns coins (e.g., destroying aliens).
        These coins are tracked locally and saved to the wallet via save_session_coins().
        
        Args:
            amount: Number of coins to add to session earnings
        """
        if amount > 0:
            self.session_coins_earned += amount 
            pass

    # save session analytics function for gold coins

    def save_session_coins(self) -> dict:
        """
        Save coins earned during the current session to the player's wallet.
        
        Call this at the end of a level or when the player completes a session
        to persist their earned coins to the backend wallet.
        
        Returns:
            Dict with:
                - success: bool indicating if save was successful
                - coins_added: number of coins added to wallet
                - new_balance: updated wallet balance
                - error: error message if failed
        """
        if self.session_coins_earned <= 0:
            return {
                "success": False,
                "coins_added": 0,
                "error": "No coins to save"
            }
        
        result = self.backend.add_earned_coins(self.session_coins_earned)
        
        if result.get("success"):
            saved_amount = self.session_coins_earned
            self.session_coins_earned = 0  # Reset session earnings
            self.sync_wallet()  # Refresh wallet balance from backend
            return {
                "success": True,
                "coins_added": saved_amount,
                "new_balance": result.get("new_balance", self.coins),
            }
        
        return {
            "success": False,
            "coins_added": 0,
            "error": result.get("error", "Failed to save coins")
        }

    # pause feature
    def pause_game(self, game_state: dict) -> dict:
        """
        Pause the game and save the current game state.
        
        Args:
            game_state: Dict containing current game state (score, health, enemies, etc.)
                       This should be a snapshot of the game at pause time.
        
        Returns:
            Dict with success status and pause timestamp
        """
        self.is_paused = True
        self.paused_state = {
            "timestamp": __import__('time').time(),
            "score": self.score,
            "health": self.health,
            "session_coins_earned": self.session_coins_earned,
            "game_state": game_state,  # Game-specific state (enemies, bullets, player pos, etc.)
        }
        return {
            "success": True,
            "message": "Game paused",
            "paused_at": self.paused_state["timestamp"],
        }
    
    def resume_game(self) -> dict:
        """
        Resume the game from a paused state.
        
        Returns:
            Dict with:
                - success: bool indicating if resume was successful
                - paused_state: the saved game state to restore
                - error: error message if failed
        """
        if not self.is_paused:
            return {
                "success": False,
                "error": "Game is not paused"
            }
        
        if not self.paused_state:
            return {
                "success": False,
                "error": "No paused state found"
            }
        
        saved_state = self.paused_state
        self.is_paused = False
        self.paused_state = None
        
        return {
            "success": True,
            "paused_state": saved_state,
            "message": "Game resumed"
        }
    
    def is_game_paused(self) -> bool:
        """Check if the game is currently paused."""
        return self.is_paused
# function to track state of the the game when paused
    def get_paused_state(self) -> Optional[dict]:
        """Get the saved pause state without resuming."""
        return self.paused_state if self.is_paused else None

    # ------------------------------------------------------------------ #
    # Avatar Store
    # ------------------------------------------------------------------ #

    def get_avatar_catalog(self) -> list[dict]:
        """Return the full avatar catalog with ownership and equipped status.

        Each entry contains: id, name, price, image_file, description,
        owned (bool), and equipped (bool).
        """
        catalog = []
        for avatar_id, info in self.avatar_catalog.items():
            catalog.append({
                "id": avatar_id,
                "name": info["name"],
                "price": info["price"],
                "image_file": info["image_file"],
                "description": info["description"],
                "owned": avatar_id in self.owned_avatars,
                "equipped": avatar_id == self.active_avatar,
            })
        return catalog

    def buy_avatar(self, avatar_id: str) -> dict:
        """Purchase an avatar from the store using gold coins.

        Args:
            avatar_id: The catalog key of the avatar to buy.

        Returns:
            Dict with success status, a message, and the avatar info
            on success, or an error string on failure.
        """
        if avatar_id not in self.avatar_catalog:
            return {"success": False, "error": "Avatar not found in store"}

        if avatar_id in self.owned_avatars:
            return {"success": False, "error": "Avatar already owned"}

        avatar_info = self.avatar_catalog[avatar_id]
        price = avatar_info["price"]

        if self.coins < price:
            return {
                "success": False,
                "error": f"Not enough coins (need {price}, have {self.coins})",
            }

        if not self.spend_coins(price):
            return {"success": False, "error": "Transaction failed"}

        self.owned_avatars.add(avatar_id)
        self.potential_prizes["New Avatar"] = True

        return {
            "success": True,
            "message": f"Purchased {avatar_info['name']}!",
            "avatar": {
                "id": avatar_id,
                "name": avatar_info["name"],
                "image_file": avatar_info["image_file"],
            },
        }

    def select_avatar(self, avatar_id: str) -> dict:
        """Set an owned avatar as the active player ship image.

        Args:
            avatar_id: The catalog key of the avatar to equip.

        Returns:
            Dict with success status and the active avatar image file,
            or an error string on failure.
        """
        if avatar_id not in self.avatar_catalog:
            return {"success": False, "error": "Avatar not found"}

        if avatar_id not in self.owned_avatars:
            return {"success": False, "error": "Avatar not owned"}

        self.active_avatar = avatar_id
        avatar_info = self.avatar_catalog[avatar_id]
        return {
            "success": True,
            "message": f"{avatar_info['name']} equipped!",
            "image_file": avatar_info["image_file"],
        }

    def get_active_avatar_image(self) -> str:
        """Return the image file path for the currently equipped avatar.

        The path is relative to the game's project root (e.g.
        ``assets/spaceship.png``).  The caller should join this with
        the project root to build an absolute path for pygame.
        """
        info = self.avatar_catalog.get(self.active_avatar)
        if info:
            return info["image_file"]
        return self.avatar_catalog["default"]["image_file"]

    @property
    def health_packs(self) -> int:
        """Get health packs count (from backend wallet)."""
        if self.synced_wallet:
            return self.synced_wallet.health_packs
        return 0

    @property
    def gems(self) -> int:
        """Get gems count (from backend wallet)."""
        if self.synced_wallet:
            return self.synced_wallet.gems
        return 0
    
    def sync_wallet(self) -> bool:
        """Push local wallet state to the backend and pull the merged result."""
        local = self.get_wallet_balance()
        wallet = self.backend.sync_wallet(local_wallet=local)
        if wallet:
            self.synced_wallet = wallet
            return True
        return False
    
    def add_score(self, amount: int):
        """Add score to the current session."""
        self.score += amount
    
    def update_health(self, health: int):
        """Update current health value."""
        self.health = max(0, min(self.max_health, health))
    
    def take_damage(self, amount: int):
        """Take damage and reduce health."""
        self.health = max(0, self.health - amount)
    
    def heal(self, amount: int):
        """Heal and increase health."""
        self.health = min(self.max_health, self.health + amount)
    
    def use_health_pack(self, heal_amount: int = 25) -> bool:
        """
        Use a health pack to restore health.
        
        Args:
            heal_amount: Amount of health to restore
            
        Returns:
            True if health pack was used successfully
        """
        if self.backend.use_health_pack():
            self.heal(heal_amount)
            self.sync_wallet()  # Refresh wallet
            return True
        return False
    
    def earn_coins(self, amount: int):
        """
        Record coins earned during gameplay.
        Note: Coins earned in-game should be synced to backend at session end.
        """
        self.session_coins_earned += amount
    
    def spend_coins(self, amount: int) -> bool:
        """
        Spend coins via backend.
        
        Args:
            amount: Number of coins to spend
            
        Returns:
            True if successful
        """
        if self.backend.spend_coins(amount):
            self.sync_wallet()
            return True
        return False
    
    def get_available_packages(self) -> list[Package]:
        """Get available in-app purchase packages."""
        return self.backend.get_packages()
    
    def purchase_package(self, package_id: str, email: Optional[str] = None) -> bool:
        """
        Initiate a package purchase (opens browser).
        
        Args:
            package_id: ID of the package to purchase
            email: Optional email for receipt
            
        Returns:
            True if checkout was opened successfully
        """
        return self.backend.initiate_purchase(package_id, email)
    
    def get_wallet_balance(self) -> dict:
        """Get current wallet balance as dictionary."""
        if self.synced_wallet:
            return {
                "gold_coins": self.synced_wallet.gold_coins,
                "health_packs": self.synced_wallet.health_packs,
                "gems": self.synced_wallet.gems,
                "total_earned_coins": self.synced_wallet.total_earned_coins,
                "total_earned_health_packs": self.synced_wallet.total_earned_health_packs,
                "session_coins_earned": self.session_coins_earned,
            }
        return {
            "gold_coins": 0,
            "health_packs": 0,
            "gems": 0,
            "total_earned_coins": 0,
            "total_earned_health_packs": 0,
            "session_coins_earned": self.session_coins_earned,
        }
    
    def get_session_summary(self) -> dict:
        """Get summary of current game session."""
        return {
            "score": self.score,
            "health": self.health,
            "session_coins_earned": self.session_coins_earned,
            "wallet": self.get_wallet_balance(),
            "prizes_unlocked": [k for k, v in self.potential_prizes.items() if v],
            "active_avatar": self.active_avatar,
            "owned_avatars": list(self.owned_avatars),
        }
    
    def reset_session(self):
        """Reset session state (for new game)."""
        self.score = 0
        self.health = self.max_health
        self.session_coins_earned = 0
        self.potential_prizes = {k: False for k in self.potential_prizes}
        self.sync_wallet()


# ============================================================================
# Convenience Functions (Backwards Compatibility)
# ============================================================================

# For backwards compatibility with existing game code
game_economy = GameEconomy


def initiate_payment(package_name: str, amount: float = None):
    """
    Legacy function to initiate payment.
    Deprecated: Use GameEconomy.purchase_package() instead.
    """
    client = BackendClient()
    
    # Map old package names to new IDs
    package_map = {
        "100 Gold Coins": "gold_100",
        "500 Gold Coins": "gold_500",
        "1000 Gold Coins": "gold_1000",
        "5 Health Packs": "health_pack_5",
        "10 Health Packs": "health_pack_10",
        "Starter Bundle": "starter_bundle",
    }
    
    package_id = package_map.get(package_name, package_name.lower().replace(" ", "_"))
    client.initiate_purchase(package_id)
