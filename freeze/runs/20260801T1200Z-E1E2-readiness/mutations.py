#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Break the budget hold seven ways and require each break to be caught.

A check never seen to say no has not been shown to check anything, so every
guarantee stage [20] claims is deliberately violated here and the controls are
re-run against the mutant.  A mutation that leaves the controls green is a
FAILURE of this script, not a curiosity.

Runs entirely on temporary copies -- `freeze/build_manifest.py` is never edited.

    python freeze/runs/20260801T1200Z-E1E2-readiness/mutations.py
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
FREEZE = HERE.parents[1]
SRC = FREEZE / "build_manifest.py"

#: (label, what the mutation breaks, old text, new text, control that must go red)
MUTATIONS = [
    ("M1/always-holds",
     "the hold fires whether or not the balance is negative",
     '    if not budget.get("over_ceiling"):\n        return held',
     '    if False:\n        return held',
     "a POSITIVE balance holds nothing"),
    ("M2/boundary",
     "exact zero counts as over-ceiling",
     "over = (remaining is not None) and (remaining < 0)",
     "over = (remaining is not None) and (remaining <= 0)",
     "remaining == 0 is not over-ceiling"),
    ("M3/silent-block",
     "item 12 is blocked without recording what was overridden",
     '        entry["budget_hold"] = {\n            "held": True,\n'
     '            "declared_status": declared,',
     '        entry["budget_hold"] = {\n            "held": True,\n'
     '            "declared_status_REMOVED": declared,',
     "the override records what it overrode"),
    ("M4/holds-everything",
     "the hold ignores BUDGET_HOLD_ITEMS and blocks the whole list",
     '        if entry["n"] not in BUDGET_HOLD_ITEMS:\n            continue',
     '        if False:\n            continue',
     "item 13 is untouched"),
    ("M5/paraphrase",
     "the verdict describes the overrun instead of quoting it",
     '    return ("And the money: the programme has already spent $%s against a $%s "',
     '    return ("And the money: the programme is somewhat over budget. (%.0s%.0s"',
     "the verdict sentence quotes the negative balance verbatim"),
    ("M6/absence-as-zero",
     "a missing budget table reads as `not over ceiling` rather than unknown",
     '            "over_ceiling": None,',
     '            "over_ceiling": False,',
     "ABSENCE, not zero"),
    ("M7/no-table",
     "the positive control is pointed at a table that is not there",
     'BUDGET_TABLE = os.path.join(HERE, "BUDGET_TABLE.json")',
     'BUDGET_TABLE = os.path.join(HERE, "NO_SUCH_TABLE.json")',
     "the real freeze/BUDGET_TABLE.json parses"),
]


def run(path: pathlib.Path) -> tuple[int, str]:
    proc = subprocess.run([sys.executable, str(path), "--selftest"],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    original = SRC.read_text(encoding="utf-8")

    rc, out = run(SRC)
    print("baseline (unmutated): rc=%d  %s" % (rc, out.strip().splitlines()[-1]))
    if rc != 0:
        print("FAIL baseline is already red; no mutation result would mean anything")
        return 1

    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = pathlib.Path(tmp)
        # the module reads BUDGET_TABLE.json relative to its own directory, so
        # the mutant has to live next to the real one to keep the positive
        # control honest.
        for label, breaks, old, new, expect in MUTATIONS:
            if old not in original:
                print("FAIL %-20s control could not be BUILT (anchor text has "
                      "moved) -- recorded as a failure, not a skip" % label)
                bad += 1
                continue
            mutant = FREEZE / ("_mutant_%s.py" % label.split("/")[0])
            mutant.write_text(original.replace(old, new, 1), encoding="utf-8")
            try:
                rc, out = run(mutant)
                red = [ln for ln in out.splitlines() if ln.startswith("FAIL")]
                caught = rc != 0 and any(expect in ln for ln in red)
                print("%s %-20s %-58s -> %d control(s) red%s"
                      % ("PASS" if caught else "FAIL", label, breaks,
                         len(red), "" if caught else "  [expected: %r]" % expect))
                if not caught:
                    bad += 1
                    for ln in out.splitlines():
                        print("      | " + ln)
            finally:
                mutant.unlink(missing_ok=True)
        shutil.rmtree(tmpdir, ignore_errors=True)

    print("%d/%d mutations caught" % (len(MUTATIONS) - bad, len(MUTATIONS)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
