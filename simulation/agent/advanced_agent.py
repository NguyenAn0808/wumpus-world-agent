from .hybrid_agent import HybridAgent
from simulation import *
from collections import deque
from heapq import heappush, heappop
from config import *

class AdvancedAgent(HybridAgent):
    """
    Advanced Agent giống HybridAgent nâng cấp
    """

    def __init__(self, location, direction, size):
        super().__init__(location, direction, size)
        self.action_count = 0
        self.last_known_threats: set[Point] = set()

        self.wumpus_probabilities = {}
        self.number_of_wumpus_alive = NUMBER_OF_WUMPUS

        self.RISK_WEIGHT = 10 

        self.setup_wumpus_prob()

    def setup_wumpus_prob(self):
        possible_wumpus_cells = self.map_size * self.map_size - 1
        if possible_wumpus_cells > 0:
            initial_prob = self.number_of_wumpus_alive / possible_wumpus_cells

            for x in range(self.map_size):
                for y in range(self.map_size):
                    pos = Point(x, y)
                    if pos == INITIAL_AGENT_LOCATION:
                        self.wumpus_probabilities[pos] = 0.0
                    else:
                        self.wumpus_probabilities[pos] = initial_prob

    def process_scream(self, shot_path: list[Point]):
        """Xử lý khi nghe thấy tiếng hét: 1 Wumpus chết, cập nhật xác suất."""
        print("Advanced Agent heard a scream! A Wumpus is dead.")
        self.number_of_wumpus_alive -= 1
        
        # Wumpus chắc chắn không còn trên đường đạn
        for pos in shot_path:
            self.wumpus_probabilities[pos] = 0.0
            
        # Xóa các sự thật về Stench cũ vì một nguồn Stench đã biến mất
        # Đây là một bước đơn giản hóa, một hệ thống phức tạp hơn sẽ suy luận lại
        self.needs_full_rethink = True
        self.planned_action.clear()
        self.normalize_probabilities()

    def normalize_probabilities(self):
        """
        Đảm bảo tổng xác suất bằng số Wumpus còn sống,
        đồng thời giữ nguyên xác suất 1.0 cho các Wumpus đã được chứng minh.
        """
        
        # Cố định xác suất của các Wumpus đã biết
        num_proven = len(self.proven_wumpuses)
        prob_sum_for_proven = 0
        for pos in self.proven_wumpuses:
            self.wumpus_probabilities[pos] = 1.0
            prob_sum_for_proven += 1.0

        # Tính tổng xác suất của các ô chưa biết
        unknown_cells = [p for p in self.wumpus_probabilities if p not in self.proven_wumpuses]
        total_prob_unknown = sum(self.wumpus_probabilities[p] for p in unknown_cells)
        
        # Số Wumpus còn lại để phân bổ cho các ô chưa biết
        remaining_wumpus_to_distribute = self.number_of_wumpus_alive - num_proven

        if remaining_wumpus_to_distribute < 0:
             print(f"WARNING: More proven wumpuses ({num_proven}) than wumpuses alive ({self.number_of_wumpus_alive}). KB is inconsistent.")
             # Trong trường hợp này, tin vào bằng chứng logic
             remaining_wumpus_to_distribute = 0

        if total_prob_unknown > 1e-6:
            factor = remaining_wumpus_to_distribute / total_prob_unknown
            for pos in unknown_cells:
                self.wumpus_probabilities[pos] *= factor
        # Nếu tổng xác suất các ô chưa biết = 0, phân bổ đều
        elif unknown_cells and remaining_wumpus_to_distribute > 0:
            prob_per_cell = remaining_wumpus_to_distribute / len(unknown_cells)
            for pos in unknown_cells:
                self.wumpus_probabilities[pos] = prob_per_cell

    def reground_probabilities_with_percepts(self):
        """Tinh chỉnh lại bản đồ xác suất dựa trên cảm biến Stench tại vị trí hiện tại."""
        print(f"Agent at {self.location} regrounding probabilities with percepts: {self.current_percepts}")
        current_pos = self.location
        neighbors = [n for n, _ in self.get_neighbors(current_pos)]

        # TH1: Không có Stench
        if Percept.STENCH not in self.current_percepts:
            for neighbor in neighbors:
                # CHỈ CẬP NHẬT NẾU CHƯA CÓ BẰNG CHỨNG LOGIC
                if neighbor not in self.proven_wumpuses:
                    self.wumpus_probabilities[neighbor] = 0.0
        
        # TH2: Có Stench
        else:
            # Lọc ra các nghi phạm thực sự (chưa được chứng minh là an toàn)
            suspects = [n for n in neighbors if n not in self.safe_cells]
            if not suspects: # Nếu tất cả các ô kề đều an toàn mà vẫn có Stench -> KB mâu thuẫn
                print("WARNING: Stench detected but all neighbors are considered safe. KB might be inconsistent.")
                self.normalize_probabilities()
                return

            prob_no_wumpus_in_suspects = 1.0
            for n in suspects:
                prob_no_wumpus_in_suspects *= (1 - self.wumpus_probabilities.get(n, 0))
            
            prob_stench_from_suspects = 1 - prob_no_wumpus_in_suspects
            
            if prob_stench_from_suspects > 1e-6:
                for n in suspects:
                    # KHÔNG CẬP NHẬT NẾU ĐÃ CHẮC CHẮN CÓ WUMPUS
                    if n in self.proven_wumpuses:
                        self.wumpus_probabilities[n] = 1.0
                        continue
                    
                    p_w_n = self.wumpus_probabilities.get(n, 0)
                    self.wumpus_probabilities[n] = p_w_n / prob_stench_from_suspects

        self.normalize_probabilities()
    
    def get_risk_score(self, pos: Point) -> float:
        """Tính điểm rủi ro cho một ô, kết hợp cả Pit và Wumpus."""
        if pos in self.proven_pits or pos in self.proven_wumpuses:
            return 1000.0
        
        # Nếu chưa chứng minh được là không có Pit, vẫn có rủi ro
        pit_risk = PIT_PROBABILITY if pos not in self.safe_cells and pos not in self.visited_cells else 0.0
        wumpus_risk = self.wumpus_probabilities.get(pos, 0.0)
        
        # Rủi ro là xác suất chết
        prob_death = 1 - ((1 - pit_risk) * (1 - wumpus_risk))
        base_risk_score = prob_death * 1000
        
        # --- CHIẾN LƯỢC ƯU TIÊN LỐI THOÁT ---
        # Đếm số lượng hàng xóm của 'pos' đã được khám phá và an toàn.
        # Ô càng có nhiều "lối thoát" đã biết thì càng tốt.
        escape_routes = 0
        for neighbor, _ in self.get_neighbors(pos):
            if neighbor in self.visited_cells:
                escape_routes += 1

        escape_bonus = escape_routes * 5 
        final_risk_score = base_risk_score - escape_bonus

        return max(0, final_risk_score)
    
    def find_least_risky_frontier_cell(self) -> Point:
        """Tìm ô biên chưa thăm có rủi ro thấp nhất."""
        frontier = self.get_frontier_cells() - self.visited_cells
        if not frontier:
            return None
        
        # Tìm ô có rủi ro thấp nhất, ưu tiên ô có rủi ro < 1000 (không chắc chắn chết)
        min_risk = float('inf')
        best_cell = None
        for cell in frontier:
            risk = self.get_risk_score(cell)
            if risk < min_risk:
                min_risk = risk
                best_cell = cell
        
        # Chỉ đi vào ô nếu rủi ro không phải là cái chết chắc chắn
        return best_cell if min_risk < 999 else None
    
    def find_closest_safe_haven(self) -> Point:
        """Tìm ô đã thăm gần nhất để làm nơi trú ẩn."""
        if not self.visited_cells:
            return None
        
        # Bỏ qua vị trí hiện tại
        possible_havens = self.visited_cells - {self.location}
        if not possible_havens:
            return None

        # Tìm ô gần nhất theo khoảng cách Manhattan
        return min(possible_havens, key=lambda p: abs(p.x - self.location.x) + abs(p.y - self.location.y))
    
    def decide_risky_shoot_action(self, kb: KB, inference: InferenceEngine):
        """Bắn vào hướng có tổng xác suất Wumpus cao nhất."""
        if not self.has_arrow: return

        direction_scores = {d: 0.0 for d in Direction}
        for direction in direction_scores:
            path_pos = self.location + DIRECTION_VECTORS[direction]
            while is_valid(path_pos, self.map_size):
                direction_scores[direction] += self.wumpus_probabilities.get(path_pos, 0.0)
                # Dừng lại nếu gặp tường hoặc Pit đã biết
                if path_pos in self.proven_pits: break
                path_pos += DIRECTION_VECTORS[direction]
        
        if not any(s > 1e-6 for s in direction_scores.values()):
            print("No probabilistic data to guide a risky shot. Falling back to random.")
            # Gọi logic cũ của HybridAgent nếu không có dữ liệu xác suất
            super().decide_risky_shoot_action(kb, inference)
            return

        best_direction = max(direction_scores, key=direction_scores.get)
        
        print(f"Agent planning probabilistic risky shot towards {best_direction.name} with score {direction_scores[best_direction]:.2f}")
        turn_actions = self.get_turn_decision(self.direction, best_direction)
        self.planned_action.extend(turn_actions)
        self.planned_action.append(Action.SHOOT)

    def update_wumpus_probabilities_after_move(self):
        new_probs = {Point(x, y): 0.0 for x in range(self.map_size) for y in range(self.map_size)}

        potentially_occupied_cells = {
            p for p, prob in self.wumpus_probabilities.items() 
            if prob > 0.5 
        }
        
        for pos, old_prob in self.wumpus_probabilities.items():
            if old_prob < 1e-6:
                continue

            possible_neighbors = [n for n, _ in self.get_neighbors(pos)]
            valid_moves = []
            for neighbor in possible_neighbors:
                if neighbor not in self.proven_pits and neighbor not in potentially_occupied_cells:
                    valid_moves.append(neighbor)

            if not valid_moves:
                new_probs[pos] += old_prob
            else:
                num_directions = 4 # N, S, E, W
                prob_per_direction = old_prob / num_directions
            
                num_blocked_directions = 0
                
                for direction_vec in DIRECTION_VECTORS.values():
                    intended_pos = pos + direction_vec
                    
                    # Kiểm tra các điều kiện chặn
                    is_blocked = (
                        not is_valid(intended_pos, self.map_size) or      # Chạm tường
                        intended_pos in self.proven_pits or               # Chạm Pit đã biết
                        intended_pos in potentially_occupied_cells        # Chạm Wumpus khác (dự đoán)
                    )

                    if is_blocked:
                        num_blocked_directions += 1
                    else:
                        # Nếu không bị chặn, phân bổ xác suất cho ô đó
                        new_probs[intended_pos] += prob_per_direction

                if num_blocked_directions > 0:
                    new_probs[pos] += num_blocked_directions * prob_per_direction

        self.wumpus_probabilities = new_probs
        self.normalize_probabilities()

    def explore_with_astar(self, goals: set[Point]):
        """
        SỬA ĐỔI A* ĐỂ TÍNH TOÁN RỦI RO.
        Chi phí giờ đây là: g_cost (số bước) + h_cost (manhattan) + risk_cost
        """
        if self.planned_action or not goals:
            return

        start_node = (self.location, self.direction)
        count = 0
        
        # (f_cost, g_cost, count, (location, direction), actions)
        # g_cost bây giờ bao gồm cả rủi ro
        frontier = [(self.calculate_heuristic(self.location, goals), 0, count, start_node, [])]
        
        visited_states = {start_node: 0}

        while frontier:
            _, g_cost, _, current_state, actions = heappop(frontier)
            current_pos, current_dir = current_state

            if current_pos in goals:
                self.planned_action.extend(actions)
                print(f"A* (Risk-Aware) found a path to {current_pos}. Plan: {[a.name for a in self.planned_action]}")
                return

            for action in [Action.MOVE_FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT]:
                new_pos, new_dir = current_pos, current_dir
                
                if action == Action.MOVE_FORWARD:
                    next_cell = current_pos + DIRECTION_VECTORS[current_dir]
                    # Chỉ có thể đi vào ô đã thăm hoặc ô mục tiêu
                    can_move = is_valid(next_cell, self.map_size) and \
                               (next_cell in self.visited_cells or next_cell in goals or next_cell in self.safe_cells)
                    if can_move:
                        new_pos = next_cell
                    else:
                        continue
                elif action == Action.TURN_LEFT: new_dir = TURN_LEFT_MAP[current_dir]
                elif action == Action.TURN_RIGHT: new_dir = TURN_RIGHT_MAP[current_dir]

                # TÍNH TOÁN CHI PHÍ MỚI (g_cost)
                # Chi phí di chuyển = 1 (hành động) + rủi ro của ô sắp tới
                move_cost = 1 + self.get_risk_score(new_pos) * self.RISK_WEIGHT
                new_g_cost = g_cost + move_cost

                new_state = (new_pos, new_dir)
                if new_state not in visited_states or new_g_cost < visited_states[new_state]:
                    visited_states[new_state] = new_g_cost
                    h_cost = self.calculate_heuristic(new_pos, goals)
                    f_cost = new_g_cost + h_cost
                    new_actions = actions + [action]
                    count += 1
                    heappush(frontier, (f_cost, new_g_cost, count, new_state, new_actions))

        print(f"A* (Risk-Aware) could not find a path to any of {goals}.")

    def after_action(self):
        """
        Tăng biến đếm sau mỗi hành động.
        """
        self.action_count += 1

    def need_wumpus_move(self) -> bool:
        """
        Kiểm tra có cần cho Wumpus di chuyển hay chưa.
        """
        return self.action_count > 0 and (self.action_count + 1)  % WUMPUS_MOVE_INTERVAL == 0
    
    def prepare_for_kb_reset(self, kb, inference):
        self.last_known_threats = set()
        # Thêm các Wumpus đã được chứng minh
        self.last_known_threats.update(self.proven_wumpuses)
        
        # Thêm các ô uncertain về Wumpus
        for cell in self.get_uncertain_cells():
            is_w_uncertain = not inference.ask_Wumpus(kb.wumpus_rules, Literal(f"W{cell.x}{cell.y}")) and \
                            not inference.ask_Wumpus(kb.wumpus_rules, Literal(f"W{cell.x}{cell.y}", negated=True))
            if is_w_uncertain:
                self.last_known_threats.add(cell)

    def reset_safe_cells(self):
        if not self.last_known_threats:
            return
        
        dangerous_zone = set()
        for threat_pos in self.last_known_threats:
            dangerous_zone.add(threat_pos)
            for neighbor_1, _ in self.get_neighbors(threat_pos):
                dangerous_zone.add(neighbor_1)

            # for neighbor_2, _ in self.get_neighbors(neighbor_1):
            #     dangerous_zone.add(neighbor_2)

        dangerous_cells = self.safe_cells.intersection(dangerous_zone)

        dangerous_cells.discard(self.location)
        dangerous_cells.discard(Point(0, 0))

        if dangerous_cells:
            self.safe_cells.difference_update(dangerous_cells)

    def reset_Wumpus_KB(self):
        if self.proven_wumpuses:
            self.proven_wumpuses.clear()

    def check_defense_with_Wumpus(self, kb: KB, inference: InferenceEngine):
        """
        Check if have no safe cells and stuck with dangerous neighbor cells (Wumpus)
        """
        if self.get_unvisited_safe_cells():
            return False
            
        for neighbor, _ in self.get_neighbors(self.location):
            if neighbor not in self.safe_cells:
                is_proven_wumpus = inference.ask_Wumpus(kb.wumpus_rules, Literal(f"W{neighbor.x}{neighbor.y}"))

                is_proven_not_wumpus = inference.ask_Wumpus(kb.wumpus_rules, Literal(f"W{neighbor.x}{neighbor.y}", negated=True))

                if not is_proven_not_wumpus and not is_proven_wumpus: # Uncertain
                    return True
                
        return False
    
    def choose_next_decision(self, kb: KB, inference: InferenceEngine):
        if self.planned_action:
            return
        
        if self.need_wumpus_move():
            is_in_dangerous_area = False
            for neighbor, _ in self.get_neighbors(self.location):
                if self.get_risk_score(neighbor) > 50:
                    is_in_dangerous_area = True
                    break
            
            if is_in_dangerous_area:
                safe_haven = self.find_closest_safe_haven() # Bỏ trốn

                if safe_haven:
                    print(f"Plan: Wumpus will move next. Retreating from {self.location} to safe haven {safe_haven}.")
                    # Dùng A* để lập kế hoạch đường đi đến nơi trú ẩn
                    self.explore_with_astar({safe_haven})
                    if self.planned_action:
                        return # Ưu tiên thực hiện kế hoạch rút lui
                

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
            
            print("Plan: No moves left, even desperate ones. Considering a risky shot.\n") # Option 4.2 (risky shot)
            self.decide_risky_shoot_action(kb, inference)
            if self.planned_action:
                return
        
        # Ưu tiên 5: Chấp nhận rủi ro, đi vào ô ít nguy hiểm nhất
        target_cell = self.find_least_risky_frontier_cell()
        if target_cell:
            print(f"Plan: No safe options. Moving to least risky cell {target_cell} with risk {self.get_risk_score(target_cell):.2f}")
            self.explore_with_astar({target_cell})
            if self.planned_action: return
        
        # Ưu tiên cuối: Bỏ cuộc, về nhà
        print("Agent has no other options. Attempting to return home to climb out.")
        self.explore_with_astar({Point(0, 0)})
        self.planned_action.append(Action.CLIMB_OUT)