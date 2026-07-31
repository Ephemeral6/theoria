# IC3_BOUNDS — where the fallback engine stops, on three axes

**Which tables here are generated, and which are not.** Every table between
`<!-- table:… -->` markers is injected from the run artefacts by
`python -m ic3bounds.document --write`; `--check` fails a build when one has
drifted. Exactly one table here has no markers — the scheme legend in axis B —
and it is labelled *(authored table)* where it appears. It contains no
measurements. An earlier draft said flatly "the tables are generated" while
carrying a hand-typed summary table whose every figure was wrong; that table is
now generated, and this paragraph exists so the claim matches the file.

**A rule this document follows, for the same reason.** Prose quotes only
*deterministic* numbers — clause counts, coverage, reachable-set sizes, LP
verdicts. Every timing lives in a generated table and is referred to, never
retyped. Wall clocks change between runs; a number retyped from an earlier run's
stdout does not.

M9 got `ic3_pdr` one non-linear inductive invariant, on peg `0111` — the
configuration `lp_potential` provably cannot certify. One point. Item E8 asked
where the line through it goes, along state-space size, predicate count and
mechanism composition, recording per rung the solve time, the invariant's size,
whether an independent checker still accepts it, and **the shape of the failure**
when there is one.

---

## The verdict, in five sentences

1. **IC3 returns a valid, independently rechecked invariant up to |S| = 8192 and
   does not finish |S| = 16384 within 300 seconds** — nor within 900, checked.
   But the *certificate* degrades before the clock does: the near-vacuity flag
   first fires at |S| = 2048, and the largest non-vacuous answer is |S| = 4096,
   half the headline.
2. **At a state space held exactly fixed, IC3's own clock moves by an order of
   magnitude with the encoding alone, and not monotonically in the number of
   predicates** — see the generated block table below for the per-block figures.
3. **The sharpest single result is not about vocabulary at all.** On peg, the
   `binary` and `native` rungs are *the same predicates in reverse declaration
   order*, over the same states — and they differ by a factor of six to eight.
   That is variable-ordering sensitivity, measured, with everything else pinned.
4. **Axis C does not measure what it was built to measure.** On five of its six
   rungs no edge leads into the bad set at all, so `¬bad` was already an
   inductive invariant and IC3's sub-second timings are closure checks rather
   than proof searches. No sentence about composition cost is supported by it.
5. The paper sentence this was run to settle, `Theoria.md` 1.10(b)'s
   *"LP/零空间够不着的形状由它兜"*, **half survives**. The LP half is now
   evidence: LP is infeasible on all ten peg rungs measured, with an algebraic
   witness. The null-space half does not: a GF(2) elimination separates the
   initial state from the goal on seven of those ten, and at n=4 the law it
   produces *is* the M9 invariant, character for character. (That is the
   *method*; `zero_space` **as shipped** does not do it — see below.)

---

## Axis A — state-space size

`runs/20260729T120000Z-E8-ic3-scale/axis_size_dense/axis_size.json`. Peg-1d,
start `0` + `1`×(n−1), one goal `01` + `0`×(n−2); the M9 configuration widened.
The goal is passed explicitly at every rung: `build_graph(goal_states=None)`
means *all* single-peg finals, which is a different question with a different
answer, and the `n=4` row is refused unless it renders the M9 CNF character for
character (`axis_size.check_anchor`, which raises).

**Why this axis is peg and not `worldgen`.** The item asks for `worldgen`'s
world family as the gradient, and axes B and C use it. Axis A cannot: the anchor
this ladder exists to extend is a *peg* configuration (M9's `0111`), and so is
the only place `lp_potential`'s infeasibility can be compared against IC3's
success. A size ladder on `worldgen` would be a different question with no anchor
and no LP comparison — worth running, and not this. `worldgen/` is imported
read-only throughout; nothing here writes into it.

**The ladder is walked densely, and that is a correction.** The measurement this
supersedes ran `4, 6, 8, 10, 12, 13, 14` — every rung even but one. Board parity
turns out to matter on this family: odd boards give a systematically more vacuous
invariant at the same |S|. The even ladder therefore reported the near-vacuity
onset two rungs late and fitted its cost exponent through a confound.

<!-- table:size begin -->
| n | \|S\| | verdict | clauses | literals | widest | saturation | frame | blocked | lit dropped | cls dropped | coverage | vacuous? | wall (s) | recheck | recheck=engine |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 16 | invariant | 2 | 4 | 2 | 0.5 | 2 | 6 | 15 | 1 | 8/16 | no | 0.075 | ACCEPT | 8=8 ok |
| 5 | 32 | invariant | 2 | 6 | 3 | 0.6 | 4 | 6 | 16 | 0 | 24/32 | no | 0.087 | ACCEPT | 24=24 ok |
| 6 | 64 | invariant | 8 | 26 | 4 | 0.541667 | 7 | 34 | 117 | 1 | 30/64 | no | 0.113 | ACCEPT | 30=30 ok |
| 7 | 128 | invariant | 4 | 17 | 6 | 0.607143 | 5 | 12 | 39 | 1 | 98/128 | no | 0.109 | ACCEPT | 98=98 ok |
| 8 | 256 | invariant | 11 | 52 | 7 | 0.590909 | 8 | 78 | 312 | 1 | 176/256 | no | 0.700 | ACCEPT | 176=176 ok |
| 9 | 512 | invariant | 9 | 53 | 8 | 0.654321 | 10 | 49 | 161 | 2 | 448/512 | no | 1.070 | ACCEPT | 448=448 ok |
| 10 | 1024 | invariant | 20 | 120 | 9 | 0.6 | 9 | 149 | 697 | 6 | 766/1024 | no | 9.093 | ACCEPT | 766=766 ok |
| 11 | 2048 | invariant | 14 | 106 | 10 | 0.688312 | 14 | 112 | 422 | 0 | 1910/2048 | **yes** | 15.181 | ACCEPT | 1910=1910 ok |
| 12 | 4096 | invariant | 29 | 215 | 11 | 0.617816 | 12 | 253 | 1343 | 13 | 3466/4096 | no | 104.985 | ACCEPT | 3466=3466 ok |
| 13 | 8192 | invariant | 20 | 173 | 12 | 0.665385 | 20 | 242 | 1120 | 3 | 7780/8192 | **yes** | 225.117 | ACCEPT | 7780=7780 ok |
| 14 | 16384 | timeout | - | - | - | - | - | - | - | - | - | - | 300.012 | n/a — no invariant | - |
<!-- table:size end -->

**Where it stops.** `n=14`, |S| = 16384, killed at 300 s — and at 900 s, run
separately to make sure the boundary was not a marginal budget artefact
(`axis_size_budget900/`). That is still a statement about this machine; the row
is flagged `machine_dependent` and a verify pass compares it on its verdict and
its budget alone.

*What is not claimed:* that `max_levels = 64` failed to bind at n=14. A killed
child reports no frame, so nothing is known about it. What is known is that the
cap did not bind on any rung that answered, and that frames grow with n — 12 at
n=12, 14 at n=11, 20 at n=13 — so the cap is something the top of this ladder is
walking towards rather than something it demonstrably avoided. The harness used
to assert the opposite in every timeout row's `detail`; it no longer does.

**Where it stops being worth anything, which is earlier.** The `vacuous?` column
is in the rendered table above, and `axis_size.json` now carries a `vacuity`
block that consumes it — it was being computed on every row and published on
none. Three facts from it:

* The flag **first fires at n=11, |S| = 2048** — a quarter of the headline, on a
  rung the previous ladder skipped.
* The **largest non-vacuous answer is n=12, |S| = 4096** — half the headline.
* n=13's invariant excludes **412** states; n=12's excludes **630**. From a
  state space twice the size, with fewer clauses and fewer literals. The answer
  did not merely become relatively weaker, it became *weaker*.

`literal_saturation` is the other degradation indicator —
`ic3bounds/harness.py` names it as the thing to watch: *"a ladder whose
saturation climbs toward 1.0 is watching IC3 degrade into state enumeration."*
It climbs, but **not monotonically over the ladder as a whole**: the sequence
splits by board parity, rising monotonically over the even boards with the odd
boards sitting systematically above them. The `vacuity.saturation` block reports
all three monotonicity questions as computed answers rather than asserting one —
an earlier version asserted "monotone", which was true of the every-other ladder
it was written against and false of this one.

**Two caveats that bound the whole axis.**

*This ladder scales the state space and not the difficulty.* The board starts
full, so the first jump is forced and the reachable set grows like n/2: **2
states at n=4, 6 at n=12, 7 at n=13**, inside state spaces of 16 and 8192. The
question "can `0111…1` reach `0100…0`" is settled by a seven-node breadth-first
search in microseconds; IC3 spends over three minutes on it at n=13. Any sentence
of the form "IC3 answers state spaces up to 8192" will be read as "the problem at
8192 is hard", and it is not — it is a seven-state reachability question embedded
in an 8192-point boolean cube. The axis measures cost against *state-space size*,
which is what E8 asked for, and nothing here says how IC3 behaves on a deep
instance.

*Explanatory content does not fall monotonically.* It rises from n=4 (0.500) to
n=6 (0.469 — a lower coverage is a stronger invariant) before falling. The trend
is real over the ladder; the first step runs against it.

---

## Axis B — predicate count, with the state space held exactly still

`runs/20260729T120000Z-E8-ic3-scale/axis_predicates.json`. New in this run.

Axis A cannot answer the question it raises. On peg-N the predicate count and
the state count are the same number — n booleans, 2^n states, one knob — so
"IC3 pays for the state space" and "IC3 pays for the vocabulary" fit its data
equally well and the ladder cannot choose between them.

This axis takes one world at a time and re-encodes it (`ic3bounds/reencode.py`).
Same states, same labelled edges, same initial state, same bad set; only the
number of booleans used to say it changes. Four schemes *(authored table)*:

| scheme | what it is | m |
|---|---|---|
| `binary` | bit *i* of the state's index. | ⌈log2 \|S\|⌉ |
| `native` | the variables the world came with. | n |
| `dual+k` | native, plus a second name for the negation of the first k — `free_pos3` beside `pos3`, which is what a modeller who writes both `occupied(i)` and `free(i)` has done. | n + k |
| `onehot` | one predicate per state: `is_01011010`. The manual that names every situation instead of describing one. | \|S\| |

Every block is one state space. Two gates run before IC3 on every rung: the
family's own transcription gate on the base system, and
`reencode.recoding_mismatches`, which reads every code back with a separately
written inverse and requires |S|, the labelled edge relation, the initial state
and the bad set to be identical. A failure is `adapter-mismatch`, escalated,
never tabulated as a boundary.

<!-- table:predicates begin -->
| board | \|S\| | encoding | m | slack | verdict | clauses | literals | saturation | coverage | abstraction | ic3 (s) | wall (s) | recheck |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| peg6 | 64 | binary | 6 | 0 | invariant | 4 | 13 | 0.541667 | 34/64 | 11.333333 | 0.0125 | 0.099 | ACCEPT |
| peg6 | 64 | native | 6 | 0 | invariant | 8 | 26 | 0.541667 | 30/64 | 10.0 | 0.0352 | 0.121 | ACCEPT |
| peg6 | 64 | dual+3 | 9 | 3 | invariant | 4 | 14 | 0.388889 | 35/64 | 11.666667 | 0.0154 | 0.103 | ACCEPT |
| peg6 | 64 | dual+6 | 12 | 6 | invariant | 8 | 26 | 0.270833 | 30/64 | 10.0 | 0.0541 | 0.142 | ACCEPT |
| peg6 | 64 | onehot | 64 | 58 | invariant | 1 | 3 | 0.046875 | 3/64 | 1.0 | 0.0031 | 0.089 | n/a — no native form |
| peg8 | 256 | binary | 8 | 0 | invariant | 6 | 24 | 0.5 | 146/256 | 36.5 | 0.1571 | 0.256 | ACCEPT |
| peg8 | 256 | native | 8 | 0 | invariant | 11 | 52 | 0.590909 | 176/256 | 44.0 | 0.5962 | 0.693 | ACCEPT |
| peg8 | 256 | dual+4 | 12 | 4 | invariant | 5 | 20 | 0.333333 | 141/256 | 35.25 | 0.0997 | 0.200 | ACCEPT |
| peg8 | 256 | dual+8 | 16 | 8 | invariant | 11 | 52 | 0.295455 | 176/256 | 44.0 | 0.9791 | 1.077 | ACCEPT |
| peg8 | 256 | onehot | 256 | 248 | invariant | 1 | 4 | 0.015625 | 4/256 | 1.0 | 0.0775 | 0.186 | n/a — no native form |
| peg10 | 1024 | binary | 10 | 0 | invariant | 7 | 32 | 0.457143 | 594/1024 | 118.8 | 1.5062 | 1.666 | ACCEPT |
| peg10 | 1024 | native | 10 | 0 | invariant | 20 | 120 | 0.6 | 766/1024 | 153.2 | 9.0820 | 9.254 | ACCEPT |
| peg10 | 1024 | dual+5 | 15 | 5 | invariant | 11 | 63 | 0.381818 | 759/1024 | 151.8 | 2.4791 | 2.642 | ACCEPT |
| peg10 | 1024 | dual+10 | 20 | 10 | invariant | 20 | 120 | 0.3 | 766/1024 | 153.2 | 15.3517 | 15.526 | ACCEPT |
| peg10 | 1024 | onehot | 1024 | 1014 | invariant | 1 | 5 | 0.004883 | 5/1024 | 1.0 | 2.0805 | 2.370 | n/a — no native form |
| peg12 | 4096 | binary | 12 | 0 | invariant | 8 | 41 | 0.427083 | 2386/4096 | 397.666667 | 13.3593 | 14.031 | ACCEPT |
| peg12 | 4096 | native | 12 | 0 | invariant | 29 | 215 | 0.617816 | 3466/4096 | 577.666667 | 104.7015 | 105.397 | ACCEPT |
| peg12 | 4096 | dual+6 | 18 | 6 | invariant | 12 | 77 | 0.356481 | 3063/4096 | 510.5 | 19.1989 | 19.873 | ACCEPT |
| peg12 | 4096 | dual+12 | 24 | 12 | invariant | 29 | 215 | 0.308908 | 3466/4096 | 577.666667 | 176.5502 | 177.242 | ACCEPT |
| peg12 | 4096 | onehot | 4096 | 4084 | invariant | 1 | 6 | 0.001465 | 6/4096 | 1.0 | 56.2456 | 58.840 | n/a — no native form |
| t1-tokens-lock | 128 | binary | 7 | 0 | invariant | 3 | 14 | 0.666667 | 117/128 | 2.34 | 0.0207 | 0.122 | n/a — no worldgen transcriber |
| t1-tokens-lock | 128 | native | 19 | 12 | invariant | 3 | 6 | 0.105263 | 121/128 | 2.42 | 0.0224 | 0.139 | n/a — no worldgen transcriber |
| t1-tokens-lock | 128 | onehot | 128 | 121 | invariant | 7 | 7 | 0.007812 | 121/128 | 2.42 | 0.6298 | 0.735 | n/a — no worldgen transcriber |
| t2-cycler-lock | 128 | binary | 7 | 0 | invariant | 2 | 10 | 0.714286 | 122/128 | 2.0 | 0.0130 | 0.132 | n/a — no worldgen transcriber |
| t2-cycler-lock | 128 | native | 19 | 12 | invariant | 2 | 4 | 0.105263 | 122/128 | 2.0 | 0.0143 | 0.117 | n/a — no worldgen transcriber |
| t2-cycler-lock | 128 | onehot | 128 | 121 | invariant | 6 | 6 | 0.007812 | 122/128 | 2.0 | 0.4843 | 0.591 | n/a — no worldgen transcriber |
<!-- table:predicates end -->

<!-- table:blocks begin -->
| block | \|S\| | reachable | m from → to | ic3 spread | wall spread | fastest by ic3 | its abstraction | its certificate | monotone in m? |
|---|---|---|---|---|---|---|---|---|---|
| peg6 | 64 | 3 | 6 → 64 | 17.3x | 1.6x | onehot | 1.0 | **state index** | **no** |
| peg8 | 256 | 4 | 8 → 256 | 12.6x | 5.8x | onehot | 1.0 | **state index** | **no** |
| peg10 | 1024 | 5 | 10 → 1024 | 10.2x | 9.3x | binary | 118.8 | world vocabulary | **no** |
| peg12 | 4096 | 6 | 12 → 4096 | 13.2x | 12.6x | binary | 397.666667 | world vocabulary | **no** |
| t1-tokens-lock | 128 | 50 | 7 → 128 | 30.5x | 6.0x | binary | 2.34 | **state index** | yes |
| t2-cycler-lock | 128 | 61 | 7 → 128 | 37.3x | 5.1x | binary | 2.0 | **state index** | yes |
<!-- table:blocks end -->

Two columns are the point of this table and neither is `n_clauses`. A clause set
over `onehot` vocabulary and one over `native` vocabulary are sentences in
different languages. What *is* comparable across a block is **coverage**, a set
of states, and **abstraction** = (states the invariant admits) ÷ (states actually
reachable). An inductive invariant must contain the reachable set;
`abstraction = 1.0` means it contains nothing else — the engine computed
reachability and returned it as a law.

### What the blocks say

**1. `binary` on peg is not a foreign vocabulary — it is the world's own,
reversed.** `peg_system` sorts its states as binary strings, so a state's index
*is* its bit string and `b_i` is exactly `pos_(n−1−i)`. This document asserted
the opposite for one draft, on the strength of the scheme's name; the
`vocabulary` and `adjudicable` columns are now **measured**
(`reencode.renaming_map` compares every predicate against every state) and they
disagree with the naming. The same measurement finds `binary` on the worldgen
worlds genuinely foreign — seven bits cannot rename nineteen variables — and
`onehot` foreign everywhere.

**2. Reversing the declaration order of the same predicates costs a factor of
six to eight.** peg10 `binary` and peg10 `native` are the *same ten predicates*
over the *same 1024 states*, differing only in the order they are declared in,
and the block table's `ic3 spread` shows what that costs. This is the cleanest
result on the axis: everything is pinned except one thing that ought not to
matter, and it matters a lot. It is a variable-ordering result, which is a known
sensitivity of this family of algorithms, measured here with the world held
exactly fixed.

**3. Cost is not monotone in predicate count** on any of the four peg blocks
(the two worldgen blocks are monotone; `monotone_in_predicates.per_board` reports
each). peg10 `dual+5` declares fifty per cent more predicates than `native` over
the identical state space and finishes faster. `onehot`, with a hundred times the
predicates, also finishes faster.

**4. On the peg blocks the cheaper certificate is also the tighter one.** peg10
`binary` admits 594 of 1024 states against `native`'s 766; peg12 `binary` admits
2386 of 4096 against 3466. Faster *and* stronger. What the extra predicates were
buying on those rungs was neither speed nor tightness — it was, at most, the
declaration order.

**5. `onehot` is where the trade is real.** It converges on exactly the reachable
set — `abstraction = 1.0`, 3 states of 64, 6 of 4096, verified against an
independent BFS — which satisfies all three Lean conditions and explains nothing.
Its predicates genuinely name state ordinals, its certificate genuinely has no
world form, and it is the fastest rung on the two smallest peg blocks. That is
speed bought with the certificate.

**Which clock.** The block table prints both. `ic3 spread` is the engine's own
clock, measured inside the child; `wall spread` includes process start-up. They
do not always agree about which rung was fastest — on the two worldgen blocks,
where every rung takes a few hundredths of a second, the wall clock puts `native`
first and the engine clock puts `binary` first. Findings 2–5 are stated on the
engine clock. **There are no repeats: every timing is one sample**, so a
sub-millisecond margin between two rungs is not a result, and the worldgen blocks'
margins are of that size. The peg blocks' orderings are not — they rest on
factors of six and up.

### The failure shapes

The item asked for the shape of each failure: *timeout / generalisation failure
/ certificate not recheckable*. Axis A only ever produced the first.

* **"Generalisation failure" does not exist in this engine and is not
  tabulated.** `pdr.generalise` iterates a finite sorted literal set and always
  returns a clause; worst case it drops nothing. It cannot fail, only fail to
  help — a continuous quantity, carried as `literal_saturation`.
* **"Certificate not recheckable" is real.** The `native`, `dual` and — once the
  column was measured rather than assumed — peg `binary` rungs all have a native
  form: `free_pos3` is `!pos3` under a second name, `b8` is `pos1` under
  another, so `reencode.desugar` rewrites the clause set into the world's own
  vocabulary literal for literal and hands it to `recheck/`, which shares no code
  with the engine. **Sixteen of the twenty peg rungs come back ACCEPT with both
  state counts agreeing.** The four `onehot` rungs have no such map — checked
  against every state, not assumed — and read `n/a — no native form`. They are
  never scored as a pass and never counted as a defect. The six worldgen rungs
  read `n/a — no worldgen transcriber`: nobody has written a second, independent
  transcription of worldgen's mechanisms, and a rechecker fed by the same adapter
  would only agree with itself.

### A caveat axis C states and axis B owes too

Coverage and abstraction on this axis are counted over the **declared** state
set, not over the 2^m boolean cube. `peg6/onehot`'s single clause admits
`3/64` of the declared states; the raw bit space it is written over has 2^64
points, almost none of which are well-formed codes. The re-encoding is a
bijection onto the declared set by construction and by gate, so every comparison
inside a block is sound — but "3 of 64" is a statement about the world, not about
the alphabet, and `n_states` is corrected away from the harness's `2 ** n` on
every row precisely so that no reader can read it the other way.

---

## Axis C — mechanism composition

`runs/20260729T120000Z-E8-ic3-scale/axis_compose.json`. Six worldgen worlds,
re-measured here with two columns the original ladder computed and never
published.

**This axis does not measure composition cost, and its original headline is
withdrawn.** The finding is in the `!bad inductive?` column:

**On five of the six rungs, no edge leads from outside the bad set into it.**
`¬bad` is therefore an inductive invariant on its own, the proof obligation is
discharged by a closure check, and IC3's sub-second timings measure it noticing
that. The `strengthening` column had been saying the same thing in a number whose
failing value is the neutral-looking 1.0 — the invariant is *exactly* the
complement of the bad set, and generalisation bought nothing. Five of six rungs
read 1.0. Five of six also carry the `near_vacuous` flag. The one rung that
required any strengthening at all, `t1-switch-latch`, is a **one-family** world.

<!-- table:compose begin -->
| world | fam | \|S\| | vars | bad | verdict | clauses | literals | widest | saturation | frame | blocked | coverage | vacuous? | strengthen | !bad inductive? | edges into bad | invariant mentions | recheck | wall (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| t1-switch-latch | 1 | 34 | 18 | 1 | invariant | 5 | 10 | 2 | 0.111111 | 6 | 19 | 29/34 | no | 5.0 | no | 1 | geometry, switch_door | not available | 0.122 |
| t1-tokens-lock | 1 | 128 | 19 | 7 | invariant | 3 | 6 | 2 | 0.105263 | 3 | 4 | 121/128 | **yes** | 1.0 | **yes** | 0 | geometry, count_lock | not available | 0.116 |
| t2-cycler-lock | 2 | 128 | 19 | 6 | invariant | 2 | 4 | 2 | 0.105263 | 3 | 3 | 122/128 | **yes** | 1.0 | **yes** | 0 | geometry, count_lock | not available | 0.107 |
| t2-lock-fragile | 2 | 576 | 30 | 21 | invariant | 3 | 6 | 2 | 0.066667 | 4 | 7 | 555/576 | **yes** | 1.0 | **yes** | 0 | geometry, count_lock | not available | 0.259 |
| t3-cycler-portal-lock | 3 | 432 | 41 | 9 | invariant | 2 | 4 | 2 | 0.04878 | 3 | 5 | 423/432 | **yes** | 1.0 | **yes** | 0 | geometry, count_lock | not available | 0.188 |
| t3-latch-maze | 3 | 1680 | 42 | 42 | invariant | 3 | 6 | 2 | 0.047619 | 4 | 7 | 1638/1680 | **yes** | 1.0 | **yes** | 0 | geometry, count_lock | not available | 0.828 |
<!-- table:compose end -->

**And the ladder never put composition into the question.** The artefact's own
`separability` block reports `n_families_in_invariant = 1` on every row,
including the two- and three-family worlds: every invariant names the variables
of at most one mechanism family. IC3 was never asked to reason across a
composition. So even setting the trivial rungs aside, the honest scope is not
"composition costs nothing for weak invariants" — it is **"composition costs
nothing for a property whose proof never crosses a family boundary,"** which is
narrower again, and is very close to a tautology.

What the axis does establish: the worldgen adapter is sound (the nine-check gate
passes on all six worlds), and IC3 handles composed worlds without breaking. That
is worth having. It is not a cost measurement.

The matched pair (`t1-tokens-lock` / `t2-cycler-lock`, 128 states and 19
predicates each) is a real control on size and vocabulary, but both halves are in
the already-inductive set, so the ratio between them compares two closure checks.

---

## The paper sentence

`Theoria.md:205`, the fallback-invariant row of the 1.10(b) engine table:

> 兜底归纳不变量 | **IC3/PDR** | 产出恰是 Lean 要的归纳不变量;**LP/零空间够不着的形状由它兜**

Theoria's own constraint 6 sets the bar: *全称断言必须带证明;裸 UNSAT 禁止*.
Split the sentence in two and the halves land very differently.

### The LP half: now evidence

`runs/20260729T120000Z-E8-ic3-scale/lp_reach.json`. `lp_potential` was run on
ten unsolvable peg rungs, n = 4…13, each confirmed unsolvable twice
independently. **It returns a certificate on none of them.**

Infeasibility is not merely the solver's report. The artefact records an
algebraic witness, in three steps rather than the two an earlier draft of this
paragraph compressed it into:

1. Summing the two opposite jump rows over each triple `(i, i+1, i+2)` gives
   `−2·w[i+1] ≤ 0`, so every interior weight `w[1..n−2] ≥ 0`.
2. The top triple's reverse row gives `w[n−3] ≤ w[n−2] + w[n−1]`, and `w[n−3] ≥ 0`
   by step 1, so `w[n−2] + w[n−1] ≥ 0` — which is what bounds the *last* weight,
   the one step 1 does not reach.
3. Hence `Σ_{i≥2} w[i] ≥ 0`, while the goal row demands `Σ_{i≥2} w[i] ≤ −margin < 0`.

The artefact machine-checks the premise — that both directions of every triple
really are rows of the LP the engine builds
(`both_directions_present_on_every_triple: true`, `missing_move_rows: []`, all
ten rungs). **The inequality chain itself is hand algebra and is not
machine-verified**, which the artefact says in its own caveats and which this
section, quoting constraint 6, has no business omitting. Corroborated three
further ways: solver status *infeasible* rather than iteration-limit at every
rung, the same verdict at `bound` = 10, 100 and 10000, and the same verdict with
the box constraint deleted. Positive controls (`1110→0100`, `11011→01000`) return
weights that pass `check_exactly`, so the harness does find certificates when
they exist.

So on every rung of axis A that answered, IC3 certifies something no *linear*
pagoda can. That is a line, not a point: D-014's claim at one configuration,
generalised to ten. Two scope limits: linear pagodas only — a quadratic or
state-dependent potential is a different question — and one goal state per rung,
which is the LP's best case rather than its worst.

### The null-space half: not supported

The GF(2) conservation laws of the same family — `c[i]+c[i+1]+c[i+2] = 0 mod 2`
— separate the initial state from the goal on **seven of the ten** rungs
(n = 4, 6, 7, 9, 10, 12, 13), missing only n ≡ 2 (mod 3). **n=8 is the only rung
of axis A's six where IC3 is the only one of the three methods that gets there.**
(Nothing is claimed about n=5 or n=11, where GF(2) also misses and IC3 was run
only on the dense ladder, not against LP.)

And the sharpest form of it: at n=4 the GF(2) global law renders as
*positions 1 and 2 always agree* — the M9 invariant, the anchor `check_anchor`
pins the whole ladder to, character for character. The point E8 was built to
extend into a line is one linear elimination away.

**The qualification, stated here rather than only in a footnote:** this is the
*method*, not the engine. `zero_space.analyse` as shipped consumes a trajectory,
takes no goal and returns no unreachability verdict, and on this family a
trajectory is at most n/2 states long. The result above comes from handing its
GF(2) core the move geometries' difference vectors instead. So `zero_space`
**as built** does not reach these rungs and **could**. That is a finding about
`zero_space`, and it is not an exoneration of the sentence: the sentence claims
a shape is out of the null space's reach, and it is not.

### What may be written

Supported by the artefacts:

> On unsolvable peg-1d configurations from |S| = 16 to |S| = 8192,
> `lp_potential` is infeasible at every rung, with an algebraic witness, and
> `ic3_pdr` returns an inductive invariant at every rung, independently
> rechecked. The invariant's explanatory content falls as the state space grows:
> it is flagged near-vacuous from |S| = 2048 upward, and at |S| = 8192 it
> excludes fewer states in absolute terms than at |S| = 4096. At |S| = 16384 the
> engine exceeds both a 300-second and a 900-second budget *on one machine*. At a
> state space held exactly fixed, the engine's cost varies by an order of
> magnitude with the boolean encoding, and by a factor of six to eight between
> two encodings that differ only in the declaration order of the same predicates.

Not supported, and should not be written:

* "the shapes **LP and the null space** cannot reach" — a GF(2) elimination
  reaches five of the six.
* anything about **composition cost** drawn from axis C: five of its six rungs
  had an already-inductive property and every invariant on it names one family.
* "IC3 covers what LP cannot" **without** the encoding qualification.
* anything about IC3 on *hard* instances. The peg ladder's instances are 2 to 7
  states deep. (The two worldgen blocks are deeper — 50 and 61 reachable states
  of 128 — but they are not on the LP comparison.)

---

## Gaps, stated

1. **The peg ladder scales |S|, not difficulty.** Reachable sets are 2–7 states.
   A second family whose reachable set grows with the board is the missing
   experiment, and nothing here substitutes for it.
2. **Axis C has no rung where composition bites.** Five of six discharge on a
   closure check and all six are separable. `worldgen` documents
   `t2-lock-fragile` as sitting outside the current engine vocabulary; a ladder
   built around rungs like that would measure what this one was supposed to.
3. **Every timing is a single sample.** No repeats, no medians, no dispersion.
   The peg orderings survive that; the two worldgen blocks' orderings do not, and
   are not relied on.
4. **No worldgen rung has an independent recheck**, on either axis. Four of axis
   B's twenty-six rungs are a real boundary (an `onehot` certificate has no world
   form); six are a missing transcriber, which is work someone could do.
5. **`tautologies_dropped` is structurally zero** for this engine's output, for
   reasons `reencode.desugar`'s docstring sets out. It is a guard against a
   different producer, not a measurement, and its zeroes are evidence of nothing.
6. **`ENGINE_TABLE.md`'s `ic3_pdr` row is now stale, and could not be fixed from
   here.** It says "no state-space ladder, no predicate-count ladder, no timeout,
   no failure-shape census" and names E8 as the open item; all four now exist.
   Neither that file nor its generator `tools/engine_table.py` is present at this
   branch's base commit — both landed on `master` afterwards — so the correction
   has to be made after this merges, by adding probes over `axis_predicates.json`
   and `lp_reach.json` in the generator's own `FACTS` style.
7. **`--check` guards the marked tables, not the prose.** Nothing can guard the
   prose. One authored table remains — the scheme legend, which carries no
   measurements — and it is labelled.
8. **One machine — and, for part of the final pass, a busy one.** Another
   session on this host was running `exam.verify` and `exam.tools.run_selftest`
   concurrently with part of the axis B measurement; the processes were observed,
   not inferred. Absolute timings in these artefacts are therefore inflated by an
   unknown amount, which is one more reason the boundary at n=14 was re-run at
   900 s rather than argued about, and why nothing here compares a wall clock for
   equality. What the findings rest on is *orderings within a block*, whose rungs
   run sequentially under the same conditions, and *factors of six and up*; a
   uniform slowdown does not reverse those. It could in principle reverse a
   sub-millisecond margin, which is exactly the margin the two worldgen blocks
   have — and they are the two the document already declines to rely on.

---

## Reproducing and checking

```bash
cd engine-rig

# the three axes (axis A dense ~12 min, axis B ~8 min, axis C ~2 s)
python -m ic3bounds --out runs/<id> --axis size
python -m ic3bounds --out runs/<id> --axis predicates
python -m ic3bounds --out runs/<id> --axis compose

# re-check the artefacts WITHOUT re-running the search: every published
# invariant is handed back to the independent checker, every derived column is
# recomputed, timings are checked for presence and ordering only
python -m ic3bounds.verify runs/20260729T120000Z-E8-ic3-scale \
                           runs/20260729T120000Z-E8-ic3-scale/axis_size_dense

# fail if a marked table in this file is no longer what the artefacts render
python -m ic3bounds.document --check

# the tests behind all of it
python -m pytest tests/test_ic3bounds_reencode.py \
                 tests/test_ic3bounds_axis_predicates.py \
                 tests/test_ic3bounds_harness.py \
                 tests/test_ic3bounds_recheck_column.py \
                 tests/test_ic3bounds_emit.py \
                 tests/test_ic3bounds_worldgen.py
```

Structural fields are re-derived and compared exactly; wall clocks are checked
for presence and ordering and never for equality (`bench/README.md` rule 3). A
`timeout` row is flagged `machine_dependent` and compared on its verdict and its
budget alone — a faster machine finishing what this one could not is news, not a
failure.
