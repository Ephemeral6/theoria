"""cold-start-a0's completion gate.

    cd cold-start-a0 && python verify.py

Three rungs, and the territory is finished only if all three are green:

  1. the suite passes;
  2. the real pipeline runs once, offline -- `python run_all.py`, nine stages
     plus the frozen-contract validation;
  3. the artefacts those stages claim to produce have the fields they claim to
     have, and their counts clear an explicit floor.

Rung 3 is the one that is usually missing.  `run_all.py` checks every stage's
returncode -- it is the best-behaved driver of the four cold starts -- but a
stage that exits 0 having written nothing at all still reads as green, because
nothing downstream ever opens the file it was supposed to write.

-----------------------------------------------------------------------------
LIMITATION, stated up front rather than buried: THIS GATE'S RUNG 2 WRITES INTO
THE WORKING TREE.
-----------------------------------------------------------------------------

`engine-rig/verify.py` -- the exemplar -- runs its pipeline into a
`tempfile.mkdtemp()`, because `tools.run_all` takes `--out`.  **`run_all.py`
here takes no arguments at all**, and neither does any of the nine stages it
drives.  The output directory is fixed in `_bootstrap.artifacts_dir()`:

    HERE = os.path.dirname(os.path.abspath(__file__))
    def artifacts_dir(): return os.path.join(HERE, "artifacts")

`HERE` comes from `__file__`, so there is no argument, no environment variable
and no seam to redirect.  Copying the territory into a temp directory does not
work either: `_bootstrap.py` computes `REPO = dirname(HERE)` and puts
`<REPO>/engine-rig` and `<REPO>/theory-compiler/src` on `sys.path`, so a
relocated copy cannot import the engines or the parser and the run stops being
the real run.

So rung 2 runs the pipeline in place, and this gate says so plainly: **running
it dirties `cold-start-a0/artifacts/` and `cold-start-a0/theory/generated*/`.**
The gate does not snapshot-and-restore them -- restoring files behind the
user's back is how a checker becomes a thing that loses work, and this
directory belongs to the theory-compiler track, which makes silently rewriting
its files worse, not better.  The gate itself writes nothing into the tree
(`tempfile.mkdtemp()` for its own scratch; pytest runs with
`-p no:cacheprovider`), and it prints a reminder at the end.  If you want a
clean tree afterwards, `git checkout -- cold-start-a0` is yours to run,
deliberately.

Compensation: because the artefacts live in the tree and may be left over from
an earlier run, rung 3 refuses to read a stale file.  Every artefact must have
an mtime later than the moment rung 2 started.  A gate that grades a committed
leftover is not grading a run.

-----------------------------------------------------------------------------
WHAT THIS TERRITORY GETS RIGHT, and is checked here anyway
-----------------------------------------------------------------------------

`certify/lean_check.py:52-58` returns `available: False` **and `green: False`**
when no toolchain is found, and `main` exits 1 on it.  That is the correct
shape and the opposite of `a0-spike/pipeline/run_a0.py`, whose verdict contains
`not report["lean"].get("available") or ...` and therefore treats "could not
install Lean" as "Lean passed".  This gate still reports Lean's availability by
name, so the distinction is visible rather than inferred from an exit code.

`run_all.py:50-61` pins the children's output encoding and decodes explicitly,
which is why a failing stage's tail survives on a cp936 console.  This gate
does the same for its own children.

-----------------------------------------------------------------------------
FLOORS -- an empty result is not a pass
-----------------------------------------------------------------------------

Every count below has a floor with a reason.  `green: true` over zero frames,
zero pixels and zero transitions is the same JSON as `green: true` over the
real thing, and only the floors tell them apart.
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

# The frozen contract's required fields (CONTRACTS/candidates_schema.md v0.1).
CANDIDATE_FIELDS = ("engine", "evidence", "id", "kind", "payload", "status",
                    "timestamp")

# Top-level fields each artefact claims.  Presence-checked, never defaulted.
REQUIRED_FIELDS = {
    "engines_report.json": ("board", "frames", "mining", "probes",
                            "segmentation", "trace", "transitions",
                            "zero_space"),
    "certify_cheap_raw_trace.json": ("anomalies", "anomaly_kinds", "frames",
                                     "green", "pixels_checked",
                                     "pixels_unexplained", "theory", "trace",
                                     "transitions"),
    "certify_lean_generated_theory_lean.json": ("available", "axiom_reports",
                                                "errors", "file", "green",
                                                "returncode", "sorries"),
    "plan_generated.json": ("actions", "backend", "execution_mismatches",
                            "green", "length", "manual_reaches_goal",
                            "problem", "status", "world_reaches_goal"),
    "unsolvable_report.json": ("certify_cheap", "certify_lean", "compiled",
                               "constructive_ground", "green", "plan",
                               "theorem", "variant", "zero_space"),
    "trace_summary.json": ("a0-base", "a0-no-button"),
}

# Every file the nine stages claim to write.  All of them must be newer than
# the run; a stage that exits 0 and writes nothing is caught here and nowhere
# else in the territory.
REQUIRED_ARTEFACTS = tuple(REQUIRED_FIELDS) + (
    "candidates.jsonl", "candidates_no_button.jsonl", "raw_trace.jsonl",
    "raw_trace_no_button.jsonl", "plan_generated_no_button.json",
    "problem_a0-base.json", "ground_truth.json",
)

# --- floors ----------------------------------------------------------------
# run_all.py drives nine stages and then the schema validation: ten lines of
# "[ok ]".  Fewer means the STEPS list lost an entry, which no returncode can
# report because the stage that vanished never ran to have a returncode.
MIN_OK_STAGES = 10
# 29 candidates from 4 engines observed on the base world.  A stream of three
# means something stopped proposing and said nothing about it.
MIN_CANDIDATES = 20
MIN_ENGINES = 3
# 13 observed on the button-less variant -- a smaller world, so a smaller
# floor, but a variant that proposes nothing is not a variant.
MIN_VARIANT_CANDIDATES = 5
# 276 frames / 275 transitions observed.  `certify_cheap.green` is "no
# anomalies found", which is trivially true of a trace with no frames in it.
MIN_FRAMES = 100
MIN_TRANSITIONS = 100
# 22356 pixels checked observed.  This is the floor that matters most here:
# "pixels_unexplained: 0" is the headline number and it is 0 for an empty
# check exactly as it is for a perfect one.
MIN_PIXELS_CHECKED = 1000
# The base level needs the Cart driven to the Button and then through the Door;
# the committed plan is 12 actions.  A plan of 0 actions means the start state
# was already the goal, which is not a demonstration of planning.
MIN_PLAN_LENGTH = 5
# Lean must actually prove something.  A .lean file with no theorems in it
# compiles very reliably.
MIN_THEOREMS = 1


def sh(argv, cwd=HERE, env=None):
    """Run a stage, decoding as UTF-8 rather than as the host locale.

    `text=True` alone decodes with cp936 on this box; a child printing UTF-8
    then either mojibakes or raises UnicodeDecodeError inside subprocess.run,
    and a checker that dies decoding its child is a checker that did not check.
    This is the same call `run_all.py:50-61` makes and for the same reason.
    """
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


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
    if not isinstance(mapping, dict) or key not in mapping:
        fail(problems, "%s is missing the field %r" % (where, key))
        return False
    value = mapping[key]
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


def load_json(problems, name):
    path = os.path.join(ARTIFACTS, name)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        fail(problems, "RED(unreadable-artefact): artifacts/%s: %s" % (name, exc))
        return None


def load_jsonl(problems, name):
    path = os.path.join(ARTIFACTS, name)
    records = []
    try:
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    fail(problems, "artifacts/%s line %d is not JSON: %s"
                         % (name, n, exc))
    except OSError as exc:
        fail(problems, "RED(unreadable-artefact): artifacts/%s: %s" % (name, exc))
        return None
    return records


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
    print("[2/3] one real run -- python run_all.py, nine stages, offline, IN TREE")
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    r = sh([sys.executable, "run_all.py"], env=env)
    out = r.stdout + r.stderr

    if r.returncode != 0:
        fail(problems, "RED(pipeline): run_all.py exited %d\n%s"
             % (r.returncode, out[-3000:]))
        return False

    # run_all's returncode is trustworthy here (it accumulates failures and
    # returns 1), but its stdout carries information the returncode does not:
    # how many stages actually ran.  A STEPS entry that disappears takes its
    # own returncode with it.
    ok_stages = out.count("[ok ]")
    bad_stages = out.count("[FAIL]")
    if bad_stages:
        fail(problems, "RED(pipeline): run_all exited 0 but printed %d [FAIL] "
                       "line(s) -- the accumulator and the printer disagree"
             % bad_stages)
        return False
    if ok_stages < MIN_OK_STAGES:
        fail(problems, "RED(stage-count): only %d stages reported [ok ], floor "
                       "is %d -- a step vanished from STEPS rather than failing"
             % (ok_stages, MIN_OK_STAGES))
        return False
    if "all steps green" not in out:
        fail(problems, "RED(pipeline): run_all exited 0 without printing "
                       "'all steps green'\n%s" % out[-2000:])
        return False

    missing, stale = [], []
    for name in REQUIRED_ARTEFACTS:
        path = os.path.join(ARTIFACTS, name)
        if not os.path.exists(path):
            missing.append(name)
        elif os.path.getmtime(path) < started_at - 2.0:
            stale.append(name)
    if missing:
        fail(problems, "RED(pipeline): run_all exited 0 but these artefacts "
                       "are absent: %s" % ", ".join(missing))
        return False
    if stale:
        fail(problems, "RED(stale-artefact): %s predate this run -- some stage "
                       "exited 0 without writing, and the gate would be "
                       "grading a committed leftover" % ", ".join(stale))
        return False

    print("   ok    %d stages green; %d artefacts, all newer than the run's "
          "start" % (ok_stages, len(REQUIRED_ARTEFACTS)))
    return True


# --------------------------------------------------------------------------
# rung 3
# --------------------------------------------------------------------------

def check_fields(problems, name, payload):
    if payload is None:
        return False
    missing = [f for f in REQUIRED_FIELDS[name] if f not in payload]
    if missing:
        fail(problems, "artifacts/%s is missing top-level %s"
             % (name, ", ".join(missing)))
        return False
    return True


def check_candidates(problems, name, floor, engine_floor):
    records = load_jsonl(problems, name)
    if records is None:
        return
    if not at_least(problems, len(records), floor, "artifacts/%s rows" % name):
        return
    for i, rec in enumerate(records):
        missing = [f for f in CANDIDATE_FIELDS if f not in rec]
        if missing:
            # Deliberately not `rec.get(f, <what we want>)`.  A gate that
            # defaults a missing field to the value it hopes for passes a run
            # in which the field silently disappeared.
            fail(problems, "artifacts/%s record %d is missing %s"
                 % (name, i, ", ".join(missing)))
            break
        if rec["status"] != "candidate":
            fail(problems, "artifacts/%s record %d has status %r; engines never "
                           "adjudicate (CONTRACTS/candidates_schema.md)"
                 % (name, i, rec["status"]))
            break
    if engine_floor is not None:
        engines = {r.get("engine") for r in records}
        at_least(problems, len(engines), engine_floor,
                 "artifacts/%s distinct engines (%s)"
                 % (name, ", ".join(sorted(map(str, engines)))))


def check_lean(problems, payload, where):
    """Report Lean by name.  Returns "green", "absent" or "red".

    Absence is a distinct, visible state and never a pass.  This territory's
    `lean_check.check` already sets `green: False` when the toolchain is
    missing, so absence would come through as RED anyway -- but "RED because
    the proof failed" and "RED because there is no prover" are different facts
    and a gate that cannot tell them apart wastes the reader's afternoon.
    """
    if payload is None or "available" not in payload:
        fail(problems, "%s has no 'available' field; refusing to guess what a "
                       "missing availability flag means" % where)
        return "red"
    if payload["available"] is not True:
        print("   LEAN  ABSENT -- %s (%s)"
              % (where, payload.get("reason", "no reason recorded")))
        print("         This is NOT a pass.  The proof form was not checked.")
        return "absent"

    ok = must_be_true(problems, payload, "green", where)
    reports = need(problems, payload, "axiom_reports", where)
    if not isinstance(reports, list) or len(reports) < MIN_THEOREMS:
        fail(problems, "%s.axiom_reports is %r -- a Lean file that proves "
                       "nothing compiles very reliably" % (where, reports))
        ok = False
    else:
        for entry in reports:
            if entry.get("axioms"):
                fail(problems, "%s: theorem %r rests on axioms %r"
                     % (where, entry.get("name"), entry["axioms"]))
                ok = False
    if payload.get("sorries"):
        fail(problems, "%s has sorries: %r" % (where, payload["sorries"][:3]))
        ok = False
    if payload.get("errors"):
        fail(problems, "%s has errors: %r" % (where, payload["errors"][:3]))
        ok = False
    if ok:
        print("   LEAN  PRESENT and green -- %s, %d theorem(s), no axioms, no "
              "sorries" % (payload.get("lean", "(path not recorded)"),
                           len(reports)))
    return "green" if ok else "red"


def rung_artifact_fields(problems):
    print("[3/3] artefact self-check")

    payloads = {}
    for name in REQUIRED_FIELDS:
        payloads[name] = load_json(problems, name)
        check_fields(problems, name, payloads[name])

    # --- the base world's evidence ---------------------------------------
    engines_report = payloads["engines_report.json"]
    if engines_report:
        at_least(problems, need(problems, engines_report, "frames",
                                "engines_report"),
                 MIN_FRAMES, "engines_report.frames")
        at_least(problems, need(problems, engines_report, "transitions",
                                "engines_report"),
                 MIN_TRANSITIONS, "engines_report.transitions")
        mining = need(problems, engines_report, "mining", "engines_report")
        if isinstance(mining, dict):
            rules = mining.get("rules")
            if not isinstance(rules, list) or not rules:
                fail(problems, "engines_report.mining.rules is %r -- an engine "
                               "that proposed no rule did not mine" % (rules,))

    # --- the cheap certificate -------------------------------------------
    cheap = payloads["certify_cheap_raw_trace.json"]
    if cheap:
        # Floors first, `green` second: `green` is "no anomalies", which is
        # trivially true of a trace with nothing in it.
        at_least(problems, need(problems, cheap, "pixels_checked",
                                "certify_cheap"),
                 MIN_PIXELS_CHECKED, "certify_cheap.pixels_checked")
        at_least(problems, need(problems, cheap, "frames", "certify_cheap"),
                 MIN_FRAMES, "certify_cheap.frames")
        unexplained = need(problems, cheap, "pixels_unexplained", "certify_cheap")
        if unexplained != 0:
            fail(problems, "certify_cheap.pixels_unexplained is %r -- the "
                           "manual does not account for the trace"
                 % (unexplained,))
        must_be_true(problems, cheap, "green", "certify_cheap")

    # --- the plan ---------------------------------------------------------
    plan = payloads["plan_generated.json"]
    if plan:
        status = need(problems, plan, "status", "plan_generated")
        if status != "SAT":
            fail(problems, "plan_generated.status is %r, expected 'SAT' -- the "
                           "base world is solvable and the planner must say so"
                 % (status,))
        actions = need(problems, plan, "actions", "plan_generated")
        if isinstance(actions, list):
            at_least(problems, len(actions), MIN_PLAN_LENGTH,
                     "plan_generated.actions")
        at_least(problems, need(problems, plan, "length", "plan_generated"),
                 MIN_PLAN_LENGTH, "plan_generated.length")
        must_be_true(problems, plan, "green", "plan_generated")
        must_be_true(problems, plan, "manual_reaches_goal", "plan_generated")
        # The claim that matters: the manual's plan works on the world, not
        # only inside the manual.
        must_be_true(problems, plan, "world_reaches_goal", "plan_generated")
        if plan.get("execution_mismatches"):
            fail(problems, "plan_generated.execution_mismatches is non-empty: %r"
                 % (plan["execution_mismatches"][:3],))

    # --- the unsolvable variant -------------------------------------------
    unsolvable = payloads["unsolvable_report.json"]
    if unsolvable:
        must_be_true(problems, unsolvable, "green", "unsolvable_report")
        inner_plan = need(problems, unsolvable, "plan", "unsolvable_report")
        if isinstance(inner_plan, dict):
            if inner_plan.get("status") == "SAT":
                fail(problems, "unsolvable_report.plan.status is 'SAT' -- the "
                               "button-less variant is supposed to have no plan")
        theorem = need(problems, unsolvable, "theorem", "unsolvable_report")
        if isinstance(theorem, dict) and not theorem.get("explanation"):
            fail(problems, "unsolvable_report.theorem has no explanation; "
                           "refusing the impossible without a reason is the "
                           "whole point of M5")
        ground = need(problems, unsolvable, "constructive_ground",
                      "unsolvable_report")
        if not isinstance(ground, str) or not ground.strip():
            fail(problems, "unsolvable_report.constructive_ground is %r"
                 % (ground,))

    # --- the traces -------------------------------------------------------
    summary = payloads["trace_summary.json"]
    if summary:
        for world in ("a0-base", "a0-no-button"):
            entry = summary.get(world)
            if not isinstance(entry, dict):
                fail(problems, "trace_summary[%r] is %r" % (world, entry))
                continue
            at_least(problems, entry.get("frames"),
                     MIN_FRAMES if world == "a0-base" else 50,
                     "trace_summary[%r].frames" % world)

    # --- the frozen contract ----------------------------------------------
    check_candidates(problems, "candidates.jsonl", MIN_CANDIDATES, MIN_ENGINES)
    check_candidates(problems, "candidates_no_button.jsonl",
                     MIN_VARIANT_CANDIDATES, None)

    validate = sh([sys.executable, "-m", "tools.validate_candidates",
                   os.path.join(ARTIFACTS, "candidates.jsonl"),
                   os.path.join(ARTIFACTS, "candidates_no_button.jsonl")],
                  cwd=os.path.join(os.path.dirname(HERE), "engine-rig"))
    if validate.returncode != 0:
        fail(problems, "RED(contract): the streams fail the frozen contract\n%s"
             % (validate.stdout + validate.stderr)[-2000:])

    # --- the proof form, by name ------------------------------------------
    lean_state = check_lean(problems,
                            payloads["certify_lean_generated_theory_lean.json"],
                            "certify_lean_generated_theory_lean")
    if unsolvable and isinstance(unsolvable.get("certify_lean"), dict):
        variant_state = check_lean(problems, unsolvable["certify_lean"],
                                   "unsolvable_report.certify_lean")
        if variant_state == "absent":
            lean_state = "absent"

    if not problems and lean_state == "green":
        print("   ok    all %d artefacts have their required fields; counts "
              "clear every floor" % len(REQUIRED_FIELDS))
    return lean_state


def main():
    problems = []
    lean_state = "red"
    # Nothing the gate itself needs goes into the tree.  (Rung 2's pipeline is
    # a different matter -- see the module docstring.)
    scratch = tempfile.mkdtemp(prefix="cold-start-a0-verify-")
    started_at = time.time()
    try:
        rung_tests(problems)
        if rung_real_run(problems, started_at):
            lean_state = rung_artifact_fields(problems)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    print("   note  rung 2 wrote into the working tree: cold-start-a0/"
          "artifacts/ and theory/generated*/.  run_all.py takes no out-dir; "
          "this gate does not restore them for you.")
    if problems:
        print("cold-start-a0: RED (%d problem(s))" % len(problems))
        return 1
    if lean_state == "absent":
        print("cold-start-a0: INCOMPLETE -- suite and pipeline green, but the "
              "Lean toolchain is absent so the proof form was never checked.")
        print("               Exit 2, deliberately: 'not checked' is not "
              "'passed'.")
        return 2
    print("cold-start-a0: green -- suite, one real run, artefact fields, "
          "Lean by name")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
