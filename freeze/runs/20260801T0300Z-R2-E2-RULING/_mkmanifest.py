# -*- coding: utf-8 -*-
"""MANIFEST writer for this run record (freeze's own convention, kept for provenance).

Same shape as freeze/runs/20260731T1546Z-U3-E1-IMPL/_mkmanifest.py: the manifest
is derived from the files on disk, never hand-written, so a hash in it is a hash
somebody can reproduce.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RD = Path(__file__).resolve().parent

files = [
    ROOT / "freeze" / "STATS_RULES.md",
    ROOT / "freeze" / "CLAIMS_TEXT.md",
    ROOT / "freeze" / "MANIFEST_DRAFT.md",
    ROOT / "freeze" / "MANIFEST.json",
    ROOT / "freeze" / "RESIDUALS.json",
    ROOT / "freeze" / "build_manifest.py",
    ROOT / "freeze" / "e2_withdrawal.py",
    ROOT / "freeze" / "verify.sh",
    ROOT / "monitor" / "inbox" /
    "2026-08-01T0300Z-freeze-to-battery-e2-withdrawn-and-turn_costs-mixes-two-axes.md",
    RD / "RUN_STATE.md",
    RD / "gate_e2_withdrawal.txt",
    RD / "verify_baseline.txt",
    RD / "verify_after.txt",
]

man = {
    "prompt_id": "r2/freeze-e2",
    "prompt": ("Act on battery's E2 verdict: rule on the front-loading paired "
               "difference as a frozen primary endpoint, produce the "
               "replacement wording in STATS_RULES.md and CLAIMS_TEXT.md, and "
               "make freeze/MANIFEST.json's readiness reflect the ruling"),
    "branch": "r2/freeze-e2",
    "base_commit": "af138a0d",
    "utc": "2026-08-01T03:00:00Z",
    "seed": None,
    "ruling": {
        "endpoint": "前载指数配对差 (Theoria.md:373 primary endpoint 3; battery metric id E2)",
        "verdict": "WITHDRAWN from the confirmatory family, demoted to exploratory",
        "where": "freeze/STATS_RULES.md §3.0",
        "holm_divisor_after": 3,
        "primary_slots": 3,
        "in_confirmatory_family_after": 2,
        "computable_today": 0,
        "evidence": {
            "attack": "batched-turn-label-coherent",
            "value": 0.973387097,
            "target": 0.95,
            "reachability": "arm-reachable",
            "poverty_certified": True,
            "breaks": [],
            "source": "battery/artifacts_live/frontload_e2l.json",
        },
        "why_not_a_threshold": ("the endpoint has no threshold -- it is a "
                                "Wilcoxon/sign test under Holm; what failed is "
                                "the validity of the bucketing axis"),
        "why_not_E2L": ["PREREG_V9 R1 demotes only",
                        "E2L has not passed process 1 and is not in REGISTRY",
                        "E2L itself reaches 1.0 under first-turn-bill-coherent",
                        "n_paired_games = 0, so no calibration is possible"],
    },
    "gates": {
        "freeze/verify.sh": {"baseline_failures": 3, "after_failures": 2,
                             "moved": ["[12] MANIFEST.json FAIL -> PASS",
                                       "[19] new stage, PASS + PASS"],
                             "unchanged_red": ["[15b] BUDGET_TABLE (live round "
                                               "is spending; regenerating "
                                               "mid-round would pin a moving "
                                               "balance)",
                                               "[18] locations (all 11 findings "
                                               "are other territories' run "
                                               "dirs)"]},
        "freeze/e2_withdrawal.py --selftest": "8/8, every control demonstrated to fire",
        "freeze/residuals.py --verify": "green (E2-AXIS, E2-BACK registered)",
        "freeze/build_manifest.py --verify": "green after regeneration",
    },
    "files": [{"path": str(f.relative_to(ROOT)).replace("\\", "/"),
               "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
              for f in files],
    "notes": ("offline only: zero API calls, zero spend, zero sealed-pile "
              "contact, no directory containing R1 was read or written. "
              "battery/ was read-only; the cross-territory request went to "
              "monitor/inbox/."),
}

(RD / "MANIFEST.json").write_text(
    json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("wrote", RD / "MANIFEST.json")
