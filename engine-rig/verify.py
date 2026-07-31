"""engine-rig's completion gate.

    cd engine-rig && python verify.py

Four rungs, and the territory is finished only if all four are green:

  1. the suite passes;
  2. the real pipeline runs once, offline -- all eight engines end to end;
  3. the artefacts that run produced have the fields they claim to have;
  4. every survey number that reaches the paper still recomputes, from a script,
     to the value on disk.

Rung 3 is the one that is usually missing.  A green suite says the code does
what its author thought; it does not say the pipeline ran, and it does not say
the stream it emitted still matches the frozen contract.  The two are different
claims and only the second one is "this territory is done".

Rung 4 is E18's (D-037).  The cross-check of 2026-07-29 published five ratios
that the paper then quoted, and its run directory holds nine Markdown files and
a manifest -- no data, no script.  A number that only a report remembers is not
evidence, and `tools/engine_table.py`'s registry did not catch it because a
regex against prose proves the paper's digits match the report's digits and
says nothing about whether the report's digits match a computation.  This rung
re-runs the recomputations and fails if any of them drifts.

Two rules this gate keeps, because breaking either is how gates in this repo
have failed before:

**It does not write into the working tree.**  Everything lands in a mkdtemp
that is removed on the way out.  ablation-arm's first verify.sh dropped files
into `artifacts/` and turned the arm's own read-only test red -- the gate broke
the thing it was guarding.  A consequence worth having: because the run is
out-of-tree and `--deterministic` is byte-stable, rung 3 can compare the fresh
stream against the reference committed at `artifacts/candidates.jsonl` and so
detect that the committed artefact has drifted from what the code produces --
without touching it.

**An empty result is not a pass.**  Every count is checked against a floor.
`figures/verify.sh` currently prints "ok (csv, out, SOURCES.sha256 all
identical)" when both of its builds produced nothing at all, because two empty
trees are byte-identical; three more checks in this repo pass the same way on an
empty set.  A family that silently emptied out reads exactly like a family that
is fine, so the floors are written down here rather than assumed.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# The contract's required fields (CONTRACTS/candidates_schema.md, frozen v0.1).
REQUIRED = ("engine", "evidence", "id", "kind", "payload", "status", "timestamp")

# Floors.  Not decoration: the number below which "the pipeline ran" stops being
# true.  engine-rig ships eight engines and 150+ tests; a stream of three
# candidates means something stopped proposing and said nothing about it.
MIN_CANDIDATES = 20
MIN_ENGINES = 5

REFERENCE = os.path.join(HERE, "artifacts", "candidates.jsonl")

# Rung 4's committed output: one JSON per survey number, written by
# `tools.survey_numbers.run_all` (D-037, E18).
COUNTS = os.path.join(HERE, "runs", "20260730T120000Z-E18", "counts")


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


def rung_tests(problems):
    print("[1/4] suite")
    r = sh([sys.executable, "-m", "pytest", "-q"])
    if r.returncode == 5:
        # pytest found nothing to run.  Read as green this would be the fifth
        # time this repo mistook a check that could not run for one that passed.
        fail(problems, "pytest collected nothing -- testpaths misconfigured, "
                       "which is a broken gate, not a passing one")
        return
    if r.returncode != 0:
        fail(problems, "suite red (exit %d)\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return
    print("   ok    %s" % (r.stdout.strip().splitlines() or ["(no output)"])[-1])


def rung_real_run(problems, out_path):
    print("[2/4] one real run -- eight engines end to end, offline")
    r = sh([sys.executable, "-m", "tools.run_all",
            "--out", out_path, "--deterministic", "--force"])
    if r.returncode != 0:
        fail(problems, "run_all exited %d\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return False
    if not os.path.exists(out_path):
        fail(problems, "run_all exited 0 but wrote no stream at all")
        return False
    print("   ok    wrote %s" % os.path.basename(out_path))
    return True


def rung_artifact_fields(problems, out_path):
    print("[3/4] artefact self-check")
    records, bad_lines = [], 0
    with open(out_path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                bad_lines += 1
                fail(problems, "line %d is not JSON: %s" % (n, exc))

    if len(records) < MIN_CANDIDATES:
        fail(problems, "only %d candidates, floor is %d -- an empty or nearly "
                       "empty stream is not a pass"
             % (len(records), MIN_CANDIDATES))
        return

    for i, rec in enumerate(records):
        missing = [f for f in REQUIRED if f not in rec]
        if missing:
            # Deliberately not `rec.get(f, <what we want>)`.  A gate that
            # defaults a missing field to the value it hopes for passes a run
            # in which the field silently disappeared.
            fail(problems, "record %d is missing %s" % (i, ", ".join(missing)))
            break
        if rec["status"] != "candidate":
            fail(problems, "record %d has status %r; engines never adjudicate "
                           "(CONTRACTS/candidates_schema.md)" % (i, rec["status"]))
            break

    engines = {r.get("engine") for r in records}
    if len(engines) < MIN_ENGINES:
        fail(problems, "only %d distinct engines proposed (%s), floor is %d"
             % (len(engines), ", ".join(sorted(map(str, engines))), MIN_ENGINES))

    r = sh([sys.executable, "-m", "tools.validate_candidates", out_path])
    if r.returncode != 0:
        fail(problems, "the stream fails the frozen contract\n%s"
             % (r.stdout + r.stderr)[-2000:])

    if not problems:
        print("   ok    %d candidates from %d engines, all %d required fields, "
              "contract clean" % (len(records), len(engines), len(REQUIRED)))


def rung_survey_numbers(problems):
    """Re-run the E18 recomputations and compare against the committed counts.

    `--check` is the whole point: it re-derives every number rather than reading
    the JSON back, so a script that has quietly stopped agreeing with itself --
    or with the engine it measures -- turns this red.  It writes nothing.

    Slow by the standards of the other rungs (thousands of worlds), so it is
    skippable for a quick loop, and skipping is *printed*: a rung that can
    vanish without saying so is how a gate becomes decoration.
    """
    print("[4/4] survey numbers -- every paper ratio recomputes from script")
    if os.environ.get("ENGINE_RIG_SKIP_SURVEY"):
        print("   skip  ENGINE_RIG_SKIP_SURVEY is set -- rung 4 did NOT run")
        return
    if not os.path.isdir(COUNTS):
        fail(problems, "no counts directory at %s -- the recomputations have "
                       "no committed output to check against"
             % os.path.relpath(COUNTS, HERE))
        return
    r = sh([sys.executable, "-m", "tools.survey_numbers.run_all",
            "--out", COUNTS, "--check"])
    if r.returncode != 0:
        fail(problems, "survey-number recomputation red (exit %d)\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return
    print("   ok    %s" % (r.stdout.strip().splitlines() or ["(no output)"])[-1])


def reference_drift(out_path):
    """Does the committed reference still match what the code produces?

    Reported, not fatal.  The run is deterministic and out-of-tree, so this
    costs nothing and answers a question nothing else in the territory asks.
    """
    if not os.path.exists(REFERENCE):
        return "artifacts/candidates.jsonl is absent"
    with open(REFERENCE, "rb") as fh:
        committed = fh.read()
    with open(out_path, "rb") as fh:
        fresh = fh.read()
    if committed == fresh:
        return None
    return ("artifacts/candidates.jsonl (%d bytes) differs from a fresh "
            "deterministic run (%d bytes)" % (len(committed), len(fresh)))


def main():
    problems = []
    scratch = tempfile.mkdtemp(prefix="engine-rig-verify-")
    try:
        out_path = os.path.join(scratch, "candidates.jsonl")
        rung_tests(problems)
        if rung_real_run(problems, out_path):
            rung_artifact_fields(problems, out_path)
            drift = reference_drift(out_path)
            if drift:
                print("   note  %s" % drift)
        rung_survey_numbers(problems)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if problems:
        print("engine-rig: RED (%d problem(s))" % len(problems))
        return 1
    print("engine-rig: green -- suite, one real run, artefact fields, "
          "survey numbers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
