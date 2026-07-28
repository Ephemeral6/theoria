"""commit -- run the script, mark every frame against the prediction.

`Theoria.md` 1.10(d): the plan is executed as a whole script, every frame is
machine-marked against the manual's prediction, and a mismatch **abandons the
plan**, records the surprise and returns to theorize. Constraint 3, inherited
from Schema unchanged: one channel for action, and a mispredicted step ends the
plan rather than being absorbed.

Zero model calls. Constraint 8's "execute, verify and engines are call-free"
is a property of this file's imports: there is no route from here to a model.

The prediction is written **before** the action is sent, and it is the manual's
own `render(step(state, action))` -- the same predictor certify replays and
plan searched. There is deliberately no second, looser predictor for execution:
a plan that only works because execution forgave it would teach the manual
nothing.
"""

from typing import Any, Callable, Dict, List, Optional, Sequence

from world.frames import Step, grid_hash


class CommitReport(dict):
    pass


def execute(namespace: Dict[str, Any], plan_actions: Sequence[Sequence[Any]],
            *, send, store, action_to_arc: Callable[[Any], int],
            step_start: int = 0) -> CommitReport:
    """Run the script. `send(arc_action_id)` performs one action and returns
    `(status, envelope, frames)`; everything else here is comparison."""
    render = namespace["render"]
    step = namespace["step"]
    initial_state = namespace["initial_state"]

    report = CommitReport(planned=len(plan_actions), executed=0, matched=0,
                          steps=[], abandoned_at=None, outcome="completed")

    # Roll the manual forward over the history so the predictor starts where
    # the world is, not where the level started.
    state = initial_state()
    for past in store.actions:
        if past is None:
            break
        try:
            state = step(state, action_to_manual(past))
        except Exception:                              # noqa: BLE001
            break

    for i, action in enumerate(plan_actions):
        action = tuple(action)
        try:
            predicted_state = step(state, action)
            predicted = render(predicted_state)
        except Exception as exc:                       # noqa: BLE001
            report["steps"].append({"i": i, "action": list(action),
                                    "error": "%s: %s" % (type(exc).__name__, exc)})
            report["abandoned_at"] = i
            report["outcome"] = "predictor_raised"
            break

        arc_action = action_to_arc(action)
        status, envelope, frames = send(arc_action)
        observed = frames[-1] if frames else None

        entry = {"i": i, "action": list(action), "arc_action": arc_action,
                 "status": status, "n_frames": len(frames),
                 "predicted_hash": grid_hash(predicted),
                 "observed_hash": grid_hash(observed)}
        report["executed"] += 1

        if status != 200 or observed is None:
            entry["mismatch"] = "the command did not return a frame"
            report["steps"].append(entry)
            report["abandoned_at"] = i
            report["outcome"] = "command_failed"
            break

        if grid_hash(predicted) == grid_hash(observed):
            entry["match"] = True
            report["matched"] += 1
            state = predicted_state
            report["steps"].append(entry)
            continue

        from world.frames import diff_cells             # noqa: PLC0415
        wrong = diff_cells(predicted, observed)
        entry["match"] = False
        entry["cells_wrong"] = len(wrong)
        entry["cells"] = [{"cell": [r, c], "manual_says": a, "world_says": b}
                          for r, c, a, b in wrong[:24]]
        report["steps"].append(entry)
        report["abandoned_at"] = i
        report["outcome"] = "execution_mismatch"
        break

    return report


def action_to_manual(arc_action: str):
    """`ACTION3` -> `('key', 3)`. The one mapping, in one place."""
    if arc_action is None:
        return None
    if arc_action == "RESET":
        return ("key", 0)
    return ("key", int(str(arc_action).replace("ACTION", "")))


def action_to_arc(manual_action) -> int:
    name, *args = tuple(manual_action)
    if name != "key" or not args:
        raise ValueError(
            "the manual's action %r is not in this world's action vocabulary. "
            "The grammar card says actions are written `act=key(<n>)` for "
            "ARC's ACTION<n>; anything else has no channel to the environment."
            % (manual_action,))
    return int(args[0])


def surprises_from(report: Dict[str, Any], register) -> List[Any]:
    fired = []
    if report.get("outcome") == "execution_mismatch":
        i = report.get("abandoned_at")
        last = report["steps"][-1] if report.get("steps") else {}
        fired.append(register.fire(
            "execution_mismatch",
            "the plan's step %s was mispredicted: %s cells differ between what "
            "the manual drew and what the world returned"
            % (i, last.get("cells_wrong")),
            step_idx=i, payload=last))
    elif report.get("outcome") == "predictor_raised":
        last = report["steps"][-1] if report.get("steps") else {}
        fired.append(register.fire(
            "replay_mismatch",
            "the manual's own predictor raised while executing the plan it "
            "produced: %s" % last.get("error"),
            step_idx=report.get("abandoned_at"), payload=last))
    return fired
