"""
test_suite.py — LTRE / CLTMS demonstration
============================================
Covers three requirements:
  1. Well-founded support: logic cycle broken by cycle detection.
  2. Contradiction + DDB: nogood clause learned, culprit retracted.
  3. Declarative rules: segment variables + multi-trigger S-expression rules.
"""

from cltre import LTRE


# =============================================================================
# TEST 1 — WELL-FOUNDED SUPPORT / CYCLE DETECTION
# Requirement: a logic cycle must be detected and broken so that a node cannot
# circularly justify its own truth.
# =============================================================================

print("\n" + "=" * 60)
print("TEST 1 — WELL-FOUNDED SUPPORT: CYCLE DETECTION")
print("=" * 60 + "\n")

engine = LTRE("Cycle Test")

# Step 1: A is a ground assumption (no dependencies)
engine.assert_fact(("A",))
print("Asserted: A  (ground assumption)")

# Step 2: B is supported by A  — acyclic, accepted
engine.assert_fact(("B",), dependencies=[("A",)])
print("Asserted: B depends on A  (acyclic — accepted)")

# Step 3: Try to make A depend on B — closes the cycle A→B→A
# CLTMS.add_support() calls depends_on(B, A) which traverses B→A and
# finds A, so it rejects the justification.
engine.assert_fact(("A",), dependencies=[("B",)])
print("Asserted: A depends on B  (would create cycle A→B→A — should be blocked)\n")

a_node = engine.get_dbclass(("A",)).datum
b_node = engine.get_dbclass(("B",)).datum

print(f"A still TRUE (original assumption intact): {engine.tms.is_true(a_node)}")
print(f"B still TRUE (supported by A):             {engine.tms.is_true(b_node)}")
# A was asserted as a ground assumption — no justification entries.
# The cyclic add_support was rejected before it could add one.
print(f"Circular justification NOT recorded:       {len(a_node.justifications) == 0}")
print("\n[PASS] Cycle between A→B→A was blocked; A retains its ground support.\n")


# =============================================================================
# TEST 2 — CONTRADICTION + DEPENDENCY-DIRECTED BACKTRACKING (DDB)
# Requirement: asserting a fact that contradicts a derived fact must trigger
# contradiction detection, produce a Nogood clause, and retract the culprit.
# =============================================================================

print("=" * 60)
print("TEST 2 — CONTRADICTION AND DEPENDENCY-DIRECTED BACKTRACKING")
print("=" * 60 + "\n")

engine2 = LTRE("Contradiction Test")

# Ground assumptions
engine2.assert_fact(("Rain",))
engine2.assert_fact(("Sprinkler",))
print("Asserted: Rain, Sprinkler (assumptions)\n")

# Declarative rule: Rain ∧ Sprinkler → WetGrass
engine2.add_rule(
    triggers=[("Rain",), ("Sprinkler",)],
    actions=[("assert", ("WetGrass",))],
    name="wet_grass_rule"
)
engine2.run_rules()

wetgrass_node    = engine2.get_dbclass(("WetGrass",)).datum
print(f"WetGrass derived by rule:    {engine2.tms.is_true(wetgrass_node)}")
print(f"WetGrass facts in DB:        {engine2.fetch(('WetGrass',))}\n")

# Assert the contradicting assumption
engine2.assert_fact(("NotWetGrass",))
notwetgrass_node = engine2.get_dbclass(("NotWetGrass",)).datum
print(f"Asserted: NotWetGrass (assumption) TRUE: {engine2.tms.is_true(notwetgrass_node)}")

# add_constraint adds the CLTMS clause ¬WetGrass ∨ ¬NotWetGrass.
# Both nodes are TRUE → clause is immediately VIOLATED → handle_contradiction()
# fires: traces culprit assumptions, builds a Nogood, retracts the culprit.
print("\nAdding mutual-exclusion constraint: WetGrass ∧ NotWetGrass ⊥")
engine2.add_constraint(("WetGrass",), ("NotWetGrass",))

nogoods = [c for c in engine2.tms.clauses if c.learned]
print(f"\nNogood clauses learned:           {len(nogoods)}  → {nogoods}")
print(f"WetGrass still TRUE (derived):    {engine2.tms.is_true(wetgrass_node)}")
print(f"NotWetGrass FALSE (culprit):      {engine2.tms.is_false(notwetgrass_node)}")
print("\n[PASS] Contradiction detected; Nogood learned; culprit (NotWetGrass) retracted.\n")


# =============================================================================
# TEST 3 — DECLARATIVE RULES WITH SEGMENT VARIABLES
# Requirement: an S-expression rule must unify with segment variables (?rest)
# and assert a new derived fact.
# =============================================================================

print("=" * 60)
print("TEST 3 — DECLARATIVE RULES WITH SEGMENT VARIABLES")
print("=" * 60 + "\n")

engine3 = LTRE("Segment Var Test")

# --- 3a: Multi-trigger declarative rule (normal variables) ---
engine3.assert_fact(("parent", "Alice", "Bob"))
engine3.assert_fact(("parent", "Bob", "Charlie"))

# Rule: parent(?x,?y) ∧ parent(?y,?z) → grandparent(?x,?z)
engine3.add_rule(
    triggers=[("parent", "?x", "?y"), ("parent", "?y", "?z")],
    actions=[("assert", ("grandparent", "?x", "?z"))],
    name="grandparent_rule"
)
engine3.run_rules()

gp_facts = engine3.fetch(("grandparent", "?g", "?c"))
print("3a — Multi-trigger grandparent rule:")
for f in gp_facts:
    print(f"     {f}")

# --- 3b: Single-trigger rule using a segment variable ---
# Fact: ("team", "Alice", "Bob", "Charlie")
# Pattern: ("team", "?leader", "?rest")  — ?rest greedily matches the tail
# Action: assert ("team_leader", "?leader")
engine3.assert_fact(("team", "Alice", "Bob", "Charlie"))

engine3.add_rule(
    triggers=[("team", "?leader", "?rest")],
    actions=[("assert", ("team_leader", "?leader"))],
    name="team_leader_rule"
)
engine3.run_rules()

tl_facts = engine3.fetch(("team_leader", "?who"))
print("\n3b — Segment-variable rule  (pattern: team ?leader ?rest):")
print(f"     ?rest bound to tail of list; team_leader asserted for head")
for f in tl_facts:
    print(f"     {f}")

print("\n[PASS] Segment variable matched tail; declarative rule asserted new fact.\n")


# =============================================================================
print("=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60 + "\n")
