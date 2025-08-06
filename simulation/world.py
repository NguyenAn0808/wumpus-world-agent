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
            Point(2, 1): {'P'},
            Point(3, 0): {'P'},
            Point(3, 3): {'P'},
            Point(1, 2): {'W'},
            Point(2, 0): {'W'},
            Point(0, 3): {'G'}
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

        for y in range(self.size):
            for x in range(self.size):
                cell = Point(x, y)

                if 'W' in self.state[y][x]:
                    self.add_adjacent_percept(cell, 'S')
                    
                if 'P' in self.state[y][x]:
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