"""battery's completion gate.

    cd battery && python verify.py        # or from anywhere; cwd does not matter

Three rungs, and the territory is finished only if all three are green:

  1. the suite passes;
  2. the real pipeline runs once, offline -- the whole capability spectrum
     recomputed from the ledgers on disk;
  3. the seven artefacts that run produced have the fields they claim to have,
     and their counts clear an explicit floor.

Rung 3 is the one that is usually missing.  A green suite says the metrics do
what their author thought; it does not say the recompute ran, and it does not
say the spectrum it emitted holds any measurement at all.  The two are
different claims and only the second one is "this territory is done".

Two rules this gate keeps, because breaking either is how gates in this repo
have failed before:

**It does not write into the working tree.**  `run_battery` takes `--out`, so
this points it at a mkdtemp that is removed on the way out, and the tracked
`battery/artifacts/` is left exactly as it was.  ablation-arm's first
verify.sh dropped files into `artifacts/` and turned the arm's own read-only
test red -- the gate broke the thing it was guarding.  The recompute is
otherwise passive by construction: it opens files and does nothing else, so
"offline" here needs no enforcement beyond removing the credentials from the
child's environment, which this does anyway.

**An empty result is not a pass.**  This territory is the sharpest case of it
in the repo.  A spectrum with all 38 metric cards, all 41 runs, and every one
of its 1,558 cells reading `not-applicable` is a structurally perfect file --
right keys, right shapes, right counts, and no measurement anywhere in it.  So
`MIN_OK_VALUES` below counts cells that actually carry a number, and it is the
floor that matters; the shape floors are the cheap ones.  `figures/verify.sh`
currently prints "ok (csv, out, SOURCES.sha256 all identical)" when both of its
builds produced nothing at all, because two empty trees are byte-identical, and
three more checks in this repo pass the same way on an empty set.

One thing this gate deliberately does **not** do: compare the fresh artefacts
against the tracked `battery/artifacts/`.  Some of the recompute's inputs --
`baseline-arms/out/shards/*.jsonl`, the schema traces -- are untracked by
design, so a checkout that does not have them legitimately produces a smaller
spectrum (41 runs here against the 95 the shipped artefacts were built from).
A byte comparison would be red on a clean worktree for a reason that is not a
defect.  The run count of both is printed instead, as a note.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SHIPPED = os.path.join(HERE, "artifacts")

# The seven files a recompute produces.  Named, not globbed: a glob over an
# output directory finds whatever is there and calls it the answer, which is
# how "0 artefacts" becomes "all artefacts present".
ARTEFACTS = ("arm_contrast.json", "capability_spectrum.json",
             "discrimination.json", "discrimination_arms.json",
             "gaming_audit.json", "redundancy.json",
             "validation_material.json")

# Required top-level keys, per artefact.  The two the battery is actually read
# for are spelled out in full; the rest must at least be a non-empty object,
# checked below.
SPECTRUM_REQUIRED = ("battery_version", "cards", "coverage", "provenance",
                     "runs")
DISCRIMINATION_REQUIRED = ("control_runs", "gradient", "ladder", "metrics",
                           "power", "role")

# Floors.  Not decoration: the number below which "the pipeline ran" stops
# being true.  Observed on a clean worktree: 38 cards, 41 runs, 570 `ok` cells,
# 34 control runs, a 3-rung ladder.  The floors sit well under those so an
# ordinary change does not turn them red, and well over zero so a silent
# emptying cannot read as green.
#
# 20 cards: 38 metrics are registered across five families (economy,
# knowledge, method, process, cross-cutting).  Under 20 an entire family has
# dropped out of the registry, and the file would still be well formed.
MIN_CARDS = 20
# 10 runs: the pilot is four arms over four games.  Under ten runs there is no
# arm left to compare against another, whatever the file says.
MIN_RUNS = 10
# 100 measured cells: the one that matters.  `status == "ok"` is the only
# status that means a metric was computed on a run; `not-applicable` and
# `insufficient-data` are both legitimate individually and, en masse, are what
# a spectrum looks like after every adapter has silently stopped parsing.
MIN_OK_VALUES = 100
# 5 control runs: discrimination compares a control arm against the rest.
# Under five the comparison is an anecdote, and `discrimination.json` would
# carry all six of its keys regardless.
MIN_CONTROL_RUNS = 5
# 2 rungs: a "model ladder" of one model is not a gradient.
MIN_LADDER = 2


def sh(argv, cwd=REPO):
    """Run a stage, decoding as UTF-8 rather than as the host locale.

    `text=True` alone decodes with cp936 on this box; a child printing UTF-8 --
    and `run_battery` prints metric prose that contains one -- then either
    mojibakes or raises UnicodeDecodeError inside subprocess.run, and a checker
    that dies decoding its child is a checker that did not check.

    cwd is the repo root, not this directory: `battery/tests` imports
    `from battery...`, and `run_battery` is a `-m` module under the same
    package, so both are invoked the way the territory documents them.  The
    child's environment has the credentials removed -- the recompute is purely
    passive, so this costs nothing and makes "offline" a property of the run
    rather than a claim about it.
    """
    env = dict(os.environ)
    for name in ("ARC_API_KEY", "ANTHROPIC_API_KEY"):
        env.pop(name, None)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


def fail(problems, message):
    print("   FAIL  %s" % message)
    problems.append(message)


def rung_tests(problems):
    print("[1/3] suite")
    r = sh([sys.executable, "-m", "pytest", "battery/tests", "-q"])
    if r.returncode == 5:
        # pytest found nothing to run.  Read as green this would be one more
        # instance of this repo mistaking a check that could not run for one
        # that passed.
        fail(problems, "pytest collected nothing -- `battery/tests` did not "
                       "resolve, which is a broken gate, not a passing one")
        return
    if r.returncode != 0:
        fail(problems, "suite red (exit %d)\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return
    print("   ok    %s" % (r.stdout.strip().splitlines() or ["(no output)"])[-1])


def rung_real_run(problems, out_dir):
    print("[2/3] one real run -- the whole spectrum recomputed from the "
          "ledgers, offline")
    r = sh([sys.executable, "-m", "battery.run_battery", "--out", out_dir])
    if r.returncode != 0:
        fail(problems, "run_battery exited %d\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return False
    written = sorted(n for n in os.listdir(out_dir)) if os.path.isdir(out_dir) else []
    if not written:
        fail(problems, "run_battery exited 0 and wrote nothing at all")
        return False
    print("   ok    wrote %d file(s)" % len(written))
    return True


def _load(problems, out_dir, name):
    path = os.path.join(out_dir, name)
    if not os.path.exists(path):
        fail(problems, "%s was not written" % name)
        return None
    with open(path, encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError as exc:
            fail(problems, "%s is not JSON: %s" % (name, exc))
            return None


def rung_artifact_fields(problems, out_dir):
    print("[3/3] artefact self-check")
    loaded = {}
    for name in ARTEFACTS:
        doc = _load(problems, out_dir, name)
        if doc is None:
            continue
        if not isinstance(doc, dict) or not doc:
            fail(problems, "%s is not a non-empty JSON object" % name)
            continue
        loaded[name] = doc
    if len(loaded) < len(ARTEFACTS):
        return

    spectrum = loaded["capability_spectrum.json"]
    # Deliberately not `spectrum.get(key, <what we want>)`.  A gate that
    # defaults a missing field to the value it hopes for passes a recompute in
    # which the field silently disappeared.
    missing = [k for k in SPECTRUM_REQUIRED if k not in spectrum]
    if missing:
        fail(problems, "capability_spectrum.json is missing %s"
             % ", ".join(missing))
        return

    cards, runs = spectrum["cards"], spectrum["runs"]
    if len(cards) < MIN_CARDS:
        fail(problems, "the spectrum carries %d metric card(s), floor is %d -- "
                       "a registry that lost a whole family is not a pass"
             % (len(cards), MIN_CARDS))
    if len(runs) < MIN_RUNS:
        fail(problems, "the spectrum carries %d run(s), floor is %d -- under "
                       "that there is no arm left to compare against another"
             % (len(runs), MIN_RUNS))

    provenance = spectrum["provenance"]
    for key in ("arms", "input_digests", "n_games", "n_runs"):
        if key not in provenance:
            fail(problems, "capability_spectrum.json provenance is missing %r"
                 % key)
    if "n_runs" in provenance and provenance["n_runs"] != len(runs):
        fail(problems, "provenance claims %r run(s); the file holds %d"
             % (provenance["n_runs"], len(runs)))

    # The check the shape checks cannot make.  Every cell could be
    # `not-applicable` and everything above would still be green.
    statuses = {}
    ok_values = 0
    for run_id in sorted(runs):
        run = runs[run_id]
        if "metrics" not in run:
            fail(problems, "spectrum run %r has no `metrics`" % run_id)
            break
        for metric_id in sorted(run["metrics"]):
            cell = run["metrics"][metric_id]
            if "status" not in cell:
                fail(problems, "spectrum cell %s/%s has no status"
                     % (run_id, metric_id))
                break
            statuses[cell["status"]] = statuses.get(cell["status"], 0) + 1
            if cell["status"] == "ok":
                if "value" not in cell:
                    fail(problems, "spectrum cell %s/%s is `ok` with no value"
                         % (run_id, metric_id))
                    break
                if cell["value"] is None:
                    fail(problems, "spectrum cell %s/%s is `ok` with a null "
                                   "value" % (run_id, metric_id))
                    break
                ok_values += 1
    if ok_values < MIN_OK_VALUES:
        fail(problems, "only %d measured cell(s) (status `ok`) across %d "
                       "cell(s) %s, floor is %d -- a spectrum in which nothing "
                       "was measured is not a pass"
             % (ok_values, sum(statuses.values()),
                sorted(statuses.items()), MIN_OK_VALUES))

    discrimination = loaded["discrimination.json"]
    missing = [k for k in DISCRIMINATION_REQUIRED if k not in discrimination]
    if missing:
        fail(problems, "discrimination.json is missing %s" % ", ".join(missing))
    else:
        control = discrimination["control_runs"]
        n_control = control if isinstance(control, int) else len(control)
        if n_control < MIN_CONTROL_RUNS:
            fail(problems, "discrimination.json reports %d control run(s), "
                           "floor is %d -- a comparison against fewer than that "
                           "is an anecdote" % (n_control, MIN_CONTROL_RUNS))
        if len(discrimination["ladder"]) < MIN_LADDER:
            fail(problems, "the model ladder has %d rung(s) (%s), floor is %d "
                           "-- one rung is not a gradient"
                 % (len(discrimination["ladder"]),
                    ", ".join(map(str, discrimination["ladder"])) or "none",
                    MIN_LADDER))
        if len(discrimination["metrics"]) < MIN_CARDS:
            fail(problems, "discrimination.json judges %d metric(s), floor is "
                           "%d" % (len(discrimination["metrics"]), MIN_CARDS))

    if not problems:
        print("   ok    %d artefacts, %d cards x %d runs, %d measured cells, "
              "%s" % (len(ARTEFACTS), len(cards), len(runs), ok_values,
                      ", ".join("%d %s" % (v, k)
                                for k, v in sorted(statuses.items()))))


def shipped_note(out_dir):
    """How the fresh spectrum compares with the one that is committed.

    Reported, not fatal, and not a byte comparison -- see the module docstring:
    some inputs are untracked by design, so a checkout without them
    legitimately recomputes a smaller spectrum.  Printing both counts turns
    that from a surprise into a fact.
    """
    fresh = os.path.join(out_dir, "capability_spectrum.json")
    committed = os.path.join(SHIPPED, "capability_spectrum.json")
    if not os.path.exists(committed):
        return "battery/artifacts/capability_spectrum.json is absent"
    try:
        with open(fresh, encoding="utf-8") as fh:
            a = json.load(fh)
        with open(committed, encoding="utf-8") as fh:
            b = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return "could not compare against battery/artifacts/: %s" % exc
    if "runs" not in a or "runs" not in b:
        return "one of the two spectra has no `runs` key to compare"
    if len(a["runs"]) == len(b["runs"]):
        return None
    return ("this recompute saw %d run(s); battery/artifacts/ was built from "
            "%d. Untracked inputs (baseline-arms/out/shards, schema traces) "
            "are absent from a clean checkout by design"
            % (len(a["runs"]), len(b["runs"])))


def main():
    problems = []
    scratch = tempfile.mkdtemp(prefix="battery-verify-")
    try:
        out_dir = os.path.join(scratch, "artifacts")
        os.makedirs(out_dir)
        rung_tests(problems)
        if rung_real_run(problems, out_dir):
            rung_artifact_fields(problems, out_dir)
            note = shipped_note(out_dir)
            if note:
                print("   note  %s" % note)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if problems:
        print("battery: RED (%d problem(s))" % len(problems))
        return 1
    print("battery: green -- suite, one real run, artefact fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
