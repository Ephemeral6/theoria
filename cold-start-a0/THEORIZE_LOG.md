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
| E-06 | a proof method for goals no linear pagoda covers | nothing — `CertificateGapError` refuses to generate | `goal count(Peg, alive) = 1` stays unproven: three of the five single-peg terminals admit no linear pagoda at all |
| E-07 | saying that two live instances of one type never share a cell | **discharged** — `unique` on a field (`dsl_grammar_v0.2` revision item 12) | see below |

E-03 is the one to fix first: a manual whose default behaviour is a comment is
not a manual.

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
