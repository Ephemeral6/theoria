# GROUND_TRUTH — `t1-walk-maze`

**Do not open while theorizing.** Scoring only.

Grid 7x9, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families none.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `floor` | 0 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 24 reachable states: holds)_
* **grid_shape** — every frame is 7 x 9  _(checked on 24 reachable states: holds)_

## Solvability

Solvable in 10 steps: `DOWN DOWN DOWN DOWN RIGHT RIGHT RIGHT RIGHT RIGHT RIGHT`.

## Reversibility stamp (A0′ criterion)

2 of 2 rules are re-witnessable (score 1.00).
