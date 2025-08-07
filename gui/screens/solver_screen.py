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
        self.screen = app.screen
        
        
        # Init Pygame
        self.screen = app.screen
        pygame.display.set_caption("Solver View")
        self.clock = pygame.time.Clock()

        # Font & Icons
        self.font = pygame.font.SysFont(None, 24)
        self.log_font = pygame.font.SysFont(None, 20)
        self.cell_icons = self.load_cell_icons()

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

        # Arrow animation
        self.arrow_animation = {
            "active": False,
            "start_pos": None,
            "direction": None,
            "progress": 0.0,
            "path": [],
            "current_index": 0,
            "speed": 6.0  # cells per second
        }
        self.arrow_icon = pygame.image.load("assets/arrow.png").convert_alpha()
        self.grab_animation_timer = 0.0  # Timer for grab animation
        self.shoot_frames = self.load_agent_shoot()
        self.grab_frames = self.load_agent_grab()
        self.shoot_anim_timer = 0.0
        self.grab_anim_timer = 0.0
        self.shoot_anim_duration = 0.3  # seconds
        self.grab_anim_duration = 0.3
        self.last_action = None
        self.shot_path = None  # Path for the arrow shot
        # Logs
        # self.logs = self.generate_logs()
        self.log_scroll = 0
        
        # Agent reasoning setup
        state = world.get_state()
        start_location = state['agent_location']
        start_direction = state['agent_direction']
        world_size = state['size']

        # Wrap world into GamePlay logic
        self.agent = HybridAgent(start_location, start_direction, world_size)
        self.gameloop = GamePlay(agent=self.agent, display_callback=self.receive_game_state)

        self.gameloop.world = world
        self.gameloop.agent.world = world
        self.world_obj = world  # optional reference

        self.auto_solve_delay = 1.0  # seconds per step
        self.auto_solve_timer = 0.0
        

    def receive_game_state(self, state_dict):
        self.map_state = state_dict
        self.state = state_dict['state']
        self.agent_x = state_dict['agent_location'].x
        self.agent_y = state_dict['agent_location'].y
        self.agent_dir = state_dict['agent_direction']
        self.last_action = state_dict['last_action']
        self.shoot_path = state_dict.get('shot_path', None)

    def auto_solve_step(self):
        self.gameloop.run_single_action()
        new_state = self.gameloop.get_game_state()
        self.receive_game_state(new_state)  # Update visuals
    #    self.logs.append(self.map_state.get('message', ''))  # Display latest message

    def load_cell_icons(self):
        def load(name):
            import os
            path = os.path.join("assets", f"{name}.png")
            return pygame.image.load(path).convert_alpha()
        return {
            'P': load('pit'),
            'G': load('gold'),
            'S': load('letter-s'),
            'B': load('letter-b'),
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
    
    def load_agent_shoot(self):
        frames = []
        i = 0
        while True:
            path = f"assets/agent/shoot/{i}.png"
            try:
                frames.append(pygame.image.load(path).convert_alpha())
                i += 1
            except FileNotFoundError:
                break
        return frames
    
    def load_agent_grab(self):
        frames = []
        i = 0
        while True:
            path = f"assets/agent/grab/{i}.png"
            try:
                frames.append(pygame.image.load(path).convert_alpha())
                i += 1
            except FileNotFoundError:
                break
        return frames

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
        box_rect = pygame.Rect(700, 360, 240, 220)
        pygame.draw.rect(self.screen, (30, 30, 30), box_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), box_rect, 2)
        visible_lines = 10
        

    def get_turn_angle(self, from_dir, to_dir):
        angles = {'up': 0, 'right': -90, 'down': -180, 'left': -270}
        return (angles[to_dir] - angles[from_dir]) % 360
    
    def draw_map(self, dt):
        MAP_PREVIEW_SIZE = 562
        MAP_TOPLEFT = (20, 44)
        cell_size = MAP_PREVIEW_SIZE // self.map_state['size']

        agent_pos = self.map_state['agent_location']
        agent_dir_enum = self.map_state['agent_direction']
        direction = agent_dir_enum.name.lower() if agent_dir_enum else 'right'
        anim_dir = DIRECTION_TO_ANIMATION.get(direction, 'right')

        for row_idx, row in enumerate(self.map_state['state']):
            for col_idx, cell in enumerate(row):
                x = MAP_TOPLEFT[0] + col_idx * cell_size
                y = MAP_TOPLEFT[1] + (self.map_state['size'] - 1 - row_idx) * cell_size

                # Draw cell background
                pygame.draw.rect(self.screen, (45, 102, 91), (x, y, cell_size, cell_size))
                pygame.draw.rect(self.screen, (35, 80, 72), (x, y, cell_size, cell_size), 2)

                # Draw cell symbols
                for symbol in cell:
                    # Draw cell symbols
                    cell_content = set(cell)  
                    rect = pygame.Rect(x, y, cell_size, cell_size)

                    # --- Stench and Breeze handling ---
                    has_stench = 'S' in cell_content
                    has_breeze = 'B' in cell_content

                    if has_stench and has_breeze:
                        stench_icon = pygame.transform.scale(self.cell_icons['S'], (cell_size // 2, cell_size // 2))
                        breeze_icon = pygame.transform.scale(self.cell_icons['B'], (cell_size // 2, cell_size // 2))
                        self.screen.blit(stench_icon, rect.topleft)
                        self.screen.blit(breeze_icon, (rect.topright[0] - cell_size // 2, rect.topright[1]))  # shift left for width
                    elif has_stench:
                        stench_icon = pygame.transform.scale(self.cell_icons['S'], (cell_size // 2, cell_size // 2))
                        self.screen.blit(stench_icon, rect.topleft)
                    elif has_breeze:
                        breeze_icon = pygame.transform.scale(self.cell_icons['B'], (cell_size // 2, cell_size // 2))
                        self.screen.blit(breeze_icon, rect.topleft)

                    # --- Wumpus full cell ---
                    if 'W' in cell_content:
                        frame = pygame.transform.scale(self.wumpus_idle_frames[self.wumpus_frame_index], (cell_size, cell_size))
                        self.screen.blit(frame, rect.topleft)

                    # --- Pit (full cell icon) ---
                    if 'P' in cell_content:
                        pit_icon = pygame.transform.scale(self.cell_icons['P'], (cell_size, cell_size))
                        self.screen.blit(pit_icon, rect.topleft)

                    # --- Gold (full cell icon) ---
                    if 'G' in cell_content:
                        gold_icon = pygame.transform.scale(self.cell_icons['G'], (cell_size, cell_size))
                        self.screen.blit(gold_icon, rect.topleft)


                        

        # Draw arrow animation first so it's under the agent
        if self.arrow_animation["active"]:
            self.animate_arrow(dt, cell_size, MAP_TOPLEFT)

        # Draw agent at current position
        x = MAP_TOPLEFT[0] + agent_pos.x * cell_size
        y = MAP_TOPLEFT[1] + (self.map_state['size'] - 1 - agent_pos.y) * cell_size

        if self.shoot_anim_timer > 0:
            frame_list = self.shoot_frames
            self.shoot_anim_timer -= dt
        elif self.grab_anim_timer > 0:
            frame_list = self.grab_frames
            self.grab_anim_timer -= dt
        else:
            frame_list = self.agent_animations.get(anim_dir, [])

        if frame_list:
            frame = frame_list[self.agent_frame % len(frame_list)]
            scaled_frame = pygame.transform.scale(frame, (cell_size, cell_size))

            if self.is_turning:
                angle = self.get_turn_angle(self.prev_dir, direction)
                interpolated_angle = angle * self.turn_progress
                rotated_frame = pygame.transform.rotate(scaled_frame, -interpolated_angle)
                frame_rect = rotated_frame.get_rect(center=(x + cell_size // 2, y + cell_size // 2))
                self.screen.blit(rotated_frame, frame_rect.topleft)
            else:
                self.screen.blit(scaled_frame, (x, y))


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

    def update_animation(self, dt):
    # Get current direction
        agent_dir_enum = self.map_state['agent_direction']
        agent_dir = agent_dir_enum.name.lower() if agent_dir_enum else 'right'

        # --- Wumpus idle ---
        self.wumpus_frame_timer += dt
        if self.wumpus_frame_timer >= self.wumpus_frame_delay:
            self.wumpus_frame_timer = 0.0
            self.wumpus_frame_index = (self.wumpus_frame_index + 1) % len(self.wumpus_idle_frames)

        # --- Agent walking ---
        direction = DIRECTION_TO_ANIMATION.get(agent_dir, 'right')
        frames = self.agent_animations.get(direction, [])
        if frames:
            self.agent_frame_timer += dt
            if self.agent_frame_timer >= self.agent_frame_delay:
                self.agent_frame_timer = 0.0
                self.agent_frame = (self.agent_frame + 1) % len(frames)

        # --- Turning ---
        if not self.turning and agent_dir != self.last_agent_dir:
            transition_lookup = {
                ('left', 'right'): 'down',
                ('right', 'left'): 'up',
                ('up', 'down'): 'right',
                ('down', 'up'): 'left',
            }
            mid = transition_lookup.get((self.last_agent_dir, agent_dir))
            if mid:
                self.turning = True
                self.turn_timer = 0.0
                self.turn_mid_frame = mid
                self.next_direction = agent_dir

        if self.turning:
            self.turn_timer += dt
            if self.turn_timer >= self.turn_duration:
                self.turning = False
                self.last_agent_dir = self.next_direction

        self.last_agent_dir = agent_dir

        # --- GRAB animation trigger ---
        if self.last_action == "GRAB":
            self.grab_anim_timer = self.grab_anim_duration

        # --- SHOOT animation trigger ---
        if self.last_action == "SHOOT":
            if self.shoot_anim_timer <= 0 and not self.arrow_animation["active"]:
                # 1. First time entering SHOOT: start shooting animation
                if self.shoot_path and self.shoot_anim_timer == 0.0:
                    self.shoot_anim_timer = self.shoot_anim_duration

                # 2. When shoot animation is finished: start arrow
                elif self.shoot_anim_timer <= 0:
                    self.arrow_animation["active"] = True
                    self.arrow_animation["path"] = self.shoot_path.copy()
                    self.arrow_animation["current_index"] = 0
                    self.arrow_animation["progress"] = 0.0
                    self.arrow_animation["direction"] = agent_dir

        if self.last_action in ["SHOOT", "GRAB"] and self.shoot_anim_timer <= 0 and not self.arrow_animation["active"]:
            self.last_action = None




    def animate_arrow(self, dt, cell_size, top_left):
        anim = self.arrow_animation
        path = anim.get("path")
        if not path or anim["current_index"] >= len(path):
            anim["active"] = False
            return

        anim["progress"] += anim["speed"] * dt

        # Move to next cell if enough progress
        if anim["progress"] >= 1.0:
            anim["progress"] = 0.0
            anim["current_index"] += 1

        # Stop if finished
        if anim["current_index"] >= len(path):
            anim["active"] = False
            return

        pos = path[anim["current_index"]]
        pixel_x = top_left[0] + pos.x * cell_size
        pixel_y = top_left[1] + (self.map_state["size"] - 1 - pos.y) * cell_size

        # Rotate arrow image
        arrow_img = pygame.transform.scale(self.arrow_icon, (cell_size, cell_size))
        rotation = {
            'north': 90, 'south': -90, 'west': 180, 'east': 0
        }[self.arrow_animation["direction"]]
        rotated = pygame.transform.rotate(arrow_img, rotation)
        self.screen.blit(rotated, (pixel_x, pixel_y))




    def render_with_dt(self, dt):
        self.update_animation(dt)

        self.screen.fill((116, 141, 166))
        self.draw_map(dt)
        self.draw_log_box()
        pygame.display.flip()

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

            # Stop if game is done
            if self.map_state.get('game_over', False):
                self.running = False
                return  # or switch to menu

            # Solver step
            self.auto_solve_timer += self.clock.get_time() / 1000.0
            if self.auto_solve_timer >= self.auto_solve_delay:
                self.auto_solve_timer = 0.0
                self.auto_solve_step()
