# GROUND_TRUTH — `t3-gravity-fragile`

**Do not open while theorizing.** Scoring only.

Grid 7x9, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `consumable`, `gravity`, `push`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `block` | 2 |
| `collapsed` | 4 |
| `floor` | 0 |
| `fragile` | 3 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `fall` | the cell directly below the agent, or below a movable entity, is free | that thing descends one cell, and this repeats to a fixpoint — a post-step settlement, appended to whatever rule ended the step, never tagged as a rule of its own | False | unreachable |
| `up_is_inert` | act=UP | the agent enters the cell above if that cell is free, then falls back into the cell it left during the same step's settlement, so the state after the step equals the state before it | True | unreachable |
| `push` | act=D and the target cell holds a block and the cell beyond it in direction D is free | the block moves one cell in direction D and the agent takes the block's old cell | conditional — only where the agent can reach the far side of the block | 1 |
| `blocked_by_block` | act=D and the target cell holds a block and the cell beyond it is not free | nothing changes | True | -1 |
| `cross_fragile` | act=D and the target cell holds an intact fragile tile | the agent moves onto the tile and the tile arms.  The tile does not collapse on this step: the collapse happens later, in settlement, on the first step at which the agent is no longer standing there — so in the trace the tile changes to the collapsed colour one frame after the crossing, not in the frame of the crossing itself | False | 1 |
| `blocked_by_collapsed` | act=D and the target cell holds a collapsed fragile tile | nothing changes | True | -1 |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 18 reachable states: holds)_
* **grid_shape** — every frame is 7 x 9  _(checked on 18 reachable states: holds)_
* **nothing_rests_on_a_free_cell** — the cell below the agent and below every movable is never free — every state a reader can observe is a settle fixpoint, so there is nowhere left to fall  _(checked on 18 reachable states: holds)_
* **block_count** — exactly 1 cell(s) show colour 2 at all times  _(checked on 18 reachable states: holds)_
* **blocks_disjoint** — no two blocks ever occupy the same cell  _(checked on 18 reachable states: holds)_
* **single_armed_tile** — at most one fragile tile is armed at any instant  _(checked on 18 reachable states: holds)_
* **armed_tile_under_agent** — an armed fragile tile's cell is the agent's cell  _(checked on 18 reachable states: holds)_
* **tile_state_is_monotone** — a fragile tile's state only ever rises, 0 -> 1 -> 2, so a collapsed tile is never crossed again  _(prose only, unverified)_

## Solvability

**Unsolvable.** the reachable set has 18 states and the agent occupies the goal cell (5, 7) in none of them

* `block` at (3, 4) — removing it makes the world solvable in 6 steps

## Reversibility stamp (A0′ criterion)

4 of 6 rules are re-witnessable (score 0.67).

Single-witness rules: `cross_fragile`, `push`.
