"""**The transfer protocol** — carry a pack onto a level, online.

This is A3's `a3pipeline/transfer.py` with the three things that made it A3's
taken out: it no longer knows a level's name, a world's colours, or where its
books live.  It is handed a `Pack` and an `Executor` and does the same seven
steps in the same order, because the order *is* the claim:

| step | what it establishes | cost |
|---|---|---|
| 0 · check the pack | the books are the books, and the toolchain is the one they were validated against | 0 |
| 1 · one frame | the layout | 1 frame |
| 2 · rebuild | the domain/problem split holds on this level | 0 actions |
| 3 · compile | the carried domain survives a new instance | 1 compile |
| 4 · **static certify** | the manual *renders* this level, before acting | 0 actions |
| 5 · plan | a route exists under the carried manual | 1 plan |
| 6 · execute | the world agrees | plan-length actions |
| 7 · **replay certify** | every predicted frame matched | 0 extra |

Step 0 is the new one and it is the one the inbox asked for.  W-1521's note
(`monitor/inbox/20260728T082700Z-…`) is about a fingerprint that every manifest
in this repository records and nothing compares; the cost of that gap was a paid
model call thrown away by a contract change that arrived on a commit the track
had never touched.  Here the comparison has a consumer: drift **stops the run**
before an action is spent.  `on_drift="warn"` exists for the case where a reader
has looked at the diff and decided, and it writes that decision into the report.

**Nothing here imports a world.**  The executor arrives as an argument; the only
module-level imports are the compile path, the two certify layers and the meter.
`tests/test_a6_sealing.py` reads this file's source and fails the suite if a
world module, a trace path or an engine stage appears in it — a claim about what
an arm did not read cannot be evidenced by the arm's own report.
"""

import json
import os
import sys
from typing import Callable, Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a3pipeline import certify_a3  # noqa: E402
from a3pipeline.meter import Meter  # noqa: E402
from a3pipeline.plan import run_plan  # noqa: E402

from a6carry import forms, rebuild  # noqa: E402
from a6carry.executor_api import one_row_trace, write_execution  # noqa: E402
from a6carry.pack import Pack  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DependencyDrift(Exception):
    """The toolchain is not the one this pack was validated against."""

    def __init__(self, verdict: Dict[str, object]):
        self.verdict = verdict
        super().__init__(
            "carrypack fingerprint drift: %s changed%s"
            % (", ".join(verdict["drifted"]) or "nothing",
               "; interpreter %s -> %s" % (verdict["recorded_interpreter"],
                                           verdict["current_interpreter"])
               if verdict["interpreter_changed"] else ""))


def carry(pack: Pack, executor, out_dir: str, artefacts: str,
          constants: Optional[Dict[str, Sequence[int]]] = None,
          invariant_builder: Optional[Callable] = None,
          on_drift: str = "refuse",
          arm: Optional[str] = None,
          note: str = "carries a carrypack onto a level it has never seen",
          ) -> Dict[str, object]:
    """Carry `pack` onto whatever `executor` is connected to.  Returns a report.

    `constants` are the level values the frame cannot show.  If omitted and the
    executor offers a `constants()` method, they are taken from there and
    recorded as **supplied** either way — the concession is the same size however
    it arrives, and a provenance record that hid the difference between "derived"
    and "handed over" would be the one thing this whole exercise is against.
    """
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    os.makedirs(artefacts, exist_ok=True)

    level = getattr(executor, "name", "<level>")
    arm = arm or "carry_%s" % level
    tag = arm
    if constants is None:
        constants = (executor.constants() if hasattr(executor, "constants")
                     else {})

    meter = Meter(arm=arm, level=level, carries_books=True, note=note)
    report: Dict[str, object] = {
        "arm": arm, "level": level, "pack": pack.pack_id,
        "protocol": "a6carry/1",
    }

    # -- 0. the pack is what it says it is, compiled by what it was validated on
    books = pack.check_books()
    drift = pack.check_fingerprint()
    report["pack_check"] = {"books": books, "fingerprint": drift,
                            "on_drift": on_drift}
    if not books["match"]:
        report["outcome"] = "pack_tampered"
        report["theorize_triggered"] = False
        return _finish(report, meter, artefacts, tag)
    if not drift["match"]:
        if on_drift == "refuse":
            report["outcome"] = "dependency_drift"
            report["theorize_triggered"] = False
            _finish(report, meter, artefacts, tag)
            raise DependencyDrift(drift)
        report["pack_check"]["accepted_drift"] = True

    # -- 1. one frame: the arm's entire observation ---------------------------
    frame = executor.first_frame()
    frame_path = os.path.join(artefacts, "%s_frame0.json" % tag)
    with open(frame_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"t": 0, "frame": frame}, sort_keys=True,
                                separators=(",", ":")) + "\n")
    meter.charge_frame(frame_path, "the carrying arm's entire observation")

    # -- 2. rebuild the problem from it ---------------------------------------
    try:
        problem, provenance = rebuild.rebuild_from_frame(
            frame_path, pack.requires, dict(constants), level)
    except rebuild.RebuildRefusal as refusal:
        # The manual is about a world this level is not, and the frame says so.
        # Nothing has been spent; stop before it is.
        report["provenance"] = {"preflight": refusal.verdict}
        report["outcome"] = "rebuild_refused"
        report["theorize_triggered"] = True
        return _finish(report, meter, artefacts, tag)
    rebuild.write_json(os.path.join(artefacts, "provenance_%s.json" % tag),
                       provenance)
    report["provenance"] = provenance

    # -- 3. compile the CARRIED domain ----------------------------------------
    written = forms.compile_forms(
        pack.domain_path, problem, out_dir, pack.requires,
        invariant_builder=invariant_builder)
    forms.clean_stale(out_dir, [v for k, v in (
        ("theory.py", "theory.py"), ("theory.md", "theory.md"),
        ("theory.lean", "theory.lean"), ("domain.pddl", "domain.pddl"),
        ("problem.pddl", "problem.pddl"), ("problem.json", "problem.json"))
        if k in written])
    meter.charge("compile_runs", 1, "the carried domain + the rebuilt problem")
    report["compiled"] = {k: v for k, v in written.items()
                          if k not in ("pddl_landmarks", "pddl_pushables")}
    report["pddl_workarounds"] = {
        "landmarks": written.get("pddl_landmarks"),
        "pushables": written.get("pddl_pushables"),
        "cells_added": written.get("pddl_cells_added"),
    }
    theory_py = os.path.join(out_dir, "theory.py")

    # -- 4. static certify, before a single action is spent -------------------
    static_trace = one_row_trace(
        frame, os.path.join(artefacts, "%s_frame0_trace.jsonl" % tag))
    static = certify_a3.cheap(theory_py, static_trace)
    meter.charge("certify_runs", 1, "render/responsibility check on frame 0")
    report["certify_static"] = certify_a3.cheap_brief(static)

    if not static["green"]:
        # The domain does not even *render* this level.  Acting now would spend
        # quota to learn something already known.
        report["outcome"] = "static_certify_red"
        report["theorize_triggered"] = True
        report["first_mismatch"] = (static.get("anomalies") or [None])[0]
        return _finish(report, meter, artefacts, tag)

    # -- 5. plan ---------------------------------------------------------------
    if "pddl" not in set(pack.requires.get("forms") or ()):
        report["outcome"] = "no_planning_form"
        report["theorize_triggered"] = True
        return _finish(report, meter, artefacts, tag)

    plan_report = run_plan(out_dir, level, meter=meter,
                           candidates_path=os.path.join(
                               artefacts, "candidates_%s.jsonl" % tag))
    meter.mark_first_plan()
    report["plan"] = plan_report
    if plan_report.get("status") != "SAT":
        report["outcome"] = "no_plan"
        report["theorize_triggered"] = True
        return _finish(report, meter, artefacts, tag)

    # -- 6. execute: the only contact with the world, and it costs -------------
    execution = executor.execute(plan_report["world_actions"])
    exec_path = os.path.join(artefacts, "%s_execution.jsonl" % tag)
    write_execution(exec_path, execution)
    meter.charge("world_actions", execution["actions_spent"],
                 "executing the plan")
    meter.charge("world_frames", len(execution["frames"]) - 1,
                 "frames returned by the execution (frame 0 already charged)")
    report["execution"] = {k: v for k, v in execution.items()
                           if k not in ("frames", "wins")}

    # -- 7. replay certify against what actually happened ---------------------
    replay = certify_a3.cheap(theory_py, exec_path)
    meter.charge("certify_runs", 1, "replay the execution under the manual")
    report["certify_replay"] = certify_a3.cheap_brief(replay)
    report["first_mismatch"] = (replay.get("anomalies") or [None])[0]

    # -- 8. the proof form, if the pack lets this domain have one -------------
    if "theory.lean" in written:
        lean_report = certify_a3.lean(os.path.join(out_dir, "theory.lean"))
        meter.charge("certify_runs", 1,
                     "Lean on the carried domain, new instance")
        report["certify_lean"] = certify_a3.lean_brief(lean_report)
    else:
        report["certify_lean"] = {
            "emitted": False, "green": None,
            "reason": written.get("lean_withheld"),
        }

    # -- 9. the numbers the claim is about ------------------------------------
    # theorize_rounds, candidates_adjudicated, engine_stages and
    # dsl_clauses_written are never charged above.  That is the claim; a future
    # change to this driver that needs to write a clause has to add the charge
    # here, and the bill will show it.
    report["theorize_triggered"] = not (replay["green"] and execution["win"])
    report["outcome"] = ("win" if execution["win"] and replay["green"]
                         else "replay_mismatch" if not replay["green"]
                         else "no_win")
    return _finish(report, meter, artefacts, tag)


def _finish(report: Dict[str, object], meter: Meter, artefacts: str,
            tag: str) -> Dict[str, object]:
    meter.write(os.path.join(artefacts, "bill_%s.json" % tag))
    report["bill"] = meter.as_json()
    with open(os.path.join(artefacts, "arm_%s.json" % tag), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True,
                                ensure_ascii=False) + "\n")
    return report


def brief(report: Dict[str, object]) -> str:
    counts = report.get("bill", {}).get("counts", {})
    static = report.get("certify_static") or {}
    replay = report.get("certify_replay") or {}
    return ("%-26s %-18s static=%-5s plan=%-5s replay=%-5s "
            "frames=%-4s actions=%-4s clauses=%s"
            % (report.get("level"), report.get("outcome"),
               static.get("green"), (report.get("plan") or {}).get("status"),
               replay.get("green"), counts.get("world_frames"),
               counts.get("world_actions"), counts.get("dsl_clauses_written")))
