"""(2) the pagoda table vs Lean `def w`, plus DSL rule-list coverage and
optimal-plan anchors for sokoban."""

import sys
sys.dont_write_bytecode = True

import json
import os
import re
from collections import deque

RIG = r"C:\Users\user\Desktop\theoria\.worktrees\e5-cert-recheck\engine-rig"
A2 = r"C:\Users\user\Desktop\theoria\cold-start-a2\theory"
sys.path.insert(0, RIG)
from recheck.ruleset import load_ruleset  # noqa: E402

CASES = os.path.join(RIG, "recheck", "cases")
LEAN = os.path.join(A2, "generated_holed", "theory.lean")

text = open(LEAN, encoding="utf-8").read()

# --- cell index -> (row, col), from the doc comment on `inductive Cell`
doc = re.search(r"/-- Arena cells.*?-/", text, re.S).group(0)
cell_map = {}
for m in re.finditer(r"c(\d+)\s*=\s*\((\d+),\s*(\d+)\)", doc):
    cell_map[int(m.group(1))] = (int(m.group(2)), int(m.group(3)))
print("cell doc-comment entries:", len(cell_map))

# --- the enum's own constructor order (the doc comment is only a comment)
enum = re.search(r"inductive Cell where(.*?)deriving", text, re.S).group(1)
ctors = re.findall(r"\|\s*c(\d+)", enum)
print("enum constructors:", len(ctors), "in order 0..n:",
      [int(x) for x in ctors] == list(range(len(ctors))))

# --- def w
wsec = re.search(r"def w : Cell → Nat\n(.*?)\n\n", text, re.S).group(1)
weights = {}
for m in re.finditer(r"\|\s*\.c(\d+)\s*=>\s*(\d+)", wsec):
    weights[int(m.group(1))] = int(m.group(2))
print("def w arms:", len(weights))

lean_zero = sorted(cell_map[i] for i, v in weights.items() if v == 0)
lean_one = sorted(cell_map[i] for i, v in weights.items() if v == 1)
other = {i: v for i, v in weights.items() if v not in (0, 1)}
print("lean zero cells: %d, one cells: %d, other: %s" % (len(lean_zero), len(lean_one), other))

# --- the arena order the rig computes, independently of the Lean comment
rs = load_ruleset(os.path.join(CASES, "a2-holed.rules.json"))
arena = [tuple(int(x) for x in n.split(",")) for n in dict(
    (v.name, v.domain) for v in rs.variables)["cart"]]
print("rig arena size:", len(arena),
      "row-major order matches Lean cell index:",
      arena == [cell_map[i] for i in range(len(cell_map))])

# --- the certificate's own table
cert = json.load(open(os.path.join(CASES, "a2-right-room-locked.cert.json"), encoding="utf-8"))
w = cert["tables"]["w"]
print("cert w: default=%r, %d entries, all values %s"
      % (w["default"], len(w["entries"]), sorted(set(e[1] for e in w["entries"]))))
cert_zero = sorted(tuple(int(x) for x in e[0].split(",")) for e in w["entries"] if e[1] == 0)
cert_all = {}
for cell in arena:
    name = "%d,%d" % cell
    hit = [e for e in w["entries"] if e[0] == name]
    cert_all[cell] = hit[0][1] if hit else w["default"]

mismatch = [(cell_map[i], weights[i], cert_all[cell_map[i]])
            for i in sorted(weights) if cert_all[cell_map[i]] != weights[i]]
print("all 37 cells, lean w vs certificate w: %d agree, %d differ"
      % (37 - len(mismatch), len(mismatch)))
for m in mismatch:
    print("   MISMATCH cell=%s lean=%s cert=%s" % m)
print("zero cells identical:", cert_zero == lean_zero, "count:", len(cert_zero))
print("cert zero cells:", cert_zero)
print("goal cell (2,7) weight: lean=%s cert=%s"
      % (weights[[i for i, c in cell_map.items() if c == (2, 7)][0]], cert_all[(2, 7)]))
print("init cell (5,1) weight:", cert_all[(5, 1)])
print("portal_exit (7,6) weight:", cert_all[(7, 6)])

# --- DSL rules section vs JSON rule names
print()
for dsl, case in (("theory.dsl", "a2-world.rules.json"),
                  ("theory_holed.dsl", "a2-holed.rules.json")):
    src = open(os.path.join(A2, dsl), encoding="utf-8").read()
    body = src.split("rules:")[1].split("goal:")[0]
    dsl_rules = re.findall(r"^\s*rule\s+(\w+)", body, re.M)
    spec = json.load(open(os.path.join(CASES, case), encoding="utf-8"))
    json_rules = [r["name"] for r in spec["rules"]]
    print("%-18s dsl=%s" % (dsl, dsl_rules))
    print("%-18s json=%s  same set=%s"
          % ("", sorted(json_rules), sorted(dsl_rules) == sorted(json_rules)))

# --- sokoban optimum anchors
print()
for level, case, optimum in (("ring", "sokoban-ring.rules.json", 1),
                             ("open4", "sokoban-open4.rules.json", 6)):
    r = load_ruleset(os.path.join(CASES, case))
    start = r.init[0]
    dist = {start: 0}
    q = deque([start])
    found = None
    while q:
        s = q.popleft()
        if r.goal(s):
            found = dist[s]
            break
        for a in r.actions:
            n = r.step(s, a)
            if n not in dist:
                dist[n] = dist[s] + 1
                q.append(n)
    print("%s: BFS optimum=%s, fixture says %s, match=%s"
          % (level, found, optimum, found == optimum))
