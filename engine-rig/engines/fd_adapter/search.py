"""The stub backend: breadth-first search over grounded STRIPS.

BFS is optimal for unit costs, which is what the acceptance criterion needs --
"the plan length equals the hand-verified optimum" means the same thing whether
Fast Downward or this produced it.  It is a stub in reach, not in correctness:
it will not scale past toy instances, and it is not meant to.
"""

from collections import deque
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from engines.fd_adapter.pddl import Atom, Domain, GroundAction, Problem, ground_actions

State = FrozenSet[Atom]


def initial_state(problem: Problem) -> State:
    return frozenset(problem.init)


def is_goal(problem: Problem, state: State) -> bool:
    return all(a in state for a in problem.goal_positive) and not any(
        a in state for a in problem.goal_negative
    )


def applicable(action: GroundAction, state: State) -> bool:
    return all(a in state for a in action.pre_positive) and not any(
        a in state for a in action.pre_negative
    )


def successor(action: GroundAction, state: State) -> State:
    return frozenset((set(state) - set(action.del_effects)) | set(action.add_effects))


def breadth_first_plan(domain: Domain, problem: Problem,
                       max_expansions: int = 500000) -> Optional[List[GroundAction]]:
    """Shortest action sequence reaching the goal, or None if there is none."""
    actions = ground_actions(domain, problem)
    start = initial_state(problem)
    if is_goal(problem, start):
        return []

    seen = {start}
    queue: deque = deque([(start, [])])
    expansions = 0
    while queue:
        state, plan = queue.popleft()
        expansions += 1
        if expansions > max_expansions:
            raise RuntimeError("search exceeded %d expansions" % max_expansions)
        for action in actions:
            if not applicable(action, state):
                continue
            nxt = successor(action, state)
            if nxt in seen:
                continue
            extended = plan + [action]
            if is_goal(problem, nxt):
                return extended
            seen.add(nxt)
            queue.append((nxt, extended))
    return None
