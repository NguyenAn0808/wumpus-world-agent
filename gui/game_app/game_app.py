import pygame
from gui.screens.menu_screen import MenuScreen
from gui.screens.loading_screen import LoadingScreen
from gui.ui.sound import SoundManager

class GameApp:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        infoObject = pygame.display.Info()
        screen_width = infoObject.current_w
        screen_height = infoObject.current_h - 65

        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Wumpus World")
        pygame.display.set_icon(pygame.image.load("gui/assets/logo.png"))
        self.clock = pygame.time.Clock()
        self.sound = SoundManager()  
        self.sound.play_music()

        # Call Screen
        self.current_screen = LoadingScreen(self)

    def run(self):
        while True:
            self.current_screen.handle_input()
            self.current_screen.render()
            pygame.display.flip()
            self.clock.tick(60)

    def switch_screen(self, new_screen):
        self.current_screen = new_screen



