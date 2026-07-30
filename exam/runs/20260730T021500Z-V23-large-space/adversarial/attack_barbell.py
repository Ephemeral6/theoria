"""Attack C, second attempt: defeat the cost model, not the two premises.

`subset_lower_bound` charges `cost = distance + 2*index` for the index-th dip
(verdict.py:426), with candidates sorted by distance from the start ascending.
The docstring's justification -- "the corridor cells lie along one path and each
dip is out-and-back" -- is only valid when the dip sources are all on ONE SIDE
of the start.  When they straddle it, the cart must walk out to one end, back
past the start, and out to the other; the model charges only the longer arm.

The plain comb hides this because 2^m is loose by a factor of ~2k there, so an
over-count of m by a few is swallowed.  A *barbell* board removes the slack:
alcoves only at the two far ends of a long bare corridor, start in the middle.
Then the honest reachable set is (positions x masks of ONE end), while the
bound multiplies both ends together.

Neither of the two premises the D-EX-028 guard checks is violated: the dip
sources are distinct cells and they lie on one contiguous switch-free
hazard-free row (the bare corridor between the two alcove blocks is exactly
that lane).  So the guard passes and the bound is still returned.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from exam.papers import verdict as V                      # noqa: E402
from exam.grading import rubrics_verdict as RV            # noqa: E402


def barbell(level_id, corridor_len, alcove, step_limit):
    """Corridor of `corridor_len` floor cells, alcoves above and below only in
    the first and last `alcove` columns.  Start dead centre."""
    width = corridor_len + 2
    border = "#" * width
    cols = ([c for c in range(1, alcove + 1)]
            + [c for c in range(corridor_len - alcove + 1, corridor_len + 1)])
    shelf = list("#" * width)
    for c in cols:
        shelf[c] = "s"
    start_col = (corridor_len + 1) // 2
    corridor = list("#" + "." * corridor_len + "#")
    corridor[start_col] = "S"
    goal_col = corridor_len
    corridor[goal_col] = "G"
    rows = [border, "".join(shelf), "".join(corridor), "".join(shelf), border]
    switches = [[1, c] for c in cols] + [[3, c] for c in cols]
    return V._level(level_id, rows, (2, start_col), (2, goal_col),
                    switches=switches, require_all_switches=True,
                    step_limit=step_limit)


#: Enumeration cap for the *measurement*.  Deliberately larger than the shipped
#: MAX_ENUMERATION, because here the enumerator is the referee and a truncated
#: count would prove nothing either way.  Nothing production reads this.
PROBE_CAP = 8_000_000


def probe(corridor_len, alcove, step_limit):
    doc = barbell("barbell-%d-%d-%d" % (corridor_len, alcove, step_limit),
                  corridor_len, alcove, step_limit)
    level = RV.Level(doc)
    problems = level.wellformed_problems()
    try:
        bound = V.subset_lower_bound(level)
    except AssertionError as exc:
        return {"corridor_len": corridor_len, "alcove": alcove,
                "step_limit": step_limit, "refused": str(exc)[:300],
                "wellformed_problems": problems}
    t0 = time.perf_counter()
    result = RV.enumerate_states(level, cap=PROBE_CAP)
    dt = time.perf_counter() - t0
    return {
        "corridor_len": corridor_len,
        "alcove": alcove,
        "step_limit": step_limit,
        "start_col": (corridor_len + 1) // 2,
        "wellformed_problems": problems,
        "m": bound["m"],
        "lower_bound": bound["lower_bound"],
        "dippable_switches": bound["dippable_switches"],
        "measured_states": result["states"],
        "truncated": result["truncated"],
        "bound_is_sound": (None if result["truncated"]
                           else result["states"] >= bound["lower_bound"]),
        "overstatement": (None if result["truncated"] or not result["states"]
                          else bound["lower_bound"] / result["states"]),
        "seconds": round(dt, 3),
    }


def main():
    rows = []
    for corridor_len in (21, 31, 41):
        for alcove in (4, 5, 6, 7, 8):
            base = (corridor_len - 1) // 2 + 8 * alcove
            for step_limit in range(max(4, base - 6), base + 10, 2):
                rows.append(probe(corridor_len, alcove, step_limit))

    unsound = [r for r in rows if r.get("bound_is_sound") is False]
    out = {
        "what": "barbell board: dip sources straddle the start, cost model "
                "`dist + 2m` under-charges the walk between the two ends",
        "probe_cap": PROBE_CAP,
        "sweep_rows": len(rows),
        "unsound_rows": len(unsound),
        "worst": (max(unsound, key=lambda r: r["overstatement"])
                  if unsound else None),
        "unsound_examples": sorted(unsound,
                                   key=lambda r: -r["overstatement"])[:15],
        "all_rows": rows,
    }
    path = os.path.join(os.path.dirname(__file__), "attack_barbell.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(out, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("sweep rows   :", len(rows))
    print("UNSOUND rows :", len(unsound))
    for row in sorted(unsound, key=lambda r: -r["overstatement"])[:10]:
        print("  len=%(corridor_len)d alcove=%(alcove)d limit=%(step_limit)d "
              "m=%(m)d bound=%(lower_bound)d measured=%(measured_states)d "
              "OVERSTATED x%(overstatement).1f" % row)


if __name__ == "__main__":
    main()
