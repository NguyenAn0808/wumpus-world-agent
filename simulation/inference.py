from .components import *
from collections import Counter

class InferenceEngine:
    """
    Implement from scratch using DPLL algorithm (Davis, Putnam, Logemann, Loveland) based on model checking 
    + Early termination
    + Pure symbol heuristic
    + Unit clause heuristic
    + Degree heuristic
    
    """
    
    def ask_Wumpus(self, KB: set[Clause], alpha: Literal) -> bool:
        """
        Checks if the Wumpus Knowledge Base (KB) entails a literal (alpha).
        e.g., ask_Wumpus(kb, Literal("W12", negated=True)) -> "Is it provably not a Wumpus at (1,2)?"
        """
        # To prove KB ╞ α, we check if (KB ∧ ¬α) is unsatisfiable.
        clauses = KB.union({frozenset([alpha.negate()])})
        return not self._dpll_satisfiable(clauses)

    def ask_Pit(self, KB: set[Clause], alpha: Literal) -> bool:
        """
        Checks if the Pit Knowledge Base (KB) entails a literal (alpha).
        e.g., ask_Pit(kb, Literal("P22")) -> "Is it provably a Pit at (2,2)?"
        """
        # To prove KB ╞ α, we check if (KB ∧ ¬α) is unsatisfiable.
        clauses = KB.union({frozenset([alpha.negate()])})
        return not self._dpll_satisfiable(clauses)
    
    def ask_safe(self, wumpus_kb: set[Clause], pit_kb: set[Clause], cell: Point) -> bool:
        """
        Checks if a cell can be proven to be safe.
        A cell is provably safe if AND ONLY IF:
        1. We can prove it has NO Wumpus (¬W).
        2. We can prove it has NO Pit (¬P).
        3. We CANNOT prove it HAS a Wumpus (¬(KB ╞ W)).
        4. We CANNOT prove it HAS a Pit (¬(KB ╞ P)).
        Conditions 3 and 4 are crucial for handling inconsistent KBs.
        """
        # --- KIỂM TRA ĐIỀU KIỆN "KHÔNG NGUY HIỂM" ---
        
        # 1. Chứng minh không có Wumpus
        is_wumpus_free = self.ask_Wumpus(wumpus_kb, Literal(f"W{cell.x}{cell.y}", negated=True))
        if not is_wumpus_free:
            return False # Không thể chứng minh là không có Wumpus -> Không an toàn.

        # 2. Chứng minh không có Hố
        is_pit_free = self.ask_Pit(pit_kb, Literal(f"P{cell.x}{cell.y}", negated=True))
        if not is_pit_free:
            return False # Không thể chứng minh là không có Hố -> Không an toàn.

        # --- KIỂM TRA CHÉO ĐỂ PHÁT HIỆN MÂU THUẪN ---
        # Các bước này cực kỳ quan trọng nếu KB có khả năng bị mâu thuẫn.
        # Nếu chúng ta có thể chứng minh cả ¬W và W, thì KB đã hỏng.
        # Trong trường hợp đó, không nên tin vào kết luận "an toàn".

        # 3. Kiểm tra xem có thể chứng minh CÓ Wumpus không
        is_proven_wumpus = self.ask_Wumpus(wumpus_kb, Literal(f"W{cell.x}{cell.y}", negated=False))
        if is_proven_wumpus:
            # Chúng ta đã chứng minh được cả ¬W và W. Đây là mâu thuẫn.
            # Không thể coi ô này là an toàn.
            print(f"WARNING: Inconsistent KB! Proved both W and ¬W for {cell}")
            return False

        # 4. Kiểm tra xem có thể chứng minh CÓ Hố không
        is_proven_pit = self.ask_Pit(pit_kb, Literal(f"P{cell.x}{cell.y}", negated=False))
        if is_proven_pit:
            # Chúng ta đã chứng minh được cả ¬P và P. Đây là mâu thuẫn.
            print(f"WARNING: Inconsistent KB! Proved both P and ¬P for {cell}")
            return False

        # Nếu vượt qua tất cả các bài kiểm tra, ô này thực sự an toàn.
        return True

    def ask_dangerous(self, wumpus_kb: set[Clause], pit_kb: set[Clause], cell: Point) -> bool:
        """
        Checks if a cell can be proven to be dangerous (contains either a Wumpus or a Pit).
        """
        # A cell is dangerous if we can prove Wumpus OR Pit.
        is_wumpus = self.ask_Wumpus(wumpus_kb, Literal(f"W{cell.x}{cell.y}", negated=False))
        if is_wumpus:
            return True
            
        is_pit = self.ask_Pit(pit_kb, Literal(f"P{cell.x}{cell.y}", negated=False))
        return is_pit

    # ------------------------------------------------------------------
    # INTERNAL DPLL IMPLEMENTATION
    # The following methods replace the old PL-Resolution logic.
    # ------------------------------------------------------------------

    def _dpll_satisfiable(self, clauses: set[Clause]) -> bool:
        """
        Top-level function to check if a set of clauses is satisfiable.
        """
        # Extract all unique symbol names (e.g., "P12", "W02") from the clauses.
        symbols = set()
        for clause in clauses:
            for literal in clause:
                symbols.add(literal.name)
        
        # Start the recursive DPLL process.
        return self._dpll(list(clauses), list(symbols), {})
    
    def _dpll(self, clauses: list[Clause], symbols: list[str], model: dict[str, bool]) -> bool:
        """
        The recursive core of the DPLL algorithm.
        `clauses`: A list of frozensets of Literals.
        `symbols`: A list of symbol names (strings) yet to be assigned.
        `model`: A dictionary mapping assigned symbol names to their boolean value (True/False).
        """
        
        # --- HEURISTIC 1: Early Termination ---
        is_satisfied, is_falsified = self._check_clauses_status(clauses, model)
        if is_falsified:
            return False # A clause is false, this branch of the search is invalid.
        if is_satisfied:
            return True # All clauses are satisfied, we have found a valid model.

        # --- HEURISTIC 2: Pure Symbol ---
        pure_symbol, value = self._find_pure_symbol(clauses, symbols, model)
        if pure_symbol:
            new_symbols = [s for s in symbols if s != pure_symbol]
            new_model = model.copy()
            new_model[pure_symbol] = value
            return self._dpll(clauses, new_symbols, new_model)

        # --- HEURISTIC 3: Unit Clause ---
        unit_symbol, value = self._find_unit_clause(clauses, model)
        if unit_symbol:
            new_symbols = [s for s in symbols if s != unit_symbol]
            new_model = model.copy()
            new_model[unit_symbol] = value
            return self._dpll(clauses, new_symbols, new_model)

        # --- Branching (Guessing with Degree Heuristic) ---
        symbol_to_try = self._select_symbol_by_degree(clauses, symbols, model)
        if not symbol_to_try:
             return True # No more symbols to try, must be satisfiable.

        remaining_symbols = [s for s in symbols if s != symbol_to_try]

        # Try assigning True to the chosen symbol
        model_true = model.copy()
        model_true[symbol_to_try] = True
        if self._dpll(clauses, remaining_symbols, model_true):
            return True

        # *** SỬA LỖI Ở ĐÂY ***
        # If assigning True fails, the result of this call is entirely dependent
        # on the result of assigning False.
        model_false = model.copy()
        model_false[symbol_to_try] = False
        return self._dpll(clauses, remaining_symbols, model_false)

    # ------------------------------------------------------------------
    # DPLL HELPER METHODS
    # ------------------------------------------------------------------

    def _check_clauses_status(self, clauses: list[Clause], model: dict[str, bool]):
        """
        Checks the status of all clauses against the current model.
        Returns a tuple: (all_clauses_are_satisfied, any_clause_is_falsified).
        """
        all_satisfied = True
        for clause in clauses:
            clause_value = self._evaluate_clause(clause, model)
            if clause_value is False:
                return False, True # Found a definitively false clause, short-circuit.
            if clause_value is None:
                all_satisfied = False # Found an unresolved clause, so not all are satisfied yet.
        return all_satisfied, False

    def _evaluate_clause(self, clause: Clause, model: dict[str, bool]):
        """
        Evaluates a single clause against the current model.
        Returns: True if the clause is satisfied.
                 False if the clause is falsified.
                 None if the clause is still unresolved.
        """
        has_unassigned_literals = False
        for literal in clause:
            if literal.name in model:
                # Check if the literal's value in the model makes it true
                if model[literal.name] is not literal.negated:
                    return True # One true literal makes the whole clause true.
            else:
                has_unassigned_literals = True
        
        if has_unassigned_literals:
            return None # Can't determine final value yet.
        else:
            return False # All literals are assigned and all are false.

    def _find_pure_symbol(self, clauses: list[Clause], symbols: list[str], model: dict[str, bool]):
        """
        Finds a symbol that only appears with one polarity (all positive or all negative)
        across all clauses that are not yet satisfied.
        """
        unassigned_symbols = {s for s in symbols if s not in model}
        if not unassigned_symbols:
            return None, None

        polarities = {} # {symbol_name: polarity_value} where value is True/False or 'impure'
        
        for symbol in unassigned_symbols:
            polarities[symbol] = None # Chưa thấy

        for clause in clauses:
            # Chỉ xét các mệnh đề chưa được giải quyết
            if self._evaluate_clause(clause, model) is None:
                for literal in clause:
                    if literal.name in polarities:
                        # Nếu ký hiệu này đã bị đánh dấu là không thuần khiết, bỏ qua
                        if polarities[literal.name] == 'impure':
                            continue
                        
                        current_polarity = not literal.negated # True for positive, False for negative
                        
                        # Nếu đây là lần đầu thấy ký hiệu này
                        if polarities[literal.name] is None:
                            polarities[literal.name] = current_polarity
                        # Nếu thấy cực tính khác với lần trước -> không thuần khiết
                        elif polarities[literal.name] != current_polarity:
                            polarities[literal.name] = 'impure'

        # Tìm ký hiệu thuần túy đầu tiên
        for symbol, value in polarities.items():
            if value is not None and value != 'impure':
                return symbol, value
        
        return None, None

    def _find_unit_clause(self, clauses: list[Clause], model: dict[str, bool]):
        """Finds a clause that has been reduced to a single unassigned literal."""
        for clause in clauses:
            if self._evaluate_clause(clause, model) is None: # Only check unresolved clauses
                unassigned_literal = None
                num_unassigned = 0
                for literal in clause:
                    if literal.name not in model:
                        num_unassigned += 1
                        unassigned_literal = literal
                
                if num_unassigned == 1:
                    # This is a unit clause. The literal must be assigned a value to make the clause true.
                    value = not unassigned_literal.negated
                    return unassigned_literal.name, value
        return None, None

    def _select_symbol_by_degree(self, clauses: list[Clause], symbols: list[str], model: dict[str, bool]) -> str:
        """Selects the next symbol to branch on using the Degree Heuristic."""
        unassigned_symbols = [s for s in symbols if s not in model]
        if not unassigned_symbols:
            return None

        # Count occurrences of unassigned symbols in unresolved clauses
        counter = Counter()
        for clause in clauses:
            if self._evaluate_clause(clause, model) is None:
                for literal in clause:
                    if literal.name in unassigned_symbols:
                        counter[literal.name] += 1
        
        if not counter:
            return unassigned_symbols[0] # Fallback: just pick the first one

        # Return the symbol that appears most frequently
        return counter.most_common(1)[0][0]
