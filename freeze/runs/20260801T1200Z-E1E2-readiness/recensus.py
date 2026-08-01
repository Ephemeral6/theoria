#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-run E1 over everything on disk after the F1/D1/D2 repair.

Offline: Lean only, no API, no model, no network.  Writes census.json and
CENSUS.md next to itself.

  python freeze/runs/20260801T0700Z-E1-kind-census/census.py [root]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))

from freeze import u3  # noqa: E402


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO
    lean = u3.find_lean()
    exclusions: list = []
    targets = u3.expand_targets([root], record_exclusions=exclusions)
    rows = []
    t0 = time.time()
    for i, t in enumerate(targets, 1):
        started = time.time()
        row = u3.evaluate(t, probe=False, lean_bin=lean)
        row["books"] = [p.name for p in u3.find_books(t)]
        row["seconds"] = round(time.time() - started, 1)
        rows.append(row)
        print("[%2d/%2d] %-14s %5.1fs  %s"
              % (i, len(targets), row["label"], row["seconds"],
                 t.relative_to(root).as_posix()), flush=True)
    rows = u3.sanitize_paths(rows)

    books = [r for r in rows if r["books"]]
    def tally(rs):
        out: dict = {}
        for r in rs:
            out[r["label"]] = out.get(r["label"], 0) + 1
        return dict(sorted(out.items()))

    result = {
        "utc": "2026-08-01T12:00:00Z",
        "lean": "4.9.0" if lean else None,
        "probe": False,
        "targets": len(rows),
        "books": len(books),
        "book_labels": tally(books),
        "all_labels": tally(rows),
        "books_attained": sum(1 for r in books if r["verdict"] == "attained"),
        "targets_attained": sum(1 for r in rows if r["verdict"] == "attained"),
        "denominator_meaning":
            "per-DIRECTORY over what is on disk.  This is NOT STATS_RULES §1.2's "
            "E1 rate: that denominator is the frozen 19 (clean layer 12) sealed "
            "claim-set games and nothing else.  The two share a name and nothing "
            "more.",
        "exclusions": u3.sanitize_paths(exclusions),
        "rows": rows,
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    (HERE / "census.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8")
    (HERE / "CENSUS.md").write_text(u3.to_markdown(books) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("rows", "exclusions")},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
