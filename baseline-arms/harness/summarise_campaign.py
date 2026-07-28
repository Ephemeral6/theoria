"""The variance envelope: how far apart do identical cells land?

The M4 pilot ran each (game, model) cell once, which buys a unit price and says
nothing whatever about spread -- one sample has no variance. This reads the
repeated cells and answers the question the pilot could not:

    run the same game, the same model, the same action budget, three times.
    How different are the three?

That number has a specific consumer. `Theoria.md`'s Phase 4 freeze list ends
with "每格重复数 n 由开发堆方差在冻结前定：方差小则 n=1 可辩护，否则 n=2" --
the sealed-pile campaign's per-cell repeat count is to be chosen from the
development pile's variance, before the freeze. This module computes the
quantity that decision needs, and reports what the standard error of a cell
mean would be at n = 1, 2 and 3, so the choice is made on numbers rather than
on the word "small".

    python -m harness.summarise_campaign [--json]
"""

import argparse
import collections
import json
import math
import os
import statistics
import sys
from typing import Any, Dict, List, Optional

from . import adjudications, run_campaign

# The quantities worth asking for a spread on. levels_completed is here even
# though the pilot saw nothing but zeros: if it is still all zeros, that is
# itself the finding, and a table that omitted it would hide it.
METRICS = [
    ("actions_ok", "successful actions"),
    ("actions_failed", "failed actions"),
    ("cost_usd", "cost $"),
    ("model_calls", "model calls"),
    ("http_calls_gameplay", "HTTP calls"),
    ("output_tokens", "output tokens"),
    # The 1.12 table leaves the bare-CC arm's per-game cache reads as "—(基线口径)",
    # i.e. never measured. It is the denominator of claim C5 (10^8 -> 10^6), so
    # an arm that reports it is worth more than one that does not.
    ("cache_read_tokens", "cache read tokens"),
    ("cache_creation_tokens", "cache creation tokens"),
    ("levels_completed", "levels completed"),
    ("wall_seconds", "wall seconds"),
]


def spread(values: List[float]) -> Dict[str, Any]:
    """Mean, sample sd, coefficient of variation, and the standard error of a
    cell mean at n = 1, 2, 3.

    The sd is the *sample* sd (n-1): these three episodes are a sample from the
    arm's behaviour, not the population of interest. With n=3 it is a noisy
    estimate of sd, and it is reported as such rather than dressed up -- three
    points is what Theoria.md's 2-3 range allows, and the honest move is to
    publish the width of the estimate, not to pretend it is tight.
    """
    n = len(values)
    mean = statistics.fmean(values) if n else None
    sd = statistics.stdev(values) if n > 1 else None
    row: Dict[str, Any] = {
        "n": n,
        "mean": round(mean, 4) if mean is not None else None,
        "sd": round(sd, 4) if sd is not None else None,
        "min": round(min(values), 4) if n else None,
        "max": round(max(values), 4) if n else None,
        "range": round(max(values) - min(values), 4) if n else None,
        "cv": (round(sd / mean, 4) if sd is not None and mean else None),
    }
    if sd is not None:
        row["sem_at_n"] = {str(k): round(sd / math.sqrt(k), 4) for k in (1, 2, 3)}
    return row


def degraded_games(cells: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """`game_id` -> the ruling that took its cells out of the aggregate.

    Read from the same append-only adjudication file the gate reads, so a game
    is degraded in the envelope for exactly the reason it is degraded in the
    gate, and never because this module decided so on its own. A game counts as
    degraded when *every* one of its recorded cells is named in a ruling: a
    partially-adjudicated game still has cells that are evidence, and dropping
    it whole would discard them.
    """
    suspended = adjudications.suspended("G4")
    by_game_ids: Dict[str, List[str]] = collections.defaultdict(list)
    for c in cells:
        by_game_ids[c["game_id"]].append(c.get("run_id") or "?")
    out: Dict[str, Dict[str, Any]] = {}
    for game_id, run_ids in by_game_ids.items():
        rulings = [suspended[r] for r in run_ids if r in suspended]
        if rulings and len(rulings) == len(run_ids):
            first = rulings[0]
            out[game_id] = {
                "finding": first["finding"],
                "authority": first["authority"],
                "reason": first["reason"],
                "evidence": first["evidence"],
                "cells": sorted(run_ids),
            }
    return out


def by_game(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    grouped: Dict[Any, List[Dict[str, Any]]] = collections.defaultdict(list)
    for c in cells:
        grouped[(c["game_id"], c["model"])].append(c)

    degraded = degraded_games(cells)
    out: Dict[str, Any] = {}
    for (game_id, model), group in sorted(grouped.items()):
        if game_id in out:
            # Grouping is per (game, model) but the result is keyed per game, so
            # a second tier for the same game would silently overwrite the
            # first and its cells would vanish from every table below. The
            # envelope is haiku-only by construction (D-011) and --model is a
            # plain flag with no guard, so this is reachable by a typo. Refuse
            # rather than lose cells.
            raise ValueError(
                "game %s has cells at two model tiers (%s and %s). The envelope "
                "is one tier by construction (DECISIONS.md D-011); reporting it "
                "per game would drop one of them silently."
                % (game_id, out[game_id]["model"], model))
        # Appending is the only write path, so a re-run of a game's three
        # repeats yields six cells for that game and the spread silently mixes
        # the failed attempt with the good one. summarise_pilot solves this by
        # keeping the better attempt per cell and *returning* the dropped ones;
        # here the honest move is different -- for a variance envelope every
        # episode is a sample and discarding the bad ones would be exactly the
        # bias the envelope exists to measure. So all of them count, and the
        # over-count is named rather than hidden.
        expected = run_campaign.REPEATS
        entry: Dict[str, Any] = {
            "model": model,
            "repeats": len(group),
            "repeats_expected": expected,
            "over_expected_repeats": (
                None if len(group) <= expected else
                "this game has %d cells where the protocol is %d. Every episode "
                "counts towards the spread -- for a variance envelope a failed "
                "attempt is a sample, not a mistake -- but the mean and sd below "
                "pool attempts from more than one sitting, so read them with the "
                "cell table above." % (len(group), expected)),
            "outcomes": sorted(c.get("outcome") for c in group),
            "run_ids": sorted(c.get("run_id") or "?" for c in group),
            "degraded": degraded.get(game_id),
            "metrics": {},
        }
        for key, _label in METRICS:
            values = [float(c.get(key) or 0) for c in group]
            entry["metrics"][key] = spread(values)
        ok = sum(c.get("actions_ok", 0) or 0 for c in group)
        failed = sum(c.get("actions_failed", 0) or 0 for c in group)
        entry["pooled_action_success_rate"] = round(ok / (ok + failed), 4) if (ok + failed) else None
        out[game_id] = entry
    return out


def envelope(per_game: Dict[str, Any]) -> Dict[str, Any]:
    """The pooled answer: across the games, how variable is a cell?

    A game an outside reviewer ruled degraded is excluded from the pooled cv and
    named in `excluded_games` instead. It keeps its own row in the per-game
    table -- the measurements happened and the money was spent -- but folding a
    cv measured under known-bad conditions into the number Phase 4 freezes `n`
    from would put the contention into the arm's variance. Which is the thing
    the envelope exists to measure and INC-BA-003 is the reason it could not be.
    """
    excluded = sorted(gid for gid, g in per_game.items() if g.get("degraded"))
    kept = {gid: g for gid, g in per_game.items() if not g.get("degraded")}
    out: Dict[str, Any] = {"_excluded_games": excluded}
    for key, label in METRICS:
        cvs = [g["metrics"][key]["cv"] for g in kept.values()
               if g["metrics"][key].get("cv") is not None]
        all_cvs = [g["metrics"][key]["cv"] for g in per_game.values()
                   if g["metrics"][key].get("cv") is not None]
        out[key] = {
            "label": label,
            "games_with_estimate": len(cvs),
            "cv_median": round(statistics.median(cvs), 4) if cvs else None,
            "cv_min": round(min(cvs), 4) if cvs else None,
            "cv_max": round(max(cvs), 4) if cvs else None,
            # The same statistic with the degraded games folded back in, so the
            # cost of excluding them is visible rather than asserted.
            "cv_median_including_degraded":
                round(statistics.median(all_cvs), 4) if all_cvs else None,
        }
    return out


def fmt(value: Optional[float], width: int = 9, places: int = 3) -> str:
    return " " * width if value is None else ("%*.*f" % (width, places, value))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    cells = run_campaign.load_cells()
    if not cells:
        print("no campaign cells in %s" % run_campaign.CELLS_PATH)
        return 1

    per_game = by_game(cells)
    env = envelope(per_game)
    gate = run_campaign.evaluate_gate(cells)

    if args.json:
        print(json.dumps({"per_game": per_game, "envelope": env, "gate": gate},
                         indent=2, sort_keys=True))
        return 0

    print("=== cells ===")
    print("%-18s %-8s %-18s %5s %5s %9s %7s" %
          ("game", "repeat", "outcome", "ok", "fail", "cost$", "wall_s"))
    for c in sorted(cells, key=lambda c: (c["game_id"], c.get("repeat", 0))):
        print("%-18s %-8s %-18s %5s %5s %9.4f %7s" % (
            c["game_id"], c.get("repeat", "?"), c.get("outcome"),
            c.get("actions_ok", 0), c.get("actions_failed", 0),
            c.get("cost_usd", 0.0), c.get("wall_seconds", 0)))

    print("\n=== per game: spread across repeats ===")
    for game_id, entry in sorted(per_game.items()):
        mark = "  ** DEGRADED **" if entry.get("degraded") else ""
        if entry.get("over_expected_repeats"):
            mark += "  ** %d REPEATS, PROTOCOL IS %d **" % (
                entry["repeats"], entry["repeats_expected"])
        print("\n%s  (%s, %d repeats)  action success %s%s"
              % (game_id, entry["model"], entry["repeats"],
                 entry["pooled_action_success_rate"], mark))
        if entry.get("degraded"):
            d = entry["degraded"]
            print("    ruled degraded by %s (%s) -- kept on its own row, "
                  "excluded from the envelope below" % (d["authority"], d["finding"]))
            for line in d["evidence"]:
                print("      evidence: %s" % line)
        print("    %-20s %9s %9s %9s %9s %7s" %
              ("metric", "mean", "sd", "min", "max", "cv"))
        for key, label in METRICS:
            row = entry["metrics"][key]
            print("    %-20s %s %s %s %s %s" % (
                label, fmt(row["mean"]), fmt(row["sd"]), fmt(row["min"]),
                fmt(row["max"]), fmt(row["cv"], 7, 3)))

    kept = [g for g in per_game.values() if not g.get("degraded")]
    print("\n=== the envelope: coefficient of variation across %d game(s) ==="
          % len(kept))
    if env["_excluded_games"]:
        print("excluded as degraded: %s  (their rows are above; the last column "
              "shows what folding them back in would do)"
              % ", ".join(env["_excluded_games"]))
    print("%-20s %6s %10s %10s %10s %12s"
          % ("metric", "games", "cv median", "cv min", "cv max", "cv med +deg"))
    for key, label in METRICS:
        row = env[key]
        print("%-20s %6s %s %s %s %s" % (
            label, row["games_with_estimate"], fmt(row["cv_median"], 10, 4),
            fmt(row["cv_min"], 10, 4), fmt(row["cv_max"], 10, 4),
            fmt(row["cv_median_including_degraded"], 12, 4)))

    print("\n=== standard error of a cell mean, by repeat count n ===")
    print("(Theoria.md Phase 4 freezes n from this. Lower is tighter.)")
    for game_id, entry in sorted(per_game.items()):
        row = entry["metrics"]["actions_ok"]
        sem = row.get("sem_at_n")
        if not sem:
            continue
        if entry.get("degraded"):
            print("  %-18s (degraded -- not an input to the n decision)" % game_id)
            continue
        print("  %-18s successful actions: mean %.2f, sd %.2f -> sem n=1 %.2f  "
              "n=2 %.2f  n=3 %.2f"
              % (game_id, row["mean"], row["sd"], sem["1"], sem["2"], sem["3"]))

    run_campaign.print_gate(gate)
    return 0


if __name__ == "__main__":
    sys.exit(main())
