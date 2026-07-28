"""The same batch on every rung: nodes, wall clock, optimality.

What the table is for.  The ladder was built in P-13 and connected to a real
Fast Downward, and the case for it was structural -- a bundled search that always
answers, an optimal planner when one is reachable, a satisficing one for what the
optimal rung cannot afford.  None of that is a number.  This module produces the
numbers, and the two things it is careful about are the two that would otherwise
make them worthless:

* **cross-rung node ratios are not reported.**  `stub-bfs` expands grounded
  STRIPS states and Fast Downward expands SAS+ states after its translator has
  merged mutex atoms into variables.  `fdrun.py`'s docstring works the gap out on
  the gripper fixture: 14 STRIPS facts become 5 SAS+ variables.  Dividing one by
  the other yields a large, quotable, meaningless number.
* **wall clock is reported three ways**, because on instances this size the
  interesting fact is that they disagree by three orders of magnitude: FD's
  search is microseconds, FD's process is milliseconds, and what the caller waits
  for is ~150 ms of Python driver startup.  A table with only the first would say
  Fast Downward is 1000x faster than the stub on instances where it is in fact
  slower end to end.

Optimality is checked against an oracle that is not a planner wherever one
exists: the gripper closed form, and the hand-derived sokoban lengths.  Where
none exists the rungs are checked against *each other*, which is weaker and is
labelled as such in the output (`agreement` rather than `optimum`).
"""

import json
import os
import time
from typing import Dict, List, Optional, Sequence

from bench import fdrun, instances as bench_instances
from engines import fd_adapter
from engines.fd_adapter import backends, search as fd_search

# The four configurations the table has a column for.  Two optimal ones, because
# two independent optimal planners agreeing on a length is worth more than one
# agreeing with itself -- the same reason `fuzz.py` asks for both.
CONFIGS = (
    ("stub-bfs", backends.STUB, None),
    ("fd-optimal/lmcut", backends.FD_OPTIMAL, "lmcut"),
    ("fd-optimal/ipdb", backends.FD_OPTIMAL, "ipdb"),
    ("fd-satisficing", backends.FD_SATISFICING, None),
)

# The bundled rung's budget.  Chosen so the gripper ladder runs off the end of it
# inside this batch rather than beyond it: a table where the stub never fails
# would not show where the stub stops being the right answer, which is the whole
# case for having rungs above it.
STUB_MAX_EXPANSIONS = 200000


def measure_stub(instance: bench_instances.BenchInstance, repeats: int = 3
                 ) -> Dict[str, object]:
    """The bundled rung, with the node account it already keeps.

    `search()` is called directly rather than through `solve_parsed()` because
    the account is the subject: `solve_parsed` returns it, but only after
    discarding it on every rung above this one, and calling the same function on
    every rung is what makes the timing column fair.
    """
    domain = fd_adapter.parse_domain(fd_adapter.read(instance.domain_path))
    problem = fd_adapter.parse_problem(fd_adapter.read(instance.problem_path))

    best_seconds: Optional[float] = None
    result = None
    for _ in range(repeats):
        started = time.perf_counter()
        try:
            result = fd_search.search(
                domain, problem, max_expansions=STUB_MAX_EXPANSIONS
            )
        except RuntimeError as exc:
            return {
                "config": "stub-bfs", "tier": backends.STUB,
                "solved": False, "proved_unsolvable": False,
                "plan_length": None,
                "nodes": {"expanded": None, "generated": None},
                "error": "over budget: %s" % exc,
                "timing": {"wall_seconds": None},
            }
        elapsed = time.perf_counter() - started
        best_seconds = elapsed if best_seconds is None else min(best_seconds, elapsed)

    plan_length = result.length
    if result.solved:
        # Never report a length this rig has not replayed independently.
        fd_adapter.validate_plan(
            domain, problem, [action.text() for action in result.plan]
        )
    return {
        "config": "stub-bfs",
        "tier": backends.STUB,
        "solved": result.solved,
        # BFS is complete, so an exhausted queue *is* a proof -- the same
        # standing this rig grants `astar` on the optimal rung and refuses LAMA.
        "proved_unsolvable": not result.solved,
        "plan_length": plan_length,
        "nodes": {
            "expanded": result.expansions,
            "generated": result.generated,
            "ground_actions": result.ground_actions,
        },
        "error": None,
        "timing": {"wall_seconds": round(best_seconds, 6)},
    }


def measure_fd(instance: bench_instances.BenchInstance, executable: str,
               tier: str, heuristic: Optional[str], name: str,
               repeats: int = 3, log_dir: Optional[str] = None
               ) -> Dict[str, object]:
    """One Fast Downward rung, plus the plan replayed against the rig's parser."""
    keep = None
    if log_dir:
        keep = os.path.join(log_dir, "%s.%s.log" % (instance.name, name.replace("/", "-")))
    record = fdrun.repeat(
        executable, instance.domain_path, instance.problem_path,
        tier=tier, heuristic=heuristic, repeats=repeats, keep_log=keep,
    )
    out = record.as_json()
    out["config"] = name

    if record.plan:
        domain = fd_adapter.parse_domain(fd_adapter.read(instance.domain_path))
        problem = fd_adapter.parse_problem(fd_adapter.read(instance.problem_path))
        # The point of the exercise: a plan Fast Downward produced, replayed by a
        # validator that shares no code with Fast Downward.  A rung that returned
        # a plausible-looking invalid plan would pass every other check here.
        fd_adapter.validate_plan(domain, problem, record.plan)
        out["replayed_by_rig_validator"] = True
    return out


def verdicts(instance: bench_instances.BenchInstance,
             rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Did the rungs answer what they were entitled to answer?

    Three separate questions, kept separate because they have different
    strengths:

    * `optimum_ok` -- an optimal rung's length against a **non-planner oracle**.
      Only meaningful where `instance.optimum` exists.
    * `agreement_ok` -- the optimal rungs against each other.  Weaker: two
      planners can share a bug where a closed form cannot.
    * `satisficing_ok` -- the satisficing rung is allowed to be longer, and only
      a *shorter* plan than the optimum would be a defect.
    """
    lengths = {
        row["config"]: row.get("plan_length")
        for row in rows if row.get("solved")
    }
    optimal_lengths = {
        key: value for key, value in lengths.items()
        if not key.startswith(backends.FD_SATISFICING)
    }

    optimum_ok: Optional[bool] = None
    if instance.optimum is not None and optimal_lengths:
        optimum_ok = all(value == instance.optimum for value in optimal_lengths.values())

    agreement_ok: Optional[bool] = None
    if len(optimal_lengths) > 1:
        agreement_ok = len(set(optimal_lengths.values())) == 1

    satisficing_ok: Optional[bool] = None
    reference = min(optimal_lengths.values()) if optimal_lengths else instance.optimum
    satisficing = lengths.get("fd-satisficing")
    if satisficing is not None and reference is not None:
        satisficing_ok = satisficing >= reference

    # Solvability is a claim too, and the rungs must not disagree about it.
    claims = {
        row["config"]: (
            "solved" if row.get("solved")
            else "unsolvable" if row.get("proved_unsolvable")
            else "no answer"
        )
        for row in rows
    }
    answered = {value for value in claims.values() if value != "no answer"}

    return {
        "optimum": instance.optimum,
        "optimal_rung_lengths": optimal_lengths,
        "satisficing_length": satisficing,
        "optimum_ok": optimum_ok,
        "agreement_ok": agreement_ok,
        "satisficing_ok": satisficing_ok,
        "solvability_claims": claims,
        "solvability_consistent": len(answered) <= 1,
    }


def run(out_dir: str, executable: Optional[str] = None, repeats: int = 3
        ) -> Dict[str, object]:
    """The whole table.  Returns the JSON that `LADDER.md` is rendered from."""
    executable = executable or backends.find_fast_downward()
    instance_dir = os.path.join(out_dir, "instances")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    batch = bench_instances.all_instances(instance_dir)
    results = []
    for instance in batch:
        rows: List[Dict[str, object]] = [measure_stub(instance, repeats=repeats)]
        if executable is not None:
            for name, tier, heuristic in CONFIGS[1:]:
                rows.append(
                    measure_fd(
                        instance, executable, tier, heuristic, name,
                        repeats=repeats, log_dir=log_dir,
                    )
                )
        results.append({
            "instance": instance.as_json(),
            "rungs": rows,
            "verdicts": verdicts(instance, rows),
        })

    return {
        "form": "ladder_benchmark",
        "repeats": repeats,
        "repeat_rule": "fastest of N; wall-clock noise is one-sided",
        "stub_max_expansions": STUB_MAX_EXPANSIONS,
        "fast_downward": executable,
        "configs": [name for name, _, _ in CONFIGS],
        "node_counts_are_not_comparable_across_rungs": (
            "stub-bfs expands grounded STRIPS states; Fast Downward expands SAS+ "
            "states after translation. No ratio between the two appears here."
        ),
        "results": results,
    }


def failures(report: Dict[str, object]) -> List[str]:
    """Every verdict in the report that came out False, as one line each."""
    out = []
    for entry in report["results"]:
        name = entry["instance"]["name"]
        verdict = entry["verdicts"]
        for key in ("optimum_ok", "agreement_ok", "satisficing_ok",
                    "solvability_consistent"):
            if verdict.get(key) is False:
                out.append("%s: %s is False (%s)" % (name, key, json.dumps(verdict)))
        for row in entry["rungs"]:
            if row.get("error") and "over budget" not in str(row["error"]):
                out.append("%s/%s: %s" % (name, row["config"], row["error"]))
    return out
