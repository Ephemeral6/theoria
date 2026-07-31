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

A rule marked **cascade** fires inside `settle`, after the rule that caused it, and therefore never carries an `Outcome.rule` tag of its own. It has no `max` because there is no tagged transition to count — that is a property of where it acts, not evidence that it cannot happen. Any *non*-cascade rule reading `never fires` is a defect, and the build refuses to ship one.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `blocked_by_door` | act=D and the target cell holds a door whose net's aggregate bit does not match its polarity | nothing changes | True | -1 |
| `door_mirrors_net` | at every instant, for a door on net N with polarity P | N is on iff any switch on N shows 1 (an OR network); the door is passable and undrawn iff N's aggregate bit matches P, and impassable and drawn otherwise | True | _cascade — untagged by construction_ |

## Invariants

3 hold, 0 violated, 0 unverified — `invariants_all_hold` is `true`. **An unverified invariant is not a satisfied one**, so it counts against that boolean exactly as a violation does; the two are kept in separate lists because they call for different work.

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 11 reachable states: holds)_
* **grid_shape** — every frame is 6 x 7  _(checked on 11 reachable states: holds)_
* **door_presence_tracks_net** — a door shows colour 2 exactly when its net's aggregate bit does not match its polarity, and shows nothing of its own otherwise  _(checked on 11 reachable states: holds)_

## Solvability

**Unsolvable.** the reachable set has 11 states and the agent occupies the goal cell (4, 5) in none of them

* `door` at (3, 4) — removing it makes the world solvable in 6 steps

## Reversibility stamp (A0′ criterion)

3 of 3 rules are re-witnessable (score 1.00).
