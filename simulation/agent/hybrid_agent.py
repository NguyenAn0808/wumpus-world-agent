from .agent import Agent
from simulation import *
from collections import deque
from heapq import heappush, heappop

class HybridAgent(Agent):
    def __init__(self, location: Point, direction: Direction, map_size: int):
        super().__init__(location, direction, map_size)
        self.current_percepts: set[Percept] = set()
        self.just_encountered_danger = False
        self.needs_full_rethink = False

        self.safe_cells: set[Point] = {location}
        self.cells_learned_from: set[Point] = {location}

        self.proven_wumpuses: set[Point] = set()
        self.proven_pits: set[Point] = set()

    def reset_internal_wumpus_knowledge(self):
        pass

    def reset_safe_cells(self):
        pass

    def after_action(self):
        pass

    def need_wumpus_move(self):
        pass

    def prepare_for_kb_reset(self, kb, inference):
        pass

    def reground_probabilities_with_percepts(self): 
        pass

    def update_wumpus_probabilities_after_move(self):
        pass
    
    def update_percepts(self, percepts: set[Percept]):
        has_new_danger = (Percept.STENCH in percepts or Percept.BREEZE in percepts) and \
                         not (Percept.STENCH in self.current_percepts or Percept.BREEZE in self.current_percepts)
        
        if has_new_danger:
            self.just_encountered_danger = True

        self.current_percepts = percepts
    
    def update_KB_from_inference(self, new_safe_cells, new_proven_wumpuses, new_proven_pits):
        self.safe_cells.update(new_safe_cells)
        self.proven_wumpuses.update(new_proven_wumpuses)
        self.proven_pits.update(new_proven_pits)

    def get_frontier_cells(self) -> set[Point]:
        return self.frontier_cells

    def get_unvisited_safe_cells(self) -> set[Point]:
        return self.safe_cells - self.visited_cells

    def get_uncertain_cells(self) -> set[Point]:
        return self.get_frontier_cells() - self.safe_cells
    
    def get_direction_to_target(self, target: Point) -> Direction:
        dx, dy = target.x - self.location.x, target.y - self.location.y
        if dx == 0 and dy > 0: return Direction.NORTH
        if dx == 0 and dy < 0: return Direction.SOUTH
        if dy == 0 and dx > 0: return Direction.EAST
        if dy == 0 and dx < 0: return Direction.WEST
        return None
    
    def decide_safe_shoot_action(self, kb: KB, inference: InferenceEngine,) -> bool:
        """
        Function to return True if shoot successfully otherwise False.
        """   
        if not self.has_arrow:
            return False

        frontier_cells = self.get_frontier_cells()

        for cell in frontier_cells:
            if inference.ask_Wumpus(kb.wumpus_rules, Literal(f"W{cell.x}{cell.y}", negated=False)):

                shooting_direction = self.get_direction_to_target(cell)

                if shooting_direction:
                    print(f"Agent has proven Wumpus at {cell}. Planning a safe shot!")
                    turn_actions = self.get_turn_decision(self.direction, shooting_direction)
                    self.planned_action.extend(turn_actions)
                    self.planned_action.append(Action.SHOOT)
                    return True
        
        return False
    
    def calculate_shoot_direction_score(self, direction: Direction, suspicious_cells: set[Point]) -> float:
        """
        Tính điểm cho một hướng bắn dựa trên:
        +1.0 điểm cho mỗi ô đáng ngờ trên đường đạn.
        +0.1 điểm cho mỗi ô chưa khám phá trên đường đạn (thu thập thông tin).
        -0.01 điểm cho mỗi hành động quay người cần thiết.
        """
        score = 0.0
        path_pos = self.location + DIRECTION_VECTORS[direction]
        
        while is_valid(path_pos, self.map_size):
            if path_pos in suspicious_cells:
                score += 1.0  # Điểm cao cho việc bắn vào mục tiêu nghi ngờ
            elif path_pos not in self.visited_cells:
                score += 0.1  # Điểm thưởng nhỏ cho việc khám phá thông tin mới
            
            path_pos += DIRECTION_VECTORS[direction]

        # Trừ điểm chi phí cho việc quay người
        turn_cost = len(self.get_turn_decision(self.direction, direction))
        score -= turn_cost * 0.01
        
        return score
    
    def decide_risky_shoot_action(self, kb: KB, inference: InferenceEngine):
        """
        There is no decision more -> We have to shoot optimally.
        Option 1: Check which direction has the most supsicious Wumpus squares.  
        (Wumpus) -> (Wumpus, Pit)

        Option 2: Shoot in a random direction which costs the least.
        """
        if self.planned_action or not self.has_arrow:
            return False
        
        uncertain_cells = self.get_uncertain_cells()
        suspicious_cells = set()
        for cell in uncertain_cells:
            # Một ô đáng ngờ là ô có thể có Wumpus
            is_wumpus_possible = not inference.ask_Wumpus(kb.wumpus_rules, Literal(f"W{cell.x}{cell.y}", negated=True))
            if is_wumpus_possible:
                suspicious_cells.add(cell)
        
        # --- PHẦN LOGIC LỰA CHỌN HƯỚNG BẮN ĐƯỢC THAY THẾ ---

        if not suspicious_cells:
            print("No suitable Wumpus suspects to shoot at. Considering shooting to explore.")
            # Nếu không có ô nào nghi ngờ có Wumpus, vẫn có thể bắn để dọn đường
            # Mục tiêu lúc này chỉ là thu thập thông tin
            suspicious_cells = set() # Đảm bảo target rỗng

        best_direction = None
        max_score = -float('inf')

        # Duyệt qua tất cả các hướng có thể bắn
        for direction in Direction:
            if not is_valid(self.location + DIRECTION_VECTORS[direction], self.map_size):
                continue # Bỏ qua nếu hướng đó là tường

            # Tính điểm cho hướng hiện tại
            score = 0.0
            path_pos = self.location + DIRECTION_VECTORS[direction]
            
            while is_valid(path_pos, self.map_size):
                if path_pos in suspicious_cells:
                    score += 1.0  # +1.0 điểm cho mỗi ô đáng ngờ
                elif path_pos not in self.visited_cells:
                    score += 0.1  # +0.1 điểm cho mỗi ô chưa khám phá
                
                path_pos += DIRECTION_VECTORS[direction]

            # Trừ điểm chi phí cho việc quay người
            turn_cost = len(self.get_turn_decision(self.direction, direction))
            score -= turn_cost * 0.01
            
            # Cập nhật hướng tốt nhất
            if score > max_score:
                max_score = score
                best_direction = direction

        # Chỉ bắn nếu tìm thấy một hướng có lợi (điểm > 0)
        if best_direction and max_score > 0:
            print(f"Agent identified best risky shot direction: {best_direction.name} with score {max_score:.2f}")
            turn_actions = self.get_turn_decision(self.direction, best_direction)
            self.planned_action.extend(turn_actions)
            self.planned_action.append(Action.SHOOT)
            return True
        else:
            # Fallback: Nếu không có hướng nào có lợi, bắn theo hướng tốn ít lượt quay nhất để lấy thông tin
            print("No beneficial direction found. Shooting towards least-cost direction for info.")
            possible_shot_directions = [d for d, v in DIRECTION_VECTORS.items() if is_valid(self.location + v, self.map_size)]
            if not possible_shot_directions:
                print("Agent is completely boxed in by walls. Cannot shoot.")
                return False
            
            possible_shot_directions.sort(key=lambda d: len(self.get_turn_decision(self.direction, d)))
            shooting_direction = possible_shot_directions[0]
            
            turn_actions = self.get_turn_decision(self.direction, shooting_direction)
            self.planned_action.extend(turn_actions)
            self.planned_action.append(Action.SHOOT)
            return True
        
    def calculate_heuristic(self, pos: Point, goals: list) -> int:
        if not goals: 
            return float('inf')
        return min(abs(pos.x - g.x) + abs(pos.y - g.y) for g in goals)
    
    def explore_with_astar(self, goals: set[Point]):
        if self.planned_action or not goals:
            return

        start_node = (self.location, self.direction)
        
        # Thêm một bộ đếm để phá vỡ thế cân bằng
        count = 0
        
        # (f_cost, g_cost, count, (location, direction), actions)
        # Thêm `count` vào tuple
        frontier = [(self.calculate_heuristic(self.location, goals), 0, count, start_node, [])]
        
        visited_states = {start_node: 0}

        while frontier:
            # Lấy các giá trị ra, bao gồm cả count (nhưng không cần dùng)
            _, g_cost, _, current_state, actions = heappop(frontier)
            current_pos, current_dir = current_state

            if current_pos in goals:
                self.planned_action.extend(actions)
                print(f"A* found a path to {current_pos}. Plan: {[a.name for a in self.planned_action]}")
                return

            possible_actions = [Action.MOVE_FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT]

            for action in possible_actions:
                new_g_cost = g_cost + 1
                new_pos, new_dir = current_pos, current_dir
                
                if action == Action.MOVE_FORWARD:
                    next_cell = current_pos + DIRECTION_VECTORS[current_dir]
                    can_move = is_valid(next_cell, self.map_size) and \
                               (next_cell in goals or \
                                next_cell in self.safe_cells or next_cell in self.visited_cells)
                    
                    if can_move:
                        new_pos = next_cell
                    else:
                        continue
                
                elif action == Action.TURN_LEFT:
                    new_dir = TURN_LEFT_MAP[current_dir]

                elif action == Action.TURN_RIGHT:
                    new_dir = TURN_RIGHT_MAP[current_dir]

                new_state = (new_pos, new_dir)
                if new_state not in visited_states or new_g_cost < visited_states[new_state]:
                    visited_states[new_state] = new_g_cost
                    h_cost = self.calculate_heuristic(new_pos, goals)
                    f_cost = new_g_cost + h_cost
                    new_actions = actions + [action]
                    
                    # Tăng bộ đếm mỗi khi thêm một phần tử mới
                    count += 1
                    # Thêm `count` vào tuple khi push vào heap
                    heappush(frontier, (f_cost, new_g_cost, count, new_state, new_actions))

        print(f"A* could not find a path to any of {goals}.")

    def process_scream(self, shot_path: list[Point]):
        self.needs_full_rethink = True
        self.planned_action.clear()
        
    def find_safe_cells(self, kb: KB, inference: InferenceEngine) -> set[Point]:
        """"
        Function to find safe cells from uncertain cells
        """
        safe = set()
        uncertain_cells = self.get_uncertain_cells()

        for cell in uncertain_cells:
            if cell not in self.safe_cells:
                is_safe = inference.ask_safe(kb.wumpus_rules, kb.pit_rules, cell)
                if is_safe:
                    safe.add(cell)

        return safe
    
    def choose_next_decision(self, kb: KB, inference: InferenceEngine):
        """
        Chooses the next best safe unvisited move. Shoot if no safe unvisited cell
        Prioritizes shortest safe path via A*.
        """
        
        if self.planned_action:
            return
    
        # Option 1: Grab gold
        if Percept.GLITTER in self.current_percepts and not self.has_gold:
            self.planned_action.append(Action.GRAB)
            print("Plan: Found Glitter! Grabbing the gold.")
            return
        
        # Option 2: Process Gold
        if self.has_gold:
            if self.location == Point(0, 0):
                self.planned_action.append(Action.CLIMB_OUT)  
                print("Plan: Climb out with gold!\n")
                return
            else:
                print("Agent has gold. Planning path to home (0,0).\n")
                self.explore_with_astar({Point(0,0)}) # Go home

                if self.planned_action:
                    return
        
        # Option 3: Find safe cells and then discover it
        unvisited_safe_cells = self.get_unvisited_safe_cells()
        if unvisited_safe_cells:
            print(f"Plan: Exploring safe unvisited cells: {unvisited_safe_cells}\n")
            self.explore_with_astar(unvisited_safe_cells)
            if self.planned_action:
                return

        # Option 4: Shoot arrow
        if self.has_arrow:
            if self.decide_safe_shoot_action(kb, inference): # Option 4.1 (Shoot safely)
                print("Plan: Confirmed Wumpus. Executing safe shot.\n")
                return 
        
            if not unvisited_safe_cells:
                if self.decide_risky_shoot_action(kb, inference):
                    print("Plan: No safe moves. Executing risky shot.")
                    return # Đã có kế hoạch bắn, chờ kết quả ở lượt sau
        
        # Option 5: Give up - return home
        print("Agent has no other options. Attempting to return home to climb out.\n")
        if self.location != Point(0, 0):
            self.explore_with_astar({Point(0, 0)})
            
        self.planned_action.append(Action.CLIMB_OUT)
        print("Final plan: Climb out.\n")