from abc import ABC, abstractmethod

class GameMode(ABC):
    @abstractmethod
    def choose_next_decision():
        pass