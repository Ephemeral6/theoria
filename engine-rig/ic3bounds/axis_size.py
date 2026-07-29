"""Axis A -- state-space size, on the family that contains the M9 anchor.

M9 proved one thing: peg `0111` cannot reach `0100`, and the invariant that shows
it is `(!pos1 | pos2) & (pos1 | !pos2)` -- positions 1 and 2 always agree.  Two
clauses, four literals, converged at frame 2, holding on 8 of 16 states.  One
point.  This module walks the same family up in board size, keeping the shape of
the question fixed and changing only |S| = 2^n, so that the numbers either trace a
line or show where the line stops.

    n = 4 ... 14                       |S| = 16 ... 16384
    start = "0" + "1"*(n-1)            the M9 configuration, widened
    goal  = "01" + "0"*(n-2)           a single final state, the M9 goal, widened

**The anchor trap, which cost this package a rung before it was written down.**
`interop.peg1d.build_graph` takes `goal_states=None` to mean *all* single-peg
finals.  At n=4 that is a different question with a different answer -- four
clauses, holding on 3 of 16 states, nothing like the M9 invariant.  A ladder that
took the default would have started one rung to the side of its own anchor and
then reported the drift as a size effect.  So the goal is always passed
explicitly, and `check_anchor()` refuses the whole run if the n=4 row does not
render the M9 CNF character for character.  It raises; it does not warn.

**Cost.**  Measured on the machine this was built on, log-log regression over
the answered rungs gives roughly |S|^2.0 -- 0.0005s at n=4, 0.6s at n=8, 100s at
n=12.  (An earlier note here said 1.9 and "deepest convergence frame 12"; both
were stale against this module's own artefact, which reaches frame 20 at n=13.
The 1.9 also came from an all-even ladder, and parity turns out to matter on
this family -- odd n gives a systematically more vacuous invariant at the same
|S| -- so the exponent was fitted through a confound.)

`max_levels=64` does not bind on any rung that *answered*: the deepest
convergence seen is frame 20.  It cannot be said not to bind on a rung that was
killed, because a killed child reports no frame, and this module no longer says
otherwise.  What can be said is that frames grow with n (12 at n=12, 14 at n=11,
20 at n=13), so a cap is a thing the top of this ladder is walking towards
rather than a thing it is known to have avoided.

**Parity.**  The ladder is walked densely rather than in even steps.  The
original was `4, 6, 8, 10, 12, 13, 14` -- all even but for one rung -- and that
hid the fact that odd boards are more vacuous: the near-vacuity flag first fires
at n=11, which the even ladder skipped, not at n=13 where it was first seen.

**The recheck column.**  E8 asks, per step, whether an *independent* checker's
recheck passes -- so every rung carries a `recheck` dict beside its
`deterministic` and `timing` halves, filled by `ic3bounds.recheck_column` from
`recheck/`'s own exit-code taxonomy (0 ACCEPT, 1 REJECT, 2 would-not-load,
3 INCONSISTENT, 4 the rechecker crashed).  Two properties of it are load-bearing:

* **A rung with no invariant reads `n/a -- no invariant`, never "passed".**  The
  top of this ladder is a timeout, and a timeout has nothing for a checker to
  check; a column that scored it green would be reporting a pass on an object
  that does not exist.
* **ACCEPT alone is not a pass.**  Every row carries the number of states the
  invariant holds on, counted twice -- by the engine over 2^n boolean tuples and
  by the rechecker over the product of the declared domains -- because a
  translation that drops one literal still ACCEPTs while denoting a smaller set
  (peg-6: 27 states instead of 30).  A row whose counts disagree is a finding,
  `recheck_findings` names it, and `python -m ic3bounds` exits 1 on it.

The column is computed in the parent, after the budgeted child has exited, so it
costs the rung's budget nothing and appears in no timing.
"""

import datetime
import json
import os
import platform
import subprocess
from typing import Any, Callable, Dict, List, Optional, Sequence

from ic3bounds import harness, recheck_column
from ic3bounds.harness import AnchorDrift, StepSpec

AXIS = "size"
FAMILY = "peg-1d"

# Dense, not every-other.  The original all-even ladder plus one odd rung put
# board parity and board size in the same column: odd boards give a more vacuous
# invariant at the same |S|, so the even ladder reported the near-vacuity onset
# two rungs late and fitted a cost exponent through the confound.
LADDER = (4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
DEFAULT_TIMEOUT_SECONDS = 300.0

ANCHOR_N = 4
ANCHOR_CNF = "(!pos1 | pos2) & (pos1 | !pos2)"
ANCHOR_COVERAGE = "8/16"
ANCHOR_N_CLAUSES = 2
ANCHOR_N_LITERALS = 4
ANCHOR_FRAME = 2

# Cost is monotone in n on this family, so once the budget has been missed twice
# there is nothing left to learn from spending it again -- the third row would
# cost another full budget to record the same word.  Stopping is reported in the
# artefact, not hidden: `stopped_early` names the reason.
STOP_AFTER_TIMEOUTS = 2


def initial_for(n: int) -> str:
    """The M9 configuration widened: one hole at the left, pegs everywhere else."""
    return "0" + "1" * (n - 1)


def goal_for(n: int) -> str:
    """The M9 goal widened: exactly one peg, at position 1."""
    return "01" + "0" * (n - 2)


def spec_for(n: int, max_levels: int = harness.DEFAULT_MAX_LEVELS) -> StepSpec:
    return StepSpec(
        axis=AXIS,
        label="n=%d" % n,
        n=n,
        initial=initial_for(n),
        goal_states=(goal_for(n),),
        max_levels=max_levels,
    )


def check_anchor(record: Dict[str, Any]) -> None:
    """The n=4 row must be M9's invariant, exactly.  Raises if it is not."""
    det = record.get("deterministic", {})
    expected = {
        "verdict": harness.INVARIANT,
        "cnf_text": ANCHOR_CNF,
        "coverage": ANCHOR_COVERAGE,
        "n_clauses": ANCHOR_N_CLAUSES,
        "n_literals": ANCHOR_N_LITERALS,
        "converged_at_frame": ANCHOR_FRAME,
    }
    drifted = {
        key: (value, det.get(key))
        for key, value in sorted(expected.items())
        if det.get(key) != value
    }
    if drifted:
        raise AnchorDrift(
            "the n=4 rung is no longer the M9 anchor, so nothing above it is on "
            "the same ladder: %s (the usual cause is goal_states=None, which "
            "means ALL single-peg finals and is a different question)"
            % json.dumps({k: {"expected": v[0], "got": v[1]}
                          for k, v in drifted.items()}, sort_keys=True)
        )


def boundary_of(steps: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The first rung that did not produce an answer, and what stopped it.

    An escalating verdict is deliberately not a boundary: `engine-refused` and
    `adapter-mismatch` say the measurement is broken, not that the problem is
    hard, and letting them terminate the table would publish a defect as a
    result.  They are surfaced through `escalations()` instead.
    """
    solved = [s for s in steps if s["deterministic"]["verdict"] in harness.ANSWERS]
    for step in steps:
        verdict = step["deterministic"]["verdict"]
        if verdict in harness.ANSWERS or verdict in harness.ESCALATING:
            continue
        return {
            "n": step["spec"]["n"],
            "label": step["spec"]["label"],
            "n_states": step["deterministic"]["n_states"],
            "verdict": verdict,
            "machine_dependent": bool(step["deterministic"]["machine_dependent"]),
            "budget_seconds": step.get("budget_seconds"),
            "largest_answered_n": solved[-1]["spec"]["n"] if solved else None,
            "detail": step["deterministic"]["detail"],
        }
    return None


def vacuity(steps: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Where the answers stop being worth having, which is not where they stop.

    `boundary_of` asks only whether a rung produced a verdict, so a rung whose
    invariant admits 95% of the state space counts exactly as answered as the
    M9 anchor, which admits half.  `near_vacuous` was being computed on every
    row and consumed by nothing -- an adversarial pass found it, and this is the
    consumer.

    `states_excluded` is here because the ratio alone understates it.  On this
    family the n=13 invariant excludes *fewer states in absolute terms* than the
    n=12 one, from a state space twice the size: the answer did not merely
    become relatively weaker, it became weaker.
    """
    rows = []
    for step in steps:
        det = step["deterministic"]
        excluded = (None if det.get("n_satisfying") is None
                    else det["n_states"] - det["n_satisfying"])
        rows.append({
            "n": step["spec"]["n"],
            "n_states": det["n_states"],
            "coverage_ratio": det.get("coverage_ratio"),
            "near_vacuous": det.get("near_vacuous"),
            "states_excluded": excluded,
            "literal_saturation": det.get("literal_saturation"),
        })
    flagged = [row for row in rows if row["near_vacuous"]]
    clean = [row for row in rows if row["near_vacuous"] is False]

    def rising(subset: Sequence[Dict[str, Any]]) -> Optional[bool]:
        values = [row["literal_saturation"] for row in subset
                  if row["literal_saturation"] is not None]
        if len(values) < 2:
            return None
        return all(a <= b for a, b in zip(values, values[1:]))

    return {
        "threshold": harness.NEAR_VACUOUS_RATIO,
        "rows": rows,
        "first_near_vacuous": flagged[0] if flagged else None,
        "largest_non_vacuous": clean[-1] if clean else None,
        "read_it_as": "the boundary a reader who wants an ADJUDICABLE invariant "
                      "should use. `boundary` above is the boundary for a reader "
                      "who wants any verdict at all, and on this family the two "
                      "are not the same rung.",
        "saturation": {
            "what": "literal_saturation climbing toward 1.0 is IC3 degrading "
                    "into state enumeration (see harness.py).",
            # Computed, not asserted. An earlier version of this block stated
            # flatly that saturation is monotone across the ladder, which was
            # true of the every-other ladder it was written against and false
            # of the contiguous one: the sequence splits by board parity, and
            # asserting a trend the rows can be checked against is exactly the
            # kind of sentence this package keeps catching itself in.
            "monotone_overall": rising(rows),
            "monotone_on_even_boards": rising([r for r in rows if r["n"] % 2 == 0]),
            "monotone_on_odd_boards": rising([r for r in rows if r["n"] % 2 == 1]),
            "parity_note": "odd boards sit systematically above even ones. That "
                           "is the same parity effect that made the original "
                           "every-other ladder report the near-vacuity onset "
                           "two rungs late.",
        },
    }


def escalations(steps: Sequence[Dict[str, Any]]) -> List[str]:
    """Rows that are defects rather than data.  Non-empty means stop and fix."""
    return [
        "%s: %s -- %s" % (step["spec"]["label"],
                          step["deterministic"]["verdict"],
                          step["deterministic"]["detail"])
        for step in steps
        if step["deterministic"]["escalate"]
    ]


def _git(repo_root: str, *args: str) -> str:
    try:
        out = subprocess.run(["git", "-C", repo_root, *args],
                             capture_output=True, text=True, timeout=60)
        return (out.stdout or "").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def provenance(command: str) -> Dict[str, Any]:
    """Self-contained provenance, carried inside the artefact.

    The repo convention is `runs/<id>/MANIFEST.json`, and `__main__.py` writes
    one when the run directory does not already have it.  It may well: several
    agents write into this E8 directory, and clobbering a manifest that lists
    someone else's files would destroy provenance rather than record it.  So the
    four required fields ride along in here too, where nothing can overwrite
    them.
    """
    engine_rig = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_root = os.path.dirname(engine_rig)
    return {
        "prompt_id": "E8-ic3-bounds",
        "branch": _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": _git(repo_root, "rev-parse", "HEAD"),
        "utc": datetime.datetime.now(datetime.timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "command": command,
        "host": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
    }


def report(steps: Sequence[Dict[str, Any]], timeout_seconds: float,
           ns: Sequence[int], complete: bool,
           stopped_early: Optional[str] = None,
           command: str = "") -> Dict[str, Any]:
    """The artefact.  Rebuilt from scratch after every rung, so the file on disk
    is always a whole document rather than a truncated one."""
    return {
        "axis": AXIS,
        "axis_letter": "A",
        "question": "where does IC3 stop, as the state space grows and nothing "
                    "else about the question changes?",
        "family": FAMILY,
        "ladder": list(ns),
        "budget_seconds": timeout_seconds,
        "complete": complete,
        "stopped_early": stopped_early,
        "anchor": {
            "n": ANCHOR_N,
            "milestone": "M9",
            "cnf_text": ANCHOR_CNF,
            "coverage": ANCHOR_COVERAGE,
            "n_clauses": ANCHOR_N_CLAUSES,
            "n_literals": ANCHOR_N_LITERALS,
            "converged_at_frame": ANCHOR_FRAME,
            "checked": "ic3bounds.axis_size.check_anchor, which raises AnchorDrift",
            "trap": "build_graph(goal_states=None) means ALL single-peg finals "
                    "and gives a different invariant at n=4 (4 clauses, 3/16) -- "
                    "the ladder passes its goal explicitly for this reason",
        },
        "determinism": {
            "deterministic_half": "Re-derived exactly by a verify pass: verdict, "
                                  "clause and literal counts, frame of "
                                  "convergence, the engine's counters, the "
                                  "rendered CNF, the coverage fraction.",
            "timing_half": "Presence and ordering only, never equality. A wall "
                           "clock is a statement about one machine on one "
                           "afternoon.",
            "carve_out": "A `timeout` row is flagged machine_dependent: its "
                         "verdict is a property of this budget on this hardware, "
                         "and only the verdict and the budget are comparable.",
        },
        "no_generalisation_failure_mode": (
            "pdr.generalise always terminates and always returns a clause -- "
            "worst case the full negated cube it was handed. There is therefore "
            "no such failure category in this engine, and none is tabulated. "
            "The same information is carried continuously by n_literals, "
            "widest_clause and literal_saturation (mean clause width over the "
            "variable count; 1.0 means nothing was generalised)."
        ),
        "recheck": {
            "column": "steps[].recheck",
            "question": "does an independent checker's recheck of this step's "
                        "invariant pass?",
            "checker": "recheck/ -- it imports nothing from engines/ and "
                       "re-derives the transition relation by grounding the "
                       "rules over the product of the declared domains",
            "ruleset_source": "recheck.build_cases, a second transcription of "
                              "the same geometry, tied to this one only through "
                              "interop.peg1d",
            "taxonomy": dict(recheck_column.TAXONOMY),
            "pass_means": "ACCEPT *and* both state counts agree. ACCEPT alone "
                          "is not a pass: on peg-6 a one-literal weakening is "
                          "ACCEPTed while denoting 27 states instead of 30, so "
                          "a column recording only the verdict would be green "
                          "about the wrong object.",
            "cross_check": "the engine counts the invariant over 2^n boolean "
                           "tuples (engines.ic3_pdr.check.verify); the "
                           "rechecker counts the emitted predicate over the "
                           "product of the declared domains. Two enumerations, "
                           "two encodings, one set of states -- and the row "
                           "carries both numbers, not their agreement alone.",
            "no_invariant": "a rung that timed out, hit the level cap or was "
                            "refused reads %r. There is no invariant on such a "
                            "row, so there is nothing to check and nothing to "
                            "pass." % recheck_column.NO_INVARIANT,
            "when_it_was_computed": "in the parent, after the budgeted child "
                                    "exited. It consumes none of the rung's "
                                    "budget and appears in no timing; the "
                                    "invariant crosses the process boundary as "
                                    "cnf_text and is read back, re-rendered and "
                                    "compared with the recorded string "
                                    "character for character before it is used.",
        },
        "recheck_findings": recheck_column.findings(steps),
        "vacuity": vacuity(steps),
        "boundary": boundary_of(steps),
        "escalations": escalations(steps),
        "steps": list(steps),
        "provenance": provenance(command),
    }


def run(ns: Sequence[int] = LADDER,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_levels: int = harness.DEFAULT_MAX_LEVELS,
        on_step: Optional[Callable[[Dict[str, Any]], None]] = None,
        command: str = "") -> Dict[str, Any]:
    """Walk the ladder.  `on_step` is called after every rung, with the report so
    far, so an interrupted run still leaves the rungs it finished on disk."""
    steps: List[Dict[str, Any]] = []
    timeouts = 0
    stopped_early: Optional[str] = None
    ordered = sorted(ns)

    for index, n in enumerate(ordered):
        record = harness.run_step(spec_for(n, max_levels=max_levels),
                                  timeout_seconds=timeout_seconds)
        if n == ANCHOR_N:
            check_anchor(record)
        # Outside the budget on purpose: the child has already exited, so the
        # recheck cannot push a rung over its own wall clock and turn an
        # answered row into a timeout.
        record["recheck"] = recheck_column.column_for(record)
        steps.append(record)
        if record["deterministic"]["verdict"] == harness.TIMEOUT:
            timeouts += 1
        remaining = ordered[index + 1:]
        if timeouts >= STOP_AFTER_TIMEOUTS and remaining:
            stopped_early = (
                "%d rungs missed the %.0fs budget and cost is monotone in n on "
                "this family, so %s would each have spent a full budget to "
                "record the same word"
                % (timeouts, timeout_seconds,
                   ", ".join("n=%d" % k for k in remaining))
            )
        complete = stopped_early is None and index == len(ordered) - 1
        current = report(steps, timeout_seconds, ordered, complete,
                         stopped_early, command)
        if on_step is not None:
            on_step(current)
        if stopped_early is not None:
            break

    if not steps:
        return report([], timeout_seconds, ordered, False, None, command)
    return current


def markdown(payload: Dict[str, Any]) -> str:
    """The table, computed from nothing the JSON does not already carry."""
    lines = [
        # `vacuous?` is in the table because it was being computed on every row
        # and published on none: the n=13 row carries near_vacuous=true and a
        # reader of the rendered table could not see it, which is how a rung
        # that excludes five per cent of the space reads the same as one that
        # excludes half.
        "| n | \\|S\\| | verdict | clauses | literals | widest | saturation | "
        "frame | blocked | lit dropped | cls dropped | coverage | vacuous? | "
        "wall (s) | recheck | recheck=engine |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for step in payload["steps"]:
        det = step["deterministic"]
        wall = (step.get("timing") or {}).get("wall_seconds")
        column = step.get("recheck") or {}

        def cell(value):
            return "-" if value is None else str(value)

        # The two counts are printed side by side rather than as a tick: the
        # numbers are the check, and a reader who sees only "ok" has to trust
        # that somebody compared the right pair.
        counts = "-"
        if column.get("recheck_n_satisfying") is not None:
            counts = "%s=%s %s" % (
                column["recheck_n_satisfying"], column["engine_n_satisfying"],
                "ok" if column.get("counts_agree") else "MISMATCH")

        lines.append(
            "| %d | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | "
            "%s | %s | %s |"
            % (
                step["spec"]["n"], det["n_states"], det["verdict"],
                cell(det["n_clauses"]), cell(det["n_literals"]),
                cell(det["widest_clause"]), cell(det["literal_saturation"]),
                cell(det["converged_at_frame"]), cell(det["states_blocked"]),
                cell(det["literals_dropped"]), cell(det["clauses_dropped"]),
                cell(det["coverage"]),
                "-" if det["near_vacuous"] is None
                else ("**yes**" if det["near_vacuous"] else "no"),
                "-" if wall is None else "%.3f" % wall,
                cell(column.get("status")), counts,
            )
        )
    return "\n".join(lines)
