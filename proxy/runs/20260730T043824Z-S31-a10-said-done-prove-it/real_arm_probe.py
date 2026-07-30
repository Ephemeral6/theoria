r"""S31 requirement 2, executed in the only form that is honest.

The ticket says: make one minimal real-arm call and see whether
`proxy/var/ledger.jsonl` gains a record whose `arm` is not `mock_arm`; if it
does, paste it; if it does not, find where the write end is broken.

The write end is not broken. `proxy/ledger.py:380` takes `arm` as an ordinary
parameter checked against the `ARMS` frozenset (`:37`), and
`proxy/runner.py:328` exposes `--arm` with **no `choices=`**, so
`python -m proxy.runner --mock --arm bare_cc` would append real-arm records to
the shared ledger today, for zero dollars and with no network.

**This script deliberately does not do that**, and the reason is the finding:

Running it would write a *mock* run under a *real* arm's name into the shared,
append-only ledger. The 2026-07-29 audit that failed A10 asks exactly one
question -- "are there records whose `arm` is not `mock_arm`?" -- so those
records would flip it from red to green without one real arm having run. The
one command that most directly satisfies the ticket's literal wording is also
the one that manufactures the evidence the ticket wants checked.

So the run below goes to a scratch ledger, and the script reports both axes the
audit collapsed into one word:

  axis 1  arm identity   -- is `arm` one of bare_cc / schema_repro / theoria,
                            ignoring `event: incident` records, which
                            `reconcile.py:521` stamps with the arm of whatever
                            run they complain about rather than an arm of their
                            own;
  axis 2  upstream       -- does the run's `run_start` name a non-localhost
                            `env_upstream` / `model_upstream`, i.e. did anything
                            actually leave this machine.

A mock run under `--arm bare_cc` scores 1-yes / 2-no. That combination is the
forgery this script exists to name, and no check in the repo currently reports
it.

Zero network beyond loopback, zero dollars, zero sealed-pile contact (the mock
serves `arc_mock.DEFAULT_GAME`, a dev-pile id), and no credential is read --
`require_keys=False`. The spend gate is a scratch pool, so the tracked
cross-session pool at `proxy/var/spend_gate.jsonl` gains nothing.

    python real_arm_probe.py <repo-root> <out-dir>
"""
import functools
import json
import os
import subprocess
import sys

REAL_ARMS = frozenset({"bare_cc", "schema_repro", "theoria"})

PLAY = r'''
import functools, json, os, sys
repo, scratch, arm = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, repo)

from proxy import scoring
from proxy.spend_gate import SpendGate, SpendPolicy, set_default_gate

# Same two redirections `proxy/verify.py:168-183` performs, and for the same
# reason: `score_run`'s `scores_dir` is bound at def time, and `default_gate()`
# resolves the policy's relative ledger against the MAIN checkout, so a run
# from a worktree would otherwise append to the tracked shared pool.
scoring.score_run = functools.partial(scoring.score_run,
                                      scores_dir=os.path.join(scratch, "scores"))
set_default_gate(SpendGate(SpendPolicy({
    "v": "1.0", "pool": "s31-real-arm-probe",
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
    record = run_game(DEFAULT_GAME, arm=arm, budget=40,
                      env_upstream=arc.base_url,
                      model_upstream=provider.base_url,
                      env_key=ARC_KEY, model_key=MODEL_KEY,
                      require_keys=False,
                      ledger_path=os.path.join(scratch, "ledger.jsonl"),
                      runs_dir=os.path.join(scratch, "runs"))
sys.stdout.write("RUN_ID " + record["run_id"] + "\n")
'''


def live(url):
    return bool(url) and "127.0.0.1" not in url and "localhost" not in url


def census(records):
    """The two axes, measured separately."""
    starts = {r["run_id"]: r for r in records if r.get("event") == "run_start"}
    axis1 = [r for r in records
             if r.get("event") != "incident" and r.get("arm") in REAL_ARMS]
    axis2 = [r for r in starts.values()
             if live(r.get("env_upstream")) or live(r.get("model_upstream"))]
    return axis1, axis2, starts


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    repo, out = os.path.abspath(argv[1]), os.path.abspath(argv[2])
    os.makedirs(out, exist_ok=True)
    scratch = os.path.join(out, "scratch")
    os.makedirs(scratch, exist_ok=True)

    arm = "bare_cc"
    proc = subprocess.run([sys.executable, "-c", PLAY, repo, scratch, arm],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    if proc.returncode != 0:
        print("the probe run failed -- that would itself be the finding")
        print(proc.stdout)
        print(proc.stderr)
        return 1

    ledger = os.path.join(scratch, "ledger.jsonl")
    records = [json.loads(line) for line in open(ledger, encoding="utf-8")
               if line.strip()]
    axis1, axis2, starts = census(records)

    lines = []
    w = lines.append
    w("S31 real-arm write-path probe")
    w("=" * 68)
    w("")
    w("run: proxy.runner.run_game(arm=%r) against the loopback mocks," % arm)
    w("     ledger redirected to a scratch file. $0.00, no network, no key.")
    w("")
    w("records written: %d" % len(records))
    w("")
    w("AXIS 1 -- arm identity is an experimental arm, ignoring incidents")
    w("   real-arm records: %d" % len(axis1))
    for r in axis1[:4]:
        w("     %s" % json.dumps({k: r[k] for k in ("seq", "event", "arm", "run_id")
                                  if k in r}, sort_keys=True))
    if len(axis1) > 4:
        w("     ... and %d more" % (len(axis1) - 4))
    w("")
    w("AXIS 2 -- the run reached a non-localhost upstream")
    for rid, r in starts.items():
        w("   %s  env_upstream=%s  model_upstream=%s"
          % (rid, r.get("env_upstream"), r.get("model_upstream")))
    w("   live runs: %d" % len(axis2))
    w("")
    w("VERDICT")
    w("   axis 1 = %d  (yes: the writer accepts a real arm and recorded one)"
      % len(axis1))
    w("   axis 2 = %d  (no: nothing left this machine)" % len(axis2))
    w("")
    w("   The write end is NOT broken. `proxy/var/ledger.jsonl` holds zero")
    w("   real-arm records because no caller has ever passed a real arm to it,")
    w("   not because a real arm was passed and dropped.")
    w("")
    w("   And this run is exactly the forgery: had its ledger not been")
    w("   redirected, an audit asking only axis 1 would now call A10")
    w("   delivered, on %d mock records." % len(axis1))

    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    with open(os.path.join(out, "real_arm_probe.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    with open(os.path.join(out, "real_arm_probe.records.jsonl"), "w",
              encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
