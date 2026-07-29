"""a0-spike's completion gate.

    cd a0-spike && python verify.py

Three rungs, and the territory is finished only if all three are green:

  1. the suite passes;
  2. the real pipeline runs once, offline -- `python -m pipeline.run_a0`;
  3. the artefact that run produced has the fields it claims to have, and its
     counts clear an explicit floor.

Rung 3 is the one that is usually missing.  A green suite says the code does
what its author thought; it does not say the pipeline ran, and it does not say
the report it emitted still has the shape the territory's README promises.

-----------------------------------------------------------------------------
LIMITATION, stated up front rather than buried: THIS GATE'S RUNG 2 WRITES INTO
THE WORKING TREE.
-----------------------------------------------------------------------------

`engine-rig/verify.py` -- the exemplar -- runs its pipeline into a
`tempfile.mkdtemp()` and touches nothing tracked, because `tools.run_all` takes
`--out`.  **`pipeline/run_a0.py` takes no arguments at all.**  Its output
directory is the module constant

    ARTIFACTS = os.path.join(HERE, "artifacts")        # run_a0.py:23

with `HERE` derived from `__file__`, and it is read by three separate stages
(`gen_exec.compile_module(out_path=...)`, `pddl_gen.write_files`, and `main`'s
report writer).  There is no argument, no environment variable and no
`artifacts_dir()` seam to override.  Copying the territory into a temp
directory does not work either: `run_a0.py:14-17` computes `REPO =
dirname(HERE)` and puts `<REPO>/engine-rig` on `sys.path`, so a relocated copy
loses `fd_adapter` and the run stops being the real run.

So rung 2 runs the pipeline in place, and this gate is honest about the
consequence: **running it dirties `a0-spike/artifacts/`** with
`a0_report.json`, `theory_exec.py` and `pddl/*.pddl`.  The gate does not
snapshot-and-restore them -- restoring files behind the user's back is how a
checker becomes a thing that loses work.  It writes nothing of its own into the
tree (`tempfile.mkdtemp()` holds everything the gate itself needs, and pytest
runs with `-p no:cacheprovider`), and it prints a reminder at the end.  If you
need a clean tree afterwards, `git checkout -- a0-spike/artifacts` is yours to
run, deliberately.

There is one compensation.  Because the artefacts are in the tree and may be
left over from a previous run, rung 3 refuses to read a stale file: every
artefact must have an mtime later than the moment rung 2 started.  A gate that
grades yesterday's report is not grading a run.

-----------------------------------------------------------------------------
THE LEAN HOLE -- the reason this file exists in its present shape
-----------------------------------------------------------------------------

`run_a0.py`'s own verdict is (run_a0.py:248-254):

    ok = (... and (not report["lean"].get("available")
                   or (report["lean"]["compiles"] and ...)))

A missing Lean toolchain makes the left disjunct true and silently drops every
proof-form check from the verdict.  "Lean is not installed" and "Lean checked
out clean" produce the same exit code, which means the territory can report
itself finished having proved nothing.

This gate does not reproduce that.  Lean's availability is reported **by name**
and gets its own outcome:

    lean available + green   -> rung 3 can be green,  exit 0
    lean absent              -> INCOMPLETE,           exit 2
    lean available + not green -> RED,                exit 1

Exit 2 is non-zero on purpose.  Absence is a distinct, visible state and it is
never a pass.

-----------------------------------------------------------------------------
FLOORS -- an empty result is not a pass
-----------------------------------------------------------------------------

Every count below has a floor with a reason.  "0 mismatches out of 0 cases"
reads exactly like "0 mismatches out of 39960 cases" to anything that only
checks the mismatch count, and several checks in this repo pass that way.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS = os.path.join(HERE, "artifacts")
REPORT = os.path.join(ARTIFACTS, "a0_report.json")
RUN_A0_SOURCE = os.path.join(HERE, "pipeline", "run_a0.py")

# Every top-level key `pipeline/run_a0.py` claims to write.  Checked by
# presence, never by `.get(field, <the value I was hoping for>)`.
REQUIRED_TOP_LEVEL = (
    "certify", "certify_generated", "explore", "grading", "held_out", "lean",
    "lean_cross_form", "levels", "mine", "perceive", "prove",
)

# Files the run must actually produce, beyond the report itself.
REQUIRED_FILES = (
    os.path.join(ARTIFACTS, "a0_report.json"),
    os.path.join(ARTIFACTS, "theory_exec.py"),
    os.path.join(ARTIFACTS, "pddl", "domain.pddl"),
)

# --- floors ----------------------------------------------------------------
# Evidence is pooled across levels on purpose (run_a0.py:37-40: "one level
# cannot force every domain rule").  Five levels is the whole point of the
# pooling; four means a level dropped out of EVIDENCE_LEVELS unnoticed.
MIN_EVIDENCE_LEVELS = 5
# 285 episodes observed.  50 is a floor, not a target: below it the explorer
# has stopped exploring, and the replay-exactness claim covers nothing.
MIN_EPISODES = 50
# 1966 transitions observed.  Replay-exactness over 3 transitions is not a
# certificate, it is a coincidence.
MIN_TRANSITIONS = 500
# 20 rules observed.  The world has four directions and each needs at minimum
# a walk rule, a push rule and a blocked rule -- 4x3 = 12 is the arithmetic
# floor below which some direction is simply unexplained.
MIN_RULES = 12
# 39960 held-out cases observed across 5 levels.  This floor is the important
# one in the file: `held_out.exact` is `all(mismatches == 0)`, which is
# vacuously True over an empty enumeration.
MIN_HELD_OUT_CASES = 10000
# 9408 Lean/Python cross-form cases observed.  `forms_agree` has the same
# vacuous-truth shape as `held_out.exact`.
MIN_LEAN_CROSS_CASES = 1000
# The territory exists to say "solved" about one level and "unsolvable, and
# here is why" about another.  One graded level cannot demonstrate both.
MIN_LEVELS_GRADED = 2


def sh(argv, cwd=HERE):
    """Run a stage, decoding as UTF-8 rather than as the host locale.

    `text=True` alone decodes with cp936 on this box; a child printing UTF-8
    then either mojibakes or raises UnicodeDecodeError inside subprocess.run,
    and a checker that dies decoding its child is a checker that did not check.
    """
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def fail(problems, message):
    print("   FAIL  %s" % message)
    problems.append(message)


def need(problems, mapping, key, where):
    """Fetch a required field, or fail.  Never defaults.

    `mapping.get(key, True)` is the single most common way a gate in this repo
    has passed a run in which the field disappeared, so the helper that could
    do it does not exist.
    """
    if not isinstance(mapping, dict) or key not in mapping:
        fail(problems, "%s is missing the field %r" % (where, key))
        return None
    return mapping[key]


def must_be_true(problems, mapping, key, where):
    value = need(problems, mapping, key, where)
    if value is None and (not isinstance(mapping, dict) or key not in mapping):
        return False
    if value is not True:
        fail(problems, "%s.%s is %r, and only the literal True is a pass"
             % (where, key, value))
        return False
    return True


def at_least(problems, value, floor, what):
    if not isinstance(value, int) or isinstance(value, bool):
        fail(problems, "%s is %r, which is not a count" % (what, value))
        return False
    if value < floor:
        fail(problems, "%s is %d, floor is %d -- an empty or nearly empty "
                       "result is not a pass" % (what, value, floor))
        return False
    return True


# --------------------------------------------------------------------------
# rung 1
# --------------------------------------------------------------------------

def rung_tests(problems):
    print("[1/3] suite")
    r = sh([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"])
    if r.returncode == 5:
        # pytest's own exit code for "collected nothing".  Named separately
        # because a gate that reads it as green is a gate that never ran.
        fail(problems, "RED(no-tests-collected): pytest exit 5 -- testpaths in "
                       "pytest.ini collected nothing.  A check that could not "
                       "run is a broken gate, not a passing one")
        return
    if r.returncode != 0:
        fail(problems, "RED(suite): exit %d\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return
    print("   ok    %s" % (r.stdout.strip().splitlines() or ["(no output)"])[-1])


# --------------------------------------------------------------------------
# rung 2
# --------------------------------------------------------------------------

def rung_real_run(problems, started_at):
    print("[2/3] one real run -- python -m pipeline.run_a0, offline, IN TREE")
    r = sh([sys.executable, "-m", "pipeline.run_a0"])
    if r.returncode != 0:
        # Checked, and reported -- but see `lean_verdict`: run_a0's own exit
        # code is not sufficient evidence of a pass, so rung 3 re-derives the
        # verdict from the report rather than trusting this number.
        fail(problems, "RED(pipeline): run_a0 exited %d\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return False, r

    missing = [p for p in REQUIRED_FILES if not os.path.exists(p)]
    if missing:
        fail(problems, "RED(pipeline): run_a0 exited 0 but did not write %s"
             % ", ".join(os.path.relpath(p, HERE) for p in missing))
        return False, r

    stale = [os.path.relpath(p, HERE) for p in REQUIRED_FILES
             if os.path.getmtime(p) < started_at - 2.0]
    if stale:
        fail(problems, "RED(stale-artefact): %s predate this run -- the gate "
                       "would be grading a committed leftover, not a run"
             % ", ".join(stale))
        return False, r

    print("   ok    wrote %d artefacts, all newer than the run's start"
          % len(REQUIRED_FILES))
    return True, r


# --------------------------------------------------------------------------
# rung 3
# --------------------------------------------------------------------------

def lean_verdict(problems, report):
    """Report Lean by name.  Returns "green", "absent" or "red".

    The one thing this function may never do is let absence read as a pass.
    """
    lean = need(problems, report, "lean", "a0_report")
    cross = need(problems, report, "lean_cross_form", "a0_report")
    if lean is None or cross is None:
        return "red"
    if "available" not in lean:
        fail(problems, "a0_report.lean has no 'available' field; refusing to "
                       "guess what a missing availability flag means")
        return "red"

    if lean["available"] is not True:
        print("   LEAN  ABSENT -- skipped because the toolchain is not here "
              "(%s)." % lean.get("skipped", "no reason recorded"))
        print("         This is NOT a pass.  The proof form was not checked, "
              "so nothing about it is known.")
        return "absent"

    ok = True
    ok &= must_be_true(problems, lean, "compiles", "a0_report.lean")
    uses_sorry = need(problems, lean, "uses_sorry", "a0_report.lean")
    if uses_sorry is not False:
        fail(problems, "a0_report.lean.uses_sorry is %r; a proof with `sorry` "
                       "in it is not a proof" % (uses_sorry,))
        ok = False
    theorems = need(problems, lean, "theorems", "a0_report.lean")
    if not isinstance(theorems, list) or not theorems:
        fail(problems, "a0_report.lean.theorems is %r -- a Lean file that "
                       "proves nothing compiles very reliably" % (theorems,))
        ok = False

    ok &= must_be_true(problems, cross, "forms_agree", "a0_report.lean_cross_form")
    cases = need(problems, cross, "cases", "a0_report.lean_cross_form")
    if cases is not None:
        ok &= at_least(problems, cases, MIN_LEAN_CROSS_CASES,
                       "a0_report.lean_cross_form.cases")
    n_mismatch = need(problems, cross, "n_mismatches", "a0_report.lean_cross_form")
    if n_mismatch != 0:
        fail(problems, "a0_report.lean_cross_form.n_mismatches is %r; the Lean "
                       "form and the Python form disagree" % (n_mismatch,))
        ok = False

    if ok:
        print("   LEAN  PRESENT and green -- %s, %d cross-form cases agree"
              % (lean.get("lean", "(path not recorded)"), cases or 0))
    return "green" if ok else "red"


def note_known_defect():
    """Name the vacuous-truth hole in run_a0's own verdict, out loud.

    Static and read-only.  It is a note, not a rung: making the gate
    permanently RED over a defect in the code it guards would just mean nobody
    runs the gate.  What actually defends against the hole is that rung 3
    re-derives the verdict here instead of trusting run_a0's exit code.
    """
    try:
        with open(RUN_A0_SOURCE, encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        print("   note  could not read run_a0.py to check for the known "
              "defect (%s)" % exc)
        return
    if 'not report["lean"].get("available")' in source:
        print("   note  KNOWN DEFECT still present -- run_a0.py's own `ok` "
              "expression contains `not report[\"lean\"].get(\"available\") "
              "or ...`, so on a machine without Lean it exits 0 having "
              "checked no proof at all.  This gate does not inherit that: "
              "see the LEAN block above.")
    else:
        print("   note  run_a0.py no longer contains the vacuous "
              "`not ...get(\"available\") or` disjunct -- the known defect "
              "appears to have been fixed upstream.")


def rung_artifact_fields(problems, report):
    print("[3/3] artefact self-check -- artifacts/a0_report.json")

    missing = [f for f in REQUIRED_TOP_LEVEL if f not in report]
    if missing:
        fail(problems, "a0_report is missing top-level %s" % ", ".join(missing))
        return "red"

    explore = report["explore"]
    levels_used = need(problems, explore, "levels", "a0_report.explore")
    if isinstance(levels_used, list):
        at_least(problems, len(levels_used), MIN_EVIDENCE_LEVELS,
                 "a0_report.explore.levels (evidence levels pooled)")
    else:
        fail(problems, "a0_report.explore.levels is %r" % (levels_used,))
    at_least(problems, need(problems, explore, "episodes", "a0_report.explore"),
             MIN_EPISODES, "a0_report.explore.episodes")
    at_least(problems, need(problems, explore, "transitions", "a0_report.explore"),
             MIN_TRANSITIONS, "a0_report.explore.transitions")

    at_least(problems, need(problems, report["mine"], "n_rules", "a0_report.mine"),
             MIN_RULES, "a0_report.mine.n_rules")

    certify = report["certify"]
    must_be_true(problems, certify, "replay_exact", "a0_report.certify")
    must_be_true(problems, certify, "exactly_one_successor", "a0_report.certify")
    at_least(problems, need(problems, certify, "transitions", "a0_report.certify"),
             MIN_TRANSITIONS, "a0_report.certify.transitions")

    generated = report["certify_generated"]
    must_be_true(problems, generated, "replay_exact", "a0_report.certify_generated")
    at_least(problems,
             need(problems, generated, "frames_checked", "a0_report.certify_generated"),
             MIN_TRANSITIONS, "a0_report.certify_generated.frames_checked")
    errors = need(problems, generated, "errors", "a0_report.certify_generated")
    if errors:
        fail(problems, "a0_report.certify_generated.errors is non-empty: %r"
             % (errors[:3],))

    held = report["held_out"]
    # Order matters: the floor is checked BEFORE `exact`, because `exact` is
    # `all(... == 0)` and is True of an empty enumeration.
    at_least(problems, need(problems, held, "total_cases", "a0_report.held_out"),
             MIN_HELD_OUT_CASES, "a0_report.held_out.total_cases")
    mismatches = need(problems, held, "total_mismatches", "a0_report.held_out")
    if mismatches != 0:
        fail(problems, "a0_report.held_out.total_mismatches is %r -- the "
                       "theory and the world disagree on unobserved states"
             % (mismatches,))
    must_be_true(problems, held, "exact", "a0_report.held_out")

    must_be_true(problems, report["prove"], "row_plus_col_is_conserved",
                 "a0_report.prove")

    grading = report["grading"]
    if not isinstance(grading, dict):
        fail(problems, "a0_report.grading is %r" % type(grading).__name__)
    else:
        at_least(problems, len(grading), MIN_LEVELS_GRADED,
                 "a0_report.grading (levels graded)")
        for name in sorted(grading):
            must_be_true(problems, grading[name], "agrees",
                         "a0_report.grading[%r]" % name)
        # The point of the pair: one level must come out solvable and one must
        # not.  Two "unsolvable" verdicts also agree with nothing interesting.
        verdicts = {bool(g.get("predicted_solvable")) for g in grading.values()
                    if "predicted_solvable" in g}
        if verdicts != {True, False}:
            fail(problems, "every graded level has predicted_solvable=%s; the "
                           "territory claims to do both 'solved' and "
                           "'unsolvable with a reason'" % verdicts)

    lean_state = lean_verdict(problems, report)
    note_known_defect()

    if not problems and lean_state == "green":
        print("   ok    %d episodes / %d transitions / %d rules / %d held-out "
              "cases, all %d top-level fields"
              % (explore["episodes"], explore["transitions"],
                 report["mine"]["n_rules"], held["total_cases"],
                 len(REQUIRED_TOP_LEVEL)))
    return lean_state


def main():
    problems = []
    lean_state = "red"
    # Nothing the gate itself needs goes into the tree.  (Rung 2's pipeline is
    # a different matter -- see the module docstring.)
    scratch = tempfile.mkdtemp(prefix="a0-spike-verify-")
    started_at = time.time()
    try:
        rung_tests(problems)
        ran, _ = rung_real_run(problems, started_at)
        if ran:
            try:
                with open(REPORT, encoding="utf-8") as fh:
                    report = json.load(fh)
            except (OSError, json.JSONDecodeError) as exc:
                fail(problems, "RED(unreadable-artefact): %s" % exc)
                report = None
            if report is not None:
                lean_state = rung_artifact_fields(problems, report)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    print("   note  rung 2 wrote into the working tree: a0-spike/artifacts/ "
          "(a0_report.json, theory_exec.py, pddl/).  run_a0 takes no out-dir; "
          "this gate does not restore them for you.")
    if problems:
        print("a0-spike: RED (%d problem(s))" % len(problems))
        return 1
    if lean_state == "absent":
        print("a0-spike: INCOMPLETE -- suite and pipeline green, but the Lean "
              "toolchain is absent so the proof form was never checked.")
        print("          Exit 2, deliberately: 'not checked' is not 'passed'.")
        return 2
    print("a0-spike: green -- suite, one real run, artefact fields, Lean by name")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
