"""Capture A9's measured evidence, so the numbers in RUN_STATE.md have a source.

    python ablation-arm/runs/20260728T191437Z-A9-readonly-baseline/capture.py

Writes, next to itself:

* `01-empty-run-control.json`  -- the background set, on its own
* `02-real-run.json`           -- the controlled observation of `run_arm.run_all(["a0-base"])`
* `03-negative-control.json`   -- one byte written under `proxy/var/`, and the
                                  same observed set run through the superseded
                                  criterion for contrast
* `04-hard-list-reachability.json` -- which hard-list patterns match a file that
                                  actually exists on this tree

Zero API calls, zero network.  `run_arm` is offline by construction
(`ablcore/ledger_abl.py`: "Zero API calls, zero network, zero dollars").

The negative control writes exactly one byte to a uniquely named file under
`proxy/var/` and removes it in a `finally`; `proxy/var/` is gitignored runtime
output and the file is never `spend_gate.jsonl`.  The script asserts the litter
is gone before it exits.
"""

from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap  # noqa: F401,E402
from _bootstrap import REPO  # noqa: E402

from ablcore import outside  # noqa: E402


def dump(name, payload):
    path = os.path.join(HERE, name)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    print("wrote %s" % name)


def main():
    entries = outside.watched(REPO)
    print("watched top-level entries (%d): %s" % (len(entries), ", ".join(entries)))

    # 01 -- the empty-run control on its own, so the background set is visible
    # as a number and not only as a subtraction inside a pass/fail.
    idle = outside.observe(lambda: None)
    dump("01-empty-run-control.json", {
        "what": "empty-run control measured against a second empty run: both "
                "legs do nothing, so everything reported here is the concurrent "
                "fleet, and `reported` should be small",
        "idle_floor_seconds": outside.IDLE_FLOOR_SECONDS,
        **idle.as_dict(),
    })

    # 02 -- the real thing.
    def run_a0():
        import run_arm
        run_arm.run_all(["a0-base"])

    real = outside.observe(run_a0)
    dump("02-real-run.json", {
        "what": "run_arm.run_all(['a0-base']) under the empty-run control",
        "action": "run_arm.run_all(['a0-base'])",
        **real.as_dict(),
    })

    # 03 -- the negative control, with the superseded criterion as contrast.
    victim_rel = "proxy/var/a9-negative-control-%d.jsonl" % os.getpid()
    victim = os.path.join(REPO, victim_rel.replace("/", os.sep))
    var_dir = os.path.dirname(victim)
    made_dir = not os.path.isdir(var_dir)

    def run_then_trespass():
        run_a0()
        os.makedirs(var_dir, exist_ok=True)
        with open(victim, "wb") as handle:
            handle.write(b"x")

    try:
        neg = outside.observe(run_then_trespass)
    finally:
        if os.path.exists(victim):
            os.remove(victim)
        if made_dir and os.path.isdir(var_dir) and not os.listdir(var_dir):
            os.rmdir(var_dir)
    assert not os.path.exists(victim), "the negative control left its own litter"

    let_through = outside.superseded_criterion(neg.observed)
    dump("03-negative-control.json", {
        "what": "one byte written to proxy/var/ during the run",
        "victim": victim_rel,
        "victim_bytes": 1,
        "victim_removed_afterwards": not os.path.exists(victim),
        "victim_is_on_hard_list": outside.is_hard(victim_rel),
        "A9_criterion_reports_it": victim_rel in neg.reported,
        "superseded_criterion_tokens": list(outside.SUPERSEDED_CONCURRENT_TOKENS),
        "superseded_criterion_reports": let_through,
        "superseded_criterion_lets_the_byte_through":
            victim_rel not in let_through,
        **neg.as_dict(),
    })

    # 03b -- the harder negative control: a byte APPENDED to a file that already
    # existed before the first snapshot, so the diff is a content change rather
    # than a key addition. An addition is caught by any criterion that diffs key
    # sets at all; an append is the shape a real escape would take.
    mut_rel = "proxy/var/a9-mutation-control-%d.jsonl" % os.getpid()
    mut = os.path.join(REPO, mut_rel.replace("/", os.sep))
    mut_dir = os.path.dirname(mut)
    mut_made_dir = not os.path.isdir(mut_dir)
    try:
        os.makedirs(mut_dir, exist_ok=True)
        with open(mut, "wb") as handle:
            handle.write(b"seed\n")

        def run_then_append():
            run_a0()
            with open(mut, "ab") as handle:
                handle.write(b"x")

        mutation = outside.observe(run_then_append)
    finally:
        if os.path.exists(mut):
            os.remove(mut)
        if mut_made_dir and os.path.isdir(mut_dir) and not os.listdir(mut_dir):
            os.rmdir(mut_dir)
    assert not os.path.exists(mut), "the mutation control left its own litter"

    dump("03b-negative-control-mutation.json", {
        "what": "one byte APPENDED to a pre-existing file outside the arm",
        "victim": mut_rel,
        "victim_existed_before_the_first_snapshot": True,
        "victim_in_background": mut_rel in mutation.background,
        "victim_removed_afterwards": not os.path.exists(mut),
        "A9_criterion_reports_it": mut_rel in mutation.reported,
        "superseded_criterion_reports":
            outside.superseded_criterion(mutation.observed),
        "superseded_criterion_lets_the_byte_through":
            mut_rel not in outside.superseded_criterion(mutation.observed),
        **mutation.as_dict(),
    })

    # 04 -- is any hard-list rule reachable by a file that exists?
    present = outside.snapshot(REPO)
    reach = []
    for pattern, why in outside.ALL_HARD:
        rx = outside._to_regex(pattern)
        hits = sorted(p for p in present if rx.match(p))
        reach.append({"pattern": pattern, "why": why,
                      "files_on_this_tree": len(hits),
                      "examples": hits[:5],
                      "mandated_by_ticket":
                          any(pattern == p for p, _ in outside.HARD_LIST)})
    dump("04-hard-list-reachability.json", {
        "what": "does each hard-list pattern match anything that actually exists "
                "on this checkout -- a rule nothing can trip has never been tested",
        "files_watched": len(present),
        "patterns": reach,
        "audit_table_paths_hidden_by_the_superseded_criterion": {
            p: {"superseded_reports_it":
                    bool(outside.superseded_criterion([p])),
                "on_hard_list": outside.is_hard(p)}
            for p in ("proxy/var/spend_gate.jsonl",
                      "arc-recon/data/contamination_log.jsonl",
                      "arc-recon/data/incidents.jsonl",
                      "engine-rig/artifacts/candidates.jsonl",
                      "baseline-arms/ledger.jsonl",
                      "monitor/state.json")
        },
    })

    print("\nempty-run control : background=%d observed=%d reported=%d "
          "(idle %.2fs / run %.2fs)"
          % (len(idle.background), len(idle.observed), len(idle.reported),
             idle.idle_seconds, idle.run_seconds))
    print("real run          : background=%d observed=%d reported=%d "
          "(idle %.2fs / run %.2fs / makeup %.2fs, aligned=%s)"
          % (len(real.background), len(real.observed), len(real.reported),
             real.idle_seconds, real.run_seconds, real.makeup_seconds,
             real.aligned))
    print("negative control  : reported=%s ; superseded lets it through=%s"
          % (victim_rel in neg.reported, victim_rel not in let_through))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
