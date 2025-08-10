from simulation import *
from gui.console_ui import display_world
from gui.game_app.game_app import GameApp
from config import INITIAL_AGENT_LOCATION, INITIAL_AGENT_DIRECTION, MAP_SIZE

def main():
    agent = RandomAgent(INITIAL_AGENT_LOCATION, INITIAL_AGENT_DIRECTION, MAP_SIZE)
    game = GamePlay(agent = agent, display_callback = display_world)
    game.run_console()

        # GUI
    #game = GameApp()

if __name__ == "__main__":
    main()
      
