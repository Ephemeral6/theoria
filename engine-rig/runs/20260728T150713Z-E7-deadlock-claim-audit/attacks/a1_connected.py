"""Attack 1 -- is the guard actually connected, or a no-op for lmcut/ipdb?

Three independent checks, none of which trusts the other:

1. **The rig's own grounder** on the plain domain versus the singleton-guarded
   one, same problem.  Lists the ground `push` instances that exist in one and
   not the other, by name.
2. **Fast Downward's translator**, same pair, reporting its own operator count
   and its own ground operator names out of `output.sas`.  If the compilation
   were a no-op these two numbers would be equal.
3. **A decisive transition.**  A one-push problem whose goal *is* the dead
   corner, carrying far6's guard facts.  The plain domain finds a 1-step plan;
   the guarded domain must find none.  That is the transition, named, on the
   command line.

Check 3's guard facts are far6's -- the carver would not prove that corner dead
on an instance whose goal is that corner, and it must not be asked to.  What
check 3 establishes is that the *compilation* has teeth, which is exactly the
question; the carver's soundness is a different module's and is checked
elsewhere.
"""

import os
import subprocess
import sys

from lens import (RIG, carve_level, executable)      # noqa: E402

sys.path.insert(0, RIG)

from bench import compile_theorems                   # noqa: E402
from bench.instances import far_level                # noqa: E402
from engines import fd_adapter                       # noqa: E402
from engines.fd_adapter.pddl import ground_actions   # noqa: E402
from fixtures import sokoban                         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work", "a1")


def sas_operators(fd: str, domain_path: str, problem_path: str, tag: str):
    """Fast Downward's own ground operator names, from its own output.sas."""
    workdir = os.path.join(WORK, "sas-%s" % tag)
    os.makedirs(workdir, exist_ok=True)
    completed = subprocess.run(
        [sys.executable, fd, "--translate", domain_path, problem_path],
        cwd=workdir, capture_output=True, text=True, timeout=600,
    )
    sas = os.path.join(workdir, "output.sas")
    names = []
    with open(sas, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for index, line in enumerate(lines):
        if line == "begin_operator":
            names.append(lines[index + 1])
    return names, completed.stdout


def main():
    fd = executable()
    level = far_level(6)
    problem_path, domain, problem, theorems, _ = carve_level(level, WORK)
    gdir = os.path.join(WORK, "singleton")
    gdom, gprob = compile_theorems.write_guarded(
        gdir, level.name, level.problem_text(), theorems, guard="singleton",
        problem=problem,
    )

    print("=== 1. the rig's own grounder ===")
    guard_domain = fd_adapter.parse_domain(fd_adapter.read(gdom))
    guard_problem = fd_adapter.parse_problem(fd_adapter.read(gprob))
    plain = {a.text() for a in ground_actions(domain, problem)}
    guarded = {a.text() for a in ground_actions(guard_domain, guard_problem)}
    print("plain ground actions   : %d" % len(plain))
    print("guarded ground actions : %d" % len(guarded))
    removed = sorted(plain - guarded)
    added = sorted(guarded - plain)
    print("removed by the guard   : %d" % len(removed))
    for name in removed:
        print("    - %s" % name)
    print("added by the guard     : %d %s" % (len(added), added[:5]))

    print()
    print("=== 2. Fast Downward's translator ===")
    plain_ops, plain_log = sas_operators(fd, sokoban.DOMAIN_PATH, problem_path, "plain")
    guard_ops, guard_log = sas_operators(fd, gdom, gprob, "singleton")
    print("plain   FD operators: %d" % len(plain_ops))
    print("guarded FD operators: %d" % len(guard_ops))
    gone = sorted(set(plain_ops) - set(guard_ops))
    print("gone from the SAS+ task: %d" % len(gone))
    for name in gone:
        print("    - %s" % name)

    print()
    print("=== 3. the decisive transition ===")
    # A corner the guard calls dead for b1 on far6.  Build a one-push problem
    # that asks for exactly that transition.
    dead1 = [t for t in theorems if t.size == 1]
    (_, box, cell), = dead1[0].pattern
    print("guard fact under test : (dead1 %s %s)" % (box, cell))
    row, col = int(cell[1]), int(cell[2])
    # Push direction: from the neighbour towards the corner.
    for direction, (dr, dc) in sokoban.DELTA.items():
        source = (row - dr, col - dc)
        pusher = (row - 2 * dr, col - 2 * dc)
        if level.is_floor(source) and level.is_floor(pusher):
            break
    else:                                             # pragma: no cover
        raise SystemExit("no push into %s on this board" % cell)
    print("push %s: player %s, box %s -> %s" % (direction, pusher, source, (row, col)))

    probe = sokoban.Level(
        name="cornerprobe", grid=level.grid, player=pusher,
        boxes=((box, source), ("b2", (3, 4))),
        goals=((box, (row, col)), ("b2", (3, 4))),
        optimum=1, path="",
    )
    probe_dir = os.path.join(WORK, "probe")
    os.makedirs(probe_dir, exist_ok=True)
    probe_plain = os.path.join(probe_dir, "cornerprobe.pddl")
    with open(probe_plain, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(probe.problem_text())
    # far6's theorems, spliced into the probe problem -- same objects, same board.
    probe_guarded = os.path.join(probe_dir, "cornerprobe_guarded_singleton.pddl")
    with open(probe_guarded, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(compile_theorems.guarded_problem_text(
            probe.problem_text(), theorems, "singleton", probe_problem(probe_plain)))

    for tag, dom, prob in (("plain", sokoban.DOMAIN_PATH, probe_plain),
                           ("guarded", gdom, probe_guarded)):
        outdir = os.path.join(probe_dir, tag)
        os.makedirs(outdir, exist_ok=True)
        completed = subprocess.run(
            [sys.executable, fd, "--plan-file", os.path.join(outdir, "sas_plan"),
             dom, prob, "--search", "astar(lmcut())"],
            cwd=outdir, capture_output=True, text=True, timeout=600,
        )
        log = completed.stdout + completed.stderr
        plan_path = os.path.join(outdir, "sas_plan")
        plan = open(plan_path).read().strip() if os.path.exists(plan_path) else "(no plan file)"
        print("--- %s: exit %d" % (tag, completed.returncode))
        for line in log.splitlines():
            if ("Solution found" in line or "unsolvable" in line.lower()
                    or "Expanded " in line or "Plan length" in line
                    or "Completely explored" in line):
                print("    %s" % line.strip())
        print("    plan: %s" % plan.replace("\n", " | "))


def probe_problem(path):
    return fd_adapter.parse_problem(fd_adapter.read(path))


if __name__ == "__main__":
    main()
