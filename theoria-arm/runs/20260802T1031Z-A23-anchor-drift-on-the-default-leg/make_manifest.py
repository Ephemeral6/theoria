"""This directory's manifest, re-derivable from the directory.

This run has no `ledger.jsonl` -- it made no API call and no model call -- so
`armtools.backfill.classify` reads it as a `process_record` and
`verify_provenance`'s re-derivation check correctly skips it: there is nothing
to derive it *from*. The four required fields are written by hand and the file
list is hashed off the disk.

    python make_manifest.py
"""

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                       # noqa: E402,F401

from armtools import backfill                           # noqa: E402

SLUG = os.path.basename(HERE)

PAYLOAD = {
    "prompt_id": "A23-anchor-drift-on-the-default-leg",
    "branch": "agent/a23-anchor-drift-on-the-default-leg",
    "base_commit": "1e5b3f00dfb40fcc73f582a5de2390d1d3466844",
    "utc": "2026-08-02T10:31:24Z",
    "territory": "theoria-arm",
    "lane": "measurement",
    "cell": "A23",
    "classification": {
        "kind": "process_record",
        "archive_material": False,
        "why": "no ledger.jsonl: no API call, no model call, no network. "
               "Every number here is read off artefacts that were already on "
               "disk.",
    },
    "what":
        "GAP R2-1 said a leg on the default frontier cannot see its own "
        "anchor drift, because keeping `--frontier ablation` byte-identical "
        "means the anchor block is written only when a switch is on. R3 paid "
        "the forward half of that trade (`anchor.jsonl`, written by every leg "
        "from now on). This pays the backward half: `armtools/anchor_drift.py` "
        "computes the drift triple -- probes / drifted / drifted-and-off-"
        "frontier -- for any archived leg, offline, from `probes.jsonl` and "
        "`trace.jsonl`. The four R1/R1b legs had never had an anchor number "
        "taken at all and now have one; the four legs R2 measured are "
        "recomputed by a reader that shares no code with R2's and reproduce "
        "35 of 52 exactly, per leg and per probe.",
    "measurement": {
        "reads": ["runs/<leg>/probes.jsonl (tracked)",
                  "runs/<leg>/trace.jsonl (gitignored; absent in a clone, and "
                  "then refused per leg and measured null, never zero)"],
        "legs": 8,
        "probes": 72,
        "drifted": 47,
        "drifted_and_off_frontier": 47,
        "drifted_and_on_frontier": 0,
        "anchored_and_off_frontier": 20,
        "on_frontier_anywhere_in_the_archive": 5,
        "on_frontier_note": "all 5 are on 20260731T1500Z-A3-sk48-carried-l1, "
                            "all 5 were anchored, and all 5 were named by the "
                            "`manual` hypothesis. On the other seven legs "
                            "on-frontier is 0 of 16 anchored and 0 of 40 "
                            "drifted, so the whole drifted-vs-anchored "
                            "contrast comes from one leg (Fisher one-tailed "
                            "p ~ 0.004). See GAP A23-3.",
        "distinct_experiments": 56,
        "deduplicated_triple": [56, 33, 33],
        "deduplicated_note": "16 of the 72 rows are byte-identical repeats of "
                             "an experiment already run on the same leg (8 of "
                             "them on sk48-carried-l1). The arm as it stands "
                             "today refuses these. See GAP A23-5.",
        "recorded_vs_recomputed_before_hash_disagreements": 0,
        "recorded_vs_recomputed_note": "a tamper check, not a second reader: "
                                       "`to_jsonl` writes both columns off the "
                                       "same Step objects and `load_store` "
                                       "replays the same production "
                                       "`add`/`current`/`grid_hash`, so they "
                                       "agree by construction. The genuine "
                                       "independent-implementation crosscheck "
                                       "is the one against R2's reader.",
        "anchored_ids_equal_the_theorize_turns_on": [
            "20260731T231654Z-R1-g50t-a", "20260801T001851Z-R1b-g50t-a",
            "20260801T001851Z-R1b-sk48-b",
            "20260731T1430Z-A3-level2-carried-r3"],
        "anchored_ids_differ_from_the_theorize_turns_on": [
            "20260731T1310Z-A3-level2-carried-r2 (theorize at turn 1 did not "
            "re-seat the anchor)",
            "20260731T1500Z-A3-sk48-carried-l1 (the anchor survives 1-2 "
            "probes past each re-seat)"],
        "new_triples": {
            "20260731T231654Z-R1-g50t-a": [5, 3, 3],
            "20260731T231654Z-R1-sk48-b": [0, 0, 0],
            "20260801T001851Z-R1b-g50t-a": [14, 9, 9],
            "20260801T001851Z-R1b-sk48-b": [1, 0, 0],
        },
        "recomputed_triples": {
            "20260731T1240Z-A3-level2-carried": [0, 0, 0],
            "20260731T1310Z-A3-level2-carried-r2": [8, 7, 7],
            "20260731T1430Z-A3-level2-carried-r3": [28, 21, 21],
            "20260731T1500Z-A3-sk48-carried-l1": [16, 7, 7],
        },
        "crosscheck": {
            "against": "runs/20260801T0900Z-R2-frontier-by-generation/"
                       "MEASUREMENT.json",
            "probes_compared": 52,
            "per_leg_disagreements": 0,
            "per_probe_disagreements": 0,
            "equal": True,
        },
    },
    "negative_controls": {
        "count": 9,
        "all_held": True,
        "detail": "NEGATIVE_CONTROLS.json",
        "shape": "per manual (two of them, one per development-pile game): a "
                 "self-consistent leg required to drift on exactly no probe, a "
                 "mispredicting leg required to drift on exactly [P-04, P-05] "
                 "(derived from the roll arithmetic, not restated), and a "
                 "cascade leg answering each command in four frames whose "
                 "triple must equal the flat leg's. Plus three refusals, each "
                 "required to name its own reason: NO_TRACE, NO_PROBES, "
                 "NO_LEG.",
        "why_the_predicates_are_sets_not_signs":
            "`drifted == 0` counts only True and folds an unknown anchor into "
            "the same zero, so a leg whose trace notes no longer join would "
            "pass it; `drifted > 0` accepts the check firing in the wrong "
            "place, and did -- a comment here predicted P-03 onward while the "
            "output said P-04, P-05. Every control now also asserts "
            "anchor_unknown == 0 and that the world moved.",
        "what_they_cannot_witness":
            "the archive's `drifted => off_frontier` implication. The "
            "mispredicting wrapper freezes the state, so at the drifted probes "
            "every hypothesis consulting `step` returns the frozen frame and "
            "the frontier collapses to width 1 -- those probes are "
            "off-frontier because of the collapse. On the toy manual the "
            "collapse is strictly wider than the drift (P-03 collapsed and "
            "anchored, P-04 both). See GAP A23-3.",
    },
    "changed": [
        "theoria-arm/armtools/anchor_drift.py (new)",
        "theoria-arm/tests/test_anchor_drift.py (new, 27 tests)",
        "theoria-arm/DECISIONS.md (+D-A23-001)",
        "theoria-arm/GAPS.md (+GAP A23-1, +GAP A23-2)",
        "theoria-arm/runs/20260802T1031Z-A23-anchor-drift-on-the-default-leg/"
        " (new)",
        "PARTNER_SYNC.md (one appended section)",
    ],
    "not_changed": [
        "every archived run directory, including the eight measured here: "
        "adding a file to one re-derives its manifest differently and turns "
        "verify_provenance check 8 red (GAP A23-1)",
        "inner/, world/, harness/ -- nothing in the arm's own path was "
        "touched, so no leg's bytes can move",
        "runs/20260801T0900Z-R2-frontier-by-generation/ -- read, never written",
    ],
    "residual_gaps": ["GAP A23-1", "GAP A23-2", "GAP A23-3", "GAP A23-4",
                      "GAP A23-5"],
    "sealed_pile_contact": "none. Development pile only "
                           "(g50t-5849a774, sk48-d8078629), read from "
                           "artefacts already on disk.",
    "spend": {"usd": 0.0, "arc_actions": 0, "model_calls": 0,
              "network": False},
    "reproduce": [
        "cd theoria-arm/runs/20260802T1031Z-A23-anchor-drift-on-the-default-leg",
        "python measure_anchor_drift.py",
        "python negative_controls.py",
        "cd ../.. && python -m pytest tests/test_anchor_drift.py -o addopts= -q",
    ],
}


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
