<<<<<<< ours
"""battery's completion gate.

    cd battery && python verify.py        # or from anywhere; cwd does not matter

Four rungs, and the territory is finished only if all four are green:

  1. the suite passes;
  2. the real pipeline runs once, offline -- the whole capability spectrum
     recomputed from the ledgers on disk;
  3. the seven artefacts that run produced have the fields they claim to have,
     and their counts clear an explicit floor;
  4. the committed documents state process 1's true separation count, and the
     ceiling that count is a consequence of has not gone stale.

Rung 4 was added by V22, after a cell whose maximum attainable score was zero
was carried elsewhere as 60%.  Rungs 1-3 were green the whole time and would
have stayed green: nothing in them reads a sentence.

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

# The sentence STATUS.md has to carry verbatim, with the two counts filled in
# from the committed artefact.  A whole sentence rather than a bare digit,
# because a status document is full of digits and a gate that accepted any of
# them would pass on a STATUS.md that never mentions process 1 at all.
STATUS_CLAIM = "%d 条指标里 `discriminating` %d 条"


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
    print("[1/4] suite")
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
    print("[2/4] one real run -- the whole spectrum recomputed from the "
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
    print("[3/4] artefact self-check")
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


def rung_separation_claim(problems):
    """[4/4] the documents state the true separation count, and cannot go stale.

    Added by V22.  Process 1's headline number is **zero** -- no metric
    separates the specified gradient -- and the way that number went wrong was
    not that anybody computed it incorrectly.  It was that nothing checked the
    prose against the artefact, so a cell whose maximum attainable score was 0
    was carried elsewhere as 60% for weeks.  Rungs 1-3 would all have been
    green throughout: the suite passes, the recompute runs, and
    `discrimination_arms.json` has every field it claims to have while
    separating nothing at all.  That is exactly the shape rung 3's docstring
    warns about, one level up -- a structurally perfect file holding no result.

    This rung reads the **committed** artefact rather than the scratch
    recompute, because the claim in a committed document is about the committed
    numbers; a clean checkout legitimately recomputes a smaller spectrum (see
    `shipped_note`) and judging the prose against that would be red for a
    reason that is not a defect.

    The third check is the one worth having.  "Zero is unreachable here" is
    true only while the pile stays too small to reach it, so the gate derives
    the threshold instead of trusting the sentence, and **flips direction**
    when the data grow: the moment a metric pairs enough games for p<0.05 to be
    attainable, the ceiling paragraph becomes false and this turns red until
    somebody rewrites it.  A gate that could only catch the claim going too
    high would let it rot in the other direction.
    """
    print("[4/4] the separation claim in the committed documents")
    path = os.path.join(SHIPPED, "discrimination_arms.json")
    if not os.path.exists(path):
        fail(problems, "battery/artifacts/discrimination_arms.json is absent; "
                       "there is no artefact for the documents to agree with")
        return
    with open(path, encoding="utf-8") as fh:
        try:
            doc = json.load(fh)
        except json.JSONDecodeError as exc:
            fail(problems, "committed discrimination_arms.json is not JSON: %s"
                 % exc)
            return

    metrics = doc.get("metrics") or {}
    if not metrics:
        fail(problems, "committed discrimination_arms.json judges no metrics")
        return
    separating = sorted(m for m, e in metrics.items()
                        if e.get("verdict") == "discriminating")
    # The sign test's **non-tied** n, not `n_paired_games`.  `2/2**n` is a
    # function of the former, and the two already differ here: P3, X2 and X3
    # pair four games and score three.  Keying the staleness flip on paired
    # games would fire the moment the pile reached six even if every metric
    # lost a pair to a tie -- n=5, floor 0.0625, the ceiling paragraph still
    # true -- and demand the rewriting of a correct sentence.
    paired = max((_non_tied(e) for e in metrics.values()), default=0)
    needed = docs_sign_test_games_needed()

    documents = {}
    for name in ("METRICS.md", "STATUS.md"):
        try:
            with open(os.path.join(HERE, name), encoding="utf-8") as fh:
                documents[name] = fh.read()
        except OSError as exc:
            fail(problems, "could not read %s: %s" % (name, exc))
    if len(documents) < 2:
        return

    # (a) METRICS.md is generated, so this is not a duplicate of test_docs: it
    # catches the file being hand-edited after generation, which is the one
    # failure the generator cannot see.
    headline = "**%d of %d metrics separate" % (len(separating), len(metrics))
    if headline not in documents["METRICS.md"]:
        fail(problems, "METRICS.md does not carry the artefact's headline %r "
                       "-- regenerate with `python -m battery.docs`"
             % headline)

    # (b) the number a reader of STATUS.md walks away with.  Checked as one
    # derived sentence rather than as "does the digit appear somewhere": the
    # first draft of this gate looked for `str(n_separating)` inside the W-13
    # section, which a document containing `0.125` or `80 run` satisfies
    # without saying anything.  Its own negative control caught it.
    claim = STATUS_CLAIM % (len(metrics), len(separating))
    if claim not in documents["STATUS.md"]:
        fail(problems, "STATUS.md does not state the separation count; it must "
                       "contain %r verbatim, so that the number a reader walks "
                       "away with is the number in the artefact" % claim)

    # (c) the anti-staleness flip.
    ceiling_claimed = "unreachable for every metric" in documents["METRICS.md"]
    if paired < needed:
        if separating:
            fail(problems, "arithmetic contradiction: the best-covered metric "
                           "pairs %d game(s) and the sign test needs %d to "
                           "reach p<0.05 at all, yet %d metric(s) are recorded "
                           "as `discriminating` (%s)"
                 % (paired, needed, len(separating), ", ".join(separating)))
        if not ceiling_claimed:
            fail(problems, "the pile is still too small to attain p<0.05 (%d "
                           "paired game(s) against the %d needed), but "
                           "METRICS.md no longer says so -- a bare zero reads "
                           "as `the metrics failed` when it means `the test "
                           "could not be sat`" % (paired, needed))
    elif ceiling_claimed:
        fail(problems, "METRICS.md still says `discriminating` is unreachable, "
                       "but the best-covered metric now pairs %d game(s) and "
                       "only %d are needed. The ceiling paragraph is stale and "
                       "the zero now means something else -- rewrite it before "
                       "this goes green" % (paired, needed))

    if not problems:
        print("   ok    %d separating of %d judged; %d paired game(s) against "
              "the %d the sign test needs; both documents agree"
              % (len(separating), len(metrics), paired, needed))


def _non_tied(entry):
    """One metric's sign-test `n`, taken from `docs.py` rather than restated.

    Same reason as `docs_sign_test_games_needed`: the gate and the document it
    checks must not hold two definitions of the count the arithmetic is a
    function of.
    """
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.docs import _non_tied as impl
    return impl(entry)


def docs_sign_test_games_needed():
    """The threshold, from the generator rather than restated here.

    Imported late and by function so that this gate and `METRICS.md` cannot
    disagree about what "enough games" means: there is one definition, in
    `battery/docs.py`, derived in turn from `audit/stats.py`'s own formula.

    The repo root goes on `sys.path` first because this file is documented as
    runnable directly -- `python battery/verify.py`, cwd irrelevant -- and in
    that mode the interpreter puts `battery/` on the path, not its parent, so
    `import battery` fails. Restating the threshold here to dodge the import
    would give the gate its own copy of the number it exists to check.
    """
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.docs import _sign_test_games_needed
    return _sign_test_games_needed()


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
    # The other half of the encoding problem.  Children are told to emit UTF-8
    # and decoded as UTF-8; this end has to be able to *print* what came back.
    # `run_battery` prints metric prose containing non-cp936 characters, and a
    # gate that dies with UnicodeEncodeError while printing its own verdict is
    # a gate whose verdict nobody read.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

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

    rung_separation_claim(problems)

    print()
    if problems:
        print("battery: RED (%d problem(s))" % len(problems))
        return 1
    print("battery: green -- suite, one real run, artefact fields, "
          "separation claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
||||||| base
=======
"""battery — the territory gate. `python -m battery.verify`

`monitor/gates.py` treats `verify.py` as a territory's canonical gate and falls
back to a bare pytest run when there is none. The battery had no gate, so its
freeze would have been checked by nothing: S13's finding was that a skipped gate
and a passing gate look identical from the outside.

Three gates, in order of what they protect:

  1. **the freeze** — `BATTERY_V1.md` still describes the tree it was written
     against (`battery/freeze.py`).
  2. **the suite** — `battery/tests`, which is what the freeze's determinism and
     anti-gaming claims rest on. A deselected or uncollected test is reported as
     loudly as a failing one: the cheapest way to disarm this gate is an
     `addopts` line, not a broken assertion.
  3. **the readings** — the seven artefacts. Drift here is *reported and
     tolerated*: Phase 4 exists to recompute against inputs the battery has
     never read, so a gate that failed on new numbers would fail by
     construction. Silence would be the wrong answer too, hence the report.

Exit 0 = the instrument matches its record. Exit 1 = something to read before
merging.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _say(text):
    """Print without dying on a console that cannot encode the bytes.

    A gate that raises UnicodeEncodeError while reporting a failure shows the
    operator a traceback instead of the reason, on a Windows console whose code
    page is not UTF-8. It failed closed, but it failed illegibly.
    """
    enc = sys.stdout.encoding or "utf-8"
    sys.stdout.write(text.encode(enc, "replace").decode(enc, "replace") + "\n")


def gate_freeze():
    from battery import freeze
    fails = freeze.check()
    if fails:
        _say("FAIL  freeze: the tree no longer matches BATTERY_V1.md")
        for f in fails:
            _say("      - " + f.replace("\n", "\n        "))
        return False
    _say("ok    freeze: %d code + %d docs + %d suite + %d freeze files, the "
         "pre-registration and the pile cut all match BATTERY_V1.md"
         % (len(freeze.CODE), len(freeze.DOCS), len(freeze.SUITE),
            len(freeze.FREEZE)))
    return True


def gate_tests():
    out = subprocess.run([sys.executable, "-m", "pytest", "battery/tests", "-q"],
                         cwd=ROOT, capture_output=True)
    text = (out.stdout + out.stderr).decode("utf-8", "replace")
    tail = text.strip().splitlines()[-1] if text.strip() else "(no output)"
    if out.returncode != 0:
        _say("FAIL  tests: battery/tests")
        for ln in text.strip().splitlines()[-15:]:
            _say("      " + ln)
        return False
    # A green run that quietly skipped the objecting tests is not a green run.
    muted = [w for w in ("deselected", "error") if w in tail]
    if muted:
        _say("FAIL  tests: %s — tests were %s rather than run. The suite is "
             "half this gate; silencing part of it is not passing it."
             % (tail, " and ".join(muted)))
        return False
    passed = re.search(r"(\d+) passed", tail)
    if not passed or int(passed.group(1)) < 200:
        _say("FAIL  tests: %s — far fewer tests ran than this suite has. "
             "Collection was cut short somewhere." % tail)
        return False
    _say("ok    tests: " + tail)
    return True


def gate_readings():
    from battery import freeze
    drift = freeze.readings_drift()
    if drift:
        _say("note  readings: %d of %d artefacts differ from BATTERY_V1.md — "
             "%s" % (len(drift), len(freeze.READINGS), ", ".join(drift)))
        _say("      Not a failure: artefacts are readings, and a recompute is "
             "supposed to change them. Record the new values in a new freeze "
             "version before publishing them.")
    else:
        _say("ok    readings: %d artefacts match the values recorded at freeze "
             "time" % len(freeze.READINGS))
    return True


def main():
    ok = True
    for gate in (gate_freeze, gate_tests, gate_readings):
        ok = gate() and ok
    _say("VERIFY " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
>>>>>>> theirs
