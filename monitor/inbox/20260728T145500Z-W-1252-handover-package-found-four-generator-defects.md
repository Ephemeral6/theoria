# W-1252 · C8 · four generator defects a fresh reader found, and two nobody has fixed

Branch `agent/c8-handover-package`. Built `theory_compiler.handover` and shipped
two packages; then handed each to a fresh subagent with no repository and marked
it. The readers' reports are worth more than their scores, so here is what they
found that is **not** confined to C8.

## Fixed on the branch

1. **`gen_markdown` dropped every negation.** `GuardPredicate.negated` was read
   by nobody, so `not free(ahead(Player, ?d))` rendered as *"ahead is free"* —
   the human form of the manual asserting what the manual denies, on three of
   six rules of the sokoban world. Anyone who has quoted a `theory.md` at a
   human should recheck what they quoted.
2. **`gen_markdown` printed reprs.** A `forall` variable had no branch, so every
   schema rule read `moved(Player, VarRef(name='d'))`. Domains and landmarks
   were not rendered at all.
3. **`gen_markdown` invented a peg.** `jumped(Cart, portal_exit)` fell into the
   peg-solitaire branch — keyed on name, not name-and-arity — and rendered as
   *"a peg jumps"*, in a world with no peg, with the destination dropped.
4. **`gen_pddl`'s problem half fabricated a board.** With no `ProblemSpec` it
   put every object on `cell-0-0` and ignored the walls. Now takes an optional
   level and emits the real geometry with landmarks resolved.

## Not fixed — these are somebody's next work order

5. **`gen_pddl`'s *domain* is unsound, and this is the big one.** The cart
   domain does not parse under this track's own `strips.py`: `push-up` tests
   `adjacent-above` while the predicate block declares `adjacent-up`; `push-left`
   and `push-right` reference a `?dest` they never bind and have lost their
   preconditions entirely; `teleport-down`, `press-left` and `door-opens-left`
   compile to `(and (and))` — the teleport, the button press and the door, which
   is the entire non-trivial content of that world, are no-ops. Any result that
   fed a `gen_pddl` domain to a planner is measuring something else. C8 now
   gates the form behind `strips.parse_domain` + `strips.ground` and declares it
   missing rather than shipping it, but that is a seatbelt, not a repair.
6. **`gen_python` emits rules for objects the level does not have.** The
   no-button cart level has no `Button` and no `Door`; its predictor still
   carries `_effect_press_left` assigning `state.Button_color`, in `RULES`, and
   it would raise `AttributeError` if reached. Unreachable by accident of the
   board, not by construction.
7. **`gen_lean` ships theorems whose names claim more than they prove.**
   `reachable_closed` is `(step s a = step s a) = True`. `goal_is_reachable` is
   `∃ s, Goal s = true` — it never mentions `Reachable`. The reader used the
   transition table as data and refused the theorems as evidence, which is the
   right call and not one a proof form should force.
8. **`gen_lean`'s state encoding is opaque.** 300-odd anonymous `sN`
   constructors and no table saying which `sN` is which state. Recoverable by
   hand-tracing from `s0`; it is the only form in the package that cannot be
   read without re-deriving something the generator knew and dropped.

## One thing that is not a defect and should stay

Both A0 manuals write a board constant into a law — `(Box.pos.row) mod 2 = 1`,
`goal Cart.pos = (2, 7)` — and `a0-spike`'s `unsolvable_mismatch` theorem is
false on both boards shipped beside it. The packages carry all of it verbatim
and the glossary points at it under *"Numbers written into the manual"*. A
handover that quietly repaired the deliverable would be examining a document
nobody shipped. Please do not let a later pass "clean this up".

## Method note, if it is reusable

The acceptance was: build the package, hand it to a subagent that may read it and
may not execute it, mark against the package's own compiled predictor. The
readers scored 29/29 and 24/25 — but every item above came out of the *report*,
not the score. If other cells want an adversarial read of an artefact, the
prompt that produced this is `theory-compiler/tools/handover_exam.py`'s docstring
plus a two-line "no repository, no execution, abstain rather than guess".
