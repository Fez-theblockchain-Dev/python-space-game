import sys
import pygame
import os
from button import Button

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Space Invaders - Main Menu")

# Theme management
class ThemeManager:
    def __init__(self):
        self.themes = []
        self.current_theme_index = 0
        self.load_themes()
    
    def load_themes(self):
        """Load all available background themes"""
        # Get the base directory (parent of game directory)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Default black background
        black_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        black_bg.fill((0, 0, 0))
        self.themes.append(("Black", black_bg))
        
        # Load main menu background if it exists
        menu_bg_path = os.path.join(base_dir, 'assets', 'main_menu_background.png')
        if os.path.exists(menu_bg_path):
            try:
                menu_bg_img = pygame.image.load(menu_bg_path).convert()
                menu_bg = pygame.transform.scale(menu_bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.themes.append(("Menu Background", menu_bg))
            except pygame.error:
                print(f"Warning: Could not load {menu_bg_path}")
        
        # Load nebula background if it exists
        nebula_bg_path = os.path.join(base_dir, 'assets', '512x512_purple_nebula_1.png')
        if os.path.exists(nebula_bg_path):
            try:
                nebula_bg_img = pygame.image.load(nebula_bg_path).convert()
                nebula_bg = pygame.transform.scale(nebula_bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.themes.append(("Purple Nebula", nebula_bg))
            except pygame.error:
                print(f"Warning: Could not load {nebula_bg_path}")
    
    def get_current_background(self):
        """Get the current background surface"""
        if self.themes:
            return self.themes[self.current_theme_index][1]
        # Fallback to black
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill((0, 0, 0))
        return bg
    
    def get_current_theme_name(self):
        """Get the name of the current theme"""
        if self.themes:
            return self.themes[self.current_theme_index][0]
        return "Default"
    
    def next_theme(self):
        """Cycle to the next theme"""
        if self.themes:
            self.current_theme_index = (self.current_theme_index + 1) % len(self.themes)

# Create global theme manager instance
theme_manager = ThemeManager()

def get_font(size):
    """Font size function"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_path = os.path.join(base_dir, 'assets', 'Fonts', 'hyperspace', 'Hyperspace Bold Italic.otf')
    try:
        return pygame.font.Font(font_path, size)
    except:
        return pygame.font.Font(None, size)

def main_menu():
    """Main menu screen"""
    clock = pygame.time.Clock()
    
    while True:
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        
        # Draw current background
        SCREEN.blit(theme_manager.get_current_background(), (0, 0))
        
        # Title
        MENU_TEXT = get_font(100).render("SPACE INVADERS", True, "#b68f40")
        MENU_RECT = MENU_TEXT.get_rect(center=(640, 100))
        SCREEN.blit(MENU_TEXT, MENU_RECT)
        
        # Current theme display
        theme_text = get_font(30).render(f"Theme: {theme_manager.get_current_theme_name()}", True, "White")
        theme_text_rect = theme_text.get_rect(center=(640, 180))
        SCREEN.blit(theme_text, theme_text_rect)
        
        # Buttons
        PLAY_BUTTON = Button(
            image=None, 
            pos=(640, 300), 
            text_input="PLAY", 
            font=get_font(75), 
            base_color="#d7fcd4", 
            hovering_color="White"
        )
        
        THEME_BUTTON = Button(
            image=None, 
            pos=(640, 400), 
            text_input="THEME", 
            font=get_font(75), 
            base_color="#d7fcd4", 
            hovering_color="White"
        )
        
        QUIT_BUTTON = Button(
            image=None, 
            pos=(640, 500), 
            text_input="QUIT", 
            font=get_font(75), 
            base_color="#d7fcd4", 
            hovering_color="White"
        )
        
        # Update button colors on hover
        for button in [PLAY_BUTTON, THEME_BUTTON, QUIT_BUTTON]:
            button.change_color(MENU_MOUSE_POS)
            button.update(SCREEN)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BUTTON.check_input(MENU_MOUSE_POS):
                    # Start the game
                    print("Starting game...")
                    try:
                        from index import main
                        main()  # This will return when menu button is clicked
                    except Exception as e:
                        print(f"Error starting game: {e}")
                
                if THEME_BUTTON.check_input(MENU_MOUSE_POS):
                    # Cycle to next theme
                    theme_manager.next_theme()
                    print(f"Theme changed to: {theme_manager.get_current_theme_name()}")
                
                if QUIT_BUTTON.check_input(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()
        
        pygame.display.update()
        clock.tick(60)

def play():
    """Play screen (placeholder)"""
    clock = pygame.time.Clock()
    
    while True:
        PLAY_MOUSE_POS = pygame.mouse.get_pos()
        SCREEN.fill("black")
        
        PLAY_TEXT = get_font(45).render("This is the PLAY screen.", True, "White")
        PLAY_RECT = PLAY_TEXT.get_rect(center=(640, 260))
        SCREEN.blit(PLAY_TEXT, PLAY_RECT)
        
        PLAY_BACK = Button(
            image=None, 
            pos=(640, 460), 
            text_input="BACK", 
            font=get_font(75), 
            base_color="White", 
            hovering_color="Green"
        )
        
        PLAY_BACK.change_color(PLAY_MOUSE_POS)
        PLAY_BACK.update(SCREEN)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BACK.check_input(PLAY_MOUSE_POS):
                    return
        
        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()
