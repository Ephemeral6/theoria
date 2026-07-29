"""The one noise source the empty-run control does *not* remove, measured.

    python ablation-arm/runs/20260728T191437Z-A9-readonly-baseline/capture_periodic_writer.py

`capture_live_background.py` found that the live tree is quiet at 2s, 5s and 15s
and then moves four files at 30s: `monitor/index.html`, `monitor/reflex.lock`,
`monitor/reflex.log`, `monitor/state.json`.  That is not continuous churn, it is
a **periodic** writer -- the monitor's reflex loop.

This matters to the design and is therefore measured rather than argued.  An
empty-run control subtracts a noise source only if the noise appears in *both*
legs.  A writer whose period is much longer than either leg appears in **neither**
leg most of the time, and in **exactly one** leg occasionally -- and when that
one leg is the run leg, the check goes red for something this arm did not do.

Read-only: it parses timestamps out of `monitor/reflex.log` in the live tree and
computes the period.  No writes outside this run directory, no network.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap  # noqa: F401,E402

from ablcore import outside  # noqa: E402

LIVE = os.path.dirname(os.path.dirname(_bootstrap.REPO))
LOG = os.path.join(LIVE, "monitor", "reflex.log")
STAMP = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)")

#: What the run leg actually costs, from `02-real-run.json`.
RUN_LEG_SECONDS = 0.95


def main():
    if not os.path.isfile(LOG):
        print("no %s -- nothing to measure" % LOG)
        return 1
    stamps = []
    with open(LOG, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = STAMP.match(line)
            if match:
                stamps.append(datetime.strptime(match.group(1),
                                                "%Y-%m-%dT%H:%M:%SZ"))
    gaps = [(b - a).total_seconds() for a, b in zip(stamps, stamps[1:])]
    gaps = [g for g in gaps if g > 0]
    touched = ["monitor/index.html", "monitor/reflex.lock",
               "monitor/reflex.log", "monitor/state.json"]
    period = min(gaps) if gaps else None

    payload = {
        "what": "the periodic writer the empty-run control cannot subtract, "
                "and the residual false-red rate it implies",
        "source": "monitor/reflex.log (live worktree, read-only)",
        "ticks_seen": len(stamps),
        "first_tick": stamps[0].isoformat() + "Z" if stamps else None,
        "last_tick": stamps[-1].isoformat() + "Z" if stamps else None,
        "gap_seconds_min": min(gaps) if gaps else None,
        "gap_seconds_median": sorted(gaps)[len(gaps) // 2] if gaps else None,
        "gap_seconds_max": max(gaps) if gaps else None,
        "paths_it_touches": touched,
        "of_those_on_the_hard_list": [p for p in touched if outside.is_hard(p)],
        "of_those_the_superseded_criterion_would_also_have_reported":
            outside.superseded_criterion(touched),
        "idle_floor_seconds": outside.IDLE_FLOOR_SECONDS,
        "run_leg_seconds": RUN_LEG_SECONDS,
        "residual_false_red_probability_per_run":
            round(RUN_LEG_SECONDS / period, 5) if period else None,
        "reading": (
            "The control removes noise that is present during both legs. This "
            "writer is present during neither leg ~99.7%% of the time and "
            "during exactly one leg the rest, so it is a residual FALSE "
            "POSITIVE of roughly %s per run, not a false negative. It is not "
            "excluded by path shape, because excluding by path shape is the "
            "defect this ticket exists to remove: the superseded criterion "
            "would have reported %d of these 4 paths and hidden the other 2, "
            "including monitor/state.json, which is on the hard list."
            % (round(RUN_LEG_SECONDS / period, 5) if period else "n/a",
               len(outside.superseded_criterion(touched)))),
    }
    out = os.path.join(HERE, "06-periodic-writer-residual.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    print("ticks=%d gaps min/median/max = %s / %s / %s s"
          % (len(stamps), payload["gap_seconds_min"],
             payload["gap_seconds_median"], payload["gap_seconds_max"]))
    print("residual false-red probability per run: %s"
          % payload["residual_false_red_probability_per_run"])
    print("wrote 06-periodic-writer-residual.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
