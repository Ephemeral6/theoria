"""Run the real STATS_RULES.md through each bypass. Red is the only pass."""
import json, os, sys, shutil, tempfile
sys.path.insert(0, os.path.join(os.getcwd(), "freeze"))
import launch_gate as G

REAL_RULES = open("freeze/STATS_RULES.md", encoding="utf-8").read()
ROOT = os.getcwd()
tmp = tempfile.mkdtemp(prefix="lgprobe_")

def run(name, rules, blockers, expect):
    rp = os.path.join(tmp, "r.md"); gp = os.path.join(tmp, "g.json")
    open(rp, "w", encoding="utf-8").write(rules)
    json.dump({"blockers": blockers}, open(gp, "w", encoding="utf-8"), ensure_ascii=False)
    try:
        v, f = G.gate(rules=rp, registry_path=gp, root=ROOT)
    except G.GateError as e:
        v, f = "error", str(e)
    print("%s  %-58s want=%s got=%s" % ("PASS" if v == expect else "FAIL", name, expect, v))
    return v, f

real_reg = json.load(open("freeze/launch_blockers.json", encoding="utf-8"))["blockers"]

# baseline: the real pair, today
run("R0 real rules + real registry (today's true state)", REAL_RULES, real_reg, "blocked")

# R1 downgrade 9.2's type cell in the real table
r1 = REAL_RULES.replace(
    "| 9.2 | U3「非平凡定理」判据 (c) 的可执行检查 | **开跑前置条件**（2026-07-29 自 `needs_impl` 升级，S4 N-3/N-4）",
    "| 9.2 | U3「非平凡定理」判据 (c) 的可执行检查 | **needs_impl**")
assert r1 != REAL_RULES, "R1 mutation did not apply -- probe is testing nothing"
run("R1 9.2 downgraded to needs_impl in the real table", r1, real_reg, "blocked")

# R2 delete the 9.2 row outright
r2 = "\n".join(l for l in REAL_RULES.splitlines() if not l.startswith("| 9.2 |"))
assert r2 != REAL_RULES, "R2 mutation did not apply"
run("R2 the 9.2 row deleted from the real table", r2, real_reg, "blocked")

# R3 all three flipped to implemented, pointed at a check that accepts anything
open(os.path.join(tmp, "yes.py"), "w").write("import sys; sys.exit(0)\n")
r3reg = {k: {"state": "implemented",
             "cmd": [sys.executable, os.path.join(tmp, "yes.py"), "{target}"],
             "positive_target": "freeze/STATS_RULES.md",
             "negative_target": "cold-start-a3/theory/generated_l1_vacuous"}
         for k in real_reg}
run("R3 all three 'implemented' by a check that accepts everything", REAL_RULES, r3reg, "blocked")

# R4 kept as found: this was my FIRST attempt at a criterion-(c) check, written
#    off the cuff, and the gate rejected it as non-discriminating -- the vacuous
#    artefact passes a "has a theorem, and it isn't literally True" heuristic.
#    That is the gate doing its job on a real case rather than a fixture, so the
#    case stays, with the expectation corrected to what it demonstrates.
#    The clearing path is proved separately in probe_r4_clearing_path.py.
open(os.path.join(tmp, "nontriv.py"), "w", encoding="utf-8").write('''import os, sys
# accepts a theory dir only if its Lean file states something with content
p = sys.argv[1]
src = ""
for base, _, files in os.walk(p):
    for f in files:
        if f.endswith(".lean"):
            src += open(os.path.join(base, f), encoding="utf-8", errors="replace").read()
sys.exit(0 if ("theorem" in src and "True" not in src.split("theorem")[-1][:200]) else 1)
''')
r4reg = dict(real_reg)
for k in r4reg:
    r4reg[k] = {"state": "implemented",
                "cmd": [sys.executable, os.path.join(tmp, "nontriv.py"), "{target}"],
                "positive_target": "cold-start-a3/theory/generated_l1",
                "negative_target": "cold-start-a3/theory/generated_l1_vacuous"}
v, f = run("R4 my first off-the-cuff (c) check -- caught as non-discriminating", REAL_RULES, r4reg, "blocked")
if v != "blocked":
    for x in f:
        if not x["cleared"]:
            print("      §%s: %s" % (x["row"], str(x["detail"])[:300]))
shutil.rmtree(tmp, ignore_errors=True)
