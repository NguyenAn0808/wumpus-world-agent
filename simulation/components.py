from enum import Enum, auto
from dataclasses import dataclass

class Orientation(Enum):
    """
    Class represents all orientations which Agent could face.
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
            return (self.x + Point.x, self.y + Point.y)
        raise ValueError("Cannot implement")