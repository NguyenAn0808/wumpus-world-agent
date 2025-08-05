import os
import pygame
import time
from abc import ABC
from gui.screens.screen import Screen  
from gui.screens.menu_screen import MenuScreen
import cv2

class LoadingScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.start_time = time.time()
        self.duration = 13.5  # seconds to show loading screen

        video_path = "gui/assets/loading.mp4" 
        if os.path.exists(video_path):
            self.video = cv2.VideoCapture(video_path)
            self.fps = self.video.get(cv2.CAP_PROP_FPS)
            self.success, self.video_image = self.video.read()

        self.last_frame_time = self.start_time
        
    def render(self):
        screen = self.app.screen

        if self.video:
            # Tính toán thời gian cho khung hình tiếp theo dựa trên FPS của video
            time_per_frame = 1 / self.fps
            if time.time() - self.last_frame_time > time_per_frame:
                self.success, self.video_image = self.video.read()
                self.last_frame_time = time.time()

            if self.success:
                frame = cv2.cvtColor(self.video_image, cv2.COLOR_BGR2RGB)
                pygame_surface = pygame.image.frombuffer(
                    frame.tobytes(), frame.shape[1::-1], "RGB"
                )
                
                infoObject = pygame.display.Info()
                screen_width = infoObject.current_w
                screen_height = infoObject.current_h - 65

                scaled_surface = pygame.transform.scale(pygame_surface, (screen_width, screen_height))
                screen.blit(scaled_surface, (0, 0))
        else:
            screen.fill((30, 30, 60))


    def handle_input(self):
        if time.time() - self.start_time > self.duration:
            if self.video:
                self.video.release()
            self.app.switch_screen(MenuScreen(self.app))
            


    def __del__(self):
        if hasattr(self, 'video') and self.video and self.video.isOpened():
            self.video.release()

    def run(self):
        clock = pygame.time.Clock()
        self.running = True

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    return

            self.handle_input()
            self.render()
            pygame.display.flip()
            clock.tick(60)

            if time.time() - self.start_time > self.duration:
                self.running = False

        if self.video:
            self.video.release()
            
        self.app.switch_screen(MenuScreen(self.app))

