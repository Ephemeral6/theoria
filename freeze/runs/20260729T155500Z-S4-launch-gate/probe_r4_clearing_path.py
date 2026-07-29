"""R4 only: prove the CLEARING path works against the real vacuous artefact."""
import json, os, re, sys, shutil, tempfile
sys.path.insert(0, os.path.join(os.getcwd(), "freeze"))
import launch_gate as G

ROOT = os.getcwd()
tmp = tempfile.mkdtemp(prefix="lgr4_")

# Not an implementation of 9.2 -- a stand-in that is genuinely discriminating,
# used only to show the gate can say "clear". Real (c) is theoria-arm's item.
open(os.path.join(tmp, "nontriv.py"), "w", encoding="utf-8").write(r'''import os, re, sys
src = ""
for base, _, files in os.walk(sys.argv[1]):
    for f in files:
        if f.endswith(".lean"):
            src += open(os.path.join(base, f), encoding="utf-8", errors="replace").read()
m = re.search(r"def I .s : St. : Bool :=\s*(.+)", src)
if not m:
    sys.exit(2)                       # no invariant at all
body = m.group(1).strip()
sys.exit(1 if body in ("true", "True") else 0)
''')

reg = {k: {"state": "implemented",
           "cmd": [sys.executable, os.path.join(tmp, "nontriv.py"), "{target}"],
           "positive_target": "cold-start-a3/theory/generated_l1",
           "negative_target": "cold-start-a3/theory/generated_l1_vacuous"}
       for k in ("9.2", "9.11", "9.14")}

rules = open("freeze/STATS_RULES.md", encoding="utf-8").read()
rp = os.path.join(tmp, "r.md"); gp = os.path.join(tmp, "g.json")
open(rp, "w", encoding="utf-8").write(rules)
json.dump({"blockers": reg}, open(gp, "w", encoding="utf-8"), ensure_ascii=False)
v, f = G.gate(rules=rp, registry_path=gp, root=ROOT)
print("%s  R4 real rules + discriminating check on the REAL vacuous artefact  want=clear got=%s"
      % ("PASS" if v == "clear" else "FAIL", v))
for x in f:
    print("      §%-5s cleared=%s  %s" % (x["row"], x["cleared"], str(x["detail"])[:160]))
shutil.rmtree(tmp, ignore_errors=True)
