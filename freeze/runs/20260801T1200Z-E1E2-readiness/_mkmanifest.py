# -*- coding: utf-8 -*-
"""MANIFEST writer for this run record — hashes derived, never typed."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RD = Path(__file__).resolve().parent

files = [
    ROOT / "freeze" / "build_manifest.py",
    ROOT / "freeze" / "MANIFEST.json",
    ROOT / "freeze" / "MANIFEST_DRAFT.md",
    ROOT / "freeze" / "verify.sh",
    ROOT / "freeze" / "tests" / "test_budget_hold.py",
    ROOT / "monitor" / "inbox"
         / "20260801T1200Z-freeze-to-exam-the-flip-list-was-four-measured-it-is-six.md",
    RD / "recensus.py",
    RD / "mutations.py",
    RD / "census.json",
    RD / "CENSUS.md",
    RD / "exam_u3_census_measured.txt",
    RD / "budget_now.json",
    RD / "gates_before.txt",
    RD / "gates_after.txt",
    RD / "mutations.txt",
    RD / "RUN_STATE.md",
]
base = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "master"],
                      capture_output=True, text=True).stdout.strip()
branch = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
man = {
    "prompt_id": "z/freeze-e2u3",
    "prompt": ("freeze territory, 2026-08-01: (1) re-run the E1 census after "
               "the U3/E1 non-triviality repair and file the exact list of "
               "exam tests that must flip; (2) restate the three primary "
               "endpoints after battery's E2 ruling withdrew the front-loading "
               "paired difference; (3) make freeze/MANIFEST.json readiness "
               "reflect reality, including a NEGATIVE remaining_measured_usd "
               "-- record the money, do not fix it."),
    "branch": branch,
    "base_commit": base,
    "utc": "2026-08-01T12:00:00Z",
    "seed": None,
    "files": [{"path": str(f.relative_to(ROOT)).replace("\\", "/"),
               "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
              for f in files],
    "notes": ("offline: Lean 4.9.0 only. ZERO API call, zero model call, zero "
              "network, zero spend, zero sealed-pile contact. gates: "
              "`python -m pytest freeze -q` 62 passed (52 -> 62, +10 new); "
              "`bash freeze/verify.sh` 79 PASS / 2 FAIL, baseline was 77/2 -- "
              "the only stages that moved are the two NEW checks in stage [20] "
              "and stage [14]'s blocking-gap count 19 -> 20. The two FAILs "
              "([15b] BUDGET_TABLE drift, [18] locations) are unchanged from "
              "clean master and both name other territories' in-flight work. "
              "census: 24 books, discharged 17 / vacuous 2 / unclassified 4 / "
              "failing_obligation 1 = 17 of 24 attained, reproducing the "
              "07:00Z run on a different checkout. exam: 6 failed / 15 passed, "
              "measured on z/exam-u3-followthrough@01d627e3 -- the 07:00Z "
              "letter derived four. budget: frozen remaining_measured_usd "
              "-35.1687, recomputed live -78.9347; item 12 held at `blocked` "
              "by BUDGET_HOLD_ITEMS; 7/7 mutations of that hold caught."),
}
(RD / "MANIFEST.json").write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n",
                                  encoding="utf-8")
print("wrote", RD / "MANIFEST.json")
