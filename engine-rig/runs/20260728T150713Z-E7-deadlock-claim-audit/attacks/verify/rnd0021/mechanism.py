"""Which dropped delete is load-bearing in the rnd0021 witness?

The reviewer's account of the mechanism names `clear c12`: "pushing b2 c12->c13
ADDS `clear c12` without removing `at b2 c12`".  Half of that is right and the
named atom is not: the sokoban `push` action never adds `clear ?from` -- it
deletes it.  What it adds is `at-player ?from`, the player stepping into the
cell the box just left.

So the isolation is run rather than argued.  Three relaxations over the same
witness state:

  * `full`      -- all deletes dropped (the textbook delete relaxation, and what
                   FD's translator computes);
  * `keep_at`   -- deletes of `at` restored, everything else dropped;
  * `keep_clear`-- deletes of `clear` restored, everything else dropped;
  * `keep_player` -- deletes of `at-player` restored, everything else dropped.

and the justification chain for the goal atom, back to the initial state.
"""

import json
import os
import sys

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

BOARD = os.path.join(ATTACKS, "work", "a3", "rnd0021", "rnd0021.pddl")


def relaxed(actions, state, wanted, keep=()):
    """Delete relaxation, optionally keeping the deletes of some predicates.

    Keeping a delete makes this no longer a relaxation and no longer monotone,
    so it is run as a *forward reachability over sets* only when `keep` is
    empty; with `keep` non-empty it is run as a real forward state search, which
    is the honest way to ask "would this still work if that delete were real".
    """
    if not keep:
        reached = set(state)
        changed = True
        while changed:
            changed = False
            for action in actions:
                if all(a in reached for a in action.pre_positive):
                    for atom in action.add_effects:
                        if atom not in reached:
                            reached.add(atom)
                            changed = True
        return all(a in reached for a in wanted)

    from collections import deque
    start = frozenset(state)
    seen = {start}
    queue = deque([start])
    while queue:
        s = queue.popleft()
        if all(a in s for a in wanted):
            return True
        for action in actions:
            if not all(a in s for a in action.pre_positive):
                continue
            drop = {a for a in action.del_effects if a[0] in keep}
            t = frozenset((set(s) - drop) | set(action.add_effects))
            if t not in seen:
                seen.add(t)
                queue.append(t)
    return False


def justify(actions, state, wanted):
    """Back-chain the relaxed achievement of each goal atom to the initial state."""
    achiever = {}
    reached = set(state)
    changed = True
    while changed:
        changed = False
        for action in actions:
            if all(a in reached for a in action.pre_positive):
                for atom in action.add_effects:
                    if atom not in reached:
                        reached.add(atom)
                        achiever[atom] = action
                        changed = True

    chain, seen = [], set()

    def walk(atom, depth=0):
        if atom in seen:
            return
        seen.add(atom)
        act = achiever.get(atom)
        if act is None:
            chain.append({"depth": depth, "atom": list(atom), "by": "INITIAL STATE"})
            return
        chain.append({"depth": depth, "atom": list(atom), "by": act.text(),
                      "needs": [list(a) for a in act.pre_positive]})
        for pre in act.pre_positive:
            walk(pre, depth + 1)

    for atom in wanted:
        walk(atom)
    return chain


def main():
    text = open(BOARD, encoding="utf-8").read()
    domain = pddl.parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
    problem = pddl.parse_problem(text)
    task = Task.build(domain, problem)
    theorems = carve(task)
    dead = pruner(theorems)
    grounded = pddl.ground_actions(domain, problem)
    actions, initial, _ok = search.strip_static(domain, problem, grounded)
    static = pddl.static_predicates(domain)
    wanted = [a for a in problem.goal_positive if a[0] not in static]

    states = claim._collect(domain, problem)
    relax_dead = {i for i, s in enumerate(states)
                  if not claim.relaxed_reachable_goal(actions, s, problem, static)}
    theorem_dead = {i for i, s in enumerate(states) if dead(s)}
    witness = sorted(theorem_dead - relax_dead)[0]
    s = states[witness]

    report = {
        "witness_state": witness,
        "player": [a[1] for a in s if a[0] == "at-player"][0],
        "boxes": {a[1]: a[2] for a in s if a[0] == "at"},
        "goal_reached_in_relaxation": {
            "full_relaxation (what FD's translator computes)":
                relaxed(actions, s, wanted),
            "deletes_of_at_restored": relaxed(actions, s, wanted, keep=("at",)),
            "deletes_of_clear_restored": relaxed(actions, s, wanted, keep=("clear",)),
            "deletes_of_at-player_restored":
                relaxed(actions, s, wanted, keep=("at-player",)),
            "no_relaxation_at_all (real dynamics)":
                relaxed(actions, s, wanted, keep=("at", "clear", "at-player")),
        },
        "justification_chain": justify(actions, s, wanted),
    }
    out = os.path.join(HERE, "mechanism.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(json.dumps(report["goal_reached_in_relaxation"], indent=1))
    print()
    for step in report["justification_chain"]:
        print("%s(%s) <- %s" % ("  " * step["depth"],
                                " ".join(step["atom"]), step["by"]))
    print("\nwrote", out)


if __name__ == "__main__":
    main()
