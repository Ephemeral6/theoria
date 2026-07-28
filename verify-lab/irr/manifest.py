"""Emit the V17 run manifest.

`CLAUDE.md`: every experiment writes `runs/<id>/MANIFEST.json` with `prompt_id`,
`branch`, `base_commit`, `utc`, and optionally `files[].sha256`. Generated rather
than hand-written so the hashes cannot drift from the files they describe.

    python verify-lab/irr/manifest.py > <run>/MANIFEST.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(LAB)
RUN = os.path.join("verify-lab", "runs", "20260729T180000Z-V17-pin-the-partial-verdict")

TOOLS = ["PARTIAL_CRITERION.md", "RELIABILITY.md",
         "irr/rows.py", "irr/overlap.py", "irr/sample.py", "irr/blindtree.py",
         "irr/agree.py", "irr/refold.py", "irr/shapes.py", "irr/manifest.py"]


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True,
                          text=True, check=True).stdout.strip()


def _sha(path: str) -> str:
    with open(os.path.join(REPO, path), "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def build(utc: str) -> Dict[str, object]:
    files: List[Dict[str, str]] = []
    for rel in TOOLS:
        files.append({"path": "verify-lab/" + rel, "sha256": _sha("verify-lab/" + rel)})
    for base, _dirs, names in os.walk(os.path.join(REPO, RUN)):
        for name in sorted(names):
            if name == "MANIFEST.json":
                continue
            rel = os.path.relpath(os.path.join(base, name), REPO).replace("\\", "/")
            files.append({"path": rel, "sha256": _sha(rel)})
    files.sort(key=lambda f: f["path"])
    return {
        "prompt_id": "V17-pin-the-partial-verdict",
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": _git("merge-base", "HEAD", "master"),
        "head_commit": _git("rev-parse", "HEAD"),
        "utc": utc,
        "merged_predecessors": {
            "V11": _git("rev-parse", "origin/agent/v11-negative-control-census"),
            "V14": _git("rev-parse", "origin/agent/v14-standing-negative-control-probe"),
            "V15": _git("rev-parse", "origin/agent/v15-census-sampling-frame"),
        },
        "preregistration_commit": "4a47472b480a68ba6280de3f7caada0761185c32",
        "judges": {
            "old_arm": ["O1", "O2", "O3"],
            "new_arm": ["N1", "N2", "N3"],
            "model": "one model, six independent instances -- not six people; "
                     "cross-model reliability was not measured",
            "blinding": "git ls-files minus 290 answer-key files; "
                        "see BLINDING.md for what was not blocked",
        },
        "network": "none", "api_calls": 0, "sealed_pile_contact": "none",
        "files": files,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--utc", default=datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    args = ap.parse_args(argv)
    json.dump(build(args.utc), sys.stdout, ensure_ascii=False, indent=2,
              sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
