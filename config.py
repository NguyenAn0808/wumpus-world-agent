from simulation import *

AGENT_TYPE = "Hybrid" # Random

MAP_SIZE = 4
PIT_PROBABILITY = 0.2
NUMBER_OF_WUMPUS = 2
NUMBER_OF_GOLD = 1

SCORES = {
    "GRAB_GOLD": 10,
    "MOVE_FORWARD": -1,
    "TURN LEFT": -1, 
    "TURN RIGHT": -1, 
    "SHOOT": -10,
    "DEATH_WUMPUS": -1000,
    "DEATH_PIT": -1000,
    "CLIMB_SUCCESS": +1000,
    "CLIMB_FAIL": 0
}

ORIENTATION_VECTORS = {
    Orientation.EAST: Point(-1, 0),
    Orientation.WEST: Point(1, 0),
    Orientation.NORTH: Point(0, 1),
    Orientation.SOUTH: Point(0, -1)
}


INITIAL_AGENT_LOCATION = (0, 0)
INITIAL_AGENT_HAS_ARROW = True
INITIAL_AGENT_ORIENTATION = "EAST"  


# Advanced settings
WUMPUS_MOVE_INTERVAL = 5