import pygame
from gui.screens.screen import Screen
from gui.ui.button import Button
from gui.ui.icon_button import IconButton
import cv2
# from ui.sprites import CarSprite

class MenuScreen(Screen):
    def __init__(self, app):
        super().__init__(app)

        infoObject = pygame.display.Info()
        self.width = infoObject.current_w
        self.height = infoObject.current_h - 65

        # Menu display
        self.buttons = [
            Button(self.width / 2 - 200, self.height / 2 - 100, 400, 100, "PLAY", self.on_play, self.app),
            Button(self.width / 2 - 200, self.height / 2 + 30, 400, 100, "INSTRUCTION", self.on_instructions, self.app),
            Button(self.width / 2 - 200, self.height / 2 + 160, 400, 100, "CREDIT", self.on_credits, self.app),
            Button(self.width / 2 - 200, self.height / 2 + 290, 400, 100, "QUIT", self.on_quit, self.app),
            IconButton(self.width - 60, 10, "gui/assets/settings.png", self.on_settings, 64, self.app)
        ]
        
        self.cap = cv2.VideoCapture("gui/assets/menu.mp4")

        self.title_image = pygame.image.load("gui/assets/among_us.png").convert_alpha()
        self.popups = []

    def render(self):
        # Load video
        if self.cap:
            ret, frame = self.cap.read()

            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
 
            if ret:
                screen_size = self.app.screen.get_size()
                frame = cv2.resize(frame, (screen_size[0], screen_size[1]))
  
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                video_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

                self.app.screen.blit(video_surface, (0, 0))
        else:
            self.app.screen.fill((0, 0, 0))

        title_rect = self.title_image.get_rect(center=(self.width / 2, self.height / 4 - 100))
        self.app.screen.blit(self.title_image, title_rect)
        
        for button in self.buttons:
            button.draw(self.app.screen)
        for popup in self.popups:
            popup.draw(self.app.screen)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Let popups handle input first
                if self.popups:
                    self.popups[-1].handle_input(event)
                else:
                    for button in self.buttons:
                        if button.is_clicked(event.pos):
                            button.on_click()

    def on_play(self):
        from gui.popups.select_mode_popup import SelectModePopup
        self.popups.append(SelectModePopup(self.app, self))

    def on_settings(self):
        from gui.popups.setting_popup import SettingsPopup
        self.popups.append(SettingsPopup(self.app, self))

    def on_instructions(self):
        from gui.screens.instruction_screen import InstructionScreen
        self.app.switch_screen(InstructionScreen(self.app))

    def on_credits(self):
        from gui.screens.credit_screen import CreditsScreen
        self.app.switch_screen(CreditsScreen(self.app))

    def on_quit(self):
        pygame.quit()
        exit()
