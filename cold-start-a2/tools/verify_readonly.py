"""Prove, rather than assert, that a full A2 run writes nothing into another track.

A2 imports the compile backends and certify layer from `cold-start-a0`, which
belongs to the theory-compiler track.  "Read-only" is easy to claim and easy to
break by accident — one reused function whose report path is built from *its*
module root, and A2 has quietly written into someone else's directory.  A0's
`plan_stage.run_plan` is exactly that function, which is why A2 rewrote the
driver (DECISIONS D-A2-006's neighbour, D-A2-010's discipline).

This script hashes every file under `cold-start-a0` (skipping `.toolchain/`,
`__pycache__/` and `.pytest_cache/`), runs `run_all.py`, and hashes again.

```bash
cd cold-start-a2 && python -m tools.verify_readonly
```

Expected output: `0 files changed`.  Anything else is a defect in A2, not in the
other track.

This is a script rather than a test on purpose.  Two sessions work this repo
concurrently, so the other track's files legitimately change while A2 runs; a
pytest case would be flaky for a reason that has nothing to do with A2's
correctness.  Run it deliberately, when the other track is idle.
"""

import hashlib
import os
import subprocess
import sys
from typing import Dict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)
TARGETS = ("cold-start-a0", "engine-rig", "theory-compiler", "CONTRACTS")
SKIP = {".toolchain", "__pycache__", ".pytest_cache", ".git"}


def snapshot(root: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for name in files:
            path = os.path.join(base, name)
            try:
                with open(path, "rb") as handle:
                    out[path] = hashlib.sha256(handle.read()).hexdigest()
            except OSError:
                pass
    return out


def main() -> int:
    roots = [os.path.join(REPO, t) for t in TARGETS
             if os.path.exists(os.path.join(REPO, t))]
    before = {}
    for root in roots:
        before.update(snapshot(root))
    print("hashed %d files across %d trees" % (len(before), len(roots)))

    proc = subprocess.run([sys.executable, "run_all.py"], cwd=ROOT,
                          capture_output=True)
    print("run_all exit: %d" % proc.returncode)
    if proc.returncode != 0:
        sys.stdout.write(proc.stdout.decode("utf-8", "replace")[-2000:])

    after = {}
    for root in roots:
        after.update(snapshot(root))

    changed = sorted(k for k in set(before) | set(after)
                     if before.get(k) != after.get(k))
    print("%d files changed" % len(changed))
    for path in changed[:40]:
        print("   ", os.path.relpath(path, REPO))
    if changed:
        print()
        print("NOTE: another session works this repo concurrently.  Re-run with "
              "the other track idle before treating this as an A2 defect.")
    return 1 if changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
