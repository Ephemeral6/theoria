"""Aggregate the pilot cells into the unit prices the budget gate needs.

The pilot buys three numbers per model tier, and nothing else matters here:

    $/action      -- cost of one *successful* game action, model side
    http/action   -- HTTP calls burned per successful action (the D-005 tax)
    wall s/action -- how long a full sweep would actually take

Everything downstream in BUDGET_REPORT.md is these three multiplied out.

    python -m harness.summarise_pilot [--json]
"""

import argparse
import collections
import glob
import json
import os
import sys
from typing import Any, Dict, List

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(TRACK, "out")


DEAD_OUTCOMES = ("no_reset_window", "harness_error", "model_error")


def load_cells():
    """Returns (kept, superseded).

    A (game, model) cell can be re-run -- the sonnet row was re-run once the
    model-call retry landed. Keep the better attempt per pair, and *return* the
    ones dropped rather than discarding them silently: a summary that quietly
    swallows a failed attempt is how a unit price ends up flattering itself.
    """
    cells = []
    for path in sorted(glob.glob(os.path.join(OUT_DIR, "pilot_*.json"))):
        with open(path, encoding="utf-8") as fh:
            for cell in json.load(fh):
                cell["_source"] = os.path.basename(path)
                cells.append(cell)

    best: Dict[Any, Dict[str, Any]] = {}
    superseded: List[Dict[str, Any]] = []
    for cell in cells:
        key = (cell["game_id"], cell["model"])
        rank = (cell.get("outcome") not in DEAD_OUTCOMES, cell.get("actions_ok", 0) or 0)
        if key not in best:
            best[key] = cell
            continue
        prev = best[key]
        prev_rank = (prev.get("outcome") not in DEAD_OUTCOMES, prev.get("actions_ok", 0) or 0)
        if rank > prev_rank:
            superseded.append(prev)
            best[key] = cell
        else:
            superseded.append(cell)
    return list(best.values()), superseded


def summarise(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_model: Dict[str, Dict[str, float]] = collections.defaultdict(
        lambda: collections.defaultdict(float))
    for c in cells:
        m = by_model[c["model"]]
        m["cells"] += 1
        m["actions_ok"] += c.get("actions_ok", 0) or 0
        m["actions_failed"] += c.get("actions_failed", 0) or 0
        m["model_calls"] += c.get("model_calls", 0) or 0
        m["cost_usd"] += c.get("cost_usd", 0.0) or 0.0
        m["http_calls"] += c.get("http_calls_gameplay", 0) or 0
        m["wall_seconds"] += c.get("wall_seconds", 0) or 0
        m["output_tokens"] += c.get("output_tokens", 0) or 0
        m["cache_read_tokens"] += c.get("cache_read_tokens", 0) or 0
        m["cache_creation_tokens"] += c.get("cache_creation_tokens", 0) or 0
        m["levels_completed"] += c.get("levels_completed", 0) or 0
        if c.get("outcome") not in ("no_reset_window", "harness_error", "model_error"):
            m["usable_cells"] += 1

    rows = {}
    for model, m in by_model.items():
        ok = m["actions_ok"]
        rows[model] = {
            "cells": int(m["cells"]),
            "usable_cells": int(m["usable_cells"]),
            "actions_ok": int(ok),
            "actions_failed": int(m["actions_failed"]),
            "model_calls": int(m["model_calls"]),
            "cost_usd": round(m["cost_usd"], 4),
            "http_calls": int(m["http_calls"]),
            "wall_seconds": int(m["wall_seconds"]),
            "output_tokens": int(m["output_tokens"]),
            "cache_read_tokens": int(m["cache_read_tokens"]),
            "cache_creation_tokens": int(m["cache_creation_tokens"]),
            "levels_completed": int(m["levels_completed"]),
            "usd_per_action": round(m["cost_usd"] / ok, 4) if ok else None,
            "usd_per_model_call": (round(m["cost_usd"] / m["model_calls"], 4)
                                   if m["model_calls"] else None),
            "http_per_action": round(m["http_calls"] / ok, 2) if ok else None,
            "wall_s_per_action": round(m["wall_seconds"] / ok, 1) if ok else None,
            "action_success_rate": (round(ok / (ok + m["actions_failed"]), 3)
                                    if (ok + m["actions_failed"]) else None),
        }
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    cells, superseded = load_cells()
    if not cells:
        print("no pilot output in %s" % OUT_DIR)
        return 1
    rows = summarise(cells)

    if args.json:
        print(json.dumps({"cells": cells, "superseded": superseded,
                          "by_model": rows}, indent=2, sort_keys=True))
        return 0

    if superseded:
        print("=== superseded attempts (re-run, not counted below) ===")
        for c in superseded:
            print("  %-18s %-28s %-18s ok=%-3s $%.4f  [%s]" % (
                c["game_id"], c["model"], c["outcome"], c.get("actions_ok", 0),
                c.get("cost_usd", 0.0), c.get("_source")))
        print("  superseded spend: $%.4f (real money, counted in the pilot total)"
              % sum(c.get("cost_usd", 0.0) or 0.0 for c in superseded))
        print()

    print("=== per cell ===")
    print("%-18s %-28s %-18s %5s %5s %6s %9s %7s" %
          ("game", "model", "outcome", "ok", "fail", "calls", "cost$", "wall_s"))
    for c in sorted(cells, key=lambda c: (c["game_id"], c["model"])):
        print("%-18s %-28s %-18s %5s %5s %6s %9.4f %7s" % (
            c["game_id"], c["model"], c["outcome"], c.get("actions_ok", 0),
            c.get("actions_failed", 0), c.get("model_calls", 0),
            c.get("cost_usd", 0.0), c.get("wall_seconds", 0)))

    print("\n=== per model tier ===")
    for model, r in sorted(rows.items()):
        print("\n%s" % model)
        for k in ("cells", "usable_cells", "actions_ok", "actions_failed",
                  "action_success_rate", "model_calls", "cost_usd",
                  "usd_per_action", "usd_per_model_call", "http_per_action",
                  "wall_s_per_action", "output_tokens", "cache_read_tokens",
                  "levels_completed"):
            print("    %-22s %s" % (k, r[k]))

    every = cells + superseded
    total = sum(c.get("cost_usd", 0.0) or 0.0 for c in every)
    actions = sum(c.get("actions_ok", 0) or 0 for c in every)
    http = sum(c.get("http_calls_gameplay", 0) or 0 for c in every)
    print("\n=== pilot total (including superseded attempts -- this is the bill) ===")
    print("  cells %d (%d kept, %d superseded) | successful actions %d "
          "| HTTP calls %d | cost $%.4f"
          % (len(every), len(cells), len(superseded), actions, http, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
