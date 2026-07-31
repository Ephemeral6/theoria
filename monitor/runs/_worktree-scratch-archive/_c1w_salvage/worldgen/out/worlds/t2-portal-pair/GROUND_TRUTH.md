# GROUND_TRUTH — `t2-portal-pair`

**Do not open while theorizing.** Scoring only.

Grid 7x9, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `portal`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `floor` | 0 |
| `portal` | 2 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `teleport_twoway` | act=D and the target cell holds one mouth of a two-way pair and the other mouth is free | the agent is placed on the other mouth, independently of D | True | -1 |
| `blocked_portal_exit` | act=D and the target cell holds a portal whose landing cell is a wall, out of bounds, or occupied | nothing changes | True | unreachable |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 24 reachable states: holds)_
* **grid_shape** — every frame is 7 x 9  _(checked on 24 reachable states: holds)_
* **agent_conserved** — exactly one cell shows the agent at all times — a portal moves the agent, it never copies or deletes it  _(checked on 24 reachable states: holds)_
* **mouths_static** — each of the 2 portal mouth(s) shows colour 2 unless the agent is standing on it  _(checked on 24 reachable states: holds)_

## Solvability

Solvable in 3 steps: `DOWN DOWN DOWN`.

## Reversibility stamp (A0′ criterion)

3 of 3 rules are re-witnessable (score 1.00).
