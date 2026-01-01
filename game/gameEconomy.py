import pygame
import webbrowser
import urllib.parse
import uuid
import os
import json
import random

PLAYER_ID_FILE = "player_id.json"
WALLET_FILE = "player_wallet.json"


def generate_player_id():
    return str(uuid.uuid4())

def get_or_create_player_id():
    """Get existing player ID or create a new one and save it"""
    if os.path.exists(PLAYER_ID_FILE):
        try:
            with open(PLAYER_ID_FILE, 'r') as f:
                data = json.load(f)
                return data.get('player_id', generate_player_id())
        except (json.JSONDecodeError, KeyError):
            # File exists but is corrupted, create new ID
            pass

    # Create new player ID
    player_id = generate_player_id()
    save_player_id(player_id)
    return player_id

def save_player_id(player_id):
    with open(PLAYER_ID_FILE, 'w') as f:
        json.dump({'player_id': player_id}, f)

# Initialize player ID on module load
player_id = get_or_create_player_id()

def get_player_id():
    return player_id

def initiate_payment(package_name, amount):
    """Open browser for payment processing"""
    base_url = "https://your-payment-server.com/purchase"
    params = {
        "package": package_name,
        "amount": amount,
        "game_id": get_player_id(),  # player tracking code
        "return_url": "yourgame://payment-success"  # Deep link back to game
    }
    payment_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    webbrowser.open(payment_url)


class PlayerWallet:
    """Wallet for managing player currency with unique serial numbers and persistent storage."""
    _used_ids: set[str] = set()
    
    def __init__(self, player_id: str = None):
        self.player_id = player_id or get_player_id()
        self.id = self._generate_serial_id()
        self.gold_coins = 0
        self.health_packs = 0
        self.total_earned_coins = 0
        self.total_earned_health_packs = 0
        self._load_wallet()
    
    @classmethod
    def _generate_serial_id(cls) -> str:
        """Generate a unique 3-digit serial ID."""
        for _ in range(1000):
            candidate = random.randint(0, 999)
            serial = f"{candidate:03d}"
            if serial not in cls._used_ids:
                cls._used_ids.add(serial)
                return serial
        raise RuntimeError("Unable to generate unique PlayerWallet ID")
    
    def get_serial_number(self) -> str:
        """Return the unique 3-digit serial number for this wallet."""
        return self.id
    
    def _get_wallet_path(self) -> str:
        """Get the wallet file path for this player."""
        return WALLET_FILE
    
    def _load_wallet(self):
        """Load wallet data from persistent storage."""
        wallet_path = self._get_wallet_path()
        if os.path.exists(wallet_path):
            try:
                with open(wallet_path, 'r') as f:
                    data = json.load(f)
                    if data.get('player_id') == self.player_id:
                        self.gold_coins = data.get('gold_coins', 0)
                        self.health_packs = data.get('health_packs', 0)
                        self.total_earned_coins = data.get('total_earned_coins', 0)
                        self.total_earned_health_packs = data.get('total_earned_health_packs', 0)
            except (json.JSONDecodeError, KeyError):
                pass
    
    def _save_wallet(self):
        """Save wallet data to persistent storage."""
        wallet_path = self._get_wallet_path()
        data = {
            'player_id': self.player_id,
            'wallet_serial': self.id,
            'gold_coins': self.gold_coins,
            'health_packs': self.health_packs,
            'total_earned_coins': self.total_earned_coins,
            'total_earned_health_packs': self.total_earned_health_packs
        }
        with open(wallet_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_gold_coins(self, amount: int):
        """Add gold coins to the wallet and persist."""
        self.gold_coins += amount
        self.total_earned_coins += amount
        self._save_wallet()
    
    def spend_gold_coins(self, amount: int) -> bool:
        """Spend gold coins if sufficient balance. Returns True if successful."""
        if self.gold_coins >= amount:
            self.gold_coins -= amount
            self._save_wallet()
            return True
        return False
    
    def add_health_pack(self, amount: int = 1):
        """Add health pack(s) to the wallet and persist."""
        self.health_packs += amount
        self.total_earned_health_packs += amount
        self._save_wallet()
    
    def use_health_pack(self) -> bool:
        """Use a health pack if available. Returns True if successful."""
        if self.health_packs > 0:
            self.health_packs -= 1
            self._save_wallet()
            return True
        return False
    
    def get_balance(self) -> dict:
        """Get current wallet balance."""
        return {
            'gold_coins': self.gold_coins,
            'health_packs': self.health_packs,
            'total_earned_coins': self.total_earned_coins,
            'total_earned_health_packs': self.total_earned_health_packs
        }


class game_economy:
    def __init__(self, initial_health=100):
        self.wallet = PlayerWallet()
        self.coins = self.wallet.gold_coins  # Load saved coins from wallet
        self.score = 0 
        self.health = initial_health
        self.potential_prizes = {
            "New Avater": False,
            "Gold Coins": False,
            "Faster_Bullet": False
        }
    
    def add_coins(self, amount):
        """Add coins to the economy and store in wallet"""
        self.coins += amount
        self.wallet.add_gold_coins(amount)
    
    def add_score(self, amount):
        """Add score to the economy"""
        self.score += amount
    
    def update_health(self, health):
        """Update health value"""
        self.health = health
    
    def earn_health_pack(self, amount: int = 1):
        """Earn a health pack and store in wallet"""
        self.wallet.add_health_pack(amount)
    
    def use_health_pack(self, heal_amount: int = 25) -> bool:
        """Use a health pack to restore health. Returns True if successful."""
        if self.wallet.use_health_pack():
            self.health = min(100, self.health + heal_amount)
            return True
        return False
    
    def get_wallet_balance(self) -> dict:
        """Get the current wallet balance."""
        return self.wallet.get_balance()
    
    def get_total_coins(self) -> int:
        """Get total coins stored in wallet."""
        return self.wallet.gold_coins
    
    def get_health_packs(self) -> int:
        """Get number of health packs in wallet."""
        return self.wallet.health_packs