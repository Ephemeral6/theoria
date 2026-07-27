"""The referee's copy of the truth, and the trace writer.

Two products, deliberately in the same file so the split is visible:

  * `write_trace` emits `artifacts/raw_trace.jsonl` -- frames, actions, win flag.
    That is *all* the discovery pipeline is ever allowed to read.
  * `write_ground_truth` emits `artifacts/ground_truth.json` and
    `world/GROUND_TRUTH.md` -- the rule set, the object masks, the invariant.
    Scoring only.  THEORIZE_LOG.md records that it was not opened until M6.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402
from world.a0_world import (  # noqa: E402
    ACTIONS, BASE, DELTA, HEIGHT, WIDTH, A0World, State, WorldSpec,
    BUTTON_DOWN, BUTTON_UP, CART, DOOR_CLOSED, FLOOR, PORTAL, WALL,
)
from world.explorer import coverage_report, explore  # noqa: E402


def write_trace(path: str, world: A0World, states: Sequence[State],
                actions: Sequence[Optional[str]]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for t, state in enumerate(states):
            row = {
                "t": t,
                "frame": world.render(state),
                "action": actions[t],
                "win": world.is_win(state),
            }
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


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


# ---------------------------------------------------------------- the truth

GROUND_RULES = [
    {
        "name": "push",
        "when": "act=D and the target cell is floor (or the opened Door cell)",
        "then": "Cart moves one cell in direction D",
    },
    {
        "name": "blocked",
        "when": "act=D and the target cell is a wall, the closed Door, or the Button",
        "then": "nothing moves",
    },
    {
        "name": "press",
        "when": "act=D and the target cell is the Button and the Button is unpressed",
        "then": "Button recolours 7 -> 8 AND the Door vanishes, in the same transition; "
                "the Cart does not move",
    },
    {
        "name": "door_open",
        "when": "(cascade of press, not an independent rule)",
        "then": "Door vanishes; the Door cell becomes passable forever after",
    },
    {
        "name": "teleport",
        "when": "act=D and the target cell is the Portal entry (7,3)",
        "then": "Cart moves to (1,1)",
    },
]

GROUND_INVARIANTS = [
    {
        "name": "cart_unique",
        "statement": "exactly one cell carries colour 6 at all times",
    },
    {
        "name": "button_latched",
        "statement": "once the Button is 8 it is never 7 again",
    },
    {
        "name": "right_room_locked (variant a0-no-button only)",
        "statement": "with no Button the Door never opens, so the Cart never occupies "
                     "a cell of the right room; the parity of the Cart's occupancy over "
                     "the right room is conserved at 0",
    },
]


def ground_truth_dict(spec: WorldSpec = BASE) -> Dict[str, object]:
    world = A0World(spec)
    reachable = world.reachable()
    return {
        "spec": {
            "name": spec.name,
            "button_cell": list(spec.button_cell) if spec.button_cell else None,
            "door_cell": list(spec.door_cell) if spec.door_cell else None,
            "portal_cell": list(spec.portal_cell) if spec.portal_cell else None,
            "portal_dest": list(spec.portal_dest),
            "cart_start": list(spec.cart_start),
            "goal_cell": list(spec.goal_cell),
        },
        "palette": {
            "floor": FLOOR, "wall": WALL, "portal": PORTAL,
            "door_closed": DOOR_CLOSED, "cart": CART,
            "button_unpressed": BUTTON_UP, "button_pressed": BUTTON_DOWN,
        },
        "grid": [HEIGHT, WIDTH],
        "actions": list(ACTIONS),
        "delta": {k: list(v) for k, v in DELTA.items()},
        "rules": GROUND_RULES,
        "invariants": GROUND_INVARIANTS,
        "reachable_states": len(reachable),
        "objects": {
            "Cart": {"shape": [1, 1], "colors": [CART]},
            "Button": {"shape": [1, 1], "colors": [BUTTON_UP, BUTTON_DOWN],
                       "cell": list(spec.button_cell) if spec.button_cell else None},
            "Door": {"shape": [1, 1], "colors": [DOOR_CLOSED],
                     "cell": list(spec.door_cell) if spec.door_cell else None,
                     "vanishes_when": "Button pressed"},
        },
        "board_cells": {
            "walls": sorted([list(c) for c in world.walls]),
            "portal_marker": list(spec.portal_cell) if spec.portal_cell else None,
        },
    }


MD_HEADER = """# GROUND_TRUTH — the referee's copy (A0)

**Do not open this file while theorizing.** It exists so that M6 can score the
induced theory against the truth, and for no other purpose. `THEORIZE_LOG.md`
records the point at which it was first read.

Generated by `world/ground_truth.py`; the JSON form is
`artifacts/ground_truth.json`.
"""


def write_ground_truth(json_path: str, md_path: str, spec: WorldSpec = BASE) -> Dict:
    truth = ground_truth_dict(spec)
    with open(json_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(truth, indent=2, sort_keys=True) + "\n")

    lines = [MD_HEADER, ""]
    lines.append("## Rules")
    lines.append("")
    lines.append("| name | when | then |")
    lines.append("|---|---|---|")
    for rule in truth["rules"]:
        lines.append("| `%s` | %s | %s |" % (rule["name"], rule["when"], rule["then"]))
    lines.append("")
    lines.append("## Invariants")
    lines.append("")
    for inv in truth["invariants"]:
        lines.append("* **%s** — %s" % (inv["name"], inv["statement"]))
    lines.append("")
    lines.append("## Objects")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(truth["objects"], indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("Reachable states in `%s`: **%d**." % (spec.name, truth["reachable_states"]))
    lines.append("")
    with open(md_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
    return truth


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    artifacts = os.path.join(root, "artifacts")
    os.makedirs(artifacts, exist_ok=True)

    summary = {}
    for spec, trace_name in ((BASE, "raw_trace.jsonl"),
                             (__import__("world.a0_world", fromlist=["NO_BUTTON"]).NO_BUTTON,
                              "raw_trace_no_button.jsonl")):
        world = A0World(spec)
        states, actions = explore(spec)
        write_trace(os.path.join(artifacts, trace_name), world, states, actions)
        report = coverage_report(spec, states, actions)
        summary[spec.name] = report
        print("[%s] %s" % (spec.name, json.dumps(report, sort_keys=True)))

    write_ground_truth(
        os.path.join(artifacts, "ground_truth.json"),
        os.path.join(here, "GROUND_TRUTH.md"),
        BASE,
    )
    with open(os.path.join(artifacts, "trace_summary.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
