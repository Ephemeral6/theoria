"""`lp_potential` — four invariants against an independent BFS over the state graph.

The engine's claim is **one-directional and the direction matters**, so the
property is one-directional too:

> a certificate implies the goal is unreachable. The converse is false — the
> method is sound but not complete, and `DECISIONS.md` D-014 makes the
> incompleteness a *test* so it cannot be quietly "fixed".

So `certificate_implies_unreachable` fires only on a certificate for a solvable
configuration. The absence of a certificate for a genuinely unsolvable one is not
checked here and must not be: it is the documented, deliberate gap. `0111` in the
rig's own peg fixture is unsolvable and admits no linear pagoda.

The oracle is a BFS written in `fuzzlab/oracles/search.py` over a successor
relation rebuilt here from `graph["edges"]` — not from anything the engine
computed, and not from the generator's own `solvable` flag either. A fuzz battery
that trusts the generator's asserted truth inherits whatever the generator got
wrong.

| invariant | claim under test |
|---|---|
| `certificate_implies_unreachable` | soundness: a certificate is only ever issued for a configuration from which no goal is truly reachable |
| `three_conditions_hold` | the certificate's own conditions really hold, recomputed in exact `Fraction` arithmetic |
| `heuristic_is_admissible` | `h(s) <= true distance(s)` for every state from which a goal is reachable |
| `infinite_means_unreachable` | `h(s) == inf` only where BFS confirms no goal is reachable |

`CertificateError` — the LP succeeded but the rational snap failed exact
re-checking — is documented behaviour (D-007), so it is recorded as `skipped`
with the reason rather than counted as a defect.

## The bare `return []`, and what it was hiding (V-13)

All four invariants used to open with `if cert is None: return []` (or
`if heuristic is None`). That made "I checked this world and found nothing"
and "I could not check this world at all" the *same empty list*, and
`campaign.json` counts a world as evaluated by an invariant unless that
invariant filed a `skipped`. So the standing campaign reported 500 of 500
worlds evaluated for each of the four while the measured figure is **267** —
`lp_potential` issues no certificate on 233 of 500 `jumpgraph` worlds (46.6%), and
on those worlds every invariant here costs a `linprog` call and reports
nothing.

The negative control for this is due to a parallel cross-check (E-11) and is
worth stating because it is sharper than any argument: replace
`engines.lp_potential.run` with `return None, None` — the engine **entirely
disabled** — and the four invariants' output is byte-identical to the real
engine's, while `campaign.json` goes on reporting `evaluated: 500, skipped: 0`.
A battery that cannot tell a working engine from a deleted one is not measuring
the engine. `tests/test_battery.py:test_a_dead_lp_potential_shows_up_as_lost_coverage`
is that experiment, kept as a regression.

Each `return []` is now a `finding.skipped` carrying the reason. **Nothing about
the engine changed and no new claim is checked** — the four invariants are the
same four. What changed is that the campaign's coverage column stopped
overstating itself by ~46%.

Two numbers that must not be mixed, because they answer different questions:

* **267/500 is about this battery** — the worlds on which these invariants
  actually evaluate anything;
* **the engine's incompleteness is ~21% of worlds** (E-11, exhaustive:
  639/2189 = 29.2% of certificate-less *cases*, 21.3% of the whole). Most
  certificate-less worlds are worlds where a goal is genuinely reachable and
  declining to certify is the engine being *sound*, which is the opposite of a
  gap. "No certificate" is not "incomplete", and the coverage number is not an
  engine defect rate.
"""

import math
from fractions import Fraction
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

from fuzzlab import rig  # noqa: F401  (path bootstrap)
from fuzzlab.oracles import search
from fuzzlab.props import finding

from engines import lp_potential as engine  # noqa: E402
from engines.lp_potential.potential import (  # noqa: E402
    CertificateError,
    LpUnavailable,
)

FAMILY = "jumpgraph"
ENGINE = "lp_potential"

# Above this the exhaustive admissibility sweep stops being worth the wall clock
# in a 500-world campaign; stated so the report can quote the number behind its
# `skipped` count.
SWEEP_BUDGET = 4096


def _successors(graph: Dict[str, Any]):
    """The jump relation, rebuilt from `edges` alone.

    A peg jump: `src` and `over` are occupied, `dst` is empty; afterwards `src`
    and `over` are empty and `dst` is occupied. Written out here rather than read
    from `graph["states"]` so the oracle depends on the geometry and not on any
    precomputed table the generator or the engine may share.
    """
    triples = [tuple(e["positions"]) for e in graph["edges"]]

    def step(state: str) -> Iterable[str]:
        for src, over, dst in triples:
            if state[src] == "1" and state[over] == "1" and state[dst] == "0":
                cells = list(state)
                cells[src] = cells[over] = "0"
                cells[dst] = "1"
                yield "".join(cells)

    return step


def _goal_set(world: Any) -> Set[str]:
    return set(world.goal_states)


def _solve(world: Any):
    return engine.run(world.graph, world.initial, goal_states=list(world.goal_states))


def _skip_no_certificate(world: Any, invariant: str) -> finding.Finding:
    """No certificate, so this invariant has nothing to evaluate — say so.

    Not a defect and not a pass. `lp_potential` is entitled to decline
    (D-014), and every invariant in this module is conditional on a certificate
    existing, so a world without one is a world this invariant did not judge.
    Recording it keeps `campaign.json`'s `invariant_worlds_evaluated` honest;
    the `return []` it replaces made a declined world indistinguishable from a
    clean one. See the module docstring for the measured size of the difference.
    """
    return finding.skipped(
        ENGINE, invariant, world,
        "the engine issued no certificate for this configuration, so there is "
        "no claim to check. Declining is permitted (sound but incomplete, "
        "DECISIONS.md D-014) and is often the *correct* answer here, since a "
        "goal may be genuinely reachable; either way this world was not judged "
        "by this invariant.",
        initial=world.initial, cause="no_certificate")


def _skip_certificate_error(world: Any, invariant: str,
                            exc: Exception) -> List[finding.Finding]:
    return [finding.skipped(
        ENGINE, invariant, world,
        "CertificateError — the LP succeeded but the rational snap failed exact "
        "re-checking. Documented behaviour (DECISIONS.md D-007), not a defect.",
        cause="certificate_error", error=str(exc))]


def _skip_solver_unavailable(world: Any, invariant: str,
                             exc: LpUnavailable) -> List[finding.Finding]:
    """The solver did not compute, so this world is unjudged — and says which.

    `engines.lp_potential.run` raises `LpUnavailable` for HiGHS status 1, 3 and 4
    (E-15): an iteration limit, an unbounded relaxation, numerical difficulties.
    None of the three is a statement about the configuration, so the engine
    refuses to return the `(None, None)` that downstream reads as *no linear
    pagoda separates the goal from the start*.

    That refusal has to land somewhere, and before V-21 it landed nowhere: this
    module caught `CertificateError` in four places and `LpUnavailable` in none,
    so it escaped to `finding.run_invariants`, became a `raised`, and
    `invariant_worlds_evaluated` -- which subtracts `skipped` and only `skipped`
    -- counted the world as **evaluated**.  Measured on 12 worlds with HiGHS
    starved to `maxiter=0`: the four invariants reported 11 worlds evaluated
    each, against **5** for the same worlds with the solver running normally.
    Blinding the battery raised the coverage it claimed, because the honest
    declines are subtracted and the blind spots are not.

    It is a `skipped` and not a `violated`: an iteration limit is not the engine
    doing something it says it does not do, and filing it as a violation would
    accuse the engine of the one behaviour E-15 was written to produce.  It is
    `cause_class == "unavailable"` and not `"declined"`: `no_certificate` is the
    engine looking and correctly having nothing to say, this is nobody knowing.
    `tests/test_battery.py` fails the suite on a non-zero `unavailable`, so the
    number is gated rather than filed.
    """
    outcome = getattr(exc, "outcome", None)
    data: Dict[str, Any] = {"error": str(exc)}
    if outcome is not None:
        data.update(lp_status=outcome.status, solver_status=outcome.solver_status,
                    solver_message=outcome.solver_message, decided=outcome.decided,
                    bound=outcome.bound, margin=outcome.margin)
    return [finding.skipped(
        ENGINE, invariant, world,
        "LpUnavailable — the solver stopped without deciding feasibility (%s). "
        "This is a fact about HiGHS, not about the configuration, so no claim "
        "about %r follows and this invariant judged nothing here. Not the "
        "documented incompleteness: that is `no_certificate`, where the engine "
        "looked and correctly declined."
        % (getattr(outcome, "status", "status unavailable"), world.initial),
        cause="solver_unavailable", **data)]


# --------------------------------------------------------------- invariants

def certificate_implies_unreachable(world: Any) -> List[finding.Finding]:
    """Soundness, and only soundness.  Incompleteness is documented and not checked."""
    try:
        cert, _heuristic = _solve(world)
    except LpUnavailable as exc:
        return _skip_solver_unavailable(world, "certificate_implies_unreachable", exc)
    except CertificateError as exc:
        return _skip_certificate_error(world, "certificate_implies_unreachable", exc)
    if cert is None:
        return [_skip_no_certificate(world, "certificate_implies_unreachable")]

    distance, exhausted = search.distance_to_any(
        world.initial, _successors(world.graph), _goal_set(world))
    if not exhausted:
        return [finding.skipped(
            ENGINE, "certificate_implies_unreachable", world,
            "BFS hit the state budget, so 'unreachable' could not be proved "
            "either way", cause="bfs_budget", initial=world.initial)]
    if distance is not None:
        return [finding.violated(
            ENGINE, "certificate_implies_unreachable", world,
            "a certificate was issued for %r, but BFS reaches a goal in %d moves"
            % (world.initial, distance),
            initial=world.initial, true_distance=distance,
            weights=[str(w) for w in cert.weights],
            conditions=dict(cert.conditions))]
    return []


def three_conditions_hold(world: Any) -> List[finding.Finding]:
    """`inv_closed` and `goal_break`, recomputed in exact rational arithmetic.

    `inv_init` is `potential(initial) <= potential(initial)` and is vacuously
    true; it is not re-derived here, because a property that "checks" a tautology
    reports a pass it did not earn.
    """
    try:
        cert, _heuristic = _solve(world)
    except LpUnavailable as exc:
        return _skip_solver_unavailable(world, "three_conditions_hold", exc)
    except CertificateError as exc:
        return _skip_certificate_error(world, "three_conditions_hold", exc)
    if cert is None:
        return [_skip_no_certificate(world, "three_conditions_hold")]

    weights = [Fraction(w) for w in cert.weights]

    def potential(state: str) -> Fraction:
        return sum((weights[i] for i, ch in enumerate(state) if ch == "1"),
                   Fraction(0))

    out: List[finding.Finding] = []
    for move in cert.moves:
        delta = weights[move.dst] - weights[move.src] - weights[move.over]
        if delta > 0:
            out.append(finding.violated(
                ENGINE, "three_conditions_hold", world,
                "inv_closed fails: %s raises the potential by %s"
                % (move.name(), delta),
                move=move.name(), delta=str(delta),
                reported=dict(cert.conditions)))
            break

    base = potential(cert.initial)
    for goal in cert.goal_states:
        gap = potential(goal) - base
        if gap < Fraction(cert.margin):
            out.append(finding.violated(
                ENGINE, "three_conditions_hold", world,
                "goal_break fails: goal %r is only %s above the initial "
                "potential, margin is %s" % (goal, gap, cert.margin),
                goal=goal, gap=str(gap), margin=str(cert.margin),
                reported=dict(cert.conditions)))
            break
    return out


def heuristic_is_admissible(world: Any) -> List[finding.Finding]:
    """`h(s) <= true distance(s)` wherever a goal is genuinely reachable.

    Note what is not asserted: nothing about sharpness. D-008 says outright that
    `M` is a worst case and "admissibility is the requirement, sharpness is
    not", so a heuristic of 0 on a state 5 moves out is correct behaviour.
    """
    try:
        cert, heuristic = _solve(world)
    except LpUnavailable as exc:
        return _skip_solver_unavailable(world, "heuristic_is_admissible", exc)
    except CertificateError as exc:
        return _skip_certificate_error(world, "heuristic_is_admissible", exc)
    if heuristic is None:
        return [_skip_no_certificate(world, "heuristic_is_admissible")]

    states = list(world.graph.get("states") or ())
    if not states:
        return [finding.skipped(ENGINE, "heuristic_is_admissible", world,
                                "graph carries no state list to sweep",
                                cause="no_state_list")]
    if len(states) > SWEEP_BUDGET:
        return [finding.skipped(ENGINE, "heuristic_is_admissible", world,
                                "%d states exceeds the sweep budget" % len(states),
                                cause="sweep_budget", n_states=len(states))]

    step = _successors(world.graph)
    goals = _goal_set(world)
    out: List[finding.Finding] = []
    for state in states:
        distance, exhausted = search.distance_to_any(state, step, goals)
        if distance is None or not exhausted:
            continue                    # unreachable states are the next invariant
        value = heuristic.value(state)
        if value > distance + 1e-9:
            out.append(finding.violated(
                ENGINE, "heuristic_is_admissible", world,
                "h(%r) = %s overestimates the true distance %d"
                % (state, value, distance),
                state=state, heuristic=value, true_distance=distance))
            break
    return out


def infinite_means_unreachable(world: Any) -> List[finding.Finding]:
    """`h(s) == inf` is a claim of unreachability, and it has to be true."""
    try:
        cert, heuristic = _solve(world)
    except LpUnavailable as exc:
        return _skip_solver_unavailable(world, "infinite_means_unreachable", exc)
    except CertificateError as exc:
        return _skip_certificate_error(world, "infinite_means_unreachable", exc)
    if heuristic is None:
        return [_skip_no_certificate(world, "infinite_means_unreachable")]

    states = list(world.graph.get("states") or ())
    if not states:
        return [finding.skipped(
            ENGINE, "infinite_means_unreachable", world,
            "graph carries no state list to sweep", cause="no_state_list")]
    if len(states) > SWEEP_BUDGET:
        return [finding.skipped(
            ENGINE, "infinite_means_unreachable", world,
            "%d states exceeds the sweep budget" % len(states),
            cause="sweep_budget", n_states=len(states))]

    step = _successors(world.graph)
    goals = _goal_set(world)
    out: List[finding.Finding] = []
    for state in states:
        if not math.isinf(heuristic.value(state)):
            continue
        distance, exhausted = search.distance_to_any(state, step, goals)
        if distance is not None:
            out.append(finding.violated(
                ENGINE, "infinite_means_unreachable", world,
                "h(%r) is infinite but BFS reaches a goal in %d moves"
                % (state, distance),
                state=state, true_distance=distance))
            break
        if not exhausted:
            out.append(finding.skipped(
                ENGINE, "infinite_means_unreachable", world,
                "BFS from %r hit the state budget" % state,
                cause="bfs_budget", state=state))
            break
    return out


INVARIANTS = {
    "certificate_implies_unreachable": certificate_implies_unreachable,
    "three_conditions_hold": three_conditions_hold,
    "heuristic_is_admissible": heuristic_is_admissible,
    "infinite_means_unreachable": infinite_means_unreachable,
}


def check(world: Any) -> List[finding.Finding]:
    return finding.run_invariants(ENGINE, world, INVARIANTS)
