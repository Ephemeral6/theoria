"""`lp_potential` mutants — six defects, against an engine that is *allowed* to
say nothing.

The seam is `props/lp_potential.py:_solve`, the single place the property module
calls `engines.lp_potential.run`. It returns the pair `(certificate, heuristic)`,
and all four invariants funnel through it, so one rebinding reaches all of them.
`_successors` and `_goal_set` are **not** seams: they are the oracle — the BFS
side that recomputes the truth from `graph["edges"]`. Corrupting those would lie
to the judge rather than to the judged, and would measure nothing.

## The thing that makes this engine different from the other five

`lp_potential` is **sound but incomplete** (`CLAUDE.md`; `DECISIONS.md` D-014;
`engines/lp_potential/README.md` "Sound but not complete"). It never certifies a
solvable configuration, and some genuinely unsolvable ones admit no linear
pagoda. That fixes what a mutant here is allowed to be:

* issuing a certificate for a configuration from which a goal **is** reachable
  is a real defect — the whole soundness claim;
* **withholding** a certificate from an unsolvable configuration is **not** a
  defect. It is the documented gap. There is deliberately no mutant below for
  it, because a mutant that removes a certificate the engine was never obliged
  to give would "survive" every invariant and that survival would mean nothing
  except that the mutant was wrong.

The same line rules out reading `CertificateError` as detection: D-007 says the
engine raises rather than emit weights that only hold to 1e-9, and
`props/lp_potential.py:_skip_certificate_error` records it as `skipped`. A mutant
that pushes worlds into `skipped` has *unmeasured* them, not survived them.

## What gates the whole battery

Every one of the four invariants opens with `if cert is None: return []` (or
`if heuristic is None`). So on a world where the engine issues no certificate,
**all four invariants are vacuous** — they cost a `linprog` call and report
nothing. Only `lp-certify-solvable` can be evaluated on such a world, because it
is the only one that manufactures a certificate rather than editing one. This is
why the per-mutant `worlds_evaluated` column matters more here than anywhere
else: it is the real size of the campaign for this engine, and it is not the
world count.

## Two structural facts, recorded here rather than discovered later

* `three_conditions_hold` re-checks `inv_closed` by iterating **`cert.moves`** —
  the engine's own list of jump geometries — not the world's `graph["edges"]`.
  So a certificate that omits a legal move is re-checked against exactly the
  moves it chose to admit. `lp-raise-one-move` and `lp-hide-the-raised-move`
  make the identical weight defect and differ only in whether the broken move
  stays in that list; the pair is the measurement of this gap.
* `infinite_means_unreachable` is **subsumed** by `heuristic_is_admissible`: an
  infinite `h` at a state with a finite true distance is, by definition, an
  overestimate, and both invariants sweep the same `graph["states"]` under the
  same `SWEEP_BUDGET`. Any world that kills the fourth invariant kills the third.
  They are not independent, and `lp-infinite-on-reachable` pre-registers both.

## Two framework notes

* The seam returns a **tuple**, and `mutants.applied` reads the `touched()` mark
  off the object the seam returned. `touched()` on a tuple raises by design. So a
  mutant that shadows a *method* on an inner object cannot be marked, and would
  be counted inert on every world. `lp-heuristic-off-by-one` and
  `lp-infinite-on-reachable` therefore return a `Heuristic` **subclass**, whose
  dataclass `repr` carries a different `__qualname__` and so is visible to the
  `repr(before) != repr(after)` check the framework falls back on. No framework
  file was edited.
* Two mutants edit `cert.weights` while the returned `Heuristic` still holds a
  reference to the same certificate object, which would let a certificate defect
  leak into the two heuristic invariants and blur which invariant did the
  catching. Both rebind `heuristic.certificate` to a pristine copy first. That is
  a describable engine state, not a convenience: D-007's snap
  (`Fraction.limit_denominator`, potential.py:173) is applied on the way into the
  certificate, so a defect introduced by the snap moves the published weights and
  not the ones the heuristic was already built from.
"""

import copy
import math
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

from fuzzlab import mutants as mut
from fuzzlab import rig  # noqa: F401  (path bootstrap)
from fuzzlab.oracles import search
from fuzzlab.props.lp_potential import _goal_set, _successors

from engines.lp_potential.potential import (  # noqa: E402
    Certificate,
    Heuristic,
    Move,
    heuristic_from,
    moves_from_graph,
)

ENGINE = "lp_potential"
SEAM = "_solve"


# --------------------------------------------------------------- oracle reads
#
# The oracle is read here to *aim* the injection — the same thing
# `mutants/zero_space.py:_add_bogus_basis_vector` does when it probes `gf2` for a
# vector known to lie outside the true null space. It decides where a lie is
# genuinely a lie; it never decides whether the invariant caught it. The property
# recomputes its own BFS from `graph["edges"]` either way.

_REACHABLE_STATE: Dict[int, Optional[Tuple[str, int]]] = {}


def _solvable_from_initial(world: Any) -> Optional[int]:
    """True distance from `world.initial` to the nearest goal, or None."""
    distance, exhausted = search.distance_to_any(
        world.initial, _successors(world.graph), _goal_set(world))
    return distance if (distance is not None and exhausted) else None


def _a_reachable_state(world: Any) -> Optional[Tuple[str, int]]:
    """Some `(state, true distance)` with the goal genuinely reachable.

    Cached per world: the seam is called once per invariant, so an uncached sweep
    would repeat this four times per world for no new information.
    """
    if world.seed in _REACHABLE_STATE:
        return _REACHABLE_STATE[world.seed]
    step = _successors(world.graph)
    goals = _goal_set(world)
    found: Optional[Tuple[str, int]] = None
    for state in world.graph.get("states") or ():
        distance, exhausted = search.distance_to_any(state, step, goals)
        if distance is not None and exhausted:
            found = (state, distance)
            break
    _REACHABLE_STATE[world.seed] = found
    return found


# ------------------------------------------------------- the weight-bump search
#
# Shared by the two `inv_closed` mutants so that they differ in exactly one line
# and their inert sets are identical, which is what makes the comparison between
# them a controlled one.

def _coefficient(move: Move, position: int) -> int:
    return ((1 if move.dst == position else 0)
            - (1 if move.src == position else 0)
            - (1 if move.over == position else 0))


def _pick_break(cert: Certificate) -> Optional[Tuple[int, int, Fraction]]:
    """`(move index, position, delta to add to that weight)` breaking one move.

    Chosen so the damage is exactly one move wide:

    * after the edit the target move raises the potential by 1, so `inv_closed`
      is false of it;
    * every *other* move in `cert.moves` still has `delta <= 0`, so nothing else
      in the certificate becomes checkable-and-broken;
    * the edited position is occupied identically in `initial` and in every goal,
      so `potential(goal) - potential(initial)` is unchanged and `goal_break`
      keeps whatever verdict it had. Without this the mutant would trip
      `three_conditions_hold` through the goal branch even when the move branch
      failed to notice, and the two branches would be indistinguishable.

    Deterministic: first move, then position in (dst, src, over) order.
    """
    weights = list(cert.weights)
    initial = cert.initial

    def gap_neutral(position: int) -> bool:
        here = initial[position]
        return all(goal[position] == here for goal in cert.goal_states)

    for index, move in enumerate(cert.moves):
        delta = move.delta(weights)
        for position in (move.dst, move.src, move.over):
            coefficient = _coefficient(move, position)
            if coefficient == 0:                       # cannot happen: distinct
                continue                               # pragma: no cover
            if not gap_neutral(position):
                continue
            change = ((-delta + 1) if coefficient > 0 else (delta - 1))
            bumped = list(weights)
            bumped[position] = bumped[position] + change
            if move.delta(bumped) <= 0:                # pragma: no cover
                continue
            if any(other.delta(bumped) > 0
                   for j, other in enumerate(cert.moves) if j != index):
                continue
            return index, position, change
    return None


def _pristine_heuristic(heuristic: Heuristic, cert: Certificate) -> None:
    """Point the heuristic at an unedited copy of the certificate."""
    heuristic.certificate = copy.deepcopy(cert)


# ------------------------------------------------------------------- mutants

def _certify_solvable(result: Any, args: Tuple[Any, ...],
                      kwargs: Dict[str, Any]) -> Any:
    cert, _heuristic = result
    if cert is not None:
        raise mut.inert("engine already issued a certificate here; this mutant "
                        "is about manufacturing one where it declined")
    world = args[0]
    if _solvable_from_initial(world) is None:
        raise mut.inert(
            "BFS finds no goal reachable from the initial state, so withholding "
            "a certificate is the documented incompleteness (D-014) and a "
            "fabricated certificate would not be a false claim about "
            "reachability")
    graph = world.graph
    weights = [Fraction(0)] * int(graph["n_pos"])
    forged = Certificate(
        weights=weights,
        initial=world.initial,
        goal_states=list(world.goal_states),
        moves=moves_from_graph(graph),
        margin=Fraction(1),
        # What a run with the two None-returning guards removed would publish:
        # the LP was infeasible, the exact re-check was never consulted, and the
        # conditions dict says the argument holds.
        conditions={"inv_init": True, "inv_closed": True, "goal_break": True},
    )
    return forged, heuristic_from(forged)


def _raise_one_move(result: Any, args: Tuple[Any, ...],
                    kwargs: Dict[str, Any]) -> Any:
    cert, heuristic = result
    if cert is None:
        raise mut.inert("no certificate on this world; there is nothing to "
                        "edit -- the incompleteness, not a defect")
    pick = _pick_break(cert)
    if pick is None:
        raise mut.inert("no single weight edit breaks exactly one listed move "
                        "while leaving the goal margin and every other move "
                        "untouched")
    _index, position, change = pick
    _pristine_heuristic(heuristic, cert)
    cert.weights[position] = cert.weights[position] + change
    return cert, heuristic


def _hide_the_raised_move(result: Any, args: Tuple[Any, ...],
                          kwargs: Dict[str, Any]) -> Any:
    cert, heuristic = result
    if cert is None:
        raise mut.inert("no certificate on this world; there is nothing to "
                        "edit -- the incompleteness, not a defect")
    pick = _pick_break(cert)
    if pick is None:
        raise mut.inert("no single weight edit breaks exactly one listed move "
                        "while leaving the goal margin and every other move "
                        "untouched")
    index, position, change = pick
    _pristine_heuristic(heuristic, cert)
    cert.weights[position] = cert.weights[position] + change
    cert.moves = [m for j, m in enumerate(cert.moves) if j != index]
    return cert, heuristic


def _overstate_margin(result: Any, args: Tuple[Any, ...],
                      kwargs: Dict[str, Any]) -> Any:
    cert, heuristic = result
    if cert is None:
        raise mut.inert("no certificate on this world; no margin to overstate")
    if not cert.goal_states:
        raise mut.inert("certificate carries no goal states")   # pragma: no cover
    base = cert.initial_potential
    gap = min(cert.potential(goal) - base for goal in cert.goal_states)
    cert.margin = gap + 1
    return cert, heuristic


class _PatchedHeuristic(Heuristic):
    """A heuristic that answers `override` at one state and defers elsewhere.

    A subclass rather than a shadowed method on the real object: the seam returns
    a tuple, `mutants.touched()` cannot mark a tuple, and the framework's
    fallback is `repr(before) != repr(after)`. A dataclass `repr` renders
    `self.__class__.__qualname__`, so the substitution is visible there and the
    mutant is not miscounted inert on every world.
    """

    def __init__(self, base: Heuristic, state: str, override: float) -> None:
        super().__init__(certificate=base.certificate,
                         max_decrease=base.max_decrease)
        self.state = state
        self.override = float(override)

    def value(self, state: str) -> float:
        if state == self.state:
            return self.override
        return super().value(state)


def _heuristic_off_by_one(result: Any, args: Tuple[Any, ...],
                          kwargs: Dict[str, Any]) -> Any:
    cert, heuristic = result
    if heuristic is None:
        raise mut.inert("no certificate on this world, so no heuristic -- the "
                        "incompleteness, not a defect")
    target = _a_reachable_state(args[0])
    if target is None:
        raise mut.inert("no state in this world reaches a goal, so no finite "
                        "true distance exists to overshoot")
    state, distance = target
    return cert, _PatchedHeuristic(heuristic, state, distance + 1)


def _infinite_on_reachable(result: Any, args: Tuple[Any, ...],
                           kwargs: Dict[str, Any]) -> Any:
    cert, heuristic = result
    if heuristic is None:
        raise mut.inert("no certificate on this world, so no heuristic -- the "
                        "incompleteness, not a defect")
    target = _a_reachable_state(args[0])
    if target is None:
        raise mut.inert("no state in this world reaches a goal, so an infinite "
                        "h would not be a false claim anywhere")
    state, _distance = target
    return cert, _PatchedHeuristic(heuristic, state, math.inf)


mut.register(
    mut.Mutant(
        id="lp-certify-solvable",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="a certificate is only ever issued for a configuration from which "
              "no goal is reachable -- engines/lp_potential/README.md 'it can "
              "never prove a false one'; potential.py:solve_certificate returns "
              "None when the LP is infeasible (line 170) and raises "
              "CertificateError when the exact re-check fails (line 186). This "
              "is the *sound* half of 'sound but incomplete', and it is the one "
              "half the incompleteness does not excuse.",
        description="on a world where BFS proves a goal reachable and the engine "
                    "correctly issued nothing, return the certificate a run with "
                    "both None-returning guards removed would publish: the "
                    "all-zero weight vector, margin 1, and a conditions dict "
                    "asserting all three conditions hold.",
        corrupt=_certify_solvable,
        expect_kill=("certificate_implies_unreachable", "three_conditions_hold"),
    ),
    mut.Mutant(
        id="lp-raise-one-move",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="inv_closed: every legal move leaves the potential non-increasing, "
              "re-checked in exact rationals -- potential.py:check_exactly lines "
              "205-209, README 'w[dst] - w[src] - w[over] <= 0 for every jump "
              "geometry'. A certificate whose weights let a listed move raise "
              "the potential has no closure step, so its unreachability claim "
              "does not follow.",
        description="add the smallest integer to one weight that makes exactly "
                    "one *listed* move raise the potential by 1, chosen so that "
                    "no other listed move turns positive and the initial-to-goal "
                    "gap is unchanged. The heuristic keeps the pre-edit "
                    "certificate, so only the certificate is defective.",
        corrupt=_raise_one_move,
        expect_kill=("three_conditions_hold",),
    ),
    mut.Mutant(
        id="lp-hide-the-raised-move",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="same claim as lp-raise-one-move, plus: cert.moves is the full set "
              "of distinct jump geometries of the graph -- "
              "potential.py:moves_from_graph builds it from graph['edges'], and "
              "check_exactly's closure argument is only 'independent of which "
              "states are reachable' if the move list is complete. A certificate "
              "that omits a legal move which *would* raise the potential asserts "
              "unreachability on an argument with a hole in it.",
        description="the identical weight edit as lp-raise-one-move, and then "
                    "the broken move is dropped from cert.moves. Normatively "
                    "three_conditions_hold should still catch it; the empirical "
                    "prediction, written before the run, is that it cannot, "
                    "because it re-checks the moves the engine reports rather "
                    "than the moves the graph has.",
        corrupt=_hide_the_raised_move,
        expect_kill=("three_conditions_hold",),
    ),
    mut.Mutant(
        id="lp-overstate-margin",
        engine=ENGINE, seam=SEAM, kind=mut.INCONSISTENT,
        claim="goal_break holds at the published margin: the LP constrains "
              "potential(s0) - potential(g) <= -margin (potential.py:142-149), "
              "check_exactly re-derives it at cert.margin, and as_json publishes "
              "margin and conditions side by side. A certificate reporting a "
              "margin its own weights do not achieve, with goal_break still "
              "True, states a false fact about its own strength.",
        description="raise cert.margin to one more than the smallest achieved "
                    "gap between a goal's potential and the initial potential, "
                    "leaving weights, moves and conditions untouched. Nothing "
                    "else in the engine reads margin, so this is the goal_break "
                    "branch of three_conditions_hold on its own.",
        corrupt=_overstate_margin,
        expect_kill=("three_conditions_hold",),
    ),
    mut.Mutant(
        id="lp-heuristic-off-by-one",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="h(s) never exceeds the true shortest distance -- DECISIONS.md "
              "D-008 'admissible by construction', Heuristic.as_json publishes "
              "\"admissible\": true, and the whole point of the ceil-of-quotient "
              "form is that it is a lower bound.",
        description="at one state the oracle proves reachable, return true "
                    "distance + 1 instead of the engine's value; every other "
                    "state answers exactly as before. The smallest possible "
                    "inadmissibility -- if the invariant needs a wilder lie than "
                    "this to fire, it is not checking admissibility.",
        corrupt=_heuristic_off_by_one,
        expect_kill=("heuristic_is_admissible",),
    ),
    mut.Mutant(
        id="lp-infinite-on-reachable",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="an infinite h is a per-state unsolvability claim and every such "
              "claim is checked against the enumeration -- README 'An infinite "
              "value is the certificate's per-state form'; potential.py:"
              "Heuristic.value documents inf as 'a per-state unsolvability "
              "claim'. Unlike a missing certificate, an infinite h is an "
              "assertion, so the incompleteness does not cover it.",
        description="at one state the oracle proves reachable, return inf. "
                    "Pre-registered against both heuristic invariants, not one: "
                    "inf at a state with a finite true distance is also an "
                    "overestimate, so infinite_means_unreachable cannot fire "
                    "where heuristic_is_admissible does not.",
        corrupt=_infinite_on_reachable,
        expect_kill=("infinite_means_unreachable", "heuristic_is_admissible"),
    ),
)
