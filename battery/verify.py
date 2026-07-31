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

Two rungs sit on top of those four.  The freeze rung (printed first) checks the
tree still matches BATTERY_V1.md.  The live-tier rung (printed last) checks the
committed `battery/artifacts_live/gaming_audit.live.json` against an in-process
recompute and against the frozen baseline it pins: the frozen
`battery/artifacts/gaming_audit.json` predates B17/V9 and still names nine
main-table metrics the live code demotes, PREREG_V9 §5 forbids rewriting it,
and the divergence is therefore a documented permanent fact — REPORTED
exit-code-neutrally, while the things that can rot around it (a stale
companion, a rewritten baseline, a vanished STATUS.md disclosure) are RED.

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
import re
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


def rung_freeze(problems):
    """[1/6] the freeze record: BATTERY_V1.md still describes this tree.

    The suite runs this same check (`test_freeze.py`), but the gate does not
    trust the suite to have been collected: one `addopts` line in `pytest.ini`
    can deselect the objecting test, which is why rung 2 also refuses a
    `deselected` tail.  Running the check in-process as well makes the freeze
    hold on two independent paths -- V5's adversarial pass demonstrated the
    single-path version being disarmed six different ways.
    """
    print("[1/6] the freeze record")
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery import freeze
    fails = freeze.check()
    if fails:
        fail(problems, "the battery freeze does not hold (%d):\n  - %s"
             % (len(fails), "\n  - ".join(fails)))
        return
    drift = freeze.readings_drift()
    if drift:
        print("   note  %d artefact(s) drifted from BATTERY_V1.md -- reported,"
              " not gated (Phase 4 recomputes on unseen inputs by design): %s"
              % (len(drift), ", ".join(drift)))
    print("   ok    the tree matches BATTERY_V1.md")


# The suite's pass-count floor.  375 tests pass on the tree this line was
# written against; a tail below this means a block of tests silently vanished
# even if nothing prints `deselected`.
MIN_TESTS_PASSED = 300


def rung_tests(problems):
    print("[2/6] suite")
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
    tail = (r.stdout.strip().splitlines() or ["(no output)"])[-1]
    # A deselected or uncollected test is treated like a failing one.  The
    # cheapest demonstrated way to disarm this gate was not a broken
    # assertion but one `addopts = -k ...` line in pytest.ini (BATTERY_V1.md
    # section 8.1), which exits 0 while every objecting test sits it out.
    if "deselected" in r.stdout:
        fail(problems, "the suite ran with tests deselected (%r) -- a "
                       "deselected test and a failing test are the same "
                       "verdict here; check pytest.ini for an `addopts` line"
             % tail)
        return
    m = re.search(r"(\d+) passed", tail)
    if not m or int(m.group(1)) < MIN_TESTS_PASSED:
        fail(problems, "the suite tail says %r; the gate requires at least "
                       "%d passing tests, so a green exit over a shrunken "
                       "collection is still red" % (tail, MIN_TESTS_PASSED))
        return
    print("   ok    %s" % tail)


def rung_real_run(problems, out_dir):
    print("[3/6] one real run -- the whole spectrum recomputed from the "
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
    print("[4/6] artefact self-check")
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
    """[5/6] the documents state the true separation count, and cannot go stale.

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
    print("[5/6] the separation claim in the committed documents")
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


def rung_live_tiers(problems, live_path=None, frozen_path=None,
                    status_path=None):
    """[6/6] the live-tier companion tracks the code, and the freeze holds.

    The frozen `battery/artifacts/gaming_audit.json` names nine main-table
    metrics; the live `tier_of()` demotes all of them (B17, then V9).
    `PREREG_V9.md` §5 forbids rewriting the baseline — the conflict stays in
    the open, in `battery/artifacts_live/gaming_audit.live.json`.  This rung
    keeps the four ways that arrangement can rot from rotting silently:

    * RED if the committed companion differs from an in-process recompute —
      the companion going stale is the same failure class as the frozen
      artefact's, one level up, and it is the one this rung exists to catch;
    * RED if the companion's `frozen_sha256` no longer matches the frozen
      file on disk — someone rewrote or regenerated the baseline, which is a
      PREREG violation either way, and a human must look before anything
      re-pins it;
    * the frozen-vs-live divergence itself is REPORTED, exit-code-neutrally.
      It is a documented permanent fact; a rung that is red forever is a rung
      people learn to ignore, which is this repo's own stated failure mode;
    * RED if divergence exists but STATUS.md no longer carries the disclosure
      — pinned as a derived sentence (the count read from the frozen file),
      the way rung 5 pins STATUS_CLAIM, so the sentence must track the
      artefact rather than merely having once been written.
    """
    print("[6/6] the live-tier companion artefact")
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.audit import live_tiers

    live_path = live_path or live_tiers.DEFAULT_OUT
    frozen_path = frozen_path or live_tiers.FROZEN
    status_path = status_path or os.path.join(HERE, "STATUS.md")
    before = len(problems)

    if not os.path.exists(live_path):
        fail(problems, "%s is absent; the live tiers have no committed form "
                       "to check. Generate it: python -m battery.audit."
                       "live_tiers" % live_path)
        return
    with open(live_path, encoding="utf-8") as fh:
        try:
            committed = json.load(fh)
        except json.JSONDecodeError as exc:
            fail(problems, "committed gaming_audit.live.json is not JSON: %s"
                 % exc)
            return

    # (ii) first, because (i)'s verdict reads differently under a rewritten
    # baseline: the recompute would differ *because* the pin moved.
    actual = live_tiers.frozen_sha256(frozen_path)
    if committed.get("frozen_sha256") != actual:
        fail(problems, "gaming_audit.live.json pins the frozen baseline at %s "
                       "but battery/artifacts/gaming_audit.json now hashes to "
                       "%s. The baseline is frozen by PREREG_V9.md §5; a "
                       "rewritten or regenerated baseline is a preregistration "
                       "violation and needs a human, not a re-pin."
             % (committed.get("frozen_sha256"), actual))

    # (i) the committed companion against an in-process recompute.
    fresh = live_tiers.build(frozen_path)
    if committed != fresh:
        changed = sorted(
            set(k for k in set(committed) | set(fresh)
                if committed.get(k) != fresh.get(k)))
        fail(problems, "committed gaming_audit.live.json differs from an "
                       "in-process recompute (top-level keys that moved: %s). "
                       "A stale companion is the exact failure this artefact "
                       "exists to make visible — regenerate and commit: "
                       "python -m battery.audit.live_tiers"
             % (", ".join(changed) or "byte-level only"))

    # (iii) the divergence table.  Reported, never fatal: it is a documented
    # permanent fact, disclosed in STATUS.md and checked below.
    diff = fresh["diff_vs_frozen"]
    if diff:
        print("   note  frozen-vs-live tier divergence, %d metric(s) "
              "(reported, not gated -- PREREG_V9 §5 keeps the frozen "
              "baseline in place and this file in the open):" % len(diff))
        for row in diff:
            print("         %-4s frozen=%-9s live=%s"
                  % (row["metric"], row["frozen"], row["live"]))

    # (iv) the disclosure.  Only demanded while there is something to disclose.
    if diff:
        with open(frozen_path, encoding="utf-8") as fh:
            frozen_doc = json.load(fh)
        claim = live_tiers.STALE_CLAIM % len(frozen_doc.get("main", []))
        try:
            with open(status_path, encoding="utf-8") as fh:
                status_text = fh.read()
        except OSError as exc:
            fail(problems, "could not read STATUS.md: %s" % exc)
            return
        if claim not in status_text:
            fail(problems, "the frozen and live audits diverge on %d "
                           "metric(s), but STATUS.md no longer carries the "
                           "disclosure; it must contain %r verbatim, so that "
                           "a reader of the status document cannot walk away "
                           "with the frozen main table as the current one."
                 % (len(diff), claim))

    if len(problems) == before:
        print("   ok    companion matches the recompute; baseline pin holds; "
              "%d divergence(s) disclosed in STATUS.md" % len(diff))


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
        rung_freeze(problems)
        rung_tests(problems)
        if rung_real_run(problems, out_dir):
            rung_artifact_fields(problems, out_dir)
            note = shipped_note(out_dir)
            if note:
                print("   note  %s" % note)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    rung_separation_claim(problems)
    rung_live_tiers(problems)

    print()
    if problems:
        print("battery: RED (%d problem(s))" % len(problems))
        return 1
    print("battery: green -- freeze, suite, one real run, artefact "
          "fields, separation claim, live tiers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
