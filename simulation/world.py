import config
import random

from .components import Orientation, Action, Point, Percept

class World:
    def __init__(self, size=None, pit_prob=None, number_of_wumpus=None):
        self.size = size or config.MAP_SIZE
        self.pit_prob = pit_prob or config.PIT_PROBABILITY
        self.number_of_wumpus = number_of_wumpus or config.NUMBER_OF_WUMPUS

        self.agent_location = Point(*config.INITIAL_AGENT_LOCATION)
        self.agent_orientation = getattr(Orientation, config.INITIAL_AGENT_ORIENTATION.upper())

        self.agent_has_gold = False
        self.agent_has_arrow = config.INITIAL_AGENT_HAS_ARROW

        self.score = 0
        self.game_over = False
        self.agent_action_count = 0
        self.wumpus_killed = False

        self.state = [[set() for _ in range(self.size)] for _ in range(self.size)]
        self.wumpus_locations = []
        self.current_percepts = set()
        self.message = ""

        self.generate_map()

    def generate_map(self):
        cells = [Point(x, y) for x in range(self.size) for y in range(self.size)]
        cells.remove(Point(0, 0))
        random.shuffle(cells)

        if cells:
            gold = cells.pop()
            self.state[gold.y][gold.x].add('G')

        for _ in range(self.number_of_wumpus):
            if not cells: break
            pos = cells.pop()
            self.wumpus_locations.append(pos)
            self.state[pos.y][pos.x].add('W')
            self._add_adjacent_percept(pos, 'S')

        for cell in cells:
            if random.random() < self.pit_prob:
                self.state[cell.y][cell.x].add('P')
                self._add_adjacent_percept(cell, 'B')

    def _add_adjacent_percept(self, center: Point, char: str):
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            x, y = center.x + dx, center.y + dy
            if 0 <= x < self.size and 0 <= y < self.size:
                self.state[y][x].add(char)

    def get_state(self):
        return {
            'size': self.size,
            'state': self.state,
            'agent_location': self.agent_location,
            'agent_orientation': self.agent_orientation,
            'agent_has_arrow': self.agent_has_arrow,
            'agent_has_gold': self.agent_has_gold,
            'score': self.score,
            'game_over': self.game_over,
            'percepts': self.current_percepts,
            'message': self.message,
        }

    def get_percepts(self):
        percepts = set()
        items = self.state[self.agent_location.y][self.agent_location.x]
        if 'G' in items: percepts.add(Percept.GLITTER)
        if 'S' in items: percepts.add(Percept.STENCH)
        if 'B' in items: percepts.add(Percept.BREEZE)
        self.current_percepts = percepts
        return percepts
