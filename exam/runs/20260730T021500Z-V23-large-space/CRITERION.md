# What makes an item class (ii), and what class (ii) is allowed to claim

V6-V23, RES-3. Work item 1 of the ticket. Numbers cited here are measured in
this run's `growth_curve.json`, `enumeration_probe.json` and
`repro_duplicate_switch.json`; nothing below is asserted from reading.

## The four candidate criteria, ranked

Theoria.md:259 splits verdict items three ways; class (ii) is "large space
unsolvable — exhaustive search is not feasible, only invariant reasoning can
answer", and the design document calls it "our home ground". A criterion has to
say what earns that label. Four were available.

**(a) reachable-state count over a threshold.** Rejected as a standalone.
`LARGE_SPACE_THRESHOLD = 10**12` (verdict.py:88) has no DECISIONS entry anywhere
in the repo — it is a number that arrived without an argument. Worse, a threshold
is only as good as the count it is applied to, and the count on the class (ii)
path was itself never measured. Threshold over an asserted quantity is a
tautology dressed as a gate.

**(b) our own enumerator truncating at its cap.** Admissible, but only in one
direction and only if it is actually run. It is circular as evidence *about the
level* — we chose the enumerator, and a weaker enumerator would "prove" more
levels large. It is not circular as evidence about *parity with class (i)*:
`_small_space` defines `naive_enumeration_feasible: True` by exactly this
enumerator terminating under exactly this cap, so the same enumerator failing to
terminate is the honest complement of the claim class (i) already makes. That is the only
use it is put to here.

**(c) a search-free constructive lower bound on distinct reachable states.**
The load-bearing half. `subset_lower_bound` (verdict.py:379) exhibits 2^m
distinct reachable states by construction — dip into any subset of m
independently-latching switches and return, and each of the 2^m masks is a
distinct reachable state. This is a *proof*, not a resource observation. It says
nothing about whether anything timed out, so it is untouched by D-024.

**(d) measured failure of real complete solvers at declared budgets.** Rejected,
and for a reason stronger than the one the ticket anticipated. The ticket warned
that engine-rig's D-024 forbids reading a timeout as a verdict, and it does:
"跑不完不等于不可解", or in this repo's own words, *a proof and a shrug must not
share a return value* (engine-rig/DECISIONS.md:779-781). But (d) fails here
before that objection is even reached. On these boards the strong solvers do not
time out — **they win in milliseconds**, because the 120 switches are monotone
and gate no geometry, which is precisely the structure every standard technique
eliminates for free. Adopting (d) would not merely be inadmissible; it would be
*false*.

## The ruling: (c) ∧ (b), and the claim narrows to match

An item is class (ii) when **both** hold, and both are recorded as measurements:

1. **(c)** a constructive lower bound of 2^m distinct reachable states, with its
   premises checked *at the point of claim* — that the m dips lie on one
   switch-free hazard-free lane (D-EX-021) and that they move m *independent*
   latch bits (D-EX-028, this run). A bound whose premises are checked three
   call frames later is not a bound; see below.
2. **(b)** the reference enumerator, the one whose termination *defines*
   `naive_enumeration_feasible: True` for class (i), measured to truncate at the
   shipped cap on this level. Measured, not assumed.

Condition 2 was previously not merely unmeasured but **counterfactually
recorded**: `_large_space` hardcoded `"truncated": False`, which is literally
true only because no enumeration was ever attempted, and reads as though one ran
and came back clean.

## What class (ii) may NOT claim, and this is the substantive change

`"exhaustive_feasible": False` is **not supportable and is withdrawn.**

The field asserts that no exhaustive method is feasible on this board. That is
false, and `crux_quotient_settles.json` in this run measures by how much. Every
shipped class (ii) item is settled by an exhaustive computation over a graph of
at most 600 nodes, in at most 5 milliseconds:

| item | claimed lower bound | what settles it | graph nodes | seconds |
|---|---|---|---|---|
| ii1 | 1.33e36 | components of `relaxed_edges`; start and goal separate | 300 | 0.0010 |
| ii2 | 1.33e36 | the same pass with the cut cell (4,2) deleted | 300 | 0.0001 |
| ii3 | 1.15e18 | relaxed distance 199 against a budget of 150 | 600 | 0.0016 |
| ii4 | 3.32e35 | surviving column deltas are {0,0,+1}; goal is left of start | — | 0.0000 |

The four mechanisms are *different*, which matters: an earlier draft of the
probe assumed all four fell to the same components pass and the measurement
refuted that for three of them. In particular `relaxed_edges` deliberately
ignores the wrapper's `observation_loss`, so on ii2 the plain pass leaves start
and goal in one component and only the severed graph separates them.

An item whose own answer key is an exhaustive walk of a 300-node graph cannot
also claim that exhaustive walks are infeasible on it.

The quotient's disclaimer at verdict.py:789-796 warns that it can report the
goal *reachable* when the level is unsolvable, and D-EX-022 withdrew the number
from `search_credible` for that reason. That warning is correct and it is also
**one-sided in the direction that matters here**: the quotient is an
over-approximation, so it can produce false *solvable*, never false
*unsolvable*. An over-approximation that says "unreachable" is a sound
unsolvability proof. D-EX-022 read the one-sidedness as a reason to distrust the
number; for the refutation direction it was the alarm bell that the barrier is
apparent rather than real.

What is supportable is the narrower, checkable statement, and it is what the
record now carries:

> `naive_enumeration_feasible: False` — forward enumeration over the full
> (cart, button, latch mask) state, the method class (i) is graded on, cannot
> terminate here. Measured. The board is nonetheless settled quickly by an
> invariant, a quotient, or a relaxation, and the item is scored on choosing
> one.

So class (ii) does not measure "only invariant reasoning can answer this". It
measures **method selection under an apparent search barrier**: the examinee who
reaches for the class (i) method cannot finish; the examinee who reaches for a
partition, a cut set or a budget argument finishes at once. That is a weaker
claim than the design document's, and it is the one the artefacts support. It is
also the more useful claim — it is falsifiable by a single counterexample
examinee, whereas "only invariant reasoning can answer this" is a universal over
all methods that no experiment could ever establish.

## Why the bound must defend its own premise where it is claimed

Every guard on class (ii) truth used to fire *after* the record was written.
`Level.wellformed_problems()` catches a malformed level only from `_self_check`
at verdict.py:1278, while the seven `_large_space` calls sit at 1010, 1030,
1055, 1081, 1212, 1241 and 1267 — all above it. Measured consequence: a
`comb_open` whose switch list repeats one cell 60 times produced a lower bound
of 2^60 = 1.15e18 on a board with **359** reachable states, an overstatement of
3.2e15, and `_large_space` stamped the record before anything objected.
`build()` did abort before returning a paper, so nothing false shipped from
`build()` — but the exposure was real for every direct caller, and a bound that
survives only because a distant caller happens to check is not a bound.
Fixed in `subset_lower_bound` itself (D-EX-028).

## Work item 2: the instances, and what they license

The bound is arithmetic and no class (ii) board has ever had its states counted.
What is affordable is enumerating the *same families* at small k and checking the
growth law. Measured to completion, with nothing fitted
(`growth_curve.json`, and pinned by
`test_the_comb_families_grow_exactly_as_the_bound_extrapolates`):

* gantry, lattice and the unbudgeted spindle: **measured = 2k·4^k = 2k·2^m**,
  exactly, at every k, with m = 2k.
* orchard: **measured = (2·4^k − 8)/3 = (8/3)(2^m − 1)**, exactly, with
  **m = 2(k−1)** — with LEFT forbidden the two column-1 alcoves sit behind the
  start and are not dippable. That is why shipped ii4 reports m=118 and not 120,
  and mistaking it for 2k makes the ratio look like drift instead of convergence
  to 8/3.

So the bound is sound at every rung measured, and loose by a factor of 2k
(growing) or 8/3 (constant). The exponent is verified over 5.77 orders of
magnitude of measured state count.

**What this licenses:** the *exponent*, not the shipped number. Extrapolating
2^m to k=60 rests on the closed form being exact wherever it can be checked, not
on any count approaching k=60 — the largest measured count is 4.7e6 against
ii1's 1.33e36, a gap of ~29 orders no enumeration crosses.

**What it does not license, and this is a correction to an earlier draft of this
run:** it does **not** cover ii3. ii3's m=60 comes from `step_limit=150`, not
from its 400 switches, so the unbudgeted closed form must not be read onto it.
The budget probe shows the bound stays sound at every budget measured, but no
closed form for a budgeted board is established here.

Two further corrections to this run's own earlier notes, recorded because they
changed decisions: enumerating k=1..9 costs **~128 s**, not the 2.3 s first
noted (2.6 s is k≤6) — which is why the shipped ladder stops at 6. And k=6 is
not merely the cheap choice: gantry at k=7 is 229,376 states, past the shipped
cap, so 6 is the largest rung that can be enumerated to completion under
`MAX_ENUMERATION` at all.

## Work item 3: the invariant path exists; no *engine* can walk it

The ticket asked whether `lp_potential` can produce a certificate for these
instances. It cannot, and the reason is worse than the expected one.

The expected obstacle — that `solve` needs a materialised edge list, so it
cannot run on a space too large to enumerate — is real: measured scaling is ×4.0
in states per corridor cell, and corridor 60 implies ~6e36 edges. The input
cannot be constructed, so `solve` is never entered.

But there is a prior obstacle that no amount of memory would fix. `lp_potential`
is a peg-solitaire engine: its move algebra is `row[dst]+=1; row[src]-=1;
row[over]-=1`, so **every expressible transition has coefficient sum −1**,
verified exhaustively over all role assignments at n_pos=5. An A2 cart move has
sum 0, or +1 when it latches. No assignment expresses an A2 transition at any
size. There is no A2→`lp_potential` adapter in the repo, and the adapter a
reader would naturally write **fails silently**: encoding a comb level and
running it anyway returns `certified` at every size, including at corridor 4
where the level is *solvable* — a clean unreachability proof for a reachable
goal, with all four of the engine's self-checks agreeing because all four read
the same wrong move list.

Surveying the rest: `ic3_pdr` enumerates states up front by its own docstring;
`fd_adapter` and `probe_frontier` need grounded PDDL and there is no
A2/worldgen→PDDL compiler anywhere in the repo; `zero_space` re-checks only
against the sample it was given; `cegis_miner` and `mdl_segmenter` mine
candidates, never verdicts. **No shipped engine can find a certificate for a
class (ii) level at shipped size.**

What *does* walk the invariant path is `exam/grading/rubrics_verdict.
check_certificate` — purpose-built for this world, machine-checking each
reference certificate in ≤3.1 ms — with zero connection to `engine-rig`. So the
honest form of the framework's claim is: the levels really are past naive
enumeration, and a cheap machine-checkable invariant path really does exist, but
it is the exam's own checker and not an engine. "Engines propose, the LLM
adjudicates" has no engine on this path today.

## Work item 4: the negative controls

A classifier tried only on true positives has not been tried. Three controls,
all built from shipped constructors and shipped operators:

1. **Looks large, enumerates.** 400 switches on a 200-cell corridor — more of
   both than any shipped class (ii) item — with a step budget of 10. The whole
   reachable set is **6,480 states**, enumerated to completion in 0.01 s, and
   `_large_space` refuses it. The refusal comes from the constructive bound
   (m=4, 2^4=16), not from anything about the board's size.
2. **Truncates, and is still refused.** The same board at a budget of 20 passes
   the 200,000 cap and truncates *exactly as ii1..ii4 do*, yet its bound is
   2^8 = 256 and it is refused. This is the conjunctive criterion in executable
   form: if truncation alone earned the label, a board 30 orders of magnitude
   smaller than ii1 would ship as class (ii) on the strength of a cap we chose
   ourselves. Criterion (b) cannot stand alone, and now something fails if it
   ever does.
3. **Inflated bound, real board.** The duplicate-switch case (above): 2^60
   claimed against 359 real states, now refused at the point of claim.

Controls 1 and 2 are the ticket's item 4 proper. Control 3 is a different
failure — a sound-looking bound on a malformed level — and neither substitutes
for the other.

## What this does not close

The sealed drill's class (ii) gap is **structural and stays open**, and that is
now a sharper statement than the ticket's. `GridWorld.reachable(limit=200_000)`
(worldgen/core/world.py:259) **raises** above the limit, so worldgen cannot
build a world with a state space exhaustive search cannot reach — the catalogue
does not merely happen to lack one. `DRILL.json`'s
`classes_absent: ["large_unsolvable"]` therefore cannot be closed from inside
`exam`; it needs a worldgen change, which is outside this ticket's territory and
is filed rather than done.
