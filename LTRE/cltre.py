"""
ltre.py — LTRE rule engine
==========================

Updates:
- `assert_fact` now accepts `dependencies` list.
- Passes dependencies to CLTMS `add_support`.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    from cltms import CLTMS, Node, Polarity
except ImportError:
    raise ImportError("cltms.py not found.")

@dataclass
class DbClass:
    form: Any
    datum: Optional[Any] = None
    facts: List['Fact'] = field(default_factory=list)

@dataclass
class Rule:
    id: int
    trigger: Any
    body: Callable[['Env', Any], None]
    triggers: Optional[List[Any]] = None
    actions: Optional[List[Any]] = None
    name: Optional[str] = None

@dataclass
class Fact:
    id: int
    lisp_form: Any
    dbclass: DbClass

Env = Dict[str, Any]

# -----------------------------------------------------------------------------
# Unification & Substitution
# -----------------------------------------------------------------------------

def is_var(x: Any) -> bool:
    return isinstance(x, str) and x.startswith("?")

def is_wildcard(x: Any) -> bool:
    return x == "?_"

def is_segment_var(x: Any) -> bool:
    return isinstance(x, str) and x.startswith("?rest")

# =============================================================================
# TASK 3.1 — ADVANCED UNIFICATION
# Implements wildcards (?_) and segment variables (?rest...) in unify() and
# unify_lists(). is_wildcard() and is_segment_var() identify the special
# pattern tokens; unify_lists() handles the segment-variable greedy match.
# =============================================================================

def unify(pat: Any, term: Any, env: Optional[Env] = None) -> Optional[Env]:

    if env is None:
        env = {}

    if pat == term:
        return env

    # TASK 3.1 — Wildcard: matches any single element, no binding stored
    if is_wildcard(pat):
        return env

    if is_var(pat):

        if pat in env:
            return unify(env[pat], term, env)

        new_env = env.copy()
        new_env[pat] = term
        return new_env
    
    if is_var(term):
        if term in env:
            return unify(pat, env[term], env)
        new_env = env.copy()
        new_env[term] = pat
        return new_env

    if isinstance(pat, (list, tuple)) and isinstance(term, (list, tuple)):
        return unify_lists(list(pat), list(term), env)

    return None


def unify_lists(pat_list: List[Any], term_list: List[Any], env: Env) -> Optional[Env]:
    # TASK 3.1 — Element-by-element unification with segment-variable support
    i = 0
    j = 0

    while i < len(pat_list):

        pat = pat_list[i]

        # TASK 3.1 — Segment variable: greedily binds remaining elements to ?rest*
        if is_segment_var(pat):

            new_env = env.copy()
            new_env[pat] = term_list[j:]
            return new_env

        if j >= len(term_list):
            return None

        env = unify(pat, term_list[j], env)

        if env is None:
            return None

        i += 1
        j += 1

    if j != len(term_list):
        return None

    return env


def subst(pat: Any, env: Env) -> Any:

    if is_var(pat):

        if pat in env:
            return subst(env[pat], env)

        return pat

    if isinstance(pat, (list, tuple)):

        result = [subst(el, env) for el in pat]

        return tuple(result) if isinstance(pat, tuple) else result

    return pat

# -----------------------------------------------------------------------------
# LTRE Class
# -----------------------------------------------------------------------------

class LTRE:

    def __init__(self, title: str, debugging: bool = False):

        self.title = title
        self.debugging = debugging

        # initialize TMS
        self.tms = CLTMS()

        self.dbclasses: Dict[str, DbClass] = {}
        self.rules: List[Rule] = []

        self.queue: List[Tuple[Rule, Env, Any]] = []
        self.rule_counter = 0
        self._fired: set = set()  # tracks (rule_id, env_key) to prevent re-firing


    def subst(self, pat: Any, env: Env) -> Any:
        return subst(pat, env)

    def get_dbclass(self, form: Any) -> DbClass:
        key = str(form)
        if key not in self.dbclasses:
            dbc = DbClass(form=form)
            dbc.datum = self.tms.create_node(form)
            self.dbclasses[key] = dbc
        return self.dbclasses[key]

    # =========================================================================
    # TASK 3.2 — DECLARATIVE RULE SCHEMAS
    # add_rule() accepts a declarative `triggers` list (antecedents) and
    # `actions` list (consequents) in place of a Python callback.
    # join_triggers() does the multi-trigger join, binding variables
    # consistently across all antecedents.  run_rules() interprets the
    # ("assert", <pattern>) action S-expression and auto-wires the LTMS clause.
    # =========================================================================

    def add_rule(self, trigger: Tuple[str, Any] = None, body: Callable[[Env, Any], None] = None,
                 name: str = None, triggers: List[Any] = None, actions: List[Any] = None) -> None:
        # TASK 3.2 — Registers a rule; `triggers`/`actions` carry the declarative form
        self.rule_counter += 1
        rule = Rule(id=self.rule_counter, trigger=trigger, body=body, name=name,
                    triggers=triggers, actions=actions)
        self.rules.append(rule)
        for dbc in self.dbclasses.values():
            self.try_match_rule_dbclass(rule, dbc)

    def join_triggers(self, triggers: List[Any], env: Env = None, idx: int = 0):
        # TASK 3.2 — Recursive join: unifies each antecedent pattern in order,
        # threading the same env so variable bindings stay consistent across triggers
        if env is None:
            env = {}
        if idx == len(triggers):
            yield env
            return
        pat = triggers[idx]
        for dbc in self.dbclasses.values():
            new_env = unify(pat, dbc.form, env)
            if new_env is not None and self.tms.is_true(dbc.datum):
                yield from self.join_triggers(triggers, new_env, idx + 1)

    def try_match_rule_dbclass(self, rule: Rule, dbc: DbClass):
        if rule.triggers:
            for env in self.join_triggers(rule.triggers):
                self.enqueue(rule, env, None)
            return

        if rule.trigger is None:
            return

        cond, pat = rule.trigger
        env = unify(pat, dbc.form)
        if env is not None:
            node = dbc.datum
            if self.check_condition(cond, node):
                self.enqueue(rule, env, node)

    def check_condition(self, cond: str, node: Any) -> bool:
        if cond == "TRUE": return self.tms.is_true(node)
        if cond == "FALSE": return self.tms.is_false(node)
        return False

    def enqueue(self, rule: Rule, env: Env, node: Any) -> None:
        # Segment variables bind lists, which aren't hashable — convert to tuples
        def _hashable(v):
            return tuple(v) if isinstance(v, list) else v
        key = (rule.id, tuple(sorted((k, _hashable(v)) for k, v in env.items())))
        if key not in self._fired:
            self._fired.add(key)
            self.queue.append((rule, env, node))

    def run_rules(self) -> None:

        while self.queue:

            rule, env, node = self.queue.pop(0)

            if rule.body:
                rule.body(env, node)

            if rule.actions:
                # TASK 3.2 — Interpret declarative S-expression consequents.
                # ("assert" <pattern>) substitutes bindings then asserts the fact,
                # which auto-wires the LTMS support clause via assert_fact().
                # Pass the matched trigger facts as dependencies so the derived
                # fact is recorded as a consequence (not an assumption) in the
                # CLTMS — essential for DDB to identify the correct culprit.
                #
                # We re-unify each trigger pattern against dbc.form (rather than
                # substituting env into the pattern) to recover the actual stored
                # fact key.  Substituting is wrong when a segment variable (?rest)
                # binds a list: subst would nest the list inside the tuple, giving
                # a key like ("team","Alice",["Bob","Charlie"]) that doesn't match
                # the stored ("team","Alice","Bob","Charlie").
                trigger_deps = None
                if rule.triggers:
                    trigger_deps = []
                    for tpat in rule.triggers:
                        for dbc in self.dbclasses.values():
                            if (unify(tpat, dbc.form, env) is not None
                                    and self.tms.is_true(dbc.datum)):
                                trigger_deps.append(dbc.form)
                                break

                for action in rule.actions:

                    if action[0] == "assert":

                        fact = subst(action[1], env)

                        self.assert_fact(
                            fact,
                            just="rule",
                            dependencies=trigger_deps or None
                        )
    # ------------------------- Facts & TMS Interface -------------------------

    def assert_fact(self, fact: Any, just: Any = "user", dependencies: List[Any] = None) -> None:
        """
        Assert a fact.
        If 'dependencies' (list of facts) is provided, it creates a justification.
        Otherwise it treats it as an assumption (if just="user") or premise.
        """
        dbc = self.get_dbclass(fact)
        node = dbc.datum

        if dependencies:
            # It's a derived fact (Logic)
            ant_nodes = [self.get_dbclass(d).datum for d in dependencies]
            self.tms.add_support(consequent=node, antecedents=ant_nodes, informant=just)
        else:
            # It's an assumption / premise
            self.tms.enable_assumption(node, Polarity.TRUE, informant=just)

        # Propagate to rules if TRUE
        if self.tms.is_true(node):
            self.propagate_fact(dbc)

    def add_constraint(self, *facts) -> None:
        """Assert that all given facts cannot simultaneously be TRUE.
        Adds the clause ¬f1 ∨ ¬f2 ∨ … to the CLTMS.
        When all are TRUE the clause is VIOLATED, triggering DDB."""
        nodes = [self.get_dbclass(f).datum for f in facts]
        self.tms.add_clause(positives=[], negatives=nodes)

    def retract(self, fact: Any, reason: Any, quiet: bool = False) -> None:
        dbc = self.get_dbclass(fact)
        node = dbc.datum
        self.tms.retract_assumption(node, informant=reason)

    def propagate_fact(self, dbc: DbClass):
        for rule in self.rules:
            self.try_match_rule_dbclass(rule, dbc)
    # =========================================================================
    # TASK 3.3 — KNOWLEDGE BASE OPTIMISATION (O(1) RETRIEVAL)
    # fetch() extracts the predicate (first atom) from the pattern and skips
    # any dbclass whose predicate doesn't match before attempting unification.
    # This gives O(1) predicate-bucket filtering: only facts that share the
    # same functor are ever unified, avoiding a full linear scan.
    # (A full Rete network would additionally index on argument positions and
    #  maintain stateful alpha/beta memories — see bonus note in README.)
    # =========================================================================
    def fetch(self, pattern: Any) -> List[Any]:
        results = []

        if isinstance(pattern, (list, tuple)):

            # TASK 3.3 — Extract predicate key for O(1) bucket filtering
            predicate = pattern[0]

            for dbc in self.dbclasses.values():

                if isinstance(dbc.form, (list, tuple)):

                    # TASK 3.3 — Skip non-matching predicates before unify (hash filter)
                    if dbc.form[0] != predicate:
                        continue

                env = unify(pattern, dbc.form)

                if env is not None:

                    if self.tms.is_true(dbc.datum):

                        results.append(subst(pattern, env))

        return results

    def explain(self, fact: Any) -> None:
        dbc = self.get_dbclass(fact)
        self.tms.why(dbc.datum)
