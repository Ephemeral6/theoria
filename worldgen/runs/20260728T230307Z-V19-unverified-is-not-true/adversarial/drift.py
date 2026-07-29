"""Does `--check` pin the COMMITTED artefacts, or only determinism?

Apply C15 (transitions_checked misreported as 0) in a sandbox, run the real
`python -m worldgen.build --check` (default --into, i.e. the sandbox's own out/),
and report the exit code plus whether the committed artefact changed.
"""
import os
import shutil
import subprocess
import sys
import tempfile

SRC = r"C:\Users\user\Desktop\theoria\.worktrees\v19-unverified-is-not-true\worldgen"
SCRATCH = (r"C:\Users\user\AppData\Local\Temp\claude"
           r"\C--Users-user-Desktop-theoria\9c21443e-474e-49a2-9789-41ea1e7d33ac"
           r"\scratchpad\mut")
SKIP = ("__pycache__", ".pytest_cache", ".pytest-runs", "runs")

EDITS = [("core/truth.py", '            row["transitions_checked"] = edges\n',
          '            row["transitions_checked"] = 0\n')]
PROBE = "worldgen/out/worlds/t1-switch-latch/ground_truth.json"

root = tempfile.mkdtemp(prefix="v19-drift-", dir=SCRATCH)
shutil.copytree(SRC, os.path.join(root, "worldgen"),
                ignore=shutil.ignore_patterns(*SKIP))
before = open(os.path.join(root, PROBE), encoding="utf-8").read()
for rel, old, new in EDITS:
    p = os.path.join(root, "worldgen", rel.replace("/", os.sep))
    t = open(p, encoding="utf-8", newline="").read()
    assert t.count(old) == 1
    open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new))

env = dict(os.environ, PYTHONPATH=root, PYTHONIOENCODING="utf-8")
proc = subprocess.run([sys.executable, "-m", "worldgen.build", "--check"],
                      cwd=root, env=env, capture_output=True)
after = open(os.path.join(root, PROBE), encoding="utf-8").read()
tail = (proc.stdout + proc.stderr).decode("utf-8", "replace")
print("build --check exit code:", proc.returncode)
print("committed artefact changed by the mutant:", before != after)
print("'transitions_checked': 104 present before:", '"transitions_checked": 104' in before)
print("'transitions_checked': 0 present after: ", '"transitions_checked": 0' in after)
print("--- tail ---")
print(tail[-800:])
shutil.rmtree(root, ignore_errors=True)
