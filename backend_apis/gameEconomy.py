"""
Game Economy Module

This module provides:
- Local game economy management (score, health, in-game session state)
- Backend API client for wallet sync and purchases
- Player ID management
"""
import uuid
import os
import json
import webbrowser
from typing import Optional
from dataclasses import dataclass

# For API calls to backend
import requests

# ============================================================================
# Configuration
# ============================================================================

PLAYER_ID_FILE = "player_id.json"
BACKEND_URL = os.getenv("GAME_BACKEND_URL", "http://localhost:8000")


# ============================================================================
# Player ID Management
# ============================================================================

def generate_player_id() -> str:
    """Generate a new unique player ID."""
    return str(uuid.uuid4())


def get_or_create_player_id() -> str:
    """Get existing player ID or create a new one and save it."""
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
    """Save player ID to file."""
    with open(PLAYER_ID_FILE, 'w') as f:
        json.dump({'player_id': player_id}, f)


# Initialize player ID on module load
_player_id = get_or_create_player_id()


def get_player_id() -> str:
    """Get the current player's ID."""
    return _player_id


# ============================================================================
# Backend API Client
# ============================================================================

@dataclass
class WalletBalance:
    """Wallet balance from backend."""
    gold_coins: int
    health_packs: int
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
    """Client for communicating with the game backend API."""
    
    def __init__(self, base_url: str = None, player_uuid: str = None):
        self.base_url = (base_url or BACKEND_URL).rstrip('/')
        self.player_uuid = player_uuid or get_player_id()
        self._cached_wallet: Optional[WalletBalance] = None
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[dict]:
        """Make an HTTP request to the backend."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Backend request failed: {e}")
            return None
    
    def get_wallet(self, force_refresh: bool = False) -> Optional[WalletBalance]:
        """
        Get wallet balance from backend.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            WalletBalance or None if request failed
        """
        if not force_refresh and self._cached_wallet:
            return self._cached_wallet
        
        data = self._request("GET", f"/api/wallet/{self.player_uuid}")
        
        if data:
            self._cached_wallet = WalletBalance(
                gold_coins=data.get("gold_coins", 0),
                health_packs=data.get("health_packs", 0),
                total_earned_coins=data.get("total_earned_coins", 0),
                total_earned_health_packs=data.get("total_earned_health_packs", 0),
                total_spent_usd=data.get("total_spent_usd", 0.0),
            )
            return self._cached_wallet
        
        return None
    
    def get_packages(self) -> list[Package]:
        """Get available purchase packages."""
        data = self._request("GET", "/api/packages")
        
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
        data = self._request(
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
        data = self._request(
            "POST",
            "/api/wallet/spend",
            json={
                "player_uuid": self.player_uuid,
                "amount": amount,
            }
        )
        
        if data and data.get("success"):
            # Invalidate cache
            self._cached_wallet = None
            return True
        
        return False
    
    def use_health_pack(self) -> bool:
        """
        Use a health pack on the backend.
        
        Returns:
            True if successful
        """
        data = self._request(
            "POST",
            "/api/wallet/use-health-pack",
            json={"player_uuid": self.player_uuid}
        )
        
        if data and data.get("success"):
            self._cached_wallet = None
            return True
        
        return False
    
    def get_transaction_history(self, limit: int = 20) -> list[dict]:
        """Get recent transaction history."""
        data = self._request(
            "GET",
            f"/api/payment/transactions/{self.player_uuid}?limit={limit}"
        )
        
        return data if data else []
    
    def sync_wallet(self) -> Optional[WalletBalance]:
        """Force sync wallet from backend."""
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

        
        

        # Prizes/achievements for this session
        self.potential_prizes = {
            "New Avatar": False,
            "Gold Coins": False,
            "Faster Bullet": False,
        }
        
        # Sync with backend on init
        self._synced_wallet: Optional[WalletBalance] = None
        self.sync_wallet()
    
    @property
    def player_id(self) -> str:
        """Get the player's unique ID."""
        return self.backend.player_uuid
    
    @property
    def coins(self) -> int:
        """Get total coins (from backend wallet)."""
        if self._synced_wallet:
            return self._synced_wallet.gold_coins
        return 0

# This method leverages the existing coins 
# property which already fetches the gold_coins 
# from the backend wallet. 

    def get_total_coins(self) -> int:
        """Get total coins from the player's wallet."""
        return self.coins
    
    @property
    def health_packs(self) -> int:
        """Get health packs count (from backend wallet)."""
        if self._synced_wallet:
            return self._synced_wallet.health_packs
        return 0
    
    def sync_wallet(self) -> bool:
        """Sync wallet balance from backend."""
        wallet = self.backend.sync_wallet()
        if wallet:
            self._synced_wallet = wallet
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
        if self._synced_wallet:
            return {
                "gold_coins": self._synced_wallet.gold_coins,
                "health_packs": self._synced_wallet.health_packs,
                "total_earned_coins": self._synced_wallet.total_earned_coins,
                "total_earned_health_packs": self._synced_wallet.total_earned_health_packs,
            }
        return {
            "gold_coins": 0,
            "health_packs": 0,
            "total_earned_coins": 0,
            "total_earned_health_packs": 0,
        }
    
    def get_session_summary(self) -> dict:
        """Get summary of current game session."""
        return {
            "score": self.score,
            "health": self.health,
            "session_coins_earned": self.session_coins_earned,
            "wallet": self.get_wallet_balance(),
            "prizes_unlocked": [k for k, v in self.potential_prizes.items() if v],
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
