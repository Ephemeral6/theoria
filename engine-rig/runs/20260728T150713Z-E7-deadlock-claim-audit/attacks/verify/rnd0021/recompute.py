"""Independent recomputation of the rnd0021 counterexample claim.

Run from anywhere:  python <this file>

Reconstructs `rnd0021` two ways (from the on-disk board file, and from
`a3_family.random_level` with the sweep's own seed), then recomputes the three
sets over the whole reachable space using `audit/claim.py`'s own functions --
`relaxed_reachable_goal`, the carver (`Task.build` + `carve` + `pruner`), and
the backward true-dead search transcribed from `claim.coverage`.

Everything is then re-derived a second time with code that shares nothing with
the first (a per-state forward reachability check for true-deadness, and a
hand-written delete-relaxation fixpoint), because the whole point of the
exercise is that a single implementation is a single guess.
"""

import json
import os
import sys
from collections import deque
from itertools import combinations

RIG = r"C:\Users\user\Desktop\theoria\.worktrees\e7-deadlock-claim\engine-rig"
ATTACKS = os.path.join(RIG, "runs", "20260728T150713Z-E7-deadlock-claim-audit",
                       "attacks")
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (RIG, ATTACKS):
    if p not in sys.path:
        sys.path.insert(0, p)

from audit import claim                                        # noqa: E402
from engines.deadlock_carver.carve import Task, carve, pruner, atom_text  # noqa: E402
from engines.fd_adapter import pddl, search                    # noqa: E402
from fixtures import sokoban                                   # noqa: E402

BOARD = os.path.join(ATTACKS, "work", "a3", "rnd0021", "rnd0021.pddl")
OUT = os.path.join(HERE, "recompute.json")


# --------------------------------------------------------------- reconstruction

def from_generator():
    """Re-derive rnd0021 from a3_family's generator with the sweep's own seed."""
    import random
    import a3_family
    rng = random.Random(20260728)
    levels, index = [], 0
    while len(levels) < 60:
        level = a3_family.random_level(rng, index)
        index += 1
        if level is not None:
            levels.append(level)
    for level in levels:
        if level.name == "rnd0021":
            return level
    return None


# ------------------------------------------------------- independent machinery

def independent_relaxed(actions, state, goal_wanted):
    """A hand-written delete relaxation fixpoint (shares no code with claim.py)."""
    reached = set(state)
    frontier = True
    while frontier:
        frontier = False
        for action in actions:
            if all(a in reached for a in action.pre_positive):
                for atom in action.add_effects:
                    if atom not in reached:
                        reached.add(atom)
                        frontier = True
    return all(a in reached for a in goal_wanted)


def independent_truly_dead(actions, problem, static, state):
    """Forward search from this one state: can any goal state be reached?"""
    seen = {state}
    queue = deque([state])
    while queue:
        s = queue.popleft()
        if search.is_goal(problem, s, static):
            return False
        for action in actions:
            if not search.applicable(action, s):
                continue
            t = search.successor(action, s)
            if t not in seen:
                seen.add(t)
                queue.append(t)
    return True


def render(state, cells):
    """Human-readable state summary."""
    player = [a[1] for a in state if a[0] == "at-player"]
    boxes = sorted((a[1], a[2]) for a in state if a[0] == "at")
    clear = sorted(a[1] for a in state if a[0] == "clear")
    return {"player": player[0] if player else None,
            "boxes": {b: c for b, c in boxes},
            "clear": clear}


def main():
    text = open(BOARD, encoding="utf-8").read()
    gen = from_generator()
    gen_text = gen.problem_text() if gen is not None else None
    report = {
        "board_file": BOARD,
        "generator_reproduces_board_file": (gen_text == text),
        "generator_found": gen is not None,
    }

    domain = pddl.parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
    problem = pddl.parse_problem(text)

    task = Task.build(domain, problem)
    theorems = carve(task)
    dead = pruner(theorems)

    grounded = pddl.ground_actions(domain, problem)
    actions, initial, _ok = search.strip_static(domain, problem, grounded)
    static = pddl.static_predicates(domain)
    goal_wanted = [a for a in problem.goal_positive if a[0] not in static]

    report["theorems"] = [t.as_json() for t in theorems]
    report["n_theorems"] = len(theorems)
    report["n_singleton"] = sum(1 for t in theorems if t.size == 1)
    report["n_pair"] = sum(1 for t in theorems if t.size == 2)
    report["n_ground_actions"] = len(actions)

    # ---- the reachable space, exactly as claim.py collects it
    states = claim._collect(domain, problem)
    index = {s: i for i, s in enumerate(states)}
    n = len(states)

    # ---- backward true-dead search, transcribed from claim.coverage
    backward = [[] for _ in states]
    goals = []
    for i, s in enumerate(states):
        if search.is_goal(problem, s, static):
            goals.append(i)
            continue
        for action in actions:
            if not search.applicable(action, s):
                continue
            j = index.get(search.successor(action, s))
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

    theorem_dead = {i for i, s in enumerate(states) if dead(s)}
    truly_dead = {i for i in range(n) if i not in alive}
    relaxation_dead = {i for i, s in enumerate(states)
                       if not claim.relaxed_reachable_goal(actions, s, problem, static)}

    # ---- the same three, recomputed independently
    ind_relax_dead = {i for i, s in enumerate(states)
                      if not independent_relaxed(actions, s, goal_wanted)}
    ind_truly_dead = {i for i, s in enumerate(states)
                      if independent_truly_dead(actions, problem, static, s)}
    # theorem-dead, recomputed without the indexed pruner
    ind_theorem_dead = {i for i, s in enumerate(states)
                        if any(all(a in s for a in t.pattern) for t in theorems)}

    outside = sorted(theorem_dead - relaxation_dead)

    report.update({
        "n_reachable": n,
        "n_goal_states": len(goals),
        "n_theorem_dead": len(theorem_dead),
        "n_relaxation_dead": len(relaxation_dead),
        "n_truly_dead": len(truly_dead),
        "n_theorem_dead_outside_relaxation": len(theorem_dead - relaxation_dead),
        "n_relaxation_dead_outside_theorems": len(relaxation_dead - theorem_dead),
        "n_truly_dead_neither_detects": len(truly_dead - relaxation_dead - theorem_dead),
        "theorem_dead_within_relaxation_dead": len(theorem_dead - relaxation_dead) == 0,
        "theorem_dead_within_truly_dead": len(theorem_dead - truly_dead) == 0,
        "relaxation_dead_within_truly_dead": len(relaxation_dead - truly_dead) == 0,
        "SOUNDNESS_theorem_dead_minus_truly_dead": sorted(theorem_dead - truly_dead),
        "cross_check": {
            "relaxation_agrees_with_independent": relaxation_dead == ind_relax_dead,
            "truly_dead_agrees_with_independent": truly_dead == ind_truly_dead,
            "theorem_dead_agrees_with_independent": theorem_dead == ind_theorem_dead,
        },
        "witness_state_ids": outside,
    })

    # ---- per-theorem soundness, individually
    per_theorem = []
    for t in theorems:
        covered = {i for i, s in enumerate(states) if t.covers(s)}
        per_theorem.append({
            "rendering": t.rendering(),
            "closure": t.kind,
            "size": t.size,
            "n_covered_reachable_states": len(covered),
            "all_covered_are_truly_dead": covered <= truly_dead,
            "n_covered_not_truly_dead": len(covered - truly_dead),
            "n_covered_outside_relaxation": len(covered - relaxation_dead),
            "covered_outside_relaxation_ids": sorted(covered - relaxation_dead),
            "goal_conflict": t.as_json()["goal_conflict"],
        })
    report["per_theorem"] = per_theorem

    # ---- the witnesses, spelled out
    witnesses = []
    for i in outside:
        s = states[i]
        witnesses.append({
            "id": i,
            "state": render(s, None),
            "atoms": sorted(list(a) for a in s),
            "theorems_covering": [t.rendering() for t in theorems if t.covers(s)],
            "truly_dead": i in truly_dead,
            "relaxation_dead_python": i in relaxation_dead,
            "relaxation_dead_independent": i in ind_relax_dead,
        })
    report["witnesses"] = witnesses

    # ---- is the relaxation alive at the initial state too?
    report["initial_state"] = {
        "relaxation_dead": index[initial] in relaxation_dead,
        "truly_dead": index[initial] in truly_dead,
        "theorem_dead": index[initial] in theorem_dead,
        "render": render(initial, None),
    }

    # ---- h^2 evidence behind the theorems: is at(b2,c11) even h^2-reachable?
    report["h2"] = {
        "n_singles": len(task.mutexes.singles),
        "n_pairs": len(task.mutexes.pairs),
        "goal_atoms": [atom_text(a) for a in task.goal_positive],
        "goal_atom_h2_reachable": {
            atom_text(a): task.mutexes.possible(a) for a in task.goal_positive},
        "goal_pair_h2_copossible": {
            "%s & %s" % (atom_text(a), atom_text(b)): task.mutexes.co_possible(a, b)
            for a, b in combinations(task.goal_positive, 2)},
    }

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")

    # also write the state list for the FD stage
    with open(os.path.join(HERE, "states.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump({"witnesses": outside,
                   "states": [sorted(list(a) for a in s) for s in states]},
                  fh, indent=2, sort_keys=True)
        fh.write("\n")

    for k in ("generator_reproduces_board_file", "n_reachable", "n_goal_states",
              "n_theorem_dead", "n_relaxation_dead", "n_truly_dead",
              "n_theorem_dead_outside_relaxation",
              "n_relaxation_dead_outside_theorems",
              "theorem_dead_within_truly_dead",
              "SOUNDNESS_theorem_dead_minus_truly_dead", "cross_check",
              "witness_state_ids"):
        print("%-42s %s" % (k, report[k]))
    print()
    for t in per_theorem:
        print("  %-40s covered=%3d sound=%s outside_relax=%d"
              % (t["rendering"], t["n_covered_reachable_states"],
                 t["all_covered_are_truly_dead"], t["n_covered_outside_relaxation"]))
    print()
    print("h2:", json.dumps(report["h2"], indent=1))
    print("initial:", json.dumps(report["initial_state"], indent=1))
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
