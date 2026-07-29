"""Q4: is claim_dependencies really an over-approximation?

Ground truth for "claim C depends on rule R": there exists a one-operator
perturbation of the world that (a) changes R's firing behaviour and (b) changes
C's truth value or its checked outcome.  Cheaper and sharper test used here:
for every claim C and rule R, does C's *value* on the reachable set depend on
transitions tagged R?  We approximate by a semantic test: recompute the claim on
a world in which R has been suppressed is not possible, so instead we check the
two structural properties the docstring asserts, plus a direct hunt for
invariants whose check reads cells another mechanism draws.
"""
import inspect
from worldgen.core import truth
from worldgen.core.world import GridWorld
from worldgen.core.types import ACTIONS, AGENT
from worldgen import mutate
from worldgen.generate import BY_ID, CATALOGUE

print("=== _invariant_owners: does any name get claimed twice? ===")
for spec in CATALOGUE:
    w = GridWorld(spec)
    counts = {}
    for m in w.mechanisms:
        for r in m.invariants(w.spec, w.mine(m)):
            counts.setdefault(r["name"], []).append(m.name)
    for name, owners in sorted(counts.items()):
        if len(owners) > 1:
            print("  COLLISION %-24s %s -> owners %s (kept: %s)"
                  % (spec.world_id, name, owners, owners[-1]))
    # world-level names shadowed by a mechanism?
    world_level = {"agent_unique", "grid_shape"}
    for name in sorted(counts):
        if name in world_level:
            print("  SHADOW %-24s mechanism %s redeclares world-level %s"
                  % (spec.world_id, counts[name], name))
print("  (no output above = no collisions)")

print("\n=== which invariants read the WHOLE frame (i.e. any mechanism's cells)? ===")
seen_src = set()
for spec in CATALOGUE:
    w = GridWorld(spec)
    owners = mutate._invariant_owners(w)
    for m in w.mechanisms:
        for r in m.invariants(w.spec, w.mine(m)):
            chk = r.get("check")
            if chk is None:
                continue
            try:
                src = inspect.getsource(chk)
            except Exception:
                continue
            key = (m.name, r["name"])
            if key in seen_src:
                continue
            seen_src.add(key)
            if "render" in src:
                print("  %-14s %-28s reads world.render() -> whole frame" % (m.name, r["name"]))

print("\n=== per-base: claims x rules, and rules NOT depended on by each claim ===")
for base in sorted({e.base for e in mutate.MUTATIONS}):
    w = GridWorld(BY_ID[base])
    d = mutate.claim_dependencies(w)
    allrules = sorted(d["rule_moves_agent"])
    print("\n-- %s  rules=%s" % (base, allrules))
    for claim, deps in sorted(d["claims"].items()):
        missing = [r for r in allrules if r not in deps]
        print("   %-32s owner=%-12s missing=%s" % (claim, d["claim_owner"][claim], missing))
