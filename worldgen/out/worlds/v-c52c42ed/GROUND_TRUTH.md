# GROUND_TRUTH — `v-c52c42ed`

**Do not open while theorizing.** Scoring only.

Grid 8x9, actions `UP`, `DOWN`, `LEFT`, `RIGHT`, families `portal`.

## Palette

| name | colour |
|---|---|
| `agent` | 6 |
| `floor` | 0 |
| `portal` | 2 |
| `wall` | 1 |

## Rules

`max` is the largest number of times **one trajectory** can witness the rule; `-1` means unboundedly often. A rule with `max = 1` is the A0 failure mode — one witness, no second one obtainable.

A rule marked **cascade** fires inside `settle`, after the rule that caused it, and therefore never carries an `Outcome.rule` tag of its own. It has no `max` because there is no tagged transition to count — that is a property of where it acts, not evidence that it cannot happen. Any *non*-cascade rule reading `never fires` is a defect, and the build refuses to ship one.

| name | when | then | claimed reversible | max |
|---|---|---|---|---|
| `walk` | act=D and the target cell is inside the grid, is not a wall, and no mechanism claims it | the agent moves one cell in direction D | conditional — reversible on open floor, not across a one-way edge | -1 |
| `blocked_by_wall` | act=D and the target cell is outside the grid or is a wall | nothing changes | True | -1 |
| `teleport_oneway` | act=D and the target cell holds a one-way portal whose dest cell is free | the agent is placed on the dest cell; nothing else changes | conditional — the rule is re-witnessable iff the agent can walk back to the mouth | -1 |
| `blocked_portal_exit` | act=D and the target cell holds a portal whose landing cell is a wall, out of bounds, or occupied | nothing changes | True | **never fires** |

## Invariants

* **agent_unique** — exactly one cell shows colour 6 at all times  _(checked on 26 reachable states: holds)_
* **grid_shape** — every frame is 8 x 9  _(checked on 26 reachable states: holds)_
* **agent_conserved** — exactly one cell shows the agent at all times — a portal moves the agent, it never copies or deletes it  _(checked on 26 reachable states: holds)_
* **mouths_static** — each of the 1 portal mouth(s) shows colour 2 unless the agent is standing on it  _(checked on 26 reachable states: holds)_

## Solvability

Solvable in 10 steps: `RIGHT RIGHT RIGHT RIGHT RIGHT RIGHT DOWN DOWN DOWN DOWN`.

## Reversibility stamp (A0′ criterion)

3 of 3 rules are re-witnessable (score 1.00).
