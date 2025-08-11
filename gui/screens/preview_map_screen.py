import pygame
import os
import cv2

from gui.screens.menu_screen import MenuScreen
from gui.screens.screen import Screen
from gui.screens.solver_screen import SolverScreen
from simulation.world import World
from simulation.game import GamePlay
from gui.ui.button import Button

class PreviewMapScreen(Screen):
    def __init__(self, app, mode):
        super().__init__(app)
        self.mode = mode
        self.screen = app.screen
        self.width, self.height = self.screen.get_size()
        pygame.display.set_icon(pygame.image.load("gui/assets/logo.png"))
        pygame.display.set_caption("Preview Map")
        self.clock = pygame.time.Clock()
        self.running = True

        self.MAP_PREVIEW_SIZE = 600
        self.MAP_AREA_TOPLEFT = (self.width / 2 - 480, self.height / 2 - 280)

        # Initial parameters
        self.map_size = 8
        self.num_wumpus = 2
        self.pit_prob = 0.2

        # World instance
        self.world = World()
        self.generate_map()

        self.buttons = []
        self.setup_ui() 

        # Load icons
        self.cell_icons = self.load_cell_icons()

        # Fonts
        self.font = pygame.font.SysFont("perpetua", 28)

        self.cap = cv2.VideoCapture("gui/assets/menu.mp4")

        original_title_image = pygame.image.load("gui/assets/frame.png").convert_alpha()
        self.title_image = pygame.transform.scale(original_title_image, (1000, 650))

    def load_cell_icons(self):
        def load(name):
            path = os.path.join("assets", f"{name}.png")
            return pygame.image.load(path).convert_alpha()

        return {
            'P': load('pit'),
            'W': load('wumpus/idle/0'),
            'G': load('gold'),
            'S': load('stench'),
            'B': load('breeze'),
            'A_up': load('agent/up/0'),
            'A_down': load('agent/down/0'),
            'A_left': load('agent/left/0'),
            'A_right': load('agent/right/0')
        }

    def generate_map(self):
        self.world = World(
            size=self.map_size,
            number_of_wumpus=self.num_wumpus,
            pit_prob=self.pit_prob,
            debug_map=False
        )

    def setup_ui(self): 
        self.buttons = []
        x, y = self.width / 2 + 150, self.height / 2 - 130
        y_offset = 60  # Khoảng cách giữa các dòng
        
        # Colors and Font for buttons - bạn có thể tùy chỉnh ở đây
        btn_bg = (255, 255, 255)
        btn_hover = (150, 150, 150)
        btn_text = pygame.Color('white')
        btn_font_small = pygame.font.SysFont("perpetua", 30, bold=True)
        btn_font_large = pygame.font.SysFont("perpetua", 30, bold=True)
        
        # --- Map Size Controls ---
        y += y_offset # Di chuyển xuống dòng Map Size
        
        # Định nghĩa hành động cho nút bằng lambda
        size_plus_action = lambda: self.set_map_size(self.map_size + 1)
        self.buttons.append(Button(x + 210, y, 40, 40, "+", size_plus_action, self.app, bg_color=btn_bg, hover_color=btn_hover, text_color=btn_text))
        # Gán font nhỏ hơn cho các nút +/-
        self.buttons[-1].font = btn_font_small

        size_minus_action = lambda: self.set_map_size(self.map_size - 1)
        self.buttons.append(Button(x + 270, y, 40, 40, "-", size_minus_action, self.app, bg_color=btn_bg, hover_color=btn_hover, text_color=btn_text))
        self.buttons[-1].font = btn_font_small
        
        # --- Wumpus Count Controls ---
        y += y_offset
        w_plus_action = lambda: self.set_wumpus_count(self.num_wumpus + 1)
        self.buttons.append(Button(x + 210, y, 40, 40, "+", w_plus_action, self.app, bg_color=btn_bg, hover_color=btn_hover, text_color=btn_text))
        self.buttons[-1].font = btn_font_small

        w_minus_action = lambda: self.set_wumpus_count(self.num_wumpus - 1)
        self.buttons.append(Button(x + 270, y, 40, 40, "-", w_minus_action, self.app, bg_color=btn_bg, hover_color=btn_hover, text_color=btn_text))
        self.buttons[-1].font = btn_font_small
        
        # --- Pit Probability Controls ---
        y += y_offset
        p_plus_action = lambda: self.set_pit_prob(self.pit_prob + 0.05)
        self.buttons.append(Button(x + 210, y, 40, 40, "+", p_plus_action, self.app, bg_color=btn_bg, hover_color=btn_hover, text_color=btn_text))
        self.buttons[-1].font = btn_font_small

        p_minus_action = lambda: self.set_pit_prob(self.pit_prob - 0.05)
        self.buttons.append(Button(x + 270, y, 40, 40, "-", p_minus_action, self.app, bg_color=btn_bg, hover_color=btn_hover, text_color=btn_text))
        self.buttons[-1].font = btn_font_small
        
        # --- Main Action Buttons ---
        y += 60
        # Hành động generate_map đã là một phương thức, không cần lambda
        gen_btn = Button(x + 60, y, 210, 50, "Generate Map", self.generate_map, self.app, bg_color=btn_bg, hover_color=btn_hover, text_color=btn_text)
        gen_btn.font = btn_font_large
        self.buttons.append(gen_btn)

        y += 70
        back_action = lambda: self.app.switch_screen(MenuScreen(self.app))
        back_btn = Button(x + 40, y, 100, 45, "Back", back_action, self.app, bg_color=btn_bg, hover_color=btn_hover, text_color=btn_text)
        back_btn.font = btn_font_large
        self.buttons.append(back_btn)

        start_action = lambda: self.app.switch_screen(SolverScreen(self.app, self.mode, self.world.get_state(), self.world))
        start_btn = Button(x + 150, y, 160, 45, "Start Game", start_action, self.app, bg_color=btn_bg, hover_color=btn_hover, text_color=btn_text)
        start_btn.font = btn_font_large
        self.buttons.append(start_btn)

    def set_map_size(self, new_size):
        self.map_size = max(4, min(10, new_size))
        self.generate_map()

    def set_wumpus_count(self, new_count):
        self.num_wumpus = max(1, new_count)
        self.generate_map()
        
    def set_pit_prob(self, new_prob):
        self.pit_prob = max(0.0, min(1.0, round(new_prob, 2)))
        self.generate_map()

    def draw_text(self, label, value, x, y):
        text = self.font.render(f"{label}: {value}", True, pygame.Color('white'))
        self.screen.blit(text, (x, y))

    def draw_button(self, label, x, y, w, h):
        pygame.draw.rect(self.screen, (100, 100, 100), (x, y, w, h))
        text = self.font.render(label, True, pygame.Color('white'))
        self.screen.blit(text, (x + 10, y + 5))
        return pygame.Rect(x, y, w, h)

    def draw_controls(self):
        x, y = self.width / 2 + 150, self.height / 2 - 130
        self.draw_text("Mode", self.mode, x, y)
        y += 60
        self.draw_text("Map Size", self.map_size, x, y)
        y += 60
        self.draw_text("Wumpus Count", self.num_wumpus, x, y)
        y += 60
        self.draw_text("Pit Probability", round(self.pit_prob, 2), x, y)
        
        # Vẽ tất cả các nút đã được tạo
        for button in self.buttons:
            button.draw(self.screen)

    def draw_map_preview(self):
        map_data = self.world.get_state()
        state = map_data["state"]
        agent_x = map_data["agent_location"].x
        agent_y = map_data["agent_location"].y
        agent_dir = map_data["agent_direction"]

        CELL_SIZE = self.MAP_PREVIEW_SIZE // self.map_size
        for row_idx, row in enumerate(state):
            for col_idx, cell in enumerate(row):
                x = self.MAP_AREA_TOPLEFT[0] + col_idx * CELL_SIZE
                y = self.MAP_AREA_TOPLEFT[1] + (self.map_size - 1 - row_idx) * CELL_SIZE

                # Draw cell background
                bg_color = (45, 102, 91)     # The green from the image
                border_color = (35, 80, 72)  # Slightly darker green

                pygame.draw.rect(self.screen, bg_color, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(self.screen, border_color, (x, y, CELL_SIZE, CELL_SIZE), 2)

                for symbol in cell:
                    if symbol in self.cell_icons:
                        icon = pygame.transform.scale(self.cell_icons[symbol], (CELL_SIZE, CELL_SIZE))
                        self.screen.blit(icon, (x, y))

                if col_idx == agent_x and row_idx == agent_y:
                    arrow_str = agent_dir.name.lower()  # 'UP' → 'up'
                    arrow_icon = pygame.transform.scale(
                        self.cell_icons.get(arrow_str, self.cell_icons['A_right']),
                        (CELL_SIZE, CELL_SIZE)
                    )
                    self.screen.blit(arrow_icon, (x, y))

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


        title_rect = self.title_image.get_rect(center= (self.width / 2, self.height / 2 + 20))
        self.app.screen.blit(self.title_image, title_rect)

        title_font = pygame.font.SysFont("perpetua", 65, bold=True)
        title_text = title_font.render("PREVIEW", True, (255, 255, 255))
        title_rect = title_text.get_rect(center= (self.width / 2, 70))
        
        self.app.screen.blit(title_text, title_rect)


        self.draw_controls()
        self.draw_map_preview()
        pygame.display.flip()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Đưa sự kiện cho mỗi nút để nó tự quyết định có phản ứng hay không
            for button in self.buttons:
                button.handle_event(event)

    def run(self):
        while self.running:
            self.clock.tick(60)
            self.handle_input()
            self.render()
        pygame.quit()
