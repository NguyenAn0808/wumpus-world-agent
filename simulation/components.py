from enum import Enum, auto
from dataclasses import dataclass

class CellStatus(Enum):
    SAFE = "PROVEN SAFE"
    DANGEROUS_WUMPUS = "PROVEN WUMPUS"
    DANGEROUS_PIT = "PROVEN PIT"
    UNCERTAIN = "UNCERTAIN"
    
class Direction(Enum):
    """
    Class represents all directions which Agent could face.
    """
    EAST = 0
    WEST = 1
    NORTH = 2
    SOUTH = 3

class Action(Enum):
    """
    Class represents all actions of Agent.
    """
    MOVE_FORWARD = auto()
    TURN_LEFT = auto()
    TURN_RIGHT = auto()
    SHOOT = auto()
    GRAB = auto()
    CLIMB_OUT = auto()

class Percept(Enum):
    """
    Class represents all percepts that Agent can observe from the environment.
    """
    STENCH = auto()
    BREEZE = auto()
    SCREAM = auto()
    BUMP = auto()
    GLITTER = auto()

@dataclass(frozen=True,eq=True)
class Point:
    """
    Class represents one coordinate(x, y) in the gameplay
    """
    x: int
    y: int

    # Calculate new coordinate if Agent reachs the new location.
    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        raise ValueError("Cannot implement")
    
@dataclass(frozen=True,eq=True)
class Literal:
    name: str
    negated: bool = False

    def __str__(self):
        return f"¬{self.name}" if self.negated else self.name

    def __repr__(self):
        return str(self)

    def negate(self):
        return Literal(self.name, not self.negated)

# No duplicate value in frozen set
Clause = frozenset[Literal]

DIRECTION_VECTORS = {
    Direction.EAST: Point(1, 0),
    Direction.WEST: Point(-1, 0),
    Direction.NORTH: Point(0, 1),
    Direction.SOUTH: Point(0, -1)
}


DIRECTION_NAMES = {
    Direction.EAST: 'EAST',
    Direction.WEST: 'WEST',
    Direction.NORTH: 'NORTH',
    Direction.SOUTH: 'SOUTH'
}

DIRECTION_ARROWS = {
    Direction.NORTH: '^',
    Direction.EAST:  '>',
    Direction.SOUTH: 'v',
    Direction.WEST:  '<',
}