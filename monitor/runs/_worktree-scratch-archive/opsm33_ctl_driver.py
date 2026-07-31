"""Run one territory's gate exactly as ci_merge.py:537-544 does."""
import json
import os
import subprocess
import sys

WT = r"C:\Users\user\Desktop\theoria\.worktrees\opsm33-control"
sys.path.insert(0, os.path.join(WT, "monitor"))
import gates  # noqa: E402

terr = sys.argv[1]
out = sys.argv[2]

row = gates.gate_for(WT, terr)
info = {"territory": terr, "kind": row["kind"], "name": row["name"],
        "cmd": row["cmd"], "canonical": row["canonical"]}
if row["kind"] == "none":
    info["returncode"] = None
    print(json.dumps(info, ensure_ascii=False))
    sys.exit(0)

env = dict(os.environ)
env.update(gates.gate_env(WT))
r = subprocess.run(row["cmd"], cwd=os.path.join(WT, terr),
                   capture_output=True, text=True, encoding="utf-8",
                   errors="replace", timeout=1800, env=env)
info["returncode"] = r.returncode
with open(out, "w", encoding="utf-8") as fh:
    fh.write("=== CMD %r\n=== CWD %s\n=== RC %d\n" % (row["cmd"], os.path.join(WT, terr), r.returncode))
    fh.write("=== STDOUT ===\n" + r.stdout + "\n=== STDERR ===\n" + r.stderr)
print(json.dumps(info, ensure_ascii=False))
