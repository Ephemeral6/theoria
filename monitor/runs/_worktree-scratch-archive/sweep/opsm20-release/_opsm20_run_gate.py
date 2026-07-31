"""Reproduce ci_merge.py's invocation of a territory's verify gate, faithfully.

ci_merge.try_merge does, for each touched dir `d` of the merged worktree `wt`:

    row = gates.gate_for(wt, d)                       # -> cmd = [git-bash, wt/d/verify.sh]
    r = sh(row["cmd"], cwd=os.path.join(wt, d), timeout=1800,
           extra_env=gates.gate_env(wt))              # PYTHONPATH=wt
    # ci_merge.sh() also injects PYTHONIOENCODING=utf-8 and PYTHONUTF8=1

Note the divergence this script exists to avoid: gates.run() calls gates.sh(),
which passes NO env at all -- no PYTHONPATH, no PYTHONUTF8. So `python
monitor/gates.py --run release` is NOT the same experiment as a ci_merge gate
run, and on a cp936 host the two can disagree about a decoder.

    python _opsm20_run_gate.py <worktree-root> <territory> [--no-utf8mode]
"""
import os
import subprocess
import sys

wt = os.path.abspath(sys.argv[1])
territory = sys.argv[2]
no_utf8 = "--no-utf8mode" in sys.argv

GIT_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
)
bash = next((c for c in GIT_BASH_CANDIDATES if os.path.isfile(c)), "bash")

gate = os.path.join(wt, territory, "verify.sh")
assert os.path.isfile(gate), gate
cmd = [bash, gate.replace("\\", "/")]
cwd = os.path.join(wt, territory)

env = dict(os.environ)
env["PYTHONPATH"] = wt + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
if not no_utf8:
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
else:
    env.pop("PYTHONIOENCODING", None)
    env.pop("PYTHONUTF8", None)

print("### cmd: %r" % (cmd,), flush=True)
print("### cwd: %s" % cwd, flush=True)
print("### PYTHONPATH=%s PYTHONUTF8=%s PYTHONIOENCODING=%s"
      % (env.get("PYTHONPATH"), env.get("PYTHONUTF8"),
         env.get("PYTHONIOENCODING")), flush=True)
r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                   encoding="utf-8", errors="replace", timeout=1800, env=env)
out = r.stdout + r.stderr
sys.stdout.write(out)
print("\n### EXIT CODE: %d" % r.returncode)
