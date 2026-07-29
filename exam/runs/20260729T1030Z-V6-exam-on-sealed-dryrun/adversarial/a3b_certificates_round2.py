"""Attack 3, round 2, against the code as it stands after the author's own
gravity/cut_set fix (SEALED_DRILL.md 4b).

Two holes remain:
  B1. `cut_set` still never relates its cells to the variant's operators, so a
      certificate can be accepted for a world it does not describe.
  B2. every side condition is keyed on `spec.families`, which is a *declaration*.
      `GridWorld` binds mechanisms from entity kinds as well
      (`worldgen/core/world.py:51-61`) and `worldgen/core/spec.py:validate` never
      checks the two agree, so a spec that simply omits the family name gets
      every refusal waived.
"""
import dataclasses
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from exam import drill_certificates as certs
from exam.drill_wrapper import solve, replay
from proxy.variants import Variant
from worldgen.core.world import GridWorld
from worldgen.generate import BY_ID


def mkv(vid, world, ops, claim="unsolvable"):
    return Variant({"variant_id": vid, "base_game": world, "claim": claim,
                    "justification": "x" * 60, "operators": ops})


print("=" * 72)
print("B1  cut_set cells are never checked against the variant's hazards")
print("=" * 72)
world = GridWorld(BY_ID["t1-walk-maze"])
CUT = {"kind": "cut_set", "cells": [[4, 1], [4, 7]]}

cases = [
    ("no observation_loss at all (a win_tighten variant)",
     [{"op": "win_tighten", "require": {"kind": "score_at_least", "value": 1}}]),
    ("no observation_loss at all (a forbid_action variant, SOLVABLE)",
     [{"op": "forbid_action", "action": "UP"}]),
    ("observation_loss on the right cells but the WRONG colour (2, not 6)",
     [{"op": "observation_loss", "cells": [[4, 1], [4, 7]], "value": 2}]),
    ("observation_loss on two completely different cells",
     [{"op": "observation_loss", "cells": [[1, 2], [1, 3]], "value": 6}]),
]
for label, ops in cases:
    v = mkv("adv-b1", "t1-walk-maze", ops, claim="unsolvable")
    res = certs.check(world.spec, ops, CUT)
    o = solve(world, v)
    bad = res["ok"] and o["solvable"]
    print("  %-58s" % label[:58])
    print("      certificate accepted=%-5s   oracle says solvable=%-5s   %s"
          % (res["ok"], o["solvable"], "ACCEPTED A FALSE CERTIFICATE" if bad else "-"))

print()
print("  For contrast, the frozen rubric refuses all four "
      "(rubrics_verdict.py:521-525 requires every cut cell to be in "
      "`level.lost_cells`).")

print()
print("=" * 72)
print("B2  the side conditions key on a self-declaration, not on the mechanisms")
print("=" * 72)
real = BY_ID["t1-portal-oneway"]
print("  t1-portal-oneway as shipped: families=%s entities=%s"
      % (real.families, [(e.kind, e.cell) for e in real.entities]))
lied = dataclasses.replace(real, families=(), world_id="t1-portal-oneway-undeclared")
w_real, w_lied = GridWorld(real), GridWorld(lied)
print("  with `families` emptied, GridWorld still binds: %s"
      % [m.name for m in w_lied.mechanisms])
print("  ...identical to the honest spec's: %s"
      % [m.name for m in w_real.mechanisms])
same = all(w_real.step(w_real.initial(), a).agent == w_lied.step(w_lied.initial(), a).agent
           for a in ("UP", "DOWN", "LEFT", "RIGHT"))
print("  and the transition function is unchanged (first-step agreement: %s)" % same)

axis, name = 0, "agent_row"
s, g = lied.agent_start[axis], lied.goal[axis]
need = "DOWN" if g > s else "UP"
ops = [{"op": "forbid_action", "action": need}]
cert = {"kind": "invariant", "invariant": name, "initial_value": s, "goal_value": g}
print()
for spec, w, tag in ((real, w_real, "families declared"),
                     (lied, w_lied, "families omitted ")):
    v = mkv("adv-b2-" + tag.strip(), spec.world_id, ops)
    r = certs.check(spec, ops, cert)
    o = solve(w, v)
    print("  %s -> invariant accepted=%-5s  oracle solvable=%-5s  %s"
          % (tag, r["ok"], o["solvable"],
             "UNSOUND" if (r["ok"] and o["solvable"]) else
             ("refused, correctly" if not r["ok"] else "sound here")))
    if not r["ok"]:
        print("       (%s)" % r["why"][:100])

print()
grav = BY_ID["t2-gravity-push"]
lied_g = dataclasses.replace(grav, families=("push",),
                             world_id="t2-gravity-push-undeclared")
wg = GridWorld(lied_g)
print("  same trick on the gravity world: families=('push',) but flag gravity=%s"
      % lied_g.flag("gravity"))
print("  bound mechanisms: %s" % [m.name for m in wg.mechanisms])
ops_g = [{"op": "observation_loss", "cells": [[2, 3]], "value": 6}]
vg = mkv("adv-b2-grav", lied_g.world_id, ops_g)
rg = certs.check(lied_g, ops_g, {"kind": "cut_set", "cells": [[2, 3]]})
og = solve(wg, vg)
print("  cut_set accepted=%-5s   oracle solvable=%-5s   %s"
      % (rg["ok"], og["solvable"],
         "UNSOUND -- the fix of SEALED_DRILL.md 4b is bypassed by one edit "
         "to a declaration" if (rg["ok"] and og["solvable"]) else "refused"))
if og["witness"]:
    print("  witness: %s" % og["witness"])
