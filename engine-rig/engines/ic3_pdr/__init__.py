"""ic3_pdr -- public entry points.

The fallback inductive-invariant engine of Theoria 1.10(b).  It answers the same
question `lp_potential` answers -- "is the goal reachable from here?" -- but it is
not restricted to invariants shaped like a linear potential function, which is
why it settles Fixture C's configuration 0111, where the LP is infeasible and
D-014 says so on the record.

    from engines import ic3_pdr
    verdict, result = ic3_pdr.run(system, out_path=...)

`verdict` is an `Invariant` (with a certificate the independent checker in
`check.py` has already re-verified) or a `Counterexample` (a real path to the
goal, replayed by the same independent checker).  Both are answers.  Nothing is
emitted that has not been checked by code the search does not share.

Candidate provenance: the frozen contract's `engine` enum has six values and
predates this engine, so its proposals go out as `lp_potential` -- the enum
member whose unfinished business they are -- and name themselves in
`payload.producer`.  See DECISIONS.md D-018.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple

from common.candidates import emit, make_candidate
from engines.ic3_pdr.check import CheckResult, replay, verify  # noqa: F401
from engines.ic3_pdr.pdr import (  # noqa: F401
    MAX_LEVELS,
    Counterexample,
    Ic3Error,
    Invariant,
    Verdict,
    ic3,
    is_inductive,
    minimise,
)
from engines.ic3_pdr.system import (  # noqa: F401
    Clause,
    Cube,
    Literal,
    State,
    System,
    clause_key,
    cube_of,
    negate,
    peg_system,
    satisfies,
    satisfies_all,
)

ENGINE = "lp_potential"                # the frozen enum; see D-018
PRODUCER = "ic3_pdr"


def to_payload(system: System, invariant: Invariant, check: CheckResult) -> Dict[str, Any]:
    """The `invariant` payload shape for an IC3 invariant; frozen in the README."""
    initial = ", ".join(system.render_state(s) for s in system.init)
    return {
        "form": "inductive_invariant",
        "producer": PRODUCER,
        "system": system.name,
        "variables": list(system.variables),
        "initial": initial,
        "goal_states": [system.render_state(s) for s in system.bad],
        "cnf": [system.clause_as_json(c) for c in invariant.clauses],
        "cnf_text": system.render_cnf(invariant.clauses),
        "n_clauses": invariant.n_clauses,
        "converged_at_frame": invariant.level,
        "frame_sizes": list(invariant.frame_sizes),
        "states_blocked": invariant.blocked,
        "literals_dropped": invariant.generalised_literals,
        "clauses_dropped": invariant.clauses_dropped,
        "conditions": dict(check.conditions),
        "check": check.as_json(),
        "checked_by": "engines.ic3_pdr.check.verify -- shares no code with the search",
        "claim": "goal unreachable from %s" % initial,
        "rendering": (
            "I(s) = %s; it holds at %s, no move leaves it, and every goal state "
            "breaks it, so no goal state is reachable from %s"
        ) % (system.render_cnf(invariant.clauses), initial, initial),
    }


def counterexample_payload(system: System, cex: Counterexample, valid: bool
                           ) -> Dict[str, Any]:
    """The `plan` payload shape for a counterexample; frozen in the README."""
    return {
        "form": "counterexample_path",
        "producer": PRODUCER,
        "system": system.name,
        "initial": system.render_state(cex.states[0]),
        "goal_state": system.render_state(cex.states[-1]),
        "length": cex.length,
        "actions": list(cex.moves),
        "trace": [system.render_state(s) for s in cex.states],
        "replayed": valid,
        "claim": "the goal IS reachable -- no invariant separates it from the start",
        "rendering": "%s reaches %s in %d move(s): %s" % (
            system.render_state(cex.states[0]),
            system.render_state(cex.states[-1]),
            cex.length,
            " ".join(cex.moves) or "(none)",
        ),
    }


def candidates(system: System, verdict: Verdict, check: Any,
               timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
    n_states = len(system.states)
    if isinstance(verdict, Invariant):
        return [
            make_candidate(
                engine=ENGINE,
                kind="invariant",
                payload=to_payload(system, verdict, check),
                # Every state was examined; the invariant holds on this many.
                transitions=list(range(check.n_satisfying)),
                coverage="%d/%d" % (check.n_satisfying, n_states),
                timestamp=timestamp,
            )
        ]
    return [
        make_candidate(
            engine=ENGINE,
            kind="plan",
            payload=counterexample_payload(system, verdict, bool(check)),
            transitions=list(range(verdict.length)),
            coverage="%d/%d" % (verdict.length, verdict.length or 1),
            timestamp=timestamp,
        )
    ]


def run(system: System, out_path: Optional[str] = None,
        max_levels: int = MAX_LEVELS, timestamp: Optional[str] = None
        ) -> Tuple[Verdict, Any]:
    """Run IC3, re-check the answer independently, emit it.

    Raises if the independent checker refuses the invariant: an unverified
    invariant is not a weaker result, it is a wrong one, and the same call the
    LP makes (D-007) applies here.
    """
    verdict = ic3(system, max_levels=max_levels)
    if isinstance(verdict, Invariant):
        check = verify(system, verdict.clauses)
        if not check.holds:
            raise Ic3Error(
                "IC3 returned an invariant the independent checker refuses: %r"
                % (check.witnesses,)
            )
    else:
        check = replay(system, verdict.states, verdict.moves)
        if not check:
            raise Ic3Error("IC3 returned a counterexample that does not replay")
    if out_path:
        emit(out_path, candidates(system, verdict, check, timestamp=timestamp))
    return verdict, check
