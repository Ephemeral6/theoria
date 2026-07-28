"""Differential fuzzer: recheck() vs an independent ground truth.

Ground truth is re-implemented here from the DSL contract prose (frame persist,
conflict exclusive, cascade single_frame) over the FULL product of the declared
domains -- the constraint plays no part in it.  If recheck() ACCEPTs while the
ground truth says a goal is reachable from init (inductive_invariant) or from a
state satisfying the predicate (dead_region), that is a soundness break.

Run:  python runs/20260728T141724Z-E5-cert-recheck/attacks/fuzz_ruleset.py
"""

import itertools
import json
import os
import random
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", ".."))

from recheck.certificate import CertificateError, certificate_from_spec
from recheck.ruleset import RuleSetError, ruleset_from_spec
from recheck.verify import recheck

RS = "engine-rig/recheck/ruleset-v1"
CS = "engine-rig/recheck/certificate-v1"


# ----------------------------------------------------- independent evaluator

def ev(node, state, action):
    op, args = node[0], node[1:]
    if op == "lit":
        return args[0]
    if op == "var":
        return state[args[0]]
    if op == "act":
        return action
    if op == "=":
        return ev(args[0], state, action) == ev(args[1], state, action)
    if op == "!=":
        return ev(args[0], state, action) != ev(args[1], state, action)
    if op == "and":
        return all(ev(a, state, action) for a in args)
    if op == "or":
        return any(ev(a, state, action) for a in args)
    if op == "not":
        return not ev(args[0], state, action)
    if op == "in":
        return ev(args[0], state, action) in list(args[1])
    if op == "if":
        return ev(args[1] if ev(args[0], state, action) else args[2], state, action)
    raise AssertionError(op)


class Truth:
    """The transition system, computed without looking at recheck's code."""

    def __init__(self, spec):
        self.names = [v["name"] for v in spec["variables"]]
        self.doms = [list(v["domain"]) for v in spec["variables"]]
        self.actions = list(spec["actions"])
        self.rules = spec["rules"]
        self.spec = spec
        self.states = [dict(zip(self.names, combo))
                       for combo in itertools.product(*self.doms)]
        self.key = [tuple(s[n] for n in self.names) for s in self.states]
        self.index = {k: i for i, k in enumerate(self.key)}

    def step(self, state, action):
        out = dict(state)
        for rule in self.rules:
            g = rule["guard"]
            if rule.get("action") is not None:
                if action != rule["action"]:
                    continue
            if not ev(g, state, action):
                continue
            for target, e in rule["effects"].items():
                out[target] = ev(e, state, action)
        return out

    def succ(self, i, a):
        nxt = self.step(self.states[i], self.actions[a])
        return self.index.get(tuple(nxt[n] for n in self.names), -1)

    def goal(self, i):
        return bool(ev(self.spec["goal"], self.states[i], None))

    def init_indices(self):
        raw = self.spec["init"]
        raw = [raw] if isinstance(raw, dict) else raw
        return [self.index[tuple(e[n] for n in self.names)] for e in raw]

    def reaches_goal(self, sources):
        seen = set(sources)
        q = deque(sources)
        for i in sources:
            if self.goal(i):
                return True
        while q:
            i = q.popleft()
            for a in range(len(self.actions)):
                j = self.succ(i, a)
                if j < 0 or j in seen:
                    continue
                seen.add(j)
                if self.goal(j):
                    return True
                q.append(j)
        return False


# ------------------------------------------------------------------ generator

def rand_expr(rng, names, doms, depth, allow_act, actions):
    if depth <= 0 or rng.random() < 0.4:
        which = rng.randrange(3 if allow_act else 2)
        if which == 0:
            v = rng.randrange(len(names))
            return ["=", ["var", names[v]], ["lit", rng.choice(doms[v])]]
        if which == 1:
            a = rng.randrange(len(names))
            b = rng.randrange(len(names))
            return [rng.choice(["=", "!="]), ["var", names[a]], ["var", names[b]]]
        return ["=", ["act"], ["lit", rng.choice(actions)]]
    op = rng.choice(["and", "or", "not"])
    if op == "not":
        return ["not", rand_expr(rng, names, doms, depth - 1, allow_act, actions)]
    n = rng.randrange(0, 3)
    return [op] + [rand_expr(rng, names, doms, depth - 1, allow_act, actions)
                   for _ in range(n)]


def rand_effect(rng, names, doms, vi):
    r = rng.random()
    if r < 0.5:
        return ["lit", rng.choice(doms[vi])]
    if r < 0.8:
        other = rng.randrange(len(names))
        if set(doms[other]) <= set(doms[vi]):
            return ["var", names[other]]
        return ["lit", rng.choice(doms[vi])]
    return ["if", rand_expr(rng, names, doms, 1, True, ["a"]),
            ["lit", rng.choice(doms[vi])], ["lit", rng.choice(doms[vi])]]


def gen(rng):
    nvar = rng.randrange(2, 4)
    names = ["v%d" % i for i in range(nvar)]
    doms = [[rng.choice(["x", "y", "z", 0, 1, 2]) for _ in range(rng.randrange(2, 4))]
            for _ in range(nvar)]
    doms = [sorted(set(d), key=repr) for d in doms]
    for d in doms:
        if len(d) < 2:
            d.append("pad")
    actions = ["a%d" % i for i in range(rng.randrange(1, 3))]

    rules = []
    for i in range(rng.randrange(1, 4)):
        vi = rng.randrange(nvar)
        rules.append({
            "name": "r%d" % i,
            "action": rng.choice(actions + [None]),
            "guard": rand_expr(rng, names, doms, 2, True, actions),
            "effects": {names[vi]: rand_effect(rng, names, doms, vi)},
        })

    spec = {
        "schema": RS,
        "name": "fuzz",
        "variables": [{"name": n, "domain": d} for n, d in zip(names, doms)],
        "actions": actions,
        "init": [{n: rng.choice(d) for n, d in zip(names, doms)}
                 for _ in range(rng.randrange(1, 3))],
        "goal": rand_expr(rng, names, doms, 2, False, actions),
        "rules": rules,
    }
    # dedupe init
    seen, keep = set(), []
    for e in spec["init"]:
        k = tuple(sorted(e.items()), )
        if k not in seen:
            seen.add(k)
            keep.append(e)
    spec["init"] = keep
    if rng.random() < 0.75:
        spec["constraint"] = rand_expr(rng, names, doms, 2, False, actions)

    kind = rng.choice(["inductive_invariant", "dead_region"])
    cert = {
        "schema": CS,
        "name": "fuzz-cert",
        "kind": kind,
        "claim": ("unsolvable" if kind == "inductive_invariant"
                  else "conditional_unsolvability"),
        "predicate": rand_expr(rng, names, doms, 2, False, actions),
    }
    return spec, cert


def main(n=20000, seed=20260728):
    rng = random.Random(seed)
    breaks = []
    stats = {"accept": 0, "reject": 0, "inconsistent": 0, "loaderr": 0, "crash": 0}
    for trial in range(n):
        spec, cert = gen(rng)
        try:
            rs = ruleset_from_spec(spec)
            ct = certificate_from_spec(cert)
        except (RuleSetError, CertificateError):
            stats["loaderr"] += 1
            continue
        try:
            v = recheck(rs, ct)
        except Exception as exc:                      # noqa: BLE001
            stats["crash"] += 1
            breaks.append({"trial": trial, "how": "CRASH: %r" % (exc,),
                           "ruleset": spec, "certificate": cert})
            continue
        stats[{"ACCEPT": "accept", "REJECT": "reject",
               "INCONSISTENT": "inconsistent"}[v.verdict]] += 1
        if v.verdict != "ACCEPT":
            continue
        t = Truth(spec)
        if cert["kind"] == "inductive_invariant":
            sources = t.init_indices()
            label = "goal reachable from init"
        else:
            sources = [i for i in range(len(t.states))
                       if ev(cert["predicate"], t.states[i], None)]
            label = "goal reachable from a predicate-satisfying state"
        if not sources:
            continue
        if t.reaches_goal(sources):
            breaks.append({"trial": trial, "how": label,
                           "ruleset": spec, "certificate": cert,
                           "has_constraint": "constraint" in spec})
    print(json.dumps({"stats": stats, "n_breaks": len(breaks),
                      "breaks": breaks[:6]}, indent=2, default=str))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20000)
