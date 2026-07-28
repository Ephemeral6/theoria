"""What the re-judged rows cost the pinned confusion matrix.

The point of pinning `部分` is not tidiness. `strict` folding counts `部分` as
*has a negative control*, so every row that leaves `部分` for `否` moves from
gold-positive to gold-negative -- and 10 of V15's 17 new pinned false negatives
are `部分` rows. If the criterion drains that cell, V15's headline moves.

This substitutes the new arm's majority verdict for the 22 re-judged rows and
recomputes `matrix.py`'s four rows. Everything else -- the frame, the probe, the
other 231 gold rows -- is untouched.

    python verify-lab/irr/refold.py

Read the output as a **sensitivity**, not as a new headline. 22 of 253 rows were
re-judged, by three agents, on one criterion; `verify-lab/RELIABILITY.md` says
why that is not enough to republish an FNR.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(LAB, "frame"))
sys.path.insert(0, os.path.join(LAB, "negctl"))

import agree     # noqa: E402
import matrix    # noqa: E402
import frame     # noqa: E402

RUN = os.path.join(LAB, "runs", "20260729T180000Z-V17-pin-the-partial-verdict")


def substitutions(agreement: Dict[str, object]) -> Dict[str, str]:
    """path -> the new arm's majority 有负控 cell."""
    out: Dict[str, str] = {}
    for path, votes in agreement["per_row"].items():  # type: ignore[union-attr]
        trio = [votes[j] for j in agree.ARMS["new"]]
        out[path] = max(agree.CATS,
                        key=lambda c: (trio.count(c), -agree.CATS.index(c)))
    return out


def run(root: str, subs: Dict[str, str]) -> Dict[str, object]:
    meas, enumerated = matrix.measured(root)
    frame_paths = {u["path"] for u in frame.build(root)}
    out: Dict[str, object] = {}
    for tag, harsh in (("strict", False), ("harsh", True)):
        # `matrix.run`'s merge rule, transcribed: a V11 row wins over a V15 row
        # naming the same file, so the merged gold has one entry per path.
        g11 = matrix.gold_v11(root, harsh)
        g15 = [(p, v) for p, v in matrix.gold_v15(frame_paths, harsh)
               if p not in {q for q, _ in g11}]
        base = g11 + g15
        swapped = [(p, matrix._fold(subs[p], harsh) if p in subs else v)
                   for p, v in base]
        out[tag] = {
            "before": matrix.confusion(base, meas, enumerated),
            "after": matrix.confusion(swapped, meas, enumerated),
            "unrestricted_before": matrix.confusion(base, meas),
            "unrestricted_after": matrix.confusion(swapped, meas),
        }
    out["substituted"] = len(subs)
    out["substitutions"] = dict(sorted(subs.items()))
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=frame.REPO)
    ap.add_argument("--agreement", default=os.path.join(RUN, "agreement.json"))
    ap.add_argument("--json", metavar="OUT")
    args = ap.parse_args(argv)
    subs = substitutions(json.load(open(args.agreement, encoding="utf-8")))
    rep = run(args.root, subs)
    print("substituted %d re-judged rows into the gold standard" % rep["substituted"])
    for tag in ("strict", "harsh"):
        for when in ("before", "after"):
            m = rep[tag][when]  # type: ignore[index]
            print("  %-6s %-6s n=%-4d TP %-3d FN %-3d FP %-3d TN %-3d FNR %s FPR %s"
                  % (tag, when, m["n"], m["TP"], m["FN"], m["FP"], m["TN"],
                     m["FNR"], m["FPR"]))
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(rep, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
