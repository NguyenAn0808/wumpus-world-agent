from gui.screens.menu_screen import MenuScreen
import pygame
import os
from gui.screens.screen import Screen
from gui.screens.solver_screen import SolverScreen
from simulation.world import World
from simulation.game import GamePlay

MAP_PREVIEW_SIZE = 484
MAP_AREA_TOPLEFT = (300, 50)

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

        # Initial parameters
        self.map_size = 8
        self.num_wumpus = 2
        self.pit_prob = 0.2

        # World instance
        self.world = World()
        self.generate_map()

        # Load icons
        self.cell_icons = self.load_cell_icons()

        # Fonts
        self.font = pygame.font.SysFont(None, 24)

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
            pit_prob=self.pit_prob
        )

    def draw_text(self, label, value, x, y):
        text = self.font.render(f"{label}: {value}", True, pygame.Color('white'))
        self.screen.blit(text, (x, y))

    def draw_button(self, label, x, y, w, h):
        pygame.draw.rect(self.screen, (100, 100, 100), (x, y, w, h))
        text = self.font.render(label, True, pygame.Color('white'))
        self.screen.blit(text, (x + 10, y + 5))
        return pygame.Rect(x, y, w, h)

    def draw_controls(self):
        x, y = 30, 50
        self.draw_text("Mode", self.mode, x, y)
        y += 40
        self.draw_text("Map Size", self.map_size, x, y)
        self.size_plus = self.draw_button("+", x + 150, y, 30, 30)
        self.size_minus = self.draw_button("-", x + 190, y, 30, 30)

        y += 40
        self.draw_text("Wumpus Count", self.num_wumpus, x, y)
        self.w_plus = self.draw_button("+", x + 150, y, 30, 30)
        self.w_minus = self.draw_button("-", x + 190, y, 30, 30)

        y += 40
        self.draw_text("Pit Probability", round(self.pit_prob, 2), x, y)
        self.p_plus = self.draw_button("+", x + 150, y, 30, 30)
        self.p_minus = self.draw_button("-", x + 190, y, 30, 30)

        y += 60
        self.gen_btn = self.draw_button("Generate Map", x, y, 200, 35)
        y += 45
        self.back_btn = self.draw_button("< Back", x, y, 90, 35)
        self.start_btn = self.draw_button("Start Game >", x + 110, y, 120, 35)

    def draw_map_preview(self):
        map_data = self.world.get_state()
        state = map_data["state"]
        agent_x = map_data["agent_location"].x
        agent_y = map_data["agent_location"].y
        agent_dir = map_data["agent_direction"]

        CELL_SIZE = MAP_PREVIEW_SIZE // self.map_size
        for row_idx, row in enumerate(state):
            for col_idx, cell in enumerate(row):
                x = MAP_AREA_TOPLEFT[0] + col_idx * CELL_SIZE
                y = MAP_AREA_TOPLEFT[1] + (self.map_size - 1 - row_idx) * CELL_SIZE

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
        self.screen.fill((30, 30, 30))
        self.draw_controls()
        self.draw_map_preview()
        pygame.display.flip()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if self.size_plus.collidepoint(pos):
                    self.map_size = min(10, self.map_size + 1)
                    self.generate_map()
                elif self.size_minus.collidepoint(pos):
                    self.map_size = max(4, self.map_size - 1)
                    self.generate_map()
                elif self.w_plus.collidepoint(pos):
                    self.num_wumpus += 1
                    self.generate_map()
                elif self.w_minus.collidepoint(pos):
                    self.num_wumpus = max(1, self.num_wumpus - 1)
                    self.generate_map()
                elif self.p_plus.collidepoint(pos):
                    self.pit_prob = min(1.0, self.pit_prob + 0.05)
                    self.generate_map()
                elif self.p_minus.collidepoint(pos):
                    self.pit_prob = max(0.0, self.pit_prob - 0.05)
                    self.generate_map()
                elif self.gen_btn.collidepoint(pos):
                    self.generate_map()
                elif self.back_btn.collidepoint(pos):
                    # TODO: implement going back
                    self.running = False
                    self.app.switch_screen(MenuScreen(self.app))
                elif self.start_btn.collidepoint(pos):
                    # TODO: implement starting game
                    self.app.switch_screen(SolverScreen(self.app, self.mode, self.world.get_state(), self.world))

    def run(self):
        while self.running:
            self.clock.tick(60)
            self.handle_input()
            self.render()
        pygame.quit()
