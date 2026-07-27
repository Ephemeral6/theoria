"""Systematic explorer: a deterministic data generator, not an agent.

Same contract as A0's: it has oracle access (it *is* the world's code) and its
only job is one contiguous trajectory that exercises every reachable
(state, action) pair, so the pipeline downstream is never starved of evidence
for a reason that has nothing to do with theorizing.  What it knows does not
leak — the pipeline reads the trace and nothing else.

**A2 adds one thing, and it is the whole point of the spike.**  The world has
three monotone strata:

    0   the Button is unpressed, the Cart is in the left room
    1   the Button is pressed,   the Cart is in the left room
    2   the Cart is in the right room

Stratum 2 is entered by exactly one (state, action) pair — pushing *down* off
the Door cell (6,4) onto the Portal — and it is one-way: the right room has no
exit.  The explorer covers each stratum exhaustively before it advances, so the
single trajectory it emits has a distinguished index:

    `portal_transition` — the first (and only) transition that leaves stratum 1.

That index is where `history_trace.jsonl` is cut.  So the two traces A2 works
with are not two different experiments; they are **one experiment and its own
prefix**:

    history_trace  = raw_trace[0 .. portal_transition]        (the play record)
    raw_trace      = the whole thing                          (the full sweep)

The history is therefore *exhaustive over its own strata*: every reachable
state–action pair with the Cart in the left room appears in it, except the one
pair that would have ended it.  That is a strictly stronger setup than the one
Theoria §1.3 describes — DC22's 175 frames were a play record, not a sweep — and
it is what lets `certify` come back 100% green on a manual that has lost a rule.
"""

import os
import sys
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a2world.a2_world import (  # noqa: E402
    ACTIONS, BASE, A2World, State, WorldSpec,
)

Key = Tuple[int, int, int]

RIGHT_ROOM_COL = 6          # column c5 is solid wall; c6 and c7 are the right room


def _shortest_paths(world: A2World, source: State) -> Dict[Key, List[str]]:
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


def stratum(state: State) -> int:
    """0 unpressed-left, 1 pressed-left, 2 right room.  Non-decreasing along
    every trajectory, which is what makes exhaustive-then-advance sound."""
    if state.cart[1] >= RIGHT_ROOM_COL:
        return 2
    return int(state.pressed)


def explore(spec: WorldSpec = BASE) -> Tuple[List[State], List[Optional[str]]]:
    """Return (states, actions); `actions[i]` is taken in `states[i]`.

    `actions` has the same length as `states`, with a trailing `None`: the last
    frame is observed but nothing is done from it.
    """
    world = A2World(spec)
    reachable = {s.key(): s for s in world.reachable()}
    uncovered = {(k, a) for k in reachable for a in ACTIONS}

    state = world.initial()
    states: List[State] = [state]
    actions: List[Optional[str]] = []

    def advances(s: State, a: str) -> bool:
        return stratum(world.step(s, a)) > stratum(s)

    while uncovered:
        paths = _shortest_paths(world, state)
        here = stratum(state)

        def pool_for(defer_advancing: bool):
            out = []
            for key, action in uncovered:
                if key not in paths:
                    continue
                target = reachable[key]
                if stratum(target) != here:
                    continue
                if defer_advancing and advances(target, action):
                    continue
                out.append((len(paths[key]), key, action))
            return out

        pool = pool_for(defer_advancing=True) or pool_for(defer_advancing=False)
        if not pool:
            pool = [(len(paths[key]), key, action)
                    for key, action in uncovered if key in paths]
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


def portal_transition(spec: WorldSpec, states: Sequence[State],
                      actions: Sequence[Optional[str]]) -> Optional[int]:
    """Index `i` such that `actions[i]` is the teleport.  There is exactly one.

    Read off the *frames' geometry* — a jump of more than one cell — not off any
    flag, so the same test would find a teleport in a trace whose mechanism we
    did not already know.
    """
    found = [
        i for i in range(len(actions) - 1)
        if abs(states[i].cart[0] - states[i + 1].cart[0])
        + abs(states[i].cart[1] - states[i + 1].cart[1]) > 1
    ]
    if len(found) != 1:
        raise AssertionError(
            "expected exactly one non-adjacent Cart transition, found %d — the "
            "history cut is only well defined if the teleport fires once"
            % len(found)
        )
    return found[0]


def coverage_report(spec: WorldSpec, states: Sequence[State],
                    actions: Sequence[Optional[str]],
                    upto: Optional[int] = None) -> Dict[str, object]:
    """Coverage of `states[:upto+1]`, scored against the strata it can reach.

    `upto=None` scores the whole sweep against every reachable pair.  With
    `upto` set (the history cut) the denominator is restricted to the strata the
    prefix could possibly have visited, and the shortfall is reported explicitly
    — a coverage number quoted against an unreachable denominator would hide
    exactly the fact this spike is about.
    """
    world = A2World(spec)
    limit = len(actions) - 1 if upto is None else upto
    reachable = world.reachable()
    if upto is None:
        scope = reachable
        scope_note = "every reachable state"
    else:
        scope = [s for s in reachable if stratum(s) <= 1]
        scope_note = "every reachable state with the Cart in the left room"

    total = {(s.key(), a) for s in scope for a in ACTIONS}
    seen = {
        (states[i].key(), actions[i])
        for i in range(min(limit, len(actions) - 1))
        if actions[i] is not None
    }
    press = [i for i in range(min(limit, len(states) - 1))
             if not states[i].pressed and states[i + 1].pressed]
    portal = [
        i for i in range(min(limit, len(states) - 1))
        if abs(states[i].cart[0] - states[i + 1].cart[0])
        + abs(states[i].cart[1] - states[i + 1].cart[1]) > 1
    ]
    door_cross = [i for i in range(min(limit, len(states) - 1))
                  if spec.door_cell is not None and states[i + 1].cart == spec.door_cell]
    wins = [i for i, s in enumerate(states[:limit + 1]) if world.is_win(s)]
    missing = sorted(
        "cart=(%d,%d) pressed=%d act=%s" % (k[0], k[1], k[2], a)
        for k, a in (total - seen)
    )
    return {
        "scope": scope_note,
        "uncovered_pairs": missing,
        "frames": min(limit + 1, len(states)),
        "transitions": min(limit, len(actions) - 1),
        "reachable_states": len(reachable),
        "states_in_scope": len(scope),
        "state_action_pairs": len(total),
        "covered_pairs": len(seen & total),
        "coverage": "%d/%d" % (len(seen & total), len(total)),
        "button_press_transitions": press,
        "portal_transitions": portal,
        "door_entry_transitions": door_cross,
        "win_frames": wins,
    }
