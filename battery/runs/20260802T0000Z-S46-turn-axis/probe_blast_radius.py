"""S46 pre-flight: how many real runs carry a mixed turn axis today?

Read-only measurement, no API calls.  Classifies every run the battery can
load by the state of its decision axis over *priced* calls, both as the
adapter writes it today (row index fabricated where `step_idx` is absent) and
as it would read if the fabrication were removed.

    cd battery && python runs/20260802T0000Z-S46-turn-axis/probe_blast_radius.py
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)

from battery.guard import load_piles                          # noqa: E402
from battery.metrics import evaluate                          # noqa: E402
from battery.run_battery import collect_runs                  # noqa: E402


def classify(run):
    """The axis verdict over the calls that carry money."""
    priced = [c for c in run.calls if c.cost_usd is not None]
    if not priced:
        return "no-priced-calls", 0, 0
    labelled = [c for c in priced if c.turn is not None]
    if not labelled:
        return "absent", len(priced), 0
    if len(labelled) < len(priced):
        return "partial", len(priced), len(labelled)
    return "exact", len(priced), len(labelled)


def classify_without_fabrication(run):
    """Same, but a turn that the adapter invented from row order is not one.

    `adapters/ledger_jsonl.py:241` writes `turn=i` when a call row carries no
    `step_idx`.  Reconstruct what the axis would look like without that.
    """
    priced = [c for c in run.calls if c.cost_usd is not None]
    if not priced:
        return "no-priced-calls", 0, 0
    labelled = [c for c in priced if c.turn is not None and c.step_idx is not None]
    # Sources that never set `step_idx` but do set a real `turn`
    # (`schema_traces`, `theoria_live`) must not be penalised here: only the
    # ledger adapter fabricates from row order.
    if run.source not in ("bare_cc-ledger", "ledger"):
        return classify(run)
    if not labelled:
        return "absent", len(priced), 0
    if len(labelled) < len(priced):
        return "partial", len(priced), len(labelled)
    return "exact", len(priced), len(labelled)


def main():
    piles = load_piles()
    runs = collect_runs(piles)
    print("loaded %d run(s)" % len(runs))
    print("sources: %s" % dict(collections.Counter(r.source for r in runs)))

    today = collections.Counter()
    fixed = collections.Counter()
    moved = []
    for run in runs:
        a, np_, nl = classify(run)
        b, _, nl2 = classify_without_fabrication(run)
        today[a] += 1
        fixed[b] += 1
        if a != b:
            moved.append((run.run_id, run.source, a, b, np_, nl, nl2))

    print("\naxis today (as the adapter writes it): %s" % dict(today))
    print("axis without row-order fabrication:    %s" % dict(fixed))
    print("\nruns whose verdict moves: %d" % len(moved))
    for row in moved[:40]:
        print("  %-52s %-16s %s -> %s  priced=%d labelled=%d/%d"
              % (row[0][:52], row[1], row[2], row[3], row[4], row[5], row[6]))

    # What do E2/E3 say today on each class?
    print("\nE2/E3 status today, by axis class:")
    tally = collections.defaultdict(collections.Counter)
    ok_cells = 0
    for run in runs:
        cls, _, _ = classify(run)
        fixed_cls, _, _ = classify_without_fabrication(run)
        vals = evaluate(run)
        for mid in ("E2", "E3"):
            v = vals[mid]
            tally[(cls, fixed_cls, mid)][v.status] += 1
        ok_cells += sum(1 for v in vals.values() if v.status == "ok")
    for key in sorted(tally, key=str):
        print("  today=%-16s fixed=%-16s %s  %s"
              % (key[0], key[1], key[2], dict(tally[key])))

    print("\ntotal `ok` cells across every metric today: %d  (verify floor 100)"
          % ok_cells)

    out = os.path.join(HERE, "blast_radius.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({
            "n_runs": len(runs),
            "axis_today": dict(today),
            "axis_without_fabrication": dict(fixed),
            "moved": [list(m) for m in moved],
            "ok_cells_today": ok_cells,
        }, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("\nwrote %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
