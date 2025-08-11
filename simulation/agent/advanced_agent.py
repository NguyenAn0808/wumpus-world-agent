from .hybrid_agent import HybridAgent
from simulation import *
from collections import deque
from heapq import heappush, heappop
from config import *

class AdvancedAgent(HybridAgent):
    """
    An agent that operates in two modes:
    1. Static Mode: Behaves exactly like a HybridAgent until the Wumpus first moves.
    2. Dynamic Mode: Activates after the first Wumpus movement, using
       heuristic risk assessment to navigate the dynamic environment.
    """

    def __init__(self, location, direction, size):
        super().__init__(location, direction, size)
        self.action_count = 0
        self.percepts_at: dict[Point, set[Percept]] = {}
        self.RISK_WEIGHT = 10

        # --- CỜ TRẠNG THÁI CHẾ ĐỘ ---
        self.dynamic_mode_activated = False
        self.highly_suspicious_cells: set[Point] = set() 
        
        # --- CƠ CHẾ CHỐNG LẶP (chỉ dùng ở chế độ động) ---
        self.recently_retreated_from: Point = None
        self.retreat_cooldown_timer = 0
        self.RETREAT_COOLDOWN = 3 

    def after_action(self):
        """Tăng biến đếm và giảm cooldown sau mỗi hành động."""
        self.action_count += 1
        if self.retreat_cooldown_timer > 0:
            self.retreat_cooldown_timer -= 1
            if self.retreat_cooldown_timer == 0:
                print(f"Cooldown for {self.recently_retreated_from} has ended.")
                self.recently_retreated_from = None

    def update_percepts(self, percepts: set[Percept]):
        """Ghi lại percepts của ô đã thăm, rồi để Hybrid xử lý bình thường."""
        self.percepts_at[self.location] = set(percepts)
        super().update_percepts(percepts)

    def need_wumpus_move(self) -> bool:
        """Kiểm tra xem Wumpus có sắp di chuyển không."""
        return self.action_count > 0 and (self.action_count + 1) % WUMPUS_MOVE_INTERVAL == 0

    def activate_dynamic_mode(self):
        """Kích hoạt chế độ động khi Wumpus di chuyển lần đầu."""
        if not self.dynamic_mode_activated:
            print("\n!!! WUMPUS IS MOVING! AGENT IS ACTIVATING DYNAMIC MODE !!!\n")
            self.dynamic_mode_activated = True

    def reset_wumpus_knowledge(self):
        """
        "Soft Reset": Chuyển các Wumpus đã biết thành các ô "nghi ngờ cao độ"
        thay vì xóa sạch.
        """
        if self.dynamic_mode_activated:
            print("--- Wumpus may have moved! Downgrading proven wumpuses to highly suspicious. ---")
            
            # Chuyển tất cả các Wumpus đã chứng minh vào danh sách nghi ngờ
            self.highly_suspicious_cells.update(self.proven_wumpuses)
            
            # Xóa danh sách Wumpus đã chứng minh (vì không còn chắc chắn 100%)
            self.proven_wumpuses.clear()
            
            self.needs_full_rethink = True

    def get_heuristic_risk_score(self, cell: Point) -> float:
        """
        Tính điểm rủi ro heuristic, có tính đến các ô "nghi ngờ cao độ".
        """
        if cell == self.recently_retreated_from:
            return 500.0
        
        # --- THÊM KIỂM TRA "TRÍ NHỚ MỜ DẦN" ---
        # Nếu một ô hoặc hàng xóm của nó nằm trong danh sách nghi ngờ cao độ,
        # rủi ro của nó sẽ tăng vọt.
        wumpus_memory_risk = 0
        if cell in self.highly_suspicious_cells:
            wumpus_memory_risk = 400 # Phạt rất nặng nếu chính nó là ô bị nghi ngờ
        else:
            for neighbor, _ in self.get_neighbors(cell):
                if neighbor in self.highly_suspicious_cells:
                    wumpus_memory_risk = 200 # Phạt nặng nếu nó ở gần một ô bị nghi ngờ
                    break

        # ... (logic tính điểm heuristic cũ giữ nguyên) ...
        if cell in self.visited_cells or cell in self.safe_cells:
            pit_score = 0
        else:
            # ... (tính pit_score như cũ) ...
            pit_score = 0
            safety_score_pit = 0
            for neighbor_pos, _ in self.get_neighbors(cell):
                if neighbor_pos in self.visited_cells:
                    neighbor_percepts = self.percepts_at.get(neighbor_pos, set())
                    if Percept.BREEZE in neighbor_percepts: pit_score += 150
                    else: safety_score_pit += 75
            pit_score = max(0, pit_score - safety_score_pit)

        wumpus_score = 0
        safety_score_wumpus = 0
        for neighbor_pos, _ in self.get_neighbors(cell):
            if neighbor_pos in self.visited_cells:
                neighbor_percepts = self.percepts_at.get(neighbor_pos, set())
                if Percept.STENCH in neighbor_percepts: wumpus_score += 100
                else: safety_score_wumpus += 50
        wumpus_score = max(0, wumpus_score - safety_score_wumpus)

        escape_routes = sum(1 for neighbor, _ in self.get_neighbors(cell) if neighbor in self.visited_cells)
        escape_bonus = escape_routes * 5
        
        # Tổng rủi ro = Rủi ro từ trí nhớ + Rủi ro từ cảm biến hiện tại
        total_risk = (pit_score * 1.2 + wumpus_score + wumpus_memory_risk) - escape_bonus
        return max(0, total_risk)
    
    def find_least_risky_frontier_cell(self) -> Point:
        """Tìm ô biên chưa thăm có rủi ro heuristic thấp nhất."""
        uncertain_cells = self.get_uncertain_cells()
        if not uncertain_cells:
            return None
        
        best_cell = min(uncertain_cells, key=lambda c: self.get_heuristic_risk_score(c))
        
        # Chỉ đi vào nếu rủi ro không quá lớn (ví dụ < 200)
        if self.get_heuristic_risk_score(best_cell) < 200:
            return best_cell
        return None
    
    def find_closest_safe_haven(self) -> Point:
        """Tìm ô đã thăm gần nhất để làm nơi trú ẩn."""
        possible_havens = self.visited_cells - {self.location}
        if not possible_havens: return None
        return min(possible_havens, key=lambda p: abs(p.x - self.location.x) + abs(p.y - self.location.y))

    def explore_with_astar(self, goals: set[Point]):
        """A* tìm đường, có tính đến rủi ro nếu ở chế độ động."""
        if self.planned_action or not goals: return

        start_node = (self.location, self.direction)
        count = 0
        frontier = [(self.calculate_heuristic(self.location, list(goals)), 0, count, start_node, [])]
        visited_states = {start_node: 0}

        while frontier:
            _, g_cost, _, current_state, actions = heappop(frontier)
            current_pos, current_dir = current_state

            if current_pos in goals:
                self.planned_action.extend(actions)
                return

            for action in [Action.MOVE_FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT]:
                new_pos, new_dir = current_pos, current_dir
                
                if action == Action.MOVE_FORWARD:
                    next_cell = current_pos + DIRECTION_VECTORS[current_dir]
                     # Logic di chuyển của Hybrid (chế độ tĩnh)
                    can_move_static = is_valid(next_cell, self.map_size) and \
                                      (next_cell in goals or \
                                       next_cell in self.safe_cells or \
                                       next_cell in self.visited_cells)
                    
                    # Logic di chuyển của Advanced (chế độ động)
                    can_move_dynamic = is_valid(next_cell, self.map_size) and \
                                       next_cell not in self.proven_pits

                    if (self.dynamic_mode_activated and not can_move_dynamic) or \
                       (not self.dynamic_mode_activated and not can_move_static):
                        continue
                    
                    new_pos = next_cell
                elif action == Action.TURN_LEFT: new_dir = TURN_LEFT_MAP[current_dir]
                elif action == Action.TURN_RIGHT: new_dir = TURN_RIGHT_MAP[current_dir]
                
                move_cost = 1
                # CHỈ TÍNH RỦI RO KHI Ở CHẾ ĐỘ ĐỘNG
                if self.dynamic_mode_activated:
                    move_cost += self.get_heuristic_risk_score(new_pos) * self.RISK_WEIGHT
                
                new_g_cost = g_cost + move_cost
                new_state = (new_pos, new_dir)

                if new_state not in visited_states or new_g_cost < visited_states[new_state]:
                    visited_states[new_state] = new_g_cost
                    h_cost = self.calculate_heuristic(new_pos, list(goals))
                    f_cost = new_g_cost + h_cost
                    new_actions = actions + [action]
                    count += 1
                    heappush(frontier, (f_cost, new_g_cost, count, new_state, new_actions))

    def choose_next_decision(self, kb: KB, inference: InferenceEngine):
        """
        Hàm quyết định chính, sẽ gọi logic của Hybrid hoặc logic Nâng cao
        tùy thuộc vào trạng thái `dynamic_mode_activated`.
        """
        if self.planned_action: return

        # Nếu chế độ động chưa được kích hoạt, hoạt động như HybridAgent
        if not self.dynamic_mode_activated:
            print("--- Operating in Static Mode (behaving like HybridAgent) ---")
            # Gọi trực tiếp hàm choose_next_decision của lớp cha (HybridAgent)
            super().choose_next_decision(kb, inference)
            return

        # --- TỪ ĐÂY TRỞ ĐI LÀ LOGIC CỦA CHẾ ĐỘ ĐỘNG ---
        print("--- Operating in Dynamic Mode (using heuristic risk assessment) ---")
        
        # Chiến lược rút lui khi Wumpus sắp di chuyển
        if self.action_count > 0 and (self.action_count + 1) % WUMPUS_MOVE_INTERVAL == 0:
            is_in_dangerous_area = any(self.get_heuristic_risk_score(n) > 50 for n, _ in self.get_neighbors(self.location))
            if is_in_dangerous_area:
                safe_haven = self.find_closest_safe_haven()
                if safe_haven and safe_haven != self.location:
                    print(f"Plan: Wumpus will move next. Retreating from {self.location} to safe haven {safe_haven}.")
                    self.recently_retreated_from = self.location
                    self.retreat_cooldown_timer = self.RETREAT_COOLDOWN
                    self.explore_with_astar({safe_haven})
                    if self.planned_action: return
                else:
                    print("Plan: Wumpus will move next, but no safe place to retreat. Stalling.")
                    self.planned_action.append(Action.TURN_LEFT)
                    return

        # Flow logic ưu tiên của chế độ động
        if Percept.GLITTER in self.current_percepts and not self.has_gold:
            self.planned_action.append(Action.GRAB)
            return
        if self.has_gold:
            self.explore_with_astar({Point(0,0)})
            if not self.planned_action: self.planned_action.append(Action.CLIMB_OUT)
            return
        
        unvisited_safe_cells = self.get_unvisited_safe_cells()
        if unvisited_safe_cells:
            self.explore_with_astar(unvisited_safe_cells)
            if self.planned_action: return
        
        if self.has_arrow:
            if self.decide_safe_shoot_action(kb, inference):
                return
            if not unvisited_safe_cells:
                 self.decide_risky_shoot_action(kb, inference)
                 if self.planned_action: return
        
        target_cell = self.find_least_risky_frontier_cell()
        if target_cell:
            self.explore_with_astar({target_cell})
            if self.planned_action: return

        self.explore_with_astar({Point(0, 0)})
        if not self.planned_action: self.planned_action.append(Action.CLIMB_OUT)