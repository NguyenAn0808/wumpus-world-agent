import random
import pygame
from gui.screens.screen import Screen
from gui.ui.button import Button
import cv2

DESERT_SAND = (210, 180, 140)

class CreditsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.message = "Wumpus World\nDeveloped by:\n23127102 - Le Quang Phuc\n23127148 - An Tien Nguyen An\n23127307 - Nguyen Pham Minh Thu\n23127442 - Tram Huu Nhan\n\nCSC14003 - Introduction to Artificial Intelligence\nSpecial thanks to:\nProf. Nguyen Ngoc Thao\nProf. Nguyen Tran Duy Minh" 
        self.font = pygame.font.SysFont("perpetua", 30)

        infoObject = pygame.display.Info()
        self.width = infoObject.current_w
        self.height = infoObject.current_h - 65

        self.btn_back = Button(self.width / 2 - 80, self.height / 2 + 250, 160, 60, "Back", self.on_back, self.app)        

        self.cap = cv2.VideoCapture("gui/assets/menu.mp4")
        self.title_image = pygame.image.load("gui/assets/frame.png").convert_alpha()

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
        
        title_rect = self.title_image.get_rect(center= (self.width / 2, self.height / 2 + 50))
        self.app.screen.blit(self.title_image, title_rect)

        screen_width = self.app.screen.get_width()
        
        # Draw title
        title_font = pygame.font.SysFont("perpetua", 65, bold=True)
        title_text = title_font.render("CREDIT", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(screen_width // 2, 90))
        self.app.screen.blit(title_text, title_rect)

        text_x = self.width / 2
        text_y = self.height / 4 - 30
        line_spacing = 30
       
        # Display message
        lines = self.message.split('\n')
        for i, line in enumerate(lines):
            rendered_line = self.font.render(line, True, (255, 255, 255))
            text_rect = rendered_line.get_rect(centerx = text_x)
            text_rect.y = text_y + (i * line_spacing)
            self.app.screen.blit(rendered_line, text_rect)

        self.btn_back.draw(self.app.screen)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_back.is_clicked(event.pos):
                    self.on_back()

    def on_back(self):
        from gui.screens.menu_screen import MenuScreen
        self.app.switch_screen(MenuScreen(self.app))

    def run(self):
        self.running = True
        while self.running:
            self.handle_input()
            self.render()
            pygame.display.flip()
            self.app.clock.tick(60)
    


