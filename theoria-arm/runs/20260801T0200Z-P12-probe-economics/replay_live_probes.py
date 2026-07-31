"""Replay the four live legs' probe streams through the new guards.

The offline mock campaign cannot reach any of this. `--mock` implies
`offline=True`, offline skips theorize, no theorize means no manual is ever
written, no manual means `books.load_predictor()` fails, and
`_probe_or_explore` with `namespace=None` never designs a probe and never calls
`plan`. The specified campaign therefore returns all-zero surprise counts and
zero probes both before and after this change -- see RUN_STATE.md.

So the measurement is taken where the failure actually happened: against
`runs/<leg>/probes.jsonl` as the live legs wrote it. Each design row carries the
action and the full `predictions` map, each result row carries the observed
hash. That is exactly the input `ProbeLog.record_result` and the loop's three
guards consume, so replaying it answers the counterfactual precisely: given the
same world responses, how many of those actions would the new arm have spent on
a probe?

Read-only. No key, no network, no model call, no ARC action.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from inner import probe as probe_beat                 # noqa: E402
from inner.loop import (MAX_PROBES_BETWEEN_THEORIZE,   # noqa: E402
                        MAX_VACUOUS_PROBES_IN_A_ROW,
                        MIN_NEW_FRAMES_BETWEEN_THEORIZE)

LEGS = [
    "20260731T1240Z-A3-level2-carried",
    "20260731T1310Z-A3-level2-carried-r2",
    "20260731T1430Z-A3-level2-carried-r3",
    "20260731T1500Z-A3-sk48-carried-l1",
]


def _load(runs_root, leg):
    path = os.path.join(runs_root, leg, "probes.jsonl")
    if not os.path.exists(path):
        return [], {}
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    designs = [r for r in rows if r.get("phase") == "design"]
    results = {r["probe_id"]: r for r in rows if r.get("phase") == "result"}
    return designs, results


def measure(runs_root, leg):
    designs, results = _load(runs_root, leg)

    # -- as it happened ---------------------------------------------------
    resolved = [(d, results[d["probe_id"]]) for d in designs
                if d["probe_id"] in results]
    vacuous = 0
    claimed_bits = 0.0
    realised_bits = 0.0
    for design, result in resolved:
        gain, is_vacuous = probe_beat.information_gain_bits(
            design.get("predictions") or {}, result["observed"])
        vacuous += bool(is_vacuous)
        realised_bits += gain
        best = (design.get("design") or {}).get("best") or {}
        claimed_bits += float(best.get("entropy_bits") or 0.0)

    # -- what the guards would have done ----------------------------------
    #
    # Faithful to `_probe_or_explore`: the streak and the repeat set are
    # consulted BEFORE the action is sent, and only a probe that is actually
    # sent updates them. A refused probe becomes an exploration action -- the
    # arm still spends the action, but on the least-tried legal action rather
    # than on a question it has already asked or cannot answer.
    #
    # The theorize cadence is `MIN_NEW_FRAMES_BETWEEN_THEORIZE`: the live legs
    # ran exactly one theorize per four probe actions, which is what
    # `turns.json` shows. Both counters are re-armed by a theorize round.
    streak = 0
    since_theorize = 0
    asked = {}
    frames_since_theorize = 0
    kept = refused_streak = refused_repeat = refused_cap = 0
    theorize_rounds = 0

    for design, result in resolved:
        if frames_since_theorize >= MIN_NEW_FRAMES_BETWEEN_THEORIZE:
            theorize_rounds += 1
            frames_since_theorize = 0
            streak = 0
            since_theorize = 0

        mark = probe_beat.fingerprint(design["action"],
                                      design.get("predictions") or {})
        if streak >= MAX_VACUOUS_PROBES_IN_A_ROW:
            refused_streak += 1
        elif mark in asked:
            refused_repeat += 1
        elif since_theorize >= MAX_PROBES_BETWEEN_THEORIZE:
            refused_cap += 1
        else:
            kept += 1
            since_theorize += 1
            asked[mark] = design["probe_id"]
            _gain, is_vacuous = probe_beat.information_gain_bits(
                design.get("predictions") or {}, result["observed"])
            streak = streak + 1 if is_vacuous else 0
        frames_since_theorize += 1

    fingerprints = {probe_beat.fingerprint(d["action"],
                                           d.get("predictions") or {})
                    for d in designs}

    return {
        "leg": leg,
        "probes_designed": len(designs),
        "probes_resolved": len(resolved),
        "distinct_experiments": len(fingerprints),
        "vacuous": vacuous,
        "vacuous_pct": (round(100.0 * vacuous / len(resolved), 1)
                        if resolved else None),
        "claimed_bits": round(claimed_bits, 3),
        "realised_bits": round(realised_bits, 3),
        "probes_kept_under_guard": kept,
        "refused_vacuous_streak": refused_streak,
        "refused_repeat": refused_repeat,
        "refused_cap": refused_cap,
        "theorize_rounds_live": None,
        "theorize_rounds_under_guard": theorize_rounds,
    }


def main() -> int:
    runs_root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    out = {"runs_root": runs_root,
           "constants": {
               "MAX_VACUOUS_PROBES_IN_A_ROW": MAX_VACUOUS_PROBES_IN_A_ROW,
               "MAX_PROBES_BETWEEN_THEORIZE": MAX_PROBES_BETWEEN_THEORIZE,
               "MIN_NEW_FRAMES_BETWEEN_THEORIZE":
                   MIN_NEW_FRAMES_BETWEEN_THEORIZE},
           "legs": [measure(runs_root, leg) for leg in LEGS]}
    totals = {}
    for key in ("probes_designed", "probes_resolved", "distinct_experiments",
                "vacuous", "probes_kept_under_guard",
                "refused_vacuous_streak", "refused_repeat", "refused_cap",
                "theorize_rounds_under_guard"):
        totals[key] = sum(leg[key] for leg in out["legs"])
    totals["claimed_bits"] = round(
        sum(leg["claimed_bits"] for leg in out["legs"]), 3)
    totals["realised_bits"] = round(
        sum(leg["realised_bits"] for leg in out["legs"]), 3)
    out["totals"] = totals
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
