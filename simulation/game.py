from .world import World 
from .agent import Agent
from .knowledge_base import KB
from .inference import InferenceEngine
from .components import *
from config import *
from gui.console_ui import display_world
import time


def format_kb_for_printing(kb: set) -> str:
    """Chuyển đổi một Knowledge Base (tập các clause) thành chuỗi dễ đọc."""
    if not kb:
        return "{}"
    
    # Chuyển mỗi clause thành một chuỗi "(L1 v L2)"
    formatted_clauses = []
    for clause in kb:
        # Nếu clause chỉ có 1 literal, in literal đó ra
        if len(clause) == 1:
            formatted_clauses.append(str(list(clause)[0]))
        # Nếu có nhiều, nối chúng bằng " v "
        else:
            literals_str = " v ".join(sorted([str(l) for l in clause]))
            formatted_clauses.append(f"({literals_str})")
            
    # Nối tất cả các clause đã định dạng bằng " ^ " (AND)
    return " ^ ".join(sorted(formatted_clauses))


class GamePlay:

    def __init__(self, agent: Agent, display_callback):
        print("-----WUMPUS WORLD AGENT-----\n")
        self.world = World(debug_map=True)
        
        start_pos = INITIAL_AGENT_LOCATION
        start_dir = INITIAL_AGENT_DIRECTION

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

    def update_agent_state_after_action(self):
        current_location = self.agent.location
        
        current_percepts = self.world.get_percepts(current_location)
        self.agent.update_percepts(current_percepts)

        self.kb.retract_and_tell_percept_facts(current_location, current_percepts)

        if current_location not in self.agent.cells_learned_from:
            self.learn_from_new_cell(current_location)
            self.agent.cells_learned_from.add(current_location)

    
    def get_game_state(self) -> dict:
        
        # kb_info = self.get_kb_for_display()
        world_info = self.world.get_state() 

        game_state = {
            'size': world_info['size'],
            'state': world_info['state'], 
            'pit_probability': world_info['pit_probability'],
            'number_of_wumpus': world_info['number_of_wumpus'],
            "wumpus_locations": world_info['wumpus_locations'],
            "gold_location": world_info['gold_location'],

            # Action of Agent
            'score': self.agent.score,
            'agent_location': self.agent.location,
            'agent_direction': self.agent.direction,
            'agent_has_arrow': self.agent.has_arrow,
            'agent_has_gold': self.agent.has_gold,
            'agent_score': self.agent.score,
            'agent_percepts': self.agent.current_percepts,

            # Gameplay
            'message': self.message,
            'game_status': self.status,
            'stop_game': self.stop_game,

            'known_safe_cells': self.agent.safe_cells,
            'known_visited_cells': self.agent.visited_cells,
            'known_proven_wumpuses': self.agent.proven_wumpuses,
            'known_proven_pits': self.agent.proven_pits,
            'known_frontier_cells': self.agent.frontier_cells,

            # KB
            # 'kb_info': kb_info
        }
        
        return game_state

    def display_current_state(self):
        if self.display_callback:
            state_to_display = self.get_game_state()
            self.display_callback(state_to_display)

    @property
    def stop_game(self):
        return self.status != GameStatus.IN_PROGRESS
    
    # GUI merge
    def run_single_action(self):
        if self.stop_game or not self.agent.alive:
            print("DEBUG: Game should stop. Exiting run_single_action.")
            return

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
            self.check_game_status()
        else:
            self.message = "Agent is hopelessly stuck and has no plan. Climbing out."
            self.excute_action(Action.CLIMB_OUT)
            self.check_game_status()

    def run_console(self):
        while not self.stop_game and self.agent.alive:
            self.display_current_state()
            time.sleep(1)

            self.run_single_action()

        self.message = f"Game Over | Final Score : {self.agent.score}"

        self.display_current_state()
        print(f"--- {self.message} ---")
        print(f"Final Score: {self.agent.score}")
    
    # Agent learn
    def update_KB_with_facts(self, cell: Point):
        x, y = cell.x, cell.y

        self.kb.tell_fact(Literal(f"P{cell.x}{cell.y}", negated=True))
        self.kb.tell_fact(Literal(f"W{cell.x}{cell.y}", negated=True))

        percepts = self.world.get_percepts(cell)

        breeze_literal = Literal(f"B{x}{y}")
        self.kb.pit_rules.discard(frozenset([breeze_literal]))
        self.kb.pit_rules.discard(frozenset([breeze_literal.negate()]))

        if Percept.BREEZE in percepts:
            self.kb.tell_fact(Literal(f"B{x}{y}"))
        else:
            self.kb.tell_fact(Literal(f"B{x}{y}", negated=True))

        stench_literal = Literal(f"S{x}{y}")
        self.kb.wumpus_rules.discard(frozenset([stench_literal]))
        self.kb.wumpus_rules.discard(frozenset([stench_literal.negate()]))

        if Percept.STENCH in percepts:
            self.kb.tell_fact(Literal(f"S{x}{y}"))
        else:
            self.kb.tell_fact(Literal(f"S{x}{y}", negated=True))

        glitter_literal = Literal(f"G{x}{y}")
        self.kb.wumpus_rules.discard(frozenset([glitter_literal]))
        self.kb.pit_rules.discard(frozenset([glitter_literal]))
        self.kb.wumpus_rules.discard(frozenset([glitter_literal.negate()]))
        self.kb.pit_rules.discard(frozenset([glitter_literal.negate()]))

        if Percept.GLITTER in percepts:
            self.kb.tell_fact(Literal(f"G{x}{y}"))
        else:
            self.kb.tell_fact(Literal(f"G{x}{y}", negated=True))

    def add_percepts_rules_to_KB(self, cell: Point):
        adj_cells = get_adjacent_cells(cell, self.world.size)
        if not adj_cells:
            return
        
        breeze = f"B{cell.x}{cell.y}"
        pit = [f"P{p.x}{p.y}" for p in adj_cells]
        
        if pit:
            cnf_clauses_pit = KB.conversion_to_CNF(breeze, pit)
            # clause = frozenset([Literal(breeze, negated=True), *[Literal(p) for p in pit]])
            self.kb.tell(cnf_clauses_pit, is_wumpus_rule=False)

        stench = f"S{cell.x}{cell.y}"
        wumpus = [f"W{p.x}{p.y}" for p in adj_cells]
        if wumpus:
            cnf_clauses_wumpus = KB.conversion_to_CNF(stench, wumpus)
            # clause = frozenset([Literal(stench, negated=True), *[Literal(w) for w in wumpus]])
            self.kb.tell(cnf_clauses_wumpus, is_wumpus_rule=True)

    def learn_from_new_cell(self, cell: Point):
        print(f"--- Agent learning from new cell {cell} ---")
        self.kb.tell_fact(Literal(f"P{cell.x}{cell.y}", negated=True))
        self.kb.tell_fact(Literal(f"W{cell.x}{cell.y}", negated=True))
        
        self.add_percepts_rules_to_KB(cell)

    def update_KB_and_inference(self):
        print(f"\n--- Agent at {self.agent.location} is thinking (Iterative Inference) ---")

        cells_to_check = self.agent.get_frontier_cells().copy()

        if self.agent.needs_full_rethink:
            print("--- Full rethink triggered! Checking all uncertain cells. ---")
            # Lấy tất cả các ô đã biết nhưng chưa đi vào và chưa chắc chắn
            all_known_cells = self.agent.safe_cells.union(self.agent.frontier_cells)
            cells_to_check.update(all_known_cells - self.agent.visited_cells)
            self.agent.needs_full_rethink = False 

        while True:
            newly_found_info = False
        
            for cell in list(cells_to_check):
                
                print(f"DEBUG: Checking cell {cell}")
                is_w_false = self.inference.ask_Wumpus(self.kb.wumpus_rules, Literal(f"W{cell.x}{cell.y}", negated=True))
                is_p_false = self.inference.ask_Pit(self.kb.pit_rules, Literal(f"P{cell.x}{cell.y}", negated=True))
                print(f"DEBUG: Is Wumpus false? {is_w_false}. Is Pit false? {is_p_false}")
                # Tìm ô an toàn mới
                if cell not in self.agent.safe_cells:
                    if self.inference.ask_safe(self.kb.wumpus_rules, self.kb.pit_rules, cell):
                        print(f"INFERRED NEW SAFE CELL: {cell}")
                        self.agent.safe_cells.add(cell)
                        # self.kb.tell_fact(Literal(f"W{cell.x}{cell.y}", negated=True))
                        # self.kb.tell_fact(Literal(f"P{cell.x}{cell.y}", negated=True))
                        newly_found_info = True

                # Tìm Wumpus mới
                if cell not in self.agent.proven_wumpuses:
                    if self.inference.ask_Wumpus(self.kb.wumpus_rules, Literal(f"W{cell.x}{cell.y}")):
                        print(f"INFERRED NEW WUMPUS: {cell}")
                        self.agent.proven_wumpuses.add(cell)
                        # self.kb.tell_fact(Literal(f"W{cell.x}{cell.y}"))
                        newly_found_info = True

                # Tìm Pit mới
                if cell not in self.agent.proven_pits:
                    if self.inference.ask_Pit(self.kb.pit_rules, Literal(f"P{cell.x}{cell.y}")):
                        print(f"INFERRED NEW PIT: {cell}")
                        self.agent.proven_pits.add(cell)
                        # self.kb.tell_fact(Literal(f"P{cell.x}{cell.y}"))
                        newly_found_info = True

            if not newly_found_info:
                print("--- Inference loop complete. No new information found. ---")
                break
            else:
                print("--- Found new info. Restarting inference loop. ---")

    def excute_action(self, action: Action):
        self.message = f"Agent action: {action.name}"
        print(f"\n>>> {self.message}")

        if action == Action.TURN_LEFT:
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
            else:
                self.message = "Agent tried to grab, but there is no gold here."
        elif action == Action.MOVE_FORWARD:
            next_location = self.agent.location + DIRECTION_VECTORS[self.agent.direction]
            # Not crash the wall
            assert is_valid(next_location, self.world.size), \
                f"FATAL LOGIC ERROR: Agent at {self.agent.location} tried to move into a wall."
            
            self.agent.update_location(next_location)
            self.agent.score += SCORES["MOVE_FORWARD"]

            new_percepts = self.world.get_percepts(self.agent.location)
            self.agent.update_percepts(new_percepts)

        elif action == Action.SHOOT:
            if not self.agent.has_arrow:
                self.message = "Agent tried to shoot, but has no arrow!"
                # Xóa kế hoạch để tránh lặp lại
                self.agent.planned_action.clear()
                return # Không làm gì cả
            
            self.agent.shoot() 
            self.agent.score += SCORES["SHOOT"]

            shot_path = []
            path_pos = self.agent.location + DIRECTION_VECTORS[self.agent.direction]
            while is_valid(path_pos, self.world.size):
                shot_path.append(path_pos)
                path_pos += DIRECTION_VECTORS[self.agent.direction]

            wumpus_killed = False 
            killed_wumpus_pos = None

            for pos in shot_path:
                if self.world.kill_wumpus(pos):
                    wumpus_killed = True
                    break 

            if wumpus_killed:
                self.message = "Agent shot an arrow. A loud SCREAM is heard!"
                print(f"--- {self.message} ---")
                self.kb.process_scream_event()
                self.agent.planned_action.clear()
                self.agent.needs_full_rethink = True
            else:
                self.message = "Agent shot an arrow into the darkness... and missed."

                for pos in shot_path:
                    wumpus_literal = Literal(f"W{pos.x}{pos.y}", negated=True)
                    self.kb.tell_fact(wumpus_literal)
                    self.agent.proven_wumpuses.discard(pos)

            self.agent.planned_action.clear()
            self.agent.needs_full_rethink = True
        else:
            self.agent.climb_out()

    def check_game_status(self):
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
                if self.agent.has_gold:
                    self.status = GameStatus.CLIMB_SUCCESS
                    self.agent.score += SCORES["CLIMB_SUCCESS"]
                    self.message = "Agent climbed out with the gold! YOU WON!"
                else:
                    self.status = GameStatus.CLIMB_FAIL
                    self.agent.score += SCORES["CLIMB_FAIL"]
                    self.message = "Agent climbed out without the gold."
            else:
                self.message = "Agent cannot climb out from here."  