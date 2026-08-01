"""Derive this run's MANIFEST.json. Byte-stable; no wall clock enters it.

The narrative fields are this run's own claims. Everything mechanical -- the
file list, the sizes, the sha256s, and the exact bytes on disk -- is derived
here and rendered through `armtools.backfill.render`, so the manifest has the
same shape and the same serialisation as every other manifest in this archive
rather than whatever `json.dump` was called with by hand.

This directory has no `ledger.jsonl` (it made no API call and no model call),
so `armtools.backfill.classify` reads it as a `process_record` and
`verify_provenance`'s re-derivation check correctly skips it -- there is
nothing to derive it *from*. That is the same footing as
`20260801T0000Z-A-probe-economics` and `20260801T0200Z-C-desk-diet`.

    python make_manifest.py
"""

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                      # noqa: E402,F401

from armtools import backfill                          # noqa: E402

SLUG = os.path.basename(HERE)


def _files():
    out = []
    for name in sorted(os.listdir(HERE)):
        if name in ("MANIFEST.json",) or name.startswith("__"):
            continue
        path = os.path.join(HERE, name)
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as fh:
            blob = fh.read()
        out.append({"path": name,
                    "sha256": hashlib.sha256(blob).hexdigest(),
                    "bytes": len(blob)})
    return out


PAYLOAD = {
    "prompt_id": "R2-frontier-by-generation",
    "branch": "r2/frontier-gen",
    "base_commit": "af138a0d2302b85f193b9a65f57aadb65c55f95a",
    "utc": "2026-08-01T09:00:00Z",
    "territory": "theoria-arm",
    "lane": "framework-change",
    "cell": "R2",
    "classification": {
        "kind": "framework-change-preparation",
        "archive_material": False,
        "why": "offline: no ARC action, no model call, no network, no ledger. "
               "Measures the four live legs of 2026-07-31 out of their own "
               "records and implements a default-off switch. Not yet run live.",
    },
    "what": (
        "The probe frontier is built by ablation -- the manual, the inert "
        "reading, and one without-rule-N variant per schema -- a family closed "
        "downward under clause deletion, so it cannot contain a mechanism the "
        "manual lacks. Measured over the same 52 completed probes of "
        "2026-07-31, this time reading the grids and not only their hashes: "
        "frontier width was 2 distinct predictions on every one of the 52; 35 "
        "of the 52 were designed against a state the world had already left "
        "(predictions['inert'], which is the anchor every hypothesis is a "
        "successor of, did not equal the world's own before_hash) and all 35 "
        "landed off-frontier; of the 17 that were anchored, 12 missed by a "
        "delta containing exactly one cell that had never changed before in "
        "the run -- a board cell, on which the arm seats no object instance "
        "and which no rule in this grammar can name. So all 47 off-frontier "
        "answers were out of reach of any ablation, and none of the 47 is "
        "attributable to choosing the wrong action. The failure class is "
        "state drift plus expressivity, not probe design; that "
        "reclassification is the primary finding. Implemented --frontier "
        "generated (default ablation, byte-identical): successor hypotheses "
        "anchored on the world's own last observed frame -- world_inert, "
        "world_anchored_manual, world_inert_plus_edge[_k], edge_advance[_k] -- "
        "each carrying a mechanism the manual does not state. Replayed "
        "through the real builder against manuals recompiled from each leg's "
        "own snapshots: 52 of 52 probes reconstructed exactly, ablation "
        "contains the world's answer 5 times, generation 43."),
    "measurement": {
        "probes_completed": 52,
        "ablation_frontier_width_distinct_values": [2],
        "ablation_contains_truth": 5,
        "off_frontier": 47,
        "off_frontier_because_the_anchor_had_drifted": 35,
        "off_frontier_while_anchored_missing_one_unnameable_cell": 12,
        "off_frontier_attributable_to_action_choice": 0,
        "probes_whose_delta_touches_a_never_before_changed_cell": 23,
        "source_legs": [
            "theoria-arm/runs/20260731T1240Z-A3-level2-carried",
            "theoria-arm/runs/20260731T1310Z-A3-level2-carried-r2",
            "theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3",
            "theoria-arm/runs/20260731T1500Z-A3-sk48-carried-l1",
        ],
        "reads": "probes.jsonl (tracked) and trace.jsonl (gitignored; the "
                 "scripts refuse per leg rather than report zero when it is "
                 "absent)",
    },
    "replay": {
        "harness": "replay_frontier.py -- every hypothesis built by "
                   "inner/probe.build_hypotheses itself, against a manual "
                   "recompiled from the leg's books/snapshots/ and a "
                   "FrameStore truncated to the moment before the action",
        "reconstruction_check": "a snapshot is accepted only if its ablation "
                                "prediction dict equals the dict probes.jsonl "
                                "recorded, key for key and hash for hash",
        "probes_replayed": 52,
        "reconstructed": 52,
        "unreconstructed": 0,
        "ablation_contains_truth": 5,
        "generated_contains_truth": 43,
        "off_frontier_answers_recovered": 38,
        "off_frontier_answers_still_missed": 9,
        "ablation_width_values": [2],
        "generated_width_values": [5, 6, 8, 10],
        "anchor_drifted": 35,
        "anchor_drifted_and_off_the_ablation_frontier": 35,
        "cut_generator_action_replay": {
            "hits": 15, "marginal_hits": 0,
            "why_cut": "all 15 were answers world_anchored_manual already had, "
                       "and it recovers none of the 9 still missed; it would "
                       "widen the frontier and lower every action's split "
                       "entropy for nothing",
            "remeasure": "replay_frontier.py --with-cut-generators",
        },
    },
    "falsifiable_prediction": {
        "written": "before any live leg runs the switch",
        "frontier_width": "2 on 52 of 52 -> at least 3 on at least 80% of "
                          "probes (the replay says 3 or more on 52 of 52)",
        "off_frontier_rate": "47/52 = 90.4% -> at most 40% (the replay says "
                             "9/52 = 17.3%; 40% allows for a live leg "
                             "diverging after the first probe)",
        "realised_information_gain_bits": "0.000 on all 52 -> above 0 on at "
                                          "least half the completed probes",
        "what_would_refute_it": [
            "off-frontier rate stays above 70% with width at least 3: the "
            "world is outside the generated class too, the failure is "
            "expressivity end to end, and the change is noise and should be "
            "reverted rather than tuned",
            "world_anchored_manual is right where manual is wrong on fewer "
            "than 20% of probes: the drift diagnosis was wrong",
            "width rises but realised bits stay at 0: a wider frontier that "
            "still never contains the truth prices every action higher for "
            "the same nothing",
        ],
        "not_predicted": "that this completes a level; nothing here was run "
                         "against ARC",
    },
    "switch": {
        "default": "ablation -- FrontierConfig().mode, byte-identical to "
                   "2026-07-31: same hypotheses, same order, same ids, and "
                   "design()'s report grows no key",
        "flag": "python -m harness.run --frontier generated",
        "env": "THEORIA_FRONTIER=generated (positive whitelist; 1, true, "
               "banana, GENERATED and the empty string all stay on ablation)",
        "explicit": "TheoriaArm(..., frontier=FrontierConfig(mode='generated'))",
        "plumbing": "the same path as --goal-protocol / --probe-economy / "
                    "--desk-diet",
    },
    "changed": [
        "theoria-arm/inner/probe.py",
        "theoria-arm/inner/loop.py",
        "theoria-arm/harness/run.py",
        "theoria-arm/tests/test_frontier_generation.py",
        "theoria-arm/tests/test_probe_guard_in_the_loop.py",
        "theoria-arm/tests/test_three_knobs_default_off.py",
    ],
    "not_changed": [
        "engine-rig (read only; cegis_miner was read, not edited -- it returns "
        "a version-space frontier when it returns anything, and on these legs "
        "it refused on every track, so the arm was not discarding one)",
        "any runs/ directory whose name contains R1 (a live round was running)",
        "CONTRACTS/",
    ],
    "tests": {
        "before": 599,
        "after": 619,
        "new_file": "tests/test_frontier_generation.py (20 tests)",
        "lost": 0,
        "negative_controls": [
            "the generated frontier is handed a world whose mechanism no "
            "generator claims, and asserted vacuous",
            "next_unnameable_cells is handed a scattered history and asserted "
            "to return nothing",
            "the environment switch is handed ten near-misses and asserted off",
            "a predictor that raises is asserted to yield 'error', not a "
            "traceback out of the beat",
            "the default path is asserted byte-identical *while* the new "
            "store= argument is passed",
        ],
    },
    "residual_gaps": [
        "the drift is diagnosed, not repaired: re-seating the manual's state "
        "on the world's frame would make certify's replay trivially green and "
        "destroy the only instrument that detects a wrong manual",
        "a leg on the default cannot see its own drift, because byte-identity "
        "forbids writing the anchor block when the switch is off",
        "the 12 expressivity cases can now be predicted but still cannot be "
        "written down: a confirmed edge hypothesis has no home in the DSL",
        "no live evidence; the counterfactual is about containment on the "
        "recorded states, not a forecast for a leg",
        "9 of the 47 are still missed, and 3 of those are correctly anchored "
        "mid-leg probes on sk48-l1 where the extrapolated edge lands on a "
        "different board cell than the world burned",
    ],
    "sealed_pile_contact": "none. Development-pile games only "
                           "(g50t-5849a774, sk48-d8078629).",
    "spend": {"usd": 0.0, "arc_actions": 0, "model_calls": 0,
              "network": "none"},
    "reproduce": [
        "cd theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation",
        "python measure_frontier.py --legs-root ../",
        "python replay_frontier.py --legs-root ../ --with-cut-generators",
        "python make_manifest.py",
    ],
}


def main():
    payload = dict(PAYLOAD)
    payload["files"] = _files()
    path = os.path.join(HERE, "MANIFEST.json")
    with open(path, "wb") as fh:
        fh.write(backfill.render(payload))
    print("wrote %s (%d files)" % (path, len(payload["files"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
