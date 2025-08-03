import random
import pygame
from gui.screens.screen import Screen
from gui.ui.button import Button
import cv2


class InstructionScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.message = "Welcome to Wumpus World!\nFind the Gold, and return to the starting square \nto climb out safely\nChoose 1 of 4 game modes for the Agent to play:\n- Hybrid Agent Intergation\n- Random Agent Baseline\n- Advance Setting: Moving Wumpus Module\n- Player Control\nActions: Move, Shoot, Grab, Climnb\n Percepts: Stench, Breeze, Glitter, Bump, Scream\nGenerate your own map with the optional\n parameters on Overview" 
        self.font = pygame.font.SysFont("perpetua", 30)

        infoObject = pygame.display.Info()
        self.width = infoObject.current_w
        self.height = infoObject.current_h - 65

        self.button_back = Button(self.width / 2 - 80, self.height / 2 + 250, 160, 60, "Back", self.on_back, self.app)

        self.cap = cv2.VideoCapture("gui/assets/menu.mp4")
        self.title_image = pygame.image.load("gui/assets/frame.png").convert_alpha()
        
    def render(self):
        screen_width = self.app.screen.get_width()

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
        
        # Draw title
        title_font = pygame.font.SysFont("perpetua", 65, bold=True)
        title_text = title_font.render("INSTRUCTION", True, (255, 255, 255))
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

        self.button_back.draw(self.app.screen)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.button_back.is_clicked(event.pos):
                    self.on_back()

    def on_back(self):
        from gui.screens.menu_screen import MenuScreen
        self.app.switch_screen(MenuScreen(self.app))

    

    
