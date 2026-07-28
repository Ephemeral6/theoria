"""Per-game ledger audit: does the account close, and did anything sealed get touched?

Run after each game of the variance campaign, before the next game starts. Three
questions, in increasing order of how bad the answer can be:

  1. **Do the counts agree?** The cell summary claims N successful actions and M
     model calls. The ledger should contain exactly that many records, with
     contiguous step indices, and a null frame on exactly the failed steps.
     A summary that disagrees with its own ledger is not evidence of anything.

  2. **Does the score reconcile?** `Theoria.md` Phase 1 makes this an obligation,
     not a nicety: "账本推得的分数必须等于 API scorecard 分数，不等 = incident".
     The authoritative number comes from the scorecard close response, or -- for
     episodes that started before close learned to retry (D-015) -- from an
     open-card snapshot, which is a step-N score and is labelled as such.

  3. **Is there any sealed game id anywhere?** This one is not a bookkeeping
     question. It should be impossible, and if it is ever answered "yes" the
     campaign stops and it is an incident, not a discrepancy to reconcile.

    python -m harness.audit_cells --game ar25-0c556536
    python -m harness.audit_cells                       # every recorded cell
"""

import argparse
import glob
import json
import os
import sys
from typing import Any, Dict, List, Optional

from . import arc_client, ledger, run_campaign

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARD_GLOB = os.path.join(TRACK, "out", "shards", "*.jsonl")


def ledger_paths() -> List[str]:
    """Both the plain ledger and any shards.

    The campaign's first game wrote to the plain path; later games write shards,
    because a concurrent campaign in the same directory introduced sharding
    mid-run (INC-BA-002). An audit that read only one of the two would report a
    perfectly self-consistent account of half the data.
    """
    paths = [os.path.join(TRACK, "ledger.jsonl")]
    paths += sorted(p for p in glob.glob(SHARD_GLOB) if os.path.basename(p).startswith("ledger."))
    return [p for p in paths if os.path.exists(p)]


def probe_paths() -> List[str]:
    paths = [os.path.join(TRACK, "probe_log.jsonl")]
    paths += sorted(p for p in glob.glob(SHARD_GLOB) if os.path.basename(p).startswith("probe_log."))
    return [p for p in paths if os.path.exists(p)]


def read_jsonl(paths: List[str]):
    for path in paths:
        for line_no, line in enumerate(open(path, encoding="utf-8"), 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line), path, line_no
            except json.JSONDecodeError as exc:
                yield {"_corrupt": str(exc)}, path, line_no


def scorecard_for(run_id: str, probes) -> Optional[Dict[str, Any]]:
    """Authoritative scores: a successful close, else the best open-card snapshot."""
    close, snapshot = None, None
    for entry in probes:
        if entry.get("kind") == "scorecard_snapshot_open_card" and entry.get("run_id") == run_id:
            if snapshot is None or (entry.get("total_actions") or 0) >= (snapshot.get("total_actions") or 0):
                snapshot = dict(entry, _source="open_card_snapshot")
        if entry.get("note") == "close scorecard" and entry.get("status") == 200:
            body = entry.get("response_summary")
            if isinstance(body, dict) and isinstance(body.get("opaque"), dict) \
                    and body["opaque"].get("run_id") == run_id:
                close = dict(body, _source="close_response")
    return close or snapshot


def audit_run(cell: Dict[str, Any], records, probes) -> Dict[str, Any]:
    run_id = cell.get("run_id")
    steps = [r for r in records if r.get("run_id") == run_id and "frame" in r]
    calls = [r for r in records if r.get("run_id") == run_id and "usage" in r]

    findings: List[str] = []
    resets = [s for s in steps if s.get("action") == "RESET"]
    actions = [s for s in steps if s.get("action") != "RESET"]
    ok = [s for s in actions if not s.get("failed")]
    failed = [s for s in actions if s.get("failed")]

    # 1. counts
    if len(ok) != (cell.get("actions_ok") or 0):
        findings.append("actions_ok: summary %s, ledger %s"
                        % (cell.get("actions_ok"), len(ok)))
    if len(failed) != (cell.get("actions_failed") or 0):
        findings.append("actions_failed: summary %s, ledger %s"
                        % (cell.get("actions_failed"), len(failed)))
    if len(calls) != (cell.get("model_calls") or 0):
        findings.append("model_calls: summary %s, ledger %s"
                        % (cell.get("model_calls"), len(calls)))
    ledger_cost = sum(float(c.get("total_cost_usd") or 0.0) for c in calls)
    if abs(ledger_cost - float(cell.get("cost_usd") or 0.0)) > 0.005:
        findings.append("cost: summary $%.4f, ledger $%.4f"
                        % (cell.get("cost_usd") or 0.0, ledger_cost))

    # frame is null exactly on failed steps (D-006)
    for s in actions:
        if bool(s.get("failed")) != (s.get("frame") is None):
            findings.append("step %s: failed=%s but frame is %s"
                            % (s.get("step_idx"), s.get("failed"),
                               "null" if s.get("frame") is None else "present"))
            break

    # step indices contiguous from 1
    idxs = sorted(s.get("step_idx") for s in actions if s.get("step_idx") is not None)
    if idxs and idxs != list(range(1, len(idxs) + 1)):
        findings.append("step_idx not contiguous: %s..%s with %d steps"
                        % (idxs[0], idxs[-1], len(idxs)))
    if len(resets) != 1:
        findings.append("expected exactly 1 RESET, found %d" % len(resets))

    # 2. score reconciliation
    card = scorecard_for(run_id, probes)
    recon: Dict[str, Any] = {"available": card is not None}
    if card:
        recon["source"] = card.get("_source")
        recon["card_total_actions"] = card.get("total_actions")
        recon["card_score"] = card.get("score")
        recon["card_levels_completed"] = card.get("total_levels_completed")
        ca = card.get("total_actions")
        if ca is not None:
            if ca == len(ok):
                recon["verdict"] = "matches successful actions only"
            elif ca == len(ok) + len(failed):
                recon["verdict"] = "matches successful + failed"
            elif card.get("_source") == "open_card_snapshot" and ca <= len(ok):
                recon["verdict"] = ("snapshot taken mid-episode (%d of %d actions); "
                                    "consistent, not final" % (ca, len(ok)))
            else:
                recon["verdict"] = "MISMATCH: card %s vs ledger ok=%d failed=%d" % (ca, len(ok), len(failed))
                findings.append(recon["verdict"])
        if card.get("total_levels_completed") is not None \
                and card["total_levels_completed"] != (cell.get("levels_completed") or 0) \
                and card.get("_source") == "close_response":
            findings.append("levels_completed: summary %s, scorecard %s"
                            % (cell.get("levels_completed"), card["total_levels_completed"]))
    else:
        findings.append("no scorecard captured -- score cannot be reconciled (D-015)")

    return {"run_id": run_id, "game_id": cell.get("game_id"), "repeat": cell.get("repeat"),
            "outcome": cell.get("outcome"), "ledger_steps": len(steps),
            "ledger_actions_ok": len(ok), "ledger_actions_failed": len(failed),
            "ledger_model_calls": len(calls), "ledger_cost_usd": round(ledger_cost, 4),
            "reconciliation": recon, "findings": findings}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    cells = run_campaign.load_cells()
    if args.game:
        stem = args.game.split("-")[0]
        cells = [c for c in cells if c["game_id"].startswith(stem)]
    if not cells:
        print("no campaign cells to audit%s" % (" for %s" % args.game if args.game else ""))
        return 1

    records = [r for r, _p, _n in read_jsonl(ledger_paths())]
    probes = [r for r, _p, _n in read_jsonl(probe_paths())]

    corrupt = [(p, n) for r, p, n in read_jsonl(ledger_paths()) if r.get("_corrupt")]
    sealed = arc_client.sealed_pile()
    dev = set(arc_client.dev_pile())

    # 3. the one that is not a bookkeeping question
    sealed_hits = []
    for r in records:
        gid = r.get("game_id")
        if gid and gid not in dev:
            sealed_hits.append(gid)
    # The run_id check is anchored, not a substring scan. A run_id is
    # `bare_cc-<game stem>-<model>-<8 hex>`, and a bare substring test against
    # the 4-character sealed prefixes matches that hex tail by accident: two of
    # the sealed prefixes are all-hex, five offsets in eight characters, so the
    # false-positive rate is roughly 1.5% per hundred run ids. That false alarm
    # prints as "sealed ids present" and is indistinguishable from the incident
    # this check exists to catch -- an alarm that cries wolf at 1.5% is worse
    # than no alarm, because the real one gets read as another collision.
    # Anchoring loses nothing: the stem always sits in the second field, and
    # the game_id scan above is the authoritative check anyway.
    sealed_stems = {s.split("-")[0].lower() for s in sealed}
    for r in records:
        rid = str(r.get("run_id") or "")
        fields = rid.lower().split("-")
        if len(fields) >= 2 and fields[1] in sealed_stems:
            sealed_hits.append(rid)

    reports = [audit_run(c, records, probes) for c in
               sorted(cells, key=lambda c: (c["game_id"], c.get("repeat", 0)))]

    clean_count = sum(1 for r in reports if not r["findings"])
    failed = clean_count != len(reports) or bool(sealed_hits) or bool(corrupt)

    if args.json:
        print(json.dumps({"reports": reports, "sealed_hits": sorted(set(sealed_hits)),
                          "corrupt_lines": corrupt, "clean": clean_count,
                          "total": len(reports), "pass": not failed},
                         indent=2, sort_keys=True))
        # Same exit code as text mode. An audit whose machine-readable form
        # always exits 0 would let CI report a clean sweep over a failing one.
        return 1 if failed else 0

    print("=== ledger files audited ===")
    for p in ledger_paths():
        print("  %s" % os.path.relpath(p, TRACK))
    print("\n=== corrupt lines: %d ===" % len(corrupt))
    for p, n in corrupt[:10]:
        print("  %s:%d" % (os.path.relpath(p, TRACK), n))

    print("\n=== sealed-pile check ===")
    if sealed_hits:
        print("  *** FAIL: sealed ids present: %s ***" % sorted(set(sealed_hits)))
    else:
        print("  PASS: every ledger record names a development-pile game (%d records)"
              % len(records))

    print("\n=== per cell ===")
    clean = clean_count
    for rep in reports:
        status = "OK" if not rep["findings"] else "FINDINGS"
        print("\n  [%s] %s rep %s (%s)" % (status, rep["game_id"], rep["repeat"], rep["outcome"]))
        print("      ledger: ok=%s failed=%s calls=%s $%.4f"
              % (rep["ledger_actions_ok"], rep["ledger_actions_failed"],
                 rep["ledger_model_calls"], rep["ledger_cost_usd"]))
        recon = rep["reconciliation"]
        if recon["available"]:
            print("      scorecard (%s): total_actions=%s score=%s levels=%s -> %s"
                  % (recon.get("source"), recon.get("card_total_actions"),
                     recon.get("card_score"), recon.get("card_levels_completed"),
                     recon.get("verdict")))
        else:
            print("      scorecard: NOT CAPTURED")
        for f in rep["findings"]:
            print("      - %s" % f)

    print("\n=== summary: %d/%d cells clean, sealed check %s ==="
          % (clean, len(reports), "FAIL" if sealed_hits else "PASS"))
    # Note: this appends to probe_log.jsonl, so the audit is itself an event in
    # the account. That is deliberate -- "was this audited, and when" belongs in
    # the ledger -- but it does mean the audit is not a read-only operation.
    ledger.probe("cell_audit", {"cells": len(reports), "clean": clean,
                                "sealed_hits": sorted(set(sealed_hits)),
                                "corrupt_lines": len(corrupt),
                                "game": args.game})
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
