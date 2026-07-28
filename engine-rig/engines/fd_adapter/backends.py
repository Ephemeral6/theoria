"""The three-rung ladder: which planner answers, and what it was asked.

Theoria 1.10b asks for a ladder rather than a switch -- a bundled search that
always answers, a real optimal planner when one is reachable, and a satisficing
one for the instances the optimal rung cannot afford:

| tier              | who answers                       | length-optimal |
|-------------------|-----------------------------------|----------------|
| `stub-bfs`        | the bundled grounded-STRIPS BFS   | yes            |
| `fd-optimal`      | Fast Downward, `astar(lmcut())`   | yes            |
| `fd-satisficing`  | Fast Downward, LAMA's first pass  | no             |

Callers do not pick a rung; `choose_tier` does, by a rule written down in its
docstring and tested clause by clause.  Whichever rung answers, the Plan that
comes back has the same shape -- and says which rung it was.

Fast Downward is installed and connected (STATUS.md, "Fast Downward"), so the
two FD rungs are exercised against the real planner when `FAST_DOWNWARD` points
at one, and against a conformance script that speaks the driver's protocol when
it does not -- the suite has to stay green on a machine with no planner.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, List, Optional, Tuple

FD_ENV_VARS = ("FAST_DOWNWARD", "FAST_DOWNWARD_HOME", "DOWNWARD_ROOT")
FD_EXECUTABLES = ("fast-downward.py", "fast-downward", "downward")

STUB = "stub-bfs"
FD_OPTIMAL = "fd-optimal"
FD_SATISFICING = "fd-satisficing"
TIERS = (STUB, FD_OPTIMAL, FD_SATISFICING)

# Spellings a caller may pass as `prefer=`.  "stub" is the legacy one and every
# committed artifact in this rig depends on it, so it keeps working verbatim.
TIER_ALIASES = {
    "stub": STUB,
    "bfs": STUB,
    "fd": FD_OPTIMAL,
    "fast-downward": FD_OPTIMAL,
    "optimal": FD_OPTIMAL,
    "lama": FD_SATISFICING,
    "satisficing": FD_SATISFICING,
}

# What the optimal rung runs.  lmcut is the default because it is admissible and
# cheap enough on the instance sizes this rig produces; ipdb is selectable
# because its cost profile is the opposite (expensive to build, strong to
# search) and the differential check wants two independent optimal answers.
FD_HEURISTICS = {
    "lmcut": "astar(lmcut())",
    "ipdb": "astar(ipdb())",
    "blind": "astar(blind())",
}
FD_DEFAULT_HEURISTIC = "lmcut"
FD_SEARCH = FD_HEURISTICS[FD_DEFAULT_HEURISTIC]

# LAMA is asked for by alias, not by search string: the alias sets a whole
# portfolio's plumbing (cost transformation, preferred operators, the lot) and
# reproducing it by hand is how configurations drift.  It is a driver option, so
# it only exists behind `fast-downward.py`; a bare search binary gets the
# explicit greedy-FF configuration below, and the payload records which.
FD_SATISFICING_ALIAS = "lama-first"
FD_SATISFICING_SEARCH = "lazy_greedy([ff()], preferred=[ff()])"

# Fast Downward's driver exit codes, read off `driver/returncodes.py` in the
# build this rig installs -- not from memory, which had them one apart.
FD_TRANSLATE_UNSOLVABLE = 10
FD_SEARCH_UNSOLVABLE = 11
FD_SEARCH_UNSOLVED_INCOMPLETE = 12

# ...and then measured, which is the part that matters.  **The exit code alone
# does not tell a proof from a shrug.**  A complete `astar(blind())` that
# exhausts the reachable state space of an instance `deadlock_carver` has
# independently proved unsolvable exits **12**, not 11: `SEARCH_UNSOLVABLE` is
# reserved for the handful of algorithms that detect it structurally (EHC, the
# PDB CEGAR loop), and a plain A* that empties its open list does not use it.
# `--alias lama-first` exits 12 on the same instance.  So exit 12 covers both
# "I explored everything and there is nothing" and "I gave up", and the code is
# the same either way.
#
# What does separate them is FD's own words plus the completeness of the
# configuration *we* chose, which we know before we call it:
FD_EXHAUSTED = "Completely explored state space"     # FD's phrase for "and that was all of it"


class FastDownwardMissing(RuntimeError):
    """A named Fast Downward rung was asked for and no executable is reachable."""


def find_fast_downward() -> Optional[str]:
    """Path to a runnable Fast Downward, or None."""
    for variable in FD_ENV_VARS:
        value = os.environ.get(variable)
        if not value:
            continue
        if os.path.isfile(value) and os.access(value, os.X_OK):
            return value
        for name in FD_EXECUTABLES:
            candidate = os.path.join(value, name)
            if os.path.isfile(candidate):
                return candidate
    for name in FD_EXECUTABLES:
        found = shutil.which(name)
        if found:
            return found
    return None


def has_driver(executable: str) -> bool:
    """Is this the `fast-downward.py` driver, rather than a bare search binary?

    Only the driver understands `--alias`, so this decides whether the
    satisficing rung gets LAMA or the hand-written greedy-FF stand-in.
    """
    return os.path.basename(executable).startswith("fast-downward")


def normalise_tier(prefer: Optional[str]) -> Optional[str]:
    """A caller's `prefer=` spelling as a tier id; None means "you decide"."""
    if prefer is None:
        return None
    tier = TIER_ALIASES.get(prefer, prefer)
    if tier not in TIERS:
        raise ValueError(
            "unknown backend %r; have %s" % (prefer, ", ".join(TIERS))
        )
    return tier


def choose_tier(prefer: Optional[str] = None, on_disk: bool = True,
                prune: Optional[object] = None,
                discover: Optional[Callable[[], Optional[str]]] = None
                ) -> Tuple[str, Optional[str]]:
    """Pick a rung of the ladder, and the executable that will answer on it.

    The rule, in order.  Each clause is here because something depends on it:

    1. `prefer="stub"` forces `stub-bfs`.  Every committed artifact in this rig
       is produced on that rung, and a machine that happens to have a planner
       installed must not produce different bytes.
    2. `prefer="fd-optimal"` / `"fd-satisficing"` names a rung and is honoured.
       If no executable is reachable it raises `FastDownwardMissing` rather than
       quietly dropping to the stub -- asking for a named planner and silently
       getting another one is how a benchmark lies.  Naming an FD rung together
       with `prune=` or an in-memory instance is a contradiction, not a
       preference, and raises too.
    3. `prune=` or an instance that exists only in memory forces `stub-bfs`.
       Fast Downward reads files and has no pruning hook, so this is a fact
       about the backend rather than a choice.
    4. Otherwise: `fd-optimal` when Fast Downward is reachable, `stub-bfs` when
       it is not.  The optimal rung is the default because every acceptance
       criterion in this rig is a plan *length*, and only an optimal rung makes
       that number mean the same thing on every machine.

    `discover` is the executable lookup, injectable so the rule above can be
    tested rung by rung on a machine with no planner on it at all.

    Returns `(tier, executable)`; `executable` is None on the stub rung.
    """
    discover = discover or find_fast_downward
    tier = normalise_tier(prefer)

    if tier == STUB:
        return STUB, None
    if tier is not None:
        if prune is not None:
            raise ValueError(
                "%s cannot take a pruner; Fast Downward has no such hook" % tier
            )
        if not on_disk:
            raise ValueError("%s needs both PDDL files on disk" % tier)
        executable = discover()
        if executable is None:
            raise FastDownwardMissing(
                "%s was asked for and no Fast Downward is reachable" % tier
            )
        return tier, executable

    if prune is not None or not on_disk:
        return STUB, None
    executable = discover()
    if executable is None:
        return STUB, None
    return FD_OPTIMAL, executable


def fd_search_config(tier: str, heuristic: Optional[str] = None,
                     executable: Optional[str] = None) -> str:
    """The configuration a rung runs, verbatim, for the record in the payload.

    One definition, used both to build the command line and to fill in
    `Plan.search`, so the payload cannot claim a configuration the planner was
    not actually given.
    """
    if tier == STUB:
        return "bfs"
    if tier == FD_OPTIMAL:
        name = heuristic or FD_DEFAULT_HEURISTIC
        if name not in FD_HEURISTICS:
            raise ValueError(
                "unknown heuristic %r; have %s"
                % (name, ", ".join(sorted(FD_HEURISTICS)))
            )
        return FD_HEURISTICS[name]
    if tier == FD_SATISFICING:
        if executable is None or has_driver(executable):
            return "--alias %s" % FD_SATISFICING_ALIAS
        return FD_SATISFICING_SEARCH
    raise ValueError("unknown tier %r; have %s" % (tier, ", ".join(TIERS)))


def fd_command(executable: str, domain_path: str, problem_path: str,
               plan_path: str, tier: str = FD_OPTIMAL,
               heuristic: Optional[str] = None) -> Tuple[List[str], str]:
    """The exact argv for a rung, and the configuration string it encodes.

    `--alias` and `--plan-file` are driver options and go before the file
    arguments; `--search` is a component option and goes after them.  The driver
    is a Python script, so it is run with the interpreter that is running us
    rather than whatever `python` happens to mean on this machine's PATH.
    """
    config = fd_search_config(tier, heuristic, executable)
    by_alias = tier == FD_SATISFICING and has_driver(executable)

    command = [sys.executable, executable] if executable.endswith(".py") else [executable]
    if by_alias:
        command += ["--alias", FD_SATISFICING_ALIAS]
    command += ["--plan-file", plan_path, domain_path, problem_path]
    if not by_alias:
        command += ["--search", config]
    return command, config


def proves_unsolvable(tier: str, returncode: int, log: str) -> bool:
    """Did this run *prove* there is no plan, or merely fail to find one?

    The whole unsolvability track hangs on this one bit, so it is decided here
    rather than by string-matching at each call site, and it is decided
    conservatively -- the direction that can only ever refuse a real proof, never
    manufacture a false one.

    Three ways to a yes:

    * exit 10, `TRANSLATE_UNSOLVABLE` -- the translator's relaxed reachability
      settled it before the search ran;
    * exit 11, `SEARCH_UNSOLVABLE` -- a search that detects unsolvability
      structurally said so;
    * exit 12 **on the optimal rung, with FD reporting an exhausted state
      space**.  A* with an admissible heuristic and no cost bound is complete, so
      an empty open list is a proof; FD just does not have a distinct exit code
      for it.

    And the no that costs us something: exit 12 on the **satisficing** rung is
    refused even when the log says the space was exhausted.  LAMA is a portfolio
    whose later iterations search under a cost bound, and "exhausted under a
    bound" proves only that no *cheaper* plan exists.  Distinguishing the cases
    would mean reasoning about which iteration wrote that line; refusing costs a
    caller one re-ask on the optimal rung, and getting it wrong would mean this
    rig issuing an unsolvability claim no planner actually made.
    """
    if returncode in (FD_TRANSLATE_UNSOLVABLE, FD_SEARCH_UNSOLVABLE):
        return True
    if returncode != FD_SEARCH_UNSOLVED_INCOMPLETE:
        return False
    return tier == FD_OPTIMAL and FD_EXHAUSTED in log


def parse_sas_plan(text: str) -> List[str]:
    """Fast Downward's plan file: one `(action args)` per line, then a cost comment."""
    plan = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        plan.append(line if line.startswith("(") else "(%s)" % line)
    return plan


def plan_file_written(plan_path: str) -> Optional[str]:
    """The plan file Fast Downward actually wrote, or None.

    A single-shot configuration writes the path it was given; an anytime one
    writes `sas_plan.1`, `sas_plan.2`, ... and the last is the best it found.
    Both are looked for, so switching rungs cannot silently turn "improved on
    its own plan" into "found no plan".
    """
    if os.path.exists(plan_path):
        return plan_path
    directory = os.path.dirname(plan_path) or "."
    stem = os.path.basename(plan_path)
    numbered = []
    for name in os.listdir(directory):
        base, _, suffix = name.rpartition(".")
        if base == stem and suffix.isdigit():
            numbered.append((int(suffix), name))
    if not numbered:
        return None
    return os.path.join(directory, max(numbered)[1])


def run_fast_downward(executable: str, domain_path: str, problem_path: str,
                      tier: str = FD_OPTIMAL, heuristic: Optional[str] = None,
                      timeout: int = 120) -> Optional[List[str]]:
    """Call Fast Downward and read the plan back; `None` when there is none.

    Three outcomes, and the middle one is what this adapter used to get wrong:

    * a plan file -- the plan, parsed;
    * a *proof* that there is no plan, per `proves_unsolvable` -- an answer, so
      it comes back as `None`, exactly as the bundled search reports it;
    * anything else -- `RuntimeError`.  A search that merely failed to find a
      plan is deliberately in this bucket: from outside it looks identical (no
      plan file, and on this planner the same exit code) but it proves nothing.
      Reporting it as unsolvable would turn "I could not find one" into "there is
      none", and a probe that read the second would close a question the planner
      never answered.
    """
    with tempfile.TemporaryDirectory() as workdir:
        plan_path = os.path.join(workdir, "sas_plan")
        command, _ = fd_command(
            executable, domain_path, problem_path, plan_path, tier, heuristic
        )
        completed = subprocess.run(
            command, cwd=workdir, capture_output=True, text=True, timeout=timeout
        )
        # FD talks on stdout; the verdict is in what it said, not only in how it
        # exited, so both streams are read.
        log = (completed.stdout or "") + (completed.stderr or "")
        written = plan_file_written(plan_path)
        if written is None:
            if proves_unsolvable(tier, completed.returncode, log):
                return None
            raise RuntimeError(
                "Fast Downward produced no plan file and no proof (exit %d, rung %s): %s"
                % (completed.returncode, tier, (completed.stderr or log)[-500:])
            )
        with open(written, "r", encoding="utf-8") as fh:
            return parse_sas_plan(fh.read())
