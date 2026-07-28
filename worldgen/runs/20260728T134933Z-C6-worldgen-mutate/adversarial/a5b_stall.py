"""Q5: prove the v-eb4c5810 stall is permanent, and price the true optimum."""
from worldgen.core.world import GridWorld
from worldgen.core.explorer import shortest_paths
from worldgen.core.types import ACTIONS
from worldgen import mutate

edit = mutate.MUTANT_BY_ID["v-eb4c5810"]
b = GridWorld(mutate.BY_ID[edit.base]); m = GridWorld(edit.spec())
print("agent_start", b.spec.agent_start, "goal", b.spec.goal)

target_cls = ("walk_through_cycler", "action_forbidden")
sites = []
for s in b.reachable():
    for a in ACTIONS:
        nb, rb = b.explain(s, a); nm, rm = m.explain(s, a)
        if (nb == nm and rb == rm):
            continue
        if (rb, rm) == target_cls:
            sites.append((s.key(), a))
mr = {s.key() for s in m.reachable()}
print("sites for", target_cls, sites)
print("of which reachable in mutant:", [x for x in sites if x[0] in mr])

# replay the greedy walk exactly, printing the state after each pick
state = m.initial()
classes = {}
for s in b.reachable():
    for a in ACTIONS:
        nb, rb = b.explain(s, a); nm, rm = m.explain(s, a)
        if nb == nm and rb == rm:
            continue
        classes.setdefault((rb, rm), []).append((s.key(), a))
wanted = {k: {x for x in v if x[0] in mr} for k, v in sorted(classes.items())
          if {x for x in v if x[0] in mr}}
print("wanted classes:", sorted(wanted))
spent = 0
while wanted:
    paths = shortest_paths(m, state)
    pool = [(len(paths[k]), k, a, cls) for cls, ss in wanted.items()
            for k, a in sorted(ss) if k in paths]
    if not pool:
        print("STALL at state", state.key(), "-- still wanted:", sorted(wanted))
        for cls in sorted(wanted):
            for k, a in sorted(wanted[cls]):
                print("   site", cls, k, a, "reachable-from-here:", k in paths)
        break
    _c, k, a, cls = min(pool)
    spent += len(paths[k]) + 1
    for sa in paths[k]:
        state = m.step(state, sa)
    state = m.step(state, a)
    wanted.pop(cls)
    print("picked %-45s cost=%d  now at %s  spent=%d" % (str(cls), _c + 1, state.key(), spent))

# true optimum: BFS over (mutant state, covered-set) to witness all 3
import itertools
from collections import deque
all_cls = sorted({k for k, v in classes.items() if {x for x in v if x[0] in mr}})
idx = {c: i for i, c in enumerate(all_cls)}
full = (1 << len(all_cls)) - 1
start = m.initial()
seen = {(start.key(), 0)}
q = deque([(start, 0, 0)])
opt = None
while q:
    st, cov, d = q.popleft()
    if cov == full:
        opt = d
        break
    for a in ACTIONS:
        nb, rb = b.explain(st, a); nm, rm = m.explain(st, a)
        c2 = cov
        if not (nb == nm and rb == rm) and (rb, rm) in idx:
            c2 |= 1 << idx[(rb, rm)]
        key = (nm.key(), c2)
        if key in seen:
            continue
        seen.add(key)
        q.append((nm, c2, d + 1))
print("greedy reported:", mutate.greedy_witness_budget(b, m)["greedy_actions"])
print("true optimal walk witnessing all %d classes: %s" % (len(all_cls), opt))
