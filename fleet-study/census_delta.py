#!/usr/bin/env python3
"""Diff two census snapshots -- what the fleet did between them, with no human in it.

    python fleet-study/census_delta.py                       # oldest history snapshot -> current
    python fleet-study/census_delta.py --from <a> --to <b>    # two explicit snapshot files
    python fleet-study/census_delta.py --json                # machine-readable

Why this exists
---------------
S17 is a *standing daily log*, not a one-off snapshot.  A day's headline is not
"the repo has N commits" -- it is "the fleet added M commits since yesterday".
That second number is the one the fleet-study thesis actually needs, and it is
the one that is easiest to get wrong by hand, so it is computed here instead of
being typed into prose.

The two commit counts mean different things and are both reported:

    commits_all_refs             work *authored* -- new commits on any ref
    commits_reachable_from_head  work *landed*   -- merges pull whole branches in

`reachable` moves in jumps far larger than `all_refs` because a single merge
lands a branch that was authored earlier.  Quoting `reachable` as a production
rate overstates the window; quoting `all_refs` as progress understates what
became real.  Report both, which is why this script refuses to collapse them.

Snapshots live in `fleet-study/data/census-history/census.<UTC>.json`, written
by copying `census.json` aside before `census.py` regenerates it.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
HISTORY = DATA / "census-history"

# Fields worth differencing, and how to read one.  Anything not listed here is
# either a constant (pile_cut) or a value whose delta is meaningless (head).
COUNTED = [
    ("commits_all_refs", "commits authored (any ref)"),
    ("commits_reachable_from_head", "commits landed on the mainline"),
    ("agent_branches", "agent branches"),
    ("partner_sync_paragraphs", "PARTNER_SYNC paragraphs"),
    ("inbox_reports_ever", "agent->monitor inbox reports (ever)"),
    ("inbox_reports_present", "inbox reports still on disk"),
    ("incident_ids_anywhere", "distinct incident ids"),
    ("incidents_in_ledger", "incidents in the ledger"),
]


def magnitude(v):
    """A census value's size: ints as themselves, lists/dicts by length."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, (list, dict)):
        return len(v)
    return None


def field(snap: dict, key: str):
    node = snap.get(key)
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node


def hours_between(a_utc: str, b_utc: str) -> float | None:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    try:
        a = datetime.strptime(a_utc, fmt).replace(tzinfo=timezone.utc)
        b = datetime.strptime(b_utc, fmt).replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None
    return (b - a).total_seconds() / 3600.0


def pick_snapshots(a: Path | None, b: Path | None) -> tuple[Path, Path]:
    if a and b:
        return a, b
    hist = sorted(HISTORY.glob("census.*.json"))
    if not hist:
        sys.exit(f"no snapshots in {HISTORY}; copy census.json aside before "
                 f"regenerating it, or pass --from/--to")
    return (a or hist[0]), (b or DATA / "census.json")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="a", type=Path, help="earlier snapshot")
    ap.add_argument("--to", dest="b", type=Path, help="later snapshot")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    pa, pb = pick_snapshots(args.a, args.b)
    for p in (pa, pb):
        if not p.exists():
            sys.exit(f"missing snapshot: {p}")
    a = json.loads(pa.read_text(encoding="utf-8"))
    b = json.loads(pb.read_text(encoding="utf-8"))

    a_utc, b_utc = field(a, "as_of_utc"), field(b, "as_of_utc")
    hours = hours_between(a_utc, b_utc)

    rows = []
    for key, label in COUNTED:
        va, vb = magnitude(field(a, key)), magnitude(field(b, key))
        if va is None or vb is None:
            continue
        rows.append({
            "field": key, "label": label,
            "before": va, "after": vb, "delta": vb - va,
            "per_hour": round((vb - va) / hours, 2) if hours else None,
        })

    out = {
        "window": {
            "from_utc": a_utc, "to_utc": b_utc,
            "from_head": field(a, "head"), "to_head": field(b, "head"),
            "hours": round(hours, 2) if hours else None,
            "from_snapshot": pa.name, "to_snapshot": pb.name,
        },
        "deltas": rows,
        "caveat": (
            "Rates are over one window on one machine; they are a measurement, "
            "not a capacity. 'landed' jumps faster than 'authored' because a "
            "merge lands a branch authored earlier -- the two are not "
            "interchangeable. Any human action inside the window belongs in "
            "human_actions.jsonl; this script cannot see one and does not "
            "claim the window was unattended."
        ),
    }

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    w = out["window"]
    print(f"census delta  {w['from_utc']} -> {w['to_utc']}"
          + (f"  ({w['hours']}h)" if w["hours"] else ""))
    print(f"              {str(w['from_head'])[:8]} -> {str(w['to_head'])[:8]}\n")
    print(f"  {'':34} {'before':>8} {'after':>8} {'delta':>8} {'/h':>7}")
    for r in rows:
        rate = f"{r['per_hour']:.2f}" if r["per_hour"] is not None else "-"
        print(f"  {r['label']:34} {r['before']:>8} {r['after']:>8} "
              f"{r['delta']:>+8} {rate:>7}")
    print(f"\n  {out['caveat']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
