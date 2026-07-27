# fd_adapter

PDDL in, plan out. One interface, two possible backends.

> **Fast Downward is not connected in this sandbox.** Two discovery/install
> attempts failed (log in `../../STATUS.md`), so the bundled BFS stub is what
> runs. The FD code path is implemented and unexercised.

## Interface

```python
from engines import fd_adapter
plan = fd_adapter.solve(domain_path, problem_path)   # or fd_adapter.run(...)
plan.actions   # ['(pick ball1 rooma left)', ...]
plan.length    # 5
plan.backend   # 'fast-downward' | 'stub-bfs'
```

`solve()` prefers Fast Downward when it can find one (via `FAST_DOWNWARD`,
`FAST_DOWNWARD_HOME`, `DOWNWARD_ROOT`, or `fast-downward.py` / `fast-downward` /
`downward` on PATH), calls it with `--search "astar(blind())"`, and parses
`sas_plan`. Otherwise it runs the stub. `prefer="stub"` forces the stub, which is
what the tests use so the same path runs on every machine.

Both backends are **length-optimal** for unit costs — A*/blind and BFS alike — so
"the plan length equals the hand-verified optimum" means the same thing under
either. No plan is ever returned unvalidated: `solve()` runs the independent
validator before handing it back.

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
| `search.py` | the stub: BFS over grounded STRIPS |
| `validate.py` | independent replay validator — imports the parser, **not** the search |
| `backends.py` | Fast Downward discovery, invocation, `sas_plan` parsing |

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

## Connecting Fast Downward later

Install it and either put `fast-downward.py` on PATH or set `FAST_DOWNWARD` to
the executable. Nothing else changes: `solve()` picks it up, the tests' skipped
`test_fast_downward_agrees_with_the_stub` starts running, and the payload's
`backend` field records which one answered.
