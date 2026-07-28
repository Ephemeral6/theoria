# THEORIZE_LOG — L2 from-scratch control arm

Every proposal in `artifacts/candidates_l2_scratch.jsonl`, and what was done
with it. The manual is `theory/domain_l2_scratch.dsl`.

**Discipline for this file.** This arm exists to find out whether a manual
induced from level 2's own evidence agrees with one induced from level 1's. So
the following were **not opened, at any point, in any form**:
`theory/domain.dsl`, `theory/playbook.dsl`, anything under `theory/generated*`,
`THEORIZE_LOG.md`, `A3_REPORT.md`, `DECISIONS.md`, everything under `a3world/`,
and `artifacts/ground_truth.json`. Nor were `candidates_l1.jsonl`,
`engines_report_l1.json`, `l1_sweep.jsonl`, `l1_solved.jsonl` or any other l1
artifact. What was read: the 35 l2-scratch candidate rows, the l2-scratch
engines report, `l2_sweep.jsonl`, `CONTRACTS/dsl_grammar_v0.2.md`, the frozen
parser, and — as **format** examples only, for syntax and annotation
conventions — `cold-start-a0/theory/theory.dsl`,
`cold-start-a2/theory/theory.dsl`, `theory-compiler/tests/fixtures/cart_theory.dsl`,
`cold-start-a0/THEORIZE_LOG.md` (for the shape of this document) and
`cold-start-a0/compile/gen_python_a0.py` (for the backend's supported guard
vocabulary). Those five are about other worlds; nothing about level 1 of *this*
world was read.

One threat is worth naming rather than hiding: the a0 log and the a0 manual are
about a **different** world, but they are the same *framework's* worlds, and
having read them I know what a button-and-door world looks like. Where a verdict
below rests on that resemblance rather than on this trace, it says so — R-4 and
R-5 are the two places.

### Contamination — declared, bounded, and after the fact

In **round 3**, while diagnosing why the Lean backend rejected this manual, I
read the docstring of `a3pipeline/compile_a3.py::switch_latch_invariant`. It
describes the blinded manual. From it I now know, without having opened
`theory/domain.dsl`, that the level-1 manual declares an object named `Switch`
carrying a `Switch_colour` axis and an object named `Door` carrying a
`Door_present` axis; that its `laws:` section contains `switch_door_latch`,
which `zero_space` proposed to it as `count(Switch, 8) + count(Door) = 1`; and
that its `THEORIZE_LOG` has an entry numbered L-02. That its mover is named
`Cart` follows from the Lean backend working for it at all.

That is a real leak and it touches four of my verdicts — O-1 (`Agent`), O-2
(`Gate`), O-3 (`Switch`) and L-2 (`gate_latch`). Two things bound it:

* **It arrived after every verdict was fixed.** The manual, this log, and the
  `compress:` figures were all complete at the end of round 2. Round 3 changed
  no verdict and no name. Nothing I knew when I decided anything came from it.
* **It is vocabulary, not evidence.** I learned what the other pass *called*
  three objects and one law. I learned nothing about what its rules say, which
  guards it accepted, what it rejected, or its semantics values.

The honest consequence: **the naming agreement between the two manuals is no
longer a clean data point.** As of round 3 two names coincided (`Switch`, and
the latch's content) and two differed (`Agent` vs `Cart`, `Gate` vs `Door`).

Round 4 then removed the question entirely: the toolchain hard-codes `Cart` and
`Door`, both arms were compelled into them, and this manual was renamed to
match (§G-5). So object names now agree across the arms for a reason that has
nothing to do with either pass's reasoning. **Report no agreement on names.**
What is left to compare — and what was decided before any of this — is
structure: the clause count and shape, the guards, the semantics values, and
which clauses are witnessed. None of that was touched after round 1.

Verdicts: **accept** (written into the manual) · **reject** ·
**entailed** (true, but already implied by something else in the manual) ·
**probe-pending** (a theorem that has not been probed is not final).

Per the contract's frontier discipline, a candidate row carrying a frontier is
adjudicated **guard by guard**, not row by row.

---

## Rounds

**Five**, numbered 0–4. Round 0 produced no verdicts; every verdict was fixed in
round 1; rounds 2, 3 and 4 changed none.

**Two of the five — rounds 3 and 4 — went to toolchain conformance rather than
to the world.** Neither was prompted by evidence. That is 40% of this control
arm's theorize budget spent on making a correct manual acceptable to the
backends, and it is the number this section exists to make countable.

Being exact about what each one was:

* **Round 0 — intake.** Read the contract, the 35 rows, the engines report. No
  verdicts. Ended with a list of things the candidate stream asserts but does
  not demonstrate: what `free` means, whether the jump displacements are one
  fact or six, and which of `persist`/`reset` the trace actually shows.
* **Round 1 — the adjudication round.** Recomputed the whole trace myself before
  ruling on anything (see "The recomputation" below), then ruled on all 35 rows
  and wrote the manual. Every verdict in this file was fixed in round 1.
* **Round 2 — revision, no verdict changed.** Replaced the `compress:`
  placeholders with the real `concept_account` numbers, and rewrote three
  comments in the manual that had quoted the miner's literal cells and
  displacements. Re-reading the constraint — *no coordinate anywhere in the
  file* — I decided a comment is still in the file, so the coordinates moved
  here (R-2, R-3) and the manual now points at this document instead. No rule,
  law, or semantics statement changed.
* **Round 3 — transcription into a compilable form, no verdict changed.**
  Forced by an **expressiveness gap in the backend, not by new evidence**:
  `compile.gen_python_a0` takes a literal direction in guards and effects and
  cannot compile `forall ?d in dir`, so the seven lifted clauses were written
  out by hand as their twenty-eight groundings. Also renamed the two landmarks
  to the keys the problem builder registers. Full accounting in §G below,
  including the two things that still do not compile and were left alone. This
  round is the one that leaked the contamination declared above.
* **Round 4 — an object rename, no verdict changed.** Forced by four components
  that hard-code object names: `certify.replay.ACTION_NAMES` emits
  `("push", "Cart", <dir>)`, `gen_python_a0.generate_python` defaults
  `mover="Cart"`, the Lean invariant helpers key on a `Door_present` axis, and
  the goal binder emits `state.Cart_pos`. The mover became `Cart` and the
  barrier `Door`; the Switch already matched. Accounting in §G-5. After it, all
  six generated forms exist and the cheap layer replays the whole trace green.

**Naming note for the rest of this document.** O-1 and O-2 argued for `Agent`
and `Gate` and I have left their text as it was written — it is the record of a
decision, not a description of the current file. Read `Agent` as the manual's
`Cart` and `Gate` as its `Door` throughout. Nothing else about those two
objects changed.

---

## The recomputation

Before adjudicating anything I rebuilt the transition table from
`l2_sweep.jsonl` directly: for each of the 336 transitions, the Agent's cell
before and after, the pressed direction, and the **colour of the cell that
direction points at**. That single table decided most of what follows, and it
is the reason several of the miner's renderings were not taken at face value.

| target colour | up | down | left | right | total | what happens |
|---|---:|---:|---:|---:|---:|---|
| 0 (floor) | 72 | 78 | 42 | 54 | **246** | Agent moves one cell in the pressed direction |
| 1 (wall) | 11 | 12 | 23 | 25 | **71** | nothing |
| 3 (pad A) | 2 | 2 | 3 | 0 | **7** | Agent lands on one fixed cell |
| 4 (pad B) | 2 | 0 | 4 | 2 | **8** | Agent lands on one *other* fixed cell |
| 7 (switch) | 0 | 2 | 0 | 0 | **2** | Switch → 8, Gate vanishes; Agent stays |
| 8 (switch) | 0 | 1 | 0 | 0 | **1** | Switch → 7, Gate appears; Agent stays |
| 5 (gate) | 1 | 0 | 0 | 0 | **1** | nothing |
| | 88 | 95 | 72 | 81 | **336** | |

Every transition is in exactly one row. **The world's response is a function of
the target cell's colour alone**; the pressed direction enters only by choosing
which cell is the target, and — for colour 0 — by choosing where the Agent goes.
That statement is the spine of the manual, and it is what licenses lifting the
rules over `dir` rather than writing sixteen ground clauses.

Two colours are marginal and the table says so honestly: colour 5 has **one**
witness (t18) and colour 8 has **one** (t140).

---

## O — objects

Three `object_hypothesis` rows, all from `mdl_segmenter`, all shape `[1,1]`.

### O-1 `obj1`, colour 6 → **accept**, named `Agent`

337/337 frames, 261 of the trace's 267 events, and the only track that ever
moves. `segmentation.mover` says the same. Naming is mine.

### O-2 `obj0`, colour 5 → **accept**, named `Gate`

Present in 152/337 frames; two `vanish` events (t61, t230) and one `appear`
(t140), all with `reidentified: true`. It never moves. Named `Gate` rather than
`Block` because of two facts held together: it is what the Switch controls, and
it obstructs (t18, R-6). That name is an interpretation and it is the only
interpretation in the word table.

### O-3 `obj2`, colour 7 → **accept**, named `Switch`

337/337 frames, never moves, three `recolor` events on exactly the transitions
where the Gate changes state. Named `Switch` rather than `Button` because it is
**reversible**: 7→8 at t61, 8→7 at t140, 7→8 at t230. A latch would not have a
t140.

### O-4 Segmentation operator → **accept** `connected_components(4)+uniform_color`

The payloads carry the comparison:

| operator | script bits | tracks | events | ratio |
|---|---:|---:|---:|---:|
| `connected_components(4)` | 5970 | 5 | 315 | 0.6616 |
| `connected_components(4)+uniform_color` | **5491** | **3** | 267 | **0.6085** |

Accepted on the framework's own criterion — shorter script. The colour-agnostic
operator paid 35 re-identification merges to recover from blobs that formed when
the Agent stood next to something; the colour-aware one paid one.

### O-5 The compression account, computed not asserted

`cold-start-a0/pipeline/concept_account.py`, with
`name_by_colour = {6: Agent, 5: Gate, 7: Switch}`:

| object | name | with (bits) | without (bits) | delta | verdict |
|---|---|---:|---:|---:|---|
| obj1 | Agent | 2713 | 5230 | **+2517** | mandatory |
| obj0 | Gate | 37 | 40 | **+3** | mandatory |
| obj2 | Switch | 41 | 40 | **−1** | mandatory |

The Agent pays enormously. The Gate pays by three bits, which is noise. The
Switch **does not pay** and is admitted anyway, for the same reason A0 admitted
its Button: `gate_latch` names it, and the invariant language — counts, parity,
finite weights over objects — has no pixel-level paraphrase of that law, so the
alternative manual is not longer, it does not exist. The three `compress:`
figures in the word table are these deltas verbatim.

I note without resolving it that a ±1-bit verdict is not a verdict. The
accounting is doing real work for the Agent and no work at all for the other
two; the load-bearing test is what actually decides them.

---

## R — rules

30 `rule_hypothesis` rows: 15 substantive, 15 no-ops. Seven clauses accepted.

### R-1 `obj1_step_{UP,DOWN,LEFT,RIGHT}` and the lifted `obj1_step` → **accept** as `step forall ?d in dir`

246/246. The lifted row is the one to take: the four ground rows are the same
claim split four ways and annotated 72/72, 78/78, 42/42, 54/54, each of which
looks weaker than the one 246/246 fact they jointly are. That is exactly ledger
entry E-02's complaint, and `forall ?d in dir` is its remedy.

**The guard frontier — three hypotheses, no experiment separates them.**
`free(strip(?d))`, `clear(strip(?d))` and `tcolor(?d)==0` are extensionally
identical on this trace and `probe_frontier` says so for all four directions
("no experiment separates these guards in this world — decide on description
length"). My recomputation agrees and says a little more: colour 0 is the *only*
colour the Agent ever steps onto, and every non-zero colour does something else,
so the three readings cannot come apart in **any** level of this world unless a
colour exists that is passable and non-zero. Adjudicated to `free` on
description length and on it being the word the sibling manuals and the
backend already use. Recorded as a preference, not a finding.

### R-2 Every guard containing a literal cell → **reject**, unconditionally

Eleven frontier entries across seven rule families propose a guard naming a
literal cell:

| rule family | literal-cell guard offered |
|---|---|
| `obj0_still_DOWN`, `obj2_still_DOWN` | `!at(6,6)` |
| `obj1_still_DOWN` (×3 entries) | `!at(4,1)` |
| `obj1_jump_DOWN` | `at(4,1)` |
| `obj1_jump_LEFT` (colour 3) | `at(5,2)` |
| `obj1_jump_LEFT` (colour 4) | `at(1,7)` |
| `obj1_jump_RIGHT` (colour 4) | `at(1,5)` |
| `obj1_jump_UP` (colour 3) | `at(6,1)` |
| `obj1_jump_UP` (colour 4) | `at(2,6)` |

**Criterion, and it is not a preference:** `dsl_grammar_v0.2` §Expressivity
boundary says `word_table + semantics + rules + laws` are the domain and travel
across levels, and that grid layout, initial state and landmark coordinates are
the problem. A guard `at(4,1)` is a level constant in a domain file. Accepting
one would make the manual true of exactly one board and silently false of every
other, which is the failure this arm is built to detect. Rejected on the
contract, before any evidential question is reached.

This is also why the manual carries no coordinate in its comments: I caught
myself quoting these cells there in round 1 and moved them here in round 2.

### R-3 The six `obj1_jump_*` rows → **accept** as two clauses, `warp_a` and `warp_b`

The miner proposes six ground displacements. They are not six facts. Laid out:

| pad | entry cell | pressed | displacement | destination | witnesses |
|---|---|---|---|---|---|
| A (colour 3) | (4,1) | down | (−3,+4) | **(1,5)** | t19, t74 |
| A | (5,2) | left | (−4,+3) | **(1,5)** | t51, t130, t223 |
| A | (6,1) | up | (−5,+4) | **(1,5)** | t193, t293 |
| B (colour 4) | (1,7) | left | (+3,−6) | **(4,1)** | t181, t199, t281, t313 |
| B | (1,5) | right | (+3,−4) | **(4,1)** | t24, t79 |
| B | (2,6) | up | (+2,−5) | **(4,1)** | t17, t66 |

Six different displacements; **two** destinations. A displacement is therefore
not what the world computes — it is what you get if you subtract two cells and
forget that the second one never changes. The portable statement is a jump to a
fixed cell, and the event language has the word for it: `jumped(o, dest)`. The
destination is level data, so it is declared `landmark warp_a_exit` /
`landmark warp_b_exit` (E-04) and located by the problem instance.

That reading also kills the `at(...)` frontier by evidence and not only by
contract. Per direction, `at(4,1) and act==DOWN` fits its two witnesses. But the
three colour-3 clauses would then be three unrelated rules that coincidentally
share one destination, and the three colour-4 clauses three more that
coincidentally share another. One coincidence is a coincidence; six are a rule.

**One reading I considered and rejected as underdetermined.** Pad A sits at
(5,1) and its exit (4,1) is directly above it; pad B sits at (1,6) and its exit
(1,5) is directly left of it — i.e. **each pad's exit is a cell adjacent to the
other pad**. That would be a coordinate-free rule. It fails: the two relative
directions differ (above vs left), and each pad has three free neighbours, so
nothing in the evidence picks the one. A derived-exit reading needs a selector
the trace does not supply. Landmarks it is. Carried as
`theorem warp_exit_is_a_landmark`, probe: pending.

**Direction generality is measured here, not assumed.** Each pad fires from
three of the four directions. The fourth is not untested-by-accident — for pad A
the `right` approach would put the Agent inside the border wall, and for pad B
the `down` approach likewise — so the lift over `dir` has no reachable
counterexample in this level and three confirmations in it.

### R-4 `obj2_recolor8_DOWN` / `obj2_recolor7_DOWN` → **accept** as `switch_press` / `switch_release`

2/2 at t61, t230 and 1/1 at t140. The two clauses are exact inverses over
colours 7 and 8, which is what makes this a toggle rather than a latch, and it
is the clearest single difference between this world and the a0 world I read for
format. `gate_latch` (L-2) holds across all three, which is the independent
check that 7 and 8 are the switch's two states and not two objects.

### R-5 `obj0_vanish_DOWN` / `obj0_appear_DOWN` → **accept** as `gate_opens` / `gate_closes`

Same guards, same transitions, different subject. The Gate's presence is
perfectly anti-correlated with the Switch reading 8, over all 337 frames, with
zero violations.

**The lift over `dir` on R-4 and R-5 is the most extrapolated thing in this
manual, and here is the exact argument.** Direct evidence is `down` only: three
witnesses, all `down`. The Switch's cell has walls on its three other sides, so
`up`, `left` and `right` are not merely unobserved, they are unreachable in this
level. I lifted anyway, on the recomputation table: the world answers to the
target cell's colour and never to the direction, demonstrated at 4/4 directions
for colour 0, 4/4 for colour 1, 3/3 reachable for colour 3 and 3/3 reachable for
colour 4. Writing the toggle as `down`-only would assert that this one colour
behaves differently from every other colour in the world, and I have no evidence
for that either. Between two unevidenced choices I took the one consistent with
the rest of the model, and flagged it: `theorem toggle_is_direction_free`,
probe: pending.

**What would separate them:** a level where the Switch is approachable from a
second side. No plan on *this* board can produce that observation, so the probe
is not a plan, it is a level. `probe_frontier` classes the related frontier as
"separable in principle, but the world was never observed in the required
state", which is the same conclusion reached from the other end.

I record that the a0 manual made the **opposite** call on its own single-witness
press (its R-05 rejected the lift and kept a ground rule). Its situation was not
this one: its world had no second colour-triggered interaction to generalise
from, so it had a pattern of one. Naming the divergence because a reader
comparing the two manuals will otherwise think one of us was careless.

### R-6 What blocks the Agent → **entailed**, not written as a rule

Colours 1, 5, 7 and 8 all leave the Agent where it is (71 + 1 + 2 + 1 = 75
transitions). The manual says this by **not** saying it: `step` requires
`free(toward(...))`, `warp_a`/`warp_b` require colours 3 and 4, and
`frame persist` does the rest. Writing a `blocked` rule would double-explain.

The Gate's solidity is the thin part: **one** witness, t18, the Agent pressing
`up` into the Gate's cell and not moving. It is thin because this level offers
exactly one reachable cell adjacent to the Gate — the Gate's other three
neighbours are wall. Carried as `theorem gate_is_solid`, probe: pending. If the
Gate turned out to be walkable scenery the manual would be wrong in a way the
trace cannot currently detect, and I would rather say that than round it off.

Note also that this is what forces `free` to mean "background colour **and**
unoccupied" rather than "background colour in the static map": the Gate's cell
is floor when the Gate is away, and not free when it is there.

### R-7 The fifteen no-op rows → **reject**, on the semantics section

`obj0_still_{UP,DOWN,LEFT,RIGHT}`, `obj1_still_{UP,DOWN,LEFT,RIGHT}`,
`obj2_still_{UP,DOWN,LEFT,RIGHT}` and the three lifted `obj{0,1,2}_still`
schemas — 15 rows, `effect: {"type": "none"}`.

**Criterion:** `semantics: frame persist` says an object no firing rule mentions
is unchanged. A rule whose effect is "unchanged" therefore states an instance of
an axiom the manual already contains, and is not a rule. This is the rejection
that A0 had to make by appealing to an axiom its manual did not carry (ledger
E-03); v0.2 makes the section mandatory precisely so the rejection has something
to cite, and this is that citation.

Two of the fifteen are also **wrong**, not merely redundant, which is worth
recording. `obj0_still_DOWN` and `obj2_still_DOWN` are annotated 92/92 with the
preferred guard `!at(6,6) and act==DOWN`. Their `cegis_guard` — the guard CEGIS
actually converged on — is `!tcolor(DOWN)==7 and !tcolor(DOWN)==8 and
act==DOWN`, which is the right shape. The frontier's *preferred* entry is the
level-constant one. Rejected twice over: as a no-op, and under R-2.

### R-8 `obj1_still_UP`, frontier truncated → **reject**, and flagged

`obj1_still_UP` reports `frontier: []` with `frontier_truncated: true` — the
only truncated frontier in the stream. Its `cegis_guard` covers 12 transitions,
which my table splits as 11 wall + 1 Gate (t18). So the truncation hid nothing I
needed; but a truncated frontier is an adjudication made by a budget rather than
by an argument, and if any verdict here had depended on that row I would have
had to say the evidence was unavailable rather than absent.

---

## G — the grounding pass (round 3)

### G-1 Why it happened

`compile.gen_python_a0`'s supported subset takes a **literal** direction, in
`act=push(o, <dir>)`, in the spatial reference, and in `moved(o, <dir>)`. A
direction-lifted clause raises `UnsupportedClause: moved(o, dir)`. So the seven
clauses of rounds 1–2 were expanded by hand into twenty-eight.

**This is a cost, not a correction.** No evidence arrived, no verdict moved, and
the lifted form remains what I think the world is: the twenty-eight clauses are
literally what `expand_theory` produced from the seven, name for name. What was
lost is exactly what ledger entry E-02 says is lost — `step`'s single 246/246
claim now reads as four claims of 72, 78, 42 and 54, each looking weaker than
the one fact they jointly are, and the reader has to reassemble them. Priced
here so the bill is visible.

### G-2 Witnessed versus extrapolated, clause by clause

Fourteen of the twenty-eight groundings have a witness in the trace and fourteen
do not. The manual marks the second group `ev: none cov: 0/0` rather than hiding
them.

| clause | up | down | left | right |
|---|---|---|---|---|
| `step_*` | **72** | **78** | **42** | **54** |
| `warp_a_*` (colour 3) | **2** | **2** | **3** | 0 † |
| `warp_b_*` (colour 4) | **2** | 0 † | **4** | **2** |
| `switch_press_*` (colour 7) | 0 ‡ | **2** | 0 ‡ | 0 ‡ |
| `gate_opens_*` (colour 7) | 0 ‡ | **2** | 0 ‡ | 0 ‡ |
| `switch_release_*` (colour 8) | 0 ‡ | **1** | 0 ‡ | 0 ‡ |
| `gate_closes_*` (colour 8) | 0 ‡ | **1** | 0 ‡ | 0 ‡ |

Bold = witnessed (14 clauses, 265 of the 336 transitions). † = the approach cell
is inside the border wall, so the grounding is **unreachable in this level**, not
untested; the pad's other three directions are witnessed and the lift is
measured. ‡ = the Switch has walls on three sides; also unreachable here, but
here **no** other direction is witnessed, so the lift is an extrapolation from
the world's uniformity and nothing else. Those six ‡ clauses in the toggle
families are the whole content of `theorem toggle_is_direction_free`.

Put plainly: two of the fourteen unwitnessed clauses (†) I would defend as
measured; twelve (‡) I would not, and six of those twelve are the ones a
different level could refute.

### G-3 What still does not compile, and what I refused to do about it

Three of the four backends now generate: `theory.py`, `theory.md`,
`domain.pddl` + `problem.pddl` + `problem.json`. **The Lean backend does not**,
and the failure is a name coupling in the toolchain rather than anything about
this world:

```
File "cold-start-a0/compile/gen_lean_a0.py", line 231, in generate_lean
    invariant, comment = built[0], built[1]
TypeError: 'NoneType' object is not subscriptable
```

Root cause, established by inspection rather than guessed: `build_axes`
(`gen_lean_a0.py:112,118,120`) discovers the state axes by probing
`probe.Cart_pos = cell` and `module.step(probe, ("push", "Cart", direction))` —
**the mover's name is hard-coded as `Cart`**. My mover is `Agent`, so no rule
ever matches, no observation ever varies, every candidate axis is dropped, and
`build_axes` returns `[]`. With no axes, the invariant builder finds neither
component and returns `None`, which `generate_lean` unpacks. `_term`
(`gen_lean_a0.py:161`) reads `state.Cart_pos` directly and would fail next.
Underneath that sits a second coupling: `compile_a3.switch_latch_invariant`
looks for an axis literally named `Door_present`, and my object is `Gate`.

Renaming `Agent` → `Cart` and `Gate` → `Door` makes it compile. **I did not do
it in this round.** Those names are verdicts O-1 and O-2, argued from the trace,
and — worse — they are the other arm's names. Changing mine to match tooling
that encodes them would manufacture exactly the agreement this experiment is
trying to measure, and would do it in the one place I have now been contaminated
about. So I escalated instead of deciding: the manual was left saying what I
think is true, and the call went to the coordinator. Logged as **E-L2-5**.

*Round 4 resolved this: the coordinator directed the rename, on the ground that
names carry no information and the cross-arm comparison quotients objects by
role rather than by label. §G-5 records what was done and what it means for the
comparison.*

### G-5 The rename (round 4)

`Agent` → `Cart`, `Gate` → `Door`. `Switch` unchanged; the two landmark names
unchanged, since nothing keys on those. Rule and law names followed for
readability only — `gate_opens_*` → `door_opens_*`, `gate_closes_*` →
`door_closes_*`, `gate_latch` → `door_latch`, `gate_is_solid` → `door_is_solid`,
`agent_unique` → `cart_unique`. Nothing else in the file moved: same 28 clauses,
same guards, same events, same `ev:`/`cov:` annotations, same semantics, same
two invariants, same three theorems, same `compress:` figures (they are computed
from the candidate payloads, which naming cannot touch).

Four hard-codings forced it, and they are worth listing because they are four
independent instances of one design fault:

| component | assumes |
|---|---|
| `certify.replay.ACTION_NAMES` | actions are `("push", "Cart", <dir>)` |
| `gen_python_a0.generate_python` | `mover="Cart"`, a default the driver never overrides |
| Lean invariant helpers | an axis literally named `Door_present` |
| the A3 goal binder | `state.Cart_pos` |

Three are upstream; the fourth is A3's own, inheriting the same assumption.

**What this costs the experiment.** Object names are now worthless as
comparison data — not because of the contamination declared at the top of this
file, but for the simpler reason that both arms were compelled into the same two
labels by the same four components. Any agreement on `Cart` and `Door` between
this manual and level 1's is an artifact of the toolchain and should be reported
as one. The comparison that survives is structural: how many clauses, over which
guards, with which semantics values, and which of them are witnessed.

**What it does not cost.** No verdict, no clause, no direction. `Cart` is still
the object O-1 identified as the only thing that moves; `Door` is still the
object O-2 identified as what the Switch controls and what blocks the mover.
I renamed the labels, not the referents.

### G-4 The landmark rename — a binding, not a verdict

The manual said `landmark warp_a_exit` / `warp_b_exit`. The problem builder
registers its landmark dictionary under `exit_a` / `exit_b`
(`a3pipeline/problem_frame.py:189`), and `patch_pddl_landmarks` rejects a manual
that jumps to a landmark the instance does not locate:

```
ValueError: the manual jumps to ['warp_a_exit', 'warp_b_exit'] but the problem
instance locates none of them; `LANDMARKS[...]` would KeyError at the first
step (trap T1)
```

Renamed, because a landmark's *name* is a binding between two files and carries
no claim about the world — unlike an object's name, which is O-2's verdict. The
underlying reading (R-3: the exits are level data reached by `jumped`) is
untouched. But nothing in `dsl_grammar_v0.2` says which side owns that name, and
a manual that guesses wrong fails at the first step. Logged as **E-L2-4**.

---

## L — laws

`zero_space` returned 2 global laws (of a 106-dimensional space, difference rank
34) and 104 cell-local laws.

### L-1 `(sum of 6@cell over 34 cells) mod 2 = 1` → **accept** as `agent_unique`

Written by the engine as a mod-2 parity over 34 literal cells, which cannot
enter a coordinate-free manual and, read literally, only says *an odd number of
Agents*. Rewritten as `count(Agent) = 1`. That is a **stronger** claim than the
engine's and I checked it rather than assuming it: every one of the 337 frames
has exactly one colour-6 cell, and segmentation reports one Agent track present
in 337/337 frames.

### L-2 `(5@(3,1) + 8@(7,6)) mod 2 = 1` → **accept** as `gate_latch`

Rewritten as `count(Gate) + count(Switch, 8) = 1`: the Gate is present exactly
when the Switch is not reading 8. Checked directly over all 337 frames — zero
violations. The Gate is absent on frames 62–140 and 231–336.

### L-3 Both invariants carry `status: open`, not `proven`

The sibling manuals write `proven`. I will not. `zero_space` observed these
holding on 336 transitions of one trajectory; that is an observation, and
`certify` has not been run against this manual (deliberately — running it is a
later step's job). `source: zero_space` records where the numbers came from,
which is what E-05 added the field for. If certify discharges them, it can
promote them.

### L-4 The 104 `cell_local` laws → **not read**

Same call A0 made. They are statements about named cells; the domain/problem
split forbids them in a manual, and reading 104 of them to reject 104 of them is
not adjudication.

---

## S — semantics

Mandatory, three statements, and each was checked against the trace rather than
copied.

| statement | value | how it was checked |
|---|---|---|
| `frame` | **persist** | Under `reset` the Gate would return to its frame-0 state on the transition after t61. It stays absent for 79 consecutive frames (62–140) and again for 106 (231–336), and the Switch holds its new colour just as long. `reset` is refuted, not merely unpreferred. |
| `conflict` | **exclusive** | The accepted guards partition the target colour: free (≡ colour 0), 3, 4, 7, 8. No two rules over one object can fire together. `mining.mutually_exclusive` is true for all three tracks independently, and `explains_every_transition` is true for all three. |
| `cascade` | **single_frame** | 336 actions, 337 frames — one action, one successor, no intermediate states anywhere in the trace. |

**`single_frame`'s parenthetical is load-bearing in this manual and not
decoration.** `switch_press` and `gate_opens` share the guard
`colored(toward(Agent, ?d), 7)`, and `switch_press` overwrites exactly the
colour that guard reads. Applied in file order rather than simultaneously
against the pre-state, `gate_opens` would re-read the cell, find colour 8, and
silently not fire — the Gate would never open and the manual would compile to a
world with no reachable second room. That is the A0 sprint's bug verbatim, and
this world reaches it at t61, t140 and t230.

**One honest limit.** `single_frame` and `multi_frame` are indistinguishable
when every rule set reaches quiescence after one round, which is the case here:
no accepted rule's effect can enable another accepted rule's guard, because
guards read the cell the Agent points at and no effect moves anything into that
cell. So the trace is consistent with `multi_frame` too. I chose `single_frame`
because it is what the trace shows and the weaker commitment; if a later level
produces a chain, this is the statement that has to change.

---

## P — probes

13 probe designs. None was run — running the world is not this step's job.

| tier | n | what they say |
|---|---:|---|
| `hypothetical` | 9 | "separable in principle, but the world was never observed in the required state" |
| (none) | 4 | "no experiment separates these guards in this world — extensionally identical; decide on description length" |

The 4 untiered ones are the `obj1_step_*` frontier and are settled in R-1 on
description length, openly. Of the 9 hypothetical ones, 6 concern the
`at(...)`-versus-colour question on the jumps, which R-2 closes on the contract
and R-3 closes again on the evidence; 3 concern the two `_still_DOWN` rows and
`obj1_still_DOWN`, all rejected as no-ops in R-7.

**No probe in the stream targets the thing I most want probed** — whether the
toggle fires from a direction other than `down` (R-4/R-5). `probe_frontier`
could not design it because it designs probes over *mined* guard alternatives,
and the miner never proposed a lifted toggle to disagree with. The gap is in the
proposal stage, not the probe stage.

---

## What I could not decide

Named rather than rounded off:

1. **`toggle_is_direction_free`.** Accepted into the manual as a lift; direct
   evidence is one direction. Separable only on a level where the Switch has a
   second reachable side. (R-4, R-5)
2. **`gate_is_solid`.** One witness. Separable on any level where the Gate has
   two reachable neighbours. (R-6)
3. **`free` vs `clear` vs `tcolor == 0`.** Extensionally identical here and, I
   argue, in any level of this world; the manual commits to `free` on
   description length and says so. (R-1)
4. **Whether the Gate may reappear under the Agent.** `gate_closes` has no
   precondition on the Agent's cell, and the one witness (t140) has the Agent
   standing next to the Switch, far from the Gate. So the manual permits a state
   the world may forbid. The DSL can express the guard, but I have no evidence
   for or against it and declined to invent one. This is the manual's most
   likely over-permission.
5. **`single_frame` vs `multi_frame`.** Indistinguishable on this trace; see §S.
6. **±1-bit concept accounts** for Gate and Switch. Admitted on load-bearing,
   not on price. (O-5)

## Expressivity ledger — things this grammar could not say

* **E-L2-1.** No way to state a precondition on an `appeared(o)` event's
  *location* being unoccupied (item 4 above). `appeared` takes only a subject.
* **E-L2-2.** No way to express "this landmark is a neighbour of that board
  feature". Had the warp exits been derivable that way, R-3 would have had a
  coordinate-free alternative to landmarks to weigh; as it stands the question
  could not even be posed in the DSL. Not requested as a change — the exits are
  underdetermined on the evidence anyway, so the landmark is the right answer
  here for an independent reason.
* **E-L2-3 (not a gap, a note).** The trace's `win` flag is true on six
  non-contiguous frames, all sharing one Agent cell. So the level's win
  predicate is positional and **not absorbing** — the Agent enters and leaves
  it. Nothing about that belongs in a `goal:` section this manual is forbidden
  to have, and it is level data regardless; recorded so the later planning step
  does not assume a win state is terminal.

* **E-L2-4 (round 3).** `dsl_grammar_v0.2` says a `landmark` names a cell the
  level locates, but does not say **who owns the name**. The manual guessed
  `warp_a_exit`; the problem builder registers `exit_a`; the PDDL patch rejects
  the mismatch at compile time. A contract that defines a cross-file binding
  should say which side is authoritative. (§G-4)
* **E-L2-5 (rounds 3–4).** Four components hard-code object names — `Cart` as
  the mover in `certify.replay`, in `gen_python_a0`'s `mover=` default and in
  the goal binder, and `Door_present` as an axis in the Lean invariant helpers.
  A manual is therefore not free to name its own objects, which contradicts the
  premise that `word_table` is the author's vocabulary. This is the single
  largest conformance cost in this arm: it consumed a whole round and it makes
  object names useless as cross-arm evidence. (§G-3, §G-5)

## Verification at the end of round 4

All six generated forms exist: `theory.py`, `theory.md`, `theory.lean`,
`domain.pddl`, `problem.pddl`, `problem.json`. The cheap certify layer replays
the full 337-frame sweep **green** — `anomaly_kinds: []`, `pixels_unexplained:
0`. Every one of the 336 transitions is predicted exactly by the manual as
written, which is the strongest check available without running the world.

Two things that green does **not** say, and should not be read as saying. It
does not vindicate the twelve unwitnessed toggle groundings (§G-2 ‡): they never
fire on this trace, so replaying it cannot test them. And it does not discharge
either invariant — `status: open` stands, because the cheap layer checks frames
against the manual, not the manual against a proof.

## What is not in the manual, on purpose

No `goal:` section. No coordinate, in a clause or in a comment. No literal
action sequence anywhere. No number that came from level 1, because level 1 was
never opened. Two object names that are the toolchain's rather than mine, and
are flagged as such in the file itself.
