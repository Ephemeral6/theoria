"""The approved full run: bare CC, haiku tier only, whole development pile.

Approved 2026-07-28 against `BUDGET_REPORT.md` §3.4 (haiku single tier,
S1 baseline-parity cap): 3014 successful actions across the four development
pile games, ~$103, ~46 h of wall clock serial and ~16 h with one process per
game.

A sixteen-hour run needs three things the pilot harness did not have:

  * **A spend ceiling that aborts.** An extrapolation is not a guarantee. Each
    game carries a hard dollar cap; crossing it stops that game rather than
    quietly spending past the approved figure.
  * **Checkpoints.** Progress is written after every episode so a crash costs
    one episode, not the campaign, and so anyone can see where it is without
    reading a 4 MB ledger.
  * **Episode restarts.** An ARC session cannot be resumed -- if it dies, the
    game restarts at level 1. That is a real cost, so restarts are counted and
    capped, and the wasted actions stay on the books.

    python -m harness.campaign --game sk48-d8078629
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from . import arc_client, bare_cc, interlock, key_proxy, ledger

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(TRACK, "out")
CAMPAIGN_DIR = os.path.join(OUT_DIR, "campaign")

APPROVED_MODEL = bare_cc.MODEL_TIERS["cheap"]          # haiku only, as approved

# Pilot-measured unit price, used only to size the abort ceiling.
USD_PER_ACTION = 0.0342
CEILING_FACTOR = 1.6          # headroom over the extrapolation before aborting

# Per-game action budget = that game's official baseline action count, summed
# over all its levels. This is BUDGET_REPORT.md scenario S1.
BASELINE_ACTIONS = {
    "ar25-0c556536": 748,
    "g50t-5849a774": 879,
    "sk48-d8078629": 1070,
    "tn36-ef4dde99": 317,
}

MAX_EPISODES = 12             # restarts per game before giving up
DEAD_OUTCOMES = ("no_reset_window", "api_unusable", "model_error", "harness_error")


def checkpoint_path(game_id: str) -> str:
    return os.path.join(CAMPAIGN_DIR, "campaign_%s.json" % game_id.split("-")[0])


def save(state: Dict[str, Any]) -> None:
    os.makedirs(CAMPAIGN_DIR, exist_ok=True)
    path = checkpoint_path(state["game_id"])
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)                     # atomic: never a half-written file


def load(game_id: str) -> Dict[str, Any]:
    path = checkpoint_path(game_id)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def run_game(game_id: str, model: str, total_budget: int, ceiling_usd: float,
             max_episodes: int, resume: bool) -> Dict[str, Any]:
    """The credential child wraps the whole game, then `_run_game` plays it.

    Split in two only so the sixteen-hour body below keeps its indentation and
    stays diffable: everything this adds is one child process, started before
    the first episode and stopped after the last one whatever happens in
    between (STATUS.md GAP-5, DECISIONS.md D-026). One child per game, not per
    episode -- the arm's cookie jar already spans episodes, and so should the
    hop in front of it.
    """
    with key_proxy.sealed_upstream(
            run_id="campaign-%s" % game_id.split("-")[0]) as proxy:
        return _run_game(game_id, model, total_budget, ceiling_usd,
                         max_episodes, resume, base_url=proxy.base_url)


def _run_game(game_id: str, model: str, total_budget: int, ceiling_usd: float,
              max_episodes: int, resume: bool,
              base_url: Optional[str] = None) -> Dict[str, Any]:
    client = arc_client.ArcClient(base_url=base_url)
    client.assert_playable(game_id)                    # fails closed on sealed

    state: Dict[str, Any] = load(game_id) if resume else {}
    if not state:
        state = {
            "game_id": game_id, "model": model, "arm": "bare_cc",
            "scenario": "S1 baseline-parity", "total_budget": total_budget,
            "ceiling_usd": round(ceiling_usd, 2), "started": ledger.utcnow(),
            "actions_ok": 0, "actions_failed": 0, "cost_usd": 0.0,
            "http_calls": 0, "model_calls": 0, "episodes": [],
            "best_levels_completed": 0, "win_levels": None,
            "status": "running", "wins": 0,
        }
    else:
        state["status"] = "running"
        state["resumed_at"] = ledger.utcnow()
    save(state)

    while True:
        remaining = total_budget - state["actions_ok"]
        if remaining <= 0:
            state["status"] = "budget_exhausted"
            break
        if state["cost_usd"] >= ceiling_usd:
            state["status"] = "spend_ceiling_hit"
            break
        if len(state["episodes"]) >= max_episodes:
            state["status"] = "episode_limit_hit"
            break

        ep_index = len(state["episodes"]) + 1
        print("[%s] episode %d, %d actions left, $%.2f of $%.2f spent"
              % (game_id, ep_index, remaining, state["cost_usd"], ceiling_usd),
              flush=True)

        # The ceiling must be enforced *inside* the episode: an episode here can
        # be 1070 actions long, so a check that only runs between episodes would
        # not run for eleven hours. The same callback checkpoints live, so
        # campaign_status reflects an episode in flight rather than 0 until it
        # ends.
        headroom = ceiling_usd - state["cost_usd"]
        live = {"n": 0}

        def on_step(partial, _state=state, _ep=ep_index, _live=live):
            _live["n"] += 1
            if _live["n"] % 5:
                return
            _state["live_episode"] = {
                "n": _ep, "actions_ok": partial.get("actions_ok"),
                "actions_failed": partial.get("actions_failed"),
                "cost_usd": round(partial.get("cost_usd", 0.0), 4),
                "levels_completed": partial.get("levels_completed"),
                "at": ledger.utcnow(),
            }
            save(_state)

        summary = bare_cc.play(game_id, model, remaining, client=client,
                               action_retries=12, model_retries=3,
                               cost_ceiling=headroom, on_step=on_step,
                               verbose=True)

        state["actions_ok"] += summary.get("actions_ok", 0) or 0
        state["actions_failed"] += summary.get("actions_failed", 0) or 0
        state["cost_usd"] += summary.get("cost_usd", 0.0) or 0.0
        state["http_calls"] += summary.get("http_calls_gameplay", 0) or 0
        state["model_calls"] += summary.get("model_calls", 0) or 0
        state["best_levels_completed"] = max(state["best_levels_completed"],
                                             summary.get("levels_completed", 0) or 0)
        state["win_levels"] = summary.get("win_levels") or state["win_levels"]
        if summary.get("outcome") == "win":
            state["wins"] += 1
        state["episodes"].append({
            "n": ep_index, "run_id": summary.get("run_id"),
            "outcome": summary.get("outcome"),
            "actions_ok": summary.get("actions_ok"),
            "actions_failed": summary.get("actions_failed"),
            "levels_completed": summary.get("levels_completed"),
            "cost_usd": round(summary.get("cost_usd", 0.0) or 0.0, 4),
            "wall_seconds": summary.get("wall_seconds"),
            "error": summary.get("error"),
            "ended": ledger.utcnow(),
        })
        save(state)

        state.pop("live_episode", None)
        save(state)

        if summary.get("outcome") == "win":
            state["status"] = "won"
            break
        if summary.get("outcome") == "spend_ceiling_hit":
            state["status"] = "spend_ceiling_hit"
            break
        # A dead episode is worth one more try; an episode that merely ran out
        # of its slice just rolls into the next one.
        if summary.get("outcome") in DEAD_OUTCOMES:
            print("[%s] episode %d died (%s); restarting from level 1"
                  % (game_id, ep_index, summary.get("outcome")), flush=True)
            time.sleep(20)

    state["ended"] = ledger.utcnow()
    save(state)
    print("[%s] DONE status=%s actions=%d/%d levels=%s/%s $%.2f"
          % (game_id, state["status"], state["actions_ok"], total_budget,
             state["best_levels_completed"], state["win_levels"],
             state["cost_usd"]), flush=True)
    return state


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True)
    ap.add_argument("--model", default=APPROVED_MODEL)
    ap.add_argument("--budget", type=int, default=None,
                    help="override the S1 per-game action budget")
    ap.add_argument("--ceiling", type=float, default=None,
                    help="override the abort ceiling in USD")
    ap.add_argument("--max-episodes", type=int, default=MAX_EPISODES)
    ap.add_argument("--no-resume", action="store_true")
    args = ap.parse_args(argv)

    dev = arc_client.dev_pile()
    matches = [g for g in dev if g.startswith(args.game.split("-")[0])]
    if not matches:
        print("%r is not in the development pile %s" % (args.game, dev))
        return 2
    game_id = matches[0]

    if not os.environ.get(ledger.SHARD_ENV):
        print("refusing to run unsharded: set %s (see harness/merge_ledger.py). "
              "One process per game appending to one ledger interleaves "
              "mid-record, and an append-only ledger cannot be repaired."
              % ledger.SHARD_ENV)
        return 2

    # INC-BA-003 / DECISIONS.md D-021: no campaign in this track starts while
    # another one is spending. This check is in every spending entry point, not
    # only the envelope's -- serialisation that holds in one direction only is
    # not serialisation, it just decides which campaign loses the race.
    lock = interlock.check()
    if not lock["clear"]:
        print("interlock: BLOCKED -- another campaign is live in this track")
        for reason in lock["blockers"]:
            print("  %s" % reason)
        print("`python -m harness.interlock` reports the current state.")
        return 4

    budget = args.budget or BASELINE_ACTIONS[game_id]
    ceiling = args.ceiling or round(budget * USD_PER_ACTION * CEILING_FACTOR, 2)

    print("campaign: %s x %s | %d actions | ceiling $%.2f"
          % (game_id, args.model, budget, ceiling), flush=True)
    state = run_game(game_id, args.model, budget, ceiling, args.max_episodes,
                     resume=not args.no_resume)
    print(json.dumps(state["episodes"][-3:], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
