from .components import *
from collections import Counter

class InferenceEngine:
    """
    Implement from scratch using DPLL algorithm (Davis, Putnam, Logemann, Loveland) based on model checking 
    + Early termination
    + Pure symbol heuristic
    + Unit clause heuristic
    + MOMS (Maximum Occurrences in clauses of Minimum Size) heuristic
    """
    
    def ask_Wumpus(self, KB: set[Clause], alpha: Literal) -> bool:
        """
        Checks if the Wumpus Knowledge Base (KB) entails a literal (alpha).
        To prove KB ╞ α, we check if (KB ∧ ¬α) is unsatisfiable.
        """
        clauses = KB.union({frozenset([alpha.negate()])})
        return not self.dpll_satisfiable(clauses)

    def ask_Pit(self, KB: set[Clause], alpha: Literal) -> bool:
        """
        Checks if the Pit Knowledge Base (KB) entails a literal (alpha).
        """
        clauses = KB.union({frozenset([alpha.negate()])})
        return not self.dpll_satisfiable(clauses)
    
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
        
        # 1
        is_wumpus_free = self.ask_Wumpus(wumpus_kb, Literal(f"W{cell.x}{cell.y}", negated=True))
        if not is_wumpus_free:
            return False 

        # 2
        is_pit_free = self.ask_Pit(pit_kb, Literal(f"P{cell.x}{cell.y}", negated=True))
        if not is_pit_free:
            return False 

        # 3
        is_proven_wumpus = self.ask_Wumpus(wumpus_kb, Literal(f"W{cell.x}{cell.y}", negated=False))
        if is_proven_wumpus:
            print(f"WARNING: Inconsistent KB! Proved both W and ¬W for {cell}")
            return False

        # 4
        is_proven_pit = self.ask_Pit(pit_kb, Literal(f"P{cell.x}{cell.y}", negated=False))
        if is_proven_pit:
            print(f"WARNING: Inconsistent KB! Proved both P and ¬P for {cell}")
            return False

        return True
    
    def dpll_satisfiable(self, clauses: set[Clause]) -> bool:
        """
        Top-level function to check if a set of clauses is satisfiable.
        """

        symbols = set()
        for clause in clauses:
            for literal in clause:
                symbols.add(literal.name)
        
        # Start the recursive DPLL process.
        return self.dpll(list(clauses), list(symbols), {})
    
    def dpll(self, clauses: list[Clause], symbols: list[str], model: dict[str, bool]) -> bool:
        """
        The recursive core of the DPLL algorithm.
        model: A dictionary mapping assigned symbol names to their boolean value (True/False).
        """
        
        # --- Early Termination ---
        is_satisfied, is_falsified = self.check_clauses_status(clauses, model)
        if is_falsified:
            return False # some clause in clauses is false -> False
        if is_satisfied:
            return True # All clauses are satisfied, we have found a valid model.

        # --- Pure Symbol Heuristic---
        pure_symbol, value = self.find_pure_symbol(clauses, symbols, model)
        if pure_symbol:
            new_symbols = [s for s in symbols if s != pure_symbol]
            new_model = model.copy()
            new_model[pure_symbol] = value
            return self.dpll(clauses, new_symbols, new_model)

        # --- Unit Clause Heuristic ---
        unit_symbol, value = self.find_unit_clause(clauses, model)
        if unit_symbol:
            new_symbols = [s for s in symbols if s != unit_symbol]
            new_model = model.copy()
            new_model[unit_symbol] = value
            return self.dpll(clauses, new_symbols, new_model)

        # --- MOMS Heuristic ---
        symbol_to_try = self.select_symbol_by_MOMS(clauses, symbols, model)
        if not symbol_to_try:
             return True # No more symbols to try, must be satisfiable.

        remaining_symbols = [s for s in symbols if s != symbol_to_try]

        # Try assigning True to the chosen symbol
        model_true = model.copy()
        model_true[symbol_to_try] = True
        if self.dpll(clauses, remaining_symbols, model_true):
            return True

        # If assigning True fails, the result of this call is entirely dependent
        # on the result of assigning False.
        model_false = model.copy()
        model_false[symbol_to_try] = False
        return self.dpll(clauses, remaining_symbols, model_false)

    def check_clauses_status(self, clauses: list[Clause], model: dict[str, bool]):
        """
        Checks the status of all clauses against the current model.
        Returns a tuple: (all_clauses_are_satisfied, any_clause_is_falsified).
        """
        all_satisfied = True
        for clause in clauses:
            clause_value = self.evaluate_clause(clause, model)

            if clause_value is False:
                return False, True # Found a definitively false clause, short-circuit.
            
            if clause_value is None:
                all_satisfied = False # Found an unresolved clause, so not all are satisfied yet.

        return all_satisfied, False

    def evaluate_clause(self, clause: Clause, model: dict[str, bool]):
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

    def find_pure_symbol(self, clauses: list[Clause], symbols: list[str], model: dict[str, bool]):
        """
        Finds a symbol that only appears with one polarity (all positive or all negative) 
        across all clauses that are not yet satisfied.
        """
        unassigned_symbols = {s for s in symbols if s not in model}
        pure_symbols = {} # {symbol_name: polarity (True/False)}
        
        for s in unassigned_symbols:
            pure_symbols[s] = None

        for clause in clauses:
            if self.evaluate_clause(clause, model) is None:

                for literal in clause:
                    if literal.name in pure_symbols:
                        polarity = not literal.negated

                        if pure_symbols[literal.name] is None:
                            pure_symbols[literal.name] = polarity

                        elif pure_symbols[literal.name] != polarity:
                            del pure_symbols[literal.name]

        # Take pure symbol
        if pure_symbols:
            symbol, value = pure_symbols.popitem()
            return symbol, value
        
        return None, None

    def find_unit_clause(self, clauses: list[Clause], model: dict[str, bool]):
        """
        Finds a clause that has been reduced to a single unassigned literal.
        """
        for clause in clauses:
            if self.evaluate_clause(clause, model) is None: # Only check unresolved clauses
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

    def select_symbol_by_MOMS(self, clauses: list[Clause], symbols: list[str], model: dict[str, bool]) -> str:
        """Selects the next symbol to branch on using the Degree Heuristic."""
        unassigned_symbols = [s for s in symbols if s not in model]
        if not unassigned_symbols:
            return None

        unresolved_clauses = [c for c in clauses if self.evaluate_clause(c, model) is None]
        if not unresolved_clauses:
            return unassigned_symbols[0] # Fallback
        
        min_len = float('inf')
        for c in unresolved_clauses:
            min_len = min(min_len, len(c))

        # Just find the minimum length clause
        shortest_clauses = [c for c in unresolved_clauses if len(c) == min_len]

        # Count occurrences of unassigned symbols in unresolved clauses
        counter = Counter()
        for c in shortest_clauses:
            for literal in c:
                if literal.name in unassigned_symbols:
                    counter[literal.name] += 1
        
        if not counter:
            return unassigned_symbols[0] # Fallback: just pick the first one

        # Return the symbol that appears most frequently
        return counter.most_common(1)[0][0]