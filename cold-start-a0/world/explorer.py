"""Systematic explorer: a deterministic data generator, not an agent.

It has oracle access to the world (it *is* the world's own code) and its only job
is to emit a single contiguous trajectory that exercises every reachable
(state, action) pair, so that the discovery pipeline downstream is never starved
of evidence for a reason that has nothing to do with theorizing.  Whatever it
knows does not leak: the pipeline reads `raw_trace.jsonl` and nothing else.

Coverage strategy -- greedy nearest-uncovered, in two strata:

  * the world has one latching flag (the Button), so a pair whose state has the
    flag clear is unreachable once the flag is set.  Pairs are therefore covered
    stratum by stratum, and inside a stratum an action that would advance the
    stratum is deferred until nothing else is left;
  * within a stratum, walk the shortest path to the nearest state carrying an
    uncovered action, take that action, repeat.

Ties are broken on explicit keys, so the trace is byte-reproducible.
"""

import os
import sys
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world.a0_world import ACTIONS, A0World, State, WorldSpec, BASE  # noqa: E402

Key = Tuple[int, int, int]


def _shortest_paths(world: A0World, source: State) -> Dict[Key, List[str]]:
    """BFS over the state graph; the action sequence reaching each state."""
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


def _stratum(state: State) -> int:
    return int(state.pressed)


def explore(spec: WorldSpec = BASE) -> Tuple[List[State], List[Optional[str]]]:
    """Return (states, actions); `actions[i]` is taken in `states[i]`.

    `actions` has the same length as `states`, with a trailing `None`: the last
    frame is observed but nothing is done from it.
    """
    world = A0World(spec)
    reachable = {s.key(): s for s in world.reachable()}
    uncovered = {(k, a) for k in reachable for a in ACTIONS}

    state = world.initial()
    states: List[State] = [state]
    actions: List[Optional[str]] = []

    def advances_stratum(s: State, a: str) -> bool:
        return _stratum(world.step(s, a)) > _stratum(s)

    while uncovered:
        paths = _shortest_paths(world, state)
        here = _stratum(state)

        def candidates(defer_advancing: bool):
            out = []
            for key, action in uncovered:
                if key not in paths:
                    continue
                target = reachable[key]
                if _stratum(target) != here:
                    continue
                if defer_advancing and advances_stratum(target, action):
                    continue
                out.append((len(paths[key]), key, action))
            return out

        pool = candidates(defer_advancing=True) or candidates(defer_advancing=False)
        if not pool:
            # nothing left in this stratum; step up if anything can
            pool = []
            for key, action in uncovered:
                if key in paths:
                    pool.append((len(paths[key]), key, action))
            if not pool:
                break
        _, key, action = min(pool)

        for step_action in paths[key]:
            state = world.step(state, step_action)
            actions.append(step_action)
            states.append(state)
        uncovered.discard((state.key(), action))
        state = world.step(state, action)
        actions.append(action)
        states.append(state)

    actions.append(None)
    return states, actions


def coverage_report(spec: WorldSpec, states: Sequence[State],
                    actions: Sequence[Optional[str]]) -> Dict[str, object]:
    world = A0World(spec)
    reachable = world.reachable()
    total = {(s.key(), a) for s in reachable for a in ACTIONS}
    seen = {
        (states[i].key(), actions[i])
        for i in range(len(actions))
        if actions[i] is not None
    }
    press = [
        i for i in range(len(actions) - 1)
        if not states[i].pressed and states[i + 1].pressed
    ]
    portal = []
    for i in range(len(actions) - 1):
        a, b = states[i].cart, states[i + 1].cart
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1:
            portal.append(i)
    door_cross = []
    for i in range(len(actions) - 1):
        if spec.door_cell is not None and states[i + 1].cart == spec.door_cell:
            door_cross.append(i)
    wins = [i for i, s in enumerate(states) if world.is_win(s)]
    missing = sorted(
        "cart=(%d,%d) pressed=%d act=%s" % (k[0], k[1], k[2], a)
        for k, a in (total - seen)
    )
    return {
        "uncovered_pairs": missing,
        "frames": len(states),
        "transitions": len(actions) - 1,
        "reachable_states": len(reachable),
        "state_action_pairs": len(total),
        "covered_pairs": len(seen & total),
        "coverage": "%d/%d" % (len(seen & total), len(total)),
        "button_press_transitions": press,
        "portal_transitions": portal,
        "door_entry_transitions": door_cross,
        "win_frames": wins,
    }
