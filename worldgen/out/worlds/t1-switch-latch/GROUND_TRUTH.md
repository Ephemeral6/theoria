# GROUND_TRUTH — `t1-switch-latch`

**Do not open while theorizing.** Scoring only.

Grid 6x7, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `switch_door`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `door` | 4 |
| `floor` | 0 |
| `switch` | 2 |
| `switch_on` | 3 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

A rule marked **cascade** fires inside `settle`, after the rule that caused it, and therefore never carries an `Outcome.rule` tag of its own. It has no `max` because there is no tagged transition to count — that is a property of where it acts, not evidence that it cannot happen. Any *non*-cascade rule reading `never fires` is a defect, and the build refuses to ship one.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `press_latch` | act=D and the target cell holds a switch in latch mode whose bit is 0 | that switch's bit becomes 1, permanently, and the agent stays where it is | False | 1 |
| `latch_already_set` | act=D and the target cell holds a switch in latch mode whose bit is already 1 | nothing changes | True | -1 |
| `blocked_toggle_would_shut_door` | act=D and the target cell holds a switch whose flip would leave the door the agent is standing on impassable | nothing changes — the switch visibly refuses to flip | True | **never fires** |
| `walk_through_door` | act=D and the target cell holds a door whose net's aggregate bit matches its polarity | the agent enters the door's cell | True | -1 |
| `blocked_by_door` | act=D and the target cell holds a door whose net's aggregate bit does not match its polarity | nothing changes | True | -1 |
| `door_mirrors_net` | at every instant, for a door on net N with polarity P | N is on iff any switch on N shows 1 (an OR network); the door is passable and undrawn iff N's aggregate bit matches P, and impassable and drawn otherwise | True | _cascade — untagged by construction_ |

## Invariants

4 hold, 0 violated, 0 unverified — `invariants_all_hold` is `true`. **An unverified invariant is not a satisfied one**, so it counts against that boolean exactly as a violation does; the two are kept in separate lists because they call for different work.

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 26 reachable states: holds)_
* **grid_shape** — every frame is 6 x 7  _(checked on 26 reachable states: holds)_
* **door_presence_tracks_net** — a door shows colour 4 exactly when its net's aggregate bit does not match its polarity, and shows nothing of its own otherwise  _(checked on 26 reachable states: holds)_
* **latch_monotone** — every latch switch's bit is monotone non-decreasing along every trajectory, and so is the aggregate bit of a net whose switches are all latches: once 1, never 0 again  _(checked on 104 transitions: holds)_

## Solvability

Solvable in 9 steps: `DOWN DOWN LEFT DOWN RIGHT RIGHT RIGHT RIGHT DOWN`.

## Reversibility stamp (A0′ criterion)

5 of 6 rules are re-witnessable (score 0.83).

Single-witness rules: `press_latch`.
