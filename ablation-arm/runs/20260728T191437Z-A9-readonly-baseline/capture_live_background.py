"""How much background noise is there actually, and how fast does it grow?

    python ablation-arm/runs/20260728T191437Z-A9-readonly-baseline/capture_live_background.py

`capture.py` runs inside this worktree, where no concurrent session writes and
`proxy/var/` does not even exist, so its background set is empty and the
empty-run control subtracts nothing.  That measures the criterion but not the
problem the criterion exists for.

This script measures the problem.  It points the same snapshot/diff machinery at
the **main worktree**, where the fleet actually runs, and takes a sequence of
idle windows of increasing length.  It is strictly **read-only**: it hashes
files and sleeps.  It never runs `run_arm`, never writes outside this run
directory, and touches no network.

Why it matters for the design choice `IDLE_FLOOR_SECONDS = 2.0`: the background
set grows with the idle window, and every path in it is a path the control will
subtract.  Too short and the control under-covers the run's exposure; too long
and it absorbs writes it should have reported.  The numbers here are what that
trade actually costs on this repo.
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

from ablcore import outside  # noqa: E402

#: The main worktree: `<repo>/.worktrees/<slug>/` -> `<repo>`.
LIVE = os.path.dirname(os.path.dirname(_bootstrap.REPO))

WINDOWS = (2.0, 5.0, 15.0, 30.0)


def main():
    if not os.path.isdir(os.path.join(LIVE, ".git")):
        print("no main worktree at %s -- nothing to measure" % LIVE)
        return 1
    entries = outside.watched(LIVE)
    print("live tree: %s" % LIVE)
    print("watched entries (%d)" % len(entries))

    rows = []
    previous = outside.snapshot(LIVE, entries)
    print("baseline snapshot: %d files" % len(previous))
    for seconds in WINDOWS:
        t0 = time.time()
        time.sleep(seconds)
        current = outside.snapshot(LIVE, entries)
        elapsed = time.time() - t0
        moved = outside.diff(previous, current)
        hard = [p for p in moved if outside.is_hard(p)]
        survives_superseded = outside.superseded_criterion(moved)
        rows.append({
            "requested_seconds": seconds,
            "exposure_seconds": round(elapsed, 3),
            "paths_moved": len(moved),
            "paths": moved[:40],
            "of_those_on_the_hard_list": hard,
            "of_those_the_superseded_criterion_would_have_reported":
                survives_superseded[:40],
        })
        print("  %5.1fs window -> %3d path(s) moved, %d on the hard list, "
              "%d would survive the superseded criterion"
              % (seconds, len(moved), len(hard), len(survives_superseded)))
        previous = current

    payload = {
        "what": "read-only measurement of concurrent-fleet churn in the live "
                "worktree, to size the background set the empty-run control "
                "has to subtract",
        "live_root": LIVE,
        "read_only": True,
        "files_watched": len(previous),
        "idle_floor_seconds_chosen": outside.IDLE_FLOOR_SECONDS,
        "windows": rows,
    }
    out = os.path.join(HERE, "05-live-background-churn.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    print("wrote 05-live-background-churn.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
