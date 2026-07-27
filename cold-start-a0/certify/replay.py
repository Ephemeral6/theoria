"""certify, cheap layer — full-history replay ∧ rendering consistency.

Constraint 2, in its upgraded form: *double reconciliation*. Two things are
checked at every frame and a failure of either is an anomaly:

1. **transition replay** — the manual's `step` reproduces the recorded action's
   successor, state for state, all the way through;
2. **rendering consistency, with full-frame responsibility** — the manual drawn
   back onto a grid equals the recorded frame *cell by cell*, and every pixel is
   owned by the board or by exactly one object. A pixel the manual does not
   explain is an anomaly: the theory does not get to pick its own exam.

A third check rides along because it is free here and expensive later:

3. **single successor** (constraint 9) — no two rules claim the same object in
   the same transition. `theory.py` raises `AmbiguousTransition` if they do.

The action vocabulary is an adjudication too, and it is written down rather than
assumed: the world emits `UP/DOWN/LEFT/RIGHT`, the manual speaks
`push(Cart, up)` and so on. That naming is THEORIZE_LOG's, not the world's.
"""

import importlib.util
import json
import os
import sys
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from world.ground_truth import read_trace  # noqa: E402

ACTION_NAMES = {
    "UP": ("push", "Cart", "up"),
    "DOWN": ("push", "Cart", "down"),
    "LEFT": ("push", "Cart", "left"),
    "RIGHT": ("push", "Cart", "right"),
}


def load_theory(path: str):
    spec = importlib.util.spec_from_file_location("a0_theory", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def certify(theory_py: str, trace_path: str) -> Dict[str, object]:
    theory = load_theory(theory_py)
    frames, actions, wins = read_trace(trace_path)

    anomalies: List[Dict[str, object]] = []
    state = theory.initial_state()
    unexplained_pixels = 0
    checked_pixels = 0

    for t, frame in enumerate(frames):
        rendered = theory.render(state)
        owner, contested = theory.responsibility(state)

        # --- rendering consistency, cell by cell -------------------------
        for r in range(theory.GRID[0]):
            for c in range(theory.GRID[1]):
                checked_pixels += 1
                if rendered[r][c] != frame[r][c]:
                    if len(anomalies) < 40:
                        anomalies.append({
                            "kind": "render_mismatch", "t": t, "cell": [r, c],
                            "manual": rendered[r][c], "world": frame[r][c],
                        })
                    unexplained_pixels += 1

        # --- full-frame responsibility -----------------------------------
        for cell, first, second in contested:
            anomalies.append({"kind": "contested_pixel", "t": t,
                              "cell": list(cell), "objects": [first, second]})
        for r in range(theory.GRID[0]):
            for c in range(theory.GRID[1]):
                if owner[r][c] is None and theory.BOARD[r][c] != frame[r][c]:
                    if len(anomalies) < 40:
                        anomalies.append({
                            "kind": "unowned_pixel", "t": t, "cell": [r, c],
                            "world": frame[r][c], "board": theory.BOARD[r][c],
                        })

        # --- goal agreement ----------------------------------------------
        if theory.is_goal(state) != bool(wins[t]):
            anomalies.append({"kind": "goal_mismatch", "t": t,
                              "manual": theory.is_goal(state), "world": bool(wins[t])})

        if actions[t] is None:
            break
        try:
            state = theory.step(state, ACTION_NAMES[actions[t]])
        except theory.AmbiguousTransition as exc:
            anomalies.append({"kind": "ambiguous_transition", "t": t,
                              "detail": str(exc)})
            break

    return {
        "theory": os.path.relpath(theory_py),
        "trace": os.path.basename(trace_path),
        "frames": len(frames),
        "transitions": max(0, len(frames) - 1),
        "pixels_checked": checked_pixels,
        "pixels_unexplained": unexplained_pixels,
        "anomalies": anomalies,
        "anomaly_kinds": sorted({a["kind"] for a in anomalies}),
        "green": not anomalies,
    }


def contested_summary(report) -> str:
    if report["green"]:
        return "GREEN  %d frames, %d pixels, 0 anomalies" % (
            report["frames"], report["pixels_checked"])
    return "RED    %d anomalies (%s)" % (
        len(report["anomalies"]), ", ".join(report["anomaly_kinds"]))


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    theory_py = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        root, "theory", "generated", "theory.py")
    trace = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        root, "artifacts", "raw_trace.jsonl")
    report = certify(theory_py, trace)
    print(contested_summary(report))
    for anomaly in report["anomalies"][:12]:
        print("   ", json.dumps(anomaly, sort_keys=True))
    out = os.path.join(root, "artifacts",
                       "certify_cheap_%s.json" % os.path.basename(trace).split(".")[0])
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0 if report["green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
