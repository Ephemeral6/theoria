# GROUND_TRUTH — `t1-tokens-lock`

**Do not open while theorizing.** Scoring only.

Grid 5x9, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `count_lock`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `floor` | 0 |
| `lock` | 3 |
| `token` | 2 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `collect_token` | act=D and the target cell holds an uncollected token | that token becomes collected — it stops being drawn and the global collected count rises by one — and the agent takes its cell | False | -1 |
| `walk_through_lock` | act=D and the target cell holds a lock whose k is at most the global number of tokens collected so far — the count is shared by every lock, not kept per lock | the agent moves onto the lock's cell | True | -1 |
| `blocked_by_lock` | act=D and the target cell holds a lock whose k exceeds the global number of tokens collected so far | nothing changes | True | -1 |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 50 reachable states: holds)_
* **grid_shape** — every frame is 5 x 9  _(checked on 50 reachable states: holds)_
* **token_count** — the number of cells showing colour 2 equals the number of tokens not yet collected  _(checked on 50 reachable states: holds)_
* **collection_is_monotone** — the number of collected tokens never decreases, so a lock that has opened never closes again  _(prose only, unverified)_

## Solvability

Solvable in 8 steps: `RIGHT RIGHT RIGHT RIGHT RIGHT RIGHT DOWN DOWN`.

## Reversibility stamp (A0′ criterion)

5 of 5 rules are re-witnessable (score 1.00).

**Claim disagreements:** `collect_token`.
