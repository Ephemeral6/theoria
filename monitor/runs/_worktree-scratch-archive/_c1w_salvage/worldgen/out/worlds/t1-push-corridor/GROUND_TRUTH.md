# GROUND_TRUTH — `t1-push-corridor`

**Do not open while theorizing.** Scoring only.

Grid 5x6, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `push`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `block` | 2 |
| `floor` | 0 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `push` | act=D and the target cell holds a block and the cell beyond it in direction D is free | the block moves one cell in direction D and the agent takes the block's old cell | conditional — only where the agent can reach the far side of the block | 1 |
| `blocked_by_block` | act=D and the target cell holds a block and the cell beyond it is not free | nothing changes | True | -1 |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 15 reachable states: holds)_
* **grid_shape** — every frame is 5 x 6  _(checked on 15 reachable states: holds)_
* **block_count** — exactly 1 cell(s) show colour 2 at all times  _(checked on 15 reachable states: holds)_
* **blocks_disjoint** — no two blocks ever occupy the same cell  _(checked on 15 reachable states: holds)_

## Solvability

Solvable in 5 steps: `DOWN DOWN RIGHT RIGHT RIGHT`.

## Reversibility stamp (A0′ criterion)

3 of 4 rules are re-witnessable (score 0.75).

Single-witness rules: `push`.
