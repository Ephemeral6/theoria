"""Run one rung of the ladder, and keep the node account it reports.

`fd_adapter.solve_parsed()` returns `SearchResult(None, 0, 0, 0, 0)` for every
Fast Downward rung -- the comment there says it outright, "FD keeps its node
account to itself".  That is the right call for the adapter, whose job is to
hand back a plan of the same shape from every rung.  It is exactly the wrong
call for a benchmark, whose entire subject is the number the adapter drops.

So this module drives the same `backends.fd_command` argv the adapter drives,
captures the log, and parses FD's own counters out of it.  It does not
re-implement the ladder: the tier rule, the search configuration and the
unsolvability verdict all come from `backends`, so a bench run cannot measure a
configuration the adapter would not actually have run.

## What the counters mean, and why they are not comparable across rungs

`stub-bfs` expands **grounded STRIPS states** -- frozensets of atoms, one node
per distinct set.  Fast Downward expands **SAS+ states** -- assignments to the
finite-domain variables its translator invents, after that translator has merged
mutually exclusive atoms into single variables and discarded unreachable ones.
On the gripper instance below, 14 STRIPS facts become 5 SAS+ variables.

The two numbers therefore answer different questions and **a ratio between them
is not a speed-up**.  What is comparable across rungs, and what this bench
actually compares:

* **plan length** -- the acceptance criterion in this rig, and unit-cost
  length-optimality means the same thing under BFS and under A*;
* **wall clock** -- what a caller pays, in seconds, which is the same second on
  every rung;
* **node counts within a rung** -- blind versus pruned on `stub-bfs`, lmcut
  versus ipdb versus lama on FD.

Cross-rung node ratios appear nowhere in the artifacts.  They would be the most
quotable number here and they would mean nothing.
"""

import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from engines.fd_adapter import backends

# Everything the *search* component prints carries a `[t=0.0025s, 2776 KB] `
# progress stamp; everything the *translator* prints does not.  One optional
# prefix covers both, and anchoring at `^` still keeps the counters from matching
# a substring of some other line.
_STAMP = r"^(?:\[t=[^\]]*\]\s*)?"

# FD's search summary, as printed by `search_statistics`.  Every one of these is
# cumulative over a single search; a portfolio that runs several searches prints
# the block several times, which is why they are summed rather than overwritten.
#
# `state\(s\)\.` is load-bearing on two of them: the translator also prints
# `Generated 17 rules.`, and the search prints `Expanded until last jump: 0
# state(s).`  Requiring the digits immediately after the verb, and the word
# `state`, excludes both.
_COUNTERS = {
    "expanded": re.compile(_STAMP + r"Expanded (\d+) state\(s\)\.", re.M),
    "generated": re.compile(_STAMP + r"Generated (\d+) state\(s\)\.", re.M),
    "evaluated": re.compile(_STAMP + r"Evaluated (\d+) state\(s\)\.", re.M),
    "reopened": re.compile(_STAMP + r"Reopened (\d+) state\(s\)\.", re.M),
    "dead_ends": re.compile(_STAMP + r"Dead ends: (\d+) state\(s\)\.", re.M),
}

# The translator's account of the task it handed the search.  This is where the
# STRIPS-versus-SAS+ gap above becomes visible rather than assumed.
_TRANSLATOR = {
    "variables": re.compile(r"^Translator variables: (\d+)", re.M),
    "facts": re.compile(r"^Translator facts: (\d+)", re.M),
    "operators": re.compile(r"^Translator operators: (\d+)", re.M),
    "mutex_groups": re.compile(r"^Translator mutex groups: (\d+)", re.M),
    "task_size": re.compile(r"^Translator task size: (\d+)", re.M),
}

_SEARCH_TIME = re.compile(_STAMP + r"Search time: ([\d.]+)s", re.M)
_TOTAL_TIME = re.compile(_STAMP + r"Total time: ([\d.]+)s", re.M)
_INITIAL_H = re.compile(_STAMP + r"Initial heuristic value for (\S+): (\S+)", re.M)
_PLAN_LENGTH = re.compile(_STAMP + r"Plan length: (\d+) step\(s\)\.", re.M)
_PLAN_COST = re.compile(_STAMP + r"Plan cost: (\d+)", re.M)
_PEAK_MEMORY = re.compile(_STAMP + r"Peak memory: (\d+) KB", re.M)


def _sum(pattern: re.Pattern, log: str) -> Optional[int]:
    found = pattern.findall(log)
    return sum(int(x) for x in found) if found else None


def _last(pattern: re.Pattern, log: str, cast=float):
    found = pattern.findall(log)
    return cast(found[-1]) if found else None


@dataclass
class FdMeasurement:
    """One Fast Downward invocation: what it answered and what it cost.

    `solved` / `proved_unsolvable` are deliberately three-valued together: a run
    can find a plan, prove there is none, or do neither, and the third case is a
    failure of the run rather than a property of the instance.  Collapsing it
    into `solved=False` is the mistake `backends.proves_unsolvable` exists to
    prevent, so this record does not re-make it one layer up.
    """

    tier: str
    config: str
    heuristic: Optional[str] = None
    returncode: int = 0
    solved: bool = False
    proved_unsolvable: bool = False
    # A fourth outcome, and it is neither an answer nor a fault: the run
    # exhausted its space and said so, on a rung this rig does not allow to
    # conclude unsolvability from that.  `backends.proves_unsolvable` refuses
    # exit 12 on the satisficing rung because LAMA's later iterations search
    # under a cost bound, where "exhausted" means "no cheaper plan", not "no
    # plan".  Recording it as an error would put a policy decision in the column
    # headed "the planner fell over".
    not_entitled: bool = False
    plan: Optional[List[str]] = None
    plan_length: Optional[int] = None
    plan_cost: Optional[int] = None
    # FD's own counters -- SAS+ states, not STRIPS states.  See the module docstring.
    nodes: Dict[str, Optional[int]] = field(default_factory=dict)
    translator: Dict[str, Optional[int]] = field(default_factory=dict)
    initial_h: Optional[str] = None
    peak_memory_kb: Optional[int] = None
    # Three clocks, because they answer three different questions: what FD's
    # search cost, what FD's process cost, and what the caller waited for.  On
    # instances this small the third is dominated by the driver's Python startup
    # and is the only one a caller can actually feel.
    search_seconds: Optional[float] = None
    fd_total_seconds: Optional[float] = None
    wall_seconds: float = 0.0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        """The run did what this rung is allowed to do. `not_entitled` counts."""
        return self.error is None

    def structural(self) -> Dict[str, object]:
        """The half that is a function of the instance, not of the afternoon."""
        return {
            "tier": self.tier,
            "config": self.config,
            "heuristic": self.heuristic,
            "returncode": self.returncode,
            "solved": self.solved,
            "proved_unsolvable": self.proved_unsolvable,
            "not_entitled": self.not_entitled,
            "plan_length": self.plan_length,
            "plan_cost": self.plan_cost,
            "nodes": dict(self.nodes),
            "translator": dict(self.translator),
            "initial_h": self.initial_h,
            "error": self.error,
        }

    def timing(self) -> Dict[str, object]:
        """The half that is not.  Never checked for equality by `verify.py`."""
        return {
            "search_seconds": self.search_seconds,
            "fd_total_seconds": self.fd_total_seconds,
            "wall_seconds": round(self.wall_seconds, 6),
            "peak_memory_kb": self.peak_memory_kb,
        }

    def as_json(self) -> Dict[str, object]:
        out = self.structural()
        out["timing"] = self.timing()
        if self.plan is not None:
            out["plan"] = list(self.plan)
        return out


def measure(executable: str, domain_path: str, problem_path: str,
            tier: str = backends.FD_OPTIMAL, heuristic: Optional[str] = None,
            timeout: int = 300, keep_log: Optional[str] = None) -> FdMeasurement:
    """One rung, one instance, one measurement.

    The argv comes from `backends.fd_command` and the unsolvability verdict from
    `backends.proves_unsolvable`, so this measures the adapter's behaviour rather
    than a lookalike of it.

    `keep_log` writes FD's raw output next to the artifacts.  A parsed counter
    with no log behind it is a number nobody can check, and this run is going to
    be quoted.
    """
    with tempfile.TemporaryDirectory() as workdir:
        plan_path = os.path.join(workdir, "sas_plan")
        command, config = backends.fd_command(
            executable, domain_path, problem_path, plan_path, tier, heuristic
        )
        return _invoke(command, config, tier, heuristic, workdir, plan_path,
                       timeout, keep_log)


def measure_search(executable: str, domain_path: str, problem_path: str,
                   search: str, timeout: int = 300,
                   keep_log: Optional[str] = None) -> FdMeasurement:
    """One instance under a **verbatim** `--search` string.

    Everything else in this module goes through `backends.fd_command`, on the
    rule stated in the module docstring: a bench must not be able to measure a
    configuration the adapter would never run.  This function is the one
    deliberate exception, and the reason is the same reason `fd-optimal/blind`
    is in `dividend.py`'s rung list -- it is a **control**, not a rung.

    What it exists for is E2's gap G7.  `astar(blind())`'s expansion count is a
    function of FD's f-tie-break as well as of the instance: an adversarial
    review of that run found `far5`'s baseline moving 958 -> 1479 (+54%) under a
    different open list, while the dividend *ratios* barely moved.  Measuring
    that needs two open lists, and `backends` has vocabulary for exactly one --
    `FD_HEURISTICS` names heuristics, not tie-breaks.  The alternative was to
    teach the adapter a tie-break parameter that no caller of the adapter wants,
    which is a benchmark editing the thing it benchmarks.

    So the argv is built here, in the same shape `fd_command` builds it (driver
    options before the files, `--search` after), and every configuration handed
    to it is recorded verbatim in the artifact beside its numbers.  Each one is
    an optimal, complete search, so `backends.proves_unsolvable`'s optimal-rung
    reading of exit 12 is the right one and is reused unchanged.
    """
    with tempfile.TemporaryDirectory() as workdir:
        plan_path = os.path.join(workdir, "sas_plan")
        command = ([sys.executable, executable] if executable.endswith(".py")
                   else [executable])
        command += ["--plan-file", plan_path, domain_path, problem_path,
                    "--search", search]
        return _invoke(command, search, backends.FD_OPTIMAL, None, workdir,
                       plan_path, timeout, keep_log)


def _invoke(command: List[str], config: str, tier: str,
            heuristic: Optional[str], workdir: str, plan_path: str,
            timeout: int, keep_log: Optional[str]) -> FdMeasurement:
    """Run one already-built argv and parse what it printed.

    Split out of `measure()` so that `measure_search()` can reuse the log
    parsing and the outcome classification verbatim rather than growing a second
    copy of them that could drift.  Nothing about the parsing depends on how the
    argv was built.
    """
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command, cwd=workdir, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return FdMeasurement(
            tier=tier, config=config, heuristic=heuristic,
            wall_seconds=time.perf_counter() - started,
            error="timeout after %ds" % timeout,
        )
    wall = time.perf_counter() - started
    log = (completed.stdout or "") + (completed.stderr or "")

    if keep_log:
        os.makedirs(os.path.dirname(keep_log) or ".", exist_ok=True)
        with open(keep_log, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(log)

    record = FdMeasurement(
        tier=tier, config=config, heuristic=heuristic,
        returncode=completed.returncode, wall_seconds=wall,
        nodes={key: _sum(pattern, log) for key, pattern in _COUNTERS.items()},
        translator={key: _sum(pattern, log) for key, pattern in _TRANSLATOR.items()},
        search_seconds=_last(_SEARCH_TIME, log),
        fd_total_seconds=_last(_TOTAL_TIME, log),
        peak_memory_kb=_last(_PEAK_MEMORY, log, int),
        plan_length=_last(_PLAN_LENGTH, log, int),
        plan_cost=_last(_PLAN_COST, log, int),
    )
    initial = _INITIAL_H.findall(log)
    if initial:
        record.initial_h = "%s=%s" % initial[-1]

    written = backends.plan_file_written(plan_path)
    if written is not None:
        with open(written, "r", encoding="utf-8") as fh:
            record.plan = backends.parse_sas_plan(fh.read())
        record.solved = True
        # Trust the plan file over the log line: an anytime configuration
        # prints one `Plan length` per improvement and the file is the last.
        record.plan_length = len(record.plan)
    elif backends.proves_unsolvable(tier, completed.returncode, log):
        record.proved_unsolvable = True
    elif (completed.returncode == backends.FD_SEARCH_UNSOLVED_INCOMPLETE
          and backends.FD_EXHAUSTED in log):
        # It emptied its open list and said so, but on this rung that is not
        # a proof this rig will accept.  See `not_entitled` above.
        record.not_entitled = True
    else:
        record.error = (
            "no plan file and no proof (exit %d, rung %s): %s"
            % (completed.returncode, tier, log[-300:])
        )
    return record


def repeat(executable: str, domain_path: str, problem_path: str,
           tier: str = backends.FD_OPTIMAL, heuristic: Optional[str] = None,
           repeats: int = 3, timeout: int = 300,
           keep_log: Optional[str] = None) -> FdMeasurement:
    """Measure `repeats` times and keep the fastest.

    The minimum, not the mean: the noise on a wall clock is one-sided -- another
    process can only ever steal time, never give it back -- so the fastest run is
    the closest thing to the cost of the work itself.  The structural half is
    identical across repeats by construction, and `ladder.py` asserts that rather
    than assuming it.
    """
    best: Optional[FdMeasurement] = None
    for index in range(repeats):
        record = measure(
            executable, domain_path, problem_path, tier, heuristic, timeout,
            keep_log=keep_log if index == 0 else None,
        )
        if record.error is not None:
            return record
        if best is None or record.wall_seconds < best.wall_seconds:
            best = record
    return best              # repeats >= 1, so this is never None in practice


def bfs_seconds(domain, problem, prune=None, repeats: int = 3,
                max_expansions: int = 500000) -> float:
    """The same fastest-of-N clock for the bundled rung, so the two are fair.

    Imported here rather than in `search.py` because timing is a benchmark's
    business: the engine must not grow a stopwatch just because something wanted
    to time it.
    """
    from engines.fd_adapter import search as fd_search

    best = None
    for _ in range(repeats):
        started = time.perf_counter()
        fd_search.search(domain, problem, prune=prune, max_expansions=max_expansions)
        elapsed = time.perf_counter() - started
        best = elapsed if best is None or elapsed < best else best
    return best
