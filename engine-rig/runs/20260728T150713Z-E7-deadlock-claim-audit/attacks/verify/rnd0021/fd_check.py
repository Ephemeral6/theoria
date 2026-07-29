"""Settle the rnd0021 witnesses against the real Fast Downward.

For each of the 11 states a carver theorem calls dead and the Python relaxation
calls alive, rebuild it as a one-state PDDL problem and ask FD three questions:

  * did the **translator** print `No relaxed solution!`  (= relaxation-dead,
    settled before search);
  * what is the **initial heuristic value** under `astar(hmax())` and
    `astar(lmcut())` -- `infinity` means the delete relaxation is dead at this
    state, a finite number means it is alive;
  * does `astar(blind())`, run to exhaustion, prove the state unsolvable.

Two controls are run beside them: a state the Python relaxation *does* call dead
(so the instrument can tell the two apart) and the instance's own initial state.
"""

import json
import os
import re
import subprocess
import sys

RIG = r"C:\Users\user\Desktop\theoria\.worktrees\e7-deadlock-claim\engine-rig"
ATTACKS = os.path.join(RIG, "runs", "20260728T150713Z-E7-deadlock-claim-audit",
                       "attacks")
HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "fd-logs")
for p in (RIG, ATTACKS):
    if p not in sys.path:
        sys.path.insert(0, p)

from audit import claim                                        # noqa: E402
from engines.deadlock_carver.carve import Task, carve, pruner  # noqa: E402
from engines.fd_adapter import pddl, search                    # noqa: E402
from fixtures import sokoban                                   # noqa: E402

FD = os.environ.get(
    "FAST_DOWNWARD",
    r"C:/Users/user/Desktop/theoria/.worktrees/p13/engine-rig/.toolchain/downward/fast-downward.py")
BOARD = os.path.join(ATTACKS, "work", "a3", "rnd0021", "rnd0021.pddl")

SEARCHES = (("hmax", "astar(hmax())"),
            ("lmcut", "astar(lmcut())"),
            ("blind", "astar(blind())"))

_EXPANDED = re.compile(r"^(?:\[t=[^\]]*\]\s*)?Expanded (\d+) state\(s\)\.", re.M)
_INITIAL_H = re.compile(
    r"^(?:\[t=[^\]]*\]\s*)?Initial heuristic value for (\S+): (\S+)", re.M)
_TASK_SIZE = re.compile(r"^Translator task size: (\d+)", re.M)
_OPERATORS = re.compile(r"^Translator operators: (\d+)", re.M)


def run_fd(problem_path, config, tag):
    plan = os.path.join(LOGS, tag + ".plan")
    cmd = [sys.executable, FD, "--plan-file", plan,
           os.path.abspath(sokoban.DOMAIN_PATH), os.path.abspath(problem_path),
           "--search", config]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    log = proc.stdout + "\n" + proc.stderr
    with open(os.path.join(LOGS, tag + ".log"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write("$ " + " ".join(cmd) + "\n\n" + log)
    h = _INITIAL_H.findall(log)
    exp = _EXPANDED.findall(log)
    size = _TASK_SIZE.findall(log)
    ops = _OPERATORS.findall(log)
    return {
        "config": config,
        "returncode": proc.returncode,
        "translator_no_relaxed_solution": "No relaxed solution!" in log,
        "translator_unsolvable_task": "Generating unsolvable task" in log,
        "initial_h": (h[-1][1] if h else None),
        "initial_h_infinite": bool(h) and h[-1][1] == "infinity",
        "expanded": int(exp[-1]) if exp else None,
        "translator_task_size": int(size[-1]) if size else None,
        "translator_operators": int(ops[-1]) if ops else None,
        "search_exhausted": "Completely explored state space" in log,
        "solution_found": "Solution found." in log,
        "log": os.path.relpath(os.path.join(LOGS, tag + ".log"), HERE),
    }


def relaxed_witness_plan(actions, state, goal_wanted):
    """The relaxed action sequence that reaches the goal -- the cheat, named."""
    reached = dict((a, None) for a in state)
    order = []
    changed = True
    while changed:
        changed = False
        for action in actions:
            if all(a in reached for a in action.pre_positive):
                new = [a for a in action.add_effects if a not in reached]
                if new:
                    order.append((action.text(), [list(a) for a in new]))
                    for a in new:
                        reached[a] = action.text()
                    changed = True
        if all(a in reached for a in goal_wanted):
            break
    return {
        "goal_reached": all(a in reached for a in goal_wanted),
        "achiever_of_each_goal_atom": {
            "(%s)" % " ".join(a): reached.get(a, "UNREACHED") for a in goal_wanted},
        "trace": order,
    }


def main():
    os.makedirs(LOGS, exist_ok=True)
    text = open(BOARD, encoding="utf-8").read()
    domain = pddl.parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
    problem = pddl.parse_problem(text)
    task = Task.build(domain, problem)
    theorems = carve(task)
    dead = pruner(theorems)

    grounded = pddl.ground_actions(domain, problem)
    actions, initial, _ok = search.strip_static(domain, problem, grounded)
    static = pddl.static_predicates(domain)
    goal_wanted = [a for a in problem.goal_positive if a[0] not in static]

    states = claim._collect(domain, problem)
    relaxed_dead = {i for i, s in enumerate(states)
                    if not claim.relaxed_reachable_goal(actions, s, problem, static)}
    theorem_dead = {i for i, s in enumerate(states) if dead(s)}
    witnesses = sorted(theorem_dead - relaxed_dead)

    # controls: a theorem-dead state the Python relaxation also calls dead, and
    # the instance's own initial state.
    control_dead = sorted(theorem_dead & relaxed_dead)[:2]
    control_init = [states.index(initial)]

    plan_of = {}
    rows = []
    groups = (("witness", witnesses),
              ("control-relaxation-dead", control_dead),
              ("control-initial-state", control_init))
    for group, ids in groups:
        for i in ids:
            s = states[i]
            path = os.path.join(HERE, "problems", "rnd0021-s%04d.pddl" % i)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(claim._problem_with_initial(text, problem, s))
            entry = {
                "group": group,
                "state": i,
                "player": [a[1] for a in s if a[0] == "at-player"][0],
                "boxes": {a[1]: a[2] for a in s if a[0] == "at"},
                "python_relaxation_dead": i in relaxed_dead,
                "theorem_dead": i in theorem_dead,
                "problem": os.path.relpath(path, HERE),
                "fd": {},
            }
            for name, config in SEARCHES:
                entry["fd"][name] = run_fd(path, config, "s%04d-%s" % (i, name))
            rows.append(entry)
            print("%-24s s%04d player=%-4s boxes=%s  translator_dead=%s "
                  "hmax_h=%-9s lmcut_h=%-9s blind_exp=%s exhausted=%s"
                  % (group, i, entry["player"], entry["boxes"],
                     entry["fd"]["hmax"]["translator_no_relaxed_solution"],
                     entry["fd"]["hmax"]["initial_h"],
                     entry["fd"]["lmcut"]["initial_h"],
                     entry["fd"]["blind"]["expanded"],
                     entry["fd"]["blind"]["search_exhausted"]))
            if group == "witness" and not plan_of:
                plan_of = relaxed_witness_plan(actions, s, goal_wanted)

    report = {
        "fast_downward": FD,
        "domain": os.path.abspath(sokoban.DOMAIN_PATH),
        "board": BOARD,
        "n_witnesses": len(witnesses),
        "witness_ids": witnesses,
        "rows": rows,
        "relaxed_cheat_trace_for_first_witness": plan_of,
        "summary": {
            "witnesses_fd_translator_called_relaxation_dead": sum(
                1 for r in rows if r["group"] == "witness"
                and r["fd"]["hmax"]["translator_no_relaxed_solution"]),
            "witnesses_hmax_infinite": sum(
                1 for r in rows if r["group"] == "witness"
                and r["fd"]["hmax"]["initial_h_infinite"]),
            "witnesses_lmcut_infinite": sum(
                1 for r in rows if r["group"] == "witness"
                and r["fd"]["lmcut"]["initial_h_infinite"]),
            "witnesses_blind_proved_unsolvable": sum(
                1 for r in rows if r["group"] == "witness"
                and r["fd"]["blind"]["search_exhausted"]
                and not r["fd"]["blind"]["solution_found"]),
            "controls_fd_translator_called_relaxation_dead": sum(
                1 for r in rows if r["group"] == "control-relaxation-dead"
                and r["fd"]["hmax"]["translator_no_relaxed_solution"]),
        },
    }
    out = os.path.join(HERE, "fd_check.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print()
    print(json.dumps(report["summary"], indent=1))
    print("wrote", out)


if __name__ == "__main__":
    main()
