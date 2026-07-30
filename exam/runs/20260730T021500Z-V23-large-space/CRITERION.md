# What makes an item class (ii), and what class (ii) is allowed to claim

V6-V23, RES-3. Work item 1 of the ticket.

**Provenance, stated completely because the earlier version of this paragraph was
not.** It named three artefacts — `growth_curve.json`, `enumeration_probe.json`,
`repro_duplicate_switch.json` — and claimed the numbers below are measured in
them. That was false by omission: the crux table, the work-item-3 findings and
the certificate timings come from four others, and three more artefacts in this
run were cited by neither this document nor `RUN_STATE.md`. A provenance claim
that lists three of eight is the same defect this ticket exists to fix — an
assertion nobody can check — so it is replaced by the full map:

| section | artefact |
|---|---|
| the ruling, criterion (b) | `enumeration_probe.json` — **all seven records it speaks for, and holding on all seven.** F5-14 said four of seven: `deterministic.items` held nine rows, i1-i5 and ii1-ii4, and the three `solvable_hard` records that also carry `naive_enumeration_feasible: False` were absent, their (b) evidence being the test alone. The probe was widened rather than the map annotated — it now calls `V.build()` and filters on `state_space.naive_enumeration_feasible is False`, so the row set cannot fall behind the builder, and iii6 / iii7 / iii8 are measured: all three truncate at `MAX_ENUMERATION` with no solution found inside the cap. That last conjunct is the load-bearing one for them, because they *are* solvable — a plan found inside the cap would have meant the naive method works there and the record's refusal was unfounded. `coverage.superseded_coverage` records what this row used to say. **F5-13 is untouched and still stands**: the shipped record itself still carries `enumeration_attempted: False` / `truncated: None`, so "both conditions are recorded as measurements" remains false *of the record*, even though (b) is now measured in two independent places |
| the crux table (what class (ii) may not claim) | `crux_quotient_settles.json` |
| the duplicate-switch overstatement | `repro_duplicate_switch.json` |
| work item 2, the growth law | `growth_curve.json` |
| work item 2, the budget rungs | `enumeration_sweep.json` (machine-dependent by construction — see below) |
| work item 3, `lp_potential` | `probe_lp_interface.json`, `probe_lp_soundness.json`, `invariant_path_probe.md` |
| the reference answer keys and certificate timings | `probe_answer_key.json` |
| the attacks on this run's own cost model | `adversarial/attack_barbell.json`, `adversarial/attack_straddle.json` |
| work item 4, the negative controls | **not an artefact** — `exam/tests/test_verdict.py` (the controls are tests, and their numbers are assertions in them) |
| the round-3 adversarial review | `adversarial/review-round3.md` |

Two caveats on that map, both stated because the earlier version of this
paragraph implied neither.

**Not every number below comes from an artefact.** Two other kinds appear, and
each is labelled where it occurs rather than blended into the measured ones:
*extrapolations* (the corridor-60 edge count, and 2^m at k=60 — carried from a
measured factor, sound only as far as the closed form is exact), and *wall-clock
observations recorded in `RUN_STATE.md` prose with no committed artefact* (the
enumeration reruns, the certificate-checking **reruns**, the 758-of-1024
latch-mask count, and the reviewer's 1,034-rung sweep over interior `start_col`).
Under this repo's own precedence rule — JSON artefacts beat prose
reports — that second kind is the weakest evidence in the document, and none of
it is gated on. It is named rather than removed because the reruns' value is the
*spread* they establish, not any single figure.

Two round-five corrections to that list. It said "the certificate-checking
times", which was wrong in a way round four then over-corrected in the opposite
direction: the four committed `check_certificate_seconds` values *are* in
`probe_answer_key.json`, exactly as the map says, and it is only the **reruns** of
that measurement that are prose-only. And the 1,034-rung sweep is new to this
list — see the round-five paragraph below, and work item 4.

**All timings are machine-dependent.** No claim here rests on one, and
`enumeration_sweep.json` in particular does not reproduce rung-for-rung by
construction (see the end of work item 4).

**Round four: the map above was itself incomplete, which is the third time this
document has had to widen a completeness claim.** A reviewer found that work item
4's five numbers (`6,480 states`, `0.01 s`, `m=4`, `2^4=16`, `2^8=256`) had no row
at all — they come from `exam/tests/test_verdict.py`, so the evidence is a passing
assertion rather than an emitted artefact, which is a legitimate kind of evidence
but a different one, and `0.01 s` is asserted nowhere even there (it appears only
in a test docstring). The reviewer's own 1,034 rungs likewise had no artefact and
appeared in no exception list. Work item 4's numbers are now row 9 of the map. The
lesson is not that the map
was sloppy — it is that **a completeness claim over a document that is still being
edited is a claim with a short shelf life**, and the only durable form of it is
the per-number question: which committed file emits this, and can I open it?

**Round five: that paragraph said "Both are now rows", and one of the two was
not** — which makes a round-four correction to a completeness claim itself
incomplete, in the paragraph that concludes such claims have a short shelf life.
At the commit round four's correction shipped in, `grep -n "1,034"` over this
document returned two lines: this paragraph, and the sweep
paragraph in work item 4. The map has ten rows and none of them is the sweep, and
it was in no exception list either. It cannot become a map row, because nothing
emits it: no file anywhere in this run directory contains the figure, and the only
record of the sweep is one paragraph of `RUN_STATE.md`. So it is now in the
exception list above, which is where a prose-only number belongs — and that is the
correction, not a row. Round five also found the criterion-(b) map row overstated
(it covers four of seven records; the row now says so), which is the fourth
widening of a completeness claim in this document and the second in the map.

## The four candidate criteria, ranked

Theoria.md:259 splits verdict items three ways; class (ii) is "large space
unsolvable — exhaustive search is not feasible, only invariant reasoning can
answer", and the design document calls it "our home ground". A criterion has to
say what earns that label. Four were available.

**(a) reachable-state count over a threshold.** Rejected as a standalone.
`LARGE_SPACE_THRESHOLD = 10**12` (`verdict.py`, module constant) had no DECISIONS
entry anywhere in the repo when this section was written — a number that arrived
without an argument. Worse, a threshold is only as good as the count it is
applied to, and the count on the class (ii) path was itself never measured.
Threshold over an asserted quantity is a tautology dressed as a gate.

*Amended (D-EX-029).* Rejecting (a) as a standalone was right, but this document
then shipped that same constant as the only gate `_large_space` applies — so it
rejected the criterion it ships. The constant now carries its argument at its
definition: the requirement is only `> MAX_ENUMERATION` (past the cap the naive
enumerator provably cannot terminate, which is the whole claim), 10^12 is that
with ~7 orders of headroom. It is a floor with margin, not a measurement. What
makes the criterion non-tautological is not the threshold; it is the conjunction
with (c), whose count is constructive rather than asserted.

**Corrected in round four, and the corrected result is weaker.** The interval was
first written `(256, 1.15e18]` and described as "robust across ~16 orders". Run
directly — patch `LARGE_SPACE_THRESHOLD`, call `_large_space` on both negative
controls — **both controls are refused at every `T` tested, down to `T = 2`**. The
refusal migrates to the second gate, `lower_bound <= MAX_ENUMERATION`. So `256`
(which is control 2's own bound) is the endpoint you get if gate 1 is the only
refusal, and that derivation predates the gate the same commit added; over
`(256, 200000]` gate 1 is dead code, since any `lb < T <= 200,000` also satisfies
`lb <= 200,000`. The upper endpoint is exact: `2^60` keeps every label, `2^60 + 1`
flips ii3.

What the audit set actually establishes is therefore **not** that the threshold is
robust: it is that these cases **cannot distinguish `10^12` from `2`**, so they do
not constrain the threshold from below at all. "Robust across ~16 orders" was a
property of the audit set masquerading as a property of the constant — a tautology
dressed as a gate, which is the phrase this section uses to reject criterion (a)
in the first place. The honest defence of `10^12` is the argument, not a sweep:
the requirement is `> MAX_ENUMERATION`, and the constant clears it with margin.

One further correction to round three's wording: it said "`_large_space` now
asserts the cap ordering instead of trusting it". It does not, and the code is
right where the prose was wrong. `_large_space` asserts a property of each
*bound* (`lower_bound <= MAX_ENUMERATION` raises), and its own comment says why
that was chosen over an ordering check — "the ordering is not stated anywhere as
a requirement and either constant can be moved by someone who never reads this
function". A summary of a guard should not claim more than the guard.

**Round five: both of the corrections above landed in this document and not in the
file they are about.** As of round five, the comment at `LARGE_SPACE_THRESHOLD`'s
own definition in `exam/papers/verdict.py` still carried the withdrawn sentence —
"any threshold in (256, 1.15e18] labels the same seven records and refuses both
negative controls, so the choice is robust across ~16 orders rather than
knife-edge" — unmarked, in the same paragraph as the `> MAX_ENUMERATION` argument
this section credits it with; and it still said "`_large_space` now asserts the
ordering rather than trusting it", which is the round-three prose the paragraph
above calls wrong, 800 lines above the comment quoted here as the authority
against it. So "the constant now carries its argument at its definition" was true
of what that comment adds and false of what it retains, and a withdrawn claim was
still shipping in tracked source while this document said the opposite about that
source. That comment has since been rewritten at its own definition — it now says
outright that `_large_space` does *not* assert the ordering, and replaces the sweep
sentence with the measurement that refuted it, that both controls are refused at
every threshold tested down to `T = 2` and so cannot distinguish 10^12 from 2
(D-EX-029, D-EX-030). Recorded rather than quietly closed, because the failure mode
is the general one: a correction written into the document that describes a file is
not a correction to the file, and this section had been asserting the opposite
about that file for two rounds. A document should not claim more than the file it
points at, for the same reason a summary should not claim more than the guard.

**(b) our own enumerator truncating at its cap.** Admissible, but only in one
direction and only if it is actually run. It is circular as evidence *about the
level* — we chose the enumerator, and a weaker enumerator would "prove" more
levels large. It is not circular as evidence about *parity with class (i)*:
`_small_space` defines `naive_enumeration_feasible: True` by exactly this
enumerator terminating under exactly this cap, so the same enumerator failing to
terminate is the honest complement of the claim class (i) already makes. That is the only
use it is put to here.

**(c) a search-free constructive lower bound on distinct reachable states.**
The load-bearing half. `subset_lower_bound` (`verdict.py`) exhibits 2^m
distinct reachable states by construction — dip into any subset of m
independently-latching switches and return, and each of the 2^m masks is a
distinct reachable state. This is a *proof*, not a resource observation. It says
nothing about whether anything timed out, so it is untouched by D-024.

**(d) measured failure of real complete solvers at declared budgets.** Rejected,
and for a reason stronger than the one the ticket anticipated. The ticket warned
that engine-rig's D-024 forbids reading a timeout as a verdict, and it does:
"跑不完不等于不可解", or in this repo's own words, *a proof and a shrug must not
share a return value* (`engine-rig/DECISIONS.md:780-781` — which is **D-031**'s
sentence citing D-024 by analogy, not D-024's own; D-024's heading is at line 466,
D-031's at 730. Round three narrowed the range correctly and invented a false
attribution in the same breath, inside the paragraph about anchor discipline. The
Chinese phrasing above is the ticket's paraphrase, not any decision's words).
But (d) fails here
before that objection is even reached. On these boards the strong solvers do not
time out — **they win in milliseconds**, because the 120 switches are monotone
and gate no geometry, which is precisely the structure every standard technique
eliminates for free. Adopting (d) would not merely be inadmissible; it would be
*false*. (**That last claim is argued, not measured, and is labelled here because
round five's per-number sweep did not reach it.** No solver was run on these
boards: no artefact in this run emits a solver time on a class (ii) level, and
work item 3 below establishes that no shipped engine can even construct the input.
What is measured is the *quotient* — the 300- and 600-node graphs of the crux
table — which is why the argument is credible; but "they win in milliseconds" is
an inference from the monotone structure, not an observation, and is the same kind
of claim as the 758-of-1024 count. The same sentence ships in `exam/STATUS.md`
unlabelled.)

## The ruling: (c) ∧ (b), and the claim narrows to match

An item is class (ii) when **both** hold — and they are established differently,
which round five had to force this section to say:

1. **(c)** a constructive lower bound of 2^m distinct reachable states, with its
   premises checked *at the point of claim* — that the m dips lie on one
   switch-free hazard-free lane (D-EX-021) and that they move m *independent*
   latch bits (D-EX-028, this run). A bound whose premises are checked three
   call frames later is not a bound; see below.
2. **(b)** the reference enumerator, the one whose termination *defines*
   `naive_enumeration_feasible: True` for class (i), truncating at the shipped cap
   on this level — derived from (c) in the record, and measured in the suite.

Condition 2 was previously not merely unmeasured but **counterfactually
recorded**: `_large_space` hardcoded `"truncated": False`, which is literally
true only because no enumeration was ever attempted, and reads as though one ran
and came back clean.

**Round five: this section said "both are recorded as measurements", and the
record says the opposite about (b).** Read the seven records in
`exam/artifacts/truth/p15-verdict-a2.truth.json` whose
`state_space.naive_enumeration_feasible` is `false` — m = 120, 60, 118, 120, 120,
120, 120, being the four class (ii) items plus the three `solvable_hard` ones —
and every one carries `enumeration_attempted: false` and `truncated: null`. Nor
does the builder ever test (b): `_large_space` applies exactly two gates,
`lower_bound < LARGE_SPACE_THRESHOLD` and `lower_bound <= MAX_ENUMERATION`, **both
functions of `lower_bound` alone**, so the conjunction the code enforces is
threshold ∧ cap over one quantity, not (c) ∧ (b). In the record (b) is *derived*
from (c), and the record says so outright — `enumeration_refused_because` gives
the derivation and names the test that checks its premise.

So the honest form is: (c) measured at the point of claim; (b) derived there and
measured elsewhere — by `test_class_ii_levels_actually_truncate_the_enumerator`,
which asserts `len(items) == 7` and runs the enumerator at the shipped cap against
all seven, and by `enumeration_probe.json` for four of them. That is a real check
and it is not the same thing as "recorded as a measurement". This is the
criterion-vs-code gap in its surviving form: the earlier record was
*counterfactual* (`"truncated": False`) and is now *honest* (`null` beside
`enumeration_attempted: false`), but the prose describing it did not narrow when
the record did.

## What class (ii) may NOT claim, and this is the substantive change

`"exhaustive_feasible": False` is **not supportable and is withdrawn.**

The field asserts that no exhaustive method is feasible on this board. That is
false, and `crux_quotient_settles.json` in this run measures by how much. Every
shipped class (ii) item is settled by an exhaustive computation over a graph of
**at most 600 nodes** — which is the structural half of the claim, and the half
that reproduces exactly:

| item | claimed lower bound | what settles it | graph nodes | seconds (one run, this machine) |
|---|---|---|---|---|
| ii1 | 1.33e36 | components of `relaxed_edges`; start and goal separate | 300 | 0.0010 |
| ii2 | 1.33e36 | the same pass with the cut cell (4,2) deleted | 300 | 0.0001 |
| ii3 | 1.15e18 | relaxed distance 199 against a budget of 150 | 600 | (not timed — see below) |
| ii4 | 3.32e35 | surviving column deltas are [0, 1]; goal is left of start | — | 0.0000 |

**ii3's row carries no timing on purpose.** The artefact records
`compute_lower_bound: 0.0047`, `enumerate_quotient: 0.0012` and
`settle_via_components: 0.0016` for ii3, and times the budget check — the thing
that actually settles it (`settled_by_budget: true`, `settled_by_partition:
false`) — not at all. Earlier drafts printed the `0.0016` here, which is the
components pass, i.e. the one this document elsewhere takes pains to say did
*not* settle ii3: a number from the right artefact attached to the wrong
mechanism, which is this ticket's own defect shape in a table cell. ii3's largest
committed timing is 0.0047 s, and that is `compute_lower_bound` — not the budget
check either.

**Round five: the "in at most 5 milliseconds" half of the headline is withdrawn,
and this document's opening caveat is the reason.** That caveat says "all timings
are machine-dependent — no claim here rests on one", and this was a claim resting
on one. `crux_quotient_settles.py` is deterministic in everything but
`timing_seconds`: re-running it four times in this worktree left every other field
byte-identical to the committed artefact, and across those four runs ii3's largest
timing came back **0.0048, 0.0049, 0.0047 and 0.0050 s** against the committed
0.0047, while round five's own rerun recorded **0.0051**. The figure straddles the
threshold it was written as, so "at most 5 milliseconds" is false on some reruns of
the same script on the same machine — and substituting a fresher millisecond count
would only move the rot. What survives is the 600 nodes and the four distinct
mechanisms, both structural and both byte-reproducible, plus the order of
magnitude: single-digit milliseconds, measured on this machine, gating nothing.
Round five found the same "at most 5 ms" sentence in three further places —
`RUN_STATE.md`, `exam/STATUS.md`, and inside `verdict.py`'s
`naive_enumeration_feasible` comment, i.e. in tracked source. `RUN_STATE.md` has
since been narrowed to "single-digit milliseconds"; the other two are not this
document's to edit and the correction is owed in each, which is the same
document-corrected-but-not-the-file pattern recorded under criterion (a) above.

The four mechanisms are *different*, which matters: an earlier draft of the
probe assumed all four fell to the same components pass and the measurement
refuted that for three of them. In particular `relaxed_edges` deliberately
ignores the wrapper's `observation_loss`, so on ii2 the plain pass leaves start
and goal in one component and only the severed graph separates them.

An item whose own answer key is an exhaustive walk of a 300-node graph cannot
also claim that exhaustive walks are infeasible on it.

The quotient's disclaimer — the `quotient_note` string `_large_space` writes into
every record — warns that it can report the
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
`Level.wellformed_problems()` catches a malformed level only from `_self_check`,
which `build()` runs *after* assembling every item, while all seven
`_large_space(lvl)` call sites sit above it in the file and earlier in the
run. (Stated as symbols, not line numbers: the line anchors this document
originally carried were measured against the base commit and had rotted ~58
lines by the time `verdict.py` grew in the same commit that cited them, then
~107 after the fixes below — which is board items P21 and P22's standing
finding, that an anchor into a file its own commit edits will rot again. The
seven call sites and `_self_check` are both greppable by name. **Round five found
that this fix had been applied to this document only.** `repro_duplicate_switch.json`
— a committed artefact of this same run, and row 3 of the provenance map above —
was still publishing the pre-fix anchors in its `wellformed_runs_at` field: nine
`verdict.py` line numbers for `_self_check`, `wellformed_problems()` and the seven
`_large_space()` call sites, every one wrong at HEAD, with the same strings
duplicated in `repro_duplicate_switch.py`. The *ordering* claim they carried — that
all seven call sites sit above `_self_check` — held throughout; only the numbers
were wrong, which is why a symbol-anchored statement of the same fact loses
nothing. That pair has since been re-anchored by symbol by its owner. The
generalisable part: de-numbering the prose and leaving the artefacts numbered
fixes the citation a reader checks and not the one a machine publishes.) Measured
consequence: a
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
changed decisions. Enumerating k=1..9 is expensive, not the 2.3 s first noted —
which is part of why the shipped ladder stops at 6. The cost is **not a single
number and this document previously gave one that matched nothing**: it said
"~128 s", while `growth_curve.json`'s `timings_seconds.total_seconds` was
`122.247` in the run committed with it — **for the
whole script, not for k=1..9**. Summing that file's own per-rung timings, the
k≤9 rungs come to ~104.6 s; the balance is orchard's k=10 and k=11 (2.322 s and
13.484 s) plus the budget probe. Attributing 122.247 to "enumerating k=1..9"
over-attributes by ~16 s of work at two rungs the phrase excludes.

The only figure here with a committed artefact behind it is that 122.247 s. A
reviewer's rerun on the same machine gave 153.24 s, and the k≤6 cost — written
"2.6 s" — has no committed artefact **for the same quantity**: the per-rung timings for k≤6 sum to
**0.629 s**, while the 2.918 s rerun is whole-script wall-clock including the
budget probe — a different measurement, between four and five times the figure for
the thing named, and round three did not distinguish them. **Those
rerun numbers are recorded in `RUN_STATE.md` prose and nowhere else**, which under
this repo's own precedence rule (JSON artefacts beat prose reports) makes them
weaker evidence than the 122.247, not stronger. Naming them is still worth it,
because what they establish is not a value but a *spread*: the same computation on
the same machine varies by ~25%, so no single wall-clock number is a property of
the artefact, and correcting "128" to "122.247" while presenting it as the cost
would repeat the original error with a better-sourced number. Read the cost as
"about two minutes, machine-dependent"; nothing gates on it.

**Round five: 122.247 is one run's value too, and every timing quoted in this
paragraph is read from `growth_curve.json`'s `timings_seconds`, not from a
property of the script.** A regeneration of the same script in this worktree
recorded `total_seconds: 143.786`, with the k≤9 per-rung sum at 122.185 and the
k≤6 sum at 0.670 — so three samples of the same computation on this machine are
122.247, 143.786 and 153.24, and the ~25% spread above is now measured over three
rather than argued from two. Any of these values quoted as *the* cost will rot on
the next regeneration; read them as the runs they came from. What does not move is
the **decomposition**, which is the only load-bearing claim here: in both artefact
runs `total_seconds` equals the k≤9 per-rung sum plus orchard's k=10 and k=11 plus
the budget probe, to within 0.04 s. That is what makes "122.247 s to enumerate
k=1..9" wrong regardless of the numbers — it names a quantity the field does not
measure.

And k=6 is not merely the cheap choice: gantry at k=7 is 229,376 states, past the
shipped cap, so 6 is the largest rung at which **all four families** complete under
`MAX_ENUMERATION`.

**Round five corrected that last sentence, which read "the largest rung that can be
enumerated to completion under `MAX_ENUMERATION` at all" and was refuted by the
artefact quoted beside it.** orchard's rows in `growth_curve.json` are 10,920 at
k=7, 43,688 at k=8 and **174,760 at k=9** — all three under the 200,000 cap; k=10
at 699,048 is the first that passes it. gantry, lattice and spindle share 229,376
at k=7 and do pass it. So the cap stops three families at 6 and orchard at 9, and
"at all" overstated the ladder's reason by three rungs. (Those rungs were
nonetheless enumerated in this run: `growth_curve.json`'s own `enumeration_cap` is
`1000000000` and it records 200,000 separately as `marker_cap_for_reference`. The
shipped cap bounds what a class (i) item may be graded on, not what this probe was
allowed to spend — which is why the ladder's stopping point is a choice about
parity with class (i), not a wall.)

## Work item 3: the invariant path exists; no *engine* can walk it

The ticket asked whether `lp_potential` can produce a certificate for these
instances. It cannot, and the reason is worse than the expected one.

The expected obstacle — that `solve` needs a materialised edge list, so it
cannot run on a space too large to enumerate — is real: measured scaling is ×4.0
in states per corridor cell, and carrying that measured factor to corridor 60
implies **~6e36 edges**. The arithmetic, from `probe_lp_interface.json`'s
`E_comb`, whose last rung is corridor 10 at 2,796,200 reachable states and
4,893,348 edges: `4,893,348 × 4^50 = 6.20e36`.

(Round three of this document said `~4e36` and called the `~6e36` it replaced
"stated without showing the arithmetic". Both halves of that were wrong. `~4e36`
is the extrapolated *state* count — `2,796,200 × 4^50 = 3.55e36` — wearing the
word "edges", off by the edges-to-states ratio of the one rung the arithmetic
uses, `4,893,348 / 2,796,200 = 1.7499993` at corridor 10; and the figure it
displaced was one multiplication from a committed column. `exam/DECISIONS.md`
never stopped saying `~6e36` and was right
throughout, so for one commit the run document and the decision record disagreed,
with the decision record holding the correct value. The ×4.0 is measured, the
extrapolation to 60 is an assertion, and they are still two different kinds of
claim — but that was never a licence to get the assertion's arithmetic wrong.)

The input cannot be constructed, so `solve` is never entered.

**Round five: the parenthetical above first named that factor "`edges/states =
1.7500`, which the same artefact measures at every rung", and that was this
document's own rounding read back as a measurement.** `probe_lp_interface.json` has
no `edges/states` field at all — the ratio is derived — and derived across its nine
`E_comb` rows it *rises* toward 7/4 from below: 1.7000 at corridor 2, then 1.7381,
1.7471, 1.7493, 1.7498, 1.7499542, 1.7499886, 1.7499971, and 1.7499993 at corridor
10. It is 1.7500 to four decimal places at the last four rungs, 1.70 at the first,
and exactly 1.75 at none — so the correction is that the arithmetic uses one rung's
ratio, not a constant the artefact measures. "At every rung", in the passage whose
whole subject is distinguishing measured from asserted, is that passage's own
defect.

But there is a prior obstacle that no amount of memory would fix. `lp_potential`
is a peg-solitaire engine: its move algebra is `row[dst]+=1; row[src]-=1;
row[over]-=1`, so **every expressible transition has coefficient sum −1**.
`probe_lp_interface.json`'s `D_coefficient_sums` is the distinct-value set
`[-1.0]`, computed over the engine's own moves.

Both sides of that comparison are now enumerated, and the route here is worth
recording because two rounds of correction got it wrong in opposite directions.

**The exhaustiveness was sourced all along; round four's withdrawal of it is
itself withdrawn (round five).** Earlier drafts said this was "verified
exhaustively over all role assignments at **n_pos=5**". Round four could find no
`5` in the artefact — whose `n_pos` values run 10, 15 … 50 — and withdrew the
exhaustiveness as unsourced. But `n_pos` is probe B and E's rung parameter, and the
exhaustive loop is in probe D over the LP row width `n`, which is `n = 5` in the
committed generator: three nested `range(n)` loops over `(src, over, dst)`, `5^3` =
125 role assignments, every one of which lands on the same coefficient sum, −1.
Round four
conflated two different `n`s and withdrew a true claim; only the *label* "n_pos=5"
was wrong. Neither round would have had to read the generator if the artefact had
carried the loop's own parameters, so it now does: `D_role_assignments` is
`{"n": 5, "assignments": 125}`, beside the `D_coefficient_sums` of `[-1.0]` that
loop produces.

**The A2 side was a hand-written literal, and the fix took two attempts (round
five).** A cart move has coefficient sum 0, or +1 when it latches — and that was
once written into `D_verdict` as the Python literals `a2_plain_move: 0` and
`a2_latching_move: 1`, printed as if measured while only the `lp_potential` side
was computed: one half of a two-sided comparison, both halves in one voice. The
first replacement measured it by enumerating the *shipped* 20-corridor comb — 40
latch bits, ~4.4e13 states — an enumeration that cannot terminate, over a board of
exactly the size this ticket's thesis says cannot be enumerated, and the artefact
was left carrying the literals' values from a run that never happened. The second
replacement is the one that shipped: the A2 side is enumerated over five small
levels chosen to cover every branch of `Level.step`, under a bound that raises
rather than truncating. `D_verdict` now records it as measurements —
`a2_coefficient_sum_by_kind` and `a2_transitions_by_kind` (a plain move and a
blocked transition sum to 0, a latching move and a button press to +1),
`a2_coefficient_sums_measured` of `[0, 1]` over `a2_transitions_enumerated` =
51,164 transitions across `a2_states_enumerated` = 12,791 states,
`a2_step_branches_covered` listing all six branches, `a2_enumeration_bound` =
200,000, and `a2_shipped_level_enumerated: false` — the last field being the honest
part: the shipped size was *not* enumerated, and the step from these levels to
every size is the monotonicity argument, not a sweep. Against `lp_potential`'s
invariant −1 — which `engine-rig`'s own `potential.py` independently confirms, one
LP row per `Move` built as `row[move.dst] += 1.0`, `row[move.src] -= 1.0`,
`row[move.over] -= 1.0` — no measured A2 sum matches, so the conclusion stands and
is now sourced on both sides: no assignment expresses an A2 transition at any size.

There is no A2→`lp_potential` adapter in the repo, and the adapter a
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
reference certificate in **single-digit milliseconds**, which
`probe_answer_key.json` records per item as `check_certificate_seconds`: 0.00306,
0.00149, 0.00075, 1e-05. Those four are sourced, and the order of magnitude is
what they establish — with zero connection to `engine-rig`.

(**This one number has now been written three ways across three rounds, and round
five settles which of them may be a headline.** Round three called `≤3.1 ms` "one
wall-clock observation restated as a bound" and replaced it with "single-digit
milliseconds"; round four called that wrong twice and restored `≤3.1 ms`. Round
four was right that the four values *are* in `probe_answer_key.json` — so this
document's caveat listing "the certificate-checking times" among the numbers with
no committed artefact did contradict its own provenance map, and that ambiguity is
fixed at the caveat, which now says *reruns*. Where round four went wrong is the
word "bound". 3.06 ms is the **maximum over those four rows**, and that is all a
set of four samples can be; it is not a bound on the operation, and round five
measured the operation exceeding it. Re-running `check_certificate` over the same
four committed certificates in four fresh processes, in the measurement order
`probe_answer_key.py` uses, put the ii3 certificate at **0.00348, 0.00360, 0.00369
and 0.00364 s** — every one past 3.1 ms — and a regeneration of
`probe_answer_key.json` in this worktree recorded **0.00313** for the same field.
The prose-only 3.66 ms rerun that round four set aside is therefore reproduced
rather than anomalous, and the counter-observation it represents was the thing to
follow: the repo's precedence rule ranks evidence *for* a claim and is not a
licence to discard evidence *against* one. So the headline reverts to the order of
magnitude, with the four rows printed beside it, which is the form
`exam/DECISIONS.md` says survives a change of machine — this document and the
decision record now say the same thing about the same number, which is the point.
`≤3.1 ms` remains true and recheckable as a *maximum over `probe_answer_key.json`'s
four rows*, and nothing here or anywhere gates on it.) So the
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

### The attacks that came back clean, and why that was not reassurance

This run shipped two adversarial probes against its own cost model — 147 KB,
`adversarial/attack_barbell.json` and `adversarial/attack_straddle.json`, 347
sweep rows between them — and an independent reviewer swept 1,034 more rungs over
interior `start_col` with binding budgets. **That 1,034 has no artefact**: nothing
in this run directory emits it and the only record is a paragraph of
`RUN_STATE.md`, so it is one of the prose-only figures in the exception list at the
top (round five added it there, and nothing below rests on it). Both probes'
summary field reads
`unsound_rows: 0`, and round three quoted that as "all of them returned zero
unsound rows".

**That is false, and checking what the field counted is the whole lesson of this
section.** `attack_straddle.json` records **21 of its 147 `all_rows` with
`bound_is_sound: false`** (max `overstatement` 2.62) and **3 of 63
`control_rows`** (max 1.31). `unsound_rows: 0` comes from a filter that drops
`truncated` rows (`attack_straddle.py:81-83`; the same filter is repeated at 84-86
for the controls, which is what round five's off-by-one note was about), and all 21 are truncated with
`measured_states: 200000` — so on those rows the predicate was comparing the bound
against *the cap*, not against a count. `attack_barbell.py:86` handles the same
situation differently again, setting `bound_is_sound` to `None` (71 such rows).
**180 of the 347 sweep rows — 52% — never produced a meaningful predicate value at
all.**

So there are two reasons these attacks came back clean, and round three named only
the second. The first-order reason is a coverage hole plus a summary field that
silently absorbs it. The second-order reason follows.

Each row's predicate is `bound_is_sound`: `lower_bound <= measured_states`. On the
rows where it was evaluable it held, and the reason it holds where it holds is
that 2^m is loose by roughly 2k and the slack absorbs the cost model's
over-count. (Round three wrote "that is true on every board tried, and always
will be". The first half is contradicted by the 24 false rows above; the second
half was never measured and is not this document's to assert.) No row records how many
of the 2^m latch masks are *reachable at c_m*, which is what the record publishes
as its justification, and which was 758 of 1024 on a board these probes swept
past.

**That 758 does not survive its own audit, and this is the sharpest open item in
the ticket.** It is not merely prose-sourced. A reviewer re-ran the reconstruction
of the removed pre-fix loop that `test_verdict.py` itself carries, and got
**m=11 (2^11 = 2048)** on the board where prose records m=10 and a denominator of
1024, and **m=44** on the corridor-60 board where `RUN_STATE.md` and the test
record m=40 and `2^40 = 1.0995e12`. Nothing committed emits either figure; the
test that surrounds them says outright that it "pins the discrimination rather
than the number" and asserts only `bound["m"] == 8`. Three different boards are
also blended into one sentence in `verdict.py`'s comment and the test docstring —
a budget of 99 belongs to the corridor-60 board, and a board with `step_limit=25`
cannot host the 137-command walk cited beside it.

Whether the reviewer's reconstruction or the recorded figure is right **cannot be
settled from anything committed**, and that is the finding. The D-EX-029 narrative
does not depend on the exact denominator — the defect it describes is that the
published justification named masks the level does not realise, which the shipped
guard now prevents regardless of whether the count was 758/1024 or 758/2048. But a
number that appears in a decision record, a code comment and a test docstring, and
that no committed artefact can regenerate, is exactly what this ticket exists to
refuse. Recorded as unverifiable rather than repaired, because inventing a
replacement figure would be worse than carrying a labelled one. Their own `what` fields name the exact board and the exact mechanism
("straddling dip sources defeat the cost model `dist + 2m`"), so the defect was
not missed for want of looking at it.

The lesson, and it generalises past this ticket: **the bound was sound and the
reason printed beside it was false, and a check on the bound cannot see that.**
It took a reviewer that went after the sentence rather than the number. An
adversarial probe inherits whatever gap sits between its predicate and the claim
it is defending, so "the attack found nothing" is only as strong as the attack's
predicate — which is itself a thing to state and audit, not to assume.

`enumeration_sweep.json` is cited nowhere above as evidence and should not be:
its script is explicitly time- and memory-budget driven, so it does not
reproduce rung-for-rung (3 rungs against 4 on rerun). It is machine-dependent by
construction and is kept as a record of what this machine could reach, not as a
measurement anything rests on.

## What this does not close

The sealed drill's class (ii) gap is **structural and stays open**, and that is
now a sharper statement than the ticket's. `GridWorld.reachable(limit=200_000)`
(worldgen/core/world.py:259) **raises** above the limit, so worldgen cannot
build a world with a state space exhaustive search cannot reach — the catalogue
does not merely happen to lack one. `DRILL.json`'s
`classes_absent: ["large_unsolvable"]` therefore cannot be closed from inside
`exam`; it needs a worldgen change, which is outside this ticket's territory and
is requested in
`monitor/inbox/20260730T071500Z-RES-3-two-findings-that-say-filed-but-are-not-on-the-board.md`
rather than done. (Written "filed" first; no such ticket existed, and checking
cost one `ls`. Round five ran that `ls` again and the citation failed a second
time — the file existed only as an untracked working-tree file in the main
worktree, in no commit on any ref, so a paragraph about the difference between
"filed" and a real file cited one that was not. It is now tracked on this branch,
so the citation resolves; the lesson is that a citation to a file is a claim about
`git ls-files`, not about the disk.)
