from simulation import *
from gui import *
from gui.game_app.game_app import GameApp

def main():
    game = GamePlay(display_callback = display_world)
    game.run_console()

    # GUI
    # game = GameApp()
    # game.run()

if __name__ == "__main__":
    main()  