from .components import *

class Agent:
    def __init__(self, location: Point, direction: Direction):
        self.location = location                  # Vị trí hiện tại
        self.direction = direction                # Hướng đang quay mặt
        self.has_arrow = True                     # Có mũi tên không
        self.has_gold = False                     # Đã lấy được vàng chưa
        self.last_action = None                   # Hành động gần nhất
        self.visited = set()                      # Tập hợp các ô đã ghé qua
        self.alive = True                         # Agent còn sống không

    def update_location(self, new_location: Point):
        self.location = new_location
        self.visited.add(new_location)

    def turn_left(self):
        self.direction = {
            Direction.NORTH: Direction.WEST,
            Direction.WEST: Direction.SOUTH,
            Direction.SOUTH: Direction.EAST,
            Direction.EAST: Direction.NORTH
        }[self.direction]
        self.last_action = Action.TURN_LEFT

    def turn_right(self):
        self.direction = {
            Direction.NORTH: Direction.EAST,
            Direction.EAST: Direction.SOUTH,
            Direction.SOUTH: Direction.WEST,
            Direction.WEST: Direction.NORTH
        }[self.direction]
        self.last_action = Action.TURN_RIGHT

    def move_forward(self):
        move_vec = DIRECTION_VECTORS[self.direction]
        new_location = self.location + move_vec
        self.update_location(new_location)
        self.last_action = Action.MOVE_FORWARD

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
