"""Brute-force validation of exam/state_space.py before any number is trusted."""
import sys
# Repo root from this file, so the evidence reruns wherever the run directory
# is copied to -- an absolute path baked in here would make it reproducible
# on exactly one machine.
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))

from exam.papers import verdict as V
from exam.grading.rubrics_verdict import Level
from exam import state_space as SS

fails = 0


def check_exact(name, doc):
    global fails
    lvl = Level(doc)
    brute = SS.brute_force_count(lvl)
    got = SS.exact_count(lvl)["states"]
    ok = (brute is not None and brute == got)
    if not ok:
        fails += 1
    print("%-34s brute=%-10s symbolic=%-10s %s"
          % (name, brute, got, "OK" if ok else "*** MISMATCH ***"))
    return got


print("== unbudgeted: symbolic census vs the naive enumerator ==")
for k in range(1, 7):
    got = check_exact("gantry k=%d" % k,
                      V.variant_of(V.comb_room("gantry", k, None), "gantry",
                                   remap={"LEFT": "RIGHT", "RIGHT": "LEFT"}))
    assert got == 2 * k * 4 ** k, (got, 2 * k * 4 ** k)
for k in range(2, 7):
    got = check_exact("lattice k=%d" % k,
                      V.variant_of(V.comb_room("lattice", k, 2), "lattice",
                                   lost_cells=[[4, 2]]))
for k in range(1, 7):
    got = check_exact("spindle-unbudgeted k=%d" % k, V.comb_open("spindle", k, 1, k))
    assert got == 2 * k * 4 ** k, (got, 2 * k * 4 ** k)
for k in range(2, 7):
    got = check_exact("orchard k=%d" % k,
                      V.variant_of(V.comb_open("orchard", k, 2, 1), "orchard",
                                   forbidden=["LEFT"]))
    assert got == (2 * 4 ** k - 8) // 3, (got, (2 * 4 ** k - 8) // 3)

print()
print("== budgeted: is the bracket a bracket? ==")
for k in (2, 3, 4, 5):
    for budget in range(0, 17):
        doc = V.variant_of(V.comb_open("spindle", k, 1, k), "spindle",
                           step_limit=budget)
        lvl = Level(doc)
        brute = SS.brute_force_count(lvl)
        br = SS.budgeted_bracket(lvl)
        lo, hi = br["lower"], br["upper"]
        ok = lo <= brute <= hi
        if not ok:
            fails += 1
        print("k=%d B=%-3d lower=%-9d true=%-9d upper=%-11d %s"
              % (k, budget, lo, brute, hi, "OK" if ok else "*** VIOLATED ***"))

print()
print("FAILURES: %d" % fails)
