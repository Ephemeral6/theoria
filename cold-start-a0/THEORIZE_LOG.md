# THEORIZE_LOG — A0

Every proposal in `artifacts/candidates.jsonl`, and what was done with it.

**Discipline for this file.** `world/GROUND_TRUTH.md` and
`artifacts/ground_truth.json` were **not opened between the end of M1 and the
completion of M5**. The adjudications below were made from the candidate stream,
the board map and the trace alone. The first read of the ground truth is stamped
at the bottom of this file, and the accuracy comparison lives in `A0_REPORT.md`.

The seal has one hole and it should be named rather than hidden: **the same
instance both built the A0 world at M1 and adjudicated it at M3.** No file was
consulted, but the world's design was not forgotten either. Every verdict below
is therefore written to be checkable against the candidate stream alone — a
reader who has only `artifacts/candidates.jsonl` and the board map should be able
to re-derive each one, and where a verdict rests on an argument rather than on
evidence (R-02, R-05) the argument is spelled out instead of asserted. That is
the best available substitute for a seal that a single-agent spike cannot have,
and `A0_REPORT.md` counts it as a threat to the result rather than a footnote.

Verdicts: **accept** (written into `theory.dsl`) · **reject** ·
**entailed** (true, but already implied by something else in the manual, so
entering it would double-explain) · **probe-pending** (constraint 7: a theorem
that has not been probed is not final).

Per D-A0-009, a candidate row carrying a frontier is adjudicated **guard by
guard**, not row by row.

---

## Round 0 — what arrived

28 candidate rows: 3 `object_hypothesis`, 23 `rule_hypothesis`,
2 `invariant`, 0 executable `probe_design` (see P-01..P-03).

The board came out of extraction before any engine ran: 43 static cells, 38
dynamic, background colour 0.

```
1 1 1 1 1 1 1 1 1
1 0 0 0 0 1 0 0 1
1 0 0 0 0 1 0 0 1
1 0 0 0 0 1 0 0 1
1 0 0 0 0 . 0 0 1     '.' = dynamic, the board cannot explain it
1 0 0 0 0 1 0 0 1
1 0 0 0 1 1 0 0 1
1 1 1 3 1 1 0 0 1
1 1 1 1 1 1 1 1 1
```

Reading it as a human reads a map: colour 1 forms a closed border and an interior
divider; colour 0 is the floor; colour 3 is a single marked cell in a dead-end
pocket at (7,3); and the divider at column 5 has exactly one cell — (4,5) — that
the board refuses to explain. **A hole in a wall that is not always a hole.**
That observation is what made me look for a door before any rule was read.

---

## O — objects

### O-01 `obj0`, colour 7 → **accept**, named `Button`
### O-02 `obj1`, colour 5 → **accept**, named `Door`
### O-03 `obj2`, colour 6 → **accept**, named `Cart`

Evidence: present in 276 / 100 / 276 frames respectively; 214 `move` events all
belong to `obj2`, 1 `recolor` to `obj0`, 1 `vanish` to `obj1`.

Naming is mine and is the only thing here that is: the engine calls them
`obj0..2`. `obj2` is the Cart because it is the only thing that ever moves and
it moves under the action. `obj1` is the Door because it sits in the wall's one
unexplained cell and it is the thing that stops existing. `obj0` is the Button
because it is the only object that changes without moving, and it does so in the
same transition as `obj1` disappearing.

**Segmentation operator.** The candidate payloads carry `operator_comparison`:

| operator | script bits | tracks | events |
|---|---|---|---|
| `connected_components(4)` | 6511 | 90 | 332 |
| `connected_components(4)+uniform_color` | **4423** | **3** | **216** |

Accepted the uniform-colour operator, by the framework's own criterion —
shorter script. The colour-agnostic operator is not *wrong*, it is
under-determined for a world where objects touch: whenever the Cart stood beside
the Button they merged into one blob, and the tracker paid for it with 88
vanishes and 87 appears. Recorded as D-A0-007.

### O-04 The compression account does not justify Button or Door — **admitted anyway**

The per-object accounts, computed from the engine's own cost model:

| object | declaration | script bits | pixel baseline | account |
|---|---|---|---|---|
| Cart | 21 | 2169 | 5136 | **+2967** |
| Button | 21 | 29 | 12 | **−17** |
| Door | 21 | 25 | 12 | **−13** |

Theoria 1.8 says a concept's ticket of admission is that it makes the manual
shorter, and constraint 5 says no entry without a gain. By that rule the Button
and the Door should both be **rejected**: each has exactly one event in 275
transitions, and a 21-bit declaration is more expensive than just listing the two
pixels that changed.

They are admitted regardless, and the reason is a different constraint.
Constraint 2 is full-frame responsibility: every pixel belongs to the board or to
some object. Cells (3,2) and (4,5) change, so they cannot be board; if they are
not objects either, then two pixels of every frame are unexplained and the cheap
certify layer fails on frame 0. And the Door's rule cannot even be *stated*
without the Button in the vocabulary.

**This is a real conflict between two of the framework's own admission criteria,
found on the first cold start.** The compression account is not wrong — it is
measuring the wrong alternative. The alternative to "Button is an object" is not
"encode its pixel edits"; it is "leave the cell unexplained forever", which has
no finite price in this accounting at all. Carried to `A0_REPORT.md` as the
first framework finding; the negative numbers are written into `theory.dsl`
honestly rather than suppressed.

---

## R — rules

### R-01 `obj2_step_{UP,DOWN,LEFT,RIGHT}` → **accept** as `push_{up,down,left,right}`

Coverage 52/52, 62/62, 46/46, 52/52. Guard `act==D ∧ free(strip(D))`.
The engine also lifted these into one `obj2_step` with `act==?dir ∧
free(strip(?dir))`, 212/212 — the single best-evidenced statement in the whole
stream.

**Frontier, 3 members per direction** — all three survive:

```
act==D ∧ free(strip(D))          <- accepted
act==D ∧ clear(strip(D))
act==D ∧ tcolor(D)==0
```

`probe_frontier` was asked to separate them and answered **no experiment in this
world can** (P-02). That is correct and it is checkable by hand: `clear` differs
from `free` only when the target strip runs off the grid, and the border is solid
wall so the Cart can never get there; and `tcolor(D)==0` *is* `free` for a 1×1
mover, since colour 0 is the background. Three names, one predicate, on this
world.

Tie broken by description length, as D-A0-009 prescribes: all three cost 12 bits,
so the engine's own second key applies — the logically strongest guard, which is
`free` (it entails both others). Recorded, because it is a decision the evidence
did not make: **if A0 ever grows a level whose border is open, this choice
becomes falsifiable and `clear` may win.**

The DSL has no `?dir`, so the lifted form is written out as four rules. Noted in
the expressivity ledger (E-02).

### R-02 `obj2_jump_DOWN` → **accept** as `teleport_down`

Coverage 2/2 (transitions 11 and 103). Effect: move by (−5,−2).

**Frontier, 2 members:**

```
act==DOWN ∧ tcolor(DOWN)==3      <- accepted, 14 bits
act==DOWN ∧ at(6,3)              <-           18 bits
```

Two readings of the same two witnesses: *the Cart jumps when it is pushed onto
the marked cell*, or *the Cart jumps when it is pushed down from (6,3)*. The
probe search found a splitting configuration — paint colour 3 below (1,1) and
push DOWN, 1.000 bits — but only in the **hypothetical** tier: the world was
never observed in that configuration and nothing in the manual says it can be
driven there. So the probe is not executable and the tie has to be broken by
argument.

Accepted `tcolor(DOWN)==3`, for two reasons, in this order:

1. it is the cheaper description (14 vs 18 bits) — the engine's own criterion;
2. `at(6,3)` is a **problem** fact wearing a **domain** rule's clothes. Theoria
   1.10a splits the manual into a domain that travels across levels and a problem
   that does not. A rule keyed to a literal cell cannot survive the portal being
   moved; a rule keyed to a visible board marker can. Choosing the transferable
   reading is the whole content of C3.

Same argument, applied to the effect: the two witnesses agree on both "always
lands at (1,1)" and "always displaces by (−5,−2)", because the pocket at (7,3)
has exactly one approach. Accepted the **absolute destination**, written as the
landmark `portal_exit` whose coordinates live in the problem instance — a portal
has a destination, a displacement is a coincidence of geometry.

Both choices are generalisations beyond the evidence and are flagged as such.

### R-03 `obj0_recolor8_LEFT` → **accept** as `press_left`

Coverage 1/1, transition 99. Guard `act==LEFT ∧ tcolor(LEFT)==7`, frontier size
1 — the vocabulary pins it exactly, no ambiguity to adjudicate.

Read in words: pushing left into a cell showing colour 7 turns that colour into
8. Colour 7 is only ever the Button, so: **pushing into the unpressed Button
presses it.** The Cart does not move (no `move` event at 99 on `obj2`; instead
`obj2_still_LEFT` fires).

### R-04 `obj1_vanish_LEFT` → **accept** as `door_opens_left`

Coverage 1/1, transition 99, guard **identical** to R-03.

This is the whole point of the A0 world and it is worth being precise about what
the evidence does and does not give. What is observed is that at transition 99
two things happen at once: the Button recolours and the Door vanishes. The
evidence does **not** distinguish

* *press causes the Door to open* (cascade — one action, two events), from
* *both are caused independently by the same push*, from
* *the Door opens whenever the Button is pressed*, whatever pressed it.

One witness cannot tell these apart, and there will never be a second: the latch
is irreversible, so this world can only ever press the Button once
(cf. D-A0-003's three permanently uncoverable state-action pairs).

Accepted the engine's guard verbatim rather than reaching for the causal reading,
because the causal reading has no more evidence and costs more to state. The
*content* of the dependency is instead carried by the invariant in L-02, which
is a stronger statement and which has 275 transitions behind it rather than one.

### R-05 Direction generality of `press_left` / `door_opens_left` → **reject, probe-pending**

The obvious generalisation: the Button is presumably pressable from any of the
four directions, exactly as the push rule lifted across all four.

**Rejected**, and the manual is knowingly left incomplete. Constraint 5 forbids
an entry without evidence, and the evidence for `press_up`, `press_down`,
`press_right` is precisely zero — not thin, zero. The analogy to the lifted push
rule is an argument, not a witness.

I want the consequence on record because it is the framework's own predicted
failure mode reproduced on the first real cold start: **the manual as written
says that pushing up into the Button does nothing, and full-history replay will
never catch that.** It is the DC22 shape from Theoria 1.3 — a rule that is
missing rather than wrong, invisible to replay, and it makes the modelled world
*smaller* than the real one.

Entered instead as a theorem with `probe: pending`
(`press_is_direction_free`). The probe that would settle it is trivial to
design and impossible to run: drive the Cart to (2,2) and push DOWN into an
unpressed Button. In this world the Button is already pressed by then. **The
experiment that would test this manual cannot be performed on this instance** —
which is a genuine finding about A0's design, and is the single item I most
expect to be wrong at M6.

### R-06 `obj0_still_LEFT`, `obj1_still_LEFT` → **entailed**

Guard `act==LEFT ∧ !tcolor(LEFT)==7`. True (65/65) and exactly the complement of
R-03/R-04's guard. Not entered: it is the frame axiom applied to R-03.

### R-07 `obj{0,1,2}_still_*`, all directions, and the lifted `obj{0,1,2}_still`
→ **entailed**

Coverage 74/74, 71/71, 64/64, 20/20, 19/19, 12/12, 10/10, 51/51 — all true.
All of them say "nothing happened", and all of them are consequences of the
frame axiom the manual declares at the top: *if no rule fires for an object,
that object is unchanged.*

Entering them would (a) lengthen the manual by eleven clauses that add no
predictive content, and (b) manufacture a mutual-exclusion obligation between
`push_left` and `Cart_still_LEFT` that only exists because both were written
down. Rejecting them is a compression gain and a proof-obligation saving at once.

One of them is not quite trivial and deserves its own line:
`obj2_still_DOWN`'s guard is `!clear(strip(DOWN)) ∧ !tcolor(DOWN)==3 ∧ act==DOWN`
— three literals, because the engine had to exclude the Portal by hand. Under
the frame axiom that literal disappears: `push_down` does not fire (the target is
not free), `teleport_down` does not fire (the target is not the marker), so
nothing happens. The engine needed a negation the manual does not.

### R-08 Blocked-by-what → **not represented, logged**

The manual cannot say *why* a push failed — the closed Door, a wall and the
Button are all just "not free". Nothing in the trajectory forces the distinction
and nothing downstream needs it, so no rule was written. Noted because it is the
kind of thing a human manual would say and this one cannot.

---

## L — laws

### L-01 `(#6) mod 2 = 1` over 37 of the 38 arena cells → **accept** as `cart_unique`

`zero_space`'s second global law. Support: every arena cell except (3,2), the
Button's cell. Read: the number of cells showing colour 6 is odd — and since the
Cart is a single cell, that is *exactly one Cart, always*. The exclusion of
(3,2) is itself informative: the engine noticed the Cart is never there, which
is the Button being an obstacle.

Written in the manual's own vocabulary as `count(Cart) = 1`, which is stronger
than the mod-2 statement the engine could express. Flagged: **this is a
strengthening, not a translation.** GF(2) cannot say "exactly one"; it can only
say "an odd number". The stronger form is what the object vocabulary means and
what Lean will be asked to prove, and Lean proving it is what makes the
strengthening safe.

### L-02 `[cell(3,2) is 8] + [cell(4,5) is 5] mod 2 = 1` → **accept** as `door_latch`

The single most valuable line in the entire candidate stream, and the one I did
not expect an engine to produce.

Read literally: over all 275 transitions, exactly one of *"the Button shows 8"*
and *"the Door exists"* holds. In manual vocabulary:
**the Door is present if and only if the Button is unpressed.**

This is the Button→Door dependency, recovered as a conservation law with 275
transitions of support, by an engine that was handed 152 anonymous indicator bits
and told nothing about buttons or doors. R-04's rule has one witness; this has
all of them. Together they are the dependency: the rule says *when* it happens,
the law says *that it always holds*.

Written as `count(Button, 8) + count(Door) = 1`.

**Caveat kept out loud.** The law is certified over the observed trajectory only.
Universality — closure under *every* legal move from *every* state — is not
something `zero_space` can give; that obligation moves to Lean, and Lean proves
it relative to the manual, not relative to the world. Two-layer truth, exactly as
Theoria 1.5 says.

### L-03 The 113 `cell_local` laws → **not read**

Per the engine's own README these are laws about the encoding, not about the
world. Filtered before emission (D-A0-010) and counted in the report. No
adjudication needed; recording that the filter exists, because 113 unread
proposals is the kind of thing that should never be silent.

---

## P — probes

### P-01 `obj2_jump_DOWN` — separable, **hypothetical tier only**
Paint colour 3 below (1,1), push DOWN: 1.000 bits, splits `tcolor(DOWN)==3` from
`at(6,3)`. Not executable — see R-02.

### P-02 `obj2_step_{UP,DOWN,LEFT,RIGHT}`, `obj2_still_{UP,LEFT,RIGHT}` — **no split anywhere**
Neither tier separates `free` / `clear` / `tcolor==0`. They are extensionally
identical on this world. Reported as a verdict rather than as a failure: the
right answer to "which experiment settles this?" is sometimes "none does".

### P-03 `obj2_still_DOWN` — separable, hypothetical tier, 6 hypotheses → 2 classes
Moot once R-07 rejects the rule.

**Zero executable probes were emitted.** For a world this small that is the
correct output and not a bug, but it does mean the probe machinery got no
real exercise in A0 — carried to `A0_REPORT.md` as a coverage gap in the spike
itself.

---

## E — expressivity ledger

Things the world said that `dsl_grammar_v0.1` cannot.

| # | wanted | worked around by | cost |
|---|---|---|---|
| E-01 | negation in a guard (`!clear(strip(D))`) | naming the complement predicate `blocked` — then dropped entirely, since R-07 made the negated guards unnecessary | none in the end |
| E-02 | direction-lifted rules (`act=push(Cart, ?dir)`) | writing four rules | manual is 3 clauses longer than the engine's own account; the lifted 212/212 evidence is split across four rules that each look weaker than it is |
| E-03 | a frame axiom / default clause | a comment at the top of `theory.dsl` and a hard-coded rule in the backends | **the most important semantic fact about `step` is not in the DSL at all** |
| E-04 | declaring a board landmark (`portal_exit`, the goal cell) | free-floating names resolved by the problem instance | the domain/problem boundary is real but unwritten; a reader of `theory.dsl` alone cannot tell which names are level data |
| E-05 | a weight function over cells for a pagoda invariant | the vector lives in the problem instance (M5) | same as E-04 |
| E-06 | a proof method for goals no linear pagoda covers | **discharged** — the certificate covers what it covers, exhaustion closes the rest, each goal attributed to its method | see below |
| E-07 | saying that two live instances of one type never share a cell | **discharged** — `unique` on a field (`dsl_grammar_v0.2` revision item 12) | see below |
| E-08 | a guard that counts (`count(Token, present = false) >= k`) — the count-lock gate | **discharged** — one rung, in the guard language; see below | the rung below it is a quantifier and it is deliberately not taken |
| E-09 | putting a *named track* in a *place*: "the object I am about to step onto is **that** one" (`faces(T,D)`) — the miner vocabulary, not the grammar | **discharged** — one rung, mover-relative, one step; see below | 2 bits per repaired transition paid in the segmentation script, and the pass that pays them is the one place the pipeline does not adjudicate by compression |

E-03 is the one to fix first: a manual whose default behaviour is a comment is
not a manual.

### E-08, in full — the widening, and the world that did *not* force it

**What was wanted.** `worldgen`'s `t2-lock-fragile` has a gate that becomes
passable once three tokens have been picked up, and picking a token up only makes
it stop being drawn. A manual for that world has to write

    rule gate_opens
      when act=open(Gate) and count(Token, present = false) >= 3 then vanished(Gate)

and under v0.3 it could not. Not for the reason one would guess: `>=` was already
legal in a guard, and so was the shape of the call. `count` was implemented
**once, inline in the goal compiler, reachable only under `=`**, and a guard that
mentioned it reached `unknown predicate 'count'`. The widening is therefore
mostly a lifting: one `_count_expr`, shared by the goal and the guard, so that a
manual cannot count one way when it predicts and another way when it decides it
has won.

**One rung, and the rung is named.** The condition is a single
`<field> = <value>` test over the declared instances of one type. No quantifier,
no nested count, no counting of cells. Each of those is refused with its own
message and each refusal has a test. A `forall` is the next rung and it needs its
own forcing world; C9's work order says so and this entry is the reason to hold
to it.

**A correction the lifting exposed.** `count(<Type>)` with no condition used to
compile to a literal `1` per declared instance — a constant. So `count(Door)`
stayed 1 after the Door vanished, and the A0 manual's own `door_latch` invariant
(`count(Button, 8) + count(Door) = 1`) is false as written on any state where the
Door is gone. Nothing caught it because invariants are never compiled and no
shipped **goal** exercised a vanish. It now counts present instances.

**The world that forced this is not the world it fixes, and that is the point of
having a ledger.** The upstream report
(`monitor/inbox/archive/20260728T093000Z-W-1610-…`) and the C9 work order both
concluded that `t2-lock-fragile` fails to mine because the relational vocabulary
cannot count. Measured before building on it: a counting atom separates **zero**
of the 276 transition pairs the miner is stuck on, and the argument closes rather
than merely failing — a colour-cardinality atom is a function of the frame's
colour histogram, and all 276 stuck pairs have identical histograms. The real
cause is that `multi_miner.mover_track` selects a *token* as the mover on any
world with consumables, because the segmenter hands the agent's identity to a
vanishing object; every positional atom is then anchored on something that never
moves. Evidence and four standalone probes:
`theory-compiler/runs/20260728T142307Z-C9-count-lock-vocabulary/FINDING_premise.md`.

So this entry's provenance is the **grammar**, not the miner: a hand-written
manual for a count-lock world cannot state its own gate rule, which is true
whatever any engine can propose, and is checked by
`theory-compiler/tests/fixtures/countlock_theory.dsl` compiling and predicting
the threshold correctly at 0, 1, 2 and 3 tokens. The miner's counting atom ships
alongside it with its measured benefit recorded as **zero on the only world that
asked for it** — see that run's `RUN_STATE.md`, which is where a widening that
did not pay belongs rather than in a footnote.

### E-09, in full — the vocabulary knew about tracks and about places, never both

**Which world forced it.** `worldgen`'s `t2-lock-fragile`, transition 31 — the
same world as E-08, and that is not a coincidence but it *is* a different gap.
E-08 was cut from a misattribution: the miner was stuck because a token had been
handed the agent's identity, not because it could not count. With the
segmentation repaired (`cold-start-a0/pipeline/identity_swap.py`) the world goes
from **19 failing mining groups to one**, and that one is real:

    FAILS  track=obj1 action=RIGHT effect=('none',0,0,None)  (23 positives)
    NoSeparatingGuard: no literal separates transition 31 from the positives

**What v1 could not say.** The rule is "this token does nothing when the agent
presses RIGHT", and the transition it must exclude is the one where the agent,
standing directly to its left, steps onto it and eats it. `a0_relational_v1` was
relational about *colours and strips*, and indexed by *track*, but it had no atom
that put a named track in a place:

| atom | why it cannot separate t=31 |
|---|---|
| `tcolor(RIGHT)==2` | "the cell ahead is a token" — also true at t=71, where the agent eats a **different** token and obj1 does nothing. Violates 1 positive. |
| `at(1,2)` | reads the mover's own anchor; the agent stands there again at t=59 and t=69, after obj1 is gone. Violates 2 positives. |
| `present(obj1)` / `color(obj1)==2` | indexed by track but blind to where it is. True at t=31. |
| `count(k)>=t` | reads the frame, not a relation. `count(0)` is 19 at t=31 and ranges 19–22 over the positives, so t=31 sits **inside** the positives' range on every colour. |

Measured rather than argued, and adversarially: of the 120 atoms in the
vocabulary at the time, **0** are true on all 23 positives and false at t=31; only
19 hold on all the positives and all 19 also hold at t=31. The conjunction of all
19 — the strongest guard the vocabulary can build for this rule — still admits
t=31. So no conjunction of *any* size works, and the failure is expressivity
rather than CEGIS search order. Probe:
`theory-compiler/runs/20260728T173400Z-C9-mover-identity/probes/09_adversarial_no_atom_separates.py`.

**What was added.** One atom. `faces(T,D)` — *track T's anchor is where the
mover's anchor would be after one step in direction D*. Four limits, each with a
test: one step only (distance is not a parameter); mover-relative only (no
relation between two non-mover tracks); anchors, not body overlap (that is the
touching-objects gap and is its own row); and only `(track, direction)` pairs the
trajectory actually exhibited, since a pair that is never true is a constant.

**What it cost.** Nothing, in the currency that matters here: ten atom kinds
still fit in four bits, so unlike E-08 no existing atom was re-priced. `faces` is
priced at `2 * (_TRACK_BITS + _DIR_BITS)` = 8 bits of payload — the same payload
as `at(r,c)`, by the published rule that an identity literal costs twice a
predicate. At the predicate price it would have been the cheapest atom in the
vocabulary while being the most instance-bound one, and it would have displaced
`tcolor` in guards with no need of it. Every mined guard in the tree is unchanged
across the widening; exactly one new guard uses the new atom, and it is the rule
that forced it:

    obj1, RIGHT, nothing happens   <-   !faces(obj1,RIGHT) and act==RIGHT

**What it did not fix, said plainly.** `t2-lock-fragile` now passes L1, L2 and
L3a (replay 110/110, render 287/287) and mines 36 rules. Its held-out accuracy is
**0.497**, and the reason is visible in the rule the lock produces: the gate
opens exactly once, so CEGIS separates that single witness with the cheapest
conjunction available (`!clear(strip(RIGHT)) and !present(obj1) and act==RIGHT
and free(strip(LEFT))`) rather than with a count. **`count` appears in no mined
guard on this world even now.** E-08's miner-side atom therefore has its measured
benefit at zero for the second time, on the world that asked for it, under
correct tracking — which is the cleaner test W-1252 could not run. That is
recorded here rather than argued away; the DSL-side half of E-08 is untouched by
it, because a hand-written manual still has to be able to state the gate.

### E-06, in full — one proposition, two methods

`goal count(Peg, alive) = 1` was unproven for one revision. The certificate
excludes `00010` algebraically; `10000`, `00100` and `00001` admit **no linear
pagoda function at all** (`engine-rig/tests/test_interop.py` pins them as
unprovable by that method, not merely unexported), and `01000` has a certificate
of its own that the compilation was not given. So the pagoda route could not
license the manual's theorem, and the compiler refused — correctly, while that
was the only route.

**Discharged 2026-07-28 by using the other method the compiler already had.**
The reachable set from `11011` is five states — `11011`, `00111`, `11100`,
`01001`, `10010` — and none of them has one peg. Exhausting it closes every goal
the certificate does not, and `decide` keeps the axiom set empty. Measured, not
asserted: `lean` 4.9.0 exits 0 on the generated file and reports
`'inv_all' does not depend on any axioms` and
`'unsolvable' does not depend on any axioms`.

**The two arguments stay separate and attributed.** The file's header names
which goal each one carried, because they are not the same argument and a
blended claim would be worse than either half. It also says only what is known:
that a goal is *not excluded by this certificate* is a fact about the
certificate, whereas *no linear pagoda exists* is a fact about the method that
only `lp_potential` can report — the first draft of the header conflated the
two and libelled `01000`, which has a certificate.

**What exhaustion does not fix, and what does.** Exhaustion is
`O(reachable set)`: it closes this configuration and does not survive a larger
board. The structural answer is a **third** method, and the engine for it already
exists — `ic3_pdr`, which is infeasible-LP's counterpart and reports the same
three obligations. Its certificate is now consumed
(`theory_compiler/ic3_certificate.py`, schema in
`CONTRACTS/ic3_certificate_v0.1.md`, manual side `clauses`/`cnf(...)` at
revision item 14), and the Lean it produces closes `inv_closed` by splitting on
**moves** — so proof size tracks the invariant rather than the state space.
Measured on the peg4 fixture: `computational` empty axiom set, `algebraic`
`propext` only, which is one axiom cheaper than the algebraic pagoda route.

**Still not discharged.** Three limits, stated rather than rounded off:

* The **emitting** half of the ic3 interop is `engine-rig`'s file and is not
  written. The consumer runs against a fixture transcribed from the candidate
  row they have already published; the schema is a draft awaiting their
  countersignature.
* "Proof size tracks the invariant" is a **structural** claim that the fixture is
  too small to demonstrate — 4 cells, 2 clauses, an inner split over 2 of 4
  positions. It pays on a large board and there is no large board here.
* `lp_potential` is still sound and incomplete, exhaustion is still
  `O(reachable set)`, and a configuration all three methods miss still has no
  proof. D-TC-008's trade-off is untouched.

### E-07, in full — an obligation the guard language cannot let a manual meet

Found 2026-07-28 while making the `conflict` obligation checkable
(`theory_compiler/conflict.py`). The peg manual declares `conflict exclusive`
and **does not entail it**.

`jump_right` is a schema quantified over two instances, `forall ?a in Peg forall
?b in Peg`, and its guard pins `?b` only by position: `?b.pos = ?a.pos + 1`.
Grounding produces one rule per pair, and two of them — `(?a=Peg_0, ?b=Peg_1)`
and `(?a=Peg_0, ?b=Peg_3)` — both claim `Peg_0` and both fire whenever `Peg_1`
and `Peg_3` occupy the same cell. Measured by exhaustive sweep of the predictor:

| swept | (state, action) pairs | rules claiming one object twice |
|---|---|---|
| every representable state | 80,000 | **600** |
| …restricted to no two live pegs sharing a cell | 59,560 | **0** |

So the declaration is true of the world and unstated in the manual. To state it,
a guard would need to quantify over instances *inside itself* — "there is no
other live `Peg` at this cell" — which the v0.2 guard language does not have,
and which `dsl_grammar_v0.2.md` forbids adding by hand. The invariant language
cannot carry it either: it reaches linear arithmetic, counts, parity and finite
weights, and "these two positions differ" is none of those. `count(Peg, pos = c,
alive = true) <= 1` would need a quantifier over cells that invariants lack.

**Cost of not having it, while it lasted.** The strongest thing any tool could
say about the peg manual was *conditional*: `exclusive` holds under a named
condition (`distinct_positions`), fails without it, both halves machine-checked
with a witness. A real result, and weaker than the manual's own claim. Same
shape as the finding behind D-TC-012 — a rule can be right as a *problem*
solution and wrong as a *domain* — and the reason the check sweeps every
representable state rather than the reachable ones.

**Discharged, 2026-07-28.** Not by weakening the check: by giving the manual
somewhere to put the fact. `object Peg { pos: Int unique, alive: Bool }` says
what was always true of the world, and with it guard analysis discharges all
228 overlapping pairs directly — the conditional route is no longer reached.
`unique` is itself an obligation rather than an assertion (`certify_uniqueness`:
true initially, preserved by `step` across all 59,560 well-formed transitions),
because a restriction nobody checks is how a manual comes to describe a world it
does not have.

Two hazards found and closed while adding it, both the same shape as the one
`semantics:` exists to close: the field regex was unanchored, so `pos: Int
unique` parsed as plain `pos: Int` and the modifier **vanished silently**; and
the pretty-printer omitted it, so a parse→print→parse round trip produced a
manual that no longer entailed its own `conflict exclusive` and looked entirely
normal. An unrecognised field modifier is now an error, and the round-trip test
compares fields rather than names.

---

## Revision history — the concept-birth timeline

The honest version, which is less flattering to the loop than I expected and
more flattering to the adjudication:

| rev | when | trigger | change |
|---|---|---|---|
| 1 | M3 | one pass over all 28 candidates plus the board map | the whole manual as it now stands: 3 objects, 7 rules, 2 invariants, 1 pending theorem |
| 2 | M5 | the plan returned UNSAT on the no-Button variant, and constraint 6 forbids stopping at a bare UNSAT | `theory_no_button.dsl` — the base manual with every Button/Door-dependent clause deleted, plus `right_room_locked` and `unsolvable_no_button` |

**The manual was revised zero times by certify.** The cheap layer went green on
its first run against revision 1; the Lean layer went green on its first run.
There was no theorize→certify→theorize loop to count, because nothing came back.

That is not the loop working well. It is the loop **not being exercised**, and
it is the biggest single gap in this spike — see `A0_REPORT.md`. The iterations
that did happen were all in the *compiler*, not the manual:

| # | layer | defect | how it surfaced |
|---|---|---|---|
| 1 | `gen_python_a0` | rules re-read their guards against the partially-updated state, so `press_left` recoloured the Button and `door_opens_left` then found colour 8 and silently did not fire | the Door never opened in the generated `step`; caught by inspection, then pinned by `test_simultaneous_rule_semantics` |
| 2 | `gen_pddl_a0` | the Door's cell got no PDDL subtype, so `press`'s `?d - doorcell` parameter had an empty domain and grounded to nothing | `fd_adapter` reported UNSAT on an instance that is plainly solvable |
| 3 | `segment_operators` | `engine-rig` grew a native `split_by_color` switch mid-sprint and the monkeypatched operator stopped matching its signature | `TypeError` on the variant run |

Two of the three were **compiler bugs that made the manual look wrong**. Both
were caught, but only one of them by the framework's own machinery.

---

## Ground-truth seal

`world/GROUND_TRUTH.md` and `artifacts/ground_truth.json` were first opened at
**M6**, after M4 and M5 were both green, and only by
`certify/score_vs_truth.py`. No clause above was written or revised after that
point. M5's additions came from the plan's UNSAT and from `zero_space` on the
variant trace, not from the referee's copy.

The score is in `artifacts/score_vs_truth.json` and is discussed in
`A0_REPORT.md`. One line of it belongs here, because it settles R-05:

> Over all 236 reachable (state, action) pairs the manual agrees with the world
> on **233**. The three it gets wrong are pressing the Button from above, from
> below and from the right — the three pairs R-05 named, for the reason R-05
> gave, before the score existed.
