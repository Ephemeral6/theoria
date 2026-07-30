"""The measurement that licenses the class (ii) bound: a parametric growth curve.

`exam/papers/verdict.py` ships four class (ii) "large space unsolvable" items
(ii1..ii4) whose claim -- *exhaustive enumeration is out of reach* -- rests on
`subset_lower_bound`, a search-free arithmetic argument that returns 2^m.  The
bound is never measured on the boards that ship: they are far too big to
enumerate, which is the whole point.  Extrapolating an arithmetic claim onto a
board nobody has counted is only honest if the same arithmetic has been checked
against a *count* somewhere, so this script counts.

It takes the same comb constructors the shipped items use, shrinks the one
parameter that sets the family size (`corridor_len`, called k here), enumerates
each small member to COMPLETION with `rubrics_verdict.enumerate_states`, and
compares the exact reachable-state count against a closed form.  Nothing is
fitted: the closed forms are stated up front and asserted at every k.  A run
that hits the enumeration cap, or that misses a closed form by one state, fails
loudly rather than writing a curve.

  family    constructor (verdict.py)                shipped as   closed form
  --------  --------------------------------------  -----------  -----------------
  gantry    comb_room(k, None) + remap L<->R         ii1 (k=60)   2*k*4^k
  lattice   comb_room(k, 2) + lost_cells [[4,2]]     ii2 (k=60)   2*k*4^k
  spindle   comb_open(k, 1, k), no step limit        ii3 (k=200)  2*k*4^k
  orchard   comb_open(k, 2, 1) + forbid LEFT         ii4 (k=60)   (2*4^k - 8)/3

with m = 2k for gantry/lattice/spindle and m = 2(k-1) for orchard (LEFT is
forbidden there and the column-1 alcoves are behind the start), so the forms
read 2*k*2^m and (8/3)*(2^m - 1) against the bound the paper actually claims.

SPINDLE CARRIES A CAVEAT AND IT IS NOT A SMALL ONE.  The shipped ii3 applies
`step_limit=150` to a corridor of 200, and the budget -- not the switch count --
is what fixes its m (60, against 400 dippable switches).  The closed form here
is measured on the UNBUDGETED geometry, so it covers ii3's board and not ii3's
item.  `budget_probe` below measures what a budget does to the count, which is:
it replaces the exponential by something much smaller, so the shipped ii3 bound
of 2^60 is the one number in this file that no closed form here extrapolates to.

BYTE-STABILITY.  Determinism is a repo requirement (CLAUDE.md), so the file this
writes is byte-identical across runs except for wall clock.  Precisely:

  * STABLE -- every key of `growth_curve.json` except `timings_seconds`.  That
    includes `stable_sha256`, which is sha256 over `canonical()` of the document
    with `timings_seconds` and `stable_sha256` themselves removed.  Two runs on
    the same commit print and store the same `stable_sha256`.
  * NOT STABLE -- `timings_seconds` alone (rounded to milliseconds, which does
    not make it stable, only readable).  Nothing else in the document is
    derived from a clock, a hash seed, a set iteration order or a path.

Cost.  Dominated by k=9, where three of the four families hold 4,718,592 states:
roughly 100 s and about 2 GB of peak RSS for a whole run on the reference
machine.  `--kmax` trims it; k<=8 runs in about 20 s.

Run:  python exam/runs/20260730T021500Z-V23-large-space/growth_curve.py
      python exam/runs/20260730T021500Z-V23-large-space/growth_curve.py --kmax 8
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam.grading import rubrics_verdict as RV      # noqa: E402
from exam.model import canonical, sha256_text, write_json  # noqa: E402
from exam.papers import verdict as V                # noqa: E402

#: Far above anything this script enumerates.  `MAX_ENUMERATION` (200,000) is a
#: guard on the *marker*; a truncated count is not a measurement, so the cap is
#: lifted here and `truncated` is asserted False at every k instead.
CAP = 10 ** 9

#: k=9 is the last rung that fits in memory on a 32 GB machine.
DEFAULT_KMAX = 9


# ------------------------------------------------------------- the families

def _gantry(k: int) -> Dict[str, Any]:
    """ii1's board: comb_room with a sealed separator, LEFT<->RIGHT relabelled."""
    return V.variant_of(V.comb_room("gantry", k, None), "gantry",
                        remap={"LEFT": "RIGHT", "RIGHT": "LEFT"})


def _lattice(k: int) -> Dict[str, Any]:
    """ii2's board: comb_room with a one-cell bridge, declared lost."""
    return V.variant_of(V.comb_room("lattice", k, 2), "lattice",
                        lost_cells=[[4, 2]])


def _spindle(k: int) -> Dict[str, Any]:
    """ii3's board WITHOUT ii3's budget -- see the module docstring."""
    return V.comb_open("spindle", k, 1, k)


def _orchard(k: int) -> Dict[str, Any]:
    """ii4's board: comb_open starting at column 2, goal at column 1, no LEFT."""
    return V.variant_of(V.comb_open("orchard", k, 2, 1), "orchard",
                        forbidden=["LEFT"])


FAMILIES: List[Dict[str, Any]] = [
    {
        "name": "gantry",
        "shipped_as": "ii1",
        "constructor": "comb_room(level_id, corridor_len=k, bridge_col=None)",
        "operators": "remap_action LEFT<->RIGHT",
        "build": _gantry,
        "kmin": 1,
        "m_form": "2*k",
        "m": lambda k: 2 * k,
        "closed_form": "2*k*4**k  ==  2*k*2**m",
        "states": lambda k: 2 * k * 4 ** k,
        "quotient_form": "3*k",
        "quotient": lambda k: 3 * k,
    },
    {
        "name": "lattice",
        "shipped_as": "ii2",
        "constructor": "comb_room(level_id, corridor_len=k, bridge_col=2)",
        "operators": "observation_loss on [[4, 2]] (the only bridge)",
        "build": _lattice,
        "kmin": 2,          # bridge_col=2 needs a corridor at least 2 wide
        "m_form": "2*k",
        "m": lambda k: 2 * k,
        "closed_form": "2*k*4**k  ==  2*k*2**m",
        "states": lambda k: 2 * k * 4 ** k,
        "quotient_form": "3*k",
        "quotient": lambda k: 3 * k,
    },
    {
        "name": "spindle",
        "shipped_as": "ii3 (geometry only -- ii3 also carries step_limit=150)",
        "constructor": "comb_open(level_id, corridor_len=k, start_col=1, goal_col=k)",
        "operators": "none (the shipped step_limit is NOT applied; see budget_probe)",
        "build": _spindle,
        "kmin": 1,
        "m_form": "2*k",
        "m": lambda k: 2 * k,
        "closed_form": "2*k*4**k  ==  2*k*2**m",
        "states": lambda k: 2 * k * 4 ** k,
        "quotient_form": "3*k",
        "quotient": lambda k: 3 * k,
    },
    {
        "name": "orchard",
        "shipped_as": "ii4",
        "constructor": "comb_open(level_id, corridor_len=k, start_col=2, goal_col=1)",
        "operators": "forbid_action LEFT",
        "build": _orchard,
        "kmin": 2,          # start_col=2 needs a corridor at least 2 wide
        "kmax_bonus": 2,    # this family is cheap; two extra rungs are free
        "m_form": "2*(k-1)",
        "m": lambda k: 2 * (k - 1),
        "closed_form": "(2*4**k - 8)//3  ==  (8*(2**m - 1))//3",
        "states": lambda k: (2 * 4 ** k - 8) // 3,
        "quotient_form": "3*(k-1)",
        "quotient": lambda k: 3 * (k - 1),
    },
]

#: The shipped items, read back off the same constructors the paper calls.
SHIPPED: List[Dict[str, Any]] = [
    {"item": "ii1", "family": "gantry", "k": 60, "build": lambda: _gantry(60)},
    {"item": "ii2", "family": "lattice", "k": 60, "build": lambda: _lattice(60)},
    {"item": "ii3", "family": "spindle", "k": 200,
     "build": lambda: V.variant_of(V.comb_open("spindle", 200, 1, 200),
                                   "spindle", step_limit=150)},
    {"item": "ii4", "family": "orchard", "k": 60, "build": lambda: _orchard(60)},
]


# ------------------------------------------------------------- measurement

def _log10(n: int) -> Optional[float]:
    return None if n <= 0 else round(math.log10(n), 6)


def measure(build: Callable[[int], Dict[str, Any]], k: int,
            timings: Dict[str, float], key: str) -> Dict[str, Any]:
    """One rung: the claimed bound, the exact count, and the quotient.

    `enumerate_states` is the paper's own enumerator, called with the cap lifted
    so that a count is a count.  `truncated` is checked here and again by the
    caller's assertion, because a capped walk that reports a number is the one
    failure mode this whole script exists to rule out.
    """
    doc = build(k)
    level = RV.Level(doc)
    bound = V.subset_lower_bound(level)

    start = time.perf_counter()
    enumerated = RV.enumerate_states(level, cap=CAP)
    elapsed = time.perf_counter() - start
    timings[key] = round(elapsed, 3)

    start = time.perf_counter()
    quotient = V.positional_states(level)
    timings[key + ".quotient"] = round(time.perf_counter() - start, 3)

    if enumerated["truncated"]:
        raise AssertionError(
            "%s k=%d hit the enumeration cap of %d; a truncated walk is not a "
            "measurement and this curve may not be built on one"
            % (doc["level_id"], k, CAP))

    measured = enumerated["states"]
    claimed = bound["lower_bound"]
    return {
        "k": k,
        "m": bound["m"],
        "dippable_switches": bound["dippable_switches"],
        "claimed_lower_bound_2_pow_m": claimed,
        "measured_states": measured,
        "measured_log10": _log10(measured),
        "ratio_measured_over_bound": round(measured / float(claimed), 6),
        "positional_states": quotient,
        "step_limit": level.step_limit,
        "board": {"height": level.height, "width": level.width},
    }


def run_family(family: Dict[str, Any], kmax: int,
               timings: Dict[str, Any]) -> Dict[str, Any]:
    """Every rung of one family, plus the verdict on its closed form.

    The closed form is TESTED, never fitted: `states(k)` is written down in
    `FAMILIES` before anything is enumerated, and a single mismatch at a single
    k marks the family `closed_form_holds: false` and raises.
    """
    name = family["name"]
    per_k: Dict[str, float] = {}
    timings[name] = per_k
    top = kmax + family.get("kmax_bonus", 0)

    rows: List[Dict[str, Any]] = []
    mismatches: List[str] = []
    unsound: List[str] = []
    for k in range(family["kmin"], top + 1):
        row = measure(family["build"], k, per_k, str(k))
        row["bound_is_sound"] = (row["measured_states"]
                                 >= row["claimed_lower_bound_2_pow_m"])
        if not row["bound_is_sound"]:
            unsound.append("k=%d claims %d, only %d exist"
                           % (k, row["claimed_lower_bound_2_pow_m"],
                              row["measured_states"]))

        predicted_m = family["m"](k)
        predicted = family["states"](k)
        predicted_q = family["quotient"](k)
        row["closed_form_states"] = predicted
        row["closed_form_matches"] = row["measured_states"] == predicted
        row["closed_form_m"] = predicted_m
        row["closed_form_m_matches"] = row["m"] == predicted_m
        row["closed_form_positional_states"] = predicted_q
        row["closed_form_positional_matches"] = row["positional_states"] == predicted_q
        if not row["closed_form_matches"]:
            mismatches.append("k=%d measured %d, form gives %d"
                              % (k, row["measured_states"], predicted))
        if not row["closed_form_m_matches"]:
            mismatches.append("k=%d m is %d, form gives %d" % (k, row["m"], predicted_m))
        if not row["closed_form_positional_matches"]:
            mismatches.append("k=%d quotient %d, form gives %d"
                              % (k, row["positional_states"], predicted_q))
        rows.append(row)
        print("  %-8s k=%-3d m=%-3d bound=%-12d measured=%-10d ratio=%-8.3f "
              "quotient=%-4d %6.2fs"
              % (name, row["k"], row["m"], row["claimed_lower_bound_2_pow_m"],
                 row["measured_states"], row["ratio_measured_over_bound"],
                 row["positional_states"], per_k[str(k)]), flush=True)

    counts = [r["measured_states"] for r in rows]
    span = None
    if counts and min(counts) > 0:
        span = round(math.log10(max(counts) / float(min(counts))), 3)

    result = {
        "name": name,
        "shipped_as": family["shipped_as"],
        "constructor": family["constructor"],
        "operators": family["operators"],
        "k_range": [rows[0]["k"], rows[-1]["k"]],
        "m_closed_form": family["m_form"],
        "states_closed_form": family["closed_form"],
        "positional_closed_form": family["quotient_form"],
        "closed_form_holds": not mismatches,
        "closed_form_mismatches": mismatches,
        "bound_is_sound_at_every_k": not unsound,
        "bound_soundness_failures": unsound,
        "orders_of_magnitude_spanned": span,
        "rows": rows,
    }
    if unsound:
        raise AssertionError(
            "%s: subset_lower_bound claims more states than exist -- %s.  The "
            "bound is not a bound." % (name, "; ".join(unsound)))
    if mismatches:
        raise AssertionError(
            "%s: the closed form %s is wrong -- %s.  Fit nothing; correct the "
            "form in FAMILIES and say so."
            % (name, family["closed_form"], "; ".join(mismatches)))
    return result


# ------------------------------------------------------ what ships, and ii3

def shipped_records() -> List[Dict[str, Any]]:
    """k, m and the claimed bound for the four items as the paper builds them.

    No enumeration here -- that is the point of the items.  These are the
    numbers the curve is being extrapolated *to*, recorded so the gap between
    the largest measured k and the shipped k is visible rather than implied.
    """
    out: List[Dict[str, Any]] = []
    for entry in SHIPPED:
        doc = entry["build"]()
        level = RV.Level(doc)
        bound = V.subset_lower_bound(level)
        out.append({
            "item": entry["item"],
            "family": entry["family"],
            "k_corridor_len": entry["k"],
            "m": bound["m"],
            "dippable_switches": bound["dippable_switches"],
            "claimed_lower_bound_2_pow_m": bound["lower_bound"],
            "claimed_lower_bound_log10": _log10(bound["lower_bound"]),
            "step_limit": level.step_limit,
            "positional_states": V.positional_states(level),
            "large_space_threshold": V.LARGE_SPACE_THRESHOLD,
            "over_threshold": bound["lower_bound"] >= V.LARGE_SPACE_THRESHOLD,
        })
    return out


def budget_probe(timings: Dict[str, Any]) -> Dict[str, Any]:
    """What a `step_limit` does to the count -- the ii3-shaped question.

    Two sweeps, both on the spindle geometry:

      * `scaled` -- the shipped budget/corridor ratio (150/199 of the corridor
        walk) carried down to small k.  It degenerates: the budget, not the
        switch count, sets the size, which is exactly why ii3's 2^60 cannot be
        read off the unbudgeted closed form.
      * `sweep_k6` -- corridor fixed at k=6 (49,152 states unbudgeted), budget
        walked from 0 upwards, showing where the budget stops binding and the
        closed form takes over.
    """
    per: Dict[str, float] = {}
    timings["budget_probe"] = per

    scaled: List[Dict[str, Any]] = []
    for k in range(2, 10):
        budget = (150 * (k - 1)) // 199
        doc = V.variant_of(V.comb_open("spindle", k, 1, k), "spindle",
                           step_limit=budget)
        level = RV.Level(doc)
        bound = V.subset_lower_bound(level)
        start = time.perf_counter()
        enumerated = RV.enumerate_states(level, cap=CAP)
        per["scaled.%d" % k] = round(time.perf_counter() - start, 3)
        if enumerated["truncated"]:
            raise AssertionError("budget_probe scaled k=%d hit the cap" % k)
        scaled.append({
            "k": k, "step_limit": budget, "m": bound["m"],
            "claimed_lower_bound_2_pow_m": bound["lower_bound"],
            "measured_states": enumerated["states"],
            "unbudgeted_closed_form": 2 * k * 4 ** k,
            "budget_binds": enumerated["states"] < 2 * k * 4 ** k,
            "bound_is_sound": enumerated["states"] >= bound["lower_bound"],
        })

    sweep: List[Dict[str, Any]] = []
    k = 6
    unbudgeted = 2 * k * 4 ** k
    for budget in list(range(0, 61, 5)) + [None]:
        doc = V.comb_open("spindle", k, 1, k)
        if budget is not None:
            doc = V.variant_of(doc, "spindle", step_limit=budget)
        level = RV.Level(doc)
        bound = V.subset_lower_bound(level)
        start = time.perf_counter()
        enumerated = RV.enumerate_states(level, cap=CAP)
        per["sweep_k6.%s" % budget] = round(time.perf_counter() - start, 3)
        if enumerated["truncated"]:
            raise AssertionError("budget_probe sweep budget=%s hit the cap" % budget)
        sweep.append({
            "step_limit": budget, "m": bound["m"],
            "claimed_lower_bound_2_pow_m": bound["lower_bound"],
            "measured_states": enumerated["states"],
            "budget_binds": enumerated["states"] < unbudgeted,
            "bound_is_sound": enumerated["states"] >= bound["lower_bound"],
        })

    sound = all(row["bound_is_sound"] for row in scaled + sweep)
    if not sound:
        raise AssertionError(
            "budget_probe: subset_lower_bound claims more states than a "
            "budgeted board has.  The budget arm of the bound is not a bound.")

    return {
        "bound_is_sound_at_every_budget": sound,
        "bound_soundness_note": (
            "Every budgeted rung below satisfies measured >= 2^m, so the "
            "budget arm of `subset_lower_bound` (m capped by dist + 2m <= "
            "step_limit) is sound where it was measured -- which is the only "
            "thing this file can say about ii3's 2^60, since no closed form "
            "for a budgeted board is established here."),
        "note": ("A step_limit makes the reachable count a function of the "
                 "budget as well as of k, so the unbudgeted closed form "
                 "2*k*4**k is an upper bound on a budgeted board and not its "
                 "value.  ii3 ships budgeted; ii1, ii2 and ii4 do not."),
        "scaled": {
            "how": "step_limit = floor(150*(k-1)/199), the shipped ratio",
            "rows": scaled,
        },
        "sweep_k6": {
            "how": "corridor_len fixed at 6, step_limit walked 0..60 then None",
            "unbudgeted_states": unbudgeted,
            "rows": sweep,
        },
    }


# -------------------------------------------------------------------- main

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--kmax", type=int, default=DEFAULT_KMAX,
                        help="largest corridor_len to enumerate (default %d)"
                             % DEFAULT_KMAX)
    args = parser.parse_args(argv)

    wall = time.perf_counter()
    timings: Dict[str, Any] = {}

    print("shipped items (no enumeration -- that is the claim under test):")
    shipped = shipped_records()
    for record in shipped:
        print("  %-4s %-8s k=%-4d m=%-4d bound=2^%-4d = 1e%.2f  quotient=%d"
              % (record["item"], record["family"], record["k_corridor_len"],
                 record["m"], record["m"], record["claimed_lower_bound_log10"],
                 record["positional_states"]), flush=True)

    print("growth curve (enumerated to completion, cap %d):" % CAP)
    families = [run_family(family, args.kmax, timings) for family in FAMILIES]

    print("budget probe:", flush=True)
    probe = budget_probe(timings)

    counts = [row["measured_states"]
              for family in families for row in family["rows"]]
    verified_span = round(math.log10(max(counts) / float(min(counts))), 3)

    doc: Dict[str, Any] = {
        "schema": "verdict.large_space.growth_curve/1",
        "what": ("Parametric growth curve for the comb families behind the "
                 "class (ii) items of exam/papers/verdict.py.  Each rung is "
                 "enumerated to completion and matched against a closed form "
                 "stated in advance; nothing is fitted."),
        "source_module": "exam/papers/verdict.py",
        "enumerator": "exam/grading/rubrics_verdict.py::enumerate_states",
        "bound_under_test": "exam/papers/verdict.py::subset_lower_bound (2**m)",
        "enumeration_cap": CAP,
        "marker_cap_for_reference": RV.MAX_ENUMERATION,
        "kmax_requested": args.kmax,
        "stable_fields": ("every key except `timings_seconds`; `stable_sha256` "
                          "is sha256 over canonical() of this document with "
                          "`timings_seconds` and `stable_sha256` removed"),
        "unstable_fields": ["timings_seconds"],
        "shipped_items": shipped,
        "families": families,
        "budget_probe": probe,
        "verified_orders_of_magnitude": verified_span,
        "closed_forms_confirmed": {
            family["name"]: family["states_closed_form"] for family in families
        },
        "all_closed_forms_hold": all(f["closed_form_holds"] for f in families),
        "bound_sound_everywhere_measured": (
            all(f["bound_is_sound_at_every_k"] for f in families)
            and probe["bound_is_sound_at_every_budget"]),
        "what_this_licenses": (
            "The exponent, not the shipped number.  Over %.2f orders of "
            "magnitude of measured state count the exact reachable set equals "
            "2*k*2^m (gantry, lattice, spindle) or (8/3)*(2^m - 1) (orchard) at "
            "every single k with no fitting, so `subset_lower_bound`'s 2^m is "
            "confirmed to be a genuine lower bound on these families and a "
            "loose one -- the truth exceeds it by a factor of 2k, which grows. "
            "Extrapolation to the shipped k is licensed by the closed form's "
            "exactness at every measured k, not by the measurement reaching "
            "the shipped k, which it never can."
            % verified_span),
        "what_this_does_not_license": [
            "It does not enumerate the shipped boards.  The largest measured "
            "state count is about 4.7e6; ii1/ii2 claim 2^120 = 1.3e36 and ii4 "
            "claims 2^118 = 3.3e35, so roughly 29 orders of magnitude separate "
            "the last rung from the shipped bound and no count crosses it.",
            "It does not cover ii3.  ii3 ships with step_limit=150 and its m=60 "
            "is set by that budget, not by its 400 switches; the closed form "
            "here is measured on the unbudgeted spindle geometry.  See "
            "budget_probe: a binding budget puts the true count far below "
            "2*k*4^k, so the unbudgeted form must not be read onto ii3.",
            "It says nothing about `subset_lower_bound` on boards outside these "
            "four families.  The lane premise it asserts (D-EX-021) is a "
            "property of the comb geometry; a different board can defeat it, "
            "which is what the AssertionError inside the function is for.",
            "It does not make enumeration infeasible as a matter of proof.  "
            "The measured curve is a statement about the reachable set's size, "
            "and `positional_states` -- 3k, tiny -- shows a solver that "
            "quotients by the latch mask faces nothing of the sort.  The "
            "quotient is not a sound abstraction here (D-EX-022), but the "
            "large-space claim is about naive enumeration and only that.",
        ],
    }

    timings["total_seconds"] = round(time.perf_counter() - wall, 3)
    stable = {key: value for key, value in doc.items()
              if key not in ("timings_seconds", "stable_sha256")}
    doc["stable_sha256"] = sha256_text(canonical(stable))
    doc["timings_seconds"] = timings

    path = os.path.join(HERE, "growth_curve.json")
    write_json(path, doc)

    print("closed forms hold at every k: %s" % doc["all_closed_forms_hold"])
    print("verified over %.2f orders of magnitude of measured state count"
          % verified_span)
    print("stable_sha256 %s" % doc["stable_sha256"])
    print("total %.2fs -> %s" % (timings["total_seconds"], path))
    return 0 if doc["all_closed_forms_hold"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
