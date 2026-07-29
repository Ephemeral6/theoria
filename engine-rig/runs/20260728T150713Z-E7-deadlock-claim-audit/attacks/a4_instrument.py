"""Attack 4 -- is the measuring instrument sound?

Four things that could make a zero appear where there is none, and one that could
make a dividend appear where there is none:

1. **Wrong line.**  `Expanded N state(s).` versus `Expanded until last jump: N
   state(s).`  If the parser read the second, every count would be wrong.
2. **Different configurations either side.**  If the guarded run were given a
   different `--search` string than the baseline, the comparison would be
   between two planners rather than between two tasks.
3. **Baseline run against the guarded task.**  If both sides read the same
   domain file the dividend is zero by construction.
4. **Summing across searches.**  `fdrun._sum` adds every `Expanded` block in the
   log.  On a portfolio that is right; if the optimal rung printed more than one
   block it would be double counting.
5. **A dividend bought by breaking the task.**  The positive control: a
   deliberately wrong guard, to show that the checks in place would have caught
   a speed-up obtained by making the instance easier.  Both directions are
   checked -- a wrong guard that removes the solution, and one that shortens it.

Reads E2's own committed logs, not only this run's, so the numbers in DIVIDEND.md
are checked rather than re-derived.
"""

import os
import re
import sys

from lens import RIG, carve_level, executable        # noqa: E402

sys.path.insert(0, RIG)

from bench import compile_theorems, fdrun            # noqa: E402
from bench.instances import far_level                # noqa: E402
from engines.fd_adapter import backends              # noqa: E402
from fixtures import sokoban                         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work", "a4")
E2 = os.path.join(RIG, "runs", "20260728T072633Z-E2-fd-ladder-bench")

_CMD = re.compile(r"search command line string: (.*)")
_TRANSLATE = re.compile(r"translator command line string: (.*)")
_SEARCH_ARG = re.compile(r"--search '([^']*)'")


def check_logs():
    log_dir = os.path.join(E2, "logs")
    print("=== E2's own logs: what each side was actually asked ===")
    problems = 0
    for name in sorted(os.listdir(log_dir)):
        parts = name.split(".")
        if not name.endswith(".log") or len(parts) != 4:
            continue                      # the ladder's own logs have no guard part
        instance, rung, guard, _ = parts
        with open(os.path.join(log_dir, name), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        search_cmd = _CMD.search(text)
        translate_cmd = _TRANSLATE.search(text)
        config = None
        if search_cmd:
            arg = _SEARCH_ARG.search(search_cmd.group(1))
            config = arg.group(1) if arg else search_cmd.group(1)
        files = translate_cmd.group(1) if translate_cmd else ""
        guarded_domain = "guarded" in files.split("' '")[1] if "' '" in files else None
        expanded = fdrun._COUNTERS["expanded"].findall(text)
        jump = re.findall(r"Expanded until last jump: (\d+) state", text)
        row = (instance, rung, guard, config, guarded_domain, expanded, jump)
        # the four failure modes
        bad = []
        if guard == "base" and guarded_domain:
            bad.append("baseline ran against a GUARDED domain")
        if guard != "base" and guarded_domain is False:
            bad.append("guarded row ran against the PLAIN domain")
        if len(expanded) > 1 and rung.startswith("fd-optimal"):
            bad.append("optimal rung printed %d Expanded blocks (summed!)" % len(expanded))
        if expanded and jump and expanded == jump and expanded[0] != "0":
            bad.append("Expanded equals 'until last jump' -- cannot tell the lines apart")
        if bad:
            problems += 1
            print("  !! %s: %s   %s" % (name, "; ".join(bad), row))
    # configuration agreement, per (instance, rung)
    seen = {}
    for name in sorted(os.listdir(log_dir)):
        parts = name.split(".")
        if not name.endswith(".log") or len(parts) != 4:
            continue                      # the ladder's own logs have no guard part
        instance, rung, guard, _ = parts
        with open(os.path.join(log_dir, name), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        search_cmd = _CMD.search(text)
        arg = _SEARCH_ARG.search(search_cmd.group(1)) if search_cmd else None
        config = arg.group(1) if arg else ("(alias)" if search_cmd else None)
        seen.setdefault((instance, rung), {})[guard] = config
    mismatched = 0
    for key, configs in sorted(seen.items()):
        distinct = {c for c in configs.values() if c is not None}
        if len(distinct) > 1:
            mismatched += 1
            print("  !! %s compared different configurations: %s" % (key, configs))
    print("rows with a structural problem: %d" % problems)
    print("(instance,rung) pairs whose sides ran different --search: %d" % mismatched)

    # The one place the two Expanded lines differ, quoted, so the parser is
    # demonstrated to pick the right one rather than asserted to.
    path = os.path.join(log_dir, "far6.fd-optimal-lmcut.base.log")
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    print("far6/lmcut/base: Expanded=%s  'until last jump'=%s  (DIVIDEND.md quotes %s)"
          % (fdrun._COUNTERS["expanded"].findall(text),
             re.findall(r"Expanded until last jump: (\d+) state", text), 47))


def positive_control():
    """A guard that is deliberately wrong, to show the checks would catch it."""
    print()
    print("=== positive control: a guard that IS unsound ===")
    fd = executable()
    level = far_level(4)
    problem_path, domain, problem, theorems, _ = carve_level(level, WORK)
    base = fdrun.measure(fd, sokoban.DOMAIN_PATH, problem_path,
                         tier=backends.FD_OPTIMAL, heuristic="lmcut")
    print("plain far4/lmcut: expanded %s, plan length %s"
          % (base.nodes.get("expanded"), base.plan_length))

    # b1's goal is c42 on far4.  Declare it dead: strictly stronger than any
    # theorem, and wrong.
    class Fake:
        size = 1
        def __init__(self, pattern):
            self.pattern = pattern
        def rendering(self):
            return "fake"

    sabotage = list(theorems) + [Fake((("at", "b1", "c42"),))]
    gdir = os.path.join(WORK, "sabotage")
    gdom, gprob = compile_theorems.write_guarded(
        gdir, "far4sab", level.problem_text(), sabotage, guard="singleton",
        problem=problem)
    bad = fdrun.measure(fd, gdom, gprob, tier=backends.FD_OPTIMAL, heuristic="lmcut")
    print("sabotaged     : expanded %s, plan length %s, exit %d, unsolvable=%s"
          % (bad.nodes.get("expanded"), bad.plan_length, bad.returncode,
             bad.proved_unsolvable))
    print("=> a guard that buys nodes by breaking the task shows up as %s"
          % ("no plan at all" if not bad.solved else "a changed plan length"))

    # And the other direction: a guard that shortens the optimal plan would be
    # caught by dividend.failures()'s plan_length_delta clause.  Demonstrate the
    # clause fires on a length change of either sign.
    from bench.dividend import failures
    fabricated = {"results": [{
        "instance": "demo", "stub": {"plan_length_unchanged": True},
        "fd": [{"guard": "singleton", "rung": "fd-optimal/lmcut",
                "guard_refused": None, "plan_length_delta": -1,
                "guarded": {"solved": True}, "replayed_on_original_domain": True}],
    }]}
    print("failures() on a -1 length delta at fd-optimal: %s" % failures(fabricated))


if __name__ == "__main__":
    check_logs()
    positive_control()
