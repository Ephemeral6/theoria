"""Is the carver sound, and is rnd0021 the only instance with witnesses?

rnd0021 cannot answer the first question by itself: every one of its 92
reachable states is truly dead, so `theorem_dead subset truly_dead` is
vacuously true there and an unsound theorem would be invisible.  So the check
is run over the whole a3 family -- the 11 hand geometries and the 60 random
boards, which include solvable instances where a bad theorem would delete a
real plan.

For each level: the reachable space, the three sets, and
`n_theorem_dead_outside_relaxation`.
"""

import json
import os
import sys
from collections import deque

RIG = r"C:\Users\user\Desktop\theoria\.worktrees\e7-deadlock-claim\engine-rig"
ATTACKS = os.path.join(RIG, "runs", "20260728T150713Z-E7-deadlock-claim-audit",
                       "attacks")
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (RIG, ATTACKS):
    if p not in sys.path:
        sys.path.insert(0, p)

from audit import claim                                        # noqa: E402
from engines.deadlock_carver.carve import Task, carve, pruner  # noqa: E402
from engines.fd_adapter import pddl, search                    # noqa: E402
from fixtures import sokoban                                   # noqa: E402

import a3_family                                               # noqa: E402

LIMIT = int(os.environ.get("SWEEP_LIMIT", "3000"))


def levels():
    import random
    out = [a3_family.parse(name, art) for name, art in sorted(a3_family.HAND.items())]
    rng = random.Random(20260728)
    made, index = [], 0
    while len(made) < 60:
        level = a3_family.random_level(rng, index)
        index += 1
        if level is not None:
            made.append(level)
    return out + made


def collect_capped(domain, problem, actions, initial, static, limit):
    """`claim._collect`, with a cap -- a 4-box 6x6 board has millions of states
    and enumerating them all just to discover it is over the limit is what made
    the first run of this sweep never finish."""
    seen = [initial]
    known = {initial}
    queue = deque([initial])
    while queue:
        if len(seen) > limit:
            return None
        state = queue.popleft()
        if search.is_goal(problem, state, static):
            continue
        for action in actions:
            if not search.applicable(action, state):
                continue
            successor = search.successor(action, state)
            if successor not in known:
                known.add(successor)
                seen.append(successor)
                queue.append(successor)
    return seen


def analyse(level):
    text = level.problem_text()
    domain = pddl.parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
    problem = pddl.parse_problem(text)
    task = Task.build(domain, problem)
    theorems = carve(task)
    dead = pruner(theorems)
    grounded = pddl.ground_actions(domain, problem)
    actions, initial, _ok = search.strip_static(domain, problem, grounded)
    static = pddl.static_predicates(domain)

    states = collect_capped(domain, problem, actions, initial, static, LIMIT)
    if states is None:
        return {"instance": level.name, "skipped": "over %d states" % LIMIT}
    index = {s: i for i, s in enumerate(states)}

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
    truly_dead = {i for i in range(len(states)) if i not in alive}
    relax_dead = {i for i, s in enumerate(states)
                  if not claim.relaxed_reachable_goal(actions, s, problem, static)}
    unsound = sorted(theorem_dead - truly_dead)
    return {
        "instance": level.name,
        "art": list(level.grid),
        "solvable": index[initial] in alive,
        "n_reachable": len(states),
        "n_goal_states": len(goals),
        "n_theorems": len(theorems),
        "theorems": [t.rendering() for t in theorems],
        "n_theorem_dead": len(theorem_dead),
        "n_relaxation_dead": len(relax_dead),
        "n_truly_dead": len(truly_dead),
        "n_theorem_dead_outside_relaxation": len(theorem_dead - relax_dead),
        "n_relaxation_dead_outside_theorems": len(relax_dead - theorem_dead),
        "UNSOUND_theorem_dead_not_truly_dead": len(unsound),
        "unsound_state_ids": unsound[:20],
        "vacuous_soundness_test": len(truly_dead) == len(states),
        "h2_proves_instance_unsolvable": any(
            not task.mutexes.possible(a) for a in task.goal_positive) or any(
            not task.mutexes.co_possible(a, b)
            for i, a in enumerate(task.goal_positive)
            for b in task.goal_positive[i + 1:]),
    }


def main():
    rows = []
    for level in levels():
        try:
            row = analyse(level)
        except Exception as exc:
            row = {"instance": level.name, "failed": repr(exc)}
        rows.append(row)
        if "skipped" in row or "failed" in row:
            print("%-20s %s" % (row["instance"], row.get("skipped") or row["failed"]))
            continue
        flag = ""
        if row["UNSOUND_theorem_dead_not_truly_dead"]:
            flag = "  *** UNSOUND ***"
        if row["n_theorem_dead_outside_relaxation"]:
            flag += "  <<< OUTSIDE RELAXATION"
        print("%-20s solv=%-5s reach=%6d thm=%5d relax=%5d true=%6d outside=%3d "
              "unsound=%d h2unsolv=%s%s"
              % (row["instance"], row["solvable"], row["n_reachable"],
                 row["n_theorem_dead"], row["n_relaxation_dead"],
                 row["n_truly_dead"], row["n_theorem_dead_outside_relaxation"],
                 row["UNSOUND_theorem_dead_not_truly_dead"],
                 row["h2_proves_instance_unsolvable"], flag))

    ok = [r for r in rows if "n_reachable" in r]
    summary = {
        "n_instances_analysed": len(ok),
        "n_unsound": sum(1 for r in ok if r["UNSOUND_theorem_dead_not_truly_dead"]),
        "instances_with_witnesses": [
            r["instance"] for r in ok if r["n_theorem_dead_outside_relaxation"]],
        "n_solvable": sum(1 for r in ok if r["solvable"]),
        "n_unsolvable": sum(1 for r in ok if not r["solvable"]),
        "n_with_nonvacuous_soundness_test": sum(
            1 for r in ok if not r["vacuous_soundness_test"]),
        "n_h2_proves_unsolvable": sum(
            1 for r in ok if r["h2_proves_instance_unsolvable"]),
        "instances_h2_unsolvable_but_relaxation_alive_somewhere": [
            r["instance"] for r in ok
            if r["h2_proves_instance_unsolvable"] and r["n_relaxation_dead"] < r["n_reachable"]],
    }
    out = os.path.join(HERE, "sweep_soundness.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"summary": summary, "rows": rows}, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print()
    print(json.dumps(summary, indent=1))
    print("wrote", out)


if __name__ == "__main__":
    main()
