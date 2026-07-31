"""Replicate ci_merge.py's gate invocation exactly, for one worktree+territory.

usage: python opsm30_runner.py <worktree-root> <territory> <outfile>
"""
import os
import subprocess
import sys

wt = os.path.abspath(sys.argv[1])
terr = sys.argv[2]
out = os.path.abspath(sys.argv[3])

assert os.path.isdir(os.path.join(wt, terr)), "territory path missing: %s" % (
    os.path.join(wt, terr),)

sys.path.insert(0, os.path.join(wt, "monitor"))
import gates  # noqa: E402

row = gates.gate_for(wt, terr)          # ci_merge.gate_for -> gates.gate_for
print("KIND=%s NAME=%s" % (row["kind"], row["name"]))
print("CMD=%r" % (row["cmd"],))
assert row["kind"] == "verify", row["why"]

# ci_merge.sh(): env = os.environ + PYTHONIOENCODING/PYTHONUTF8, then extra_env
env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
env.update(gates.gate_env(wt))
r = subprocess.run(row["cmd"], cwd=os.path.join(wt, terr), capture_output=True,
                   text=True, encoding="utf-8", errors="replace", timeout=1800,
                   env=env)
print("RC=%d" % r.returncode)
with open(out, "w", encoding="utf-8", errors="replace") as fh:
    fh.write("RC=%d\nCMD=%r\nCWD=%s\n" % (r.returncode, row["cmd"],
                                          os.path.join(wt, terr)))
    fh.write("=== STDOUT ===\n" + r.stdout + "\n=== STDERR ===\n" + r.stderr)
