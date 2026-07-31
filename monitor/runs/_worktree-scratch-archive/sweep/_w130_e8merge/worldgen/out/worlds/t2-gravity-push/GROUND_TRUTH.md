# GROUND_TRUTH — `t2-gravity-push`

**Do not open while theorizing.** Scoring only.

Grid 7x9, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `gravity`, `push`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `block` | 2 |
| `floor` | 0 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

A rule marked **cascade** fires inside `settle`, after the rule that caused it, and therefore never carries an `Outcome.rule` tag of its own. It has no `max` because there is no tagged transition to count — that is a property of where it acts, not evidence that it cannot happen. Any *non*-cascade rule reading `never fires` is a defect, and the build refuses to ship one.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `fall` | a movable has a free cell directly below it, or the agent has a cell directly below it that the agent may be deposited on | that thing descends one cell, and this repeats to a fixpoint — a post-step settlement, appended to whatever rule ended the step, never tagged as a rule of its own | False | _cascade — untagged by construction_ |
| `agent_does_not_fall_onto_live_entities` | the cell below the agent holds an uncollected token or an intact fragile tile | the agent does not descend into it — it stays where it is, hovering, until it walks in and triggers the effect properly | True | _cascade — untagged by construction_ |
| `up_is_inert` | act=UP and the cell above the agent is plain floor | the agent rises into it, then falls straight back during the same step's settlement, so the state after the step equals the state before it | True | _cascade — untagged by construction_ |
| `push` | act=D and the target cell holds a block and the cell beyond it in direction D is free | the block moves one cell in direction D and the agent takes the block's old cell | conditional — only where the agent can reach the far side of the block | 2 |
| `blocked_by_block` | act=D and the target cell holds a block and the cell beyond it is not free | nothing changes | True | -1 |

## Invariants

5 hold, 0 violated, 0 unverified — `invariants_all_hold` is `true`. **An unverified invariant is not a satisfied one**, so it counts against that boolean exactly as a violation does; the two are kept in separate lists because they call for different work.

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 35 reachable states: holds)_
* **grid_shape** — every frame is 7 x 9  _(checked on 35 reachable states: holds)_
* **nothing_rests_on_a_free_cell** — no movable has a free cell below it, and the agent has no cell below it that it could be deposited on — every state a reader can observe is a settle fixpoint, so there is nowhere left to fall  _(checked on 35 reachable states: holds)_
* **block_count** — exactly 1 cell(s) show colour 2 at all times  _(checked on 35 reachable states: holds)_
* **blocks_disjoint** — no two blocks ever occupy the same cell  _(checked on 35 reachable states: holds)_

## Solvability

Solvable in 10 steps: `RIGHT RIGHT LEFT LEFT RIGHT RIGHT RIGHT RIGHT RIGHT RIGHT`.

## Reversibility stamp (A0′ criterion)

4 of 4 rules are re-witnessable (score 1.00).
