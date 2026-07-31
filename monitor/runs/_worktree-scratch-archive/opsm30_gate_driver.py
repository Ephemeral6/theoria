"""Replicate ci_merge.py's gate invocation exactly (NOT gates.run()).

ci_merge:  r = sh(cmd, cwd=os.path.join(wt, d), timeout=1800,
                  extra_env=gates.gate_env(wt))
   where sh() = subprocess.run(..., env=dict(os.environ,
                 PYTHONIOENCODING="utf-8", PYTHONUTF8="1") updated with extra_env)
   and gate_env(wt) = os.environ + PYTHONPATH=wt prepended.
"""
import os
import subprocess
import sys

WT = os.path.abspath(sys.argv[1])
TERRITORY = sys.argv[2]

sys.path.insert(0, os.path.join(WT, "monitor"))
import gates  # noqa: E402

base = os.path.join(WT, TERRITORY)
print("PATH-EXISTS %s -> %s" % (base, os.path.isdir(base)))
row = gates.gate_for(WT, TERRITORY)
print("GATE kind=%s name=%s cmd=%r" % (row["kind"], row["name"], row["cmd"]))
if row["kind"] == "none":
    print("RC=none")
    raise SystemExit(0)

env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
env.update(gates.gate_env(WT))
print("PYTHONPATH=%s" % env["PYTHONPATH"])

r = subprocess.run(row["cmd"], cwd=base, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=1800, env=env)
out = r.stdout + r.stderr
sys.stdout.write(out)
print("\n==== RC=%d ====" % r.returncode)
