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

## Three things E6 added, and why each one had to be in *this* table

**The zero row.**  DECISIONS D-020 and `engines/deadlock_carver/README.md` both
record `open4`: sixteen true theorems, 47 expansions before and 47 after.  E2's
batch was generated (`far4-7`, `ringstuck4-8`) and `open4` is a committed fixture,
so the regenerable dividend table contained only instances where the dividend was
positive -- the null result survived in two hand-written documents and in neither
artifact anybody regenerates.  D-020's own argument is that the zero row is the
informative one; a table that drops it makes a conditional result look
unconditional.  `COMMITTED` puts both committed sokoban fixtures back in the
batch, first, so `open4` is row one.

**The FD wall clock, with the carve on the invoice.**  E2 priced the dividend in
seconds only on the bundled rung, where the answer is negative once carving is
counted (`far7`: 1.44 s to carve, 0.08 s saved).  The FD rows carried three raw
clocks but nothing subtracted them, so "the planner speeds up" had no second-side
number at all.  `_wall_clock()` does the subtraction and charges the carve against
it.  It charges against FD's **search** clock, not its end-to-end clock: the
end-to-end figure on this batch is ~150 ms of Python driver startup that no
theorem can touch, and quoting a dividend against it would be measuring the
driver.  Both are recorded; only one is the invoice.

**Tie-break sensitivity (E2's G7).**  `astar(blind())`'s absolute expansion count
is a property of FD's open list as well as of the instance.  E2's adversarial
review found `far5` going 958 -> 1479 under a different one and reported that the
*ratios* held -- in a sentence, in a review.  `tiebreak_sensitivity()` measures it
here, so "the ratios are stable" is a spread in a column.
"""

import os
import time
from typing import Dict, List, Optional, Sequence, Tuple

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

# The committed fixtures, read from `fixtures/data/` exactly as they sit in git.
#
# `open4` is here for the reason the module docstring gives: it is the instance
# where the theorems buy nothing, it is the row DECISIONS D-020 argues the table
# must contain, and until now no regenerable artifact contained it.
#
# `open4far` is here as its control.  `instances.far_level(4)` is *supposed* to
# be `open4far` -- `tests/test_bench.py` asserts the two `Level` objects match
# field by field -- but that is an assertion about a dataclass, not about a
# measurement.  Running the committed file through the same pipeline as the
# generated `far4` turns it into one: two rows that must agree in every
# structural column, from two different files on disk.
COMMITTED = (sokoban.OPEN4, sokoban.OPEN4FAR)


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


def batch(instance_dir: str) -> List[Tuple[str, sokoban.Level, str, str]]:
    """Every row of the dividend table: `(family, level, path, problem_text)`.

    The committed fixtures come **first**, and `open4` is therefore row one.
    That ordering is the point of E6's first extension: `open4` is where sixteen
    true theorems save zero expansions, DECISIONS D-020 argues that the zero row
    is the informative one, and a generated batch that starts at `far4` puts
    every positive dividend above the null result or drops it entirely.

    Committed instances are read from `fixtures/data/` **as bytes on disk** and
    never re-rendered.  `Level.problem_text()` would almost certainly produce the
    same characters -- `fixtures.generate_all` writes those files from these
    objects -- but "almost certainly" is not a property this rig accepts about
    the input to a measurement, and reading the file removes the question.
    Nothing here writes into `fixtures/data/`; `tests/test_bench.py` checks that.
    """
    rows: List[Tuple[str, sokoban.Level, str, str]] = []
    for level in COMMITTED:
        with open(level.path, "r", encoding="utf-8") as fh:
            rows.append(("committed", level, level.path, fh.read()))
    for side in FAR_SIDES:
        level = bench_instances.far_level(side)
        rows.append(("solvable", level, _write(instance_dir, level),
                     level.problem_text()))
    for side in RING_SIDES:
        level = ring_level(side)
        rows.append(("unsolvable", level, _write(instance_dir, level),
                     level.problem_text()))
    return rows


def stub_dividend(domain, problem, theorems, repeats: int = 3,
                  max_expansions: int = 400000,
                  carve_seconds: float = 0.0) -> Dict[str, object]:
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
    saved = round(blind - with_theorems, 6)
    out = report.as_json()
    out["timing"] = {
        "blind_seconds": round(blind, 6),
        "pruned_seconds": round(with_theorems, 6),
        # Below 1.0 means the pruned search finished sooner.  It is a weaker
        # number than the expansion ratio and is not the headline: the pruner is
        # a Python callable invoked per generated state, so it can easily cost
        # more per node than the nodes it removes are worth.
        "seconds_ratio": round(with_theorems / blind, 4) if blind else None,
        # The same invoice the FD rows now carry, so the two engines' wall-clock
        # verdicts can be read side by side rather than one in a table and the
        # other in a paragraph of E2's narrative.
        "seconds_saved": saved,
        "carve_seconds": round(carve_seconds, 6),
        "net_seconds_with_carving": round(carve_seconds - saved, 6),
        "carving_is_repaid": saved >= carve_seconds,
    }
    out["dividend_is_honest"] = report.same_answer
    return out


def _sub(after: Optional[float], before: Optional[float]) -> Optional[float]:
    """`before - after`, or None if either side is missing."""
    if after is None or before is None:
        return None
    return round(before - after, 6)


def _wall_clock(base: "fdrun.FdMeasurement", guarded: "fdrun.FdMeasurement",
                carve_seconds: float) -> Dict[str, object]:
    """The FD-side wall-clock dividend, with carving on the same invoice.

    E2 priced the dividend in seconds on the bundled rung only.  On the FD rungs
    the three clocks were recorded and never subtracted, so §1.9's "the planner
    speeds up" had a node number on both engines and a *second* number on one.
    This is the missing one.

    Two clocks, and they are not interchangeable:

    * **`search_seconds`** is what Fast Downward's search cost.  It is the only
      clock a deadlock theorem can move -- the theorem removes transitions from
      the search, and nothing else.  It is therefore the one the carve is charged
      against.
    * **`end_to_end_seconds`** is what the caller waited for: ~150 ms of Python
      driver startup, translation, and a 280 MB binary loading, on every instance
      this batch contains, almost regardless of the instance (E2 §1).  A dividend
      quoted against it would be measuring the driver, and its sign on a batch
      this small is noise.  Recorded, labelled, and never the headline.

    Neither is compared for equality by anything.  `verify.py` checks that the
    clocks are present and correctly nested and stops there, which is the house
    rule for every timing in this package.
    """
    search_saved = _sub(guarded.search_seconds, base.search_seconds)
    end_saved = _sub(guarded.wall_seconds, base.wall_seconds)
    net = None if search_saved is None else round(carve_seconds - search_saved, 6)
    return {
        "charged_against": "search_seconds",
        "search_seconds_before": base.search_seconds,
        "search_seconds_after": guarded.search_seconds,
        "search_seconds_saved": search_saved,
        "carve_seconds": round(carve_seconds, 6),
        # Positive means the carve was not repaid by the search it shortened --
        # which is every row on this batch, and is the same verdict the bundled
        # rung reaches by its own clock.
        "net_seconds_with_carving": net,
        "carving_is_repaid": None if search_saved is None else search_saved >= carve_seconds,
        # How many times this exact instance would have to be re-solved from the
        # same theorems before the carve pays for itself.  None where the guard
        # saved nothing or cost time: no number of repeats repays a carve out of
        # a saving that is zero or negative.
        "solves_to_repay_carving": (
            None if not search_saved or search_saved <= 0
            else int(-(-carve_seconds // search_saved))
        ),
        "end_to_end_seconds_before": round(base.wall_seconds, 6),
        "end_to_end_seconds_after": round(guarded.wall_seconds, 6),
        "end_to_end_seconds_saved": end_saved,
        "end_to_end_is_driver_startup": (
            "~150 ms of driver startup on every row of this batch; not a clock "
            "any theorem can move, and not the invoice"
        ),
    }


def fd_dividend(problem_text: str, problem_path: str, domain, problem,
                theorems, executable: str, work_dir: str, name: str,
                repeats: int = 3, log_dir: Optional[str] = None,
                carve_seconds: float = 0.0) -> List[Dict[str, object]]:
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

    for guard in compile_theorems.guardable_guards(theorems):
        guard_domain, guard_problem = compile_theorems.write_guarded(
            work_dir, name, problem_text, theorems, guard=guard, problem=problem
        )
        size = compile_theorems.guard_size(theorems, guard, problem)
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
                #
                # `to_original_plan` is a rename, not a repair: the `indexed`
                # guard splits `push` into `push-pair<k>` schemas, so its steps
                # are not in the original domain's vocabulary.  The validator
                # refused them outright the first time, which is the outcome it
                # exists for -- the mapping is applied here rather than by
                # relaxing what the validator will accept.
                fd_adapter.validate_plan(
                    domain, problem,
                    compile_theorems.to_original_plan(guarded.plan, guard),
                )
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
                # The three raw clocks above are what E2 recorded.  This is the
                # subtraction nothing performed, with the carve on it.
                "wall_clock": _wall_clock(base, guarded, carve_seconds),
            })
    return rows


# ------------------------------------------------------------- tie-break (G7)

# Three optimal blind searches over the same f = g + blind(), differing only in
# how they order states *within* an f-layer.  All three are complete and
# admissible, so all three must return the same optimal length -- which
# `failures()` checks rather than assumes, since a tie-break that changed an
# optimal length would mean one of these strings is not the search it claims.
#
# The middle one is not a guess.  E2's adversarial review reported `far5`'s blind
# baseline moving 958 -> 1479 under "a different f-tie-break" without naming the
# configuration; `eager(single(...))` reproduces 1479 exactly, so the number this
# module measures is the number that review measured.
TIEBREAKS = (
    ("astar", "astar(blind())",
     "FD's own `astar()` shorthand: a tie-breaking open list keyed on (f, h), "
     "FIFO inside a bucket. Every other blind number in this file is this one."),
    ("single", "eager(single(sum([g(),blind()])),reopen_closed=true)",
     "The same f, ordered by a single-key open list. Same f-layers, different "
     "order inside them -- this is the configuration E2's review found."),
    ("goalcount", "eager(tiebreaking([sum([g(),blind()]),goalcount()]),reopen_closed=true)",
     "The same f, ties inside a layer broken by unsatisfied goal count. A third "
     "point, so the spread is a range rather than a difference of two."),
)

# Blind accepts both of these; `indexed` is left out on purpose.  The question
# here is whether a *ratio* survives a change of tie-break, and `indexed` changes
# the task by an order of magnitude as well, which would put two variables in one
# column.  `singleton` and `full` are the pair E2's review quoted (-9%/-12%).
TIEBREAK_GUARDS = ("singleton", "full")


def tiebreak_sensitivity(problem_text: str, problem_path: str, problem,
                         theorems, executable: str, work_dir: str, name: str,
                         log_dir: Optional[str] = None) -> List[Dict[str, object]]:
    """E2's G7, measured instead of reviewed.

    Structural only, and deliberately: `repeats` is 1 and no clock is recorded.
    The question is whether the expansion *ratio* is a property of the instance
    or of FD's open list, and a wall clock answers neither half of it.
    """
    guards = {}
    for guard in TIEBREAK_GUARDS:
        if guard in compile_theorems.guardable_guards(theorems):
            guards[guard] = compile_theorems.write_guarded(
                work_dir, name, problem_text, theorems, guard=guard, problem=problem
            )

    rows = []
    for tiebreak, search, note in TIEBREAKS:
        keep = os.path.join(log_dir, "%s.tiebreak-%s.base.log" % (name, tiebreak)) \
            if log_dir else None
        base = fdrun.measure_search(executable, sokoban.DOMAIN_PATH, problem_path,
                                    search, keep_log=keep)
        before = base.nodes.get("expanded")
        row = {
            "instance": name,
            "tiebreak": tiebreak,
            "search": search,
            "note": note,
            "expansions_before": before,
            "plan_length_before": base.plan_length,
            "error": base.error,
            "guards": {},
        }
        for guard, (guard_domain, guard_problem) in guards.items():
            keep = os.path.join(
                log_dir, "%s.tiebreak-%s.%s.log" % (name, tiebreak, guard)
            ) if log_dir else None
            guarded = fdrun.measure_search(executable, guard_domain, guard_problem,
                                           search, keep_log=keep)
            after = guarded.nodes.get("expanded")
            row["guards"][guard] = {
                "expansions_after": after,
                "plan_length_after": guarded.plan_length,
                # The number the whole block exists to compare across tie-breaks.
                "expansions_ratio": (
                    round(after / before, 4) if before and after is not None else None
                ),
                "error": guarded.error,
            }
        rows.append(row)
    return rows


def tiebreak_summary(rows: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Turn the tie-break rows into the two spreads the claim is about.

    `baseline_spread_pct` is how much the **absolute** blind count moves when
    only the open list changes -- the quantity E2 warned about.
    `ratio_spread_points` is how much the **dividend** moves under the same
    change, in percentage points.  The claim "the ratios are stable" is true
    exactly when the second is small while the first is not, and both are now
    numbers rather than an assurance.
    """
    by_instance: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        by_instance.setdefault(row["instance"], []).append(row)

    out = []
    for instance, group in by_instance.items():
        counts = [row["expansions_before"] for row in group
                  if row["expansions_before"] is not None]
        entry: Dict[str, object] = {
            "instance": instance,
            "tiebreaks": [row["tiebreak"] for row in group],
            "baseline_min": min(counts) if counts else None,
            "baseline_max": max(counts) if counts else None,
            "baseline_spread_pct": (
                round(100.0 * (max(counts) - min(counts)) / min(counts), 1)
                if counts and min(counts) else None
            ),
            "guards": {},
        }
        for guard in TIEBREAK_GUARDS:
            ratios = [row["guards"][guard]["expansions_ratio"] for row in group
                      if guard in row["guards"]
                      and row["guards"][guard]["expansions_ratio"] is not None]
            if not ratios:
                continue
            entry["guards"][guard] = {
                "ratio_min": min(ratios),
                "ratio_max": max(ratios),
                "dividend_min_pct": round(100.0 * (1.0 - max(ratios)), 1),
                "dividend_max_pct": round(100.0 * (1.0 - min(ratios)), 1),
                "ratio_spread_points": round(100.0 * (max(ratios) - min(ratios)), 1),
            }
        out.append(entry)
    return out


def run(out_dir: str, executable: Optional[str] = None, repeats: int = 3
        ) -> Dict[str, object]:
    """Both ladders, all three questions."""
    executable = executable or backends.find_fast_downward()
    work_dir = os.path.join(out_dir, "guarded")
    instance_dir = os.path.join(out_dir, "instances")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    domain = fd_adapter.parse_domain(fd_adapter.read(sokoban.DOMAIN_PATH))

    entries = []
    tiebreak_rows: List[Dict[str, object]] = []
    for family, level, problem_path, problem_text in batch(instance_dir):
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
            "problem_path": os.path.relpath(problem_path, out_dir)
            if problem_path.startswith(out_dir) else problem_path,
            "stub": stub_dividend(domain, problem, theorems, repeats=repeats,
                                  carve_seconds=carve_seconds),
            "fd": [],
        }
        if executable is not None:
            entry["fd"] = fd_dividend(
                problem_text, problem_path, domain, problem, theorems,
                executable, work_dir, level.name, repeats=repeats, log_dir=log_dir,
                carve_seconds=carve_seconds,
            )
            if family != "unsolvable":
                tiebreak_rows += tiebreak_sensitivity(
                    problem_text, problem_path, problem, theorems,
                    executable, work_dir, level.name, log_dir=log_dir,
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
        "tiebreak_sensitivity": {
            "gap_closed": (
                "E2 G7 -- absolute blind-search expansion counts carry a "
                "tie-break dependence that the bench did not measure"
            ),
            "question": (
                "Is the dividend a property of the instance, or of the order "
                "Fast Downward happens to pop states off an f-layer?"
            ),
            "configurations": [
                {"tiebreak": key, "search": search, "note": note}
                for key, search, note in TIEBREAKS
            ],
            "guards": list(TIEBREAK_GUARDS),
            "excluded": (
                "The unsolvable family: Fast Downward's translator settles every "
                "`ringstuck*` instance during relaxed reachability, the search "
                "never starts, and 0 expansions has no tie-break."
            ),
            "timings_not_measured": (
                "Structural only, one run per cell. The question is whether a "
                "ratio survives a change of open list; a wall clock answers "
                "neither half of it."
            ),
            "rows": tiebreak_rows,
            "summary": tiebreak_summary(tiebreak_rows),
        },
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

    # The tie-break block's own soundness obligation.  Every configuration in
    # `TIEBREAKS` is a complete search over the same admissible f, so all of them
    # must return the same optimal length on the same task -- and the guarded
    # task must return the baseline's length under every one of them.  A length
    # that moves here means either a `--search` string that is not the search it
    # claims to be, or a guard whose unsoundness only one node ordering exposes.
    # Both are exactly the kind of thing a new configuration could smuggle in,
    # which is why the extension carries a check rather than only a table.
    for row in report.get("tiebreak_sensitivity", {}).get("rows", []):
        if row.get("error"):
            out.append(
                "%s/%s: the blind baseline did not answer under this tie-break: %s"
                % (row["instance"], row["tiebreak"], str(row["error"])[:160])
            )
            continue
        for guard, cell in row["guards"].items():
            if cell.get("error"):
                out.append(
                    "%s/%s/%s: guarded task did not answer under this tie-break: %s"
                    % (row["instance"], row["tiebreak"], guard,
                       str(cell["error"])[:160])
                )
                continue
            if cell["plan_length_after"] != row["plan_length_before"]:
                out.append(
                    "%s/%s/%s: optimal length %r guarded against %r unguarded -- "
                    "a guard must not change an optimal length under any tie-break"
                    % (row["instance"], row["tiebreak"], guard,
                       cell["plan_length_after"], row["plan_length_before"])
                )
    return out
