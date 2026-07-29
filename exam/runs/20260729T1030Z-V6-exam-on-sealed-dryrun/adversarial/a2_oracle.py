"""Attack 2: is the exhaustive oracle exhaustive?

`solve()` folds the command counter -- to 0 when no `step_limit` is declared,
to `min(commands, budget+1)` otherwise -- and resumes a `VariantRuntime` at each
node instead of replaying.  Both are load-bearing; both are places a merge of two
genuinely different states would produce a wrong answer.

The decider below shares nothing with `solve()`:

  * it never resumes -- every candidate sequence is replayed from t=0 through a
    fresh `VariantRuntime`;
  * its visited key is the FULL runtime state (world state, command counter,
    dead, the serialised `last_body`) -- every attribute `VariantRuntime` holds,
    plus the world;
  * the ONLY concession is that the counter must be capped or the key set is
    infinite when no `step_limit` is declared.  So the cap is *swept*: if
    `solve()`'s folding merged two genuinely different states, raising the cap
    would change an answer or a shortest-witness length somewhere.

A2-B then checks that `OracleTruncated` fires before a truncated search can
return "unsolvable".
"""
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from exam.drill_wrapper import (WorldSession, apply_command, solve,
                                OracleTruncated, _step_budget)
from exam.tools.sealed_drill import VARIANTS
from proxy.variants import Variant, VariantRuntime
from worldgen.core.types import ACTIONS
from worldgen.core.world import GridWorld
from worldgen.generate import BY_ID


def run_sequence(world, variant, seq):
    """A full episode from t=0. No resumption anywhere."""
    sess = WorldSession(world)
    rt = VariantRuntime(variant)
    body = sess.body()
    if variant is not None:
        body, _ = rt.after(body)
    if rt.dead:
        return sess, rt, False
    if body.get("state") == "WIN":
        return sess, rt, True
    for cmd in seq:
        body, _f, _a = apply_command(rt, sess, cmd)
        if body.get("state") == "WIN":
            return sess, rt, True
    return sess, rt, False


def independent_decide(world, variant, cap, commands=ACTIONS, node_cap=300_000):
    """BFS over command sequences, each replayed from scratch, memoised on the
    whole runtime state with the counter capped at `cap`."""
    seen = set()

    def sig(sess, rt):
        return (sess.state.key(), min(rt.commands, cap), rt.dead,
                json.dumps(rt.last_body, sort_keys=True))

    sess, rt, won = run_sequence(world, variant, ())
    if won:
        return True, [], 1
    seen.add(sig(sess, rt))
    frontier = [()]
    while frontier:
        nxt = []
        for prefix in frontier:
            for cmd in commands:
                seq = prefix + (cmd,)
                sess, rt, won = run_sequence(world, variant, seq)
                if won:
                    return True, list(seq), len(seen)
                s = sig(sess, rt)
                if s in seen:
                    continue
                if len(seen) > node_cap:
                    raise RuntimeError("cap")
                seen.add(s)
                nxt.append(seq)
        frontier = nxt
    return False, None, len(seen)


def mkv(vid, world, ops):
    return Variant({"variant_id": vid, "base_game": world, "claim": "unsolvable",
                    "justification": "x" * 60, "operators": ops})


CASES = [("drill:" + e["key"], e["world"], e["operators"]) for e in VARIANTS] + [
    ("two-step-limits-20-and-9", "t1-walk-maze",
     [{"op": "step_limit", "limit": 20}, {"op": "step_limit", "limit": 9}]),
    ("two-step-limits-40-and-10", "t1-walk-maze",
     [{"op": "step_limit", "limit": 40}, {"op": "step_limit", "limit": 10}]),
    ("two-step-limits-equal-10", "t1-walk-maze",
     [{"op": "step_limit", "limit": 10}, {"op": "step_limit", "limit": 10}]),
    ("limit-zero", "t1-walk-maze", [{"op": "step_limit", "limit": 0}]),
    ("loss-plus-budget-14", "t1-walk-maze",
     [{"op": "observation_loss", "cells": [[4, 1]], "value": 6},
      {"op": "step_limit", "limit": 14}]),
    ("loss-plus-budget-13", "t1-walk-maze",
     [{"op": "observation_loss", "cells": [[4, 1]], "value": 6},
      {"op": "step_limit", "limit": 13}]),
    ("loss-on-start-cell", "t1-walk-maze",
     [{"op": "observation_loss", "cells": [[1, 1]], "value": 6}]),
    ("loss-on-goal-cell", "t1-walk-maze",
     [{"op": "observation_loss", "cells": [[5, 7]], "value": 6}]),
    ("win-tighten-plus-budget-12", "t1-walk-maze",
     [{"op": "win_tighten", "require": {"kind": "score_at_least", "value": 1}},
      {"op": "step_limit", "limit": 12}]),
    ("win-tighten-value-zero", "t1-walk-maze",
     [{"op": "win_tighten", "require": {"kind": "score_at_least", "value": 0}}]),
    ("forbid-plus-budget-10", "t1-walk-maze",
     [{"op": "forbid_action", "action": "LEFT"}, {"op": "step_limit", "limit": 10}]),
    ("remap-onto-forbidden", "t1-walk-maze",
     [{"op": "forbid_action", "action": "UP"},
      {"op": "remap_action", "from": "LEFT", "to": "UP"}]),
    ("push-corridor-budget-5", "t1-push-corridor", [{"op": "step_limit", "limit": 5}]),
    ("push-corridor-budget-4", "t1-push-corridor", [{"op": "step_limit", "limit": 4}]),
    ("push-open-budget-3", "t1-push-open", [{"op": "step_limit", "limit": 3}]),
    ("fragile-budget-6", "t1-fragile-bridge", [{"op": "step_limit", "limit": 6}]),
    ("fragile-forbid-right", "t1-fragile-bridge",
     [{"op": "forbid_action", "action": "RIGHT"}]),
    ("gravity-cut-2-3", "t2-gravity-push",
     [{"op": "observation_loss", "cells": [[2, 3]], "value": 6}]),
    ("gravity-budget-10", "t2-gravity-push", [{"op": "step_limit", "limit": 10}]),
    ("gravity-budget-9", "t2-gravity-push", [{"op": "step_limit", "limit": 9}]),
    ("switch-toggle-forbid-up", "t1-switch-toggle",
     [{"op": "forbid_action", "action": "UP"}]),
    ("tokens-lock-budget-10", "t1-tokens-lock", [{"op": "step_limit", "limit": 10}]),
    ("cycler-gate-budget-6", "t1-cycler-gate", [{"op": "step_limit", "limit": 6}]),
]

print("A2-A  solve()'s folded/resumed graph vs a from-scratch replay search")
print("      (cap = the counter cap in the INDEPENDENT decider; solve() always")
print("       folds at budget+1, or at 0 when no step_limit is declared)")
print()
print("%-27s %-7s %-6s | %s" % ("case", "solve", "wit", "independent, per cap"))
print("-" * 96)
bad = 0
for name, wid, ops in CASES:
    world = GridWorld(BY_ID[wid])
    v = mkv("adv-" + name, wid, ops)
    s = solve(world, v)
    b = _step_budget(v)
    caps = [(b + 1) if b is not None else 0]
    caps += [caps[0] + 3, caps[0] + 8, caps[0] + 16]
    cells = []
    for cap in caps:
        try:
            a, w, n = independent_decide(world, v, cap)
            cells.append("cap%d:%s/%s" % (cap, "S" if a else "U",
                                          "-" if w is None else len(w)))
            if a != s["solvable"] or (w is None) != (s["witness"] is None) or \
               (w is not None and len(w) != len(s["witness"])):
                bad += 1
                cells[-1] += "  <<< DISAGREES"
        except RuntimeError:
            cells.append("cap%d:capped" % cap)
    print("%-27s %-7s %-6s | %s"
          % (name[:27], "S" if s["solvable"] else "U",
             "-" if s["witness"] is None else len(s["witness"]), "  ".join(cells)))
print("-" * 96)
print("%d disagreements over %d cases x 4 caps" % (bad, len(CASES)))

print()
print("A2-B  does OracleTruncated fire before a wrong answer can be returned?")
print("-" * 96)
world = GridWorld(BY_ID["t1-walk-maze"])
for label, ops, true_answer in (
        ("budget 10 (solvable)", [{"op": "step_limit", "limit": 10}], True),
        ("budget 9 (unsolvable)", [{"op": "step_limit", "limit": 9}], False)):
    v = mkv("adv-trunc", "t1-walk-maze", ops)
    full = solve(world, v)
    print("  %s: full search -> solvable=%s in %d nodes"
          % (label, full["solvable"], full["reachable_nodes"]))
    for lim in (1, 5, 20, 60, full["reachable_nodes"] - 1, full["reachable_nodes"]):
        try:
            r = solve(world, v, node_limit=lim)
            tag = "" if r["solvable"] == true_answer else "   <<< WRONG ANSWER RETURNED"
            print("     node_limit=%-6d -> solvable=%s nodes=%d%s"
                  % (lim, r["solvable"], r["reachable_nodes"], tag))
        except OracleTruncated:
            print("     node_limit=%-6d -> OracleTruncated (refused to answer)" % lim)

print()
print("A2-C  is the counter really unread when no step_limit is declared?")
print("-" * 96)
import inspect
src = inspect.getsource(VariantRuntime)
for i, line in enumerate(src.splitlines(), 1):
    if "self.commands" in line:
        print("   %s" % line.strip())
print("   -> the only read is the step_limit comparison; the only writes are the")
print("      RESET zeroing and the pre-step_limit increment.")
