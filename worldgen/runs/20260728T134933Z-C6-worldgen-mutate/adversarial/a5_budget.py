"""Q5: greedy_witness_budget -- state tracking, upper-bound claim, orphan logic."""
from worldgen.core.world import GridWorld
from worldgen.core.explorer import shortest_paths
from worldgen.core.types import ACTIONS
from worldgen import mutate


def instrumented(base, mutant):
    classes = {}
    for state in base.reachable():
        for action in ACTIONS:
            nb, rb = base.explain(state, action)
            nm, rm = mutant.explain(state, action)
            if nb == nm and rb == rm:
                continue
            classes.setdefault((rb, rm), []).append((state.key(), action))

    # classes visible ONLY from mutant-reachable states -- invisible to the fn
    mut_classes = {}
    for state in mutant.reachable():
        for action in ACTIONS:
            nb, rb = base.explain(state, action)
            nm, rm = mutant.explain(state, action)
            if nb == nm and rb == rm:
                continue
            mut_classes.setdefault((rb, rm), []).append((state.key(), action))
    missed = sorted(set(mut_classes) - set(classes))

    reachable_in_mutant = {s.key() for s in mutant.reachable()}
    wanted = {}
    orphans = []
    for key, sites in sorted(classes.items()):
        live = {s for s in sites if s[0] in reachable_in_mutant}
        if live:
            wanted[key] = live
        else:
            orphans.append(key)

    state = mutant.initial()
    spent = 0
    tracking_ok = True
    stalled = None
    witnessed = set()
    while wanted:
        paths = shortest_paths(mutant, state)
        pool = [(len(paths[k]), k, a, cls)
                for cls, sites in wanted.items()
                for k, a in sorted(sites) if k in paths]
        if not pool:
            stalled = sorted(wanted)
            break
        _c, k, a, cls = min(pool)
        spent += len(paths[k]) + 1
        for sa in paths[k]:
            state = mutant.step(state, sa)
        if state.key() != k:
            tracking_ok = False
        # what did we actually witness with this action?
        nb, rb = base.explain(state, a)
        nm, rm = mutant.explain(state, a)
        if not (nb == nm and rb == rm):
            witnessed.add((rb, rm))
        state = mutant.step(state, a)
        wanted.pop(cls, None)
    return dict(spent=spent, classes=len(classes), orphans=orphans,
                stalled=stalled, tracking_ok=tracking_ok,
                witnessed=len(witnessed), missed=missed)


print("%-12s %-6s %-8s %-8s %-6s %-9s %s" %
      ("id", "spent", "classes", "orphans", "track", "witnessed", "stalled/missed"))
for eid, edit in sorted(mutate.MUTANT_BY_ID.items()):
    b = GridWorld(mutate.BY_ID[edit.base])
    m = GridWorld(edit.spec())
    r = instrumented(b, m)
    shipped = mutate.greedy_witness_budget(b, m)
    flag = ""
    if r["stalled"]:
        flag += " STALLED:%s" % (r["stalled"],)
    if r["missed"]:
        flag += " MUTANT-ONLY-CLASSES:%s" % (r["missed"],)
    if not r["tracking_ok"]:
        flag += " TRACKING-BROKEN"
    assert shipped["greedy_actions"] == r["spent"], (eid, shipped, r)
    print("%-12s %-6d %-8d %-8d %-6s %-9d %s" %
          (eid, r["spent"], r["classes"], len(r["orphans"]), r["tracking_ok"],
           r["witnessed"], flag))
