# Case study 3 · A true theorem that is false

**Two Lean files. Same generator, same tactic, same `decide`, same empty axiom
list, both green. One of them is false of the world, and no check inside the
instrument can tell you which.**

Theoria §1.10a promises this artefact by name — *两层真值制度:Lean 担保「相对于说明书为真」;
说明书对不对得上世界,靠戳探与打脸。分开是特性——Phase 1 验收件 A2 的展品,正是一条「类型检查通过、
对世界为假」的定理* ([`../../Theoria.md:193`](../../Theoria.md)) — and §3.2 books it
as 图 5 ([`../../Theoria.md:416`](../../Theoria.md)). This case study is that
figure's text body: the exhibit, the six-beat repair, and what the pair of files
does and does not license.

---

## 0 · What was run instead of the literal A2

Phase 1's A2 item asks for the DC22 model to be ported into the DSL. DC22 is in
the sealed pile, and its upstream artifacts teach the mechanics as well as
playing does. The collision was raised, recorded as **INC-004**, and ruled on
2026-07-28, option (b): *A2 is fulfilled by a self-built world isomorphic to
DC22's failure structure … The isomorphism argument may cite only the structural
description already printed in Theoria §1.3 — no upstream DC22 artifact is ever
read* ([`../../cold-start-a2/A2_REPORT.md:22-26`](../../cold-start-a2/A2_REPORT.md)).

What that costs is stated first, not last: **no claim about DC22 itself is
available or made** — not its geometry, not its 175 frames, not how its search
actually failed ([`../../cold-start-a2/A2_REPORT.md:43-46`](../../cold-start-a2/A2_REPORT.md)).
What it buys is that §1.3's claim is *constructive*, so a self-built world can
make it **stronger** rather than merely re-illustrate it — and the strengthening
is the near-exhaustive history in §2 below
([`../../cold-start-a2/A2_REPORT.md:48-63`](../../cold-start-a2/A2_REPORT.md)).

## 1 · The exhibit is a deletion

`theory/theory_holed.dsl` is `theory/theory.dsl` with one rule removed:

```
rule teleport_down [ev: t183 cov: 1/1]
  when act=push(Cart, down) and colored(below(Cart), 3) then jumped(Cart, portal_exit)
```

— present at [`../../cold-start-a2/theory/theory.dsl:51-52`](../../cold-start-a2/theory/theory.dsl),
absent from [`../../cold-start-a2/theory/theory_holed.dsl`](../../cold-start-a2/theory/theory_holed.dsl),
which quotes it in its own header at
[`:6-8`](../../cold-start-a2/theory/theory_holed.dsl) as the thing it does not
contain.

**A precision the reports overstate.** [`../../cold-start-a2/A2_REPORT.md:69-71`](../../cold-start-a2/A2_REPORT.md)
says *"Nothing else differs; `diff` the files and the deletion is the whole
diff."* That is true of the manual's **rule content** and false of the file's
bytes. `diff theory/theory.dsl theory/theory_holed.dsl` also shows: the
`jumped` event dropped from the event line
([`:31`](../../cold-start-a2/theory/theory.dsl) → [`:60`](../../cold-start-a2/theory/theory_holed.dsl));
the four push rules re-counted 56/51/39/43 → 38/39/32/35
([`:34-43`](../../cold-start-a2/theory/theory.dsl) → [`:63-72`](../../cold-start-a2/theory/theory_holed.dsl));
the Cart's compression account re-priced 1891 → 1433
([`:21`](../../cold-start-a2/theory/theory.dsl) → [`:50`](../../cold-start-a2/theory/theory_holed.dsl));
and the pending theorem swapped from `teleport_is_colour_triggered` to
`right_room_locked` ([`:66`](../../cold-start-a2/theory/theory.dsl) →
[`:87`](../../cold-start-a2/theory/theory_holed.dsl)). Every one of those deltas
is what an honest re-derivation on the shorter evidence *should* produce — the
holed theorizer saw 184 frames, not the 248-frame sweep — so the methodology is
right and only the sentence is loose. Corrected here rather than repeated.

## 2 · Every gate goes green, and the theorem is false

The ordinary inner loop then runs on the holed manual and the play record,
unaltered and unassisted:

| gate | result |
|---|---|
| certify, cheap | **GREEN** — 184 frames, 14 904 pixels, **0 anomalies** |
| plan (`fd_adapter`) | **UNSAT** |
| certificate | `zero_space` → 21-cell occupancy law → 0/1 pagoda weight |
| certify, expensive | **GREEN** — Lean 4.9.0, `decide` only, no `sorry` |
| `#print axioms unsolvable` | **`[]`** |

— [`../../cold-start-a2/A2_REPORT.md:81-87`](../../cold-start-a2/A2_REPORT.md);
raw at [`../../cold-start-a2/artifacts/exhibit_report.json`](../../cold-start-a2/artifacts/exhibit_report.json)
(`certify_cheap`: `frames 184`, `pixels_checked 14904`, `pixels_unexplained 0`;
`certify_lean`: `returncode 0`, `sorries []`, `axiom_reports [{name: "unsolvable",
axioms: []}]`; `plan.status "UNSAT"`).

The theorem itself, verbatim from the generated file:

```lean
theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true := by
  rintro ⟨s, hr, hg⟩
  have hi : I s = true := inv_all s hr
  have hb : I s = false := goal_break s hg
  rw [hi] at hb
  exact absurd hb (by decide)

#print axioms unsolvable
```

— [`../../cold-start-a2/theory/generated_holed/theory.lean:784-791`](../../cold-start-a2/theory/generated_holed/theory.lean).
148 states, all decided by the kernel, no Mathlib, no `native_decide`, no axioms
([`../../cold-start-a2/A2_REPORT.md:88-90`](../../cold-start-a2/A2_REPORT.md)).

**And the world reaches the goal in 18 actions**
([`../../cold-start-a2/artifacts/refutation.json`](../../cold-start-a2/artifacts/refutation.json):
`episode.length 18`, `episode.final_win true`, `win_frames [18]`, `refuted true`).

The report's reading is the one that matters:

> Nothing in that column is broken. The planner is right: no plan exists *under
> this manual*. The invariant really is closed under the manual's `step`. Lean
> really did check it and the axiom list really is empty. **The manual is wrong,
> and every check in the column is a check of the manual against its own past.**
> — [`../../cold-start-a2/A2_REPORT.md:94-97`](../../cold-start-a2/A2_REPORT.md)

## 3 · The claim is bounded, and the bound is published

The same holed manual against the **full sweep** is RED: 128 unexplained pixels
across 20 088 checked, 44 anomalies, the first at t184, cell (6,4), where the
manual keeps the Cart the world has already teleported away
([`../../cold-start-a2/A2_REPORT.md:112-118`](../../cold-start-a2/A2_REPORT.md);
[`../../cold-start-a2/artifacts/exhibit_report.json`](../../cold-start-a2/artifacts/exhibit_report.json),
key `certify_cheap_vs_full_sweep`: `anomalies 44`, `frames 248`,
`first_anomaly {t: 184, cell: [6,4], kind: "render_mismatch", manual: 6, world: 0}`).

So the hole is invisible *relative to the evidence its theorizer had* — which is
exactly §1.3's claim and exactly its limit. The report says why it publishes the
second half: *"Reporting only the first half would be the kind of result this
project exists to refuse to write."*
([`../../cold-start-a2/A2_REPORT.md:117-118`](../../cold-start-a2/A2_REPORT.md)).

And the strengthening over DC22 is a counted one: the play record covers **163 of
the 164** reachable (state, action) pairs with the Cart in the left room, and
omits exactly the pair that fires the deleted rule
([`../../cold-start-a2/A2_REPORT.md:53-58`](../../cold-start-a2/A2_REPORT.md)).
The defect survives near-total evidence. It is not a coverage failure.

## 4 · The six beats

| beat | claim | evidence | result |
|---|---|---|---|
| **打脸** | the theorem is false | `refutation.json` | 18 actions, `win` on frame 18 |
| **定位** | §1.4's three-way narrows it | `locate_report.json` | board ✗, goal test ✗, **step ✓ at t=11** |
| **戳探** | predictions first, then execute | `probes.jsonl` | 5 designed, 4 run, 1 recorded unrunnable |
| **修订** | rewritten from the probe record | `theory_repaired.dsl` | re-derivable from grown evidence |
| **重证** | old certificate dies, true one replaces it | `repair_report.json` | Lean RED then GREEN |
| **解出** | plan, and the world agrees | `plan_repaired.json` | SAT in 18, 0 mismatches |

— [`../../cold-start-a2/A2_REPORT.md:129-136`](../../cold-start-a2/A2_REPORT.md).
Three of those rows are worth more than a row.

**定位 is a three-check, not a search.** §1.4 says the error is *necessarily* on
the witness path and in one of three places
([`../../Theoria.md:43`](../../Theoria.md)). All three are run rather than
stopping at the first, because *"step 12 disagrees" without "and the goal test and
the board were fine" has narrowed nothing*
([`../../cold-start-a2/A2_REPORT.md:139-143`](../../cold-start-a2/A2_REPORT.md)).
The verdict, from [`../../cold-start-a2/artifacts/locate_report.json`](../../cold-start-a2/artifacts/locate_report.json):
`checks: {misread_board: false, wrong_goal_test: false, mispredicted_step: true}`,
at `t: 11`, `mover_at [6,4]`, action `DOWN`, `rules_that_fired []`,
`manual_predicts [6,4]`, `world_shows [7,6]`.

Since no rule in the manual moves the mover more than one cell, the diagnosis is
sharper than "wrong": it is a **missing rule**. *Nothing can be corrected;
something has to be added*
([`../../cold-start-a2/A2_REPORT.md:144-147`](../../cold-start-a2/A2_REPORT.md)).

**One probe could not be run, and that is in the record.** R-05's guard frontier
never closed — `tcolor(DOWN)==3` and `at(6,4)` both fit the single witness, and
separating them needs a configuration this level cannot reach, because there is
exactly one Portal. `probe_frontier` ranks the experiment at 1.0 bits and
classifies it hypothetical
([`../../cold-start-a2/artifacts/probes.jsonl`](../../cold-start-a2/artifacts/probes.jsonl),
record `P-03`: `status "not_separable_in_this_world"`, `tier "hypothetical"`).
The manual therefore carries `teleport_is_colour_triggered [probe: pending]`
rather than quietly claiming the question settled
([`../../cold-start-a2/theory/theory.dsl:66-67`](../../cold-start-a2/theory/theory.dsl)).
The log's rule for this: *"A probe that cannot be run is a finding; a probe
quietly dropped is a lie."*
([`../../cold-start-a2/THEORIZE_LOG.md:190-191`](../../cold-start-a2/THEORIZE_LOG.md)).

**The refuted certificate has a corpse.** `theory/generated_repaired_stale/`
holds the exhibit's invariant regenerated against the *repaired* `step`. Lean
fails it at line 769 — `tactic 'decide' proved that the proposition ... is false`
— which is `inv_closed`'s case split
([`../../cold-start-a2/theory/generated_repaired_stale/theory.lean:767-769`](../../cold-start-a2/theory/generated_repaired_stale/theory.lean);
[`../../cold-start-a2/A2_REPORT.md:157-161`](../../cold-start-a2/A2_REPORT.md)).
The pagoda is broken by exactly the rule the probe added. The red file is kept
on purpose: *"A repaired manual that simply stopped mentioning its refuted
theorem would have been edited, not corrected."*
([`../../cold-start-a2/A2_REPORT.md:160-161`](../../cold-start-a2/A2_REPORT.md)).

The repair then closes: cheap certify green over the grown 196-frame trace
(15 876 pixels), Lean green with `axioms []` on both `unsolvable` and the latch
invariant, and the plan **SAT in 18 actions with `execution_mismatches: []`** —
the same length as the world's own shortest solution
([`../../cold-start-a2/artifacts/repair_report.json`](../../cold-start-a2/artifacts/repair_report.json)).

## 5 · The pair of files — the whole point

| | `generated_holed/theory.lean` | `generated_repaired/theory.lean` |
|---|---|---|
| theorem | `unsolvable` | `unsolvable` |
| goal | the goal cell (2,7) | the sealed pocket (7,1) |
| invariant | 0/1 pagoda weight, 0 on **21** cells | 0/1 pagoda weight, 0 on **35** cells |
| tactic | `decide` | `decide` |
| Mathlib | none | none |
| `#print axioms` | `[]` | `[]` |
| status | **GREEN** | **GREEN** |
| **true of the world** | **NO** — 18-action witness | **YES** — 0 of 55 reachable states |

— [`../../cold-start-a2/A2_REPORT.md:169-178`](../../cold-start-a2/A2_REPORT.md).

> They differ in their weight table and in nothing else. The generator, the
> tactic, the dependency surface and the axiom list are identical. **The
> instrument cannot tell them apart, and it is not supposed to be able to.** Lean
> guarantees *true relative to the manual*; whether the manual matches the world
> is settled by §1.4's refutation loop and nowhere else.
> — [`../../cold-start-a2/A2_REPORT.md:180-185`](../../cold-start-a2/A2_REPORT.md)

That is the two-layer regime of [`../../Theoria.md:51`](../../Theoria.md) — *机器
担保的是「相对于手册为真」;手册对不对得上世界,靠 1.4 的打脸机制。两层分开,是特性不是缺陷* —
delivered as two files a referee can diff and rerun.

One detail keeps the true one honest. The repaired manual's region had to be
**widened**: `zero_space` on the probed trace proposes 22 cells — everywhere the
Cart was observed, including (7,6) where the probe left it — and that law is *not*
closed under the repaired `step`, since one move inside the right room leaves it.
It was widened to the manual's own reachability closure, **35 cells**, computed
by running `theory.py` ([`../../cold-start-a2/THEORIZE_LOG.md:149-155`](../../cold-start-a2/THEORIZE_LOG.md)).
The log declines to blame the engine: *"this is the division of labour in
miniature, and the engine cannot be blamed for it: under-determined evidence is
all it had."*

## 6 · Was the repair remembered or re-derived?

The fair objection to any self-built A2 is that the repairer already knows the
answer, because the control manual sits in the same directory. Three checks
answer it, and none is "trust us"
([`../../cold-start-a2/A2_REPORT.md:190-206`](../../cold-start-a2/A2_REPORT.md)):

1. the repair was written from `probes.jsonl`, whose `P-01` record contains the
   holed manual's own prediction, written before the action and refuted by the
   outcome;
2. re-running the miner on `probed_trace.jsonl` proposes a jump effect again
   ([`../../cold-start-a2/artifacts/engines_diff_probed.json`](../../cold-start-a2/artifacts/engines_diff_probed.json)),
   so the repaired manual is derivable from the evidence the theorizer holds;
3. agreement with the control is asserted as a **test**, not assumed —
   `test_the_repair_agrees_with_the_control_on_that_rule` compares the two `when`
   clauses byte-for-byte, and it passing is a result: *the same frontier survived
   the same description-length adjudication twice.*

What is explicitly **not** claimed: that the repaired manual is uniquely
determined. P-03 says the opposite, on the record
([`../../cold-start-a2/A2_REPORT.md:208-209`](../../cold-start-a2/A2_REPORT.md)).

## 7 · The instrument was borrowed, and it broke twice

A2 writes no engine and no generator, because *an exhibit produced by a compiler
written for the exhibit would prove nothing about the instrument*
([`../../cold-start-a2/A2_REPORT.md:215-219`](../../cold-start-a2/A2_REPORT.md)).
Running the borrowed one on a second world found two defects A0 could not have
seen: **the PDDL backend cannot ground a teleport** (D-A2-006), so a manual
*containing* the teleport rule came back UNSAT — latent in A0, which reached its
goal through the Door and so *returned a correct answer by luck*
([`:221-230`](../../cold-start-a2/A2_REPORT.md)); and **`lean_check` destroys the
diagnostic when there is one** (D-A2-007), decoding Lean's U+2019-bearing errors
with a GBK locale and raising exactly when a proof fails — *A0 never had a red
Lean file. A2 has one on purpose.*
([`:232-235`](../../cold-start-a2/A2_REPORT.md)). Neither was fixed upstream, and
`artifacts/upstream_pin.json` hashes every upstream file A2 imports, so "which
compiler produced this exhibit" is a question the artefacts answer themselves
([`:237-240`](../../cold-start-a2/A2_REPORT.md)).

## 8 · What this case study does not show

* **Nothing about DC22.** Anything this project later says about DC22 must carry
  INC-004's `design_document_disclosed` caveat
  ([`../../cold-start-a2/A2_REPORT.md:43-46`](../../cold-start-a2/A2_REPORT.md),
  [`:270`](../../cold-start-a2/A2_REPORT.md)).
* **Nothing about whether an LLM would have written these manuals.** *The
  theorize step is done by hand here, as in A0 — the DSL files are checked in as
  artefacts. A2 tests the instrument and the loop, not the theorizer.*
  ([`../../cold-start-a2/A2_REPORT.md:271-273`](../../cold-start-a2/A2_REPORT.md)).
  This is the sharpest limit on the whole case-study set.
* **Nothing about scale.** 55 reachable states, 148 in the Lean enumeration,
  `decide` over the whole space. *The invariant is found because a wall separates
  two rooms; a world needing a genuinely clever pagoda is what A1 is for.*
  ([`../../cold-start-a2/A2_REPORT.md:274-276`](../../cold-start-a2/A2_REPORT.md)).
* **`fd_adapter` is still the bundled BFS stub**, not Fast Downward — optimal for
  unit costs, so `SAT`/`UNSAT` and plan length are sound here
  ([`../../cold-start-a2/A2_REPORT.md:277-279`](../../cold-start-a2/A2_REPORT.md)).
  Independently re-checked since: all seven generated cold-start domains, A2's
  base / holed / repaired among them, agree between the stub and real Fast
  Downward on plan length and on unsolvability — **7 of 7**
  ([`../../engine-rig/STATUS.md:103-107`](../../engine-rig/STATUS.md)).
* **The `?dir`-parameterised rules are not used.** The miner's better manual —
  one `obj1_step` at 189/189 instead of four ground rules — cannot be compiled,
  because the Python backend's guard subset takes a literal direction
  ([`../../cold-start-a2/A2_REPORT.md:280-283`](../../cold-start-a2/A2_REPORT.md)).

---

*Previous:* [`02-reversibility-beats-coverage.md`](02-reversibility-beats-coverage.md).
Chart data: [`data/cs03-two-lean-files.json`](data/cs03-two-lean-files.json).
