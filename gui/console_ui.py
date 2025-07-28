import time

class Orientation:
    EAST = 0
    WEST = 1
    NORTH = 2
    SOUTH = 3

DIRECTION_ARROWS = {
    Orientation.EAST: '>',
    Orientation.WEST: '<',
    Orientation.NORTH: '^',
    Orientation.SOUTH: 'v'
}

ORIENTATION_NAMES = {
    Orientation.EAST: 'EAST',
    Orientation.WEST: 'WEST',
    Orientation.NORTH: 'NORTH',
    Orientation.SOUTH: 'SOUTH'
}

def display_world(map_state: dict):
    size = map_state['size']
    state = map_state['state']
    agent_location = map_state['agent_location']
    agent_orientation = map_state['agent_orientation']
    score = map_state['score']
    game_over = map_state['game_over']
    message = map_state.get('message', '')

    CELL_WIDTH = 9
    top_border = "+" + ("-" * CELL_WIDTH + "+") * size

    print(top_border)
    for y in range(size - 1, -1, -1):
        row_left = "|"
        row_center = "|"
        row_right = "|"

        for x in range(size):
            items = state[y][x]
            left = ""
            center = ""
            right = ""

            # 1. Trái: Stench (S)
            if 'S' in items:
                left = "S"

            # 2. Phải: Breeze (B)
            if 'B' in items:
                right = "B"

            # 3. Giữa: Wumpus, Pit, Agent
            if 'W' in items: center += "W"
            if 'P' in items: center += "P"
            if 'G' in items: center += "G"  # Optional, hoặc cho ra hàng dưới nếu muốn

            if agent_location.x == x and agent_location.y == y:
                arrow = DIRECTION_ARROWS.get(agent_orientation, '>')
                center += f"A{arrow}"

            row_left += f" {left:<{CELL_WIDTH-2}} |"
            row_center += f" {center:^{CELL_WIDTH-2}} |"
            row_right += f" {right:>{CELL_WIDTH-2}} |"

        print(row_left)
        print(row_center)
        print(row_right)
        print(top_border)

    print("\n" + "="*40)
    print("AGENT STATUS & PERCEPTS:")
    print(f"  Location: ({agent_location.x}, {agent_location.y}) | Orientation: {ORIENTATION_NAMES.get(agent_orientation, '?')}")
    print(f"  Score: {score}")
    print(f"  Has Arrow: {'Yes' if map_state['agent_has_arrow'] else 'No'}")
    print(f"  Has Gold: {'Yes' if map_state['agent_has_gold'] else 'No'}")
    print(f"  Current Percepts: {', '.join([p.name if hasattr(p, 'name') else str(p) for p in map_state.get('percepts', set())])}")
    
    if message:
        print(f"\n  MESSAGE: {message}")
    
    if game_over:
        print("\n  !!! GAME OVER !!!")
    print("="*40 + "\n")
