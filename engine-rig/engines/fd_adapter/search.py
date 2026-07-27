"""The stub backend: breadth-first search over grounded STRIPS.

BFS is optimal for unit costs, which is what the acceptance criterion needs --
"the plan length equals the hand-verified optimum" means the same thing whether
Fast Downward or this produced it.  It is a stub in reach, not in correctness:
it will not scale past toy instances, and it is not meant to.
"""

from collections import deque
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from engines.fd_adapter.pddl import (
    Atom,
    Domain,
    GroundAction,
    Problem,
    ground_actions,
    static_predicates,
)

State = FrozenSet[Atom]


def initial_state(problem: Problem) -> State:
    return frozenset(problem.init)


def is_goal(problem: Problem, state: State, static: Optional[set] = None) -> bool:
    static = static or set()
    return all(
        a in state for a in problem.goal_positive if a[0] not in static
    ) and not any(
        a in state for a in problem.goal_negative if a[0] not in static
    )


def applicable(action: GroundAction, state: State) -> bool:
    return all(a in state for a in action.pre_positive) and not any(
        a in state for a in action.pre_negative
    )


def successor(action: GroundAction, state: State) -> State:
    return frozenset((set(state) - set(action.del_effects)) | set(action.add_effects))


def strip_static(domain: Domain, problem: Problem, actions: List[GroundAction]):
    """Remove static atoms from the search entirely.

    A static atom's truth never changes, and grounding has already discarded
    every action whose static preconditions are false. Carrying them through the
    search is pure cost: on the A0 board each state dragged ~800 `adj` facts that
    were copied on every expansion, which is most of a 49-second solve.

    Returns (reduced actions, reduced initial state, static goal satisfied).
    """
    static = static_predicates(domain)
    initial = set(problem.init)

    def keep(atoms):
        return tuple(a for a in atoms if a[0] not in static)

    reduced = [
        GroundAction(
            name=a.name, args=a.args,
            pre_positive=keep(a.pre_positive), pre_negative=keep(a.pre_negative),
            add_effects=a.add_effects, del_effects=a.del_effects, cost=a.cost,
        )
        for a in actions
    ]
    start = frozenset(atom for atom in initial if atom[0] not in static)
    static_goal_ok = all(
        atom in initial for atom in problem.goal_positive if atom[0] in static
    ) and not any(
        atom in initial for atom in problem.goal_negative if atom[0] in static
    )
    return reduced, start, static_goal_ok


def breadth_first_plan(domain: Domain, problem: Problem,
                       max_expansions: int = 500000) -> Optional[List[GroundAction]]:
    """Shortest action sequence reaching the goal, or None if there is none."""
    actions = ground_actions(domain, problem)
    actions, start, static_goal_ok = strip_static(domain, problem, actions)
    if not static_goal_ok:
        return None
    static = static_predicates(domain)
    if is_goal(problem, start, static):
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
            if is_goal(problem, nxt, static):
                return extended
            seen.add(nxt)
            queue.append((nxt, extended))
    return None
