"""
CLTMS
Robust Logical Truth Maintenance System with:

PART 1
Boolean Constraint Propagation

PART 2
Dependency Directed Backtracking

Implements
Node
Clause
BCP queue propagation
Contradiction detection
Nogood learning
Cycle prevention
"""

from enum import Enum
from collections import deque
from typing import List, Dict, Optional, Set


# ============================================================
# POLARITY
# ============================================================

class Polarity(Enum):
    TRUE = 1
    FALSE = 2
    UNKNOWN = 3


# ============================================================
# PART 1.1
# NODE ARCHITECTURE
# ============================================================

class Node:

    def __init__(self, node_id, datum):
        self.id = node_id
        self.datum = datum

        self.value = Polarity.UNKNOWN

        self.assumption = False
        self.decision_level = 0

        # history of all justifications
        self.justifications = []

        # current support
        self.current_support = None

        # clauses containing this node
        self.clauses = []

        # nodes that depend on this node
        self.consequences = []

    def __repr__(self):
        return f"<Node {self.id} {self.datum} {self.value.name}>"


# ============================================================
# PART 1.1
# CLAUSE ARCHITECTURE
# ============================================================

class Clause:

    def __init__(self, positives, negatives, learned=False):
        self.positives = positives
        self.negatives = negatives
        self.learned = learned

        for n in positives + negatives:
            n.clauses.append(self)

    def __repr__(self):
        p = [n.datum for n in self.positives]
        n = [n.datum for n in self.negatives]
        return f"<Clause +{p} -{n}>"


# ============================================================
# CLTMS
# ============================================================

class CLTMS:

    def __init__(self, name="CLTMS"):
        self.name = name
        self.nodes: Dict[int, Node] = {}
        self.node_counter = 0

        self.clauses: List[Clause] = []

        # BCP queue
        self.queue = deque()

        # assumption stack
        self.assumption_stack = []

    # ============================================================
    # NODE CREATION
    # ============================================================

    def create_node(self, datum):
        self.node_counter += 1
        n = Node(self.node_counter, datum)
        self.nodes[n.id] = n
        return n

    # ============================================================
    # PART 1.3
    # CYCLE DETECTION
    # ============================================================

    def depends_on(self, start, target, visited=None):

        if visited is None:
            visited = set()

        if start == target:
            return True

        visited.add(start)

        for j in start.justifications:
            for ant in j:
                if ant not in visited:
                    if self.depends_on(ant, target, visited):
                        return True

        return False

    # ============================================================
    # CLAUSE ADDITION
    # ============================================================

    def add_clause(self, positives, negatives):

        clause = Clause(positives, negatives)

        self.clauses.append(clause)

        self.queue.append(clause)

        self.propagate()

    # ============================================================
    # PART 1.2
    # CLAUSE EVALUATION
    # ============================================================

    def evaluate_clause(self, clause):

        unknown_literals = []

        for n in clause.positives:

            if n.value == Polarity.TRUE:
                return "SATISFIED"

            if n.value == Polarity.UNKNOWN:
                unknown_literals.append((n, Polarity.TRUE))

        for n in clause.negatives:

            if n.value == Polarity.FALSE:
                return "SATISFIED"

            if n.value == Polarity.UNKNOWN:
                unknown_literals.append((n, Polarity.FALSE))

        if len(unknown_literals) == 0:
            return "VIOLATED"

        if len(unknown_literals) == 1:
            node, value = unknown_literals[0]
            return ("UNIT", node, value)

        return "UNRESOLVED"

    # ============================================================
    # PART 1.2
    # BOOLEAN CONSTRAINT PROPAGATION QUEUE
    # ============================================================

    def propagate(self):

        while self.queue:

            clause = self.queue.popleft()

            result = self.evaluate_clause(clause)

            if result == "SATISFIED":
                continue

            if result == "VIOLATED":
                self.handle_contradiction(clause)
                continue

            if isinstance(result, tuple):

                _, node, value = result

                if node.value == Polarity.UNKNOWN:
                    node.value = value
                    node.current_support = clause

                    for c in node.clauses:
                        self.queue.append(c)

    # ============================================================
    # ASSUMPTIONS
    # ============================================================

    def assume(self, node, value):

        node.assumption = True
        node.value = value

        self.assumption_stack.append(node)

        for c in node.clauses:
            self.queue.append(c)

        self.propagate()

    # ============================================================
    # PART 2.1
    # CONTRADICTION DETECTION
    # ============================================================

    def handle_contradiction(self, clause):

        print("Contradiction detected")

        conflict_set = self.trace_conflict(clause)

        nogood = self.build_nogood(conflict_set)

        self.clauses.append(nogood)

        culprit = next(iter(conflict_set))

        print("Retracting", culprit)

        self.retract(culprit)

    # ============================================================
    # PART 2.2
    # TRACE CONFLICT SET
    # ============================================================

    def trace_conflict(self, clause):

        conflict = set()

        for n in clause.positives + clause.negatives:
            if n.assumption:
                conflict.add(n)

        return conflict

    # ============================================================
    # PART 2.2
    # BUILD NOGOOD CLAUSE
    # ============================================================

    def build_nogood(self, conflict_set):

        negatives = list(conflict_set)

        clause = Clause([], negatives, learned=True)

        print("Nogood learned", clause)

        return clause

    # ============================================================
    # RETRACTION
    # ============================================================

    def retract(self, node):

        node.value = Polarity.UNKNOWN
        node.assumption = False

        for c in node.clauses:
            self.queue.append(c)

        self.propagate()

    # ============================================================
    # LTRE INTERFACE METHODS
    # ============================================================

    def enable_assumption(self, node, polarity, informant=None):
        self.assume(node, polarity)

    def retract_assumption(self, node, informant=None):
        self.retract(node)

    def is_true(self, node):
        return node.value == Polarity.TRUE

    def is_false(self, node):
        return node.value == Polarity.FALSE

    def add_support(self, consequent, antecedents, informant=None):
        # Cycle detection: skip if consequent already supports any antecedent
        for ant in antecedents:
            if self.depends_on(ant, consequent):
                print(f"Cycle detected: skipping support for {consequent.datum}")
                return

        # Record justification
        consequent.justifications.append(antecedents[:])

        # Horn clause: ant1 ∧ ant2 ∧ ... → consequent
        # Represented as: consequent ∨ ¬ant1 ∨ ¬ant2 ∨ ...
        self.add_clause(positives=[consequent], negatives=antecedents)

    def why(self, node):
        print(f"Node {node.datum}: {node.value.name}")
        if node.current_support:
            print(f"  Supported by clause: {node.current_support}")
        elif node.assumption:
            print(f"  Assumed")
        else:
            print(f"  No support")
