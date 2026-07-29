"""Q3: are base and mutant state spaces comparable for every operator in MUTATIONS?"""
from worldgen.core.world import GridWorld
from worldgen import mutate
from worldgen.core.types import ACTIONS

bad = []
for eid, edit in sorted(mutate.MUTANT_BY_ID.items()):
    b = GridWorld(mutate.BY_ID[edit.base])
    m = GridWorld(edit.spec())
    same_slices = b.slices == m.slices
    same_order = [x.name for x in b.mechanisms] == [x.name for x in m.mechanisms]
    nb = len(b.initial().vars); nm = len(m.initial().vars)
    ok = same_slices and same_order and nb == nm
    ops = ",".join(o["op"] + ":" + str(o.get("prop", o.get("action", ""))) for o in edit.operators)
    print("%-12s %-22s %-40s slices=%s order=%s nvars=%d/%d %s"
          % (eid, edit.base, ops, same_slices, same_order, nb, nm,
             "" if ok else "  <-- MISMATCH"))
    if not ok:
        bad.append(eid)
        print("     base ", b.slices, [x.name for x in b.mechanisms])
        print("     mut  ", m.slices, [x.name for x in m.mechanisms])

print("\nMISMATCHES:", bad)

print("\n=== cross-world explain() on foreign states: crash / var-domain check ===")
for eid, edit in sorted(mutate.MUTANT_BY_ID.items()):
    b = GridWorld(mutate.BY_ID[edit.base])
    m = GridWorld(edit.spec())
    bs = {s.key() for s in b.reachable()}
    ms = {s.key() for s in m.reachable()}
    only_m = ms - bs
    only_b = bs - ms
    errs = 0
    for s in m.reachable():
        if s.key() in only_m:
            for a in ACTIONS:
                try:
                    b.explain(s, a)
                except Exception as exc:
                    errs += 1
                    print("  %s base.explain FAILED on mutant-only state %s: %r"
                          % (eid, s.key(), exc))
                    break
            if errs:
                break
    for s in b.reachable():
        if s.key() in only_b:
            for a in ACTIONS:
                try:
                    m.explain(s, a)
                except Exception as exc:
                    errs += 1
                    print("  %s mutant.explain FAILED on base-only state %s: %r"
                          % (eid, s.key(), exc))
                    break
            if errs:
                break
    print("%-12s only_in_mutant=%-5d only_in_base=%-5d errors=%d"
          % (eid, len(only_m), len(only_b), errs))
