# bench

What the ladder is worth, and what a proved deadlock is worth. Numbers, not
architecture.

```bash
cd engine-rig
export FAST_DOWNWARD=".../.toolchain/downward/fast-downward.py"   # optional
python -m bench --out runs/<UTC>-E2-fd-ladder-bench
python -m bench.verify runs/<UTC>-E2-fd-ladder-bench
```

Without `FAST_DOWNWARD` everything still runs: the FD columns come back empty and
the bundled rung answers alone. That is the state this repo is in as checked out,
because `.toolchain/` is gitignored.

## The four rules this package is built on

**1. Nothing here is imported by an engine.** A benchmark that shares code with
the thing it benchmarks can only ever confirm it. The one deliberate exception is
`dividend.py` calling `deadlock_carver.pruning_report` — the engine's own
comparison, used rather than reimplemented, so a disagreement between the two
would be a bug in one of them and not a difference of opinion.

**2. Node counts do not compare across rungs.** `stub-bfs` expands grounded
STRIPS states; Fast Downward expands SAS+ states after its translator has merged
mutex atoms into finite-domain variables — on the gripper fixture, 14 STRIPS
facts become 5 SAS+ variables. A ratio between the two would be the most quotable
number in the run and would mean nothing. It appears nowhere. What is compared
across rungs is plan length and wall clock; node counts are compared only *within*
a rung.

**3. Structural results are reproducible; timings are not, and the artifacts say
which is which.** Every record splits in two. Node counts, plan lengths, task
sizes and exit codes are a function of the instance and the configuration;
`verify.py` re-derives them and compares exactly. Wall clock is a function of this
machine on this afternoon; `verify.py` checks only that the three clocks are
present and ordered (FD's search time inside FD's total time inside the
subprocess wall clock). The repo's byte-reproducibility requirement covers the
first half. Claiming it for the second would be a lie the next run would expose.

**4. No plan is reported unreplayed.** Every plan from every rung — including the
ones produced from a theorem-compiled task — is replayed against the **original**
domain by `fd_adapter.validate_plan`, which shares no code with any search.

## The modules

| File | Role |
|---|---|
| `fdrun.py` | run one FD rung and keep its node account — the thing `solve_parsed()` deliberately discards |
| `instances.py` | the batch: a gripper size ladder with a closed-form optimum, and the sokoban fixtures extended by size |
| `ladder.py` | the same batch on all four configurations; nodes, wall clock, optimality verdicts |
| `compile_theorems.py` | deadlock theorems compiled into PDDL, for the rungs with no pruning hook |
| `dividend.py` | blind versus pruned, on the bundled rung and on FD |
| `toolchain.py` | which planner produced the numbers, and the gap `.toolchain/` leaves |
| `report.py` | the JSON rendered as tables; computes nothing the JSON lacks |
| `verify.py` | re-derive the deterministic half and check it |

## Why `compile_theorems.py` exists

Fast Downward reads files and has no pruning hook — `backends.choose_tier` clause
3 — so Theoria 1.9's promise ("every deadlock proved, the planner speeds up at
the same time") cannot be tested on the FD rungs by the route the bundled rung
uses. It can be tested by putting the theorem *in the task*: forbid exactly the
transitions that enter a proved-dead pattern. Since every such state is dead,
removing them preserves plan existence and optimal length.

Two guards, because one of them does not fit through the optimal rungs:

* `singleton` — corner deadlocks, as a negative precondition. Stays in STRIPS,
  every rung accepts it.
* `full` — adds pair deadlocks, which need a universally quantified negated
  conjunction, hence `:adl`. FD's translator turns that into an **axiom** and
  `astar(lmcut())` / `astar(ipdb())` refuse a task with axioms (driver exit 34).

That refusal is a finding of the run, pinned by
`tests/test_bench.py::test_the_full_guard_is_refused_by_the_optimal_rung_for_the_reason_recorded`
so it cannot quietly stop being true.

## Tests

`tests/test_bench.py` runs on a machine with no planner. The log parser — the one
part that depends on Fast Downward's exact wording — is tested against FD output
that is **committed**: `runs/p13-fd-real/work/lmcut/run.log`. The assertion is the
number P-13's manifest quotes, recovered from the log it quoted it from.
