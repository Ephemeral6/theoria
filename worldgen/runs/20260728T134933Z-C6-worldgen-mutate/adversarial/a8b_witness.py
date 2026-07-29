"""Q8: a concrete state where the shipped mechanism rule text is false."""
import json, os
from worldgen.core.world import GridWorld
from worldgen import mutate

edit = mutate.MUTANT_BY_ID["v-eb4c5810"]
w = GridWorld(edit.spec())
base = GridWorld(mutate.BY_ID[edit.base])
print("cycler entities:", [(e.kind, e.cell, e.props) for e in w.spec.entities])
print("layout:")
for r in w.spec.layout:
    print("   ", r)

found = 0
for s in w.reachable():
    for a in ("UP",):
        from worldgen.core.types import shift
        tgt = shift(s.agent, a)
        if any(e.kind == "cycler" and e.cell == tgt for e in w.spec.entities):
            nxt, rule = w.explain(s, a)
            nb, rb = base.explain(s, a)
            print("state agent=%s vars=%s  act=UP target=%s" % (s.agent, s.vars, tgt))
            print("  mutant: rule=%-18s vars->%s" % (rule, nxt.vars))
            print("  base  : rule=%-18s vars->%s" % (rb, nb.vars))
            found += 1
            if found >= 3:
                break
    if found >= 3:
        break
print("UP-into-cycler situations reachable in the mutant:", found)

p = os.path.join("worldgen", "out", "worlds", "v-eb4c5810", "ground_truth.json")
if os.path.exists(p):
    blob = json.load(open(p, encoding="utf-8"))
    for r in blob["rules"]:
        if r["name"] in ("advance_cycler", "walk_through_cycler", "action_forbidden"):
            print("SHIPPED %-20s when=%s" % (r["name"], r["when"]))
