"""Derive this run's MANIFEST.json. Byte-stable; no wall clock enters it.

The narrative fields are this run's own claims. Everything mechanical -- the
file list, the sizes, the sha256s -- is derived here and rendered through
`armtools.backfill.render`, so the manifest has the same shape and the same
serialisation as every other manifest in this archive rather than whatever
`json.dump` was called with by hand.

This directory has no `ledger.jsonl` (it made no API call and no model call),
so `armtools.backfill.classify` reads it as a `process_record` and
`verify_provenance`'s re-derivation check correctly skips it -- there is
nothing to derive it *from*. Same footing as
`20260801T0900Z-R2-frontier-by-generation`.

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
    "prompt_id": "R3-anchor-duality",
    "branch": "z/anchor-duality",
    "base_commit": "e8345affa0d500b8358e19fab65b8e25f615c7f9",
    "utc": "2026-08-01T12:00:00Z",
    "territory": "theoria-arm",
    "lane": "framework-change",
    "cell": "R3",
    "classification": {
        "kind": "framework-change-preparation",
        "archive_material": False,
        "why": "offline: no ARC action, no model call, no network, no ledger, "
               "no spend. Measures the eight live legs and the 52 completed "
               "probes out of their own records and implements a default-off "
               "switch. Not yet run live.",
    },
    "what": (
        "inner/loop._roll_forward answers one question -- where would the "
        "manual be if it were right -- and the arm spends that one answer on "
        "two jobs whose requirements are opposed. certify's replay is a test "
        "of the manual BECAUSE it is open-loop from initial_state() and free "
        "to drift; a re-seated replay cannot diverge by more than one step "
        "and goes green on a manual that is wrong everywhere, and Theoria.md "
        "1.3 makes it the detector of a wrong rule while GAPS.md GAP 3 "
        "records that both Lean routes are shut on a real ARC level, so it is "
        "the only one. The probe frontier needs the opposite: every "
        "hypothesis is a successor of that state, so it must be the frame the "
        "world is showing. One variable serves both and the audit job wins "
        "silently -- 35 of 52 completed probes were designed from a frame the "
        "world had already left, and all 35 landed off-frontier. The obvious "
        "repair, re-seating the state on the world's frame, fixes probe "
        "design by destroying certify's instrument, and is not well-posed "
        "anyway because render is not injective. Implemented --anchor "
        "observed (default rolled, byte-identical): each hypothesis keeps its "
        "mechanism and only the frame its answer is read against moves -- "
        "hash(world XOR (render(h(state,a)) - render(state))). Same ids, same "
        "order, same width. certify is untouched and a test enforces that it "
        "stays untouched. Replayed through the real builder against manuals "
        "recompiled from each leg's own snapshots: 52 of 52 reconstructed, "
        "containment goes from 5 of 52 to 25 of 52 at unchanged width."),
    "the_tension": {
        "job_a": "certify.cheap's replay -- open-loop from initial_state(), "
                 "must be free to drift or it is not a test",
        "job_b": "probe.build_hypotheses -- every hypothesis is a successor "
                 "of the state, so it must be the world's current frame",
        "today": "one variable, and job A wins silently",
        "the_obvious_fix_and_why_not": "re-seating the manual's state on the "
                                       "world's frame each turn makes "
                                       "certify's replay trivially green, "
                                       "destroying the only detector of a "
                                       "wrong manual; and render is not "
                                       "injective, so the state to re-seat to "
                                       "would have to be guessed",
        "designs_considered": [
            "D1 re-seat everywhere -- rejected, destroys the instrument",
            "D2a add world-anchored hypotheses beside the ablations (R2's "
            "--frontier generated) -- works, but widens the frontier from 2 "
            "to 5-10 distinct predictions and so prices every action higher; "
            "measured here to be SUBSUMED by the anchor switch",
            "D2b move the ablations' own anchor -- ADOPTED",
            "D3 re-anchor for probe design only, discard the rolled state, "
            "log each re-anchor -- rejected: a re-anchor is a bit and the "
            "finding is a magnitude (20 of the 35 were off by ONE cell in "
            "4096, 8 by 23-25), and it still needs the ill-posed inversion",
            "D4 drift as an eighth surprise -- rejected: Theoria.md 1.9 "
            "closes the taxonomy at seven and inner/surprise.py raises on an "
            "eighth by construction, and drift is not a new KIND of evidence "
            "but the accumulated consequence of a replay_mismatch that has "
            "already fired and already paid for a call, so a second surprise "
            "double-counts against constraint 8's arithmetic",
        ],
    },
    "measurement": {
        "probes_replayed": 52,
        "reconstructed": 52,
        "unreconstructed": 0,
        "anchor_drifted": 35,
        "the_2x2_contains_the_worlds_answer": {
            "rolled__ablation": 5,
            "observed__ablation": 25,
            "rolled__generated": 43,
            "observed__generated": 43,
            "of": 52,
        },
        "on_the_35_drifted_probes_only": {
            "rolled__ablation": 0,
            "observed__ablation": 20,
            "rolled__generated": 30,
            "observed__generated": 30,
        },
        "frontier_width_distinct_predictions": {
            "rolled__ablation": [2],
            "observed__ablation": [1, 2],
            "rolled__generated": [5, 6, 8, 10],
            "observed__generated": [3, 6, 8],
        },
        "how_many_of_the_35_would_be_seated_correctly": {
            "count": 35,
            "why": "all of them, BY CONSTRUCTION and not by measurement: "
                   "under --anchor observed the frontier's anchor IS the "
                   "world's last observed frame. Reporting that as a result "
                   "would be reporting a definition; the containment row is "
                   "the measurement.",
        },
        "the_subsumption_is_exact": "manual under the observed anchor is "
                                    "right on 25 probes and so is "
                                    "world_anchored_manual; inert anchored is "
                                    "right on 4 and so is world_inert. Same "
                                    "predictions, provable from the "
                                    "definitions, pinned as a test.",
        "the_cost": "on 4 of the 52 the anchored ablation frontier collapses "
                    "to width 1, entropy 0, and the arm correctly refuses the "
                    "action -- 4 probes that were bought on the rolled anchor "
                    "would not be bought on the observed one",
        "still_missed": "the same 9 as R2 (r2 P-01/02/04, r3 P-01/02/04, "
                        "sk48-l1 P-03/06/09) -- the expressivity residue, "
                        "which anchoring was never going to reach",
    },
    "drift_per_leg": {
        "what_it_is": "cells on which the manual's open-loop rolled-forward "
                      "state and the world's observed frame disagree, per "
                      "transition, out of 4096. It is certify's own replay "
                      "series -- the same walk from the same origin over the "
                      "same actions -- which the arm computes every certify "
                      "beat and does not archive.",
        "legs_listed": 8,
        "legs_measured": 8,
        "legs_that_ever_drifted": 6,
        "legs_that_never_drifted": 2,
        "under_the_manual_each_leg_finished_with": {
            "20260731T1240Z-A3-level2-carried": {
                "transitions": 5, "drifted": 4, "max": 25, "mean": 5.8},
            "20260731T1310Z-A3-level2-carried-r2": {
                "transitions": 13, "drifted": 4, "max": 2, "mean": 0.4615},
            "20260731T1430Z-A3-level2-carried-r3": {
                "transitions": 29, "drifted": 0, "max": 0, "mean": 0.0},
            "20260731T1500Z-A3-sk48-carried-l1": {
                "transitions": 17, "drifted": 10, "max": 96, "mean": 6.2353},
            "20260731T231654Z-R1-g50t-a": {
                "transitions": 9, "drifted": 0, "max": 0, "mean": 0.0},
            "20260731T231654Z-R1-sk48-b": {
                "transitions": 5, "drifted": 1, "max": 96, "mean": 19.2},
            "20260801T001851Z-R1b-g50t-a": {
                "transitions": 21, "drifted": 5, "max": 1, "mean": 0.2381},
            "20260801T001851Z-R1b-sk48-b": {
                "transitions": 5, "drifted": 1, "max": 96, "mean": 19.2},
        },
        "at_the_moment_each_probe_was_designed": {
            "0_cells": 17, "1_cell": 20, "2_cells": 5, "6_to_7_cells": 2,
            "23_to_25_cells": 8, "total": 52, "non_zero": 35,
            "note": "the end-state table understates the bill because "
                    "theorize repairs the manual and the repaired one replays "
                    "clean -- r3 is the extreme case: 23 cells wrong at its "
                    "first certify round, 0 at every round after, and 21 of "
                    "its 28 probes designed while it was still wrong",
        },
        "a_one_cell_error_is_fatal": "20 of the 35 drifted probes are off by "
                                     "exactly one cell in 4096; predictions "
                                     "are compared by whole-frame hash, so "
                                     "1/4096 and 96/4096 are the same answer",
        "negative_control": "two of the eight legs report zero drift on every "
                            "transition (r3 on its final manual, and "
                            "R1-g50t-a on all four of its certify rounds). An "
                            "instrument never seen to say 'no drift' has not "
                            "been shown to measure drift.",
    },
    "corrections_to_earlier_claims": [
        "'one mispredicted transition desynchronises the manual's state "
        "permanently' (R2's README, and this ticket's brief) is FALSE. Drift "
        "recovers: 8 recovery events across the 8 live legs, on 4 of the 6 "
        "that ever drifted, non-monotone series on those 4. The manual's step "
        "is not injective, so a capped mover or a set-rather-than-toggled "
        "cell re-converges. The case for the change survives -- what matters "
        "is whether the anchor was wrong WHEN a probe was designed, and it "
        "was, 35 times of 52.",
        "GAPS.md R2-1 said a default leg cannot see its own drift. In fact "
        "certify.cheap has computed it every beat since P-8 and written it "
        "into report['replay_steps'], which never reaches disk. The quantity "
        "was measured all along and filed as an audit line nobody read as the "
        "error of the frame the probes were designed against.",
        "R2's replay harness was checked before its number was built on: it "
        "rolls the manual over [s.action for s in prefix.steps] (beginning "
        "with RESET) while inner/loop._roll_forward rolls it over "
        "store.actions (that list shifted by one, trailing None). Different "
        "sequences. Recomputed on every probe: equal on 52 of 52, disagreed "
        "on 0. R2's 35 is a fact about the arm, not an artefact of its "
        "harness.",
    ],
    "switch": {
        "default": "rolled -- AnchorConfig().mode, byte-identical to "
                   "2026-07-31: same hypotheses, same order, same ids, same "
                   "predictions, and design()'s report grows no key",
        "flag": "python -m harness.run --anchor observed",
        "env": "THEORIA_ANCHOR=observed (positive whitelist; 1, true, "
               "OBSERVED, observed! and the empty string all stay on rolled)",
        "explicit": "TheoriaArm(..., anchor=AnchorConfig(mode='observed'))",
        "plumbing": "the same path as --goal-protocol / --probe-economy / "
                    "--desk-diet / --frontier",
        "orthogonal_to_frontier": "yes -- the 2x2 is measured, and the two "
                                  "axes are not additive",
    },
    "closes": {
        "GAPS.md R2-1": "a leg on the default can now see its own drift. The "
                        "per-turn series goes to anchor.jsonl and anchor.json "
                        "-- files that did not exist before -- so no existing "
                        "artefact moves a byte and the byte-identity "
                        "guarantee R2 chose over the diagnostic is kept "
                        "rather than traded away.",
    },
    "changed": [
        "theoria-arm/inner/anchor.py (new)",
        "theoria-arm/inner/probe.py",
        "theoria-arm/inner/loop.py",
        "theoria-arm/harness/run.py",
        "theoria-arm/tests/test_anchor.py (new)",
        "theoria-arm/DECISIONS.md",
        "theoria-arm/GAPS.md",
        "theoria-arm/PARTNER_SYNC.md",
    ],
    "not_changed": [
        "theoria-arm/inner/certify.py -- deliberately, and "
        "tests/test_anchor.py::test_certify_never_reads_the_anchor fails the "
        "day anybody wires the two together",
        "inner/surprise.py -- the taxonomy stays at seven",
        "engine-rig, theory-compiler, proxy, CONTRACTS (read only)",
        "any runs/ directory other than this one",
        "the main worktree",
    ],
    "tests": {
        "new_file": "tests/test_anchor.py (16 tests)",
        "negative_controls": [
            "test_no_drift_means_no_change -- on an undrifted manual the "
            "transplant is the identity and every anchored prediction is "
            "byte-identical to the rolled one, hypothesis for hypothesis. The "
            "acceptance: a switch that changed the answer when there was "
            "nothing to correct would not be re-anchoring.",
            "its partner test_drift_means_the_predictions_move asserts the "
            "predictions DO move when there is drift, so neither is vacuous",
            "the environment switch is handed nine near-misses and asserted "
            "off",
            "an unanchorable turn (no frame observed yet) is asserted to fall "
            "back to the rolled frontier and to SAY it did, rather than to "
            "anchor on nothing",
            "divergence() is asserted to return None with a reason on three "
            "unmeasurable cases, never 0",
            "drift_summary()'s denominator is asserted to exclude the turns "
            "it could not measure, so an unmeasured turn cannot read as a "
            "clean one",
            "the default path is asserted byte-identical WHILE the new "
            "anchor= argument is passed",
            "certify is asserted to take no anchor parameter and to contain "
            "neither 'anchor' nor '_roll_forward' in its source",
        ],
    },
    "residual_gaps": [
        "R3-1: protecting one instrument is not having two -- GAP 3 still "
        "shuts both Lean routes, so the replay remains the only detector of a "
        "wrong rule",
        "R3-2: no live evidence; the 2x2 is containment on states the ROLLED "
        "anchor produced, and 4 of the 52 would not have been bought at all "
        "under the observed anchor",
        "R3-3: the 9 still missed are the expressivity residue and are now "
        "the whole residue; a confirmed edge hypothesis has no home in the "
        "DSL, which is theory-compiler's grammar change",
        "R3-4: the archived drift series is per certify beat, not per turn, "
        "and four certify rounds are unreconstructed because the archived "
        "report carries no replay to reproduce",
    ],
    "what_a_live_run_would_cost_and_settle": {
        "not_run": "the programme is over its spend ceiling and this ticket "
                   "had zero spend authority",
        "shape": "ONE leg, not two -- the archive plus anchor.jsonl supplies "
                 "the rolled control for free. One carried leg on "
                 "g50t-5849a774 or sk48-d8078629 with --anchor observed, at "
                 "the R1b budget.",
        "cost_usd": "16-19, from the measured $2.695 carried-manual desk call "
                    "and R1b-g50t-a's 8 certify rounds; NOT from a cold run's "
                    "basis, which GAPS.md E3-3 records as wrong by 2.1x",
        "settles": "whether manual on a correctly anchored frontier is RIGHT "
                   "on a live leg, and whether width-1 collapse stays rare. "
                   "Neither is decidable offline: a live leg's states are the "
                   "states this change itself produces.",
        "does_not_need_to_settle": "the drift magnitudes, which are measured "
                                   "here off the archive at no cost",
    },
    "sealed_pile_contact": "none. Development-pile games only "
                           "(g50t-5849a774, sk48-d8078629).",
    "spend": {"usd": 0.0, "arc_actions": 0, "model_calls": 0,
              "network": "none"},
    "reproduce": [
        "cd theoria-arm/runs/20260801T1200Z-R3-anchor-duality",
        "python measure_drift.py --legs-root ../",
        "python replay_anchor.py --legs-root ../",
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
