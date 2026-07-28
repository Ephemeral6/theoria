"""BUDGET_REPORT section 2.1, re-derived per transport.

D-019: the cookie jar landed between the M4 pilot and the variance envelope, so
section 2.1's unit prices describe a transport that no longer exists. Its
`HTTP/action 7.11` is the headline casualty, and every extrapolation in section
3 is built on it.

Re-measuring does not mean re-buying. Three of the six numbers this table needs
are already paid for: the A7 envelope ran nine jar-on cells on the cheap tier,
same budget, same games. So this module derives what the record already
contains and leaves only the genuinely unmeasured cells to be run.

**The comparison is restricted to games both transports covered**, and that is
not a detail. The pilot ran four games; the jar-on cells so far run three. Left
unrestricted, "http/action fell from 7.11 to 1.97" would be partly a statement
about which games were in each average -- and between-game spread on that metric
is 3x, larger than the effect being claimed. `--common-games` is on by default
for exactly that reason.

    python -m harness.unit_prices                 # the table, both transports
    python -m harness.unit_prices --all-games     # unrestricted, for contrast

**Not every column in this table is caused by the transport, and reading it as
if they were would be wrong in a way that matters.** The rows are labelled by
transport because that is what cleanly separates the two populations in time,
not because the jar explains every difference between them:

  * `http_per_action`, `action_success_rate` -- **caused by the transport**, with
    a mechanism: cookies pin the ALB replica that holds the session, so the
    `400 game not found` storm stops. arc-recon measured 20/20 against 0/20.
  * `usd_per_model_call` -- **cannot be caused by the transport.** The jar routes
    HTTP to `three.arcprize.org`; model calls go to Anthropic and never touch
    it. Yet this rose ~55% on both measured tiers. Whatever did that is a
    coincident change, not this one, and the table must not be read as claiming
    otherwise.
  * `usd_per_action`, `wall_s_per_action` -- mixtures of the two, so no clean
    attribution is available for them either.

Two candidate mechanisms for the `$/call` rise were tested against the record
and both failed. Episode length: within-episode drift is +5% from step 1 to 30
across 269 jar-on calls, so the 20-vs-30 budget difference cannot produce 55%.
Prompt-cache busting from a game that actually progresses: cache-creation per
call is uncorrelated with success rate, r = 0.11 across nine jar-on cells and
r = -0.06 across twelve jar-off cells spanning the full 0.000-1.000 range.
The cause is **unestablished**, and is recorded that way rather than filled in
with the most plausible-sounding story.
"""

import argparse
import glob
import json
import os
import sys
from typing import Any, Dict, List, Optional

from . import run_campaign

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(TRACK, "out")

#: Outcomes whose cell is a usable price sample. A cell that died before doing
#: any work prices nothing; one that was refused by the budget gate prices even
#: less. Kept explicit rather than "outcome != error" so adding an outcome forces
#: a decision about whether it belongs in a denominator.
PRICEABLE = ("budget_exhausted", "failure_grind", "gave_up", "unparseable_reply",
             "win", "game_over", "api_unusable", "spend_ceiling_hit")


def pilot_cells() -> List[Dict[str, Any]]:
    """The M4 pilot's episodes. Every one predates the cookie jar."""
    out: List[Dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(OUT, "pilot_*.json"))):
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        for cell in (payload if isinstance(payload, list) else [payload]):
            out.append(dict(cell, _source=os.path.basename(path)))
    return out


def transport_of(cell: Dict[str, Any]) -> str:
    """`jar-on` or `jar-off`, by provenance rather than by inference.

    Deliberately not inferred from `http_amplification`: that is the quantity
    under measurement, and classifying cells by it would make the finding
    circular. Provenance is exact -- the pilot files and the ar25 campaign cells
    were all written before `e2915e1`, and every cell carrying a `spend` record
    was written after it, since the spend gate and the jar-on runs arrived
    together. `verify_transport()` checks the classification against the probe
    logs, which record `cookies_enabled` per call.
    """
    if cell.get("_source", "").startswith("pilot_"):
        return "jar-off"
    return "jar-on" if cell.get("spend") else "jar-off"


def verify_transport() -> Dict[str, Any]:
    """Corroborate the provenance split against what the probe logs recorded.

    The probe log carries `cookies_enabled` on every `arc_api_call`. If the
    split above is right, the pre-jar logs are 100% disabled and the A7 shards
    100% enabled. This does not prove the per-cell mapping, and says so: it
    proves the two populations are cleanly separated, which is the assumption
    the mapping rests on.
    """
    populations: Dict[str, Dict[str, int]] = {}
    paths = [os.path.join(TRACK, "probe_log.jsonl")]
    paths += sorted(glob.glob(os.path.join(OUT, "shards", "probe_log.*.jsonl")))
    for path in paths:
        if not os.path.exists(path):
            continue
        name = os.path.basename(path)
        bucket = populations.setdefault(name, {"calls": 0, "jar_on": 0})
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            detail = record.get("detail") or record
            if detail.get("method") and "status" in detail:
                bucket["calls"] += 1
                if detail.get("cookies_enabled"):
                    bucket["jar_on"] += 1
    mixed = [n for n, b in populations.items()
             if b["calls"] and 0 < b["jar_on"] < b["calls"]]
    return {"populations": populations, "mixed_files": mixed,
            "clean_split": not mixed}


def aggregate(cells: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """One section-2.1 row. Totals over cells, not a mean of per-cell ratios.

    Ratio-of-sums, deliberately. A mean of per-cell ratios weights a cell that
    completed three actions the same as one that completed thirty, and the
    pilot's dead cells are exactly the light ones -- section 2.1 is a unit price
    for extrapolating a large run, so the heavy cells must dominate it.
    """
    usable = [c for c in cells if c.get("outcome") in PRICEABLE]
    if not usable:
        return None

    # A cell that bought no successful action still spent money, and the ratio
    # of sums charges that money to the actions other cells did get. That is the
    # right default -- it is what "a successful action costs $X" has to mean if
    # the figure is going to extrapolate a run that will also have dead cells,
    # and it is what the M4 pilot did (section 7 counted its two api_unusable
    # cells in the denominator). But one such cell can move the number a lot:
    # opus/tn36 spent $1.13 for zero actions, which is +17% on the tier's price
    # from a single cell. Reported both ways, so the reader can see how much of
    # the unit price is the arm working and how much is it failing.
    barren = [c for c in usable if not (c.get("actions_ok") or 0)]
    productive = [c for c in usable if (c.get("actions_ok") or 0)]
    barren_cost = round(sum(float(c.get("cost_usd") or 0.0) for c in barren), 4)
    prod_ok = sum(c.get("actions_ok") or 0 for c in productive)
    prod_cost = sum(float(c.get("cost_usd") or 0.0) for c in productive)

    ok = sum(c.get("actions_ok") or 0 for c in usable)
    failed = sum(c.get("actions_failed") or 0 for c in usable)
    calls = sum(c.get("model_calls") or 0 for c in usable)
    http = sum(c.get("http_calls_gameplay") or 0 for c in usable)
    cost = sum(float(c.get("cost_usd") or 0.0) for c in usable)
    wall = sum(float(c.get("wall_seconds") or 0.0) for c in usable)
    return {
        "cells": len(usable),
        "cells_seen": len(cells),
        "games": sorted({c.get("game_id") for c in usable}),
        "actions_ok": ok, "actions_failed": failed,
        "model_calls": calls, "http_calls": http,
        "cost_usd": round(cost, 4),
        "usd_per_action": round(cost / ok, 4) if ok else None,
        # The same price with the barren cells' money removed from the
        # numerator. Never the headline: it is what the arm costs *when it
        # works*, which is not what a run costs.
        "usd_per_action_working_cells_only": (round(prod_cost / prod_ok, 4)
                                              if prod_ok else None),
        "barren_cells": len(barren),
        "barren_cost_usd": barren_cost,
        "usd_per_model_call": round(cost / calls, 4) if calls else None,
        "http_per_action": round(http / ok, 2) if ok else None,
        "wall_s_per_action": round(wall / ok, 1) if ok else None,
        "action_success_rate": round(ok / (ok + failed), 3) if (ok + failed) else None,
    }


def build(common_games: bool = True) -> Dict[str, Any]:
    cells = pilot_cells() + run_campaign.load_cells()
    for cell in cells:
        cell["_transport"] = transport_of(cell)

    games = {t: {c.get("game_id") for c in cells
                 if c["_transport"] == t and c.get("outcome") in PRICEABLE}
             for t in ("jar-off", "jar-on")}
    shared = sorted(games["jar-off"] & games["jar-on"])

    scoped = cells
    if common_games:
        scoped = [c for c in cells if c.get("game_id") in shared]

    rows: Dict[str, Dict[str, Any]] = {}
    for transport in ("jar-off", "jar-on"):
        for model in sorted({c.get("model") for c in scoped}):
            group = [c for c in scoped
                     if c["_transport"] == transport and c.get("model") == model]
            row = aggregate(group)
            if row is not None:
                rows["%s|%s" % (model, transport)] = row

    return {
        "rows": rows,
        "common_games": shared,
        "scoped_to_common_games": common_games,
        "games_by_transport": {t: sorted(g) for t, g in games.items()},
        "transport_check": verify_transport(),
        "generated": run_campaign.ledger.utcnow(),
    }


def print_report(report: Dict[str, Any]) -> None:
    check = report["transport_check"]
    print("=== BUDGET_REPORT section 2.1, re-derived per transport ===\n")
    print("  scope: %s"
          % ("games measured on BOTH transports -- %s"
             % ", ".join(report["common_games"]) if report["scoped_to_common_games"]
             else "ALL games, transports not comparable game-for-game"))
    for transport, games in sorted(report["games_by_transport"].items()):
        print("    %-8s %s" % (transport, ", ".join(games) or "(none)"))
    print("  transport split corroborated by probe logs: %s"
          % ("clean" if check["clean_split"]
             else "MIXED in %s -- the split is not trustworthy"
                  % ", ".join(check["mixed_files"])))
    print()

    header = ("%-30s %-8s %6s %10s %10s %11s %8s %9s %8s"
              % ("model", "transport", "cells", "$/action", "$/act-wk", "$/call",
                 "http/act", "wall s/a", "success"))
    print(header)
    print("  " + "-" * (len(header) - 2))
    for key in sorted(report["rows"]):
        model, transport = key.split("|")
        row = report["rows"][key]
        print("%-30s %-8s %6d %10s %10s %11s %8s %9s %8s"
              % (model, transport, row["cells"],
                 _f(row["usd_per_action"], 4),
                 _f(row["usd_per_action_working_cells_only"], 4),
                 _f(row["usd_per_model_call"], 4),
                 _f(row["http_per_action"], 2), _f(row["wall_s_per_action"], 1),
                 _f(row["action_success_rate"], 3)))
        if row["barren_cells"]:
            print("%-30s %-8s   %d cell(s) bought no action at all, $%.4f of the "
                  "numerator" % ("", "", row["barren_cells"], row["barren_cost_usd"]))

    print("\n  deltas where both transports have a row:")
    any_pair = False
    for key in sorted(report["rows"]):
        model, transport = key.split("|")
        if transport != "jar-on":
            continue
        old = report["rows"].get("%s|jar-off" % model)
        new = report["rows"][key]
        if not old:
            continue
        any_pair = True
        print("    %s" % model)
        for field, places in (("usd_per_action", 4), ("usd_per_model_call", 4),
                              ("http_per_action", 2), ("wall_s_per_action", 1),
                              ("action_success_rate", 3)):
            a, b = old.get(field), new.get(field)
            if a in (None, 0) or b is None:
                continue
            print("      %-22s %10s -> %-10s  %+.0f%%"
                  % (field, _f(a, places), _f(b, places), 100.0 * (b - a) / a))
    if not any_pair:
        print("    (none -- no model has been measured on both transports)")

    missing = [m for m in sorted({k.split("|")[0] for k in report["rows"]})
               if "%s|jar-on" % m not in report["rows"]]
    if missing:
        print("\n  NOT YET MEASURED ON THE JAR: %s" % ", ".join(missing))
        print("  Their section 2.1 rows still describe a transport that no "
              "longer exists.")


def _f(value, places):
    return "-" if value is None else ("%%.%df" % places) % value


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-games", action="store_true",
                    help="do not restrict to games both transports covered")
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)

    report = build(common_games=not args.all_games)
    print_report(report)
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
        print("\nwrote %s" % args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
