"""cold-start-a3's completion gate.

    cd cold-start-a3 && python verify.py

Three rungs, and the territory is finished only if all three are green:

  1. the suite passes;
  2. the real pipeline runs once, offline -- `python run_all.py`, seven stages
     across five arms;
  3. the artefacts those stages claim to produce have the fields they claim to
     have, and their counts clear an explicit floor.

-----------------------------------------------------------------------------
THE DEFECT THIS GATE IS SHAPED AROUND: run_all.py CANNOT FAIL
-----------------------------------------------------------------------------

`run_all.py:122-123` ends

        print("done in %.1fs" % (time.time() - start))
        return 0

There is no failure accumulator anywhere in that file -- compare
`cold-start-a2/run_all.py:105`, which collects failures and returns 1.  A3's
driver returns 0 on every path it can reach.  Worse, `run_all.py:67-73` prints

        SKIPPED — domain_l2_scratch.dsl is absent.  The report's like-for-like
        column cannot be produced without it.

and continues.  The control arm is the whole comparison; without it the
"transfer is cheaper" claim has nothing to be cheaper *than*, and the run still
exits 0.

So **this gate never treats `run_all.py` exit 0 as success.**  It checks the
returncode (a crash still matters and is still named), and then establishes the
run three other ways:

  * **SKIPPED detection.**  stdout is scanned for `SKIPPED`.  Any occurrence is
    RED(stage-skipped) with the offending line quoted.
  * **freshness.**  Every required artefact must have an mtime later than the
    moment rung 2 started.  This is the check that matters most here: a skipped
    stage leaves last run's `bill_l2_from_scratch.json` on disk, `bill.build()`
    picks it up from disk, and `like_for_like_level_2` comes out fully
    populated from stale numbers.  Content alone cannot tell you that happened.
  * **the arms roster.**  `bill_table.arms` must contain all three arms, and
    `like_for_like_level_2` must not be null -- `bill.py:69` sets it to `None`
    exactly when the control arm's bill is missing.

-----------------------------------------------------------------------------
LIMITATION, stated up front rather than buried: THIS GATE'S RUNG 2 WRITES INTO
THE WORKING TREE.
-----------------------------------------------------------------------------

`engine-rig/verify.py` -- the exemplar -- runs its pipeline into a
`tempfile.mkdtemp()`, because `tools.run_all` takes `--out`.  **`run_all.py`
here takes no arguments at all.**  The output directory is fixed in
`_bootstrap.artifacts_dir()`:

    HERE = os.path.dirname(os.path.abspath(__file__))
    def artifacts_dir(): return os.path.join(HERE, "artifacts")

`HERE` comes from `__file__`; there is no argument, no environment variable and
no seam.  Copying the territory into a temp directory does not work either:
`_bootstrap.py` computes `REPO = dirname(HERE)` and puts `<REPO>/engine-rig`,
`<REPO>/theory-compiler/src` and `<REPO>/cold-start-a0` on `sys.path`, so a
relocated copy cannot import the engines, the parser or A0's compile backends,
and the run stops being the real run.

So rung 2 runs the pipeline in place: **running this gate dirties
`cold-start-a3/artifacts/` and `cold-start-a3/theory/generated_*/`.**  The gate
does not snapshot-and-restore them -- restoring files behind the user's back is
how a checker becomes a thing that loses work.  The gate itself writes nothing
into the tree (`tempfile.mkdtemp()` for its own scratch; pytest runs with
`-p no:cacheprovider`), and it prints a reminder at the end.
`git checkout -- cold-start-a3` is yours to run, deliberately.

-----------------------------------------------------------------------------
FLOORS -- an empty result is not a pass
-----------------------------------------------------------------------------

Every count below has a floor with a reason.  A3's headline is a *ratio*, and
ratios are the easiest number in the repo to fake by accident: `0 / 0` is
guarded to `None` in `bill.py`, but `transfer=0, scratch=0` reads as "infinite
saving" to a careless reader and as a completely untouched experiment to
anyone who looks.  The floors are on the denominators.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ARTIFACTS = os.path.join(HERE, "artifacts")

# The frozen contract's required fields (CONTRACTS/candidates_schema.md v0.1).
CANDIDATE_FIELDS = ("engine", "evidence", "id", "kind", "payload", "status",
                    "timestamp")

# Top-level fields each artefact claims.  Presence-checked, never defaulted.
REQUIRED_FIELDS = {
    "bill_table.json": ("arms", "cost_to_first_plan", "like_for_like_level_2",
                        "note", "table"),
    "bill_l2_transfer.json": ("arm", "carries_books", "cost_to_first_plan",
                              "counts", "events", "level", "note"),
    "bill_l1_cold_start.json": ("arm", "carries_books", "cost_to_first_plan",
                                "counts", "events", "level", "note"),
    "bill_l2_from_scratch.json": ("arm", "carries_books",
                                  "cost_to_first_plan", "counts", "events",
                                  "level", "note"),
    "negative_controls.json": ("all_caught", "controls",
                               "none_claimed_a_win"),
    "score_vs_truth.json": ("results",),
}

# Every file the seven stages claim to write.  All must be newer than the run.
# This list is the SKIPPED detector's second line of defence: `bill_*.json` for
# the control arm is here precisely because a skipped stage leaves the previous
# run's copy in place and everything downstream reads it happily.
REQUIRED_ARTEFACTS = tuple(REQUIRED_FIELDS) + (
    "bill_table.md", "candidates_l1.jsonl", "candidates_l2_scratch.jsonl",
    "arm_l1_cold_start.json", "arm_l2_from_scratch.json",
    "arm_l2_transfer.json", "arm_l2neg.json", "arm_l2rew.json",
    "engines_report_l1.json", "engines_report_l2_scratch.json",
    "ground_truth.json", "l1_sweep.jsonl", "l2_sweep.jsonl",
    "concept_accounts.json", "upstream_pin.json",
)

# The three arms the comparison is made of.  Two of them is not a comparison.
REQUIRED_ARMS = ("l1_cold_start", "l2_from_scratch", "l2_transfer")

# The meter lines every bill must carry.  `counts[line]` is read directly by
# `bill.compare`, so a missing line is a KeyError there and a silent zero here
# if anyone reaches for `.get`.
METER_LINES = ("world_frames", "world_actions", "engine_stages",
               "candidates_adjudicated", "theorize_rounds",
               "dsl_clauses_written", "compile_runs", "certify_runs",
               "plan_runs")

# --- floors ----------------------------------------------------------------
# 41 candidates from 3 engines observed on level 1; 35 on the level-2 control.
# A stream of three means something stopped proposing and said nothing.
MIN_CANDIDATES_L1 = 20
MIN_CANDIDATES_L2_SCRATCH = 15
MIN_ENGINES = 3
# 348 and 347 frames observed for the two cold-start arms.  This is the
# denominator of the headline ratio: if the from-scratch arm costs 0 frames,
# "transfer saves 97%" is arithmetic on nothing.
MIN_SCRATCH_FRAMES = 100
MIN_SCRATCH_ACTIONS = 100
# 33 clauses written from scratch for level 2, 23 for level 1.  A control arm
# that wrote no manual did not do the work the transfer arm is being spared.
MIN_SCRATCH_CLAUSES = 10
# The transfer arm carries the books, so most of its lines are legitimately 0.
# What it may not be is *inert*: it must observe the level, plan, and execute.
# 11 frames / 10 actions observed; a plan of length 0 is not a plan.
MIN_TRANSFER_FRAMES = 2
MIN_TRANSFER_ACTIONS = 1
# 8 events observed on the transfer bill.  `events` is the audit trail behind
# `counts`; an empty trail means the counts were asserted, not metered.
MIN_EVENTS = 5
# Five arms are metered, three of them appear in the table, and two negative
# controls exist to catch a manual that is wrong.  Zero controls means the
# safety valve was removed.
MIN_NEGATIVE_CONTROLS = 2
# Nine meter lines and three arms: 9 rows in the table.
MIN_TABLE_ROWS = 9
# Every reachable pair is scored against the referee for each theory/level
# pairing; the committed run reports several.  Zero rows means nothing was
# scored and `accuracy` is a statement about no data.
MIN_SCORE_ROWS = 3
MIN_PAIRS_CHECKED = 50


def sh(argv, cwd=HERE, env=None):
    """Run a stage, decoding as UTF-8 rather than as the host locale.

    `text=True` alone decodes with cp936 on this box; a child printing UTF-8
    then either mojibakes or raises UnicodeDecodeError inside subprocess.run,
    and a checker that dies decoding its child is a checker that did not check.
    That matters more here than usual: the SKIPPED line this gate hunts for
    sits in the middle of stdout, alongside CJK prose from the bill table.
    """
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


def fail(problems, message):
    print("   FAIL  %s" % message)
    problems.append(message)


def need(problems, mapping, key, where):
    """Fetch a required field, or fail.  Never defaults.

    `mapping.get(key, <the number I was hoping for>)` is the single most common
    way a gate in this repo has passed a run in which the field disappeared, so
    the helper that could do it does not exist.
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
        # cold-start-a3's pytest.ini has testpaths but no addopts, so this is
        # the one territory where a stray -k or a renamed tests/ would land
        # here rather than in a red assertion.
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
    print("[2/3] one real run -- python run_all.py, five arms, offline, IN TREE")
    print("   ...   NOTE: run_all.py returns 0 unconditionally (run_all.py:123)"
          ".  Its exit code is checked but proves nothing; what follows does "
          "the work.")
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    r = sh([sys.executable, "run_all.py"], env=env)
    out = r.stdout + r.stderr

    if r.returncode != 0:
        # It has no non-zero path, so a non-zero code here means it crashed
        # outright -- worth naming, but its absence means nothing.
        fail(problems, "RED(pipeline): run_all.py exited %d, which it has no "
                       "code path to do deliberately -- it crashed\n%s"
             % (r.returncode, out[-3000:]))
        return False

    # SKIPPED detection.  run_all.py:67-73 and coldstart.py:249-252 both print
    # this and continue; the control arm dropping out is invisible in the exit
    # code and nearly invisible in the artefacts.
    skipped = [line.strip() for line in out.splitlines() if "SKIPPED" in line]
    if skipped:
        fail(problems, "RED(stage-skipped): run_all printed %d SKIPPED line(s) "
                       "and exited 0 anyway:\n        %s"
             % (len(skipped), "\n        ".join(skipped[:4])))
        return False

    # Traceback detection.  Stages are called in-process here, not as
    # subprocesses, so an exception inside one would propagate -- but a stage
    # that catches and prints is indistinguishable from one that worked.
    if "Traceback (most recent call last)" in out:
        fail(problems, "RED(pipeline): a traceback was printed during the run "
                       "and run_all exited 0 anyway\n%s" % out[-2000:])
        return False

    if "done in " not in out:
        fail(problems, "RED(pipeline): run_all exited 0 without reaching its "
                       "final 'done in' line -- it did not finish\n%s"
             % out[-2000:])
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
        # The important one.  A skipped arm leaves the previous run's bill on
        # disk; `bill.load_bills` reads whatever is there, and the table comes
        # out fully populated from numbers this run did not produce.
        fail(problems, "RED(stale-artefact): %s predate this run -- an arm was "
                       "skipped or a stage exited without writing, and the "
                       "bill would be built from a previous run's numbers"
             % ", ".join(stale))
        return False

    print("   ok    no SKIPPED, no traceback, reached 'done in'; %d artefacts, "
          "all newer than the run's start" % len(REQUIRED_ARTEFACTS))
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


def check_bill(problems, name, bill, expect_arm, carries_books):
    """A bill's counts and its audit trail, checked against each other."""
    if bill is None:
        return None
    arm = need(problems, bill, "arm", name)
    if arm != expect_arm:
        fail(problems, "artifacts/%s has arm %r, expected %r"
             % (name, arm, expect_arm))
    books = need(problems, bill, "carries_books", name)
    if books is not carries_books:
        fail(problems, "artifacts/%s.carries_books is %r, expected %r -- the "
                       "arm's whole identity is whether it carried the books"
             % (name, books, carries_books))

    counts = need(problems, bill, "counts", name)
    if not isinstance(counts, dict):
        fail(problems, "artifacts/%s.counts is %r" % (name, counts))
        return None
    for line in METER_LINES:
        if line not in counts:
            fail(problems, "artifacts/%s.counts is missing the meter line %r"
                 % (name, line))

    events = need(problems, bill, "events", name)
    if not isinstance(events, list):
        fail(problems, "artifacts/%s.events is %r" % (name, events))
    else:
        at_least(problems, len(events), MIN_EVENTS, "artifacts/%s.events" % name)
        for i, event in enumerate(events):
            for field in ("amount", "line", "running_total", "seq", "why"):
                if field not in event:
                    fail(problems, "artifacts/%s.events[%d] is missing %r"
                         % (name, i, field))
                    break
            else:
                if not str(event["why"]).strip():
                    fail(problems, "artifacts/%s.events[%d] charges %r with no "
                                   "reason; an unexplained charge is not a "
                                   "meter reading" % (name, i, event["line"]))
    return counts


def rung_artifact_fields(problems):
    print("[3/3] artefact self-check")

    payloads = {}
    for name in REQUIRED_FIELDS:
        payloads[name] = load_json(problems, name)
        check_fields(problems, name, payloads[name])

    scratch = check_bill(problems, "bill_l2_from_scratch.json",
                         payloads["bill_l2_from_scratch.json"],
                         "l2_from_scratch", False)
    transfer = check_bill(problems, "bill_l2_transfer.json",
                          payloads["bill_l2_transfer.json"],
                          "l2_transfer", True)
    check_bill(problems, "bill_l1_cold_start.json",
               payloads["bill_l1_cold_start.json"], "l1_cold_start", False)

    # --- the denominators -------------------------------------------------
    # A3's claim is a ratio.  Floors go on the control arm, because a control
    # arm that cost nothing makes every saving look total.
    if scratch:
        at_least(problems, scratch.get("world_frames"), MIN_SCRATCH_FRAMES,
                 "bill_l2_from_scratch.counts.world_frames")
        at_least(problems, scratch.get("world_actions"), MIN_SCRATCH_ACTIONS,
                 "bill_l2_from_scratch.counts.world_actions")
        at_least(problems, scratch.get("dsl_clauses_written"),
                 MIN_SCRATCH_CLAUSES,
                 "bill_l2_from_scratch.counts.dsl_clauses_written")
        at_least(problems, scratch.get("candidates_adjudicated"),
                 MIN_CANDIDATES_L2_SCRATCH,
                 "bill_l2_from_scratch.counts.candidates_adjudicated")

    # --- the numerator ----------------------------------------------------
    # The transfer arm carries the books, so most lines are legitimately 0.
    # What it may not be is inert: an arm that observed nothing and executed
    # nothing "saves" 100% of everything and demonstrates nothing.
    if transfer:
        at_least(problems, transfer.get("world_frames"), MIN_TRANSFER_FRAMES,
                 "bill_l2_transfer.counts.world_frames")
        at_least(problems, transfer.get("world_actions"), MIN_TRANSFER_ACTIONS,
                 "bill_l2_transfer.counts.world_actions")
        at_least(problems, transfer.get("plan_runs"), 1,
                 "bill_l2_transfer.counts.plan_runs")

    # --- the table --------------------------------------------------------
    table = payloads["bill_table.json"]
    if table:
        arms = need(problems, table, "arms", "bill_table")
        names = [a.get("arm") for a in arms] if isinstance(arms, list) else []
        for wanted in REQUIRED_ARMS:
            if wanted not in names:
                fail(problems, "bill_table.arms is missing %r (has %s) -- the "
                               "comparison needs all three arms and this is "
                               "what a skipped stage looks like from here"
                     % (wanted, ", ".join(map(str, names)) or "nothing"))

        rows = need(problems, table, "table", "bill_table")
        if isinstance(rows, list):
            at_least(problems, len(rows), MIN_TABLE_ROWS, "bill_table.table")

        # `bill.py:69` sets this to None exactly when the control arm's bill is
        # absent -- i.e. exactly when the control stage was SKIPPED.  Checking
        # it here is cheap and it is the artefact-side witness of the defect.
        lfl = need(problems, table, "like_for_like_level_2", "bill_table")
        if lfl is None:
            fail(problems, "bill_table.like_for_like_level_2 is null -- "
                           "bill.py sets it to None when the l2_from_scratch "
                           "bill is missing, which means the control arm did "
                           "not run.  Without it there is no like-for-like "
                           "comparison and C3's claim is unsupported")
        elif isinstance(lfl, dict):
            for line in METER_LINES:
                if line not in lfl:
                    fail(problems, "bill_table.like_for_like_level_2 is "
                                   "missing the meter line %r" % line)
            # The claim itself.  If carrying the books saves nothing on the
            # lines the report leads with, the experiment came out negative --
            # which is a legitimate finding, but not a green gate, because it
            # would mean the committed A3_REPORT.md no longer describes the run.
            for line in ("world_actions", "dsl_clauses_written"):
                entry = lfl.get(line)
                if not isinstance(entry, dict) or "saved" not in entry:
                    fail(problems, "bill_table.like_for_like_level_2[%r] is %r"
                         % (line, entry))
                elif not isinstance(entry["saved"], int) or entry["saved"] <= 0:
                    fail(problems, "bill_table.like_for_like_level_2[%r].saved "
                                   "is %r -- carrying the books saved nothing "
                                   "on this line, so A3's C3 claim is not what "
                                   "this run shows" % (line, entry["saved"]))

    # --- the safety valve -------------------------------------------------
    negctl = payloads["negative_controls.json"]
    if negctl:
        controls = need(problems, negctl, "controls", "negative_controls")
        if not isinstance(controls, list):
            fail(problems, "negative_controls.controls is %r" % (controls,))
        else:
            at_least(problems, len(controls), MIN_NEGATIVE_CONTROLS,
                     "negative_controls.controls")
            for i, row in enumerate(controls):
                if "caught" not in row:
                    fail(problems, "negative_controls.controls[%d] has no "
                                   "'caught' field" % i)
                elif row["caught"] is not True:
                    fail(problems, "negative_controls.controls[%d] (%s) was "
                                   "not caught -- a wrong manual passed"
                         % (i, row.get("arm")))
        # Floors first, verdicts second: both of these are `all(...)` over
        # `controls` and are vacuously True of an empty list.
        must_be_true(problems, negctl, "all_caught", "negative_controls")
        must_be_true(problems, negctl, "none_claimed_a_win",
                     "negative_controls")

    # --- the referee ------------------------------------------------------
    score = payloads["score_vs_truth.json"]
    if score:
        results = need(problems, score, "results", "score_vs_truth")
        if not isinstance(results, list):
            fail(problems, "score_vs_truth.results is %r" % (results,))
        else:
            at_least(problems, len(results), MIN_SCORE_ROWS,
                     "score_vs_truth.results")
            for i, row in enumerate(results):
                for field in ("accuracy", "level", "pairs_checked",
                              "pairs_correct", "theory"):
                    if field not in row:
                        fail(problems, "score_vs_truth.results[%d] is missing "
                                       "%r" % (i, field))
                        break
                else:
                    # `accuracy` of 1.0 over 0 pairs is the same float as
                    # `accuracy` of 1.0 over 4000.
                    at_least(problems, row["pairs_checked"], MIN_PAIRS_CHECKED,
                             "score_vs_truth.results[%d].pairs_checked" % i)

    # --- the frozen contract ----------------------------------------------
    for name, floor in (("candidates_l1.jsonl", MIN_CANDIDATES_L1),
                        ("candidates_l2_scratch.jsonl",
                         MIN_CANDIDATES_L2_SCRATCH)):
        records = load_jsonl(problems, name)
        if records is None:
            continue
        if not at_least(problems, len(records), floor,
                        "artifacts/%s rows" % name):
            continue
        for i, rec in enumerate(records):
            missing = [f for f in CANDIDATE_FIELDS if f not in rec]
            if missing:
                # Deliberately not `rec.get(f, <what we want>)`.  A gate that
                # defaults a missing field to the value it hopes for passes a
                # run in which the field silently disappeared.
                fail(problems, "artifacts/%s record %d is missing %s"
                     % (name, i, ", ".join(missing)))
                break
            if rec["status"] != "candidate":
                fail(problems, "artifacts/%s record %d has status %r; engines "
                               "never adjudicate "
                               "(CONTRACTS/candidates_schema.md)"
                     % (name, i, rec["status"]))
                break
        engines = {r.get("engine") for r in records}
        at_least(problems, len(engines), MIN_ENGINES,
                 "artifacts/%s distinct engines (%s)"
                 % (name, ", ".join(sorted(map(str, engines)))))

    validate = sh([sys.executable, "-m", "tools.validate_candidates",
                   os.path.join(ARTIFACTS, "candidates_l1.jsonl"),
                   os.path.join(ARTIFACTS, "candidates_l2_scratch.jsonl")],
                  cwd=os.path.join(REPO, "engine-rig"))
    if validate.returncode != 0:
        fail(problems, "RED(contract): the streams fail the frozen contract\n%s"
             % (validate.stdout + validate.stderr)[-2000:])

    if not problems:
        lfl = payloads["bill_table.json"]["like_for_like_level_2"]
        print("   ok    three arms metered, control arm real (%d frames, %d "
              "clauses), like-for-like saves %d actions and %d clauses"
              % (scratch["world_frames"], scratch["dsl_clauses_written"],
                 lfl["world_actions"]["saved"],
                 lfl["dsl_clauses_written"]["saved"]))


def main():
    problems = []
    # Nothing the gate itself needs goes into the tree.  (Rung 2's pipeline is
    # a different matter -- see the module docstring.)
    scratch = tempfile.mkdtemp(prefix="cold-start-a3-verify-")
    started_at = time.time()
    try:
        rung_tests(problems)
        if rung_real_run(problems, started_at):
            rung_artifact_fields(problems)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    print("   note  rung 2 wrote into the working tree: cold-start-a3/"
          "artifacts/ and theory/generated_*/.  run_all.py takes no out-dir; "
          "this gate does not restore them for you.")
    print("   note  run_all.py returns 0 on every path it has (run_all.py:123) "
          "and prints SKIPPED rather than failing when a fixture is absent "
          "(run_all.py:67-73).  This gate's verdict is built from the "
          "artefacts and from stdout, not from that exit code.")
    if problems:
        print("cold-start-a3: RED (%d problem(s))" % len(problems))
        return 1
    print("cold-start-a3: green -- suite, one real run with no skipped stage, "
          "artefact fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
