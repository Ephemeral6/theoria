"""Take the measurement `_large_space()` never takes -- on every record it writes.

`exam/papers/verdict.py`'s `_large_space()` stamps every truth record it builds
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
also runs the class (i) levels as a contrast column, so the two can be read side
by side.

**Scoped by the record, not by the class -- round five's F5-14.**  The earlier
version of this script rebuilt nine levels from a hardcoded literal list: i1-i5
and ii1-ii4.  `_large_space` is called by *seven* items, not four -- the three
`solvable_hard` lattice items (iii6, iii7, iii8) carry the same
`naive_enumeration_feasible: False` claim, and a probe scoped to
`large_unsolvable` left three shipped records with no criterion-(b) evidence
except a test assertion.  CRITERION.md's provenance map had to be annotated
"four of the seven records it speaks for" to stay honest.  So the list is gone:
the records are now *asked for* rather than restated, by calling
`verdict.build()` and filtering on the field that defines the claim.  That is
the same filter `test_class_ii_levels_actually_truncate_the_enumerator` uses,
and the same count it asserts.

Calling `build()` has a side effect the old docstring cited as the reason not to
call it: it writes the variant specs under `exam/artifacts/variant_specs/`.
Those 17 files are tracked and `build()` is documented deterministic ("Two calls
produce byte-identical sheets and specs"), and `exam/tests/` calls it on every
run, so the rewrite is byte-identical and leaves the tree clean.  The gain is
that the levels probed here are the shipped level blobs -- `truth["level_blob"]`
-- rather than reconstructions that have to be kept in step with the builder by
hand.

Bounding.  Every enumeration here is capped at `rubrics_verdict.MAX_ENUMERATION`,
the same constant the territory already uses; no second budget is invented.  The
cap is what makes this script terminate on a board whose bound is 2^120: BFS
stops at 200,000 distinct states whatever the space behind them.  A record that
cannot be measured is reported as `measured: false` with an
`unmeasured_reason` and the numbers that show why -- never omitted, and never
replaced by a guess.  `deterministic.status` says so in one line at the top.

Determinism.  Everything under `"deterministic"` is a pure function of the
repo: the levels come from `build()`'s own truth records, and `enumerate_states`
is a deterministic BFS with a fixed cap.  Wall-clock seconds are the only
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
    MAX_ENUMERATION, Level, enumerate_states,
)
from exam.papers import verdict as V              # noqa: E402

OUT = os.path.join(HERE, "enumeration_probe.json")

#: What `test_class_ii_levels_actually_truncate_the_enumerator` asserts:
#: `assert len(items) == 7, "expected 4 class (ii) + 3 solvable_hard"`.  Held
#: here as an expectation to *check*, not a list to iterate -- the rows come
#: from `build()`.
EXPECTED_CRITERION_B_RECORDS = 7

#: The class whose records `_small_space` builds and which therefore carry the
#: opposite of the criterion-(b) claim.  Kept as the contrast column.
CONTRAST_CLASS = "small_unsolvable"


def _item_key(variant_id: str) -> str:
    """`a2var-iii6-lattice-safe` -> `iii6`.

    The paper's opaque `item_id` (`vq-...`) is a hash and says nothing to a
    reader; the short key is the one RUN_STATE, CRITERION.md and round five all
    use.  It is read off the shipped `variant_id` rather than assigned here, so
    it cannot drift from the record it names.
    """
    parts = variant_id.split("-")
    if len(parts) < 2 or parts[0] != "a2var":
        raise AssertionError("unexpected variant_id shape: %r" % variant_id)
    return parts[1]


def records():
    """Ask the builder which records criterion (b) speaks for.

    Returns `(criterion_b, contrast)`, both lists of `exam.model.Item`, sorted
    by short key so the artefact's row order is stable under `build()`'s
    hash-keyed shuffle.

    `criterion_b` is exactly the filter the test uses:
    `truth["state_space"]["naive_enumeration_feasible"] is False`.  That field
    *is* the claim -- it is what `_large_space` writes and `_small_space` does
    not -- so filtering on it cannot miss a record the way filtering on
    `class == "large_unsolvable"` did.
    """
    paper = V.build()
    criterion_b = [it for it in paper.items
                   if it.truth["state_space"]["naive_enumeration_feasible"]
                   is False]
    contrast = [it for it in paper.items
                if it.truth["class"] == CONTRAST_CLASS]
    key = lambda it: _item_key(it.truth["spec"]["variant_id"])   # noqa: E731
    order = lambda it: (len(key(it)), key(it))                   # noqa: E731
    return sorted(criterion_b, key=order), sorted(contrast, key=order)


def probe(item, criterion_b_applies):
    """Measure one shipped record.  Bounded by `MAX_ENUMERATION`, or unmeasured.

    Nothing here runs unbounded: `enumerate_states` is always called with
    `cap=MAX_ENUMERATION`, so it visits at most 200,000 distinct states however
    large the space is.  This is the bound whose absence made an earlier version
    of this ticket's probe try to walk a ~4.4e13-state board.  If a measurement
    raises anyway, the row is kept and marked `measured: false` with the
    exception on it -- the one thing that must not happen is a missing row,
    because a missing row is what F5-14 was.
    """
    level_doc = json.loads(item.truth["level_blob"])
    level = Level(level_doc)
    shipped = item.truth["state_space"]
    variant_id = item.truth["spec"]["variant_id"]

    record = {
        "item": _item_key(variant_id),
        "item_id": item.item_id,
        "level_id": level.level_id,
        "class": item.truth["class"],
        "variant_id": variant_id,
        "builder": ("_small_space" if shipped["naive_enumeration_feasible"]
                    else "_large_space"),
        "builder_enumerates": bool(shipped["naive_enumeration_feasible"]),
        # Does the criterion-(b) claim -- "the reference enumerator truncates at
        # the shipped cap on this level" -- apply to this record at all?
        "criterion_b_applies": criterion_b_applies,
        # The bound, named rather than inlined, so a reader can see there is one.
        "measurement_bound": "rubrics_verdict.MAX_ENUMERATION",
        "cap": MAX_ENUMERATION,
        # Set below.  Present on every row whatever happens.
        "measured": False,
        "unmeasured_reason": None,
        "truncated": None,
        "states_visited": None,
        "hit_cap": None,
        "solution_found": None,
        "solution_length": None,
        "criterion_b_holds": None,
        "criterion_b_conjuncts": None,
        # what the shipped record asserts instead, recomputed here
        "subset_lower_bound_m": None,
        "subset_lower_bound_2_pow_m": None,
        "dippable_switches": None,
        "positional_states": None,
        # board facts that explain the numbers
        "switches": len(level.switches),
        "step_limit": level.step_limit,
        "commands": list(level.commands()),
        "hazards": sorted(list(c) for c in level.lost_cells),
        # and what the shipped record says, so the two sit side by side
        "shipped_record": {
            "naive_enumeration_feasible": shipped["naive_enumeration_feasible"],
            "enumeration_attempted": shipped["enumeration_attempted"],
            "enumerated": shipped["enumerated"],
            "truncated": shipped["truncated"],
            "lower_bound": shipped["lower_bound"],
            "m": shipped.get("m"),
            "positional_states": shipped["positional_states"],
        },
    }
    timing = {
        "enumerate_states_seconds": None,
        "subset_lower_bound_seconds": None,
        "positional_states_seconds": None,
    }

    try:
        t1 = time.perf_counter()
        bound = V.subset_lower_bound(level)
        timing["subset_lower_bound_seconds"] = round(time.perf_counter() - t1, 3)
        record["subset_lower_bound_m"] = bound["m"]
        record["subset_lower_bound_2_pow_m"] = bound["lower_bound"]
        record["dippable_switches"] = bound["dippable_switches"]

        t2 = time.perf_counter()
        record["positional_states"] = V.positional_states(level)
        timing["positional_states_seconds"] = round(time.perf_counter() - t2, 3)

        t0 = time.perf_counter()
        result = enumerate_states(level, cap=MAX_ENUMERATION)
        timing["enumerate_states_seconds"] = round(time.perf_counter() - t0, 3)
    except (AssertionError, MemoryError, RecursionError, OverflowError,
            ValueError, KeyError) as exc:
        # Not a measurement, and not pretended to be one.  The numbers already
        # gathered stay on the row, because they are the numbers that show why.
        record["unmeasured_reason"] = "%s: %s" % (type(exc).__name__, exc)
        return record, timing

    conjuncts = {
        # criterion (b) proper: the enumerator ran out of room.
        "truncated": result["truncated"] is True,
        "states_reached_cap": result["states"] >= result["cap"],
        # It must run out of room, not run into the answer: a record whose plan
        # turned up inside the cap would mean the naive method does work here.
        "no_solution_inside_cap": result["solution"] is None,
    }
    record.update({
        "measured": True,
        "truncated": result["truncated"],
        "states_visited": result["states"],
        "cap": result["cap"],
        "hit_cap": result["states"] >= result["cap"],
        "solution_found": result["solution"] is not None,
        "solution_length": (None if result["solution"] is None
                            else len(result["solution"])),
        "criterion_b_conjuncts": conjuncts,
        "criterion_b_holds": (all(conjuncts.values()) if criterion_b_applies
                              else None),
    })
    return record, timing


def main():
    criterion_b_items, contrast_items = records()

    rows = []
    timings = {}
    for item in criterion_b_items:
        record, timing = probe(item, criterion_b_applies=True)
        rows.append(record)
        timings[record["item"]] = timing
    for item in contrast_items:
        record, timing = probe(item, criterion_b_applies=False)
        rows.append(record)
        timings[record["item"]] = timing

    for record in rows:
        print("%-5s %-8s %-14s %-14s measured=%-5s truncated=%-5s "
              "states=%7s  2^m=%s  quotient=%s  (b)=%s"
              % (record["item"], record["level_id"], record["class"],
                 record["builder"], record["measured"], record["truncated"],
                 record["states_visited"],
                 record["subset_lower_bound_2_pow_m"],
                 record["positional_states"], record["criterion_b_holds"]))

    covered = [r for r in rows if r["criterion_b_applies"]]
    unmeasured = [{"item": r["item"], "variant_id": r["variant_id"],
                   "reason": r["unmeasured_reason"],
                   "subset_lower_bound_2_pow_m": r["subset_lower_bound_2_pow_m"],
                   "cap": r["cap"]}
                  for r in covered if not r["measured"]]
    failed = [r["item"] for r in covered
              if r["measured"] and r["criterion_b_holds"] is not True]
    by_class = {}
    for r in covered:
        by_class[r["class"]] = by_class.get(r["class"], 0) + 1

    if unmeasured:
        status = ("UNMEASURED: %d of %d criterion-(b) records could not be "
                  "measured; see coverage.unmeasured"
                  % (len(unmeasured), len(covered)))
    elif failed:
        status = ("CRITERION (b) DOES NOT HOLD for %s: the enumerator did not "
                  "truncate at the cap, so these shipped records' stated "
                  "evidence is absent" % ", ".join(failed))
    elif len(covered) != EXPECTED_CRITERION_B_RECORDS:
        status = ("COUNT MISMATCH: build() yielded %d criterion-(b) records, "
                  "not the %d test_verdict.py asserts"
                  % (len(covered), EXPECTED_CRITERION_B_RECORDS))
    else:
        status = ("OK: criterion (b) measured and holding on all %d records "
                  "that claim it" % len(covered))

    coverage = {
        "source": ("exam.papers.verdict.build(), filtered on "
                   "truth['state_space']['naive_enumeration_feasible'] is "
                   "False -- the same filter and count as "
                   "test_class_ii_levels_actually_truncate_the_enumerator"),
        "criterion_b_records_expected": EXPECTED_CRITERION_B_RECORDS,
        "criterion_b_records_probed": len(covered),
        "criterion_b_records_measured": len(covered) - len(unmeasured),
        "criterion_b_records_holding": len(
            [r for r in covered if r["criterion_b_holds"] is True]),
        "criterion_b_records_by_class": dict(sorted(by_class.items())),
        "unmeasured": unmeasured,
        "criterion_b_failures": failed,
        "contrast_rows": len(rows) - len(covered),
        "contrast_class": CONTRAST_CLASS,
        "superseded_coverage": ("four of seven (ii1-ii4 only); the three "
                               "solvable_hard records iii6/iii7/iii8 were "
                               "absent -- round five F5-14"),
    }

    deterministic = {
        "status": status,
        "cap": MAX_ENUMERATION,
        "large_space_threshold": V.LARGE_SPACE_THRESHOLD,
        "note": (
            "`exam/papers/verdict.py`'s `_large_space()` writes "
            "naive_enumeration_feasible=false, enumeration_attempted=false, "
            "enumerated=null and truncated=null onto every record it builds "
            "without calling enumerate_states. This file is that call, made at "
            "the shipped cap on the shipped levels, so `truncated` here is "
            "measured where in the shipped record it is a constant. "
            "Scope: all seven records `_large_space` writes, not the four "
            "class (ii) ones. `_large_space` is also called by the three "
            "`solvable_hard` lattice items iii6/iii7/iii8, and until this "
            "widening they had no criterion-(b) artefact -- their evidence was "
            "`test_class_ii_levels_actually_truncate_the_enumerator` alone, "
            "which is why CRITERION.md's provenance map carried the annotation "
            "'four of the seven records it speaks for' (round five F5-14). The "
            "rows are no longer a literal list of reconstructed levels: "
            "`build()` is called and its items are filtered on "
            "`state_space.naive_enumeration_feasible is False`, so the levels "
            "probed are the shipped `truth.level_blob`s and the row set cannot "
            "fall behind the builder. Every enumeration is capped at "
            "`rubrics_verdict.MAX_ENUMERATION`; a record that could not be "
            "measured would appear with `measured: false` and an "
            "`unmeasured_reason` rather than be dropped, and "
            "`deterministic.status` states the outcome in one line. "
            "Anchored by symbol: this note first read `verdict.py:767`, which was "
            "`def _large_space` exactly at base commit 415556f8 and is 130 lines "
            "off by 824b9fb4, and it named `exhaustive_feasible=False` and "
            "`truncated=false` -- the two fields D-EX-028 renamed and nulled in "
            "this same run. So for several commits this artefact contradicted the "
            "rename its own run shipped, while being row 1 of CRITERION.md's "
            "provenance map."),
        "coverage": coverage,
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
    print("status: %s" % status)
    if not status.startswith("OK:"):
        # The artefact is written first: the evidence lands on disk even when
        # the run is a failure, and the failure is not silent.
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
