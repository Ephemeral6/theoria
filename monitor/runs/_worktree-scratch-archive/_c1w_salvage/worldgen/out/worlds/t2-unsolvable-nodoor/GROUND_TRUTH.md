# GROUND_TRUTH — `t2-unsolvable-nodoor`

**Do not open while theorizing.** Scoring only.

Grid 6x7, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `switch_door`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `door` | 2 |
| `floor` | 0 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `walk_through_door` | act=D and the target cell holds a door whose net's aggregate bit matches its polarity | the agent enters the door's cell | True | unreachable |
| `blocked_by_door` | act=D and the target cell holds a door whose net's aggregate bit does not match its polarity | nothing changes | True | -1 |
| `door_mirrors_net` | at every instant, for a door on net N with polarity P | N is on iff any switch on N shows 1 (an OR network); the door is passable and undrawn iff N's aggregate bit matches P, and impassable and drawn otherwise | True | unreachable |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 19 reachable states: holds)_
* **grid_shape** — every frame is 6 x 7  _(checked on 19 reachable states: holds)_
* **door_presence_tracks_net** — a door shows colour 2 exactly when its net's aggregate bit does not match its polarity, and shows nothing of its own otherwise  _(checked on 19 reachable states: holds)_

## Solvability

Solvable in 5 steps: `DOWN DOWN RIGHT RIGHT RIGHT`.

## Reversibility stamp (A0′ criterion)

3 of 3 rules are re-witnessable (score 1.00).
