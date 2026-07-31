# -*- coding: utf-8 -*-
"""One-shot MANIFEST writer for this run record (kept for provenance)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RD = Path(__file__).resolve().parent

files = [
    ROOT / "freeze" / "u3.py",
    ROOT / "freeze" / "tests" / "test_u3.py",
    RD / "u3_table.md",
    RD / "u3_table.json",
    RD / "RUN_STATE.md",
]
man = {
    "prompt_id": "closeout/u3-e1",
    "prompt": ("Implement U3 (E1, primary endpoint one) attainment evaluator "
               "per frozen STATS_RULES.md 1.2/1.2.1; CLI + tests + negative "
               "controls + sweep over all theoria-arm and A0 runs"),
    "branch": "closeout/u3-e1",
    "base_commit": "f6a95719",
    "utc": "2026-07-31T15:46:00Z",
    "seed": None,
    "files": [{"path": str(f.relative_to(ROOT)).replace("\\", "/"),
               "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
              for f in files],
    "notes": ("sweep read the MAIN tree theoria-arm/runs read-only while two "
              "live legs ran; gate: 29 passed in 14.00s"),
}
(RD / "MANIFEST.json").write_text(json.dumps(man, indent=1) + "\n",
                                  encoding="utf-8")
print("wrote", RD / "MANIFEST.json")
