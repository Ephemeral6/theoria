# fd_adapter

PDDL in, plan out. One interface, three rungs.

> **Fast Downward is connected** (P-13, 2026-07-28): a real FD 24.06+ build, with
> provenance in `../../runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`. `.toolchain/` is
> gitignored by design, so on a machine without that build the adapter falls back
> to the bundled BFS stub and three tests skip — expected, not a defect. This note
> used to say the opposite; it was left behind when the planner landed.
>
> What the ladder is worth, in numbers, is `../../bench/` — and the headline is
> that on the instances this rig produces, the bundled rung is still the fastest
> one end to end. See `../../STATUS.md`, "What the ladder is worth (E2)".

## Interface

```python
from engines import fd_adapter
plan = fd_adapter.solve(domain_path, problem_path)   # or fd_adapter.run(...)
plan.actions   # ['(pick ball1 rooma left)', ...]
plan.length    # 5
plan.backend   # 'stub-bfs' | 'fd-optimal' | 'fd-satisficing'
plan.search    # 'bfs' | 'astar(lmcut())' | '--alias lama-first'
plan.optimal   # False on the satisficing rung, True on the other two
```

## The ladder

| tier | who answers | length-optimal |
|---|---|---|
| `stub-bfs` | the bundled grounded-STRIPS BFS | yes |
| `fd-optimal` | Fast Downward, `astar(lmcut())`; `heuristic="ipdb"` selectable | yes |
| `fd-satisficing` | Fast Downward, `--alias lama-first` | no |

`backends.choose_tier(prefer, on_disk, prune, discover)` picks one, by this rule
in this order:

1. `prefer="stub"` forces `stub-bfs`. Every committed artifact rides on this
   clause — a machine that happens to have a planner installed must not produce
   different bytes.
2. `prefer="fd-optimal"` / `"fd-satisficing"` names a rung and is honoured; if no
   executable is reachable it raises `FastDownwardMissing` rather than quietly
   dropping to another rung. Naming an FD rung together with `prune=` or an
   in-memory instance raises — that is a contradiction, not a preference.
3. `prune=` or an instance that exists only in memory forces `stub-bfs`. Fast
   Downward reads files and has no pruning hook.
4. Otherwise `fd-optimal` when Fast Downward is reachable, `stub-bfs` when not.

`discover` is injectable, so the whole table is tested on a machine with no
planner (`tests/test_fd_ladder.py`).

Discovery itself is unchanged: `FAST_DOWNWARD`, `FAST_DOWNWARD_HOME`,
`DOWNWARD_ROOT`, or `fast-downward.py` / `fast-downward` / `downward` on PATH.

The two optimal rungs are **length-optimal** for unit costs — A* with an
admissible heuristic and BFS alike — so "the plan length equals the hand-verified
optimum" means the same thing under either. The satisficing rung is not, and says
so in `plan.optimal` so its length cannot be read as an optimum. No plan is ever
returned unvalidated, on any rung: `solve()` runs the independent validator
before handing it back.

## Unsolvable is a result; giving up is not

When the planner *proves* there is no plan, `solve_parsed()` returns `None`,
exactly as the bundled search does, and `solve()` raises `NoPlanExists` — a
`RuntimeError` subclass, so callers written against the old bare `RuntimeError`
keep working. A run that merely failed to find a plan stays a hard
`RuntimeError`, as does a crash or a timeout: it proves nothing, and reporting it
as unsolvable would turn "I could not find one" into "there is none", closing a
question the planner never answered.

**Which of the two happened cannot be read off the exit code.** FD's
`driver/returncodes.py` has `TRANSLATE_UNSOLVABLE = 10`, `SEARCH_UNSOLVABLE =
11`, `SEARCH_UNSOLVED_INCOMPLETE = 12` — but 11 is emitted only by algorithms
that detect unsolvability structurally. A complete `astar(blind())` that
exhausts the state space exits **12**, printing `Completely explored state space
-- no solution!`; an incomplete search that gave up also exits 12. So
`backends.proves_unsolvable` reads the log *and* the rung: 10 and 11 are proofs,
12 is a proof only on the optimal rung and only with FD's exhaustion line, and
the satisficing rung is never allowed to prove unsolvability at all — LAMA's
later iterations search under a cost bound, where exhaustion proves only that no
cheaper plan exists. See DECISIONS D-024.

## Determinism

`run()` — the entry point that writes `artifacts/candidates.jsonl` — is pinned to
`stub-bfs` regardless of what is installed. The higher rungs are opt-in there
(`prefer="fd-optimal"`). `solve()` still climbs the ladder on its own.

## Two callers who need more than `solve()`

```python
plan, result = fd_adapter.solve_parsed(domain, problem, prune=None)
result.expansions, result.generated, result.pruned, result.ground_actions
```

`solve_parsed` takes an already-parsed instance, returns `None` for the plan
instead of raising when there is none — on **every** rung, see above — and
reports the node account. Both matter to the engines added after M8:

* `probe_frontier` synthesises a problem in memory and asks "is this
  configuration reachable?" — where **unsolvable is the answer**, not an error;
* `deadlock_carver` needs the expansion counts to show that its theorems pay,
  and passes a `prune` callable so the search skips states it has proved dead.

A pruner is `State -> bool`, and it must be **sound**: a wrong `True` silently
deletes the answer. The only pruner in this rig comes with a proof and with a
test that the pruned and blind searches return the same plan. Goal-testing
happens before pruning, so a pruner that is wrong about a goal state cannot hide
a solution — it would have to be wrong about an interior one.

Fast Downward reads files, so an instance with no `problem_path` on disk always
takes the bundled search. That is the substitution `STATUS.md` already records,
not a new one.

## The instance

A minimal gripper: 2 rooms, 2 balls, 2 grippers; move both balls from `rooma` to
`roomb`. Independent of every fixture in this rig.

**Hand-verified optimum: 5.** Each ball needs one pick and one drop (4 actions),
and at least one move is needed since both balls start in the wrong room (1), so
5 is a lower bound; `pick / pick / move / drop / drop` attains it.

The test suite checks that number three ways that do not share code with the
search: the literal 5, validation by an independent replayer, and exhaustive
enumeration showing no plan of length ≤ 4 reaches the goal.

## The PDDL subset

`:strips`, `:typing`, `:negative-preconditions`; conjunctive preconditions,
goals and effects with `not`. Anything else — `or`, `forall`, `exists`, `when`,
numeric fluents — raises `PddlError` rather than being silently mis-parsed.

## Modules

| File | Role |
|---|---|
| `pddl.py` | tokeniser, parser, typed grounding |
| `search.py` | the stub: BFS over grounded STRIPS, with the node account and the pruning hook |
| `validate.py` | independent replay validator — imports the parser, **not** the search |
| `backends.py` | the tier rule, Fast Downward discovery, invocation, `sas_plan` parsing |
| `fuzz.py` | random gripper instances and the closed-form optimum they are checked against |

`validate.py` re-grounds its own actions on purpose: a bug in the search's
successor generation (a dropped delete effect, say) must not be able to validate
itself.

## Payload shape — `kind: "plan"` (stable)

```json
{
  "domain": "gripper",
  "problem": "gripper-two-balls",
  "backend": "stub-bfs",
  "search": "bfs",
  "optimal": true,
  "length": 5,
  "actions": ["(pick ball1 rooma left)", "(pick ball2 rooma right)",
              "(move rooma roomb)", "(drop ball1 roomb left)",
              "(drop ball2 roomb right)"]
}
```

`evidence.transitions` indexes the plan steps; `evidence.coverage` is
`<length>/<length>`.

## The differential fuzz

`fuzz.py` generates small random gripper instances — 1–3 balls out of place plus
some already-settled ones, seeded, so the sequence is a function of the seed —
and checks each rung's plan length against the gripper optimum in **closed form**:

```
optimum(m) = 2m + 2*ceil(m / grippers) - 1        (m > 0)
```

Every misplaced ball needs one pick and one drop and no schedule can share
either; the robot carries at most `grippers` balls, so it makes `ceil(m/g)` trips
out and one fewer back. Fill-both-move-empty-move-back attains both counts, so
this is the optimum, not a bound. `optimum(2) == 5`, the hand-verified fixture.

The oracle is arithmetic, so it shares no code with anything it checks and the
fuzz is a real differential on a machine with no planner installed. Where one is
installed, `fd-optimal` under both heuristics and `fd-satisficing` join in and
the run does more rounds.

## Connecting Fast Downward later

Install it and either put `fast-downward.py` on PATH or set `FAST_DOWNWARD` to
the executable or its directory. Nothing else changes: `solve()` picks it up, the
skipped tests (`test_fast_downward_agrees_with_the_stub`, the cross-rung
agreement pair) start running, the fuzz adds the FD rungs, and the payload's
`backend` and `search` fields record which rung answered and what it was asked.
`run()` stays on `stub-bfs` on purpose, so the committed artifact does not move.
