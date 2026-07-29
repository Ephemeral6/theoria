# Transcription lens — adversarial review of `recheck/build_cases.py`

**Question asked:** are the JSON rule sets under `recheck/cases/` faithful
re-descriptions of the worlds they claim to describe?  If not, every verdict the
rechecker produces about them is worthless.

**Answer: 0 concrete discrepancies found.**  Every check below was actually run,
not reasoned about.  Scripts are in this directory and are re-runnable:

| script | what it does |
|---|---|
| `a2_differential.py` | rule-set `step` vs `cold-start-a2` compiled predictors, whole product |
| `replay_world_episode.py` | rule-set `rendered` vs the WORLD's own 19 recorded frames, pixel by pixel |
| `pagoda_and_anchors.py` | `def w` in the Lean file vs the certificate's `w` table; DSL rule lists; sokoban optima |
| `sokoban_differential.py` | rule-set `step` vs a generically-parsed, generically-grounded PDDL STRIPS simulator |
| `deadlock_spotcheck.py` | the shipped dead-region theorems vs the carver's actual output and the fixture geometry |

`python -m recheck.build_cases --check` → `30 cases, 0 drifted`, so the JSON I
inspected is exactly what the generator emits.

Nothing outside this directory was written.  `sys.dont_write_bytecode = True` is
set before any import so that reading `cold-start-a2` cannot even drop a
`__pycache__` there.

---

## 1. `a2-world.rules.json` / `a2-holed.rules.json`

### The strongest check: differential `step` over the whole product

`a2_differential.py` loads each rule set, enumerates its declared product
(button ∈ {7,8} × cart ∈ 37 arena cells × door ∈ {no,yes} = **148 states**),
maps each to a `theory.State`, and compares.

```
== a2-world vs generated/          == a2-holed vs generated_holed/
   n_states=148, n_rules=7            n_states=148, n_rules=6
   init MATCH                         init MATCH
   BOARD literal: 81/81 agree         BOARD literal: 81/81 agree
   rendered(): 11988/11988 agree      rendered(): 11988/11988 agree
   free():     11988/11988 agree      free():     11988/11988 agree
   is_goal:    148/148 agree          is_goal:    148/148 agree
   step:  592 agree, 0 disagree       step:  592 agree, 0 disagree
   fired-rule-name sets differing: 0  fired-rule-name sets differing: 0
```

592 = 148 × 4 actions, both worlds.  The `fired` comparison is stronger than
`step` alone: it checks that the *same named rules* fire, not merely that the
successors coincide, so a rule that happened to be a no-op in the right places
could not hide.

Sanity anti-check (a differential that finds nothing proves nothing unless it can
find something): the `a2-world` rule set vs the **holed** predictor gives
**4 disagreements** — exactly the 4 states with `cart=(6,4)` (2 button values ×
2 door values), action `down`.  That is the teleport, and nothing else.

Point by point, on the questions asked:

* **BOARD literal identical** — yes.  Compared cell by cell against
  `generated_holed/theory.py` *and* `generated/theory.py`; the two BOARD literals
  are themselves identical, so `A2_BOARD` is right against both.  81/81.
* **Render draw order** — correct, and this is the subtlest thing in the file.
  `render()` paints board → Button → Cart → Door, so the *last* drawn wins:
  **Door > Cart > Button > board**.  The JSON `rendered` def is an `if`-chain in
  the *reverse* order (Door tested first, then Cart, then Button, else `board`),
  which is the correct inversion of "last drawn wins".  Getting this backwards
  would have been invisible in most states and fatal in two: `cart=(1,1)`
  (Cart over Button) and `cart=(6,4)` with `door=yes` (Door over Cart).
  Verified over all 148 × 81 = 11 988 (state, cell) pairs against `render()`
  itself, so both of those cases are covered by construction.
* **`free` / `colored` semantics** — correct.  `free(x)` is
  `rendered(x) == 0`, matching `_free` = `_cell_colour(...) == BACKGROUND`, where
  `_cell_colour` reads *off the rendered frame*, not off BOARD.  This matters:
  the Door at (6,4) makes a background cell non-free, and the Button at (1,1)
  makes a background cell non-free.  The `colored(_, 3)` / `colored(_, 7)` guards
  are likewise `rendered(...) == 3` / `== 7`, not board lookups.  11 988/11 988
  agree on `free` too.
* **Teleport destination** — `A2_PORTAL_EXIT = (7,6)` matches
  `generated/theory.py`'s `LANDMARKS = {'portal_exit': (7, 6)}`.  (The DSL names
  the landmark but does not give its coordinate; the compiled form is the
  operational definition, and that is what was transcribed.)
* **Goal** — `(2,7)`, matching `is_goal` in both compiled forms and
  `goal Cart.pos = (2, 7)` in both DSLs.  148/148 agreement on the goal predicate.
* **Initial state** — `button=7, cart=(5,1), door=yes` matches
  `initial_state()`: `Button_colour=7, Cart_pos=(5,1), Door_present=True`.
* **`conflict exclusive` / `frame persist`** — reproduced.  `RuleSet.step`
  raises on two rules writing one variable and leaves untouched variables alone;
  `theory.py`'s `step` raises `AmbiguousTransition` on two rules claiming one
  *object*.  In A2 the object↔variable map is 1:1 (Cart↔cart, Button↔button,
  Door↔door) and the `owns` fields match `RULES`' owner column exactly.  The
  obligation `step_single_valued` is **true** over the whole product for both
  rule sets, and no `AmbiguousTransition` was raised on any of the 592 pairs, so
  the two policies are not merely compatible in principle, they never fire.
  The one place they could have collided — `push_down` vs `teleport_down`, both
  owning `cart` on action `down` — is excluded because the guards
  (`rendered(below)==0` vs `==3`) are disjoint.
* **Nothing missing, nothing extra** — the DSL `rules:` sections and the JSON
  rule name lists are set-equal:
  `theory.dsl` = {push_up, push_down, push_left, push_right, teleport_down,
  press_up, door_opens_up} = `a2-world.rules.json`;
  `theory_holed.dsl` = the same minus `teleport_down` = `a2-holed.rules.json`.
  The two rule sets differ by exactly one rule, as advertised.

### Extra check the brief did not ask for: replay against the WORLD

`replay_world_episode.py` replays A2's recorded 18-action winning episode
(`cold-start-a2/artifacts/solved_episode.jsonl`, 19 frames captured from the
actual game) through the rule set's own `rendered`, comparing all 81 pixels of
all 19 frames and the win flag:

```
a2-world.rules.json    19 frames, 0 mispredicted pixels, win flag agrees throughout
a2-holed.rules.json    19 frames, 14 mispredicted pixels, first at t=12 cell (6,4);
                       win flag disagrees at t=18 (rules=False, episode=True)
```

So `a2-world` is not just faithful to the compiled control manual — it is
faithful to the world, 1539/1539 pixels.  And `a2-holed` diverges at exactly one
place: the teleport step, action 11 (`DOWN`) from `(6,4)`.  That is the exhibit
behaving as claimed.

### One structural observation (not a discrepancy)

Neither A2 rule set declares a `constraint`, so the enumerated product contains
physically unreachable states: `cart=(1,1)` (on the Button), `cart=(6,4)` with
`door=yes` (inside the closed Door), `cart=(7,1)` (a walled-off pocket).  This is
**correct**, and in fact necessary: Lean's `St` is exactly
`Cell × ButtonColour × DoorPresent` = 37 × 2 × 2 = 148 and `inv_closed` is proved
by `cases … <;> decide` over all of it.  The rechecker quantifies over the same
148 states the Lean proof does, so `inv_closed` here and `inv_closed` there are
the same obligation.  Had `build_cases` "helpfully" added a reachability
constraint, the recheck would have been weaker than the proof it re-checks.

---

## 2. Pagoda weight table vs Lean `def w`

`pagoda_and_anchors.py` parses `generated_holed/theory.lean` mechanically: the
`inductive Cell` constructor list, the doc-comment `cN = (row, col)` map, and the
37 arms of `def w`.

* The enum's constructors are `c0 … c36` in order, so the doc comment's index →
  cell map is index-correct and not merely adjacent-correct.
* Independently, `build_cases.a2_arena()` produces the 37 background cells in
  row-major order, and **`arena[i] == cell_map[i]` for all i** — the rig's cell
  index and Lean's cell index are the same function.  This is the mapping the
  brief flagged, and it is used correctly.
* `def w` has 37 arms, values only in {0,1}: **21 zeros, 16 ones**.
* Certificate `w` table: `default: 1`, 21 entries, all values `0`.
* **All 37 cells agree, 0 differ.**  The 21 zero cells are exactly

```
(1,3) (1,4)
(2,1) (2,2) (2,3) (2,4)
(3,1) (3,2) (3,3) (3,4)
(4,1) (4,2) (4,3) (4,4)
(5,1) (5,2) (5,3) (5,4)
(6,2) (6,3) (6,4)
```

  = Lean `c1 c2 c5..c8 c11..c14 c17..c20 c23..c26 c29..c31`.
* Goal cell `(2,7)` = `c10` carries weight **1** in both, as the Lean comment and
  the certificate comment both claim.  Init cell `(5,1)` carries 0.
  `portal_exit` `(7,6)` carries 1 — which is why the invariant breaks under the
  teleport and not merely under some accounting slip.
* The certificate's prose claim ("0 on the 21 cells the Cart was ever observed
  on") also checks out empirically: scanning colour 6 across all 184 frames of
  `artifacts/history_trace.jsonl` yields exactly those 21 cells.
* `predicate` = `w[cart] == 0` matches Lean `def I (s : St) : Bool := w s.cart == 0`.

End-to-end, the certificate does what it says: `ACCEPT` on `a2-holed`
(`inv_init`, `inv_closed`, `goal_break` all true) and `REJECT` on `a2-world`
(`inv_closed` false).

---

## 3. `sokoban-open4far.rules.json` / `sokoban-ringstuck.rules.json`

`sokoban_differential.py` does not trust any hand-reading of the PDDL.  It
tokenises and parses `sokoban_domain.pddl` into schemas (typed parameters,
precondition list, add/delete lists), parses the problem's typed objects and
`:init`, grounds every action instance whose *static* (`adj`) preconditions hold,
and then compares the grounded STRIPS transition system to the rule set's derived
`step`.  Nothing about sokoban is hardcoded except the file paths.

```
level       cells  adj/nb   init   goal   placements×actions checked/agree/differ   reachable (pddl/rules)  solvable
ringstuck   12 ✓   24 ✓     ✓      ✓      1 056 / 1 056 / 0                          44 / 44  identical     False/False
open4far    16 ✓   48 ✓     ✓      ✓      26 880 / 26 880 / 0                        3 352 / 3 352 identical True/True
ring        12 ✓   24 ✓     ✓      ✓      1 056 / 1 056 / 0                          44 / 44  identical     True/True
open4       16 ✓   48 ✓     ✓      ✓      26 880 / 26 880 / 0                        3 352 / 3 352 identical True/True
```

* **Grids, player, boxes, goals** — match `fixtures/sokoban.py`'s `Level`
  literals and the generated PDDL:
  `ringstuck` RING grid, player (1,1), b1@(1,2), goal b1@(3,1);
  `open4far` OPEN4 grid, player (4,4), b1@(2,2) b2@(3,3), goals b1@(4,2) b2@(1,3).
  Checked not by eye but by rebuilding the PDDL `:init` set from the rule set's
  `init` + declared cell domain and demanding **set equality including every
  single `(clear …)` fact** — which is how a mis-transcribed player or box
  position would show up even if the `at`/`at-player` facts happened to line up.
* **`nb` table vs `adj`** — set-identical in both directions, all 24 / 48 facts.
  So the neighbour relation carries exactly the wall geometry the PDDL grounds
  against, no more and no less.
* **`clear` covering the player as well as boxes** — yes, and this is checked
  behaviourally, not textually.  The rule set's derived
  `clear(x) := x != none ∧ x != player ∧ x != b1 ∧ x != b2` is compared against
  the PDDL's `clear` fluent as it actually evolves through the add/delete lists.
  If `clear` had been transcribed as "no box" only, the rule set would allow a
  `move` onto the player's own cell and a `push` that shoves a box onto the
  player, and both would appear as `PDDL-FORBIDS-RULES-ALLOWS`.  Zero such.
* **Anything the PDDL allows that is disallowed here, or vice versa** — checked
  in both directions and separately labelled (`PDDL-FORBIDS-RULES-ALLOWS`,
  `RULES-FORBID-PDDL-ALLOWS`, `DIFFERENT-SUCCESSOR`).  All zero.  The check runs
  over **every canonical placement**, not only reachable ones: all
  16·15·14 = 3 360 (open4far) and 12·11 = 132 (ringstuck) distinct
  (player, boxes) assignments, times 8 actions.  So an encoding error confined to
  states the search never visits would still have been caught.
* The comparison also asserts that every PDDL successor of a canonical state is
  itself canonical (the `clear` set stays exactly "cells with nothing on them").
  It is, everywhere — which is the machine-checked form of the domain comment
  that `clear` is maintained rather than assumed.
* **Reachable sets coincide exactly**, and the placement↔PDDL-state map is
  injective on them (44 ↔ 44, 3 352 ↔ 3 352).  Solvability agrees:
  `ringstuck` unsolvable on both sides, `open4far` solvable on both.
* **Optimum anchors** (the reason the un-certificated `ring` / `open4` cases are
  in the corpus at all): BFS over the rule set gives `ring` = 1 and `open4` = 6,
  matching the hand-derived optima in `fixtures/sokoban.py`.
* **Declared constraint is honest** — `constraint_init` and `constraint_closed`
  are both true for all four levels, so the "distinct occupants" restriction is
  proved inductive rather than assumed, and cannot be hiding an escaping
  transition.
* **Dead-region theorems** (`deadlock_spotcheck.py`, beyond the brief): all 2
  ringstuck and all 16 open4far patterns are genuinely closed under every action
  and contain no goal state — 0 leaks each.  And they are byte-for-byte the
  patterns `engines/deadlock_carver` actually emits when re-run against the
  fixtures today (2 and 16, same order), so `RINGSTUCK_THEOREMS` /
  `OPEN4FAR_THEOREMS` are transcriptions of engine output, not of intuition.

---

## Observations that are not discrepancies, but are worth someone's attention

1. **`ringstuck` ships 2 of the 4 corner deadlocks the geometry supports.**
   `(4,1)` and `(4,4)` are corners of the ring and are not the goal, so
   `at(b1, ·)` there is dead — but no certificate is shipped for them.  This is
   *not* a transcription error: the carver itself emits only the two, because it
   derives patterns from reachable pairs and b1 cannot reach the bottom row.  It
   is an incompleteness in the engine's output, faithfully transcribed.  Nothing
   here is unsound.

2. **Certificate→rule-set binding is by name only.**  `peg4-0111-ic3` and the 18
   sokoban dead-region certificates carry `"ruleset": {"name": ...}` with no
   `sha256`, and `verify._binding_ok` only compares the digest when one is
   present.  A rule set could therefore be swapped for a differently-hashed one
   of the same name and the binding condition would still go green.  The A2
   certificate carries no binding at all — deliberately, since it is rechecked
   against both `a2-holed` (ACCEPT) and `a2-world` (REJECT), which is the whole
   exhibit.  Out of scope for a transcription review; flagging it because the
   `sha256` field exists and is simply not populated.

3. `build_cases.py`'s module docstring says the boards are transcribed from
   `generated_holed/theory.py`, while the `a2-world` provenance block points at
   `generated/theory.py`.  Both BOARD literals are byte-identical (verified
   81/81 against each), so the two statements are consistent; noting it only
   because a future edit to one compiled form would silently break the other's
   provenance claim.

---

## Verdict

**No discrepancy found, in 0 of the checks — and the checks were run.**
Totals actually executed: 1 184 A2 state-action pairs across two rule sets
(0 disagreements), 23 976 (state, cell) render comparisons (0), 1 539 world
pixels replayed (0), 37 pagoda cells (0), 55 872 sokoban placement-action
comparisons across four levels (0), 4 reachable-set identities, 2 optimum
anchors.  The one thing most likely to have been wrong — the render draw order,
where "Door then Cart then Button" has to become an `if`-chain in the opposite
order — is right.
