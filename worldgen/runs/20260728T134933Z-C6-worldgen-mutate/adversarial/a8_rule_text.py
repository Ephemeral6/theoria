"""Q8: base_rules' replace() and whether mechanism rule text goes stale."""
from worldgen.core import truth
from worldgen.core.world import GridWorld
from worldgen import mutate
from worldgen.generate import BY_ID

print("=== BASE_RULES 'act=D and ' present? ===")
for r in truth.BASE_RULES:
    print(" ", r["name"], "->", "act=D and " in r["when"])

for eid, edit in sorted(mutate.MUTANT_BY_ID.items()):
    if edit.edit_family != "forbid_action":
        continue
    w = GridWorld(edit.spec())
    print("\n=== %s (%s, forbid %s) ===" % (eid, edit.base,
          sorted(w.forbidden)))
    for r in truth.base_rules(w):
        print("  BASE %-18s when=%s" % (r["name"], r["when"][:110]))
    stale = []
    for m in w.mechanisms:
        for r in m.truth_rules(w.spec, w.mine(m)):
            if r["when"].startswith("act=D and "):
                stale.append((m.name, r["name"], r["when"]))
    print("  STALE mechanism rules (still say 'act=D and ...', unguarded): %d" % len(stale))
    for mn, rn, wh in stale:
        print("    %-12s %-22s %s" % (mn, rn, wh[:100]))
