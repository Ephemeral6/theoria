"""The variance envelope, and the number Phase 4 needs from it.

`Theoria.md`'s frozen list says the per-cell repeat count `n` is fixed by the
development pile's variance before the freeze. The M4 pilot could not supply it:
one episode per cell has no spread. This reads `out/campaign_cells.jsonl` and
produces both halves of the answer -- the per-repeat table, and the `n` that the
measured spread implies.

    python -m harness.summarise_envelope
    python -m harness.summarise_envelope --json out/envelope.json

Two things it deliberately does NOT do:

  * **It does not drop cells to make the spread look smaller.** Degraded cells
    are excluded only when the exclusion is named, and the reason is printed
    next to the table rather than applied quietly.
  * **It does not report `n` as a single number.** `n` depends on which quantity
    Phase 4 intends to compare and on how big a difference it wants to see, and
    a single number would hide both choices inside an arithmetic result.
"""

import argparse
import json
import math
import os
import sys
from typing import Any, Dict, List, Optional

from . import run_campaign

#: Cells excluded from the envelope, and why. Named here rather than filtered by
#: a predicate, so an exclusion is a line someone wrote and can be argued with.
EXCLUDED: Dict[str, str] = {
    "ar25-0c556536": ("degraded: measured under INC-BA-003's concurrent-campaign "
                      "load, and killed by an abort threshold that did not scale "
                      "with the action budget (BUDGET_REPORT 11.2). Kept in the "
                      "record and in every cumulative gate; not re-run, and not "
                      "used to estimate a spread that would be the contention's "
                      "and not the arm's."),
}

#: What a cell contributes to the envelope. Each is a per-cell scalar, so the
#: spread across repeats of one cell is the quantity of interest.
def metrics(cell: Dict[str, Any]) -> Dict[str, Optional[float]]:
    ok = cell.get("actions_ok") or 0
    failed = cell.get("actions_failed") or 0
    http = cell.get("http_calls_gameplay") or 0
    return {
        "actions_ok": float(ok),
        "levels_completed": float(cell.get("levels_completed") or 0),
        "cost_usd": float(cell.get("cost_usd") or 0.0),
        "wall_seconds": float(cell.get("wall_seconds") or 0.0),
        "http_per_action": (http / ok) if ok else None,
        "action_success_rate": (ok / (ok + failed)) if (ok + failed) else None,
        "usd_per_action": ((cell.get("cost_usd") or 0.0) / ok) if ok else None,
    }


METRIC_ORDER = ["actions_ok", "levels_completed", "action_success_rate",
                "usd_per_action", "http_per_action", "cost_usd", "wall_seconds"]


# ------------------------------------------------------------------ statistics
def mean(xs: List[float]) -> float:
    return sum(xs) / len(xs)


def sample_sd(xs: List[float]) -> Optional[float]:
    """n-1 in the denominator. With n=3 that is 2 degrees of freedom, which is
    very little -- see the caveats printed with the report."""
    if len(xs) < 2:
        return None
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def cv(xs: List[float]) -> Optional[float]:
    """Coefficient of variation. Undefined at a zero mean, and that is not a
    formality here: `levels_completed` was 0 in all twelve pilot cells, so the
    metric Phase 4 might most want to compare can have no CV at all."""
    if len(xs) < 2:
        return None
    m = mean(xs)
    if abs(m) < 1e-12:
        return None
    sd = sample_sd(xs)
    return None if sd is None else sd / abs(m)


#: 97.5th percentile of Student's t, by degrees of freedom. Tabulated rather
#: than imported: this module must run wherever the harness runs, and the
#: numbers below are the only ones a 2-to-8 repeat design can reach.
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
        8: 2.306, 9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086,
        30: 2.042, 60: 2.000}


def t975(df: int) -> float:
    if df <= 0:
        return float("inf")
    for key in sorted(T975):
        if df <= key:
            return T975[key]
    return 1.960


def n_for_precision(cv_value: float, rel_margin: float) -> int:
    """Smallest n whose 95% CI half-width for a cell mean is <= `rel_margin`.

    Searched upward rather than iterated to a fixed point. The obvious
    `n <- (t(n-1) * cv / margin)^2` loop does not converge: at cv=0.05 and a 10%
    margin it alternates between 2 (where t=12.706 demands 41) and 41 (where
    t=2.000 demands 2), and after a bounded number of turns it returns whichever
    end it stopped on -- which can be an n that fails its own inequality by a
    factor of four. `test_n_for_precision_reaches_the_fixed_point_it_claims`
    found that, and it is the reason this checks the condition it reports rather
    than trusting the recurrence.

    Capped at 60: past that the answer is not "run more repeats", it is "this
    quantity is too noisy to compare this way".
    """
    for n in range(2, 61):
        if t975(n - 1) * cv_value / math.sqrt(n) <= rel_margin:
            return n
    return 60


def n_for_two_sample(cv_value: float, rel_effect: float,
                     alpha: float = 0.05, power: float = 0.80) -> int:
    """Repeats **per arm** to detect a relative difference `rel_effect`.

    This is the one Phase 4 actually needs. The envelope is not being bought so
    that a bare-CC cell mean can be quoted precisely; it is being bought so that
    a bare-CC cell and a Theoria cell can be told apart. Normal approximation
    with the usual 1.960 / 0.842, inflated by 2 for the small-sample t penalty
    the way sample-size tables do.
    """
    z_alpha, z_beta = 1.960, 0.842                      # alpha=0.05, power=0.80
    if alpha != 0.05 or power != 0.80:                  # pragma: no cover
        raise ValueError("only the standard 0.05 / 0.80 pair is tabulated here")
    n = 2 * ((z_alpha + z_beta) ** 2) * (cv_value ** 2) / (rel_effect ** 2)
    return max(2, min(60, int(math.ceil(n)) + 2))


# --------------------------------------------------------------------- report
def build(cells: List[Dict[str, Any]],
          model: Optional[str] = None) -> Dict[str, Any]:
    """The envelope over `cells`, optionally restricted to one tier.

    `campaign_cells.jsonl` holds more than one campaign now, and the section-2.1
    re-measurement put opus and sonnet cells in it. Pooling a tier's cells into
    another tier's spread would not be a small error: the tiers differ by 3-4x
    in unit price, so the "within-cell spread" would become a between-tier
    difference wearing its name. The caller passes the campaign; this filters
    the tier.
    """
    if model is not None:
        cells = [c for c in cells if c.get("model") == model]
    included = [c for c in cells if c.get("game_id") not in EXCLUDED]
    excluded = [c for c in cells if c.get("game_id") in EXCLUDED]

    by_game: Dict[str, List[Dict[str, Any]]] = {}
    for cell in included:
        by_game.setdefault(cell["game_id"], []).append(cell)

    games: Dict[str, Any] = {}
    pooled: Dict[str, List[float]] = {m: [] for m in METRIC_ORDER}

    for game_id, group in sorted(by_game.items()):
        group = sorted(group, key=lambda c: c.get("repeat") or 0)
        rows = [dict(metrics(c),
                     repeat=c.get("repeat"), outcome=c.get("outcome"),
                     run_id=c.get("run_id"),
                     actions_failed=c.get("actions_failed"),
                     failed_consecutive_max=c.get("actions_failed_consecutive_max"),
                     reservation_id=(c.get("spend") or {}).get("reservation_id"))
                for c in group]
        stats: Dict[str, Any] = {}
        for name in METRIC_ORDER:
            xs = [r[name] for r in rows if r.get(name) is not None]
            stats[name] = {
                "n": len(xs),
                "mean": round(mean(xs), 6) if xs else None,
                "sd": (round(sample_sd(xs), 6)
                       if sample_sd(xs) is not None else None),
                "cv": round(cv(xs), 6) if cv(xs) is not None else None,
                "min": min(xs) if xs else None,
                "max": max(xs) if xs else None,
            }
            # Pooled as CVs, not as raw values: the games have different scales
            # and pooling the raw numbers would measure between-game differences
            # rather than within-cell repeatability, which is the whole target.
            if cv(xs) is not None:
                pooled[name].append(cv(xs))
        games[game_id] = {"repeats": rows, "stats": stats,
                          "outcomes": sorted({r["outcome"] for r in rows})}

    pooled_cv = {name: (round(mean(vals), 6) if vals else None)
                 for name, vals in pooled.items()}

    sizing: Dict[str, Any] = {}
    for name, value in pooled_cv.items():
        if value is None or value == 0:
            sizing[name] = {"cv": value, "note": (
                "no usable CV: the metric was constant or its mean was zero "
                "across every repeat. A quantity with no spread needs no "
                "repeats to estimate -- and one that is identically zero, like "
                "levels_completed, cannot be compared between arms at all.")}
            continue
        sizing[name] = {
            "cv": value,
            "n_for_ci_10pct": n_for_precision(value, 0.10),
            "n_for_ci_20pct": n_for_precision(value, 0.20),
            "n_to_detect_25pct_difference": n_for_two_sample(value, 0.25),
            "n_to_detect_50pct_difference": n_for_two_sample(value, 0.50),
        }

    return {
        "model": model,
        "games": games,
        "excluded": {game: {"reason": EXCLUDED[game],
                            "cells": len([c for c in excluded
                                          if c.get("game_id") == game])}
                     for game in sorted({c["game_id"] for c in excluded})},
        "pooled_cv": pooled_cv,
        "sizing": sizing,
        "degrees_of_freedom": sum(
            max(0, len(g["repeats"]) - 1) for g in games.values()),
    }


def print_report(report: Dict[str, Any]) -> None:
    print("=== variance envelope: bare_cc x haiku-4.5, 30-action budget ===\n")

    for game_id, game in report["games"].items():
        print("%s  (%s)" % (game_id, ", ".join(game["outcomes"])))
        print("  %-4s %-18s %5s %5s %5s %7s %8s %9s %8s"
              % ("rep", "outcome", "ok", "fail", "run", "http/a", "success",
                 "$", "wall s"))
        for row in game["repeats"]:
            print("  %-4s %-18s %5s %5s %5s %7s %8s %9s %8s"
                  % (row["repeat"], (row["outcome"] or "")[:18],
                     int(row["actions_ok"]), row["actions_failed"],
                     row.get("failed_consecutive_max"),
                     _f(row["http_per_action"], 2),
                     _f(row["action_success_rate"], 3),
                     _f(row["cost_usd"], 4), _f(row["wall_seconds"], 0)))
        print("  %-4s %-18s" % ("", "mean / sd / cv"))
        for name in METRIC_ORDER:
            s = game["stats"][name]
            if s["mean"] is None:
                continue
            print("    %-22s mean %-12s sd %-12s cv %s"
                  % (name, _f(s["mean"], 4), _f(s["sd"], 4), _f(s["cv"], 4)))
        print()

    for game, info in report["excluded"].items():
        print("EXCLUDED %s (%d cell(s))\n  %s\n" % (game, info["cells"], info["reason"]))

    print("=== pooled within-cell CV, and the n it implies ===")
    print("  pooled over %d game(s), %d degrees of freedom total\n"
          % (len(report["games"]), report["degrees_of_freedom"]))
    print("  %-24s %8s %8s %8s %9s %9s"
          % ("metric", "cv", "n(+-10%)", "n(+-20%)", "n(d=25%)", "n(d=50%)"))
    for name in METRIC_ORDER:
        s = report["sizing"].get(name, {})
        if s.get("cv") in (None, 0):
            print("  %-24s %8s   -- %s" % (name, _f(s.get("cv"), 4),
                                           s.get("note", "")[:60]))
            continue
        print("  %-24s %8s %8d %8d %9d %9d"
              % (name, _f(s["cv"], 4), s["n_for_ci_10pct"], s["n_for_ci_20pct"],
                 s["n_to_detect_25pct_difference"],
                 s["n_to_detect_50pct_difference"]))


def _f(value, places):
    if value is None:
        return "-"
    return ("%%.%df" % places) % value


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None, help="also write the report here")
    ap.add_argument("--campaign", default=run_campaign.CAMPAIGN_NAME)
    ap.add_argument("--model", default=run_campaign.CAMPAIGN_TIER)
    args = ap.parse_args(argv)

    report = build(run_campaign.load_cells(args.campaign), model=args.model)
    print_report(report)
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
        print("\nwrote %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
