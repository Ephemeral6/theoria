"""Ask Fast Downward's HEURISTIC -- not its translator -- about a dead state.

The audit's own instrument for the mechanism claim (`audit.claim.heuristic_knows`)
rebuilds each sampled state as a one-state PDDL problem and reads FD's
`Initial heuristic value` line.  On this family every dead state is
relaxation-dead, so FD's *translator* aborts with `No relaxed solution!` and
substitutes an unsolvable task before any heuristic is constructed.  The proof
that this is what happens: in the run's own `H-far4-dead-*-blind.log` files,
`astar(blind())` -- which has no deadness test whatever -- also reports
`Initial heuristic value for blind: infinity`.

This module bypasses the translator entirely.  far4 is translated ONCE (it is
solvable, so the shortcut does not fire), then the `begin_state` block of the
resulting `output.sas` is rewritten to the state under test and the *search
component* alone is run on the edited SAS file.  The heuristic is then built on
the real task and asked about the real state, and its answer is its own.

    python sasprobe.py            # writes sasprobe.json beside this file
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, RIG)

FD = os.environ.get(
    "FAST_DOWNWARD",
    "C:/Users/user/Desktop/theoria/.worktrees/p13/engine-rig/.toolchain/downward/fast-downward.py",
)

from audit import claim                                     # noqa: E402
from bench.instances import far_level                       # noqa: E402
from engines.deadlock_carver.carve import Task, carve, pruner  # noqa: E402
from engines.fd_adapter import pddl, search                 # noqa: E402
from fixtures import sokoban                                # noqa: E402


def parse_sas(path):
    text = open(path, encoding="utf-8").read()
    blocks = re.findall(
        r"begin_variable\nvar(\d+)\n(-?\d+)\n(\d+)\n(.*?)end_variable", text, re.S)
    variables = []
    for index, _axiom, _n, values in blocks:
        variables.append((int(index), [v for v in values.strip().split("\n")]))
    variables.sort()
    return text, [v for _i, v in variables]


def sas_name(atom):
    if atom[0] == "at":
        return "Atom at(%s, %s)" % (atom[1], atom[2])
    return "Atom %s(%s)" % (atom[0], ", ".join(atom[1:]))


def state_to_sas(variables, state):
    """The SAS value vector for a stripped search state. Exact, or it raises."""
    present = {sas_name(a) for a in state}
    out = []
    for values in variables:
        chosen = [i for i, v in enumerate(values) if v in present]
        if len(chosen) == 1:
            out.append(chosen[0])
            continue
        if not chosen and len(values) == 2 and values[1].startswith("NegatedAtom"):
            out.append(1)                      # the atom is simply false here
            continue
        raise RuntimeError("state does not determine %r (matched %r)" % (values, chosen))
    return out


def write_sas(text, path, assignment):
    new = re.sub(r"(begin_state\n).*?(end_state)",
                 lambda m: m.group(1) + "".join("%d\n" % v for v in assignment) + m.group(2),
                 text, count=1, flags=re.S)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(new)


HEURISTIC = {"blind": "blind()", "lmcut": "lmcut()", "ipdb": "ipdb()"}


def run_search(sas_path, heuristic, tag):
    log = os.path.join(HERE, "logs", tag + ".log")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    proc = subprocess.run(
        [sys.executable, FD, "--plan-file", os.path.join(HERE, "work", tag + ".plan"),
         sas_path, "--search", "astar(%s)" % HEURISTIC[heuristic]],
        capture_output=True, text=True, cwd=os.path.join(HERE, "work"))
    text = proc.stdout + proc.stderr
    with open(log, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    h = re.search(r"Initial heuristic value for \S+: (\S+)", text)
    expanded = re.search(r"Expanded (\d+) state\(s\)\.", text)
    return {
        "initial_h": h.group(1) if h else None,
        "expanded": int(expanded.group(1)) if expanded else None,
        "solved": "Solution found." in text,
        "unsolvable": "Search stopped without finding a solution" in text
                      or "Completely explored state space" in text,
        "translator_ran": "No relaxed solution!" in text,
        "returncode": proc.returncode,
    }


def main():
    os.makedirs(os.path.join(HERE, "work"), exist_ok=True)
    level = far_level(4)
    text = level.problem_text()
    domain = pddl.parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
    problem = pddl.parse_problem(text)
    task = Task.build(domain, problem)
    theorems = carve(task)
    theorem_dead = pruner(theorems)

    report = claim.coverage(4)
    states = report["_states"]
    relaxed = set(report["_relaxation_dead"])
    themdead = set(report["_theorem_dead"])

    sas_text, variables = parse_sas(os.path.join(HERE, "far4.sas"))

    # Three groups, so the answer cannot be read off one kind of state.
    groups = {
        "theorem_dead": [i for i in sorted(themdead)],
        "relaxation_dead_only": [i for i in sorted(relaxed - themdead)],
        "alive": [i for i in range(len(states)) if i not in relaxed],
    }
    picked = {}
    for name, pool in groups.items():
        step = max(1, len(pool) // 6)
        picked[name] = pool[::step][:6]

    rows = []
    for group, indices in sorted(picked.items()):
        for i in indices:
            state = states[i]
            assignment = state_to_sas(variables, state)
            sas_path = os.path.join(HERE, "work", "far4-%05d.sas" % i)
            write_sas(sas_text, sas_path, assignment)
            row = {"group": group, "state": i,
                   "python_relaxation_dead": i in relaxed,
                   "theorem_dead": i in themdead,
                   "boxes": sorted(a for a in state if a[0] == "at"),
                   "player": sorted(a for a in state if a[0] == "at-player")}
            for heuristic in ("blind", "lmcut", "ipdb"):
                row[heuristic] = run_search(sas_path, heuristic,
                                            "far4-%05d-%s" % (i, heuristic))
            rows.append(row)
            print(group, i, {h: rows[-1][h]["initial_h"] for h in
                             ("blind", "lmcut", "ipdb")}, flush=True)

    out = os.path.join(HERE, "sasprobe.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    raise SystemExit(main())
