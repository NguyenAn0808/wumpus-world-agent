from simulation import *
from gui.console_ui import display_world

def main():
    my_world = World()
    current_state = my_world.get_state()

    display_world(current_state)

if __name__ == "__main__":
    main()