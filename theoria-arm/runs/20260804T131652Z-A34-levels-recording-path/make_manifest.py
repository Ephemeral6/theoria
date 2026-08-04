"""Derive this run's MANIFEST.json. Byte-stable; no wall clock enters it.

The narrative fields are this run's own claims. Everything mechanical -- the
file list, the sizes, the sha256s -- is derived here and rendered through
`armtools.backfill.render`, so the manifest has the same shape and the same
serialisation as every other manifest in this archive.

This directory has no `ledger.jsonl` (no API call, no model call, no network),
so `armtools.backfill.classify` reads it as a `process_record` and
`verify_provenance`'s re-derivation check correctly skips it: there is nothing
to derive it from.

    python make_manifest.py            # write it
    python make_manifest.py --check    # re-derive and compare, byte for byte
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
    "prompt_id": "A34-levels-jsonl-recording-path",
    "branch": "q/a34-levels",
    "base_commit": "4846e66dee64940b3bb457b408db13775728915c",
    "utc": "2026-08-04T13:16:52Z",
    "territory": "theoria-arm",
    "lane": "framework-change",
    "cell": "A34",
    "classification": {
        "kind": "instrument-repair",
        "archive_material": False,
        "why": "offline: no ARC action, no model call, no network, no ledger. "
               "Every leg run here went through proxy/mock over a loopback "
               "socket with the mock's own literal fake key.",
    },
    "what": (
        "A34 asked whether the level-boundary detector is never called, called "
        "and never firing, or firing and never writing. Answer: called on "
        "every recorded step, never fired, and -- for every case but one -- it "
        "writes correctly when it does. Two things were established and one "
        "defect was found. (1) The mock legs' zero bytes are not evidence "
        "about the recording path: the offline explorer is "
        "`min(legal, key=(times_tried, id))`, which on the mock's level 1 "
        "oscillates between two cells forever, so no mock leg on the default "
        "policy can reach the goal at any budget -- 200 actions, 2 distinct "
        "positions, 0 completions. (2) The positive control that had never "
        "existed: a scripted mock leg through the real `harness.run.play` "
        "shell that genuinely reaches the goal writes a 263-byte "
        "`levels.jsonl` with the boundary in it, cuts `starts` at the right "
        "step, appends a `level` turn and captures the winning frame. Every "
        "earlier test of this path drove `TheoriaArm._record` directly with a "
        "hand-built envelope, which proves the unit and not the shell -- and "
        "the shell is what wrote the twenty-two empty files. (3) The defect: "
        "`LevelLog.observe` suppressed the event on the game's final level. "
        "The suppression is right for the DESTRUCTIVE half of the handling "
        "(the boundary handler drops problem.json and generated/, which on a "
        "winning run deletes the artefacts that say how it was won) and was "
        "silently extended to the RECORD, which it never covered. Measured on "
        "a synthetic 3-level win: `levels.jsonl` 2 rows, `ScoreWatch` 3 "
        "events, verdict `observed`, witnessed_wins 2. A seven-level g50t win "
        "would have written six rows and left the win itself off disk while "
        "the second instrument recorded all seven."),
    "measurement": _measurement(),
    "the_number_the_ticket_turns_on": {
        "levels_jsonl_files_on_disk": 22,
        "of_which_zero_bytes": 22,
        "leg_directories_swept": 30,
        "verdict_observed": 0,
        "verdict_evidence_missing": 0,
        "verdict_measured_absent": 11,
        "verdict_unmeasured": 19,
        "mock_explorer_distinct_positions_in_200_actions": 2,
        "levels_jsonl_bytes_on_the_first_leg_that_completed_a_level": 263,
        "rows_before_the_fix_on_a_three_level_win": 2,
        "rows_after_the_fix_on_a_three_level_win": 3,
    },
    "negative_controls": [
        "a leg that completed a level, with levels.jsonl truncated to zero "
        "bytes, reads as `evidence_missing` with levels_completed None -- not "
        "0 and not 1. This is A34's own closing section, built.",
        "the same leg aggregated with a genuine zero and a leg that never "
        "looked: legs_counted 1 of 3, the other two named rather than summed",
        "a leg with 4 envelopes carrying the counter and no increase reads "
        "`measured_absent` with 0 -- the one verdict under which a zero is "
        "honest",
        "a leg whose only trace row is a failed command reads `unmeasured` "
        "with None",
        "the default offline explorer over 200 mock actions: 2 distinct "
        "positions, 0 completions -- absence of a completion recorded as "
        "absence of a reachable goal, not as a broken detector",
        "the destructive half of the boundary handler is still refused at a "
        "win: problem.json survives, generated/ survives, starts is not cut, "
        "and levels.level does not become 4 in a 3-level game",
        "the pre-fix tree was re-run under the new tests (git stash of "
        "inner/): test_the_two_instruments_agree_about_the_winning_increment "
        "failed with '2 row(s) reached disk; the missing one is the win'. The "
        "test is red without the fix.",
    ],
    "synthetic_positives": [
        "a scripted mock leg through the real shell writes one "
        "`level_boundary` row and one witness with the winning grid",
        "a synthetic three-level win writes two `level_boundary` rows and one "
        "`game_won` row, and three witnesses",
    ],
    "untested_on_a_real_positive": (
        "No archived leg contains a real boundary: 30 leg directories, 0 "
        "`observed`, 0 `evidence_missing`, 11 `measured_absent`, 19 "
        "`unmeasured`. The same claim from the other side is pinned by A27's "
        "test_no_recorded_leg_contains_a_real_boundary over 2,700 env_step "
        "rows and 47 recoverable scorecards. Every positive here is synthetic "
        "or mock, and the fix is unexercised on a real one. What changed is "
        "that the instrument is now known to fire and known to write, so the "
        "next 'no boundary' is a measurement instead of an unfalsifiable "
        "sentence."),
    "the_two_instruments": (
        "A27's ScoreWatch and inner/levels.LevelLog contradicted each other on "
        "exactly one input -- the winning increment -- and neither could say "
        "so. `ScoreWatch.corroborate()` compares the envelope counter against "
        "a SCORECARD reading; it never compares its own event list against "
        "LevelLog's. On a won game the arm would have reported "
        "boundary_observed: true with a levels.jsonl short by one row and no "
        "`disagree` anywhere. They now agree by construction, and the test "
        "asserts boundaries + game_won == the free rung's event count. They "
        "are still reconciled by a test and not at runtime."),
    "changed": [
        "theoria-arm/inner/levels.py",
        "theoria-arm/inner/loop.py",
        "theoria-arm/armtools/level_evidence.py (new)",
        "theoria-arm/armtools/round.py",
        "theoria-arm/tests/test_levels_recording_path.py (new)",
    ],
    "not_changed": [
        "inner/scoreboard.py -- A27's territory and correct as it stands. The "
        "disagreement was LevelLog's silence, not ScoreWatch's speech.",
        "inner/surprise.py -- the set stays closed at seven; a win fires no "
        "surprise",
        "tests/test_levels.py -- every assertion in it, including "
        "test_winning_the_last_level_does_not_open_an_eighth, still holds "
        "unchanged",
        "proxy/ and proxy/mock -- another track's",
        "any runs/ directory whose name contains A26 (a live round is in "
        "flight). They were read by the sweep and not written.",
        "CONTRACTS/, PARTNER_SYNC.md, monitor/",
    ],
    "residual_gaps": [
        "unexercised on a real positive; the fix is proven on synthetic and "
        "mock boundaries only (GAP A34-1)",
        "`_on_game_won` has never run against a live API and cannot be run "
        "against the mock either: proxy/mock never returns `win_levels`, so "
        "`arc.win_levels` stays None and no mock leg can reach the "
        "final_level branch. It is exercised through hand-built envelopes "
        "only (GAP A34-2)",
        "LevelLog and ScoreWatch are reconciled by a test, not at runtime. A "
        "divergence introduced later is caught in pytest and nowhere in a leg "
        "(GAP A34-3)",
        "level_evidence reads trace.jsonl, which is written at _save_all, so "
        "a leg killed before that reads `unmeasured` even if its ledger holds "
        "the increment. The ledger is the stronger source and is not "
        "consulted (GAP A34-4)",
        "armtools/round.py's totals changed shape (levels_completed integer -> "
        "levels object). No round.json on disk was rewritten (GAP A34-5)",
    ],
    "sealed_pile_contact": "none. Development-pile ids only "
                           "(g50t-5849a774, ar25-0c556536), and the mock "
                           "world is proxy/mock's own synthetic maze.",
    "spend": {"usd": 0.0, "arc_actions": 0, "model_calls": 0,
              "network": "none"},
    "reproduce": [
        "cd theoria-arm && python -m pytest tests/test_levels_recording_path.py -q",
        "cd theoria-arm && python -m armtools.level_evidence runs",
        "cd theoria-arm && python -m pytest -q",
        "cd theoria-arm && python verify.py",
        "cd theoria-arm && python -m armtools.verify_provenance",
        "python runs/20260804T131652Z-A34-levels-recording-path/make_manifest.py --check",
    ],
}


def _payload():
    payload = dict(PAYLOAD)
    payload["files"] = _files()
    return payload


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    path = os.path.join(HERE, "MANIFEST.json")
    blob = backfill.render(_payload())
    if "--check" in argv:
        if not os.path.exists(path):
            print("FAIL: no MANIFEST.json to check")
            return 1
        with open(path, "rb") as fh:
            on_disk = fh.read()
        if on_disk == blob:
            print("OK: MANIFEST.json re-derives byte for byte (%d bytes)"
                  % len(blob))
            return 0
        print("FAIL: MANIFEST.json does not re-derive; the files moved under it")
        return 1
    with open(path, "wb") as fh:
        fh.write(blob)
    print("wrote %s (%d files)" % (path, len(_payload()["files"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
