"""Capture A9's measured evidence, so the numbers in RUN_STATE.md have a source.

    python ablation-arm/runs/20260728T191437Z-A9-readonly-baseline/capture.py

Writes, next to itself:

* `01-empty-run-control.json`  -- the background set, on its own
* `02-real-run.json`           -- the controlled observation of `run_arm.run_all(["a0-base"])`
* `03-negative-control.json`   -- one byte created at the repo root, and the
                                  same observed set run through the superseded
                                  criterion for contrast
* `03b-negative-control-mutation.json` -- one byte *appended* to a file that
                                  already existed, which is the shape a real
                                  escape would take
* `03c-concurrent-writer.json` -- a thread writing across both legs: the only
                                  measurement here in which the empty-run
                                  subtraction actually runs
* `04-hard-list-reachability.json` -- which hard-list patterns match a file that
                                  actually exists on this tree

Zero API calls, zero network.  `run_arm` is offline by construction
(`ablcore/ledger_abl.py`: "Zero API calls, zero network, zero dollars").

Every victim is a uniquely named file at the repo **root**, removed in a
`finally` and asserted gone before the script exits.  The root rather than
`proxy/var/` because the adversarial review showed the latter is already hashed
unconditionally by `pin` -- see `ADVERSARIAL-RESPONSE.md`.  No file belonging to
another territory is touched.
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
    # The victim is at the repo ROOT, not under `proxy/var/`. The adversarial
    # review showed why: `proxy` is in `pin.UPSTREAM_TREES` and `var` is not in
    # `pin.SKIP_DIRS`, so a byte written there is caught unconditionally by the
    # pre-A9 pin test and the control discriminates nothing.
    victim_rel = "a9-negative-control-%d.jsonl" % os.getpid()
    victim = os.path.join(REPO, victim_rel)
    from ablcore import pin
    assert victim_rel not in pin.hash_tree(), "victim is inside an upstream tree"

    def run_then_trespass():
        run_a0()
        with open(victim, "wb") as handle:
            handle.write(b"x")

    try:
        neg = outside.observe(run_then_trespass)
        seen_by_pin = victim_rel in pin.hash_tree()
    finally:
        if os.path.exists(victim):
            os.remove(victim)
    assert not os.path.exists(victim), "the negative control left its own litter"

    let_through = outside.superseded_criterion(neg.observed)
    dump("03-negative-control.json", {
        "what": "one byte written at the repo root during the run",
        "victim": victim_rel,
        "victim_bytes": 1,
        "victim_visible_to_the_pre_A9_pin_test": seen_by_pin,
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
    mut_rel = "a9-mutation-control-%d.jsonl" % os.getpid()
    mut = os.path.join(REPO, mut_rel)
    try:
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

    # 03c -- the subtraction itself, which nothing else here reaches. In a
    # worktree the background set is always empty, so `subtracted` and
    # `reported_by_hard_list` never receive a non-empty input; the adversarial
    # review measured 0 background paths in 75/75 idle windows and said so. So
    # this *is* the concurrent session: a thread appends to two files across
    # both legs, one ordinary and one matching the mandated `**/ledger.jsonl`
    # rule. Same writer, same cadence, opposite verdicts.
    import threading

    pid = os.getpid()
    ordinary_rel = "a9-noise-%d.txt" % pid
    hard_rel = "a9-noise-%d/ledger.jsonl" % pid
    ordinary = os.path.join(REPO, ordinary_rel)
    hard = os.path.join(REPO, hard_rel.replace("/", os.sep))
    hard_dir = os.path.dirname(hard)
    stop = threading.Event()

    def churn():
        n = 0
        while not stop.is_set():
            n += 1
            for path in (ordinary, hard):
                try:
                    with open(path, "ab") as handle:
                        handle.write(b"%d\n" % n)
                except OSError:
                    pass
            stop.wait(0.05)

    writer = threading.Thread(target=churn, daemon=True)
    try:
        os.makedirs(hard_dir, exist_ok=True)
        for path in (ordinary, hard):
            with open(path, "wb") as handle:
                handle.write(b"seed\n")
        writer.start()
        noisy = outside.observe(run_a0)
    finally:
        stop.set()
        writer.join(timeout=10)
        for path in (ordinary, hard):
            if os.path.exists(path):
                os.remove(path)
        if os.path.isdir(hard_dir) and not os.listdir(hard_dir):
            os.rmdir(hard_dir)
    assert not os.path.exists(ordinary) and not os.path.isdir(hard_dir), \
        "the concurrent-writer control left its own litter"

    dump("03c-concurrent-writer.json", {
        "what": "a real concurrent writer touching two files across both legs: "
                "the only measurement in this directory where the empty-run "
                "subtraction actually runs",
        "ordinary_path": ordinary_rel,
        "hard_listed_path": hard_rel,
        "hard_rule_it_matches": outside.hard_reason(hard_rel),
        "both_moved_during_the_empty_leg":
            ordinary_rel in noisy.background and hard_rel in noisy.background,
        "ordinary_was_subtracted": ordinary_rel in noisy.subtracted,
        "ordinary_was_reported": ordinary_rel in noisy.reported,
        "hard_listed_was_reported": hard_rel in noisy.reported,
        "hard_listed_was_subtracted": hard_rel in noisy.subtracted,
        **noisy.as_dict(),
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
