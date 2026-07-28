# E11 — six engines judging each other

Each engine here has its own assertions and its own tests, and every one of them
passes. Nobody had checked whether the engines **agree with each other**. So:
six cross-checks, each taking one engine's output and re-deriving it by a
*different* engine's method — conservation laws re-checked as linear
constraints, potentials re-checked by exhaustive reachability, frontiers by
brute-force enumeration, deadlock theorems by reachability graph, segmentations
by reconstructing the original frames, probe entropy by brute-force partition.

The point was never to run anything twice. It was to find the inconsistencies
that **only** a cross-check can expose: a fact each engine's own tests are
structurally incapable of contradicting.

`engine-rig` was not modified — the work order forbids it and the manifest
records zero code bytes changed. Findings went to the owning territories'
inboxes.

## The independence discipline, stated first because it is what makes this worth anything

Every partial carries a **shared-dependency list**: what the "independent"
checker actually has in common with the thing it is checking. A cross-check that
does not say this has no evidence of its own independence.

That discipline earned its keep. One partial claimed *"two independent oracles
agreed, zero disagreement"* — and the adversarial review showed the agreement
was **vacuous**: frame-change count = judged-false rows = mover-move count, all
three equal, because both oracles shared one interpretive premise about what an
"effect" is. They could not have disagreed on the disputed point.

> **Two oracles agreeing is one piece of evidence, not two, when they share a
> premise. Independence has to be traced to the premises, not to the
> implementations.**

## What held up

| claim | verdict |
|---|---|
| deadlock theorems and unsolvability certificates — 50 claims, incl. 18 `ring`/`open4` never touched by recheck | **50 / 50 upheld, 0 overturned.** Three encodings (STRIPS, C4 Lean, the reviewer's own) agree bit-for-bit on `open4far`: 112 actions, 3352 reachable states, optimal 11 |
| `lp_potential` soundness — 3000 worlds, 505 312 states exhaustively enumerated, no budget exhaustion | **1550 certificates, zero false.** 42 090 admissibility comparisons, zero violations |
| `probe_frontier` entropy / partition / ranking — 4000 worlds | 0 partition mismatches, 0 entropy mismatches, **0 real reorderings** (35 differences, all ties or float noise) |
| `cegis_miner` frontier completeness within each rule's declared `frontier_max_size` | **zero omissions.** P3 holds |
| `mdl_segmenter` geometry and bit identities | 0 wrong cells across 506 302; declaration/script/baseline identities 300/300; 6939 events re-priced individually with zero deviation |

Five results that a paper can lean on, and they exist because somebody tried to
break them from outside rather than confirming them from inside.

## What did not

**`mdl_segmenter` — a bit-accounting error that changes the answer.** The
`objid` field width is derived from the maximum components in a single *frame*,
but tracks span frames: **126 of 300 worlds cannot number their own tracks**
(worst case 40 tracks in 2 bits). Undercharges 5.7 % of bits, and correcting it
means **10 worlds no longer beat baseline**. MDL bits are this engine's only
basis for choosing a segmentation. Also: the declaration charges per-cell colour
while storing one `color`, so 89.4 % of the colour budget buys something never
emitted; `segment_operator` is a string literal (0/800 payload differences
against 479/800 real track-count differences — confirmed three ways).

**`cegis_miner` — lifted rules violate the engine's own P1, and the reading does
not matter.** `lift` substitutes `?dir` into a template guard and never
re-verifies; 104 of 149 lifted rules have the guard `["act==?dir"]`. The
evaluator is a plain string comparison (`action == arg`), so the atom is
*always false*, and no consumer anywhere binds `?dir`. Unbound, the rule never
fires and is published as mined anyway; bound, it fires on rows without that
effect. **P1 is false either way.** Separately, 131 of 149 lifted rules'
`applicable` is not derivable from their own published guard.

**`probe_frontier` — a cross-track contract break.** Bare `Infinity` reaches
`candidates.jsonl` (1633/4000). It is not valid JSON; Python accepts it as its
own extension and every strict reader rejects it; neither
`tools/validate_candidates.py` nor the frozen `candidates_schema.md` mentions
it. That stream is shared with the other track. Also: a zero-cost useless action
scores `inf`, ranks first, and makes `best_probe` return `None` — discarding an
available 1-bit experiment (82/4000); and the same engine holds two opposite
definitions, `ProbeValue.value(cost=0) = inf` versus
`ExecutableProbe.value(cost=0) = 0.0`.

**A contradiction in an adjudication rule rather than in any theorem.**
`cold-start-a0/certify/fd_unsat.py` reads Fast Downward's exit 12 as *proved
unsolvable* on the exception string alone; `engine-rig`'s `backends.py` treats
12 as ambiguous and additionally requires the optimal rung with an exhausted
state space. a0's rule turns "I gave up" into "I proved it" — the exact failure
its own docstring says it prevents. Both sides' tests are green because a0's
tests encode the mapping into their assertions. It has not fired only because
the pipeline runs the stub. Cross-track, registered, untouched.

## Two claims of mine that the adversarial reviews killed

Both are here rather than quietly dropped.

**`zero_space` has no defect.** A cross-check found 102 published "conservation
laws" falsified on a legal transition, and I read it as a quantifier error. The
reviewer found `DECISIONS.md` **D-003 pre-registers that exact mechanism and
calls it sound** — a pre-written exemption. My separate complaint that
`coverage = n/n` cannot express thin evidence was also wrong: `common/candidates.py:75`
defines k/n as *transitions the guard applies to*, and an invariant's guard is
tautological, so n/n is correct. The quantitative results all reproduced
bit-for-bit; only my characterisation was wrong. Nothing was escalated as a
defect.

What the reviewer found instead is worth more: on the real g50t game the engine
publishes **366 laws from 4 independent differences** (`space_dimension = 366`,
`difference_rank = 4`, `n_features = 370`; 2911 such rows in `theoria-arm`).
`366 = 370 − 4` is arithmetic, not a bug — and `difference_rank` *is* in the
payload, so the thinness is disclosed. Nothing downstream discounts by it. The
k=2 immunity that protected `parityworld` (0/135) does not hold on ARC.

**`cegis_miner`'s headline was wrong.** The claim was 1209 published rows false
because the miner mined a static obstacle. The objects in those 72 worlds have
**zero displacement throughout** (72/72), so `effect: none` is a *true statement
about that rock*; and P1's quantifier ranges over ledger rows, not worlds, which
expands to `applicable == support` — verified 932/932. The residual defect is
different and smaller and real: **`rule_hypothesis` carries no object binding**
while `object_hypothesis` sits beside it in the same stream carrying
`object_id`. The danger is a reader attaching a subjectless rule to the moving
object — a mistake the reader makes because the engine gave it no way not to.

## The thread running through all six

Where these engines fail, they fail **at the seams**: an object-selection
convention crossing from segmenter to miner, an exit code crossing from planner
to certifier, a bookkeeping choice in `cegis` deciding which experiment
`probe_frontier` recommends, a float written by one engine and parsed by another
track. Every engine is internally consistent and separately green. Nothing that
tests one engine at a time can see any of it.

That is the argument for this kind of work existing at all, and it is also the
limitation: six cross-checks found what six pairings could reach. The pairings
were chosen in the work order, not derived, and a different six would find a
different set.
