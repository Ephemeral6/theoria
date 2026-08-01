# -*- coding: utf-8 -*-
"""One-shot MANIFEST writer for this run record (kept for provenance)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RD = Path(__file__).resolve().parent

files = [
    ROOT / "exam" / "u3_census.py",
    ROOT / "exam" / "tests" / "test_u3_census.py",
    RD / "census.json",
    RD / "census.md",
    RD / "RUN_STATE.md",
]
man = {
    "prompt_id": "ep/u3-exam-audit",
    "prompt": ("Implement U3 (E1, primary endpoint one). Premise was stale: "
               "freeze/u3.py already implements it (6c4a0bb2, merged 5adf4fcd). "
               "Built the missing half instead -- discovery/enumeration -- and "
               "audited the adjudicator against the frozen text."),
    "branch": "ep/u3-exam-audit",
    "base_commit": "21a724ed",
    "utc": "2026-08-01T04:00:00Z",
    "seed": None,
    "territory": "exam",
    "adjudicator": {
        "module": "freeze/u3.py",
        "sha256": hashlib.sha256((ROOT / "freeze" / "u3.py").read_bytes()).hexdigest(),
        "note": ("every verdict in census.json is this module's return value; "
                 "the census contains no second opinion"),
    },
    "toolchain": {"lean": "4.9.0 x86_64-w64-windows-gnu 8f9843a4a5fe"},
    "census": {
        "books": "14/24 attained",
        "bookless_claimants": "15 runs, 0 attained",
        "probe": False,
        "wall_clock": "4m47s",
        "byte_reproducible": True,
        "denominator_warning": (
            "NOT STATS_RULES.md 1.2's rate. 1.2's denominator is 19 sealed "
            "games (12 clean); nothing on disk today is a sealed game."),
    },
    "findings": [
        "F1: u3.classify_theorem is a prefix name-matcher; prune/unknown kinds "
        "fail closed and are LABELLED `vacuous`, conflating 'no checker for "
        "this shape' with 'proved a tautology'. The C4 sokoban deadlock "
        "development -- named by STATS_RULES.md:123 as the paradigm U3 "
        "theorem -- compiles with an empty axiom set and reads `vacuous`.",
        "F2: the `unsolvable` (c) check has a 0/14 yes-rate on this repo; all "
        "14 attainments came through invariant-kind theorems.",
        "F3: a book-only census flatters itself -- the four live legs have "
        "certify.json and no .lean; reported in a separate denominator.",
        "D1: u3.evaluate only looks for <dir>/theory.lean; Level.lean books "
        "read as no_evidence (4 handover packages).",
        "D2: u3.expand_targets descends one level; 3 nested books unreachable.",
    ],
    "sealed_pile_contact": "none",
    "files": [{"path": str(f.relative_to(ROOT)).replace("\\", "/"),
               "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
              for f in files],
}
# LF explicitly. `exam/.gitattributes` pins `* text eol=lf`, so git stores LF;
# Python's text mode on Windows writes CRLF, and a sha256 taken over that
# working copy would fail to reproduce after a fresh checkout — the hashes
# below would be wrong about the very files they certify.
with open(RD / "MANIFEST.json", "w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(man, indent=1, ensure_ascii=False) + "\n")
print("wrote", RD / "MANIFEST.json")
