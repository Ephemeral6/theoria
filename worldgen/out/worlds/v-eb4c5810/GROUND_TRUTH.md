# GROUND_TRUTH — `v-eb4c5810`

**Do not open while theorizing.** Scoring only.

Grid 6x7, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `color_cycle`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `cycler` | 2 |
| `cycler_1` | 3 |
| `cycler_2` | 4 |
| `floor` | 0 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

A rule marked **cascade** fires inside `settle`, after the rule that caused it, and therefore never carries an `Outcome.rule` tag of its own. It has no `max` because there is no tagged transition to count — that is a property of where it acts, not evidence that it cannot happen. Any *non*-cascade rule reading `never fires` is a defect, and the build refuses to ship one.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D, D is not `UP`, and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D, D is not `UP`, and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `action_forbidden` | act=D and D is `UP` | nothing changes — the command is refused before the grid is consulted, so the refusal is indistinguishable from a world in which that direction never does anything | True | -1 |
| `walk_through_cycler` | act=D, D is not `UP`, and the target cell holds a cycler whose phase equals its open phase | the agent enters the cell and the phase does not change | True | -1 |
| `advance_cycler` | act=D, D is not `UP`, and the target cell holds a cycler whose phase is not its open phase | the agent does not move and the cycler's phase becomes (phase + 1) mod k | True | 2 |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 41 reachable states: holds)_
* **grid_shape** — every frame is 6 x 7  _(checked on 41 reachable states: holds)_
* **phase_in_range** — every cycler's phase stays in range(k)  _(checked on 41 reachable states: holds)_
* **color_reads_phase** — the colour of a cycler cell determines its phase, except where the agent covers it  _(checked on 41 reachable states: holds)_

## Solvability

Solvable in 5 steps: `DOWN DOWN RIGHT RIGHT RIGHT`.

## Reversibility stamp (A0′ criterion)

5 of 5 rules are re-witnessable (score 1.00).
