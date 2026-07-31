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

# ------------------------------------------------------------ the status bit
#
# One word per way the LP can end, kept apart all the way to the caller.  The
# split that matters is `decided` vs not: `certified` and `no_linear_pagoda` are
# statements about the *configuration*, the other three are statements about
# HiGHS.  Collapsing them -- which this engine did until E15 -- lets an
# iteration limit publish itself as a geometric fact.

CERTIFIED = "certified"                 # HiGHS 0: weights found and re-checked
NO_LINEAR_PAGODA = "no_linear_pagoda"   # HiGHS 2: proved infeasible, in the box
BUDGET = "budget"                       # HiGHS 1: iteration limit
UNBOUNDED = "unbounded"                 # HiGHS 3: unbounded relaxation
NUMERICAL = "numerical"                 # HiGHS 4: numerical difficulties
UNDECIDED = "undecided"                 # any status this table does not know

#: The whole mapping, in one place, so a reader can check the claim "only 2 is
#: an answer" against a table instead of against control flow.
STATUS_WORDS: Dict[int, str] = {
    0: CERTIFIED,
    1: BUDGET,
    HIGHS_INFEASIBLE: NO_LINEAR_PAGODA,
    3: UNBOUNDED,
    4: NUMERICAL,
}

#: Outcomes that say something about the configuration rather than the solver.
DECIDED_STATUSES = (CERTIFIED, NO_LINEAR_PAGODA)

STATUS_MEANINGS: Dict[str, str] = {
    CERTIFIED: "weights found and re-checked in exact rationals",
    # The hedge is in the payload, not only in the write-up.  An adversarial
    # review found this string was the one unqualified existence claim that
    # reached an emitted artifact while the "floating point, no Farkas dual"
    # caveat lived only in Markdown -- i.e. exactly the shape this item exists
    # to remove, one level up: a solver's word wearing the costume of a proof.
    NO_LINEAR_PAGODA: (
        "HiGHS reported the LP infeasible in floating point, so no weight "
        "function of this shape was found with |w_i| <= bound; no exact "
        "rational infeasibility certificate (Farkas dual) is produced, so this "
        "is the solver's verdict, not a proof of non-existence"
    ),
    BUDGET: "HiGHS hit its iteration limit; feasibility was not decided",
    UNBOUNDED: "the relaxation was unbounded; feasibility was not decided",
    NUMERICAL: "HiGHS reported numerical difficulties; feasibility was not decided",
    UNDECIDED: "HiGHS returned a status this engine does not recognise",
}


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

    Since E15 this exception is the *narrow* interface: `solve` returns an
    `LpOutcome` naming which of the three it was, and only the compatibility
    wrapper `solve_certificate` still throws.
    """

    def __init__(self, message: str, outcome: Optional["LpOutcome"] = None):
        super().__init__(message)
        #: The full structured result, so a caller catching this does not have
        #: to parse the message to learn which status fired.
        self.outcome = outcome


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
            # Published because `conditions` alone does not say what it looks like
            # it says: `all({}.values())` is True, so a consumer re-deriving the
            # verdict from the dict reads "never checked" as "passed".  `holds`
            # special-cases the empty dict (D-034); the payload has to carry the
            # verdict, not the ingredients of one.
            "holds": self.holds,
            "claim": "goal unreachable from %s" % self.initial,
            "rendering": (
                "potential(s) = sum of w over occupied cells; every legal move leaves "
                "it non-increasing, and every goal state has potential > potential(%s), "
                "so no goal state is reachable from %s"
            ) % (self.initial, self.initial),
        }


@dataclass(frozen=True)
class LpOutcome:
    """What the LP ended up saying -- including *that* it did not say anything.

    The engine used to hand the caller a `Certificate` or a bare `None`, and the
    `None` carried four different meanings at once (E15).  This object carries
    the one bit that was being lost: whether the silence is a fact about the
    configuration or a fact about HiGHS.

    `no_linear_pagoda` is deliberately not spelled "infeasible": the LP is
    infeasible, the *configuration* is what the caller wants to know about, and
    the box `|w_i| <= bound` sits between the two.  `bound` therefore travels
    with the verdict rather than being a defaulted argument nobody records --
    E11 found one world in 3000 that is infeasible at `bound=10` and feasible at
    `bound=100`, so the number is load-bearing.
    """

    status: str
    solver_status: int
    solver_message: str
    bound: int
    margin: int
    certificate: Optional[Certificate] = None

    @property
    def decided(self) -> bool:
        """Did the solver answer the question that was asked of it?"""
        return self.status in DECIDED_STATUSES

    @property
    def no_linear_pagoda(self) -> bool:
        """True only where HiGHS *reported* the LP infeasible -- status 2.

        This is the predicate the whole item exists for.  A caller must never
        reconstruct it as `certificate is None`: that expression is also true
        for an iteration limit.

        "Reported", not "proved".  The reading is floating point and no exact
        rational infeasibility certificate (Farkas dual) is produced, so this is
        the solver's verdict about the LP -- attributable, which is the whole
        point, but not a proof that no such weight function exists.  E11 §7 said
        the same about the same 638 worlds; separating status 2 from status 1
        does not upgrade it, and the word here should not imply otherwise.
        """
        return self.status == NO_LINEAR_PAGODA

    @property
    def meaning(self) -> str:
        return STATUS_MEANINGS.get(self.status, STATUS_MEANINGS[UNDECIDED])

    def as_json(self) -> Dict[str, object]:
        return {
            "form": "lp_outcome",
            "status": self.status,
            "solver": "scipy.optimize.linprog (HiGHS)",
            "solver_status": self.solver_status,
            "solver_message": self.solver_message,
            "decided": self.decided,
            "no_linear_pagoda": self.no_linear_pagoda,
            "bound": self.bound,
            "margin": self.margin,
            "meaning": self.meaning,
            # Stated on every row, not only the ones where it bit: a reader of
            # `no_linear_pagoda` is entitled to know the claim is boxed.
            "scope_of_claim": (
                "linear pagodas with |w_i| <= %d and goal margin >= %d; weights "
                "outside the box are not examined" % (self.bound, self.margin)
            ),
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


def solve(graph: Dict[str, object], initial: str,
          goal_states: Optional[Sequence[str]] = None,
          margin: int = 1, bound: int = 10,
          solver_options: Optional[Dict[str, object]] = None) -> LpOutcome:
    """Look for pagoda weights proving `initial` cannot reach the goal.

    Always returns an `LpOutcome`.  There is no return value that means two
    things: `certified` carries the weights, `no_linear_pagoda` means HiGHS
    **proved the LP infeasible** (status 2), and `budget` / `unbounded` /
    `numerical` / `undecided` each name one way the solver stopped without
    deciding.  Only `no_linear_pagoda` is a statement about the configuration.

    What `no_linear_pagoda` still under-states, and why `bound` is on the
    outcome: the box is a solver parameter, not part of the pagoda definition,
    so an infeasibility is infeasibility *within* `|w_i| <= bound`.  Weights
    outside the box can exist -- E11's exhaustive sweep found one instance in
    3000 (seed 17475932563032345095, weights [12,9,3,7,-1,11,10,-4], verified in
    exact rationals).  This direction is sound: declining never certifies
    anything.  It is the engine's documented incompleteness (CLAUDE.md), widened
    slightly by a constant.

    `solver_options` is passed straight to `linprog`.  It exists so a negative
    control can drive the real solver into a real iteration limit (`maxiter`)
    instead of substituting a fake result object -- a test that stubs the solver
    proves the branch is reachable, not that HiGHS ever reaches it.
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
        options=dict(solver_options) if solver_options else None,
    )
    # HiGHS status codes: 0 optimal, 1 iteration limit, 2 infeasible,
    # 3 unbounded, 4 numerical difficulties.  The table is the classification;
    # nothing below re-derives it from `success`.
    word = STATUS_WORDS.get(int(result.status), UNDECIDED)
    message = str(getattr(result, "message", ""))
    outcome = LpOutcome(
        status=word,
        solver_status=int(result.status),
        solver_message=message,
        bound=bound,
        margin=margin,
    )
    # `success` and the status table disagreeing would mean one of the two is
    # being read wrong; that is a defect in this function, not a fact about the
    # world, so it is raised rather than classified.  The check is symmetric on
    # purpose (E15's M30 survivor): the interesting direction is not the one
    # that was guarded first.  `status == 0` with `success` false would fall
    # through to `result.x` and mint a Certificate out of whatever the failed
    # solve left behind -- and `certificate.holds` would then report it as a
    # CertificateError, i.e. as *weights that failed re-checking*, when the
    # truth is that no solve succeeded at all.  Refusing keeps a solver
    # contradiction from being laundered into a statement about the geometry,
    # which is the whole thesis of this item.
    if bool(result.success) != (word == CERTIFIED):
        # The outcome attached to the refusal is rebuilt as `undecided`, not
        # handed over as `word`.  `word` here is the reading the engine has just
        # announced it does not trust, and an exception carrying
        # `decided is True` would let a caller read a verdict off a refusal --
        # the same collapse this item removes from the return path, reappearing
        # on the error path.  What survives is the raw `solver_status`, so the
        # contradiction stays diagnosable without being quotable.
        raise LpUnavailable(
            "linprog reported success=%r with status %r, which this engine "
            "reads as %r; the two disagree, so it refuses to classify."
            % (bool(result.success), result.status, word),
            LpOutcome(
                status=UNDECIDED,
                solver_status=int(result.status),
                solver_message=message,
                bound=bound,
                margin=margin,
            ),
        )
    if word != CERTIFIED:
        return outcome

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
    return LpOutcome(
        status=CERTIFIED,
        solver_status=int(result.status),
        solver_message=message,
        bound=bound,
        margin=margin,
        certificate=certificate,
    )


def solve_certificate(graph: Dict[str, object], initial: str,
                      goal_states: Optional[Sequence[str]] = None,
                      margin: int = 1, bound: int = 10,
                      solver_options: Optional[Dict[str, object]] = None
                      ) -> Optional[Certificate]:
    """`solve`, narrowed to the older two-valued interface.

    Kept because a dozen call sites read `Certificate | None`, and because the
    narrowing is the honest one: `None` here means *only* `no_linear_pagoda`,
    and every undecided outcome raises `LpUnavailable` carrying the outcome
    itself.  New callers should use `solve` -- this signature cannot express
    "the solver gave up" without an exception, which is precisely the shape that
    made the status bit easy to lose.
    """
    outcome = solve(graph, initial, goal_states=goal_states, margin=margin,
                    bound=bound, solver_options=solver_options)
    if outcome.status == CERTIFIED:
        return outcome.certificate
    if outcome.status == NO_LINEAR_PAGODA:
        return None
    raise LpUnavailable(
        "linprog stopped without deciding feasibility: %s -- status %r (%s). "
        "This is a fact about the solver, not about the configuration, so no "
        "unreachability claim follows from it."
        % (outcome.status, outcome.solver_status, outcome.solver_message),
        outcome,
    )


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
        counterexamples: List[Dict[str, object]] = []
        if rows is None:
            sampled: Optional[bool] = None
            summary = "not run"
        elif not rows:
            # An empty report is not a clean report.  `admissibility_report`
            # returns [] on any graph where no state has a finite distance to a
            # goal, and `not []` is True -- so scoring it as a pass would make
            # "no state was examined" indistinguishable from "every state
            # passed", which is the defect this whole payload is about.
            sampled = None
            summary = "vacuous -- no state has a finite distance to a goal"
        else:
            counterexamples = [r for r in rows if not r.get("admissible")]
            sampled = not counterexamples
            summary = "%d state(s), %d counterexample(s)" % (len(rows), len(counterexamples))
        return {
            "certificate_holds": proved,
            "certificate_conditions": dict(self.certificate.conditions),
            "empirical_check": summary,
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


def premises_against_graph(certificate: "Certificate", graph: Dict[str, object]
                           ) -> Dict[str, object]:
    """Re-derive the certificate's premises from the graph, not from the certificate.

    D-035 site 1: `check_exactly` iterates `certificate.moves`, so a move geometry
    missing from that list is unconstrained in the LP and unexamined in the
    re-check at once.  Every condition can pass over a truncated list while a
    dropped move raises the potential and the claim is simply false.

    So this asks the graph instead.  `moves_raising_potential` is `inv_closed`
    recomputed over **every** geometry the graph has, which is the check
    `check_exactly` cannot perform on its own inputs.

    The goal comparison is reported, not judged: `run(..., goal_states=[...])` is
    a supported call and a certificate about other goals proves what it says.
    What it does *not* license is scoring `h` against `graph["distance_to_goal"]`,
    which measures the distance to a different set -- see `admissibility_report`.
    """
    graph_moves = moves_from_graph(graph)
    listed = {move.name() for move in certificate.moves}
    missing = [m.name() for m in graph_moves if m.name() not in listed]
    raising = [m.name() for m in graph_moves
               if m.delta(certificate.weights) > 0]
    graph_goals = sorted(graph["goal_states"])          # type: ignore[index]
    cert_goals = sorted(certificate.goal_states)
    return {
        "move_list_complete": not missing,
        "missing_moves": missing,
        "moves_raising_potential": raising,
        "goal_states_match_graph": cert_goals == graph_goals,
        "certificate_goal_states": cert_goals,
        "graph_goal_states": graph_goals,
        "sound_over_graph": not missing and not raising,
    }


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
