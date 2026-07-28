"""proxy's completion gate.

    cd proxy && python verify.py

Three rungs, and the territory is finished only if all three are green:

  1. the suite passes;
  2. the real pipeline runs once, offline -- one whole game through both
     proxies against the mocks: no key, no network, no cost;
  3. the ledger that run produced carries the envelope `LEDGER_FORMAT.md` v1.0
     requires on every record, its `seq` is dense from 1, and it passes the
     format's own executable checker.

Rung 3 is the one that is usually missing.  A green suite says the writer does
what its author thought; it does not say a game was played, and it does not say
the stream it emitted still matches the format document.  The two are different
claims and only the second one is "this territory is done".

Three rules this gate keeps, because breaking any of them is how gates in this
repo have failed before:

**It does not write into the working tree, and it does not touch the shared
spend pool.**  `python -m proxy.runner --mock` is the documented invocation and
it is *not* what runs here, for a reason worth stating: `runner.main` writes to
three places the CLI cannot move.  `--ledger` moves the ledger; `runs_dir` and
`scoring.SCORES_DIR` are hardcoded under `proxy/var/`; and `default_gate()`
resolves the spend policy's relative ledger against the **main checkout**, on
purpose (see `spend_gate.POOL_ROOT`), so a `--mock` run from a worktree appends
its fictional dollars to `proxy/var/spend_gate.jsonl` in the main checkout --
the tracked, shared, cross-session pool a live campaign reads to decide whether
it may spend.  A gate that runs on every pass would eat real headroom, and the
gate is deliberately unable to tell the difference.  So this calls
`runner.run_game` -- the same function `main` calls, with the same mocks and
the same arguments -- with all four destinations inside a mkdtemp that is
removed on the way out.  `set_default_gate` is the sanctioned way to do that:
its docstring names "a caller that is deliberately running against a scratch
pool and knows it", and `tests/conftest.py` uses it for the whole session.

**An empty result is not a pass.**  Every count is checked against a floor
written down here with its reason.  A ledger holding nothing but `run_start`
and `run_end` is a perfectly valid ledger and passes every structural check;
`figures/verify.sh` prints "ok" today when both of its builds produced nothing,
because two empty trees are byte-identical.  Zero goes red here.

**A known leak is named, not hidden.**  Rung 1 -- the suite itself -- writes
one JSON file per scored run into `proxy/var/scores/`.  `tests/conftest.py`
redirects the spend pool but not `scoring.SCORES_DIR`, and that default is
bound at function-definition time so it cannot be redirected from outside.
`proxy/var/` is gitignored, so `git status` stays clean and nothing tracked
moves -- but it is still a write into the working tree, it is not this gate's
to fix without editing the territory, and it is reported below rather than left
for someone to discover.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
VAR = os.path.join(HERE, "var")

LEDGER_VERSION = "1.0"

# The common envelope every record carries, whatever its type.
# LEDGER_FORMAT.md v1.0 §2.
ENVELOPE_REQUIRED = ("arm", "event", "run_id", "seq", "ts", "v")

# Every top-level key a run record must carry.  `proxy/runner.py` writes one
# per game into `runs/<run_id>.json`.
RUN_REQUIRED = ("arm", "env_proxy", "game_id", "ledger", "model_proxy",
                "reconciliation", "run_id", "score", "scorer", "spend",
                "summary")

# Floors.  Not decoration: the number below which "the pipeline ran" stops
# being true.  A mock game at the runner's default budget of 40 produces about
# 61 records -- 29 `env_step`, 28 `model_call`, 2 `env_meta`, and the pair of
# bookends.  The floors sit well under that so an ordinary change does not turn
# them red, and well over zero so a silent emptying cannot read as green.
#
# 25 records: run_start + run_end + the two env_meta is 4.  A file at 4 is a
# run that opened a scorecard and closed it without playing.
MIN_RECORDS = 25
# 10 environment steps: a quarter of the budget.  Under ten the arm did not
# play a game, it failed at RESET and the ledger recorded the failure tidily.
MIN_ENV_STEPS = 10
# 10 model calls: the model side is half of what "closed system" means.  A
# ledger with environment steps and no model calls is a proxy pair with one
# proxy dead, and every structural check would still pass on it.
MIN_MODEL_CALLS = 10
# Exact, not floors.  One run is one game is one scorecard, and the bookends
# are written once each by `RunLedger`.
EXPECT_RUN_START = 1
EXPECT_RUN_END = 1


def sh(argv, cwd=HERE, stdin=None):
    """Run a stage, decoding as UTF-8 rather than as the host locale.

    `text=True` alone decodes with cp936 on this box; a child printing UTF-8
    then either mojibakes or raises UnicodeDecodeError inside subprocess.run,
    and a checker that dies decoding its child is a checker that did not check.

    The child's environment has both credentials removed.  This territory is
    the one place in the repo that *is* network-facing, so "offline" has to be
    a property of the run and not a claim about it: with no key in the
    environment, a stage that reached upstream by mistake fails rather than
    spends.
    """
    env = dict(os.environ)
    for name in ("ARC_API_KEY", "ANTHROPIC_API_KEY"):
        env.pop(name, None)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env,
                          input=stdin)


def fail(problems, message):
    print("   FAIL  %s" % message)
    problems.append(message)


def rung_tests(problems):
    print("[1/3] suite")
    # No `-q`: pytest.ini already sets it, and a second one suppresses the
    # summary line this prints.
    r = sh([sys.executable, "-m", "pytest"])
    if r.returncode == 5:
        # pytest found nothing to run.  Read as green this would be one more
        # instance of this repo mistaking a check that could not run for one
        # that passed.
        fail(problems, "pytest collected nothing -- testpaths misconfigured, "
                       "which is a broken gate, not a passing one")
        return
    if r.returncode != 0:
        fail(problems, "suite red (exit %d)\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return
    print("   ok    %s" % (r.stdout.strip().splitlines() or ["(no output)"])[-1])


# The real run.  Everything `runner.main --mock` does, with the four
# destinations moved out of tree and off the shared pool.  Fed on stdin so the
# gate creates no file anywhere but the mkdtemp.
PLAY = r'''
import functools, os, sys
repo, scratch = sys.argv[1], sys.argv[2]
sys.path.insert(0, repo)

from proxy import scoring
from proxy.spend_gate import SpendGate, SpendPolicy, set_default_gate

# `score_run`'s `scores_dir` default is bound at def time, so the module
# attribute cannot be reassigned to move it.  Binding the keyword is the only
# way to keep the scored artefact out of proxy/var/.
scoring.score_run = functools.partial(scoring.score_run,
                                      scores_dir=os.path.join(scratch, "scores"))

# A scratch pool, so this gate's fictional dollars never reach the tracked
# cross-session ledger the real campaigns draw on.
set_default_gate(SpendGate(SpendPolicy({
    "v": "1.0", "pool": "verify-scratch",
    "usd_ceiling": 1000.0, "action_ceiling": 100000,
    "ledger": os.path.join(scratch, "spend_gate.jsonl"),
    "default_ttl_seconds": 3600, "lock_timeout_seconds": 30.0,
    "default_run_caps": {"usd": 5.0, "actions": 600},
}, source=None)))

from proxy.runner import run_game
from proxy.mock.arc_mock import DEFAULT_GAME, DEFAULT_KEY as ARC_KEY, MockArc
from proxy.mock.model_mock import DEFAULT_KEY as MODEL_KEY, MockProvider

with MockArc(api_key=ARC_KEY, games=[DEFAULT_GAME]) as arc, \
        MockProvider(api_key=MODEL_KEY) as provider:
    record = run_game(DEFAULT_GAME, arm="mock_arm", budget=40,
                      env_upstream=arc.base_url,
                      model_upstream=provider.base_url,
                      env_key=ARC_KEY, model_key=MODEL_KEY,
                      require_keys=False,
                      ledger_path=os.path.join(scratch, "ledger.jsonl"),
                      runs_dir=os.path.join(scratch, "runs"))
sys.stdout.write("RUN_ID " + record["run_id"] + "\n")
'''


def rung_real_run(problems, scratch, ledger_path):
    print("[2/3] one real run -- one game through both proxies, offline mocks, "
          "no key, no cost")
    r = sh([sys.executable, "-", REPO, scratch], cwd=REPO, stdin=PLAY)
    if r.returncode != 0:
        fail(problems, "the mock run exited %d\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return False
    if not os.path.exists(ledger_path):
        fail(problems, "the run exited 0 but wrote no ledger at all")
        return False
    print("   ok    played one game, wrote %s" % os.path.basename(ledger_path))
    return True


def _load_ledger(problems, ledger_path):
    records = []
    with open(ledger_path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                fail(problems, "ledger line %d is not JSON: %s" % (n, exc))
    return records


def rung_artifact_fields(problems, scratch, ledger_path):
    print("[3/3] artefact self-check")
    records = _load_ledger(problems, ledger_path)

    if len(records) < MIN_RECORDS:
        fail(problems, "only %d ledger record(s), floor is %d -- a ledger that "
                       "holds the bookends and nothing between them is not a pass"
             % (len(records), MIN_RECORDS))
        return

    for i, rec in enumerate(records):
        # Deliberately not `rec.get(f, <what we want>)`.  A gate that defaults
        # a missing field to the value it hopes for passes a run in which the
        # field silently disappeared.
        missing = [f for f in ENVELOPE_REQUIRED if f not in rec]
        if missing:
            fail(problems, "ledger record %d is missing %s"
                 % (i, ", ".join(missing)))
            break
        if rec["v"] != LEDGER_VERSION:
            fail(problems, "ledger record %d declares v=%r, not %r"
                 % (i, rec["v"], LEDGER_VERSION))
            break

    if problems:
        return

    # §2: "monotonic within the file, assigned by the writer under a lock.
    # Gaps are impossible; duplicates are a corrupt file."  A repeated `seq` is
    # also what an appended forgery looks like when someone tries to make a
    # later record replace an earlier one.
    seqs = [rec["seq"] for rec in records]
    if sorted(seqs) != list(range(1, len(records) + 1)):
        duplicates = sorted({s for s in seqs if seqs.count(s) > 1})
        fail(problems, "seq is not dense from 1 over %d record(s) "
                       "(min %r, max %r, %d duplicate value(s): %s)"
             % (len(records), min(seqs), max(seqs), len(duplicates),
                ", ".join(map(str, duplicates[:10])) or "none"))

    run_ids = {rec["run_id"] for rec in records}
    if len(run_ids) != 1:
        fail(problems, "one run should write one run_id; this ledger holds %d "
                       "(%s)" % (len(run_ids), ", ".join(sorted(run_ids))[:200]))

    counts = {}
    for rec in records:
        counts[rec["event"]] = counts.get(rec["event"], 0) + 1

    env_steps = counts.get("env_step", 0)
    if env_steps < MIN_ENV_STEPS:
        fail(problems, "only %d env_step record(s), floor is %d -- under that "
                       "the arm did not play a game" % (env_steps, MIN_ENV_STEPS))
    model_calls = counts.get("model_call", 0)
    if model_calls < MIN_MODEL_CALLS:
        fail(problems, "only %d model_call record(s), floor is %d -- a ledger "
                       "with steps and no model calls is half a closed system"
             % (model_calls, MIN_MODEL_CALLS))
    if counts.get("run_start", 0) != EXPECT_RUN_START:
        fail(problems, "%d run_start record(s), expected exactly %d"
             % (counts.get("run_start", 0), EXPECT_RUN_START))
    if counts.get("run_end", 0) != EXPECT_RUN_END:
        fail(problems, "%d run_end record(s), expected exactly %d"
             % (counts.get("run_end", 0), EXPECT_RUN_END))

    # The format document's own executable half: envelope types, the canonical
    # field registry, frame_hash recomputation, level derivation.
    r = sh([sys.executable, "-m", "proxy.tools.validate_ledger", ledger_path],
           cwd=REPO)
    if r.returncode != 0:
        fail(problems, "the ledger fails LEDGER_FORMAT.md v1.0\n%s"
             % (r.stdout + r.stderr)[-2000:])

    # The run record beside it.
    runs_dir = os.path.join(scratch, "runs")
    run_files = (sorted(n for n in os.listdir(runs_dir) if n.endswith(".json"))
                 if os.path.isdir(runs_dir) else [])
    if len(run_files) != 1:
        fail(problems, "the run wrote %d run record(s), expected exactly 1"
             % len(run_files))
    else:
        with open(os.path.join(runs_dir, run_files[0]), encoding="utf-8") as fh:
            try:
                record = json.load(fh)
            except json.JSONDecodeError as exc:
                record = None
                fail(problems, "%s is not JSON: %s" % (run_files[0], exc))
        if record is not None:
            missing = [k for k in RUN_REQUIRED if k not in record]
            if missing:
                fail(problems, "%s is missing %s"
                     % (run_files[0], ", ".join(missing)))
            elif record["run_id"] not in run_ids:
                fail(problems, "%s names run_id %r, which the ledger does not "
                               "contain" % (run_files[0], record["run_id"]))

    if not problems:
        print("   ok    %d records (%d env_step, %d model_call), seq dense "
              "1..%d, one run_id, all %d envelope fields, LEDGER_FORMAT v%s "
              "clean" % (len(records), env_steps, model_calls, len(records),
                         len(ENVELOPE_REQUIRED), LEDGER_VERSION))


def var_leak(before):
    """What rung 1 dropped into `proxy/var/`, named rather than hidden.

    Reported, not fatal.  `proxy/var/` is gitignored so nothing tracked moves,
    and the gate cannot stop the suite writing there without editing
    `tests/conftest.py`, which is not this file's business.  Printing the count
    keeps it a known fact instead of a discovery.
    """
    after = _var_snapshot()
    new = sorted(after - before)
    if not new:
        return None
    return ("the suite wrote %d file(s) into proxy/var/ (gitignored, nothing "
            "tracked moves): %s" % (len(new), ", ".join(new[:4])
                                    + (", ..." if len(new) > 4 else "")))


def _var_snapshot():
    found = set()
    for root, _dirs, names in os.walk(VAR):
        for name in names:
            found.add(os.path.relpath(os.path.join(root, name), VAR)
                      .replace(os.sep, "/"))
    return found


def main():
    problems = []
    before = _var_snapshot()
    scratch = tempfile.mkdtemp(prefix="proxy-verify-")
    try:
        ledger_path = os.path.join(scratch, "ledger.jsonl")
        rung_tests(problems)
        if rung_real_run(problems, scratch, ledger_path):
            rung_artifact_fields(problems, scratch, ledger_path)
        leak = var_leak(before)
        if leak:
            print("   note  %s" % leak)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if problems:
        print("proxy: RED (%d problem(s))" % len(problems))
        return 1
    print("proxy: green -- suite, one real run, artefact fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
