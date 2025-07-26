import config 
import random

from .components import *

class World:
    """
    This class manages the state of the map, items, and the agent's physical
    presence. It enforces game rules, processes agent actions, provides percepts,
    and handles the advanced 'Moving Wumpus' logic. It is designed to be
    completely independent of the UI and the agent's internal reasoning.
    """
    def __init__(self, size = None, pit_prob = None, number_of_wumpus = None):
        self.size = size if size is not None else config.MAP_SIZE 
        self.pit_prob = pit_prob if pit_prob is not None else config.PIT_PROBABILITY
        self.number_of_wumpus = number_of_wumpus if number_of_wumpus is not None else config.NUMBER_OF_WUMPUS
        self.number_of_gold = config.NUMBER_OF_GOLD

        self.agent_location = Point(*config.INITIAL_AGENT_LOCATION)
        self.agent_orientation = config.INITIAL_AGENT_ORIENTATION 
        self.agent_has_gold = False
        self.agent_has_arrow = config.INITIAL_AGENT_HAS_ARROW

        self.score = 0 
        self.game_over = False
        
        self.state = [[set() for _ in range(self.size)] for _ in range(self.size)]
        self.gold_location = None

        # Advance setting
        self.agent_action_count = 0
        self.wumpus_locations = []
        
        self.generate_map()

    def generate_map(self):
        """
        Randomly generate NxN maps with multiple K wumpus, adjustable pit density (pit_prob),
        provide concepts to the agent. 
        This map needs to meet the constraint of the game. 
        """

        cells = [Point(x, y) for x in range(self.size) for y in range(self.size)]
        start_cell = Point(0, 0)
        
        if start_cell in cells:
            cells.remove(start_cell)

        random.shuffle(cells)

        # Place gold
        self.gold_location = cells.pop()
        self.state[self.gold_location.y][self.gold_location.x] = 'G'

        # Place wumpus
        for _ in range(self.number_of_wumpus):
            coordinate = cells.pop()
            self.wumpus_locations.append(coordinate)
            self.state[coordinate.y][coordinate.x] = 'W'

        # Place pit
        for cell in cells:
            p = random.random() # float from [0.0, 1.0]
            if p < self.pit_prob:
                self.state[cell.y][cell.x] = 'P'

    def get_state(self) -> dict:
        """
        Package the current world state -> dictionary for display in UI.
        """
        # To do percept -> find correct dictionary
        return {
            'size': self.size,
            'state': self.state,
            'agent_location': self.agent_location,
            'agent_orientation': self.agent_orientation,
            'agent_has_arrow': self.agent_has_arrow,
            'agent_has_gold': self.agent_has_gold,
            'score': self.score,
            'game_over': self.game_over,
            # percepts
            # message
        }

    def get_percepts(self):
        pass

    def execute_action(self):
        pass

