"""Take the measurement `_large_space()` never takes.

`exam/papers/verdict.py`'s `_large_space()` stamps every class (ii) truth record
with `"naive_enumeration_feasible": False, "enumeration_attempted": False,
"enumerated": null, "truncated": null` *without ever calling
`enumerate_states`*.  It used to write `"exhaustive_feasible": False` beside
`"truncated": false`, and both were wrong in the same way: the field claimed no
exhaustive method is feasible, which a 600-node pass refutes, and `truncated:
false` was true only in the sense that no enumeration was attempted while
reading exactly like one that ran and came back clean.  D-EX-028 renamed the
first and nulled the second, and a separate `enumeration_attempted` flag now says
outright that nothing ran.  `_small_space()`, by contrast, actually runs
`enumerate_states(level, cap=MAX_ENUMERATION)` and raises if it truncated.

This script runs the enumeration `_large_space` skips, on the *same levels*
`build()` ships, at the *same* shipped cap, and records what comes back.  It
also runs the class (i) levels as a contrast row, so the two columns can be
read side by side.

Determinism.  Everything under `"deterministic"` is a pure function of the
repo: the levels are rebuilt from `verdict.py`'s own constructors, and
`enumerate_states` is a deterministic BFS.  Wall-clock seconds are the only
non-reproducible quantity, so they are isolated under a separate top-level
`"timings_nondeterministic"` key and rounded to 3 decimals; `deterministic`
carries its own sha256 so the stable half can be diffed on its own.

Run:  python exam/runs/20260730T021500Z-V23-large-space/enumeration_probe.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam.grading.rubrics_verdict import (        # noqa: E402
    MAX_ENUMERATION, Level, enumerate_states, relaxed_distance,
)
from exam.papers import verdict as V              # noqa: E402

OUT = os.path.join(HERE, "enumeration_probe.json")


def levels():
    """The nine levels `build()` ships for classes (i) and (ii).

    Rebuilt from the same constructors and the same operator arguments used in
    `verdict.build()` (verdict.py lines 871-1083), so these are the levels the
    shipped truth records describe -- not lookalikes.  `build()` itself is not
    called because it writes spec files into `exam/artifacts/`; the level
    documents are the whole of what `_small_space`/`_large_space` see.
    """
    atrium = V.a2_echo()
    atrium_distance = relaxed_distance(Level(atrium), (5, 1), (2, 7))
    i4_budget = atrium_distance - 4
    return [
        # ---- class (i): `_small_space()` -- enumeration actually run at build
        ("i1", "atrium", "small_unsolvable", "a2var-i1-atrium-nodown",
         V.variant_of(atrium, "atrium", forbidden=["DOWN"])),
        ("i2", "updraft", "small_unsolvable", "a2var-i2-updraft-noup",
         V.variant_of(V.updraft(), "updraft", forbidden=["UP"])),
        ("i3", "cistern", "small_unsolvable", "a2var-i3-cistern-cut",
         V.variant_of(V.cistern(), "cistern", lost_cells=[[3, 5]])),
        ("i4", "atrium", "small_unsolvable", "a2var-i4-atrium-budget",
         V.variant_of(atrium, "atrium", step_limit=i4_budget)),
        ("i5", "quarry", "small_unsolvable", "a2var-i5-quarry-swap",
         V.variant_of(V.quarry(), "quarry",
                      remap={"LEFT": "RIGHT", "RIGHT": "LEFT"})),
        # ---- class (ii): `_large_space()` -- enumeration NEVER run
        ("ii1", "gantry", "large_unsolvable", "a2var-ii1-gantry-sealed",
         V.variant_of(V.comb_room("gantry", 60, None), "gantry",
                      remap={"LEFT": "RIGHT", "RIGHT": "LEFT"})),
        ("ii2", "lattice", "large_unsolvable", "a2var-ii2-lattice-bridge",
         V.variant_of(V.comb_room("lattice", 60, 2), "lattice",
                      lost_cells=[[4, 2]])),
        ("ii3", "spindle", "large_unsolvable", "a2var-ii3-spindle-budget",
         V.variant_of(V.comb_open("spindle", 200, 1, 200), "spindle",
                      step_limit=150)),
        ("ii4", "orchard", "large_unsolvable", "a2var-ii4-orchard-noleft",
         V.variant_of(V.comb_open("orchard", 60, 2, 1), "orchard",
                      forbidden=["LEFT"])),
    ]


def probe(item_key, level_doc):
    level = Level(level_doc)

    t0 = time.perf_counter()
    result = enumerate_states(level, cap=MAX_ENUMERATION)
    enum_seconds = time.perf_counter() - t0

    t1 = time.perf_counter()
    bound = V.subset_lower_bound(level)
    bound_seconds = time.perf_counter() - t1

    t2 = time.perf_counter()
    quotient = V.positional_states(level)
    quotient_seconds = time.perf_counter() - t2

    record = {
        "item": item_key,
        "level_id": level.level_id,
        # what enumerate_states actually reports
        "truncated": result["truncated"],
        "states_visited": result["states"],
        "cap": result["cap"],
        "hit_cap": result["states"] >= result["cap"],
        "solution_found": result["solution"] is not None,
        "solution_length": (None if result["solution"] is None
                            else len(result["solution"])),
        # what the shipped record asserts instead
        "subset_lower_bound_m": bound["m"],
        "subset_lower_bound_2_pow_m": bound["lower_bound"],
        "dippable_switches": bound["dippable_switches"],
        "positional_states": quotient,
        # board facts that explain the numbers
        "switches": len(level.switches),
        "step_limit": level.step_limit,
        "commands": list(level.commands()),
        "hazards": sorted(list(c) for c in level.lost_cells),
    }
    timing = {
        "enumerate_states_seconds": round(enum_seconds, 3),
        "subset_lower_bound_seconds": round(bound_seconds, 3),
        "positional_states_seconds": round(quotient_seconds, 3),
    }
    return record, timing


def main():
    rows = []
    timings = {}
    for item_key, _base, klass, variant_id, doc in levels():
        record, timing = probe(item_key, doc)
        record["class"] = klass
        record["variant_id"] = variant_id
        record["builder"] = ("_small_space" if klass == "small_unsolvable"
                             else "_large_space")
        record["builder_enumerates"] = (klass == "small_unsolvable")
        rows.append(record)
        timings[item_key] = timing
        print("%-4s %-8s %-14s truncated=%-5s states=%7d  2^m=%s  quotient=%d"
              % (item_key, record["level_id"], record["builder"],
                 record["truncated"], record["states_visited"],
                 record["subset_lower_bound_2_pow_m"],
                 record["positional_states"]))

    deterministic = {
        "cap": MAX_ENUMERATION,
        "large_space_threshold": V.LARGE_SPACE_THRESHOLD,
        "note": (
            "`exam/papers/verdict.py`'s `_large_space()` writes "
            "naive_enumeration_feasible=false, enumeration_attempted=false, "
            "enumerated=null and truncated=null onto every class (ii) record "
            "without calling enumerate_states. This file is that call, made at "
            "the shipped cap on the shipped levels, so `truncated` here is "
            "measured where in the shipped record it is a constant. "
            "Anchored by symbol: this note first read `verdict.py:767`, which was "
            "`def _large_space` exactly at base commit 415556f8 and is 130 lines "
            "off by 824b9fb4, and it named `exhaustive_feasible=False` and "
            "`truncated=false` -- the two fields D-EX-028 renamed and nulled in "
            "this same run. So for several commits this artefact contradicted the "
            "rename its own run shipped, while being row 1 of CRITERION.md's "
            "provenance map."),
        "items": rows,
    }
    blob = json.dumps(deterministic, sort_keys=True, separators=(",", ":"))
    document = {
        "deterministic": deterministic,
        "deterministic_sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "timings_nondeterministic": timings,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("\nwrote %s" % OUT)
    print("deterministic sha256 %s" % document["deterministic_sha256"])


if __name__ == "__main__":
    main()
