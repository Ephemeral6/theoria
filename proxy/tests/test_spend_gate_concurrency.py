"""Multi-process fuzz on the spend pool. Real OS processes, real contention.

INC-BA-003's writers were four separate processes started by a session that
could not see this one, so a test that spawns threads would be testing the wrong
thing: a `threading.Lock` passes it and would still have lost the money. Every
test here launches real interpreters against one pool file.

Two properties are asserted, and they are the two the incident needed:

  * **Nothing is lost and nothing is double-counted.** Every worker reports what
    it believes it recorded; the pool's own total must equal the sum of those
    beliefs, exactly, and the ledger's sequence numbers must be dense.
  * **Over the ceiling is refused, not absorbed.** When the workers' combined
    appetite exceeds the pool, somebody is told no -- and the total never passes
    the ceiling, no matter who wins the race.

    cd proxy && python -m pytest tests/test_spend_gate_concurrency.py
"""

import json
import os
import subprocess
import sys
import textwrap

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

WORKER = textwrap.dedent(r'''
    import json, os, random, sys, time
    sys.path.insert(0, %(repo)r)
    from proxy.spend_gate import (SpendGate, SpendPolicy, SpendGateTripped,
                                  SpendGateError, SpendGateUnavailable)

    ledger, campaign, seed, rounds, usd_cap, action_cap, per, ceiling_usd, \
        ceiling_actions, hold = sys.argv[1:11]
    rng = random.Random(int(seed))
    policy = SpendPolicy({"v": "1.0", "pool": "fuzz",
                          "usd_ceiling": float(ceiling_usd),
                          "action_ceiling": int(ceiling_actions),
                          "ledger": ledger,
                          "default_ttl_seconds": 600,
                          "lock_timeout_seconds": 60.0,
                          "default_run_caps": {"usd": 1.0, "actions": 10}},
                         source=None)
    out = {"campaign": campaign, "recorded_usd": 0.0, "recorded_actions": 0,
           "records": 0, "refused_reserve": False, "refusals": 0, "error": None}
    try:
        gate = SpendGate(policy)
        try:
            res = gate.reserve(campaign, float(usd_cap), int(action_cap))
        except SpendGateTripped:
            out["refused_reserve"] = True
            time.sleep(float(hold))
            print(json.dumps(out)); raise SystemExit(0)
        # Hold the claim while the other processes try for theirs. Without this
        # the fleet runs serially -- worker 0 reserves, spends and releases
        # before worker 1 has started -- and the admission check is never put
        # under the contention it exists for.
        time.sleep(float(hold))
        for _ in range(int(rounds)):
            time.sleep(rng.random() * 0.004)      # random interleaving
            amount = float(per)
            try:
                # check BEFORE the money moves; this is the call that must stop
                # the pool from ever passing its ceiling.
                gate.check(res, usd=amount, actions=1)
            except (SpendGateTripped, SpendGateError):
                out["refusals"] += 1
                continue
            gate.record(res, usd=amount, actions=1)
            out["recorded_usd"] = round(out["recorded_usd"] + amount, 6)
            out["recorded_actions"] += 1
            out["records"] += 1
        gate.release(res)
    except (SpendGateUnavailable, SpendGateError) as exc:
        out["error"] = "%%s: %%s" %% (type(exc).__name__, exc)
    print(json.dumps(out))
''')


def run_fleet(tmp_path, *, workers, rounds, usd_cap, action_cap, per,
              ceiling_usd, ceiling_actions, hold=0.0):
    ledger = str(tmp_path / "pool.jsonl")
    script = tmp_path / "worker.py"
    script.write_text(WORKER % {"repo": REPO}, encoding="utf-8")

    procs = []
    for i in range(workers):
        procs.append(subprocess.Popen(
            [sys.executable, str(script), ledger, "campaign-%d" % i, str(1000 + i),
             str(rounds), str(usd_cap), str(action_cap), str(per),
             str(ceiling_usd), str(ceiling_actions), str(hold)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
    reports = []
    for proc in procs:
        stdout, stderr = proc.communicate(timeout=180)
        assert proc.returncode == 0, stderr
        reports.append(json.loads(stdout.strip().splitlines()[-1]))
    records = [json.loads(l) for l in
               open(ledger, encoding="utf-8").read().splitlines() if l.strip()]
    return reports, records


# -- nothing lost, nothing doubled ------------------------------------------

@pytest.mark.parametrize("workers", [4])
def test_concurrent_writers_lose_nothing_and_double_nothing(tmp_path, workers):
    reports, records = run_fleet(
        tmp_path, workers=workers, rounds=12, usd_cap=5.0, action_cap=50,
        per=0.01, ceiling_usd=1000.0, ceiling_actions=100000)

    assert not any(r["error"] for r in reports), [r["error"] for r in reports]
    believed_usd = round(sum(r["recorded_usd"] for r in reports), 6)
    believed_actions = sum(r["recorded_actions"] for r in reports)

    spends = [r for r in records if r["kind"] == "spend"]
    assert len(spends) == sum(r["records"] for r in reports)
    assert round(sum(r["usd"] for r in spends), 6) == believed_usd
    assert sum(r["actions"] for r in spends) == believed_actions

    # Dense sequence: no append clobbered another, none was skipped.
    assert [r["seq"] for r in records] == list(range(1, len(records) + 1))


def test_every_worker_actually_got_through(tmp_path):
    """The negative control for the test above: an assertion over four workers
    that all failed to write anything would also pass it."""
    reports, records = run_fleet(
        tmp_path, workers=4, rounds=6, usd_cap=5.0, action_cap=50, per=0.01,
        ceiling_usd=1000.0, ceiling_actions=100000)
    assert all(r["records"] == 6 for r in reports), reports
    assert len({r["campaign"] for r in records if r.get("campaign")}) == 4


def test_the_ledger_is_never_interleaved_mid_line(tmp_path):
    """Every line is complete JSON. A torn append is how a pool becomes
    uncountable, and `_read_locked` would then refuse the whole file."""
    _, records = run_fleet(tmp_path, workers=4, rounds=10, usd_cap=5.0,
                           action_cap=50, per=0.01, ceiling_usd=1000.0,
                           ceiling_actions=100000)
    assert all(isinstance(r, dict) and "kind" in r for r in records)


# -- over the ceiling is refused, not absorbed ------------------------------

def test_the_pool_ceiling_holds_under_a_race(tmp_path):
    """Four workers, each wanting $1.00, against a $2.50 pool. Somebody must be
    told no, and the total must not pass the ceiling."""
    reports, records = run_fleet(
        tmp_path, workers=4, rounds=25, usd_cap=1.0, action_cap=100, per=0.04,
        ceiling_usd=2.50, ceiling_actions=100000)

    assert not any(r["error"] for r in reports), [r["error"] for r in reports]
    total = round(sum(r["usd"] for r in records if r["kind"] == "spend"), 6)
    assert total <= 2.50, total
    refused = sum(1 for r in reports if r["refused_reserve"]) \
        + sum(r["refusals"] for r in reports)
    assert refused > 0, "nobody was refused, so the ceiling was never tested"


def test_reservations_cannot_all_claim_the_whole_pool(tmp_path):
    """The admission check: held headroom is subtracted before a claim is
    granted. Without it, four sessions each 'correctly' hold the whole budget --
    which is INC-BA-003, exactly."""
    reports, _ = run_fleet(
        tmp_path, workers=4, rounds=1, usd_cap=1.0, action_cap=10, per=0.001,
        ceiling_usd=2.50, ceiling_actions=100000, hold=2.0)
    granted = [r for r in reports if not r["refused_reserve"]]
    assert len(granted) <= 2, [r["campaign"] for r in granted]
    assert len(granted) >= 1


def test_the_action_ceiling_holds_under_a_race(tmp_path):
    reports, records = run_fleet(
        tmp_path, workers=4, rounds=20, usd_cap=100.0, action_cap=15, per=0.0,
        ceiling_usd=1000.0, ceiling_actions=30)
    assert not any(r["error"] for r in reports), [r["error"] for r in reports]
    actions = sum(r["actions"] for r in records if r["kind"] == "spend")
    assert actions <= 30, actions
