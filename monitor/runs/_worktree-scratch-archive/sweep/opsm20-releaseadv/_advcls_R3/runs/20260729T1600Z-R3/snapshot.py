"""Snapshot the enumerator's classification of every tracked file.

    python release/runs/20260729T1600Z-R3/snapshot.py before.jsonl
    python release/runs/20260729T1600Z-R3/snapshot.py after.jsonl

Run once against the UNFIXED enumerator and once against the fixed one; the diff
between the two files is the measured impact of `R3-release-classifier-defaults`.

It calls `enumerate.build()` directly rather than `enumerate.main()`, and that is
deliberate. `main()` gates the whole enumeration behind `check_redlines`, which
in a checkout without `.env` refuses in `generate` mode -- so the distribution
this run exists to measure would never be computed. The red-line gate decides
whether a manifest may be *written*; this script writes no manifest, only a
census, so it reads the classifier directly.
"""

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
RELEASE = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, RELEASE)

import enumerate as enum  # noqa: E402


def main(argv):
    out = os.path.join(_HERE, argv[0] if argv else "snapshot.jsonl")
    rows = enum.build(enum._tracked())
    body = "\n".join(
        json.dumps(
            {"path": r["path"], "class": r["class"], "verdict": r["verdict"],
             "size": r["size"], "evidence": r["evidence"]},
            sort_keys=True, ensure_ascii=False)
        for r in rows
    ) + "\n"
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    counts = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    print(f"{len(rows)} rows -> {out}")
    for cls in sorted(counts):
        print(f"  {cls}  {counts[cls]:5d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
