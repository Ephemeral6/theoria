"""Re-measure the live tree's churn on a frame big enough to see it.

    python ablation-arm/runs/20260728T191437Z-A9-readonly-baseline/capture_live_resample.py [windows]

`05-live-background-churn.json` sampled **four** windows totalling 53s and
concluded the live tree is quiet at 2s/5s/15s. The adversarial review sampled
~245s and found that a 2s window is non-empty about 9% of the time, driven by
`monitor/ci/merge.log` -- a writer the first frame never saw at all. Four windows
is not a sampling frame for a p ~ 0.09 event, and `06`'s headline residual was
computed from `gap_seconds_min` while its own prose used the median: two
estimators in one number.

So this re-measures properly: N windows at the criterion's own
`IDLE_FLOOR_SECONDS`, each one an independent Bernoulli trial for "did anything
move", and reports the per-window hit rate with a Wilson interval, per-path hit
counts, and the residual false-red rate that follows.

Strictly read-only against the live worktree: it hashes files and sleeps. It
never runs `run_arm`, writes nothing outside this run directory, and touches no
network.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap  # noqa: F401,E402

from ablcore import outside  # noqa: E402

LIVE = os.path.dirname(os.path.dirname(_bootstrap.REPO))

#: The measured action leg from `02-real-run.json` / `07-repeat-trials.json`.
ACTION_SECONDS = 1.0


def wilson(hits: int, n: int, z: float = 1.96):
    if not n:
        return (0.0, 0.0)
    p = hits / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4))


def main(windows: int = 100):
    if not os.path.exists(os.path.join(LIVE, ".git")):
        print("no main worktree at %s" % LIVE)
        return 1

    print("live tree: %s ; %d windows of %.1fs"
          % (LIVE, windows, outside.IDLE_FLOOR_SECONDS))
    previous = outside.snapshot(LIVE)
    print("baseline snapshot: %d files" % len(previous))

    hits = 0
    per_path = Counter()
    exposure = 0.0
    t_start = time.time()
    for i in range(windows):
        t0 = time.time()
        time.sleep(outside.IDLE_FLOOR_SECONDS)
        current = outside.snapshot(LIVE)
        exposure += time.time() - t0
        moved = outside.diff(previous, current)
        if moved:
            hits += 1
            per_path.update(moved)
            print("  window %3d: %s" % (i, moved[:6]))
        previous = current

    n = windows
    p = hits / n if n else 0.0
    lo, hi = wilson(hits, n)
    mean_window = exposure / n if n else 0.0
    # Rate per second of exposure, then the chance of at least one event landing
    # in an action leg of ACTION_SECONDS.
    lam = (hits / exposure) if exposure else 0.0
    residual = 1 - math.exp(-lam * ACTION_SECONDS)

    payload = {
        "what": "wider re-measurement of live-tree churn; supersedes the "
                "4-window frame in 05/06, which was too small to see the "
                "largest writer",
        "supersedes": ["05-live-background-churn.json",
                       "06-periodic-writer-residual.json"],
        "live_root": LIVE,
        "read_only": True,
        "files_watched": len(previous),
        "window_seconds": outside.IDLE_FLOOR_SECONDS,
        "mean_window_exposure_seconds": round(mean_window, 3),
        "windows": n,
        "windows_with_any_change": hits,
        "hit_rate_per_window": round(p, 4),
        "hit_rate_wilson_95": [lo, hi],
        "total_exposure_seconds": round(exposure, 1),
        "events_per_second": round(lam, 5),
        "action_seconds_assumed": ACTION_SECONDS,
        "residual_false_red_per_run": round(residual, 4),
        "paths_by_window_count": [
            {"path": path, "windows": count,
             "on_hard_list": outside.is_hard(path),
             "superseded_criterion_would_report":
                 bool(outside.superseded_criterion([path]))}
            for path, count in per_path.most_common(40)],
        "reading": (
            "The empty-run control subtracts a writer only when it fires in "
            "both legs, probability ~p^2 at this rate; it pays a false red "
            "when it fires in exactly one, probability ~2p(1-p). At p=%.3f "
            "that is a residual false red of ~%.1f%% per run and effectively "
            "no subtraction. The control is insurance against the day the "
            "fleet writes into the worktree, not a mechanism that is doing "
            "work today." % (p, 100 * residual)),
    }
    out = os.path.join(HERE, "08-live-background-resample.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")

    print("\n%d/%d windows moved something (p=%.3f, 95%% CI %s-%s)"
          % (hits, n, p, lo, hi))
    print("exposure %.0fs, %.4f events/s, residual false red ~%.1f%% per run"
          % (exposure, lam, 100 * residual))
    print("top paths: %s" % per_path.most_common(8))
    print("wall clock %.0fs; wrote 08-live-background-resample.json"
          % (time.time() - t_start))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 100))
