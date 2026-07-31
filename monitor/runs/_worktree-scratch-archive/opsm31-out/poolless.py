"""Read-only single-variable experiment.

Arm A's checkout, Arm A's committed BUDGET_TABLE.{json,md}, Arm A's generator --
the ONLY thing changed is that resolve_pool() returns None, which is exactly what
it does when REPO is not under `.worktrees/` (ci_merge uses tempfile.mkdtemp,
monitor/ci_merge.py:513).  Replicates main()'s `--verify` block verbatim.
Writes nothing.
"""
import importlib.util
import json
import os
import sys

WT = os.path.abspath(sys.argv[1])
spec = importlib.util.spec_from_file_location(
    "bbt", os.path.join(WT, "freeze", "build_budget_table.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print("REPO: %s" % m.REPO)
print("resolve_pool BEFORE patch: %r" % m.resolve_pool("proxy/var/spend_gate.jsonl"))
m.resolve_pool = lambda rel: None            # the one variable
print("resolve_pool AFTER  patch: %r" % m.resolve_pool("proxy/var/spend_gate.jsonl"))
print("--- now replaying main()'s --verify block (allow_absent_pool=False, "
      "as freeze/verify.sh:1158 invokes it) ---")

data = m.build()
text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
block = m.render(data)

rc = 0
strip = lambda blob: {k: v for k, v in json.loads(blob).items()
                      if k != "generated_from"}
on_disk = open(m.OUT_JSON, encoding="utf-8").read()
if strip(on_disk) != strip(text):
    old, new = strip(on_disk), strip(text)
    moved = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
    print("DRIFT: freeze/BUDGET_TABLE.json no longer describes this tree.")
    print("       sections that moved: %s" % ", ".join(moved))
    if "pool" in moved or "balance" in moved:
        print("       `pool`/`balance` moved => THE BALANCE MOVED.")
    rc = 1
spliced = m.splice(block)
if spliced is None:
    print("DRIFT: freeze/BUDGET_TABLE.md is missing or has lost its markers.")
    rc = 1
elif spliced != open(m.OUT_MD, encoding="utf-8").read():
    print("DRIFT: the generated block in freeze/BUDGET_TABLE.md is stale or "
          "was hand-edited.")
    rc = 1
if not data["pool"]["present"]:
    print("POOL ABSENT: %s" % data["pool"]["why"])
    rc = 1                                   # no --allow-absent-pool in verify.sh
if data["citations"]["drifted"]:
    print("CITATION DRIFT: %s" % ", ".join(data["citations"]["drifted"]))
    rc = 1
print("RC=%d" % rc)
