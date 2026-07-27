"""An independent checker for the invariant IC3 returns.

Deliberately does *not* import `pdr`.  It re-derives the three conditions from
the system and the clause set alone, by enumeration, so a bug in the frames --
a convergence test that fires one level early, a clause propagated without being
relative-inductive -- cannot certify itself.  Same discipline as the plan
validator (DECISIONS D-010), and the same reason: a search that grades its own
homework grades it generously.

The three conditions are the Lean skeleton of Theoria 1.10(a), verbatim:

    theorem inv_init   : I s0
    theorem inv_closed : forall s a, I s -> I (step s a)
    theorem goal_break : forall s, Goal s -> not (I s)

and together they give `unsolvable`.  `lp_potential` reports the same three
keys for its pagoda certificate, which is the point: two engines, two invariant
shapes, one proof obligation, so the adjudicating reader compares like with like.
"""

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from engines.ic3_pdr.system import Clause, State, System, satisfies_all


@dataclass
class CheckResult:
    conditions: Dict[str, bool]
    witnesses: Dict[str, List[str]]
    n_states: int
    n_satisfying: int

    @property
    def holds(self) -> bool:
        return bool(self.conditions) and all(self.conditions.values())

    def as_json(self) -> Dict[str, object]:
        return {
            "conditions": dict(self.conditions),
            "counterexamples": {k: list(v) for k, v in sorted(self.witnesses.items())},
            "n_states": self.n_states,
            "n_satisfying": self.n_satisfying,
            "method": "exhaustive enumeration over the state space",
        }


def verify(system: System, clauses: Sequence[Clause]) -> CheckResult:
    """Re-check inv_init / inv_closed / goal_break from scratch."""
    clauses = list(clauses)
    satisfying = [s for s in system.states if satisfies_all(s, clauses)]
    inside = set(satisfying)

    failures: Dict[str, List[str]] = {"inv_init": [], "inv_closed": [], "goal_break": []}

    for state in system.init:
        if state not in inside:
            failures["inv_init"].append(system.render_state(state))

    for state in satisfying:
        for label, successor in system.moves(state):
            if successor not in inside:
                failures["inv_closed"].append(
                    "%s -%s-> %s"
                    % (system.render_state(state), label, system.render_state(successor))
                )

    for state in system.bad:
        if state in inside:
            failures["goal_break"].append(system.render_state(state))

    return CheckResult(
        conditions={name: not found for name, found in failures.items()},
        witnesses={name: found for name, found in failures.items() if found},
        n_states=len(system.states),
        n_satisfying=len(satisfying),
    )


def replay(system: System, states: Sequence[State], moves: Sequence[str]) -> bool:
    """Check a counterexample really is a path from init to a bad state."""
    if not states or states[0] not in system.init:
        return False
    if len(states) != len(moves) + 1:
        return False
    for index, label in enumerate(moves):
        if (label, states[index + 1]) not in system.moves(states[index]):
            return False
    return system.is_bad(states[-1])
