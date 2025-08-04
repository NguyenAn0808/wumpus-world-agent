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
    
    def retract_and_tell_percept_facts(self, cell: Point, percepts: set[Percept]):
        """
        Rút lại các sự thật cũ về percepts tại `cell` và thêm vào các sự thật mới.
        """
        x, y = cell.x, cell.y
        
        # Các literal có thể có về percepts tại ô này
        breeze_pos = frozenset([Literal(f"B{x}{y}")])
        breeze_neg = frozenset([Literal(f"B{x}{y}", negated=True)])
        stench_pos = frozenset([Literal(f"S{x}{y}")])
        stench_neg = frozenset([Literal(f"S{x}{y}", negated=True)])

        # Rút lại (xóa) các sự thật cũ
        self.pit_rules.discard(breeze_pos)
        self.pit_rules.discard(breeze_neg)
        self.wumpus_rules.discard(stench_pos)
        self.wumpus_rules.discard(stench_neg)

        # Thêm vào sự thật mới
        if Percept.BREEZE in percepts:
            self.tell_fact(Literal(f"B{x}{y}"))
        else:
            self.tell_fact(Literal(f"B{x}{y}", negated=True))

        if Percept.STENCH in percepts:
            self.tell_fact(Literal(f"S{x}{y}"))
        else:
            self.tell_fact(Literal(f"S{x}{y}", negated=True))
            
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

