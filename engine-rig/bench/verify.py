"""Check a run directory against the machine it is sitting on.

    cd engine-rig && python -m bench.verify runs/<id>

Five checks, and the reason each one exists:

1. **Manifest hashes.**  Every file the manifest lists still hashes to what it
   said.  This is the cheap one and it catches the failure that matters most
   often: a report edited by hand after the run that produced it.

2. **Structural re-derivation.**  A subset of the batch is measured again and
   the *deterministic* fields -- node counts, plan lengths, task sizes, exit
   codes -- are compared for exact equality.  Not the timings; see below.

3. **Timing sanity, never timing equality.**  Wall clock is a property of this
   machine at this moment.  What can be checked is that the three clocks are
   present and ordered: FD's search time is inside FD's total time, which is
   inside what the caller waited for.  A run where that ordering broke would
   have a parsing bug, which is a real defect; a run 20% slower than last time
   is a busier laptop.

4. **No recorded soundness problems.**

5. **The planner is the one the run says it used**, by binary hash.  Without
   this the structural comparison in (2) could pass against a different planner
   that happened to agree, or fail against the same one rebuilt.

Check 2 is skipped with a stated reason, not silently, when no Fast Downward is
reachable -- which is the state every machine that has not run P-13's build is
in, and the state this repo is in as checked out.  The bundled rung is still
re-derived there, so the run is not wholly unverifiable without the toolchain.
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Dict, List, Optional

from bench import fdrun, instances as bench_instances, ladder, toolchain
from engines.fd_adapter import backends

# The subset re-derived in check 2.  Small on purpose: re-running the whole batch
# would take minutes and would re-measure the same three code paths twenty times.
# One gripper instance from each end of the ladder, the two committed sokoban
# fixtures whose lengths are argued elsewhere in this rig, and the unsolvable one
# -- which is the row where the rungs disagree about what they may conclude.
SUBSET = ("gripper-02", "gripper-06", "sokoban-open4", "sokoban-open4far",
          "sokoban-ringstuck")

# Compared for exact equality.  Everything else in a rung record is either a
# timing or derived from these.
STRUCTURAL = ("solved", "proved_unsolvable", "not_entitled", "plan_length")


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_manifest_hashes(run_dir: str, manifest: Dict) -> List[str]:
    problems = []
    for entry in manifest.get("files", []):
        path = os.path.join(run_dir, entry["path"])
        if not os.path.isfile(path):
            problems.append("missing: %s" % entry["path"])
            continue
        actual = sha256(path)
        if actual != entry["sha256"]:
            problems.append(
                "%s: sha256 %s, manifest says %s -- edited after the run?"
                % (entry["path"], actual[:16], entry["sha256"][:16])
            )
    return problems


def check_timings(report: Dict) -> List[str]:
    """The ordering, not the values."""
    problems = []
    for entry in report["results"]:
        for row in entry["rungs"]:
            timing = row.get("timing") or {}
            wall = timing.get("wall_seconds")
            if row.get("error") and "over budget" in str(row["error"]):
                continue
            if wall is None:
                problems.append("%s/%s: no wall clock recorded"
                                % (entry["instance"]["name"], row["config"]))
                continue
            search = timing.get("search_seconds")
            total = timing.get("fd_total_seconds")
            if search is not None and total is not None and search > total:
                problems.append(
                    "%s/%s: FD search time %.6f exceeds FD total time %.6f -- "
                    "the log parser is reading the wrong lines"
                    % (entry["instance"]["name"], row["config"], search, total)
                )
            if total is not None and total > wall:
                problems.append(
                    "%s/%s: FD total time %.6f exceeds the wall clock %.6f around "
                    "the subprocess -- impossible, so one of them is misparsed"
                    % (entry["instance"]["name"], row["config"], total, wall)
                )
    return problems


def rederive(run_dir: str, report: Dict, executable: Optional[str]) -> List[str]:
    """Measure the subset again; compare the deterministic half exactly."""
    problems = []
    recorded = {entry["instance"]["name"]: entry for entry in report["results"]}
    instance_dir = os.path.join(run_dir, "instances")
    batch = {inst.name: inst for inst in bench_instances.all_instances(instance_dir)}

    for name in SUBSET:
        if name not in recorded or name not in batch:
            problems.append("%s: in the subset but not in the run" % name)
            continue
        instance = batch[name]
        rows = {row["config"]: row for row in recorded[name]["rungs"]}

        fresh = ladder.measure_stub(instance, repeats=1)
        was = rows.get("stub-bfs", {})
        for field in ("solved", "plan_length"):
            if fresh.get(field) != was.get(field):
                problems.append(
                    "%s/stub-bfs: %s is now %r, run recorded %r"
                    % (name, field, fresh.get(field), was.get(field))
                )
        if (fresh.get("nodes") or {}).get("expanded") != (was.get("nodes") or {}).get("expanded"):
            problems.append(
                "%s/stub-bfs: expansions now %r, run recorded %r -- the bundled "
                "search is deterministic, so this is a real change"
                % ((fresh.get("nodes") or {}).get("expanded"),
                   (was.get("nodes") or {}).get("expanded"))
            )

        if executable is None:
            continue
        for config, tier, heuristic in ladder.CONFIGS[1:]:
            was = rows.get(config)
            if was is None:
                continue
            now = fdrun.measure(executable, instance.domain_path,
                                instance.problem_path, tier, heuristic)
            fresh = now.structural()
            for field in STRUCTURAL:
                if fresh.get(field) != was.get(field):
                    problems.append(
                        "%s/%s: %s is now %r, run recorded %r"
                        % (name, config, field, fresh.get(field), was.get(field))
                    )
            for counter in ("expanded", "generated"):
                if fresh["nodes"].get(counter) != (was.get("nodes") or {}).get(counter):
                    problems.append(
                        "%s/%s: %s is now %r, run recorded %r"
                        % (name, config, counter, fresh["nodes"].get(counter),
                           (was.get("nodes") or {}).get(counter))
                    )
    return problems


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="bench.verify")
    parser.add_argument("run_dir")
    args = parser.parse_args(argv)
    run_dir = os.path.abspath(args.run_dir)

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_root = os.path.dirname(here)

    with open(os.path.join(run_dir, "MANIFEST.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    with open(os.path.join(run_dir, "ladder.json"), encoding="utf-8") as fh:
        ladder_report = json.load(fh)

    problems: List[str] = []
    skipped: List[str] = []

    print("1. manifest hashes")
    problems += check_manifest_hashes(run_dir, manifest)

    print("2. recorded soundness problems")
    for line in manifest.get("soundness_problems", []):
        problems.append("recorded in MANIFEST.json: %s" % line)

    print("3. timing sanity (ordering only, never equality)")
    problems += check_timings(ladder_report)

    print("4. the planner is the one the run used")
    executable = backends.find_fast_downward()
    recorded_tool = manifest.get("toolchain", {})
    if executable is None:
        skipped.append(
            "No Fast Downward reachable, so the FD half of check 5 cannot run. "
            "This is the expected state on a machine that has not built "
            "`.toolchain/` -- see %s." % toolchain.TOOLCHAIN_MANIFEST
        )
    else:
        live = toolchain.probe(executable, repo_root)
        if recorded_tool.get("binary_sha256") and \
                live["binary_sha256"] != recorded_tool["binary_sha256"]:
            problems.append(
                "planner mismatch: this machine has %s, the run used %s"
                % (live["binary_sha256"][:16], recorded_tool["binary_sha256"][:16])
            )

    print("5. structural re-derivation on %d instances" % len(SUBSET))
    problems += rederive(run_dir, ladder_report, executable)

    for line in skipped:
        print("   SKIPPED: %s" % line)
    if problems:
        print("\nFAIL (%d):" % len(problems))
        for line in problems:
            print("  - %s" % line)
        return 1
    print("\nok -- %s verifies%s"
          % (run_dir, " (FD checks skipped)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
