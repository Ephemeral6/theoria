"""Negative control (B): duplicate switch entries inflate `subset_lower_bound`.

Deterministic, offline, no network.  Builds one level whose `switches` list
names the SAME cell 60 times, then asks three separate questions:

  1. what `subset_lower_bound` claims (m and 2^m);
  2. what the level actually has, by `enumerate_states` (exact, under the cap);
  3. which of the three guards -- the lane AssertionError inside
     `subset_lower_bound`, the `LARGE_SPACE_THRESHOLD` floor inside
     `_large_space`, and `Level.wellformed_problems()` -- refuses it.

The board is `comb_open`'s, unmodified, so the geometry is a shipped one; the
only surgery is the `switches` list, which is exactly the hand-transcription
hazard `wellformed_problems` was written for.  The point of the control is
*when* that check runs: `verdict.build()` calls `_self_check` (and therefore
`wellformed_problems`) at the very end of `build()`, after every
`_large_space()` call has already produced a truth record.

Anchors here are symbol names, not line numbers.  The first version of this file
pinned `verdict.py:1278` for the `_self_check(items)` call, `:1354` for
`wellformed_problems()`, and 1010/1030/1055/1081/1212/1241/1267 for the seven
`_large_space(lvl)` call sites.  All nine resolved exactly at base commit
`415556f8`; eight were already off by 58 lines and the ninth by 64 at
`1486875e`, the commit that shipped this artefact; and they are off by 176 and
182 at `824b9fb4`.  Rot is quoted against named commits because it keeps
growing -- `verdict.py` moved again at `0154c8f1`, after the anchors were
replaced.  That is board items P21/P22's standing finding, and re-pinning to
today's numbers only resets the clock.

One disambiguation, because two readers have now taken it the other way: 1278
named the *call* `_self_check(items)`, not the definition.  `def _self_check`
sat at 1338 at the base commit and was never anchored here, so comparing 1278
against today's `def` line gives a different and larger figure than the rot of
the anchor that was actually written.

Run:  python exam/runs/20260730T021500Z-V23-large-space/repro_duplicate_switch.py
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam.grading import rubrics_verdict as RV      # noqa: E402
from exam.papers import verdict as V                # noqa: E402

DUP_CELL = [1, 1]        # the alcove every one of the 60 entries names
DUP_COUNT = 60           # 2^60 = 1.15e18, comfortably over the 1e12 threshold
CORRIDOR_LEN = 60


def build_level():
    """`comb_open`'s board, with the switch list replaced by 60 copies of one
    cell.  Nothing else is touched: same rows, same start, same goal, same
    `require_all_switches`, no step limit."""
    base = V.comb_open("negctl-dup-switch", CORRIDOR_LEN, 1, CORRIDOR_LEN)
    return V.variant_of(base, "negctl-dup-switch",
                        switches=[list(DUP_CELL) for _ in range(DUP_COUNT)])


def main() -> int:
    doc = build_level()
    level = RV.Level(doc)

    out = {
        "level_id": doc["level_id"],
        "board": {"height": level.height, "width": level.width,
                  "corridor_len": CORRIDOR_LEN},
        "switch_entries": len(level.switches),
        "distinct_switch_cells": len(level.switch_index),
        "step_limit": level.step_limit,
        "large_space_threshold": V.LARGE_SPACE_THRESHOLD,
        "enumeration_cap": RV.MAX_ENUMERATION,
    }

    # ---- 1. the claimed bound -------------------------------------------
    try:
        bound = V.subset_lower_bound(level)
        out["subset_lower_bound"] = {
            "raised": False,
            "m": bound["m"],
            "dippable_switches": bound["dippable_switches"],
            "lower_bound": bound["lower_bound"],
            "arithmetic": bound["arithmetic"],
        }
        out["guard_lane_assertion_refused"] = False
    except AssertionError as exc:
        out["subset_lower_bound"] = {"raised": True, "message": str(exc)}
        out["guard_lane_assertion_refused"] = True

    # ---- 2. what `_large_space` writes into the truth record -------------
    try:
        record = V._large_space(doc)
        out["large_space_record"] = {
            "raised": False,
            # Was `record["exhaustive_feasible"]`, renamed by D-EX-028 in the very
            # commit that shipped this file. It survived because the new guard
            # makes `_large_space` raise, so this branch never runs -- meaning the
            # ONLY path that reports the defect this control exists to catch (the
            # guard regressing and an inflated record being written) died with a
            # KeyError instead. A control whose failure path is broken is not a
            # control.
            "naive_enumeration_feasible": record["naive_enumeration_feasible"],
            "lower_bound": record["lower_bound"],
            "m": record["m"],
            "dippable_switches": record["dippable_switches"],
            "positional_states": record["positional_states"],
        }
        out["guard_threshold_refused"] = False
    except AssertionError as exc:
        out["large_space_record"] = {"raised": True, "message": str(exc)}
        # A threshold refusal and a lane refusal both surface here; attribute it.
        out["guard_threshold_refused"] = "under the" in str(exc)

    # ---- 3. the truth ----------------------------------------------------
    enumerated = RV.enumerate_states(level, cap=RV.MAX_ENUMERATION)
    out["true_reachable_states"] = enumerated["states"]
    out["enumeration_truncated"] = enumerated["truncated"]
    out["positional_states"] = V.positional_states(level)

    # ---- 4. the check that does fire, and where it runs ------------------
    problems = level.wellformed_problems()
    out["wellformed_problems"] = problems
    out["guard_wellformed_refused"] = bool(problems)
    out["wellformed_runs_at"] = (
        "exam/papers/verdict.py: `build()` calls `_self_check(items)` as its "
        "last step, after the deterministic shuffle; `_self_check` is that "
        "module's only caller of `Level.wellformed_problems()`. All seven "
        "`_large_space(lvl)` calls are argument expressions of `_make_item(...)` "
        "earlier in `build()`, so all seven truth records already exist when the "
        "check runs. Anchored by symbol rather than by line. The nine line "
        "numbers this field first published -- 1010/1030/1055/1081/1212/1241/"
        "1267 for the call sites, 1278 for the `_self_check(items)` CALL (not "
        "its `def`, which was at 1338 and was never anchored) and 1354 for "
        "`wellformed_problems()` -- resolved exactly at base commit 415556f8, "
        "were already off by 58 lines (64 for the last) at 1486875e, the commit "
        "that shipped this artefact, and are off by 176 (182 for the last) at "
        "824b9fb4. Quoted against named commits because the rot keeps growing: "
        "verdict.py moved again at 0154c8f1, after these anchors were replaced "
        "(P21/P22)")

    claimed = out["subset_lower_bound"].get("lower_bound")
    if claimed is not None and not out["enumeration_truncated"]:
        out["overstatement_factor"] = claimed / out["true_reachable_states"]

    path = os.path.join(HERE, "repro_duplicate_switch.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(out, handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(json.dumps(out, indent=2, sort_keys=True))
    print("\nwrote %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
