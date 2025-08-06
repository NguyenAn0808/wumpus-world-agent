
from .agent import Agent
from simulation import *
from collections import deque
import random

class RandomAgent(Agent):
    def update_percepts(self, percepts: set[Percept]):
        self.current_percepts = percepts
        
    def choose_next_decision(self):
        """
        Agent sẽ chọn một hướng hợp lệ (không đụng tường ngay trước mặt)
        và đi một bước về hướng đó.
        """
    
        # Nếu có kế hoạch thì thực hiện tiếp
        if self.planned_action:
            return self.planned_action.popleft()
    
        # Nếu thấy vàng thì nhặt ngay
        if Percept.GLITTER in self.current_percepts and not self.has_gold:
            return Action.GRAB
    
        # Nếu có vàng và ở (0,0) thì leo ra
        if self.has_gold and self.location == Point(0, 0):
            return Action.CLIMB_OUT
    
        # Ngẫu nhiên bắn với xác suất 5%
        if self.has_arrow and random.random() < 0.05:
            return Action.SHOOT
    
        # Lấy danh sách hướng hợp lệ mà ô tiếp theo không phải tường
        valid_directions = []
        for dir_, vec in DIRECTION_VECTORS.items():
            next_cell = self.location + vec
            if is_valid(next_cell, self.map_size):
                valid_directions.append(dir_)
    
        # Nếu không còn hướng nào => leo ra
        if not valid_directions:
            return Action.CLIMB_OUT
    
        # Chọn một hướng ngẫu nhiên trong các hướng hợp lệ
        target_direction = random.choice(valid_directions)
    
        # Tạo kế hoạch: xoay cho đúng hướng rồi đi một bước
        if self.direction != target_direction:
            turns = self.get_turn_actions_to_face(target_direction)
            self.planned_action.extend(turns)
    
        self.planned_action.append(Action.MOVE_FORWARD)
    
        return self.planned_action.popleft()