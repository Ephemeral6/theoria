"""S46 pre-flight, part two: the live legs, where the mixed axis is real.

The offline corpus turned out to be fully labelled (`probe_blast_radius.py`),
so the collision the ask names can only be reached through
`adapters/theoria_live.py`, whose `_turn_map` returns `None` for any call the
arm's published join does not cover.  Measure that, and measure how many
*unpriced* calls anywhere carry a fabricated row-order turn.

    cd battery && python runs/20260802T0000Z-S46-turn-axis/probe_live_legs.py
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)

from battery.adapters.theoria_live import load_theoria_live_runs as load_live_runs      # noqa: E402
from battery.guard import load_piles                          # noqa: E402
from battery.metrics import evaluate                          # noqa: E402
from battery.run_battery import collect_runs                  # noqa: E402


def axis(calls):
    priced = [c for c in calls if c.cost_usd is not None]
    lab_p = [c for c in priced if c.turn is not None]
    lab_all = [c for c in calls if c.turn is not None]
    return {
        "calls": len(calls),
        "priced": len(priced),
        "priced_labelled": len(lab_p),
        "all_labelled": len(lab_all),
        "distinct_turns": len({c.turn for c in calls if c.turn is not None}),
    }


def collide(calls):
    """Would the current fallback put a row index in a real label's bucket?"""
    labels = {c.turn for c in calls if c.turn is not None}
    hits = []
    for i, call in enumerate(sorted(calls, key=lambda c: c.idx)):
        if call.turn is None and i in labels:
            hits.append(i)
    return hits


def main():
    piles = load_piles()
    out = {}

    print("=== live legs (adapters/theoria_live.py) ===")
    live = load_live_runs(piles=piles)
    live_rows = []
    for run in live:
        a = axis(run.calls)
        hits = collide(run.calls)
        vals = evaluate(run)
        row = {
            "run_id": run.run_id,
            "turn_join": run.notes.get("turn_join"),
            "axis": a,
            "collision_keys": hits,
            "turn_costs_len": len(run.turn_costs()),
            "E2": vals["E2"].as_dict(),
            "E3": vals["E3"].as_dict(),
        }
        live_rows.append(row)
        print("\n%s" % run.run_id)
        print("  join      : %s" % (run.notes.get("turn_join") or {}))
        print("  axis      : %s" % a)
        print("  collisions: %s" % (hits or "none"))
        print("  turn_costs: %d bucket(s)" % len(run.turn_costs()))
        print("  E2 %-18s E3 %s"
              % (vals["E2"].status, vals["E3"].status))
    out["live_legs"] = live_rows

    print("\n=== offline corpus: unpriced calls with no step_idx ===")
    bad = []
    for run in collect_runs(piles):
        unanchored = [c for c in run.calls if c.step_idx is None]
        if unanchored and run.calls:
            bad.append((run.run_id, run.source, len(unanchored), len(run.calls),
                        collide(run.calls)))
    if not bad:
        print("  none -- every call in the offline corpus carries a step_idx")
    for row in bad[:30]:
        print("  %-52s %-20s %d/%d unanchored, collisions=%s"
              % (row[0][:52], row[1], row[2], row[3], row[4] or "none"))
    out["offline_unanchored"] = [list(map(str, r)) for r in bad]

    dest = os.path.join(HERE, "live_legs.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True, default=str)
        fh.write("\n")
    print("\nwrote %s" % dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
