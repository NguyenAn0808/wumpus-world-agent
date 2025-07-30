from .components import *

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
        # W(2, 2) <=> (S(2, 3) v S(3, 2) v S(2, 1) v S(1, 2)) | Left <=> (Right1 v Right2 v Right3 ...) 
        left_literal = Literal(left)
        right_literals = [Literal(r) for r in right]

        clause = frozenset([left_literal.negate(), *right_literals])
        CNF_clauses = {clause}

        for r in right_literals:
            CNF_clauses.add(frozenset([r.negate(), left_literal]))
        
        return CNF_clauses
    
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
        self.wumpus_rules.add(fact_clause)
        self.pit_rules.add(fact_clause)

