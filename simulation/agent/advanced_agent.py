from .hybrid_agent import HybridAgent
from .agent import Agent
from simulation.components import Action, Percept
from config import WUMPUS_MOVE_INTERVAL

class AdvancedAgent(HybridAgent):
    """
    Advanced Agent giống HybridAgent nâng cấp
    """

    def __init__(self, location, direction, size):
        super().__init__(location, direction, size)
        self.action_count = 0

    def choose_action(self):
        """
        Chọn hành động như HybridAgent (từ KB, inference).
        (Phần này chỉnh inference sau).
        """
        return super().choose_action()

    def after_action(self, action: Action):
        """
        Tăng biến đếm sau mỗi hành động.
        """
        self.action_count += 1

    def need_wumpus_move(self) -> bool:
        """
        Kiểm tra có cần cho Wumpus di chuyển hay chưa.
        """
        return self.action_count > 0 and self.action_count % WUMPUS_MOVE_INTERVAL == 0
