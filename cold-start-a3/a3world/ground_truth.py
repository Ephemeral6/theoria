"""M1 — the traces, and the referee's copy of the truth.

Everything the pipeline is ever allowed to see is written here, as frames.  The
referee's own knowledge — the transition function, the reachable sets, the
shortest solutions — is written to `ground_truth.json` and
`a3world/GROUND_TRUTH.md` for scoring, and `THEORIZE_LOG.md` records when it
was first read.

The trace format is A0's and A2's, unchanged, because A0's `certify/replay.py`
and `compile/problem.py` both read it and a fourth spelling of the same four
keys would be a way to lose:

    {"t": int, "frame": [[int]], "action": str|null, "win": bool}

`action[t]` is the action that *produced* frame `t`; `action[0]` is null.
Written with `sort_keys=True`, `separators=(",", ":")` and LF, so the files are
byte-comparable across runs and across boxes.

Six traces, and which arm is allowed which is the whole experimental design:

| file | level | who may read it |
|---|---|---|
| `l1_sweep.jsonl` | L1 | the L1 cold start — its entire evidence |
| `l1_solved.jsonl` | L1 | the L1 commit step, after a plan exists |
| `l2_sweep.jsonl` | L2 | **the from-scratch control arm only** |
| `l2_solved.jsonl` | L2 | the control arm's commit step |
| `l2_frame0.json` | L2 | **the transfer arm — one frame, and nothing else** |
| `l2neg_frame0.json` / `l2rew_frame0.json` | negative controls | ditto |

The transfer arm gets a *frame*, not a trace, and that is enforced by there
being no L2 trace on its input list rather than by a rule it is asked to
follow.  `tests/test_sealing.py` checks that `a3pipeline.transfer` imports no
world module and opens no `*_sweep.jsonl`.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a3world.a3_world import (  # noqa: E402
    ACTIONS, L1, L2, L2_ONEWAY, L2_REWIRED, LevelSpec, A3World, State,
)
from a3world.explorer import (  # noqa: E402
    coverage_report, first_frame, solved_episode, sweep,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")


# ------------------------------------------------------------------- traces

def write_trace(path: str, world: A3World, states: Sequence[State],
                actions: Sequence[Optional[str]]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for t, state in enumerate(states):
            row = {
                "t": t,
                "frame": world.render(state),
                "action": actions[t],
                "win": world.is_win(state),
            }
            handle.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")


def read_trace(path: str):
    frames, actions, wins = [], [], []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            frames.append(row["frame"])
            actions.append(row["action"])
            wins.append(row["win"])
    return frames, actions, wins


def write_frame(path: str, frame: List[List[int]]) -> None:
    """One frame, as its own file — the transfer arm's whole observation."""
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"t": 0, "frame": frame},
                                sort_keys=True, indent=2) + "\n")


def read_frame(path: str) -> List[List[int]]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)["frame"]


# ---------------------------------------------------------------- the truth

GROUND_RULES = [
    {
        "name": "push",
        "when": "the target cell is floor, or the Door cell while the Door is absent",
        "then": "the Cart moves one cell in the action's direction",
    },
    {
        "name": "blocked",
        "when": "the target cell is a wall, the grid edge, or the Door while present",
        "then": "nothing changes",
    },
    {
        "name": "toggle",
        "when": "the target cell is the Switch",
        "then": "the Switch flips 7<->8 AND the Door appears/vanishes to match, "
                "in the same transition; the Cart does not move",
    },
    {
        "name": "teleport_a",
        "when": "the target cell is portal-A (colour 3)",
        "then": "the Cart is placed on portal-B",
    },
    {
        "name": "teleport_b",
        "when": "the target cell is portal-B (colour 4)",
        "then": "the Cart is placed on portal-A "
                "(deleted in a3-l2-oneway; rewired in a3-l2-rewired)",
    },
    {
        "name": "win",
        "when": "the Cart is on the level's goal cell",
        "then": "the frame is flagged as a win; the goal cell is NOT rendered",
    },
]


def truth_for(spec: LevelSpec) -> Dict[str, object]:
    world = A3World(spec)
    plan = world.solve()
    return {
        "level": spec.name,
        "cart_start": list(spec.cart_start),
        "switch_cell": list(spec.switch_cell),
        "door_cell": list(spec.door_cell),
        "portal_a": list(spec.portal_a),
        "portal_b": list(spec.portal_b),
        "exit_a": list(spec.exit_a),
        "exit_b": list(spec.exit_b),
        "goal_cell": list(spec.goal_cell),
        "portal_one_way": spec.portal_one_way,
        "rewired_exit_b": (list(spec.rewired_exit_b)
                           if spec.rewired_exit_b else None),
        "reachable_states": len(world.reachable()),
        "shortest_solution": plan,
        "shortest_solution_length": len(plan) if plan is not None else None,
        "solvable": plan is not None,
        "guard_contexts": world.guard_contexts(),
    }


def build(levels: Sequence[LevelSpec] = (L1, L2)) -> Dict[str, object]:
    """Write every trace and the referee's copy.  Deterministic, no clock."""
    os.makedirs(ARTIFACTS, exist_ok=True)
    report: Dict[str, object] = {"rules": GROUND_RULES, "levels": {}}

    tag = {"a3-l1": "l1", "a3-l2": "l2"}
    for spec in levels:
        world = A3World(spec)
        short = tag[spec.name]

        states, actions = sweep(world)
        write_trace(os.path.join(ARTIFACTS, "%s_sweep.jsonl" % short),
                    world, states, actions)

        won_states, won_actions = solved_episode(world)
        write_trace(os.path.join(ARTIFACTS, "%s_solved.jsonl" % short),
                    world, won_states, won_actions)

        write_frame(os.path.join(ARTIFACTS, "%s_frame0.json" % short),
                    first_frame(spec))

        report["levels"][spec.name] = {
            "truth": truth_for(spec),
            "coverage": coverage_report(world, states, actions),
        }

    # The negative controls hand over a first frame and nothing else.  Their
    # frames are *identical* to L2's by construction — the edit is in the
    # transition function, not in the pixels — and that is the point: no
    # amount of looking at the board can reveal it.
    for spec, short in ((L2_ONEWAY, "l2neg"), (L2_REWIRED, "l2rew")):
        write_frame(os.path.join(ARTIFACTS, "%s_frame0.json" % short),
                    first_frame(spec))
        report["levels"][spec.name] = {"truth": truth_for(spec)}

    out = os.path.join(ARTIFACTS, "ground_truth.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    report = build()
    for name, entry in sorted(report["levels"].items()):
        truth = entry["truth"]
        cov = entry.get("coverage")
        print("%-14s states=%-4s solution=%-5s %s" % (
            name, truth["reachable_states"], truth["shortest_solution_length"],
            ("sweep %d frames, coverage %.3f"
             % (cov["frames"], cov["coverage"])) if cov else "(frame 0 only)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
