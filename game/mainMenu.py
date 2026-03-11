import asyncio  # Required for Pygbag web deployment
import sys
import pygame
import os
from button import Button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_BACKGROUND_THEME, resource_path

# Initialize pygame
pygame.init()

script_dir = os.path.dirname(os.path.abspath(__file__))

# Screen setup - use get_surface() at runtime so we draw to the active display
# (main.py may recreate the display; drawing to a stale SCREEN causes blank screen)
def _get_screen():
    surf = pygame.display.get_surface()
    if surf is None:
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Cowboys🚀 - Main Menu")
    return pygame.display.get_surface()


# Theme management
class ThemeManager:
    def __init__(self):
        self.themes = []
        self.current_theme_index = 0
        self.load_themes()
    
    def load_themes(self):
        """Load all available background themes"""
        # Load default purple nebula background from the game directory.
        nebula_bg_path = DEFAULT_BACKGROUND_THEME
        if os.path.exists(nebula_bg_path):
            try:
                nebula_bg_img = pygame.image.load(nebula_bg_path).convert()
                nebula_bg = pygame.transform.scale(nebula_bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.themes.append(("Purple Nebula", nebula_bg))
            except pygame.error:
                print(f"Warning: Could not load {nebula_bg_path}")
        
        # Flat black background
        black_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        black_bg.fill((0, 0, 0))
        self.themes.append(("Black", black_bg))
        
        # Load main menu background if it exists
        menu_bg_path = resource_path("assets", "main_menu_background.png")
        if os.path.exists(menu_bg_path):
            try:
                menu_bg_img = pygame.image.load(menu_bg_path).convert()
                menu_bg = pygame.transform.scale(menu_bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.themes.append(("Menu Background", menu_bg))
            except pygame.error:
                print(f"Warning: Could not load {menu_bg_path}")
    
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
    font_path = resource_path("assets", "Fonts", "hyperspace", "Hyperspace Bold Italic.otf")
    try:
        return pygame.font.Font(font_path, size)
    except:
        return pygame.font.Font(None, size)

async def main_menu():
    """Main menu screen (async for Pygbag)"""
    clock = pygame.time.Clock()
    
    while True:
        screen = _get_screen()
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        
        # Draw background using theme manager
        current_bg = theme_manager.get_current_background()
        screen.blit(current_bg, (0, 0))
        
        # Title
        MENU_TEXT = get_font(100).render("SPACE COWBOYS🚀", True, "#b68f40")
        MENU_RECT = MENU_TEXT.get_rect(center=(640, 100))
        screen.blit(MENU_TEXT, MENU_RECT)
        
        # Current theme display
        theme_text = get_font(30).render(f"Theme: {theme_manager.get_current_theme_name()}", True, "White")
        theme_text_rect = theme_text.get_rect(center=(640, 180))
        screen.blit(theme_text, theme_text_rect)
        
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
            button.update(screen)
        
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
                        from main import main
                        await main()  # Await async main function
                        # Ensures display is still active after game returns
                        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                        pygame.display.set_caption("Space Cowboys🚀 - Main Menu")
                    except Exception as e:
                        print(f"Error starting game: {e}")
                        import traceback
                        traceback.print_exc()

                
                if THEME_BUTTON.check_input(MENU_MOUSE_POS):
                    # Cycle to next theme
                    theme_manager.next_theme()
                    print(f"Theme changed to: {theme_manager.get_current_theme_name()}")
                
                if QUIT_BUTTON.check_input(MENU_MOUSE_POS):
                    pygame.quit()
                    sys.exit()
        
        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(0)  # Yield control to browser (required for Pygbag)

def play():
    """Play screen (placeholder)"""
    clock = pygame.time.Clock()
    
    while True:
        screen = _get_screen()
        PLAY_MOUSE_POS = pygame.mouse.get_pos()
        screen.fill("black")
        
        PLAY_TEXT = get_font(45).render("This is the PLAY screen.", True, "White")
        PLAY_RECT = PLAY_TEXT.get_rect(center=(640, 260))
        screen.blit(PLAY_TEXT, PLAY_RECT)
        
        PLAY_BACK = Button(
            image=None, 
            pos=(640, 460), 
            text_input="BACK", 
            font=get_font(75), 
            base_color="White", 
            hovering_color="Green"
        )
        
        PLAY_BACK.change_color(PLAY_MOUSE_POS)
        PLAY_BACK.update(screen)
        
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
    asyncio.run(main_menu())
