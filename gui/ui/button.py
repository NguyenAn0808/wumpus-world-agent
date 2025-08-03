import pygame
from gui.ui.sound import SoundManager

class Button:
    def __init__(self, x, y, width, height, label, on_click, app=None,
                 bg_color=(255, 255, 255), text_color=(255, 255, 255), hover_color=(150, 150, 150), hover_text_color=(150, 150, 150)):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.on_click = on_click
        self.font = pygame.font.SysFont("perpetua", 50, bold=True)  # Use a carved-stone feel font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hover_text_color = hover_text_color
        self.app = app
        self.hovered = False

    def draw(self, screen):
        # Determine if hovered
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)

        # Apply hover color
        color = self.hover_color if self.hovered else self.bg_color
        label_color = self.hover_text_color if self.hovered else self.text_color
        
        pygame.draw.rect(screen, color, self.rect, width=5, border_radius=15)

        text_surface = self.font.render(self.label, True, label_color)
        text_rect = text_surface.get_rect(center=self.rect.center)

        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.is_clicked(event.pos):
            self.on_click()

    def is_clicked(self, pos):
        if self.rect.collidepoint(pos):
            self.play_click_sound()
            return True
        return False

    def play_click_sound(self):
        if self.app and hasattr(self.app, 'sound'):
            self.app.sound.play_click()
