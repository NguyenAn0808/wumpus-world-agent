from simulation import *
from collections import deque
import random
from simulation.agent.agent import Agent

class RandomAgent(Agent):
    def __init__(self, location: Point, direction: Direction, size: int):
        super().__init__(location, direction, size)  
        self.location = location
        self.direction = direction
        self.size = size

        self.visited = set()
        self.safe_cells = set()
        self.path = deque()
        self.current_percepts = set()
        self.has_gold = False
        self.has_arrow = True
        self.cells_learned_from = set()
        self.proven_wumpuses = set()
        self.visited_cells = set()
        self.proven_pits = set()
        self.frontier_cells = set()
        self.just_encountered_danger = set()
        self.planned_action = deque()
        self.needs_full_rethink = False
 
    def get_frontier_cells(self):
        return self.frontier_cells
    
    def update_percepts(self, percepts: set[Percept]):
        self.current_percepts = percepts
        self.visited.add(self.location)
        self.safe_cells.add(self.location)

        # Thêm ô xung quanh vào safe_cells nếu nằm trong bản đồ
        for neighbor, _ in self.get_neighbors(self.location):
            if self.in_bounds(neighbor):
                self.safe_cells.add(neighbor)
                
    def choose_next_decision(self, kb=None, inference=None):
        if self.planned_action:
            return
    
        if self.has_arrow and random.random() < 0.05:
            self.planned_action.append(Action.SHOOT)
            self.has_arrow = False
            return
    
        if self.location == Point(0, 0) and self.has_gold:
            self.planned_action.append(Action.CLIMB_OUT)
            return
    
        if Percept.GLITTER in self.current_percepts and not self.has_gold:
            self.planned_action.append(Action.GRAB)
            self.has_gold = True
            self.path.clear()  # Xóa path cũ để đi về (0,0)
            return
    
        if not self.path:
            if self.has_gold:
                target = Point(0, 0)  # Về 0,0 ngay lập tức
            else:
                target = self.find_next_safe_unvisited()
    
            if target:
                self.path = self.bfs(self.location, target)
                if self.path and self.path[0] == self.location:
                    self.path.popleft()
    
        if not self.path:
            self.planned_action.append(random.choice([Action.TURN_LEFT, Action.TURN_RIGHT]))
            return
    
        next_cell = self.path[0]
        desired_direction = self.get_direction_to(self.location, next_cell)
    
        turn_actions = self.get_turn_decision(self.direction, desired_direction)
        for act in turn_actions:
            self.planned_action.append(act)
    
        if not turn_actions:
            self.planned_action.append(Action.MOVE_FORWARD)
            self.path.popleft()

    def find_next_safe_unvisited(self):
        """Chọn ô an toàn chưa thăm."""
        candidates = [cell for cell in self.safe_cells if cell not in self.visited]
        return random.choice(candidates) if candidates else None

    def bfs(self, start: Point, goal: Point):
        """BFS tìm đường từ start tới goal."""
        queue = deque([(start, [])])
        visited_bfs = {start}
        while queue:
            current, path = queue.popleft()
            if current == goal:
                return deque(path + [goal])
            for neighbor, _ in self.get_neighbors(current):
                if neighbor not in visited_bfs and self.in_bounds(neighbor):
                    visited_bfs.add(neighbor)
                    queue.append((neighbor, path + [current]))
        return deque()

    def get_neighbors(self, point: Point):
        """Trả về các ô kề và hướng tương ứng."""
        for direction, vec in DIRECTION_VECTORS.items():
            neighbor = Point(point.x + vec.x, point.y + vec.y)
            yield neighbor, direction

    def get_direction_to(self, src: Point, dst: Point):
        dx = dst.x - src.x
        dy = dst.y - src.y
        for direction, vec in DIRECTION_VECTORS.items():
            if vec.x == dx and vec.y == dy:
                return direction
        return self.direction
    
    def get_turn_decision(self, current_direction: Direction, target_direction: Direction) -> list[Action]:
        if current_direction == target_direction:
            return []

        dirs = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        try:
            current_index = dirs.index(current_direction)
            target_index = dirs.index(target_direction)
        except ValueError:
            return [Action.TURN_RIGHT, Action.TURN_RIGHT]  # Fallback

        diff = (target_index - current_index + 4) % 4

        if diff == 1:
            return [Action.TURN_RIGHT]
        if diff == 3:
            return [Action.TURN_LEFT]
        if diff == 2:
            return [Action.TURN_RIGHT, Action.TURN_RIGHT]
        return []

    def in_bounds(self, point: Point):
        return 0 <= point.x < self.size and 0 <= point.y < self.size
    
    def reset_safe_cells(self):
        pass

    def after_action(self):
        pass

    def need_wumpus_move(self):
        return False

    def prepare_for_kb_reset(self, kb, inference):
        pass

    def process_scream(self, shot_path: list[Point]):
        pass

    def update_wumpus_probabilities_after_move(self):
        pass

    def reground_probabilities_with_percepts(self):
        pass