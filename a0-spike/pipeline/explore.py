"""Targeted exploration: reach a divergent state, then act there.

The first mining pass on a casual walk produces rules whose guards are accidental
correlates -- `blocked_DOWN` came out as `act==DOWN and ahead_is_box(LEFT)`,
which is true of both its witnesses and of nothing else, and is nonsense. That is
not a defect in the miner; it is what two witnesses entitle anyone to conclude.

The cure is the framework's: reaching a state that discriminates is a planning
problem, and getting back to it is prefix replay -- reset and re-walk a recorded
path, which costs actions but no model calls (Theoria 1.10b).

So exploration here is a set of *episodes*. Each episode resets, walks a planned
prefix to a state where some rule class can be witnessed, and takes the action
that witnesses it. Transitions from all episodes pool into one evidence set.
"""

import os
import sys
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from world.sokoban2 import (        # noqa: E402
    BLOCKED,
    DIRECTIONS,
    Level,
    State,
    initial_state,
    render,
    step,
)


@dataclass
class Episode:
    """One reset-and-walk. `actions` includes the final witnessing action."""

    actions: List[str]
    purpose: str


def _paths_from_start(level: Level, max_states: int = 20000
                      ) -> Dict[Tuple, List[str]]:
    """Shortest action prefix from the initial state to every reachable state."""
    start = initial_state(level)
    paths: Dict[Tuple, List[str]] = {start.key(): []}
    queue = deque([start])
    while queue and len(paths) < max_states:
        state = queue.popleft()
        for action in DIRECTIONS:
            nxt, event = step(level, state, action)
            if event == BLOCKED or nxt.key() in paths:
                continue
            paths[nxt.key()] = paths[state.key()] + [action]
            queue.append(nxt)
    return paths


def _state_of(level: Level, actions: Sequence[str]) -> State:
    state = initial_state(level)
    for action in actions:
        state, _ = step(level, state, action)
    return state


def _signature(level: Level, state: State, action: str) -> str:
    """Observable situation type, computed from what a frame shows.

    Uses only predicates the pipeline can evaluate on a rendered frame -- where
    the box is relative to the player, and whether the cells it would cross are
    clear. It does NOT read the rule table. Its job is to make sure the evidence
    set contains both halves of every distinction the guard language can draw,
    which is what stops a rule being under-guarded merely because the situation
    never came up.
    """
    from world.sokoban2 import DELTA, is_wall

    dr, dc = DELTA[action]
    ahead = (state.player[0] + dr, state.player[1] + dc)
    if ahead != state.box:
        on_board = 0 <= ahead[0] < level.height and 0 <= ahead[1] < level.width
        return "clear" if (on_board and not is_wall(level, ahead)) else "obstructed"
    over = (state.box[0] + dr, state.box[1] + dc)
    landing = (state.box[0] + dr * 2, state.box[1] + dc * 2)

    def free(cell):
        return (0 <= cell[0] < level.height and 0 <= cell[1] < level.width
                and not is_wall(level, cell))

    if free(over) and free(landing):
        return "box_slidable"
    return "box_stuck"


def plan_episodes(level: Level, per_class: int = 4) -> List[Episode]:
    """Episodes witnessing each (action, situation) at least `per_class` times.

    Classifying by *situation* rather than by outcome is the point: "nothing
    moved" lumps a wall in front together with a box that cannot slide, and if
    only one of those is ever seen the mined guard is under-determined while
    still replaying history perfectly.

    Deterministic: states are taken in breadth-first order, so a level always
    yields the same evidence set.
    """
    paths = _paths_from_start(level)
    ordered = sorted(paths.items(), key=lambda kv: (len(kv[1]), kv[0]))

    counts: Dict[Tuple[str, str], int] = {}
    episodes: List[Episode] = []
    for key, prefix in ordered:
        state = _state_of(level, prefix)
        for action in DIRECTIONS:
            situation = _signature(level, state, action)
            slot = (action, situation)
            if counts.get(slot, 0) >= per_class:
                continue
            counts[slot] = counts.get(slot, 0) + 1
            episodes.append(
                Episode(actions=list(prefix) + [action],
                        purpose="witness %s under %s" % (situation, action))
            )
    return episodes


def run_episodes(level: Level, episodes: Sequence[Episode]) -> List[Dict[str, object]]:
    """Execute each episode, returning frames and actions per episode."""
    out = []
    for episode in episodes:
        state = initial_state(level)
        frames = [render(level, state)]
        events = []
        for action in episode.actions:
            state, event = step(level, state, action)
            frames.append(render(level, state))
            events.append(event)
        out.append(
            {
                "frames": frames,
                "actions": list(episode.actions),
                "events": events,
                "purpose": episode.purpose,
            }
        )
    return out


def evidence_set(level: Level, per_class: int = 4) -> Dict[str, object]:
    episodes = plan_episodes(level, per_class=per_class)
    runs = run_episodes(level, episodes)
    total_actions = sum(len(r["actions"]) for r in runs)      # type: ignore[arg-type]
    return {
        "episodes": runs,
        "n_episodes": len(runs),
        "action_budget_spent": total_actions,
        "witnessed": _coverage(runs),
    }


def _coverage(runs: Sequence[Dict[str, object]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for run in runs:
        for action, event in zip(run["actions"], run["events"]):    # type: ignore[arg-type]
            key = "%s/%s" % (action, event)
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))
