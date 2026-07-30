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
import subprocess
import sys
from pathlib import Path

ARM = Path(__file__).resolve().parent.parent
REPO = ARM.parent
UPSTREAM_NAME = "origin/master"
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

    # ---- 1b. the half the artefact's own pin does not cover ----------------
    # `sources` pins 17 files, all of them upstream (`cold-start-a0/`,
    # `cold-start-a2/`). Not one `ablation-arm/` path is in it -- yet every row
    # of the 19-row table reads its LEFT-hand value out of this arm's own
    # artefacts, and this arm is under active development while upstream is not.
    # So the guard the calibration ships protects the stationary half and leaves
    # the moving half open. An adversarial review of A15 found that; this closes
    # it without touching the artefact, by asking git whether any cited
    # ablation-arm file has changed on the mainline since the calibration
    # commit. Comparing committed blobs rather than working files on purpose:
    # `verify.sh` legitimately rewrites these artefacts on every run, so a
    # working-tree pin would be red every time and would train its reader to
    # ignore it.
    def cite_to_path(tok: str) -> str:
        tok = tok.strip("`'\"(),;")
        # Citations carry an anchor after the filename -- `exhibits.json:E2`,
        # `episode.jsonl:12`. Keep the file, drop the anchor. Without this the
        # anchor rode along into `git rev-parse`, which ECHOES an argument it
        # cannot parse instead of printing nothing, so two different echoed
        # strings compared unequal and the gate reported drift in a file that
        # had not moved. A gate's first duty is not to cry wolf.
        head, sep, tail = tok.rpartition(":")
        return head if sep and "/" not in tail else tok

    def blob_at(rev: str, rel: str) -> str | None:
        p = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{rev}:{rel}"],
                           cwd=REPO, capture_output=True, text=True)
        out = p.stdout.strip()
        # --verify --quiet plus an explicit 40-hex shape: belt and braces
        # against rev-parse's echo behaviour ever leaking a non-hash through.
        return out if p.returncode == 0 and len(out) == 40 else None

    cited = sorted({
        c for c in (cite_to_path(t) for t in
                    json.dumps(cal, ensure_ascii=False).replace('\\"', " ").split())
        if c.startswith("ablation-arm/") and "." in c.rsplit("/", 1)[-1]
    })
    calib_commit = "f7df3168"  # the commit that produced the tracked artefact
    drifted: list[str] = []
    checked = 0
    for rel in cited:
        then, now = blob_at(calib_commit, rel), blob_at("HEAD", rel)
        if then is None or now is None:
            continue
        checked += 1
        if then != now:
            drifted.append(rel)
    print(f"cited ablation-arm files   {checked - len(drifted)}/{checked} unchanged since {calib_commit}")
    if drifted:
        fails.append(
            "the calibration reads numbers out of ablation-arm files that have changed on the "
            "mainline since it was measured, and its own `sources` pin does not cover them: "
            + ", ".join(drifted)
        )

    # ---- 2. the census ------------------------------------------------------
    # Before reading its numbers, prove the instrument still addresses the file
    # it is asked about. This is not paranoia: `hash-object --stdin-paths`
    # resolves relative paths against the repo top-level, which silently made
    # every unregistered directory read as fully preserved until it was caught.
    from abltools.worktree_audit import self_check  # noqa: PLC0415 -- gate-local

    for problem in self_check(str(REPO)):
        fails.append(f"census self-check: {problem}")
    print("census self-check           hasher addresses the file it is given")

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
        # Staleness is a NOTE, deliberately, not a failure. origin/master moves
        # every few minutes in this repository, so failing on any drift would
        # make this gate permanently red -- and a permanently red gate is one
        # nobody reads, which is worse than not having it. The census's contract
        # is "re-run before acting"; the gate's job is to say how far out of date
        # it is, in commits, so a reader can judge.
        live = subprocess.run(["git", "rev-parse", UPSTREAM_NAME], cwd=REPO,
                              capture_output=True, text=True).stdout.strip()
        taken = c.get("upstream_head")
        if live and taken and taken != live:
            behind = subprocess.run(["git", "rev-list", "--count", f"{taken}..{live}"],
                                    cwd=REPO, capture_output=True, text=True).stdout.strip()
            notes.append(
                f"the census was taken against {taken[:8]}; {UPSTREAM_NAME} is now "
                f"{live[:8]}, {behind or '?'} commit(s) later. Re-run before acting on it."
            )
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
