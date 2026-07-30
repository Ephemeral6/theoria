# GROUND_TRUTH — `v-ce732813`

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

A rule marked **cascade** fires inside `settle`, after the rule that caused it, and therefore never carries an `Outcome.rule` tag of its own. It has no `max` because there is no tagged transition to count — that is a property of where it acts, not evidence that it cannot happen. Any *non*-cascade rule reading `never fires` is a defect, and the build refuses to ship one.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D, D is not `DOWN`, and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D, D is not `DOWN`, and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `action_forbidden` | act=D and D is `DOWN` | nothing changes — the command is refused before the grid is consulted, so the refusal is indistinguishable from a world in which that direction never does anything | True | -1 |

## Invariants

2 hold, 0 violated, 0 unverified — `invariants_all_hold` is `true`. **An unverified invariant is not a satisfied one**, so it counts against that boolean exactly as a violation does; the two are kept in separate lists because they call for different work.

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 3 reachable states: holds)_
* **grid_shape** — every frame is 7 x 9  _(checked on 3 reachable states: holds)_

## Solvability

**Unsolvable.** the reachable set has 3 states and the agent occupies the goal cell (5, 7) in none of them

_The blocker analysis ran and attributed the unsolvability to no single entity._

## Reversibility stamp (A0′ criterion)

3 of 3 rules are re-witnessable (score 1.00).
