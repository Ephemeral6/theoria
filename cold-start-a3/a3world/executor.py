"""The environment proxy — the only way an arm may touch the world after planning.

An arm has to be able to *act*: a plan that is never executed proves nothing,
and Theoria's inner loop ends in 解出 (solve), not in 规划 (plan).  What an arm
must never do is *read the transition function*.  Those two are separated here
rather than by a rule someone is asked to follow:

* `execute(level, plan)` takes a level **name** and a list of actions, and
  returns **frames** — the same four-key rows every trace in this directory
  uses.  It is shaped like a game API on purpose.
* `a3pipeline/*` may import this module.  It may not import `a3world.a3_world`
  or name `A3World`, and `tests/test_sealing.py::test_no_pipeline_module_imports
  _the_world` fails the suite if one does.

The level is named by string for the same reason.  An arm that had to import
`L2` to execute against it would already be holding a `LevelSpec`, and a
`LevelSpec` is the answer key: every coordinate the transfer arm is supposed to
be deriving or being supplied is a field on it.

**Executing costs actions, and the meter charges for them.**  This is the line
that matters on a live game, where an action is quota.  The transfer arm's bill
is dominated by it — the arm reads one frame and then spends exactly as many
actions as its plan is long, which is the shape C3 predicts and the reason the
meter counts frames and actions separately.
"""

import json
import os
from typing import Dict, List, Optional, Sequence

from a3world.a3_world import LEVELS, A3World


def execute(level: str, plan: Sequence[str],
            stop_on_win: bool = True) -> Dict[str, object]:
    """Run `plan` from the level's initial state; hand back frames.

    Returns the observation record and nothing derived from the world's
    internals: frames, the actions that produced them, the win flag, and how
    many actions were actually spent.  No state object, no transition function,
    no reachable set.
    """
    if level not in LEVELS:
        raise KeyError("no such level: %r" % level)
    world = A3World(LEVELS[level])

    state = world.initial()
    frames: List[List[List[int]]] = [world.render(state)]
    wins: List[bool] = [world.is_win(state)]
    taken: List[Optional[str]] = []

    for action in plan:
        if wins[-1] and stop_on_win:
            break
        state = world.step(state, action)
        frames.append(world.render(state))
        wins.append(world.is_win(state))
        taken.append(action)

    return {
        "level": level,
        "frames": frames,
        "wins": wins,
        "actions": list(taken),
        "actions_spent": len(taken),
        "win": wins[-1],
        "plan_length": len(plan),
    }


def write_execution(path: str, record: Dict[str, object]) -> str:
    """Persist an execution as an ordinary trace, so certify can replay it.

    Outgoing-keyed actions and a `win` flag per frame — the format A0's
    `certify/replay.py` reads.  Nothing about this file says which arm produced
    it, which is deliberate: the cheap layer must not be able to tell.
    """
    frames = record["frames"]
    actions = list(record["actions"]) + [None]
    wins = record["wins"]
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for t, frame in enumerate(frames):
            row = {
                "t": t,
                "frame": frame,
                "action": actions[t],
                "win": bool(wins[t]),
            }
            handle.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")
    return path


def run_and_record(level: str, plan: Sequence[str], path: str) -> Dict[str, object]:
    record = execute(level, plan)
    write_execution(path, record)
    record["trace"] = os.path.basename(path)
    return record
