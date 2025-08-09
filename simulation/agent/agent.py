from abc import ABC, abstractmethod
from simulation import *
from collections import deque

class Agent(ABC):
    """
    Abstract base class for agent strategies.
    """

    def __init__(self, location: Point, direction: Direction, map_size: int):
        self.map_size = map_size
        self.location = location                 
        self.direction = direction                
        self.has_arrow = True                     
        self.has_gold = False                     
        self.last_action: Action = None                       
        self.alive = True                         
        self.planned_action = deque()
        self.score = 0            

        self.visited_cells: set[Point] = {location}

        self.frontier_cells: set[Point] = {
            neighbor for neighbor, _ in self.get_neighbors(location)
        }

    @abstractmethod
    def update_percepts(self, percepts: set[Percept]):
        pass
    
    @abstractmethod
    def reset_safe_cells(self):
        pass

    @abstractmethod
    def after_action(self):
        pass

    @abstractmethod
    def need_wumpus_move(self):
        pass

    @abstractmethod
    def prepare_for_kb_reset(self, kb, inference):
        pass

    @abstractmethod
    def process_scream(self, shot_path: list[Point]):
        pass
    
    @abstractmethod
    def update_wumpus_probabilities_after_move(self):
        pass

    @abstractmethod
    def reground_probabilities_with_percepts(self):
        pass
    
    def get_neighbors(self, pos: Point) -> list[tuple[Point, Direction]]:
        neighbors = []
        for direction, vec in DIRECTION_VECTORS.items():
            next_pt = pos + vec
            if is_valid(next_pt, self.map_size):
                neighbors.append((next_pt, direction))
        return neighbors
    
    def update_location(self, new_location: Point):
        self.location = new_location
        self.visited_cells.add(new_location)

        self.frontier_cells.discard(new_location)

        for neighbor, _ in self.get_neighbors(new_location):
            if neighbor not in self.visited_cells:
                self.frontier_cells.add(neighbor)

        self.last_action = Action.MOVE_FORWARD

    def turn_left(self):
        self.direction = TURN_LEFT_MAP[self.direction]
        self.last_action = Action.TURN_LEFT

    def turn_right(self):
        self.direction = TURN_RIGHT_MAP[self.direction]
        self.last_action = Action.TURN_RIGHT

    def move_forward(self):
        move_vec = DIRECTION_VECTORS[self.direction]
        new_location = self.location + move_vec

        self.last_action = Action.MOVE_FORWARD
        return new_location

    def shoot(self):
        if self.has_arrow:
            self.has_arrow = False
            self.last_action = Action.SHOOT

    def grab_gold(self):
        self.has_gold = True
        self.last_action = Action.GRAB

    def climb_out(self):
        self.last_action = Action.CLIMB_OUT

    def __str__(self):
        return f"Agent({self.location}, {DIRECTION_NAMES[self.direction]}, Arrow={self.has_arrow}, Gold={self.has_gold})"

    def get_turn_decision(self, current_direction: Direction, target_direction: Direction) -> list[Action]:
        """
        Function to return list of turn actions
        """
        if current_direction == target_direction:
            return []

        dirs = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        try:
            current_index = dirs.index(current_direction)
            target_index = dirs.index(target_direction)     
        except ValueError: 
            return [Action.TURN_RIGHT, Action.TURN_RIGHT] # Fallback

        diff = (target_index - current_index + 4) % 4

        if diff == 1: return [Action.TURN_RIGHT]
        if diff == 3: return [Action.TURN_LEFT]
        if diff == 2: return [Action.TURN_RIGHT, Action.TURN_RIGHT]
        return []
    
    @abstractmethod
    def choose_next_decision(self, kb: KB, inference: InferenceEngine):
        pass