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
    
    def get_unvisited_pit_free_cells(self, kb: KB, inference: InferenceEngine) -> set[Point]:
        pit_free_cells = set()
        
        uncertain_frontier = self.get_uncertain_cells()

        for cell in uncertain_frontier:
            is_pit_negated_literal = Literal(f"P{cell.x}{cell.y}", negated=True)
            
            if inference.ask_Pit(kb.pit_rules, is_pit_negated_literal):
                pit_free_cells.add(cell)
                
        return pit_free_cells
    
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
    
    def decide_risky_shoot_action(self, kb: KB, inference: InferenceEngine):
        """
        There is no decision more -> We have to shoot optimally.
        Option 1: Check which direction has the most supsicious Wumpus squares.  
        (Wumpus) -> (Wumpus, Pit)

        Option 2: Shoot in a random direction which costs the least.
        """
        if self.planned_action or not self.has_arrow:
            return
        
        uncertain_cells = self.get_uncertain_cells()

        primary_cells = set() # Just doubt about Wumpus
        secondary_cells = set() # Doubt about (Wumpus, Pit)

        for cell in uncertain_cells:
            # KB entail alpha => KB ^ not aplha -> true (so if False -> not proven safe)
            is_proven_safe = inference.ask_Wumpus(kb.wumpus_rules, Literal(f"W{cell.x}{cell.y}", negated=True))

            if not (not is_proven_safe): # Safe cell
                continue
            
            is_proven_safe = inference.ask_Pit(kb.pit_rules, Literal(f"P{cell.x}{cell.y}", negated=True))

            is_pit_suspect = not is_proven_safe

            if not is_pit_suspect:
                primary_cells.add(cell) # W
            else:
                secondary_cells.add(cell) # (W, P)
            
        target = primary_cells if primary_cells else secondary_cells

        if not target:
            print("No suitable Wumpus suspects to shoot at.")
            return 
        
        # Best direction to shoot
        direction_count = {d: 0 for d in Direction}

        for cell in target:
            direction = self.get_direction_to_target(cell)
            if direction:
                direction_count[direction] += 1

        max_count = max(direction_count.values()) if direction_count else 0

        shooting_direction = None
        if max_count > 0:
            # Logic cũ: Tìm hướng tốt nhất dựa trên số lượng ô đáng ngờ
            best_directions = [d for d, count in direction_count.items() if count == max_count]
            if len(best_directions) > 1:
                best_directions.sort(key=lambda d: len(self.get_turn_decision(self.direction, d)))
            shooting_direction = best_directions[0]
            print(f"Agent identified best risky shot direction: {shooting_direction.name}")
        else:
            print("No optimal shooting direction found. Random shot regarding to least cost")
        
            possible_shot_directions = []
            for direction, vec in DIRECTION_VECTORS.items():
                if is_valid(self.location + vec, self.map_size):
                    possible_shot_directions.append(direction)

            if not possible_shot_directions:
                print("Agent is completely boxed in by walls. Cannot shoot.")
                return # Không thể bắn

            # Sắp xếp các hướng khả thi theo số lần quay ít nhất
            possible_shot_directions.sort(key=lambda d: len(self.get_turn_decision(self.direction, d)))
            
            # Chọn hướng cần ít lần quay nhất
            shooting_direction = possible_shot_directions[0]
            print(f"Agent will shoot towards {shooting_direction.name} to gather information.")

        if shooting_direction:
            turn_actions = self.get_turn_decision(self.direction, shooting_direction)
            self.planned_action.extend(turn_actions)
            self.planned_action.append(Action.SHOOT)

            print(f"Agent is stuck. Planning a risky shot towards {shooting_direction.name}. Plan: {[a.name for a in self.planned_action]}")

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
        
        print("\n--- AGENT DECISION PROCESS ---")
        print(f"Current safe_cells: {self.safe_cells}")
        print(f"Current visited_cells: {self.visited_cells}")

        # Option 1: Grab gold
        if Percept.GLITTER in self.current_percepts and not self.has_gold:
            self.planned_action.append(Action.GRAB)
            print("Plan: Found Glitter! Grabbing the gold.")
            # Sau khi nhặt, agent sẽ tự động chuyển sang ưu tiên 1 ở lượt sau
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
        print(f"Found unvisited safe cells: {unvisited_safe_cells}")
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
        
            print("Plan: No moves left, even desperate ones. Considering a risky shot.\n") # Option 4.2 (risky shot)
            self.decide_risky_shoot_action(kb, inference)
            if self.planned_action:
                return
        
        # Option 5: Give up - return home
        print("Agent has no other options. Attempting to return home to climb out.\n")
        if self.location != Point(0, 0):
            self.explore_with_astar({Point(0, 0)})
            
        self.planned_action.append(Action.CLIMB_OUT)
        print("Final plan: Climb out.\n")