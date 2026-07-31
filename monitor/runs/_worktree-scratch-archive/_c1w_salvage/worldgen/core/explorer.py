"""The systematic walk that produces a world's trajectory.

The algorithm is `cold-start-a0/prime/world/explorer.py`'s, lifted to an
arbitrary `GridWorld`: repeatedly find the nearest not-yet-covered
`(state, action)` pair, walk to it along a shortest path, take the action.  It
is greedy, deterministic, and it covers everything if you let it run.

Two things are different, and both are on purpose.

**The budget is a stated fraction, fixed before the gaps are looked at.**  A0′'s
report is emphatic that this is the only honest way to leave holes in a
trajectory: choose the rule, then report whatever holes appear, rather than
tuning the cut until an interesting one shows up.  `BUDGET_FRACTION` is the
default and every world in the catalogue records the budget it actually used.

**Coverage is reported per rule, not per hand-written category.**  `GridWorld.explain`
returns the ground-truth rule name alongside the successor, so the "which
mechanisms did the walk witness, and how often" table is produced by the same
code path that produces the transition.  A0′ had to re-derive that
classification in the explorer and could therefore have disagreed with the
world; here it cannot.
"""

from collections import deque
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .types import ACTIONS, State
from .world import GridWorld

BUDGET_FRACTION = 0.40
Key = Tuple[int, int, Tuple[int, ...]]


def shortest_paths(world: GridWorld, source: State) -> Dict[Key, List[str]]:
    out: Dict[Key, List[str]] = {source.key(): []}
    queue = deque([source])
    while queue:
        state = queue.popleft()
        path = out[state.key()]
        for action in ACTIONS:
            nxt = world.step(state, action)
            if nxt.key() in out:
                continue
            out[nxt.key()] = path + [action]
            queue.append(nxt)
    return out


def _walk(world: GridWorld, budget: Optional[int]) -> Tuple[List[State], List[str]]:
    reachable = {s.key(): s for s in world.reachable()}
    uncovered = {(k, a) for k in reachable for a in ACTIONS}

    state = world.initial()
    states: List[State] = [state]
    actions: List[str] = []

    while uncovered:
        if budget is not None and len(actions) >= budget:
            break
        paths = shortest_paths(world, state)
        pool = [(len(paths[key]), key, action)
                for key, action in uncovered if key in paths]
        if not pool:
            break
        _, key, action = min(pool)
        for step_action in paths[key]:
            if budget is not None and len(actions) >= budget:
                break
            state = world.step(state, step_action)
            actions.append(step_action)
            states.append(state)
        if budget is not None and len(actions) >= budget:
            break
        uncovered.discard((state.key(), action))
        state = world.step(state, action)
        actions.append(action)
        states.append(state)

    return states, actions


def exhaustive_length(world: GridWorld) -> int:
    return len(_walk(world, budget=None)[1])


def budget_for(world: GridWorld, fraction: float = BUDGET_FRACTION) -> int:
    """`fraction` of the exhaustive walk, floored to a multiple of ten.

    Floored to ten so that the number in a world's manifest is obviously a
    policy and not a tuned constant.
    """
    return max(10, int(exhaustive_length(world) * fraction) // 10 * 10)


def explore(world: GridWorld, budget: Optional[int] = None,
            fraction: float = BUDGET_FRACTION):
    """Returns `(states, actions)` with `actions[-1] is None`, matching the trace format."""
    if budget is None:
        budget = budget_for(world, fraction)
    states, actions = _walk(world, budget=budget)
    return states, list(actions) + [None]


def coverage_report(world: GridWorld, states: Sequence[State],
                    actions: Sequence[Optional[str]]) -> Dict[str, object]:
    reachable = world.reachable()
    total = {(s.key(), a) for s in reachable for a in ACTIONS}
    seen = {(states[i].key(), actions[i])
            for i in range(len(actions)) if actions[i] is not None}

    witnessed: Dict[str, int] = {}
    for i, action in enumerate(actions):
        if action is None:
            continue
        rule = world.explain(states[i], action)[1]
        witnessed[rule] = witnessed.get(rule, 0) + 1

    by_key = {s.key(): s for s in reachable}
    never: Dict[str, int] = {}
    for key, action in sorted(total - seen):
        rule = world.explain(by_key[key], action)[1]
        never[rule] = never.get(rule, 0) + 1

    return {
        "budget": len(actions) - 1,
        "frames": len(states),
        "transitions": len(actions) - 1,
        "reachable_states": len(reachable),
        "state_action_pairs": len(total),
        "covered_pairs": len(seen & total),
        "coverage": "%d/%d" % (len(seen & total), len(total)),
        "coverage_fraction": round(len(seen & total) / max(1, len(total)), 4),
        "rules_witnessed": dict(sorted(witnessed.items())),
        "rules_never_witnessed": dict(sorted(never.items())),
        "win_frames": [i for i, s in enumerate(states) if world.is_win(s)],
    }
