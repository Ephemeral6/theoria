"""Export an lp_potential certificate in the form the theory-compiler track needs.

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

from engines.lp_potential.potential import Certificate

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "certificates")


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
        "schema": "lp_potential/pagoda_certificate@1",
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
