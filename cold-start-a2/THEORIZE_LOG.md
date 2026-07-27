# THEORIZE_LOG — cold-start-a2

The adjudication record. Every clause in the three `.dsl` files was written by
hand after reading a proposal in `artifacts/candidates*.jsonl`; this file says
which proposal, and why it was accepted, rejected, or carried as pending.

`O-` objects · `R-` rules · `L-` laws · `P-` the loop's beats.

**Ground truth discipline.** `artifacts/ground_truth.json` and
`a2world/GROUND_TRUTH.md` were not opened during O-, R- or L-. They were first
read at **P-6**, to score the repaired manual's `pocket_unreachable` theorem
against the world, and that read is the only one. The loop's own beats
(P-1 … P-5) go through frames: `solved_episode.jsonl` and `probes.jsonl`.

---

## O — objects

**O-01 · three tracks, three objects.** `mdl_segmenter` returned obj0 (colour 7),
obj1 (colour 6), obj2 (colour 5); `multi_miner` named obj1 the mover. Named
`Button`, `Cart`, `Door` by colour, which is the only stable handle the engine
emits. Compression ratio 0.6026 on the sweep (3953 script bits against 6560
baseline).

**O-02 · the Portal is board, not object.** Cell (7,4) carries colour 3 in every
frame of every trace, so `extract_board` sinks it to the board and it is not a
track. That is correct and it is worth naming: **the teleport's trigger is a
board feature, and board features do not get object hypotheses.** A theorizer
who only reads the object stream will never be prompted about it. This is a
second, independent reason the missing rule is easy to miss, alongside its
having no witness.

**O-03 · the pocket is board too.** (7,1) is floor, constant colour 0, sunk to
the board. It never appears in any proposal, in any trace. It is *named* for the
first time in `theory_repaired.dsl`'s `pocket_unreachable` — the theorize step
naming something the engines never proposed, which is what a manual is for.

**O-04 · Button and Door do not pay for themselves, and are admitted anyway.**
`artifacts/concept_accounts.json`: Cart +1891 bits, Button −5, Door −1 (on the
sweep). By Theoria §1.8's admission rule — a concept earns its place by making
the manual shorter — the Button and the Door should be rejected. They are
admitted on full-frame responsibility (their cells vary, so they cannot be
board) and on the invariant language having no pixel-level paraphrase of
`count(Button, 8) + count(Door) = 1`. Two of the framework's own criteria
disagree. **This is A0's finding (A0_REPORT §4), reproduced on a second world
rather than restated** — which is the only thing A2 can add to it.

---

## R — rules

**R-01 … R-04 · the four pushes.** `obj1_step_{UP,DOWN,LEFT,RIGHT}` on the
sweep, coverage 56/56, 51/51, 39/39, 43/43, guard `act==D AND free(strip(D))`.
Accepted as written. The miner also offers the `?dir`-parameterised
`obj1_step` at 189/189, which is the better manual; it is not used because the
Python backend's supported guard subset takes a literal direction
(`gen_python_a0`'s `UnsupportedClause`), so the four ground rules are the
compilable form of the same claim.

**R-05 · `teleport_down`, and the frontier that never closed.** Proposal
`obj1_jump_DOWN`, coverage **1/1**, transition t183, effect
`{"type":"move","dy":1,"dx":2}` — the only proposal in any A2 stream whose
effect moves the mover more than one cell (`artifacts/engines_diff.json`).

Its guard frontier has two survivors and the engines say so:
`["act==DOWN", "tcolor(DOWN)==3"]` and `["act==DOWN", "at(6,4)"]`.
`probe_frontier` ranks a separating experiment at 1.0 bits and classifies it
**hypothetical** — separating them needs either a second colour-3 cell or a Cart
on (6,4) with something else below it, and this level has exactly one Portal, so
neither configuration is reachable.

Adjudicated to `colored(below(Cart), 3)` on description length: the colour guard
is the one that would transfer to another level, and `at(6,4)` is a problem-level
fact wearing a domain-level rule's clothes (`dsl_grammar_v0.1`'s domain/problem
split). The choice is honest only if it is declared, so it is carried as
`theorem teleport_is_colour_triggered [probe: pending]` in both the control and
the repaired manual, and P-03 records the unrunnable experiment rather than
dropping it.

**R-06 · `press_up` and R-07 · `door_opens_up`.** `obj0_recolor8_UP` and
`obj2_vanish_UP`, both 1/1 at t90, identical guards
`act==UP AND tcolor(UP)==7`. Two rules with one guard is what
`cascade single_frame` means (D-A2-004); the PDDL backend reads the shared guard
and folds the vanish into the recolour action, which is the encoding, not an
assumption. Only one direction is witnessed because the Button sits in a
one-cell alcove — (1,1) has three walls — so unlike A0 there is no
direction-freedom question to carry here.

**R-08 · THE DELETION.** `theory_holed.dsl` is `theory.dsl` minus R-05, and the
`jumped` event and the `portal_exit` landmark lose their only user with it.
Nothing else changes; `diff` the two files and the deletion is the whole diff.

Four properties make the deletion isomorphic to the defect Theoria §1.3
describes, and each is checked by machine rather than asserted:

| §1.3's property | A2's check | result |
|---|---|---|
| the missing rule is a teleport | `engines_diff.json`, the only \|dy\|+\|dx\| > 1 proposal | yes |
| it never fired in the history | `trace_summary.json`, cut at t183 | 0 witnesses |
| the history owes it nothing | `exhibit_report.json` `certify_cheap` | 184/184, 0 anomalies |
| the holed model proves the goal unreachable | `generated_holed/theory.lean` | `unsolvable`, axioms `[]` |

And the check that bounds the claim rather than inflating it: the same manual
against the **full sweep** is RED, first anomaly at t184, cell (6,4) — the
manual keeps the Cart where the world has already teleported it away from. The
hole is invisible *to the evidence its theorizer had*. Not invisible.

**R-09 · the repair.** `theory_repaired.dsl` restores exactly one rule, written
from `probes.jsonl` P-01 and citing t194 in `probed_trace.jsonl`. That its guard
and effect come out identical to the control's R-05 is a **result, not an
input**: the same frontier survived the same adjudication, and
`tests/test_a2.py::test_the_repair_agrees_with_the_control_on_that_rule` is what
checks it. Re-running the miner on the grown evidence proposes the jump again
(`engines_diff_probed.json`), so the repaired manual is re-derivable from the
evidence rather than remembered.

---

## L — laws

**L-01 · `cart_unique`.** `count(Cart) = 1`. Proven, but **not in Lean**:
representing the state as the Cart's cell already assumes there is exactly one
Cart, so a Lean proof would be discharged by the representation. Checked where
it can actually fail — per frame, by the cheap layer's responsibility pass.
A0's call, kept.

**L-02 · `door_latch`.** `count(Button, 8) + count(Door) = 1`. Proposed by
`zero_space` as the GF(2) law `(8@0 + 5@31) mod 2 = 1`. Proved in Lean on the
control manual (`generated/theory.lean`, `inv_all`, axioms `[]`) and again on the
repaired manual (`generated_repaired/theory_latch.lean`) — a second Lean file
rather than a dropped invariant, because a manual that still declares a law owes
a proof of it.

**L-03 · `right_room_locked` — THE EXHIBIT.** A 0/1 pagoda weight: w = 0 on the
21 cells `zero_space`'s occupancy law supports, w = 1 elsewhere, and
`I(s) := w(cart) = 0`. Closed under the holed manual's `step` because that manual
has no rule moving the Cart more than one cell and the two rooms are not
adjacent. The goal cell carries w = 1, so `goal_break` holds and `unsolvable`
follows.

Lean: green, `#print axioms unsolvable` → `[]`. 37 arena cells × 2 Button
colours × 2 Door states = 148 states, all decided by the kernel.

**And it is false.** The world reaches the goal in 18 actions
(`refutation.json`). Nothing in the proof is broken. The manual is missing a
rule, and no amount of checking the manual against its own past could have said
so. This is the artefact Theoria §1.10a promises and Phase 1 asks A2 for.

**L-04 · the region had to be widened for the repaired manual.** `zero_space` on
`probed_trace.jsonl` proposes 22 cells — everywhere the Cart was observed,
including (7,6) where the probe left it. That law is **not closed** under the
repaired `step`: one move inside the right room leaves it. Widened to the
manual's own reachability closure (35 cells), computed by running `theory.py`.
See D-A2-009 — this is the division of labour in miniature, and the engine
cannot be blamed for it: under-determined evidence is all it had.

**L-05 · `pocket_unreachable` — the true one.** Same weight shape, same tactic,
same empty axiom list, `goal_cell = (7,1)`. Green. And scored against the
referee's copy: **0** reachable world states put the Cart in the pocket.

The two Lean files differ in their weight table and nothing else. The instrument
cannot tell them apart. Only the probes can.

---

## P — the loop

**P-1 · 打脸.** `refutation.json`. An 18-action episode, written out as
`solved_episode.jsonl` — frames, actions, win flag, nothing else — ends on the
goal with `win: true`. The axiom-free theorem is false.

**P-2 · 定位.** `locate_report.json`. §1.4's three-way, all three run rather than
stopping at the first: board misread **no**, goal test wrong **no**, step
mispredicted **yes**, at t=11. The Cart is at (6,4), the action is DOWN, the
manual fires **nothing** and predicts the Cart stays, the world puts it at (7,6)
— three cells away. No rule in the manual has an effect that moves the mover
more than one cell, so the defect is a **missing rule, not a wrong one**:
nothing here can be corrected, something has to be added.

**P-3 · 戳探.** `probes.jsonl`, five designed, four executed, predictions written
before acting in every case.

* **P-01** — the transition P-2 located. Three hypotheses on the record first,
  including the holed manual's own "stays". Observed: jumps to (7,6). Two
  refuted, one survives.
* **P-02.1–3** — the wall ring around the pocket, at the only three reachable
  (cell, action) pairs that touch it. All three confirm `ring_is_solid`. Run
  **before** L-05 is proved, not after.
* **P-03** — R-05's frontier. Designed, **not runnable**, recorded as such with
  the reason. A probe that cannot be run is a finding; a probe quietly dropped
  is a lie.

One ordering constraint, and it is the world's: the Portal is one-way, so every
left-room probe had to run before P-01. An irreversible world constrains
experiment *order*, not only experiment design. A0 met the mirror image of this
— an irreversible latch had ruled its divergent states out entirely.

**P-4 · 修订.** R-09 above. `probed_trace.jsonl` grows 184 → 196 frames and the
next certify covers the probes too.

**P-5 · 重证.** Two obligations, both discharged:

* the refuted certificate **dies**. L-03's invariant, regenerated against the
  repaired `step` into `generated_repaired_stale/`, fails at `theory.lean:769` —
  `tactic 'decide' proved that the proposition ... is false`. The pagoda is
  broken by exactly the rule the probe added. The red file is kept: a manual
  that dropped its refuted theorem silently would leave no trace of this.
* a true certificate **replaces it** — L-05.

**P-6 · 解出.** `plan_repaired.json`. SAT in 18 actions; the manual agrees, the
world agrees, zero execution mismatches. Same length as the world's own shortest
solution.

**P-6 is also where `ground_truth.json` was first opened**, to score L-05. Every
beat above it went through frames.
