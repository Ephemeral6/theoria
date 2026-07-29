# IC3_BOUNDS — where the fallback engine stops, on three axes

**The tables in this file are generated.** Do not edit them by hand; run
`python -m ic3bounds.document --write`, and `python -m ic3bounds.document --check`
to fail a build when they have drifted from the artefacts. The prose is
authored, and is the part a reader should argue with.

M9 got `ic3_pdr` one non-linear inductive invariant, on peg `0111` — the
configuration `lp_potential` provably cannot certify. One point. Item E8 asked
where the line through it goes, along state-space size, predicate count and
mechanism composition, recording per rung the solve time, the invariant's size,
whether an independent checker still accepts it, and **the shape of the failure**
when there is one.

---

## The verdict, in four sentences

1. **IC3 answers to |S| = 8192 and is stopped at 16384** by a 300-second budget
   on this machine — but the *certificate* degrades long before the clock does,
   from excluding half the state space at n=4 to excluding five per cent of it
   at n=13, where the engine's own near-vacuity flag fires.
2. **At a state space held exactly fixed, IC3's cost moves by 12–35× with the
   encoding alone, and not monotonically in the number of predicates.** On all
   six held-fixed blocks the *fastest* encoding is one whose certificate
   contains no word of the world's own vocabulary.
3. **Composing mechanism families costs nothing measurable** (axis C), on
   invariants that are close to vacuous — which makes that a narrower sentence
   than it sounds.
4. The paper sentence this was run to settle, `Theoria.md` 1.10(b)'s
   *"LP/零空间够不着的形状由它兜"*, **half survives**. The LP half is now
   evidence rather than assertion: LP is provably infeasible on all ten peg
   rungs measured. The null-space half does not survive: a GF(2) elimination
   separates the initial state from the goal on seven of those ten, and at n=4
   the law it produces *is* the M9 invariant, character for character.

---

## Axis A — state-space size

`runs/20260728T203711Z-E8-ic3-bounds/axis_size.json`. Peg-1d, start
`0` + `1`×(n−1), one goal `01` + `0`×(n−2); the M9 configuration widened. The
goal is passed explicitly at every rung: `build_graph(goal_states=None)` means
*all* single-peg finals, which is a different question with a different answer,
and the `n=4` row is refused unless it renders the M9 CNF character for
character (`axis_size.check_anchor`, which raises).

<!-- table:size begin -->
| n | \|S\| | verdict | clauses | literals | widest | saturation | frame | blocked | lit dropped | cls dropped | coverage | wall (s) | recheck | recheck=engine |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 16 | invariant | 2 | 4 | 2 | 0.5 | 2 | 6 | 15 | 1 | 8/16 | 0.069 | ACCEPT | 8=8 ok |
| 6 | 64 | invariant | 8 | 26 | 4 | 0.541667 | 7 | 34 | 117 | 1 | 30/64 | 0.109 | ACCEPT | 30=30 ok |
| 8 | 256 | invariant | 11 | 52 | 7 | 0.590909 | 8 | 78 | 312 | 1 | 176/256 | 0.648 | ACCEPT | 176=176 ok |
| 10 | 1024 | invariant | 20 | 120 | 9 | 0.6 | 9 | 149 | 697 | 6 | 766/1024 | 8.751 | ACCEPT | 766=766 ok |
| 12 | 4096 | invariant | 29 | 215 | 11 | 0.617816 | 12 | 253 | 1343 | 13 | 3466/4096 | 101.900 | ACCEPT | 3466=3466 ok |
| 13 | 8192 | invariant | 20 | 173 | 12 | 0.665385 | 20 | 242 | 1120 | 3 | 7780/8192 | 214.211 | ACCEPT | 7780=7780 ok |
| 14 | 16384 | timeout | - | - | - | - | - | - | - | - | - | 300.013 | n/a — no invariant | - |
<!-- table:size end -->

**Where it stops.** `n=14`, |S| = 16384, killed at 300 s. That is a statement
about this budget and this machine — the row is flagged `machine_dependent` and
a verify pass compares it on its verdict and its budget alone. `max_levels = 64`
never binds on this family; the deepest convergence seen is frame 20. So the
wall is the clock, not a knob.

**Where it stops being worth anything, which is earlier.** Read the `coverage`
column, not the verdict:

| n | 4 | 6 | 8 | 10 | 12 | 13 |
|---|---|---|---|---|---|---|
| fraction of |S| the invariant admits | 0.50 | 0.47 | 0.69 | 0.75 | 0.85 | **0.95** |

At n=4 the invariant is a law — *positions 1 and 2 always hold the same thing*,
two clauses, half the state space excluded. At n=13 it is twenty clauses
excluding five per cent, and `near_vacuous` is `true` on that row against the
module's declared 0.9 threshold. It is a sound proof and it explains nothing. A
reader who takes "answered" as the boundary gets |S| = 8192; a reader who wants
an invariant a person can adjudicate should read the boundary as **somewhere
between n = 10 and n = 12**, and the ladder does not resolve it more finely
than that.

**A caveat that bounds the whole axis.** This ladder scales the state space and
not the difficulty. The board starts full, so the first jump is forced and the
reachable set grows like n/2: **2 states at n=4, 6 at n=12, 7 at n=13**, inside
state spaces of 16 and 8192. Every rung is a shallow instance in an
exponentially larger space. The cost curve is therefore IC3's cost *against
state-space size*, which is what E8 asked for, and it is emphatically not a
cost against problem hardness. Nothing here says how IC3 behaves on a deep
instance.

---

## Axis B — predicate count, with the state space held exactly still

`runs/20260729T120000Z-E8-ic3-scale/axis_predicates.json`. New in this run.

Axis A cannot answer the question it raises. On peg-N the predicate count and
the state count are the same number — n booleans, 2^n states, one knob — so
"IC3 pays for the state space" and "IC3 pays for the vocabulary" fit its data
equally well and the ladder cannot choose between them.

This axis takes one world at a time and re-encodes it (`ic3bounds/reencode.py`).
Same states, same labelled edges, same initial state, same bad set; only the
number of booleans used to say it changes. Four schemes:

| scheme | what it is | m |
|---|---|---|
| `binary` | bit *i* of the state's index. No predicate means anything. | ⌈log2 \|S\|⌉ |
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
| peg6 | 64 | binary | 6 | 0 | invariant | 4 | 13 | 0.541667 | 34/64 | 11.333333 | 0.0124 | 0.104 | n/a — no native form |
| peg6 | 64 | native | 6 | 0 | invariant | 8 | 26 | 0.541667 | 30/64 | 10.0 | 0.0348 | 0.128 | ACCEPT |
| peg6 | 64 | dual+3 | 9 | 3 | invariant | 4 | 14 | 0.388889 | 35/64 | 11.666667 | 0.0147 | 0.117 | ACCEPT |
| peg6 | 64 | dual+6 | 12 | 6 | invariant | 8 | 26 | 0.270833 | 30/64 | 10.0 | 0.0522 | 0.144 | ACCEPT |
| peg6 | 64 | onehot | 64 | 58 | invariant | 1 | 3 | 0.046875 | 3/64 | 1.0 | 0.0032 | 0.098 | n/a — no native form |
| peg8 | 256 | binary | 8 | 0 | invariant | 6 | 24 | 0.5 | 146/256 | 36.5 | 0.1519 | 0.264 | n/a — no native form |
| peg8 | 256 | native | 8 | 0 | invariant | 11 | 52 | 0.590909 | 176/256 | 44.0 | 0.5953 | 0.701 | ACCEPT |
| peg8 | 256 | dual+4 | 12 | 4 | invariant | 5 | 20 | 0.333333 | 141/256 | 35.25 | 0.1006 | 0.199 | ACCEPT |
| peg8 | 256 | dual+8 | 16 | 8 | invariant | 11 | 52 | 0.295455 | 176/256 | 44.0 | 0.9668 | 1.072 | ACCEPT |
| peg8 | 256 | onehot | 256 | 248 | invariant | 1 | 4 | 0.015625 | 4/256 | 1.0 | 0.0772 | 0.186 | n/a — no native form |
| peg10 | 1024 | binary | 10 | 0 | invariant | 7 | 32 | 0.457143 | 594/1024 | 118.8 | 1.4429 | 1.607 | n/a — no native form |
| peg10 | 1024 | native | 10 | 0 | invariant | 20 | 120 | 0.6 | 766/1024 | 153.2 | 9.2482 | 9.416 | ACCEPT |
| peg10 | 1024 | dual+5 | 15 | 5 | invariant | 11 | 63 | 0.381818 | 759/1024 | 151.8 | 2.4446 | 2.622 | ACCEPT |
| peg10 | 1024 | dual+10 | 20 | 10 | invariant | 20 | 120 | 0.3 | 766/1024 | 153.2 | 15.2930 | 15.466 | ACCEPT |
| peg10 | 1024 | onehot | 1024 | 1014 | invariant | 1 | 5 | 0.004883 | 5/1024 | 1.0 | 2.0989 | 2.390 | n/a — no native form |
| peg12 | 4096 | binary | 12 | 0 | invariant | 8 | 41 | 0.427083 | 2386/4096 | 397.666667 | 13.7709 | 14.460 | n/a — no native form |
| peg12 | 4096 | native | 12 | 0 | invariant | 29 | 215 | 0.617816 | 3466/4096 | 577.666667 | 106.6268 | 107.318 | ACCEPT |
| peg12 | 4096 | dual+6 | 18 | 6 | invariant | 12 | 77 | 0.356481 | 3063/4096 | 510.5 | 18.9132 | 19.571 | ACCEPT |
| peg12 | 4096 | dual+12 | 24 | 12 | invariant | 29 | 215 | 0.308908 | 3466/4096 | 577.666667 | 179.6764 | 180.366 | ACCEPT |
| peg12 | 4096 | onehot | 4096 | 4084 | invariant | 1 | 6 | 0.001465 | 6/4096 | 1.0 | 69.8745 | 72.685 | n/a — no native form |
| t1-tokens-lock | 128 | binary | 7 | 0 | invariant | 3 | 14 | 0.666667 | 117/128 | 2.34 | 0.0217 | 0.404 | n/a — no worldgen transcriber |
| t1-tokens-lock | 128 | native | 19 | 12 | invariant | 3 | 6 | 0.105263 | 121/128 | 2.42 | 0.0231 | 0.131 | n/a — no worldgen transcriber |
| t1-tokens-lock | 128 | onehot | 128 | 121 | invariant | 7 | 7 | 0.007812 | 121/128 | 2.42 | 0.6208 | 0.732 | n/a — no worldgen transcriber |
| t2-cycler-lock | 128 | binary | 7 | 0 | invariant | 2 | 10 | 0.714286 | 122/128 | 2.0 | 0.0128 | 0.275 | n/a — no worldgen transcriber |
| t2-cycler-lock | 128 | native | 19 | 12 | invariant | 2 | 4 | 0.105263 | 122/128 | 2.0 | 0.0157 | 0.125 | n/a — no worldgen transcriber |
| t2-cycler-lock | 128 | onehot | 128 | 121 | invariant | 6 | 6 | 0.007812 | 122/128 | 2.0 | 0.4889 | 0.597 | n/a — no worldgen transcriber |
<!-- table:predicates end -->

Two columns are the point of this table and neither is `n_clauses`. A clause set
over `onehot` vocabulary and one over `native` vocabulary are sentences in
different languages, and `onehot`'s single clause is not a simpler certificate
than `native`'s twenty-nine. What *is* comparable across a block is **coverage**,
a set of states, and **abstraction** = (states the invariant admits) ÷ (states
actually reachable). An inductive invariant must contain the reachable set;
`abstraction = 1.0` means it contains nothing else — the engine computed
reachability and returned it as a law.

### What the blocks say

| block | \|S\| | reachable | m from … to | IC3-clock spread | fastest | its abstraction | is the fastest certificate in world vocabulary? |
|---|---|---|---|---|---|---|---|
| peg6 | 64 | 3 | 6 → 64 | **14.8×** | `onehot` | 1.00 | no |
| peg8 | 256 | 4 | 8 → 256 | **12.2×** | `onehot` | 1.00 | no |
| peg10 | 1024 | 5 | 10 → 1024 | **11.7×** | `binary` | 118.8 | no |
| peg12 | 4096 | 6 | 12 → 4096 | **13.1×** | `binary` | 397.7 | no |
| `t1-tokens-lock` | 128 | 50 | 7 → 128 | **31.0×** | `binary` | 2.34 | no |
| `t2-cycler-lock` | 128 | 61 | 7 → 128 | **35.0×** | `binary` | 2.00 | no |

**1. Cost is not monotone in predicate count.** `monotone_in_predicates` reports
`false`, on every block. The clearest single pair is peg10: `dual+5` declares
*fifty per cent more* predicates than `native` over the identical state space
and finishes in 2.44 s against 9.25 s — nearly 4× faster with more vocabulary.
And `onehot`, with a hundred times the predicates, finishes in 2.10 s.

**2. Neither is it determined by predicate count and state count together.**
peg10 `binary` and peg10 `native` declare *the same ten predicates* over *the
same 1024 states*, and differ by 6.4× (1.44 s against 9.25 s). Everything about
those two rungs is equal except which ten booleans were chosen. Whatever IC3 is
paying for, it is not a number this axis or axis A can name.

**3. The cheapest encoding is never the adjudicable one.** Six blocks, six
times the fastest rung is `binary` or `onehot`, whose predicates name index bits
and state ordinals. `(!is_01011010)` is a true clause about a real world that
tells a reader nothing, and it is the certificate on the fastest rung of the two
smallest peg blocks. That is the trade this axis found and it is not a
technicality: what the extra predicates were buying was never speed, it was the
certificate.

**4. Padding degrades the certificate as well as the clock.** peg6 `native`
gives eight clauses admitting 30 of 64 states; `dual+3` gives four clauses
admitting 35. The certificate got shorter, weaker and less like a law, for two
extra names for facts the world already had.

### The failure shape axis A never reached

The item asked for the shape of each failure: *timeout / generalisation failure
/ certificate not recheckable*. Axis A only ever produced the first.

* **"Generalisation failure" does not exist in this engine and is not
  tabulated.** `pdr.generalise` iterates a finite sorted literal set and always
  returns a clause; worst case it drops nothing. It cannot fail, only fail to
  help — a continuous quantity, carried as `literal_saturation` (mean clause
  width ÷ predicate count). A category would have hidden it.
* **"Certificate not recheckable" is real, and axis B is where it appears.**
  Fourteen of the twenty-six rungs have no form the independent rechecker can
  read. The `dual` and `native` rungs do: `free_pos3` is not a new fact, it is
  `!pos3` under a second name, so `reencode.desugar` rewrites the clause set
  into the world's own vocabulary literal for literal and hands it to `recheck/`,
  which shares no code with the engine — **all twelve peg `native`/`dual` rungs
  come back ACCEPT with both state counts agreeing**. The eight `binary` and
  `onehot` rungs do not, and read `n/a — no native form`. They are never scored
  as a pass and never counted as a defect. The six worldgen rungs read `n/a — no
  worldgen transcriber`, for the reason axis C gives: nobody has written a
  second, independent transcription of worldgen's mechanisms, and a rechecker
  fed by the same adapter would only agree with itself.

---

## Axis C — mechanism composition at held-fixed size

`runs/20260728T203711Z-E8-ic3-bounds/axis_compose.json`. Six worldgen worlds;
`t1-tokens-lock` and `t2-cycler-lock` are the matched control — same 128 states,
same 19 predicates, one family against two.

<!-- table:compose begin -->
| world | fam | \|S\| | vars | bad | verdict | clauses | literals | widest | saturation | frame | blocked | coverage | strengthen | invariant mentions | recheck | wall (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| t1-switch-latch | 1 | 34 | 18 | 1 | invariant | 5 | 10 | 2 | 0.111111 | 6 | 19 | 29/34 | 5.0 | geometry, switch_door | not available | 0.113 |
| t1-tokens-lock | 1 | 128 | 19 | 7 | invariant | 3 | 6 | 2 | 0.105263 | 3 | 4 | 121/128 | 1.0 | geometry, count_lock | not available | 0.104 |
| t2-cycler-lock | 2 | 128 | 19 | 6 | invariant | 2 | 4 | 2 | 0.105263 | 3 | 3 | 122/128 | 1.0 | geometry, count_lock | not available | 0.097 |
| t2-lock-fragile | 2 | 576 | 30 | 21 | invariant | 3 | 6 | 2 | 0.066667 | 4 | 7 | 555/576 | 1.0 | geometry, count_lock | not available | 0.249 |
| t3-cycler-portal-lock | 3 | 432 | 41 | 9 | invariant | 2 | 4 | 2 | 0.04878 | 3 | 5 | 423/432 | 1.0 | geometry, count_lock | not available | 0.173 |
| t3-latch-maze | 3 | 1680 | 42 | 42 | invariant | 3 | 6 | 2 | 0.047619 | 4 | 7 | 1638/1680 | 1.0 | geometry, count_lock | not available | 0.771 |
<!-- table:compose end -->

No boundary: every rung answers in under a second. But read the coverage column
before reading that as "composition is free". The six invariants admit 85–98 per
cent of their state spaces, and **five of the six carry the harness's own
`near_vacuous` flag** against its declared 0.9 threshold — every rung except
`t1-switch-latch`, at 0.853. Axis B measured the reachable sets of the two
matched worlds — 50 and 61 states of 128 — so those two invariants abstract by
2.4× and 2.0×, against 578× on peg12. The honest sentence is not "composition
costs nothing"; it is **"composition costs nothing *for invariants this
weak*"**, and the ladder does not contain a rung where composition is made to
bite.

The matched pair's timings are both around 0.1 s, which is process-startup
territory; the artefact flags the comparison `machine_dependent` and no ratio
taken from it should be reported to two figures.

---

## The paper sentence

`Theoria.md:205`, the fallback-invariant row of the 1.10(b) engine table:

> 兜底归纳不变量 | **IC3/PDR** | 产出恰是 Lean 要的归纳不变量;**LP/零空间够不着的形状由它兜**

Theoria's own constraint 6 sets the bar for a claim of this shape: *全称断言必须
带证明;裸 UNSAT 禁止*. Split the sentence in two and the two halves land very
differently.

### The LP half: now evidence, and stronger than E8 asked for

`runs/20260729T120000Z-E8-ic3-scale/lp_reach.json`. `lp_potential` was run on
ten unsolvable peg rungs, n = 4…13, each confirmed unsolvable twice
independently.

**LP returns a certificate on none of them.** Ten of ten infeasible, and
infeasible provably rather than by solver report: summing the two opposite jump
rows over each triple forces every interior weight non-negative, hence
Σ w[i≥2] ≥ 0, while the goal row demands Σ w[i≥2] ≤ −margin < 0. The artefact
machine-checks that both rows are in the LP the engine actually builds. Same
verdict at `bound` = 10, 100 and 10000, and with the box constraint deleted;
positive controls (`1110→0100`, `11011→01000`) confirm the harness does return
certificates when they exist.

So on all six rungs of axis A that answered, IC3 is certifying something no
linear pagoda can. That is a line, not a point, and it is the claim D-014
asserted at one configuration generalised to six.

### The null-space half: not supported

The GF(2) conservation laws of the same family — `c[i]+c[i+1]+c[i+2] = 0 mod 2`
— separate the initial state from the goal on **seven of the ten rungs**
(n = 4, 6, 7, 9, 10, 12, 13), missing only n ≡ 2 (mod 3). That is five of axis
A's six. **n=8 is the only rung on the whole ladder where IC3 is the only one of
the three methods that gets there.**

And the sharpest form of it: at n=4 the GF(2) global law renders as
*positions 1 and 2 always agree* — the M9 invariant, the anchor `check_anchor`
pins the whole ladder to, character for character. The point E8 was built to
extend into a line is one linear elimination away.

Two qualifications, both of which matter and neither of which rescues the
sentence:

* This is the *method*, not the engine as shipped. `zero_space.analyse` consumes
  a trajectory, takes no goal and returns no unreachability verdict, and on this
  family a trajectory is at most n/2 states long. The result above comes from
  handing its GF(2) core the move geometries' difference vectors instead. So
  the honest reading is that `zero_space` **as built** does not reach these and
  **could**, which is a finding about `zero_space` rather than an exoneration of
  the sentence.
* The LP result is about *linear* pagodas only. A quadratic or state-dependent
  potential is a different question that nothing here touches.

### What may be written

Supported by the artefacts:

> On unsolvable peg-1d configurations from |S| = 16 to |S| = 8192, `lp_potential`
> is provably infeasible at every rung and `ic3_pdr` returns an inductive
> invariant at every rung, independently rechecked at all six. The invariant's
> explanatory content falls as the state space grows — from excluding half the
> space at |S| = 16 to five per cent at |S| = 8192 — and at |S| = 16384 the
> engine exceeds a 300-second budget. At a state space held fixed, its cost
> varies by up to 35× with the choice of boolean encoding alone.

Not supported, and should not be written:

* "the shapes **LP and the null space** cannot reach" — a GF(2) elimination
  reaches five of the six.
* "IC3 covers what LP cannot" **without** the encoding qualification: which
  encoding the world is written in moves the cost by more than an order of
  magnitude, and the cheapest one produces a certificate nobody can adjudicate.
* anything about IC3 on *hard* instances. This ladder's instances are 2 to 7
  states deep.

---

## Gaps, stated

1. **The ladder scales |S|, not difficulty.** Reachable sets are 2–7 states. A
   second family whose reachable set grows with the board is the missing
   experiment, and nothing here substitutes for it.
2. **Axis C's rungs are too easy to bite.** Every world answers in under a
   second with a near-vacuous invariant. A composition ladder needs a rung where
   composition costs something; `t2-lock-fragile` is documented in `worldgen` as
   sitting outside the current engine vocabulary and is the obvious candidate.
3. **No worldgen rung has an independent recheck.** Fourteen of twenty-six axis
   B rungs and all six axis C rungs read `not available`. Eight of those
   fourteen are a real boundary — a state-index certificate has no world form,
   and that is the finding rather than a gap. The other six are a missing
   transcriber, which is work someone could do.
4. **The `binary`/`onehot` invariants are unaudited by anything but the engine's
   own checker.** They re-verify (`ic3bounds.verify` re-runs `check.verify` on
   every published clause set) but no second implementation has seen them.
5. **`tautologies_dropped` is structurally zero** for this engine's output, for
   reasons `reencode.desugar`'s docstring sets out. The column is a guard
   against a different producer, not a measurement, and its zeroes are evidence
   of nothing.
6. **`ENGINE_TABLE.md`'s `ic3_pdr` row is now stale, and could not be fixed
   from here.** It says "no state-space ladder, no predicate-count ladder, no
   timeout, no failure-shape census" and names E8 as the open item; all four now
   exist. Neither that file nor its generator `tools/engine_table.py` is present
   at this branch's base commit — both landed on `master` afterwards — so the
   correction has to be made after this merges, by adding probes over
   `axis_predicates.json` and `lp_reach.json` in the generator's own `FACTS`
   style rather than by editing the generated file.
7. **One machine, one afternoon.** Every wall clock is this machine's. The
   spreads in axis B survive that (an ordering that reverses under 12–35× is not
   noise); the absolute boundary at n=14 does not.

---

## Reproducing and checking

```bash
cd engine-rig

# the three axes (axis A ~15 min, axis B ~8 min, axis C ~1 min)
python -m ic3bounds --out runs/<id> --axis size
python -m ic3bounds --out runs/<id> --axis predicates
python -m ic3bounds --out runs/<id> --axis compose

# re-check the artefacts WITHOUT re-running the search: every published
# invariant is handed back to the independent checker, every derived column is
# recomputed, timings are checked for presence and ordering only
python -m ic3bounds.verify runs/20260728T203711Z-E8-ic3-bounds \
                           runs/20260729T120000Z-E8-ic3-scale

# fail if a table in this file is no longer what the artefacts render
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
