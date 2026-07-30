"""Attack C: can `subset_lower_bound` still be fooled after the D-EX-028 guard?

The guard added by this run checks two premises: the m dip sources lie on one
straight switch-free hazard-free lane, and the m chosen switches are distinct
cells (distinct latch bits).  Neither premise touches the *cost model*.

`subset_lower_bound` decides how many dips the step budget affords with

    cost = distance + 2 * index                     (verdict.py:426)

where `distance` is the shortest-path distance from the start to the index-th
dip source, and the candidates are sorted by that distance ascending.  The
docstring justifies it: "the corridor cells lie along one path and each dip is
out-and-back".  That is true only when the dip sources all lie on ONE SIDE of
the start.  Put the start in the middle of the lane -- which `comb_open` takes
as a parameter, `start_col` -- and visiting a prefix that straddles the start
costs an extra 2*min(left_reach, right_reach) commands the model never charges.

If the step budget then binds, `m` is too large and 2^m is not a lower bound.

No production file is touched; this builds levels with the shipped constructor
and calls the shipped functions.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from exam.papers import verdict as V                      # noqa: E402
from exam.grading import rubrics_verdict as RV            # noqa: E402


def probe(corridor_len, start_col, goal_col, step_limit):
    doc = V.variant_of(V.comb_open("straddle", corridor_len, start_col, goal_col),
                       "straddle-sl%s" % step_limit, step_limit=step_limit)
    level = RV.Level(doc)
    problems = level.wellformed_problems()
    try:
        bound = V.subset_lower_bound(level)
    except AssertionError as exc:
        return {"corridor_len": corridor_len, "start_col": start_col,
                "step_limit": step_limit, "refused": str(exc)[:200],
                "wellformed_problems": problems}
    t0 = time.perf_counter()
    result = RV.enumerate_states(level, cap=RV.MAX_ENUMERATION)
    dt = time.perf_counter() - t0
    return {
        "corridor_len": corridor_len,
        "start_col": start_col,
        "goal_col": goal_col,
        "step_limit": step_limit,
        "wellformed_problems": problems,
        "m": bound["m"],
        "lower_bound": bound["lower_bound"],
        "dippable_switches": bound["dippable_switches"],
        "measured_states": result["states"],
        "truncated": result["truncated"],
        "bound_is_sound": result["states"] >= bound["lower_bound"],
        "overstatement": (bound["lower_bound"] / result["states"]
                          if result["states"] else None),
        "seconds": round(dt, 3),
    }


def main():
    rows = []
    # Sweep: corridor with the start in the middle, tight budgets.
    for corridor_len in (9, 11, 13, 15, 17, 21, 25):
        mid = (corridor_len + 1) // 2
        for step_limit in range(4, 46, 2):
            rows.append(probe(corridor_len, mid, corridor_len, step_limit))
    # Control: the shipped shape, start at column 1, no straddle possible.
    control = []
    for corridor_len in (9, 15, 25):
        for step_limit in range(4, 46, 2):
            control.append(probe(corridor_len, 1, corridor_len, step_limit))

    unsound = [r for r in rows
               if not r.get("refused") and not r.get("truncated")
               and r.get("bound_is_sound") is False]
    unsound_control = [r for r in control
                       if not r.get("refused") and not r.get("truncated")
                       and r.get("bound_is_sound") is False]
    out = {
        "what": "straddling dip sources defeat the cost model `dist + 2m`",
        "sweep_rows": len(rows),
        "unsound_rows": len(unsound),
        "worst": (max(unsound, key=lambda r: r["overstatement"])
                  if unsound else None),
        "unsound_examples": unsound[:12],
        "control_start_col_1_unsound_rows": len(unsound_control),
        "all_rows": rows,
        "control_rows": control,
    }
    path = os.path.join(os.path.dirname(__file__), "attack_straddle.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("sweep rows           :", len(rows))
    print("UNSOUND rows         :", len(unsound))
    print("control unsound rows :", len(unsound_control))
    if unsound:
        worst = max(unsound, key=lambda r: r["overstatement"])
        print("worst:", json.dumps(worst, sort_keys=True))
    for row in unsound[:8]:
        print("  len=%(corridor_len)d start=%(start_col)d limit=%(step_limit)d "
              "m=%(m)d bound=%(lower_bound)d measured=%(measured_states)d "
              "ratio=%(overstatement).2f" % row)


if __name__ == "__main__":
    main()
