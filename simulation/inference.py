from .components import *

class InferenceEngine:
    """
    Implement from scratch using Propositional Logic - Resolution
    """
    def is_tautology(self, clause: Clause) -> bool:
        """
        Function to check if clause is a tautology ({P, ~P}, ...)
        """

        for literal in clause:
            if literal.negate() in clause:
                return True
            
        return False
    
    def PL_Resolve(self, C1: Clause, C2: Clause) -> set[Clause]:
        """
        Function to resolve two clauses
        """
        resolvents = set()

        for l1 in C1:
            if l1.negate() in C2:
                new_clause = (C1 - {l1}).union(C2 - {l1.negate()})

                if not self.is_tautology(new_clause):
                    resolvents.add(new_clause)

        return resolvents

    def PL_Resolution(self, KB: set[Clause], alpha: Literal) -> bool:
        """
        Function to proof by contradiction (resolution algorithm). 
        To show KB entails alpha, prove KB entails not alpha is unsatisfiable
        """

        negation_alpha = alpha.negate()
        new_clause = set()

        clauses = list(KB)
        clauses.append(frozenset([negation_alpha]))

        # Optimize soon
        while True:
            n = len(clauses)
            pairs = [(clauses[i], clauses[j]) for i in range(n) for j in range(i + 1, n)]
            for (Ci, Cj) in pairs:
                resolvents = self.PL_Resolve(Ci, Cj)
                
                if frozenset() in resolvents:
                    return True
                
                new_clause.update(resolvents)

            clauses_set = set(clauses)
            if new_clause.issubset(clauses_set):
                return False
            
            for clause in new_clause:
                if clause not in clauses_set:
                    clauses.append(clause) 

    def ask_Wumpus(self, KB: set[Clause], alpha: Literal) -> bool:
        return self.PL_Resolution(KB, alpha)

    def ask_Pit(self, KB: set[Clause], alpha: Literal) -> bool:
        return self.PL_Resolution(KB, alpha)
    

    