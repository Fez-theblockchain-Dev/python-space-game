🛸 Space Cowboys🚀

🎮 Introduction
Space Cowboys🚀 is a modern take on the classic retro arcade shooter, built using Python and Pygame. This project demonstrates object-oriented design principles, game development fundamentals, and a foundational understanding of rendering, event handling, and sprite-based animation.

Designed as a showcase project for a Junior Python Developer, it also introduces a basic game economy, including gold coin collection through gameplay and an in-progress integration of in-app purchases via Apple Pay.

📜 Table of Contents

Installation:

Prerequisites - Python 3.8+ and Pygame are required for the game client.

Steps:

1.Clone the repository:
git clone https://github.com/Fez-theblockchain-Dev/python-space-game
cd python-space-game

2.(Recommended) Create and activate a virtual environment:
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

3.Install the game dependency (Pygame):
pip install pygame


4.Run the game:
python -m game
# or: python game/main.py

5.Backend API dependencies - Install the backend API required software to get full bemefits of the game, such as, in-progress shop/payment features, install backend dependencies from the API folder:

pip install -r backend_apis/requirements.txt

Usage:
Movement - Arrow keys move the ship.

Shoot - Spacebar fires lasers.

Game includes a main menu and themed backgrounds handled by the menu system.

Features:
Object-oriented design with dedicated classes for player, enemies, lasers, and obstacles.

In-game currency system (gold coins).

Planned Apple Pay integration for purchases (in progress).

Interactive main menu, sound, sprites, and increasing difficulty mechanics.

Project Structure:
game/__main__.py — main game loop and runtime setup (Pygbag entrypoint).

game/config.py — game settings and constants (screen size, economy values).

game/mainMenu.py — menu rendering and theme management.

assets/ — image and font assets loaded by the game (backgrounds, fonts, ship sprite).

audio/ — sound effects (laser sound loaded by the player class).

backend_apis/ — backend services and economy integration.

Demo of Space Cowboys🚀 Shop:
- Space Cowboys🚀 Shop screen recording: [https://share.icloud.com/photos/04aff3DEOm7JH6AvxIznxHbeA]

Dependencies:
Game Client

Python 3.8+

Pygame

Backend API

FastAPI, SQLAlchemy, Requests, Pydantic (for the backend server)


Configuration:
-Gameplay and economy constants (screen size, coin rates, rewards) live in game/config.py.

-The backend API base URL is configurable via the GAME_BACKEND_URL environment variable (defaults to http://localhost:8000).

-** Pygbag server for playing the space cowboys🚀 game through DOM browser can be run using:
python -m pygbag --template custom.tmpl --port 9666 game **

  Note: port 9666 (not 8xxx) is deliberate. Pygbag 0.9.2 hardcodes
  http://localhost:8000/archives/repo/ as the pygame-wheel source whenever the
  browser origin matches localhost:8* (pygbag/support/cross/aio/pep0723.py
  ~line 233). On this project port 8000 is the Django dev server, which 404s
  for wheel URLs and blocks pygame from loading in the browser. Staying off
  8xxx avoids that collision.

Troubleshooting:
-Ensure Python and Pygame are installed correctly.
-If the game window doesn’t launch, check display drivers or reinstall Pygame.
-Audio warnings can appear if sound files are missing or fail to load (the game will continue).
-In-app purchases are a work in progress and may be disabled.

📝 License: MIT

👨‍💻 Contributors - Ramez L. Festek ( Full-Stack Software Engineer): 

Hello! Thanks for reading thru the full md file, I'm looking for opportunities to contribute to larger Python projects or join a development team! Preferably in TX/FL/Remote, however open to relocating elsewhere.

