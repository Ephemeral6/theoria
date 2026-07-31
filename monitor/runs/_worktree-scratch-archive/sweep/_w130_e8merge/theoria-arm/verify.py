"""theoria-arm's completion gate.

    cd theoria-arm && python verify.py

Three rungs, and the territory is finished only if all three are green:

  1. the suite passes -- and collects a plausible number of tests;
  2. the arm runs once, end to end, **offline against `proxy/mock`**;
  3. the artefacts that run produced have the fields they claim to have, in the
     counts they claim to have them in.

Rung 3 is the one that is usually missing.  A green suite says the code does
what its author thought; it does not say the arm ran, and it does not say the
manifest it wrote still carries the fields the provenance convention requires.

Money, the key, and the network
-------------------------------
**This gate never spends, never reaches the network, and never needs
`ARC_API_KEY`.**  `harness/run.py` has two shapes and only one of them is safe
to automate:

* `python -m harness.run --mock` -- the whole shell against `proxy/mock`, with
  the mock's own literal fake key (`mock-arc-key-0000000000000000`),
  `require_key=False`, and the inner loop in `offline=True`.  No credential is
  read, no model is called, nothing leaves the machine.  The env proxy does
  bind a loopback socket and talk to an in-process mock over it; that is a
  socket, not a network call, and it is the same arrangement the arm's own
  docstring calls "no key, no network".
* the same command **without** `--mock` plays the live ARC API and requires the
  credential; `--desk` turns `offline` off and makes real model calls.  Neither
  form is invoked here, at any budget, for any reason.  A gate that spends is
  not a gate.

Belt and braces: the child is launched with `ARC_API_KEY` and
`ANTHROPIC_API_KEY` stripped from its environment, so if some future edit ever
did route the gate at the live path it would fail loudly instead of quietly
billing someone.  No credential value is ever printed, logged, or compared
against here -- the sealing evidence this gate reads is the *count* of
credential occurrences the arm itself records, which is 0 or it is a finding.

The sealed pile
---------------
The game is pinned to `g50t-5849a774` and checked against
`arc-recon/data/piles.json` **before** anything runs: if it is not in the
development pile the gate refuses to run at all.  Afterwards, rung 3 reads the
manifest's own `sealing` block and requires `sealed_pile_untouched` to be
literally `True` and `sealed_game_ids_found` to be empty.

Two rules this gate keeps, because breaking either is how gates in this repo
have failed before
------------------------------------------------------------------------------
**It does not write into the working tree.**  `harness.run` and
`armtools.archive` both resolve their output through `_bootstrap.path("runs",
...)`, which is hard-wired to `theoria-arm/runs/` and has no CLI override -- and
`runs/*/` is *tracked*, so a naive gate would drop a whole run directory into
the repo on every invocation.  So the run is driven by a small in-process driver
written into a `tempfile.mkdtemp()`, which patches `_bootstrap.path` before
`harness.run` is imported (it snapshots `RUNS_DIR` at import time) and therefore
redirects both the run and the archive step out of the tree.  The scratch
directory is removed in a `finally`.  ablation-arm's first `verify.sh` dropped
files into `artifacts/` and turned the arm's own read-only test red -- the gate
broke the thing it was guarding.

**An empty result is not a pass.**  Every count is checked against a floor
written down below with the reason for its value.  `figures/verify.sh` prints
"ok" when both of its builds produced nothing at all, because two empty trees
are byte-identical; a run that silently produced nothing reads exactly like a
run that is fine unless someone writes the floor down.  Nothing here uses
`dict.get(field, <the value I want>)`: a missing field is a missing field.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PILES = os.path.join(REPO, "arc-recon", "data", "piles.json")

# The development pile game this gate plays against the mock.  Pinned, not
# defaulted, and checked against piles.json before the run -- see `dev_pile()`.
GAME = "g50t-5849a774"

# Small enough that the gate stays a gate (the mock run is under a second at
# this budget) and large enough that the ledger, the scorecard and the world
# summary all have something in them.
BUDGET_ACTIONS = 6

# --------------------------------------------------------------------------
# Floors.  Not decoration: the number below which "the arm ran" stops being
# true.
# --------------------------------------------------------------------------

# The suite is 51 tests in tests/test_arm.py (pytest.ini pins testpaths=tests).
# 45 survives a couple of honest deletions and still goes red if the one test
# file stops being collected -- which is the failure this floor exists for,
# because pytest exits 0 on a suite of one test just as happily as on 51.
MIN_TESTS = 45

# One env_step per budgeted action is the weakest true statement about a run
# that spent its whole budget.  The observed mock run makes 7 (6 actions + the
# RESET).
MIN_ENV_STEPS = BUDGET_ACTIONS

# run_start + run_end + one step per action.  The observed run writes 11
# records (those two, two env_meta, seven env_step).
MIN_LEDGER_RECORDS = BUDGET_ACTIONS + 2

# The manifest enumerates the run directory.  The observed run leaves 12 files
# (ledger, run.json, RUN_STATE, theorize, plan, certify, commit, turns,
# surprises, desk log, desk failures, trace).  8 means the run got past its
# opening beats; a run directory holding only a ledger is a run that died.
MIN_RUN_FILES = 8

# The scorecard is the environment's own count, independent of the ledger.  If
# it disagrees with the budget the two books have diverged.
MIN_SCORECARD_ACTIONS = BUDGET_ACTIONS

# CLAUDE.md's provenance convention requires prompt_id / branch / base_commit /
# utc; armtools.archive writes a superset.  Listed in full so that a field
# quietly disappearing from the manifest is a red gate and not a shrug.
REQUIRED_MANIFEST = (
    "arm", "arm_version", "base_commit", "branch", "budget", "cost", "files",
    "game_id", "ledger", "outcome", "prompt_id", "run_id", "scorecard",
    "sealing", "seed", "slug", "world",
)

# The `sealing` block armtools.archive computes from the ledger.  Each entry is
# (key, required exact value).  Compared with `is`/`==` against the literal --
# never `get(key, True)`, which would turn a vanished sealing check into a pass.
REQUIRED_SEALING = (
    ("sealed_pile_untouched", True),
    ("cut_integrity", True),
    ("sealed_pile_requests", 0),
    ("bypass_attempts", 0),
    ("credential_in_body", 0),   # a count, never a value.  0 or it is a finding.
    ("incidents", 0),
)

# The driver.  Written into the scratch directory, never into the tree.
DRIVER = r'''
import os
import sys

ARM, OUT, SLUG, GAME, BUDGET = sys.argv[1:6]
sys.path.insert(0, ARM)

import _bootstrap

# Redirect every artefact this run produces out of the working tree.  Must
# happen before `harness.run` is imported: it snapshots RUNS_DIR at import
# time, while armtools.archive resolves the path per call.
_orig_path = _bootstrap.path


def _path(*parts):
    if parts and parts[0] == "runs":
        return os.path.join(OUT, *parts[1:])
    return _orig_path(*parts)


_bootstrap.path = _path

from harness.run import main as run_main          # noqa: E402

argv = ["--mock", "--slug", SLUG, "--game", GAME, "--budget", BUDGET]
assert "--mock" in argv and "--desk" not in argv, "offline only"
rc = run_main(argv)
if rc != 0:
    raise SystemExit("harness.run returned %r" % (rc,))

from armtools.archive import build               # noqa: E402

build(SLUG, prompt_id="S14-gate")
'''


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


def dev_pile(problems):
    """The development pile, straight off `arc-recon/data/piles.json`.

    Read before anything runs.  An unreadable or malformed piles.json is RED,
    not "assume the game is fine" -- the whole point of the cut is that it is
    not assumed.
    """
    if not os.path.exists(PILES):
        fail(problems, "arc-recon/data/piles.json is absent; the pile cut "
                       "cannot be checked and so no game may be played")
        return None
    try:
        with open(PILES, encoding="utf-8") as fh:
            piles = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        fail(problems, "arc-recon/data/piles.json unreadable: %s" % exc)
        return None
    if "dev_pile" not in piles or "sealed_pile" not in piles:
        fail(problems, "piles.json has no dev_pile/sealed_pile keys")
        return None
    dev = set(piles["dev_pile"])
    if GAME not in dev:
        fail(problems, "the pinned game %s is NOT in the development pile "
                       "(%s) -- refusing to run" % (GAME, ", ".join(sorted(dev))))
        return None
    return dev


def rung_tests(problems):
    print("[1/3] suite")
    # `-o addopts=` neutralises pytest.ini's `-q`, so `-q --collect-only` prints
    # one node id per line here exactly as it does in a territory with no ini.
    # Counting node ids is how the test-count floor gets an integer instead of
    # a substring match on a summary line.
    r = sh([sys.executable, "-m", "pytest", "-o", "addopts=",
            "-p", "no:cacheprovider", "-q", "--collect-only"])
    if r.returncode == 5:
        fail(problems, "pytest collected nothing -- testpaths misconfigured, "
                       "which is a broken gate, not a passing one")
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

    r = sh([sys.executable, "-m", "pytest", "-o", "addopts=",
            "-p", "no:cacheprovider", "-q"])
    if r.returncode == 5:
        fail(problems, "pytest collected nothing on the real run")
        return
    if r.returncode != 0:
        fail(problems, "suite red (exit %d)\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return
    print("   ok    %d tests collected, suite green" % len(collected))


def rung_real_run(problems, scratch, runs_dir, slug):
    print("[2/3] one real run -- the whole arm, offline against proxy/mock")
    driver = os.path.join(scratch, "_gate_driver.py")
    with open(driver, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(DRIVER)

    r = sh([sys.executable, driver, HERE, runs_dir, slug, GAME,
            str(BUDGET_ACTIONS)])
    if r.returncode != 0:
        fail(problems, "the offline run exited %d\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return False

    run_dir = os.path.join(runs_dir, slug)
    manifest = os.path.join(run_dir, "MANIFEST.json")
    ledger = os.path.join(run_dir, "ledger.jsonl")
    for path, what in ((manifest, "MANIFEST.json"), (ledger, "ledger.jsonl")):
        if not os.path.exists(path):
            fail(problems, "the run exited 0 but wrote no %s" % what)
            return False
    print("   ok    game %s, budget %d actions, no key, no network"
          % (GAME, BUDGET_ACTIONS))
    return True


def rung_artefacts(problems, runs_dir, slug, dev):
    print("[3/3] artefact self-check")
    run_dir = os.path.join(runs_dir, slug)

    with open(os.path.join(run_dir, "MANIFEST.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)

    missing = [f for f in REQUIRED_MANIFEST if f not in manifest]
    if missing:
        # Deliberately `not in`, not `get(f, <what we want>)`.  A gate that
        # defaults a missing field to the value it hopes for passes a run in
        # which the field silently disappeared.  `seed` is legitimately null
        # in this arm, which is exactly why presence and value are separate
        # questions here.
        fail(problems, "MANIFEST.json is missing %s" % ", ".join(missing))
        return

    if manifest["game_id"] != GAME:
        fail(problems, "manifest game_id is %r, not the pinned %r"
             % (manifest["game_id"], GAME))
    if manifest["arm"] != "theoria":
        fail(problems, "manifest arm is %r, not 'theoria'" % (manifest["arm"],))

    files = manifest["files"]
    if not isinstance(files, list) or len(files) < MIN_RUN_FILES:
        fail(problems, "manifest lists %s run file(s), floor is %d -- a run "
                       "directory with almost nothing in it is not a run"
             % (len(files) if isinstance(files, list) else "non-list",
                MIN_RUN_FILES))

    # -- the ledger -------------------------------------------------------
    records, steps = [], 0
    with open(os.path.join(run_dir, "ledger.jsonl"), encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(problems, "ledger line %d is not JSON: %s" % (n, exc))
                return
            records.append(rec)
            if rec.get("event") == "env_step":
                steps += 1

    if len(records) < MIN_LEDGER_RECORDS:
        fail(problems, "ledger has %d record(s), floor is %d -- an empty "
                       "ledger is not a pass" % (len(records), MIN_LEDGER_RECORDS))
        return
    if steps < MIN_ENV_STEPS:
        fail(problems, "only %d env_step record(s), floor is %d for a %d-action "
                       "budget" % (steps, MIN_ENV_STEPS, BUDGET_ACTIONS))
    events = {r.get("event") for r in records}
    for required in ("run_start", "run_end"):
        if required not in events:
            fail(problems, "the ledger has no %s record -- run.py's finally "
                           "clause exists so that this can never happen" % required)

    # -- the scorecard ----------------------------------------------------
    scorecard = manifest["scorecard"]
    if not isinstance(scorecard, dict) or "total_actions" not in scorecard:
        fail(problems, "manifest scorecard is absent or carries no "
                       "total_actions: %r" % (scorecard,))
    elif scorecard["total_actions"] < MIN_SCORECARD_ACTIONS:
        fail(problems, "scorecard reports %d action(s), floor is %d"
             % (scorecard["total_actions"], MIN_SCORECARD_ACTIONS))

    # -- sealing ----------------------------------------------------------
    sealing = manifest["sealing"]
    if not isinstance(sealing, dict):
        fail(problems, "manifest sealing block is not a dict: %r" % (sealing,))
    else:
        for key, want in REQUIRED_SEALING:
            if key not in sealing:
                fail(problems, "sealing block has no %r -- a vanished sealing "
                               "check is not a passed one" % key)
            elif sealing[key] != want:
                fail(problems, "sealing[%r] is %r, required %r"
                     % (key, sealing[key], want))
        found = sealing.get("sealed_game_ids_found")
        if found is None:
            fail(problems, "sealing block has no sealed_game_ids_found")
        elif found:
            fail(problems, "SEALED PILE CONTACT: %s appear in the ledger"
                 % ", ".join(map(str, found)))
        seen = sealing.get("game_ids_anywhere_in_the_records")
        if seen is None:
            fail(problems, "sealing block has no game_ids_anywhere_in_the_records")
        else:
            stray = [g for g in seen if g not in dev]
            if stray:
                fail(problems, "the ledger mentions non-development-pile "
                               "game(s): %s" % ", ".join(map(str, stray)))

    if not problems:
        print("   ok    %d ledger records (%d env_steps), %d run files, all %d "
              "manifest fields, sealing clean, dev pile only"
              % (len(records), steps, len(files), len(REQUIRED_MANIFEST)))


def main():
    problems = []
    scratch = tempfile.mkdtemp(prefix="theoria-arm-verify-")
    try:
        dev = dev_pile(problems)
        rung_tests(problems)
        if dev is not None:
            runs_dir = os.path.join(scratch, "runs")
            os.makedirs(runs_dir, exist_ok=True)
            slug = "gate-offline-smoke"
            if rung_real_run(problems, scratch, runs_dir, slug):
                rung_artefacts(problems, runs_dir, slug, dev)
        else:
            print("[2/3] skipped -- the pile cut could not be verified")
            print("[3/3] skipped")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if problems:
        print("theoria-arm: RED (%d problem(s))" % len(problems))
        return 1
    print("theoria-arm: green -- suite, one offline run, artefact fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
