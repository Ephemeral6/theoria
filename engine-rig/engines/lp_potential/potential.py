"""lp_potential -- one weight function, two products: a certificate and a bound.

Solve for weights w over board positions such that the potential of a state
(the sum of w over its occupied cells) never increases under a legal move, while
every goal state has a strictly higher potential than the start.  Then:

  * as a **certificate**, that is the three-line unreachability argument -- the
    invariant holds at the start, no move breaks it, winning requires breaking
    it, therefore the goal is unreachable, with no search over paths;
  * as a **heuristic**, the same w gives an admissible lower bound: the potential
    must fall by w(s) - w(g) and no single move can drop it by more than M, so at
    least (w(s)-w(g))/M moves remain.

"Certificate and heuristic are the same object" (Theoria 1.9), on one LP.

The LP runs in floating point; the answer is then snapped to rationals and every
condition is re-checked in exact arithmetic.  A certificate that only holds to
1e-9 is not a certificate -- see DECISIONS.md D-007.
"""

import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.optimize import linprog

DENOMINATOR_LIMIT = 1000

# scipy's `linprog` status for "the problem is infeasible" -- the one
# unsuccessful outcome that is an answer about the problem rather than about the
# solver's budget or arithmetic.
HIGHS_INFEASIBLE = 2


class CertificateError(Exception):
    """The LP returned weights that do not survive exact re-checking."""


class LpUnavailable(RuntimeError):
    """The solver stopped without deciding feasibility.

    Raised rather than folded into the `None` return, on the same rule as
    `fd_adapter/search.py`'s expansion budget: a resource limit or a numerical
    breakdown is a fact about HiGHS, and `solve_certificate` returning `None` is
    read as a fact about the configuration ("no linear pagoda separates the goal
    from the start").  Sharing one value between the two would let an iteration
    limit publish itself as a geometric fact, which is exactly the reading
    Theoria's constraint 6 forbids.  A caller that wants the old collapse can
    catch this; it cannot get it by accident.
    """


@dataclass(frozen=True)
class Move:
    src: int
    over: int
    dst: int

    def name(self) -> str:
        return "jump(%d,%d,%d)" % (self.src, self.over, self.dst)

    def delta(self, weights: Sequence[Fraction]) -> Fraction:
        """Change in potential: the jumped peg and the source leave, the destination fills."""
        return weights[self.dst] - weights[self.src] - weights[self.over]


@dataclass
class Certificate:
    weights: List[Fraction]
    initial: str
    goal_states: List[str]
    moves: List[Move]
    margin: Fraction
    conditions: Dict[str, bool] = field(default_factory=dict)

    def potential(self, state: str) -> Fraction:
        return sum(
            (self.weights[i] for i, cell in enumerate(state) if cell == "1"),
            Fraction(0),
        )

    @property
    def initial_potential(self) -> Fraction:
        return self.potential(self.initial)

    @property
    def max_decrease(self) -> Fraction:
        """M: the largest potential drop any single legal move can cause."""
        drops = [-move.delta(self.weights) for move in self.moves]
        return max(drops) if drops else Fraction(0)

    @property
    def holds(self) -> bool:
        return all(self.conditions.values()) and bool(self.conditions)

    def as_json(self) -> Dict[str, object]:
        return {
            "form": "potential_weights",
            "weights": [str(w) for w in self.weights],
            "weights_float": [float(w) for w in self.weights],
            "initial": self.initial,
            "initial_potential": str(self.initial_potential),
            "goal_states": list(self.goal_states),
            "goal_potentials": {g: str(self.potential(g)) for g in self.goal_states},
            "margin": str(self.margin),
            "max_decrease": str(self.max_decrease),
            "conditions": dict(self.conditions),
            "claim": "goal unreachable from %s" % self.initial,
            "rendering": (
                "potential(s) = sum of w over occupied cells; every legal move leaves "
                "it non-increasing, and every goal state has potential > potential(%s), "
                "so no goal state is reachable from %s"
            ) % (self.initial, self.initial),
        }


# ------------------------------------------------------------------ the LP

def moves_from_graph(graph: Dict[str, object]) -> List[Move]:
    """Distinct jump geometries, taken from the graph's edges over the full space."""
    seen = []
    for edge in graph["edges"]:                      # type: ignore[index]
        src, over, dst = edge["positions"]
        move = Move(src, over, dst)
        if move not in seen:
            seen.append(move)
    return sorted(seen, key=lambda m: (m.src, m.dst))


def _occupancy(state: str) -> List[int]:
    return [1 if cell == "1" else 0 for cell in state]


def solve_certificate(graph: Dict[str, object], initial: str,
                      goal_states: Optional[Sequence[str]] = None,
                      margin: int = 1, bound: int = 10) -> Optional[Certificate]:
    """Find pagoda weights proving `initial` cannot reach the goal, or None.

    Returning None is a real answer, and only ever that one: it means HiGHS
    **proved the LP infeasible** (status 2), so no weight function of this shape
    exists.  Every other way the solver can stop -- iteration limit, numerical
    difficulties, an unbounded relaxation -- raises `LpUnavailable`, because
    those say nothing about the configuration and the caller's docstring reads
    `None` as though they did.

    One thing `None` still under-states, recorded rather than fixed here: the
    box `bound` is a solver parameter, not part of the pagoda definition, so an
    infeasibility is infeasibility *within* `|w_i| <= bound`.  Weights outside
    the box can exist -- E11's exhaustive sweep found one instance in 3000
    (seed 17475932563032345095, weights [12,9,3,7,-1,11,10,-4], verified in
    exact rationals).  This direction is sound: `None` never certifies anything,
    it only declines to.  It is the engine's documented incompleteness (CLAUDE.md),
    widened slightly by a constant.
    """
    goals = list(goal_states or graph["goal_states"])  # type: ignore[index]
    moves = moves_from_graph(graph)
    n = int(graph["n_pos"])                            # type: ignore[index]

    # Variables: w_0..w_{n-1}, then t_0..t_{n-1} for the L1 objective.
    rows: List[List[float]] = []
    rhs: List[float] = []

    for move in moves:                                 # every legal move: dw <= 0
        row = [0.0] * (2 * n)
        row[move.dst] += 1.0
        row[move.src] -= 1.0
        row[move.over] -= 1.0
        rows.append(row)
        rhs.append(0.0)

    start = _occupancy(initial)
    for goal in goals:                                 # winning needs dw > 0
        row = [0.0] * (2 * n)
        for i in range(n):
            row[i] += start[i]
        for i, occupied in enumerate(_occupancy(goal)):
            row[i] -= occupied
        rows.append(row)
        rhs.append(-float(margin))

    for i in range(n):                                 # |w_i| <= t_i
        row = [0.0] * (2 * n)
        row[i], row[n + i] = 1.0, -1.0
        rows.append(row)
        rhs.append(0.0)
        row = [0.0] * (2 * n)
        row[i], row[n + i] = -1.0, -1.0
        rows.append(row)
        rhs.append(0.0)

    objective = [0.0] * n + [1.0] * n                  # smallest weights that work
    bounds = [(-bound, bound)] * n + [(0, bound)] * n
    result = linprog(
        c=objective,
        A_ub=np.array(rows, dtype=float),
        b_ub=np.array(rhs, dtype=float),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        # HiGHS status codes: 0 optimal, 1 iteration limit, 2 infeasible,
        # 3 unbounded, 4 numerical difficulties.  Only 2 is an answer.
        if result.status != HIGHS_INFEASIBLE:
            raise LpUnavailable(
                "linprog stopped without deciding feasibility: status %r (%s). "
                "This is a fact about the solver, not about the configuration, "
                "so no unreachability claim follows from it."
                % (result.status, getattr(result, "message", ""))
            )
        return None

    weights = [
        Fraction(float(value)).limit_denominator(DENOMINATOR_LIMIT)
        for value in result.x[:n]
    ]
    certificate = Certificate(
        weights=weights,
        initial=initial,
        goal_states=goals,
        moves=moves,
        margin=Fraction(margin),
    )
    certificate.conditions = check_exactly(certificate)
    if not certificate.holds:
        raise CertificateError(
            "LP weights %r fail exact re-checking: %r"
            % ([str(w) for w in weights], certificate.conditions)
        )
    return certificate


# ------------------------------------------------------- exact verification

def check_exactly(certificate: Certificate) -> Dict[str, bool]:
    """The three certificate conditions, in exact rational arithmetic.

    Mirrors the Lean skeleton of Theoria 1.10a: inv_init, inv_closed, goal_break.
    """
    invariant_bound = certificate.initial_potential
    return {
        # I(s) := potential(s) <= potential(s0)
        "inv_init": certificate.potential(certificate.initial) <= invariant_bound,
        # every legal move is non-increasing, so I is closed under any move from
        # any state -- checked on the move instances, which is what makes the
        # closure argument independent of which states are reachable
        "inv_closed": all(
            move.delta(certificate.weights) <= 0 for move in certificate.moves
        ),
        # reaching a goal would require breaking I, by at least `margin`
        "goal_break": all(
            certificate.potential(goal) - invariant_bound >= certificate.margin
            for goal in certificate.goal_states
        ),
    }


# ---------------------------------------------------------------- heuristic

@dataclass
class Heuristic:
    """h(s) from the same weights: an admissible lower bound on moves-to-go."""

    certificate: Certificate
    max_decrease: Fraction

    def value(self, state: str) -> float:
        """Lower bound on the number of moves from `state` to any goal state.

        Infinite means the potential would have to *rise*, which no legal move
        can do -- a per-state unsolvability claim, the certificate's local form.
        """
        best = math.inf
        current = self.certificate.potential(state)
        for goal in self.certificate.goal_states:
            required = current - self.certificate.potential(goal)
            if required < 0:
                continue                      # potential never rises: unreachable
            if required == 0:
                best = 0
                break
            if self.max_decrease <= 0:
                continue                      # no move shifts the potential at all
            best = min(best, math.ceil(Fraction(required) / self.max_decrease))
        return float(best)

    def entitlement(self, admissibility_check: Optional[Sequence[Dict[str, object]]]
                    = None) -> Dict[str, object]:
        """What actually licenses calling this heuristic admissible, itemised.

        The bound is `h(s) = min_g ceil((potential(s) - potential(g)) / M)`, and
        the argument for it is: every legal move leaves the potential
        non-increasing and drops it by at most `M`, so k moves cannot close a gap
        wider than `k*M`.  That argument is exactly the certificate's
        `inv_closed` condition plus `M`'s definition -- which means the licence is
        `certificate.holds`, the exact rational re-check, and **not** the author's
        confidence.  A certificate whose `conditions` are empty has not been
        re-checked at all and `holds` is false for that reason too.

        `admissibility_check`, when the caller has one, is the empirical half:
        h against the true shortest path on every state with a finite one.  It is
        a sample, not a proof, so it can only ever *subtract* -- a single row with
        `admissible: false` is a counterexample and settles the matter.
        """
        proved = self.certificate.holds
        rows = list(admissibility_check) if admissibility_check is not None else None
        if rows is None:
            sampled: Optional[bool] = None
            counterexamples: List[Dict[str, object]] = []
        else:
            counterexamples = [r for r in rows if not r.get("admissible")]
            sampled = not counterexamples
        return {
            "certificate_holds": proved,
            "certificate_conditions": dict(self.certificate.conditions),
            "empirical_check": "not run" if sampled is None else (
                "%d state(s), %d counterexample(s)" % (len(rows or []), len(counterexamples))
            ),
            "counterexamples": counterexamples,
            "admissible": bool(proved) and (sampled is not False),
        }

    def as_json(self, admissibility_check: Optional[Sequence[Dict[str, object]]] = None
                ) -> Dict[str, object]:
        """The payload.  `admissible` is derived here and nowhere else.

        It used to be the literal `True`, sitting beside an `admissibility_check`
        the headline never read -- so a heuristic built on a certificate that
        fails its own exact re-check still published `"admissible": true`.  The
        headline and the evidence are now computed by one expression, in one
        place, because two sites that agree on today's data are exactly what
        D-033 found drifting apart.
        """
        basis = self.entitlement(admissibility_check)
        payload: Dict[str, object] = {
            "form": "potential_lower_bound",
            "weights": [str(w) for w in self.certificate.weights],
            "max_decrease": str(self.max_decrease),
            "goal_states": list(self.certificate.goal_states),
            "formula": "h(s) = min_g ceil((potential(s) - potential(g)) / M), "
                       "infinite when potential(s) < potential(g)",
            "admissible": basis["admissible"],
            "admissible_basis": basis,
            "rendering": "at least ceil((potential(s) - potential(goal)) / %s) moves remain"
                         % self.max_decrease,
        }
        if admissibility_check is not None:
            payload["admissibility_check"] = list(admissibility_check)
        return payload


def heuristic_from(certificate: Certificate) -> Heuristic:
    return Heuristic(certificate=certificate, max_decrease=certificate.max_decrease)


def admissibility_report(heuristic: Heuristic, graph: Dict[str, object]
                         ) -> List[Dict[str, object]]:
    """h(s) against the true shortest path, for every state with a finite one."""
    distances: Dict[str, Optional[int]] = graph["distance_to_goal"]   # type: ignore[index]
    out = []
    for state in sorted(distances):
        distance = distances[state]
        if distance is None:
            continue
        out.append(
            {
                "state": state,
                "h": heuristic.value(state),
                "true_distance": distance,
                "admissible": heuristic.value(state) <= distance,
            }
        )
    return out
