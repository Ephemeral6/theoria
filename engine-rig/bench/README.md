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

Three guards:

* `singleton` — corner deadlocks, as a negative precondition. Stays in STRIPS,
  every rung accepts it.
* `full` — adds pair deadlocks as a universally quantified negated conjunction,
  hence `:adl`. FD's `normalize.py` turns any `forall` precondition into an
  **axiom**, and `astar(lmcut())` / `astar(ipdb())` refuse a task with axioms
  (driver exit 34). `astar(blind())` accepts it.
* `indexed` — the same pair guard with the quantifier removed: static `npair<k>`
  gives a position's dead-partner count, `deadpair<i>` names the i-th, and one
  `push-pair<k>` schema per arity binds them. Pure STRIPS; the optimal rungs
  accept it.

`indexed` exists because an adversarial review refuted the run's first
conclusion, that pair deadlocks could not reach the admissible rungs at all. They
can — and doing so makes those rungs *worse* (`lmcut` on `far6`: 47 expansions
without the pair theorems, 66 with, task size 2813 → 26253). FD compiles a
negative precondition on a fluent into one operator copy per other value of that
variable, so a guard meant to cost only grounding costs the search a much larger
operator set. Both halves are pinned by tests.

Its plans need `to_original_plan()` before replay: `indexed` renames `push` to
`push-pair<k>`, so its steps are not in the original domain's vocabulary. The
validator refused them outright the first time, which is what it is for — the
mapping is applied at the call site rather than by relaxing the validator.

**One trap worth knowing if you extend the guard.** The pair guard reads the
**pre-state**, where the pushed box still holds its old position. So a pattern
naming the same box twice blocks transitions that *leave* the pattern instead of
entering it — strictly stronger than the theorem, and stronger is the direction
that breaks optimality (measured: `far4` 11 → 25). `guardable()` clause 3 refuses
such patterns. `carve()` cannot currently produce one, but that is a property of
another module and this one is not supposed to lean on it.

## Tests

`tests/test_bench.py` runs on a machine with no planner. The log parser — the one
part that depends on Fast Downward's exact wording — is tested against FD output
that is **committed**: `runs/p13-fd-real/work/lmcut/run.log`. The assertion is the
number P-13's manifest quotes, recovered from the log it quoted it from.
