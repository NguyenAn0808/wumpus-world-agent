import pygame
import os

from gui.screens.screen import Screen
# from gui.ui.button import Button

# --- Layout Constants ---
GRID_SIZE = 8
CELL_SIZE = 70 # Increased cell size for better visibility
GAME_AREA_WIDTH = GRID_SIZE * CELL_SIZE
UI_PANEL_WIDTH = 400
UI_PANEL_HEIGHT = 400
SCREEN_WIDTH = GAME_AREA_WIDTH + UI_PANEL_WIDTH
SCREEN_HEIGHT = GRID_SIZE * CELL_SIZE

class SelfPlayScreen(Screen):
    def __init__(self, app, map_state, world):
        super().__init__(app)
        self.map_state = map_state
        self.world = world
        self.game_mode = "manual" # Changed to reflect current controls

        # --- Pygame Setup ---
        self.screen = app.screen

        pygame.display.set_caption(f"Wumpus Solver - {self.game_mode.capitalize()} Mode")
        self.clock = pygame.time.Clock()
        self.running = True

        # --- Fonts ---
        self.ui_font_title = pygame.font.SysFont("Arial", 24, bold=True)
        self.ui_font_log = pygame.font.SysFont("Consolas", 16)
        self.action_log = ["Game Started..."]

        # --- Asset Loading ---
        self.cell_icons = self.load_cell_icons()
        self.agent_frames = self.load_agent_animations()
        self.wumpus_frames = self.load_wumpus_idle()

        # --- Agent State ---
        self.agent_frame_index = 0
        self.agent_anim_timer = 0
        self.agent_anim_speed = 8 # Lower is faster
        self.agent_pos = [0, 0]  # Grid coordinates (col, row), origin bottom-left
        self.agent_pix_pos = self.get_pixel_pos_from_grid(self.agent_pos[0], self.agent_pos[1])
        self.agent_direction = "right" # Directions: 'up', 'down', 'left', 'right'
        self.is_moving = False

        # --- Wumpus State ---
        self.wumpus_frame_index = 0
        self.wumpus_anim_timer = 0
        self.wumpus_anim_speed = 15 # Controls wumpus animation speed

        # --- Input Handling for manual control ---
        self.move_delay = 8  # frames between continuous moves
        self.move_timer = 0
        
        # Moving timing
        self.move_duration = 0.3  # Thời gian (giây) để di chuyển qua một ô
        self.move_progress = 0.0  # Tiến trình di chuyển (từ 0.0 đến 1.0)
        self.move_start_pix_pos = None
        self.move_target_pix_pos = None

        # Turning timing
        self.turning = False
        self.turn_timer = 0.0
        self.turn_duration = 0.2  # seconds
        self.turn_mid_frame = None
        self.next_direction = None
        
        # Animation timing
        self.time_per_anim_frame = 0.1 # Giá trị mặc định, sẽ được tính toán lại

        # Logic game
        self.is_game_over = False
        self.has_arrow = True
        self.score = 0
        self.has_gold = False

        # ScrollBar
        self.log_scroll_y = 0               
        self.log_line_height = 20           
        self.log_surface_needs_update = True  
        self.log_full_surface = None        
        self.auto_scroll_to_bottom = True  

        self.panel_rect = pygame.Rect(GAME_AREA_WIDTH, 0, UI_PANEL_WIDTH, UI_PANEL_HEIGHT) 
    
    def get_pixel_pos_from_grid(self, grid_x, grid_y):
        """Converts grid coordinates (bottom-left origin) to pixel coordinates (top-left origin)."""
        pix_x = grid_x * CELL_SIZE
        pix_y = SCREEN_HEIGHT - ((grid_y + 1) * CELL_SIZE)
        return [pix_x, pix_y]

    def load_cell_icons(self):
        """Loads all icons for game objects like pits, gold, etc."""
        icons = {}
        # Helper to load and handle potential errors
        def load_image(name):
            path = os.path.join("assets", f"{name}.png")
            try:
                return pygame.image.load(path).convert_alpha()
            except (pygame.error, FileNotFoundError) as e:
                print(f"Warning: Could not load image '{path}'. Using a placeholder. Error: {e}")
                # Create a placeholder surface if image fails to load
                placeholder = pygame.Surface((CELL_SIZE, CELL_SIZE))
                placeholder.fill((255, 0, 255)) # Bright pink to indicate missing texture
                return placeholder

        icons['P'] = load_image('pit')
        icons['G'] = load_image('gold')
        icons['S'] = load_image('stench')
        icons['B'] = load_image('breeze')
        return icons

    def load_agent_animations(self):
        """Loads all directional animation frames for the agent."""
        animations = {}
        for direction in ['up', 'down', 'left', 'right']:
            frames = []
            i = 0
            while True:
                path = os.path.join("assets", "agent", direction, f"{i}.png")
                try:
                    frames.append(pygame.image.load(path).convert_alpha())
                    i += 1
                except (pygame.error, FileNotFoundError):
                    if i == 0: # If not even one frame is found, create a placeholder
                        print(f"Warning: No frames found for agent direction '{direction}'.")
                        placeholder = pygame.Surface((CELL_SIZE, CELL_SIZE))
                        placeholder.fill((0, 255, 0)) # Green placeholder
                        frames.append(placeholder)
                    break # Stop if no more frames are found
            animations[direction] = frames
        return animations

    def load_wumpus_idle(self):
        """Loads all idle animation frames for the Wumpus."""
        frames = []
        i = 0
        while True:
            path = os.path.join("assets", "wumpus", "idle", f"{i}.png")
            try:
                frames.append(pygame.image.load(path).convert_alpha())
                i += 1
            except (pygame.error, FileNotFoundError):
                if i == 0:
                    print("Warning: No frames found for Wumpus. Using placeholder.")
                    placeholder = pygame.Surface((CELL_SIZE, CELL_SIZE))
                    placeholder.fill((255, 0, 0)) # Red placeholder
                    frames.append(placeholder)
                break
        return frames
    
    def get_turn_transition_frame(self, from_dir, to_dir):
        mid_map = {
            ('left', 'right'): 'down',
            ('right', 'left'): 'up',
            ('up', 'down'): 'right',
            ('down', 'up'): 'left'
        }
        return mid_map.get((from_dir, to_dir))

    def update_animations(self, dt):
        if self.turning:
            self.turn_timer += dt
            if self.turn_timer >= self.turn_duration:
                self.turning = False
                self.agent_direction = self.next_direction
                self.turn_mid_frame = None
            return  # Skip walking animation during turn
        if self.is_moving:
            self.agent_anim_timer += dt
            if self.agent_anim_timer >= self.time_per_anim_frame:
                self.agent_frame_index = (self.agent_frame_index + 1) % len(self.agent_frames[self.agent_direction])
                self.agent_anim_timer = 0
        else:
            self.agent_frame_index = 0

        self.wumpus_anim_timer += dt
        if self.wumpus_anim_timer >= 0.15:
            self.wumpus_frame_index = (self.wumpus_frame_index + 1) % len(self.wumpus_frames)
            self.wumpus_anim_timer = 0

        # Wumpus animation
        self.wumpus_anim_timer += dt
        if self.wumpus_anim_timer >= 0.1:
            self.wumpus_frame_index = (self.wumpus_frame_index + 1) % len(self.wumpus_frames)
            self.wumpus_anim_timer = 0
            
    def draw_game_area(self):
        """Draws the main game grid, including tiles, items, and characters."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # --- Draw Grid and Cell Contents ---
                rect = pygame.Rect(x * CELL_SIZE, (GRID_SIZE - 1 - y) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (45, 102, 91), rect) # Cell background
                pygame.draw.rect(self.screen, (35, 80, 72), rect, 2) # Cell border

                # TODO: Draw Borders for outer edges 
                
                
                # --- Draw Items from map_state ---
                state = self.map_state['state']
                if y < len(state) and x < len(state[y]):
                    cell_content = state[y][x]
                    # Draw Wumpus
                    if 'W' in cell_content:
                        wumpus_frame = pygame.transform.scale(self.wumpus_frames[self.wumpus_frame_index], (CELL_SIZE, CELL_SIZE))
                        self.screen.blit(wumpus_frame, rect.topleft)
                    # Draw other icons
                    for symbol in ['P', 'G', 'S', 'B']:
                         if symbol in cell_content:
                            icon = pygame.transform.scale(self.cell_icons[symbol], (CELL_SIZE, CELL_SIZE))
                            self.screen.blit(icon, rect.topleft)

        # --- Draw Agent ---
        if self.turning and self.turn_mid_frame:
            frame = self.agent_frames[self.turn_mid_frame][0]
        else:
            frame = self.agent_frames[self.agent_direction][self.agent_frame_index]

        scaled_agent = pygame.transform.scale(frame, (CELL_SIZE, CELL_SIZE))
        self.screen.blit(scaled_agent, self.agent_pix_pos)

    def draw_ui_panel(self):
        # 1. Vẽ nền cho panel
        
        pygame.draw.rect(self.screen, (220, 220, 240), self.panel_rect) # Nền xám nhạt

        # --- Phần Action Log ---
        log_title = self.ui_font_title.render("Action Log", True, (0, 0, 0))
        self.screen.blit(log_title, (GAME_AREA_WIDTH + 20, 20))

        # 2. Định nghĩa khu vực hiển thị cho log (viewable area)
        log_view_rect = pygame.Rect(GAME_AREA_WIDTH, 60, UI_PANEL_WIDTH, UI_PANEL_HEIGHT - 80) # Dành không gian cho tiêu đề và lề

        # 3. Tạo/Cập nhật Surface chứa toàn bộ log nếu cần
        if self.log_surface_needs_update and self.action_log:
            # Tính toán chiều cao cần thiết cho tất cả các dòng log
            full_height = len(self.action_log) * self.log_line_height
            # Tạo một surface mới đủ lớn
            self.log_full_surface = pygame.Surface((log_view_rect.width - 40, full_height)) # -40 để có lề
            self.log_full_surface.fill((220, 220, 240)) # Màu nền giống panel

            # Vẽ từng dòng log lên surface lớn này
            for i, entry in enumerate(self.action_log):
                log_text = self.ui_font_log.render(entry, True, (50, 50, 50))
                self.log_full_surface.blit(log_text, (0, i * self.log_line_height))
            
            self.log_surface_needs_update = False # Đánh dấu là đã cập nhật

        # 4. Vẽ phần log có thể thấy được lên màn hình
        if self.log_full_surface:
            # Tính toán giá trị cuộn tối đa
            max_scroll_y = self.log_full_surface.get_height() - log_view_rect.height
            if max_scroll_y < 0:
                max_scroll_y = 0

            # Tự động cuộn xuống dưới cùng nếu được bật
            if self.auto_scroll_to_bottom:
                self.log_scroll_y = max_scroll_y
            
            # Đảm bảo không cuộn ra ngoài giới hạn
            self.log_scroll_y = max(0, min(self.log_scroll_y, max_scroll_y))
            
            # Vùng "camera" chúng ta sẽ cắt từ surface lớn
            source_rect = pygame.Rect(0, self.log_scroll_y, log_view_rect.width, log_view_rect.height)
            
            # Vị trí đích để vẽ trên màn hình chính
            dest_pos = (log_view_rect.left + 20, log_view_rect.top) # +20 để có lề trái
            
            self.screen.blit(self.log_full_surface, dest_pos, source_rect)

            # 5. Vẽ thanh cuộn (Scrollbar)
            if max_scroll_y > 0:
                # Vị trí và kích thước của đường ray
                scrollbar_track_rect = pygame.Rect(self.panel_rect.right - 20, log_view_rect.top, 15, log_view_rect.height)
                pygame.draw.rect(self.screen, (200, 200, 220), scrollbar_track_rect) # Màu đường ray

                # Tính toán kích thước và vị trí của tay cầm
                # Chiều cao tay cầm tỉ lệ với lượng nội dung có thể thấy
                handle_height = log_view_rect.height * (log_view_rect.height / self.log_full_surface.get_height())
                handle_height = max(20, handle_height) # Chiều cao tối thiểu cho tay cầm

                # Vị trí Y của tay cầm tỉ lệ với vị trí cuộn
                scroll_percentage = self.log_scroll_y / max_scroll_y
                handle_y = scrollbar_track_rect.top + (scroll_percentage * (scrollbar_track_rect.height - handle_height))
                
                scrollbar_handle_rect = pygame.Rect(scrollbar_track_rect.left, handle_y, 15, handle_height)
                pygame.draw.rect(self.screen, (150, 150, 170), scrollbar_handle_rect) # Màu tay cầm

            # Vẽ icon hướng dẫn chơi bên dưới game area
            icon_keys = pygame.image.load(os.path.join("assets", "keys.png")).convert_alpha()
            
            icon_arrow = pygame.image.load(os.path.join("assets", "space.png")).convert_alpha()
            # icon_arrow = pygame.transform.scale(icon_arrow)
            icon_esc = pygame.image.load(os.path.join("assets",  "escape.png")).convert_alpha()
            # icon_esc = pygame.transform.scale(icon_esc)
            icon_enter = pygame.image.load(os.path.join("assets", "enter.png")).convert_alpha()
            # icon_enter = pygame.transform.scale(icon_enter)
            self.screen.blit(icon_arrow, (SCREEN_HEIGHT + 20, 100))
            self.screen.blit(icon_keys, (SCREEN_HEIGHT + 20, 150))
            self.screen.blit(icon_esc, (SCREEN_HEIGHT + 20, 200))
            self.screen.blit(icon_enter, (SCREEN_HEIGHT + 20, 250))


    def add_to_log(self, message):
        self.action_log.append(message)
        self.log_surface_needs_update = True


    def check_consequences(self):
        x, y = self.agent_pos

        cell_content = self.map_state['state'][y][x]

        if 'W' in cell_content:
            self.add_to_log("Wumpus!")
            self.is_game_over = True
            self.score -= 1000
            self.running = False
        elif 'P' in cell_content:
            self.add_to_log("Pit!")
            self.is_game_over = True
            self.score -= 1000
            self.running = False

    def shoot_arrow(self):
        self.add_to_log("You shoot an arrow...")
        self.has_arrow = False 
        self.score -= 10

        direction_map = {
            'up':    (0, 1),
            'down':  (0, -1),
            'left':  (-1, 0),
            'right': (1, 0),
        }
        dx, dy = direction_map[self.agent_direction]

        arrow_x, arrow_y = self.agent_pos

        while True:
            arrow_x += dx
            arrow_y += dy

            # Kiểm tra xem mũi tên có bay ra ngoài bản đồ không
            if not (0 <= arrow_x < GRID_SIZE and 0 <= arrow_y < GRID_SIZE):
                break 

            cell_content = self.map_state['state'][arrow_y][arrow_x]
            if 'W' in cell_content:
                self.add_to_log("SCREAM")
                
                # Delete wumpus
                self.map_state['state'][arrow_y][arrow_x].discard('W')
                
                # Delete Stenches
                for off_x, off_y in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    stench_x, stench_y = arrow_x + off_x, arrow_y + off_y
                    if 0 <= stench_x < GRID_SIZE and 0 <= stench_y < GRID_SIZE:
                        self.map_state['state'][stench_y][stench_x].discard('S')

                break 

    def handle_input(self):
        if self.is_game_over:
            return
       
        # Chỉ xử lý input mới nếu agent không bận (không di chuyển và không xoay)
        if self.is_moving or self.turning:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    if hasattr(self.app, 'quit'):
                        self.app.quit()
            return 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                if hasattr(self.app, 'quit'):
                    self.app.quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.panel_rect.collidepoint(event.pos): # Chỉ cuộn nếu chuột ở trong panel
                    # event.button 4 is scroll up, 5 is scroll down
                    if event.button == 4: # Scroll Up
                        self.log_scroll_y = max(0, self.log_scroll_y - self.log_line_height * 3) # Cuộn 3 dòng
                        self.auto_scroll_to_bottom = False # Người dùng đã tự cuộn
                    elif event.button == 5: # Scroll Down
                        self.log_scroll_y += self.log_line_height * 3
                        
                        # logic kiểm tra để bật lại auto-scroll sẽ được xử lý trong draw_ui_panel
                        # để đảm bảo tính toán chính xác sau khi nội dung được cập nhật.
                        # Tuy nhiên, chúng ta có thể làm một phép kiểm tra sơ bộ ở đây
                        if self.log_full_surface:
                            max_scroll = self.log_full_surface.get_height() - (UI_PANEL_HEIGHT - 80)
                            if self.log_scroll_y >= max_scroll - self.log_line_height: # Gần dưới cùng
                                self.auto_scroll_to_bottom = True

            if event.type == pygame.KEYDOWN:
                dx, dy = 0, 0
                desired_dir = None

                if event.key == pygame.K_UP:
                    desired_dir = 'up'
                    dy = 1
                elif event.key == pygame.K_DOWN:
                    desired_dir = 'down'
                    dy = -1
                elif event.key == pygame.K_LEFT:
                    desired_dir = 'left'
                    dx = -1
                elif event.key == pygame.K_RIGHT:
                    desired_dir = 'right'
                    dx = 1
                elif event.key == pygame.K_SPACE:
                    x, y = self.agent_pos
                    if 'G' in self.map_state['state'][y][x]:
                        self.has_gold = True
                        self.score += 10
                        self.add_to_log("GOLD!")
                        self.map_state['state'][y][x].discard('G')
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if self.has_arrow:
                        self.shoot_arrow()
                elif event.key == pygame.K_ESCAPE:
                    if self.agent_pos == [0, 0]:
                        if self.has_gold:
                            self.score += 1000

                        self.running = False

                if desired_dir:
                    # Nếu hướng mong muốn khác hướng hiện tại -> xoay người
                    if desired_dir != self.agent_direction:
                        if (desired_dir == 'up' and self.agent_direction == 'down') or  (desired_dir == 'down' and self.agent_direction == 'up') or (desired_dir == 'right' and self.agent_direction == 'left') or  (desired_dir == 'left' and self.agent_direction == 'right'):
                            self.score -= 2
                        else:
                            self.score -= 1
                    
                        self.turning = True
                        self.turn_timer = 0.0
                        self.turn_mid_frame = self.get_turn_transition_frame(self.agent_direction, desired_dir)
                        self.next_direction = desired_dir

                        self.add_to_log(f"Turn {desired_dir}")
                    # Nếu đã đúng hướng -> bắt đầu di chuyển
                    else:
                        self.start_move(dx, dy)
                        self.score -= 1

    def start_move(self, dx, dy):
        new_x = self.agent_pos[0] + dx
        new_y = self.agent_pos[1] + dy

        if not (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE):
            return

        # Thiết lập trạng thái di chuyển
        self.is_moving = True
        self.move_progress = 0.0
        self.move_start_pix_pos = self.agent_pix_pos[:] # Tạo bản sao

        # Cập nhật vị trí logic ngay lập tức
        self.agent_pos = [new_x, new_y]
        self.move_target_pix_pos = self.get_pixel_pos_from_grid(new_x, new_y)

        num_frames = len(self.agent_frames[self.agent_direction])
        if num_frames > 0: # Tránh lỗi chia cho 0
            self.time_per_anim_frame = self.move_duration / num_frames

    def update(self, dt):
        if self.is_game_over:
            return

        if self.is_moving:
            self.move_progress += dt / self.move_duration
            
            if self.move_progress >= 1.0:
                self.is_moving = False
                self.agent_pix_pos = self.move_target_pix_pos[:] # Snap vào vị trí cuối cùng
                self.add_to_log(f"Move to ({self.agent_pos[0]}, {self.agent_pos[1]})")

                self.check_consequences()
            else:
                px = self.move_start_pix_pos[0] + (self.move_target_pix_pos[0] - self.move_start_pix_pos[0]) * self.move_progress
                py = self.move_start_pix_pos[1] + (self.move_target_pix_pos[1] - self.move_start_pix_pos[1]) * self.move_progress
                self.agent_pix_pos = [px, py]

        # Update animation
        self.update_animations(dt)

    def render(self):
        self.screen.fill((190, 212, 184))
        self.draw_game_area()
        self.draw_ui_panel()
        pygame.display.flip()

    def run(self):
        self.running = True
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            self.handle_input()

            self.update(dt)

            self.render()

        print("Total score: ", self.score)
        