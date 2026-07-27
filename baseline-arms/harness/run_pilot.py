"""The M4 pilot: development pile x three model tiers, bare-CC arm.

Deliberately small and hard-capped. The ticket calls the two baseline arms the
project's most escape-prone cost, so the pilot exists to buy a *unit price*,
not results: enough steps per cell to extrapolate, and not one more.

Scope is fixed here rather than passed in, so widening it is a code change with
a diff, not a flag someone can bump on a whim:

    games   -- the development pile, all 4 (there are only 4)
    models  -- three tiers, full ids (D-002)
    budget  -- 25 actions per cell (D-008)

    python -m harness.run_pilot [--only-game G] [--only-model M] [--budget N]
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List

from . import arc_client, bare_cc, ledger

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(TRACK, "out")

PILOT_MODELS = [
    bare_cc.MODEL_TIERS["cheap"],
    bare_cc.MODEL_TIERS["mid"],
    bare_cc.MODEL_TIERS["expensive"],
]
PILOT_BUDGET = 25


def run_cell(game_id: str, model: str, budget: int) -> Dict[str, Any]:
    print("=== %s x %s (budget %d) ===" % (game_id, model, budget), flush=True)
    started = time.time()
    try:
        summary = bare_cc.play(game_id, model, budget)
    except arc_client.SealedGameError:
        raise
    except Exception as exc:                       # a dead cell must not kill the run
        summary = {"run_id": None, "arm": "bare_cc", "game_id": game_id,
                   "model": model, "budget": budget, "outcome": "harness_error",
                   "error": "%s: %s" % (type(exc).__name__, exc),
                   "actions_ok": 0, "actions_failed": 0, "model_calls": 0,
                   "cost_usd": 0.0, "http_calls_gameplay": 0}
    summary["wall_seconds"] = round(time.time() - started, 1)
    print("--- %s x %s -> %s (%d ok / %d failed, $%.4f, %.0fs)"
          % (game_id, model, summary["outcome"], summary.get("actions_ok", 0),
             summary.get("actions_failed", 0), summary.get("cost_usd", 0.0),
             summary["wall_seconds"]), flush=True)
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-game", default=None)
    ap.add_argument("--only-model", default=None)
    ap.add_argument("--budget", type=int, default=PILOT_BUDGET)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    games: List[str] = arc_client.dev_pile()
    if args.only_game:
        games = [g for g in games if g.startswith(args.only_game.split("-")[0])]
        if not games:
            print("no development-pile game matches %r" % args.only_game)
            return 2
    models = [args.only_model] if args.only_model else PILOT_MODELS

    # Belt and braces: the guard in arc_client fires anyway, but assert here too
    # so a bad --only-game can never even reach the loop.
    sealed = arc_client.sealed_pile()
    for g in games:
        assert g not in sealed, "sealed game %s reached the pilot" % g

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = args.out or os.path.join(
        OUT_DIR, "pilot_%s.json" % (args.only_game or "all"))

    results = []
    for game_id in games:
        for model in models:
            results.append(run_cell(game_id, model, args.budget))
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(results, fh, indent=2, sort_keys=True)

    ledger.probe("pilot_complete", {"games": games, "models": models,
                                    "budget": args.budget, "cells": len(results)})
    print(json.dumps(results, indent=2, sort_keys=True))
    print("\nwrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
