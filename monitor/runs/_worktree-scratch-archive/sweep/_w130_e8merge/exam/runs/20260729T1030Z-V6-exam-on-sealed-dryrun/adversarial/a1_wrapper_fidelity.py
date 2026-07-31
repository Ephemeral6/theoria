"""Attack 1: is the drill's wrapper really the proxy's semantics, end to end?

Three probes:
  A. resumption-vs-replay: for every node the oracle reaches, replay the path it
     recorded and compare the *whole* runtime state against what the node carried.
  B. the RESET question: does admitting RESET to the alphabet change any verdict?
  C. structural diff of apply_command against proxy/env_proxy.py:373-406.
"""
import itertools
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from exam.drill_wrapper import (WorldSession, apply_command, solve, replay,
                                _runtime_at, _path)
from exam.tools.sealed_drill import VARIANTS
from proxy.variants import Variant, VariantRuntime
from worldgen.core.types import ACTIONS
from worldgen.core.world import GridWorld
from worldgen.generate import BY_ID


def mkvariant(entry):
    return Variant({"variant_id": "adv-" + entry["key"], "base_game": entry["world"],
                    "claim": entry["claim"], "justification": entry["justification"],
                    "operators": entry["operators"]})


print("=" * 72)
print("A1-A  every oracle node, resumed vs replayed")
print("=" * 72)


def all_nodes(world, variant, commands=ACTIONS):
    """Re-run solve()'s exact loop but keep every node and its stored body."""
    from exam.drill_wrapper import _step_budget
    budget = _step_budget(variant)

    def fold(c):
        return 0 if budget is None else min(c, budget + 1)
    s0 = WorldSession(world)
    b0 = s0.body()
    boot = _runtime_at(variant, 0, False, None)
    if variant is not None:
        b0, _ = boot.after(b0)
    start_key = (s0.state.key(), 0, False)
    seen = {start_key: None}
    order = [(start_key, s0.state, b0)]
    cursor = 0
    while cursor < len(order):
        nk, ns, nb = order[cursor]
        cursor += 1
        for cmd in commands:
            sess = WorldSession(world)
            sess.state = ns
            rt = _runtime_at(variant, nk[1], nk[2], nb)
            body, _f, _a = apply_command(rt, sess, cmd)
            nxt = (sess.state.key(), fold(rt.commands), rt.dead)
            if nxt in seen:
                continue
            seen[nxt] = (nk, cmd)
            order.append((nxt, sess.state, body))
    return seen, order


bad = 0
checked = 0
for entry in VARIANTS:
    world = GridWorld(BY_ID[entry["world"]])
    variant = mkvariant(entry)
    seen, order = all_nodes(world, variant)
    for nk, ns, nb in order:
        path = _path(seen, nk)
        # straight replay of the recorded path, keeping the live runtime
        sess = WorldSession(world)
        rt = VariantRuntime(variant)
        body = sess.body()
        body, _ = rt.after(body)
        for cmd in path:
            body, _f, _a = apply_command(rt, sess, cmd)
        checked += 1
        problems = []
        if sess.state.key() != nk[0]:
            problems.append("world state %s vs node %s" % (sess.state.key(), nk[0]))
        fold_rt = nk[1]
        from exam.drill_wrapper import _step_budget
        b = _step_budget(variant)
        live_fold = 0 if b is None else min(rt.commands, b + 1)
        if live_fold != fold_rt:
            problems.append("commands %s vs node %s" % (live_fold, fold_rt))
        if rt.dead != nk[2]:
            problems.append("dead %s vs node %s" % (rt.dead, nk[2]))
        if rt.last_body != nb:
            problems.append("last_body %r vs node body %r" % (rt.last_body, nb))
        if problems:
            bad += 1
            if bad <= 6:
                print("  DIVERGENCE %-28s path=%s" % (entry["key"], path))
                for p in problems:
                    print("      %s" % p)
print("  %d nodes checked, %d divergences" % (checked, bad))

print()
print("=" * 72)
print("A1-B  RESET admitted to the alphabet -- does any verdict move?")
print("=" * 72)
for entry in VARIANTS:
    world = GridWorld(BY_ID[entry["world"]])
    variant = mkvariant(entry)
    a = solve(world, variant)
    b = solve(world, variant, commands=tuple(ACTIONS) + ("RESET",))
    flag = "  <-- MOVED" if a["solvable"] != b["solvable"] else ""
    print("  %-28s no-RESET=%-5s with-RESET=%-5s nodes %d->%d%s"
          % (entry["key"], a["solvable"], b["solvable"],
             a["reachable_nodes"], b["reachable_nodes"], flag))

print()
print("=" * 72)
print("A1-C  a step_limit refusal: what the node stores vs what a live runtime holds")
print("=" * 72)
world = GridWorld(BY_ID["t1-walk-maze"])
v = Variant({"variant_id": "adv-b2", "base_game": "t1-walk-maze", "claim": "unsolvable",
             "justification": "x" * 60, "operators": [{"op": "step_limit", "limit": 2}]})
sess = WorldSession(world)
rt = VariantRuntime(v)
body = sess.body()
body, _ = rt.after(body)
for cmd in ("DOWN", "DOWN", "DOWN"):
    body, f, a = apply_command(rt, sess, cmd)
    print("  %-5s forwarded=%-5s returned state=%-12s runtime.last_body['state']=%s"
          % (cmd, f, body.get("state"), (rt.last_body or {}).get("state")))
print("  -> solve() stores the *returned* body on the node; a live runtime's")
print("     last_body is the pre-refusal one. Benign here because _terminal_body")
print("     overwrites `state` anyway, but the two are not the same object.")
