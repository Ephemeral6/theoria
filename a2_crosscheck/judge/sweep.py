"""Compare predictors against the world, and against each other, state by state.

One sweep answers all of the questions the experiment asks:

* **held-out accuracy** -- predictor vs. truth over states nobody visited;
* **divergence** -- predictor vs. predictor, on the same world, so that two
  independently written theories can be made to disagree in public;
* **the joint blind spot** -- the cells where *every* predictor is wrong. Those
  are the ones that are not about anyone's implementation.

Two state sets are swept and both are reported, never merged. `representable`
is every state the level's own state type admits; `reachable` is the subset the
level actually reaches from its initial configuration. A manual that is perfect
on the second and wrong on the first is not a manual with a bug in it -- it is a
manual that solved the *problem* and not the *domain*, which is a different
finding with a different remedy, and averaging the two would hide which happened.
"""

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from a2_crosscheck.judge import truth

Frame = List[List[int]]
Predictor = Callable[[str, Frame, str], Frame]

REFUSED = "<refused>"


def _key(frame: Frame):
    return tuple(tuple(int(v) for v in row) for row in frame)


def _call(predictor: Predictor, level_id: str, frame: Frame,
          action: str) -> Tuple[Optional[Frame], Optional[str]]:
    try:
        return predictor(level_id, frame, action), None
    except Exception as exc:
        return None, "%s: %s" % (type(exc).__name__, str(exc)[:160])


def sweep_level(world_id: str, level_id: str,
                predictors: Dict[str, Predictor],
                scope: str = "representable",
                max_records: int = 60) -> Dict[str, Any]:
    """Every (state, action) of one level, through every predictor."""
    frames = (truth.representable_frames(world_id, level_id)
              if scope == "representable"
              else truth.reachable_frames(world_id, level_id))
    actions = truth.actions_of(world_id)
    names = sorted(predictors)

    correct = {n: 0 for n in names}
    refused = {n: 0 for n in names}
    wrong = {n: 0 for n in names}
    cases = 0
    disagreements: List[Dict[str, Any]] = []
    joint_errors: List[Dict[str, Any]] = []
    n_disagreements = 0
    n_joint_errors = 0

    for frame in frames:
        for action in actions:
            cases += 1
            actual = truth.truth_step_frame(world_id, level_id, frame, action)
            outcomes: Dict[str, Any] = {}
            for name in names:
                predicted, error = _call(predictors[name], level_id, frame, action)
                if error is not None:
                    refused[name] += 1
                    outcomes[name] = REFUSED
                    continue
                outcomes[name] = _key(predicted)
                if outcomes[name] == _key(actual):
                    correct[name] += 1
                else:
                    wrong[name] += 1

            distinct = {v for v in outcomes.values()}
            if len(distinct) > 1:
                n_disagreements += 1
                if len(disagreements) < max_records:
                    disagreements.append(
                        _record(world_id, level_id, frame, action, actual,
                                outcomes, names))
            elif distinct and _key(actual) not in distinct:
                # every predictor agreed, and every predictor was wrong
                n_joint_errors += 1
                if len(joint_errors) < max_records:
                    joint_errors.append(
                        _record(world_id, level_id, frame, action, actual,
                                outcomes, names))

    return {
        "world": world_id,
        "level": level_id,
        "scope": scope,
        "states": len(frames),
        "cases": cases,
        "per_predictor": {
            name: {
                "correct": correct[name],
                "wrong": wrong[name],
                "refused": refused[name],
                "accuracy": round(correct[name] / cases, 6) if cases else None,
            }
            for name in names
        },
        "n_disagreements": n_disagreements,
        "n_joint_errors": n_joint_errors,
        "disagreements": disagreements,
        "joint_errors": joint_errors,
    }


def _record(world_id: str, level_id: str, frame: Frame, action: str,
            actual: Frame, outcomes: Dict[str, Any],
            names: Sequence[str]) -> Dict[str, Any]:
    """One divergence, in a form a human can adjudicate without rerunning it."""
    return {
        "level": level_id,
        "action": action,
        "state": _describe(world_id, level_id, frame),
        "truth": _describe(world_id, level_id, actual),
        "predicted": {
            name: (REFUSED if outcomes[name] == REFUSED
                   else _describe(world_id, level_id,
                                  [list(r) for r in outcomes[name]]))
            for name in names
        },
        "agrees_with_truth": [
            name for name in names
            if outcomes[name] != REFUSED and outcomes[name] == _key(actual)
        ],
    }


def _describe(world_id: str, level_id: str, frame: Frame) -> str:
    """A one-line reading of a frame, in referee vocabulary."""
    if world_id == "S":
        player = box = None
        for r, row in enumerate(frame):
            for c, v in enumerate(row):
                if v == 2:
                    player = (r, c)
                elif v == 4:
                    box = (r, c)
        return "player=%s box=%s" % (player, box)
    cart = None
    door_open = True
    button = None
    for r, row in enumerate(frame):
        for c, v in enumerate(row):
            if v == 6:
                cart = (r, c)
            elif v == 5:
                door_open = False
            elif v in (7, 8):
                button = "pressed" if v == 8 else "up"
    return "cart=%s door=%s button=%s" % (
        cart, "open" if door_open else "closed", button)


def sweep_world(world_id: str, predictors: Dict[str, Predictor],
                levels: Optional[Sequence[str]] = None,
                max_records: int = 60) -> Dict[str, Any]:
    out: Dict[str, Any] = {"world": world_id, "levels": {}}
    for level_id in (levels or truth.LEVELS_OF[world_id]):
        out["levels"][level_id] = {
            scope: sweep_level(world_id, level_id, predictors, scope=scope,
                               max_records=max_records)
            for scope in ("representable", "reachable")
        }
    out["totals"] = _totals(out["levels"], sorted(predictors))
    return out


def _totals(levels: Dict[str, Any], names: Sequence[str]) -> Dict[str, Any]:
    totals: Dict[str, Any] = {}
    for scope in ("representable", "reachable"):
        cases = sum(l[scope]["cases"] for l in levels.values())
        totals[scope] = {
            "cases": cases,
            "per_predictor": {
                name: {
                    "correct": sum(l[scope]["per_predictor"][name]["correct"]
                                   for l in levels.values()),
                    "wrong": sum(l[scope]["per_predictor"][name]["wrong"]
                                 for l in levels.values()),
                    "refused": sum(l[scope]["per_predictor"][name]["refused"]
                                   for l in levels.values()),
                }
                for name in names
            },
            "n_disagreements": sum(l[scope]["n_disagreements"]
                                   for l in levels.values()),
            "n_joint_errors": sum(l[scope]["n_joint_errors"]
                                  for l in levels.values()),
        }
        for name in names:
            entry = totals[scope]["per_predictor"][name]
            entry["accuracy"] = round(entry["correct"] / cases, 6) if cases else None
    return totals
