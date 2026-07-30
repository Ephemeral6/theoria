"""B4 · the exact count had to stop being exponential, and stay the same number.

V25's whole argument for enumerating instead of shuffling is that an exact answer
carries no seed and no error bar. That argument dies if the exact answer is too
slow to compute, because a gate slow enough to be switched off is a gate that is
not there.

`_fire_count_bruteforce` walks every split of the carriers across answer classes:
prod(s_i + 1) of them, exponential in the number of *answer classes* -- and the
answer classes are the one thing an exam does not control. An exam whose answers
are integers (`plan_len`) has as many classes as it has distinct answers.

Measured here, on this machine, before anything was changed:

    2 classes, n=80   0.00s
    4 classes, n=80   0.01s
    6 classes, n=80   0.46s
    8 classes, n=80  14.67s        <- 30x per two classes
   12 classes, n=120 did not finish

So the count was rewritten to collapse states instead of enumerating splits
(`_fire_count`). This script is the evidence that the rewrite changed the cost and
not the answer:

1. a differential sweep against the oracle over every class-size multiset it can
   afford, at six tolerances including the ones that sit exactly on a float
   boundary;
2. the same comparison on cases with a large nonzero count, because agreeing on
   zero is easy and worthless;
3. the timings that were pathological before.

No RNG anywhere -- the sweep is a full enumeration of small shapes, so this file
is byte-reproducible.

    python -m exam.runs.<this dir>.b4_fast_count_vs_oracle     # or run it directly
"""

from __future__ import annotations

import itertools
import json
import os
import sys
import time
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import leakage  # noqa: E402

# Tolerances: the shipped one, two loose ones that make the majority floor the
# binding clause instead, the two degenerate ends, and 0.875 -- which is exactly
# 7/8 and therefore an exact float tie at n=8, where a rewrite diverges silently.
TOLERANCES = (0.90, 0.75, 0.50, 0.99, 1.0, 0.875)


def sweep(max_n: int = 9, max_classes: int = 4, max_size: int = 6):
    """Every class-size multiset the oracle can afford, every k, every tolerance."""
    mismatches = []
    cases = 0
    for m in range(1, max_classes + 1):
        for sizes in itertools.combinations_with_replacement(
                range(1, max_size + 1), m):
            n = sum(sizes)
            if n > max_n:
                continue
            for k in range(1, n):
                for tol in TOLERANCES:
                    fast = leakage._fire_count(sizes, k, tol)
                    slow = leakage._fire_count_bruteforce(sizes, k, tol)
                    cases += 1
                    if fast != slow:
                        mismatches.append({"sizes": list(sizes), "k": k,
                                           "tolerance": tol,
                                           "fast": fast, "oracle": slow})
    return cases, mismatches


#: Shapes chosen so the count is large and nonzero -- one dominant class plus
#: singletons (carriers land only on the singletons), and a mixed six-class group
#: the size of the real `heldout` paper. Agreement on zero proves nothing.
NONZERO = (
    ((75, 1, 1, 1, 1, 1), 3, 0.90),
    ((75, 1, 1, 1, 1, 1), 4, 0.90),
    ((75, 1, 1, 1, 1, 1), 5, 0.90),
    ((40, 30, 4, 3, 2, 1), 35, 0.60),
    ((6, 2), 2, 0.90),                 # v11-handover-a0 / solvable: 1/28
    ((6, 6), 6, 0.90),                 # 2 / C(12,6)
    ((4, 2), 2, 0.90),                 # the n=6 planted leak: 1 / C(6,2)
)

#: The cases that were pathological before the rewrite. `_fire_count_bruteforce`
#: is NOT run on these -- that is the point of the file.
TIMED = (
    ({"c%d" % j: 40 for j in range(2)}, 3),
    ({"c%d" % j: 20 for j in range(4)}, 3),
    ({"c%d" % j: 13 for j in range(6)}, 40),
    ({"c%d" % j: 10 for j in range(8)}, 3),
    ({"c%d" % j: 10 for j in range(12)}, 3),
    ({"c%d" % j: 10 for j in range(20)}, 5),
    ({"c0": 75, **{"c%d" % j: 1 for j in range(1, 6)}}, 3),
)


def main() -> int:
    out = {"tolerances": list(TOLERANCES)}

    cases, mismatches = sweep()
    out["differential"] = {"cases": cases, "mismatches": mismatches}
    print("differential sweep: %d configurations, %d mismatches"
          % (cases, len(mismatches)))
    for bad in mismatches[:10]:
        print("  MISMATCH %r" % (bad,))

    print("\nnonzero-count agreement (oracle is run on these):")
    out["nonzero"] = []
    for sizes, k, tol in NONZERO:
        fast = leakage._fire_count(sizes, k, tol)
        slow = leakage._fire_count_bruteforce(sizes, k, tol)
        ok = fast == slow
        out["nonzero"].append({"sizes": list(sizes), "k": k, "tolerance": tol,
                               "fast": fast, "oracle": slow, "agree": ok})
        print("  sizes=%-22s k=%-3d tol=%.2f count=%-22d %s"
              % (sizes, k, tol, fast, "agree" if ok else "DISAGREE %d" % slow))

    print("\ntimings for the fast count (oracle deliberately not run):")
    out["timings"] = []
    for counts, k in TIMED:
        start = time.perf_counter()
        p = leakage.token_fire_probability(counts, k)
        elapsed = time.perf_counter() - start
        n = sum(counts.values())
        out["timings"].append({"classes": len(counts), "n": n, "k": k,
                               "p_fire": p, "seconds": round(elapsed, 4)})
        print("  %2d classes n=%-4d k=%-3d p=%.8g  %.4fs"
              % (len(counts), n, k, p, elapsed))

    # The identity that says the count is a probability at all: summed over every
    # k the gate could see, hits can never exceed the subsets available.
    checks = []
    for counts in ({"a": 6, "b": 2}, {"a": 6, "b": 6}, {"a": 4, "b": 2},
                   {"a": 5, "b": 3, "c": 2}):
        n = sum(counts.values())
        for k in range(1, n):
            p = leakage.token_fire_probability(counts, k)
            checks.append(0.0 <= p <= 1.0
                          and leakage._fire_count(
                              [counts[c] for c in sorted(counts)], k, 0.90)
                          <= comb(n, k))
    out["bounds_hold"] = all(checks)
    print("\nevery p in [0,1] and every count <= C(n,k): %s" % all(checks))

    path = os.path.join(HERE, "fast_count_check.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(out, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("\nwrote %s" % os.path.basename(path))
    return 0 if not mismatches and all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
