"""A replay validator: independent of the search, not of the grounding.

Deliberately does *not* import `search`.  It replays the plan itself, so a bug
in the search's frontier, ordering or duplicate detection cannot certify its own
output -- and `__init__.py` calls this on every rung of the ladder, including a
plan handed back by a real Fast Downward, whose frontier is not ours at all.
That is the part worth keeping: no planner here grades its own answer.

The shared premise is `pddl.ground_actions`, which this module and `search` both
import.  That is not merely the parser.  `ground_actions` filters on static
preconditions while it instantiates, and so decides which action instances could
ever fire, with which effects -- it is the successor-generation layer.  A
forgotten delete effect *there* is invisible here, because the replay steps
through the same instances the search stepped through.  So a plan passing this
is a plan whose steps are legal under the shared grounding, not one legal under
the PDDL as written.

The gap runs the other way too.  For a plan produced outside this rig, a
grounding disagreement surfaces as `"is not a ground action"` below: a false
reject of a sound plan, not a false accept of an unsound one.

See DECISIONS.md D-010 and D-035.
"""

from typing import Dict, List, Sequence, Set, Tuple

from engines.fd_adapter.pddl import (
    Atom,
    Domain,
    Problem,
    _substitute,
    ground_actions,
)


class InvalidPlan(Exception):
    pass


def parse_action_text(text: str) -> Tuple[str, Tuple[str, ...]]:
    parts = text.strip().strip("()").split()
    if not parts:
        raise InvalidPlan("empty action %r" % text)
    return parts[0], tuple(parts[1:])


def validate_plan(domain: Domain, problem: Problem, plan: Sequence[str]) -> bool:
    """Replay the plan from the initial state and check the goal holds at the end.

    Raises InvalidPlan with the offending step rather than returning False, so a
    failure names what went wrong.
    """
    index = {(a.name, a.args): a for a in ground_actions(domain, problem)}
    state: Set[Atom] = set(problem.init)

    for step, text in enumerate(plan):
        key = parse_action_text(text)
        action = index.get(key)
        if action is None:
            raise InvalidPlan("step %d: %r is not a ground action" % (step, text))
        for atom in action.pre_positive:
            if atom not in state:
                raise InvalidPlan(
                    "step %d (%s): precondition %s does not hold" % (step, text, " ".join(atom))
                )
        for atom in action.pre_negative:
            if atom in state:
                raise InvalidPlan(
                    "step %d (%s): negative precondition %s is violated"
                    % (step, text, " ".join(atom))
                )
        state -= set(action.del_effects)
        state |= set(action.add_effects)

    for atom in problem.goal_positive:
        if atom not in state:
            raise InvalidPlan("goal atom %s does not hold at the end" % " ".join(atom))
    for atom in problem.goal_negative:
        if atom in state:
            raise InvalidPlan("negated goal atom %s holds at the end" % " ".join(atom))
    return True
