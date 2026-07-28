# THEORIZE log — A0

The adjudication record. Engines propose; this is where the LLM decides what
enters the manual, and why. Each entry is a decision, its evidence, and what it
cost or bought.

---

## T-1 · Two objects, and a board

**Proposed by** `mdl_segmenter` (colour-splitting operator).

**Evidence** 5 connected components across every frame. Two of them account for
every event in the edit script; three never move.

**Adjudicated** `object Player { pos: Cell }`, `object Box { pos: Cell }`. The
three static components settle into `board` — "what never co-varies is the
board" (Theoria 1.8), and they need no name of their own.

**Cost** the edit script runs 373 bits against a 412-bit per-pixel baseline on
the longest episode. A real but unimpressive win: this world's typical
transition moves one cell, so a pixel dump is only two edits and there is little
to compress. The Cart fixture's 0.29 ratio is not the number to expect here.

---

## T-2 · The colour-splitting segmentation operator

**Why it is in the manual** The default colour-agnostic operator fuses the player
with any wall it stands against and with the box it is about to push, and the
trajectory becomes unreadable. Which operator a world needs is part of the
manual, not a hidden default (Theoria 1.8: the operator hypothesis space).

**Adjudicated** recorded as the segmentation method for this world.

---

## T-3 · `walk` — accepted immediately

**Proposed by** `cegis_miner` core, four rules, 56–101 witnesses each.

    act==D and ahead_free(D)  ->  player moves one cell

**Adjudicated** in. Well-evidenced, uniform across all four directions, and it
lifts to one schema over `?dir`.

---

## T-4 · `push2` — rejected on the first pass, accepted on the second

**First pass** (a 28-step casual walk) gave

    act==D and ahead_is_box(D)  ->  box moves two cells

with **one witness per direction**. Replay was exact. The rule is still wrong:
it predicts a push even when the box has nowhere to go.

**This is the DC22 shape** — perfect on history, broken on the unseen. Accepting
it because replay passed is exactly the failure the framework exists to catch, so
it was refused.

**Probe** The discriminating situation is "box ahead, but the cells it would
cross are not clear". Exploration was re-planned to witness each *situation*
rather than each *outcome*, reaching those states by prefix replay.

**Second pass** with 341 transitions:

    act==D and ahead_is_box(D) and box_beyond_free(D)  ->  box moves two cells

12–19 witnesses per direction. **Adjudicated in.** The probe cost 341 actions and
bought the difference between a rule that replays and a rule that holds.

---

## T-5 · `blocked` — the guard language bites

**Finding** No single conjunction covers the class. "Nothing moved" is genuinely
disjunctive: a wall ahead, *or* the box ahead with its path obstructed.
`cegis_miner.synthesize` raised `NoSeparatingGuard`, correctly.

**Adjudicated** as *several* rules with conjunctive guards whose disjunction is
the class — sequential covering. Every individual rule stays inside the frozen
grammar, which says guards are conjunctions. The alternative (adding disjunction
to the guard language) would have needed a contract change and an entry in the
expressiveness ledger; it was not taken.

**Known wart** `blocked_DOWN_1` carries literals about LEFT and RIGHT that are
accidental. Greedy covering found a local optimum. It is sound on all 341
transitions — replay is exact and every transition has exactly one successor —
but it is not the rule a person would write. Recorded rather than hand-edited:
the manual is supposed to say what the evidence forced.

---

## T-6 · The conservation law — the engine found a stronger one than I proposed

**I proposed** `(box.row + box.col) mod 2 = 0` — the box never changes
checkerboard colour.

**`zero_space` returned** a null space of dimension **2**, basis `[[1,0],[0,1]]`:
`box.row mod 2` and `box.col mod 2` are *each* conserved, separately. That is
strictly stronger, and it is true — a push moves the box by two cells along one
axis, so each coordinate's parity survives on its own.

**Adjudicated** the stronger pair goes into the manual; the sum is kept as a
derived corollary because it is the form the unsolvability argument uses.

**Why this entry matters** The engine corrected the adjudicator, which is the
division of labour working in the direction it was designed to work in: the
engine computes, the LLM decides, and the LLM was wrong.

---

## T-7 · The unsolvability theorem

**Adjudicated**

    theorem unsolvable_mismatch
      "箱子每次滑动两格，(row+col) 的奇偶不变；开局箱子在偶格，目标格是奇格，
       所以永远到不了"

Three lines, no search: the law holds at the start, no rule breaks it, and
winning requires breaking it.

**What it bought** On `mismatch` the planner exhausts the state space to report
"no plan". The theorem answers in one arithmetic step and, unlike the planner,
says *why*. That gap — a certificate against "I searched and found nothing" — is
the whole thesis, and A0 shows it on a world small enough to check by hand.

---

## T-8 · Compiling the manual caught an error the mined rules had not

**What happened** certify was rewired to replay history through the executable
form compiled from `theory.dsl`, rather than through the miner's in-memory rule
objects. The generated code immediately walked the player off the board.

**Cause, in the manual, not the engine** I had adjudicated

    rule blocked_wall  ... then moved(Player, dir)
    rule blocked_box   ... then moved(Player, dir)

The mined rules had the right effect all along — `(0,0), (0,0)`, nothing moves.
The error was in my transcription of them into the manual, and the event
vocabulary was complicit: `moved | slid` had no way to say "nothing happened", so
the nearest available event was a movement one.

**Adjudicated** `stayed(o)` added to the event vocabulary; both blocked rules now
end `then stayed(Player)`.

**Why this entry is the point of the exercise** Replaying through the mined rules
would never have found this: those rules were correct. Only the compiled manual
is accountable for what the manual actually says, which is exactly why the
framework insists the sole predictor be generated from it. One rewiring, one real
error caught, in a manual I had already reviewed and called done.

---

## T-9 · Held-out testing found a wrong rule that replay could not

**What happened** With certify green — 341 transitions replayed exactly through
the compiled manual — the theory was checked against the world on *every*
well-formed state of the board, not just the observed ones. **8 mismatches.**

**The missing literal** `push2` required only `free(beyond(Box, dir))` — the cell
the box lands on. The world also requires `free(ahead(Box, dir))` — the cell the
box *crosses*. Example: player (1,3), box (1,4), RIGHT. The landing cell (1,6) is
free, so the theory pushed; the crossed cell (1,5) is a wall, so the world did
nothing.

**Why no amount of exploring `match` could have found it** The box's crossed cell
always has odd parity, and every wall in `match` sits on an even cell. "Blocked
while crossing" is not merely unobserved there — it is **unreachable**. All 8
mismatching states are unreachable from `s0`; on the 315 reachable states the
theory was already exact.

**So the rule was right as a *problem* solution and wrong as a *domain*.** That
distinction is the frozen contract's own (`word_table + rules + laws` is domain,
the layout is problem), and it has teeth: a manual meant to travel between levels
cannot be pinned down by one level's evidence.

**Adjudicated** four more evidence levels, one per direction, each with a wall on
an odd-parity cell so that "blocked while crossing" becomes reachable in that
direction. Evidence pooled across all five. The mined guard gained
`box_ahead_free(dir)` in every direction, and `blocked_box` split into
`blocked_box_crossing` and `blocked_box_landing` — two conjunctions, because the
disjunction cannot be one.

**Result** 39,960 well-formed states across five levels, **0 mismatches**.

**What this cost and bought** 1,966 actions instead of 341. It bought the
difference between a theory that is right about the level it was learned on and
one that is right about the world. Replay said "exact" both times.

---

## T-10 · Variant injection: one rule changed, four times

Not an adjudication but a measurement, and the exam item it answers is
"改一条规则,多快适应回来".

| variant | one rule changed | detected on `match` | detected anywhere | theorems hit | old verdict |
|---|---|---|---|---|---|
| `ghost` | walls stop being solid (a `walk` guard) | 6 actions | 6 actions | none | still correct |
| `push1` | box slides 1 instead of 2 (effect) | 18 actions | 18 actions | `unsolvable_mismatch` | **flipped** |
| `push3` | box slides 3 instead of 2 (effect) | 18 actions | 18 actions | `unsolvable_mismatch` | still correct |
| `nocross` | the box may pass through an obstructed cell (a guard) | **never, in 341 actions** | 6 actions | `unsolvable_mismatch` | still correct |

Every variant repaired to a replay-exact theory with the effect the injection
actually made.

**Detection latency is about firing frequency, not about the size of the change.**
`ghost` weakens a guard on `walk`, which fires on nearly every action, and it is
caught in 6. `nocross` weakens a guard on `push2` in a way that only shows when
the box is blocked by the cell it crosses — and in `match` that configuration is
*unreachable*, so the changed world replays perfectly for 341 actions. The world
changed and the theory noticed nothing.

**Where you look decides whether you notice at all.** The same `nocross` change is
caught in 6 actions once the `crossing_*` levels are in play. That is the same
parity argument as T-9, arriving from the other direction: there, evidence from
one level could not *pin down* a rule; here, it cannot *refute* one.

**The one that matters is `push1`.** Sliding one cell instead of two destroys the
conservation law, and `mismatch` — the level the manual proves impossible —
becomes solvable. The old theory goes on asserting a false impossibility. Nothing
in replay catches this; the surprise is detected 18 actions in, but detecting a
prediction failure does not by itself tell you that a *theorem* is now false. What
does is the declaration `theorem unsolvable_mismatch [depends: push2]`: the
changed rule is named, so the theorem is pulled up for re-examination
automatically.

That is exactly the failure mode the whole architecture is built against — a
confident, well-supported, false claim of impossibility — and here the dependency
edge is the only thing standing between the agent and it.

---

## T-11 · `semantics:` — three facts about this world that the manual never said

Run `runs/20260728T040057Z-c2` · prompt `C2-semantics-migrate` ·
contract `CONTRACTS/dsl_grammar_v0.2.md` revision item 1 (ledger E-03).

**What happened** `theory_compiler`'s parser made `semantics:` mandatory and
began rejecting this manual outright. All 32 of a0-spike's failures were that one
`SemanticsError`. The merge referee (OPS-M) declined to patch it, correctly: the
three statements are assertions about the A0 world, not wiring, and choosing them
wrong compiles a different world *silently*.

**The rule this entry is written under** is the contract's own migration note —
*"Do not copy these three values from another manual… If you do not know which is
true, that is a finding to probe, not a default to accept."* A0 and A2 both
declare `persist` / `exclusive` / `single_frame`, and this manual ends up
declaring the same three. **That is a measurement, not an inheritance**, and the
sub-entries below are what separates the two. Each value was adjudicated by
*refuting its alternative with a concrete witness*, never by the chosen value
merely fitting: `persist` and `reset` agree on every transition in which a rule
happens to mention every object, so a probe that only confirmed would have
noticed nothing.

Instrument: `probes/semantics_probe.py`, over **47,040 representable
state-action pairs** across all five evidence levels — the same set T-9's
held-out check uses, widened by 7,080 (see FINDING-2 in the run's `RUN_STATE.md`).
Ground truth grades; it never predicts.

**A value is adjudicated on the cases that *discriminate* between the two
readings**, not on a hand-picked subset of states. Cases where both readings
mispredict are evidence about neither, and there are 52 of them — all one shape,
all a `push2` guard defect, ledger X-5. Two earlier revisions of this probe got
that wrong in opposite directions: the first filtered the 52 out by reachability,
which D-TC-012 forbids; the second filtered them out by claiming the states have
no frame of their own, **which is simply false** — `render` is injective within a
level (measured: 2,352 states of `match`, 2,352 distinct frames, 0 collisions).
The adversarial review caught the second, and the fix was to stop filtering and
change the verdict rule instead. `runs/20260728T040057Z-c2/ADVERSARIAL_REVIEW.md`
carries its report unedited.

### T-11a · `frame persist`

**Proposal** `persist` — an object no firing rule mentions is unchanged.

**Evidence** Over all 47,040 pairs: **`persist`-only wrong 0**, **`reset`-only
wrong 45,630**, both wrong 52. Witness: `match`, player (0,0), box (0,1), DOWN.
The world walks the player to (1,0) and leaves the box at (0,1). `walk` is the
only rule that fires and it claims only the Player, so under `reset` the box —
mentioned by no firing rule — returns to its declared initial (3,3). It teleports
home on every step the player takes. Under `persist`, **0 mismatches**.

**The objection worth answering.** The probe also reports that *exactly one rule
fires for every one of the 47,040 pairs* — the rule set is total, 0 states with
no rule. If a rule always fires, is `persist` doing any work, or is it
unfalsifiable here? It is doing work, because the frame axiom is **per object,
not per state**. `walk` fires on 372 `match` transitions and claims the Player
only; on every one of them the Box is an object no firing rule mentions. Totality
of the rule set and vacuity of the frame axiom are different properties, and A0
has the first without the second.

**Adjudicated** `persist`. Cost: nothing — it is what all four forms already
encoded.

**What it does *not* buy here, corrected.** An earlier draft of this entry said
`persist` now rejects "the eleven `*_still_*` no-op rules R-07 rejected" on paper
rather than by appeal to a comment. **That is `cold-start-a0`'s R-07, not this
directory's** — a0-spike's log runs T-1…T-11 and has no R-series at all. The
claim was imported from `cold-start-a0/proposals/dsl_grammar_v0.2_semantics.md`
without checking that it transfers, which is the exact failure this whole section
exists to prevent, committed inside the section. Recorded rather than quietly
deleted.

The truth for a0-spike is the opposite and is worth more than the error was:
**this manual keeps its no-op rules, and it must.** The three `blocked_*` rules
emit `stayed(Player)` and are the only rules covering their guard region, so they
are what makes the rule set *total*. Measured — strip them and compile:

```
RuntimeError: no rule fired for UP in State(player=(0,0), box=(3,3))
              -- the rule set is not total, so the manual determines no successor
```

So the frame axiom removes a clause only when **some other rule already fires**
and simply fails to mention the object in question. It says what happens to
objects no firing rule mentions; it cannot say what happens when *no rule fires
at all*. cold-start-a0's eleven were redundant in the first sense. a0-spike's
three are load-bearing in the second, which is also why `stayed(o)` had to be
invented as an event at all (see the note at the head of `events:`). Two
directories, one axiom, opposite consequences — and the distinction is invisible
if you read the axiom as "no-op rules are unnecessary".

### T-11b · `conflict exclusive`

**Proposal** `exclusive` — at most one rule per object per transition.

**Evidence, route 2 (exhaustive sweep).** Over all **47,040** pairs: maximum
rules firing simultaneously **1**; maximum rules claiming a common object **1**.
Both strata, so this discharge is **unconditional** — not relative to any
undeclared well-formedness condition, which v0.2 §"Discharging `conflict`" would
have made a defect report in its own right.

**The trap, and it is the reason this sub-entry is not one line.** `push2` emits
`slid(Box, dir)`, and reading the event name alone says it claims the Box. It
does not: `gen_exec._compile_effect` moves the Box two cells **and carries the
Player one**, because the frozen grammar gives a rule exactly one event while a
push visibly does two things. v0.2 makes the obligation range over rules whose
*claimed objects intersect*, so `slid` must be read **wide** — `{Box, Player}` —
or the check quietly ranges over fewer pairs than it should. Read wide, `push2`
collides in scope with all three `blocked_*` rules and with `walk`, and the sweep
still returns 1. Read narrow, the number would also have been 1, and it would
have meant less. Ledger entry X-1 below is the same fact seen as a limitation.

**Evidence, route 1 (guard analysis), and it is the stronger of the two.** Write
the four guard atoms as `A = free(ahead(P,d))`, `B = (Box.pos = ahead(P,d))`,
`C = free(ahead(Box,d))`, `D = free(beyond(Box,d))`. The five guards are then:

| rule | guard | claims |
|---|---|---|
| `walk` | `A` | Player |
| `push2` | `B ∧ C ∧ D` | Box **and Player** (see X-1) |
| `blocked_wall` | `¬A ∧ ¬B` | Player |
| `blocked_box_crossing` | `B ∧ ¬C` | Player |
| `blocked_box_landing` | `B ∧ C ∧ ¬D` | Player |

`free(c)` entails `c ≠ Box.pos` (`world/sokoban2.py:119`), so **`A ∧ B` is
unsatisfiable**. That leaves 12 satisfiable assignments of the four atoms, and
**exactly one rule fires in each of the 12**:

| | `¬A ∧ ¬B` | `¬A ∧ B` | `A ∧ ¬B` |
|---|---|---|---|
| `C ∧ D` | `blocked_wall` | `push2` | `walk` |
| `C ∧ ¬D` | `blocked_wall` | `blocked_box_landing` | `walk` |
| `¬C` (D either) | `blocked_wall` (×2) | `blocked_box_crossing` (×2) | `walk` (×2) |

**This table names no wall set, no board size and no level**, so `exclusive` is
entailed for the entire domain — every level the manual will ever travel to, not
only the five swept. That is a strictly stronger result than route 2 gives, and
it is the one to quote. Route 2 remains worth having because it is checked by
machine and does not depend on my reading the guards correctly.

Spelled out pairwise, the same fact: `walk` requires `free(ahead(P,d))` and
`walk` requires `free(ahead(P,d))` and `push2` requires `Box.pos = ahead(P,d)`,
which is its complement — disjoint. Each `blocked_*` negates a predicate one of
the others asserts: `blocked_wall` (`not Box.pos = ahead(P,d)`) against everything
that requires `Box.pos = ahead(P,d)`; `blocked_box_crossing`
(`not free(ahead(Box,d))`) against `push2` and `blocked_box_landing`, both of
which require `free(ahead(Box,d))`; `blocked_box_landing`
(`not free(beyond(Box,d))`) against `push2`'s `free(beyond(Box,d))`. All ten pairs
disjoint syntactically. Two routes, agreeing, and one of them does not require the
predictor to be correct.

**Adjudicated** `exclusive`. It also names which of constraint 9's two discharge
routes this manual claims — until now `certify`'s `exactly-one-successor=True`
was discharging an obligation the manual had never stated it was taking on.

### T-11c · `cascade single_frame`

**Proposal** `single_frame` — one action, one successor, all guards read the
pre-state, all effects apply together.

**The question the dispatch actually asked**: does the box sliding two cells count
as a cascade? **No, and the reason is this sub-entry's whole content.** The two
cells are *one rule's one effect*, applied whole. `multi_frame` is not "an effect
spans more than one cell"; it is "**the rule set is re-run** on the intermediate
state until quiescence". Those come apart, and conflating them is the easy wrong
answer here.

**Evidence** Under `multi_frame` with the action held across rounds:
**`single_frame`-only wrong 0**, **`multi_frame`-only wrong 27,030**, both wrong
the same 52. Every A0 rule guards on `act=move(Player, dir)`, so
nothing switches the action off: `walk` re-fires and the player slides across
open floor until something stops it. One `move` moves the player many cells. The
world moves it one. Under `single_frame`, **0 mismatches**.

**The alternative reading, stated because the refutation depends on which one you
take.** If instead the action is *consumed* after round 1, then no A0 rule can
fire in round 2 — all five guard on the action — so quiescence is immediate and
`multi_frame` becomes observationally *identical* to `single_frame`. Under that
reading the probe's witness is vacuous. **The declaration survives either way**,
and the argument that does not depend on the reading is this: `cascade` exists to
record whether the world has a **self-triggering tick** (Theoria 1.8 deferred it
to the trace for exactly that reason). A0 has no action-free rule — nothing can
fire on an intermediate state without a fresh action — so there is no tick to
declare. `single_frame` under the discriminating reading, and `single_frame`
under the reading where the distinction is unobservable.

**Adjudicated** `single_frame`.

### What this cost

Three statements in the manual, one probe, and one behaviour change: `gen_exec`
now **refuses** a declared value it does not implement (v0.2 revision item 10,
three negative tests). Before, all of a0-spike's forms ignored the section
completely — the migration would have satisfied the parser and changed nothing,
which is the hazard the section exists to close, one layer down.

---

## 表达力台账 — expressivity ledger

Opened by T-11. `gen_exec.py` had claimed to have filed against a ledger that did
not exist in this directory; these are the entries it meant, plus what T-11 found.
Prefix `X-` so as not to collide with `cold-start-a0`'s `E-` series.

| # | the gap | what it costs today | status |
|---|---|---|---|
| **X-1** | **A rule may carry exactly one event, and a push does two things.** `when <guard> then <event>` is the frozen shape, so `push2`'s `slid(Box, dir)` is **compound** — its compiled effect moves the Box two cells *and* the Player one. The Player's motion is real, load-bearing, and named nowhere in the manual's own vocabulary. **v0.2 also never defines what `frame persist`'s "mentions" ranges over**, and the three available readings do not agree: *the rule's text* leaves the successor undetermined (`blocked_wall`'s guard mentions `Box.pos`, so the Box would be pinned by a rule that does not move it); *the event signature* — `slid` writes `{Box}` — freezes the Player across a push and **mispredicts 376 pairs**, measured; only *the compiled effect* — `{Box, Player}` — matches the world. | A reader of `theory.dsl` alone cannot see that a push moves the player, and `frame persist` is true only relative to an effect dictionary that lives in `gen_exec._compile_effect`, not in the manual and not in the contract. It also makes `conflict`'s per-object obligation depend on that same private knowledge: read `slid` by its name and the sweep ranges over too few pairs. T-11b compensates by hand. | **open** — reported to `theory-compiler` via PARTNER_SYNC, as two requests: an event signature that names every object it writes (or multiple events per rule), **and** a definition of "mentions" in v0.3. The 376 is the cost of guessing the second one wrong. Found by the adversarial review, Attack 1. |
| **X-2** | **Only one of a0-spike's forms is derived from the manual.** `gen_exec` parses `theory.dsl`; `pddl_gen` builds the domain from *level data* and never reads the manual; `artifacts/A0.lean` is checked in and only *checked* by `lean_stage`. | The `semantics:` guard T-11 added can only be enforced where the manual is read. A manual declaring `cascade multi_frame` is refused by the Python form and silently ignored by the PDDL and Lean forms — precisely the `gen_pddl` defect v0.2 revision item 10 records. a0-spike's version is worse: those backends cannot be guarded at all, because they never read the manual. | **open** — the honest scope of "四形态同源" here is one form derived, one hand-written, one level-derived. Not fixed: rebuilding Lean and PDDL as real generators is a sprint, not a migration. |
| **X-3** | **Nothing checks that a no-op rule is redundant before it is dropped, or load-bearing before it is kept.** `frame persist` makes the question stateable — a rule whose event writes nothing is redundant exactly when some *other* rule fires on the same guard region — but no tool decides it. This directory keeps three such rules and needs them (T-11a, measured); `cold-start-a0` dropped eleven and was right to. Both calls are adjudications; neither is checked. | The manual's length rests on a judgement about entailment that no artefact re-derives. Getting it wrong in the dropping direction makes the rule set non-total and `step` raises — loud. Getting it wrong in the keeping direction is silent, and leaves clauses that carry no predictive content while each adding a mutual-exclusion obligation to discharge. | **open** — smaller than X-1/X-2 and now *sharper* than when first filed: the obligation is "for each rule whose event writes nothing, is its guard region covered by another rule?", which `certify` already has the machinery for. Wants a `certify` obligation, not a grammar change. **The first draft of this entry mis-cited `cold-start-a0`'s R-07 as this directory's; see T-11a.** |
| **X-5** | **"the Box is not standing on a wall" is inexpressible in the v1 guard language**, and the manual is wrong about 52 states because of it. The world checks `is_wall(target)` *before* `target != state.box` (`world/sokoban2.py:142-145`), so a box parked on a wall blocks the player at the wall and no push is considered; `push2` has no clause that can see this. It cannot get one: `free(Box.pos)` compiles to `_free(state, state.box)`, which is unconditionally false because `_free` excludes the box's own cell. | 52 mispredictions across the five levels, every one firing `push2`. They are **not** evidence about `frame` or `cascade` — both readings of each mispredict them identically — but they are a real defect, and by v0.2 §"Discharging `conflict`" the honest name for the situation is a **discharge conditional on an undeclared well-formedness condition** ("no object stands on a wall"), which that section says is simultaneously a defect report. | **open**. Not reachable in play, which is exactly why T-9 says that is not a defence. Wants either a guard predicate over level-static data (the compiled module already holds `WALLS`), or a `unique`-style declaration that objects and walls do not share cells. Found by the adversarial review, Attack 4 — my own justification for excluding these states was factually wrong, and is corrected in FINDING-2. |
| **X-4** | **`a0_report.json` embeds an absolute path to the Lean binary**, so the artefact is not byte-reproducible across machines. | CLAUDE.md makes determinism a requirement and the Phase 4 manifest publishes tracked files; this field varies by developer, and on this machine it also leaks a home directory. Pre-existing — T-11 only changed *which* absolute path it holds. | **open**, recorded not fixed: changing the field is a schema decision, and provenance genuinely wants to know which Lean ran. Candidate fix is the version string plus a repo-relative or basename form. |
