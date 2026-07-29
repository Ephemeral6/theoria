# C8 · 分层移交包 — what was built, what it found, what it does not have

`prompt_id: C8-handover-package` · worker `W-1252` · branch `agent/c8-handover-package`
· `python -m tools.verify_c8` re-establishes every claim below.

## What exists now that did not

`theory_compiler.handover` — given a `theory.dsl`, an optional `playbook.dsl` and
**two or more** level instances, it writes a directory a fresh reader can be
handed *instead of* the repository. Two packages ship:

| package | tier | boards | forms present |
|---|---|---|---|
| `handover_packages/a0-cart` | `manual+playbook` | `base`, `no-button` | English, executable, proof |
| `handover_packages/a0-sokoban2` | `manual` | `match`, `crossing-up` | English, executable, proof |

Both tiers of Theoria 1.11 are represented, and by what the arms actually
produced rather than by withholding one: `cold-start-a0` shipped a playbook,
`a0-spike` did not.

## The acceptance, and what it cost

The bar in the work order is **答错即包不合格 — 修包不修读者**. Two rounds, each a
fresh subagent given one staged copy of a package outside the repository, told it
may read every file and **may not execute any of them**, and told to abstain
rather than guess. Truth is computed from the package's own compiled predictor,
never from the repository.

| round | package | score | abstentions |
|---|---|---|---|
| 1 | `a0-cart` | 24/25 | 0 |
| 1 | `a0-sokoban2` | 29/29 | 0 |
| 2 | `a0-cart` | **24/24** | 0 |
| 2 | `a0-sokoban2` | **29/29** | 0 |

Round 1 is kept in `acceptance/round1/`. Its one wrong answer was **the sheet's
fault, not the reader's**: `effect_of_teleport_down` was classed `world_law`
because the probe measured the same displacement on both boards, but the
teleport lands on the cell `portal_exit` names and only a board says where that
is. The reader said `level_data` and was right. `_effect_origin` now reads the
compiled effect and classes any rule whose effect reaches `LANDMARKS[...]` as
board-supplied; such an item is then dropped when the boards agree.

**The reports were worth more than the scores.** Everything in the next two
sections came out of a reader's write-up, not out of a mark.

## Four defects fixed, all of them "the package lies and the reader is blamed"

* **`gen_markdown` dropped every negation.** `GuardPredicate.negated` was read by
  nobody, so `not free(ahead(Player, ?d))` rendered as *"ahead is free"* — the
  human form of the manual asserting what the manual denies, on three of six
  rules of the sokoban world.
* **`gen_markdown` printed reprs.** A `forall` variable had no branch, so every
  schema rule read `moved(Player, VarRef(name='d'))`; domains and landmarks were
  not rendered at all, so `?d` arrived with nothing saying what it ranges over.
* **`gen_markdown` invented a peg.** Event rendering dispatched on name alone, so
  `jumped(Cart, portal_exit)` fell into the peg-solitaire branch and read *"a peg
  jumps"* — in a world with no peg, with the destination dropped. Dispatch is now
  on name **and arity**, wording taken from what `gen_python._effect` compiles.
* **`gen_pddl`'s problem half fabricated a board** — every object on `cell-0-0`,
  walls ignored. It now takes an optional `ProblemSpec` and emits the level's
  real geometry with landmarks resolved.

## The gate that matters most: generated is not checked

The first cart reader judged `manual/DOMAIN.pddl` unusable while `MANIFEST.json`
recorded it `"status": "generated"`. D-TC-031 had already logged two of its
faults; the reader found a third (`push-up` tests `adjacent-above`, the predicate
block declares `adjacent-up`). Their sentence is the finding: *"if I had treated
the PDDL as authoritative, both optimal-action answers would be wrong."*

`handover.check_pddl` now runs this track's own `strips.parse_domain` +
`strips.ground` before any PDDL is called generated. Neither package ships a
planning form any more; both say so on their front page with the generator's own
message. The backend is **not** repaired here — D-TC-031's judgement stands and
the repair is somebody's work order (`monitor/inbox/20260728T145500Z-W-1252-…`).

## Gaps — carried, not closed

1. **`gen_pddl`'s domain is unsound.** Above. Gated, not fixed. Consequence:
   neither package has a planning form, so **the "four co-derived forms" claim is
   3-of-4 in practice for both worlds shipped.** Stated on each README.
2. **`gen_python` emits rules for objects a level does not instantiate.** The
   `no-button` predictor carries `_effect_press_left` assigning
   `state.Button_color` on a `State` with no such field; it is in `RULES` and
   would raise if reached. Unreachable by accident of the board, not by
   construction. Both cart readers found it independently.
3. **`gen_lean` ships theorems whose names claim more than they prove.**
   `reachable_closed` is `(step s a = step s a) = True`; `goal_is_reachable` is
   `∃ s, Goal s = true` and never mentions `Reachable`. Both readers used the
   transition table as data and declined the theorems as evidence.
4. **`gen_lean`'s state encoding is opaque** — 300-odd anonymous `sN` and no table
   saying which is which. Recoverable by hand-tracing from `s0`; it is the only
   form in either package that cannot be read without re-deriving something the
   generator knew and dropped.
5. **The upstream `a0-spike/theory/theory.dsl` yields no package at all**, and the
   refusal is earlier than the known `dir`-is-free blocker: it declares
   `slid(o, dir)` where the language implements `slid(o, pusher, dir)`, so half
   the event's effect is unnamed and there is no statement of what it does to
   hand a reader. Ledger X-1 from the handover side. Measured in
   `upstream_vs_shipped.json`; the shipped manual is the v0.3 migration and the
   substitution is in that package's `MANIFEST.json`.
6. **Neither package's boards are fresh.** They are the boards each manual was
   adjudicated against. Choosing unseen instances is the exam's job (1.11's
   「全新实例」), not the package builder's; what these two demonstrate is the
   domain/problem split, for which any two boards suffice. A real handover
   *measurement* must supply its own.
7. **The level-data family drops names it cannot demonstrate.** Both packages'
   boards are the same size, so `board_shape` — level data by any reading — is
   excluded rather than asked, because this package cannot *show* it varying.
   8 names excluded for `a0-cart`, 3 for `a0-sokoban2`, each with its reason in
   the sheet's `excluded` field. The family is also class-imbalanced (12 world-law
   to 1 level-data on `a0-cart`); under a zero-error bar that costs nothing, but
   a fraction-correct score off this sheet would be uninterpretable.

## Deliverable defects carried verbatim, on purpose

Both readers found that the manuals contradict the boards shipped beside them:
`a0-spike`'s `unsolvable_mismatch` is tagged `probe: passed` and is false on both
sokoban boards; the cart's `door_latch` invariant is `[status: proven]` and reads
0 = 1 on `no-button`; both manuals bake a board constant into a law
(`mod 2 = 1`, `goal Cart.pos = (2, 7)`).

**None of this is repaired.** A package that quietly fixed the deliverable would
be handing over a document nobody shipped. What the package does instead is point
at it, mechanically: `GLOSSARY.md` lists every number written into the manual, and
— added after the round-2 reader observed the glossary was pointing at the
invariants and not at the theorem that actually fails — a section listing every
invariant and theorem beside the evidence tag its author gave it, under the
sentence *a tag is a claim about evidence that is not in this package*.

## Honest note on version drift

The round-2 readers were handed a staged copy that differs from what ships in
exactly two files: `README.md` (a "in this package?" column added to the forms
table) and `MANIFEST.json` (its digest of that README). No file any answer
depends on differs. Sheet wording was then also corrected from their reports
(`goal_form`'s definition, `wall_cells` naming a term the package does not use,
the sheet presenting a world-law vocabulary keyed per board); item ids are
content-hashed and stable, so the recorded answers still mark against the current
sheet — `verify_c8` re-marks them and gets 24/24 and 29/29.

## Reproduce

```bash
cd theory-compiler
python -m tools.build_handover_packages          # write both packages
python -m tools.build_handover_packages --check  # byte-for-byte against disk
python -m tools.handover_exam sheet handover_packages/a0-cart /tmp/t.json \
    --reader-out /tmp/sheet.json
python -m tools.verify_c8                        # all six checks
```

Zero network, zero model calls in the build or the marking, zero sealed-pile
contact, $0.00. The two readers were Claude subagents; they are the measurement,
not part of the artefact, and nothing they produced is on any generation path.
