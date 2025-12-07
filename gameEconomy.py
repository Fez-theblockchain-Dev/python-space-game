import pygame
import player


import webbrowser
import urllib.parse

PLAYER_ID_FILE = "player_id.json"


def generate_player_id():
    return str(uuid.uuid4())
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
    def __init__(self):
        self.coins = 0 
        self.score = 0 
        self.health = player
        self.potential_prizes = {
            "New Avater": False,
            "Gold Coins": False,
            "Faster_Bullet": False

        }