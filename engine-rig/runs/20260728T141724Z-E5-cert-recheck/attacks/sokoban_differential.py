"""Differential: recheck sokoban rule sets vs the generated PDDL, grounded.

The PDDL domain and problem are parsed generically (s-expressions, typed
objects, STRIPS add/delete lists) and grounded; nothing about sokoban is
hardcoded except the file paths.  The grounded transition system is then
compared to the rule set's derived `step`, both over the whole reachable space
and over every canonical (player, boxes) placement.
"""

import sys
sys.dont_write_bytecode = True

import itertools
import os
from collections import deque

RIG = r"C:\Users\user\Desktop\theoria\.worktrees\e5-cert-recheck\engine-rig"
DATA = r"C:\Users\user\Desktop\theoria\engine-rig\fixtures\data"
sys.path.insert(0, RIG)

from recheck.ruleset import load_ruleset  # noqa: E402

CASES = os.path.join(RIG, "recheck", "cases")


# --------------------------------------------------------------- s-expressions

def tokenize(text):
    out = []
    for line in text.splitlines():
        line = line.split(";;")[0] if line.strip().startswith(";;") else line
        if line.strip().startswith(";"):
            continue
        out.append(line)
    text = "\n".join(out).replace("(", " ( ").replace(")", " ) ")
    return text.split()


def parse_sexp(tokens):
    tok = tokens.pop(0)
    if tok == "(":
        lst = []
        while tokens[0] != ")":
            lst.append(parse_sexp(tokens))
        tokens.pop(0)
        return lst
    return tok


def read_sexp(path):
    with open(path, "r", encoding="utf-8") as fh:
        return parse_sexp(tokenize(fh.read()))


def find(sections, key):
    for s in sections:
        if isinstance(s, list) and s and s[0] == key:
            return s
    return None


# -------------------------------------------------------------- domain/problem

def parse_typed_list(items):
    """['a','b','-','t','c','-','u'] -> {'a':'t','b':'t','c':'u'}"""
    out = {}
    pending = []
    i = 0
    while i < len(items):
        if items[i] == "-":
            for p in pending:
                out[p] = items[i + 1]
            pending = []
            i += 2
        else:
            pending.append(items[i])
            i += 1
    for p in pending:
        out[p] = "object"
    return out


def flatten_and(node):
    if node[0] == "and":
        return [tuple(x) for x in node[1:]]
    return [tuple(node)]


def split_effect(node):
    adds, dels = [], []
    parts = node[1:] if node[0] == "and" else [node]
    for p in parts:
        if p[0] == "not":
            dels.append(tuple(p[1]))
        else:
            adds.append(tuple(p))
    return adds, dels


def parse_domain(path):
    d = read_sexp(path)
    actions = []
    for s in d:
        if isinstance(s, list) and s and s[0] == ":action":
            name = s[1]
            rest = s[2:]
            params = parse_typed_list(rest[rest.index(":parameters") + 1])
            porder = [p for p in rest[rest.index(":parameters") + 1] if p.startswith("?")]
            pre = flatten_and(rest[rest.index(":precondition") + 1])
            adds, dels = split_effect(rest[rest.index(":effect") + 1])
            actions.append({"name": name, "params": porder, "types": params,
                            "pre": pre, "add": adds, "del": dels})
    return actions


def parse_problem(path):
    p = read_sexp(path)
    objects = parse_typed_list(find(p, ":objects")[1:])
    init = set(tuple(f) for f in find(p, ":init")[1:])
    goal = set(tuple(f) for f in flatten_and(find(p, ":goal")[1]))
    return objects, init, goal


def ground(actions, objects, init):
    """Every grounded instance whose static preconditions hold in init."""
    by_type = {}
    for o, t in objects.items():
        by_type.setdefault(t, []).append(o)
    static = {"adj"}
    out = []
    for a in actions:
        choices = [sorted(by_type[a["types"][p]]) for p in a["params"]]
        for combo in itertools.product(*choices):
            sub = dict(zip(a["params"], combo))
            def g(f):
                return tuple(sub.get(x, x) for x in f)
            pre = [g(f) for f in a["pre"]]
            if any(f[0] in static and f not in init for f in pre):
                continue
            out.append({
                "name": "%s(%s)" % (a["name"], ",".join(combo)),
                "schema": a["name"],
                "args": sub,
                "pre": frozenset(f for f in pre if f[0] not in static),
                "add": frozenset(g(f) for f in a["add"]),
                "del": frozenset(g(f) for f in a["del"]),
            })
    return out


def apply_action(state, op):
    return frozenset((state - op["del"]) | op["add"])


# ------------------------------------------------------------------- mapping

def rs_cell_to_pddl(name):
    r, c = name.split(",")
    return "c%s%s" % (r, c)


def rs_state_to_pddl(rs, state, cells):
    """The canonical PDDL state for a (player, boxes...) assignment."""
    facts = set()
    occupied = set()
    for i, v in enumerate(rs.variables):
        cell = rs_cell_to_pddl(state[i])
        occupied.add(cell)
        if v.name == "player":
            facts.add(("at-player", cell))
        else:
            facts.add(("at", v.name, cell))
    for c in cells:
        if c not in occupied:
            facts.add(("clear", c))
    return frozenset(facts)


def pddl_to_rs_state(rs, facts):
    vals = {}
    for f in facts:
        if f[0] == "at-player":
            vals["player"] = f[1]
        elif f[0] == "at":
            vals[f[1]] = f[2]
    return tuple("%s,%s" % (vals[v.name][1], vals[v.name][2]) for v in rs.variables)


# --------------------------------------------------------------------- compare

def compare(level, rs_file):
    print("== %s" % level)
    rs = load_ruleset(os.path.join(CASES, rs_file))
    domain = parse_domain(os.path.join(DATA, "sokoban_domain.pddl"))
    objects, init, goal = parse_problem(os.path.join(DATA, "sokoban_%s.pddl" % level))
    cells = sorted(o for o, t in objects.items() if t == "cell")
    ops = ground(domain, objects, init)

    problems = []

    # --- static data: cells, init, goal
    rs_cells = sorted(rs_cell_to_pddl(n) for n in rs.variables[0].domain)
    if rs_cells != cells:
        problems.append("cell sets differ: rules=%s pddl=%s" % (rs_cells, cells))
    print("   cells: %d, identical=%s" % (len(cells), rs_cells == cells))

    # `adj` is static; it lives in the rule set's `nb` table, compared separately.
    fluent_init = frozenset(f for f in init if f[0] != "adj")
    pddl_adj = set(f for f in init if f[0] == "adj")
    nb = rs.tables["nb"]
    rs_adj = set(("adj", rs_cell_to_pddl("%s" % k[0]), rs_cell_to_pddl(v), k[1])
                 for k, v in nb.entries.items())
    if rs_adj != pddl_adj:
        problems.append("adj/nb differ: only-rules=%s only-pddl=%s"
                        % (sorted(rs_adj - pddl_adj), sorted(pddl_adj - rs_adj)))
    print("   adj facts: pddl=%d nb entries=%d identical=%s"
          % (len(pddl_adj), len(rs_adj), rs_adj == pddl_adj))

    rs_init_pddl = rs_state_to_pddl(rs, rs.init[0], cells)
    if rs_init_pddl != fluent_init:
        problems.append("init differs: only-in-rules=%s only-in-pddl=%s"
                        % (sorted(rs_init_pddl - fluent_init),
                           sorted(fluent_init - rs_init_pddl)))
    print("   init identical (incl. every `clear`): %s" % (rs_init_pddl == fluent_init))

    rs_goal_facts = set()
    for term in rs.goal_src[1:]:
        rs_goal_facts.add(("at", term[1][1], rs_cell_to_pddl(term[2][1])))
    if rs_goal_facts != goal:
        problems.append("goal differs: rules=%s pddl=%s" % (sorted(rs_goal_facts), sorted(goal)))
    print("   goal identical: %s (%s)" % (rs_goal_facts == goal, sorted(goal)))

    # --- every canonical placement, not just the reachable ones
    var_names = [v.name for v in rs.variables]
    n_checked = 0
    agree = 0
    mism = []
    for combo in itertools.permutations(cells, len(var_names)):
        state = tuple("%s,%s" % (c[1], c[2]) for c in combo)
        if not rs.constraint(state):
            continue
        pstate = rs_state_to_pddl(rs, state, cells)
        # what PDDL allows here, keyed by (schema, direction)
        pddl_succ = {}
        for op in ops:
            if op["pre"] <= pstate:
                key = (op["schema"], op["args"]["?d"])
                nxt = apply_action(pstate, op)
                if key in pddl_succ and pddl_succ[key] != nxt:
                    problems.append("PDDL non-determinism at %s %s" % (state, key))
                pddl_succ[key] = nxt
        for a in rs.actions:
            n_checked += 1
            schema, direction = a.split("-")
            nxt_rs = rs.step(state, a)
            moved = nxt_rs != state
            key = (schema, direction)
            allowed = key in pddl_succ
            if not allowed:
                # PDDL: inapplicable.  rule set must be a self-loop.
                if moved:
                    mism.append(("PDDL-FORBIDS-RULES-ALLOWS", state, a, nxt_rs))
                else:
                    agree += 1
                continue
            expect = pddl_to_rs_state(rs, pddl_succ[key])
            # the PDDL `clear` set must stay canonical too
            canon = rs_state_to_pddl(rs, expect, cells)
            if canon != pddl_succ[key]:
                problems.append("PDDL successor not canonical at %s %s: %s"
                                % (state, a, sorted(pddl_succ[key] ^ canon)))
            if not moved and expect != state:
                mism.append(("RULES-FORBID-PDDL-ALLOWS", state, a, expect))
            elif nxt_rs != expect:
                mism.append(("DIFFERENT-SUCCESSOR", state, a, nxt_rs, expect))
            else:
                agree += 1
    print("   canonical placements x actions: %d checked, %d agree, %d disagree"
          % (n_checked, agree, len(mism)))
    for m in mism[:10]:
        print("      ", m)

    # --- reachable-space comparison, from init, both sides
    seen = {fluent_init}
    q = deque([fluent_init])
    while q:
        s = q.popleft()
        for op in ops:
            if op["pre"] <= s:
                n = apply_action(s, op)
                if n not in seen:
                    seen.add(n)
                    q.append(n)
    pddl_reach = set(pddl_to_rs_state(rs, s) for s in seen)

    rs_seen = {rs.init[0]}
    q = deque([rs.init[0]])
    while q:
        s = q.popleft()
        for a in rs.actions:
            n = rs.step(s, a)
            if n not in rs_seen:
                rs_seen.add(n)
                q.append(n)
    print("   reachable: pddl=%d (as placements %d), rules=%d, identical=%s"
          % (len(seen), len(pddl_reach), len(rs_seen), pddl_reach == rs_seen))
    if pddl_reach != rs_seen:
        problems.append("reachable sets differ: only-pddl=%s only-rules=%s"
                        % (sorted(pddl_reach - rs_seen)[:5], sorted(rs_seen - pddl_reach)[:5]))

    # --- solvability
    rs_solvable = any(rs.goal(s) for s in rs_seen)
    pddl_solvable = any(goal <= s for s in seen)
    print("   solvable: pddl=%s rules=%s" % (pddl_solvable, rs_solvable))
    if rs_solvable != pddl_solvable:
        problems.append("solvability differs")

    ob = rs.obligations()
    print("   obligations:", dict(sorted(ob.conditions.items())))
    for k, v in ob.witnesses.items():
        print("      ", k, v[:3])
    for p in problems:
        print("   PROBLEM:", p)
    print()
    return len(mism) + len(problems)


bad = 0
for level, f in (("ringstuck", "sokoban-ringstuck.rules.json"),
                 ("open4far", "sokoban-open4far.rules.json"),
                 ("ring", "sokoban-ring.rules.json"),
                 ("open4", "sokoban-open4.rules.json")):
    bad += compare(level, f)
print("TOTAL SOKOBAN DISCREPANCIES:", bad)
