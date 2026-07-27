"""A0′: trace writer and the referee's copy of the truth.

Same split as A0. `prime/artifacts/raw_trace.jsonl` is everything the discovery
pipeline may read; `GROUND_TRUTH.md` is scoring only, and the first read of it is
stamped in `prime/THEORIZE_LOG.md`.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

import _bootstrap  # noqa: F401,E402

from prime.world import a0p_world as W  # noqa: E402
from prime.world.explorer import coverage_report, explore  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACTS = os.path.join(ROOT, "prime", "artifacts")


def write_trace(path: str, world: W.A0PWorld, states, actions) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for t, state in enumerate(states):
            row = {"t": t, "frame": world.render(state),
                   "action": actions[t], "win": world.is_win(state)}
            handle.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")


def append_frames(path: str, world: W.A0PWorld, states, actions,
                  tag: str) -> None:
    """Append probe frames to the trace, tagged so provenance survives.

    Theoria 1.10d: a probe runs through the same single channel and its result is
    recorded.  Keeping the frames in the same append-only file is what makes the
    revised manual's replay cover the probe as well.
    """
    start = sum(1 for _ in open(path, encoding="utf-8"))
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        for i, state in enumerate(states):
            row = {"t": start + i, "frame": world.render(state),
                   "action": actions[i], "win": world.is_win(state),
                   "probe": tag}
            handle.write(json.dumps(row, sort_keys=True,
                                    separators=(",", ":")) + "\n")


GROUND_RULES = [
    {"name": "push", "when": "act=D and the target cell is floor or the open Door",
     "then": "the Cart moves one cell in direction D"},
    {"name": "toggle", "when": "act=D and the target cell is the Switch",
     "then": "the Switch flips 7<->8 and the Door mirrors it (present iff 7); "
             "the Cart does not move.  Works from all four directions, both ways."},
    {"name": "teleport", "when": "act=D and the target cell is the Portal marker",
     "then": "the Cart moves to (1,1)"},
    {"name": "blocked", "when": "act=D and the target is a wall, the Crate, or the "
                                "closed Door",
     "then": "nothing happens"},
]

GROUND_INVARIANTS = [
    {"name": "cart_unique", "statement": "exactly one cell shows colour 6"},
    {"name": "door_mirrors_switch",
     "statement": "the Door is present if and only if the Switch shows 7"},
    {"name": "right_room_locked (a0p-no-switch only)",
     "statement": "with no Switch the Door never opens, so the Cart never "
                  "occupies a right-room cell"},
]


def ground_truth_dict(spec: W.WorldSpec) -> Dict[str, object]:
    world = W.A0PWorld(spec)
    return {
        "spec": {
            "name": spec.name,
            "switch_cell": list(spec.switch_cell) if spec.switch_cell else None,
            "door_cell": list(spec.door_cell) if spec.door_cell else None,
            "crate_cell": list(spec.crate_cell) if spec.crate_cell else None,
            "portal_cell": list(spec.portal_cell) if spec.portal_cell else None,
            "portal_dest": list(spec.portal_dest),
            "cart_start": list(spec.cart_start),
            "goal_cell": list(spec.goal_cell),
        },
        "palette": {"floor": W.FLOOR, "wall": W.WALL, "crate": W.CRATE,
                    "portal": W.PORTAL, "door_closed": W.DOOR_CLOSED,
                    "cart": W.CART, "switch_off": W.SWITCH_OFF,
                    "switch_on": W.SWITCH_ON},
        "grid": [W.HEIGHT, W.WIDTH],
        "actions": list(W.ACTIONS),
        "rules": GROUND_RULES,
        "invariants": GROUND_INVARIANTS,
        "reachable_states": len(world.reachable()),
    }


def main() -> int:
    os.makedirs(ARTIFACTS, exist_ok=True)
    summary = {}
    for spec, name in ((W.BASE, "raw_trace.jsonl"),
                       (W.NO_SWITCH, "raw_trace_no_switch.jsonl")):
        world = W.A0PWorld(spec)
        states, actions = explore(spec)
        write_trace(os.path.join(ARTIFACTS, name), world, states, actions)
        report = coverage_report(spec, states, actions)
        summary[spec.name] = report
        print("[%s] budget=%d coverage=%s never=%s"
              % (spec.name, report["budget"], report["coverage"],
                 json.dumps(report["mechanisms_never_witnessed"])))

    truth = {s.name: ground_truth_dict(s) for s in (W.BASE, W.NO_SWITCH)}
    with open(os.path.join(ARTIFACTS, "ground_truth.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(truth, indent=2, sort_keys=True) + "\n")
    with open(os.path.join(ARTIFACTS, "trace_summary.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    md = ["# GROUND_TRUTH — A0′ referee's copy", "",
          "**Do not open while theorizing.** Scoring only; the first read is "
          "stamped in `prime/THEORIZE_LOG.md`.", "",
          "## Rules", "", "| name | when | then |", "|---|---|---|"]
    for rule in GROUND_RULES:
        md.append("| `%s` | %s | %s |" % (rule["name"], rule["when"], rule["then"]))
    md += ["", "## Invariants", ""]
    for inv in GROUND_INVARIANTS:
        md.append("* **%s** — %s" % (inv["name"], inv["statement"]))
    md.append("")
    with open(os.path.join(ROOT, "prime", "world", "GROUND_TRUTH.md"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
