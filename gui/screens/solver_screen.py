import pygame
from gui.screens.screen import Screen
from simulation import *


DIRECTION_TO_ANIMATION = {
    'north': 'up',
    'south': 'down',
    'east': 'right',
    'west': 'left',
}


def add_percept_rules_to_kb(kb: KB, world: World, point: Point):
    """
    "Học" các luật chơi: Chỉ thêm các luật liên quan đến percept
    tại vị trí hiện tại vào KB.
    Hàm này chỉ được gọi một lần cho mỗi ô đã ghé thăm.
    """
    x, y = point.x, point.y
    adj_cells = world.get_adjacent_cells(point)

    # Nếu có các ô hàng xóm, thì mới có luật cho Breeze/Stench
    if not adj_cells:
        return

    # Tạo và thêm luật cho Breeze tại (x,y)
    breeze_literal_str = f"B{x}{y}"
    pit_literal_strs = [f"P{p.x}{p.y}" for p in adj_cells]
    pit_rules = KB.conversion_to_CNF(breeze_literal_str, pit_literal_strs)
    kb.tell(pit_rules, is_wumpus_rule=False)
    print(f"-> Agent learned the rule for Breeze at ({x},{y}).")

    # Tạo và thêm luật cho Stench tại (x,y)
    stench_literal_str = f"S{x}{y}"
    wumpus_literal_strs = [f"W{p.x}{p.y}" for p in adj_cells]
    wumpus_rules = KB.conversion_to_CNF(stench_literal_str, wumpus_literal_strs)
    kb.tell(wumpus_rules, is_wumpus_rule=True)
    print(f"-> Agent learned the rule for Stench at ({x},{y}).")

def update_kb_with_facts(kb: KB, world: World, point: Point):
    """
    Cập nhật KB với các sự thật (facts) từ vị trí hiện tại:
    1. Ô hiện tại chắc chắn an toàn.
    2. Các percept cảm nhận được.
    """
    x, y = point.x, point.y
    
    # Fact 1: Agent biết ô nó đang đứng là an toàn.
    kb.tell_fact(Literal(f"P{x}{y}", negated=True))
    kb.tell_fact(Literal(f"W{x}{y}", negated=True))
    print(f"-> Added fact: Cell ({x},{y}) is visited and safe (¬P{x}{y}, ¬W{x}{y}).")

    # Fact 2: Agent cảm nhận môi trường và thêm facts.
    percepts = world.get_percepts()
    
    if Percept.BREEZE in percepts:
        kb.tell_fact(Literal(f"B{x}{y}", negated=False))
        print(f"-> Added fact: Perceived a Breeze at ({x},{y}) (B{x}{y}).")
    else:
        kb.tell_fact(Literal(f"B{x}{y}", negated=True))
        print(f"-> Added fact: No Breeze at ({x},{y}) (¬B{x}{y}).")

    if Percept.STENCH in percepts:
        kb.tell_fact(Literal(f"S{x}{y}", negated=False))
        print(f"-> Added fact: Perceived a Stench at ({x},{y}) (S{x}{y}).")
    else:
        kb.tell_fact(Literal(f"S{x}{y}", negated=True))
        print(f"-> Added fact: No Stench at ({x},{y}) (¬S{x}{y}).")

def infer_cell_status(kb: KB, inference_engine: InferenceEngine, cells_to_check: list[Point]) -> dict[Point, CellStatus]:
    """
    Suy luận trạng thái của các ô (An toàn, Nguy hiểm, Không chắc chắn).
    Trả về một dictionary: Point -> CellStatus.
    """
    print("\n" + "="*50)
    print("AGENT IS INFERRING THE STATUS OF UNVISITED, ADJACENT CELLS")
    print("="*50)
    
    cell_statuses = {}
    
    for cell in cells_to_check:
        x, y = cell.x, cell.y
        print(f"\n--- Querying for cell ({x},{y}) ---")
        
        # --- KIỂM TRA AN TOÀN ---
        # Hỏi: KB |= ¬Pxy ?
        query_not_pit = Literal(f"P{x}{y}", negated=True)
        is_not_pit = inference_engine.ask_Pit(kb.pit_rules, query_not_pit)
        print(f"  - Asking if NOT a Pit (KB |= ¬P{x}{y}): {is_not_pit}")
        
        # Hỏi: KB |= ¬Wxy ?
        query_not_wumpus = Literal(f"W{x}{y}", negated=True)
        is_not_wumpus = inference_engine.ask_Wumpus(kb.wumpus_rules, query_not_wumpus)
        print(f"  - Asking if NOT a Wumpus (KB |= ¬W{x}{y}): {is_not_wumpus}")

        if is_not_pit and is_not_wumpus:
            cell_statuses[cell] = CellStatus.SAFE
            print(f"  => RESULT: {CellStatus.SAFE.value}")
            continue # Đã xác định là an toàn, chuyển sang ô tiếp theo

        # --- NẾU KHÔNG AN TOÀN, KIỂM TRA NGUY HIỂM ---
        # Hỏi: KB |= Pxy ?
        query_is_pit = Literal(f"P{x}{y}", negated=False)
        is_pit = inference_engine.ask_Pit(kb.pit_rules, query_is_pit)
        print(f"  - Asking if IS a Pit (KB |= P{x}{y}): {is_pit}")
        if is_pit:
            cell_statuses[cell] = CellStatus.DANGEROUS_PIT
            print(f"  => RESULT: {CellStatus.DANGEROUS_PIT.value}")
            continue

        # Hỏi: KB |= Wxy ?
        query_is_wumpus = Literal(f"W{x}{y}", negated=False)
        is_wumpus = inference_engine.ask_Wumpus(kb.wumpus_rules, query_is_wumpus)
        print(f"  - Asking if IS a Wumpus (KB |= W{x}{y}): {is_wumpus}")
        if is_wumpus:
            cell_statuses[cell] = CellStatus.DANGEROUS_WUMPUS
            print(f"  => RESULT: {CellStatus.DANGEROUS_WUMPUS.value}")
            continue

        # --- NẾU KHÔNG RƠI VÀO CÁC TRƯỜNG HỢP TRÊN ---
        cell_statuses[cell] = CellStatus.UNCERTAIN
        print(f"  => RESULT: {CellStatus.UNCERTAIN.value}")
            
    return cell_statuses

class SolverScreen(Screen):
    def __init__(self, app, mode, map_state, world : World):
        super().__init__(app)
        self.mode = mode
        self.map_state = map_state
        self.running = True
        infoObject = pygame.display.Info()
        screen_width = infoObject.current_w
        screen_height = infoObject.current_h - 55

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
        self.logs = self.generate_logs()
        self.log_scroll = 0
        
        # Agent reasoning setup
        self.kb = KB()
        self.inference_engine = InferenceEngine()
        self.world_obj = world
        self.current_location = Point(self.agent_x, self.agent_y)
        self.cell_statuses = {}
        self.auto_solve_delay = 1.0  # seconds per step
        self.auto_solve_timer = 0.0
        self.visited = {self.current_location}  # track visited points


        # First reasoning cycle
        add_percept_rules_to_kb(self.kb, self.world_obj, self.current_location)
        update_kb_with_facts(self.kb, self.world_obj, self.current_location)
        self.cell_statuses = infer_cell_status(
            self.kb, self.inference_engine, 
            self.world_obj.get_adjacent_cells(self.current_location)
        )

        # Add reasoning results to logs
        for cell, status in self.cell_statuses.items():
            self.logs.append(f"Inferred: ({cell.x},{cell.y}) → {status.value}")

    def choose_next_safe_cell(self):
        for cell, status in self.cell_statuses.items():
            if status == CellStatus.SAFE and cell not in self.visited:
                return cell
        return None

    def auto_solve_step(self):
        # 1. Add percept rules and facts
        add_percept_rules_to_kb(self.kb, self.world_obj, self.current_location)
        update_kb_with_facts(self.kb, self.world_obj, self.current_location)

        # 2. Infer
        adjacent = self.world_obj.get_adjacent_cells(self.current_location)
        self.cell_statuses = infer_cell_status(self.kb, self.inference_engine, adjacent)

        # 3. Log new inferences
        for cell, status in self.cell_statuses.items():
            log = f"Inferred: ({cell.x},{cell.y}) → {status.value}"
            if log not in self.logs:
                self.logs.append(log)

        # 4. Pick next safe move
        next_cell = self.choose_next_safe_cell()
        if next_cell:
            # 5. Update agent's location and direction
            dx = next_cell.x - self.current_location.x
            dy = next_cell.y - self.current_location.y

            if dx == 1: self.agent_dir = Direction.EAST
            elif dx == -1: self.agent_dir = Direction.WEST
            elif dy == 1: self.agent_dir = Direction.NORTH
            elif dy == -1: self.agent_dir = Direction.SOUTH

            self.agent_x = next_cell.x
            self.agent_y = next_cell.y
            self.current_location = next_cell
            self.visited.add(next_cell)

            # 6. Update map_state for UI/log
            self.map_state = self.world_obj.get_state()
            self.logs += self.generate_logs()
        else:
            self.logs.append("No more known safe moves.")

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

    def generate_logs(self):
        logs = []
        logs.append(f"Location: ({self.agent_x}, {self.agent_y}) | Direction: {self.agent_dir.name}")
        logs.append(f"Score: {self.map_state['score']}")
        logs.append(f"Has Arrow: {'Yes' if self.map_state['agent_has_arrow'] else 'No'}")
        logs.append(f"Has Gold: {'Yes' if self.map_state['agent_has_gold'] else 'No'}")
        percepts = self.map_state.get('percepts', set())
        percept_names = [p.name if hasattr(p, 'name') else str(p) for p in percepts]
        logs.append("Percepts: " + ", ".join(percept_names))
        message = self.map_state.get('message', '')
        if message:
            logs.append("Message: " + message)
        if self.map_state['game_over']:
            logs.append("!!! GAME OVER !!!")
        return logs

    def draw_log_box(self):
        box_rect = pygame.Rect(540, 360, 240, 220)
        pygame.draw.rect(self.screen, (30, 30, 30), box_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), box_rect, 2)
        visible_lines = 10
        for i in range(visible_lines):
            idx = self.log_scroll + i
            if idx < len(self.logs):
                text = self.log_font.render(self.logs[idx], True, (255, 255, 255))
                self.screen.blit(text, (box_rect.x + 10, box_rect.y + 10 + i * 20))

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
        # Auto-solve timer
        self.auto_solve_timer += dt
        if self.auto_solve_timer >= self.auto_solve_delay and not self.map_state['game_over']:
            self.auto_solve_timer = 0.0
            self.auto_solve_step()
        
    def run(self):
        while self.running:
            self.handle_input()
            self.render()
        pygame.quit()