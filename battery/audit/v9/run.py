"""Write the V9 run directory.  Passive: it reads nothing but its own code.

Deliberately writes to `battery/runs/<utc>-V9-battery-gaming-audit/` and
**never** to `battery/artifacts/`.  A known defect is registered elsewhere in
this repository — a bare `run_battery` overwrites `battery/artifacts/` — and
the V9 ticket says not to fix it in passing, so this tool simply stays out of
that directory.

    python -m battery.audit.v9.run <utc-stamp>
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
from typing import Dict, List

PROMPT_ID = "V9-battery-gaming-audit"
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _git(*args: str) -> str:
    return subprocess.check_output(("git",) + args, cwd=REPO).decode().strip()


def _sha256(path: str) -> str:
    with io.open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def write(stamp: str) -> str:
    from battery.audit.v9.verdict import adjudicate, disagreements_with_b14

    out_dir = os.path.join(REPO, "battery", "runs",
                           "%s-%s" % (stamp, PROMPT_ID))
    os.makedirs(out_dir, exist_ok=True)

    table = adjudicate()
    payload = {
        "prompt_id": PROMPT_ID,
        "verdict": table,
        "disagreements_with_b14": disagreements_with_b14(),
        "predictions": [{"id": i, "text": t}
                        for i, t in __import__(
                            "battery.audit.v9.prereg", fromlist=["x"]
                        ).PREDICTIONS],
    }
    verdict_path = os.path.join(out_dir, "v9_gaming_audit.json")
    with io.open(verdict_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")

    tracked: List[str] = [
        "battery/PREREG_V9.md",
        "battery/BLINDING.md",
        "battery/audit/v9/prereg.py",
        "battery/audit/v9/check.py",
        "battery/audit/v9/attack.py",
        "battery/audit/v9/verdict.py",
        "battery/audit/v9/run.py",
    ]
    attack_dir = os.path.join(REPO, "battery", "audit", "v9", "attacks")
    if os.path.isdir(attack_dir):
        tracked.extend(
            "battery/audit/v9/attacks/%s" % name
            for name in sorted(os.listdir(attack_dir)) if name.endswith(".py"))

    files: List[Dict[str, str]] = []
    run_relative = ["battery/runs/%s-%s/%s" % (stamp, PROMPT_ID, name)
                    for name in ("v9_gaming_audit.json", "pytest.txt",
                                 "RUN_STATE.md")]
    for rel in tracked + ["battery/METRICS.md", "battery/STATUS.md",
                          "battery/audit/v9/mutants.py",
                          "battery/audit/v9/REPORT.md",
                          "battery/tests/test_v9_prereg.py",
                          "battery/tests/test_v9_defences.py"] + run_relative:
        absolute = os.path.join(REPO, rel.replace("/", os.sep))
        if os.path.isfile(absolute):
            files.append({"path": rel, "sha256": _sha256(absolute)})

    manifest = {
        "prompt_id": PROMPT_ID,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": _git("rev-parse", "HEAD"),
        "utc": stamp,
        "prereg_commit": _git("rev-list", "-1", "HEAD",
                              "--", "battery/PREREG_V9.md"),
        "python": sys.version.split()[0],
        "files": files,
    }
    with io.open(os.path.join(out_dir, "MANIFEST.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return out_dir


if __name__ == "__main__":
    print(write(sys.argv[1] if len(sys.argv) > 1 else "UNSTAMPED"))
