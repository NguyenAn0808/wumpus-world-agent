import pygame
from gui.screens.screen import Screen
from simulation import *
from simulation.game import GamePlay

DIRECTION_TO_ANIMATION = {
    'north': 'up',
    'south': 'down',
    'east': 'right',
    'west': 'left',
}


class SolverScreen(Screen):
    def __init__(self, app, mode, map_state, world : World):
        super().__init__(app)
        self.mode = mode
        self.map_state = map_state
        self.running = True
        infoObject = pygame.display.Info()
        screen_width = infoObject.current_w
        screen_height = infoObject.current_h - 65

        self.screen = pygame.display.set_mode((screen_width, screen_height))
        
        # Init Pygame
        self.screen = app.screen
        pygame.display.set_caption("Solver View")
        self.clock = pygame.time.Clock()

        # Font & Icons
        self.font = pygame.font.SysFont(None, 24)
        self.log_font = pygame.font.SysFont(None, 20)
        self.cell_icons = self.load_cell_icons()

        # Animation variables
        self.map_size = map_state['size']
        self.agent_x = map_state['agent_location'].x
        self.agent_y = map_state['agent_location'].y
        self.agent_dir = map_state['agent_direction']
        self.state = map_state['state']

        self.agent_frame = 0
        self.agent_frame_timer = 0.0
        self.agent_frame_delay = 0.2
        self.agent_animations = self.load_agent_animations()
        self.last_agent_dir = None

        # Rotation transition
        # Full turning animation logic
        self.turning = False
        self.turn_timer = 0.0
        self.turn_duration = 0.2
        self.turn_mid_frame = None
        self.next_direction = None

        self.is_turning = False
        self.turn_progress = 0.0
        self.turn_duration = 0.15
        self.prev_dir = None

        # Wumpus idle animation
        self.wumpus_idle_frames = self.load_wumpus_idle()
        self.wumpus_frame_index = 0
        self.wumpus_frame_timer = 0.0
        self.wumpus_frame_delay = 0.1

        # Logs
        # self.logs = self.generate_logs()
        self.log_scroll = 0
        
        # Agent reasoning setup

        # Wrap world into GamePlay logic
        self.gameloop = GamePlay(display_callback=self.receive_game_state)
        self.world_obj = self.gameloop.world
        self.agent = self.gameloop.agent  # Get current agent reference

        self.auto_solve_delay = 1.0  # seconds per step
        self.auto_solve_timer = 0.0
        

    def receive_game_state(self, state_dict):
        self.map_state = state_dict
        self.state = state_dict['state']
        self.agent_x = state_dict['agent_location'].x
        self.agent_y = state_dict['agent_location'].y
        self.agent_dir = state_dict['agent_direction']

    def auto_solve_step(self):
        self.gameloop.run_single_action()
    #    self.logs.append(self.map_state.get('message', ''))  # Display latest message

    def load_cell_icons(self):
        def load(name):
            import os
            path = os.path.join("assets", f"{name}.png")
            return pygame.image.load(path).convert_alpha()
        return {
            'P': load('pit'),
            'G': load('gold'),
            'S': load('stench'),
            'B': load('breeze')
        }

    def load_agent_animations(self):
        animations = {}
        for direction in ['up', 'down', 'left', 'right']:
            frames = []
            i = 0
            while True:
                path = f"assets/agent/{direction}/{i}.png"
                try:
                    frames.append(pygame.image.load(path).convert_alpha())
                    i += 1
                except FileNotFoundError:
                    break
            animations[direction] = frames
        return animations

    def load_wumpus_idle(self):
        frames = []
        i = 0
        while True:
            path = f"assets/wumpus/idle/{i}.png"
            try:
                frames.append(pygame.image.load(path).convert_alpha())
                i += 1
            except FileNotFoundError:
                break
        return frames


    def draw_log_box(self):
        box_rect = pygame.Rect(540, 360, 240, 220)
        pygame.draw.rect(self.screen, (30, 30, 30), box_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), box_rect, 2)
        visible_lines = 10
        

    def get_turn_angle(self, from_dir, to_dir):
        angles = {'up': 0, 'right': -90, 'down': -180, 'left': -270}
        return (angles[to_dir] - angles[from_dir]) % 360

    def draw_map(self, dt):
        #TODO: Visualize Reasoned Statuses
        MAP_PREVIEW_SIZE = 512
        MAP_TOPLEFT = (20, 44)
        cell_size = MAP_PREVIEW_SIZE // self.map_size

        self.agent_frame_timer += dt
        if self.agent_frame_timer >= self.agent_frame_delay:
            self.agent_frame_timer = 0.0
            raw_direction = self.agent_dir.name.lower()
            direction = DIRECTION_TO_ANIMATION.get(raw_direction)
            frame_count = len(self.agent_animations[direction])
            self.agent_frame = (self.agent_frame + 1) % frame_count

        self.wumpus_frame_timer += dt
        if self.wumpus_frame_timer >= self.wumpus_frame_delay:
            self.wumpus_frame_timer = 0.0
            self.wumpus_frame_index = (self.wumpus_frame_index + 1) % len(self.wumpus_idle_frames)

        for row_idx, row in enumerate(self.state):
            for col_idx, cell in enumerate(row):
                x = MAP_TOPLEFT[0] + col_idx * cell_size
                y = MAP_TOPLEFT[1] + (self.map_size - 1 - row_idx) * cell_size

                pygame.draw.rect(self.screen, (45, 102, 91), (x, y, cell_size, cell_size))
                pygame.draw.rect(self.screen, (35, 80, 72), (x, y, cell_size, cell_size), 2)

                for symbol in cell:
                    if symbol == 'W':
                        frame = pygame.transform.scale(self.wumpus_idle_frames[self.wumpus_frame_index], (cell_size, cell_size))
                        self.screen.blit(frame, (x, y))
                    elif symbol in self.cell_icons:
                        icon = pygame.transform.scale(self.cell_icons[symbol], (cell_size, cell_size))
                        self.screen.blit(icon, (x, y))

                if col_idx == self.agent_x and row_idx == self.agent_y:
                    direction = self.agent_dir.name.lower()
                    anim_dir = direction if direction in self.agent_animations else 'right'

                    if self.turning and self.turn_mid_frame:
                        frame = self.agent_animations[self.turn_mid_frame][0]
                    else:
                        frame = self.agent_animations[anim_dir][self.agent_frame]

                    scaled_frame = pygame.transform.scale(frame, (cell_size, cell_size))
                    self.screen.blit(scaled_frame, (x, y))
                    raw_direction = self.agent_dir.name.lower()
                    direction = raw_direction if raw_direction in self.agent_animations else 'right'
                    if direction != self.last_agent_dir:
                        self.prev_dir = self.last_agent_dir or direction
                        self.is_turning = True
                        self.turn_progress = 0.0
                    self.last_agent_dir = direction

                    if self.is_turning:
                        self.turn_progress += dt / self.turn_duration
                        if self.turn_progress >= 1.0:
                            self.turn_progress = 1.0
                            self.is_turning = False
                        angle = self.get_turn_angle(self.prev_dir, direction)
                        interpolated_angle = angle * self.turn_progress
                        frame = self.agent_animations[self.prev_dir][0]
                        frame = pygame.transform.rotate(pygame.transform.scale(frame, (cell_size, cell_size)), -interpolated_angle)
                        frame_rect = frame.get_rect(center=(x + cell_size//2, y + cell_size//2))
                        self.screen.blit(frame, frame_rect.topleft)
                    else:
                        frame = self.agent_animations[direction][self.agent_frame]
                        frame = pygame.transform.scale(frame, (cell_size, cell_size))
                        self.screen.blit(frame, (x, y))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pass
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.log_scroll = max(0, self.log_scroll - 1)
                elif event.key == pygame.K_DOWN:
                    self.log_scroll = min(len(self.logs) - 10, self.log_scroll + 1)


    def render(self):
        dt = self.clock.tick(60) / 1000.0
        self.handle_input()
        self.render_with_dt(dt)

    def render_with_dt(self, dt):
        self.screen.fill((10, 10, 10))
        self.draw_map(dt)
        self.draw_log_box()
        pygame.display.flip()
        # Handle direction change and animation
        if not self.turning and self.agent_dir.name.lower() != self.last_agent_dir:
            transition_lookup = {
                ('left', 'right'): 'down',
                ('right', 'left'): 'up',
                ('up', 'down'): 'right',
                ('down', 'up'): 'left',
            }
            old_dir = self.last_agent_dir
            new_dir = self.agent_dir.name.lower()
            mid = transition_lookup.get((old_dir, new_dir))
            if mid:
                self.turning = True
                self.turn_timer = 0.0
                self.turn_mid_frame = mid
                self.next_direction = new_dir

        if self.turning:
            self.turn_timer += dt
            if self.turn_timer >= self.turn_duration:
                self.turning = False
                self.last_agent_dir = self.next_direction

        self.auto_solve_timer += dt
        if self.auto_solve_timer >= self.auto_solve_delay and not self.map_state.get('stop_game', False):
            self.auto_solve_timer = 0.0
            self.auto_solve_step()

    def run(self):
        self.running = True
        while self.running:
            self.handle_input()
            self.render()
            pygame.display.flip()
            self.app.clock.tick(60)
            
            if not self.map_state.get('game_over', False):
                self.auto_solve_timer += self.clock.get_time() / 1000.0
                if self.auto_solve_timer >= self.auto_solve_delay:
                    self.auto_solve_timer = 0.0
                    self.auto_solve_step()
