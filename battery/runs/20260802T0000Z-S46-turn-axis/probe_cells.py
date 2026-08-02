"""Negative control 1, at corpus scale: did any metric cell move?

The ticket's first negative control is that a fully labelled record must come
out reading exactly what it read before -- otherwise this was a silent change
of口径 rather than a repair.  Every run in the offline corpus is fully labelled
(`probe_blast_radius.py`), so the whole spectrum is the control, and the claim
is checkable rather than argued.

Dumps every metric cell for every run to `cells_<label>.json`; run once on
master and once on the branch, then `--diff` the two.

    python runs/20260802T0000Z-S46-turn-axis/probe_cells.py master
    python runs/20260802T0000Z-S46-turn-axis/probe_cells.py branch
    python runs/20260802T0000Z-S46-turn-axis/probe_cells.py --diff
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)


def dump(label):
    from battery.guard import load_piles
    from battery.metrics import evaluate
    from battery.run_battery import collect_runs

    runs = collect_runs(load_piles())
    cells = {}
    for run in runs:
        for mid, value in evaluate(run).items():
            cells["%s/%s" % (run.run_id, mid)] = value.as_dict()
    dest = os.path.join(HERE, "cells_%s.json" % label)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(cells, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("%d run(s), %d cell(s) -> %s" % (len(runs), len(cells), dest))


def diff():
    a = json.load(open(os.path.join(HERE, "cells_master.json"),
                       encoding="utf-8"))
    b = json.load(open(os.path.join(HERE, "cells_branch.json"),
                       encoding="utf-8"))
    print("cells: master=%d branch=%d" % (len(a), len(b)))
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    moved_value, moved_status, moved_reason = [], [], []
    for key in sorted(set(a) & set(b)):
        if a[key].get("value") != b[key].get("value"):
            moved_value.append((key, a[key].get("value"), b[key].get("value")))
        if a[key].get("status") != b[key].get("status"):
            moved_status.append((key, a[key]["status"], b[key]["status"]))
        elif a[key].get("reason") != b[key].get("reason"):
            moved_reason.append(key)

    print("cells only on master : %d %s" % (len(only_a), only_a[:5]))
    print("cells only on branch : %d %s" % (len(only_b), only_b[:5]))
    print("VALUES that moved    : %d" % len(moved_value))
    for row in moved_value[:20]:
        print("   %s  %s -> %s" % row)
    print("STATUSES that moved  : %d" % len(moved_status))
    for row in moved_status[:20]:
        print("   %s  %s -> %s" % row)
    print("reason-only changes  : %d %s" % (len(moved_reason),
                                            moved_reason[:5]))
    ok = not (only_a or only_b or moved_value or moved_status)
    print("\nnegative control 1 at corpus scale: %s"
          % ("HOLDS -- not one cell moved" if ok else "VIOLATED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--diff"]:
        raise SystemExit(diff())
    raise SystemExit(dump(sys.argv[1] if len(sys.argv) > 1 else "current"))
