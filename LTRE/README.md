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

### Task 3.1 — Advanced Unification

Unification is split across two functions:

- **`unify(pat, term, env)`** — handles atoms, variables (`?x`), wildcards (`?_`),
  and delegates lists to `unify_lists`.
- **`unify_lists(pat_list, term_list, env)`** — iterates element-by-element.
  When a **segment variable** (`?rest…`) is encountered it greedily consumes the
  entire remaining tail of the term list into one binding and returns immediately.
  This gives variable-length argument matching without backtracking.

Wildcards (`?_`) are checked before the ordinary variable branch so they never
produce a binding, keeping the environment clean.

### Task 3.2 — Declarative Rule Schemas

Rules are stored as `Rule` dataclass instances with two optional fields:

- `triggers` — a list of fact patterns (the antecedents / LHS)
- `actions`  — a list of S-expression tuples such as `("assert", <pattern>)`

**`add_rule()`** accepts these fields alongside the legacy Python-callback API so
both styles coexist.

**`join_triggers()`** performs the multi-antecedent join by recursing through the
trigger list depth-first, threading a single `env` dict so bindings made by
trigger *i* are visible when unifying trigger *i+1*. This is a miniature
Rete-style join without explicit stateful memory nodes.

**`run_rules()`** interprets each action: for `("assert", pattern)` it calls
`subst(pattern, env)` to substitute bindings and then calls `assert_fact()`,
which calls `CLTMS.add_support()` to wire the LTMS justification clause
automatically.

### Task 3.3 — Knowledge Base Optimisation (O(1) Retrieval)

**`fetch(pattern)`** extracts `predicate = pattern[0]` and skips any `DbClass`
whose `form[0]` does not match before attempting unification. Because `dbclasses`
is a `dict` keyed by `str(form)`, the backing store is already a hash table; the
predicate check eliminates all facts in unrelated buckets in O(1) per entry
before the more expensive `unify` call is made.

A full **Rete network** would additionally maintain:
- *Alpha memories* — one node per predicate, populated at assertion time.
- *Beta memories* — stateful partial-match records per rule join node.
- *Token propagation* — incremental updates instead of re-scanning on every query.

The current predicate-filter approach delivers the largest real-world speedup
(skipping irrelevant predicates entirely) without the added complexity of
stateful Rete memories.

---

## CLTMS — BCP, DDB, and Well-Founded Support

### BCP (Part 1) — Boolean Constraint Propagation

Every derived fact is represented as a Horn clause
`consequent ∨ ¬ant₁ ∨ ¬ant₂ ∨ …` in `CLTMS.clauses`. A queue-based BCP loop
evaluates each clause after any node value changes. The four clause states are:

| State | Meaning |
|-------|---------|
| SATISFIED | At least one literal already satisfied |
| VIOLATED | All literals contradicted — triggers DDB |
| UNIT | Exactly one unknown literal — force it |
| UNRESOLVED | Multiple unknowns — wait |

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
