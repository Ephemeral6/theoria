# V6-V23 — class (ii) large-space unsolvable, actually tested

RES-3, 2026-07-30. Branch `agent/v6-v23-large-space-verdict-gap`, base
`415556f8`. Territory `exam`. Zero API, zero sealed-pile contact.

The ruling and its argument are in `CRITERION.md`; the durable form is D-EX-028
at the end of `exam/DECISIONS.md`. This file is the narrative: what was done, in
what order, and what changed my mind.

## The headline

The ticket asked whether class (ii) — Theoria.md:259's "our home ground" — had
ever been really tested. It had not, and the reason turned out to be more
interesting than the gap: **the class's central claim was false, not merely
unmeasured.**

`exhaustive_feasible: False` asserted that no exhaustive method is feasible on
these boards. Every shipped class (ii) item is settled by an exhaustive
computation over at most 600 nodes in at most 5 ms, against claimed bounds of
1.15e18 to 1.33e36 (`crux_quotient_settles.json`). So the field is withdrawn and
replaced by `naive_enumeration_feasible: False`, which is true, measured, and
narrower: forward enumeration over the full (cart, button, latch mask) state —
the method class (i) is graded on — cannot terminate here.

That reframes what class (ii) measures, from "only invariant reasoning can
answer this" to **method selection under an apparent search barrier**. Weaker
than the design document, and it is what the artefacts support. It is also the
more useful claim, being falsifiable by one counterexample examinee where a
universal over all methods is not establishable by any experiment.

## Order of work, and the two places the measurement overruled me

1. **Recon carried over from the previous session** (`monitor/res/RES-3-notes/`).
   Three read-only lenses, all numbers re-derived here rather than trusted.
2. **The duplicate-switch defect**, confirmed exactly: `comb_open` with 60
   repeated switch entries gave 2^60 = 1.15e18 on a board with **359** reachable
   states, and neither the lane premise nor the threshold refused it — only
   `wellformed_problems`, from `_self_check`, after every `_large_space` call had
   written its record. Fixed in `subset_lower_bound` itself.

   *First correction.* My initial fix keyed on `level.switches`. The subagent's
   own self-refutation showed that is too coarse: a repeated entry naming a wall
   never becomes a dip candidate, so the bound over the real alcoves stays sound
   and the coarse guard would be a false refusal. The guard is gated on
   `candidates[:m]`. Both directions are pinned and both were mutation-tested
   red — and the coarse-guard mutation produces a self-contradictory message
   ("the first 40 dips name only 40 distinct cells"), which is the tell.

3. **The crux measurement**, which I ran myself rather than delegate, because
   the whole ruling rests on it.

   *Second correction, and the one that mattered.* I wrote the probe assuming
   all four items fall to the same connected-components pass. The measurement
   refuted that for three of them: `relaxed_edges` deliberately ignores the
   wrapper's `observation_loss`, so on ii2 the plain pass leaves start and goal
   in one component; ii3 is settled by a budget argument and ii4 by a monotone
   column. Had I not measured each separately the ruling would have shipped with
   a false supporting claim. The four mechanisms are now recorded separately.

4. **Three subagents in parallel**: the growth curve, the enumeration probe, the
   invariant-path survey. Each corrected something (below).
5. **The negative controls**, built last — see "what the review would have
   caught" below.
6. **An adversarial reviewer** on the finished diff.

## What the parallel work corrected

* **k=1..9 costs ~128 s, not the 2.3 s my own prior notes recorded** (2.6 s is
  k≤6). The shipped ladder stops at 6 — and k=6 turns out to be principled, not
  merely cheap: gantry at k=7 is 229,376 states, past the shipped cap, so 6 is
  the largest rung enumerable to completion under `MAX_ENUMERATION` at all.
* **orchard's m is 2(k−1), not 2k.** With LEFT forbidden the two column-1
  alcoves sit behind the start and are not dippable. This is why shipped ii4
  reports m=118 rather than 120, and mistaking it makes the ratio look like
  drift instead of convergence to 8/3.
* **The growth families include their operators.** My first test built bare
  constructors and failed on two families; the operator is part of the family.
* **`_large_space` is called by seven items, not four.** The three
  `solvable_hard` items carry the same record, so a check scoped to
  `large_unsolvable` would have left three unmeasured records behind the very
  check written to catch them. The test is scoped by the record.
* **`lp_potential` cannot walk this path, for a worse reason than expected.**
  Beyond the materialised-edge-list obstacle, its move algebra pins every
  transition's coefficient sum at −1 while an A2 move is 0 or +1, so no
  assignment expresses an A2 transition at any size. Worse, the adapter a reader
  would naturally write **fails silently** — it returns `certified` for a
  *solvable* level, with all four of the engine's self-checks agreeing because
  all four read the same wrong move list. No shipped engine can certify a class
  (ii) level at shipped size.

## What the review would have caught, and I fixed first

The ticket's item 4 asked for a board that **looks big but is enumerable**,
asserted not to be class (ii). I had been treating the duplicate-switch case as
that control. It is not — it is a bound-inflation control, a different failure.
Two proper controls now exist, and the second is the more valuable:

* 400 switches on a 200-cell corridor at budget 10: 6,480 states, enumerated to
  completion in 0.01 s, refused.
* The same board at budget 20 **truncates exactly as ii1..ii4 do**, and is still
  refused, because its bound is only 2^8. That is the conjunctive criterion in
  executable form: truncation alone must never earn the label, or a board 30
  orders of magnitude smaller than ii1 would ship as class (ii) on the strength
  of a cap we chose ourselves.

## State

`exam` suite **465 passed, 2 xfailed**; baseline before this run was 456/2.
`python exam/verify.py` **GREEN**, including its two-build determinism check
under PYTHONHASHSEED 7 vs 99. Artefacts regenerated with
`python -m exam.tools.build_papers` — never hand-edited.

Note on the artefact diff: most of `build_manifest.json`'s churn is not mine.
`exam/leakage.py` was last changed 2026-07-30 (d35e89cb) but the artefacts were
last regenerated 2026-07-29 (a95f7b32), so the committed files were stale
against their own generator and my rebuild absorbs that debt. Separately, the
manifest embeds **absolute worktree paths** (24 lines of the diff), so it churns
for whoever rebuilds it from wherever they happen to be working — a determinism
defect in a tracked generated artefact, filed rather than fixed here.

## Recorded, not fixed -- and, it turned out, not filed either

The heading here said "Filed, not fixed" and `monitor/board/items/` contained
no ticket for any of them. "Filed" implies a ticket exists; none did. That is
the fourth instance in this one ticket of a claim with nothing behind it, and the
cheapest to have checked -- one `ls`. Cross-territory supply belongs to the
monitor per `CHARTER.md`, so the first two are now written up in full and
requested in
`monitor/inbox/20260730T071500Z-RES-3-two-findings-that-say-filed-but-are-not-on-the-board.md`,
which is a real file rather than a word.

* **The sealed drill's class (ii) gap is structural.**
  `GridWorld.reachable(limit=200_000)` (worldgen/core/world.py:259) *raises*
  above the limit, so worldgen cannot build a world exhaustive search cannot
  reach — the catalogue does not merely happen to lack one. `DRILL.json`'s
  `classes_absent: ["large_unsolvable"]` cannot be closed from inside `exam`.
* **No engine on the invariant path** (above). An engine-rig change.
* **The quotient can exceed the true count**: class (i) item i4 enumerates to 31
  states but reports `positional_states` 55, because the quotient ignores
  `step_limit`. A live shipped instance of the unsoundness `quotient_note`
  already warns about, now with a number.
* **The calibration gate cannot catch a wrong `search_credible`**: the marker
  (`rubrics_verdict.py:869`) and the gate (`calibration.py:318`) read the same
  key, so a wrong derivation would be graded and calibrated consistently wrong.
  Already at `exam/STATUS.md:597-598`; repeated because the rename passes
  through that line.

## The second session: what the adversarial pass changed (RES-3, 2026-07-30)

The session that wrote everything above died before its three adversarial
reviewers reported, holding the commit `1486875e` unpushed. Withholding delivery
until they landed was the right call — **two of them found defects that would have
shipped**, and one of those is a soundness hole in the bound this whole run is
about. Recorded here because the run's own headline claims are what moved.

### The premise was checked in two directions out of three (D-EX-029)

`subset_lower_bound`'s docstring costs the walk at `dist(c_m) + 2m`. That is the
true cost only when the start lies **outside** the span of the dip sources — which
is true of every shipped item (`start_col=1`, the corridor end) and was assumed of
all boards. With an interior start the m nearest sources straddle the start, no
single walk to c_m touches the ones behind it, and the real cost is a
there-and-back sweep.

Built from a shipped constructor plus two shipped operators — `comb_open` with
hazards on both switch rows and an interior `start_col` — a board on which:

* `wellformed_problems()` is empty and both existing guards pass;
* `subset_lower_bound` returns m=40, `lower_bound` 2^40 = 1.0995e12, over
  `LARGE_SPACE_THRESHOLD`;
* `_large_space` **accepts it and writes the class (ii) record**;
* the enumerator truncates at the cap, so that half passes too;
* and the walk the published `arithmetic` describes costs 137 commands against a
  budget of 99, so it does not exist.

Measured, at three sizes: 758 of a claimed 2^10 latch masks actually reachable,
28,188 of 2^15, 32 of 32 only where the start sits at a corridor end. The **number**
survived every attempt — it stays a true lower bound on total states — so what
shipped false was the *justification*, on the class that is graded on justification.

Fixed at the selection, not by refusing: m is now the largest prefix whose **sweep
cost** fits the budget (`_sweep_cost` — reach the nearer end of the span, sweep to
the far end, 2 per dip). Verified both directions:

* the falsified boards now claim exactly what they realise — 32/32, 256/256,
  2048/2048 — and the straddle board drops to m=29, under threshold, refused;
* **all seven shipped records are unchanged**: m = 60, 118, 120, 120, 120, 120,
  120, and every bound identical to the byte. `min(ends) + span` collapses to
  `dist(c_m)` when the start is outside the span, which is why nothing moved.

The published `arithmetic` now names the sweep and prints its measured value
(spindle: 149 commands against its budget of 150) instead of the `dist + 2m`
shorthand that was the false clause.

### Three more, all confirmed by reproduction rather than accepted on report

* **The refusal message was true only by a coincidence of two constants.**
  `enumeration_refused_because` asserts the bound is "past the cap", and nothing
  checked it: it held because `MAX_ENUMERATION` (200,000) happens to sit below
  `LARGE_SPACE_THRESHOLD` (10^12). Raise the cap above the threshold and the record
  still published "past the cap of ...", a false sentence about the arithmetic
  printed beside it. `_large_space` now asserts the ordering.
* **`LARGE_SPACE_THRESHOLD` had no argument, and D-EX-028 rejects the criterion it
  ships.** The decision rejects "a threshold" as a standalone criterion precisely
  because the constant "arrived without an argument" — while in code that threshold
  over a computed bound *is* the whole gate. It now carries its derivation: the
  requirement is only `> MAX_ENUMERATION`, 10^12 is that with seven orders of
  headroom, every shipped item clears it by 6 to 24 orders, and any threshold in
  (256, 1.15e18] labels the same seven records and refuses both negative controls
  — robust across ~16 orders, a floor with margin rather than a measurement.
* **The grader printed the withdrawn claim at examinees.** `rubrics_verdict.py`
  told every examinee scoring zero on a search reason that "the state space of this
  level is beyond enumeration ... it is a false statement about the search" — the
  universal this run withdrew, machine-emitted, and the only account the examinee
  gets of its zero. D-EX-022 caught this exact sentence once; D-EX-028 renamed the
  field underneath it and left it standing. Now scoped to the naive enumerator, and
  it says outright that a cheaper complete method may exist.

### And one that made a negative control stop being one

`repro_duplicate_switch.py` read `record["exhaustive_feasible"]`, renamed out of
existence in the same commit that shipped the file. It survived because the new
guard makes `_large_space` raise, so the branch never ran — meaning the **only path
that reports the defect the control exists to catch** (the guard regressing and an
inflated record being written) had become a `KeyError`. A control whose failure
path is broken is not a control.

### State after the fixes

`exam` **465 passed, 2 xfailed**; `python exam/verify.py` **GREEN**, including the
two-build determinism check. Artefacts regenerated through
`python -m exam.tools.build_papers` — the `arithmetic` string is embedded in the
shipped truth keys, so the rename of a cost clause is an artefact change, not a
comment change.

### Why this run's own adversarial attacks missed it, which is the lesson

This is the part worth keeping. The straddle defect was **not** missed for want of
looking at it. This run shipped two adversarial probes, 147 KB of them, and their
own `what` fields name the exact board and the exact mechanism:

> `attack_barbell.json` — "barbell board: dip sources straddle the start, cost
> model `dist + 2m` under-charges the walk between the two ends"
>
> `attack_straddle.json` — "straddling dip sources defeat the cost model
> `dist + 2m`"

347 sweep rows between them. Both report `unsound_rows: 0`, `worst: null`. A third
reviewer's independent sweep, 1,034 completed rungs over interior `start_col` with
binding budgets, also found zero.

They were all asking the wrong question. Each row's predicate is
`bound_is_sound` — `lower_bound <= measured_states`, i.e. *is 2^m a true lower
bound on the total reachable state count*. It is, always, on every board tried:
2^m is loose by roughly 2k, and that slack absorbs the whole over-count. No row
records how many of the 2^m **latch masks are reachable at c_m**, which is the
thing the record actually publishes as its justification, and which is 758 of 1024
on the board the probe swept past.

So an adversarial probe was aimed at the right target, with the right hypothesis
in its own description, and returned clean — because its predicate was weaker
than the claim it was defending. The bound was sound and the reason printed beside
it was false, and a check on the bound cannot see that. It took a reviewer that
went after *the sentence* rather than *the number*.

Two consequences, both acted on:

* the probes' predicate is the bug, not their coverage. A sweep that measured mask
  reachability at c_m would have failed on its first straddling row.
* **`unsound_rows: 0` is now reported rather than left in a JSON file.** Neither
  `CRITERION.md` nor this file mentioned these two artefacts at all before this
  paragraph — 147 KB of committed negative-result evidence invisible to a reader,
  which is under-claiming, and it also meant nobody re-read what the predicate was.

### One thing deliberately NOT regenerated

`exam/runs/20260729T1030Z-V6-exam-on-sealed-dryrun/DRILL.json` is committed, and
this branch moves its generator twice: `classes_absent_because` loses the phrase
"a state space exhaustive search cannot reach", and every truth record gains the
`state_space` measurement described above. So that artefact now disagrees with
`sealed_drill.py` as shipped.

Left alone on purpose. Artefacts under `runs/` are provenance — pinned by their
own run's `MANIFEST.json` and historical by construction — and rewriting a
previous run's output to match today's code destroys the only record of what that
run actually produced. The same reasoning is why check G in the `papers` territory
scans only the live directory and treats `runs/` as the past.

What that costs, stated rather than left implicit: a reader who re-runs the drill
gets different bytes from the committed ones, and nothing in that run directory
says why. The `classes_absent` **verdict** in it is still correct — the whole
worldgen catalogue tops out at 2654 reachable states — so the finding it records
stands; it is the wording of the reason and the absence of the `state_space`
record that have moved. Filed for whoever next touches the drill: the V6 run
should either be re-run wholesale under a new UTC directory or carry a note
pointing here, and a one-line stamp convention for `runs/` artefacts (the same
idea as `papers`' `audit-stamp`) would make this class of drift visible instead of
needing a paragraph like this one.

### State of the third reviewer's findings

The measured-versus-asserted audit reproduced every load-bearing claim: the ≤600
nodes and ≤5 ms crux, the 1.15e18/3.32e35/1.33e36 bounds, 465/2 and the 456/2
baseline (by extracting the base commit and running it), gantry k=7 = 229,376,
orchard's m = 2(k−1), the seven-not-four scoping, the silent lp `certified` on a
solvable level, and the 24 absolute paths. `MANIFEST.json`'s four required fields
are present and `base_commit 415556f8` is exactly `HEAD^`.

What it found not reproducible, and what is being corrected in the documents rather
than defended:

* `probe_answer_key.json` shipped **pre-rename** — 24 leaf diffs against its own
  generator, in a commit whose subject is the rename. Regenerated.
* "machine-checking each certificate in ≤3.1 ms" is one wall-clock observation
  restated as a bound; fresh runs give 3.06 ms and 3.66 ms. A timing is not a
  bound.
* "~128 s" for k=1..9 matches neither `growth_curve.json`'s own
  `total_seconds: 122.247` nor a rerun's 153.24 — a third number with no source.
  The *decision* it justifies (stop the ladder at k=6) is independently sound:
  gantry at k=7 is 229,376, past the cap.
* `CRITERION.md`'s opening claim that its numbers come from three named artefacts
  is false — the work-item-3 section, the certificate timing and the crux table
  come from four others, and `enumeration_sweep.json`, `invariant_path_probe.md`
  and both adversarial probes are cited by neither document.
* "surviving column deltas are {0,0,+1}" against an artefact computing
  `sorted(set(...)) = [0, 1]`. The repeated 0 inside set braces corresponds to
  nothing computed.
* every `verdict.py` line anchor in `CRITERION.md` points at the base commit, ~58
  lines off, because `verdict.py` grew 80 lines in the same commit — and the fixes
  above widened it to ~107. Being switched to symbol names rather than re-numbered:
  a line anchor into a file the same commit edits will rot again, which is the
  standing finding of board items P21 and P22.
* two figures are honestly asserted rather than measured and now say so: the
  corridor-60 edge count (~4e36 by carrying a measured ×4.0, against a stated
  ~6e36) and "2.6 s is k≤6" (no committed artefact; a rerun gives 2.918 s).
* `enumeration_sweep.json` does not reproduce (3 rungs against 4) because the
  script is explicitly time- and memory-budget driven. Machine-dependent by
  construction, no audited claim rests on it, and it is labelled rather than
  presented as deterministic.
* `D_verdict`'s A2 half — `a2_plain_move: 0`, `a2_latching_move: 1` — is a pair of
  Python literals printed as if measured, while only the lp side (125 role
  assignments, all −1) is computed. The claim is true (`potential.py:306-308`
  confirms it independently) but the artefact does not measure the half that makes
  it bite. The same shape as the standing audit finding about a hand-written first
  ledger entry.

## Third session: the corrections landed, and one of them was itself the defect

The list above was written as *findings*. It is now also a record of work done, so
this section closes each one rather than leaving a reader to diff two documents.

Applied to `CRITERION.md` in `fd362f02`:

* the provenance paragraph naming three of eight artefacts, replaced by a
  section-to-artefact map covering all of them;
* every `verdict.py` line anchor, **switched to symbol names rather than
  re-numbered**. Re-numbering resets the clock and nothing more: the anchors had
  rotted ~58 lines against the base commit and ~107 once this round's code fixes
  landed, and P21/P22's standing finding is that an anchor into a file its own
  commit edits will rot again. The three anchors into files this work does not
  touch were verified line-by-line and kept: `Theoria.md:259`,
  `engine-rig/DECISIONS.md:780-781` (narrowed from `779-781` to D-024's actual
  sentence), `worldgen/core/world.py:259`;
* `{0,0,+1}` → `[0, 1]`, matching what `crux_quotient_settles.json` computes;
* `~6e36` → `~4e36`, which is what carrying the measured ×4.0 to corridor 60
  actually gives, with the measured part and the extrapolated part now separated;
* criterion (a) amended with D-EX-029, since the document rejected a bare
  threshold and then shipped that constant as its only gate;
* the two adversarial probes and `enumeration_sweep.json`, previously cited by
  neither document, now cited with what came back — zero unsound rows — and with
  why that was not reassurance.

Then, in `ee9befa0`, a correction to the correction. `fd362f02` replaced "~128 s"
(a number matching nothing) with `growth_curve.json`'s recorded `total_seconds:
122.247`, and in the same passage cited the rerun's 153.24 s, "2.6 s"/2.918 s,
3.06/3.66 ms and 758-of-1024 as though they were equally sourced. **They are not.
Every one of those exists only in this file's prose, with no committed artefact.**
Under this repo's own precedence rule — JSON artefacts beat prose reports — they
are the weakest evidence in the document, not the fix to it.

That is the third distinct appearance of one shape in this ticket: a claim whose
justification is weaker than the claim. First `exhaustive_feasible: False`, whose
own answer key was a 600-node walk. Then the adversarial probes, whose predicate
tested the bound while the record's justification was about reachable latch masks.
Now a provenance correction sourced from prose. The reruns are kept and labelled
rather than deleted, because what they establish is a ~25% spread — no single
wall-clock figure is a property of the artefact — and swapping 128 for 122.247
while still calling it "the cost" would have repeated the original error with a
better-sourced number.

Worth stating plainly for whoever picks this up: **the defect class survives being
named.** It was named in this file, in a DECISIONS entry, and in two commit
messages, and it still recurred in the commit that was fixing it. What caught it
was not vigilance but a mechanical question asked of each number — "which
committed file emits this, and can I open it?" — which is the only form of the
check that does not depend on remembering to be careful.
