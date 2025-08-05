import pygame
import os

from gui.screens.screen import Screen
# from gui.ui.button import Button

# --- Layout Constants ---
GRID_SIZE = 8
CELL_SIZE = 80 # Increased cell size for better visibility
GAME_AREA_WIDTH = GRID_SIZE * CELL_SIZE
UI_PANEL_WIDTH = GAME_AREA_WIDTH // 3 # UI panel is 1/3 of the game area
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
        
        self.turning = False
        self.turn_timer = 0.0
        self.turn_duration = 0.2  # seconds
        self.turn_mid_frame = None
        self.next_direction = None


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
            if self.agent_anim_timer >= 0.1:
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

    def move_agent(self, dx, dy):
        """Moves the agent by dx, dy on the grid if the move is valid."""
        new_x = self.agent_pos[0] + dx
        new_y = self.agent_pos[1] + dy
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            self.agent_pos = [new_x, new_y]
            self.agent_pix_pos = self.get_pixel_pos_from_grid(new_x, new_y)
            self.add_to_log(f"Moved to ({new_x}, {new_y})")

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
        """Draws the UI panel on the right side of the screen."""
        panel_rect = pygame.Rect(GAME_AREA_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, (220, 220, 240), panel_rect) # Light grey background

        # --- Action Log Section ---
        log_title = self.ui_font_title.render("Action Log", True, (0,0,0))
        self.screen.blit(log_title, (GAME_AREA_WIDTH + 20, 20))

        # Display log entries
        log_y_start = 60
        for i, entry in enumerate(self.action_log[-25:]): # Show last 25 entries
            log_text = self.ui_font_log.render(entry, True, (50, 50, 50))
            self.screen.blit(log_text, (GAME_AREA_WIDTH + 20, log_y_start + i * 20))

    def add_to_log(self, message):
        """Adds a message to the action log."""
        self.action_log.append(message)
        if len(self.action_log) > 100: # Keep the log from getting too long
            self.action_log.pop(0)

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                if hasattr(self.app, 'quit'):
                    self.app.quit()


    def update(self, dt):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        desired_dir = None
        self.is_moving = False

        if keys[pygame.K_UP]:
            desired_dir = 'up'
            dy = 1
        elif keys[pygame.K_DOWN]:
            desired_dir = 'down'
            dy = -1
        elif keys[pygame.K_LEFT]:
            desired_dir = 'left'
            dx = -1
        elif keys[pygame.K_RIGHT]:
            desired_dir = 'right'
            dx = 1

        # Handle turning before movement
        if desired_dir and desired_dir != self.agent_direction and not self.turning:
            self.turning = True
            self.turn_timer = 0.0
            self.turn_mid_frame = self.get_turn_transition_frame(self.agent_direction, desired_dir)
            self.next_direction = desired_dir
            self.is_moving = False
        elif not self.turning and desired_dir:
            # Already facing the right direction → allow movement
            self.is_moving = True
            self.move_timer += 1
            if self.move_timer >= self.move_delay:
                self.move_agent(dx, dy)
                self.move_timer = 0
        else:
            # Reset move timer if no key is pressed
            self.move_timer = self.move_delay

        self.update_animations(dt)

    def render(self):
        self.screen.fill((190, 212, 184))
        self.draw_game_area()
        self.draw_ui_panel()
    

