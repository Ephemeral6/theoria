# GROUND_TRUTH — `t2-lock-fragile`

**Do not open while theorizing.** Scoring only.

Grid 7x9, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `consumable`, `count_lock`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `collapsed` | 5 |
| `floor` | 0 |
| `fragile` | 4 |
| `lock` | 3 |
| `token` | 2 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

A rule marked **cascade** fires inside `settle`, after the rule that caused it, and therefore never carries an `Outcome.rule` tag of its own. It has no `max` because there is no tagged transition to count — that is a property of where it acts, not evidence that it cannot happen. Any *non*-cascade rule reading `never fires` is a defect, and the build refuses to ship one.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `collect_token` | act=D and the target cell holds an uncollected token | that token becomes collected — it stops being drawn and the global collected count rises by one — and the agent takes its cell | False | 3 |
| `walk_through_lock` | act=D and the target cell holds a lock whose k is at most the global number of tokens collected so far — the count is shared by every lock, not kept per lock | the agent moves onto the lock's cell | True | -1 |
| `blocked_by_lock` | act=D and the target cell holds a lock whose k exceeds the global number of tokens collected so far | nothing changes | True | -1 |
| `cross_fragile` | act=D and the target cell holds an intact fragile tile | the agent moves onto the tile and the tile arms.  The tile does not collapse on this step: the collapse happens later, in settlement, on the first step at which the agent is no longer standing there — so in the trace the tile changes to the collapsed colour one frame after the crossing, not in the frame of the crossing itself | False | 1 |
| `blocked_by_collapsed` | act=D and the target cell holds a collapsed fragile tile | nothing changes | True | -1 |

## Invariants

7 hold, 0 violated, 0 unverified — `invariants_all_hold` is `true`. **An unverified invariant is not a satisfied one**, so it counts against that boolean exactly as a violation does; the two are kept in separate lists because they call for different work.

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 87 reachable states: holds)_
* **grid_shape** — every frame is 7 x 9  _(checked on 87 reachable states: holds)_
* **token_count** — the number of cells showing colour 2 equals the number of tokens not yet collected  _(checked on 87 reachable states: holds)_
* **collection_is_monotone** — the number of collected tokens never decreases, so a lock that has opened never closes again  _(checked on 348 transitions: holds)_
* **single_armed_tile** — at most one fragile tile is armed at any instant  _(checked on 87 reachable states: holds)_
* **armed_tile_under_agent** — an armed fragile tile's cell is the agent's cell  _(checked on 87 reachable states: holds)_
* **tile_state_is_monotone** — a fragile tile's state only ever rises, 0 -> 1 -> 2, so a collapsed tile is never crossed again  _(checked on 348 transitions: holds)_

## Solvability

Solvable in 18 steps: `DOWN DOWN UP UP RIGHT RIGHT RIGHT RIGHT DOWN DOWN DOWN DOWN RIGHT RIGHT UP UP UP UP`.

## Reversibility stamp (A0′ criterion)

6 of 7 rules are re-witnessable (score 0.86).

Single-witness rules: `cross_fragile`.
