import os
import random
import pygame
from gui.ui.button import Button
from gui.screens.self_play_screen import SelfPlayScreen
from simulation.world import World
class SelectModePopup:
    def __init__(self, app, parent_screen):
        self.app = app
        self.parent = parent_screen
        self.width = parent_screen.width 
        self.height = parent_screen.height 

        self.btn_hybrid = Button(self.width / 2 - 180, self.height / 2 - 90, 360, 60, "Hybrid mode", self.on_hybrid, self.app)
        self.btn_random = Button(self.width / 2 - 180, self.height / 2 - 15, 360, 60, "Random mode", self.on_random, self.app)
        self.btn_advanced = Button(self.width / 2 - 180, self.height / 2 + 60, 360, 60, "Advanced mode", self.on_advanced, self.app)
        self.btn_player = Button(self.width / 2 - 180, self.height / 2 + 135, 360, 60, "Player mode", self.on_player, self.app)

        original_title_image = pygame.image.load("gui/assets/frame.png").convert_alpha()
        self.title_image = pygame.transform.scale(original_title_image, (525, 315))

    def draw(self, screen):
        title_rect = self.title_image.get_rect(center= (self.width / 2, self.height / 2 + 50))
        self.app.screen.blit(self.title_image, title_rect)

        title_font = pygame.font.SysFont("perpetua", 65, bold=True)
        title_text = title_font.render("MODE", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, self.height /2 - 140))
        self.app.screen.blit(title_text, title_rect)
        
        self.btn_hybrid.draw(screen)
        self.btn_random.draw(screen)
        self.btn_advanced.draw(screen)
        self.btn_player.draw(screen)

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_hybrid.is_clicked(event.pos):
                self.on_hybrid()
            elif self.btn_random.is_clicked(event.pos):
                self.on_random()
            elif self.btn_advanced.is_clicked(event.pos):
                self.on_advanced()
            elif self.btn_player.is_clicked(event.pos):
                self.on_player()

    def on_hybrid(self):
        self.parent.popups.clear()
        from gui.screens.preview_map_screen import PreviewMapScreen
        self.app.switch_screen(PreviewMapScreen(self.app, "hybrid"))


    def on_random(self):
        self.parent.popups.clear()
        from gui.screens.preview_map_screen import PreviewMapScreen
        self.app.switch_screen(PreviewMapScreen(self.app, "random"))

    def on_advanced(self):
        self.parent.popups.clear()
        from gui.screens.preview_map_screen import PreviewMapScreen
        self.app.switch_screen(PreviewMapScreen(self.app, "advanced"))

    def on_player(self):
        self.parent.popups.clear()
        world = World()                # Random world generated
        map_state = world.get_state()           # Get the agent’s initial view/state

        # --- Step 3: Switch to SelfPlayScreen ---
        self.app.switch_screen(SelfPlayScreen(self.app, map_state, world))

        