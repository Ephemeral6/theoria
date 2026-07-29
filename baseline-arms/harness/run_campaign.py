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

from . import arc_client, bare_cc, ledger, spend

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(TRACK, "out")
CELLS_PATH = os.path.join(OUT_DIR, "campaign_cells.jsonl")
GATE_PATH = os.path.join(OUT_DIR, "campaign_gate.json")
#: Append-only, tracked. Adjudications: which cells have been ruled on, by
#: whom, and what was fixed as a result. See `barriers()` and G4 below.
BARRIERS_PATH = os.path.join(OUT_DIR, "campaign_barriers.jsonl")

CAMPAIGN_NAME = "phase3-variance-envelope"

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
#: Outcomes that are NOT dead cells, spelled out because two of them are new and
#: the distinction is load-bearing. `failure_grind` is an episode that spent its
#: budget and failed a lot of actions -- a result about the arm, measured by G5
#: and G2, not evidence the API is down. `spend_gate_tripped` is the pool
#: refusing, which is a correct stop and says nothing about the API at all.
#: Filing either under a dead outcome would put a *finding* into G4's streak and
#: stop the campaign for having measured something.
LIVE_OUTCOMES = ("budget_exhausted", "failure_grind", "spend_gate_tripped",
                 "win", "game_over", "gave_up", "unparseable_reply",
                 "spend_ceiling_hit")


# ------------------------------------------------------------------- barriers
def barriers() -> List[Dict[str, Any]]:
    """Adjudications, oldest first. See `evaluate_gate` for what they change.

    A budget gate is a stop-and-adjudicate mechanism, but the first version had
    no way to record that the adjudication had happened -- so G4, once tripped,
    was permanent, and BUDGET_REPORT section 11.5's "re-runs just append, and
    `--gate-only` can re-adjudicate at any time" was not actually reachable.
    A barrier is that record.

    **The rule for what a barrier moves, stated once so it is not discovered one
    gate at a time.** The eight thresholds are two kinds:

      * **Condition clocks** -- G4 (consecutive dead cells) and G6a (real time
        since the first cell started). Each is a claim about what is happening
        *now*: "the API is failing repeatedly", "this has been running all day".
        A barrier restarts both, because a campaign that ran for twenty-four
        minutes, stopped on a correct refusal, was diagnosed, and resumed
        sixteen hours later has neither a live failure streak nor a day of
        running behind it -- it has a gap, and measuring the gap is a unit
        error of the same family as the one that split G6 in two.
      * **Cumulative sums** -- G1, G1b, G2, G3, G5, G6b, G7. Every one of them
        keeps summing every cell ever recorded, adjudicated or not. Money spent
        is never forgiven, compute hours already burned still count, and a
        sealed-pile contact is not something an adjudication can retire. A
        barrier that reset a dollar total would be the "raise the threshold
        until it goes green" move that section 11.3 exists to forbid, and the
        test for it is here: `test_a_barrier_moves_g4_and_nothing_else`.

    And it has to say what was fixed. `remediations` is required and a barrier
    with an empty one is refused, because the entire difference between an
    adjudication and a mute button is whether something changed.
    """
    if not os.path.exists(BARRIERS_PATH):
        return []
    out = []
    for line in open(BARRIERS_PATH, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if not record.get("remediations"):
            raise ValueError(
                "%s has a barrier with no `remediations` (%r). A barrier that "
                "does not say what was fixed is a gate being silenced, which is "
                "the one move BUDGET_REPORT.md section 11.3 rules out."
                % (BARRIERS_PATH, record.get("barrier_id")))
        out.append(record)
    return out


def cells_after_last_barrier(cells: List[Dict[str, Any]],
                             bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The cells G4 still judges: everything after the last adjudicated run_id."""
    if not bars:
        return cells
    last = bars[-1].get("adjudicated_through_run_id")
    ids = [c.get("run_id") for c in cells]
    if last not in ids:
        # Fail closed: a barrier naming a cell that is not in the record cannot
        # be positioned, so it is not applied. Judging everything is the safe
        # direction -- it can only stop the campaign, never let it run on.
        return cells
    return cells[ids.index(last) + 1:]


# ------------------------------------------------------------------ ledgering
def append_cell(cell: Dict[str, Any]) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(CELLS_PATH, "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(cell, sort_keys=True, ensure_ascii=True) + "\n")


def load_cells(campaign: Optional[str] = None) -> List[Dict[str, Any]]:
    """Every recorded cell, or only one campaign's.

    `campaign_cells.jsonl` is append-only and now holds more than one campaign:
    the variance envelope, and the section-2.1 unit-price re-measurement that
    followed it on two other tiers. They must not be summed together. The gate's
    thresholds are per campaign (a campaign's $50 cap is not a licence for the
    next one), and the envelope's spread is meaningless if another tier's cells
    are pooled into it. A cell written before the field existed is treated as
    belonging to the envelope, which is where it came from.
    """
    if not os.path.exists(CELLS_PATH):
        return []
    out = []
    for line in open(CELLS_PATH, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        cell = json.loads(line)
        if campaign is None or (cell.get("campaign") or CAMPAIGN_NAME) == campaign:
            out.append(cell)
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
    # `judged` is the post-adjudication segment: what the two condition clocks
    # (G4, G6a) look at. Everything else below sums `cells`, all of them.
    bars = barriers()
    judged = cells_after_last_barrier(cells, bars)

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
    for c in judged:
        streak = streak + 1 if c.get("outcome") in DEAD_OUTCOMES else 0
        if streak >= CONSECUTIVE_DEAD_CAP:
            tripped.append("G4 %d consecutive dead cells, last %s (%s)%s"
                           % (streak, c.get("run_id"), c.get("outcome"),
                              (" [judging %d of %d cells, after barrier %s]"
                               % (len(judged), len(cells), bars[-1]["barrier_id"]))
                              if bars else ""))
            break

    # G6a is a condition clock: real time since the *current* segment's first
    # cell. Measured across an adjudicated stop it would count the stop itself,
    # which is a duration nobody spent and nothing was running for. G6b below
    # is the work-done clock and keeps summing every cell ever recorded.
    elapsed = elapsed_seconds(judged)
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
        # Printed and persisted whether or not G4 fires, so a green gate can
        # never quietly be green *because* of a barrier nobody noticed.
        "barriers": [{"barrier_id": b["barrier_id"],
                      "adjudicated_through_run_id": b.get("adjudicated_through_run_id"),
                      "utc": b.get("utc"),
                      "remediations": b.get("remediations")} for b in bars],
        "g4_judges_cells": len(judged),
        "totals": {
            "cells": len(cells),
            "cost_usd": round(total_cost, 4),
            "cost_by_tier": {k: round(v, 4) for k, v in sorted(by_tier.items())},
            "actions_ok": total_ok,
            "actions_failed": total_failed,
            "http_calls": total_http,
            "compute_seconds": round(total_wall, 1),
            "elapsed_seconds": round(elapsed, 1) if elapsed is not None else None,
            "elapsed_seconds_all_cells": (
                round(elapsed_seconds(cells), 1)
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


def gate_path(campaign: str = CAMPAIGN_NAME) -> str:
    """One gate file per campaign. Sharing one would let the last campaign to
    finish overwrite the standing verdict on another, which is how a RED becomes
    invisible."""
    if campaign == CAMPAIGN_NAME:
        return GATE_PATH
    slug = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in campaign)
    return os.path.join(OUT_DIR, "campaign_gate.%s.json" % slug)


def write_gate(gate: Dict[str, Any], campaign: str = CAMPAIGN_NAME) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(gate_path(campaign), "w", encoding="utf-8") as fh:
        json.dump(gate, fh, indent=2, sort_keys=True)
    ledger.probe("campaign_gate", {"campaign": campaign, "state": gate["state"],
                                   "tripped": gate["tripped"],
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
    for tier, tier_spend in sorted(t["cost_by_tier"].items()):
        print("  tier %-28s $%.4f / cap $%.2f"
              % (tier, tier_spend, TIER_USD_CAP.get(tier, 0.0)))
    # Always printed, never only when G4 fires: a green gate must not be green
    # because of a barrier the reader did not know was there.
    for bar in gate.get("barriers", []):
        print("  BARRIER %s (%s): G4 judges the %d cell(s) after %s"
              % (bar["barrier_id"], bar.get("utc"), gate.get("g4_judges_cells", 0),
                 bar.get("adjudicated_through_run_id")))
    for reason in gate["tripped"]:
        print("  TRIPPED: %s" % reason)


def print_pool(when: str) -> None:
    """The shared pool, across every campaign and every session.

    Printed at both ends of a game because the number that matters is the one
    INC-BA-003 could not see: not what this campaign spent, but what the pool
    holds in total while other sessions are also drawing on it.
    """
    try:
        gate = spend.SpendGate()
        totals = gate.totals()
    except spend.SpendGateError as exc:
        print("\n=== shared spend pool (%s): UNAVAILABLE ===\n  %s" % (when, exc))
        return
    print("\n=== shared spend pool (%s) ===" % when)
    print("  spent $%.4f / $%.2f   %d / %d actions   (%d live reservation(s))"
          % (totals.usd, totals.ceiling_usd, totals.actions,
             totals.ceiling_actions, len(totals.live)))
    for name, bucket in sorted(totals.by_campaign.items()):
        print("    %-34s $%8.4f  %6d actions" % (name, bucket["usd"], bucket["actions"]))
    if len(totals.live) > 1:
        print("  NOTE: %d concurrent reservations on one pool -- counted, which "
              "is what INC-BA-003 could not do." % len(totals.live))


# --------------------------------------------------------------------- runner
def cell_caps(model: str, budget: int) -> Dict[str, Any]:
    """What one cell may claim from the shared pool.

    Both numbers are the campaign's own gates, restated as a claim rather than
    computed afresh, so there is one threshold and not two that can drift:

      * dollars -- G2's ceiling exactly (`CELL_COST_MULTIPLE` x the tier's pilot
        unit price x the action budget). A cell that would exhaust its
        reservation is a cell G2 was about to fail anyway; the difference is
        that the pool refuses it before the money leaves rather than after.
      * actions -- G3's ceiling (`HTTP_PER_ACTION_CAP` x budget) plus the
        episode's fixed overhead: the RESET envelope retries up to 30 times and
        the scorecard is opened once and closed with up to 8 retries.
    """
    unit = PILOT_UNIT.get(model, {}).get("usd_per_action")
    usd = (CELL_COST_MULTIPLE * unit * budget) if unit is not None else 5.00
    overhead = 30 + 1 + 8
    return {"usd": round(usd, 4),
            "actions": int(HTTP_PER_ACTION_CAP * budget) + overhead}


def run_repeat(game_id: str, model: str, budget: int, rep: int,
               results: Dict[int, Dict[str, Any]], lock: threading.Lock,
               campaign: str = CAMPAIGN_NAME) -> None:
    started = time.time()
    caps = cell_caps(model, budget)
    binding = None
    #: Bound before the try so the `finally` cannot raise a NameError over the
    #: top of a SealedGameError -- the one exception here that is re-raised, and
    #: the one that must never be masked.
    summary: Optional[Dict[str, Any]] = None

    def dead(outcome: str, exc: Exception) -> Dict[str, Any]:
        return {"run_id": None, "arm": "bare_cc", "game_id": game_id,
                "model": model, "budget": budget, "outcome": outcome,
                "error": "%s: %s" % (type(exc).__name__, exc),
                "spend_gate_rule": getattr(exc, "rule", None),
                "actions_ok": 0, "actions_failed": 0, "model_calls": 0,
                "cost_usd": 0.0, "http_calls_gameplay": 0}

    try:
        # One reservation per cell, not per campaign. Three repeats run
        # concurrently, so a shared claim would give three threads one set of
        # counters and no cell could say what it had spent -- which is
        # INC-BA-003's third damage (an append-only file mixing campaigns with
        # no line able to say which was which) reproduced one level down. Per
        # cell, the reservation id lands in the cell record and the attribution
        # is exact rather than reconstructed.
        binding = spend.open_binding(
            campaign, caps["usd"], caps["actions"],
            holder={"game_id": game_id, "model": model, "repeat": rep,
                    "budget": budget, "runner": "run_campaign"},
            ttl_seconds=7200)
        summary = bare_cc.play(game_id, model, budget, verbose=False,
                               spend_binding=binding)
    except arc_client.SealedGameError:
        raise
    except spend.SpendGateError as exc:
        # The pool refused. Not a harness fault and not an API fault: a correct
        # refusal, recorded with the rule that produced it.
        summary = dead("spend_gate_tripped", exc)
    except Exception as exc:
        summary = dead("harness_error", exc)
    finally:
        if binding is not None:
            # Give the unspent remainder back. What was spent stays against the
            # pool for ever; only the *hold* is released.
            if summary is not None:
                summary["spend"] = summary.get("spend") or binding.describe()
            binding.release("cell finished")
    summary["cell_caps"] = caps
    summary["wall_seconds"] = round(time.time() - started, 1)
    summary["repeat"] = rep
    summary["campaign"] = campaign
    with lock:
        results[rep] = summary
    print("  [rep %d] %s -> %s (%d ok / %d failed, longest fail run %s, "
          "$%.4f, %.0fs)"
          % (rep, model, summary["outcome"], summary.get("actions_ok", 0),
             summary.get("actions_failed", 0),
             summary.get("actions_failed_consecutive_max", "?"),
             summary.get("cost_usd", 0.0), summary["wall_seconds"]), flush=True)


def run_game(game_id: str, model: str, repeats: int, budget: int,
             campaign: str = CAMPAIGN_NAME) -> List[Dict[str, Any]]:
    """The `repeats` episodes of one cell, concurrently.

    Concurrent because the whole point is repeated *identical* cells: running
    them minutes apart instead of hours apart keeps API-side conditions closer
    to constant, so the spread that comes out is the arm's variance and not the
    afternoon's. The pilot already established the API tolerates 4-way
    concurrency (BUDGET_REPORT section 7).
    """
    print("=== %s x %s x %d repeats (budget %d) [%s] ==="
          % (game_id, model, repeats, budget, campaign), flush=True)
    results: Dict[int, Dict[str, Any]] = {}
    lock = threading.Lock()
    threads = [threading.Thread(target=run_repeat,
                                args=(game_id, model, budget, rep, results, lock,
                                      campaign))
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
    ap.add_argument("--campaign", default=CAMPAIGN_NAME,
                    help="which campaign these cells belong to; gates and "
                         "summaries are scoped to it and never summed across")
    ap.add_argument("--gate-only", action="store_true",
                    help="re-evaluate the gate over recorded cells and exit")
    args = ap.parse_args(argv)

    if args.gate_only:
        gate = evaluate_gate(load_cells(args.campaign))
        write_gate(gate, args.campaign)
        print_gate(gate)
        print_pool("now")
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
    gate = evaluate_gate(load_cells(args.campaign))
    if gate["state"] == "red":
        print_gate(gate)
        print("\ngate is already RED -- not starting %s" % game_id)
        return 3

    print_pool("before %s" % game_id)
    cells = run_game(game_id, args.model, args.repeats, args.budget,
                     campaign=args.campaign)
    for cell in cells:
        append_cell(cell)

    gate = evaluate_gate(load_cells(args.campaign))
    write_gate(gate, args.campaign)
    print_gate(gate)
    print_pool("after %s" % game_id)
    print(json.dumps(cells, indent=2, sort_keys=True))
    return 3 if gate["state"] == "red" else 0


if __name__ == "__main__":
    sys.exit(main())
