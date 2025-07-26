from simulation import *

def display_world(map_state: dict):
    """
    Print the state of the map (including large squares representing each cell (x, y) and its value)
    """

    size = map_state['size']
    state = map_state['state']
    agent_location = map_state['agent_location']
    agent_orientation = map_state['agent_orientation']
    score = map_state['score']
    game_over = map_state['game_over']

    matrix = [[{} for _ in range(size)] for _ in range(size)]

    CELL_WIDTH = 9
    top_border = "+" + ("-" * CELL_WIDTH + "+") * size
    
    print(top_border)
    for y in range(size - 1, -1, -1):
        main_line = "|"

        for x in range(size):
            # Value of each cell
            cell_content = ""
            
            # Check movement of Agent
            # if agent_location.x == x and agent_location.y == y:
            #     arrow = DIRECTION_ARROWS.get(agent_orientation, '?')
            #     cell_content += f"A{arrow}"
            
            # 2. Kiểm tra các vật phẩm khác
            items = state[y][x]
            if 'W' in items: cell_content += "W"
            if 'P' in items: cell_content += "P"
            if 'G' in items: cell_content += "G"
            
            # Thêm nội dung vào hàng, căn giữa
            main_line += f" {cell_content:^{CELL_WIDTH-2}} |"
        
        # In hàng chính và đường viền dưới
        print(main_line)
        print(top_border)

    print("\n" + "="*40)
    print("AGENT STATUS & PERCEPTS:")
    print(f"  Location: ({agent_location.x}, {agent_location.y}) | Orientation: {agent_orientation}")
    print(f"  Score: {score}")

    if game_over:
        print("\n  !!! GAME OVER !!!")
    print("="*40 + "\n")