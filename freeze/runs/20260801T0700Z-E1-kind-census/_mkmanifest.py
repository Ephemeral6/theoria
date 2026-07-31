# -*- coding: utf-8 -*-
"""MANIFEST writer for this run record — hashes derived, never typed."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RD = Path(__file__).resolve().parent

files = [
    ROOT / "freeze" / "theorem_shape.py",
    ROOT / "freeze" / "u3.py",
    ROOT / "freeze" / "tests" / "test_u3_kind.py",
    RD / "census.py",
    RD / "compare.py",
    RD / "census.json",
    RD / "CENSUS.md",
    RD / "COMPARISON.md",
    RD / "RUN_STATE.md",
]
base = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "master"],
                      capture_output=True, text=True).stdout.strip()
branch = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
man = {
    "prompt_id": "r2/u3-kind",
    "prompt": ("Repair the three defects exam found in freeze/u3.py (E1, U3 "
               "attainment): F1 the non-triviality gate keys on theorem names; "
               "D1 only theory.lean is discovered; D2 expand_targets descends "
               "one level.  Classify by what a theorem PROVES, split `vacuous` "
               "from `unclassified`, re-run the census."),
    "branch": branch,
    "base_commit": base,
    "utc": "2026-08-01T07:00:00Z",
    "seed": None,
    "files": [{"path": str(f.relative_to(ROOT)).replace("\\", "/"),
               "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
              for f in files],
    "notes": ("offline: Lean 4.9.0 only, no API/model/network.  gates: "
              "`python -m pytest freeze -q` 52 passed; `bash freeze/verify.sh` "
              "3 failed, IDENTICAL to clean master in this worktree (MANIFEST "
              "drift, BUDGET_TABLE drift, locations findings in arc-recon/ "
              "proxy/ theoria-arm run dirs) -- no stage moved.  census: 24 "
              "books, discharged 14->17, vacuous 9->2, unclassified 0->4, "
              "failing_obligation 1->1."),
}
(RD / "MANIFEST.json").write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n",
                                  encoding="utf-8")
print("wrote", RD / "MANIFEST.json")
