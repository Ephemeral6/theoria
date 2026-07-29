"""Q1 fuzz: every legal single-knob edit of every catalogue world, compared
against two independent oracles.  Much wider than the 15 shipped mutants."""
import itertools, sys
from collections import deque
from worldgen.core.world import GridWorld
from worldgen.core.types import ACTIONS
from worldgen import mutate
from worldgen.mutate import _frame_key, earliest_detection, _apply_one
from worldgen.generate import CATALOGUE
sys.path.insert(0, "worldgen/runs/20260728T134933Z-C6-worldgen-mutate/adversarial")
from a1_earliest import full_product_min_depth, brute_force

DOMAINS = {
    ("switch", "mode"): ["toggle", "latch"],
    ("door", "polarity"): ["open_when_on", "open_when_off"],
    ("door", "net"): ["a", "b", "c"],
    ("switch", "net"): ["a", "b", "c"],
    ("lock", "k"): [1, 2, 3, 4],
    ("cycler", "open_phase"): [0, 1, 2],
    ("cycler", "phase0"): [None, 0, 1, 2],
    ("portal", "mode"): ["oneway", "twoway", "paired"],
}

n = 0; disagree = 0
for spec in CATALOGUE:
    for ent in spec.entities:
        for (kind, prop), values in DOMAINS.items():
            if ent.kind != kind:
                continue
            cur = ent.prop(prop)
            for v in values:
                if v == cur:
                    continue
                op = {"op": "set_prop", "kind": kind, "cell": list(ent.cell),
                      "prop": prop, "from": cur, "to": v}
                try:
                    ms = _apply_one(spec, op)
                    b = GridWorld(spec); m = GridWorld(ms)
                    b.reachable(); m.reachable()
                except Exception:
                    continue
                # portal dest edits, too
                got = earliest_detection(b, m)
                a_d, _w, a_ok = full_product_min_depth(b, m)
                cap = 5 if (got["actions"] is None or got["actions"] > 5) else got["actions"] + 1
                bf, _ = brute_force(b, m, min(cap, 5))
                n += 1
                ok = (got["actions"] == a_d) and (bf is None or bf == got["actions"])
                if not ok:
                    disagree += 1
                    print("DISAGREE %-24s %s %s->%s  shipped=%s A=%s B=%s"
                          % (spec.world_id, (kind, prop), cur, v,
                             got["actions"], a_d, bf))
                if got["actions"] is None and got["complete"]:
                    print("OBS-EQUIV %-24s %s %s->%s" % (spec.world_id, (kind, prop), cur, v))
print("pairs tested: %d, disagreements: %d" % (n, disagree))
