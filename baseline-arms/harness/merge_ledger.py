"""Fold the per-process shards into the single append-only ledger.

The full run writes one shard per game so concurrent processes cannot interleave
mid-record (see `ledger._resolve`). This merges them back, in timestamp order,
into `ledger.jsonl` -- which stays the one file that merges with arc-gateway's.

Merging is *additive and idempotent*: every line already in the ledger is
remembered, and re-running adds only what is new. Shards are left in place, so
the merged file can always be rebuilt from them.

    python -m harness.merge_ledger [--check]
"""

import argparse
import glob
import json
import os
import sys

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARD_DIR = os.path.join(TRACK, "out", "shards")


def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [l for l in (line.rstrip("\n") for line in fh) if l]


def merge(basename: str, check_only: bool) -> int:
    target = os.path.join(TRACK, basename)
    stem, ext = os.path.splitext(basename)
    shards = sorted(glob.glob(os.path.join(SHARD_DIR, "%s.*%s" % (stem, ext))))
    if not shards:
        print("%-18s no shards" % basename)
        return 0

    existing = read_lines(target)
    seen = set(existing)
    corrupt = [i for i, l in enumerate(existing, 1) if not _parses(l)]

    fresh = []
    for shard in shards:
        for line in read_lines(shard):
            if not _parses(line):
                corrupt.append("%s:?" % os.path.basename(shard))
                continue
            if line not in seen:
                seen.add(line)
                fresh.append(line)

    fresh.sort(key=_ts)
    print("%-18s %d shards | %d existing | %d new | %d unparseable"
          % (basename, len(shards), len(existing), len(fresh), len(corrupt)))
    if corrupt:
        print("   UNPARSEABLE: %s" % corrupt[:5])

    if check_only or not fresh:
        return len(corrupt)
    with open(target, "a", encoding="utf-8", newline="") as fh:
        for line in fresh:
            fh.write(line + "\n")
    print("   appended %d lines to %s" % (len(fresh), basename))
    return len(corrupt)


def _parses(line: str) -> bool:
    try:
        json.loads(line)
        return True
    except Exception:
        return False


def _ts(line: str) -> str:
    try:
        return json.loads(line).get("timestamp") or ""
    except Exception:
        return ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report without writing")
    args = ap.parse_args(argv)
    bad = 0
    for basename in ("ledger.jsonl", "probe_log.jsonl"):
        bad += merge(basename, args.check)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
