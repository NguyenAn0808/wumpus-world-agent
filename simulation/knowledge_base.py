from .components import *
import traceback

class KB:
    """
    Class stores the agent's knowledge as a set of CNF clauses.
    It seperates KB about Pits and Wumpuses to optimize for PL-Resolution
    """ 

    def __init__(self):
        # Type hint
        self.pit_rules: set[Clause] = set() 
        self.wumpus_rules: set[Clause] = set()

    @staticmethod 
    def conversion_to_CNF(left: str, right: list[str]) -> set[Clause]: 
        # W(2, 2) <=> (S(2, 3) ^ S(3, 2) ^ S(2, 1) ^ S(1, 2)) | Left <=> (Right1 ^ Right2 ^ Right3 ...) 
        left_literal = Literal(left)
        right_literals = [Literal(r) for r in right]

        clause = frozenset([left_literal.negate(), *right_literals])
        CNF_clauses = {clause}

        for r in right_literals:
            CNF_clauses.add(frozenset([r.negate(), left_literal]))
        
        return CNF_clauses
    
    def retract_and_tell_percept_facts(self, cell: Point, new_percepts: set[Percept]):
        x, y = cell.x, cell.y
        
        # --- STENCH ---
        stench_literal = Literal(f"S{x}{y}")

        self.wumpus_rules.discard(frozenset([stench_literal]))
        self.wumpus_rules.discard(frozenset([stench_literal.negate()]))
        
        if Percept.STENCH in new_percepts:
            self.tell_fact(stench_literal)
        else:
            self.tell_fact(stench_literal.negate())

        # --- BREEZE ---
        breeze_literal = Literal(f"B{x}{y}")

        self.pit_rules.discard(frozenset([breeze_literal]))
        self.pit_rules.discard(frozenset([breeze_literal.negate()]))

        if Percept.BREEZE in new_percepts:
            self.tell_fact(breeze_literal)
        else:
            self.tell_fact(breeze_literal.negate())
            
        # --- GLITTER ---
        glitter_literal = Literal(f"G{x}{y}")
        self.wumpus_rules.discard(frozenset([glitter_literal]))
        self.pit_rules.discard(frozenset([glitter_literal]))
        self.wumpus_rules.discard(frozenset([glitter_literal.negate()]))
        self.pit_rules.discard(frozenset([glitter_literal.negate()]))

        if Percept.GLITTER in new_percepts:
            self.tell_fact(glitter_literal) 
        else:
            self.tell_fact(glitter_literal.negate())
            
    def tell(self, KB_clauses : set[Clause], is_wumpus_rule: bool):
        """
        Function to add new rules to the appropriate KB
        """
        if is_wumpus_rule:
            self.wumpus_rules.update(KB_clauses)
        else:
            self.pit_rules.update(KB_clauses)

    def tell_fact(self, fact: Literal):
        """
        Function to add a single literal fact to both KBs 
        """
        fact_clause = frozenset([fact])
        fact_name = fact.name
        
        # Pit_rules (P, B)
        if fact_name.startswith('P') or fact_name.startswith('B'):
            self.pit_rules.add(fact_clause)

        # Wumpus_rules (W, S)
        elif fact_name.startswith('W') or fact_name.startswith('S'):
            self.wumpus_rules.add(fact_clause)

        elif fact_name.startswith('G'):
            self.pit_rules.add(fact_clause)

    def process_scream_event(self):
        clauses_to_remove = set()
        
        for clause in self.wumpus_rules:
            if len(clause) == 1:
                literal = next(iter(clause))
                
                if literal.name.startswith('S'):
                    clauses_to_remove.add(clause)
        
        self.wumpus_rules.difference_update(clauses_to_remove)
        
        if clauses_to_remove:
            print(f"Removed {len(clauses_to_remove)} old Stench facts from Wumpus KB.")