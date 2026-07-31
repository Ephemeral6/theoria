# GROUND_TRUTH — `t3-latch-maze`

**Do not open while theorizing.** Scoring only.

Grid 8x10, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `consumable`, `count_lock`, `switch_door`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `collapsed` | 9 |
| `door` | 4 |
| `floor` | 0 |
| `fragile` | 8 |
| `lock` | 7 |
| `switch` | 2 |
| `switch_on` | 3 |
| `token` | 5 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `press_latch` | act=D and the target cell holds a switch in latch mode whose bit is 0 | that switch's bit becomes 1, permanently, and the agent stays where it is | False | 1 |
| `latch_already_set` | act=D and the target cell holds a switch in latch mode whose bit is already 1 | nothing changes | True | -1 |
| `walk_through_door` | act=D and the target cell holds a door whose net's aggregate bit matches its polarity | the agent enters the door's cell | True | -1 |
| `blocked_by_door` | act=D and the target cell holds a door whose net's aggregate bit does not match its polarity | nothing changes | True | -1 |
| `door_mirrors_net` | at every instant, for a door on net N with polarity P | N is on iff any switch on N shows 1 (an OR network); the door is passable and undrawn iff N's aggregate bit matches P, and impassable and drawn otherwise | True | unreachable |
| `collect_token` | act=D and the target cell holds an uncollected token | that token becomes collected — it stops being drawn and the global collected count rises by one — and the agent takes its cell | False | -1 |
| `walk_through_lock` | act=D and the target cell holds a lock whose k is at most the global number of tokens collected so far — the count is shared by every lock, not kept per lock | the agent moves onto the lock's cell | True | -1 |
| `blocked_by_lock` | act=D and the target cell holds a lock whose k exceeds the global number of tokens collected so far | nothing changes | True | -1 |
| `cross_fragile` | act=D and the target cell holds an intact fragile tile | the agent moves onto the tile and the tile arms.  The tile does not collapse on this step: the collapse happens later, in settlement, on the first step at which the agent is no longer standing there — so in the trace the tile changes to the collapsed colour one frame after the crossing, not in the frame of the crossing itself | False | 1 |
| `blocked_by_collapsed` | act=D and the target cell holds a collapsed fragile tile | nothing changes | True | -1 |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 436 reachable states: holds)_
* **grid_shape** — every frame is 8 x 10  _(checked on 436 reachable states: holds)_
* **door_presence_tracks_net** — a door shows colour 4 exactly when its net's aggregate bit does not match its polarity, and shows nothing of its own otherwise  _(checked on 436 reachable states: holds)_
* **latch_monotone** — every latch switch's bit is monotone non-decreasing along every trajectory, and so is the aggregate bit of a net whose switches are all latches: once 1, never 0 again  _(prose only, unverified)_
* **token_count** — the number of cells showing colour 5 equals the number of tokens not yet collected  _(checked on 436 reachable states: holds)_
* **collection_is_monotone** — the number of collected tokens never decreases, so a lock that has opened never closes again  _(prose only, unverified)_
* **single_armed_tile** — at most one fragile tile is armed at any instant  _(checked on 436 reachable states: holds)_
* **armed_tile_under_agent** — an armed fragile tile's cell is the agent's cell  _(checked on 436 reachable states: holds)_
* **tile_state_is_monotone** — a fragile tile's state only ever rises, 0 -> 1 -> 2, so a collapsed tile is never crossed again  _(prose only, unverified)_

## Solvability

Solvable in 12 steps: `DOWN DOWN DOWN DOWN DOWN RIGHT RIGHT RIGHT RIGHT RIGHT RIGHT RIGHT`.

## Reversibility stamp (A0′ criterion)

9 of 11 rules are re-witnessable (score 0.82).

Single-witness rules: `cross_fragile`, `press_latch`.

**Claim disagreements:** `collect_token`.
