"""Recover a run that died before it could close its own scorecard.

A run that raises somewhere `play()` does not catch never reaches `_finish()`,
so the scorecard stays open and the arm's own summary files are never written.
Both are recoverable from the ledger, which is written as it goes:

* the `card_id` is in the `env_meta` record for `POST /api/scorecard/open`;
* the trace is in the `env_step` records, frames and all.

Closing matters because of D-015: the score exists **only** inside a successful
close response, a closed card can never be re-fetched, and close 404s
transiently often enough that `baseline-arms` lost 22 of 23 pilot scores to it.
An unclosed card yields no score at all.

    python -m tools.salvage --slug <slug>            # report only
    python -m tools.salvage --slug <slug> --close    # also close the scorecard
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap                                     # noqa: F401  (sys.path)

from proxy.ledger import read_ledger


def card_ids(records: List[Dict[str, Any]]) -> List[str]:
    found: List[str] = []
    for record in records:
        if record.get("event") == "env_meta":
            response = record.get("response")
            if isinstance(response, dict) and response.get("card_id"):
                if response["card_id"] not in found:
                    found.append(response["card_id"])
        for key in ("card_id",):
            value = record.get(key)
            if value and value not in found:
                found.append(value)
    return found


def rebuild_trace(records: List[Dict[str, Any]], out_path: str) -> Dict[str, Any]:
    """`trace.jsonl` in the shape `world.frames.load_store` reads, from the
    ledger's own `env_step` records."""
    steps = [r for r in records
             if r.get("event") == "env_step"
             and (r.get("http") or {}).get("status") == 200]
    n = 0
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        for record in steps:
            row = {
                "step_idx": n,
                "action": record["action"]["name"],
                "data": record["action"].get("data"),
                "status": 200,
                "state": record.get("state"),
                "levels_completed": record.get("levels_completed"),
                "available_actions": None,
                "probe": False,
                "note": "rebuilt from the ledger",
                "frames": record.get("frames") or [],
            }
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":")))
            fh.write("\n")
            n += 1
    return {"path": out_path, "states": n,
            "cascade_lengths": sorted({len(r.get("frames") or []) for r in steps})}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--close", action="store_true",
                    help="open a proxy and close the scorecard (real traffic)")
    ap.add_argument("--game", default="g50t-5849a774")
    args = ap.parse_args(argv)

    run_dir = _bootstrap.path("runs", args.slug)
    records = read_ledger(os.path.join(run_dir, "ledger.jsonl"))
    cards = card_ids(records)
    steps = [r for r in records if r.get("event") == "env_step"]
    ok = [r for r in steps if (r.get("http") or {}).get("status") == 200]

    out: Dict[str, Any] = {
        "slug": args.slug,
        "records": len(records),
        "env_steps": len(steps),
        "env_steps_ok": len(ok),
        "successful_actions": sum(1 for r in ok
                                  if r["action"]["name"] != "RESET"),
        "card_ids": cards,
        "run_end_present": any(r.get("event") == "run_end" for r in records),
    }
    out["trace"] = rebuild_trace(records, os.path.join(run_dir, "trace.jsonl"))

    if args.close and cards:
        from harness.arc import ArcThroughProxy       # noqa: PLC0415
        from harness.budget import Budget             # noqa: PLC0415
        from harness.run import Run                   # noqa: PLC0415
        with Run(args.game, args.slug + "-salvage") as run:
            run.start_record(note="salvage: closing an orphaned scorecard")
            arc = ArcThroughProxy(run.env_base, args.game,
                                  Budget(actions=0, commands=60))
            arc.card_id = cards[0]
            out["scorecard_on_close"] = arc.close_scorecard()
            run.end_record(outcome="salvage", steps=0)
    elif args.close:
        out["scorecard_on_close"] = "no card_id found in the ledger"

    with open(os.path.join(run_dir, "SALVAGE.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    print(json.dumps(out, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
