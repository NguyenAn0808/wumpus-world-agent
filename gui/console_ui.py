import time
from simulation.components import *

def display_world(map_state: dict):
    size = map_state.get('size', 4)
    state = map_state.get('state', [[]])
    agent_location = map_state.get('agent_location', Point(0,0))
    agent_direction = map_state.get('agent_direction', Direction.EAST)
    score = map_state.get('score', 0)
    stop_game = map_state.get('stop_game', False)
    game_status = map_state.get('game_status', None)
    message = map_state.get('message', '')

    safe_cells = map_state.get('known_safe_cells', set())
    visited_cells = map_state.get('known_visited_cells', set())

    CELL_WIDTH = 9
    horizontal_border = "+" + ("-" * CELL_WIDTH + "+") * size

    # --- BẮT ĐẦU VẼ BẢN ĐỒ ---
    print(horizontal_border)
    
    # Vòng lặp này vẽ từng hàng của bản đồ, từ trên xuống (y lớn đến y nhỏ)
    for y in range(size - 1, -1, -1):
        row_1_percepts = "|"
        row_2_objects = "|"
        row_3_knowledge = "|"

        # Vòng lặp này xây dựng nội dung cho một hàng
        for x in range(size):
            cell_point = Point(x, y)
            items = state[y][x]
            
            # Dòng 1: Percepts (Breeze, Stench)
            percept_str = ""
            if 'S' in items: percept_str += "S "
            if 'B' in items: percept_str += "B"
            row_1_percepts += f" {percept_str:<{CELL_WIDTH-2}} |"

            # Dòng 2: World Objects (Wumpus, Pit, Gold, Agent)
            center_str = ""
            if 'W' in items: center_str += "W "
            if 'P' in items: center_str += "P "
            if 'G' in items: center_str += "G "
            if agent_location == cell_point:
                arrow = DIRECTION_ARROWS.get(agent_direction, '>')
                center_str += f"A{arrow}"
            row_2_objects += f" {center_str:^{CELL_WIDTH-2}} |"

            # Dòng 3: Agent Knowledge (Visited, Safe)
            knowledge_str = ""
            if cell_point in visited_cells:
                knowledge_str += "V "
            if cell_point in safe_cells and cell_point not in visited_cells:
                knowledge_str += "OK "
            row_3_knowledge += f" {knowledge_str:>{CELL_WIDTH-2}} |"

        # In ra 3 dòng text tạo nên một hàng của bản đồ
        print(row_1_percepts)
        print(row_2_objects)
        print(row_3_knowledge)
        print(horizontal_border)
    # --- KẾT THÚC VẼ BẢN ĐỒ (Vòng lặp for y kết thúc ở đây) ---


    # --- BẮT ĐẦU VẼ KHỐI STATUS (Code này nằm ngoài vòng lặp) ---
    current_percepts_set = set()
    if is_valid(agent_location, size):
        loc_items = state[agent_location.y][agent_location.x]
        if 'S' in loc_items: current_percepts_set.add("Stench")
        if 'B' in loc_items: current_percepts_set.add("Breeze")
        if 'G' in loc_items: current_percepts_set.add("Glitter")

    print("\n" + "="*40)
    print("AGENT STATUS & PERCEPTS:")
    print(f"  Location: ({agent_location.x}, {agent_location.y}) | Direction: {DIRECTION_NAMES.get(agent_direction, '?')}")
    print(f"  Score: {score}")
    print(f"  Has Arrow: {'Yes' if map_state.get('agent_has_arrow', False) else 'No'}")
    print(f"  Has Gold: {'Yes' if map_state.get('agent_has_gold', False) else 'No'}")
    print(f"  Current Percepts: {', '.join(current_percepts_set) if current_percepts_set else 'None'}")

    if message:
        print(f"\n  MESSAGE: {message}")
    
    if stop_game:
        status_name = game_status.name if game_status else "CLIMB FAIL"
        print(f"\n  !!! {status_name} !!!")
    print("="*45 + "\n")
    # --- KẾT THÚC VẼ KHỐI STATUS ---