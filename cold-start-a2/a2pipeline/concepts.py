"""The concept account, and the upstream pin.  Two small bookkeeping products.

**Concept accounts** price each object in the word table against a
responsibility-complete alternative, using A0's `pipeline/concept_account.py`
unmodified.  The `compress:` figures in the three .dsl files come from here and
are not invented.  A2 expects the same verdict A0 got — the Cart pays for itself
many times over, the Button and Door do not and are admitted anyway on
full-frame responsibility plus the invariant language having no pixel-level
paraphrase of `count(Button, 8) + count(Door) = 1`.  That two of the framework's
own criteria disagree is A0's finding; A2 reproduces it on a second world rather
than restating it.

**The upstream pin** hashes every `cold-start-a0` file A2 imports.  That tree
belongs to another track and had work in flight while A2 was built, so "which
version of the compiler produced this exhibit" is a question the artefacts have
to be able to answer on their own.  A2 never writes there; it only records what
it read.
"""

import hashlib
import json
import os
import subprocess
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from pipeline.concept_account import accounts  # noqa: E402  (cold-start-a0)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
ARTIFACTS = os.path.join(ROOT, "artifacts")
A0 = os.path.join(REPO, "cold-start-a0")

NAME_BY_COLOUR = {7: "Button", 5: "Door", 6: "Cart"}

# Every cold-start-a0 module A2 imports, directly or through one of these.
UPSTREAM = [
    "compile/__init__.py",
    "compile/compile_a0.py",
    "compile/dialect.py",
    "compile/gen_lean_a0.py",
    "compile/gen_pddl_a0.py",
    "compile/gen_python_a0.py",
    "compile/problem.py",
    "certify/__init__.py",
    "certify/lean_check.py",
    "certify/replay.py",
    "pipeline/__init__.py",
    "pipeline/atoms_a0.py",
    "pipeline/board.py",
    "pipeline/concept_account.py",
    "pipeline/engines_stage.py",
    "pipeline/multi_miner.py",
    "pipeline/segment_operators.py",
    "world/__init__.py",
    "world/a0_world.py",
    "world/explorer.py",
    "world/ground_truth.py",
    "_bootstrap.py",
]


def _sha256(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def pin() -> Dict[str, object]:
    files = {}
    for rel in UPSTREAM:
        path = os.path.join(A0, rel)
        files[rel] = _sha256(path) if os.path.exists(path) else None
    head = None
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                              capture_output=True, timeout=30).stdout.decode(
                                  "utf-8", "replace").strip()
    except Exception:                                   # noqa: BLE001
        head = None
    return {
        "why": "A2 imports these files from cold-start-a0 and never writes to "
               "that tree.  It had uncommitted work in flight from another "
               "session while A2 was built, so the exhibit records which bytes "
               "it was compiled by.  A changed hash here means A2's results "
               "must be regenerated before they are quoted.",
        "repo_head_when_pinned": head,
        "sha256": files,
        "missing": sorted(k for k, v in files.items() if v is None),
    }


def main() -> int:
    report: Dict[str, object] = {}
    for tag, candidates, dsl in (
        ("a2-base", "candidates.jsonl", "theory.dsl"),
        ("a2-holed", "candidates_history.jsonl", "theory_holed.dsl"),
        ("a2-repaired", "candidates_probed.jsonl", "theory_repaired.dsl"),
    ):
        rows = accounts(os.path.join(ARTIFACTS, candidates),
                        os.path.join(ROOT, "theory", dsl), NAME_BY_COLOUR)
        report[tag] = [a.as_json() for a in rows]
        print("[%s]" % tag)
        print("  %-8s %-8s %8s %8s %8s  %-10s %s"
              % ("object", "name", "with", "without", "delta", "verdict", "reason"))
        for a in rows:
            print("  %-8s %-8s %8d %8d %+8d  %-10s %s"
                  % (a.object_id, a.name or "-", a.script_with, a.script_without,
                     a.script_delta, a.verdict, a.reason))
    with open(os.path.join(ARTIFACTS, "concept_accounts.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")

    pinned = pin()
    with open(os.path.join(ARTIFACTS, "upstream_pin.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(pinned, indent=2, sort_keys=True) + "\n")
    print("pinned %d upstream files, %d missing"
          % (len(pinned["sha256"]), len(pinned["missing"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
