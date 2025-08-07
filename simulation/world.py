import config
import random

from .components import *
from config import *

class World:
    def __init__(self, size=None, pit_prob=None, number_of_wumpus=None, debug_map=False):
        self.size = size if size is not None else MAP_SIZE
        self.pit_prob = pit_prob if pit_prob is not None else PIT_PROBABILITY
        self.number_of_wumpus = number_of_wumpus if number_of_wumpus is not None else NUMBER_OF_WUMPUS

        self.state = [[set() for _ in range(self.size)] for _ in range(self.size)]
        self.wumpus_locations = []
        self.gold_location = None

        self.debug_map = debug_map
        self.generate_map()
    
    def get_state(self):
        return {
            "state": self.state,
            "agent_location": INITIAL_AGENT_LOCATION,
            "agent_has_arrow": INITIAL_AGENT_HAS_ARROW,
            "agent_direction": INITIAL_AGENT_DIRECTION,
            "pit_probability": self.pit_prob,
            "number_of_wumpus": self.number_of_wumpus,
            "size": self.size,
            "debug_map": self.debug_map,
            "wumpus_locations": self.wumpus_locations,
            "gold_location": self.gold_location
        }
    
    def generate_map(self):
        self.state = [[set() for _ in range(self.size)] for _ in range(self.size)]
        self.wumpus_locations = []
        self.gold_location = None

        if self.debug_map:
            self.generate_fixed_map()
        else:
            self.generate_random_map()

    def generate_fixed_map(self):
        print("--- DEBUG MODE: Using a fixed map layout. ---")

        self.state = [[set() for _ in range(self.size)] for _ in range(self.size)]
        self.wumpus_locations = []
        self.gold_location = None

        fixed_layout = {
            Point(4, 0): {'P'},
            Point(4, 2): {'P'},
            Point(3, 3): {'P'},
            Point(3, 4): {'P'},
            Point(4, 3): {'W'},
            Point(3, 3): {'W'},
            Point(1, 3): {'G'}
        }

        # 3. Áp dụng layout cố định vào self.state
        for pos, items in fixed_layout.items():
            if is_valid(pos, self.size):
                self.state[pos.y][pos.x].update(items)
                if 'W' in items:
                    self.wumpus_locations.append(pos)
                if 'G' in items:
                    self.gold_location = pos
        
        if is_valid(INITIAL_AGENT_LOCATION, self.size):
            self.state[INITIAL_AGENT_LOCATION.y][INITIAL_AGENT_LOCATION.x].clear()


        for y in range(self.size):
            for x in range(self.size):
                cell = Point(x, y)
                # Nếu ô này có Wumpus, thêm Stench vào các ô kề
                if 'W' in self.state[y][x]:
                    self.add_adjacent_percept(cell, 'S')
                # Nếu ô này có Pit, thêm Breeze vào các ô kề
                if 'P' in self.state[y][x]:
                    self.add_adjacent_percept(cell, 'B')

    def generate_random_map(self):
        cells = [Point(x, y) for x in range(self.size) for y in range(self.size)]
        cells.remove(INITIAL_AGENT_LOCATION)
        random.shuffle(cells)

        if cells:
            gold = cells.pop()
            self.state[gold.y][gold.x].add('G')

        for _ in range(self.number_of_wumpus):
            if not cells: break
            pos = cells.pop()
            self.wumpus_locations.append(pos)
            self.state[pos.y][pos.x].add('W')
            self.add_adjacent_percept(pos, 'S')

        for cell in cells:
            if random.random() < self.pit_prob:
                self.state[cell.y][cell.x].add('P')
                self.add_adjacent_percept(cell, 'B')

    def add_adjacent_percept(self, center: Point, char: str):
        for vec in DIRECTION_VECTORS.values():
            adj_point = center + vec
            if is_valid(adj_point, self.size):
                self.state[adj_point.y][adj_point.x].add(char)

    def get_percepts(self, cell: Point) -> set[Percept]:
        if not is_valid(cell, self.size):
            return set()
        
        percepts = set()
        items = self.state[cell.y][cell.x]
        if 'G' in items: percepts.add(Percept.GLITTER)
        if 'S' in items: percepts.add(Percept.STENCH)
        if 'B' in items: percepts.add(Percept.BREEZE)

        return percepts
    
    def kill_wumpus(self, wumpus_pos: Point):
        if is_valid(wumpus_pos, self.size) and 'W' in self.state[wumpus_pos.y][wumpus_pos.x]:
            print(f"--- World Event: Wumpus at {wumpus_pos} has been killed. ---")
            
            self.state[wumpus_pos.y][wumpus_pos.x].remove('W')
            
            if wumpus_pos in self.wumpus_locations:
                self.wumpus_locations.remove(wumpus_pos)

            self.remove_stench(wumpus_pos)
            
            return True 
        return False 
            
    def remove_stench(self, wumpus_pos: Point):
        for cell in get_adjacent_cells(wumpus_pos, self.size):
            has_other_wumpus_neighbor = False
            for neighbor in get_adjacent_cells(cell, self.size):
                if 'W' in self.state[neighbor.y][neighbor.x]:
                    has_other_wumpus_neighbor = True
                    break

            # No more wumpuses -> Remove Stench
            if not has_other_wumpus_neighbor:
                self.state[cell.y][cell.x].discard('S')

    def remove_gold(self, gold_pos: Point):
        if is_valid(gold_pos, self.size):
            cell_items = self.state[gold_pos.y][gold_pos.x]
            
            if 'G' in cell_items:
                cell_items.remove('G')
                print(f"World state: Gold removed from {gold_pos}.")
                self.gold_location = None 
   
    def move_wumpuses(self):
        """
        Di chuyển từng Wumpus một bước ngẫu nhiên:
        - Chỉ di chuyển sang ô kề hợp lệ (Đông/Tây/Nam/Bắc).
        - Không vào Pit.
        - Không chồng lên Wumpus khác.
        - Nếu không có ô hợp lệ -> đứng yên.
        Sau đó, cập nhật lại percept (Stench).
        """
        if not self.wumpus_locations:
            return
        
        planned_moves = {}
        current_wumpus_positions = set(self.wumpus_locations)

        for wumpus_pos in self.wumpus_locations:
            chosen_direction_vector = random.choice(list(DIRECTION_VECTORS.values()))
            intended_pos = wumpus_pos + chosen_direction_vector

            final_pos = wumpus_pos

            is_move_valid = True
            if not is_valid(intended_pos, self.size):          # Tường
                is_move_valid = False
            elif 'P' in self.state[intended_pos.y][intended_pos.x]: # Hố
                is_move_valid = False
            elif intended_pos in current_wumpus_positions:
                is_move_valid = False

            if is_move_valid:
                final_pos = intended_pos

            planned_moves[wumpus_pos] = final_pos # Di chuyển thành công

        for old_pos in self.wumpus_locations:
            self.state[old_pos.y][old_pos.x].discard('W')
            self.remove_stench(old_pos)

        new_wumpus_locations = list(planned_moves.values())

        final_positions = []
        occupied_destinations = set() # Two Wumpuses in one cell

        for old_pos in self.wumpus_locations:
            new_pos = planned_moves[old_pos]
            if new_pos not in occupied_destinations:
                final_positions.append(new_pos)
                occupied_destinations.add(new_pos)
            else:
                # Vị trí mới đã bị chiếm, Wumpus này đứng yên ở vị trí cũ
                final_positions.append(old_pos)
        
        self.wumpus_locations = final_positions

        for pos in self.wumpus_locations:
            self.state[pos.y][pos.x].add('W')
            self.add_adjacent_percept(pos, 'S')

