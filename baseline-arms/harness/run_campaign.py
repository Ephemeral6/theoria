"""The Phase-3 variance envelope for the bare-CC arm, with a hard budget gate.

`Theoria.md` Phase 3 economics: the two comparison arms each run 2-3 episodes on
the development pile to produce a variance envelope, and then freeze -- after
that only the Theoria arm burns money. This module is the bare-CC half of that:
the same game, the same model, the same action budget, run N times, so the
spread between *identical* cells can be measured. That spread is what Phase 4
needs in order to fix its per-cell repeat count `n` (Theoria.md's frozen list:
"每格重复数 n 由开发堆方差在冻结前定").

The pilot (M4) bought a unit price from one episode per cell. It cannot say
anything about variance, because a single sample has none. This buys that.

Scope is fixed here rather than passed in, for the same reason it is in
run_pilot.py: widening it should be a code change with a diff, not a flag.

    tier     -- the cheap tier only. It is the only tier with 4/4 usable pilot
                cells and it costs 23% of opus per action (BUDGET_REPORT 2.1).
    repeats  -- 3 per game, the top of Theoria.md's 2-3 range
    budget   -- 30 actions per episode

    python -m harness.run_campaign --game sk48-d8078629
    python -m harness.run_campaign --gate-only

The budget gate below is the operative one, not advisory. Every threshold is
anchored to a measured pilot number, and tripping any of them stops the
campaign where it stands -- see BUDGET_REPORT.md section 9.
"""

import argparse
import json
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from . import arc_client, bare_cc, ledger

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(TRACK, "out")
CELLS_PATH = os.path.join(OUT_DIR, "campaign_cells.jsonl")
GATE_PATH = os.path.join(OUT_DIR, "campaign_gate.json")

CAMPAIGN_TIER = bare_cc.MODEL_TIERS["cheap"]
REPEATS = 3
ACTION_BUDGET = 30

# Measured in the M4 pilot; BUDGET_REPORT.md section 2.1. Every gate below is a
# multiple of one of these, so no threshold is a number someone felt like.
PILOT_UNIT = {
    "claude-haiku-4-5-20251001": {"usd_per_action": 0.0342, "http_per_action": 7.11,
                                  "wall_s_per_action": 54.7, "action_success_rate": 0.713},
    "claude-sonnet-5": {"usd_per_action": 0.1672, "http_per_action": 10.73,
                        "wall_s_per_action": 100.2, "action_success_rate": 0.536},
    "claude-opus-5": {"usd_per_action": 0.1459, "http_per_action": 11.20,
                      "wall_s_per_action": 58.5, "action_success_rate": 0.522},
}

# ---- the gate (BUDGET_REPORT.md section 9) --------------------------------
CAMPAIGN_USD_CAP = 50.00        # whole campaign, every tier, every re-run
TIER_USD_CAP = {                # per tier, so one tier cannot eat the cap
    "claude-haiku-4-5-20251001": 20.00,
    "claude-opus-5": 30.00,
    "claude-sonnet-5": 30.00,
}
CELL_COST_MULTIPLE = 3.0        # one cell vs its tier's pilot unit price
HTTP_PER_ACTION_CAP = 20.0      # pilot haiku 7.11; 2.8x is API-side degradation
ACTION_SUCCESS_FLOOR = 0.35     # pilot haiku 0.713
CONSECUTIVE_DEAD_CAP = 2
# Two different clocks, because the repeats of a cell run concurrently and the
# sum of their wall times is compute-hours, not elapsed hours. Capping elapsed
# time with a sum would fire at a third of the intended duration -- so cap each
# on its own terms. ELAPSED is the one that means "this has been running all
# day"; COMPUTE is the one that means "this is doing far more work than planned".
ELAPSED_SECONDS_CAP = 8 * 3600
COMPUTE_SECONDS_CAP = 20 * 3600
MIN_ACTIONS_FOR_RATIOS = 20     # ratios are noise below this

DEAD_OUTCOMES = ("no_reset_window", "harness_error", "model_error", "api_unusable")


# ------------------------------------------------------------------ ledgering
def append_cell(cell: Dict[str, Any]) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CELLS_PATH, "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(cell, sort_keys=True, ensure_ascii=True) + "\n")


def load_cells() -> List[Dict[str, Any]]:
    if not os.path.exists(CELLS_PATH):
        return []
    out = []
    for line in open(CELLS_PATH, encoding="utf-8"):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


# ---------------------------------------------------------------------- gate
def elapsed_seconds(cells: List[Dict[str, Any]]) -> Optional[float]:
    """Real time since the first cell started, in seconds."""
    stamps = [c.get("started") for c in cells if c.get("started")]
    if not stamps:
        return None
    first = time.strptime(min(stamps), "%Y-%m-%dT%H:%M:%SZ")
    return time.time() - time.mktime(first) + time.timezone


def evaluate_gate(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Returns {"state": "green"|"red", "tripped": [...], "totals": {...}}.

    Deliberately computed from the persisted cell records rather than from
    in-memory state: a gate that only exists inside the process that is
    spending the money is not a gate.
    """
    tripped: List[str] = []
    total_cost = sum(c.get("cost_usd", 0.0) or 0.0 for c in cells)
    total_ok = sum(c.get("actions_ok", 0) or 0 for c in cells)
    total_failed = sum(c.get("actions_failed", 0) or 0 for c in cells)
    total_http = sum(c.get("http_calls_gameplay", 0) or 0 for c in cells)
    total_wall = sum(c.get("wall_seconds", 0) or 0 for c in cells)

    by_tier: Dict[str, float] = {}
    for c in cells:
        by_tier[c["model"]] = by_tier.get(c["model"], 0.0) + (c.get("cost_usd", 0.0) or 0.0)

    if total_cost > CAMPAIGN_USD_CAP:
        tripped.append("G1 campaign cost $%.2f > cap $%.2f" % (total_cost, CAMPAIGN_USD_CAP))
    for tier, spend in sorted(by_tier.items()):
        cap = TIER_USD_CAP.get(tier)
        if cap is not None and spend > cap:
            tripped.append("G1b tier %s spend $%.2f > cap $%.2f" % (tier, spend, cap))

    for c in cells:
        unit = PILOT_UNIT.get(c["model"], {}).get("usd_per_action")
        if unit is None:
            continue
        ceiling = CELL_COST_MULTIPLE * unit * (c.get("budget") or ACTION_BUDGET)
        if (c.get("cost_usd", 0.0) or 0.0) > ceiling:
            tripped.append("G2 cell %s cost $%.4f > %.1fx pilot unit ($%.4f)"
                           % (c.get("run_id"), c["cost_usd"], CELL_COST_MULTIPLE, ceiling))

    if total_ok >= MIN_ACTIONS_FOR_RATIOS:
        http_per_action = total_http / total_ok
        if http_per_action > HTTP_PER_ACTION_CAP:
            tripped.append("G3 http/action %.2f > cap %.1f" % (http_per_action, HTTP_PER_ACTION_CAP))
    if (total_ok + total_failed) >= MIN_ACTIONS_FOR_RATIOS:
        rate = total_ok / (total_ok + total_failed)
        if rate < ACTION_SUCCESS_FLOOR:
            tripped.append("G5 action success %.3f < floor %.2f" % (rate, ACTION_SUCCESS_FLOOR))

    streak = 0
    for c in cells:
        streak = streak + 1 if c.get("outcome") in DEAD_OUTCOMES else 0
        if streak >= CONSECUTIVE_DEAD_CAP:
            tripped.append("G4 %d consecutive dead cells, last %s (%s)"
                           % (streak, c.get("run_id"), c.get("outcome")))
            break

    elapsed = elapsed_seconds(cells)
    if elapsed is not None and elapsed > ELAPSED_SECONDS_CAP:
        tripped.append("G6a elapsed %.1f h > cap %.1f h"
                       % (elapsed / 3600, ELAPSED_SECONDS_CAP / 3600))
    if total_wall > COMPUTE_SECONDS_CAP:
        tripped.append("G6b compute %.1f h > cap %.1f h"
                       % (total_wall / 3600, COMPUTE_SECONDS_CAP / 3600))

    # G7 is the one that is not about money. It should be unreachable -- the
    # client refuses sealed games before opening a socket -- so if it ever
    # fires, something structural is wrong and the campaign must not continue.
    dev = set(arc_client.dev_pile())
    for c in cells:
        if c.get("game_id") not in dev:
            tripped.append("G7 SEALED-PILE CONTACT: cell %s names %s, not in the "
                           "development pile" % (c.get("run_id"), c.get("game_id")))

    return {
        "state": "red" if tripped else "green",
        "tripped": tripped,
        "evaluated_at": ledger.utcnow(),
        "totals": {
            "cells": len(cells),
            "cost_usd": round(total_cost, 4),
            "cost_by_tier": {k: round(v, 4) for k, v in sorted(by_tier.items())},
            "actions_ok": total_ok,
            "actions_failed": total_failed,
            "http_calls": total_http,
            "compute_seconds": round(total_wall, 1),
            "elapsed_seconds": (round(elapsed_seconds(cells), 1)
                                if elapsed_seconds(cells) is not None else None),
            "http_per_action": round(total_http / total_ok, 2) if total_ok else None,
            "action_success_rate": (round(total_ok / (total_ok + total_failed), 3)
                                    if (total_ok + total_failed) else None),
            "usd_per_action": round(total_cost / total_ok, 4) if total_ok else None,
        },
        "caps": {
            "campaign_usd": CAMPAIGN_USD_CAP,
            "tier_usd": TIER_USD_CAP,
            "cell_cost_multiple": CELL_COST_MULTIPLE,
            "http_per_action": HTTP_PER_ACTION_CAP,
            "action_success_floor": ACTION_SUCCESS_FLOOR,
            "consecutive_dead": CONSECUTIVE_DEAD_CAP,
            "elapsed_seconds": ELAPSED_SECONDS_CAP,
            "compute_seconds": COMPUTE_SECONDS_CAP,
        },
    }


def write_gate(gate: Dict[str, Any]) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(GATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(gate, fh, indent=2, sort_keys=True)
    ledger.probe("campaign_gate", {"state": gate["state"], "tripped": gate["tripped"],
                                   "totals": gate["totals"]})


def print_gate(gate: Dict[str, Any]) -> None:
    t = gate["totals"]
    print("\n=== budget gate: %s ===" % gate["state"].upper())
    print("  cells %s | $%.4f | ok %s / failed %s | http %s | elapsed %.1f h "
          "| compute %.1f h"
          % (t["cells"], t["cost_usd"], t["actions_ok"], t["actions_failed"],
             t["http_calls"], (t["elapsed_seconds"] or 0) / 3600,
             (t["compute_seconds"] or 0) / 3600))
    print("  $/action %s | http/action %s | success %s"
          % (t["usd_per_action"], t["http_per_action"], t["action_success_rate"]))
    for tier, spend in sorted(t["cost_by_tier"].items()):
        print("  tier %-28s $%.4f / cap $%.2f" % (tier, spend, TIER_USD_CAP.get(tier, 0.0)))
    for reason in gate["tripped"]:
        print("  TRIPPED: %s" % reason)


# --------------------------------------------------------------------- runner
def run_repeat(game_id: str, model: str, budget: int, rep: int,
               results: Dict[int, Dict[str, Any]], lock: threading.Lock) -> None:
    started = time.time()
    try:
        summary = bare_cc.play(game_id, model, budget, verbose=False)
    except arc_client.SealedGameError:
        raise
    except Exception as exc:
        summary = {"run_id": None, "arm": "bare_cc", "game_id": game_id,
                   "model": model, "budget": budget, "outcome": "harness_error",
                   "error": "%s: %s" % (type(exc).__name__, exc),
                   "actions_ok": 0, "actions_failed": 0, "model_calls": 0,
                   "cost_usd": 0.0, "http_calls_gameplay": 0}
    summary["wall_seconds"] = round(time.time() - started, 1)
    summary["repeat"] = rep
    summary["campaign"] = "phase3-variance-envelope"
    with lock:
        results[rep] = summary
    print("  [rep %d] %s -> %s (%d ok / %d failed, $%.4f, %.0fs)"
          % (rep, model, summary["outcome"], summary.get("actions_ok", 0),
             summary.get("actions_failed", 0), summary.get("cost_usd", 0.0),
             summary["wall_seconds"]), flush=True)


def run_game(game_id: str, model: str, repeats: int, budget: int) -> List[Dict[str, Any]]:
    """The `repeats` episodes of one cell, concurrently.

    Concurrent because the whole point is repeated *identical* cells: running
    them minutes apart instead of hours apart keeps API-side conditions closer
    to constant, so the spread that comes out is the arm's variance and not the
    afternoon's. The pilot already established the API tolerates 4-way
    concurrency (BUDGET_REPORT section 7).
    """
    print("=== %s x %s x %d repeats (budget %d) ===" % (game_id, model, repeats, budget),
          flush=True)
    results: Dict[int, Dict[str, Any]] = {}
    lock = threading.Lock()
    threads = [threading.Thread(target=run_repeat,
                                args=(game_id, model, budget, rep, results, lock))
               for rep in range(1, repeats + 1)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return [results[k] for k in sorted(results)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=None, help="one development-pile game id")
    ap.add_argument("--model", default=CAMPAIGN_TIER)
    ap.add_argument("--repeats", type=int, default=REPEATS)
    ap.add_argument("--budget", type=int, default=ACTION_BUDGET)
    ap.add_argument("--gate-only", action="store_true",
                    help="re-evaluate the gate over recorded cells and exit")
    args = ap.parse_args(argv)

    if args.gate_only:
        gate = evaluate_gate(load_cells())
        write_gate(gate)
        print_gate(gate)
        return 3 if gate["state"] == "red" else 0

    if not args.game:
        print("--game is required: the campaign advances one game at a time so "
              "the ledger can be audited between games")
        return 2

    dev = arc_client.dev_pile()
    matches = [g for g in dev if g.startswith(args.game.split("-")[0])]
    if not matches:
        print("no development-pile game matches %r" % args.game)
        return 2
    game_id = matches[0]
    assert game_id not in arc_client.sealed_pile(), "sealed game reached the campaign"

    # Pre-flight: never start a game the gate has already stopped.
    gate = evaluate_gate(load_cells())
    if gate["state"] == "red":
        print_gate(gate)
        print("\ngate is already RED -- not starting %s" % game_id)
        return 3

    cells = run_game(game_id, args.model, args.repeats, args.budget)
    for cell in cells:
        append_cell(cell)

    gate = evaluate_gate(load_cells())
    write_gate(gate)
    print_gate(gate)
    print(json.dumps(cells, indent=2, sort_keys=True))
    return 3 if gate["state"] == "red" else 0


if __name__ == "__main__":
    sys.exit(main())
