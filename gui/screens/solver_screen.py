import pygame
import os
import cv2

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
        self.width, self.height = self.screen.get_size()
        
        # Init Pygame
        self.screen = app.screen
        pygame.display.set_caption("Solver View")
        self.clock = pygame.time.Clock()

        # Font & Icons
        self.font = pygame.font.SysFont("perpetua", 24)
        self.log_font = pygame.font.SysFont("perpetua", 20)
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
        if(mode == 'hybrid' or mode == 'random'):
            self.wumpus_idle_frames = self.load_wumpus_idle()
        else:
            self.wumpus_idle_frames = self.load_wumpus_walking()

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
        if self.mode == "hybrid":
            self.agent = HybridAgent(start_location, start_direction, world_size)
        elif self.mode == "random":
            self.agent = RandomAgent(start_location, start_direction, world_size)
        elif self.mode == "advanced":  # advanced mode
            self.agent = AdvancedAgent(start_location, start_direction, world_size)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
        
        self.gameloop = GamePlay(agent=self.agent, display_callback=self.receive_game_state)

        self.gameloop.world = world
        self.gameloop.agent.world = world
        self.world_obj = world  # optional reference

        self.auto_solve_delay = 1.0  # seconds per step
        self.auto_solve_timer = 0.0

        self.cap = cv2.VideoCapture("gui/assets/menu.mp4")

        original_title_image = pygame.image.load("gui/assets/frame.png").convert_alpha()
        self.title_image = pygame.transform.scale(original_title_image, (1350, 700))

        self.panel_rect = pygame.Rect(self.width / 2 + 230, self.height / 2 - 80, 400, 400) 
        
        self.score_rect = pygame.Rect(self.width / 2 + 230, self.height / 2 - 280, 400, 180) 
        
        self.ui_font_title = pygame.font.SysFont("perpetua", 24, bold=True)
        self.ui_font_log = pygame.font.SysFont("perpetua", 20)
        self.show_map = False
        self.known_visited_cells = set() 

        self.action_log = ["Game Started..."]    
        self.log_scroll_y = 0                     
        self.log_line_height = 20                  
        self.log_surface_needs_update = True       
        self.log_full_surface = None               
        self.auto_scroll_to_bottom = True
        
    def add_to_log(self, message):
        self.action_log.append(message)
        self.log_surface_needs_update = True
        self.auto_scroll_to_bottom = True

    def receive_game_state(self, state_dict):
        self.map_state = state_dict
        self.state = state_dict['state']
        self.agent_x = state_dict['agent_location'].x
        self.agent_y = state_dict['agent_location'].y
        self.agent_dir = state_dict['agent_direction']

        self.last_action = state_dict['last_action']
        
        if self.last_action:
            log_message = f"Action: {self.last_action}"
            
            if self.last_action == "TURN_LEFT":
                log_message = "Turn left"
            elif self.last_action == "TURN_RIGHT":
                log_message = "Turn right"
            elif self.last_action == "MOVE_FORWARD":
                new_pos = state_dict['agent_location']
                new_dir = state_dict['agent_direction'].name.capitalize()
                log_message = f"Move to ({new_pos.x}, {new_pos.y})"
            elif self.last_action == "SHOOT":
                log_message = "You shoot an arrow"
                if "SCREAM" in state_dict.get("percepts", []):
                    self.add_to_log("SCREAM!")
            elif self.last_action == "GRAB":
                log_message = " Grab gold!"
            elif self.last_action == "CLIMB_OUT":
                log_message = " Climb out!"

            self.add_to_log(log_message)

        self.shoot_path = state_dict.get('shot_path', None)
        self.known_visited_cells = state_dict.get('known_visited_cells', set())

    def auto_solve_step(self):
        self.gameloop.run_single_action()
        new_state = self.gameloop.get_game_state()
        self.receive_game_state(new_state)  # Update visuals

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

    def load_wumpus_walking(self):
        frames = []
        i = 0
        while True:
            path = f"assets/wumpus/walking/{i}.png"
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
    
    def get_turn_angle(self, from_dir, to_dir):
        angles = {'up': 0, 'right': -90, 'down': -180, 'left': -270}
        return (angles[to_dir] - angles[from_dir]) % 360
    
    def draw_map(self, dt):
        MAP_PREVIEW_SIZE = 600
        MAP_TOPLEFT = (self.width / 2 - 390, self.height / 2 - 280)
        cell_size = MAP_PREVIEW_SIZE // self.map_state['size']

        agent_pos = self.map_state['agent_location']
        agent_dir_enum = self.map_state['agent_direction']
        direction = agent_dir_enum.name.lower() if agent_dir_enum else 'right'
        anim_dir = DIRECTION_TO_ANIMATION.get(direction, 'right')
        
        for row_idx, row in enumerate(self.map_state['state']):
            for col_idx, cell in enumerate(row):
                x = MAP_TOPLEFT[0] + col_idx * cell_size
                y = MAP_TOPLEFT[1] + (self.map_state['size'] - 1 - row_idx) * cell_size
                cell_coords = (col_idx, row_idx)
                visited_cells = {(p.x, p.y) for p in self.gameloop.agent.visited_cells}
                
                # Draw cell background
                pygame.draw.rect(self.screen, (45, 102, 91), (x, y, cell_size, cell_size))
                pygame.draw.rect(self.screen, (35, 80, 72), (x, y, cell_size, cell_size), 2)

                if not self.show_map and cell_coords not in visited_cells:
                    rect = pygame.Rect(x, y, cell_size, cell_size)
                    fog_color = (20, 20, 30, 200) 
                    fog_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
                    fog_surface.fill(fog_color)
                    self.screen.blit(fog_surface, rect.topleft)

                    continue
            
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

            overlay_x = self.width / 2 - 600
            overlay_y = self.height / 2 - 230
            overlay_width = 150  # total width for 3 squares
            overlay_height = 50  # height of each square

            overlay_rect = pygame.Rect(overlay_x, overlay_y, overlay_width, overlay_height)
            pygame.draw.rect(self.screen, (255, 255, 255), overlay_rect)

            square_width = overlay_width // 3

            # Fetch symbols at agent's current cell
            agent_pos = self.map_state['agent_location']
            cell_symbols = set(self.map_state['state'][agent_pos.y][agent_pos.x])

            # Define percepts in order
            icons = [('B', pygame.image.load(os.path.join("assets", "breeze.png")).convert_alpha()), ('S', pygame.image.load(os.path.join("assets", "stench.png")).convert_alpha()), ('G', pygame.image.load(os.path.join("assets", "glitter.png")).convert_alpha())]

            for i, (symbol, icon) in enumerate(icons):
                square_rect = pygame.Rect(overlay_x + i * square_width, overlay_y, square_width, overlay_height)
                pygame.draw.rect(self.screen, (30, 30, 30), square_rect, 1)  # border for each square

                if symbol in cell_symbols and icon:
                    scaled_icon = pygame.transform.scale(icon, (square_width, overlay_height))
                    self.screen.blit(scaled_icon, square_rect.topleft)

                title_font = pygame.font.SysFont("perpetua", 35, bold=True)
        
        # Draw Pannel
        border_color = (255, 255, 255)  
        border_thickness = 3         
        border_radius_val = 10       

        # Log box
        pygame.draw.rect(self.screen, border_color, self.panel_rect, width=border_thickness, border_radius=border_radius_val)

        # Score box
        pygame.draw.rect(self.screen, border_color, self.score_rect, width=border_thickness, border_radius=border_radius_val)

        info_title = title_font.render("Info", True, (255, 255, 255))
        info_rect = info_title.get_rect(topleft= (self.width / 2 + 400, self.height / 2 - 280))
        self.screen.blit(info_title, info_rect)

        font = pygame.font.SysFont("perpetua", 26, bold=True)
        title_text = font.render("Score: ", True, (255, 255, 255))
        title_rect = title_text.get_rect(topleft= (self.width / 2 + 300, self.height /2 - 240))
        self.app.screen.blit(title_text, title_rect)

        title_text = font.render("Arrow: ", True, (255, 255, 255))
        title_rect = title_text.get_rect(topleft= (self.width / 2 + 300, self.height /2 - 195))
        self.app.screen.blit(title_text, title_rect)

        title_text = font.render("Gold: ", True, (255, 255, 255))
        title_rect = title_text.get_rect(topleft= (self.width / 2 + 300, self.height /2 - 150))
        self.app.screen.blit(title_text, title_rect)

        value_surf = self.ui_font_title.render(str(self.agent.score), True, (255, 255, 255)) 
        value_rect = value_surf.get_rect(topleft= (self.width / 2 + 380, self.height /2 - 237))
        self.screen.blit(value_surf, value_rect)

        if self.agent.has_arrow:
            text = "Yes"
        else:
            text = "No"
        value_surf = self.ui_font_title.render(text, True, (255, 255, 255)) 
        value_rect = value_surf.get_rect(topleft= (self.width / 2 + 390, self.height /2 - 192))
        self.screen.blit(value_surf, value_rect)
        
        if self.agent.has_gold:
            text = "Yes"
        else:
            text = "No"
        value_surf = self.ui_font_title.render(text, True, (255, 255, 255)) 
        value_rect = value_surf.get_rect(topleft= (self.width / 2 + 380, self.height /2 - 147))
        self.screen.blit(value_surf, value_rect)

        icon_temp = pygame.image.load(os.path.join("assets", "score.png")).convert_alpha()
        icon = pygame.transform.scale(icon_temp, (40, 40))
        self.screen.blit(icon, (self.width / 2 + 245, self.height /2 - 245))

        icon_temp = pygame.image.load(os.path.join("assets", "arrow.png")).convert_alpha()
        icon = pygame.transform.scale(icon_temp, (50, 50))
        self.screen.blit(icon, (self.width / 2 + 235, self.height /2 - 195))

        icon_temp = pygame.image.load(os.path.join("assets", "gold.png")).convert_alpha()
        icon = pygame.transform.scale(icon_temp, (50, 50))
        self.screen.blit(icon, (self.width / 2 + 240, self.height /2 - 170))

        # --- Phần Action Log ---
        log_title = title_font.render("Action Log", True, (255, 255, 255))
        log_rect = log_title.get_rect(topleft= (self.width / 2 + 350, self.height / 2 - 75))
        self.screen.blit(log_title, log_rect)

        self.checkbox_rect = pygame.Rect(self.width // 2 - 630, self.height // 2 + 200, 20, 20)


        pygame.draw.rect(self.screen, (255, 255, 255), self.checkbox_rect, 2)

        if self.show_map:
            pygame.draw.rect(self.screen, (255, 255, 255), self.checkbox_rect)

        label = self.ui_font_title.render("Remove Walls", True, (255, 255, 255))
        self.screen.blit(label, (self.checkbox_rect.right + 10, self.checkbox_rect.top - 2))

        log_view_rect = pygame.Rect(self.width / 2 + 240, self.height / 2 - 35, 400, 400 - 55)

        # 2. Tạo/Cập nhật Surface chứa toàn bộ log nếu cần
        if self.log_surface_needs_update and self.action_log:
            full_height = len(self.action_log) * self.log_line_height
            # -20 cho lề phải để thanh cuộn không đè lên chữ
            self.log_full_surface = pygame.Surface((log_view_rect.width - 20, full_height))
            #self.log_full_surface.fill((30, 69, 62)) # Tô màu nền cho log để dễ đọc hơn

            for i, entry in enumerate(self.action_log):
                log_text = self.ui_font_log.render(f"{entry}", True, (255, 255, 255))
                self.log_full_surface.blit(log_text, (20, i * self.log_line_height))
            
            self.log_surface_needs_update = False

        # 3. Vẽ phần log có thể thấy được lên màn hình
        if self.log_full_surface:
            # Tính toán giá trị cuộn tối đa
            max_scroll_y = self.log_full_surface.get_height() - log_view_rect.height
            if max_scroll_y < 0:
                max_scroll_y = 0

            if self.auto_scroll_to_bottom:
                self.log_scroll_y = max_scroll_y
            
            self.log_scroll_y = max(0, min(self.log_scroll_y, max_scroll_y))
            
            source_rect = pygame.Rect(0, self.log_scroll_y, log_view_rect.width, log_view_rect.height)
            dest_pos = (log_view_rect.left + 5, log_view_rect.top) # +5 để có lề trái
            
            self.screen.blit(self.log_full_surface, dest_pos, source_rect)

            # 4. Vẽ thanh cuộn (Scrollbar)
            if max_scroll_y > 0:
                scrollbar_track_rect = pygame.Rect(
                    log_view_rect.right - 20, 
                    log_view_rect.top, 
                    15, 
                    log_view_rect.height
                )
                pygame.draw.rect(self.screen, (255, 255, 255), scrollbar_track_rect)

                handle_height = max(20, log_view_rect.height * (log_view_rect.height / self.log_full_surface.get_height()))
                scroll_percentage = self.log_scroll_y / max_scroll_y
                handle_y = scrollbar_track_rect.top + (scroll_percentage * (scrollbar_track_rect.height - handle_height))
                
                scrollbar_handle_rect = pygame.Rect(scrollbar_track_rect.left, handle_y, 15, handle_height)
                pygame.draw.rect(self.screen, (180, 180, 180), scrollbar_handle_rect)

        # --- KẾT THÚC PHẦN SỬA ĐỔI ---

        # Phần vẽ checkbox giữ nguyên
        self.checkbox_rect = pygame.Rect(self.width // 2 - 630, self.height // 2 + 200, 20, 20)


    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.checkbox_rect.collidepoint(event.pos):
                    self.show_map = not self.show_map

                if self.panel_rect.collidepoint(event.pos):
                    if event.button == 4: # Scroll Up
                        self.log_scroll_y = max(0, self.log_scroll_y - self.log_line_height * 3)
                        self.auto_scroll_to_bottom = False # Người dùng đã tự cuộn, tắt tự động
                    elif event.button == 5: # Scroll Down
                        self.log_scroll_y += self.log_line_height * 3
                        if self.log_full_surface:
                            max_scroll = self.log_full_surface.get_height() - self.panel_rect.height
                            if self.log_scroll_y >= max_scroll - self.log_line_height:
                                self.auto_scroll_to_bottom = True


    def render(self):
        dt = self.clock.tick(60) / 1000.0
        self.handle_input()
        self.render_with_dt(dt)

        self.auto_solve_timer += dt
        if self.auto_solve_timer >= self.auto_solve_delay and not self.map_state.get('stop_game', False):
            self.auto_solve_timer = 0.0
            self.auto_solve_step()
            
    # def update_animation(self, dt):
    # # Get current direction
    #     agent_dir_enum = self.map_state['agent_direction']
    #     agent_dir = agent_dir_enum.name.lower() if agent_dir_enum else 'right'

    #     # --- Wumpus idle ---
    #     self.wumpus_frame_timer += dt
    #     if self.wumpus_frame_timer >= self.wumpus_frame_delay:
    #         self.wumpus_frame_timer = 0.0
    #         self.wumpus_frame_index = (self.wumpus_frame_index + 1) % len(self.wumpus_idle_frames)

    #     # --- Agent walking ---
    #     direction = DIRECTION_TO_ANIMATION.get(agent_dir, 'right')
    #     frames = self.agent_animations.get(direction, [])
    #     if frames:
    #         self.agent_frame_timer += dt
    #         if self.agent_frame_timer >= self.agent_frame_delay:
    #             self.agent_frame_timer = 0.0
    #             self.agent_frame = (self.agent_frame + 1) % len(frames)

    #     # --- Turning ---
    #     if not self.turning and agent_dir != self.last_agent_dir:
    #         transition_lookup = {
    #             ('left', 'right'): 'down',
    #             ('right', 'left'): 'up',
    #             ('up', 'down'): 'right',
    #             ('down', 'up'): 'left',
    #         }
    #         mid = transition_lookup.get((self.last_agent_dir, agent_dir))
    #         if mid:
    #             self.turning = True
    #             self.turn_timer = 0.0
    #             self.turn_mid_frame = mid
    #             self.next_direction = agent_dir

    #     if self.turning:
    #         self.turn_timer += dt
    #         if self.turn_timer >= self.turn_duration:
    #             self.turning = False
    #             self.last_agent_dir = self.next_direction

    #     self.last_agent_dir = agent_dir

    #     # --- GRAB animation trigger ---
    #     if self.last_action == "GRAB":
    #         self.grab_anim_timer = self.grab_anim_duration

    #     # --- SHOOT animation trigger ---
    #     if self.last_action == "SHOOT":
    #         if self.shoot_anim_timer <= 0 and not self.arrow_animation["active"]:
    #             if self.shoot_path:
    #                 # Start arrow animation now
    #                 self.arrow_animation.update({
    #                     "active": True,
    #                     "path": self.shoot_path.copy(),
    #                     "current_index": 0,
    #                     "progress": 0.0,
    #                     "direction": agent_dir
    #                 })

    #     # Reset last_action only when arrow is done
    #     if self.last_action == "SHOOT" and not self.arrow_animation["active"] and self.shoot_anim_timer <= 0:
    #         self.last_action = None


    # def animate_arrow(self, dt, cell_size, top_left):
    #     anim = self.arrow_animation
    #     path = anim.get("path")
    #     if not path or anim["current_index"] >= len(path):
    #         anim["active"] = False
    #         return

    #     anim["progress"] += anim["speed"] * dt

    #     # Move to next cell if enough progress
    #     if anim["progress"] >= 1.0:
    #         anim["progress"] = 0.0
    #         anim["current_index"] += 1

    #     # Stop if finished
    #     if anim["current_index"] >= len(path):
    #         anim["active"] = False
    #         return

    #     pos = path[anim["current_index"]]
    #     visited_cells_coords = {(p.x, p.y) for p in self.gameloop.agent.visited_cells}
    
    #     arrow_cell_coords = (pos.x, pos.y)

    #     if arrow_cell_coords in visited_cells_coords:
    #         pixel_x = top_left[0] + pos.x * cell_size
    #         pixel_y = top_left[1] + (self.map_state["size"] - 1 - pos.y) * cell_size

    #         arrow_img = pygame.transform.scale(self.arrow_icon, (cell_size, cell_size))
    #         rotation = {
    #             'north': 90, 'south': -90, 'west': 180, 'east': 0
    #         }.get(self.arrow_animation["direction"], 0) 
            
    #         rotated = pygame.transform.rotate(arrow_img, rotation)
          
    #         rect = rotated.get_rect(center=(pixel_x + cell_size // 2, pixel_y + cell_size // 2))
    #         self.screen.blit(rotated, rect.topleft)

    def render_with_dt(self, dt):
        self.update_animation(dt)

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
        if self.mode == "hybrid":
            title_text = title_font.render("HYBRID MODE", True, (255, 255, 255))
        elif self.mode == "random":
            title_text = title_font.render("RANDOM MODE", True, (255, 255, 255))
        else:
            title_text = title_font.render("ADVANCED MODE", True, (255, 255, 255))

        title_rect = title_text.get_rect(center=(self.width / 2, 40))
        self.app.screen.blit(title_text, title_rect)

        self.draw_map(dt)
        pygame.display.flip()

        self.auto_solve_timer += dt
        if self.auto_solve_timer >= self.auto_solve_delay and not self.map_state.get('stop_game', False):
            self.auto_solve_timer = 0.0
            self.auto_solve_step()

        
    # 2. Simplify the run() method:
    def run(self):
        self.running = True
        while self.running:
            self.render()  # This now handles everything including timing
            pygame.display.flip()
            
            # Stop if game is done
            if self.map_state.get('stop_game', False):
                self.running = False
                return

    # 3. Add frame rate capping to arrow animation for smoother movement:
    def animate_arrow(self, dt, cell_size, top_left):
        anim = self.arrow_animation
        path = anim.get("path")
        if not path or anim["current_index"] >= len(path):
            anim["active"] = False
            return

        # Cap the dt to prevent huge jumps when frame rate drops
        capped_dt = min(dt, 1.0/30.0)  # Don't allow dt larger than 30fps frame
        anim["progress"] += anim["speed"] * capped_dt

        # Move to next cell if enough progress
        if anim["progress"] >= 1.0:
            anim["progress"] = 0.0
            anim["current_index"] += 1

        # Stop if finished
        if anim["current_index"] >= len(path):
            anim["active"] = False
            return

        pos = path[anim["current_index"]]
        visited_cells_coords = {(p.x, p.y) for p in self.gameloop.agent.visited_cells}

        arrow_cell_coords = (pos.x, pos.y)

        if arrow_cell_coords in visited_cells_coords:
            pixel_x = top_left[0] + pos.x * cell_size
            pixel_y = top_left[1] + (self.map_state["size"] - 1 - pos.y) * cell_size

            arrow_img = pygame.transform.scale(self.arrow_icon, (cell_size, cell_size))
            rotation = {
                'north': 90, 'south': -90, 'west': 180, 'east': 0
            }.get(self.arrow_animation["direction"], 0) 
            
            rotated = pygame.transform.rotate(arrow_img, rotation)
        
            rect = rotated.get_rect(center=(pixel_x + cell_size // 2, pixel_y + cell_size // 2))
            self.screen.blit(rotated, rect.topleft)

    # 4. Also cap dt in update_animation for consistent frame animation:
    def update_animation(self, dt):
        # Cap dt to prevent animation skipping
        capped_dt = min(dt, 1.0/30.0)
        
        # Get current direction
        agent_dir_enum = self.map_state['agent_direction']
        agent_dir = agent_dir_enum.name.lower() if agent_dir_enum else 'right'

        # --- Wumpus idle ---
        self.wumpus_frame_timer += capped_dt
        if self.wumpus_frame_timer >= self.wumpus_frame_delay:
            self.wumpus_frame_timer = 0.0
            self.wumpus_frame_index = (self.wumpus_frame_index + 1) % len(self.wumpus_idle_frames)

        # --- Agent walking ---
        direction = DIRECTION_TO_ANIMATION.get(agent_dir, 'right')
        frames = self.agent_animations.get(direction, [])
        if frames:
            self.agent_frame_timer += capped_dt
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
            self.turn_timer += capped_dt
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
                if self.shoot_path:
                    # Start arrow animation now
                    self.arrow_animation.update({
                        "active": True,
                        "path": self.shoot_path.copy(),
                        "current_index": 0,
                        "progress": 0.0,
                        "direction": agent_dir
                    })

        # Update shoot/grab timers with capped dt
        if self.shoot_anim_timer > 0:
            self.shoot_anim_timer -= capped_dt
        if self.grab_anim_timer > 0:
            self.grab_anim_timer -= capped_dt

        # Reset last_action only when arrow is done
        if self.last_action == "SHOOT" and not self.arrow_animation["active"] and self.shoot_anim_timer <= 0:
            self.last_action = None