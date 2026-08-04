"""Write this run's MANIFEST.json from the tree, not from memory.

Required by `CLAUDE.md`: `prompt_id`, `branch`, `base_commit`, `utc`, plus a
per-file sha256 of everything the run delivers.  Same shape as
`battery/runs/20260802T0000Z-S46-turn-axis/make_manifest.py` -- the
territory's own tool, copied forward rather than reinvented.

    cd <repo> && python battery/runs/20260804T1330Z-B12-live-companions/make_manifest.py
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

PROMPT_ID = "B12-live-readings-predate-several-legs"
UTC = "2026-08-04T13:30:00Z"
BASE_COMMIT = "4846e66d"

DELIVERED = [
    "battery/audit/live_census.py",
    "battery/artifacts_live/live_census.json",
    "battery/tests/test_live_census.py",
    "battery/verify.py",
    "battery/freeze.py",
    "battery/BATTERY_V1.md",
]

EVIDENCE = [
    "RUN_STATE.md",
    "probe_refresh.py", "refresh.json",
    "probe_shape_floor.py", "shape_floor.json",
    "gate_pytest.txt", "gate_verify.txt",
    "make_manifest.py",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.check_output(
        ["git"] + list(args), cwd=REPO).decode().strip()


def entries(paths, root):
    out = []
    for rel in paths:
        path = os.path.join(root, rel.replace("/", os.sep))
        if not os.path.isfile(path):
            print("  missing, skipped: %s" % rel, file=sys.stderr)
            continue
        out.append({"path": rel, "sha256": sha256(path),
                    "bytes": os.path.getsize(path)})
    return sorted(out, key=lambda e: e["path"])


def main():
    doc = {
        "prompt_id": PROMPT_ID,
        "prompt": ("no board item exists: monitor/board/items/ carries no B* "
                   "item at 4846e66d, and none appears in done/, claimed/, "
                   "board.log or git history. The dispatch prompt was the "
                   "whole brief."),
        "utc": UTC,
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": BASE_COMMIT,
        "head_commit": git("rev-parse", "HEAD"),
        "territory": "battery",
        "api_spend_usd": 0.0,
        "network": "none -- every number here is recomputed offline",
        "sealed_pile_contact": (
            "none; dev-pile g50t-5849a774 / sk48-d8078629 legs read only. The "
            "pile guard now runs over the whole archive, and the one test "
            "that needs a sealed id reads it from arc-recon/data/piles.json "
            "at run time rather than writing it down."),
        "what": (
            "The brief's premise was tested first and is false: all five "
            "existing artifacts_live/ companions recompute byte-identically "
            "(refresh.json, 0 of 6 moved), because S46 already brought the "
            "R1/R1b/R2/R2b legs in on 2026-08-02. The real defect is one "
            "level down: theoria_live.discover filters by campaign label "
            "BEFORE load_leg, so 14 live-arm leg archives are in neither the "
            "runs map nor the excluded list of either companion, and no rung "
            "can turn red over them. battery/audit/live_census.py walks the "
            "archive unfiltered, gives every ledger a named disposition, "
            "runs the pile guard over all of it, and verify.py rung 9 gates "
            "it."),
        "results": {
            "companions_recomputed": 6,
            "companions_moved": 0,
            "metrics_changed": 0,
            "archive_dirs": 79,
            "archive_ledgers": 37,
            "scored": 14,
            "excluded_with_reason": 9,
            "invisible_to_every_rung": 14,
            "invisible_env_steps": 682,
            "invisible_billed_calls": 42,
            "invisible_billed_usd": 23.855414,
            "min_turns_for_shape": 8,
            "legs_clearing_shape_floor": 1,
            "cumulative_live_usd_over_scored_legs": 124.639439,
            "suite": "491 passed",
            "verify_py": "green on all 9 rungs",
            "freeze_check": "empty",
            "readings_drift": "empty",
            "frozen_artifacts_touched": 0,
        },
        "deviations": [
            "The ticket asked what moved in the live readings. Nothing moved; "
            "the answer is reported as a digest table rather than a metric "
            "list, and the work went to the gap that made the question "
            "unanswerable by the rungs.",
        ],
        "gaps": [
            "The census does not close the gap it found: 14 live legs, 682 "
            "env steps and 23.86 USD remain outside every reading. The "
            "campaign label is theoria-arm's; raised via monitor/inbox/.",
            "Only this territory's adapter was audited. baseline-arms and "
            "ablation-arm have their own discovery paths and were not "
            "checked -- out of territory, stated rather than assumed clean.",
            "The A26b legs in flight were deliberately not read. When they "
            "land, rungs 7, 8 and 9 all go red until the companions are "
            "regenerated, which is the designed behaviour.",
            "n_dirs counts directories; 42 of 79 carry no ledger and are "
            "counted but not classified. A leg archive shipping its ledger "
            "under a different name would be missed the way discover misses "
            "an unlabelled one.",
            "Rung 9 cross-checks the census against rung 7's companion only; "
            "live_economy.json is covered transitively by rung 8.",
        ],
        "files": entries(DELIVERED, REPO),
        "evidence": entries(EVIDENCE, HERE),
    }
    dest = os.path.join(HERE, "MANIFEST.json")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s (%d delivered, %d evidence)"
          % (dest, len(doc["files"]), len(doc["evidence"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
