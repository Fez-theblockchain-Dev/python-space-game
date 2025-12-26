🛸 Space Invaders
🎮 Introduction

Space Invaders is a modern take on the classic retro arcade shooter, built using Python and Pygame. This project demonstrates object-oriented design principles, game development fundamentals, and a foundational understanding of rendering, event handling, and sprite-based animation.

Designed as a showcase project for a Junior Python Developer, it also introduces a basic game economy, including gold coin collection through gameplay and an in-progress integration of in-app purchases via Apple Pay.

📜 Table of Contents

Installation

Usage

Features

Project Structure

Dependencies

Configuration

Examples

Troubleshooting

Contributors

License

💾 Installation

Clone the repository:

git clone https://github.com/yourusername/space-invaders.git
cd space-invaders


Install dependencies:

pip install -r requirements.txt


Run the game:

python index.py

🚀 Usage

Use the keyboard to navigate and shoot enemies. Earn gold coins by defeating aliens. A shop system and Apple Pay integration for purchasing gold is currently under development.

Controls:

Arrow keys to move

Spacebar to shoot

✨ Features

Object-Oriented Design

Custom player, enemy, laser, and obstacle classes

In-game currency system (gold coins)

Planned support for Apple Pay

Interactive main menu with buttons

Sound and sprite effects

Increasing difficulty mechanics

📁 Project Structure
.
├── index.py            # Main game loop
├── config.py           # Game settings and constants
├── player.py           # Player class logic
├── alien.py            # Alien enemy behavior
├── obstacle.py         # Destructible barriers
├── laser.py            # Laser projectile logic
├── spaceship.py        # Base class for player/enemy ships
├── button.py           # Button UI logic
├── gameEconomy.py      # Coin system and (future) Apple Pay integration
├── mainMenu.py         # Main menu rendering and navigation

📦 Dependencies

Python 3.8+

Pygame

To install:

pip install pygame

⚙️ Configuration

Settings such as screen dimensions, player attributes, and colors are defined in config.py. You can tweak these values to customize the game.

🧪 Examples
# Run the main game
python index.py


As the game starts, aliens will descend and shoot lasers. Eliminate them to collect gold. The game will continue until the player loses all lives.

🛠️ Troubleshooting

Ensure Python and Pygame are correctly installed.

If the game window doesn't launch, verify the display drivers or Pygame installation.

In-app purchase system is a work in progress and currently disabled.

👨‍💻 Contributors

Created by a Junior Python Developer passionate about game development and object-oriented programming.

Looking for opportunities to contribute to larger Python projects or join a development team!

📝 License

This project is licensed under the MIT License
.

✅ Next Steps

Before finalizing the README:

Would you like to include screenshots or a GIF of gameplay?

Do you want to add your name or GitHub profile?

Should I help you generate a requirements.txt file?

Let me know if you'd like this exported to a .md file or pushed to a GitHub repo structure. 