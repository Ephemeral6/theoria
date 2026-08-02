#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adjudicate EVERY book in a directory separately, not best-of.

`u3.evaluate` returns one verdict per DIRECTORY, taking the best book in it.
That is right for the endpoint (a game attains if the arm produced at least one
theorem) but it hides which book carried the directory, and it hides a book
that failed for an environmental reason behind a sibling that did not.  This
runs each book alone, sequentially, so the C4 rows can be read per file.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
from freeze import u3  # noqa: E402

DIRS = [
    REPO / "theory-compiler" / "runs" / "20260728T080019Z-C4-deadlock-lean",
    REPO / "theory-compiler" / "runs" / "20260728T080019Z-C4-deadlock-lean" / "verify",
]

def main() -> int:
    lean = u3.find_lean()
    out = []
    for d in DIRS:
        for b in u3.find_books(d):
            t0 = time.time()
            row = u3.eval_lean_source(b, probe=False, lean_bin=lean, recorded={})
            rec = {
                "dir": d.relative_to(REPO).as_posix(),
                "book": b.name,
                "verdict": row["verdict"],
                "label": row["label"],
                "a_compiles": row["criteria"].get("a_compiles"),
                "b_axioms": row["criteria"].get("b_axioms"),
                "c_nonvacuous": row["criteria"].get("c_nonvacuous"),
                "attaining": row["criteria"].get("attaining"),
                "stderr_tail": (row.get("evidence") or {}).get("stderr_tail"),
                "seconds": round(time.time() - t0, 1),
            }
            out.append(rec)
            print(json.dumps(rec, ensure_ascii=False), flush=True)
    (HERE / "per_book.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8")
    return 0

if __name__ == "__main__":
    sys.exit(main())
