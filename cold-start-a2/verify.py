"""cold-start-a2's completion gate.

    cd cold-start-a2 && python verify.py

Three rungs, and the territory is finished only if all three are green:

  1. the suite passes;
  2. the real pipeline runs once, offline -- `python run_all.py`, thirteen
     stages plus the frozen-contract validation, with the read-only claim
     measured across the run rather than asserted;
  3. the artefacts those stages claim to produce have the fields they claim to
     have, and their counts clear an explicit floor.

Rung 3 is the one that is usually missing.  A green suite says the code does
what its author thought; it does not say the loop closed, and `loop_ledger.json`
carrying `"green": true` says nothing at all if nobody checks that it also
carries eight beats.

-----------------------------------------------------------------------------
LIMITATION, stated up front rather than buried: THIS GATE'S RUNG 2 WRITES INTO
THE WORKING TREE.
-----------------------------------------------------------------------------

`engine-rig/verify.py` -- the exemplar -- runs its pipeline into a
`tempfile.mkdtemp()`, because `tools.run_all` takes `--out`.  **`run_all.py`
here takes no arguments at all**, and neither does any of the thirteen stages
it drives.  The output directory is fixed in `_bootstrap.artifacts_dir()`:

    HERE = os.path.dirname(os.path.abspath(__file__))
    def artifacts_dir(): return os.path.join(HERE, "artifacts")

`HERE` comes from `__file__`; there is no argument, no environment variable and
no seam.  Copying the territory into a temp directory does not work either:
`_bootstrap.py` computes `REPO = dirname(HERE)` and puts `<REPO>/engine-rig`,
`<REPO>/theory-compiler/src` and `<REPO>/cold-start-a0` on `sys.path`, so a
relocated copy cannot import the engines, the parser or A0's compile backends,
and the run stops being the real run.

So rung 2 runs the pipeline in place, and this gate says so plainly: **running
it dirties `cold-start-a2/artifacts/` and `cold-start-a2/theory/generated*/`.**
The gate does not snapshot-and-restore them -- restoring files behind the
user's back is how a checker becomes a thing that loses work.  The gate itself
writes nothing into the tree (`tempfile.mkdtemp()` for its own scratch; pytest
runs with `-p no:cacheprovider`), and it prints a reminder at the end.
`git checkout -- cold-start-a2` is yours to run, deliberately.

Compensation: rung 3 refuses to read a stale file.  Every artefact must have an
mtime later than the moment rung 2 started, so a stage that exits 0 without
writing cannot be covered for by last week's committed copy.

-----------------------------------------------------------------------------
THE READ-ONLY CLAIM, and why this gate hashes rather than shelling out
-----------------------------------------------------------------------------

A2 imports A0's compile backends and certify layer and claims never to write
into that track.  `tools/verify_readonly.py` is the territory's own check of
that claim and it is a good one -- but this gate does not call it, for two
reasons:

* `verify_readonly.py:60-65` runs `run_all.py` itself and then **discards its
  returncode**: it prints `run_all exit: %d` and returns `1 if changed else 0`.
  A run that failed outright but wrote nothing upstream comes out of it as
  exit 0.  That is precisely the silent-pass shape this gate exists to refuse.
* calling it would mean a second full ~17s pipeline run for a fact the gate can
  measure around the run it is already doing.

So the hashing is done here, in-gate, around rung 2's single run: the same four
trees, the same skip list, the same "0 files changed" verdict -- with rung 2's
returncode checked properly.  Nothing is restored; nothing is written.  Hashing
is a measurement, and the only thing this gate does with the result is name it.

Two sessions work this repo concurrently (CLAUDE.md), so a change upstream
during the run may be someone else's.  That makes the read-only result a named
AMBER rather than an unqualified RED -- reported, visible, and never silent.

-----------------------------------------------------------------------------
FLOORS -- an empty result is not a pass
-----------------------------------------------------------------------------

Every count below has a floor with a reason.  `loop_ledger.summary` is
`{"pass": n, "fail": 0, "absent": 0, "total": n}`; with n = 0 that object is
green, complete, and describes a loop that never ran.
"""

import hashlib
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
    "loop_ledger.json": ("authority", "beats", "green", "summary", "traces",
                         "world"),
    "exhibit_report.json": ("certify_cheap", "certify_cheap_vs_full_sweep",
                            "certify_lean", "compiled", "constructive_ground",
                            "evidence", "exhibit_green",
                            "exhibit_is_false_of_the_world", "manual", "plan",
                            "theorem", "world_says", "zero_space"),
    "engines_report.json": ("board", "frames", "mining", "probes",
                            "segmentation", "trace", "transitions",
                            "zero_space"),
}

# Every file the thirteen stages claim to write.  All must be newer than the
# run; a stage that exits 0 and writes nothing is caught here and nowhere else.
REQUIRED_ARTEFACTS = tuple(REQUIRED_FIELDS) + (
    "raw_trace.jsonl", "history_trace.jsonl", "probed_trace.jsonl",
    "probes.jsonl", "solved_episode.jsonl",
    "candidates_history.jsonl", "candidates_probed.jsonl",
    "certify_generated.json", "plan_generated.json",
    "refutation.json", "locate_report.json", "probe_report.json",
    "repair_report.json", "upstream_pin.json", "engines_diff.json",
)

# Candidate streams and their floors.  `candidates.jsonl` is deliberately not
# in this list with a large floor: on the sweep evidence A2 emits a single
# consolidated candidate, and pretending otherwise would make the floor a lie.
CANDIDATE_STREAMS = {
    # 27 and 28 rows observed.  The history and probed streams are where the
    # engines actually propose; a collapse here is the failure worth naming.
    "candidates_history.jsonl": 15,
    "candidates_probed.jsonl": 15,
    # 1 row observed on each of these.  The floor is 1 and it is not
    # decoration: 0 rows means the stage produced nothing and said nothing.
    "candidates.jsonl": 1,
    "candidates_probe.jsonl": 1,
    "candidates_repaired.jsonl": 1,
}

# The trees A2 imports from and must not write into.
READONLY_TREES = ("cold-start-a0", "engine-rig", "theory-compiler", "CONTRACTS")
READONLY_SKIP = {".toolchain", "__pycache__", ".pytest_cache", ".git",
                 ".worktrees"}

# --- floors ----------------------------------------------------------------
# run_all.py drives thirteen stages and then the schema validation: fourteen
# lines of "[ok ]".  Fewer means a STEPS entry vanished, which no returncode
# can report because the stage that vanished never ran to have a returncode.
MIN_OK_STAGES = 14
# The loop is 打脸 · 定位 · 戳探 · 修订 · 重证 · 解出 plus the M0/M5 bookends:
# eight beats, and the committed ledger has eight.  A ledger of one beat is not
# a loop.
MIN_BEATS = 8
# 248 frames / 247 transitions observed on the sweep.  `certify` green over an
# empty trace is green over nothing.
MIN_FRAMES = 100
MIN_TRANSITIONS = 100
# 5 probes observed, 4 of them executable.  M8's job is to design experiments
# that separate hypotheses; a probe_report with an empty `probes` list is a
# report that no experiment was run, and it is green-shaped all the same.
MIN_PROBES = 4
# The engines must propose rules, not just segment.  An empty rule list means
# cegis proposed nothing.
MIN_RULES = 1


def sh(argv, cwd=HERE, env=None):
    """Run a stage, decoding as UTF-8 rather than as the host locale.

    `text=True` alone decodes with cp936 on this box; a child printing UTF-8
    then either mojibakes or raises UnicodeDecodeError inside subprocess.run,
    and a checker that dies decoding its child is a checker that did not check.
    This territory hit the same hazard from the inside (DECISIONS D-A2-007).
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


def snapshot(root):
    """sha256 every file under `root`, skipping the generated directories."""
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in READONLY_SKIP]
        for name in files:
            path = os.path.join(base, name)
            try:
                with open(path, "rb") as fh:
                    out[path] = hashlib.sha256(fh.read()).hexdigest()
            except OSError:
                pass
    return out


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

def rung_real_run(problems, notes, started_at):
    print("[2/3] one real run -- python run_all.py, thirteen stages, offline, "
          "IN TREE")

    roots = [os.path.join(REPO, t) for t in READONLY_TREES
             if os.path.isdir(os.path.join(REPO, t))]
    if len(roots) < len(READONLY_TREES):
        fail(problems, "RED(read-only-check-cannot-run): only %d of the %d "
                       "trees A2 imports from exist (%s) -- the read-only "
                       "claim cannot be measured, so it is not established"
             % (len(roots), len(READONLY_TREES),
                ", ".join(os.path.basename(r) for r in roots)))
    before = {}
    for root in roots:
        before.update(snapshot(root))
    print("   ...   hashed %d files across %d upstream trees" % (len(before),
                                                                 len(roots)))

    env = dict(os.environ)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    r = sh([sys.executable, "run_all.py"], env=env)
    out = r.stdout + r.stderr

    if r.returncode != 0:
        fail(problems, "RED(pipeline): run_all.py exited %d\n%s"
             % (r.returncode, out[-3000:]))
        return False

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

    after = {}
    for root in roots:
        after.update(snapshot(root))
    changed = sorted(k for k in set(before) | set(after)
                     if before.get(k) != after.get(k))
    if changed:
        # AMBER, not RED: two sessions work this repo concurrently, so a change
        # upstream during the run may be someone else's.  Named and visible.
        notes.append("AMBER(read-only): %d file(s) under %s changed across the "
                     "run: %s%s.  Either A2 wrote into another track, or "
                     "another session did -- re-run with the other tracks idle "
                     "before calling it an A2 defect."
                     % (len(changed), "/".join(READONLY_TREES),
                        ", ".join(os.path.relpath(p, REPO)
                                  for p in changed[:6]),
                        " ..." if len(changed) > 6 else ""))
    else:
        print("   ok    read-only holds: 0 of %d upstream files changed"
              % len(before))

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


def check_ledger(problems, ledger):
    """The loop closed, and it closed over eight beats rather than zero."""
    beats = need(problems, ledger, "beats", "loop_ledger")
    if not isinstance(beats, list):
        fail(problems, "loop_ledger.beats is %r" % type(beats).__name__)
        return
    # Floor BEFORE `green`: `summary` is green for an empty beat list, and
    # `green` is computed from `summary`.
    at_least(problems, len(beats), MIN_BEATS, "loop_ledger.beats")

    for i, beat in enumerate(beats):
        for field in ("beat", "claim", "detail", "evidence", "name"):
            if field not in beat:
                fail(problems, "loop_ledger.beats[%d] is missing %r"
                     % (i, field))
                break
        else:
            if not beat.get("evidence"):
                fail(problems, "loop_ledger.beats[%d] (%s) cites no evidence "
                               "file; a beat with no artefact behind it is a "
                               "sentence, not a result" % (i, beat.get("beat")))

    summary = need(problems, ledger, "summary", "loop_ledger")
    if isinstance(summary, dict):
        total = need(problems, summary, "total", "loop_ledger.summary")
        passed = need(problems, summary, "pass", "loop_ledger.summary")
        failed = need(problems, summary, "fail", "loop_ledger.summary")
        absent = need(problems, summary, "absent", "loop_ledger.summary")
        at_least(problems, total, MIN_BEATS, "loop_ledger.summary.total")
        if failed != 0:
            fail(problems, "loop_ledger.summary.fail is %r" % (failed,))
        if absent != 0:
            fail(problems, "loop_ledger.summary.absent is %r -- a beat whose "
                           "evidence file is missing is not a passing beat"
                 % (absent,))
        if passed != total:
            fail(problems, "loop_ledger.summary: %r of %r beats passed"
                 % (passed, total))
        if isinstance(total, int) and total != len(beats):
            fail(problems, "loop_ledger.summary.total is %d but there are %d "
                           "beats" % (total, len(beats)))

    # Checked last, on purpose: `green` is the territory's own verdict and it
    # is only worth reading once the things it summarises have been counted.
    must_be_true(problems, ledger, "green", "loop_ledger")

    authority = need(problems, ledger, "authority", "loop_ledger")
    if not isinstance(authority, str) or not authority.strip():
        fail(problems, "loop_ledger.authority is %r -- A2's world exists under "
                       "an INC-004 ruling and the ledger is where that is "
                       "recorded" % (authority,))
    world = need(problems, ledger, "world", "loop_ledger")
    if not isinstance(world, str) or not world.strip():
        fail(problems, "loop_ledger.world is %r" % (world,))


def check_exhibit(problems, exhibit):
    """The exhibit is the territory's sharpest claim, so it gets both halves.

    A manual that is certified, provable, plan-complete AND FALSE of the world
    is the whole point.  Checking only `exhibit_green` would pass an exhibit
    that had quietly become true, which would demonstrate nothing.
    """
    must_be_true(problems, exhibit, "exhibit_green", "exhibit_report")
    must_be_true(problems, exhibit, "exhibit_is_false_of_the_world",
                 "exhibit_report")
    ground = need(problems, exhibit, "constructive_ground", "exhibit_report")
    if not isinstance(ground, str) or not ground.strip():
        fail(problems, "exhibit_report.constructive_ground is %r -- the "
                       "exhibit's falseness has to be known before the prover "
                       "runs, not inferred from it" % (ground,))
    manual = need(problems, exhibit, "manual", "exhibit_report")
    if not manual:
        fail(problems, "exhibit_report.manual is %r" % (manual,))


def check_candidates(problems, name, floor):
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
            fail(problems, "artifacts/%s record %d has status %r; engines "
                           "never adjudicate "
                           "(CONTRACTS/candidates_schema.md)"
                 % (name, i, rec["status"]))
            break


def rung_artifact_fields(problems):
    print("[3/3] artefact self-check")

    payloads = {}
    for name in REQUIRED_FIELDS:
        payloads[name] = load_json(problems, name)
        check_fields(problems, name, payloads[name])

    if payloads["loop_ledger.json"]:
        check_ledger(problems, payloads["loop_ledger.json"])
    if payloads["exhibit_report.json"]:
        check_exhibit(problems, payloads["exhibit_report.json"])

    engines = payloads["engines_report.json"]
    if engines:
        at_least(problems, need(problems, engines, "frames", "engines_report"),
                 MIN_FRAMES, "engines_report.frames")
        at_least(problems, need(problems, engines, "transitions",
                                "engines_report"),
                 MIN_TRANSITIONS, "engines_report.transitions")
        mining = need(problems, engines, "mining", "engines_report")
        if isinstance(mining, dict):
            rules = mining.get("rules")
            if not isinstance(rules, list):
                fail(problems, "engines_report.mining.rules is %r" % (rules,))
            else:
                at_least(problems, len(rules), MIN_RULES,
                         "engines_report.mining.rules")

    # The loop's middle.  打脸 must actually have landed, 定位 must have
    # narrowed to something, and 戳探 must have settled something -- each of
    # these reports is green-shaped whether or not it did any work.
    refutation = load_json(problems, "refutation.json")
    if refutation:
        must_be_true(problems, refutation, "refuted", "refutation")

    locate = load_json(problems, "locate_report.json")
    if locate:
        culprits = need(problems, locate, "culprits", "locate_report")
        if not culprits:
            fail(problems, "locate_report.culprits is %r -- 定位 that names "
                           "nobody has not located anything" % (culprits,))
        at_least(problems, need(problems, locate, "n_step_diffs",
                                "locate_report"),
                 1, "locate_report.n_step_diffs")

    probe_report = load_json(problems, "probe_report.json")
    if probe_report:
        probes = need(problems, probe_report, "probes", "probe_report")
        if not isinstance(probes, list):
            fail(problems, "probe_report.probes is %r" % type(probes).__name__)
        else:
            at_least(problems, len(probes), MIN_PROBES, "probe_report.probes")
            for i, probe in enumerate(probes):
                for field in ("id", "question", "status"):
                    if field not in probe:
                        fail(problems, "probe_report.probes[%d] is missing %r"
                             % (i, field))
                        break
                else:
                    # A probe that was actually run has to have said what it
                    # expected first, or "refuted" is a claim made after the
                    # fact.  Probes classed `not_separable_in_this_world` were
                    # never run and carry a `frontier` instead -- a different
                    # shape for a different thing, not a missing field.
                    if (probe["status"] in ("refuted", "confirmed")
                            and not probe.get("predictions")):
                        fail(problems, "probe_report.probes[%d] (%s) is %r but "
                                       "recorded no predictions -- an outcome "
                                       "with no prior is not an experiment"
                             % (i, probe["id"], probe["status"]))
            # A probe that separates no hypothesis is a question, not an
            # experiment.  At least one must have come back refuting something.
            if not any(p.get("status") == "refuted" for p in probes):
                fail(problems, "no probe came back 'refuted' -- 戳探 that "
                               "settles nothing did not settle anything")
        at_least(problems, need(problems, probe_report, "executable",
                                "probe_report"),
                 MIN_PROBES, "probe_report.executable")

    repair = load_json(problems, "repair_report.json")
    if repair:
        must_be_true(problems, repair, "green", "repair_report")
        # The repaired manual must have been re-certified against the grown
        # evidence, and the stale one must have died on it: a repair that
        # leaves the old certificate standing repaired nothing.
        stale = need(problems, repair, "stale_certificate", "repair_report")
        if isinstance(stale, dict):
            must_be_true(problems, stale, "died",
                         "repair_report.stale_certificate")

    # The traces the loop is built on, floored so that "replayed exactly"
    # cannot be a statement about an empty file.
    for name, floor in (("raw_trace.jsonl", MIN_FRAMES),
                        ("probed_trace.jsonl", MIN_FRAMES),
                        ("history_trace.jsonl", MIN_FRAMES),
                        ("probes.jsonl", MIN_PROBES),
                        ("solved_episode.jsonl", 1)):
        rows = load_jsonl(problems, name)
        if rows is not None:
            at_least(problems, len(rows), floor, "artifacts/%s rows" % name)

    for name, floor in sorted(CANDIDATE_STREAMS.items()):
        check_candidates(problems, name, floor)

    validate = sh([sys.executable, "-m", "tools.validate_candidates"]
                  + [os.path.join(ARTIFACTS, n) for n in
                     sorted(CANDIDATE_STREAMS)],
                  cwd=os.path.join(REPO, "engine-rig"))
    if validate.returncode != 0:
        fail(problems, "RED(contract): the streams fail the frozen contract\n%s"
             % (validate.stdout + validate.stderr)[-2000:])

    if not problems:
        ledger = payloads["loop_ledger.json"]
        print("   ok    %d loop beats all green, exhibit false-of-the-world, "
              "%d candidate streams clean"
              % (len(ledger["beats"]) if ledger else 0, len(CANDIDATE_STREAMS)))


def main():
    problems, notes = [], []
    # Nothing the gate itself needs goes into the tree.  (Rung 2's pipeline is
    # a different matter -- see the module docstring.)
    scratch = tempfile.mkdtemp(prefix="cold-start-a2-verify-")
    started_at = time.time()
    try:
        rung_tests(problems)
        if rung_real_run(problems, notes, started_at):
            rung_artifact_fields(problems)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    for note in notes:
        print("   %s" % note)
    print("   note  rung 2 wrote into the working tree: cold-start-a2/"
          "artifacts/ and theory/generated*/.  run_all.py takes no out-dir; "
          "this gate does not restore them for you.")
    if problems:
        print("cold-start-a2: RED (%d problem(s))" % len(problems))
        return 1
    if notes:
        print("cold-start-a2: AMBER -- suite, run and artefacts are green, but "
              "see the note(s) above.")
        print("               Exit 3, deliberately: an unexplained write into "
              "another track is not a clean pass.")
        return 3
    print("cold-start-a2: green -- suite, one real run, read-only across the "
          "run, artefact fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
