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

**A crash is not a finding (E14).** The constraint-9 sweep used to swallow
every non-`AmbiguousTransition` exception with a bare `pass`, then report
`ok: true` and "no (state, action) among N x M admitted two rules". Two things
were wrong with that sentence at once. `N x M` is the *nominal* product, not
the number of pairs actually adjudicated -- a pair whose `step` crashed was
counted into the claimed coverage and never judged -- and the generated `step`
is documented total, so a crash there is a defect rather than an inapplicable
action. The arithmetic therefore ran backwards: the more the predictor crashed,
the more pairs got skipped, the cleaner the certificate came out. The sweep now
counts crashes, reports `pairs_checked` alongside `pairs_nominal`, records
`AMBIGUITY_SAMPLE_CAP` positively, and refuses `ok: true` while the crash count
is non-zero.
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

#: Verbatim crash messages kept in the artifact. The count is never capped.
CRASH_SAMPLE_CAP = 8


class _NoAmbiguityClassDeclared(Exception):
    """Stand-in for a missing `AmbiguousTransition`, and it is never raised.

    E14 (adversarial review, correction 10). The default used to be `Exception`,
    which turns `except ambiguous` into `except Exception` and files **every**
    crash as a constraint-9 clash -- an assertion that two rules claimed one
    object, i.e. a finding about the world, manufactured out of a bug. It also
    left `pairs_checked` above `pairs_nominal` with a crash count of zero.
    A class nothing raises means a manual without a declared ambiguity type
    simply has no ambiguity to find, and its crashes stay crashes.
    """


class CertifyReport(dict):
    pass


class StepCrashLog:
    """Exceptions out of the generated `step`, counted, typed and located.

    Emitted whether or not it is empty, for the same reason `plan.py` does: a
    printed zero is evidence, an absent one is indistinguishable from a check
    that never looked.
    """

    def __init__(self, site: str) -> None:
        self.site = site
        self.count = 0
        self.by_type: Dict[str, int] = {}
        self.by_phase: Dict[str, int] = {}
        self.samples: List[Dict[str, Any]] = []

    def record(self, exc: BaseException, *, phase: str,
               detail: Optional[Dict[str, Any]] = None) -> None:
        self.count += 1
        kind = type(exc).__name__
        self.by_type[kind] = self.by_type.get(kind, 0) + 1
        self.by_phase[phase] = self.by_phase.get(phase, 0) + 1
        if len(self.samples) < CRASH_SAMPLE_CAP:
            entry = {"type": kind, "message": str(exc)[:400], "phase": phase}
            entry.update(detail or {})
            self.samples.append(entry)

    def as_json(self) -> Dict[str, Any]:
        return {
            "site": self.site,
            "count": self.count,
            "by_type": dict(sorted(self.by_type.items())),
            "by_phase": dict(sorted(self.by_phase.items())),
            "samples": self.samples,
            "sample_cap": CRASH_SAMPLE_CAP,
            "note": ("`step` is documented total and its only declared "
                     "exception, AmbiguousTransition, is a constraint-9 "
                     "violation which is counted as a clash rather than here. "
                     "Anything counted here is a bug in the compiled manual, "
                     "and each one removed a pair from adjudication while "
                     "leaving it inside the nominal coverage."),
        }


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
    ambiguous = namespace.get("AmbiguousTransition", _NoAmbiguityClassDeclared)

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
    ambiguous = namespace.get("AmbiguousTransition", _NoAmbiguityClassDeclared)
    step = namespace["step"]
    initial_state = namespace["initial_state"]
    actions = list(namespace.get("ACTIONS") or [])
    crashes = StepCrashLog("certify._ambiguity: step(state, action)")
    if not actions:
        return {"ok": True, "scope": "sampled", "states": 0, "actions": 0,
                "pairs_nominal": 0, "pairs_checked": 0,
                "sample_cap": AMBIGUITY_SAMPLE_CAP,
                "step_crashes": crashes.as_json(),
                "detail": "the manual declares no actions, so no pair of rules "
                          "can claim one object"}

    # Reconstruct the visited states by replaying; a state the manual never
    # reaches cannot be checked from here, which is exactly why this is sampled.
    states = [initial_state()]
    replay_truncated = False
    for i, arc_action in enumerate(store.actions[:AMBIGUITY_SAMPLE_CAP]):
        if arc_action is None:
            break
        try:
            states.append(step(states[-1], action_of(arc_action)))
        except Exception as exc:                       # noqa: BLE001
            # E14: was a bare `break`. It still breaks -- carrying on from a
            # state the manual could not produce would be worse -- but the
            # truncation is now on the record instead of shortening the sweep
            # in silence.
            crashes.record(exc, phase="reconstruct",
                           detail={"at_action_index": i,
                                   "arc_action": str(arc_action)})
            replay_truncated = True
            break

    swept = states[:AMBIGUITY_SAMPLE_CAP]
    clashes = []
    pairs_checked = 0
    for state in swept:
        for action in actions:
            try:
                step(state, action)
            except ambiguous as exc:                   # noqa: B902
                clashes.append({"action": list(action), "detail": str(exc)})
            except Exception as exc:                   # noqa: BLE001
                # E14: was a bare `pass`. The pair stayed inside the claimed
                # denominator and was never judged.
                crashes.record(exc, phase="sweep",
                               detail={"action": list(action)})
                continue
            pairs_checked += 1

    # The denominator is the number of states actually swept, not `len(states)`
    # -- the old detail line reported the latter, which could exceed the former
    # by one once the cap bit (initial state + 400 replayed).
    pairs_nominal = len(swept) * len(actions)
    out: Dict[str, Any] = {
        "scope": "sampled",
        "states": len(swept),
        "states_reconstructed": len(states),
        "actions": len(actions),
        "sample_cap": AMBIGUITY_SAMPLE_CAP,
        "cap_reached": len(states) > AMBIGUITY_SAMPLE_CAP,
        "replay_truncated_by_crash": replay_truncated,
        "pairs_nominal": pairs_nominal,
        "pairs_checked": pairs_checked + len(clashes),
        "clashes": clashes[:12],
        "n_clashes": len(clashes),
        "step_crashes": crashes.as_json(),
    }
    if crashes.count:
        out["ok"] = False
        out["error"] = ("step raised %d time(s) (%s); %d of %d (state, action) "
                        "pairs went unadjudicated"
                        % (crashes.count,
                           ", ".join("%s x%d" % (k, v)
                                     for k, v in sorted(crashes.by_type.items())),
                           pairs_nominal - out["pairs_checked"], pairs_nominal))
        out["detail"] = (
            "constraint 9 is NOT certified: %d of %d (state, action) pairs were "
            "adjudicated and %d call(s) to `step` raised. `step` is documented "
            "total, so a crash is a defect in the compiled manual, and a pair "
            "that crashed is a pair on which ambiguity was never decided -- "
            "counting it inside the coverage would let a crashier manual look "
            "cleaner. %s"
            % (out["pairs_checked"], pairs_nominal, crashes.count,
               "%d ambiguous transitions were also found." % len(clashes)
               if clashes else "No ambiguity was found among the pairs that "
                               "did run, which settles nothing about the rest."))
        return out
    out["ok"] = not clashes
    out["detail"] = (
        "no (state, action) among %d x %d admitted two rules, and all %d pairs "
        "were adjudicated -- no call to `step` raised"
        % (len(swept), len(actions), pairs_nominal) if not clashes else
        "%d ambiguous transitions found" % len(clashes))
    return out


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
