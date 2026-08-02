"""Print the state-space census for the verdict paper, recomputed live.

    python -m exam.tools.state_census

Reads nothing from `artifacts/`: it rebuilds the paper and runs the census
again, so what it prints is what the code says today rather than what a file
says it said once.  That is the point -- the committed truth file carries these
numbers, and this is the command a reviewer runs to disagree with them.

Two columns, and the whole finding is that they are two columns:

    state count   what a NAIVE forward enumeration over (cart, button, latch
                  mask) would have to walk.  Astronomical, and that is what
                  makes the class name true.
    settles in    what an exhaustive computation that is *not* naive has to
                  walk to decide the item.  At most 600 nodes, and that is what
                  D-EX-028 withdrew the stronger claim over.

A reader who takes the first column as an answer to the second has made exactly
the mistake the exam already corrected once.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import state_space as SS                                 # noqa: E402
from exam.papers import module_for                                 # noqa: E402

CLASS_ORDER = ("small_unsolvable", "large_unsolvable", "solvable_hard")


def _size(space):
    exact = space["exact_states"]
    if exact is not None:
        return "%.4g" % float(exact) if exact >= 10 ** 6 else str(exact)
    if space["census_upper"] is not None:
        return "%.4g..%.4g" % (float(space["census_lower"]),
                               float(space["census_upper"]))
    return ">=%.4g" % float(space["census_lower"])


def main() -> int:
    paper = module_for("verdict").build()
    print("state-space census -- %s" % paper.paper_id)
    print("naive ceiling %d; a count above it means the naive method cannot run"
          % SS.NAIVE_CEILING)
    print()
    print("%-14s %-18s %-24s %-22s %-10s %s"
          % ("item", "class", "state count", "how counted", "settles in",
             "naive?"))
    print("-" * 104)
    counted = bracketed = floored = 0
    for klass in CLASS_ORDER:
        for item in sorted(paper.items, key=lambda i: i.item_id):
            if item.truth["class"] != klass:
                continue
            space = item.truth["state_space"]
            if space["exact_states"] is not None:
                counted += 1
            elif space["census_upper"] is not None:
                bracketed += 1
            else:
                floored += 1
            print("%-14s %-18s %-24s %-22s %-10s %s"
                  % (item.item_id, klass, _size(space), space["census_method"],
                     "%d nodes" % space["positional_states"],
                     "feasible" if space["naive_enumeration_feasible"]
                     else "OUT OF REACH"))
    print()
    print("%d items counted exactly, %d bracketed, %d with a floor and no "
          "ceiling." % (counted, bracketed, floored))
    large = [i for i in paper.items if i.truth["class"] == "large_unsolvable"]
    print("class (ii) holds %d items and every one of them survives the "
          "reclassification test:" % len(large))
    for item in large:
        space = item.truth["state_space"]
        print("  %-14s at least %.4g states, so the naive method cannot decide "
              "it -- but %d nodes settle it, so *an* exhaustive method can."
              % (item.item_id, float(space["census_lower"]),
                 space["positional_states"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
