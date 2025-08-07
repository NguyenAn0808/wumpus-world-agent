import pygame
import os
import cv2

from gui.screens.screen import Screen
from gui.screens.menu_screen import MenuScreen
from simulation import DIRECTION_VECTORS
from simulation.components import Point, Direction
# from gui.ui.button import Button

# --- Layout Constants ---
GRID_SIZE = 8
CELL_SIZE = 75 # Increased cell size for better visibility
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
        self.width, self.height = self.screen.get_size()

        pygame.display.set_caption(f"Wumpus Solver - {self.game_mode.capitalize()} Mode")
        self.clock = pygame.time.Clock()
        self.running = True

        # --- Fonts ---
        self.ui_font_title = pygame.font.SysFont("perpetua", 24, bold=True)
        self.ui_font_log = pygame.font.SysFont("perpetua", 20)
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
        self.has_arrow = True
        self.score = 0
        self.has_gold = False

        # ScrollBar
        self.log_scroll_y = 0               
        self.log_line_height = 20           
        self.log_surface_needs_update = True  
        self.log_full_surface = None        
        self.auto_scroll_to_bottom = True  

        self.panel_rect = pygame.Rect(self.width / 2 + 230, self.height / 2 - 80, UI_PANEL_WIDTH, UI_PANEL_HEIGHT) 
        
        self.score_rect = pygame.Rect(self.width / 2 + 230, self.height / 2 - 280, UI_PANEL_WIDTH, 180) 

        # Popups endgame
        self.overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 150)) # Màu đen, độ mờ 150/255
        self.game_over_state = None  

        self.video_capture = None        # Đối tượng cv2.VideoCapture
        self.current_video_frame = None  # Surface Pygame của frame hiện tại
        self.video_fps = 0               # FPS của video đang phát
        self.video_frame_timer = 0.0     # Đồng hồ để đồng bộ frame

        self.video_display_size = (400, 400)
        self.popup_video_paths = {
            'wumpus': os.path.join("gui", "assets", "wumpus.mp4"),
            'pit': os.path.join("gui", "assets", "pit.mp4"),
            'scream': os.path.join("gui", "assets", "scream.mp4"),
            'climb out': os.path.join("gui", "assets", "climb out.mp4")
        }

        self.terminating_states = ['wumpus', 'pit', 'climb out', 'error']

        # --- Action animations ---
        self.shoot_anim_active = False
        self.shoot_anim_timer = 0.0
        self.hit_wumpus_delay_timer = 0.0
        self.hit_wumpus_delay_duration = 0.5
        self.shoot_anim_duration = 0.5  # seconds

        self.grab_anim_active = False
        self.grab_anim_timer = 0.0
        self.grab_anim_duration = 0.5  # seconds

        self.agent_grab_frames = self.load_agent_action_frames("grab")
        self.agent_shoot_frames = self.load_agent_action_frames("shoot")

        self.arrow_icon = pygame.image.load("assets/arrow.png").convert_alpha()
        self.arrow_path = []
        self.arrow_anim = {
            "active": False,
            "path": [],
            "current_index": 0,
            "progress": 0.0,
            "speed": 6.0,  # cells per second
            "direction": None
        }

        self.cap = cv2.VideoCapture("gui/assets/menu.mp4")

        original_title_image = pygame.image.load("gui/assets/frame.png").convert_alpha()
        self.title_image = pygame.transform.scale(original_title_image, (1350, 700))

        self.visited_cells = set()
        self.visited_cells.add(tuple(self.agent_pos))

    def load_agent_action_frames(self, action):
        # Loads action animation frames like 'grab' or 'shoot
        frames = []
        i = 0
        while True:
            path = os.path.join("assets", "agent", action, f"{i}.png")
            try:
                frames.append(pygame.image.load(path).convert_alpha())
                i += 1
            except (pygame.error, FileNotFoundError):
                break
        return frames

    def trigger_grab_animation(self):
        self.grab_anim_active = True
        self.grab_anim_timer = self.grab_anim_duration

    def trigger_shoot_animation(self):
        self.shoot_anim_active = True
        self.shoot_anim_timer = self.shoot_anim_duration

    def start_arrow_animation(self, direction, path):
        self.arrow_anim["active"] = True
        self.arrow_anim["path"] = path
        self.arrow_anim["current_index"] = 0
        self.arrow_anim["progress"] = 0.0
        self.arrow_anim["direction"] = direction

    def load_popup_image(self, name):
        path = os.path.join("gui", "assets", f"{name}.png") # Giả sử ảnh nằm trong assets/ui
        try:
            return pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError) as e:
            print(f"Warning: Could not load popup image '{path}'. Error: {e}")
            # Tạo placeholder nếu không có ảnh
            placeholder = self.ui_font_title.render(f"{name.upper()}", True, (255, 0, 0))
            return placeholder
        
    def start_game_over_video(self, state):
        """Kích hoạt trạng thái game over và mở video bằng CV2."""
        self.game_over_state = state
        video_path = self.popup_video_paths.get(state)

        if video_path and os.path.exists(video_path):
            try:
                self.video_capture = cv2.VideoCapture(video_path)
                if not self.video_capture.isOpened():
                    raise IOError(f"Cannot open video file: {video_path}")
                
                # Lấy FPS của video
                self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
                # Nếu không lấy được FPS, đặt giá trị mặc định
                if self.video_fps == 0:
                    print(f"Warning: Could not get FPS for {video_path}. Defaulting to 30 FPS.")
                    self.video_fps = 30

            except Exception as e:
                print(f"Error loading video with cv2: {e}")
                self.video_capture = None
                # Nếu có lỗi, chuyển về menu sau 3 giây
                self.game_over_state = 'error' # Một trạng thái dự phòng
                self.game_over_timer = 0.0
                self.game_over_duration = 3.0
        else:
            print(f"Video not found for state: {state}")
            self.game_over_state = 'error'
            self.game_over_timer = 0.0
            self.game_over_duration = 3.0
    
    def get_pixel_pos_from_grid(self, grid_x, grid_y):
        """Converts grid coordinates (bottom-left origin) to pixel coordinates (top-left origin)."""
        pix_x = grid_x * CELL_SIZE
        pix_y = SCREEN_HEIGHT - ((grid_y + 1) * CELL_SIZE)
        return [pix_x + (self.width / 2 - 390), pix_y + (self.height / 2 - 280)]

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
        icons['S'] = load_image('letter-s')
        icons['B'] = load_image('letter-b')
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
        # Grab animation timer
        if self.grab_anim_active:
            self.grab_anim_timer -= dt
            if self.grab_anim_timer <= 0:
                self.grab_anim_active = False

        # Shoot animation timer
        if self.shoot_anim_active:
            self.shoot_anim_timer -= dt
            if self.shoot_anim_timer <= 0:
                self.shoot_anim_active = False
                # Start arrow AFTER shoot anim ends
                self.shoot_arrow()

        # Arrow animation
        if self.arrow_anim["active"]:
            self.arrow_anim["progress"] += dt * self.arrow_anim["speed"]

            if self.arrow_anim["progress"] >= 1.0:
                self.arrow_anim["progress"] = 0.0
                self.arrow_anim["current_index"] += 1

                if self.arrow_anim["current_index"] >= len(self.arrow_anim["path"]):
                    self.arrow_anim["active"] = False


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
                rect = pygame.Rect((self.width / 2 - 390) + x * CELL_SIZE, (self.height / 2 - 280)+(GRID_SIZE - 1 - y) * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (45, 102, 91), rect) # Cell background
                pygame.draw.rect(self.screen, (35, 80, 72), rect, 2) # Cell border

                if (x, y) not in self.visited_cells:
                    fog_color = (20, 20, 30, 200)
                    fog_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
                    fog_surface.fill(fog_color)
                    self.screen.blit(fog_surface, rect.topleft)

                    continue

                # --- Draw Items from map_state ---
                state = self.map_state['state']
                if y < len(state) and x < len(state[y]):
                    cell_content = state[y][x]
                    if 'S' in cell_content or 'B' in cell_content:
                        if 'S' in cell_content and 'B' in cell_content:
                            stench_icon = pygame.transform.scale(self.cell_icons['S'], (CELL_SIZE // 2, CELL_SIZE // 2))
                            breeze_icon = pygame.transform.scale(self.cell_icons['B'], (CELL_SIZE // 2, CELL_SIZE // 2))

                            self.screen.blit(stench_icon, rect.topleft)
                            self.screen.blit(breeze_icon, (rect.topright[0] - CELL_SIZE // 2, rect.topright[1]))  # Adjust x for width
                        elif 'S' in cell_content:
                            stench_icon = pygame.transform.scale(self.cell_icons['S'], (CELL_SIZE // 2, CELL_SIZE // 2))
                            self.screen.blit(stench_icon, rect.topleft)
                        elif 'B' in cell_content:
                            breeze_icon = pygame.transform.scale(self.cell_icons['B'], (CELL_SIZE // 2, CELL_SIZE // 2))
                            self.screen.blit(breeze_icon, rect.topleft)
                    # Draw Wumpus
                    if 'W' in cell_content:
                        wumpus_frame = pygame.transform.scale(self.wumpus_frames[self.wumpus_frame_index], (CELL_SIZE, CELL_SIZE))
                        self.screen.blit(wumpus_frame, rect.topleft)
                    # Draw other icons
                    if 'P' in cell_content:
                        pit_icon = pygame.transform.scale(self.cell_icons['P'], (CELL_SIZE, CELL_SIZE))
                        self.screen.blit(pit_icon, rect.topleft)
                    if 'G' in cell_content:
                        gold_icon = pygame.transform.scale(self.cell_icons['G'], (CELL_SIZE, CELL_SIZE))
                        self.screen.blit(gold_icon, rect.topleft)

        # -- Draw Arrow Animation ---
        if self.arrow_anim["active"]:
            pos = self.arrow_anim["path"][self.arrow_anim["current_index"]]
            if (pos.x, pos.y) in self.visited_cells:
                pixel_x = pos.x * CELL_SIZE + (self.width / 2 - 390)
                pixel_y = (self.map_state['size'] - 1 - pos.y) * CELL_SIZE + (self.height / 2 - 280)

                arrow_img = pygame.transform.scale(self.arrow_icon, (CELL_SIZE, CELL_SIZE))
                rotated = {
                    'up': 90, 'down': -90, 'left': 180, 'right': 0
                }[self.arrow_anim["direction"]]
                rotated_img = pygame.transform.rotate(arrow_img, rotated)
                self.screen.blit(rotated_img, (pixel_x, pixel_y))

        # --- Draw Agent ---
        if self.turning and self.turn_mid_frame:
            frame = self.agent_frames[self.turn_mid_frame][0]
        elif self.shoot_anim_active and self.agent_shoot_frames:
            index = int((self.shoot_anim_duration - self.shoot_anim_timer) / self.shoot_anim_duration * len(self.agent_shoot_frames))
            index = min(index, len(self.agent_shoot_frames) - 1)
            frame = self.agent_shoot_frames[index]
        elif self.grab_anim_active and self.agent_grab_frames:
            index = int((self.grab_anim_duration - self.grab_anim_timer) / self.grab_anim_duration * len(self.agent_grab_frames))
            index = min(index, len(self.agent_grab_frames) - 1)
            frame = self.agent_grab_frames[index]
        else:
            frame = self.agent_frames[self.agent_direction][self.agent_frame_index]

        scaled_agent = pygame.transform.scale(frame, (CELL_SIZE, CELL_SIZE))
        self.screen.blit(scaled_agent, self.agent_pix_pos)

    def draw_ui_panel(self):
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

        # --- Hiển thị Điểm số ---
        value_surf = self.ui_font_title.render(str(self.score), True, (255, 255, 255)) 
        value_rect = value_surf.get_rect(topleft= (self.width / 2 + 380, self.height /2 - 237))
        self.screen.blit(value_surf, value_rect)
        
        if self.has_arrow:
            text = "Yes"
        else:
            text = "No"
        value_surf = self.ui_font_title.render(text, True, (255, 255, 255)) 
        value_rect = value_surf.get_rect(topleft= (self.width / 2 + 390, self.height /2 - 192))
        self.screen.blit(value_surf, value_rect)
        
        if self.has_gold:
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

        # 2. Định nghĩa khu vực hiển thị cho log (viewable area)
        log_view_rect = pygame.Rect(self.width / 2 + 220, self.height / 2 - 35, UI_PANEL_WIDTH, UI_PANEL_HEIGHT - 55) # Dành không gian cho tiêu đề và lề

        # 3. Tạo/Cập nhật Surface chứa toàn bộ log nếu cần
        if self.log_surface_needs_update and self.action_log:
            # Tính toán chiều cao cần thiết cho tất cả các dòng log
            full_height = len(self.action_log) * self.log_line_height
            # Tạo một surface mới đủ lớn
            self.log_full_surface = pygame.Surface((log_view_rect.width - 40, full_height)) # -40 để có lề

            # Vẽ từng dòng log lên surface lớn này
            for i, entry in enumerate(self.action_log):
                log_text = self.ui_font_log.render(entry, True, (255, 255, 255))
                self.log_full_surface.blit(log_text, (10, i * self.log_line_height))
            
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
                pygame.draw.rect(self.screen, (255, 255, 255), scrollbar_track_rect) # Màu đường ray

                # Tính toán kích thước và vị trí của tay cầm
                # Chiều cao tay cầm tỉ lệ với lượng nội dung có thể thấy
                handle_height = log_view_rect.height * (log_view_rect.height / self.log_full_surface.get_height())
                handle_height = max(20, handle_height) # Chiều cao tối thiểu cho tay cầm

                # Vị trí Y của tay cầm tỉ lệ với vị trí cuộn
                scroll_percentage = self.log_scroll_y / max_scroll_y
                handle_y = scrollbar_track_rect.top + (scroll_percentage * (scrollbar_track_rect.height - handle_height))
                
                scrollbar_handle_rect = pygame.Rect(scrollbar_track_rect.left, handle_y, 15, handle_height)
                pygame.draw.rect(self.screen, (180, 180, 180), scrollbar_handle_rect) # Màu tay cầm


            # Draw percepts information 
            overlay_x = self.width / 2 - 600
            overlay_y = self.height / 2 - 230
            overlay_width = 150  # total width for 3 squares
            overlay_height = 50  # height of each square

            # Draw the black background rectangle for the percept overlay
            overlay_rect = pygame.Rect(overlay_x, overlay_y, overlay_width, overlay_height)
            pygame.draw.rect(self.screen, (255, 255, 255), overlay_rect)

            square_width = overlay_width // 3

            # Define percept icons
            icons = [('B', pygame.image.load(os.path.join("assets", "breeze.png")).convert_alpha()), ('S', pygame.image.load(os.path.join("assets", "stench.png")).convert_alpha()), ('G', pygame.image.load(os.path.join("assets", "glitter.png")).convert_alpha())]

            # Get symbols in the agent's current cell
            agent_x, agent_y = self.agent_pos
            cell_symbols = self.map_state['state'][agent_y][agent_x] if 0 <= agent_y < GRID_SIZE and 0 <= agent_x < GRID_SIZE else set()

            for i, (symbol, icon) in enumerate(icons):
                square_rect = pygame.Rect(overlay_x + i * square_width, overlay_y, square_width, overlay_height)
                pygame.draw.rect(self.screen, (30, 30, 30), square_rect, 1)  # draw border for each square

                if symbol in cell_symbols and icon:
                    scaled_icon = pygame.transform.scale(icon, (square_width, overlay_height))
                    self.screen.blit(scaled_icon, square_rect.topleft)

            # Vẽ icon hướng dẫn chơi bên dưới game area

            icon_temp_keys = pygame.image.load(os.path.join("assets", "keys.png")).convert_alpha()
            icon_keys = pygame.transform.scale(icon_temp_keys, (90, 90))

            icon_temp_space = pygame.image.load(os.path.join("assets", "space.png")).convert_alpha()
            icon_space = pygame.transform.scale(icon_temp_space, (90, 90))
            
            icon_temp_enter = pygame.image.load(os.path.join("assets", "enter.png")).convert_alpha()
            icon_enter = pygame.transform.scale(icon_temp_enter, (90, 90))

            icon_temp_esc = pygame.image.load(os.path.join("assets", "escape.png")).convert_alpha()
            icon_esc = pygame.transform.scale(icon_temp_esc, (90, 90))
   
            self.screen.blit(icon_keys, (self.width / 2 - 625, self.height /2 - 170))
            self.screen.blit(icon_space, (self.width / 2 - 630, self.height /2 - 70))
            self.screen.blit(icon_enter, (self.width / 2 - 630, self.height /2  + 30))
            self.screen.blit(icon_esc, (self.width / 2 - 630, self.height /2 + 130))

            title_text = title_font.render("Move", True, (255, 255, 255))
            title_rect = title_text.get_rect(topleft= (self.width / 2 - 515, self.height /2 - 140))
            self.app.screen.blit(title_text, title_rect)

            title_text = title_font.render("Pick", True, (255, 255, 255))
            title_rect = title_text.get_rect(topleft= (self.width / 2 - 515, self.height /2 - 40))
            self.app.screen.blit(title_text, title_rect)

            title_text = title_font.render("Shoot", True, (255, 255, 255))
            title_rect = title_text.get_rect(topleft= (self.width / 2 - 515, self.height /2 + 60))
            self.app.screen.blit(title_text, title_rect)

            title_text = title_font.render("Climb", True, (255, 255, 255))
            title_rect = title_text.get_rect(topleft= (self.width / 2 - 515, self.height /2 + 160))
            self.app.screen.blit(title_text, title_rect)

    def draw_game_over_video(self):
        self.screen.blit(self.overlay, (0, 0))

        if self.current_video_frame:
            screen_rect = self.screen.get_rect()
            frame_rect = self.current_video_frame.get_rect(center=screen_rect.center)
            self.screen.blit(self.current_video_frame, frame_rect)

    def add_to_log(self, message):
        self.action_log.append(message)
        self.log_surface_needs_update = True

    def check_consequences(self):
        if self.game_over_state: return

        x, y = self.agent_pos
        cell_content = self.map_state['state'][y][x]

        if 'W' in cell_content:
            self.add_to_log("Wumpus!")
            self.score -= 1000
            self.start_game_over_video('wumpus')
        elif 'P' in cell_content:
            self.add_to_log("Pit!")
            self.score -= 1000
            self.start_game_over_video('pit')

    def shoot_arrow(self):
        self.add_to_log("You shoot an arrow...")
        self.has_arrow = False
        self.score -= 10

        GUI_TO_ENUM_DIRECTION = {
            'up': Direction.NORTH,
            'down': Direction.SOUTH,
            'left': Direction.WEST,
            'right': Direction.EAST
        }
        enum_direction = GUI_TO_ENUM_DIRECTION[self.agent_direction]
        dx, dy = DIRECTION_VECTORS[enum_direction].x, DIRECTION_VECTORS[enum_direction].y

        self.arrow_path = []  
        current_arrow_x = self.agent_pos[0] + dx
        current_arrow_y = self.agent_pos[1] + dy

        while 0 <= current_arrow_x < GRID_SIZE and 0 <= current_arrow_y < GRID_SIZE:
            self.arrow_path.append(Point(current_arrow_x, current_arrow_y))

            cell_content = self.map_state['state'][current_arrow_y][current_arrow_x]

            # Kiểm tra nếu trúng Wumpus
            if 'W' in cell_content:
                self.add_to_log("SCREAM")
                self.game_over_state = 'hit_wumpus_depanding'
                self.hit_wumpus_delay_timer = self.hit_wumpus_delay_duration # Bắt đầu đếm ngược
                    

                # Xóa Wumpus khỏi bản đồ
                self.map_state['state'][current_arrow_y][current_arrow_x].discard('W')

                # Xóa các mùi hôi (Stench) xung quanh vị trí Wumpus vừa bị tiêu diệt
                for off_x, off_y in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    stench_x, stench_y = current_arrow_x + off_x, current_arrow_y + off_y
                    if 0 <= stench_x < GRID_SIZE and 0 <= stench_y < GRID_SIZE:
                        self.map_state['state'][stench_y][stench_x].discard('S')
                
                break

            current_arrow_x += dx
            current_arrow_y += dy

        self.start_arrow_animation(self.agent_direction, self.arrow_path)

    def handle_input(self):
        if self.game_over_state:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    if hasattr(self.app, 'quit'):
                        self.app.quit()
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
                        self.trigger_grab_animation()  
                        self.map_state['state'][y][x].discard('G')
                        
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if self.has_arrow:
                        self.trigger_shoot_animation()  

                elif event.key == pygame.K_ESCAPE:
                    if self.agent_pos == [0, 0]:
                        if self.has_gold:
                            self.score += 1000

                        self.start_game_over_video('climb out')

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
        if self.game_over_state and self.game_over_state not in ['hit_wumpus_depanding']:
            if self.video_capture:
                # Thời gian chờ giữa các frame video
                time_per_frame = 1.0 / self.video_fps
                self.video_frame_timer += dt

                # Nếu đã đến lúc hiển thị frame tiếp theo
                if self.video_frame_timer >= time_per_frame:
                    self.video_frame_timer -= time_per_frame
                    
                    success, frame = self.video_capture.read()

                    if success:
                        resized_frame = cv2.resize(frame, self.video_display_size)
                        # CV2 đọc frame ở định dạng BGR, Pygame cần RGB.
                        frame_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                        # Frame của CV2 là (height, width), cần xoay để thành (width, height) cho Pygame
                        frame_pygame = frame_rgb.transpose([1, 0, 2])
                        # Tạo Surface Pygame từ mảng numpy
                        self.current_video_frame = pygame.surfarray.make_surface(frame_pygame)
                    else:
                        # Video đã kết thúc
                        self.video_capture.release() 
                        self.video_capture = None

                        if self.game_over_state in self.terminating_states:
                            self.app.switch_screen(MenuScreen(self.app))
                            self.running = False
                        else:
                            self.game_over_state = None
                            self.current_video_frame = None 
            
            # Xử lý trường hợp video bị lỗi
            elif self.game_over_state == 'error':
                self.game_over_timer += dt
                if self.game_over_timer >= self.game_over_duration:
                    self.app.switch_screen(MenuScreen(self.app))
                    self.running = False

            return 

        if self.game_over_state == 'hit_wumpus_depanding':
            self.hit_wumpus_delay_timer -= dt
            if self.hit_wumpus_delay_timer <= 0:
                self.start_game_over_video('scream')

        if self.is_moving:
            self.move_progress += dt / self.move_duration
            
            if self.move_progress >= 1.0:
                self.is_moving = False
                self.agent_pix_pos = self.move_target_pix_pos[:] # Snap vào vị trí cuối cùng
                self.add_to_log(f"Move to ({self.agent_pos[0]}, {self.agent_pos[1]})")

                self.visited_cells.add(tuple(self.agent_pos))

                self.check_consequences()
            else:
                px = self.move_start_pix_pos[0] + (self.move_target_pix_pos[0] - self.move_start_pix_pos[0]) * self.move_progress
                py = self.move_start_pix_pos[1] + (self.move_target_pix_pos[1] - self.move_start_pix_pos[1]) * self.move_progress
                self.agent_pix_pos = [px, py]

        # Update animation
        self.update_animations(dt)

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
        title_text = title_font.render("PLAYER MODE", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.width / 2, 40))
        
        self.app.screen.blit(title_text, title_rect)
        
        self.draw_game_area()
        self.draw_ui_panel()

        if self.game_over_state:
            self.draw_game_over_video()
        
        pygame.display.flip()

    def run(self):
        self.running = True
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            self.handle_input()

            self.update(dt)

            self.render()

        