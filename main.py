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
<<<<<<< HEAD
    # main()
    game = GameApp()
      
=======
    main()
>>>>>>> 041cabf514f4bb9f114b867d348f799ed5c9fc57
