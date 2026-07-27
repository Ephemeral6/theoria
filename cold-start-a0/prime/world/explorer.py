"""A0′'s explorer: the same systematic walk as A0's, cut off at a budget.

A0's explorer covered every reachable (state, action) pair, and that is why A0's
inner loop had nothing to do: with complete evidence the first manual is already
the last one. `A0_REPORT.md` §6.1 called the resulting revision count of 0 a
non-result.

So A0′ truncates. The walk is identical and deterministic; it simply stops after
`BUDGET` transitions. The budget was fixed **once**, before looking at what gaps
it produced, by a stated rule:

    BUDGET = 40% of the transitions the exhaustive walk would take, rounded down
             to a multiple of ten.

That is the honest way to leave holes: pick the rule first, then report whatever
holes appear, rather than tuning the cut until the interesting one shows up. The
gaps that actually resulted are listed in `artifacts/prime_trace_summary.json`
and none of them was designed for.

`probes.jsonl` then extends the trace: a probe is executed through the same
single channel, from a state reached by replaying a prefix, and its frames are
appended. That is the mechanism A0 never got to use.
"""

import os
import sys
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from prime.world.a0p_world import ACTIONS, A0PWorld, BASE, State, WorldSpec  # noqa: E402

Key = Tuple[int, int, int]
BUDGET_FRACTION = 0.40


def shortest_paths(world: A0PWorld, source: State) -> Dict[Key, List[str]]:
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


def _walk(spec: WorldSpec, budget: Optional[int]):
    """Greedy nearest-uncovered walk; stops at `budget` transitions if given."""
    world = A0PWorld(spec)
    reachable = {s.key(): s for s in world.reachable()}
    uncovered = {(k, a) for k in reachable for a in ACTIONS}

    state = world.initial()
    states: List[State] = [state]
    actions: List[Optional[str]] = []

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


def budget_for(spec: WorldSpec) -> int:
    """40% of the exhaustive walk, floored to a multiple of ten."""
    _states, actions = _walk(spec, budget=None)
    return int(len(actions) * BUDGET_FRACTION) // 10 * 10


def explore(spec: WorldSpec = BASE, budget: Optional[int] = None):
    if budget is None:
        budget = budget_for(spec)
    states, actions = _walk(spec, budget=budget)
    actions.append(None)
    return states, actions


def coverage_report(spec: WorldSpec, states: Sequence[State],
                    actions: Sequence[Optional[str]]) -> Dict[str, object]:
    world = A0PWorld(spec)
    reachable = world.reachable()
    total = {(s.key(), a) for s in reachable for a in ACTIONS}
    seen = {(states[i].key(), actions[i])
            for i in range(len(actions)) if actions[i] is not None}

    def _kind(state: State, action: str) -> str:
        nxt = world.step(state, action)
        if nxt.switch_on != state.switch_on:
            return "toggle_%s_%s" % ("on" if nxt.switch_on else "off", action)
        if nxt.cart == state.cart:
            dr, dc = {"UP": (-1, 0), "DOWN": (1, 0),
                      "LEFT": (0, -1), "RIGHT": (0, 1)}[action]
            target = (state.cart[0] + dr, state.cart[1] + dc)
            if target == spec.crate_cell:
                return "blocked_by_crate"
            if target == spec.door_cell:
                return "blocked_by_closed_door"
            return "blocked_by_wall"
        if abs(nxt.cart[0] - state.cart[0]) + abs(nxt.cart[1] - state.cart[1]) > 1:
            return "teleport"
        return "step"

    witnessed: Dict[str, int] = {}
    for i in range(len(actions)):
        if actions[i] is None:
            continue
        witnessed[_kind(states[i], actions[i])] = \
            witnessed.get(_kind(states[i], actions[i]), 0) + 1

    never: Dict[str, int] = {}
    for key, action in sorted(total - seen):
        state = next(s for s in reachable if s.key() == key)
        kind = _kind(state, action)
        never[kind] = never.get(kind, 0) + 1

    return {
        "budget": len(actions) - 1,
        "frames": len(states),
        "transitions": len(actions) - 1,
        "reachable_states": len(reachable),
        "state_action_pairs": len(total),
        "covered_pairs": len(seen & total),
        "coverage": "%d/%d" % (len(seen & total), len(total)),
        "mechanisms_witnessed": dict(sorted(witnessed.items())),
        "mechanisms_never_witnessed": dict(sorted(never.items())),
        "win_frames": [i for i, s in enumerate(states) if world.is_win(s)],
    }
