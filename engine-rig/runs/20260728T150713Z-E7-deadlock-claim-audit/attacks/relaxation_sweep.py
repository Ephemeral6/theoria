"""Adversarial sweep: is `theorem_dead` really always inside `relaxation_dead`?

The claim under attack is measured on exactly one family -- `far{N}`, an open
N x N interior with two boxes and the player in a corner.  This module runs the
same three-set analysis `audit.claim.coverage()` runs, but over an arbitrary
`fixtures.sokoban.Level`, so the family can be varied: corridors, interior
walls, chokepoints, dead-end pockets, three boxes, boxes parked on goals, goals
against walls, non-square boards, and a randomized fuzz over small grids.

The number that would refute the claim is `n_theorem_dead_outside_relaxation`.
Anything above zero on any geometry is a carver theorem that detects a dead
state Fast Downward's translator does not.

Nothing here is imported by the rig.  `relaxed_reachable_goal` is imported from
`audit.claim` on purpose: an attack that reimplements the thing it is attacking
can only find bugs in its own copy.

    python -m attacks.relaxation_sweep sweep      # every named geometry
    python -m attacks.relaxation_sweep fuzz 200   # randomized small boards
    python -m attacks.relaxation_sweep goalcut    # attack 3: the _collect cut
"""

import json
import os
import random
import sys
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if RIG not in sys.path:
    sys.path.insert(0, RIG)

from audit.claim import relaxed_reachable_goal              # noqa: E402
from bench.instances import far_level                       # noqa: E402
from engines.deadlock_carver.carve import Task, carve, pruner  # noqa: E402
from engines.fd_adapter import pddl, search                 # noqa: E402
from fixtures import sokoban                                # noqa: E402

Cell = Tuple[int, int]


# ------------------------------------------------------------------ machinery

def load(level: sokoban.Level, domain_path: str = sokoban.DOMAIN_PATH):
    text = level.problem_text()
    with open(domain_path, encoding="utf-8") as handle:
        domain = pddl.parse_domain(handle.read())
    problem = pddl.parse_problem(text)
    return domain, problem, text


def collect(domain, problem, actions, initial, static, expand_goals: bool,
            cap: int) -> Optional[List]:
    """Reachable states.  `expand_goals=False` reproduces `claim._collect`."""
    seen = [initial]
    known = {initial}
    queue = deque([initial])
    while queue:
        state = queue.popleft()
        if not expand_goals and search.is_goal(problem, state, static):
            continue
        for action in actions:
            if not search.applicable(action, state):
                continue
            successor = search.successor(action, state)
            if successor not in known:
                known.add(successor)
                seen.append(successor)
                if len(seen) > cap:
                    return None
                queue.append(successor)
    return seen


def analyse(level: sokoban.Level, domain_path: str = sokoban.DOMAIN_PATH,
            cap: int = 40000, expand_goals: bool = False,
            want_truly_dead: bool = True) -> Dict[str, object]:
    """`audit.claim.coverage()`, generalised to any level and any domain."""
    domain, problem, _text = load(level, domain_path)
    task = Task.build(domain, problem)
    theorems = carve(task)
    dead = pruner(theorems)

    grounded = pddl.ground_actions(domain, problem)
    actions, initial, static_ok = search.strip_static(domain, problem, grounded)
    static = pddl.static_predicates(domain)

    states = collect(domain, problem, actions, initial, static, expand_goals, cap)
    if states is None:
        return {"instance": level.name, "skipped": "over %d states" % cap,
                "n_theorems": len(theorems)}

    index = {state: i for i, state in enumerate(states)}
    theorem_dead = {i for i, s in enumerate(states) if dead(s)}
    relaxation_dead = {
        i for i, s in enumerate(states)
        if not relaxed_reachable_goal(actions, s, problem, static)
    }

    out: Dict[str, object] = {
        "instance": level.name,
        "cells": len(level.floors()),
        "boxes": len(level.boxes),
        "static_goal_ok": static_ok,
        "expand_goals": expand_goals,
        "n_theorems": len(theorems),
        "n_singleton_theorems": sum(1 for t in theorems if t.size == 1),
        "n_pair_theorems": sum(1 for t in theorems if t.size == 2),
        "theorem_kinds": sorted({t.kind for t in theorems}),
        "n_reachable": len(states),
        "n_theorem_dead": len(theorem_dead),
        "n_relaxation_dead": len(relaxation_dead),
        "n_theorem_dead_outside_relaxation": len(theorem_dead - relaxation_dead),
        "n_relaxation_dead_outside_theorems": len(relaxation_dead - theorem_dead),
    }

    if want_truly_dead:
        backward: List[List[int]] = [[] for _ in states]
        goals = []
        for i, state in enumerate(states):
            if search.is_goal(problem, state, static):
                goals.append(i)
                if not expand_goals:
                    continue
            for action in actions:
                if not search.applicable(action, state):
                    continue
                j = index.get(search.successor(action, state))
                if j is not None:
                    backward[j].append(i)
        alive = set(goals)
        queue = deque(goals)
        while queue:
            i = queue.popleft()
            for j in backward[i]:
                if j not in alive:
                    alive.add(j)
                    queue.append(j)
        truly_dead = {i for i in range(len(states)) if i not in alive}
        out["_truly_dead"] = truly_dead
        out.update({
            "n_goal_states": len(goals),
            "n_truly_dead": len(truly_dead),
            "relaxation_dead_equals_truly_dead": relaxation_dead == truly_dead,
            "n_truly_dead_outside_relaxation": len(truly_dead - relaxation_dead),
            "n_relaxation_dead_outside_truly_dead": len(relaxation_dead - truly_dead),
            "n_theorem_dead_outside_truly_dead": len(theorem_dead - truly_dead),
        })

    # Keep the witnesses, not the whole space.
    witnesses = sorted(theorem_dead - relaxation_dead)[:5]
    out["witness_states"] = [sorted(states[i]) for i in witnesses]
    out["witness_theorems"] = [
        [t.rendering() for t in theorems if t.covers(states[i])] for i in witnesses
    ]
    out["_states"] = states
    out["_theorems"] = theorems
    out["_problem"] = problem
    out["_actions"] = actions
    out["_static"] = static
    out["_relaxation_dead"] = relaxation_dead
    return out


def public(entry: Dict[str, object]) -> Dict[str, object]:
    return {k: v for k, v in entry.items() if not k.startswith("_")}


# ------------------------------------------------------------------ geometries

def grid_from(rows: Sequence[str]) -> Tuple[str, ...]:
    return tuple(rows)


def level(name, rows, player, boxes, goals) -> sokoban.Level:
    return sokoban.Level(name=name, grid=grid_from(rows), player=player,
                         boxes=tuple(boxes), goals=tuple(goals),
                         optimum=None, path="")


def open_rows(height: int, width: int) -> List[str]:
    return (["#" * (width + 2)]
            + ["#" + "." * width + "#" for _ in range(height)]
            + ["#" * (width + 2)])


def named_levels() -> List[sokoban.Level]:
    """Every geometry this attack tries, each one aimed at a specific escape."""
    out: List[sokoban.Level] = []

    # 0. The family under attack, as a control.
    out.append(far_level(4))

    # 1. The committed fixtures: a 1-wide corridor loop, solvable and not.
    out.append(sokoban.RING)
    out.append(sokoban.RING_STUCK)
    out.append(sokoban.OPEN4)
    out.append(sokoban.OPEN4FAR)

    # 2. The two dead-start shapes, whose docstring predicts the split.
    from audit import deadstart
    out.append(deadstart.corner_level(4))
    out.append(deadstart.pair_level(4))
    out.append(deadstart.alive_level(4))

    # 3. Non-square boards.
    out.append(level("rect3x5", open_rows(3, 5), (3, 5),
                     [("b1", (2, 2)), ("b2", (2, 4))],
                     [("b1", (2, 4)), ("b2", (2, 2))]))
    out.append(level("rect2x6", open_rows(2, 6), (2, 6),
                     [("b1", (1, 2)), ("b2", (2, 4))],
                     [("b1", (2, 5)), ("b2", (1, 3))]))
    out.append(level("rect5x3", open_rows(5, 3), (5, 3),
                     [("b1", (2, 2)), ("b2", (4, 2))],
                     [("b1", (4, 2)), ("b2", (2, 2))]))

    # 4. Interior walls: a pillar in an open room makes non-corner dead cells
    #    (a box against the pillar's flank) that a *pair* theorem cannot see and
    #    a singleton can.
    pillar = ["######",
              "#....#",
              "#.##.#",
              "#....#",
              "######"]
    out.append(level("pillar-a", pillar, (3, 4),
                     [("b1", (1, 2)), ("b2", (3, 3))],
                     [("b1", (3, 2)), ("b2", (1, 3))]))
    out.append(level("pillar-b", pillar, (1, 1),
                     [("b1", (1, 3)), ("b2", (3, 2))],
                     [("b1", (3, 4)), ("b2", (1, 2))]))

    # 5. Two rooms joined by a 1-wide corridor: a box in the corridor is a
    #    chokepoint, so `at-player(far side)` and `at(b, choke)` are globally
    #    mutex -- an h^2 fact the delete relaxation does not have.
    choke = ["#######",
             "#..#..#",
             "#.....#",
             "#..#..#",
             "#######"]
    out.append(level("choke-a", choke, (2, 1),
                     [("b1", (2, 3)), ("b2", (2, 5))],
                     [("b1", (2, 5)), ("b2", (2, 2))]))
    out.append(level("choke-b", choke, (1, 1),
                     [("b1", (2, 3)), ("b2", (3, 5))],
                     [("b1", (1, 5)), ("b2", (1, 2))]))

    # 6. A dead-end pocket reached only through one cell: the pusher cell for
    #    the only push out of the chokepoint is inside the pocket, which the
    #    player can only be in if it went there first.
    pocket = ["######",
              "#....#",
              "###.##",
              "#....#",
              "######"]
    out.append(level("pocket-a", pocket, (1, 1),
                     [("b1", (2, 3)), ("b2", (3, 2))],
                     [("b1", (3, 4)), ("b2", (1, 4))]))
    out.append(level("pocket-b", pocket, (3, 4),
                     [("b1", (1, 3)), ("b2", (3, 3))],
                     [("b1", (3, 1)), ("b2", (1, 2))]))

    # 7. Three boxes on a small board -- more pairs, more chances for a pattern
    #    whose closure needs the third box's mutexes.
    out.append(level("three-a", open_rows(4, 4), (4, 4),
                     [("b1", (2, 2)), ("b2", (2, 3)), ("b3", (3, 2))],
                     [("b1", (4, 2)), ("b2", (1, 3)), ("b3", (3, 4))]))
    out.append(level("three-b", open_rows(3, 4), (3, 4),
                     [("b1", (1, 2)), ("b2", (2, 2)), ("b3", (2, 3))],
                     [("b1", (3, 3)), ("b2", (1, 4)), ("b3", (3, 1))]))

    # 8. A box already on its goal, and a goal in a corner: a corner that is a
    #    goal is not a dead cell, so the carver must not emit it -- and the
    #    relaxation must agree.
    out.append(level("goal-in-corner", open_rows(4, 4), (4, 4),
                     [("b1", (2, 2)), ("b2", (3, 3))],
                     [("b1", (1, 1)), ("b2", (4, 4))]))
    out.append(level("box-on-goal", open_rows(4, 4), (4, 4),
                     [("b1", (1, 1)), ("b2", (3, 3))],
                     [("b1", (1, 1)), ("b2", (1, 3))]))
    out.append(level("goal-against-wall", open_rows(4, 4), (4, 4),
                     [("b1", (2, 2)), ("b2", (3, 3))],
                     [("b1", (1, 2)), ("b2", (4, 3))]))

    # 9. Cross / plus shape: every arm is a 1-wide corridor, so a box that
    #    enters an arm can never turn.
    plus = ["#####",
            "##.##",
            "#...#",
            "##.##",
            "#####"]
    out.append(level("plus", plus, (2, 1),
                     [("b1", (2, 2))],
                     [("b1", (3, 2))]))
    plus2 = ["######",
             "##..##",
             "#....#",
             "#....#",
             "##..##",
             "######"]
    out.append(level("plus2", plus2, (1, 2),
                     [("b1", (2, 2)), ("b2", (3, 3))],
                     [("b1", (4, 3)), ("b2", (1, 3))]))

    # 10. An L-shaped room and a T: concave corners that are not board corners.
    ell = ["######",
           "#..###",
           "#..###",
           "#....#",
           "#....#",
           "######"]
    out.append(level("ell", ell, (4, 4),
                     [("b1", (2, 2)), ("b2", (3, 3))],
                     [("b1", (4, 2)), ("b2", (1, 2))]))
    tee = ["######",
           "#....#",
           "##..##",
           "##..##",
           "######"]
    out.append(level("tee", tee, (1, 1),
                     [("b1", (1, 3)), ("b2", (2, 2))],
                     [("b1", (3, 3)), ("b2", (1, 4))]))

    # 11. A corridor with a widening: the only place a box can be passed.
    corridor = ["#######",
                "#.....#",
                "###.###",
                "#.....#",
                "#######"]
    out.append(level("hcorridor", corridor, (1, 1),
                     [("b1", (1, 3)), ("b2", (3, 3))],
                     [("b1", (3, 5)), ("b2", (1, 5))]))

    # 12. far5 -- the same family one size up, as a second control.
    out.append(far_level(5))
    return out


# ---------------------------------------------------------------------- fuzz

def random_level(rng: random.Random, index: int) -> Optional[sokoban.Level]:
    height = rng.choice((3, 4, 4, 5))
    width = rng.choice((3, 4, 4, 5))
    rows = [list(row) for row in open_rows(height, width)]
    interior = [(r, c) for r in range(1, height + 1) for c in range(1, width + 1)]
    for cell in rng.sample(interior, rng.randint(0, min(3, len(interior) - 4))):
        rows[cell[0]][cell[1]] = "#"
    grid = tuple("".join(row) for row in rows)
    floors = [(r, c) for r in range(1, height + 1) for c in range(1, width + 1)
              if grid[r][c] == "."]
    if len(floors) < 5:
        return None
    # One connected component only, or the instance is trivially unsolvable for
    # a reason that has nothing to do with deadlocks.
    seen = {floors[0]}
    stack = [floors[0]]
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (r + dr, c + dc)
            if nxt in floors and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    if len(seen) != len(floors):
        return None
    n_boxes = rng.choice((2, 2, 3))
    if len(floors) < n_boxes + 2:
        return None
    picked = rng.sample(floors, n_boxes + 1)
    player = picked[0]
    boxes = [("b%d" % (i + 1), cell) for i, cell in enumerate(picked[1:])]
    goal_cells = rng.sample(floors, n_boxes)
    goals = [("b%d" % (i + 1), cell) for i, cell in enumerate(goal_cells)]
    return level("fuzz%03d" % index, list(grid), player, boxes, goals)


# ----------------------------------------------------------------- subcommands

def cmd_sweep(argv: Sequence[str]) -> None:
    cap = int(argv[0]) if argv else 45000
    rows = []
    for lvl in named_levels():
        entry = public(analyse(lvl, cap=cap))
        rows.append(entry)
        report(entry)
    dump(rows, os.path.join(HERE, "sweep_named.json"))


def cmd_fuzz(argv: Sequence[str]) -> None:
    count = int(argv[0]) if argv else 120
    seed = int(argv[1]) if len(argv) > 1 else 20260728
    cap = int(argv[2]) if len(argv) > 2 else 20000
    rng = random.Random(seed)
    rows = []
    index = 0
    tried = 0
    while len(rows) < count and tried < count * 20:
        tried += 1
        lvl = random_level(rng, index)
        if lvl is None:
            continue
        index += 1
        try:
            entry = public(analyse(lvl, cap=cap))
        except Exception as exc:                                # pragma: no cover
            entry = {"instance": lvl.name, "error": "%s: %s" % (type(exc).__name__, exc)}
        entry["grid"] = list(lvl.grid)
        entry["player"] = list(lvl.player)
        entry["boxes"] = [[n, list(c)] for n, c in lvl.boxes]
        entry["goals"] = [[n, list(c)] for n, c in lvl.goals]
        rows.append(entry)
        report(entry)
    dump(rows, os.path.join(HERE, "sweep_fuzz.json"))
    breaks = [r for r in rows if r.get("n_theorem_dead_outside_relaxation")]
    print("\nfuzz: %d levels, %d with theorem-dead outside the relaxation"
          % (len(rows), len(breaks)))
    mismatch = [r for r in rows if r.get("relaxation_dead_equals_truly_dead") is False]
    print("fuzz: %d levels where relaxation-dead != truly-dead" % len(mismatch))


def cmd_goalcut(argv: Sequence[str]) -> None:
    """Attack 3: `_collect` stops at goal states.  Does that lose states?"""
    rows = []
    for side in (4, 5):
        for expand in (False, True):
            entry = public(analyse(far_level(side), expand_goals=expand))
            rows.append(entry)
            report(entry)
    dump(rows, os.path.join(HERE, "goalcut.json"))


def cmd_nc(argv: Sequence[str]) -> None:
    """Attack 4: the same worlds in the `occupied` encoding, side by side.

    The transition relation is isomorphic, so `n_reachable` and `n_truly_dead`
    must come out identical; anything that moves is a property of the encoding,
    not of sokoban.
    """
    from attacks import noclear

    wanted = list(argv) or ["far4", "ell", "three-b", "box-on-goal", "ringstuck",
                            "goal-in-corner", "rect3x5", "plus2"]
    by_name = {lvl.name: lvl for lvl in named_levels()}
    domain_path = noclear.write_domain(os.path.join(HERE, "crosscheck"))
    rows = []
    for name in wanted:
        lvl = by_name[name]
        plain = public(analyse(lvl))
        nc = public(analyse(noclear.as_nc(lvl), domain_path=domain_path))
        report(plain)
        report(nc)
        rows.append({"clear": plain, "occupied": nc, "level": name,
                     "same_state_space": plain["n_reachable"] == nc["n_reachable"],
                     "same_truly_dead": plain.get("n_truly_dead") == nc.get("n_truly_dead"),
                     "relaxation_lost": (nc["n_reachable"] - nc["n_relaxation_dead"])
                                        - (plain["n_reachable"] - plain["n_relaxation_dead"]),
                     "theorems_lost": plain["n_theorems"] - nc["n_theorems"]})
    dump(rows, os.path.join(HERE, "noclear_compare.json"))
    for r in rows:
        print("%-16s same_space=%-5s same_truly_dead=%-5s theorems %d->%d  "
              "relaxation_dead %d->%d"
              % (r["level"], r["same_state_space"], r["same_truly_dead"],
                 r["clear"]["n_theorems"], r["occupied"]["n_theorems"],
                 r["clear"]["n_relaxation_dead"], r["occupied"]["n_relaxation_dead"]))


def report(entry: Dict[str, object]) -> None:
    if "skipped" in entry or "error" in entry:
        print("%-18s %s" % (entry["instance"], entry.get("skipped") or entry.get("error")))
        return
    print("%-18s states=%-6s thm=%-5s relax=%-6s true=%-6s | thm\\relax=%-4s "
          "relax==true=%-5s thm\\true=%s  (%d theorems: %s)"
          % (entry["instance"], entry["n_reachable"], entry["n_theorem_dead"],
             entry["n_relaxation_dead"], entry.get("n_truly_dead"),
             entry["n_theorem_dead_outside_relaxation"],
             entry.get("relaxation_dead_equals_truly_dead"),
             entry.get("n_theorem_dead_outside_truly_dead"),
             entry["n_theorems"], ",".join(entry["theorem_kinds"]) or "-"))


def dump(obj, path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(obj, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("-> %s" % path)


COMMANDS = {"sweep": cmd_sweep, "fuzz": cmd_fuzz, "goalcut": cmd_goalcut, "nc": cmd_nc}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit("usage: python -m attacks.relaxation_sweep {%s} [args]"
                         % "|".join(sorted(COMMANDS)))
    COMMANDS[sys.argv[1]](sys.argv[2:])
