# -*- coding: utf-8 -*-
"""MANIFEST writer for this run record — hashes derived, never typed."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RD = Path(__file__).resolve().parent

files = [
    ROOT / "freeze" / "u3.py",
    ROOT / "freeze" / "tests" / "test_u3_kind.py",
    RD / "census.py",
    RD / "per_book.py",
    RD / "census.json",
    RD / "per_book.json",
    RD / "CENSUS.md",
    RD / "RUN_STATE.md",
]
base = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "master"],
                      capture_output=True, text=True).stdout.strip()
branch = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
man = {
    "prompt_id": "freeze/d1-recheck",
    "prompt": ("Close D1 (u3.evaluate looks only for <dir>/theory.lean) and D2 "
               "(expand_targets descends one level), re-run the census, report "
               "attainment against 14/24, and say whether the C4 deadlock "
               "development attains."),
    "branch": branch,
    "base_commit": base,
    "utc": "2026-08-02T10:00:00Z",
    "seed": None,
    "files": [{"path": str(f.relative_to(ROOT)).replace("\\", "/"),
               "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
              for f in files],
    "notes": ("D1 and D2 were ALREADY CLOSED on master at 1c063290 (2026-08-01); "
              "the brief that commissioned this run was describing landed work. "
              "This run re-derives the census independently and reproduces it "
              "exactly: 24 books, discharged 17, vacuous 2, unclassified 4, "
              "failing_obligation 1, 17/24 attained.  50 directories today "
              "against 44 on 08-01 -- six theoria-arm run dirs appeared since, "
              "all bookless, and the book count is unchanged.  New work here is "
              "D1's second half: the widened search made the directory verdict a "
              "MAX over N books and nothing recorded which book carried it, so a "
              "book Lean OOMs on is absorbed by a sibling and two negative "
              "controls in C4's verify/ were weighed invisibly.  offline: Lean "
              "4.9.0 only, no API/model/network/spend, no sealed-pile contact."),
}
(RD / "MANIFEST.json").write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n",
                                  encoding="utf-8")
print("wrote", RD / "MANIFEST.json")
