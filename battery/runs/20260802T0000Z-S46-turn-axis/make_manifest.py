"""Write this run's MANIFEST.json from the tree, not from memory.

Required by `CLAUDE.md`: `prompt_id`, `branch`, `base_commit`, `utc`, plus a
per-file sha256 of everything the run delivers.

    cd <repo> && python battery/runs/20260802T0000Z-S46-turn-axis/make_manifest.py
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

PROMPT_ID = "S46-turn-costs-mixes-two-axes"
UTC = "2026-08-02T00:00:00Z"
BASE_COMMIT = "d10788f7"

# What the ticket delivers, relative to the repo root.
DELIVERED = [
    "battery/model.py",
    "battery/metrics/economy.py",
    "battery/adapters/ledger_jsonl.py",
    "battery/audit/frontload.py",
    "battery/audit/live_economy.py",
    "battery/audit/live_arm.py",
    "battery/audit/exploits/economy.py",
    "battery/audit/v9/mutants.py",
    "battery/run_battery.py",
    "battery/freeze.py",
    "battery/PREREG_E2L.md",
    "battery/BATTERY_V1.md",
    "battery/tests/test_turn_axis.py",
    "battery/tests/test_metrics.py",
    "battery/tests/test_v9_defences.py",
    "battery/tests/test_live_economy.py",
    "battery/tests/test_threat_and_frontload.py",
    "battery/artifacts_live/frontload_e2l.json",
    "battery/artifacts_live/live_economy.json",
    "battery/artifacts_live/live_arm_readings.json",
]

EVIDENCE = [
    "RUN_STATE.md",
    "probe_blast_radius.py", "blast_radius.json",
    "probe_live_legs.py", "live_legs.json",
    "probe_tiers.py", "tiers_master.json", "tiers_branch.json",
    "tiers_branch2.json",
    "probe_cells.py", "cells_master.json", "cells_branch.json",
    "append_prereg_amendment.py", "repin_freeze.py", "make_manifest.py",
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
        "prompt": "monitor/board/items/%s.md" % PROMPT_ID,
        "utc": UTC,
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": BASE_COMMIT,
        "head_commit": git("rev-parse", "HEAD"),
        "territory": "battery",
        "worker": "W-9205",
        "api_spend_usd": 0.0,
        "network": "none -- every number here is recomputed offline",
        "sealed_pile_contact": "none; dev-pile g50t/sk48 legs read only",
        "what": (
            "Removes the fallback in Run.turn_costs() that substituted a "
            "call's enumeration index for a missing Call.turn and shared one "
            "bucket dictionary with the real labels "
            "(freeze/RESIDUALS.json E2-AXIS). The axis is now reported by "
            "Run.turn_axis() and E2/E3 refuse rather than degrade."),
        "results": {
            "suite": "470 passed, 0 failed",
            "verify_py": "green on all 8 rungs",
            "v9_demotions": {"master": 38, "branch": 38, "promotions": 0},
            "tier_moves": 0,
            "metric_cells_compared": 4028,
            "metric_cells_moved": 0,
            "frontload_n_evaluable": {"before": 8, "after": 7},
            "legs_refused_by_G6": ["20260731T231654Z-R1-g50t-a",
                                   "20260731T231654Z-R1-sk48-b"],
        },
        "deviations": [
            "Acceptance item 3 was delivered differently: E2L is NOT gated on "
            "join_confidence. Reasons and evidence in RUN_STATE.md section 5; "
            "reported to monitor at monitor/inbox/"
            "2026-08-02T0000Z-W-9205-s46-turn-axis-landed-and-one-deviation.md",
        ],
        "gaps": [
            "E2-AXIS clears_when (b) needs `轴的效度` in papers/*.md; papers/ "
            "is another territory and was not touched.",
            "adapters/theoria_live.py:268 still hardcodes Call.step_idx=None "
            "(PREREG_E2L.md section 5 defers it to its own ticket).",
            "battery/artifacts/gaming_audit.json still drifts by design "
            "(PREREG_V9.md section 5).",
        ],
        "files": entries(DELIVERED, REPO),
        "evidence": entries(EVIDENCE, HERE),
    }
    dest = os.path.join(HERE, "MANIFEST.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s (%d delivered, %d evidence)"
          % (dest, len(doc["files"]), len(doc["evidence"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
