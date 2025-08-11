from .world import World 
from .agent import Agent, HybridAgent, AdvancedAgent, RandomAgent
from .knowledge_base import KB
from .inference import InferenceEngine
from .components import *
from config import *
from gui.console_ui import display_world
import time

class GamePlay:

    def __init__(self, agent: Agent, display_callback):
        print("-----WUMPUS WORLD AGENT-----\n")
        self.world = World(debug_map=False)
        
        self.last_shot_path = None
        self.agent = agent
        self.kb = KB()
        self.inference = InferenceEngine()
        self.status = GameStatus.IN_PROGRESS

        self.learn_from_new_cell(self.agent.location)
        initial_percepts = self.world.get_percepts(self.agent.location)
        self.agent.update_percepts(initial_percepts)
        self.message = "Game started!!!\n"
        self.update_agent_state_after_action()
        self.display_callback = display_callback

    def get_game_state(self) -> dict:
        # Giữ nguyên, không cần thay đổi
        world_info = self.world.get_state() 
        game_state = {
            'size': world_info['size'],
            'state': world_info['state'], 
            'score': self.agent.score,
            'agent_location': self.agent.location,
            'agent_direction': self.agent.direction,
            'agent_has_arrow': self.agent.has_arrow,
            'agent_has_gold': self.agent.has_gold,
            'agent_percepts': self.agent.current_percepts,
            'message': self.message,
            'game_status': self.status,
            'stop_game': self.stop_game,
            'known_safe_cells': self.agent.safe_cells,
            'known_visited_cells': self.agent.visited_cells,
            'known_proven_wumpuses': self.agent.proven_wumpuses,
            'known_proven_pits': self.agent.proven_pits,
            'known_frontier_cells': self.agent.frontier_cells,
            'last_action': self.agent.last_action.name if self.agent.last_action else None,
            'shot_path': self.last_shot_path
        }
        return game_state

    def check_game_status(self):
        # Giữ nguyên, không cần thay đổi
        location = self.agent.location
        cell = self.world.state[location.y][location.x]
        if 'W' in cell:
            self.agent.alive = False
            self.status = GameStatus.DEAD_BY_WUMPUS
            self.agent.score += SCORES["DEATH_WUMPUS"]
            self.message = f"Agent was eaten by a Wumpus at {location}!"
        elif 'P' in cell:
            self.agent.alive = False
            self.status = GameStatus.DEAD_BY_PIT
            self.agent.score += SCORES["DEATH_PIT"]
            self.message = f"Agent fell into a pit at {location}!"
        elif self.agent.last_action == Action.CLIMB_OUT:
            if location == INITIAL_AGENT_LOCATION:
                self.status = GameStatus.CLIMB_SUCCESS if self.agent.has_gold else GameStatus.CLIMB_FAIL
                self.agent.score += SCORES["CLIMB_SUCCESS"] if self.agent.has_gold else SCORES["CLIMB_FAIL"]
                self.message = "Agent climbed out with the gold! YOU WON!" if self.agent.has_gold else "Agent climbed out without the gold."
            else:
                self.message = "Agent cannot climb out from here."

        if self.stop_game:
            self.message = f"Final Score : {self.agent.score}"
            print(f"--- {self.message} ---")

            self.message = f"Agent's Path History: {len(self.agent.path_history)}"
            print(f"--- {self.message} ---")

            path_str = " -> ".join([f"({p.x},{p.y})" for p in self.agent.path_history])
            self.message = f"Final Path : {path_str}"
            print(f"--- {self.message} ---")

    def display_current_state(self):
        if self.display_callback:
            self.display_callback(self.get_game_state())

    @property
    def stop_game(self):
        return self.status != GameStatus.IN_PROGRESS
    
    def handle_Wumpus_move(self):
        print("\n--- WUMPUS MOVEMENT PHASE ---")
        self.world.move_wumpuses()

        if 'W' in self.world.state[self.agent.location.y][self.agent.location.x]:
             self.agent.alive = False
             self.status = GameStatus.DEAD_BY_WUMPUS
            #  self.agent.score += SCORES["DEATH_WUMPUS"]
             self.message = f"Agent at {self.agent.location} was eaten by a moving Wumpus!"
             return False 
        
        # --- THÊM LOGIC CHO ADVANCED AGENT ---
        if isinstance(self.agent, AdvancedAgent):
            # Kích hoạt chế độ động nếu đây là lần đầu
            self.agent.activate_dynamic_mode()
            # Yêu cầu agent reset kiến thức Wumpus của nó
            self.agent.reset_wumpus_knowledge()
        
        # Xóa các sự thật về Stench khỏi KB logic
        self.kb.retract_all_stench_facts()
        
        # Xóa kế hoạch cũ và cảm nhận lại thế giới mới
        self.agent.planned_action.clear()
        self.agent.needs_full_rethink = True
        
        print("--- WUMPUS MOVEMENT COMPLETE. Agent is re-evaluating. ---")
        return True

    def run_single_action(self):
        if self.stop_game or not self.agent.alive:
            return

        # --- SỬA ĐỔI LOGIC KIỂM TRA WUMPUS MOVE ---
        # Chỉ kiểm tra và xử lý Wumpus move nếu agent là AdvancedAgent
        if self.agent.needs_full_rethink:
            print("--- Agent needs to rethink due to a major event (e.g., shot). ---")
            self.agent.planned_action.clear()

        if isinstance(self.agent, AdvancedAgent) and self.agent.need_wumpus_move():
            if not self.handle_Wumpus_move():
                self.check_game_status()
                return
            # Sau khi Wumpus di chuyển, agent cần cập nhật lại trạng thái ngay
            self.update_agent_state_after_action()
            
        self.update_agent_state_after_action()

        if self.agent.just_encountered_danger and self.agent.planned_action:
            print(f"--- DANGER PERCEPT AT {self.agent.location}! Clearing old plan: {[a.name for a in self.agent.planned_action]} ---")
            self.agent.planned_action.clear()
            self.agent.just_encountered_danger = False

        if not self.agent.planned_action:
            self.update_KB_and_inference()
            self.agent.choose_next_decision(self.kb, self.inference)

        if self.agent.planned_action:
            next_action = self.agent.planned_action.popleft()
            self.excute_action(next_action)

            # --- SỬA ĐỔI LOGIC GỌI AFTER_ACTION ---
            # Chỉ gọi after_action nếu agent là AdvancedAgent
            if isinstance(self.agent, AdvancedAgent):
                self.agent.after_action()

            self.check_game_status()
        else:
            self.message = "Agent is hopelessly stuck and has no plan. Climbing out."
            self.excute_action(Action.CLIMB_OUT)

            if isinstance(self.agent, AdvancedAgent):
                self.agent.after_action()

            self.check_game_status()
        
    def run_console(self):
        while not self.stop_game and self.agent.alive:
            self.display_current_state()
            time.sleep(1)
            self.run_single_action()
            self.update_agent_state_after_action()
        
        self.display_current_state()

    def add_percepts_rules_to_KB(self, cell: Point):
        # Giữ nguyên
        adj_cells = get_adjacent_cells(cell, self.world.size)
        if not adj_cells: return
        
        breeze = f"B{cell.x}{cell.y}"
        pit = [f"P{p.x}{p.y}" for p in adj_cells]
        if pit: self.kb.tell(KB.conversion_to_CNF(breeze, pit), is_wumpus_rule=False)

        stench = f"S{cell.x}{cell.y}"
        wumpus = [f"W{p.x}{p.y}" for p in adj_cells]
        if wumpus: self.kb.tell(KB.conversion_to_CNF(stench, wumpus), is_wumpus_rule=True)

    def learn_from_new_cell(self, cell: Point):
        print(f"--- Agent learning from new cell {cell} ---")
        self.kb.tell_fact(Literal(f"P{cell.x}{cell.y}", negated=True))
        self.kb.tell_fact(Literal(f"W{cell.x}{cell.y}", negated=True))
        self.agent.safe_cells.add(cell) # Thêm vào đây để nhất quán
        self.add_percepts_rules_to_KB(cell)

    def update_agent_state_after_action(self):
        current_location = self.agent.location
        
        current_percepts = self.world.get_percepts(current_location)
        self.agent.update_percepts(current_percepts)

        self.kb.retract_and_tell_percept_facts(current_location, current_percepts)

        if current_location not in self.agent.cells_learned_from:
            self.learn_from_new_cell(current_location)
            self.agent.cells_learned_from.add(current_location)

    def update_KB_and_inference(self):
        print(f"\n--- Agent at {self.agent.location} is thinking... ---")
        inference_loop_limit = self.world.size * 2
        loop_count = 0
        
        newly_found_info = True
        while newly_found_info:
            loop_count += 1
            if loop_count > inference_loop_limit:
                print("WARNING: Inference loop reached limit. Breaking.")
                break

            newly_found_info = False
            cells_to_check = self.agent.get_frontier_cells().copy()
            if self.agent.needs_full_rethink:
                cells_to_check.update(self.agent.visited_cells)
                self.agent.needs_full_rethink = False

            for cell in list(cells_to_check):
                if cell not in self.agent.safe_cells and self.inference.ask_safe(self.kb.wumpus_rules, self.kb.pit_rules, cell):
                    self.agent.safe_cells.add(cell)
                    newly_found_info = True
                if cell not in self.agent.proven_wumpuses and self.inference.ask_Wumpus(self.kb.wumpus_rules, Literal(f"W{cell.x}{cell.y}")):
                    self.agent.proven_wumpuses.add(cell)
                    newly_found_info = True
                if cell not in self.agent.proven_pits and self.inference.ask_Pit(self.kb.pit_rules, Literal(f"P{cell.x}{cell.y}")):
                    self.agent.proven_pits.add(cell)
                    newly_found_info = True

    def excute_action(self, action: Action):
        if action != Action.SHOOT: self.last_shot_path = None
        self.message = f"Agent action: {action.name}"
        print(f"\n>>> {self.message}")

        # ... (Các action khác giữ nguyên) ...
        if action == Action.MOVE_FORWARD:
            next_location = self.agent.location + DIRECTION_VECTORS[self.agent.direction]
            self.agent.update_location(next_location)
            self.agent.score += SCORES["MOVE_FORWARD"]
        elif action == Action.TURN_LEFT:
            self.agent.turn_left()
            self.agent.score += SCORES["TURN_LEFT"]
        elif action == Action.TURN_RIGHT:
            self.agent.turn_right()
            self.agent.score += SCORES["TURN_RIGHT"]
        elif action == Action.GRAB:
            if Percept.GLITTER in self.world.get_percepts(self.agent.location):
                self.agent.grab_gold()
                self.agent.score += SCORES["GRAB_GOLD"]
                self.world.remove_gold(self.agent.location)
                self.message = "Agent grabbed the GOLD!"
        elif action == Action.SHOOT:
            if not self.agent.has_arrow: return
            self.agent.shoot()
            self.agent.score += SCORES["SHOOT"]
            shot_path = []
            path_pos = self.agent.location + DIRECTION_VECTORS[self.agent.direction]
            wumpus_killed = False
            while is_valid(path_pos, self.world.size):
                shot_path.append(path_pos)
                if self.world.kill_wumpus(path_pos):
                    self.message = "Agent shot an arrow. A loud SCREAM is heard!"
                    # --- THÊM LOGIC CHO ADVANCED AGENT ---
                    if hasattr(self.agent, 'process_scream'):
                        self.agent.process_scream(shot_path) 
                    self.kb.process_scream_event()
                    self.agent.planned_action.clear()
                    self.agent.needs_full_rethink = True
                    wumpus_killed = True
                    break
                path_pos += DIRECTION_VECTORS[self.agent.direction]
            
            if not wumpus_killed:
                self.message = "Agent shot an arrow into the darkness... and missed."
            self.last_shot_path = shot_path
        elif action == Action.CLIMB_OUT:
            self.agent.climb_out()
            