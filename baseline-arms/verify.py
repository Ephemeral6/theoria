"""baseline-arms' completion gate.

    cd baseline-arms && python verify.py

Three rungs, and the territory is finished only if all three are green:

  1. the suite passes -- and collects a plausible number of tests;
  2. an **offline re-adjudication** of the campaign that was already run;
  3. an artefact self-check over both the fresh re-adjudication and the
     committed record, with every count against a written-down floor.

Rung 2 is weaker than the exemplar's, and honestly so
-----------------------------------------------------
`engine-rig/verify.py` rung 2 runs the real pipeline, because engine-rig's
pipeline is offline synthetic fixtures.  **This territory has no offline
pipeline entry point at all.**  Its two entry points are:

    python -m harness.run_pilot        # live ARC API, requires ARC_API_KEY
    python -m harness.run_campaign     # live ARC API, requires ARC_API_KEY

Both play real games against the live environment through
`proxy/spend_gate.py`, and the campaign this territory's record is built from
cost $13.06 of a $50 cap.  There is no `--mock`, no fixture server, no replay
mode.  **A gate that spends money on every invocation is not a gate**, and one
that needs a credential to say "done" cannot run in CI, so this gate does not
run the pipeline and says so rather than pretending rung 2 is what it is not.

What rung 2 does instead is re-derive the campaign's two conclusions from the
recorded cells, with two read-only adjudicators that take real work and can
really fail:

    python -m harness.summarise_envelope --json <tmp>   # the variance envelope
    python -m harness.audit_pool         --json <tmp>   # cells vs the spend pool

`audit_pool` is the sharper of the two: it reconciles each cell against
`proxy/var/spend_gate.jsonl`, the machine's single cross-session register of
money, and it exits 1 on any disagreement.  That is a genuine adjudication over
real recorded money -- it is just not a pipeline run, and this docstring is the
place that difference gets stated instead of being smoothed over.

Three things this gate deliberately does NOT run
------------------------------------------------
* `python -m harness.run_campaign --gate-only` re-evaluates the campaign gate
  offline, which is tempting -- but it **writes `out/campaign_gate.json` into
  the working tree** and appends to a ledger, with no output override.  A gate
  that rewrites the artefact it is checking cannot then check it, and it would
  paint the territory `dirty`/`drift` on every run.  So rung 3 reads the
  committed `out/campaign_gate.json` instead of regenerating it -- which means
  this gate verifies the artefact's *shape and contents*, not that the code
  still produces it.  That is a real gap and it is the direct cost of the
  no-writes rule.
* `python -m harness.campaign_status` reads only checkpoints -- but it reads
  them from `out/campaign/`, which is **untracked**, and it `return 1`s when
  the directory holds no checkpoints.  On any clean checkout that is a
  guaranteed red for a reason that has nothing to do with the territory being
  finished, so it is not a rung.
* anything that reads `ARC_API_KEY`.  Children here are launched with
  `ARC_API_KEY` and `ANTHROPIC_API_KEY` stripped from their environment, so an
  accidental live path fails loudly instead of quietly billing someone.  No
  credential value is read, printed, compared, or logged anywhere in this file.

The sealed pile
---------------
Every `game_id` in the recorded cells and in the fresh envelope is checked
against `arc-recon/data/piles.json`'s development pile.  A sealed id appearing
in this territory's record would mean live API contact with a sealed game, so
it is checked here rather than assumed -- and an unreadable piles.json is RED,
because the point of the cut is that it is not taken on trust.

An empty result is not a pass
-----------------------------
Every count below has an explicit floor with the reason for its value.  Nothing
here uses `dict.get(field, <the value I want>)`; a missing field is a missing
field, and zero cells is RED, never "ok (0 cells)".
"""

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PILES = os.path.join(REPO, "arc-recon", "data", "piles.json")

CELLS = os.path.join(HERE, "out", "campaign_cells.jsonl")
GATE_JSON = os.path.join(HERE, "out", "campaign_gate.json")

CAMPAIGN = "phase3-variance-envelope"    # harness.run_campaign.CAMPAIGN_NAME

# --------------------------------------------------------------------------
# Floors.  Not decoration: the number below which "the campaign happened"
# stops being true.
# --------------------------------------------------------------------------

# The suite is 75 tests across 5 files in tests/ (there is no pytest.ini
# anywhere in this territory, so the path is passed explicitly).  60 survives
# honest deletions and still goes red if a whole test file stops being
# collected -- pytest exits 0 on a suite of one test just as happily as on 75.
MIN_TESTS = 60

# The recorded campaign is the development pile -- 4 games -- at 3 repeats
# each.  12 is not "roughly how many there are": it is what a variance envelope
# over the dev pile *is*, and one fewer means a cell was dropped from the
# record after the money for it was spent.
MIN_CELLS = 12

# A spread needs at least three points; two give one degree of freedom and a
# standard deviation nobody should quote.
MIN_REPEATS_PER_GAME = 3

# The envelope names one exclusion (ar25-0c556536, degraded under INC-BA-003),
# so 4 dev-pile games minus 1 named exclusion = 3 usable games.  Below that the
# pooled CV is one game's noise wearing the pile's name.
MIN_ENVELOPE_GAMES = 3

# 3 games x (3 repeats - 1) = 6.  Derived, not observed.
MIN_DOF = 6

# 12 cells x 30 budgeted actions = 360 actions were paid for.  The territory's
# own policy sets `action_success_floor = 0.35` (out/campaign_gate.json caps),
# so 360 * 0.35 = 126 is the point below which the campaign's own rule says the
# arm was not usable -- and an envelope built on that is measuring the API's
# failure mode, not the arm.  The recorded run made 286.
MIN_ACTIONS_OK = 126

# Required top-level fields.  Listed in full so that one quietly disappearing
# is a red gate and not a shrug.
REQUIRED_GATE = ("barriers", "caps", "evaluated_at", "g4_judges_cells",
                 "state", "totals", "tripped")
REQUIRED_TOTALS = ("action_success_rate", "actions_failed", "actions_ok",
                   "cells", "cost_usd", "http_calls")
REQUIRED_ENVELOPE = ("degrees_of_freedom", "excluded", "games", "pooled_cv",
                     "sizing")
REQUIRED_CELL = ("actions_ok", "budget", "campaign", "cost_usd", "game_id",
                 "outcome", "repeat", "run_id")
REQUIRED_POOL = ("all_cells", "campaign", "cells", "clean", "problem_count")


def child_env():
    """The environment a gate child gets.

    Two changes from ours, both deliberate:

    * `ARC_API_KEY` / `ANTHROPIC_API_KEY` are removed.  Nothing this gate runs
      should want them, and if something ever does it should die rather than
      spend.
    * `PYTHONIOENCODING=utf-8` so the child *encodes* what we *decode*.  The
      host locale here is cp936; decoding a cp936 stream as UTF-8 mojibakes at
      best, and this pins both ends instead of only one.
    """
    env = dict(os.environ)
    env.pop("ARC_API_KEY", None)
    env.pop("ANTHROPIC_API_KEY", None)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def sh(argv, cwd=HERE):
    """Run a stage, decoding as UTF-8 rather than as the host locale.

    `text=True` alone decodes with cp936 on this box; a child printing UTF-8
    then either mojibakes or raises UnicodeDecodeError inside subprocess.run,
    and a checker that dies decoding its child is a checker that did not check.
    """
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=child_env())


def fail(problems, message):
    print("   FAIL  %s" % message)
    problems.append(message)


def load_json(problems, path, what):
    if not os.path.exists(path):
        fail(problems, "%s is absent (%s)" % (what, path))
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        fail(problems, "%s unreadable: %s" % (what, exc))
        return None


def dev_pile(problems):
    """The development pile, straight off `arc-recon/data/piles.json`."""
    piles = load_json(problems, PILES, "arc-recon/data/piles.json")
    if piles is None:
        return None
    if "dev_pile" not in piles or "sealed_pile" not in piles:
        fail(problems, "piles.json has no dev_pile/sealed_pile keys; the cut "
                       "cannot be checked and so nothing may be certified")
        return None
    return set(piles["dev_pile"]), set(piles["sealed_pile"])


def check_pile(problems, dev, sealed, ids, where):
    breach = sorted(g for g in ids if g in sealed)
    if breach:
        fail(problems, "SEALED PILE CONTACT in %s: %s" % (where, ", ".join(breach)))
    stray = sorted(g for g in ids if g not in dev and g not in sealed)
    if stray:
        fail(problems, "%s names game id(s) in neither pile: %s"
             % (where, ", ".join(stray)))


# ---------------------------------------------------------------- rung 1

def rung_tests(problems):
    print("[1/3] suite")
    # There is no pytest.ini anywhere in this territory, so `tests` is passed
    # explicitly; a bare `python -m pytest` here happens to collect the same 75
    # today, but that is an accident of the rootdir it picks, not a promise.
    base = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q"]
    r = sh(base + ["--collect-only", "tests"])
    if r.returncode == 5:
        fail(problems, "pytest collected nothing under tests/ -- a check that "
                       "cannot run is broken, not passing")
        return
    if r.returncode != 0:
        fail(problems, "collection failed (exit %d)\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return
    collected = [ln for ln in r.stdout.splitlines() if "::" in ln]
    if len(collected) < MIN_TESTS:
        fail(problems, "only %d tests collected, floor is %d -- a suite that "
                       "shrank to nothing exits 0 like any other"
             % (len(collected), MIN_TESTS))
        return

    r = sh(base + ["tests"])
    if r.returncode == 5:
        fail(problems, "pytest collected nothing on the real run")
        return
    if r.returncode != 0:
        fail(problems, "suite red (exit %d)\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return
    print("   ok    %d tests collected, suite green" % len(collected))


# ---------------------------------------------------------------- rung 2

def rung_readjudicate(problems, scratch):
    print("[2/3] offline re-adjudication -- NOT a pipeline run (see docstring)")
    env_out = os.path.join(scratch, "envelope.json")
    pool_out = os.path.join(scratch, "pool.json")

    r = sh([sys.executable, "-m", "harness.summarise_envelope",
            "--json", env_out])
    if r.returncode != 0:
        fail(problems, "summarise_envelope exited %d\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return None, None
    if not os.path.exists(env_out):
        fail(problems, "summarise_envelope exited 0 but wrote no envelope")
        return None, None

    # audit_pool returns 1 on any cell that disagrees with the shared spend
    # pool.  Its exit code is the whole point of running it; it is checked, not
    # grepped for.
    r = sh([sys.executable, "-m", "harness.audit_pool",
            "--campaign", CAMPAIGN, "--json", pool_out])
    if r.returncode != 0:
        fail(problems, "audit_pool exited %d -- cells disagree with the shared "
                       "spend pool\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return env_out, None
    if not os.path.exists(pool_out):
        fail(problems, "audit_pool exited 0 but wrote no report")
        return env_out, None

    print("   ok    envelope re-derived, %d cell(s) reconciled against the "
          "spend pool" % json.load(open(pool_out, encoding="utf-8"))["all_cells"])
    return env_out, pool_out


# ---------------------------------------------------------------- rung 3

def check_envelope(problems, path, dev, sealed, label):
    env = load_json(problems, path, label)
    if env is None:
        return
    missing = [f for f in REQUIRED_ENVELOPE if f not in env]
    if missing:
        fail(problems, "%s is missing %s" % (label, ", ".join(missing)))
        return

    games = env["games"]
    if not isinstance(games, dict) or len(games) < MIN_ENVELOPE_GAMES:
        fail(problems, "%s covers %s game(s), floor is %d -- an envelope over "
                       "nothing is not an envelope"
             % (label, len(games) if isinstance(games, dict) else "non-dict",
                MIN_ENVELOPE_GAMES))
        return
    check_pile(problems, dev, sealed, set(games), label)

    for gid, g in sorted(games.items()):
        if "repeats" not in g:
            fail(problems, "%s: game %s has no repeats list" % (label, gid))
            continue
        if len(g["repeats"]) < MIN_REPEATS_PER_GAME:
            fail(problems, "%s: game %s has %d repeat(s), floor is %d"
                 % (label, gid, len(g["repeats"]), MIN_REPEATS_PER_GAME))

    if env["degrees_of_freedom"] < MIN_DOF:
        fail(problems, "%s reports %d degrees of freedom, floor is %d"
             % (label, env["degrees_of_freedom"], MIN_DOF))

    cv = env["pooled_cv"]
    if not isinstance(cv, dict) or not cv:
        fail(problems, "%s pooled_cv is empty -- no metric produced a usable "
                       "spread, which is a finding and not a pass" % label)
    elif all(v is None for v in cv.values()):
        fail(problems, "%s pooled_cv is present but every metric is null"
             % label)


def check_pool(problems, path):
    rep = load_json(problems, path, "audit_pool report")
    if rep is None:
        return
    missing = [f for f in REQUIRED_POOL if f not in rep]
    if missing:
        fail(problems, "audit_pool report is missing %s" % ", ".join(missing))
        return
    if rep["clean"] is not True:
        fail(problems, "audit_pool report is not clean: %d problem(s)"
             % rep["problem_count"])
    if rep["all_cells"] < MIN_CELLS:
        fail(problems, "audit_pool saw %d cell(s), floor is %d"
             % (rep["all_cells"], MIN_CELLS))
    if rep["campaign"] != CAMPAIGN:
        fail(problems, "audit_pool report is for campaign %r, expected %r"
             % (rep["campaign"], CAMPAIGN))


def check_cells(problems, dev, sealed):
    if not os.path.exists(CELLS):
        fail(problems, "out/campaign_cells.jsonl is absent -- the campaign's "
                       "record is the territory's whole output")
        return
    rows, per_game = [], {}
    with open(CELLS, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(problems, "campaign_cells.jsonl line %d is not JSON: %s"
                     % (n, exc))
                return
            rows.append(row)

    if len(rows) < MIN_CELLS:
        fail(problems, "only %d cell(s) recorded, floor is %d -- an empty or "
                       "thinned record is not a pass" % (len(rows), MIN_CELLS))
        return

    for i, row in enumerate(rows):
        missing = [f for f in REQUIRED_CELL if f not in row]
        if missing:
            fail(problems, "cell %d is missing %s" % (i, ", ".join(missing)))
            return
        per_game.setdefault(row["game_id"], []).append(row)

    check_pile(problems, dev, sealed, set(per_game), "out/campaign_cells.jsonl")
    for gid, cells in sorted(per_game.items()):
        if len(cells) < MIN_REPEATS_PER_GAME:
            fail(problems, "game %s has %d repeat(s) in the record, floor is %d"
                 % (gid, len(cells), MIN_REPEATS_PER_GAME))
    return rows


def check_gate_json(problems):
    gate = load_json(problems, GATE_JSON, "out/campaign_gate.json")
    if gate is None:
        return
    missing = [f for f in REQUIRED_GATE if f not in gate]
    if missing:
        # `not in`, never `get(f, <what I want>)`: defaulting a vanished field
        # to the value the gate hopes for passes a run that lost it.
        fail(problems, "out/campaign_gate.json is missing %s"
             % ", ".join(missing))
        return

    totals = gate["totals"]
    if not isinstance(totals, dict):
        fail(problems, "campaign_gate totals is not a dict")
        return
    missing = [f for f in REQUIRED_TOTALS if f not in totals]
    if missing:
        fail(problems, "campaign_gate totals is missing %s" % ", ".join(missing))
        return

    if totals["cells"] < MIN_CELLS:
        fail(problems, "campaign_gate counts %d cell(s), floor is %d"
             % (totals["cells"], MIN_CELLS))
    if totals["actions_ok"] < MIN_ACTIONS_OK:
        fail(problems, "only %d successful action(s) across the campaign, floor "
                       "is %d (12 cells x 30 budgeted x the territory's own "
                       "0.35 success floor)"
             % (totals["actions_ok"], MIN_ACTIONS_OK))
    if gate["state"] != "green":
        fail(problems, "campaign gate state is %r, tripped=%s"
             % (gate["state"], gate["tripped"]))
    elif gate["tripped"]:
        fail(problems, "campaign gate says green but lists tripped caps: %s"
             % (gate["tripped"],))


def committed_envelope_drift(fresh_path):
    """Does a committed `runs/*/envelope.json` still match a fresh re-derivation?

    Reported, not fatal.  The committed envelope is a snapshot taken at a
    moment; the fresh one is what the recorded cells say today.  A difference
    is a real finding about the record, but it belongs to whoever owns the
    record rather than to whichever branch happens to be running the gate --
    the same split `monitor/gates.py` draws between `dirty` and `drift`.
    """
    paths = sorted(glob.glob(os.path.join(HERE, "runs", "*", "envelope.json")))
    if not paths:
        return "no committed runs/*/envelope.json to compare against"
    newest = paths[-1]
    try:
        with open(newest, encoding="utf-8") as fh:
            committed = json.load(fh)
        with open(fresh_path, encoding="utf-8") as fh:
            fresh = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return "could not compare %s: %s" % (os.path.basename(newest), exc)
    if committed == fresh:
        return None
    return ("%s differs from a fresh re-derivation over the current cells"
            % os.path.relpath(newest, HERE).replace(os.sep, "/"))


def rung_artefacts(problems, env_out, pool_out, dev, sealed):
    print("[3/3] artefact self-check")
    if env_out:
        check_envelope(problems, env_out, dev, sealed,
                       "the freshly re-derived envelope")
    if pool_out:
        check_pool(problems, pool_out)
    rows = check_cells(problems, dev, sealed)
    check_gate_json(problems)
    if not problems:
        print("   ok    %d recorded cells over %d dev-pile game(s), envelope "
              "and spend pool both clean, campaign gate green"
              % (len(rows), len({r["game_id"] for r in rows})))


def main():
    problems = []
    scratch = tempfile.mkdtemp(prefix="baseline-arms-verify-")
    try:
        piles = dev_pile(problems)
        rung_tests(problems)
        env_out, pool_out = rung_readjudicate(problems, scratch)
        if piles is None:
            print("[3/3] skipped -- the pile cut could not be verified")
        else:
            dev, sealed = piles
            rung_artefacts(problems, env_out, pool_out, dev, sealed)
            if env_out:
                drift = committed_envelope_drift(env_out)
                if drift:
                    print("   note  %s" % drift)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if problems:
        print("baseline-arms: RED (%d problem(s))" % len(problems))
        return 1
    print("baseline-arms: green -- suite, offline re-adjudication (NOT a "
          "pipeline run: the pipeline is live-API only), artefact fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
