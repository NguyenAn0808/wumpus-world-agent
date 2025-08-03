import pygame
from gui.ui.button import Button
from gui.ui.icon_button import IconButton
from gui.screens.menu_screen import MenuScreen
from gui.ui.icon_toggle import IconToggleButton

class SettingsPopup:
    def __init__(self, app, parent_screen):
        self.app = app
        self.parent = parent_screen
        self.font = pygame.font.SysFont("perpetua", 60)
        self.width = parent_screen.width 
        self.height = parent_screen.height  
        self.btn_close = Button(self.width / 2 - 80, self.height / 2 + 130, 160, 60, "Close", self.on_close, self.app,
                                bg_color=(0, 0, 0), text_color=(0, 0, 0), hover_color=(50, 50, 50), hover_text_color=(50, 50, 50))
        
        original_title_image = pygame.image.load("gui/assets/frame.png").convert_alpha()
        self.title_image = pygame.transform.scale(original_title_image, (525, 315))

        box_x, box_y = self.width / 2 - 300, self.height / 2 - 100
        box_height = 400

        # Icon toggles
        self.sound_toggle = IconToggleButton(
            x= box_x + 130, y = (box_y + box_height) / 2,
            icon_on_path="gui/assets/volume.png",
            icon_off_path="gui/assets/mute.png",
            initial_state=True,
            on_toggle=self.toggle_sound
        )

        self.music_toggle = IconToggleButton(
            x= box_x + 400, y = (box_y + box_height) / 2,
            icon_on_path="gui/assets/music-player.png",
            icon_off_path="gui/assets/music-off.png",
            initial_state=True,
            on_toggle=self.toggle_music
        )

        self.sound_enabled = True
        self.music_enabled = True

    def draw(self, screen):
        title_rect = self.title_image.get_rect(center= (self.width / 2, self.height / 2 + 50))
        self.app.screen.blit(self.title_image, title_rect)


        box_x, box_y = self.width / 2 - 250, self.height / 2 - 100
        box_width, box_height = 500, 300
        pygame.draw.rect(screen, (240, 240, 240), (box_x, box_y, box_width, box_height), border_radius=12)

        title_font = pygame.font.SysFont("perpetua", 65, bold=True)
        title_text = title_font.render("SETTING", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.width // 2, self.height /2 - 140))
        self.app.screen.blit(title_text, title_rect)

        label_y = (box_y + box_height) / 2 + 100
        sound_label = self.font.render("Sound", True, (0, 0, 0))
        music_label = self.font.render("Music", True, (0, 0, 0))

        screen.blit(sound_label, (box_x + 40, label_y))
        screen.blit(music_label, (box_x + 320, label_y))

        # Draw
        self.sound_toggle.draw(screen)
        self.music_toggle.draw(screen)

        self.btn_close.draw(screen)

    def handle_input(self, event):
        self.sound_toggle.handle_event(event)
        self.music_toggle.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            print(event.pos)
            for btn in [self.btn_close]:
                if btn.is_clicked(event.pos):
                    btn.on_click()
    
    def toggle_sound(self, enabled):
        self.app.sound.toggle_sound()

    def toggle_music(self, enabled):
        self.app.sound.toggle_music()

    def on_close(self):
        if hasattr(self.parent, "popups") and self in self.parent.popups:
            self.parent.popups.remove(self)
