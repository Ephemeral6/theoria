"""How far the manual's rolled-forward state drifts from the world, per turn.

The number nothing in this arm has ever reported, and it turns out the arm has
been computing it every certify beat and throwing it away. `certify.cheap`
replays the manual open-loop from `initial_state()` and writes
`entry["cells_wrong"]` for every transition -- **that series is the drift**,
because `_roll_forward` and certify's replay are the same walk from the same
origin over the same actions. `certify.json` keeps only the summary
(`16/21 transitions replay exactly`) and the first divergence; `replay_steps`,
which is where the per-transition counts live, never reaches disk. So the
quantity was measured, filed as an audit line, and never read as what it also
is: the error of the frame every probe on that turn was designed against.

This recomputes it, and the recomputation is **checked before it is used**. For
each archived certify report, every snapshot of the leg's books is compiled and
replayed, and a snapshot is accepted only if the `checks.replay` block it
produces equals the archived one field for field -- `transitions`, `matched`,
`ok`, `detail` and `first_divergence`. A report no snapshot reproduces is
`unreconstructed` and contributes nothing. Same discipline as
`runs/20260801T0900Z-R2-frontier-by-generation/replay_frontier.py`, and for the
same reason: a series computed against a manual we cannot show the leg was
using is a story, not a measurement.

Offline. Reads `certify.json` (tracked) and `trace.jsonl` (gitignored). No
model call, no ARC action, no network. Development-pile games only.

    python measure_drift.py [--legs-root <dir>] [--out DRIFT.json]
"""

import argparse
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                      # noqa: E402,F401

from inner import certify as certify_beat              # noqa: E402
from inner import commit                               # noqa: E402
from inner.books import Books                          # noqa: E402
from world.frames import FrameStore, load_store        # noqa: E402

#: Every leg this arm has played live. The four of 2026-07-31 that R2 measured,
#: plus the two R1 legs and the two R1b legs that ran after it. Listed by name
#: rather than globbed so that a directory appearing under `runs/` cannot
#: silently enter a measurement.
LEGS = [
    "20260731T1240Z-A3-level2-carried",
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
    "20260731T231654Z-R1-g50t-a",
    "20260731T231654Z-R1-sk48-b",
    "20260801T001851Z-R1b-g50t-a",
    "20260801T001851Z-R1b-sk48-b",
]

#: The fields of `checks.replay` a reconstruction has to match exactly. This is
#: the whole block minus nothing: `detail` is derived from `matched` and
#: `transitions`, and `first_divergence` carries the cell coordinates, so
#: agreeing on all five is agreeing on the replay.
REPLAY_FIELDS = ("ok", "transitions", "matched", "detail", "first_divergence")


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _namespaces(leg_dir, workdir):
    """Every snapshot of this leg's books, compiled, newest first."""
    snaps = os.path.join(leg_dir, "books", "snapshots")
    out = []
    if not os.path.isdir(snaps):
        return out
    for name in sorted(os.listdir(snaps), reverse=True):
        src = os.path.join(snaps, name)
        dst = os.path.join(workdir, name, "books")
        os.makedirs(dst, exist_ok=True)
        for fname in ("theory.dsl", "playbook.dsl", "problem.json"):
            path = os.path.join(src, fname)
            if os.path.exists(path):
                shutil.copy2(path, os.path.join(dst, fname))
        books = Books(dst)
        try:
            books.compile_all()
        except Exception:                              # noqa: BLE001
            continue
        out.append((name, books))
    return out


def _prefix_store(store, n_grids):
    """A store holding the first `n_grids` observed frames."""
    view = FrameStore()
    kept = 0
    for step in store.steps:
        if step.grid is not None:
            if kept >= n_grids:
                break
            kept += 1
        view.steps.append(step)
    return view


def _replay_block(report):
    cheap = (report or {}).get("cheap") or {}
    return ((cheap.get("checks") or {}).get("replay")) or {}


def _same(a, b):
    return all(a.get(k) == b.get(k) for k in REPLAY_FIELDS)


def measure_leg(leg_dir, workdir):
    leg = os.path.basename(leg_dir)
    certify_path = os.path.join(leg_dir, "certify.json")
    trace_path = os.path.join(leg_dir, "trace.jsonl")
    if not os.path.exists(certify_path):
        return {"leg": leg, "status": "no certify.json; nothing measured"}
    if not os.path.exists(trace_path):
        # `.gitignore` excludes trace.jsonl, so in a clone this is the normal
        # case. It refuses per leg rather than reporting a drift of zero.
        return {"leg": leg,
                "status": "trace.jsonl is gitignored and absent here; "
                          "nothing measured"}

    archived = _read_json(certify_path)
    store = load_store(trace_path)
    namespaces = _namespaces(leg_dir, os.path.join(workdir, leg))

    rounds = []
    for idx, report in enumerate(archived):
        want = _replay_block(report)
        if not want or not want.get("transitions"):
            # certify ran but the replay did not: the manual would not compile,
            # or `render` raised on the initial state. Recorded, not skipped.
            rounds.append({"certify_round": idx, "reconstructed": False,
                           "why": ("the archived report has no replay to "
                                   "reproduce (transitions=%s)"
                                   % want.get("transitions"))})
            continue
        prefix = _prefix_store(store, int(want["transitions"]) + 1)
        row = {"certify_round": idx, "reconstructed": False,
               "archived_detail": want.get("detail")}
        for name, books in namespaces:
            got = certify_beat.cheap(books, prefix, commit.action_to_manual)
            block = (got.get("checks") or {}).get("replay") or {}
            if not _same(block, want):
                continue
            series = [s.get("cells_wrong") for s in (got.get("replay_steps")
                                                     or [])]
            row.update({
                "reconstructed": True,
                "snapshot": name,
                "transitions": want["transitions"],
                "matched": want["matched"],
                "cells_wrong_per_transition": series,
                "cells_total": ((got.get("checks") or {})
                                .get("responsibility") or {}).get("total_cells"),
            })
            break
        rounds.append(row)

    done = [r for r in rounds if r.get("reconstructed")]
    # The leg's drift is read off its LAST reconstructed certify round: that is
    # the manual the leg finished with, replayed over the longest history it
    # ever saw. Earlier rounds are kept so the series can be watched moving as
    # the desk rewrites the manual, which is the other question this answers.
    last = done[-1] if done else None
    series = (last or {}).get("cells_wrong_per_transition") or []
    measured = [c for c in series if c is not None]
    drifted = [c for c in measured if c]
    first_nonzero = next((i for i, c in enumerate(series) if c), None)
    return {
        "leg": leg,
        "status": "measured" if done else "no certify round reconstructed",
        "certify_rounds": len(rounds),
        "reconstructed_rounds": len(done),
        "unreconstructed_rounds": len(rounds) - len(done),
        "snapshot_used": (last or {}).get("snapshot"),
        "transitions": len(series),
        "transitions_with_a_cells_wrong_number": len(measured),
        "transitions_drifted": len(drifted),
        "first_drifted_transition": first_nonzero,
        "cells_wrong_first": measured[0] if measured else None,
        "cells_wrong_last": measured[-1] if measured else None,
        "cells_wrong_max": max(measured) if measured else None,
        "cells_wrong_mean": (round(sum(measured) / float(len(measured)), 4)
                             if measured else None),
        "cells_total": (last or {}).get("cells_total"),
        "series": series,
        "per_certify_round": [
            {"certify_round": r["certify_round"],
             "snapshot": r.get("snapshot"),
             "reconstructed": r.get("reconstructed"),
             "why": r.get("why"),
             "transitions": r.get("transitions"),
             "matched": r.get("matched"),
             "cells_wrong_max": (max([c for c in
                                      (r.get("cells_wrong_per_transition") or [])
                                      if c is not None] or [0])
                                 if r.get("reconstructed") else None)}
            for r in rounds],
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--legs-root", default=os.path.dirname(HERE))
    ap.add_argument("--out", default=os.path.join(HERE, "DRIFT.json"))
    args = ap.parse_args(argv)

    per_leg = []
    workdir = tempfile.mkdtemp(prefix="r3-drift-")
    try:
        for leg in LEGS:
            per_leg.append(measure_leg(os.path.join(args.legs_root, leg),
                                       workdir))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    measured = [row for row in per_leg if row.get("status") == "measured"]
    totals = {
        "legs_listed": len(LEGS),
        "legs_measured": len(measured),
        "legs_not_measured": [row["leg"] for row in per_leg
                              if row.get("status") != "measured"],
        "legs_that_ever_drifted": sum(1 for row in measured
                                      if row["transitions_drifted"]),
        "legs_that_never_drifted": sum(1 for row in measured
                                       if not row["transitions_drifted"]),
        "what_the_number_is": (
            "cells on which the manual's open-loop rolled-forward state and "
            "the world's observed frame disagree, per transition. It is "
            "certify's own replay series, which the arm computes every certify "
            "beat and does not archive; the drift of the probe frontier's "
            "anchor is the same walk from the same origin, so this IS that "
            "drift."),
    }
    payload = {"legs": per_leg, "totals": totals}
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(totals, indent=1, sort_keys=True))
    for row in per_leg:
        print(json.dumps({k: v for k, v in row.items()
                          if k not in ("series", "per_certify_round")},
                         sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
