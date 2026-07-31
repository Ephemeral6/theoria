"""Attack 3, round 3: make the `invariant` side condition accept a world that
teleports, by the only edit it can see -- the `families` declaration.

`_require_local_motion` reads `spec.families`.  `GridWorld` binds a mechanism
from `spec.families` OR from any entity's `kind` (`worldgen/core/world.py:52-61`),
and `worldgen/core/spec.py:validate` never checks the two agree.  So a spec that
carries a portal entity and simply does not list `portal` in `families` gets a
portal's dynamics and an axis invariant's blessing at the same time.
"""
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from exam import drill_certificates as certs
from exam.drill_wrapper import solve, replay
from proxy.variants import Variant
from worldgen.core.spec import Entity, WorldSpec
from worldgen.core.world import GridWorld

LAYOUT = ("#####",
          "#...#",
          "#####",
          "#...#",
          "#####")
PORTAL = Entity.make("portal", (1, 3), dest=[3, 3], mode="oneway")

honest = WorldSpec(world_id="adv-portal-honest", layout=LAYOUT,
                   agent_start=(1, 1), goal=(3, 1), entities=(PORTAL,),
                   colors=(("portal", 3),), families=("portal",), tier=1)
lying = WorldSpec(world_id="adv-portal-undeclared", layout=LAYOUT,
                  agent_start=(1, 1), goal=(3, 1), entities=(PORTAL,),
                  colors=(("portal", 3),), families=(), tier=1)

OPS = [{"op": "forbid_action", "action": "DOWN"}]
CERT = {"kind": "invariant", "invariant": "agent_row",
        "initial_value": 1, "goal_value": 3}
CERT_C = {"kind": "counting", "bound": 4, "limit": 3}
OPS_C = [{"op": "step_limit", "limit": 3}]

for row in LAYOUT:
    print("   ", row)
print("start (1,1)  goal (3,1)  one-way portal (1,3) -> (3,3)")
print("row 2 is solid wall: no command moves the agent between the two rooms.")
print()

for spec in (honest, lying):
    world = GridWorld(spec)
    print("%-26s families=%-11s bound mechanisms=%s"
          % (spec.world_id, str(spec.families), [m.name for m in world.mechanisms]))

    v = Variant({"variant_id": "adv-" + spec.world_id, "base_game": spec.world_id,
                 "claim": "unsolvable", "justification": "x" * 60, "operators": OPS})
    o = solve(world, v)
    r = certs.check(spec, OPS, CERT)
    print("   forbid DOWN  -> oracle solvable=%-5s witness=%s"
          % (o["solvable"], o["witness"]))
    print("                   invariant accepted=%-5s  %s"
          % (r["ok"], "*** UNSOUND: a certificate of unsolvability for a world "
                      "the oracle wins ***" if (r["ok"] and o["solvable"])
             else r.get("why", "")[:80]))

    vc = Variant({"variant_id": "adv-c-" + spec.world_id, "base_game": spec.world_id,
                  "claim": "unsolvable", "justification": "x" * 60,
                  "operators": OPS_C})
    oc = solve(world, vc)
    rc = certs.check(spec, OPS_C, CERT_C)
    print("   step_limit 3 -> oracle solvable=%-5s witness=%s"
          % (oc["solvable"], oc["witness"]))
    print("                   counting  accepted=%-5s  %s"
          % (rc["ok"], "*** UNSOUND: Manhattan bound 4 beaten in %d commands ***"
             % (len(oc["witness"]) if oc["witness"] else -1)
             if (rc["ok"] and oc["solvable"]) else rc.get("why", "")[:80]))
    print()
