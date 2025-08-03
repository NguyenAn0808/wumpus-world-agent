from simulation import *
from gui import *
from gui.game_app.game_app import GameApp

def add_percept_rules_to_kb(kb: KB, world: World, point: Point):
    """
    "Học" các luật chơi: Chỉ thêm các luật liên quan đến percept
    tại vị trí hiện tại vào KB.
    Hàm này chỉ được gọi một lần cho mỗi ô đã ghé thăm.
    """
    x, y = point.x, point.y
    adj_cells = world.get_adjacent_cells(point)

    # Nếu có các ô hàng xóm, thì mới có luật cho Breeze/Stench
    if not adj_cells:
        return

    # Tạo và thêm luật cho Breeze tại (x,y)
    breeze_literal_str = f"B{x}{y}"
    pit_literal_strs = [f"P{p.x}{p.y}" for p in adj_cells]
    pit_rules = KB.conversion_to_CNF(breeze_literal_str, pit_literal_strs)
    kb.tell(pit_rules, is_wumpus_rule=False)
    print(f"-> Agent learned the rule for Breeze at ({x},{y}).")

    # Tạo và thêm luật cho Stench tại (x,y)
    stench_literal_str = f"S{x}{y}"
    wumpus_literal_strs = [f"W{p.x}{p.y}" for p in adj_cells]
    wumpus_rules = KB.conversion_to_CNF(stench_literal_str, wumpus_literal_strs)
    kb.tell(wumpus_rules, is_wumpus_rule=True)
    print(f"-> Agent learned the rule for Stench at ({x},{y}).")

def update_kb_with_facts(kb: KB, world: World, point: Point):
    """
    Cập nhật KB với các sự thật (facts) từ vị trí hiện tại:
    1. Ô hiện tại chắc chắn an toàn.
    2. Các percept cảm nhận được.
    """
    x, y = point.x, point.y
    
    # Fact 1: Agent biết ô nó đang đứng là an toàn.
    kb.tell_fact(Literal(f"P{x}{y}", negated=True))
    kb.tell_fact(Literal(f"W{x}{y}", negated=True))
    print(f"-> Added fact: Cell ({x},{y}) is visited and safe (¬P{x}{y}, ¬W{x}{y}).")

    # Fact 2: Agent cảm nhận môi trường và thêm facts.
    percepts = world.get_percepts()
    
    if Percept.BREEZE in percepts:
        kb.tell_fact(Literal(f"B{x}{y}", negated=False))
        print(f"-> Added fact: Perceived a Breeze at ({x},{y}) (B{x}{y}).")
    else:
        kb.tell_fact(Literal(f"B{x}{y}", negated=True))
        print(f"-> Added fact: No Breeze at ({x},{y}) (¬B{x}{y}).")

    if Percept.STENCH in percepts:
        kb.tell_fact(Literal(f"S{x}{y}", negated=False))
        print(f"-> Added fact: Perceived a Stench at ({x},{y}) (S{x}{y}).")
    else:
        kb.tell_fact(Literal(f"S{x}{y}", negated=True))
        print(f"-> Added fact: No Stench at ({x},{y}) (¬S{x}{y}).")

def infer_cell_status(kb: KB, inference_engine: InferenceEngine, cells_to_check: list[Point]) -> dict[Point, CellStatus]:
    """
    Suy luận trạng thái của các ô (An toàn, Nguy hiểm, Không chắc chắn).
    Trả về một dictionary: Point -> CellStatus.
    """
    print("\n" + "="*50)
    print("AGENT IS INFERRING THE STATUS OF UNVISITED, ADJACENT CELLS")
    print("="*50)
    
    cell_statuses = {}
    
    for cell in cells_to_check:
        x, y = cell.x, cell.y
        print(f"\n--- Querying for cell ({x},{y}) ---")
        
        # --- KIỂM TRA AN TOÀN ---
        # Hỏi: KB |= ¬Pxy ?
        query_not_pit = Literal(f"P{x}{y}", negated=True)
        is_not_pit = inference_engine.ask_Pit(kb.pit_rules, query_not_pit)
        print(f"  - Asking if NOT a Pit (KB |= ¬P{x}{y}): {is_not_pit}")
        
        # Hỏi: KB |= ¬Wxy ?
        query_not_wumpus = Literal(f"W{x}{y}", negated=True)
        is_not_wumpus = inference_engine.ask_Wumpus(kb.wumpus_rules, query_not_wumpus)
        print(f"  - Asking if NOT a Wumpus (KB |= ¬W{x}{y}): {is_not_wumpus}")

        if is_not_pit and is_not_wumpus:
            cell_statuses[cell] = CellStatus.SAFE
            print(f"  => RESULT: {CellStatus.SAFE.value}")
            continue # Đã xác định là an toàn, chuyển sang ô tiếp theo

        # --- NẾU KHÔNG AN TOÀN, KIỂM TRA NGUY HIỂM ---
        # Hỏi: KB |= Pxy ?
        query_is_pit = Literal(f"P{x}{y}", negated=False)
        is_pit = inference_engine.ask_Pit(kb.pit_rules, query_is_pit)
        print(f"  - Asking if IS a Pit (KB |= P{x}{y}): {is_pit}")
        if is_pit:
            cell_statuses[cell] = CellStatus.DANGEROUS_PIT
            print(f"  => RESULT: {CellStatus.DANGEROUS_PIT.value}")
            continue

        # Hỏi: KB |= Wxy ?
        query_is_wumpus = Literal(f"W{x}{y}", negated=False)
        is_wumpus = inference_engine.ask_Wumpus(kb.wumpus_rules, query_is_wumpus)
        print(f"  - Asking if IS a Wumpus (KB |= W{x}{y}): {is_wumpus}")
        if is_wumpus:
            cell_statuses[cell] = CellStatus.DANGEROUS_WUMPUS
            print(f"  => RESULT: {CellStatus.DANGEROUS_WUMPUS.value}")
            continue

        # --- NẾU KHÔNG RƠI VÀO CÁC TRƯỜNG HỢP TRÊN ---
        cell_statuses[cell] = CellStatus.UNCERTAIN
        print(f"  => RESULT: {CellStatus.UNCERTAIN.value}")
            
    return cell_statuses

def main():
    # ... (phần khởi tạo không đổi) ...
    world = World()
    display_world(world.get_state())
    inference_engine = InferenceEngine()
    kb = KB()
    current_location = Point(0, 0)
    
    print("\n" + "="*50)
    print(f"AGENT IS AT ({current_location.x},{current_location.y}) AND IS THINKING...")
    print("="*50)

    add_percept_rules_to_kb(kb, world, current_location)
    update_kb_with_facts(kb, world, current_location)

    cells_to_check = world.get_adjacent_cells(current_location)
    
    # Gọi hàm suy luận mới
    statuses = infer_cell_status(kb, inference_engine, cells_to_check)

    # --- IN KẾT QUẢ CUỐI CÙNG ---
    print("\n" + "="*50)
    print("INFERENCE COMPLETE FOR THE CURRENT STEP")
    for cell, status in statuses.items():
        print(f"  - Cell ({cell.x},{cell.y}): {status.value}")
    print("="*50 + "\n")


if __name__ == "__main__":
    # main()

    # Test GUI
    game = GameApp()
    game.run()