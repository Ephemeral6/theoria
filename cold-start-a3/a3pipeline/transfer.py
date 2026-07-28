"""**The transfer arm.**  Carry the two books to level 2 and pay the bill.

This is the arm C3 is about.  It is allowed:

  * `theory/domain.dsl` and `theory/playbook.dsl` — byte-identical to the files
    level 1 produced, which a test asserts by sha256 rather than by inspection;
  * `artifacts/l2_frame0.json` — **one frame**;
  * three level constants — the goal cell and the two portal exits — supplied
    the way `CONTRACTS/dsl_grammar_v0.2.md` says level constants are supplied
    ("Grid layout, initial state, landmark coordinates and weight vectors are
    the problem, and are supplied per level").  D-A3-002 and D-A3-003 explain
    why these three and no others: neither the goal nor a portal exit is drawn
    in any frame of this world.

It is not allowed to mine a rule, and that is not a promise it makes — it is a
property of this file.  There is no import of the engine stage, no import of a
world module, and no path to a sweep trace or a candidate stream anywhere in
it, and `tests/test_sealing.py::test_the_transfer_arm_cannot_reach_a_level_2
_trace` reads the source and fails the suite if one appears.  A claim about
what an arm did *not* read cannot be evidenced by the arm's own report.

**The one thing it may do to the world is act.**  `a3world.executor` is an
environment proxy shaped like a game API: hand it a level name and a list of
actions, get frames back.  Executing costs actions and the meter charges every
one of them, because on a live game that line is quota.  A plan that is never
executed proves nothing, so the arm ends in 解出 and not in 规划.

The order of operations is the claim, in sequence:

| step | what it establishes | cost |
|---|---|---|
| read one frame | the layout | 1 frame |
| rebuild problem₂ | domain/problem split holds | 0 actions |
| compile the carried domain | the books survive a new instance | 1 compile |
| **static certify** | the manual *renders* level 2 correctly, before acting | 0 actions |
| plan | a route exists under the carried manual | 1 plan |
| execute | the world agrees | plan-length actions |
| **replay certify** | every predicted frame matched | 0 extra |

The static certify is the step worth naming.  Running the cheap layer against a
one-row trace built from frame 0 checks render, responsibility and the goal
predicate *before a single action is spent* — so a domain that does not fit the
new level is caught for free.  That is the 渲染失配 half of the safety valve,
and `negctl.py` shows the 重放失配 half firing when only the second can see the
problem.
"""

import json
import os
import sys
from typing import Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a3world.executor import run_and_record  # noqa: E402  (act only; frames back)

from a3pipeline import certify_a3, compile_a3, problem_frame  # noqa: E402
from a3pipeline.meter import Meter  # noqa: E402
from a3pipeline.plan import run_plan  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
THEORY = os.path.join(ROOT, "theory")

#: The three level constants the frame cannot show.  Every other field of the
#: problem instance is read off the pixels; `problem_frame.provenance` records
#: which is which and the report prints the split.
LEVEL_2_CONSTANTS = {
    "goal_cell": (1, 1),
    "exit_a": (1, 5),
    "exit_b": (4, 1),
}


def one_row_trace(frame_path: str, out_path: str) -> str:
    """Frame 0, written as a one-row trace so the cheap layer can read it.

    Not a new checker: `certify.replay.certify` on a single frame runs exactly
    the render, responsibility and goal-predicate passes and has no transition
    to replay.  Reusing it is better than writing a bespoke render check,
    because a bespoke check is one more thing that could be lenient in a way
    the real one is not.
    """
    with open(frame_path, encoding="utf-8") as handle:
        frame = json.load(handle)["frame"]
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"t": 0, "frame": frame, "action": None,
                                 "win": False},
                                sort_keys=True, separators=(",", ":")) + "\n")
    return out_path


def run(level: str = "a3-l2", frame_name: str = "l2_frame0.json",
        out_name: str = "generated_l2", tag: str = "l2_transfer",
        constants: Optional[Dict[str, Tuple[int, int]]] = None,
        arm: str = "l2_transfer",
        note: str = "carries domain.dsl + playbook.dsl from level 1, unchanged",
        ) -> Dict[str, object]:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    constants = dict(constants or LEVEL_2_CONSTANTS)

    meter = Meter(arm=arm, level=level, carries_books=True, note=note)
    report: Dict[str, object] = {"arm": arm, "level": level}

    # -- 1. one frame ------------------------------------------------------
    frame_path = os.path.join(ARTIFACTS, frame_name)
    meter.charge_frame(frame_path, "the transfer arm's entire observation")

    # -- 2. rebuild the problem from it -----------------------------------
    problem, provenance = problem_frame.from_frame(
        frame_path, level,
        goal_cell=constants["goal_cell"],
        exit_a=constants["exit_a"],
        exit_b=constants["exit_b"],
    )
    problem_frame.write_provenance(
        os.path.join(ARTIFACTS, "provenance_%s.json" % tag), provenance)
    report["provenance"] = provenance

    # -- 3. compile the CARRIED domain ------------------------------------
    # `theory/domain.dsl` is not re-read from some level-2 copy; it is the file
    # level 1 wrote.  Nothing in this call is level-2-specific except `problem`.
    out_dir = os.path.join(THEORY, out_name)
    written = compile_a3.compile_instance(
        os.path.join(THEORY, "domain.dsl"), problem, out_dir,
        invariant_builder=compile_a3.switch_latch_invariant,
    )
    meter.charge("compile_runs", 1, "domain.dsl + problem_2 -> four forms")
    report["compiled"] = {k: v for k, v in written.items()
                          if isinstance(v, int)}

    theory_py = os.path.join(out_dir, "theory.py")

    # -- 4. static certify, before a single action is spent ----------------
    static_trace = one_row_trace(
        frame_path, os.path.join(ARTIFACTS, "%s_frame0_trace.jsonl" % tag))
    static = certify_a3.cheap(theory_py, static_trace)
    meter.charge("certify_runs", 1, "render/responsibility check on frame 0")
    report["certify_static"] = certify_a3.cheap_brief(static)

    if not static["green"]:
        # The domain does not even *render* the new level.  Stop: acting now
        # would spend quota to learn something already known.
        report["outcome"] = "static_certify_red"
        report["theorize_triggered"] = True
        meter.write(os.path.join(ARTIFACTS, "bill_%s.json" % tag))
        report["bill"] = meter.as_json()
        return report

    # -- 5. plan ------------------------------------------------------------
    plan_report = run_plan(out_dir, level, meter=meter,
                           candidates_path=os.path.join(
                               ARTIFACTS, "candidates_%s.jsonl" % tag))
    meter.mark_first_plan()
    report["plan"] = plan_report

    if plan_report.get("status") != "SAT":
        report["outcome"] = "no_plan"
        report["theorize_triggered"] = True
        meter.write(os.path.join(ARTIFACTS, "bill_%s.json" % tag))
        report["bill"] = meter.as_json()
        return report

    # -- 6. execute: the only contact with the world, and it costs -----------
    actions = plan_report["world_actions"]
    execution = run_and_record(
        level, actions,
        os.path.join(ARTIFACTS, "%s_execution.jsonl" % tag))
    meter.charge("world_actions", execution["actions_spent"],
                 "executing the plan")
    meter.charge("world_frames", len(execution["frames"]) - 1,
                 "frames returned by the execution (frame 0 already charged)")
    report["execution"] = {k: v for k, v in execution.items()
                           if k not in ("frames", "wins")}

    # -- 7. replay certify against what actually happened --------------------
    replay = certify_a3.cheap(
        theory_py, os.path.join(ARTIFACTS, "%s_execution.jsonl" % tag))
    meter.charge("certify_runs", 1, "replay the execution under the manual")
    report["certify_replay"] = certify_a3.cheap_brief(replay)

    # -- 8. Lean -------------------------------------------------------------
    lean_report = certify_a3.lean(os.path.join(out_dir, "theory.lean"))
    meter.charge("certify_runs", 1, "Lean on the carried domain, new instance")
    report["certify_lean"] = certify_a3.lean_brief(lean_report)

    # -- 9. the numbers the claim is about ----------------------------------
    # theorize_rounds and dsl_clauses_written stay at zero and are *not*
    # charged anywhere above.  That is the claim; if a future change to this
    # arm needs to write a clause, the charge has to appear here and the
    # comparison table will show it.
    report["theorize_triggered"] = not (replay["green"] and execution["win"])
    report["outcome"] = ("win" if execution["win"] and replay["green"]
                         else "replay_mismatch" if not replay["green"]
                         else "no_win")

    meter.write(os.path.join(ARTIFACTS, "bill_%s.json" % tag))
    report["bill"] = meter.as_json()

    with open(os.path.join(ARTIFACTS, "arm_%s.json" % tag), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def _brief(entry: Dict[str, object]) -> str:
    return "%-5s %s frames, %s anomalies %s" % (
        "GREEN" if entry.get("green") else "RED",
        entry.get("frames"), entry.get("anomaly_count"),
        entry.get("anomaly_kinds") or "")


def main() -> int:
    report = run()
    print("outcome            %s" % report["outcome"])
    print("static certify     %s" % _brief(report["certify_static"]))
    if "certify_replay" in report:
        print("replay certify     %s" % _brief(report["certify_replay"]))
    if "plan" in report:
        print("plan               %s, %s steps"
              % (report["plan"].get("status"), report["plan"].get("length")))
    if "execution" in report:
        print("execution          win=%s, %d actions spent"
              % (report["execution"]["win"], report["execution"]["actions_spent"]))
    counts = report["bill"]["counts"]
    print("bill               frames=%d actions=%d engines=%d candidates=%d "
          "rounds=%d clauses=%d"
          % (counts["world_frames"], counts["world_actions"],
             counts["engine_stages"], counts["candidates_adjudicated"],
             counts["theorize_rounds"], counts["dsl_clauses_written"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
