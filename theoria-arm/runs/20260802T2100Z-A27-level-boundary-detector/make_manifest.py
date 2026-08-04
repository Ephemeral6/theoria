"""Derive this run's MANIFEST.json. Byte-stable; no wall clock enters it.

The narrative fields are this run's own claims. Everything mechanical -- the
file list, the sizes, the sha256s -- is derived here and rendered through
`armtools.backfill.render`, so the manifest has the same shape and the same
serialisation as every other manifest in this archive.

This directory has no `ledger.jsonl` (no API call, no model call, no network),
so `armtools.backfill.classify` reads it as a `process_record` and
`verify_provenance`'s re-derivation check correctly skips it: there is nothing
to derive it from.

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


def _files():
    out = []
    for name in sorted(os.listdir(HERE)):
        if name == "MANIFEST.json" or name.startswith("__"):
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


def _measurement():
    path = os.path.join(HERE, "MEASUREMENT.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


PAYLOAD = {
    "prompt_id": "A27-level-boundary-detector",
    "branch": "w/a27-level-boundary",
    "base_commit": "b45400263428600a246408b2be6985ee84be63a9",
    "utc": "2026-08-02T21:00:00Z",
    "territory": "theoria-arm",
    "lane": "framework-change",
    "cell": "A27",
    "classification": {
        "kind": "framework-change-preparation",
        "archive_material": False,
        "why": "offline: no ARC action, no model call, no network, no ledger. "
               "Reads the three arms' existing ledgers and adds an instrument "
               "with a default-on free rung and a default-off paid rung. The "
               "paid rung has never dialled anything.",
    },
    "what": (
        "A27 asked what the arm reads and what it ignores at a level boundary. "
        "The board item's wording -- 'the arm cannot see a win even if it gets "
        "one' -- is half wrong and the surviving half is sharper. The arm "
        "already reads `levels_completed` off EVERY gameplay envelope in "
        "`_record` and fires `_on_level_boundary` synchronously, and reads "
        "`state == \"WIN\"` at the top of every turn; both of ARC's plausible "
        "level signals have been handled since `inner/levels.py` was written. "
        "What no code path read during a leg is the scorecard: `score`, "
        "`level_scores`, `level_actions`, `level_count` and "
        "`level_baseline_actions` appear on no gameplay response, and the only "
        "fetch was `close_scorecard` in `_finish` -- after `_main_loop` "
        "returns, on a card D-015 records as unrecoverable once closed. So the "
        "leg could never hold its own denominator: g50t level 1 costs a "
        "reference solver 78 actions, the best leg ever run spent 33, and that "
        "ratio was legible for free from the first RESET onward. Built: "
        "`inner/scoreboard.ScoreWatch`, a second witness that normalises "
        "envelope and scorecard readings into one shape, fires named events on "
        "a score / per-level-score / counter increase, cross-checks the two "
        "witnesses without resolving a disagreement, and computes the reach "
        "arithmetic every turn BEFORE theorize. Plus "
        "`ArcThroughProxy.read_scorecard` (GET, non-destructive, no action "
        "quota, one attempt, never raises) and `witnessed_wins.json`, which "
        "keeps the last frame of a cleared level -- the positive example R1b "
        "measured the desk waiting for."),
    "measurement": _measurement(),
    "the_number_the_ticket_turns_on": {
        "g50t_level_baseline_actions": [78, 175, 179, 230, 96, 54, 67],
        "source": "runs/20260728T012311Z-g50t-first-contact-salvage2/"
                  "ledger.jsonl, and 11 other ledgers carrying the same vector",
        "best_recorded_sum_level_actions": 33,
        "read_by_the_arm_during_a_leg_before_this_ticket": False,
        "read_by_the_arm_during_a_leg_after_this_ticket": "only on the "
            "`scorecard` rung, which is opt-in and has never run",
    },
    "negative_controls": [
        "a 12-step flat leg on the envelope rung reports `measured_absent` "
        "with zero events -- a MEASURED absence",
        "a single reading reports `not_measured` / `boundary_observed: null`, "
        "never `false` and never `0`",
        "a first reading against a card already carrying score 3.0 and three "
        "completed levels fires nothing: a floor is not a jump, and a "
        "fabricated boundary is the worst outcome available here",
        "a decrease fires nothing (a full reset would produce one)",
        "the two sources alternating fire nothing: each diffs against its own "
        "history, so an envelope's absent score cannot look like a score "
        "vanishing",
        "the `off` rung reads nothing and adds no key to the summary",
        "a leg with no boundary has an empty `witnessed_wins` and writes no "
        "file at all",
        "a scorecard claiming a completed level fires the watch, leaves "
        "`LevelLog` untouched, writes no witness, and `corroborate` says "
        "`disagree`",
        "an instrument that raises at a boundary does not end the leg: the "
        "boundary still lands and the error goes on the event",
        "a mock baseline is labelled `baseline_is_from_a_mock: true`",
    ],
    "synthetic_positives": [
        "a total-score jump fires `score_moved` with from/to",
        "a per-level score jump fires `level_score_moved` naming the level",
        "a counter jump fires `level_boundary` naming which source saw it",
    ],
    "untested_on_a_real_positive": (
        "No recorded leg contains a boundary. 2,700 `env_step` rows across "
        "theoria-arm, baseline-arms and ablation-arm: `levels_completed` is 0 "
        "on the 547 rows carrying it and absent on 2,153, `state` is "
        "NOT_FINISHED on all 547 and never WIN or GAME_OVER. All 47 "
        "recoverable scorecards read total_levels_completed 0, score 0.0 and "
        "all-zero level_scores. Every positive above is synthetic, and "
        "`test_no_recorded_leg_contains_a_real_boundary` asserts that state of "
        "the record so it fails the day it stops being true."),
    "changed": [
        "theoria-arm/inner/scoreboard.py (new)",
        "theoria-arm/tests/test_scoreboard.py (new)",
        "theoria-arm/inner/loop.py",
        "theoria-arm/harness/arc.py",
        "theoria-arm/harness/budget.py",
        "theoria-arm/DECISIONS.md",
        "theoria-arm/GAPS.md",
    ],
    "not_changed": [
        "inner/levels.py -- LevelLog remains the SOLE authority over `starts`, "
        "the snapshot and the dropped problem. The watch is a witness, never a "
        "trigger: a scorecard glitch must not be able to manufacture a "
        "boundary in the arm's own record",
        "inner/goal.py -- the rider that would carry a witnessed win is "
        "written in inner/scoreboard.py and is not wired to any theorize call",
        "inner/surprise.py -- the set stays closed at seven",
        "proxy/ -- another track's; the GET is issued through it, not added "
        "to it",
        "any runs/ directory whose name contains A26 (a live round is in "
        "flight)",
        "CONTRACTS/",
    ],
    "rungs": {
        "off": "byte-identical to a run made before inner/scoreboard.py "
               "existed: no readings, no summary key, no turn block",
        "envelope": "DEFAULT. Reads only fields already on every recorded "
                    "Step. No socket, no action, no model call, no dollar. It "
                    "changes the record, which is the thing A27 found silent",
        "scorecard": "opt-in. Adds bounded GET /api/scorecard/{card_id} "
                     "readings, one every 4 turns, at one request and zero "
                     "actions each. Never run",
    },
    "residual_gaps": [
        "the detector has never fired on a real positive and cannot until a "
        "leg clears a level (GAP A27-1)",
        "the paid rung has never dialled anything: the GET is exercised "
        "against a stubbed transport only, and whether proxy/ forwards a GET "
        "at all is unverified from this side (GAP A27-2)",
        "the path from a witnessed win to a goal clause stops at the seam: "
        "the observation half is wired, the rider is written and nothing "
        "calls it (GAP A27-3)",
        "Theoria.md Phase 2's 对账义务 is still owed -- readings go into the "
        "summary and the turn records, not into env_step, so "
        "archive.reconcile still writes score_reconciliation: unavailable "
        "(GAP A27-4)",
        "seven ledger files carry proxy/mock's [8, 8, 8] with nothing next to "
        "it saying so; named here, not rewritten (GAP A27-5)",
    ],
    "sealed_pile_contact": "none. Development-pile ids only (g50t-5849a774, "
                           "sk48-d8078629, ar25-0c556536), and only as strings "
                           "read out of existing ledgers.",
    "spend": {"usd": 0.0, "arc_actions": 0, "model_calls": 0,
              "network": "none"},
    "reproduce": [
        "cd theoria-arm/runs/20260802T2100Z-A27-level-boundary-detector",
        "python measure_boundaries.py",
        "python make_manifest.py",
        "cd ../.. && python -m pytest -q",
        "cd ../.. && python verify.py",
        "cd ../.. && python -m armtools.verify_provenance",
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
