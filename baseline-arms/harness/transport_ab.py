"""One cell on each transport, side by side. The A/B behind arc-recon INC-007a.

Every cost figure in `BUDGET_REPORT.md` was measured on a client that echoed no
cookies. arc-recon showed that transport was paying five to ten HTTP calls per
command to a load balancer that kept routing it to replicas holding no session,
and that a cookie jar removes it. This runs the two transports through *this
track's own workload* -- a real bare-CC cell, a real model, real frames -- so
the numbers land in this track's units rather than arc-recon's.

WHAT IS AND IS NOT COMPARABLE HERE

The two cells are identical in game, model, budget and code path, and differ
only in `ArcClient(cookies=...)`. But a bare-CC cell is driven by a language
model, so the two runs take *different trajectories*. That makes exactly one
metric trustworthy and the rest indicative:

  * **HTTP attempts per executed command** -- trustworthy. It is a property of
    the transport alone: how many times the client had to ask before the server
    answered. Trajectory length cancels out of the ratio.
  * actions_ok, cost, wall clock, outcome -- indicative only. A different
    trajectory reaches different frames and asks the model different questions.

AND THE COUNTER-INTUITIVE PART, WHICH IS THE POINT

`bare_cc.play` aborts a cell at `actions_failed >= 10`. On the old transport an
action "fails" when all eight of its retries miss, which at roughly one-in-nine
per attempt happens about 39% of the time -- so cells died early, having spent
their money on retries rather than gameplay. Fixing the transport means the cell
*survives to spend its whole budget*, so **the dollar cost of a cell can go UP
while the cost per successful action goes DOWN**. Reporting only $/cell would
make the fix look like a regression. Both are reported.

    cd baseline-arms && BASELINE_ARMS_SHARD=transport-ab \\
        python -m harness.transport_ab --game ar25-0c556536 --budget 20

SPENDS MONEY AND ACTION QUOTA. Two cells. Development pile only -- the sealed
guard in `arc_client` fails closed regardless. Reads arc-recon's cross-track
campaign freeze file before spending anything.
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from . import arc_client, bare_cc, ledger

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(TRACK)
OUT_PATH = os.path.join(TRACK, "out", "transport_ab.json")
FREEZE_PATH = os.path.join(REPO, "arc-recon", "data", "campaign_freeze.json")

DEFAULT_MODEL = bare_cc.MODEL_TIERS["cheap"]
DEFAULT_BUDGET = 20
COST_CEILING_PER_CELL = 2.0


def assert_not_frozen() -> None:
    """The cross-track gate arc-recon's canary writes on drift.

    Read as data, not imported as code: the whole point of putting the gate in
    a file was that any track can consult it without coupling to another
    track's modules (INC-BA-003 -- two gates that could not see each other).
    """
    if not os.path.exists(FREEZE_PATH):
        return
    with open(FREEZE_PATH, encoding="utf-8") as fh:
        state = json.load(fh)
    if state.get("frozen"):
        raise SystemExit(
            "campaigns are frozen since %s by %s (%s). Refusing to spend."
            % (state.get("since"), state.get("incident"), state.get("reason")))


def run_cell(game_id: str, model: str, budget: int, cookies: bool) -> Dict[str, Any]:
    label = "cookies=%s" % cookies
    print("=== %s | %s x %s (budget %d) ===" % (label, game_id, model, budget),
          flush=True)
    client = arc_client.ArcClient(cookies=cookies)
    started = time.time()
    try:
        summary = bare_cc.play(game_id, model, budget, client=client,
                               cost_ceiling=COST_CEILING_PER_CELL)
    except arc_client.SealedGameError:
        raise
    except Exception as exc:                    # a dead cell must not kill the A/B
        summary = {"outcome": "harness_error",
                   "error": "%s: %s" % (type(exc).__name__, exc),
                   "actions_ok": 0, "actions_failed": 0, "model_calls": 0,
                   "cost_usd": 0.0, "http_calls_gameplay": 0,
                   "reset_attempts": 0}
    summary["transport"] = client.transport
    summary["cookies"] = cookies
    summary["wall_seconds"] = round(time.time() - started, 1)
    summary["cookies_held_at_end"] = client.cookies_held()
    summary["client_calls_total"] = client.calls

    commands = summary["actions_ok"] + summary["actions_failed"]
    summary["executed_commands"] = commands
    summary["http_per_command"] = (round(summary["http_calls_gameplay"] / commands, 2)
                                   if commands else None)
    summary["cost_per_successful_action"] = (
        round(summary["cost_usd"] / summary["actions_ok"], 4)
        if summary["actions_ok"] else None)

    print("--- %s -> %s | %d ok / %d failed | http %d (%.2f/command) | $%.4f | %.0fs"
          % (label, summary["outcome"], summary["actions_ok"],
             summary["actions_failed"], summary["http_calls_gameplay"],
             summary["http_per_command"] or 0.0, summary["cost_usd"],
             summary["wall_seconds"]), flush=True)
    return summary


def decompose(probe_path: Optional[str] = None) -> Dict[str, Any]:
    """Separate routing failures from deterministic ones, per arm.

    `http_per_command` is the honest headline but it flatters nothing and
    explains nothing: it lumps together two failures with opposite characters.
    A `400 game <id> not found` is the routing miss this whole exercise is
    about -- it succeeds on the next attempt from a different replica. A `500`
    is the server refusing the request itself, and no number of retries will
    change its mind.

    That distinction matters most *after* the fix, because removing the
    dominant failure promotes the next one: on the fixed transport nearly all
    the remaining HTTP traffic is `resilient` spending eight attempts on 500s
    that were deterministic the first time. Reporting only the headline would
    credit the transport with a residue that has nothing to do with it, in
    both directions.
    """
    probe_path = probe_path or ledger.PROBE_PATH
    if not os.path.exists(probe_path):
        return {"available": False, "reason": "%s not found" % probe_path}
    calls = []
    with open(probe_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("kind") == "arc_api_call" and "/api/cmd/" in entry.get("url", ""):
                calls.append(entry)

    out: Dict[str, Any] = {"available": True, "gameplay_calls_only": True}
    for cookies in (False, True):
        arm = [c for c in calls if bool(c.get("cookies_enabled")) is cookies]
        ok = [c for c in arm if c["status"] == 200]
        routing = [c for c in arm
                   if c["status"] == 400
                   and "not found" in str((c.get("response_summary") or {})
                                          .get("message", ""))]
        server = [c for c in arm if c["status"] == 500]
        out["cookies_%s" % cookies] = {
            "gameplay_calls": len(arm),
            "succeeded": len(ok),
            "routing_400_not_found": len(routing),
            "server_500": len(server),
            "routing_retries_per_success": (round(len(routing) / len(ok), 2)
                                            if ok else None),
            "server_500_per_success": (round(len(server) / len(ok), 2)
                                       if ok else None),
        }
    a = out["cookies_False"]["routing_retries_per_success"]
    b = out["cookies_True"]["routing_retries_per_success"]
    out["verdict"] = (
        "Routing retries per successful gameplay call: %s -> %s. That is the "
        "transport effect, isolated. The headline http_per_command ratio is "
        "SMALLER than this because the fixed arm's remaining traffic is almost "
        "entirely 500s being retried eight times each -- a different defect, "
        "described below." % (a, b))
    out["the_next_bottleneck"] = (
        "`bare_cc.resilient` retries EVERY non-200 up to eight times, including "
        "500s. On the old transport that was invisible: routing misses "
        "dominated. On the fixed transport 500s are most of what is left, and "
        "each one costs eight attempts to learn what the first attempt already "
        "said. arc-recon's precheck deliberately retries only "
        "`400 ... not found` / 429 / transport errors, on the grounds that "
        "burning a retry budget on a deterministic error is just a slower way "
        "of failing. Recommended next change for this track -- NOT made here, "
        "because it would alter the very retry accounting this A/B just "
        "measured, and it deserves its own before/after.")
    return out


def compare(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    old = next(c for c in cells if not c["cookies"])
    new = next(c for c in cells if c["cookies"])

    def ratio(a: Optional[float], b: Optional[float]) -> Optional[float]:
        return round(a / b, 2) if (a and b) else None

    return {
        "primary_metric": "http_calls_gameplay / executed_commands",
        "why": ("the only figure the two cells can be compared on without "
                "reservation: it is a property of the transport, and the "
                "trajectory length cancels out of the ratio"),
        "http_per_command": {"cookies_false": old["http_per_command"],
                             "cookies_true": new["http_per_command"],
                             "improvement_x": ratio(old["http_per_command"],
                                                    new["http_per_command"])},
        "indicative_only": {
            "note": ("a bare-CC cell is model-driven, so the two runs take "
                     "different trajectories; these differ for reasons beyond "
                     "the transport"),
            "outcome": {"cookies_false": old["outcome"],
                        "cookies_true": new["outcome"]},
            "actions_ok": {"cookies_false": old["actions_ok"],
                           "cookies_true": new["actions_ok"]},
            "actions_failed": {"cookies_false": old["actions_failed"],
                               "cookies_true": new["actions_failed"]},
            "cost_usd": {"cookies_false": old["cost_usd"],
                         "cookies_true": new["cost_usd"]},
            "cost_per_successful_action": {
                "cookies_false": old["cost_per_successful_action"],
                "cookies_true": new["cost_per_successful_action"]},
            "wall_seconds": {"cookies_false": old["wall_seconds"],
                             "cookies_true": new["wall_seconds"]},
            "reset_attempts": {"cookies_false": old["reset_attempts"],
                               "cookies_true": new["reset_attempts"]},
        },
        "read_the_dollars_carefully": (
            "A cell aborts at actions_failed >= 10. On the old transport an "
            "action fails when all eight retries miss, so cells died early with "
            "their money spent on retries instead of gameplay. A fixed "
            "transport lets the cell survive to spend its whole budget, so "
            "$/cell can RISE while $/successful-action falls. $/cell is not the "
            "figure that improves; $ per unit of actual gameplay is."),
        "failure_decomposition": None,   # filled in by main()
        "confounds": [
            "One cell per arm. This is a demonstration in this track's units, "
            "not an estimate with an error bar.",
            "Run back to back, not interleaved -- a whole cell cannot be "
            "interleaved. API conditions vary over minutes, and arc-recon "
            "measured 9.19 vs 11.88 http/action on two cookie-less canary "
            "sweeps 35 minutes apart, so treat single-cell differences under "
            "about 30% as noise.",
            "Other processes were sharing the API and the account while this "
            "ran (INC-BA-003's standing hazard).",
        ],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="transport_ab",
                                 description=__doc__.splitlines()[0])
    ap.add_argument("--game", default="ar25-0c556536")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    ap.add_argument("--reanalyse", action="store_true",
                    help="recompute the decomposition from the existing probe "
                         "shard and rewrite the report; spends nothing")
    args = ap.parse_args(argv)

    if args.reanalyse:
        with open(OUT_PATH, encoding="utf-8") as fh:
            report = json.load(fh)
        report["comparison"]["failure_decomposition"] = decompose()
        with open(OUT_PATH, "w", encoding="utf-8", newline="") as fh:
            json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        print(json.dumps(report["comparison"]["failure_decomposition"],
                         indent=2, ensure_ascii=False))
        return 0

    assert_not_frozen()
    arc_client.ArcClient(api_key="unused-for-the-guard-check", cookies=False) \
        .assert_playable(args.game)

    if not os.environ.get(ledger.SHARD_ENV):
        print("  WARNING: %s is not set, so this writes to the track's main "
              "ledger while other processes may be appending to it."
              % ledger.SHARD_ENV, flush=True)

    print("  ledger -> %s" % os.path.relpath(ledger.LEDGER_PATH, TRACK), flush=True)
    cells = []
    # Old transport first: it is the one expected to abort early, so if anything
    # goes wrong the cheaper cell is the one already spent.
    for cookies in (False, True):
        cells.append(run_cell(args.game, args.model, args.budget, cookies))

    report = {
        "t": ledger.utcnow(),
        "game_id": args.game, "model": args.model, "budget": args.budget,
        "order": ["cookies=False", "cookies=True"],
        "cells": cells,
        "comparison": {**compare(cells),
                       "failure_decomposition": decompose()},
        "provenance": ("arc-recon INC-007 / INC-007a; ported to this track's "
                       "client 2026-07-28, INC-010"),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("  report -> %s" % os.path.relpath(OUT_PATH, TRACK), flush=True)
    print("  http/command  %s -> %s"
          % (report["comparison"]["http_per_command"]["cookies_false"],
             report["comparison"]["http_per_command"]["cookies_true"]), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
