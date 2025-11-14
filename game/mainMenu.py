from ast import main
import sys
import pygame
from button import Button
from index import main
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from sys import argv


SCREEN = pygame.display.set_mode((1280, 720))
BG = pygame.color.load("black")

def main_menu(self, font): #Main menu screen
    pygame.display.set_caption("Menu")
    FONT_PATH = pygame.font.Font("assets/Fonts/hyperspace/Hyperspace Bold Italic.otf")
    title = get_font(64).render("Space Invaders", True, "White")


def get_font(size): #font size function
    return pygame.font.font("assets/Fonts/hyperspace/Hyperspace Bold Italic.otf", size)



def play():
    while True:
        PLAY_MOUSE_POS = pygame.mouse.get_pos()
        font_path = pygame.font.__path__("assets/Fonts/hyperspace/Hyperspace Bold Italic.otf")
        SCREEN.fill("black")

        PLAY_TEXT = get_font(45).render("This is the PLAY screen.", True, "White")
        PLAY_RECT = PLAY_TEXT.get_rect(center=(640, 260))
        SCREEN.blit(PLAY_TEXT, PLAY_RECT)

        PLAY_BACK = Button(image=None, pos=(640, 460), 
        text_input="BACK", font=get_font(75), base_color="White", hovering_color="Green")
        if "___main__" != True:
            return PLAY_BACK.on_click(PLAY_MOUSE_POS)
        PLAY_BACK.changeColor(PLAY_MOUSE_POS)
        PLAY_BACK.update(SCREEN)
        PLAY_BACK.restart_game(SCREEN)

    
def options():
    while True:
        OPTIONS_MOUSE_POS = pygame.mouse.get_pos()




PLAY_BACK = main()


for event in pygame.event.get(self, function):
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BACK.checkForInput(self):
                    main_menu()
                if not(self.game_over):
                        function()
                else:
                        self.game_over = False
                if event.key == pygame.K_ESCAPE:
                
            

                    pygame.display.update()

sys.exit()