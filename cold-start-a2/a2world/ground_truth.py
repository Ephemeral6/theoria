"""M1 — the two traces, and the referee's copy of the truth.

Three products, deliberately in one file so the split stays visible:

  * `raw_trace.jsonl` — the full sweep.  Every reachable (state, action) pair,
    the teleport included, ending on the goal.  This is what the pipeline
    induces the **complete** manual from.
  * `history_trace.jsonl` — the same trajectory cut at the teleport.  A play
    record that maps the left room exhaustively and stops at the Door's
    threshold.  This is the evidence the **holed** manual is certified against,
    and it is the A2 stand-in for DC22's 175 frames.
  * `ground_truth.json` / `a2world/GROUND_TRUTH.md` — the rules, the objects,
    the reachable sets with and without the teleport.  Scoring only.
    `THEORIZE_LOG.md` records when it was first read.

The cut is not a curation choice: `explorer.portal_transition` finds the single
non-adjacent Cart move by looking at the frames' geometry, and the history is
everything strictly before it.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a2world.a2_world import (  # noqa: E402
    ACTIONS, BASE, DELTA, HEIGHT, POCKET_CELL, WIDTH, A2World, State, WorldSpec,
    BUTTON_DOWN, BUTTON_UP, CART, DOOR_CLOSED, FLOOR, PORTAL, WALL,
)
from a2world.explorer import (  # noqa: E402
    coverage_report, explore, portal_transition, stratum,
)


def write_trace(path: str, world: A2World, states: Sequence[State],
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
        "when": "act=UP and the Cart is at (2,1), so the target is the Button, "
                "and the Button is unpressed",
        "then": "Button recolours 7 -> 8 AND the Door vanishes, in the same "
                "transition; the Cart does not move",
    },
    {
        "name": "teleport",
        "when": "act=DOWN and the target cell is the Portal entry (7,4) — which "
                "is only ever true from the Door cell (6,4), and only after the "
                "Door has opened",
        "then": "Cart moves to (7,6), inside the right room",
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
        "name": "pocket_unreachable",
        "statement": "(7,1) is floor walled on all four sides; no state with the "
                     "Cart there is reachable, with or without the teleport. "
                     "TRUE of the world — this is what the repaired manual proves.",
    },
    {
        "name": "right_room_locked_WITHOUT_teleport",
        "statement": "delete the teleport and the right room is unreachable, "
                     "because column c5 is solid wall from r1 to r7. "
                     "FALSE of the world — this is the exhibit.",
    },
]


def ground_truth_dict(spec: WorldSpec = BASE) -> Dict[str, object]:
    world = A2World(spec)
    full = world.reachable()
    holed = world.reachable(holed=True)
    solution = world.solve()
    return {
        "spec": {
            "name": spec.name,
            "button_cell": list(spec.button_cell) if spec.button_cell else None,
            "door_cell": list(spec.door_cell) if spec.door_cell else None,
            "portal_cell": list(spec.portal_cell) if spec.portal_cell else None,
            "portal_dest": list(spec.portal_dest),
            "cart_start": list(spec.cart_start),
            "goal_cell": list(spec.goal_cell),
            "pocket_cell": list(POCKET_CELL),
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
        "reachable_states": len(full),
        "reachable_states_without_teleport": len(holed),
        "goal_reachable": solution is not None,
        "shortest_solution": solution,
        "shortest_solution_length": len(solution) if solution is not None else None,
        "goal_reachable_without_teleport": world.solve(holed=True) is not None,
        "pocket_ever_occupied": any(s.cart == POCKET_CELL for s in full),
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


MD_HEADER = """# GROUND_TRUTH — the referee's copy (A2)

**Do not open this file while theorizing.** It exists so that the loop can be
scored against the truth, and for no other purpose. `THEORIZE_LOG.md` records the
point at which it was first read.

Generated by `a2world/ground_truth.py`; the JSON form is
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
    lines.append("## Reachability, with and without the teleport")
    lines.append("")
    lines.append("| | states | goal reachable |")
    lines.append("|---|---|---|")
    lines.append("| the world | %d | %s |" % (truth["reachable_states"],
                                              truth["goal_reachable"]))
    lines.append("| the world minus the teleport rule | %d | %s |"
                 % (truth["reachable_states_without_teleport"],
                    truth["goal_reachable_without_teleport"]))
    lines.append("")
    lines.append("Shortest solution: **%d** actions, `%s`."
                 % (truth["shortest_solution_length"],
                    " ".join(truth["shortest_solution"] or [])))
    lines.append("")
    with open(md_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
    return truth


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    artifacts = os.path.join(root, "artifacts")
    os.makedirs(artifacts, exist_ok=True)

    world = A2World(BASE)
    states, actions = explore(BASE)
    cut = portal_transition(BASE, states, actions)

    write_trace(os.path.join(artifacts, "raw_trace.jsonl"), world, states, actions)

    history_states = list(states[:cut + 1])
    history_actions = list(actions[:cut]) + [None]
    write_trace(os.path.join(artifacts, "history_trace.jsonl"), world,
                history_states, history_actions)

    summary = {
        "portal_transition": cut,
        "raw_trace": coverage_report(BASE, states, actions),
        "history_trace": coverage_report(BASE, states, actions, upto=cut),
        "cut_rule": "history_trace = raw_trace[0 .. portal_transition]; the cut "
                    "index is the single non-adjacent Cart move, found from the "
                    "frames' geometry",
    }
    hist = summary["history_trace"]
    summary["history_omits_exactly_one_pair"] = (
        len(hist["uncovered_pairs"]) == 1
        and hist["uncovered_pairs"][0].endswith("act=DOWN")
    )
    summary["history_omitted_pairs"] = hist["uncovered_pairs"]

    for name in ("raw_trace", "history_trace"):
        print("[%s] %s" % (name, json.dumps(
            {k: summary[name][k] for k in
             ("frames", "transitions", "coverage", "portal_transitions",
              "win_frames")}, sort_keys=True)))
    print("[cut] portal_transition=%d  history omits %s"
          % (cut, summary["history_omitted_pairs"]))

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
