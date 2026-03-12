# LTRE — Logic-based Truth-maintenance Rule Engine

A Python implementation of a clause-based Truth Maintenance System (CLTMS) with a
forward-chaining rule engine. The system is split into two layers:

| File | Role |
|------|------|
| `cltms.py` | Clause-based TMS — nodes, clauses, BCP, DDB, cycle detection |
| `cltre.py` | Rule engine — unification, declarative rules, KB fetch |
| `test_suite.py` | Runnable demonstration of all three tasks |

---

## Architectural Choices

## CLTMS — BCP, DDB, and Well-Founded Support

### BCP (Part 1) — Boolean Constraint Propagation Queue

Every derived fact is represented as a Horn clause
`consequent ∨ ¬ant₁ ∨ ¬ant₂ ∨ …` in `CLTMS.clauses`. A queue-based BCP loop
evaluates each clause after any node value changes.

#### Queue Design Choice: `collections.deque` (FIFO)

The BCP queue (`self.queue`) is a `collections.deque` processed in **FIFO order**
(`appendleft` / `popleft`). This was a deliberate architectural choice for three reasons:

1. **O(1) enqueue and dequeue.** A plain `list.pop(0)` costs O(n) per operation because
   it shifts every remaining element. `deque.popleft()` is O(1), keeping each propagation
   step constant-time regardless of queue depth.

2. **Breadth-first unit propagation.** FIFO ordering means all clauses that were affected
   by the *same* node assignment are processed before the clauses triggered by the forced
   values those clauses produce. This breadth-first sweep mirrors standard DPLL/CDCL BCP
   and produces deterministic, reproducible propagation chains.

3. **Stable contradiction detection.** Because all consequences of a given assignment are
   flushed before the next wave begins, a VIOLATED clause is detected at the earliest
   possible point — minimising the chance that a later propagation step masks or delays
   the contradiction.

**Entry points that feed the queue:**

| Trigger | What is enqueued |
|---------|-----------------|
| `add_clause(clause)` | The new clause itself |
| `assume(node, value)` | Every clause that contains that node |
| `retract(node)` | Every clause that contains that node |

**Propagation loop outcome per clause:**

| State | Meaning | Action |
|-------|---------|--------|
| SATISFIED | At least one literal already satisfied | Skip |
| VIOLATED | All literals contradicted | Trigger DDB |
| UNIT | Exactly one unknown literal | Force its value; re-enqueue its clauses |
| UNRESOLVED | Multiple unknowns remain | Leave for a future round |

### Dependency-Directed Backtracking (Part 2)

When a clause is VIOLATED:

1. **`trace_conflict`** collects all assumption nodes (`assumption=True`) in the
   violated clause — these are the culprits.
2. **`build_nogood`** creates a learned clause `¬a₁ ∨ ¬a₂ ∨ …` that permanently
   records this combination of assumptions as inconsistent.
3. The culprit assumption is retracted; BCP re-runs and forces it to FALSE via the
   stored mutual-exclusion constraint, preventing the same conflict from recurring.

The mutual-exclusion constraint is exposed to the rule engine via
`LTRE.add_constraint(*facts)`, which adds `Clause([], [node₁, node₂, …])` directly
to the CLTMS — violated the moment all listed facts are simultaneously TRUE.

### Well-Founded Support / Cycle Detection (Part 1.3)

**`CLTMS.add_support(consequent, antecedents)`** calls
`depends_on(ant, consequent)` before recording the justification. `depends_on`
performs a DFS over the justification graph; if any antecedent already transitively
depends on the consequent the support is rejected, ensuring the justification DAG
stays acyclic and every belief has a well-founded grounding.

---

## Running the Tests

```bash
python test_suite.py
```

The test suite covers three scenarios:

1. **Cycle detection** — A→B→A is blocked; A retains its original ground support.
2. **DDB** — Rain ∧ Sprinkler derives WetGrass; asserting NotWetGrass with a
   mutual-exclusion constraint triggers contradiction detection, learns a Nogood,
   and retracts NotWetGrass as the culprit.
3. **Declarative rules + segment variables** — a grandparent rule using normal
   variables derives `('grandparent', 'Alice', 'Charlie')`; a team-leader rule
   using `?rest` captures the tail of a variable-length fact and asserts
   `('team_leader', 'Alice')`.
