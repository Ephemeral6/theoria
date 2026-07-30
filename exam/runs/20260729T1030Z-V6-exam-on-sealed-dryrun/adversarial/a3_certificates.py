"""Attack 3: get a WRONG certificate accepted by exam/drill_certificates.py."""
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


def mkvariant(vid, world, ops, claim="unsolvable"):
    return Variant({
        "variant_id": vid, "base_game": world, "claim": claim,
        "justification": "x" * 60, "operators": ops,
    })


print("=" * 72)
print("A3-1  cut_set never looks at the operators")
print("=" * 72)
world = GridWorld(BY_ID["t1-walk-maze"])
# The variant that walk-win-tighten-scoreless uses: a win_tighten. It has
# nothing whatever to do with cells (4,1) and (4,7).
ops = [{"op": "win_tighten", "require": {"kind": "score_at_least", "value": 1}}]
cert = {"kind": "cut_set", "cells": [[4, 1], [4, 7]]}
print("operators :", json.dumps(ops))
print("certificate:", json.dumps(cert))
print("result    :", json.dumps(certs.check(world.spec, ops, cert), indent=2))

print()
print("... and the same certificate against a variant that is SOLVABLE:")
ops2 = [{"op": "forbid_action", "action": "UP"}]        # walk-forbid-up: solvable
v2 = mkvariant("adv-forbid-up", "t1-walk-maze", ops2, claim="solvable")
oracle2 = solve(world, v2)
print("operators :", json.dumps(ops2))
print("oracle    : solvable=%s witness_len=%s" % (
    oracle2["solvable"], None if oracle2["witness"] is None else len(oracle2["witness"])))
print("cut_set check:", json.dumps(certs.check(world.spec, ops2, cert)))

print()
print("The frozen rubric this module claims to mirror key-for-key REFUSES that,")
print("`exam/grading/rubrics_verdict.py:521-525`:")
import inspect
import exam.grading.rubrics_verdict as rv
src = inspect.getsource(rv._check_cut_set).splitlines()
for line in src[10:16]:
    print("   ", line)

print()
print("=" * 72)
print("A3-2  a real board cut that the state space walks straight through")
print("=" * 72)
gw = GridWorld(BY_ID["t2-gravity-push"])
print("t2-gravity-push, families=%s flags=%s" % (gw.spec.families, gw.spec.flags))
for i, row in enumerate(gw.spec.layout):
    print("   %d %s" % (i, row))
print("start", gw.spec.agent_start, "goal", gw.spec.goal)
cut = {"kind": "cut_set", "cells": [[2, 3]]}
ops3 = [{"op": "observation_loss", "cells": [[2, 3]], "value": 6}]
v3 = mkvariant("adv-gravity-cut", "t2-gravity-push", ops3)
print()
print("row 2 is '###.#####' -- (2,3) is its only open cell, so deleting it")
print("separates the goal from the start on the board graph:")
print("  certificate check ->", json.dumps(certs.check(gw.spec, ops3, cut)))
print()
oracle3 = solve(gw, v3)
print("  exhaustive oracle -> solvable=%s witness=%s"
      % (oracle3["solvable"], oracle3["witness"]))
if oracle3["witness"] is not None:
    out = replay(gw, v3, oracle3["witness"])
    print("  replay of that witness -> win=%s used=%d dead=%s"
          % (out["win"], out["used"], out["dead"]))
    # show that the agent is never *observed* on the cut cell
    from exam.drill_wrapper import WorldSession
    from proxy.variants import VariantRuntime
    from exam.drill_wrapper import apply_command
    s = WorldSession(gw)
    r = VariantRuntime(v3)
    b = s.body()
    b, _ = r.after(b)
    print("  agent positions actually observed, frame by frame:")
    print("    t=0 agent=%s" % (s.state.agent,))
    for t, cmd in enumerate(oracle3["witness"], 1):
        b, f, a = apply_command(r, s, cmd)
        print("    t=%d %-5s agent=%s state=%s" % (t, cmd, s.state.agent, b["state"]))
print()
print("The agent falls (1,3) -> (2,3) -> (3,3) inside one settle(); only the")
print("post-settle frame is rendered, so observation_loss on (2,3) never fires.")
print("drill_certificates.TELEPORTING = %r, NON_COMMANDED = %r; cut_set refuses")
print("only TELEPORTING, so gravity sails through." % ())

print()
print("=" * 72)
print("A3-3  invariant / counting under push, count_lock, switch_door, consumable")
print("=" * 72)
for wid in ("t1-push-open", "t1-push-corridor", "t2-switch-push", "t1-tokens-lock",
            "t1-fragile-bridge", "t1-cycler-gate"):
    w = GridWorld(BY_ID[wid])
    s = w.spec
    man = abs(s.goal[0] - s.agent_start[0]) + abs(s.goal[1] - s.agent_start[1])
    ops_c = [{"op": "step_limit", "limit": man - 1}]
    v = mkvariant("adv-count-%s" % wid, wid, ops_c)
    c = certs.check(s, ops_c, {"kind": "counting", "bound": man, "limit": man - 1})
    o = solve(w, v)
    verdict = "OK" if (c["ok"] and not o["solvable"]) or not c["ok"] else "UNSOUND"
    print("  %-20s counting bound=%d limit=%d -> accepted=%s oracle_solvable=%s  %s"
          % (wid, man, man - 1, c["ok"], o["solvable"], verdict))

print()
for wid in ("t1-push-open", "t1-push-corridor", "t2-switch-push", "t2-gravity-push",
            "t3-gravity-fragile"):
    w = GridWorld(BY_ID[wid])
    s = w.spec
    for axis, name in ((0, "agent_row"), (1, "agent_col")):
        if s.goal[axis] == s.agent_start[axis]:
            continue
        need = "DOWN" if (axis == 0 and s.goal[0] > s.agent_start[0]) else \
               "UP" if axis == 0 else \
               "RIGHT" if s.goal[1] > s.agent_start[1] else "LEFT"
        ops_i = [{"op": "forbid_action", "action": need}]
        v = mkvariant("adv-inv-%s-%s" % (wid, name), wid, ops_i)
        c = certs.check(s, ops_i, {"kind": "invariant", "invariant": name,
                                   "initial_value": s.agent_start[axis],
                                   "goal_value": s.goal[axis]})
        o = solve(w, v)
        verdict = "UNSOUND" if (c["ok"] and o["solvable"]) else "ok"
        print("  %-20s invariant %-9s forbid %-5s -> accepted=%s oracle_solvable=%s  %s"
              % (wid, name, need, c["ok"], o["solvable"], verdict))
