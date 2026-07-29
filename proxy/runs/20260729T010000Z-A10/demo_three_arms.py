#!/usr/bin/env python3
"""Three arm identities, three OS processes, one ledger, one intact chain.

    python proxy/runs/20260729T010000Z-A10/demo_three_arms.py

A10's acceptance evidence, and deliberately the narrow claim rather than the
broad one.

**What this shows.** Three *concurrently running processes*, writing under three
different `arm` identities, appending to a single shared ledger, producing a
stream with no duplicate `seq`, no gaps, and a hash chain that verifies end to
end. Before the fix in this same item that was not possible: the writer seeded
`seq`/`prev` once at construction under a thread-only lock, so overlapping
processes forked the chain (`LEDGER_FORMAT.md`, "Duplicate `seq` from two
processes", and a real 253-line casualty under `theoria-arm/runs/`).

**What this does NOT show, and must not be read as.** These are the *ledger
identities* of three arms, driven by this script. It is not the three real arms
running their own inner loops through the proxy -- that requires editing
`theoria-arm/`, `baseline-arms/` and `ablation-arm/`, which is outside this
item's `proxy` territory and is recorded as a gap in `SCOPE.md` §1. Nothing here
runs an arm, opens a socket, or spends a cent.

`arm` values are the registered ones (`proxy.ledger.ARMS`). `schema_repro`
stands in for the ablation identity because `ARMS` has no ablation name; per
`ablation-arm/DECISIONS.md` D-AB-004 that arm currently ships under `theoria`
with a `requested_arm_name` in its `run_start` payload, and PARTNER_SYNC:835
already ruled that not a blocker.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

ARMS = ["theoria", "bare_cc", "schema_repro"]
#: A development-pile game. The sealed pile is never named here.
GAME = "ar25-0c556536"
STEPS = 12


def _worker(args) -> int:
    """One arm, one process, its own Ledger over the shared path."""
    path, arm, steps = args
    sys.path.insert(0, str(REPO))
    from proxy.ledger import Ledger, RunLedger

    ledger = Ledger(path)
    run = RunLedger(ledger, "r-%s-demo" % arm, arm)
    run.run_start(game_id=GAME, note="A10 shared-ledger demonstration")
    for i in range(steps):
        run.env_step(
            GAME,
            {"name": "RESET" if i == 0 else "ACTION2",
             "id": 0 if i == 0 else 2, "data": None},
            frames=[[[0]]],
            step_idx=i,
            state="NOT_FINISHED",
            levels_completed=0,
            http={"status": 200, "elapsed_ms": 1},
        )
    run.run_end(game_id=GAME, outcome="NOT_FINISHED",
                steps=steps, model_calls=0)
    return os.getpid()


def survey(path: Path) -> dict:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip()] if path.exists() else []
    arms: dict[str, int] = {}
    for r in rows:
        arms[str(r.get("arm"))] = arms.get(str(r.get("arm")), 0) + 1
    seqs = [r.get("seq") for r in rows]
    return {"records": len(rows), "by_arm": dict(sorted(arms.items())),
            "distinct_seq": len(set(seqs)),
            "duplicate_seq": len(seqs) - len(set(seqs)),
            "real_arm_records": sum(n for a, n in arms.items()
                                    if a not in ("mock_arm", "replay", "None"))}


def main() -> int:
    print("=" * 68)
    print("BEFORE -- the shared ledger as this item found it")
    print("=" * 68)
    # `proxy/var/` is gitignored, so a linked worktree has its own empty copy.
    # The ledger this item is *about* lives in the main checkout -- the same
    # reason `spend_gate.POOL_ROOT` resolves through `main_checkout()`, so that
    # worktrees share one pool instead of each inventing a private one.
    from proxy.spend_gate import main_checkout
    root = Path(main_checkout(str(REPO)) or REPO)
    shared = root / "proxy" / "var" / "ledger.jsonl"
    print("  reading: %s" % shared)
    print("  (main checkout, not this worktree -- proxy/var is gitignored)")
    before = survey(shared)
    print(json.dumps(before, ensure_ascii=False, indent=2))
    print("\n  real-arm records: %d   <-- the defect A10 was raised for"
          % before["real_arm_records"])

    print("\n" + "=" * 68)
    print("AFTER -- three arms, three processes, one ledger")
    print("=" * 68)
    with tempfile.TemporaryDirectory() as td:
        path = str(Path(td) / "ledger.jsonl")
        ctx = mp.get_context("spawn")
        with ctx.Pool(len(ARMS)) as pool:
            pids = pool.map(_worker, [(path, a, STEPS) for a in ARMS])
        print("  worker pids: %s (distinct: %d)" % (pids, len(set(pids))))

        after = survey(Path(path))
        print(json.dumps(after, ensure_ascii=False, indent=2))

        chain = subprocess.run(
            [sys.executable, "-m", "proxy.tools.verify_chain", path],
            cwd=str(REPO), capture_output=True, text=True)
        print("\n  verify_chain rc=%d" % chain.returncode)
        print("  " + (chain.stdout or chain.stderr).strip().replace("\n", "\n  "))

        ok = (after["duplicate_seq"] == 0
              and after["records"] == len(ARMS) * (STEPS + 2)
              and after["real_arm_records"] == after["records"]
              and chain.returncode == 0
              and len(set(pids)) == len(ARMS))
        print("\n  VERDICT: %s" % ("PASS" if ok else "FAIL"))
        if not ok:
            print("  (expected %d records, 0 duplicate seq, chain rc=0, "
                  "%d distinct pids)" % (len(ARMS) * (STEPS + 2), len(ARMS)))
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
