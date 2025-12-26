import pygame
import webbrowser
import urllib.parse
import uuid
import os
import json

PLAYER_ID_FILE = "player_id.json"


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


class game_economy:
    def __init__(self, initial_health=100):
        self.coins = 0 
        self.score = 0 
        self.health = initial_health
        self.potential_prizes = {
            "New Avater": False,
            "Gold Coins": False,
            "Faster_Bullet": False
        }
    
    def add_coins(self, amount):
        """Add coins to the economy"""
        self.coins += amount
    
    def add_score(self, amount):
        """Add score to the economy"""
        self.score += amount
    
    def update_health(self, health):
        """Update health value"""
        self.health = health