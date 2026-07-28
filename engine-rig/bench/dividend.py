"""What a proved deadlock is worth, on each rung that can be told about one.

Theoria 1.9: *每证一个死锁，规划器同时提速* -- every deadlock proved, the planner
speeds up at the same time.  That is a claim about numbers and it has never had
any.  `deadlock_carver.pruning_report` already solves twice and compares, so the
machinery exists; what did not exist is a measurement across instance sizes, and
across the rungs of the ladder rather than only the one with a pruning hook.

Three questions, and they do not have the same answer:

1. **The bundled rung**, which takes a `prune` callable.  Blind versus pruned,
   same instance, same search.  This is `pruning_report`, run over a size ladder
   instead of one board.

2. **The optimal rung**, which has no pruning hook -- so the theorems are
   compiled into the task instead (`compile_theorems.py`).  The comparison is the
   same task with and without the guard.

3. **The satisficing rung**, same compilation.  Its numbers need a warning the
   other two do not: LAMA is not length-optimal, so it can expand fewer nodes
   *and return a worse plan*, and that is not a speed-up.  `plan_length_delta` is
   reported beside every satisficing row for exactly that reason, and
   `dividend_is_honest` is False wherever the plan got longer.

## What counts as the dividend, and what does not

Expansions, on the same rung, on the same instance, with the plan unchanged.
That last clause is the soundness check and it is not decorative: an unsound
theorem shows up here as a shorter plan or a lost solution, which is why the
comparison is always run to completion rather than stopped once the numbers look
good.  Wall clock is recorded too and is the weaker number -- on instances this
small it is dominated by the carving itself, which is reported separately so that
"the search expanded fewer nodes" and "the run finished sooner" cannot be quietly
merged.
"""

import os
import time
from typing import Dict, List, Optional, Sequence

from bench import compile_theorems, fdrun, instances as bench_instances
from engines import deadlock_carver as dc
from engines import fd_adapter
from engines.fd_adapter import backends
from fixtures import sokoban

# Board sizes for the solvable ladder and the unsolvable one.  Both use a
# construction that already exists in `fixtures/sokoban.py`, extended by size
# only, so the shape of the theorems is held constant while the board grows.
FAR_SIDES = (4, 5, 6, 7)
RING_SIDES = (4, 5, 6, 7, 8)


def ring_level(side: int) -> sokoban.Level:
    """`ringstuck`, generalised: a 1-wide corridor loop, box asked off it.

    At `side=4` this is `fixtures.sokoban.RING_STUCK` exactly -- the corridor
    ring, the box on (1,2), the goal on (3,1) -- which
    `tests/test_bench_instances.py` checks rather than assumes.

    The instance is unsolvable, and unsolvable for the reason the fixture's own
    comment gives: turning a box out of a 1-wide corridor needs the player beside
    it and a 1-wide corridor has no beside.  It is the case where a deadlock
    theorem should pay most, because proving "no plan" means exhausting the space
    and a large part of that space is dead.
    """
    if side < 4:
        raise ValueError("side %d leaves no ring" % side)
    grid = ["#" * (side + 2)]
    for row in range(1, side + 1):
        cells = [
            "." if (row in (1, side) or col in (1, side)) else "#"
            for col in range(1, side + 1)
        ]
        grid.append("#" + "".join(cells) + "#")
    grid.append("#" * (side + 2))
    return sokoban.Level(
        name="ringstuck%d" % side,
        grid=tuple(grid),
        player=(1, 1),
        boxes=(("b1", (1, 2)),),
        goals=(("b1", (side - 1, 1)),),
        optimum=None,
        path="",
    )


def _write(directory: str, level: sokoban.Level) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "%s.pddl" % level.name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(level.problem_text())
    return path


def stub_dividend(domain, problem, theorems, repeats: int = 3,
                  max_expansions: int = 400000) -> Dict[str, object]:
    """Blind versus pruned on the rung that takes a pruner.

    The node account comes from `deadlock_carver.pruning_report` -- the engine's
    own comparison, not a reimplementation of it, so a bench that disagreed with
    the engine would be a bug in one of them rather than a difference of opinion.
    Only the clock is added here.
    """
    report = dc.pruning_report(domain, problem, theorems, max_expansions=max_expansions)
    blind = fdrun.bfs_seconds(domain, problem, prune=None, repeats=repeats,
                              max_expansions=max_expansions)
    pruner = dc.pruner(theorems)
    with_theorems = fdrun.bfs_seconds(domain, problem, prune=pruner, repeats=repeats,
                                      max_expansions=max_expansions)
    out = report.as_json()
    out["timing"] = {
        "blind_seconds": round(blind, 6),
        "pruned_seconds": round(with_theorems, 6),
        # Below 1.0 means the pruned search finished sooner.  It is a weaker
        # number than the expansion ratio and is not the headline: the pruner is
        # a Python callable invoked per generated state, so it can easily cost
        # more per node than the nodes it removes are worth.
        "seconds_ratio": round(with_theorems / blind, 4) if blind else None,
    }
    out["dividend_is_honest"] = report.same_answer
    return out


def fd_dividend(problem_text: str, problem_path: str, domain, problem,
                theorems, executable: str, work_dir: str, name: str,
                repeats: int = 3, log_dir: Optional[str] = None
                ) -> List[Dict[str, object]]:
    """The same question on the rungs that have no pruning hook.

    Each row is one (guard, rung) pair against that rung's own unguarded
    baseline.  The baseline is measured per rung and never borrowed across rungs:
    `fd-optimal` and `fd-satisficing` explore different spaces, and subtracting
    one's expansions from the other's would produce a dividend nobody earned.
    """
    rows: List[Dict[str, object]] = []
    rungs = (
        # A diagnostic configuration, not a rung of the ladder: `choose_tier`
        # never selects it.  It is here because it is the *control*.  A* with a
        # zero heuristic is the bundled BFS in different clothes, so it isolates
        # what the theorems are worth to a search with no other way of knowing a
        # region is dead -- and that is the only way to tell "the theorems do
        # nothing" from "the heuristic already did it".  `tools/p13_fd_dividend.py`
        # measured on this configuration and only this one; running it here is
        # what makes the two results comparable instead of contradictory.
        ("fd-optimal/blind", backends.FD_OPTIMAL, "blind"),
        ("fd-optimal/lmcut", backends.FD_OPTIMAL, "lmcut"),
        ("fd-optimal/ipdb", backends.FD_OPTIMAL, "ipdb"),
        ("fd-satisficing", backends.FD_SATISFICING, None),
    )

    baselines = {}
    for rung, tier, heuristic in rungs:
        keep = os.path.join(log_dir, "%s.%s.base.log" % (name, rung.replace("/", "-"))) \
            if log_dir else None
        baselines[rung] = fdrun.repeat(
            executable, sokoban.DOMAIN_PATH, problem_path,
            tier=tier, heuristic=heuristic, repeats=repeats, keep_log=keep,
        )

    for guard in ("singleton", "full"):
        guard_domain, guard_problem = compile_theorems.write_guarded(
            work_dir, name, problem_text, theorems, guard=guard
        )
        size = compile_theorems.guard_size(theorems, guard)
        for rung, tier, heuristic in rungs:
            keep = os.path.join(
                log_dir, "%s.%s.%s.log" % (name, rung.replace("/", "-"), guard)
            ) if log_dir else None
            guarded = fdrun.repeat(
                executable, guard_domain, guard_problem,
                tier=tier, heuristic=heuristic, repeats=repeats, keep_log=keep,
            )
            base = baselines[rung]

            replayed = None
            if guarded.plan:
                # The safety net compile_theorems.py promises: a plan produced
                # from the guarded task, replayed against the ORIGINAL domain by
                # the rig's own validator.  A guard that removed a transition it
                # had no right to remove cannot survive this.
                fd_adapter.validate_plan(domain, problem, guarded.plan)
                replayed = True

            length_delta = None
            if base.plan_length is not None and guarded.plan_length is not None:
                length_delta = guarded.plan_length - base.plan_length

            rows.append({
                "instance": name,
                "guard": guard,
                "rung": rung,
                "guard_size": size,
                "baseline": base.structural(),
                "guarded": guarded.structural(),
                "expansions_before": base.nodes.get("expanded"),
                "expansions_after": guarded.nodes.get("expanded"),
                "task_size_before": base.translator.get("task_size"),
                "task_size_after": guarded.translator.get("task_size"),
                "plan_length_delta": length_delta,
                "replayed_on_original_domain": replayed,
                "guard_refused": guarded.error,
                # False when the guard bought nodes by returning a worse plan.
                # Only the satisficing rung can do this, and it does.  None --
                # not False -- when there is no plan on either side to compare,
                # which is every row on the unsolvable ladder: nobody claimed a
                # dividend there, so there is nothing to call dishonest.
                "dividend_is_honest": (
                    None if (guarded.error or length_delta is None)
                    else length_delta <= 0
                ),
                "timing": {
                    "baseline": base.timing(),
                    "guarded": guarded.timing(),
                },
            })
    return rows


def run(out_dir: str, executable: Optional[str] = None, repeats: int = 3
        ) -> Dict[str, object]:
    """Both ladders, all three questions."""
    executable = executable or backends.find_fast_downward()
    work_dir = os.path.join(out_dir, "guarded")
    instance_dir = os.path.join(out_dir, "instances")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    domain = fd_adapter.parse_domain(fd_adapter.read(sokoban.DOMAIN_PATH))
    families = [
        ("solvable", [bench_instances.far_level(side) for side in FAR_SIDES]),
        ("unsolvable", [ring_level(side) for side in RING_SIDES]),
    ]

    entries = []
    for family, levels in families:
        for level in levels:
            problem_path = _write(instance_dir, level)
            problem = fd_adapter.parse_problem(fd_adapter.read(problem_path))

            started = time.perf_counter()
            task = dc.Task.build(domain, problem)
            theorems = dc.carve(task)
            carve_seconds = time.perf_counter() - started
            compile_theorems.guardable(domain, theorems)

            entry = {
                "instance": level.name,
                "family": family,
                "cells": len(level.floors()),
                "boxes": len(level.boxes),
                "n_theorems": len(theorems),
                "n_singleton_theorems": sum(1 for t in theorems if t.size == 1),
                "n_pair_theorems": sum(1 for t in theorems if t.size == 2),
                # Carving is not free and the ladder above does not pay it. A
                # dividend quoted without it is a saving with the invoice torn off.
                "carve_seconds": round(carve_seconds, 6),
                "stub": stub_dividend(domain, problem, theorems, repeats=repeats),
                "fd": [],
            }
            if executable is not None:
                entry["fd"] = fd_dividend(
                    level.problem_text(), problem_path, domain, problem, theorems,
                    executable, work_dir, level.name, repeats=repeats, log_dir=log_dir,
                )
            entries.append(entry)

    return {
        "form": "deadlock_dividend",
        "claim_under_test": (
            "Theoria 1.9: every deadlock proved, the planner speeds up at the "
            "same time"
        ),
        "repeats": repeats,
        "fast_downward": executable,
        "results": entries,
    }


def failures(report: Dict[str, object]) -> List[str]:
    """Soundness violations only.

    A dividend of zero is a finding, not a failure -- the point of measuring was
    that it might be zero.  What is a failure is an **optimal** answer changing:
    that would mean a theorem removed a state it had no right to remove, and it
    is the one outcome that invalidates the engine rather than the claim.

    On the satisficing rung the plan length moves in both directions and neither
    is a defect; see the comment on that clause below.
    """
    out = []
    for entry in report["results"]:
        if not entry["stub"]["plan_length_unchanged"]:
            out.append(
                "%s: pruning changed the bundled rung's answer -- unsound theorem"
                % entry["instance"]
            )
        for row in entry["fd"]:
            if row["guard_refused"]:
                continue          # a refusal is a finding; see RUN_STATE.md
            # A *shorter* plan under the guard is a contradiction only where the
            # baseline was an optimum.  On the satisficing rung it is not one --
            # LAMA returns the first plan its greedy search reaches, the guard
            # changes which one that is, and shorter is simply a different roll.
            # An earlier draft flagged four such rows as unsound compilations;
            # they were LAMA being LAMA, and the check was wrong, not the guard.
            if row["rung"].startswith("fd-optimal") and row["plan_length_delta"]:
                out.append(
                    "%s/%s/%s: optimal rung's length moved by %d under a guard that "
                    "must preserve optimal length -- unsound compilation"
                    % (entry["instance"], row["guard"], row["rung"],
                       row["plan_length_delta"])
                )
            if row["guarded"].get("solved") and not row["replayed_on_original_domain"]:
                out.append(
                    "%s/%s/%s: guarded plan was not replayed against the original domain"
                    % (entry["instance"], row["guard"], row["rung"])
                )
    return out
