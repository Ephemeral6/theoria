"""Export an engine certificate in the form the theory-compiler track needs.

Two schemas live here, one per engine:

    lp_potential/pagoda_certificate@1               `build` / `verify` / `write`
    ic3_pdr/inductive_invariant_certificate@1       `build_ic3` / `verify_ic3` /
                                                    `write_ic3`

The second is `CONTRACTS/ic3_certificate_v0.1.md`, whose "谁写哪一半" table puts
the emitting half on this track and had it standing at **未实现**.  It exists for
one reason worth restating: `lp_potential` is sound but *incomplete* -- there are
unsolvable configurations with no linear pagoda at all -- and `ic3_pdr` answers
the same question with the same three obligations and a different shape of
invariant, so a consumer that reads both loses nothing and gains the
configurations the LP cannot reach.

**The contract omits a `moves` field and that omission is the substance.**  An
invariant is only inductive *with respect to a transition relation*, so the
relation may not arrive in the same document that asserts the induction -- that
would be a certificate closed under a move set it chose for itself.  The consumer
derives the geometry independently and cross-checks; `verify_ic3` below does the
same thing on this side, deriving from `interop.peg1d` rather than reading
anything the document says about moves, because the document says nothing.

The original note, for the pagoda half:

Their M8 note asks for exactly this: "后续汇合 sprint 需接入 engine-rig 的 LP 输出并
重构 Lean 证明策略" -- their A1 rehearsal used hand-computed pagoda constants and a
Lean proof by BFS enumeration, and wants LP-solved weights and an algebraic proof
instead.

What crosses the boundary is a **certificate**, not a search: exact integer
weights plus, for every obligation, the arithmetic that discharges it. Lean then
only checks. Weights are scaled from rationals to integers (the constraints are
homogeneous, and the margin scales with them), because integer literals are what
a generated Lean proof wants to manipulate.

This module writes files; it does not touch `/theory-compiler/`.
"""

import json
import os
from fractions import Fraction
from math import gcd
from typing import Any, Dict, List, Optional, Sequence

from engines.ic3_pdr.system import Clause, System, clause_key
from engines.lp_potential.potential import Certificate
from interop import peg1d

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "certificates")

PAGODA_SCHEMA = "lp_potential/pagoda_certificate@1"
IC3_SCHEMA = "ic3_pdr/inductive_invariant_certificate@1"


def _lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def to_integer_weights(weights: Sequence[Fraction]) -> List[int]:
    """Scale exact rationals to the smallest integers preserving every ratio."""
    multiplier = 1
    for w in weights:
        multiplier = _lcm(multiplier, w.denominator)
    scaled = [int(w * multiplier) for w in weights]
    divisor = 0
    for value in scaled:
        divisor = gcd(divisor, abs(value))
    if divisor > 1:
        scaled = [value // divisor for value in scaled]
    return scaled


def _potential(weights: Sequence[int], state: str) -> int:
    return sum(weights[i] for i, cell in enumerate(state) if cell == "1")


def build(certificate: Certificate, graph: Dict[str, Any],
          claim_name: str = "unsolvable") -> Dict[str, Any]:
    """A certificate document carrying the arithmetic for every obligation.

    Every obligation carries its own witnesses -- the move constraints with both
    sides evaluated, the goal-breaking condition per goal state -- so a checker
    can redo the sums without an LP solver, and Lean can manipulate integers.

    What the document does not carry is a reason to believe its own move list is
    complete. The witnesses are whatever `certificate.moves` held; nothing here
    ties them back to `graph`, which is read only for `n_pos`. A checker that
    wants closure under the *rules* rather than over a list has to ground the
    moves itself -- `recheck/verify.py` does, and says why in its docstring.
    """
    weights = to_integer_weights(certificate.weights)
    initial = certificate.initial
    bound = _potential(weights, initial)

    move_obligations = []
    for move in certificate.moves:
        delta = weights[move.dst] - weights[move.src] - weights[move.over]
        move_obligations.append(
            {
                "move": move.name(),
                "positions": [move.src, move.over, move.dst],
                "w_dst": weights[move.dst],
                "w_src": weights[move.src],
                "w_over": weights[move.over],
                "delta": delta,
                "holds": delta <= 0,
            }
        )

    goal_obligations = [
        {
            "goal_state": goal,
            "potential": _potential(weights, goal),
            "exceeds_initial_by": _potential(weights, goal) - bound,
            "holds": _potential(weights, goal) > bound,
        }
        for goal in certificate.goal_states
    ]

    document = {
        "schema": PAGODA_SCHEMA,
        "produced_by": "engine-rig/engines/lp_potential",
        "claim": claim_name,
        "n_pos": graph["n_pos"],
        "initial_state": initial,
        "goal_states": list(certificate.goal_states),
        "weights_integer": weights,
        "weights_rational": [str(w) for w in certificate.weights],
        "initial_potential": bound,
        "invariant": "I(s) := potential(s) <= %d, where potential(s) = sum of w[i] over occupied i" % bound,
        "obligations": {
            "inv_init": {
                "statement": "potential(initial) <= %d" % bound,
                "value": bound,
                # A literal, not a test: `bound` *is* potential(initial), so
                # this reads "x <= x". It is here for the Lean skeleton's third
                # slot, and an importer should treat it as shape, not evidence.
                "holds": True,
            },
            "inv_closed": {
                "statement": "every legal move has delta <= 0",
                # An assertion about `certificate.moves`, made by the producer
                # and re-derived by nobody: the move set is not cross-checked
                # against `graph` here, and `verify()` below reads this list
                # rather than regenerating it.
                "checked_over": "the %d move instances this document lists"
                                % len(move_obligations),
                "n_checked": len(move_obligations),
                "witnesses": move_obligations,
                "holds": all(o["holds"] for o in move_obligations),
            },
            "goal_break": {
                "statement": "every goal state has potential > %d" % bound,
                "witnesses": goal_obligations,
                "holds": all(o["holds"] for o in goal_obligations),
            },
        },
    }
    document["verified"] = all(
        section["holds"] for section in document["obligations"].values()
    )
    # Written after `verified`, and from it.  It was a literal above the line
    # that computes the verdict, so a document whose obligations fail carried
    # `verified: false` beside `conclusion: "no goal state is reachable from X"`
    # -- the verdict as a sibling field of the headline it contradicts, which is
    # the shape D-034 exists to stop.  The conclusion is what the obligations
    # license, so it is derived from them or it is not stated.
    document["conclusion"] = (
        "no goal state is reachable from %s" % initial if document["verified"]
        else "nothing follows: %s obligation(s) are not discharged by this document"
             % ", ".join(sorted(name for name, section
                                in document["obligations"].items()
                                if not section["holds"]))
    )
    return document


def verify(document: Dict[str, Any]) -> List[str]:
    """Re-check a certificate document's arithmetic, in integers.

    Recomputing rather than reading the `holds` flags catches a producer whose
    sums are wrong -- a mis-scaled weight, a stale `initial_potential`, a goal
    that no longer breaks the bound. That is worth having, and the tampering
    tests exercise it.

    It does not catch a producer whose premises are wrong. The move witnesses
    iterated below are the document's own list, and this function never sees the
    rule set, so a document that omits an inconvenient move instance returns
    `[]`. Passing entitles a reader to "the stated obligations are discharged
    over the stated moves" -- not "the invariant is closed under the rules".
    `recheck/verify.py` is the checker without that gap: it grounds the move
    relation from the declared rules and refuses an `obligations` key outright.
    """
    errors: List[str] = []
    weights = document["weights_integer"]
    bound = _potential(weights, document["initial_state"])
    if bound != document["initial_potential"]:
        errors.append("initial_potential %s disagrees with the weights (%s)"
                      % (document["initial_potential"], bound))
    for obligation in document["obligations"]["inv_closed"]["witnesses"]:
        src, over, dst = obligation["positions"]
        delta = weights[dst] - weights[src] - weights[over]
        if delta > 0:
            errors.append("%s raises the potential by %d" % (obligation["move"], delta))
    for goal in document["goal_states"]:
        if _potential(weights, goal) <= bound:
            errors.append("goal %s does not exceed the initial potential" % goal)
    return errors


# ========================================== ic3_pdr/inductive_invariant@1

def _bits(state: str) -> tuple:
    return tuple(cell == "1" for cell in state)


def _cnf_of(clauses: Sequence[Clause], system: System) -> List[List[List[Any]]]:
    """The CNF as the contract writes it: `[[[name, value], ...], ...]`.

    Clauses in `clause_key` order and literals in `sorted()` order, so the same
    invariant always produces the same bytes.  `ic3bounds.emit` orders its
    `recheck` predicate the same way and for the same reason; the two are
    deliberately separate code, because this module must not depend on the
    rechecker in order to describe an engine result.
    """
    return [system.clause_as_json(clause)
            for clause in sorted(clauses, key=clause_key)]


def _satisfies_cnf(state: str, cnf: Sequence[Sequence[Sequence[Any]]],
                   index: Dict[str, int]) -> bool:
    for clause in cnf:
        if not any((state[index[name]] == "1") == bool(value)
                   for name, value in clause):
            return False
    return True


def build_ic3(system: System, invariant: Any, check: Any = None,
              claim_name: Optional[str] = None) -> Dict[str, Any]:
    """An `ic3_pdr/inductive_invariant_certificate@1` document.

    `invariant` is an `engines.ic3_pdr.Invariant` (or any sequence of clauses).
    `check` is the engine's own `CheckResult`, and it is optional because the
    consumer does not read it -- the contract says the producer's self-check is
    "生产方的意见" and recomputes all three obligations itself.  It is emitted
    anyway, under `obligations`, because it is useful to a human reading the file
    and because the pagoda document carries the same block.

    There is deliberately no `moves` key.  See the module docstring.
    """
    clauses = list(getattr(invariant, "clauses", invariant))
    variables = list(system.variables)
    index = {name: i for i, name in enumerate(variables)}
    n_pos = len(variables)
    initial = system.render_state(system.init[0])
    goals = [system.render_state(state) for state in system.bad]
    cnf = _cnf_of(clauses, system)
    rendering = system.render_cnf(sorted(clauses, key=clause_key))

    states = [system.render_state(state) for state in system.states]
    satisfying = [s for s in states if _satisfies_cnf(s, cnf, index)]
    inside = set(satisfying)

    escapes = []
    n_edges = 0
    for state in system.states:
        text = system.render_state(state)
        if text not in inside:
            continue
        for label, target in system.moves(state):
            n_edges += 1
            if system.render_state(target) not in inside:
                escapes.append({"state": text, "move": label,
                                "successor": system.render_state(target)})

    goal_obligations = [
        {"goal_state": goal, "satisfies_invariant": goal in inside,
         "holds": goal not in inside}
        for goal in goals
    ]

    document: Dict[str, Any] = {
        "schema": IC3_SCHEMA,
        "produced_by": "engine-rig/engines/ic3_pdr",
        "claim": claim_name or "unsolvable_%s_to_%s" % (initial, "+".join(goals)),
        "conclusion": "no goal state is reachable from %s" % initial,
        "invariant": "I(s) := %s" % rendering,
        "n_pos": n_pos,
        "variables": variables,
        "initial_state": initial,
        "goal_states": goals,
        "cnf": cnf,
        "n_clauses": len(cnf),
        "n_states": len(states),
        "n_satisfying": len(satisfying),
        "obligations": {
            "inv_init": {
                "statement": "the invariant holds at %s" % initial,
                "holds": initial in inside,
            },
            "inv_closed": {
                "statement": "every legal move from a state satisfying the "
                             "invariant lands on a state satisfying it",
                "checked_over": "all states satisfying the invariant, reachable "
                                "or not, over the full 2^n space",
                "n_checked": n_edges,
                "witnesses": escapes[:8],
                "holds": not escapes,
            },
            "goal_break": {
                "statement": "no goal state satisfies the invariant",
                "witnesses": goal_obligations,
                "holds": all(o["holds"] for o in goal_obligations),
            },
        },
    }
    if check is not None:
        # The producer's own independent checker, recorded as provenance and
        # nothing more. The consumer recomputes; so does `verify_ic3`.
        document["producer_check"] = {
            "conditions": dict(sorted(dict(check.conditions).items())),
            "n_states": check.n_states,
            "n_satisfying": check.n_satisfying,
            "checked_by": "engines.ic3_pdr.check.verify -- shares no code with "
                          "the search",
        }
    document["verified"] = all(
        section["holds"] for section in document["obligations"].values()
    )
    return document


def verify_ic3(document: Dict[str, Any]) -> List[str]:
    """Re-check an IC3 certificate from its own contents, geometry aside.

    An importer should be able to run this without trusting the producer, so it
    recomputes rather than reading `verified` or `obligations[*].holds` -- the
    same discipline `verify` applies to the pagoda document, for the same
    reason.

    The geometry is **not** read from the document.  It is re-derived from
    `interop.peg1d`, because an invariant closed under a move set the same file
    supplied would be closed under a move set it chose for itself.  That is why
    the contract has no `moves` field.
    """
    errors: List[str] = []
    if document.get("schema") != IC3_SCHEMA:
        errors.append("schema is %r, not %r" % (document.get("schema"), IC3_SCHEMA))
        return errors
    for key in ("n_pos", "variables", "initial_state", "goal_states", "cnf"):
        if key not in document:
            errors.append("required field %r is missing" % key)
    if "moves" in document:
        errors.append(
            "a certificate may not carry `moves`: an invariant closed under the "
            "move set its own document supplies is closed under nothing")
    if errors:
        return errors

    n_pos = document["n_pos"]
    variables = list(document["variables"])
    if len(variables) != n_pos:
        errors.append("n_pos is %d but %d variables are declared"
                      % (n_pos, len(variables)))
    if len(set(variables)) != len(variables):
        errors.append("duplicate variable name")
    index = {name: i for i, name in enumerate(variables)}
    if errors:
        return errors

    cnf = document["cnf"]
    if not cnf:
        errors.append("the clause set is empty, so the invariant is identically "
                      "true and separates nothing")
    for position, clause in enumerate(cnf):
        if not clause:
            errors.append("clause %d is empty, so the invariant is identically "
                          "false and does not hold at the initial state" % position)
        for literal in clause:
            if len(literal) != 2 or literal[0] not in index:
                errors.append(
                    "clause %d names %r, which is not a declared variable; an "
                    "undeclared name is an error, not a guess"
                    % (position, literal[0] if literal else literal))
    initial = document["initial_state"]
    goals = list(document["goal_states"])
    for state in [initial] + goals:
        if len(state) != n_pos or set(state) - {"0", "1"}:
            errors.append("%r is not a %d-position bit string" % (state, n_pos))
    if errors:
        return errors

    # The three obligations, recomputed over the whole state space -- not the
    # reachable part, which would make the closure check circular.
    states = peg1d.all_states(n_pos)
    moves = peg1d.move_instances(n_pos)
    inside = {s for s in states if _satisfies_cnf(s, cnf, index)}

    if initial not in inside:
        errors.append("inv_init: the invariant does not hold at %s, so it "
                      "separates nothing" % initial)
    escapes = 0
    for state in sorted(inside):
        for move in moves:
            if not peg1d.legal(state, move):
                continue
            successor = peg1d.apply(state, move)
            if successor not in inside:
                escapes += 1
                if escapes <= 4:
                    errors.append(
                        "inv_closed: %s -jump(%d,%d,%d)-> %s escapes the invariant"
                        % (state, move["src"], move["over"], move["dst"], successor))
    if escapes > 4:
        errors.append("inv_closed: and %d further escaping transitions" % (escapes - 4))
    for goal in goals:
        if goal in inside:
            errors.append("goal_break: the invariant admits the goal state %s" % goal)

    # Not an obligation, a consistency check on the document's own arithmetic.
    for key, value in (("n_satisfying", len(inside)), ("n_states", len(states)),
                       ("n_clauses", len(cnf))):
        if key in document and document[key] != value:
            errors.append("%s says %r, recomputed %r" % (key, document[key], value))
    return errors


def write_ic3(document: Dict[str, Any], path: Optional[str] = None) -> str:
    path = path or os.path.join(
        OUT_DIR,
        "ic3_%s_%s_to_%s.json" % (
            document["n_pos"],
            document["initial_state"],
            "+".join(document["goal_states"]),
        ),
    )
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(document, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def write(document: Dict[str, Any], path: Optional[str] = None) -> str:
    # The goal belongs in the name: two claims can share a start state and differ
    # only in their target, and the first version of this silently overwrote one
    # with the other.
    path = path or os.path.join(
        OUT_DIR,
        "pagoda_%s_%s_to_%s.json" % (
            document["n_pos"],
            document["initial_state"],
            "+".join(document["goal_states"]),
        ),
    )
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(document, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path
