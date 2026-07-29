"""Spot-check: are the shipped sokoban dead-region theorems true of the rule
sets, and are they complete w.r.t. the geometry the fixture describes?"""

import sys
sys.dont_write_bytecode = True

import glob
import itertools
import json
import os

RIG = r"C:\Users\user\Desktop\theoria\.worktrees\e5-cert-recheck\engine-rig"
sys.path.insert(0, RIG)
sys.path.insert(0, r"C:\Users\user\Desktop\theoria\engine-rig")
from recheck.ruleset import load_ruleset  # noqa: E402
from recheck.certificate import load_certificate  # noqa: E402
from fixtures import sokoban as fx  # noqa: E402

CASES = os.path.join(RIG, "recheck", "cases")

for level in ("sokoban-ringstuck", "sokoban-open4far"):
    rs = load_ruleset(os.path.join(CASES, "%s.rules.json" % level))
    certs = sorted(glob.glob(os.path.join(CASES, "%s-dead-*.cert.json" % level)))
    print("== %s: %d dead-region certificates" % (level, len(certs)))
    for path in certs:
        cert = load_certificate(path)
        pred = cert.compile(rs)
        states = [s for s in rs.states() if rs.constraint(s)]
        region = [s for s in states if pred(s)]
        leaks = []
        goals = []
        for s in region:
            if rs.goal(s):
                goals.append(s)
            for a in rs.actions:
                n = rs.step(s, a)
                if not pred(n):
                    leaks.append((s, a, n))
        print("   %-46s |region|=%4d leaks=%d goal-in-region=%d"
              % (os.path.basename(path), len(region), len(leaks), len(goals)))

    # completeness against the fixture's own corner geometry
    fixture = fx.by_name(level.replace("sokoban-", ""))
    corners = set(fixture.corners())
    goal_cells = set(fixture.goal_cells())
    covered = set()
    for path in certs:
        spec = json.load(open(path, encoding="utf-8"))
        terms = spec["predicate"][1:]
        if len(terms) == 1:
            box = terms[0][1][1]
            cell = tuple(int(x) for x in terms[0][2][1].split(","))
            covered.add((box, cell))
    want = set((b, c) for b in fixture.box_names() for c in corners if c not in goal_cells)
    print("   corner deadlocks the geometry supports: %d; shipped as theorems: %d"
          % (len(want), len(covered & want)))
    missing = sorted(want - covered)
    if missing:
        print("   NOT SHIPPED:", missing)
    print()
