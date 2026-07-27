"""Coverage probes: go and test the clauses the trajectory never exercised.

`probe_frontier` answers *"which action best splits the surviving guards?"*.
That is the right question when several hypotheses survive. It is the wrong
question — indeed it asks nothing at all — about a clause the evidence never
touched, because there is no frontier to split. And a clause the evidence never
touched is exactly where a manual is silently wrong: A0's manual said pushing up
into the Button does nothing, full-history replay agreed, and the claim was
false (`A0_REPORT.md` §2).

So this is the other half of constraint 7 — *"定理未经戳探不得定案"* — implemented
against the manual rather than against the candidate stream:

1. enumerate the manual's own reachable state space;
2. for each rule, collect the (state, action) pairs where **its guard fires**;
3. a rule is **untested** when none of those pairs occurs in the trace. Replay
   can say nothing about it, by construction;
4. for each untested rule, navigate to the nearest firing state **using the
   manual**, write down the manual's predicted successor frame, execute the
   action in the world, and compare;
5. a mismatch is a refutation and goes back to theorize; a match promotes the
   rule from `probe: pending` to `probe: passed`.

Step 4 is the part A0 could not do. A0's latch made the firing states of
`press_*` unreachable once the trajectory had passed through them; A0′'s toggle
makes every firing state reachable again, which is the whole reason the world
was rebuilt.
"""

import importlib.util
import json
import os
import sys
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from prime.world import a0p_world as W  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

ACTION_NAMES = {"UP": ("push", "Cart", "up"), "DOWN": ("push", "Cart", "down"),
                "LEFT": ("push", "Cart", "left"), "RIGHT": ("push", "Cart", "right")}
WORLD_OF = {v[2]: k for k, v in ACTION_NAMES.items()}


def load_theory(path: str):
    spec = importlib.util.spec_from_file_location("a0p_manual", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reachable(theory, limit: int = 5000):
    """The manual's own state space, and how to get to each state."""
    start = theory.initial_state()
    paths = {start.key(): []}
    order = [start]
    queue = deque([start])
    while queue and len(order) < limit:
        state = queue.popleft()
        for action in theory.ACTIONS:
            nxt = theory.step(state, action)
            if nxt.key() in paths:
                continue
            paths[nxt.key()] = paths[state.key()] + [action]
            order.append(nxt)
            queue.append(nxt)
    return order, paths


def firing_sites(theory, states) -> Dict[str, List[Tuple[object, tuple]]]:
    sites: Dict[str, List[Tuple[object, tuple]]] = {}
    for state in states:
        for action in theory.ACTIONS:
            for name in theory.fired(state, action):
                sites.setdefault(name, []).append((state, action))
    return sites


def trace_sites(theory, trace_path: str):
    """(frame, action) pairs the trajectory actually contains."""
    frames, actions, _wins = read_trace(trace_path)
    out = set()
    for t, action in enumerate(actions):
        if action is None:
            continue
        out.add((json.dumps(frames[t]), ACTION_NAMES[action]))
    return out


def navigate(theory, start, target_key, paths):
    """Manual-side path from `start` to the state with `target_key`."""
    prefix = paths.get(start.key())
    suffix = paths.get(target_key)
    if suffix is None:
        return None
    if prefix is not None and suffix[:len(prefix)] == prefix:
        return suffix[len(prefix):]
    # not a prefix: BFS afresh from here
    seen = {start.key()}
    queue = deque([(start, [])])
    while queue:
        state, path = queue.popleft()
        if state.key() == target_key:
            return path
        for action in theory.ACTIONS:
            nxt = theory.step(state, action)
            if nxt.key() in seen:
                continue
            seen.add(nxt.key())
            queue.append((nxt, path + [action]))
    return None


def run(theory_py: str, trace_path: str, spec: W.WorldSpec,
        probes_path: str, max_probes: int = 12) -> Dict[str, object]:
    theory = load_theory(theory_py)
    states, paths = reachable(theory)
    sites = firing_sites(theory, states)
    seen = trace_sites(theory, trace_path)

    untested = []
    for name, _guard, _effect, _obj in theory.RULES:
        pairs = sites.get(name, [])
        if not pairs:
            untested.append((name, None, "the manual's own state space contains "
                                         "no state where this rule fires"))
            continue
        exercised = any((json.dumps(theory.render(s)), a) in seen for s, a in pairs)
        if not exercised:
            untested.append((name, pairs[0], "%d firing states, none in the trace"
                             % len(pairs)))

    world = W.A0PWorld(spec)
    wstate = world.initial()
    mstate = theory.initial_state()
    _frames, actions, _wins = read_trace(trace_path)
    for action in actions:
        if action is None:
            break
        wstate = world.step(wstate, action)
        mstate = theory.step(mstate, ACTION_NAMES[action])

    rows: List[Dict[str, object]] = []
    for name, site, reason in untested[:max_probes]:
        if site is None:
            rows.append({"rule": name, "status": "vacuous", "reason": reason})
            continue
        target, action = site
        path = navigate(theory, mstate, target.key(), paths)
        if path is None:
            rows.append({"rule": name, "status": "unreachable", "reason": reason})
            continue

        drift = None
        for step_action in path:
            mstate = theory.step(mstate, step_action)
            wstate = world.step(wstate, WORLD_OF[step_action[2]])
            if theory.render(mstate) != world.render(wstate):
                drift = step_action
                break
        if drift is not None:
            rows.append({"rule": name, "status": "execution_mismatch",
                         "reason": reason, "at": str(drift)})
            continue

        # --- prediction, written before the action is taken ---------------
        predicted = theory.render(theory.step(mstate, action))
        wstate = world.step(wstate, WORLD_OF[action[2]])
        observed = world.render(wstate)
        mstate = theory.step(mstate, action)

        rows.append({
            "rule": name,
            "reason": reason,
            "navigation_steps": len(path),
            "action": WORLD_OF[action[2]],
            "cart_before": list(target.Cart_pos),
            "predicted_cart": [i for i in _cart_of(predicted)],
            "observed_cart": [i for i in _cart_of(observed)],
            "agreed": predicted == observed,
            "status": "confirmed" if predicted == observed else "refuted",
        })

    with open(probes_path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    return {
        "rules": len(theory.RULES),
        "untested_rules": [name for name, _s, _r in untested],
        "probes_run": len([r for r in rows if r["status"] in
                           ("confirmed", "refuted")]),
        "confirmed": [r["rule"] for r in rows if r["status"] == "confirmed"],
        "refuted": [r["rule"] for r in rows if r["status"] == "refuted"],
        "vacuous": [r["rule"] for r in rows if r["status"] == "vacuous"],
        "unreachable": [r["rule"] for r in rows if r["status"] == "unreachable"],
        "rows": rows,
    }


def _cart_of(frame):
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value == 6:
                return (r, c)
    return (-1, -1)
