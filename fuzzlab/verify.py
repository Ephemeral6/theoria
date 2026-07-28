"""One command that decides whether fuzzlab is green.

```bash
cd .worktrees/e4-property-fuzz && python -m fuzzlab.verify
```

Three stages:

| stage | question |
|---|---|
| `pytest fuzzlab/tests` | do the oracles compute what they claim, and does a short campaign still find nothing? |
| `campaign --worlds 60` | does the battery run end to end on every engine, with a reproducible seed table? |
| `engine-rig pytest` | is the tree under test the one the report says it is? |

**A violation does not fail this script**, and that is the point: 失败是战利品.
A found defect is the battery's product. What fails is fuzzlab being broken —
an oracle that disagrees with its own closed form, a generator that cannot build
its own world, a campaign that cannot run. Violations are counted, printed, and
routed to `BUGS.md`; the exit code is about the instrument, not the reading.
"""

import json
import os
import subprocess
import sys
from typing import List, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENGINE_RIG = os.path.join(ROOT, "engine-rig")

STAGES: Tuple[Tuple[str, Sequence[str], str], ...] = (
    ("oracle and battery tests",
     (sys.executable, "-m", "pytest", "fuzzlab/tests", "-q"), ROOT),
    ("campaign smoke, all six engines",
     (sys.executable, "-m", "fuzzlab.campaign", "--worlds", "60"), ROOT),
    ("engine-rig's own suite (the tree under test)",
     (sys.executable, "-m", "pytest", "-q"), ENGINE_RIG),
)


def main() -> int:
    failures: List[str] = []
    for label, command, cwd in STAGES:
        proc = subprocess.run(command, cwd=cwd, capture_output=True)
        text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
        ok = proc.returncode == 0
        print("[%s] %s" % ("ok  " if ok else "FAIL", label))
        tail = text.strip().splitlines()
        for line in tail[-(4 if ok else 14):]:
            print("        " + line)
        if not ok:
            failures.append(label)

    findings = os.path.join(HERE, "out", "campaign.json")
    if os.path.exists(findings):
        with open(findings, encoding="utf-8") as handle:
            totals = json.load(handle)["totals"]
        print()
        print("last campaign totals: %s" % json.dumps(totals, sort_keys=True))
        if totals.get("violated"):
            print("  violations are the product, not a failure — see fuzzlab/BUGS.md")

    print()
    if failures:
        print("FAILED: %s" % ", ".join(failures))
        return 1
    print("green")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
