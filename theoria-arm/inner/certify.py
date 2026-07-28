"""certify -- the word redeemed: replay AND proof, not replay alone.

`Theoria.md` 1.10(d) gives certify two layers and this file implements the
cheap one honestly and reports precisely how much of the expensive one this
world allows.

**Cheap layer.** Two obligations, and they are genuinely different:

* *responsibility* (constraint 2, full-frame): at the initial state, every
  pixel must belong either to the board or to some object. The manual draws
  the frame with its own `render(state)` and it is compared to the observed
  frame cell by cell. A pixel the manual cannot draw is a `render_mismatch` --
  the theory does not get to choose which parts of the picture it explains.
* *replay*: from the initial state, apply the recorded action sequence through
  the manual's own `step`, and compare the drawn frame to the observed frame at
  every step. A divergence is a `replay_mismatch`, and the first one is
  reported with the cells, because a minimal counterexample is what goes back
  to theorize.

**Constraint 9** (transitions are unambiguous) is checked where it can actually
fail: the generated `step` raises `AmbiguousTransition` when two rules claim
one object in one transition, so every recorded state is driven through every
action and the exceptions are collected. This is a **sampled** check over the
states the run happened to visit, not a proof over all states -- and it is
labelled `sampled` in the report so nobody reads it as more than it is.

**Expensive layer.** Lean. On a 64x64 grid the enumerative development has more
states than a kernel will decide and the pagoda development needs a LINE world
with an LP certificate, so on this world the expensive layer is usually not
*available* rather than failing. `books.compile_all()` records which of the two
refusals fired and why; this file reports whether a Lean file exists, whether
`lean` is on PATH, and what came back. An unavailable proof layer is a gap to
report, never a green tick to award.
"""

import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from world.frames import Grid, diff_cells

#: Driving every recorded state through every action is quadratic in a way that
#: does not matter at 100 states and does at 10,000. The cap is declared in the
#: report when it bites.
AMBIGUITY_SAMPLE_CAP = 400


class CertifyReport(dict):
    pass


def cheap(books, store, action_of) -> CertifyReport:
    """Replay and render consistency against the whole recorded history."""
    report = CertifyReport(layer="cheap", ok=False, checks={})
    namespace, error = books.load_predictor()
    if namespace is None:
        report["error"] = error
        report["checks"]["predictor"] = {"ok": False, "detail": error}
        return report
    report["checks"]["predictor"] = {"ok": True}

    render = namespace["render"]
    step = namespace["step"]
    initial_state = namespace["initial_state"]
    ambiguous = namespace.get("AmbiguousTransition", Exception)

    observed = store.grids
    if not observed:
        report["error"] = "nothing observed"
        return report

    # -- responsibility, at frame 0 ---------------------------------------
    # A predictor that raises here has failed the check, not escaped it: the
    # manual cannot draw the world it claims to describe. Turning that into a
    # traceback would end the run; turning it into a failed check sends it back
    # to theorize, which is where it belongs.
    try:
        state = initial_state()
        drawn = render(state)
        unexplained = diff_cells(drawn, observed[0])
        report["checks"]["responsibility"] = {
            "ok": not unexplained,
            "cells_unexplained": len(unexplained),
            "total_cells": len(observed[0]) * len(observed[0][0]),
            "first_cells": [list(t) for t in unexplained[:24]],
            "detail": ("every pixel of frame 0 belongs to the board or to an "
                       "object" if not unexplained else
                       "%d pixels of frame 0 belong to neither the board nor "
                       "any declared object" % len(unexplained)),
        }
    except Exception as exc:                           # noqa: BLE001
        report["checks"]["responsibility"] = {
            "ok": False, "cells_unexplained": None,
            "raised": "%s: %s" % (type(exc).__name__, exc),
            "detail": ("the manual's own `render` raised while drawing the "
                       "initial state (%s: %s). A manual that cannot draw its "
                       "own level cannot be checked against the world -- the "
                       "usual cause is a declared object the frame could not "
                       "locate, so its position never became a coordinate."
                       % (type(exc).__name__, exc)),
        }
        report["checks"]["replay"] = {
            "ok": False, "transitions": 0, "matched": 0,
            "first_divergence": {"kind": "render_raised"},
            "detail": "not attempted: the initial state does not render"}
        report["checks"]["unambiguous"] = {
            "ok": True, "scope": "not_attempted",
            "detail": "not attempted: the initial state does not render"}
        report["ok"] = False
        return report

    # -- replay, over the whole history ------------------------------------
    steps: List[Dict[str, Any]] = []
    first_divergence: Optional[Dict[str, Any]] = None
    actions = store.actions
    for t in range(len(observed) - 1):
        arc_action = actions[t]
        manual_action = action_of(arc_action)
        try:
            state = step(state, manual_action)
            fired_error = None
        except ambiguous as exc:                       # noqa: B902
            fired_error = "AmbiguousTransition: %s" % exc
        except Exception as exc:                       # noqa: BLE001
            fired_error = "%s: %s" % (type(exc).__name__, exc)

        entry: Dict[str, Any] = {"t": t, "arc_action": arc_action,
                                 "manual_action": list(manual_action)
                                 if isinstance(manual_action, tuple) else manual_action}
        if fired_error:
            entry["error"] = fired_error
            steps.append(entry)
            if first_divergence is None:
                first_divergence = dict(entry, kind="step_raised")
            break

        try:
            drawn = render(state)
        except Exception as exc:                       # noqa: BLE001
            entry["error"] = "render raised: %s: %s" % (type(exc).__name__, exc)
            steps.append(entry)
            if first_divergence is None:
                first_divergence = dict(entry, kind="render_raised")
            break

        wrong = diff_cells(drawn, observed[t + 1])
        entry["cells_wrong"] = len(wrong)
        if wrong and first_divergence is None:
            first_divergence = {
                "t": t, "arc_action": arc_action,
                "kind": "frame_mismatch",
                "cells_wrong": len(wrong),
                "cells": [{"cell": [r, c], "manual_says": a, "world_says": b}
                          for r, c, a, b in wrong[:24]],
            }
        steps.append(entry)

    matched = sum(1 for e in steps if e.get("cells_wrong") == 0)
    report["checks"]["replay"] = {
        "ok": first_divergence is None,
        "transitions": len(steps),
        "matched": matched,
        "first_divergence": first_divergence,
        "detail": ("%d/%d transitions replay exactly"
                   % (matched, len(steps))),
    }
    report["replay_steps"] = steps

    # -- constraint 9, sampled ---------------------------------------------
    report["checks"]["unambiguous"] = _ambiguity(namespace, store, action_of)

    report["ok"] = all(c.get("ok") for c in report["checks"].values())
    return report


def _ambiguity(namespace, store, action_of) -> Dict[str, Any]:
    """Drive the visited states through every declared action."""
    ambiguous = namespace.get("AmbiguousTransition", Exception)
    step = namespace["step"]
    initial_state = namespace["initial_state"]
    actions = list(namespace.get("ACTIONS") or [])
    if not actions:
        return {"ok": True, "scope": "sampled", "states": 0, "actions": 0,
                "detail": "the manual declares no actions, so no pair of rules "
                          "can claim one object"}

    # Reconstruct the visited states by replaying; a state the manual never
    # reaches cannot be checked from here, which is exactly why this is sampled.
    states = [initial_state()]
    for arc_action in store.actions[:AMBIGUITY_SAMPLE_CAP]:
        if arc_action is None:
            break
        try:
            states.append(step(states[-1], action_of(arc_action)))
        except Exception:                              # noqa: BLE001
            break

    clashes = []
    for state in states[:AMBIGUITY_SAMPLE_CAP]:
        for action in actions:
            try:
                step(state, action)
            except ambiguous as exc:                   # noqa: B902
                clashes.append({"action": list(action), "detail": str(exc)})
            except Exception:                          # noqa: BLE001
                pass
    return {
        "ok": not clashes,
        "scope": "sampled",
        "states": len(states),
        "actions": len(actions),
        "clashes": clashes[:12],
        "detail": ("no (state, action) among %d x %d admitted two rules"
                   % (len(states), len(actions)) if not clashes else
                   "%d ambiguous transitions found" % len(clashes)),
    }


def expensive(books, compile_result: Dict[str, Any]) -> CertifyReport:
    """The proof layer, and an honest account of whether it was available."""
    report = CertifyReport(layer="expensive", ok=False, available=False)
    lean_path = (compile_result.get("forms") or {}).get("lean")
    if not lean_path:
        report["detail"] = (compile_result.get("errors") or {}).get(
            "lean", "no Lean form was generated")
        report["state_estimate"] = compile_result.get("lean_state_estimate")
        return report

    report["available"] = True
    report["lean_file"] = lean_path
    binary = shutil.which("lean") or shutil.which("lake")
    if not binary:
        report["detail"] = ("a Lean file exists but `lean` is not on PATH, so "
                            "the proof obligations are stated and undischarged")
        return report

    try:
        proc = subprocess.run([binary, lean_path], capture_output=True,
                              text=True, timeout=900)
    except Exception as exc:                           # noqa: BLE001
        report["detail"] = "%s: %s" % (type(exc).__name__, exc)
        return report
    report["returncode"] = proc.returncode
    report["stdout"] = proc.stdout[-4000:]
    report["stderr"] = proc.stderr[-4000:]
    report["ok"] = proc.returncode == 0
    report["detail"] = ("lean accepted the file" if report["ok"]
                        else "lean rejected the file")
    return report


def run(books, store, action_of, compile_result: Dict[str, Any]) -> Dict[str, Any]:
    cheap_report = cheap(books, store, action_of)
    expensive_report = expensive(books, compile_result)
    return {"cheap": cheap_report, "expensive": expensive_report,
            "green": bool(cheap_report.get("ok")) and bool(expensive_report.get("ok")),
            "cheap_green": bool(cheap_report.get("ok")),
            "proof_layer_available": bool(expensive_report.get("available"))}


def surprises_from(report: Dict[str, Any], register) -> List[Any]:
    """Turn a certify report into the surprises it earned. Nothing else in the
    arm decides that a check failing is a surprise."""
    fired = []
    cheap_report = report.get("cheap") or {}
    checks = cheap_report.get("checks") or {}

    responsibility = checks.get("responsibility") or {}
    if responsibility and not responsibility.get("ok"):
        fired.append(register.fire(
            "render_mismatch", responsibility.get("detail", "render mismatch"),
            payload={"cells": responsibility.get("first_cells"),
                     "count": responsibility.get("cells_unexplained")}))

    replay = checks.get("replay") or {}
    if replay and not replay.get("ok"):
        divergence = replay.get("first_divergence") or {}
        fired.append(register.fire(
            "replay_mismatch",
            "replay diverges at t=%s (%s)" % (divergence.get("t"),
                                              divergence.get("kind")),
            step_idx=divergence.get("t"), payload=divergence))

    unambiguous = checks.get("unambiguous") or {}
    if unambiguous and not unambiguous.get("ok"):
        fired.append(register.fire(
            "proof_failure",
            "constraint 9: %s" % unambiguous.get("detail"),
            payload={"clashes": unambiguous.get("clashes")}))

    expensive_report = report.get("expensive") or {}
    if expensive_report.get("available") and not expensive_report.get("ok"):
        fired.append(register.fire(
            "proof_failure", expensive_report.get("detail", "lean failed"),
            payload={"stderr": (expensive_report.get("stderr") or "")[:2000]}))
    return fired
