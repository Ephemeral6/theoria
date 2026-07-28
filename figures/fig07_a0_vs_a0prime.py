"""fig07_a0_vs_a0prime -- the A0 vs A0' coverage-accuracy contrast.

The claim, in one sentence: **coverage went down, accuracy went up, because what
was seen could be seen again.** A0's mechanism is a Button -- a latch, pressable
once. A0''s is a Switch -- a toggle, re-witnessable. A0''s explorer was then
weakened on purpose to 40% of A0's walk, and A0' still shipped a manual with no
errors while A0, which saw almost everything, shipped one wrong in three places.
`cold-start-a0/prime/A0P_REPORT.md` section 1 states the thesis this plate draws:

    The variable is not how much was seen. It is whether what was seen could be
    seen **again**.

**Which pair is A0'.** `figures/PLAN.md` section 2 concluded that A0' is the
battery run `a0-spike`. That is wrong, and this module does not implement it.
`a0-spike/` is a *separate* A0 cold start, on a *different* world, run by the
*other track* (`papers/phase1-workshop/sections/03_a0.md` 3.5: "Its numbers are
not comparable with `cold-start-a0/`'s and are not merged with them here"). The
real A0' is `cold-start-a0/prime/` -- same track, same instance, deliberately
constructed as the controlled variant, and named as A0' by
`monitor/prompts/P-16-workshop-paper.md`. `a0-spike` still appears on this plate,
in panel B only, on the far side of a divider, because the one thing it is good
for here is showing what a K2 of 1.000 costs in denominator.

What this script does, in order:

1. reads three declared sources through ``sources`` -- never a raw path;
2. derives every drawn quantity, and records the derivation in ``notes``. Two
   numbers are *computed* rather than read, and both are cross-checked against a
   stored value: A0's coverage (``pairs - held_out_pairs``, because the held-out
   set is defined as the pairs the trajectory could never contain, so its
   complement is the covered set) and A0''s truncation ratio (``budget`` from the
   prime trace over ``steps`` from the battery -- 110/275 = 40.0%, which is the
   report's "truncated at 40%" arrived at from two artefacts);
3. writes ``csv/fig07_a0_vs_a0prime.csv`` -- every number on the plate, checkable
   without reading plotting code, with the sampling frames in ``frame_note``;
4. renders one figure per theme, two themes x svg+png = 4 images.

Six things must survive into the picture, and all six are drawn rather than
captioned:

* **the analytic-entailment banner.** `03_a0.md` 3.3: "n = 1 per arm, on worlds
  built by the same instance that theorized them" covers sampling error; the
  sharper objection is that A0''s toggle was *designed* so that every
  direction-by-polarity combination would have its own witness, so the
  adjudication rule mechanically admits what it mechanically rejected in A0. The
  outcome follows from the construction. This contrast **demonstrates the
  mechanism rather than tests it**. Banner, not footnote;
* **"identical except" is a false description and is not used.** Panel C puts all
  eight differences on the plate and shades the two that were advertised;
* **no K2 without its denominator.** Panel B never shows A0's 0.000 without
  ``n = 3`` and a0-spike's 1.000 without ``n = 39960``. `battery/REPORT_V1.md`:
  "Both are `K2`, and comparing them directly would be wrong.";
* **A0' has no held-out set**, so its K2 is *absent*. Drawn with
  ``theme.ABSENCE['not-applicable']``, never as a zero;
* **A0' has no battery run at all** -- ``battery/adapters/`` carries ``a0.py``,
  ``a0_spike.py``, ``a2.py`` and no prime adapter, and the absence is detected
  here by looking for a prime run in the spectrum rather than asserted. The gap
  is drawn as a gap;
* **both worlds are self-built and adjudicated by the same instance**
  (`A0P_REPORT.md` 5.5: "The seal has the same hole as A0's").

One quantity this figure wants and cannot have: A0's executable-probe count.
`A0P_REPORT.md` section 1 reports 0 of 22 designed, but that count lives in
``cold-start-a0/artifacts/engines_report.json``, which is not in
``figures/sources.py``. Adding an undeclared source would make it unhashed, so
the cell is drawn as *not readable from a declared source* rather than as a 0 --
the same rule that forbids drawing A0''s missing held-out set as a zero.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

import sources  # noqa: E402
import theme  # noqa: E402

NAME = "fig07_a0_vs_a0prime"

#: Colour slots, fixed. Three series are visible pairwise on this plate (A0,
#: A0', a0-spike), which is exactly ``theme.MAX_ALLPAIRS_SERIES``. Everything
#: else on the plate is an absence and wears no colour at all -- which is the
#: point: a gap is not a fourth series.
SERIES: tuple[str, ...] = ("A0", "A0'", "a0-spike")

#: The four battery runs panel B ranges over, in a declared order. ``None`` in
#: the second slot is A0', which has no battery run -- see the module docstring.
BATTERY_KEYS: tuple[str | None, ...] = ("a0-base", None, "a0-no-button", "a0-spike")

#: Tolerance for "the recomputed ratio agrees with the stored one". The
#: artefacts store accuracy rounded to six places; agree/pairs is exact.
RATIO_TOLERANCE = 1e-6

CSV_HEADER = (
    "arm",
    "world",
    "run",
    "metric",
    "value",
    "status",
    "numerator",
    "denominator",
    "n_states",
    "frame_note",
)

#: Statuses used in the CSV. Each one has a distinct drawn encoding, and none of
#: them is ever rendered as a zero.
ST_OK = "ok"
ST_NO_HELD_OUT = "absent-no-held-out-set"
ST_INSUFFICIENT = "insufficient-data"
ST_NO_BATTERY = "absent-no-battery-adapter"
ST_UNREGISTERED = "absent-not-in-source-registry"
ST_PROSE = "prose-only-not-in-source-registry"

_A0_WORLD = "cold-start-a0"
_A0P_WORLD = "cold-start-a0/prime"
_SPIKE_WORLD = "a0-spike (other track, different world)"


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------


def _ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        raise ZeroDivisionError("a ratio with a zero denominator is not a value")
    return numerator / denominator


def extract() -> tuple[dict, list[str]]:
    """Every drawn quantity, plus notes. No plotting, no writing."""
    notes: list[str] = []

    score = sources.read_json("a0_score_vs_truth")
    prime = sources.read_json("a0prime_report")
    spectrum = sources.read_json("capability_spectrum")

    # ---- A0 ---------------------------------------------------------------
    beh = score["base"]["behavioural"]
    held = score["base"]["held_out"]
    a0_pairs = int(beh["pairs"])
    a0_agree = int(beh["agree"])
    a0_disagree = int(beh["disagree"])
    a0_states = int(beh["reachable_states"])
    a0_held_pairs = int(held["held_out_pairs"])
    a0_held_acc = float(held["accuracy"])
    a0_held_agree = int(held["agree"])

    # Coverage is derived, not stored: the held-out set is defined as the pairs
    # the trajectory could never contain, so its complement is the covered set.
    a0_covered = a0_pairs - a0_held_pairs
    a0_coverage = _ratio(a0_covered, a0_pairs)
    a0_accuracy = _ratio(a0_agree, a0_pairs)
    if abs(a0_accuracy - float(beh["accuracy"])) > RATIO_TOLERANCE:
        raise ValueError(
            f"A0 accuracy {a0_accuracy!r} recomputed from {a0_agree}/{a0_pairs} "
            f"disagrees with the stored {beh['accuracy']!r} beyond tolerance"
        )

    # The coincidence worth naming: A0's covered count and its agreement count
    # are both 233, because the three uncovered pairs are exactly the three the
    # manual gets wrong. Checked here rather than asserted.
    a0_errors_are_the_gaps = (
        a0_covered == a0_agree
        and a0_disagree == a0_held_pairs
        and sorted(map(repr, beh["examples"])) == sorted(map(repr, held["examples"]))
    )
    a0_error_actions = sorted({str(e["action"]) for e in held["examples"]})

    # Rules in A0's manual: the structural table names one manual clause per
    # ground rule. Rows whose clause is null (entailed by the frame axiom) or
    # "<missing>" (rejected at R-05) are not clauses in the file.
    structural = score["structural"]
    a0_rules = sum(
        1
        for row in structural
        if row.get("manual_clause") not in (None, "<missing>")
    )
    a0_press_missing = sorted(
        str(row["ground_rule"]) for row in structural if row.get("manual_clause") == "<missing>"
    )

    variant = score["variant"]["behavioural"]
    a0v_pairs = int(variant["pairs"])
    a0v_agree = int(variant["agree"])
    a0v_states = int(variant["reachable_states"])

    # ---- A0' --------------------------------------------------------------
    trace = prime["trace"]["a0p-base"]
    run_a = prime["run_a"]
    run_b = prime["run_b"]
    engines = prime["engines"]

    a0p_pairs = int(trace["state_action_pairs"])
    a0p_covered = int(trace["covered_pairs"])
    a0p_states = int(trace["reachable_states"])
    a0p_budget = int(trace["budget"])
    a0p_coverage = _ratio(a0p_covered, a0p_pairs)
    if trace["coverage"] != f"{a0p_covered}/{a0p_pairs}":
        raise ValueError(
            f"A0' coverage string {trace['coverage']!r} disagrees with "
            f"{a0p_covered}/{a0p_pairs}"
        )

    a0p_agree = int(run_a["score_vs_truth"]["agree"])
    a0p_score_pairs = int(run_a["score_vs_truth"]["pairs"])
    a0p_accuracy = _ratio(a0p_agree, a0p_score_pairs)
    if abs(a0p_accuracy - float(run_a["score_vs_truth"]["accuracy"])) > RATIO_TOLERANCE:
        raise ValueError("A0' run A accuracy disagrees with its own agree/pairs")
    a0p_rules = int(run_a["coverage_probes"]["rules"])
    a0p_untested = len(run_a["coverage_probes"]["untested_rules"])
    a0p_revisions = int(run_a["revisions"])
    a0p_objects = len(engines["tracks"])
    a0p_probes_exec = int(engines["executable_probes"])
    a0p_probes_total = int(engines["total_probes"])

    # The toggle, evidenced rather than quoted: one witness per direction x
    # polarity is exactly what "re-witnessable" buys, and it is in the trace.
    toggle_keys = sorted(k for k in trace["mechanisms_witnessed"] if k.startswith("toggle_"))
    toggle_witnesses = {k: int(trace["mechanisms_witnessed"][k]) for k in toggle_keys}

    # ---- Run B ------------------------------------------------------------
    rb_before_agree = int(run_b["score_vs_truth_before"]["agree"])
    rb_before_pairs = int(run_b["score_vs_truth_before"]["pairs"])
    rb_before = _ratio(rb_before_agree, rb_before_pairs)
    rb_after_agree = int(run_b["score_vs_truth_after"]["agree"])
    rb_after_pairs = int(run_b["score_vs_truth_after"]["pairs"])
    rb_after = _ratio(rb_after_agree, rb_after_pairs)
    if abs(rb_before - float(run_b["score_vs_truth_before"]["accuracy"])) > RATIO_TOLERANCE:
        raise ValueError("A0' run B accuracy_before disagrees with its own agree/pairs")
    rb_refuted = sorted(str(r) for r in run_b["coverage_probes"]["refuted"])
    rb_untested = sorted(str(r) for r in run_b["coverage_probes"]["untested_rules"])
    rb_probes_run = int(run_b["coverage_probes"]["probes_run"])
    rb_revisions = int(run_b["revisions"])
    rb_lean = str(run_b["certify_lean"])
    rb_replay_is_bare_bool = isinstance(run_b["certify_cheap"], bool)

    # ---- battery ----------------------------------------------------------
    runs = spectrum["runs"]
    prime_runs = sorted(r for r in runs if "prime" in r)
    if prime_runs:
        raise ValueError(
            "the capability spectrum now carries a prime run "
            f"({prime_runs}); panel B's declared gap is stale and must be redrawn"
        )
    a0_steps = int(runs["a0-base"]["steps"])
    truncation = _ratio(a0p_budget, a0_steps)

    battery: dict[str, dict] = {}
    for key in sorted(k for k in BATTERY_KEYS if k is not None):
        metrics = runs[key]["metrics"]
        battery[key] = {}
        for metric in ("K1", "K2", "K4"):
            cell = metrics[metric]
            support = cell.get("support") or {}
            battery[key][metric] = {
                "value": cell.get("value"),
                "status": str(cell.get("status")),
                "agree": support.get("agree"),
                "pairs": support.get("pairs"),
                "annotated": support.get("annotated"),
                "unannotated": support.get("unannotated"),
                "min_witnesses": support.get("min_witnesses"),
                "frame": str(support.get("frame") or cell.get("reason") or ""),
            }

    data = {
        "a0": {
            "pairs": a0_pairs,
            "agree": a0_agree,
            "disagree": a0_disagree,
            "states": a0_states,
            "covered": a0_covered,
            "coverage": a0_coverage,
            "accuracy": a0_accuracy,
            "held_pairs": a0_held_pairs,
            "held_agree": a0_held_agree,
            "held_accuracy": a0_held_acc,
            "held_frame": battery["a0-base"]["K2"]["frame"],
            "rules": a0_rules,
            "steps": a0_steps,
            "press_missing": a0_press_missing,
            "error_actions": a0_error_actions,
            "errors_are_the_gaps": a0_errors_are_the_gaps,
            "variant_pairs": a0v_pairs,
            "variant_agree": a0v_agree,
            "variant_states": a0v_states,
        },
        "a0p": {
            "pairs": a0p_pairs,
            "covered": a0p_covered,
            "coverage": a0p_coverage,
            "states": a0p_states,
            "budget": a0p_budget,
            "truncation": truncation,
            "agree": a0p_agree,
            "score_pairs": a0p_score_pairs,
            "accuracy": a0p_accuracy,
            "rules": a0p_rules,
            "untested_rules": a0p_untested,
            "revisions": a0p_revisions,
            "objects": a0p_objects,
            "probes_exec": a0p_probes_exec,
            "probes_total": a0p_probes_total,
            "toggle_witnesses": toggle_witnesses,
        },
        "run_b": {
            "before": rb_before,
            "before_agree": rb_before_agree,
            "before_pairs": rb_before_pairs,
            "after": rb_after,
            "after_agree": rb_after_agree,
            "after_pairs": rb_after_pairs,
            "refuted": rb_refuted,
            "untested": rb_untested,
            "probes_run": rb_probes_run,
            "revisions": rb_revisions,
            "lean": rb_lean,
            "replay_is_bare_bool": rb_replay_is_bare_bool,
        },
        "battery": battery,
    }

    # ---- notes: every derivation, named ------------------------------------
    notes.append(
        f"A0' is cold-start-a0/prime, NOT a0-spike. PLAN.md section 2 identified "
        "a0-spike as A0'; a0-spike is a different world run by the other track "
        "(papers/phase1-workshop/sections/03_a0.md 3.5) and appears here only in "
        "panel B, behind a divider, as the denominator contrast."
    )
    notes.append(
        f"A0 coverage derived as pairs - held_out_pairs = {a0_pairs} - {a0_held_pairs} "
        f"= {a0_covered}; {a0_covered}/{a0_pairs} = {a0_coverage:.6f}. The held-out set "
        "is the pairs the trajectory could never contain, so its complement is covered."
    )
    notes.append(
        f"A0' coverage read from trace.a0p-base: {a0p_covered}/{a0p_pairs} = "
        f"{a0p_coverage:.6f}; the artefact's own coverage string agrees."
    )
    notes.append(
        f"truncation derived across two artefacts: A0' budget {a0p_budget} transitions "
        f"over A0's {a0_steps} steps (battery runs.a0-base.steps) = {truncation * 100:.1f}% "
        "-- A0P_REPORT section 1's 'truncated at 40%', arrived at independently."
    )
    if a0_errors_are_the_gaps:
        notes.append(
            f"cross-check holds: A0's covered count and agreement count are both "
            f"{a0_agree}, because the {a0_disagree} uncovered pairs are exactly the "
            f"{a0_disagree} the manual gets wrong -- pressing the Button from "
            + "/".join(a0_error_actions)
            + " (THEORIZE_LOG R-05 named them before the score existed)."
        )
    else:
        notes.append(
            "cross-check FAILED, reported not reconciled: A0's held-out examples are "
            "no longer identical to its behavioural disagreements, so 'the errors are "
            "the gaps' no longer follows from the artefact."
        )
    notes.append(
        f"A0 manual rules counted from score_vs_truth.structural (clauses that are "
        f"neither null nor '<missing>'): {a0_rules}. Rejected at R-05 and still "
        f"missing: {', '.join(a0_press_missing)}."
    )
    notes.append(
        f"A0' toggle witnesses, one per direction x polarity: "
        f"{len(toggle_witnesses)} of 8, each with "
        f"{sorted(set(toggle_witnesses.values()))} witness(es). That is what "
        "'re-witnessable' buys, and it is also why the contrast is analytically "
        "entailed rather than tested."
    )
    notes.append(
        "A0' has no battery run: no run id in capability_spectrum.json contains "
        "'prime', and battery/adapters/ has a0.py, a0_spike.py, a2.py and no prime "
        "adapter. Panel B draws that column as a structural gap, hatched, not as a value."
    )
    notes.append(
        "SOURCE NEEDED, degraded rather than added: A0's executable-probe count "
        "(A0P_REPORT section 1 reports 0 of 22 designed) lives in "
        "cold-start-a0/artifacts/engines_report.json, which is not declared in "
        "figures/sources.py. Panel C draws that cell as not-readable, not as 0."
    )
    notes.append(
        "SOURCE NEEDED, degraded rather than added: object counts. A0''s 3 comes from "
        "prime_report engines.tracks; A0's 3 is prose only "
        "(papers/phase1-workshop/sections/03_a0.md 3.3) and is labelled as such on the plate."
    )
    if rb_replay_is_bare_bool:
        notes.append(
            "Run B's certify_cheap is the bare boolean true; the 111-frame / 8991-pixel "
            "shape of that check is recorded under run_a, on the unseeded manual. Panel D "
            "says so rather than borrowing run A's counts."
        )
    return data, notes


# --------------------------------------------------------------------------
# csv
# --------------------------------------------------------------------------


def csv_rows(data: dict) -> list[list]:
    """Every number on the plate, sorted by ``(arm, world, run, metric)``."""
    a0 = data["a0"]
    a0p = data["a0p"]
    rb = data["run_b"]
    battery = data["battery"]
    rows: list[list] = []

    def add(arm, world, run, metric, value, status, num=None, den=None, states=None, frame=""):
        rows.append([arm, world, run, metric, value, status, num, den, states, frame])

    # ---- A0 ---------------------------------------------------------------
    add("A0", _A0_WORLD, "base", "state_action_coverage",
        theme.fmt_num(a0["coverage"], 6), ST_OK, a0["covered"], a0["pairs"], a0["states"],
        "derived: pairs - held_out_pairs; the held-out set is the pairs the trajectory "
        "could never contain, so its complement is the covered set")
    add("A0", _A0_WORLD, "base", "accuracy_vs_truth_on_trace",
        theme.fmt_num(a0["accuracy"], 6), ST_OK, a0["agree"], a0["pairs"], a0["states"],
        "full-history replay over every reachable pair; 3 disagreements")
    add("A0", _A0_WORLD, "base", "accuracy_held_out_off_trace",
        theme.fmt_num(a0["held_accuracy"], 6), ST_OK, a0["held_agree"], a0["held_pairs"],
        a0["states"], a0["held_frame"])
    add("A0", _A0_WORLD, "base", "reachable_states", a0["states"], ST_OK, None, None,
        a0["states"], "")
    add("A0", _A0_WORLD, "base", "state_action_pairs", a0["pairs"], ST_OK, None, None,
        a0["states"], "")
    add("A0", _A0_WORLD, "base", "explorer_steps", a0["steps"], ST_OK, None, None, a0["states"],
        "battery capability_spectrum runs.a0-base.steps; the exhaustive walk")
    add("A0", _A0_WORLD, "base", "rules_in_manual", a0["rules"], ST_OK, None, None, None,
        "counted from score_vs_truth.structural: clauses neither null nor '<missing>'")
    add("A0", _A0_WORLD, "base", "objects_in_manual", 3, ST_PROSE, None, None, None,
        "papers/phase1-workshop/sections/03_a0.md 3.3; no declared source carries it")
    add("A0", _A0_WORLD, "base", "executable_probes", None, ST_UNREGISTERED, None, None, None,
        "A0P_REPORT section 1 reports 0 of 22 designed; the count lives in "
        "cold-start-a0/artifacts/engines_report.json, which figures/sources.py does not declare")
    add("A0", _A0_WORLD, "base", "revisions", 0, ST_OK, None, None, None,
        "A0_REPORT: nothing came back from certify, so the loop was never exercised")
    add("A0", _A0_WORLD, "base", "mechanism_witnessed_directions", 1, ST_OK, 1, 4, None,
        "press witnessed leftward only (structural: press_left); "
        + ", ".join(a0["press_missing"]) + " rejected at R-05 for want of evidence")
    add("A0", _A0_WORLD, "base", "errors_named_in_advance",
        ";".join(a0["error_actions"]), ST_OK, a0["disagree"], a0["pairs"], a0["states"],
        "the three uncovered pairs are exactly the three the manual gets wrong -- "
        "THEORIZE_LOG R-05 named them before the score existed")

    add("A0 no-button", _A0_WORLD + " (button-less variant)", "variant",
        "accuracy_vs_truth_on_trace",
        theme.fmt_num(_ratio(a0["variant_agree"], a0["variant_pairs"]), 6), ST_OK,
        a0["variant_agree"], a0["variant_pairs"], a0["variant_states"],
        "the M5 variant: the Button removed, so the latch cannot bite")
    add("A0 no-button", _A0_WORLD + " (button-less variant)", "variant",
        "accuracy_held_out_off_trace", None, ST_INSUFFICIENT, None, None,
        a0["variant_states"], battery["a0-no-button"]["K2"]["frame"])

    # ---- A0' --------------------------------------------------------------
    add("A0'", _A0P_WORLD, "run-a", "state_action_coverage",
        theme.fmt_num(a0p["coverage"], 6), ST_OK, a0p["covered"], a0p["pairs"], a0p["states"],
        "the truncated explorer's own count (trace.a0p-base.covered_pairs)")
    add("A0'", _A0P_WORLD, "run-a", "accuracy_vs_truth_on_trace",
        theme.fmt_num(a0p["accuracy"], 6), ST_OK, a0p["agree"], a0p["score_pairs"],
        a0p["states"], "scored over all 228 reachable pairs; 0 disagreements")
    add("A0'", _A0P_WORLD, "run-a", "accuracy_held_out_off_trace", None, ST_NO_HELD_OUT,
        None, None, a0p["states"],
        "no held-out set is defined for A0'. ABSENT -- not 1.0 and not 0.0. Drawn with "
        "theme.ABSENCE['not-applicable']")
    add("A0'", _A0P_WORLD, "run-a", "reachable_states", a0p["states"], ST_OK, None, None,
        a0p["states"], "")
    add("A0'", _A0P_WORLD, "run-a", "state_action_pairs", a0p["pairs"], ST_OK, None, None,
        a0p["states"], "")
    add("A0'", _A0P_WORLD, "run-a", "explorer_budget", a0p["budget"], ST_OK, None, None,
        a0p["states"], "transitions walked before the explorer was cut off")
    add("A0'", _A0P_WORLD, "run-a", "explorer_truncation",
        theme.fmt_num(a0p["truncation"], 6), ST_OK, a0p["budget"], a0["steps"], None,
        "derived across two artefacts: prime budget over battery runs.a0-base.steps")
    add("A0'", _A0P_WORLD, "run-a", "rules_in_manual", a0p["rules"], ST_OK, None, None, None,
        "run_a.coverage_probes.rules")
    add("A0'", _A0P_WORLD, "run-a", "objects_in_manual", a0p["objects"], ST_OK, None, None,
        None, "prime_report engines.tracks, after re-identification merged 7 tracks into 3")
    add("A0'", _A0P_WORLD, "run-a", "executable_probes", a0p["probes_exec"], ST_OK,
        a0p["probes_exec"], a0p["probes_total"], None, "13 executable of 27 designed")
    add("A0'", _A0P_WORLD, "run-a", "rules_untested_by_trace", a0p["untested_rules"], ST_OK,
        None, a0p["rules"], None, "run_a.coverage_probes.untested_rules")
    add("A0'", _A0P_WORLD, "run-a", "revisions", a0p["revisions"], ST_OK, None, None, None,
        "0 revisions, and now with a measured reason: nothing was untested and nothing refuted")
    add("A0'", _A0P_WORLD, "run-a", "mechanism_witnessed_directions",
        len(a0p["toggle_witnesses"]), ST_OK, len(a0p["toggle_witnesses"]), 8, None,
        "one witness per direction x polarity: "
        + ", ".join(f"{k}={v}" for k, v in sorted(a0p["toggle_witnesses"].items())))

    add("A0'", _A0P_WORLD, "run-b", "accuracy_vs_truth_before_repair",
        theme.fmt_num(rb["before"], 6), ST_OK, rb["before_agree"], rb["before_pairs"],
        a0p["states"], "seeded manual: one false clause, push_onto_crate, invisible to replay")
    add("A0'", _A0P_WORLD, "run-b", "accuracy_vs_truth_after_repair",
        theme.fmt_num(rb["after"], 6), ST_OK, rb["after_agree"], rb["after_pairs"],
        a0p["states"], "after deleting the seeded clause")
    add("A0'", _A0P_WORLD, "run-b", "revisions", rb["revisions"], ST_OK, None, None, None,
        "one revision, and it was a deletion -- no multi-round repair is exercised anywhere")
    add("A0'", _A0P_WORLD, "run-b", "coverage_probes_run", rb["probes_run"], ST_OK, None, None,
        None, "refuted: " + ", ".join(rb["refuted"]))
    add("A0'", _A0P_WORLD, "run-b", "replay_verdict", "GREEN", ST_OK, None, None, None,
        "blind to the seeded clause, exactly as predicted; the artefact records it as a bare "
        "boolean, and the 111-frame / 8991-pixel shape belongs to run A's unseeded manual")
    add("A0'", _A0P_WORLD, "run-b", "lean_verdict", "CAUGHT", ST_OK, None, None, None, rb["lean"])
    add("A0'", _A0P_WORLD, "run-b", "coverage_probe_verdict", "CAUGHT", ST_OK, None, None, None,
        "untested by the trace: " + ", ".join(rb["untested"])
        + "; navigated to a firing state, wrote the prediction down first, world disagreed")

    # ---- battery ----------------------------------------------------------
    arm_of = {"a0-base": "A0", "a0-no-button": "A0 no-button", "a0-spike": "a0-spike"}
    world_of = {
        "a0-base": _A0_WORLD,
        "a0-no-button": _A0_WORLD + " (button-less variant)",
        "a0-spike": _SPIKE_WORLD,
    }
    for key in sorted(k for k in BATTERY_KEYS if k is not None):
        for metric in ("K1", "K2", "K4"):
            cell = battery[key][metric]
            # K4's support is annotated / unannotated / min_witnesses -- counts,
            # not the two halves of a fraction. Putting them in the numerator and
            # denominator columns would invent a ratio the battery never claims,
            # so they go to frame_note and those two columns stay empty.
            frame = cell["frame"]
            if metric == "K4":
                num = den = None
                frame = (
                    f"mean coverage over annotated clauses; annotated="
                    f"{cell['annotated']}, unannotated={cell['unannotated']} "
                    "(reported alongside, never folded in), min_witnesses="
                    f"{cell['min_witnesses']}. K4 is never read without K2 beside it."
                )
            else:
                num = cell["agree"]
                den = cell["pairs"]
            add(
                arm_of[key],
                world_of[key],
                f"battery:{key}",
                f"battery_{metric}",
                theme.fmt_num(cell["value"], 6) if cell["value"] is not None else None,
                cell["status"],
                num,
                den,
                None,
                frame,
            )
    add("A0'", _A0P_WORLD, "battery:none", "battery_K2", None, ST_NO_BATTERY, None, None, None,
        "A0' has no battery run at all: no run id in capability_spectrum.json contains "
        "'prime', and battery/adapters/ carries a0.py, a0_spike.py, a2.py and no prime adapter")

    rows.sort(key=lambda r: (str(r[0]), str(r[1]), str(r[2]), str(r[3])))
    return rows


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

_BANNER = (
    "ANALYTIC ENTAILMENT -- this contrast DEMONSTRATES the mechanism, it does not TEST it. "
    "\"n = 1 per arm, on worlds built by the same instance that theorized them\" covers only "
    "sampling error. The objection that bites is analytic: A0''s toggle was designed so that "
    "every direction-by-polarity combination would have its own witness, and the adjudication "
    "rule -- admit a generalisation iff every case is witnessed -- then mechanically admits what "
    "it mechanically rejected in A0. The outcome follows from the construction; nothing was "
    "learned that was not built in. (papers/phase1-workshop/sections/03_a0.md 3.3.)"
)

_TWO_VARIABLES = (
    "TWO VARIABLES, NOT ONE, AND NOT THE ONLY TWO -- the advertised change is latch -> toggle, "
    "and the explorer is THEN weakened on purpose. \"Identical except\" would be a false "
    "description and is not used: see panel C for all eight differences."
)


def _label_box(p: dict) -> dict:
    return {
        "boxstyle": "round,pad=0.34",
        "facecolor": p["surface"],
        "edgecolor": p["axis"],
        "linewidth": 0.6,
    }


def _panel_a(ax, data: dict, p: dict, colour: dict) -> None:
    """Coverage x accuracy. Two points, an arrow, and A0's drop to its K2."""
    a0, a0p = data["a0"], data["a0p"]

    ax.set_xlim(0.0, 1.08)
    # The band below y = 0 carries no data and never will: it is reserved for
    # the series key, so no legend entry can land under a callout box.
    ax.set_ylim(-0.26, 1.16)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_xlabel("state-action coverage (pairs the trace covered / reachable pairs)")
    ax.set_ylabel("accuracy vs ground truth (share)")
    ax.set_title(
        "A. coverage went DOWN, accuracy went UP", loc="left"
    )
    ax.grid(True, axis="both")
    ax.axhline(1.0, color=p["grid"], linewidth=0.6, zorder=0)

    # --- A0's drop: on-trace K1 to off-trace K2, at the same coverage -------
    ax.plot(
        [a0["coverage"], a0["coverage"]],
        [a0["accuracy"], a0["held_accuracy"]],
        color=colour["A0"],
        linewidth=1.2,
        linestyle=(0, (4, 2)),
        zorder=2,
    )
    ax.plot(
        [a0["coverage"]],
        [a0["held_accuracy"]],
        marker=theme.series_marker(0),
        markersize=7.0,
        markerfacecolor="none",
        markeredgecolor=colour["A0"],
        markeredgewidth=1.4,
        linestyle="none",
        zorder=3,
    )
    ax.annotate(
        f"A0 off-trace (K2) = {theme.fmt_num(a0['held_accuracy'])}\n"
        f"n = {a0['held_pairs']} uncovered pairs, adversarial\n"
        "the metric replay cannot see",
        xy=(a0["coverage"], a0["held_accuracy"]),
        xytext=(0.958, 0.055),
        fontsize=theme.BASE_FONT_SIZE - 2,
        color=p["ink_secondary"],
        ha="right",
        va="bottom",
        bbox=_label_box(p),
        arrowprops={
            "arrowstyle": "-",
            "color": p["axis"],
            "linewidth": 0.6,
            "shrinkB": 6,
        },
        zorder=4,
    )

    # --- the two on-trace points -------------------------------------------
    ax.plot(
        [a0["coverage"]],
        [a0["accuracy"]],
        marker=theme.series_marker(0),
        markersize=8.5,
        color=colour["A0"],
        linestyle="none",
        zorder=5,
    )
    ax.plot(
        [a0p["coverage"]],
        [a0p["accuracy"]],
        marker=theme.series_marker(1),
        markersize=8.5,
        color=colour["A0'"],
        linestyle="none",
        zorder=5,
    )

    # --- the arrow that is the finding -------------------------------------
    ax.annotate(
        "",
        xy=(a0p["coverage"], a0p["accuracy"]),
        xytext=(a0["coverage"], a0["accuracy"]),
        arrowprops={
            "arrowstyle": "-|>",
            "color": p["ink_secondary"],
            "linewidth": 1.5,
            "shrinkA": 10.0,
            "shrinkB": 10.0,
            "connectionstyle": "arc3,rad=0.22",
        },
        zorder=4,
    )
    ax.text(
        0.700,
        1.115,
        f"coverage {theme.fmt_num(a0p['coverage'] - a0['coverage'])}\n"
        f"accuracy +{theme.fmt_num(a0p['accuracy'] - a0['accuracy'])}",
        fontsize=theme.BASE_FONT_SIZE - 2,
        color=p["ink_secondary"],
        ha="center",
        va="center",
        zorder=5,
    )

    ax.annotate(
        f"A0 -- Button, a LATCH (pressable once)\n"
        f"coverage {a0['covered']}/{a0['pairs']} = {theme.fmt_num(a0['coverage'])}\n"
        f"accuracy {a0['agree']}/{a0['pairs']} = {theme.fmt_num(a0['accuracy'])}\n"
        f"n = {a0['pairs']} pairs over {a0['states']} reachable states\n"
        f"3 errors: the Button pressed from "
        + "/".join(a0["error_actions"]),
        xy=(a0["coverage"], a0["accuracy"]),
        xytext=(0.995, 0.760),
        fontsize=theme.BASE_FONT_SIZE - 2,
        color=p["ink"],
        ha="right",
        va="top",
        bbox=_label_box(p),
        arrowprops={"arrowstyle": "-", "color": p["axis"], "linewidth": 0.6, "shrinkB": 8},
        zorder=6,
    )
    ax.annotate(
        f"A0' -- Switch, a TOGGLE (re-witnessable)\n"
        f"coverage {a0p['covered']}/{a0p['pairs']} = {theme.fmt_num(a0p['coverage'])}\n"
        f"accuracy {a0p['agree']}/{a0p['score_pairs']} = {theme.fmt_num(a0p['accuracy'])}\n"
        f"n = {a0p['pairs']} pairs over {a0p['states']} reachable states\n"
        f"explorer truncated to {theme.fmt_num(a0p['truncation'] * 100, 1)}% of A0's walk\n"
        "no held-out set defined: off-trace\n"
        "accuracy is ABSENT -- not 1.0, not 0.0",
        xy=(a0p["coverage"], a0p["accuracy"]),
        xytext=(0.035, 0.520),
        fontsize=theme.BASE_FONT_SIZE - 2,
        color=p["ink"],
        ha="left",
        va="top",
        bbox=_label_box(p),
        arrowprops={"arrowstyle": "-", "color": p["axis"], "linewidth": 0.6, "shrinkB": 8},
        zorder=6,
    )
    ax.text(
        0.040,
        0.095,
        "\"The variable is not how much\nwas seen. It is whether what was\nseen could be seen "
        "AGAIN.\"\n-- A0P_REPORT.md section 1",
        fontsize=theme.BASE_FONT_SIZE - 1,
        color=p["ink_secondary"],
        ha="left",
        va="bottom",
        zorder=3,
    )


def _panel_b(ax, data: dict, p: dict, colour: dict) -> None:
    """Held-out K2 -- and never without its denominator."""
    battery = data["battery"]

    columns: list[dict] = []
    for i, key in enumerate(BATTERY_KEYS):
        if key is None:
            columns.append(
                {
                    "x": i,
                    "tick": "A0' run A\ncold-start-a0/prime\nno held-out set,\nno battery run",
                    "kind": "not-applicable",
                    "note": "structural gap:\nno prime adapter in\nbattery/adapters/,\n"
                    "and no held-out\nset is defined",
                    "colour": None,
                }
            )
            continue
        cell = battery[key]["K2"]
        if cell["status"] == "ok":
            columns.append(
                {
                    "x": i,
                    "tick": {
                        "a0-base": f"A0\n{_A0_WORLD}\nn = {cell['pairs']} pairs",
                        "a0-spike": f"a0-spike\nother track / world\nn = {cell['pairs']} pairs",
                    }[key],
                    "kind": "value",
                    "value": float(cell["value"]),
                    "pairs": int(cell["pairs"]),
                    "note": {
                        "a0-base": "3 adversarially-chosen\nuncovered pairs.\n"
                        "Gaps left by the trace,\nnot a sample drawn\nfrom the world.",
                        "a0-spike": "39960 exhaustively\nenumerated well-formed\npairs, most of them\n"
                        "unreachable. NOTHING\nwas withheld.",
                    }[key],
                    "colour": colour["A0" if key == "a0-base" else "a0-spike"],
                    "marker": theme.series_marker(0 if key == "a0-base" else 2),
                }
            )
        else:
            columns.append(
                {
                    "x": i,
                    "tick": "A0 no-button\nbutton-less variant\nno held-out pairs",
                    "kind": "insufficient-data",
                    "note": "every reachable pair\nwas covered, so the\nheld-out set is empty",
                    "colour": None,
                }
            )

    # A left gutter, wide enough for the absence key to sit clear of the first
    # column: a legend printed over a hatched gap is a gap nobody can read.
    ax.set_xlim(-1.05, len(columns) - 0.35)
    ax.set_ylim(-0.22, 1.30)
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticks([c["x"] for c in columns])
    ax.set_xticklabels([c["tick"] for c in columns], fontsize=theme.BASE_FONT_SIZE - 4)
    ax.set_ylabel("held-out (off-trace) accuracy K2")
    ax.set_title("B. 0.000 beside 1.000 is meaningless without the denominators", loc="left")

    for c in columns:
        if c["kind"] == "value":
            ax.plot(
                [c["x"], c["x"]],
                [0.0, c["value"]],
                color=c["colour"],
                linewidth=1.2,
                zorder=2,
            )
            ax.plot(
                [c["x"]],
                [c["value"]],
                marker=c["marker"],
                markersize=9.0,
                color=c["colour"],
                linestyle="none",
                zorder=3,
            )
            ax.text(
                c["x"],
                c["value"] + 0.055,
                f"{theme.fmt_num(c['value'])}\nn = {c['pairs']}",
                ha="center",
                va="bottom",
                fontsize=theme.BASE_FONT_SIZE - 2,
                color=p["ink"],
                zorder=4,
            )
        else:
            spec = theme.ABSENCE[c["kind"]]
            ax.add_patch(
                Rectangle(
                    (c["x"] - 0.34, -0.02),
                    0.68,
                    1.04,
                    facecolor=spec["facecolor"],
                    edgecolor=p["ink_secondary"] if spec["hatch"] else p["muted"],
                    hatch=spec["hatch"],
                    linewidth=0.8,
                    linestyle="-" if spec["hatch"] else ":",
                    zorder=2,
                )
            )
            ax.text(
                c["x"],
                1.06,
                spec["label"].replace(" (structural)", ""),
                ha="center",
                va="bottom",
                fontsize=theme.BASE_FONT_SIZE - 2,
                color=p["ink_secondary"],
                zorder=4,
            )
        ax.text(
            c["x"],
            -0.055,
            c["note"],
            ha="center",
            va="top",
            fontsize=theme.BASE_FONT_SIZE - 4,
            color=p["muted"],
            zorder=4,
        )

    # The divider: everything left of it is this track's A0 family in one world
    # pair; a0-spike is a different world, run by the other track.
    ax.axvline(len(columns) - 1.5, color=p["axis"], linewidth=0.8, zorder=1)
    ax.text(
        len(columns) - 1.42,
        1.245,
        "different world,\nother track --\nnot comparable",
        ha="left",
        va="top",
        fontsize=theme.BASE_FONT_SIZE - 3,
        color=p["ink_secondary"],
        zorder=4,
    )
    ax.text(
        -1.00,
        1.245,
        "battery/REPORT_V1.md: \"Both are K2, and comparing\nthem directly would be wrong.\"",
        ha="left",
        va="top",
        fontsize=theme.BASE_FONT_SIZE - 3,
        color=p["ink_secondary"],
        zorder=4,
    )
    ax.grid(True, axis="y")
    ax.legend(
        handles=theme.absence_handles(theme_name_of(p)),
        loc="center left",
        bbox_to_anchor=(0.005, 0.46),
        fontsize=theme.BASE_FONT_SIZE - 3,
        ncols=1,
        title="an absence is never drawn as a zero",
        alignment="left",
        title_fontsize=theme.BASE_FONT_SIZE - 3,
    )


def theme_name_of(p: dict) -> str:
    """Which theme a palette belongs to. Avoids threading the name everywhere."""
    for name in theme.THEMES:
        if theme.PALETTE[name] is p:
            return name
    raise ValueError("palette does not belong to a declared theme")


def _panel_c(ax, data: dict, p: dict, colour: dict) -> None:
    """"Identical except" would be false. Here is every difference."""
    a0, a0p = data["a0"], data["a0p"]
    toggles = len(a0p["toggle_witnesses"])

    rows: list[tuple[str, str, str, bool]] = [
        (
            "mechanism  [ADVERTISED VARIABLE]",
            f"Button, a LATCH -- press witnessed in 1 of 4 directions",
            f"Switch, a TOGGLE -- witnessed in {toggles} of 8 direction x polarity",
            True,
        ),
        (
            "explorer  [ADVERTISED VARIABLE]",
            f"exhaustive: {a0['steps']} steps, {a0['covered']}/{a0['pairs']} pairs covered",
            f"truncated: {a0p['budget']}-transition budget = "
            f"{theme.fmt_num(a0p['truncation'] * 100, 1)}% of A0's walk, "
            f"{a0p['covered']}/{a0p['pairs']} covered",
            True,
        ),
        ("reachable states", str(a0["states"]), str(a0p["states"]), False),
        ("state-action pairs", str(a0["pairs"]), str(a0p["pairs"]), False),
        ("rules in the manual", str(a0["rules"]), str(a0p["rules"]), False),
        (
            "objects in the manual",
            "3  (prose only: 03_a0.md 3.3; no declared source)",
            f"{a0p['objects']}  (engines.tracks, after re-identification)",
            False,
        ),
        (
            "executable probes emitted",
            "NOT READABLE from a declared source\n(A0P_REPORT section 1: 0 of 22 designed)",
            f"{a0p['probes_exec']} of {a0p['probes_total']} designed",
            False,
        ),
        (
            "revisions",
            "0  (nothing came back from certify)",
            f"{a0p['revisions']} in run A, 1 in run B (seeded, panel D)",
            False,
        ),
    ]

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")
    ax.set_title(
        "C. \"identical except\" is a false description and is not used: shaded = the two "
        "ADVERTISED variables, the six below differ too",
        loc="left",
    )

    x_q, x_a, x_b = 0.004, 0.235, 0.615
    top, step = 0.955, 0.108
    ax.text(x_q, top, "quantity", fontsize=theme.BASE_FONT_SIZE - 2, color=p["ink_secondary"],
            va="center", ha="left")
    ax.text(x_a, top, "A0  (cold-start-a0)", fontsize=theme.BASE_FONT_SIZE - 2,
            color=colour["A0"], va="center", ha="left")
    ax.text(x_b, top, "A0'  (cold-start-a0/prime)", fontsize=theme.BASE_FONT_SIZE - 2,
            color=colour["A0'"], va="center", ha="left")
    ax.plot([0.0, 1.0], [top - 0.045, top - 0.045], color=p["axis"], linewidth=0.6)

    for i, (quantity, left, right, advertised) in enumerate(rows):
        y = top - 0.075 - i * step
        if advertised:
            ax.add_patch(
                Rectangle(
                    (0.0, y - step * 0.44),
                    1.0,
                    step * 0.88,
                    facecolor=p["grid"],
                    edgecolor="none",
                    zorder=0,
                )
            )
        ax.text(x_q, y, quantity, fontsize=theme.BASE_FONT_SIZE - 2, color=p["ink"],
                va="center", ha="left", zorder=2)
        ax.text(x_a, y, left, fontsize=theme.BASE_FONT_SIZE - 2, color=p["ink_secondary"],
                va="center", ha="left", zorder=2)
        ax.text(x_b, y, right, fontsize=theme.BASE_FONT_SIZE - 2, color=p["ink_secondary"],
                va="center", ha="left", zorder=2)


def _panel_d(ax, data: dict, p: dict) -> None:
    """Run B: the seeded-error controlled experiment."""
    rb = data["run_b"]

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")
    ax.set_title(
        "D. A0' run B -- a controlled experiment with a seeded error, not a discovery: "
        "one false clause, invisible to replay",
        loc="left",
    )

    layers = [
        (
            "full-history replay (cheap certify)",
            "GREEN -- AND BLIND",
            "warning",
            "the seeded clause never fires in the 110-transition history, so replay cannot "
            "see it. Exactly as predicted.",
        ),
        (
            "Lean transcription",
            "CAUGHT IT",
            "good",
            rb["lean"],
        ),
        (
            f"coverage probe ({rb['probes_run']} probe run)",
            "CAUGHT IT",
            "good",
            ", ".join(rb["untested"])
            + " has 2 firing states and neither is in the trace -- navigate, write the "
            "prediction down first, execute, world disagrees: refuted.",
        ),
    ]

    top, step = 0.90, 0.235
    for i, (layer, verdict, status, detail) in enumerate(layers):
        y = top - i * step
        ax.text(0.004, y, layer, fontsize=theme.BASE_FONT_SIZE - 1, color=p["ink"],
                va="center", ha="left")
        ax.text(
            0.245,
            y,
            verdict,
            fontsize=theme.BASE_FONT_SIZE - 2,
            # Near-black on a status fill, in both themes: the fill is the same
            # colour in light and dark, so the text on it must be too.
            color=theme.PALETTE["light"]["ink"],
            va="center",
            ha="center",
            bbox={
                "boxstyle": "round,pad=0.30",
                "facecolor": theme.STATUS[status],
                "edgecolor": "none",
            },
        )
        ax.text(0.335, y, detail, fontsize=theme.BASE_FONT_SIZE - 2.5,
                color=p["ink_secondary"], va="center", ha="left", wrap=False)

    ax.text(
        0.004,
        top - 3 * step + 0.02,
        f"repair: delete the clause -- {rb['revisions']} revision, and it was a deletion.   "
        f"accuracy {theme.fmt_num(rb['before'], 6)} ({rb['before_agree']}/{rb['before_pairs']})"
        f"  ->  {theme.fmt_num(rb['after'], 6)} ({rb['after_agree']}/{rb['after_pairs']}).   "
        "No multi-round repair is exercised anywhere in either run.",
        fontsize=theme.BASE_FONT_SIZE - 2,
        color=p["ink"],
        va="center",
        ha="left",
    )


def _render(data: dict, theme_name: str) -> list[str]:
    p = theme.apply_theme(theme_name)
    colours = theme.series_colours(theme_name, len(SERIES), all_pairs=True)
    colour = {name: colours[i] for i, name in enumerate(SERIES)}

    fig = plt.figure(figsize=(13.2, 13.4))
    gs = fig.add_gridspec(5, 2, height_ratios=[0.40, 1.42, 0.86, 0.70, 0.20])
    ax_banner = fig.add_subplot(gs[0, :])
    ax_plane = fig.add_subplot(gs[1, 0])
    ax_k2 = fig.add_subplot(gs[1, 1])
    ax_diff = fig.add_subplot(gs[2, :])
    ax_runb = fig.add_subplot(gs[3, :])
    ax_pad = fig.add_subplot(gs[4, :])
    ax_pad.axis("off")

    ax_banner.axis("off")
    ax_banner.set_xlim(0.0, 1.0)
    ax_banner.set_ylim(0.0, 1.0)
    ax_banner.text(
        0.5,
        0.60,
        _BANNER,
        fontsize=theme.BASE_FONT_SIZE - 1,
        color=p["ink"],
        ha="center",
        va="center",
        wrap=True,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": p["page"],
            "edgecolor": theme.STATUS["warning"],
            "linewidth": 1.2,
        },
    )
    ax_banner.text(
        0.5,
        0.02,
        _TWO_VARIABLES,
        fontsize=theme.BASE_FONT_SIZE - 2,
        color=p["ink_secondary"],
        ha="center",
        va="bottom",
        wrap=True,
    )

    _panel_a(ax_plane, data, p, colour)
    _panel_b(ax_k2, data, p, colour)
    _panel_c(ax_diff, data, p, colour)
    _panel_d(ax_runb, data, p)

    series_handles = [
        Line2D([], [], color=colour["A0"], marker=theme.series_marker(0), linestyle="none",
               markersize=6.0, label="A0 -- Button, latch"),
        Line2D([], [], color=colour["A0'"], marker=theme.series_marker(1), linestyle="none",
               markersize=6.0, label="A0' -- Switch, toggle"),
        Line2D([], [], color=colour["a0-spike"], marker=theme.series_marker(2), linestyle="none",
               markersize=6.0,
               label="a0-spike -- other world, panel B"),
        Line2D([], [], color=p["ink_secondary"], marker=theme.series_marker(0),
               markerfacecolor="none", markeredgewidth=1.4, linestyle=(0, (4, 2)),
               markersize=6.0, label="off-trace K2 (open marker)"),
    ]
    leg_plane = ax_plane.legend(
        handles=series_handles,
        # Anchored in the reserved band below y = 0 (axes fraction 0.183), so it
        # cannot collide with a callout however the callouts are laid out.
        loc="upper center",
        bbox_to_anchor=(0.5, 0.170),
        fontsize=theme.BASE_FONT_SIZE - 2.5,
        ncols=2,
        title="colour + marker (identity is never colour alone)",
        alignment="left",
        title_fontsize=theme.BASE_FONT_SIZE - 2.5,
    )
    leg_plane.get_title().set_color(p["ink_secondary"])

    fig.suptitle(
        "Figure 7 -- A0 vs A0': coverage went down, accuracy went up, because what was seen "
        "could be seen again"
    )
    theme.caveat(
        fig,
        "A0' is cold-start-a0/prime, not a0-spike: PLAN.md section 2 named a0-spike as A0', and "
        "a0-spike is a separate cold start on a different world run by the other track "
        "(03_a0.md 3.5), so it appears only in panel B, behind a divider.  |  "
        "The two K2 values in panel B are not comparable and are never shown without their "
        "denominators: A0's n = 3 is the adversarial gaps the trace left, a0-spike's n = 39960 "
        "is an exhaustive enumeration with nothing withheld. battery/REPORT_V1.md: \"Both are "
        "K2, and comparing them directly would be wrong.\"  battery/REPORT_V2.md: "
        "\"Comparability was bought. Safety was not.\"  |  A0' has no held-out set, so its K2 is "
        "absent, not zero; and A0' has no battery run at all -- battery/adapters/ carries a0.py, "
        "a0_spike.py, a2.py and no prime adapter -- so the battery panel cannot include it, and "
        "the gap is drawn as a gap.  |  Both worlds are self-built: one instance built the world "
        "and adjudicated it (A0P_REPORT.md 5.5, \"the seal has the same hole as A0's\"), and the "
        "manuals differ in eight ways, not one (panel C).  |  A0's executable-probe count and "
        "both object counts are not readable from any source declared in figures/sources.py; "
        "they are labelled on the plate rather than drawn as numbers this pipeline can hash.",
        theme=theme_name,
    )
    return theme.save(fig, NAME, theme_name)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------


def build() -> dict:
    data, notes = extract()
    rows = csv_rows(data)
    csv_path = theme.write_csv(NAME, CSV_HEADER, rows)

    images: list[str] = []
    for theme_name in theme.THEMES:
        images.extend(_render(data, theme_name))

    notes.append(
        f"{len(rows)} CSV rows; 3 colour series (A0, A0', a0-spike) = "
        f"theme.MAX_ALLPAIRS_SERIES, and every absence wears no colour at all."
    )
    return {"csv": csv_path, "images": images, "notes": notes}


if __name__ == "__main__":
    result = build()
    print(result["csv"])
    for image in result["images"]:
        print(image)
    for note in result["notes"]:
        print("note:", note)
