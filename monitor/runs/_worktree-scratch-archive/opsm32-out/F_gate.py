"""Run one territory's gate exactly as monitor/ci_merge.py does.

usage: python F_gate.py <worktree-abs-path> <territory> <out-file>
"""
import os, subprocess, sys

wt, terr, outp = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(wt, "monitor"))
for m in [m for m in list(sys.modules) if m == "gates"]:
    del sys.modules[m]
import gates
sys.path.pop(0)
row = gates.gate_for(wt, terr)
env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
env.update(gates.gate_env(wt))
p = subprocess.run(row["cmd"], cwd=os.path.join(wt, terr), capture_output=True,
                   text=True, encoding="utf-8", errors="replace",
                   timeout=1800, env=env)
out = (p.stdout or "") + (p.stderr or "")
with open(outp, "w", encoding="utf-8", errors="replace") as fh:
    fh.write("worktree: %s\nterritory: %s\ncmd: %r\ncwd: %s\nrc: %d\n%s\n%s"
             % (wt, terr, row["cmd"], os.path.join(wt, terr), p.returncode,
                "-" * 70, out))
print("rc=%d -> %s" % (p.returncode, outp))
