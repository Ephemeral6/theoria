"""E18: recompute the deadlock / planner numbers the E11 cross-check published as prose.

E11's `partials/deadlock-via-reachability.md` adjudicated 50 machine-readable
deadlock and unsolvability claims by exhaustive reachability and reported **50
CONFIRMED, 0 refuted**.  It shipped nine Markdown files and a `MANIFEST.json` --
no script, no data.  Its own closing line says the adjudicating code
(`indep_ground.py`, `adjudicate.py`, `adj2.py`, `adj_a2.py` and three inline
drivers) was "written this session in the session scratchpad, **not committed**".
So the strongest published claim in the deadlock lane rested on a file that no
longer exists, and `ENGINE_TABLE.md` probed it with a regex against the prose.

This module is the executable form.  It re-derives every one of the eleven
registry numbers in the `dl.*` / `fd.open4far_*` / `ic3.*` families from the
fixtures, certificates and world specs on disk, and adjudicates all 50 claims
again.

**Three encodings, actually run.**  `CROSSCHECK.md:39` claims three encodings
agree bit-for-bit on `sokoban-open4far` (112 ground actions, 3352 reachable
states, optimal 11).  An agreement claim is not confirmed by one derivation, so
three are computed here:

* `own_strips`  -- a fresh s-expression reader, STRIPS grounder with static
  filtering, forward BFS over atom sets, backward alive-closure.  Nothing from
  `engines/` runs on this path.
* `positional`  -- the C4 Lean shape: a state is `(player, b1, b2)` over cells,
  `clear` is *derived* from occupancy rather than stored as an atom, and the
  action instances are re-derived from the `adj` relation and the two schemas by
  hand.  This is the encoding whose numbers `theory-compiler/runs/
  20260728T080019Z-C4-deadlock-lean/verify/EVIDENCE.json` records.
* `engine`      -- the defendant's own: `engines.fd_adapter.pddl.ground_actions`
  + `strip_static` + `engines.fd_adapter.search.search`.  Included precisely
  because E11 excluded it: E11 proved its own grounder agrees with C4's Lean, and
  left "does the engine's grounder agree with either" to inference.

plus a fourth leg that is **read, not re-run**: C4's `verify/EVIDENCE.json`.  No
Lean toolchain is invoked here.

Run:

    cd engine-rig
    python -m tools.survey_numbers.deadlock_reach
    python -m tools.survey_numbers.deadlock_reach \
        --jsonl runs/20260730T120000Z-E18/raw/deadlock_reach.jsonl

Takes about 20 s, nearly all of it the three sokoban sweeps.  The committed
counts are `runs/20260730T120000Z-E18/counts/dl.claims_n.json`, written by
`tools.survey_numbers.run_all`.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
from collections import deque
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from tools.survey_numbers import _common

_common.add_repo_root()

ROOT = _common.repo_root()
RIG = ROOT / "engine-rig"

E11_PARTIAL = ("engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/"
               "partials/deadlock-via-reachability.md")
C4_EVIDENCE = ("theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/"
               "verify/EVIDENCE.json")

SOKOBAN = ("open4", "open4far", "ring", "ringstuck")
DIRS4 = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
WORLDGEN = ("t2-unsolvable-nodoor", "v-707a64ad", "v-d2c2b1b9", "v-ce732813")


# ======================================================================== PDDL
# A fresh reader.  `engines.fd_adapter.pddl` is imported later, but only to make
# the `engine` encoding a third *independent implementation* of the same
# grounding -- never as the source of a number this module reports as its own.

_COMMENT = re.compile(r";[^\n]*")


def parse_sexp(text: str) -> Any:
    toks = _COMMENT.sub("", text).replace("(", " ( ").replace(")", " ) ").split()
    pos = 0

    def read() -> Any:
        nonlocal pos
        tok = toks[pos]
        pos += 1
        if tok == "(":
            out = []
            while toks[pos] != ")":
                out.append(read())
            pos += 1
            return out
        return tok.lower()

    return read()


def _read_pddl(rel: str) -> Any:
    return parse_sexp((ROOT / rel).read_text(encoding="utf-8"))


def typed_list(items: Sequence[str]) -> List[Tuple[str, Optional[str]]]:
    """`['?a', '?b', '-', 'cell']` -> `[('?a','cell'), ('?b','cell')]`."""
    out: List[Tuple[str, Optional[str]]] = []
    buf: List[str] = []
    i = 0
    while i < len(items):
        if items[i] == "-":
            out += [(n, items[i + 1]) for n in buf]
            buf = []
            i += 2
        else:
            buf.append(items[i])
            i += 1
    return out + [(n, None) for n in buf]


def conj(formula: Any) -> List[Any]:
    return list(formula[1:]) if formula and formula[0] == "and" else [formula]


def domain_schemas(dom: Any) -> List[Tuple[str, List[Tuple[str, Optional[str]]], Any, Any]]:
    out = []
    for item in dom[2:]:
        if isinstance(item, list) and item and item[0] == ":action":
            body = {item[i]: item[i + 1] for i in range(2, len(item), 2)}
            out.append((item[1], typed_list(body[":parameters"]),
                        body[":precondition"], body[":effect"]))
    return sorted(out)


def static_predicates(dom: Any) -> FrozenSet[str]:
    """A predicate no action schema writes.  Re-derived, not declared."""
    declared = set()
    written = set()
    for item in dom[2:]:
        if isinstance(item, list) and item and item[0] == ":predicates":
            declared |= {p[0] for p in item[1:]}
        if isinstance(item, list) and item and item[0] == ":action":
            body = {item[i]: item[i + 1] for i in range(2, len(item), 2)}
            for lit in conj(body[":effect"]):
                written.add(lit[1][0] if lit[0] == "not" else lit[0])
    return frozenset(declared - written)


def problem_parts(prob: Any) -> Tuple[List[Tuple[str, Optional[str]]], List[tuple], List[tuple]]:
    parts: Dict[str, Any] = {}
    for item in prob[2:]:
        if isinstance(item, list) and item and item[0] in (":objects", ":init", ":goal"):
            parts[item[0]] = item[1:]
    objects = typed_list(parts[":objects"])
    init = [tuple(a) for a in parts[":init"]]
    goal = [tuple(a) for a in conj(parts[":goal"][0])]
    return objects, init, goal


Atom = Tuple[str, ...]
State = FrozenSet[Atom]
Action = Tuple[str, FrozenSet[Atom], FrozenSet[Atom], FrozenSet[Atom]]


def ground(dom: Any, prob: Any) -> Tuple[List[Action], State, List[Atom]]:
    """Ground every schema, drop instances with a false static precondition.

    Static atoms are then stripped from states entirely -- they hold everywhere,
    so carrying them only inflates the state representation.
    """
    objects, init, goal = problem_parts(prob)
    by_type: Dict[Optional[str], List[str]] = {}
    for name, typ in objects:
        by_type.setdefault(typ, []).append(name)
    static = static_predicates(dom)
    init_set = set(init)

    actions: List[Action] = []
    for name, params, pre, eff in domain_schemas(dom):
        vars_ = [p for p, _ in params]
        domains = [sorted(by_type[t]) for _, t in params]
        pre_lits, eff_lits = conj(pre), conj(eff)
        for combo in itertools.product(*domains):
            sub = dict(zip(vars_, combo))

            def bind(atom: Any) -> Atom:
                return tuple(sub.get(x, x) for x in atom)

            positive: List[Atom] = []
            ok = True
            for lit in pre_lits:
                atom = bind(lit)
                if atom[0] in static:
                    if atom not in init_set:
                        ok = False
                        break
                else:
                    positive.append(atom)
            if not ok:
                continue
            add = [bind(e) for e in eff_lits if e[0] != "not"]
            dele = [bind(e[1]) for e in eff_lits if e[0] == "not"]
            actions.append((
                "(%s %s)" % (name, " ".join(combo)),
                frozenset(a for a in positive if a[0] not in static),
                frozenset(a for a in add if a[0] not in static),
                frozenset(a for a in dele if a[0] not in static),
            ))
    start = frozenset(a for a in init if a[0] not in static)
    goal_atoms = [g for g in goal if g[0] not in static]
    return sorted(actions), start, sorted(goal_atoms)


# ================================================== exhaustive reachability
# Forward BFS, then a backward closure from the goal states over the reachable
# subgraph.  A state is alive if some goal state is reachable from it.  Nothing
# here has a budget, so every "unreachable" below is a proof and not a timeout.

class Reach:
    __slots__ = ("states", "succ", "edges", "goals", "alive", "optimal", "start")

    def __init__(self, start, succ_fn, is_goal):
        self.start = start
        seen = {start}
        order = [start]
        queue = deque([start])
        succ: Dict[Any, List[Any]] = {}
        edges = 0
        while queue:
            state = queue.popleft()
            outs = succ_fn(state)
            succ[state] = outs
            edges += len(outs)
            for nxt in outs:
                if nxt not in seen:
                    seen.add(nxt)
                    order.append(nxt)
                    queue.append(nxt)
        self.states = order
        self.succ = succ
        self.edges = edges
        self.goals = [s for s in order if is_goal(s)]

        pred: Dict[Any, set] = {}
        for state, outs in succ.items():
            for nxt in outs:
                pred.setdefault(nxt, set()).add(state)
        alive = set(self.goals)
        queue = deque(self.goals)
        while queue:
            state = queue.popleft()
            for prev in pred.get(state, ()):
                if prev not in alive:
                    alive.add(prev)
                    queue.append(prev)
        self.alive = alive

        self.optimal: Optional[int] = None
        if is_goal(start):
            self.optimal = 0
        else:
            dist = {start: 0}
            queue = deque([start])
            while queue and self.optimal is None:
                state = queue.popleft()
                for nxt in succ[state]:
                    if nxt in dist:
                        continue
                    dist[nxt] = dist[state] + 1
                    if is_goal(nxt):
                        self.optimal = dist[nxt]
                        break
                    queue.append(nxt)

    @property
    def dead(self) -> int:
        return len(self.states) - len(self.alive)

    def summary(self) -> Dict[str, Any]:
        return {
            "ground_actions": None,
            "reachable_states": len(self.states),
            "edges": self.edges,
            "goal_states_reachable": len(self.goals),
            "alive": len(self.alive),
            "dead": self.dead,
            "solvable": bool(self.goals),
            "optimal_plan": self.optimal,
        }


# ---------------------------------------------------------- encoding 1: STRIPS

def strips_reach(dom: Any, prob: Any) -> Tuple[Reach, List[Action], List[Atom]]:
    actions, start, goal = ground(dom, prob)
    goalset = frozenset(goal)

    def succ(state: State) -> List[State]:
        out = []
        for _name, pre, add, dele in actions:
            if pre <= state:
                out.append((state - dele) | add)
        return out

    return Reach(start, succ, lambda s: goalset <= s), actions, goal


# ------------------------------------------------------ encoding 2: positional
# One cell per moving thing; `clear` derived.  Transitions re-derived from the
# `adj` relation and the two schemas as written in the domain file, not from the
# grounded STRIPS actions -- otherwise this would be encoding 1 wearing a hat.

def positional_reach(prob: Any) -> Tuple[Reach, int, int, int]:
    objects, init, goal = problem_parts(prob)
    by_type: Dict[Optional[str], List[str]] = {}
    for name, typ in objects:
        by_type.setdefault(typ, []).append(name)
    cells = sorted(by_type["cell"])
    boxes = sorted(by_type["box"])
    dirs = sorted(by_type["dir"])

    nb = {(a[1], a[3]): a[2] for a in init if a[0] == "adj"}
    start_player = next(a[1] for a in init if a[0] == "at-player")
    start_boxes = tuple(next(a[2] for a in init if a[0] == "at" and a[1] == b) for b in boxes)
    goal_boxes = {g[1]: g[2] for g in goal if g[0] == "at"}

    moves = sorted((f, nb[(f, d)]) for f in cells for d in dirs if (f, d) in nb)
    pushes = sorted(
        (p, nb[(p, d)], nb[(nb[(p, d)], d)], b)
        for p in cells for d in dirs if (p, d) in nb
        for b in boxes if (nb[(p, d)], d) in nb
    )
    n_actions = len(moves) + len(pushes)
    index = {b: i for i, b in enumerate(boxes)}

    def succ(state):
        player, occupied = state[0], state[1:]
        occ = set(occupied)
        out = []
        for src, dst in moves:                       # clear(dst): no box there
            if player == src and dst not in occ:
                out.append((dst,) + occupied)
        for pusher, src, dst, box in pushes:
            i = index[box]
            if player != pusher or occupied[i] != src:
                continue
            if dst in occ or dst == player:          # clear(dst): derived
                continue
            nxt = list(occupied)
            nxt[i] = dst
            out.append((src,) + tuple(nxt))
        return out

    def is_goal(state):
        return all(state[1 + index[b]] == c for b, c in goal_boxes.items())

    reach = Reach((start_player,) + start_boxes, succ, is_goal)
    n = len(cells)
    well_formed = 1
    for k in range(1 + len(boxes)):
        well_formed *= n - k
    return reach, n_actions, well_formed, n ** (1 + len(boxes))


# --------------------------------------------------------- encoding 3: engine

def engine_reach(dom_text: str, prob_text: str):
    """The defendant's own grounder and its own BFS."""
    from engines.fd_adapter import pddl as epddl        # noqa: E402
    from engines.fd_adapter import search as esearch    # noqa: E402

    dom = epddl.parse_domain(dom_text)
    prob = epddl.parse_problem(prob_text)
    grounded = epddl.ground_actions(dom, prob)
    actions, start, _ok = esearch.strip_static(dom, prob, grounded)
    static = epddl.static_predicates(dom)

    def succ(state):
        return [esearch.successor(a, state) for a in actions if esearch.applicable(a, state)]

    reach = Reach(start, succ, lambda s: esearch.is_goal(prob, s, static))
    result = esearch.search(dom, prob)
    return reach, len(actions), result


# ============================================================ claim harvesting

def atom_text(atom: Sequence[str]) -> str:
    return "%s(%s)" % (atom[0], ",".join(atom[1:])) if len(atom) > 1 else atom[0]


def pattern_text(pattern: Sequence[Sequence[str]]) -> str:
    return " AND ".join(atom_text(a) for a in pattern)


def harvest_theorems() -> Dict[str, List[Tuple[Atom, ...]]]:
    """The defendant stating its own case: `deadlock_carver.carve` per instance.

    Harvest only.  Nothing from `carve` touches an adjudicating path -- if it
    under-reports its own theorems the effect is that fewer claims get judged,
    which is why the harvested count is itself one of the reported numbers.
    """
    from engines import deadlock_carver as dc              # noqa: E402
    from engines.fd_adapter import pddl as epddl           # noqa: E402

    dom = epddl.parse_domain(
        (RIG / "fixtures/data/sokoban_domain.pddl").read_text(encoding="utf-8"))
    out: Dict[str, List[Tuple[Atom, ...]]] = {}
    for inst in SOKOBAN:
        prob = epddl.parse_problem(
            (RIG / ("fixtures/data/sokoban_%s.pddl" % inst)).read_text(encoding="utf-8"))
        task = dc.Task.build(dom, prob)
        out[inst] = [tuple(sorted(tuple(a) for a in t.pattern)) for t in dc.carve(task)]
        out[inst].sort(key=lambda p: (len(p), pattern_text(p)))
    return out


def decode_cert_pattern(node: Any) -> List[Atom]:
    """`["=", ["var","b1"], ["lit","1,1"]]` -> `("at","b1","c11")`."""
    if node[0] == "and":
        out: List[Atom] = []
        for child in node[1:]:
            out += decode_cert_pattern(child)
        return out
    if node[0] == "=" and node[1][0] == "var" and node[2][0] == "lit":
        row, col = str(node[2][1]).split(",")
        return [("at", node[1][1], "c%s%s" % (row, col))]
    raise ValueError("unrecognised certificate predicate node: %r" % (node,))


def harvest_certificates() -> Dict[Tuple[str, Tuple[Atom, ...]], str]:
    """Every `dead_region` certificate on disk, keyed by (instance, pattern)."""
    out = {}
    for path in sorted((RIG / "recheck/cases").glob("*.cert.json")):
        cert = json.loads(path.read_text(encoding="utf-8"))
        if cert.get("kind") != "dead_region":
            continue
        instance = cert["ruleset"]["name"].replace("sokoban-", "")
        pattern = tuple(sorted(decode_cert_pattern(cert["predicate"])))
        out[(instance, pattern)] = path.name
    return out


# =========================================================== peg solitaire
# The jump rule re-implemented from `fixtures/peg4.py`'s docstring prose:
# "a move takes a peg at i, jumps it over a peg at i+-1 into an empty hole at
# i+-2, and removes the jumped peg".  `peg4.successors` is never called.

def peg_successors(state: str) -> List[str]:
    n = len(state)
    out = []
    for i in range(n):
        for step in (1, -1):
            over, dst = i + step, i + 2 * step
            if not 0 <= dst < n:
                continue
            if state[i] == "1" and state[over] == "1" and state[dst] == "0":
                cells = list(state)
                cells[i] = cells[over] = "0"
                cells[dst] = "1"
                out.append("".join(cells))
    return sorted(out)


def peg_reach(start: str) -> Dict[str, int]:
    dist = {start: 0}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for nxt in peg_successors(state):
            if nxt not in dist:
                dist[nxt] = dist[state] + 1
                queue.append(nxt)
    return dist


def peg_states(n: int) -> List[str]:
    return ["".join(bits) for bits in itertools.product("01", repeat=n)]


# ================================================= the little rule-set language
# `and`/`or`/`not`/`=`/`!=`/`if`/`lit`/`var`/`param`/`table`/`call`, re-implemented.
# `engine-rig/recheck/expr.py` is deliberately NOT imported: `recheck`'s verdicts
# are a source of claims here, so its evaluator must not also be the judge.

class RuleEval:
    def __init__(self, tables: Dict[str, Any], defs: Iterable[Dict[str, Any]] = ()):
        self.tables = tables
        self.defs = {d["name"]: d for d in defs}

    def ev(self, node: Any, state: Dict[str, Any], env: Dict[str, Any]) -> Any:
        head = node[0]
        if head == "lit":
            return node[1]
        if head == "var":
            return state[node[1]]
        if head == "param":
            return env[node[1]]
        if head == "and":
            return all(self.ev(x, state, env) for x in node[1:])
        if head == "or":
            return any(self.ev(x, state, env) for x in node[1:])
        if head == "not":
            return not self.ev(node[1], state, env)
        if head == "=":
            return self.ev(node[1], state, env) == self.ev(node[2], state, env)
        if head == "!=":
            return self.ev(node[1], state, env) != self.ev(node[2], state, env)
        if head == "if":
            branch = 2 if self.ev(node[1], state, env) else 3
            return self.ev(node[branch], state, env)
        if head == "table":
            table = self.tables[node[1]]
            args = tuple(self.ev(a, state, env) for a in node[2:])
            for row in table["entries"]:
                if tuple(row[:len(args)]) == args:
                    return row[len(args)]
            if "default" in table:
                return table["default"]
            raise KeyError((node[1], args))
        if head == "call":
            definition = self.defs[node[1]]
            sub = {p: self.ev(a, state, env)
                   for p, a in zip(definition["params"], node[2:])}
            return self.ev(definition["body"], state, sub)
        raise ValueError("unknown expression head %r" % (head,))


def _product_states(spec: Dict[str, Any]) -> Iterable[Tuple[Tuple[str, Any], ...]]:
    """Every state of the declared variable product, in a fixed order."""
    names = sorted(v["name"] for v in spec["variables"])
    domains = {v["name"]: list(v["domain"]) for v in spec["variables"]}
    for combo in itertools.product(*(domains[n] for n in names)):
        yield tuple(zip(names, combo))


def rules_reach(spec: Dict[str, Any]) -> Tuple[Reach, int, Any]:
    ev = RuleEval(spec.get("tables", {}), spec.get("defs", []))
    product_size = 1
    for var in spec["variables"]:
        product_size *= len(var["domain"])

    def succ(state):
        as_dict = dict(state)
        out = []
        for action in sorted(spec["actions"]):
            nxt = dict(as_dict)
            for rule in spec["rules"]:
                if rule["action"] != action:
                    continue
                if not ev.ev(rule["guard"], as_dict, {}):
                    continue
                for var, expr in sorted(rule["effects"].items()):
                    nxt[var] = ev.ev(expr, as_dict, {})
            out.append(tuple(sorted(nxt.items())))
        return out

    def is_goal(state):
        return bool(ev.ev(spec["goal"], dict(state), {}))

    return Reach(tuple(sorted(spec["init"].items())), succ, is_goal), product_size, ev


# ======================================================= A0 spike, from A0.lean

A0_WALLS = frozenset({(1, 5), (4, 4), (5, 5)})
A0_H = A0_W = 7
A0_START = (3, 5, 3, 3)          # pr, pc, br, bc -- `def s0` in A0.lean
A0_GOAL_BOX = (3, 2)             # `def Goal`
A0_DIRS = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}


def a0_step(state, direction, push_distance):
    """`def step`, re-executed.  `push_distance=2` is A0.lean; 1 is the variant."""
    drow, dcol = A0_DIRS[direction]
    pr, pc, br, bc = state

    def free(r, c):
        return 0 <= r < A0_H and 0 <= c < A0_W and (r, c) not in A0_WALLS and (r, c) != (br, bc)

    if free(pr + drow, pc + dcol):
        return (pr + drow, pc + dcol, br, bc)
    if ((pr + drow, pc + dcol) == (br, bc)
            and free(br + drow, bc + dcol)
            and (push_distance == 1
                 or free(br + push_distance * drow, bc + push_distance * dcol))):
        return (br, bc, br + push_distance * drow, bc + push_distance * dcol)
    return state


def a0_reach(push_distance: int) -> Reach:
    return Reach(
        A0_START,
        lambda s: [a0_step(s, d, push_distance) for d in sorted(A0_DIRS)],
        lambda s: (s[2], s[3]) == A0_GOAL_BOX,
    )


# ======================================== the no-button manual, from theory.lean

_LEAN_STEP = re.compile(r"\|\s*⟨Cell\.(c\d+)⟩,\s*\.(\w+)\s*=>\s*⟨Cell\.(c\d+)⟩")


def no_button_reach() -> Tuple[Reach, int, str, str]:
    text = (ROOT / "cold-start-a0/theory/generated_no_button/theory.lean").read_text(
        encoding="utf-8")
    rows = _LEAN_STEP.findall(text)
    table = {(src, direction): dst for src, direction, dst in rows}
    start = re.search(r"def s0 : St := ⟨Cell\.(c\d+)⟩", text).group(1)
    goal = re.search(r"def Goal \(s : St\) : Bool := s\.cart == Cell\.(c\d+)", text).group(1)
    reach = Reach(start,
                  lambda c: [table[(c, d)] for d in ("down", "left", "right", "up")],
                  lambda c: c == goal)
    return reach, len(rows), start, goal


# ================================================= worldgen, by open-door relaxation
# Every door a switch could ever drive is treated as permanently OPEN.  That can
# only add reachable states, so goal-unreachable in the relaxation implies
# goal-unreachable in the world.  `worldgen`'s own door/switch semantics are
# never modelled, which is the point: modelling them from the spec would risk
# reproducing whatever the generator believes.

def worldgen_relaxed(world: str) -> Dict[str, Any]:
    spec = json.loads((ROOT / ("worldgen/out/worlds/%s/spec.json" % world))
                      .read_text(encoding="utf-8"))
    layout = spec["layout"]
    entities = spec.get("entities", [])
    driven = {e["props"]["net"] for e in entities if e["kind"] == "switch"}
    shut = sorted(tuple(e["cell"]) for e in entities
                  if e["kind"] == "door" and e["props"]["net"] not in driven)
    driveable = sorted(tuple(e["cell"]) for e in entities
                       if e["kind"] == "door" and e["props"]["net"] in driven)
    forbidden = spec.get("flags", {}).get("forbidden_action")
    actions = [a for a in sorted(DIRS4) if a != forbidden]
    shut_set = set(shut)

    def passable(cell):
        r, c = cell
        if not (0 <= r < len(layout) and 0 <= c < len(layout[0])):
            return False
        return layout[r][c] != "#" and cell not in shut_set

    goal = tuple(spec["goal"])

    def succ(cell):
        out = []
        for act in actions:
            dr, dc = DIRS4[act]
            nxt = (cell[0] + dr, cell[1] + dc)
            if passable(nxt):
                out.append(nxt)
        return out

    reach = Reach(tuple(spec["agent_start"]), succ, lambda c: c == goal)
    truth = json.loads((ROOT / ("worldgen/out/worlds/%s/ground_truth.json" % world))
                       .read_text(encoding="utf-8"))["solvability"]
    return {
        "world": world,
        "undriven_doors": [list(c) for c in shut],
        "driveable_doors": [list(c) for c in driveable],
        "forbidden_action": forbidden,
        "relaxed_cells": len(reach.states),
        "goal": list(goal),
        "goal_reachable": bool(reach.goals),
        "certificate_agent_cells": truth.get("agent_cells"),
        "certificate_states": truth.get("reachable_states"),
        "certificate_solvable": truth.get("solvable"),
    }


# ================================================================ the inventory

INPUTS = [
    E11_PARTIAL,
    C4_EVIDENCE,
    "a0-spike/artifacts/A0.lean",
    "a0-spike/artifacts/adaptation.json",
    "cold-start-a0/theory/generated_no_button/theory.lean",
    "engine-rig/artifacts/candidates.jsonl",
    "engine-rig/engines/deadlock_carver/carve.py",
    "engine-rig/engines/deadlock_carver/mutex.py",
    "engine-rig/engines/fd_adapter/backends.py",
    "engine-rig/engines/fd_adapter/pddl.py",
    "engine-rig/engines/fd_adapter/search.py",
    "engine-rig/fixtures/data/sokoban_domain.pddl",
    "engine-rig/interop/certificates/pagoda_5_11011_to_00010.json",
    "engine-rig/interop/certificates/pagoda_5_11011_to_01000.json",
    "engine-rig/recheck/cases/a2-holed.rules.json",
    "engine-rig/recheck/cases/a2-right-room-locked.cert.json",
    "engine-rig/recheck/cases/a2-world.rules.json",
    "engine-rig/recheck/cases/peg4-0111-ic3.cert.json",
    "exam/artifacts/truth/p15-verdict-a2.truth.json",
    "theory-compiler/tests/fixtures/strips/sokoban_open4far.pddl",
] + [
    "engine-rig/fixtures/data/sokoban_%s.pddl" % i for i in SOKOBAN
] + [
    "worldgen/out/worlds/%s/spec.json" % w for w in WORLDGEN
] + [
    "worldgen/out/worlds/%s/ground_truth.json" % w for w in WORLDGEN
] + sorted(
    ("engine-rig/recheck/cases/" + p.name)
    for p in (RIG / "recheck/cases").glob("*.cert.json")
) + sorted(
    "proxy/variants/" + p.name for p in (ROOT / "proxy/variants").glob("*.json")
)


def _row(recomputed: Any, prose: Any, registry_key: Optional[str]) -> Dict[str, Any]:
    return {
        "recomputed": recomputed,
        "e11_prose": prose,
        "agrees": recomputed == prose,
        "registry_key": registry_key,
    }


def compute(jsonl_path: Optional[str | Path] = None) -> Dict[str, Any]:
    dom_text = (RIG / "fixtures/data/sokoban_domain.pddl").read_text(encoding="utf-8")
    dom = parse_sexp(dom_text)

    # ------------------------------------------------ the three sokoban encodings
    sokoban: Dict[str, Dict[str, Any]] = {}
    strips_state: Dict[str, Any] = {}
    for inst in SOKOBAN:
        prob_text = (RIG / ("fixtures/data/sokoban_%s.pddl" % inst)).read_text(encoding="utf-8")
        prob = parse_sexp(prob_text)

        own, own_actions, goal = strips_reach(dom, prob)
        pos, pos_actions, well_formed, encodable = positional_reach(prob)
        eng, eng_actions, eng_result = engine_reach(dom_text, prob_text)

        strips_state[inst] = (own, own_actions, goal)
        summary_own = own.summary()
        summary_own["ground_actions"] = len(own_actions)
        summary_pos = pos.summary()
        summary_pos["ground_actions"] = pos_actions
        summary_eng = eng.summary()
        summary_eng["ground_actions"] = eng_actions

        sokoban[inst] = {
            "own_strips": summary_own,
            "positional": summary_pos,
            "engine": summary_eng,
            "positional_well_formed_states": well_formed,
            "positional_encodable_states": encodable,
            "engine_search_plan_length": eng_result.length,
            "engine_search_expansions": eng_result.expansions,
            "engine_search_exhaustive": bool(getattr(eng_result, "exhaustive", False)),
            "three_encodings_agree": summary_own == summary_pos == summary_eng,
        }

    far = sokoban["open4far"]
    c4 = json.loads((ROOT / C4_EVIDENCE).read_text(encoding="utf-8"))
    c4_cases = {case["case"]: case for case in c4["cases"]}
    c4_corner = c4_cases["corner"]
    c4_pair = c4_cases["pair"]

    # ------------------------------------------------------- 36 deadlock claims
    harvested = harvest_theorems()
    certs = harvest_certificates()

    claim_rows: List[Dict[str, Any]] = []
    per_instance: Dict[str, Dict[str, Any]] = {}
    controls: List[Dict[str, Any]] = []
    counter = 0

    for inst in ("open4far", "open4", "ringstuck", "ring"):
        reach, _actions, _goal = strips_state[inst]
        alive = reach.alive
        covered: set = set()
        refuted = vacuous = 0
        matches_by_size: Dict[int, set] = {}
        for pattern in harvested[inst]:
            counter += 1
            matching = [s for s in reach.states if all(a in s for a in pattern)]
            alive_hits = [s for s in matching if s in alive]
            covered |= set(matching)
            vacuous += not matching
            refuted += bool(alive_hits)
            matches_by_size.setdefault(len(pattern), set()).add(len(matching))
            cert_name = certs.get((inst, pattern))
            claim_rows.append({
                "claim_id": "D%02d" % counter,
                "family": "deadlock",
                "instance": "sokoban-" + inst,
                "claim": "every reachable state containing %s is dead" % pattern_text(pattern),
                "certificate": cert_name,
                "rechecked": cert_name is not None,
                "reachable_matches": len(matching),
                "alive_matches": len(alive_hits),
                "verdict": "REFUTED" if alive_hits else "CONFIRMED",
                "method": "exhaustive forward BFS + backward alive-closure (own STRIPS grounder)",
            })
        per_instance[inst] = {
            "theorems": len(harvested[inst]),
            "refuted": refuted,
            "vacuous_over_reachable": vacuous,
            "reachable_states_covered": len(covered),
            "instance_dead_states": reach.dead,
            "coverage_pct": round(100.0 * len(covered) / reach.dead, 1) if reach.dead else None,
            "matches_per_pattern": {str(k): sorted(v) for k, v in sorted(matches_by_size.items())},
        }

    # negative controls -- these must NOT come out dead
    far_reach = strips_state["open4far"][0]
    for pattern in ((("at", "b1", "c22"),),
                    (("at", "b1", "c22"), ("at", "b2", "c23"))):
        matching = [s for s in far_reach.states if all(a in s for a in pattern)]
        alive_hits = [s for s in matching if s in far_reach.alive]
        controls.append({
            "pattern": pattern_text(pattern),
            "reachable_matches": len(matching),
            "alive_matches": len(alive_hits),
            "correctly_rejected": bool(alive_hits),
        })

    # the same 18 patterns, decoded from the certificate JSON instead of carve()
    cert_agreements = 0
    for (inst, pattern), _name in sorted(certs.items()):
        reach = strips_state[inst][0]
        matching = [s for s in reach.states if all(a in s for a in pattern)]
        cert_agreements += not any(s in reach.alive for s in matching)

    theorems_total = sum(len(v) for v in harvested.values())
    theorems_confirmed = sum(1 for r in claim_rows if r["verdict"] == "CONFIRMED")
    recheck_untouched = sum(1 for r in claim_rows if not r["rechecked"])

    # ----------------------------------------------- U1-U14, the categorical claims
    peg4_all = peg_states(4)
    peg4 = {s: peg_reach(s) for s in ("1110", "0111", "1011", "1101")}
    peg5 = peg_reach("11011")

    ic3_cert = json.loads((RIG / "recheck/cases/peg4-0111-ic3.cert.json")
                          .read_text(encoding="utf-8"))
    ic3_ev = RuleEval({})

    def ic3_holds(state: str) -> bool:
        env = {"pos%d" % i: int(bit) for i, bit in enumerate(state)}
        return bool(ic3_ev.ev(ic3_cert["predicate"], env, {}))

    ic3_satisfying = sorted(s for s in peg4_all if ic3_holds(s))
    ic3_check = {
        "state_space": len(peg4_all),
        "satisfying_states": len(ic3_satisfying),
        "holds_at_0111": ic3_holds("0111"),
        "closed_under_every_jump_from_every_satisfying_state": all(
            ic3_holds(t) for s in ic3_satisfying for t in peg_successors(s)),
        "excludes_goal_0100": not ic3_holds("0100"),
        "contains_reachable_set_of_0111": all(ic3_holds(s) for s in peg4["0111"]),
    }

    a0_push2 = a0_reach(2)
    a0_push1 = a0_reach(1)
    a0_box_cells_2 = sorted({(s[2], s[3]) for s in a0_push2.states})
    a0_box_cells_1 = sorted({(s[2], s[3]) for s in a0_push1.states})

    nb_reach, nb_entries, nb_start, nb_goal = no_button_reach()

    a2: Dict[str, Any] = {}
    a2_specs: Dict[str, Any] = {}
    a2_specs_eval: Dict[str, RuleEval] = {}
    for name in ("a2-world", "a2-holed"):
        spec = json.loads((RIG / ("recheck/cases/%s.rules.json" % name))
                          .read_text(encoding="utf-8"))
        reach, product_size, ev = rules_reach(spec)
        a2_specs[name] = spec
        a2_specs_eval[name] = ev
        a2[name] = {
            "reach": reach,
            "product_states": product_size,
            "reachable": len(reach.states),
            "goal_reachable": bool(reach.goals),
            "goal_distance": reach.optimal,
            "n_actions": len(spec["actions"]),
        }

    # `right_room_locked`'s three obligations, over both manuals
    a2_cert = json.loads((RIG / "recheck/cases/a2-right-room-locked.cert.json")
                         .read_text(encoding="utf-8"))
    a2_cert_ev = RuleEval(a2_cert["tables"])

    def a2_invariant(state) -> bool:
        return bool(a2_cert_ev.ev(a2_cert["predicate"], dict(state), {}))

    a2_obligations = {}
    for name in ("a2-holed", "a2-world"):
        reach = a2[name]["reach"]
        breaking = sorted(
            (state, nxt)
            for state in reach.states if a2_invariant(state)
            for nxt in reach.succ[state] if not a2_invariant(nxt)
        )
        closed = not breaking
        witness = ({"from": dict(breaking[0][0]), "to": dict(breaking[0][1])}
                   if breaking else None)
        # `goal_break` is a property of the goal predicate, not of what happens to
        # be reachable, so it is checked over every state of the declared product.
        goal_break = all(
            not a2_invariant(candidate)
            for candidate in _product_states(a2_specs[name])
            if a2_specs_eval[name].ev(a2_specs[name]["goal"], dict(candidate), {})
        )
        a2_obligations[name] = {
            "inv_init": a2_invariant(reach.start),
            "inv_closed": closed,
            "goal_break": goal_break,
            "goal_reachable": bool(reach.goals),
            "breaking_transitions": len(breaking),
            "first_breaking_transition": witness,
            # E11 printed one witness for a2-world; ties are broken differently
            # here, so the question is whether its witness is in the set at all.
            "e11_witness_present": any(
                dict(a)["cart"] == "6,4" and dict(a)["door"] == "no"
                and dict(a)["button"] == 7
                and dict(b)["cart"] == "7,6" and dict(b)["door"] == "no"
                and dict(b)["button"] == 7
                for a, b in breaking),
            "all_breaking_transitions_move_cart_6_4_to_7_6": (
                all(dict(a)["cart"] == "6,4" and dict(b)["cart"] == "7,6"
                    for a, b in breaking) if breaking else None),
            # Why E11's witness is not in the set: `press_up` and `door_opens_up`
            # share one guard and both fire on `up`, so door=="no" forces
            # button==8 in every reachable state.
            "reachable_states_with_door_no_and_button_7": sum(
                1 for s in reach.states
                if dict(s).get("door") == "no" and dict(s).get("button") == 7),
        }

    worldgen = [worldgen_relaxed(w) for w in WORLDGEN]

    def ring_box_cells(inst: str) -> List[str]:
        reach = strips_state[inst][0]
        return sorted({a[2] for s in reach.states for a in s if a[0] == "at"})

    unsolvability: List[Tuple[str, str, str, bool, Any]] = [
        ("U1", "peg4", "peg-4 goal unreachable from 1110 (lp_potential pagoda)",
         "0100" not in peg4["1110"], {"reachable": sorted(peg4["1110"])}),
        ("U2", "peg4", "peg-4 goal unreachable from 1011 (lp_potential pagoda)",
         "0100" not in peg4["1011"], {"reachable": sorted(peg4["1011"])}),
        ("U3", "peg4", "peg-4 goal unreachable from 0111 (ic3_pdr invariant)",
         "0100" not in peg4["0111"] and all(ic3_check[k] is True for k in
                                            ("holds_at_0111",
                                             "closed_under_every_jump_from_every_satisfying_state",
                                             "excludes_goal_0100",
                                             "contains_reachable_set_of_0111")),
         {"reachable": sorted(peg4["0111"]), "ic3": ic3_check}),
        ("U4", "sokoban-ringstuck", "sokoban-ringstuck has no plan (fd_adapter BFS exhaustion)",
         not strips_state["ringstuck"][0].goals,
         {"reachable_states": len(strips_state["ringstuck"][0].states),
          "goal_states": len(strips_state["ringstuck"][0].goals)}),
        ("U5", "peg5", "peg-5 11011 cannot reach 01000 (pagoda certificate)",
         "01000" not in peg5, {"reachable": sorted(peg5)}),
        ("U6", "peg5", "peg-5 11011 cannot reach 00010 (pagoda certificate)",
         "00010" not in peg5, {"reachable": sorted(peg5)}),
        ("U7", "sokoban-ring",
         "probe p_side UNREACHABLE -- the box cannot reach c31 on sokoban-ring",
         "c31" not in ring_box_cells("ring"), {"box_cells": ring_box_cells("ring")}),
        ("U8", "a0-spike-mismatch", "A0 spike mismatch unsolvable -- the box never reaches (3,2)",
         A0_GOAL_BOX not in a0_box_cells_2 and all((s[2] + s[3]) % 2 == 0
                                                   for s in a0_push2.states),
         {"reachable_states": len(a0_push2.states),
          "box_cells": [list(c) for c in a0_box_cells_2]}),
        ("U9", "a0-no-button",
         "the no-button manual is unsolvable -- the Cart never reaches the goal cell",
         not nb_reach.goals,
         {"step_entries": nb_entries, "reachable_cells": len(nb_reach.states),
          "start": nb_start, "goal": nb_goal}),
        ("U10", "a2-holed",
         "right_room_locked -- the Cart can never occupy (2,7), of the holed manual",
         not a2["a2-holed"]["goal_reachable"]
         and a2_obligations["a2-holed"]["inv_init"]
         and a2_obligations["a2-holed"]["inv_closed"]
         and a2_obligations["a2-holed"]["goal_break"],
         {"holed": {k: v for k, v in a2["a2-holed"].items() if k != "reach"},
          "world": {k: v for k, v in a2["a2-world"].items() if k != "reach"},
          "obligations": a2_obligations}),
    ]
    for i, world in enumerate(worldgen):
        unsolvability.append((
            "U%d" % (11 + i),
            world["world"],
            "worldgen world %s is unsolvable (exhaustive_reachability certificate)"
            % world["world"],
            not world["goal_reachable"],
            world,
        ))

    for claim_id, instance, text, confirmed, detail in unsolvability:
        claim_rows.append({
            "claim_id": claim_id,
            "family": "unsolvability",
            "instance": instance,
            "claim": text,
            "certificate": None,
            "rechecked": None,
            "reachable_matches": None,
            "alive_matches": None,
            "verdict": "CONFIRMED" if confirmed else "REFUTED",
            "method": "exhaustive reachability, re-derived from the world description",
            "detail": detail,
        })

    # Sorted by family then by the claim id read as a number, so D2 precedes D10
    # and U2 precedes U10 -- lexicographic order would interleave them.
    claim_rows.sort(key=lambda r: (r["family"], r["claim_id"][0], int(r["claim_id"][1:])))
    n_claims = len(claim_rows)
    n_confirmed = sum(1 for r in claim_rows if r["verdict"] == "CONFIRMED")
    n_refuted = n_claims - n_confirmed
    claims_line = "%d CONFIRMED, %d refuted" % (n_confirmed, n_refuted)

    # ------------------------------------------------------ what was NOT judged
    exam = json.loads((ROOT / "exam/artifacts/truth/p15-verdict-a2.truth.json")
                      .read_text(encoding="utf-8"))
    exam_unsolvable = [i for i in exam["items"]
                       if i["truth"].get("claim") == "unsolvable"
                       and i["truth"].get("certificate_blob") is not None]
    exam_small = sum(1 for i in exam_unsolvable
                     if i["truth"].get("class") == "small_unsolvable")
    arc_variants = [json.loads(p.read_text(encoding="utf-8"))
                    for p in sorted((ROOT / "proxy/variants").glob("*.json"))]
    arc_unsolvable = sorted(v["variant_id"] for v in arc_variants
                            if v.get("claim") == "unsolvable")

    coverage = per_instance["open4far"]["coverage_pct"]
    uncovered = round(
        100.0 * (per_instance["open4far"]["instance_dead_states"]
                 - per_instance["open4far"]["reachable_states_covered"])
        / per_instance["open4far"]["instance_dead_states"], 1)

    # ----------------------------------------------------------- Fast Downward
    from engines.fd_adapter import backends                 # noqa: E402
    fd_executable = backends.find_fast_downward()
    fd_present = fd_executable is not None

    counts: Dict[str, Any] = {
        # ---------------------------- the eleven the ticket names --------------
        "dl.claims": _row(claims_line, "50 CONFIRMED, 0 refuted", "dl.claims"),
        "dl.claims_n": _row(n_claims, 50, "dl.claims_n"),
        "dl.coverage_open4far": _row(coverage, 55.9, "dl.coverage_open4far"),
        "dl.uncovered": _row(uncovered, 44.1, "dl.uncovered"),
        "dl.theorems": _row("%d of %d" % (theorems_confirmed, theorems_total),
                            "36 of 36", "dl.theorems"),
        "dl.unadjudicated_arc": _row(len(arc_unsolvable), 3, "dl.unadjudicated_arc"),
        "dl.unadjudicated_exam": _row(len(exam_unsolvable), 9, "dl.unadjudicated_exam"),
        "fd.open4far_actions": _row(far["own_strips"]["ground_actions"], 112,
                                    "fd.open4far_actions"),
        "fd.open4far_optimal": _row(far["own_strips"]["optimal_plan"], 11,
                                    "fd.open4far_optimal"),
        "fd.open4far_states": _row(far["own_strips"]["reachable_states"], 3352,
                                   "fd.open4far_states"),
        "ic3.states": _row(ic3_check["state_space"], 16, "ic3.states"),
        # ------------- supporting figures from the same sweep, prose-only in E11 --
        "dl.recheck_untouched": _row(recheck_untouched, 18, None),
        "dl.cert_decoded_patterns": _row(len(certs), 18, None),
        "dl.cert_verdicts_agree": _row(cert_agreements, 18, None),
        "dl.open4far_edges": _row(far["own_strips"]["edges"], 9552, None),
        "dl.open4far_dead": _row(far["own_strips"]["dead"], 2904, None),
        "dl.open4far_alive": _row(far["own_strips"]["alive"], 448, None),
        "dl.open4far_goal_states": _row(far["own_strips"]["goal_states_reachable"], 14, None),
        "dl.open4far_covered": _row(per_instance["open4far"]["reachable_states_covered"],
                                    1624, None),
        "dl.open4_optimal": _row(sokoban["open4"]["own_strips"]["optimal_plan"], 6, None),
        "dl.ring_actions": _row(sokoban["ring"]["own_strips"]["ground_actions"], 40, None),
        "dl.ringstuck_states": _row(sokoban["ringstuck"]["own_strips"]["reachable_states"],
                                    44, None),
        "dl.ringstuck_covered": _row(per_instance["ringstuck"]["reachable_states_covered"],
                                     22, None),
        "dl.control_corner_alive": _row(controls[0]["alive_matches"], 70, None),
        "dl.control_pair_alive": _row(controls[1]["alive_matches"], 14, None),
        "dl.well_formed_open4far": _row(far["positional_well_formed_states"], 3360, None),
        "dl.a0_push2_states": _row(len(a0_push2.states), 315, None),
        "dl.a0_push1_states": _row(len(a0_push1.states), 2070, None),
        "dl.no_button_cells": _row(len(nb_reach.states), 23, None),
        "dl.no_button_step_entries": _row(nb_entries, 148, None),
        "dl.a2_world_reachable": _row(a2["a2-world"]["reachable"], 55, None),
        "dl.a2_world_distance": _row(a2["a2-world"]["goal_distance"], 18, None),
        "dl.a2_holed_reachable": _row(a2["a2-holed"]["reachable"], 41, None),
        "dl.a2_product_states": _row(a2["a2-world"]["product_states"], 148, None),
        "dl.a2_inv_closed_breaks": _row(a2_obligations["a2-world"]["breaking_transitions"],
                                        1, None),
        "dl.ic3_satisfying": _row(ic3_check["satisfying_states"], 8, None),
        "dl.exam_small_unsolvable": _row(exam_small, 5, None),
        "extra": {
            "sokoban": sokoban,
            "per_instance": per_instance,
            "negative_controls": controls,
            "c4_evidence_recorded": {
                "ground_actions": c4_corner["ground_actions"],
                "reachable_states": c4_corner["encoding"]["reachable_states"],
                "encodable_states": c4_corner["encoding"]["encodable_states"],
                "plan_length": c4_corner["plan_length"],
                "corner_reachable_states_covered": c4_corner["bite"]["reachable_states_covered"],
                "pair_reachable_states_covered": c4_pair["bite"]["reachable_states_covered"],
                "note": "read from verify/EVIDENCE.json; no Lean toolchain was invoked here",
            },
            "open4far_four_way": {
                "own_strips": {"ground_actions": far["own_strips"]["ground_actions"],
                               "reachable_states": far["own_strips"]["reachable_states"],
                               "optimal_plan": far["own_strips"]["optimal_plan"]},
                "positional": {"ground_actions": far["positional"]["ground_actions"],
                               "reachable_states": far["positional"]["reachable_states"],
                               "optimal_plan": far["positional"]["optimal_plan"]},
                "engine": {"ground_actions": far["engine"]["ground_actions"],
                           "reachable_states": far["engine"]["reachable_states"],
                           "optimal_plan": far["engine"]["optimal_plan"]},
                "c4_lean_recorded": {"ground_actions": c4_corner["ground_actions"],
                                     "reachable_states":
                                         c4_corner["encoding"]["reachable_states"],
                                     "optimal_plan": c4_corner["plan_length"]},
                "all_four_agree": (
                    far["own_strips"]["ground_actions"]
                    == far["positional"]["ground_actions"]
                    == far["engine"]["ground_actions"]
                    == c4_corner["ground_actions"]
                    and far["own_strips"]["reachable_states"]
                    == far["positional"]["reachable_states"]
                    == far["engine"]["reachable_states"]
                    == c4_corner["encoding"]["reachable_states"]
                    and far["own_strips"]["optimal_plan"]
                    == far["positional"]["optimal_plan"]
                    == far["engine"]["optimal_plan"]
                    == c4_corner["plan_length"]),
            },
            "ic3_invariant_check": ic3_check,
            "a2_obligations": a2_obligations,
            "worldgen": worldgen,
            "a0_box_cells_push2": [list(c) for c in a0_box_cells_2],
            "a0_push1_reaches_goal_cell": list(A0_GOAL_BOX) in [list(c) for c in a0_box_cells_1],
            "unadjudicated": {
                "exam_items": sorted(i["item_id"] for i in exam_unsolvable),
                "exam_small_unsolvable": exam_small,
                "exam_large_unsolvable": len(exam_unsolvable) - exam_small,
                "arc_variants": arc_unsolvable,
            },
            "fast_downward": {
                "build_found": fd_present,
                "executable": fd_executable,
                "note": ("no FD build on this machine; every number here is BFS over "
                         "the full reachable set, so none of them can move with the "
                         "toolchain"),
            },
        },
    }

    registry_rows = {k: v for k, v in counts.items()
                     if isinstance(v, dict) and v.get("registry_key")}
    disagreements = sorted(k for k, v in counts.items()
                           if isinstance(v, dict) and "agrees" in v and not v["agrees"])

    caveats = [
        "THREE ENCODINGS, ACTUALLY RUN. CROSSCHECK.md:39 says three encodings agree "
        "bit-for-bit on open4far. Recomputed here by three that ran -- own_strips "
        "(fresh grounder, atom sets with `clear` stored), positional (C4's shape: "
        "(player,b1,b2) with `clear` derived), engine (fd_adapter's own grounder and "
        "BFS) -- plus C4's verify/EVIDENCE.json read from disk. All four give 112 "
        "ground actions / 3352 reachable states / optimal 11: %s."
        % ("agreement confirmed"
           if counts["extra"]["open4far_four_way"]["all_four_agree"] else "THEY DIFFER"),
        "LIMIT ON THAT AGREEMENT -- the world description is a common ancestor. All "
        "three recomputed encodings read engine-rig/fixtures/data/sokoban_open4far.pddl, "
        "and theory-compiler/tests/fixtures/strips/sokoban_open4far.pddl (the file C4's "
        "Lean was built from) is byte-identical to it. So the agreement is evidence "
        "about the encodings, not about the board; a systematic error in "
        "fixtures/sokoban.py would be inherited by all four. E11 recorded the same "
        "limitation (shared dependency 1) and this module inherits it.",
        "The `engine` encoding is the defendant's own code and is NOT independent -- "
        "E11 excluded it deliberately. It is run here because the claim under audit is "
        "an agreement claim: E11 showed its grounder agrees with C4's Lean and left "
        "'does the engine agree with either' to inference. It does.",
        "AMBIGUITY RESOLVED -- what `dl.claims_n` counts. 36 deadlock theorems "
        "(open4far 16, open4 16, ringstuck 2, ring 2, harvested by deadlock_carver.carve) "
        "plus 14 categorical unsolvability claims U1-U14. carve() is claim harvest only; "
        "no engine decision procedure runs on an adjudicating path here.",
        "THE RECHECK GAP, COUNTED. %d of the 36 deadlock claims carry a "
        "recheck/cases/*.cert.json and %d do not -- the open4 16 and the ring 2, exactly "
        "the split E11 named. '50/50 upheld' would be weaker if the recheck path and the "
        "cross-check path shared a premise, so the %d cert-carrying patterns were "
        "adjudicated a second time from the certificate predicate "
        "(['=',['var','b1'],['lit','1,1']] -> at(b1,c11)) rather than from carve(): "
        "%d/%d same verdict. The remaining %d are judged here by nothing else in the repo."
        % (len(certs), recheck_untouched, len(certs), cert_agreements, len(certs),
           recheck_untouched),
        "U10 is CONFIRMED *of the holed manual* and REFUTED *of the world*, which is "
        "how the repo already records it. My own rule-set evaluator (recheck/expr.py "
        "was not imported) reaches the goal on a2-world at distance %s and finds "
        "inv_closed broken by %d transition(s), every one of them cart 6,4 -> 7,6: %s. "
        "That is the teleport_down rule, which a2-world.rules.json's own provenance "
        "names as the single rule the holed manual is missing. E11 printed the "
        "button=7 instance of that transition; this module's tie-break surfaces %s "
        "first, and E11's exact witness is %s in the set. Counted as CONFIRMED, "
        "following E11's convention that a claim is judged against what it claims."
        % (a2["a2-world"]["goal_distance"],
           a2_obligations["a2-world"]["breaking_transitions"],
           a2_obligations["a2-world"]["all_breaking_transitions_move_cart_6_4_to_7_6"],
           json.dumps(a2_obligations["a2-world"]["first_breaking_transition"],
                      sort_keys=True),
           "present" if a2_obligations["a2-world"]["e11_witness_present"] else "ABSENT"),
        "FINDING (cosmetic, and the only place this module parts company with the "
        "prose) -- E11 section 6b prints the inv_closed witness as "
        "`{button: 7, cart: \"6,4\", door: \"no\"} --down--> {button: 7, cart: \"7,6\", "
        "door: \"no\"}`. No such state is reachable: `press_up` and `door_opens_up` "
        "share one guard and both fire on `up`, so door==\"no\" forces button==8, and "
        "this module counts %d reachable a2-world states with door==\"no\" and "
        "button==7. The witness's button field is stale; the transition it names (cart "
        "6,4 -> 7,6 under teleport_down) and the localisation to a single rule are both "
        "correct, and it is the only inv_closed break in the reachable set. Reported "
        "rather than smoothed over, because the whole point of a named witness is that "
        "a reader can go and look at it."
        % a2_obligations["a2-world"]["reachable_states_with_door_no_and_button_7"],
        "The four worldgen worlds are confirmed by RELAXATION, not by modelling "
        "worldgen's door/switch semantics: every door a switch could drive is treated "
        "as permanently open, which can only add reachable states. Cell counts %s. Two "
        "match the certificates exactly (t2-unsolvable-nodoor 11, v-ce732813 3); for the "
        "two v-* worlds the certificate counts 21 states (cell x net) and 11 agent_cells "
        "where this counts 12 cells under the relaxation. Different units -- stated, "
        "not glossed, and not a match."
        % ", ".join("%s %d" % (w["world"], w["relaxed_cells"]) for w in worldgen),
        "FAST DOWNWARD IS ABSENT on this machine (.toolchain/ is gitignored; "
        "backends.find_fast_downward() returned %r) and NONE of the eleven numbers "
        "depends on it. All three sokoban encodings are complete BFS over a 3352-state "
        "space that exhausts in milliseconds; no planner is consulted for any figure "
        "here. The one place the toolchain could bite is fd.open4far_optimal: `optimal` "
        "is only a property of the search that produced it, and fd_adapter's own "
        "fd-satisficing rung (lazy_greedy/lama-first) is not optimal, so a plan length "
        "read off that rung could exceed 11 without any of these numbers being wrong. "
        "This module never calls solve(); it BFSes, so 11 is optimal by construction. "
        "engines.fd_adapter.search.search() agrees: plan length %s, %d expansions, "
        "exhaustive=%s."
        % (fd_executable, far["engine_search_plan_length"],
           far["engine_search_expansions"], far["engine_search_exhaustive"]),
        "COMMIT 2a1c30d (C11) landed after E11's base commit ed592a6 and touched "
        "engines/fd_adapter/{backends,search}.py, bench/fdrun.py and "
        "tools/p13_fd_dividend.py. It moves none of the eleven. What it changed in this "
        "territory is provenance, not arithmetic: SearchResult gained `max_expansions` "
        "and `exhaustive` fields (both kept out of as_json(), so candidates.jsonl is "
        "byte-unchanged), and run_fast_downward() gained encoding='utf-8', "
        "errors='replace' on the subprocess. No successor function, no goal test, no "
        "grounding rule moved -- verified by recomputing on today's tree and getting "
        "E11's 112 / 3352 / 9552 / 14 / 448 / 2904 / 11 back unchanged. Its real subject "
        "is the other direction: reading a tool's exit state as a fact about the world, "
        "which is E11 section 4's finding and is about cold-start-a0's fd_unsat.py, a "
        "file 2a1c30d did not touch (that track's to take or leave).",
        "GAP -- E11 section 4's exit-code contradiction is NOT re-measured here. It is a "
        "claim about two source files' constants (backends.py's FD_SEARCH_UNSOLVABLE=11 "
        "versus cold-start-a0's FD_UNSOLVABLE_EXIT=12), adjudicated against "
        "runs/p13-fd-real/TOOLCHAIN_MANIFEST.md. With no FD build present neither E11 "
        "nor this module can re-run the planner, and no registry number in this family "
        "depends on the answer.",
        "GAP -- the nine exam items and three ARC-variant claims are COUNTED, not "
        "adjudicated, exactly as in E11. The counts are recomputed from disk "
        "(exam/artifacts/truth/p15-verdict-a2.truth.json: %d unsolvable items with a "
        "certificate_blob, %d small_unsolvable + %d large_unsolvable; "
        "proxy/variants/*.json: %d with claim==unsolvable out of %d files). The five "
        "small_unsolvable items carry exhaustive_feasible with 7-31 enumerated states "
        "and remain the obvious next target."
        % (len(exam_unsolvable), exam_small, len(exam_unsolvable) - exam_small,
           len(arc_unsolvable), len(arc_variants)),
        "GAP -- U8 and U9 are judged against their own Lean encodings. `step` was "
        "re-executed from a0-spike/artifacts/A0.lean's definition and the no-button "
        "step table (%d entries) was parsed out of "
        "cold-start-a0/theory/generated_no_button/theory.lean. A DSL->Lean "
        "transcription error is out of reach here, the same scope the Lean proof has."
        % nb_entries,
        "U8's documented retraction reproduced: with the box sliding one cell instead of "
        "two, the space grows %d -> %d states and the box does reach (3,2), so the parity "
        "invariant genuinely stops holding -- a correct retraction, not a defect."
        % (len(a0_push2.states), len(a0_push1.states)),
        "Per-pattern match counts, all with zero alive: %s."
        % "; ".join("%s %s" % (i, per_instance[i]["matches_per_pattern"])
                    for i in ("open4far", "open4", "ring", "ringstuck")),
        ("Every figure agrees with E11." if not disagreements
         else "Disagrees with E11 on: " + ", ".join(disagreements)),
    ]

    if jsonl_path is not None:
        _write_jsonl(Path(jsonl_path), claim_rows)

    return _common.result(
        key="dl.claims_n",
        question=(
            "How many machine-readable deadlock / unsolvability claims does the rig "
            "carry, and how many of them survive exhaustive reachability?"
        ),
        value=n_claims,
        e11_prose=50,
        counts=counts,
        inputs=_common.input_digests(INPUTS),
        method=(
            "Census: %d deadlock theorems harvested by deadlock_carver.carve over the "
            "four sokoban instances, plus %d categorical unsolvability claims read out "
            "of candidates.jsonl, recheck/cases/, interop/certificates/, the Lean files "
            "and worldgen's ground_truth.json. Adjudication: exhaustive forward BFS "
            "from the initial state, then a backward closure from the goal states over "
            "the reachable subgraph -- a state is alive if some goal state is reachable "
            "from it, dead otherwise. No budget anywhere, so every 'unreachable' is a "
            "proof and not a timeout. sokoban is computed three times over (own STRIPS "
            "grounder / positional encoding with `clear` derived / fd_adapter's own) and "
            "compared against C4's verify/EVIDENCE.json. peg-4 and peg-5 use a jump rule "
            "re-implemented from fixtures/peg4.py's docstring; the a2 manuals use a "
            "rule-set evaluator written here rather than recheck/expr.py; A0 and the "
            "no-button manual re-execute the `step` written in their own Lean; the four "
            "worldgen worlds are judged by an open-door relaxation over the layout "
            "literal. No network, no API, no planner, no RNG."
            % (theorems_total, n_claims - theorems_total)
        ),
        caveats=caveats,
    )


JSONL_FIELDS = ("claim_id", "family", "instance", "claim", "certificate", "rechecked",
                "reachable_matches", "alive_matches", "verdict", "method")


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    """One raw row per adjudicated claim, sorted, LF-terminated, keys sorted."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps({k: row.get(k) for k in JSONL_FIELDS},
                                    sort_keys=True) + "\n")


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--jsonl", metavar="PATH", default=None,
                        help="write one raw row per adjudicated claim to PATH")
    args = parser.parse_args()
    _common.main(lambda: compute(jsonl_path=args.jsonl))


if __name__ == "__main__":
    _main()
