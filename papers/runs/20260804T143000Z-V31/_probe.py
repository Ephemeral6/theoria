"""Throwaway probe: run individual checks and print their heads.

Kept in the run directory rather than in the territory, because it is
provenance for how the numbers in RUN_STATE.md were taken, not a tool.

    cd papers/phase1-workshop && python ../runs/20260804T143000Z-V31/_probe.py [TAG ...]
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "phase1-workshop")))
import verify_paper as vp  # noqa: E402

ALL = {
    "A": ("A GENERATED", vp.check_generated),
    "B": ("B PATHS", vp.check_paths),
    "C": ("C FIGDATA", vp.check_figdata),
    "E": ("E UNCITED", vp.check_uncited),
    "F": ("F BARE", vp.check_bare),
}

for tag in (sys.argv[1:] or ["B", "C", "E", "F"]):
    name, fn = ALL[tag]
    ok, notes = fn()
    print("==", name, "OK" if ok else "FAIL")
    for line in notes:
        print("   ", line[:200])
