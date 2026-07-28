# GROUND_TRUTH — `t3-cycler-portal-lock`

**Do not open while theorizing.** Scoring only.

Grid 8x10, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `color_cycle`, `count_lock`, `portal`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `cycler` | 5 |
| `cycler_1` | 7 |
| `cycler_2` | 8 |
| `floor` | 0 |
| `lock` | 4 |
| `portal` | 2 |
| `token` | 3 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

A rule marked **cascade** fires inside `settle`, after the rule that caused it, and therefore never carries an `Outcome.rule` tag of its own. It has no `max` because there is no tagged transition to count — that is a property of where it acts, not evidence that it cannot happen. Any *non*-cascade rule reading `never fires` is a defect, and the build refuses to ship one.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `walk_through_cycler` | act=D and the target cell holds a cycler whose phase equals its open phase | the agent enters the cell and the phase does not change | True | -1 |
| `advance_cycler` | act=D and the target cell holds a cycler whose phase is not its open phase | the agent does not move and the cycler's phase becomes (phase + 1) mod k | True | 1 |
| `teleport_twoway` | act=D and the target cell holds one mouth of a two-way pair and the other mouth is free | the agent is placed on the other mouth, independently of D | True | -1 |
| `blocked_portal_exit` | act=D and the target cell holds a portal whose landing cell is a wall, out of bounds, or occupied | nothing changes | True | **never fires** |
| `collect_token` | act=D and the target cell holds an uncollected token | that token becomes collected — it stops being drawn and the global collected count rises by one — and the agent takes its cell | False | 2 |
| `walk_through_lock` | act=D and the target cell holds a lock whose k is at most the global number of tokens collected so far — the count is shared by every lock, not kept per lock | the agent moves onto the lock's cell | True | -1 |
| `blocked_by_lock` | act=D and the target cell holds a lock whose k exceeds the global number of tokens collected so far | nothing changes | True | -1 |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 262 reachable states: holds)_
* **grid_shape** — every frame is 8 x 10  _(checked on 262 reachable states: holds)_
* **phase_in_range** — every cycler's phase stays in range(k)  _(checked on 262 reachable states: holds)_
* **color_reads_phase** — the colour of a cycler cell determines its phase, except where the agent covers it  _(checked on 262 reachable states: holds)_
* **agent_conserved** — exactly one cell shows the agent at all times — a portal moves the agent, it never copies or deletes it  _(checked on 262 reachable states: holds)_
* **mouths_static** — each of the 2 portal mouth(s) shows colour 2 unless the agent is standing on it  _(checked on 262 reachable states: holds)_
* **token_count** — the number of cells showing colour 3 equals the number of tokens not yet collected  _(checked on 262 reachable states: holds)_
* **collection_is_monotone** — the number of collected tokens never decreases, so a lock that has opened never closes again  _(prose only, unverified)_

## Solvability

Solvable in 5 steps: `DOWN DOWN DOWN DOWN DOWN`.

## Reversibility stamp (A0′ criterion)

7 of 8 rules are re-witnessable (score 0.88).

Single-witness rules: `advance_cycler`.
