"""An independent plan validator.

Deliberately does *not* import `search`: it re-grounds the actions it needs and
applies them itself, so a bug in the search's successor generation (a forgotten
delete effect, say) cannot validate itself.  The only code shared with the
planner is the parser.  See DECISIONS.md D-010.
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
