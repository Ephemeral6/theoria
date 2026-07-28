"""Reconcile the shared spend pool against this campaign's cells.

`audit_cells.py` asks whether a cell agrees with the harness ledger and with the
API scorecard. Wiring this track to `proxy/spend_gate.py` (D-017) created a
third book that nobody was checking: the pool has one line per outbound request
and one per model call, written under a cross-process lock, and it is the only
record any *other* session can see. A cell that disagrees with the pool is worse
than a cell that disagrees with its own ledger, because the pool is what the
next session will make its go/no-go decision from.

Three questions:

  1. **Does every pool line belong to a cell?** A `spend` record whose
     reservation is not claimed by any cell is money this campaign cannot
     account for -- which is INC-BA-003's unattributable spend, in the file
     built to prevent it.
  2. **Does the action count close?** Exactly, not approximately. An episode
     makes `reset_attempts` RESET requests, one scorecard open, its gameplay
     requests, and between 1 and 8 close attempts:

         pool_actions = reset_attempts + 1 + http_calls_gameplay + close_tries

     so `close_tries` is determined by the other four, and it has to land in
     [1, 8]. That is a real constraint and not a restatement: any miscount in
     any term pushes it out of range.
  3. **Do the dollars agree?** The cell sums `total_cost_usd` from the CLI
     envelopes; the pool sums one settlement per call. They are two independent
     additions of the same figures and must match to the cent -- unless a call
     went unpriced, which is reported rather than absorbed.

    python -m harness.audit_pool --campaign phase3-variance-envelope
    python -m harness.audit_pool --game g50t-5849a774
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from . import run_campaign, spend

#: Bounds from `arc_client.close_scorecard(tries=8)` and the fact that a cell
#: that owns its card always opens exactly one.
CLOSE_TRIES_MIN, CLOSE_TRIES_MAX = 1, 8
CENT = 0.01


def pool_records(gate: Optional[spend.SpendGate] = None) -> List[Dict[str, Any]]:
    gate = gate or spend.SpendGate()
    path = gate.ledger_path
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def by_reservation(records: List[Dict[str, Any]],
                   campaign: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    acc: Dict[str, Dict[str, Any]] = {}
    for record in records:
        if campaign is not None and record.get("campaign") != campaign:
            continue
        rid = record.get("reservation_id")
        if rid is None:
            continue
        entry = acc.setdefault(rid, {
            "reservation_id": rid, "campaign": record.get("campaign"),
            "usd": 0.0, "actions": 0, "unpriced": 0, "model_calls": 0,
            "released": False, "holder": {}, "spend_lines": 0, "trips": []})
        kind = record.get("kind")
        if kind == "reserve":
            entry["holder"] = record.get("holder") or {}
            entry["usd_cap"] = record.get("usd_cap")
            entry["action_cap"] = record.get("action_cap")
        elif kind == "release":
            entry["released"] = True
        elif kind == "spend":
            entry["usd"] = round(entry["usd"] + float(record.get("usd") or 0.0), 6)
            entry["actions"] += int(record.get("actions") or 0)
            entry["spend_lines"] += 1
            if record.get("unpriced"):
                entry["unpriced"] += 1
            if (record.get("detail") or {}).get("step_idx") is not None \
                    or "model" in (record.get("detail") or {}):
                entry["model_calls"] += 1
        elif kind == "trip":
            entry["trips"].append(record.get("rule"))
    return acc


def audit(cells: List[Dict[str, Any]], campaign: str,
          gate: Optional[spend.SpendGate] = None) -> Dict[str, Any]:
    records = pool_records(gate)
    pool = by_reservation(records, campaign)

    findings: List[str] = []
    rows: List[Dict[str, Any]] = []
    claimed = set()

    for cell in cells:
        rid = (cell.get("spend") or {}).get("reservation_id")
        row: Dict[str, Any] = {
            "run_id": cell.get("run_id"), "game_id": cell.get("game_id"),
            "repeat": cell.get("repeat"), "outcome": cell.get("outcome"),
            "reservation_id": rid, "problems": []}

        if rid is None:
            # Every cell recorded before D-017 is in this position. It is a
            # permanent gap in the record, not a fault, and it is reported as
            # its own category: counting it as a problem would make every future
            # audit read NOT CLEAN for a reason nobody can ever fix, and an
            # alarm that can never be cleared is one people learn to ignore.
            row["unreconcilable"] = (
                "predates the spend gate wiring (D-017); there is no pool line "
                "to reconcile against and there never will be")
            rows.append(row)
            continue

        claimed.add(rid)
        entry = pool.get(rid)
        if entry is None:
            row["problems"].append(
                "reservation %s is named by the cell but absent from the pool "
                "ledger -- the cell claims a spend nobody can see" % rid)
            rows.append(row)
            continue

        row["pool_actions"] = entry["actions"]
        row["pool_usd"] = entry["usd"]
        row["released"] = entry["released"]

        # -- the action identity ------------------------------------------
        gameplay = cell.get("http_calls_gameplay") or 0
        resets = cell.get("reset_attempts") or 0
        implied_close = entry["actions"] - resets - 1 - gameplay
        row["implied_close_tries"] = implied_close
        if cell.get("outcome") == "no_reset_window":
            # No card was ever reset into play; the identity's gameplay term is
            # zero by construction and close may not have been reached at all.
            pass
        elif not (CLOSE_TRIES_MIN <= implied_close <= CLOSE_TRIES_MAX):
            row["problems"].append(
                "action identity does not close: pool %d - resets %d - open 1 "
                "- gameplay %d = %d close attempts, outside [%d, %d]"
                % (entry["actions"], resets, gameplay, implied_close,
                   CLOSE_TRIES_MIN, CLOSE_TRIES_MAX))

        # -- the dollars ---------------------------------------------------
        cell_usd = float(cell.get("cost_usd") or 0.0)
        if entry["unpriced"]:
            row["problems"].append(
                "%d model call(s) could not be priced; the pool's dollar figure "
                "for this cell is a ceiling, not a settlement" % entry["unpriced"])
        elif abs(entry["usd"] - cell_usd) > CENT:
            row["problems"].append(
                "dollars disagree: pool $%.4f vs cell $%.4f (difference $%.4f). "
                "These are two independent sums of the same CLI figures."
                % (entry["usd"], cell_usd, entry["usd"] - cell_usd))

        # -- the lease -----------------------------------------------------
        if not entry["released"]:
            row["problems"].append(
                "reservation was never released; its unspent remainder is still "
                "held against the pool and other sessions cannot reserve it")

        if entry["trips"]:
            row["trips"] = entry["trips"]

        rows.append(row)

    # -- pool lines with no cell ------------------------------------------
    #
    # Only a *cell-bearing* campaign can have orphans. A campaign with no cell
    # records at all -- a smoke test, a quota probe -- is not unattributable
    # spend: it is spend attributed to a named campaign, with a holder record
    # saying what it was for, which is precisely what running it under its own
    # name buys. Reporting those as orphans would train a reader to dismiss the
    # one finding here that actually means INC-BA-003.
    audits_cells = any(r.get("reservation_id") for r in rows)
    orphans = []
    unclaimed_informational = []
    for rid, entry in sorted(pool.items()):
        if rid in claimed or entry["spend_lines"] == 0:
            continue
        item = {"reservation_id": rid, "usd": entry["usd"],
                "actions": entry["actions"], "holder": entry["holder"]}
        (orphans if audits_cells else unclaimed_informational).append(item)
    if orphans:
        findings.append(
            "%d reservation(s) spent against campaign %r but are claimed by no "
            "cell of it. Unattributable spend is the thing spend_gate.py exists "
            "to prevent -- a smoke test or probe belongs under its own campaign "
            "name, not inside this one." % (len(orphans), campaign))
    if not audits_cells and unclaimed_informational:
        findings.append(
            "campaign %r has no cell records; its %d reservation(s) are "
            "attributed by holder only. That is what a probe or smoke campaign "
            "looks like and is not a discrepancy."
            % (campaign, len(unclaimed_informational)))

    problems = sum(len(r["problems"]) for r in rows)
    return {"campaign": campaign, "cells": rows, "orphans": orphans,
            "unclaimed_informational": unclaimed_informational,
            "findings": findings, "problem_count": problems,
            "unreconcilable_count": sum(1 for r in rows if r.get("unreconcilable")),
            "clean": problems == 0 and not orphans}


def print_report(report: Dict[str, Any]) -> None:
    print("=== spend pool reconciliation: campaign %r ===\n" % report["campaign"])
    for row in report["cells"]:
        mark = "--" if row.get("unreconcilable") else ("OK" if not row["problems"]
                                                       else "!!")
        print("  [%s] %s rep %s (%s)"
              % (mark, row["game_id"], row["repeat"], row["outcome"]))
        if row.get("unreconcilable"):
            print("        %s" % row["unreconcilable"])
        elif row.get("reservation_id"):
            print("        pool: %s actions, $%s, close-tries %s, released=%s"
                  % (row.get("pool_actions"), row.get("pool_usd"),
                     row.get("implied_close_tries"), row.get("released")))
        for problem in row["problems"]:
            print("        - %s" % problem)
    for orphan in report["orphans"]:
        print("\n  ORPHAN %s  $%.4f  %d actions  holder=%s"
              % (orphan["reservation_id"], orphan["usd"], orphan["actions"],
                 json.dumps(orphan["holder"], sort_keys=True)))
    for item in report["unclaimed_informational"]:
        print("  (no cells) %s  $%.4f  %d actions  holder=%s"
              % (item["reservation_id"], item["usd"], item["actions"],
                 json.dumps(item["holder"], sort_keys=True)))
    for finding in report["findings"]:
        print("\n  FINDING: %s" % finding)
    print("\n=== %s: %d cell(s), %d reconciled, %d unreconcilable, "
          "%d problem(s) ==="
          % ("CLEAN" if report["clean"] else "NOT CLEAN", len(report["cells"]),
             len(report["cells"]) - report["unreconcilable_count"],
             report["unreconcilable_count"], report["problem_count"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", default=run_campaign.CAMPAIGN_NAME)
    ap.add_argument("--game", default=None, help="restrict to one game id prefix")
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)

    cells = run_campaign.load_cells()
    if args.game:
        prefix = args.game.split("-")[0]
        cells = [c for c in cells if (c.get("game_id") or "").startswith(prefix)]

    report = audit(cells, args.campaign)
    print_report(report)
    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
