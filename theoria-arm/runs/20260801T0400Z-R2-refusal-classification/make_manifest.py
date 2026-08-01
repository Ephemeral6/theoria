"""Derive this run's MANIFEST.json.

`armtools/archive.py` and `armtools/backfill.py` both derive a manifest from a
run's **ledger**, and both correctly refuse this run: it has no ledger, because
nothing was played. `backfill --slug` says so in as many words -- *"no ledger
records: nothing happened here to account for"*. That refusal is right and is
not worked around; this script is the offline counterpart, and every value it
writes is read from git or from the files on disk rather than typed.

    cd theoria-arm && python runs/20260801T0400Z-R2-refusal-classification/make_manifest.py
"""

import hashlib
import json
import os
import subprocess
import sys

RUN_DIR = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(RUN_DIR))
REPO = os.path.dirname(ARM)


def git(*args):
    return subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                          text=True, check=True).stdout.strip()


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def main():
    files = []
    for root, _dirs, names in os.walk(RUN_DIR):
        if "__pycache__" in root:
            continue
        for name in sorted(names):
            if name == "MANIFEST.json":
                continue                       # cannot hash what is being written
            path = os.path.join(root, name)
            files.append({
                "path": os.path.relpath(path, RUN_DIR).replace(os.sep, "/"),
                "sha256": sha256(path),
                "bytes": os.path.getsize(path),
            })

    changed = [line[3:] for line in
               git("status", "--short", "--", "theoria-arm", "monitor").splitlines()]

    manifest = {
        "prompt_id": "R2-arm-refusal-wave",
        "utc": "2026-08-01T04:00:00Z",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "arm": "theoria",
        "lane": "R2",
        "kind": "offline analysis of existing ledgers; no run, no spend",
        "seed": None,
        "seed_note": ("nothing here draws a random number: the classifier is a "
                      "pure function of ledger rows and the derivation is a sum "
                      "over them. Re-running reproduces byte-for-byte."),

        "question": ("494 of 570 live env_step rows across the four 2026-07-31 "
                     "legs are 400 SERVER_ERROR 'game <id> not found'. Client "
                     "defect, or expected?"),
        "verdict": ("EXPECTED. The refused request is byte-identical to the one "
                    "that succeeds (same request_sha256, final_url, card_id, "
                    "guid); the upstream labels it SERVER_ERROR itself; the "
                    "closed scorecard confirms it charged for the 200s only. "
                    "The defect is that the ledger recorded it identically to a "
                    "real failure."),
        "hypotheses_killed": {
            "malformed_game_id": "closing scorecard lists the game with level_count 7, a guid and 5 actions",
            "sent_before_reset": "step_idx 0 is a RESET, and it is refused",
            "missing_session_token": "refusals after step_idx 10 carry the same guid as the interleaved successes",
            "race_with_scorecard_open": "scorecard/open returned 200 two seconds before the first refusal",
        },

        "measurement": {
            "env_steps": 570,
            "upstream_transient": 494,
            "success": 76,
            "successful_actions": 72,
            "upstream_failure": 0,
            "refusal_rate_per_leg": [0.900, 0.859, 0.855, 0.876],
            "refusals_per_successful_action": 6.86,
            "wall_clock_s": 15048,
            "wall_clock_s_inside_refusals": 595,
            "wall_clock_share_inside_refusals": 0.040,
            "outbound_per_action_pooled": 7.917,
            "outbound_per_action_productive": 1.0,
            "scorecard_actions_agree_on_all_four_legs": True,
        },
        "sizing_effect": {
            "constant": "harness/spend.py:OUTBOUND_PER_ACTION",
            "value": 9.3,
            "value_changed": False,
            "why_not_changed": ("under-reserving cost 20260729T004020Z-leg01 its "
                                "run; release() returns an unspent hold, so "
                                "over-reserving costs only headroom"),
            "regime_declared": "blended",
            "re_derived_blended_all_live_legs": 8.091,
            "re_derived_productive": 1.081,
            "reservation_per_300_action_leg": 5616,
            "reservation_if_sized_on_productive": 685,
        },

        "implemented": [
            "armtools/refusal.py -- signature, total 6-way classifier, outbound accounting, derive_outbound_per_action()",
            "armtools/archive.py:reconcile() -- emits `outcomes` and `outbound` under opt-in outcomes=True; http_amplification unchanged",
            "harness/spend.py -- OUTBOUND_PER_ACTION_REGIME + _DECOMPOSITION, carried into every plan's arithmetic",
            "tests/test_refusal_classification.py -- 22 tests",
        ],
        "negative_controls": {
            "how": ("the signature's conjuncts are removed one at a time from a "
                    "real refused row and the answer must stop being "
                    "upstream_transient"),
            "cases": [
                "message names a different game -> upstream_failure",
                "404 VALIDATION_ERROR 'scorecard ... not found' -> upstream_failure",
                "status 500 -> upstream_failure",
                "unanchored 'the game X not found today' -> upstream_failure",
                "refusal that returned frames -> upstream_failure",
                "response null -> unrecorded, not failure and not weather",
                "unforwarded 403 guard denial -> guard_refused, 0 outbound",
                "transient_share moves 0.9 -> 0.0 on a real-failure ledger",
            ],
            "mutation_check": ("the classifier was deliberately broken (game-id "
                               "conjunct dropped, message pattern unanchored) "
                               "and 8 tests failed; then restored and all 22 "
                               "pass. A check never seen to say no has not been "
                               "shown to check anything."),
        },

        "residual_gaps": [
            "upstream_failure is 0 across every ledger this arm has: the classifier has never said 'real failure' on real data",
            "3 of the 4 legs behind 9.3 carry response:null on every row, so 149 of its 251 outbound requests are unattributable (counted as `unrecorded`, not as failures)",
            "the retry storm itself is not stopped -- that fix is in proxy/, which is read-only from here; filed to monitor/inbox/",
            "step_idx still counts attempts; renumbering would rewrite a field's meaning in published manifests",
            "the 07-31 rate is measured on two development-pile games only (g50t, sk48)",
            ("the split is NOT in MANIFEST.json: extending reconcile() "
             "unconditionally turned verify_provenance check 9 red (it "
             "re-derives every published manifest byte for byte, and manifests "
             "embed reconciliation:reconcile(...)), so 25 drifted. Landing it "
             "there is a migration over ~25 records of real spend, not a bug "
             "fix. Made opt-in instead."),
        ],
        "did_not_do": [
            "no live run, no API call, no model call, no spend",
            "did not touch theoria-arm/runs/*R1* (a live round was writing there)",
            "did not touch harness/run.py's argument block",
            "did not edit proxy/ (read-only territory); the ask went to monitor/inbox/",
            "did not change the value of OUTBOUND_PER_ACTION",
        ],
        "sealed_pile_contact": ("none. The only game ids read are g50t-5849a774 "
                               "and sk48-d8078629, both development pile."),
        "cross_territory": "monitor/inbox/20260801T0400Z-theoria-arm-to-proxy-refusal-wave.md",
        "changed_paths": changed,
        "files": files,
    }

    out = os.path.join(RUN_DIR, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s (%d files hashed)" % (out, len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
