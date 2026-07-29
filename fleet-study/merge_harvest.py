#!/usr/bin/env python3
"""Fold a day's harvest into fleet-study/data/, deterministically.

    python fleet-study/merge_harvest.py runs/<id>/harvest            # do it
    python fleet-study/merge_harvest.py runs/<id>/harvest --dry-run  # show only

S17 is a standing daily log, so this happens every day and the tricky part is
the same every day.  It is written down here rather than improvised in a shell
one-liner, because it was improvised once and lost a column.

## Two kinds of dataset, two merge rules

**Append-keyed** (`failures`, `timeline`, `counterevidence`, `assembly`,
`human_actions`, `bus`) carry synthetic ascending ids -- `F-97`, `T-46`.  A new
row is a new fact.  These are concatenated, and the verifier's ascending-id
check is what catches a numbering collision between two harvesters.

**State-keyed** (`deliveries`) is keyed by the board item's own slug, so the
same key comes back tomorrow with a *later state*: `open` -> `claimed` ->
`done`.  Concatenating gives duplicate ids and the verifier goes red -- which
is correct, because two rows for one item is two answers to one question.

The wrong fix is to let the new row replace the old one wholesale.  Yesterday's
row holds `first_claim_utc` and `priority`; today's holds `done_utc` and a
higher `commits`, and sets the fields it did not observe to `null`.  A wholesale
replace silently drops the claim time -- the very quantity the delivery record
exists to provide.  So state-keyed rows are merged **field by field**:

    scalar   today's value wins unless it is null/empty, else keep yesterday's
    list     union, order-preserving (claimed_by, released, evidence)
    position the row stays where it first appeared, so diffs stay readable

That rule is lossless in the only direction that matters: a fact once observed
is never un-observed by a later harvest that simply did not look for it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

#: dataset -> harvest filenames to fold in, in order.  A harvest file that is
#: absent is skipped without complaint: not every day produces every dataset.
SOURCES = {
    "failures": ["failures_new.jsonl"],
    "timeline": ["timeline_new.jsonl"],
    "counterevidence": ["counterevidence_selfaudit.jsonl",
                        "counterevidence_denominators.jsonl",
                        "counterevidence_new.jsonl"],
    "assembly": ["assembly_new.jsonl"],
    "human_actions": ["human_actions.jsonl"],
    "bus": ["bus.jsonl"],
    "deliveries": ["deliveries_new.jsonl"],
}

#: Keyed by a slug that recurs across days, so rows merge instead of appending.
STATE_KEYED = {"deliveries"}

#: Fields whose values are unioned rather than overwritten.
LIST_FIELDS = {"claimed_by", "released", "evidence", "commits_list"}


def read_rows(path: Path) -> list[dict]:
    raw = path.read_bytes()
    if b"\r" in raw:
        sys.exit(f"{path}: CRLF; the datasets are pinned to LF")
    return [json.loads(line) for line in raw.decode("utf-8").splitlines()
            if line.strip()]


def write_rows(path: Path, rows: list[dict]) -> None:
    body = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    path.write_bytes(body.encode("utf-8"))


def merge_row(old: dict, new: dict) -> dict:
    """Field-by-field: today wins where it observed something, never where it
    did not.  Lists union.  Keys only yesterday knew about survive."""
    out = dict(old)
    for key, val in new.items():
        if key in LIST_FIELDS:
            seen, merged = set(), []
            for item in list(old.get(key) or []) + list(val or []):
                marker = json.dumps(item, ensure_ascii=False, sort_keys=True)
                if marker not in seen:
                    seen.add(marker)
                    merged.append(item)
            out[key] = merged
        elif val is None or val == "" or val == []:
            continue          # today did not look; keep what yesterday saw
        else:
            out[key] = val
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("harvest", type=Path, help="runs/<id>/harvest directory")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    harvest = args.harvest if args.harvest.is_absolute() else Path.cwd() / args.harvest
    if not harvest.is_dir():
        sys.exit(f"not a directory: {harvest}")

    total_added = total_merged = 0
    for ds, filenames in SOURCES.items():
        parts = [harvest / f for f in filenames]
        parts = [p for p in parts if p.exists()]
        if not parts:
            continue

        target = DATA / f"{ds}.jsonl"
        rows = read_rows(target) if target.exists() else []
        index = {r.get("id"): i for i, r in enumerate(rows)}
        added = merged = 0

        skipped = 0
        for part in parts:
            for new in read_rows(part):
                rid = new.get("id")
                if rid in index:
                    if ds in STATE_KEYED:
                        rows[index[rid]] = merge_row(rows[index[rid]], new)
                        merged += 1
                    else:
                        # Append-keyed and already present: this harvest has
                        # been folded before.  Re-running must be a no-op, not
                        # a duplicate -- a daily tool that cannot be re-run
                        # safely gets run twice by someone eventually.
                        skipped += 1
                else:
                    index[rid] = len(rows)
                    rows.append(new)
                    added += 1

        total_added += added
        total_merged += merged
        verb = "would write" if args.dry_run else "wrote"
        note = f", {skipped} already present" if skipped else ""
        print(f"  {ds + '.jsonl':<26} {len(rows):>4} rows  "
              f"(+{added} new, {merged} merged{note})  {verb}")
        if not args.dry_run:
            write_rows(target, rows)

    print(f"\n{total_added} rows added, {total_merged} state-keyed rows merged.")
    print("Now run `python fleet-study/verify.py` -- this script does not "
          "validate, it only folds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
