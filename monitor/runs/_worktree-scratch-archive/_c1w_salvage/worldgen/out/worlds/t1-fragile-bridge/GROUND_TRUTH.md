# GROUND_TRUTH — `t1-fragile-bridge`

**Do not open while theorizing.** Scoring only.

Grid 5x7, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `consumable`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `collapsed` | 3 |
| `floor` | 0 |
| `fragile` | 2 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `cross_fragile` | act=D and the target cell holds an intact fragile tile | the agent moves onto the tile and the tile arms.  The tile does not collapse on this step: the collapse happens later, in settlement, on the first step at which the agent is no longer standing there — so in the trace the tile changes to the collapsed colour one frame after the crossing, not in the frame of the crossing itself | False | -1 |
| `blocked_by_collapsed` | act=D and the target cell holds a collapsed fragile tile | nothing changes | True | -1 |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 42 reachable states: holds)_
* **grid_shape** — every frame is 5 x 7  _(checked on 42 reachable states: holds)_
* **single_armed_tile** — at most one fragile tile is armed at any instant  _(checked on 42 reachable states: holds)_
* **armed_tile_under_agent** — an armed fragile tile's cell is the agent's cell  _(checked on 42 reachable states: holds)_
* **tile_state_is_monotone** — a fragile tile's state only ever rises, 0 -> 1 -> 2, so a collapsed tile is never crossed again  _(prose only, unverified)_

## Solvability

Solvable in 4 steps: `RIGHT RIGHT RIGHT RIGHT`.

## Reversibility stamp (A0′ criterion)

4 of 4 rules are re-witnessable (score 1.00).

**Claim disagreements:** `cross_fragile`.
