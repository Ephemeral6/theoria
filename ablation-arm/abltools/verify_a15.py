#!/usr/bin/env python
"""A15's gate: the two claims this item is entitled to make, checked against artefacts.

    python -m abltools.verify_a15

Exit 0 green, 1 red. Two independent halves, because A15 asked two different
questions and only one of them is about this arm:

  1. The calibration is on the mainline and still describes the tree it pins.
     The item's premise was that `artifacts/calibration.json` existed only inside
     `.worktrees/a4b-ablation-calibrate/`. It does not -- but "it is committed"
     is a weaker claim than the item needs. An outdated comparison table is worse
     than no table, so the real check is that all 17 pinned upstream sha256s
     still match the files on disk. If a source file has moved, the calibration
     is a fossil and must say so.

  2. The worktree census exists, is internally consistent, and is honest about
     its own limits -- in particular that a census of a live repository is a
     snapshot. `.worktrees/_tmp_v5b` was deleted by another process *while the
     first census was running*, which is the sharpest possible demonstration
     that the number is a reading, not a fact.

Assertion 1 is the one that can fail from ordinary drift. It is meant to.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

ARM = Path(__file__).resolve().parent.parent
REPO = ARM.parent
RUN = ARM / "runs" / "2026-07-29T1400Z-A15-ablation-calibration-uncommitted"

# Every JSON in this repo is UTF-8; the machines it runs on default to GBK and
# raise UnicodeDecodeError on the first non-ASCII byte. Always go through this.
def load(path: Path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    fails: list[str] = []
    notes: list[str] = []

    # ---- 1. the calibration, and whether it still describes the world --------
    cal_path = ARM / "artifacts" / "calibration.json"
    if not cal_path.exists():
        fails.append(f"calibration.json missing at {cal_path}")
        print("\n".join(f"FAIL {f}" for f in fails))
        return 1

    cal = load(cal_path)
    print(f"calibration.json          {sha256(cal_path)[:16]}  prompt_id={cal.get('prompt_id')}")

    sources = cal.get("sources", {})
    if not sources:
        fails.append("calibration.json carries no `sources` pin -- staleness cannot be checked")
    bad, missing = [], []
    for rel, pinned in sorted(sources.items()):
        f = REPO / rel
        if not f.exists():
            missing.append(rel)
            continue
        if sha256(f) != pinned:
            bad.append(rel)
    print(f"pinned upstream sources   {len(sources) - len(bad) - len(missing)}/{len(sources)} match")
    if bad:
        fails.append(
            "the calibration pins upstream files that have since changed, so its comparison "
            "table describes a tree that no longer exists: " + ", ".join(bad)
        )
    if missing:
        fails.append("pinned upstream files are gone: " + ", ".join(missing))

    # The claims the pin is there to protect. If the artefact ever stops
    # asserting these, the pin is guarding nothing and the check is theatre.
    for key, path in (
        ("predictions_hold", ("predictions_hold",)),
        ("a2_fork.holds", ("a2_fork", "holds")),
        ("cost.P4", ("cost", "P4_this_arm_is_cheaper_not_dearer")),
        ("upstream_unchanged", ("upstream_unchanged",)),
    ):
        node = cal
        for seg in path:
            node = node.get(seg) if isinstance(node, dict) else None
        if node is not True:
            fails.append(f"calibration.json: expected {key} to be true, found {node!r}")
    a0 = cal.get("a0_table", {})
    n = a0.get("n_rows")
    parts = (a0.get("n_identical", 0), a0.get("n_differing", 0), a0.get("n_not_comparable", 0))
    if n != sum(parts):
        fails.append(f"a0_table rows do not add up: n_rows={n} but parts sum to {sum(parts)}")
    print(f"a0_table                  {n} rows = {parts[0]} identical + {parts[1]} differing "
          f"+ {parts[2]} not comparable")
    if cal.get("api_calls") != 0:
        fails.append(f"calibration.json claims api_calls={cal.get('api_calls')}, expected 0")

    # ---- 2. the census ------------------------------------------------------
    census_path = RUN / "worktree_census.json"
    if not census_path.exists():
        fails.append(f"worktree census missing at {census_path}")
    else:
        c = load(census_path)
        s = c["summary"]
        print(f"worktree census           {s['total']} worktrees, {s['AT-RISK']} at risk, "
              f"{s['authored_paths_only_on_disk']} authored files only on disk")
        if c.get("deleted_anything") is not False:
            fails.append("the census claims to have deleted something; it must never do that")
        if c.get("read_only") is not True:
            fails.append("census is not marked read_only")
        counted = sum(s.get(k, 0) for k in
                      ("AT-RISK", "RECOVERABLE", "RECLAIMABLE", "PRIMARY", "MISSING", "UNKNOWN"))
        if counted != s["total"]:
            fails.append(f"census dispositions sum to {counted}, not {s['total']} -- "
                         f"some worktree fell through every class")
        # Every at-risk worktree must justify itself: unique authored content,
        # something unhashable, or commits on no remote. A bare "it looked dirty"
        # is the failure mode this tool was rewritten to eliminate.
        for r in c["worktrees"]:
            if r["disposition"] != "AT-RISK":
                continue
            if (r.get("unique_authored_count") or 0) == 0 \
               and (r.get("unhashable_count") or 0) == 0 \
               and not (r.get("commits_ahead") and not r.get("on_remote")):
                fails.append(f"{r['path']} is AT-RISK with no unique content and no unpushed "
                             f"commits -- the disposition is unjustified")
        n_at_risk = sum(1 for r in c["worktrees"] if r["disposition"] == "AT-RISK")
        if n_at_risk != s["AT-RISK"]:
            fails.append(f"summary says {s['AT-RISK']} at risk, records say {n_at_risk}")
        if not (RUN / "worktree_census.md").exists():
            fails.append("census markdown missing -- the human-readable half is the deliverable")
        notes.append(
            "the census is a snapshot of a live repository: between two runs of it on "
            "2026-07-29, .worktrees/_tmp_v5b was deleted by another process and three "
            "ci-merge-* worktrees came and went under the OS temp directory. Re-run before "
            "acting on it."
        )

    print()
    for nte in notes:
        print(f"NOTE {nte}")
    if fails:
        print()
        for f in fails:
            print(f"FAIL {f}")
        print(f"\nA15 RED ({len(fails)} failure(s))")
        return 1
    print("\nA15 GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
