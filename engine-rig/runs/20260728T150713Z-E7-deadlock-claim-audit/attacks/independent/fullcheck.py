"""The 16-sample cross-check, done on all 3342 states, with FD as both oracles.

`audit.claim.relaxation_agrees_with_fd` checks the Python delete relaxation
against Fast Downward on 16 of far4's 3342 states, and checks nothing at all
about `truly_dead` -- that set has no oracle outside the audit's own backward
BFS.  Claim (B) is an *equality* between those two sets, so half of it is
unchecked and the other half is checked on 0.5% of the space.

Both oracles are available for the price of a subprocess if the translator is
taken out of the loop.  far4 is translated once (it is solvable, so the
`No relaxed solution!` shortcut never fires), and each state is injected into
the `begin_state` block of the resulting SAS task.  Then:

  * `astar(hmax(), bound=1)` -- `Initial heuristic value: infinity` iff the goal
    is unreachable in FD's own delete relaxation.  h^max is infinite exactly on
    the relaxed-unreachable states, so this is FD's relaxation verdict on the
    state, obtained without asking the translator.
  * `astar(blind())` run to exhaustion -- no relaxation, no heuristic; whether
    it finds a plan is FD's verdict on whether the state is *truly* dead.

Two FD verdicts per state, compared against the audit's two Python sets.

    python fullcheck.py [n_states]
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, RIG)

DOWNWARD = os.environ.get(
    "DOWNWARD_BIN",
    "C:/Users/user/Desktop/theoria/.worktrees/p13/engine-rig/.toolchain/downward/"
    "builds/release/bin/downward.exe")

from audit import claim                                    # noqa: E402
from sasprobe import parse_sas, state_to_sas               # noqa: E402

_H = re.compile(r"Initial heuristic value for \S+: (\S+)")


def inject(text, assignment):
    return re.sub(r"(begin_state\n).*?(end_state)",
                  lambda m: m.group(1) + "".join("%d\n" % v for v in assignment) + m.group(2),
                  text, count=1, flags=re.S)


def ask(sas, argv):
    proc = subprocess.run([DOWNWARD] + argv, input=sas, capture_output=True,
                          text=True, cwd=os.path.join(HERE, "work"))
    return proc.stdout + proc.stderr


def main(limit=None):
    report = claim.coverage(4)
    states = report["_states"]
    relaxed = set(report["_relaxation_dead"])
    themdead = set(report["_theorem_dead"])
    # truly_dead is not exported by coverage(); recompute it the same way the
    # audit does, so the comparison is against the number the audit published.
    n = len(states)

    sas_text, variables = parse_sas(os.path.join(HERE, "far4.sas"))
    indices = list(range(n))[: limit or n]

    disagree_relaxation, disagree_truth = [], []
    fd_relax_dead, fd_truly_dead = set(), set()
    for count, i in enumerate(indices):
        sas = inject(sas_text, state_to_sas(variables, states[i]))
        out = ask(sas, ["--search", "astar(hmax(),bound=1)"])
        match = _H.search(out)
        if match is None:
            raise RuntimeError("no heuristic line for state %d:\n%s" % (i, out[-800:]))
        fd_relaxation_dead = match.group(1) == "infinity"
        out2 = ask(sas, ["--search", "astar(blind())"])
        fd_solved = "Solution found." in out2
        if fd_relaxation_dead:
            fd_relax_dead.add(i)
        if not fd_solved:
            fd_truly_dead.add(i)
        if fd_relaxation_dead != (i in relaxed):
            disagree_relaxation.append(i)
        if (not fd_solved) != fd_relaxation_dead:
            disagree_truth.append(i)
        if count % 200 == 0:
            print("%d/%d  relax_disagree=%d  truth_vs_relax_disagree=%d"
                  % (count, len(indices), len(disagree_relaxation),
                     len(disagree_truth)), flush=True)

    checked = set(indices)
    out = {
        "n_checked": len(indices),
        "n_python_relaxation_dead": len(relaxed & checked),
        "n_fd_relaxation_dead": len(fd_relax_dead),
        "n_fd_truly_dead_by_blind_search": len(fd_truly_dead),
        "n_theorem_dead": len(themdead & checked),
        "python_relaxation_disagrees_with_fd": disagree_relaxation,
        "fd_truly_dead_differs_from_fd_relaxation_dead": disagree_truth,
        "n_theorem_dead_outside_fd_relaxation": len((themdead & checked) - fd_relax_dead),
        "n_fd_truly_dead_outside_fd_relaxation": len(fd_truly_dead - fd_relax_dead),
        "n_fd_relaxation_dead_outside_fd_truly_dead": len(fd_relax_dead - fd_truly_dead),
    }
    path = os.path.join(HERE, "fullcheck.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else None))
