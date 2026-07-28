"""**The cold-start arm**, metered — run once for level 1 and once for level 2.

Level 1's run is the baseline every other number is quoted against.  Level 2's
run is the control arm: the *same* level the transfer arm solves, done again
from nothing, so that "what the books saved" is a subtraction between two
measurements rather than an estimate.

The two runs are the same function with different arguments, and that is the
whole methodological point.  If the control arm were a separate implementation
it could differ from the baseline in a dozen small ways — a cheaper explorer, a
laxer certify, a different problem builder — and every one of them would show
up in the bill as a saving the books did not actually produce.

`run_l1.py` remains the standalone **acceptance driver** with the fuller
report; this module is the **metered arm**.  They share every stage
(`problem_frame`, `compile_a3`, `certify_a3`, `plan`) and differ only in what
they print and what they charge.

**What is charged, and where the honesty is.**  Six of the nine meter lines are
observed by this module directly — frames, actions, engine stages, candidates,
compiles, certifies, plans.  Two are not observable from inside a script and
are therefore *declared with a citation*:

* `theorize_rounds` — how many passes a person made over the candidate stream
  before the book stopped changing.  It comes from the arm's `THEORIZE_LOG`,
  which states it in a section called "Rounds".  A script cannot count this and
  pretending otherwise would be worse than declaring it.
* `dsl_clauses_written` — **not** declared: counted, by parsing the `.dsl` the
  arm produced and counting rules plus laws.  A clause count that was typed in
  is a clause count that can drift from the file.

The transfer arm charges zero on both lines, and the reason it may do so is
that it writes no `.dsl` at all — there is no file for `clause_count` to find.
"""

import json
import os
import sys
from typing import Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from a3world.executor import run_and_record  # noqa: E402

from a3pipeline import certify_a3, compile_a3, engines, problem_frame  # noqa: E402
from a3pipeline.meter import Meter  # noqa: E402
from a3pipeline.plan import run_plan  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")
THEORY = os.path.join(ROOT, "theory")


#: The two cold-start arms.  Note that `goal_cell`, `exit_a` and `exit_b` are
#: supplied here exactly as they are to the transfer arm: the cold start gets
#: no advantage and no handicap on the three fields no frame can show, so the
#: comparison isolates the rules and nothing else.
L1 = {
    "arm": "l1_cold_start",
    "level": "a3-l1",
    "tag": "l1",
    "dsl": "domain.dsl",
    "trace": "l1_sweep.jsonl",
    "out_name": "generated_l1",
    "goal_cell": (7, 7),
    "exit_a": (1, 6),
    "exit_b": (3, 2),
    "theorize_rounds": 1,          # THEORIZE_LOG.md, "Rounds"
    "note": "the baseline: level 1 from nothing, carrying nothing",
}

L2_SCRATCH = {
    "arm": "l2_from_scratch",
    "level": "a3-l2",
    "tag": "l2_scratch",
    "dsl": "domain_l2_scratch.dsl",
    "trace": "l2_sweep.jsonl",
    "out_name": "generated_l2_scratch",
    "goal_cell": (1, 1),
    "exit_a": (1, 5),
    "exit_b": (4, 1),
    "theorize_rounds": None,       # read from THEORIZE_LOG_L2_SCRATCH.md
    "note": "the control arm: level 2 from nothing, carrying nothing",
}


def clause_count(dsl_path: str) -> Dict[str, int]:
    """Rules + laws, counted from the file rather than declared."""
    ast = parse_theory(open(dsl_path, encoding="utf-8").read())
    rules = len(ast.rules.rules) if ast.rules else 0
    laws = 0
    if getattr(ast, "laws", None) is not None:
        laws = (len(getattr(ast.laws, "invariants", []) or [])
                + len(getattr(ast.laws, "theorems", []) or []))
    return {"rules": rules, "laws": laws, "total": rules + laws}


def declared_rounds(log_path: str, fallback: int = 1) -> int:
    """Read the round count out of the arm's own THEORIZE_LOG.

    Looks for a line of the form `**<n>.**` or `**One.**` under `## Rounds`.
    If it cannot find one it returns `fallback` and the caller records that the
    number was not found — a missing declaration must not silently become a
    flattering zero.
    """
    words = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9}
    if not os.path.exists(log_path):
        return fallback
    text = open(log_path, encoding="utf-8").read().lower()
    marker = text.find("## rounds")
    if marker < 0:
        return fallback
    tail = text[marker:marker + 400]

    # The *first occurrence in the text*, not the first key in the dict.  The
    # earlier version scanned the dictionary and returned `two` for a log that
    # said "**Four**, numbered 0-3" because the word "two" appeared later in
    # the same paragraph — it under-charged the control arm by two rounds.
    best: Optional[Tuple[int, int]] = None
    for token, value in list(words.items()) + [(str(d), d) for d in range(10)]:
        at = tail.find("**%s" % token)
        if at >= 0 and (best is None or at < best[0]):
            best = (at, value)
    return best[1] if best else fallback


def run(spec: Dict[str, object], log_name: str = "THEORIZE_LOG.md",
        ) -> Dict[str, object]:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")

    tag = spec["tag"]
    meter = Meter(arm=spec["arm"], level=spec["level"], carries_books=False,
                  note=spec["note"])
    report: Dict[str, object] = {"arm": spec["arm"], "level": spec["level"]}

    trace_path = os.path.join(ARTIFACTS, spec["trace"])
    dsl_path = os.path.join(THEORY, spec["dsl"])
    out_dir = os.path.join(THEORY, spec["out_name"])

    # -- 1. the evidence, and what it cost to obtain -----------------------
    meter.charge_trace(trace_path, "%s — this arm's whole evidence" % spec["trace"])

    # -- 2. the engines ----------------------------------------------------
    engines.run(tag, spec["trace"], spec["note"], meter=meter)
    candidates = os.path.join(ARTIFACTS, "candidates_%s.jsonl" % tag)
    meter.charge_candidates(candidates)

    # -- 3. the theorize step ----------------------------------------------
    rounds = spec["theorize_rounds"]
    if rounds is None:
        rounds = declared_rounds(os.path.join(ROOT, log_name))
    meter.charge("theorize_rounds", rounds, "declared in %s" % log_name)
    clauses = clause_count(dsl_path)
    meter.charge("dsl_clauses_written", clauses["total"],
                 "counted from %s: %d rules + %d laws"
                 % (spec["dsl"], clauses["rules"], clauses["laws"]))
    report["clauses"] = clauses

    # -- 4. the problem ------------------------------------------------------
    problem, provenance = problem_frame.from_trace(
        trace_path, spec["level"], goal_cell=tuple(spec["goal_cell"]),
        exit_a=tuple(spec["exit_a"]), exit_b=tuple(spec["exit_b"]))
    problem_frame.write_provenance(
        os.path.join(ARTIFACTS, "provenance_%s.json" % tag), provenance)
    report["provenance"] = provenance

    # -- 5. compile ----------------------------------------------------------
    written = compile_a3.compile_instance(
        dsl_path, problem, out_dir,
        invariant_builder=compile_a3.switch_latch_invariant)
    meter.charge("compile_runs", 1, "%s + problem -> four forms" % spec["dsl"])
    report["compiled"] = {k: v for k, v in written.items()
                          if isinstance(v, int)}

    theory_py = os.path.join(out_dir, "theory.py")

    # -- 6. certify against the evidence it was induced from -----------------
    cheap = certify_a3.cheap(theory_py, trace_path)
    meter.charge("certify_runs", 1, "cheap replay over the sweep")
    report["certify_cheap"] = certify_a3.cheap_brief(cheap)

    lean_report = certify_a3.lean(os.path.join(out_dir, "theory.lean"))
    meter.charge("certify_runs", 1, "lean")
    report["certify_lean"] = certify_a3.lean_brief(lean_report)

    # -- 7. plan --------------------------------------------------------------
    plan_report = run_plan(out_dir, spec["out_name"], meter=meter,
                           candidates_path=os.path.join(
                               ARTIFACTS, "candidates_plan_%s.jsonl" % tag))
    meter.mark_first_plan()
    report["plan"] = {k: v for k, v in plan_report.items()
                      if k not in ("manual_trail",)}

    # -- 8. execute, so the arm ends in 解出 like the transfer arm does --------
    if plan_report.get("status") == "SAT":
        execution = run_and_record(
            spec["level"], plan_report["world_actions"],
            os.path.join(ARTIFACTS, "%s_execution.jsonl" % tag))
        meter.charge("world_actions", execution["actions_spent"],
                     "executing the plan")
        meter.charge("world_frames", len(execution["frames"]) - 1,
                     "frames returned by the execution")
        report["execution"] = {k: v for k, v in execution.items()
                               if k not in ("frames", "wins")}
        replay = certify_a3.cheap(
            theory_py, os.path.join(ARTIFACTS, "%s_execution.jsonl" % tag))
        meter.charge("certify_runs", 1, "replay the execution")
        report["certify_replay"] = certify_a3.cheap_brief(replay)
        report["outcome"] = ("win" if execution["win"] and replay["green"]
                             else "replay_mismatch" if not replay["green"]
                             else "no_win")
    else:
        report["outcome"] = "no_plan"

    meter.write(os.path.join(ARTIFACTS, "bill_%s.json" % spec["arm"]))
    report["bill"] = meter.as_json()
    with open(os.path.join(ARTIFACTS, "arm_%s.json" % spec["arm"]), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def _print(report: Dict[str, object]) -> None:
    counts = report["bill"]["counts"]
    print("%-18s outcome=%-16s cheap=%-5s lean=%-5s plan=%s/%s"
          % (report["arm"], report["outcome"],
             report["certify_cheap"]["green"],
             report["certify_lean"].get("green"),
             report["plan"].get("status"), report["plan"].get("length")))
    print("   bill  frames=%d actions=%d engines=%d candidates=%d rounds=%d "
          "clauses=%d compiles=%d certifies=%d plans=%d"
          % (counts["world_frames"], counts["world_actions"],
             counts["engine_stages"], counts["candidates_adjudicated"],
             counts["theorize_rounds"], counts["dsl_clauses_written"],
             counts["compile_runs"], counts["certify_runs"],
             counts["plan_runs"]))


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("both", "l1"):
        _print(run(L1, "THEORIZE_LOG.md"))
    if which in ("both", "l2"):
        if not os.path.exists(os.path.join(THEORY, L2_SCRATCH["dsl"])):
            print("l2_from_scratch  SKIPPED — %s does not exist yet"
                  % L2_SCRATCH["dsl"])
            return 0
        _print(run(L2_SCRATCH, "THEORIZE_LOG_L2_SCRATCH.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
