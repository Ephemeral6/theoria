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
computation over **at most 600 nodes** — single-digit milliseconds on this
machine — against claimed bounds of
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
  the largest rung at which **all four** families complete under
  `MAX_ENUMERATION`. (This said "the largest rung enumerable to completion under
  `MAX_ENUMERATION` at all", which the artefact beside it refutes:
  `growth_curve.json`'s orchard family, whose m is 2(k−1), measures 10,920 states
  at k=7, 43,688 at k=8 and 174,760 at k=9 — all under 200,000 — and only passes
  the cap at k=10 with 699,048. gantry, lattice and spindle all reach 229,376 at
  k=7. "At all" overstated it by three rungs; the all-four form is what the
  ladder actually needs. Corrected in the fourth session below.)
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
which is a real file rather than a word — tracked, and reachable at commit
`98091f99` on this branch (`git log --all --oneline -- <path>`). When round five
of the adversarial pass checked, that was not yet true: the file existed only as
an untracked working-tree file in the main worktree and was in no commit on any
ref, so between this paragraph being written and `98091f99` landing, the sentence
was an instance of exactly the defect it is about. `98091f99` is the commit whose
own finding is that 94 of the fleet's 229 `monitor/inbox/` proposals were in no
commit while documents cited them as filed.

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
* **The `searcher` probe cannot catch a wrong `search_credible`**: the marker
  (`exam/grading/rubrics_verdict.py:869`) and the probe's expectation
  (`exam/grading/calibration.py:318`) read the same key, so a wrong derivation
  would be graded and calibrated consistently wrong. Already `exam/STATUS.md`
  **item 28**, "The `searcher` probe cannot see a wrong `search_credible`";
  repeated here because the rename passes through it.

  (Two corrections, both from round five. This bullet was headed "The
  calibration gate", which names a different `exam/STATUS.md` item — "The
  calibration gate sees two of eleven marking outcomes", a separate finding
  about marking coverage. And it cited `exam/STATUS.md:597-598`, correct at base
  `415556f8` and rotted by this run's own edit to that file: inserting the new
  item 27 pushed item 28 down to lines 608-615, and 597-598 now fall inside item
  27's text. Anchored by item number instead, since a line anchor into a file
  this run edits is P21/P22's standing finding. The two source anchors were
  re-checked line-by-line today and both hold.)

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
  printed beside it. `_large_space` now asserts, **per item**, that that item's
  bound exceeds `MAX_ENUMERATION`.

  (This said "`_large_space` now asserts the ordering", and that claims more than
  the guard — the same defect as summarising a check by what you wanted it to do.
  Read today, `_large_space` applies exactly two gates, both functions of one
  item's `lower_bound` and neither a comparison between the two constants:
  `lower_bound < LARGE_SPACE_THRESHOLD` raises, then `lower_bound <=
  MAX_ENUMERATION` raises. Its own comment says why an ordering check was
  rejected — "the ordering is not stated anywhere as a requirement and either
  constant can be moved by someone who never reads this function". The code is
  right and three copies of the prose were wrong; see the fourth session below.)
* **`LARGE_SPACE_THRESHOLD` had no argument, and D-EX-028 rejects the criterion it
  ships.** The decision rejects "a threshold" as a standalone criterion precisely
  because the constant "arrived without an argument" — while in code that threshold
  over a computed bound *is* the whole gate. It now carries its derivation: the
  requirement is only `> MAX_ENUMERATION`, 10^12 is that with roughly seven orders
  of headroom over the cap of 200,000, and every shipped item clears 10^12 by 6 to
  24 orders (bounds 1.15e18 to 1.33e36) — a floor with margin rather than a
  measurement.

  (This bullet also said "any threshold in (256, 1.15e18] labels the same seven
  records and refuses both negative controls — robust across ~16 orders".
  **Withdrawn.** Re-measured today by patching `LARGE_SPACE_THRESHOLD` and calling
  `V.build()` and `V._large_space` directly: the same **seven** records are
  labelled at every T from **1** through **2^60 = 1152921504606846976**
  inclusive, and at 2^60 + 1 `build()` raises on spindle — so the upper endpoint
  is exact, but the interval runs down to 1, not 256. The reason is that the
  controls are not held out by the threshold at all: control 2's bound is 2^8 =
  256, so for every T ≤ 256 it is refused by the **second** gate
  (`lower_bound <= MAX_ENUMERATION`), and at T = 2 both controls are refused by
  that gate. 256 is control 2's own bound — the lower endpoint you get only if
  you assume gate 1 is the only refusal. The audit set therefore cannot
  distinguish 10^12 from T = 1 and does not constrain the constant from below,
  which makes "robust across ~16 orders" a property of the audit set stated as a
  property of the constant. `CRITERION.md` and D-EX-029 withdrew this in
  `08820583`; the sentence stood here until the fourth session below.)
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

## Fourth session: round five, and the corrections that had landed in one document only

Round five's report is `adversarial/round5-findings.md` (F5-1 … F5-14), written
against tip `08820583`. Its finding about round four is that the *analysis* held
under reproduction and the *landing* did not: three corrections were applied to
`CRITERION.md` and nowhere else, so the withdrawn sentence was still shipping in
`exam/papers/verdict.py`, in `exam/DECISIONS.md`, and in this file. This section
closes the findings whose fix is in this file or in one of this run's artefacts.
Everything below was re-derived here; no number is carried over from the report.

### The two withdrawn sentences that were still standing in this file

* **F5-1 — the threshold interval.** The paragraph above at "`LARGE_SPACE_THRESHOLD`
  had no argument" still asserted "(256, 1.15e18] … robust across ~16 orders",
  withdrawn in `08820583`. Corrected in place, with the old wording quoted, and
  re-measured rather than copied: T from 1 to 2^60 inclusive all label the same
  seven records, 2^60 + 1 raises on spindle, and the controls are held out by the
  cap gate rather than by the threshold. The code half was fixed in `0154c8f1` —
  `LARGE_SPACE_THRESHOLD`'s comment now says "no sweep over this audit set defends
  the constant … these cases cannot distinguish 10^12 from 2 and do not constrain
  the number from below at all".
* **F5-2 — "`_large_space` now asserts the ordering."** Corrected in place, with
  the old sentence quoted. Read today, the guard applies two gates, both over one
  item's `lower_bound`, and neither compares the constants. `0154c8f1` fixed the
  copy in `verdict.py`, whose comment now says outright "`_large_space` does not
  assert the ordering: its second gate asserts a property of each *bound*
  instead". Three copies of one wrong summary, in three files, from one round-three
  sentence.
* **F5-8 — "the largest rung enumerable under `MAX_ENUMERATION` at all"**, in the
  parallel-work list above. Refuted by the artefact cited in the same sentence and
  corrected in place: `growth_curve.json`'s orchard family measures 10,920 /
  43,688 / 174,760 states at k = 7 / 8 / 9, all under 200,000. The claim the
  ladder needs — largest rung at which all four families complete — is true.
* **F5-11 — "in at most 5 ms"** in the headline. The ≤600-node half is structural
  and reproduces to the byte; the millisecond half does not, so the headline now
  carries the node count and calls the timing machine-dependent. Measured:
  `crux_quotient_settles.py` re-run three times here gives ii3 a maximum of
  0.0049 / 0.0049 / 0.0048 s against the committed 0.0047, and round five's run
  on this same machine gave 0.0051 — over the claimed bound. The claim is 4% from
  false and has already been false once. The same sentence still ships in
  `exam/papers/verdict.py`, `exam/STATUS.md` (twice) and `exam/DECISIONS.md`;
  those are not this file's to edit and are recorded here as still open.

### The rotted anchors round three and four did not reach

* **F5-5 — nine `verdict.py` line anchors published in an artefact, not a
  comment.** `repro_duplicate_switch.json`'s `wellformed_runs_at` field, and the
  same strings in `repro_duplicate_switch.py`'s docstring and body, pinned
  `_self_check` at 1278, `wellformed_problems()` at 1354 and seven `_large_space`
  call sites at 1010/1030/1055/1081/1212/1241/1267. Every one had rotted by 176 to
  182 lines. (The measurement, not a new anchor: `_self_check(items)` is called at
  1454, defined at 1520 and calls `wellformed_problems()` at 1536, and the seven
  call sites are at 1186/1206/1231/1257/1388/1417/1443 — as of this paragraph, and
  quoted here only so the size of the rot is checkable.) Both file and artefact now
  anchor by symbol
  — `build()` calls `_self_check(items)` as its last step, `_self_check` is the
  module's only caller of `Level.wellformed_problems()`, and all seven
  `_large_space(lvl)` calls are argument expressions of `_make_item(...)` earlier
  in `build()`. Deliberately *not* re-pinned to today's numbers: `verdict.py` grew
  another 13 lines during this session alone, which moved round five's own
  observed numbers before its report was a day old.
* **F5-6 — a fourth rotted anchor, `exam/STATUS.md:597-598`.** Correct at base
  `415556f8`; rotted 11 lines when this run inserted the new item 27 above it, so
  597-598 now fall inside item 27's own text. Replaced by "item 28". Its bullet
  heading was also wrong — it named "the calibration gate", which is a different
  `exam/STATUS.md` item — and is now the `searcher` probe, which is what item 28
  is called. Both source anchors were re-checked and hold:
  `exam/grading/rubrics_verdict.py:869` and `exam/grading/calibration.py:318` both
  read `search_credible`.

* **Two more rotted anchors, found in the same artefacts after the F5-5 fix** — one
  of them in the note written to fix F5-5, which is worth recording as such.

  First: the F5-5 note said the nine anchors "had all rotted by 176 to 182 lines",
  and a reader made it 242 for one of the nine by comparing 1278 against today's
  `def _self_check`. Settled against the commits rather than argued: at base
  `415556f8`, line 1278 is `_self_check(items)` — the **call** — and `def
  _self_check` is at 1338, never anchored. So all nine were correct at the base
  commit; eight were off by 58 and the ninth (`wellformed_problems()`) by 64 at
  `1486875e`, the commit that shipped the artefact; and they are off by 176 and 182
  at `824b9fb4`. The range was right and ambiguous, which for an anchor is the same
  problem. The note now names which symbol each number pointed at, and pins each
  rot figure to a commit, because `verdict.py` moved again at `0154c8f1` after the
  anchors were replaced.

  Second: **`enumeration_probe.json`'s `deterministic.note` was two renames and one
  anchor out of date**, and it is row 1 of `CRITERION.md`'s provenance map. It read
  "`_large_space()` (verdict.py:767) writes exhaustive_feasible=False,
  enumerated=null, truncated=false onto every class (ii) record". `verdict.py:767`
  was `def _large_space` exactly at base `415556f8` and is 130 lines off at
  `824b9fb4`; `exhaustive_feasible` is the field this whole run renamed to
  `naive_enumeration_feasible`; and `truncated` is `null`, not `false` — the change
  D-EX-028 made specifically so a record could not read as an enumeration that ran
  and came back clean. So the document's central rename was contradicted by the
  first artefact its own map points at. Round five quoted rows out of this file and
  never read its note. Corrected in the generator and regenerated: of 230 leaves, 8
  moved — the note, the `deterministic_sha256` it feeds, and 6 wall-clock timings.
  All 219 measured values are unchanged.

### F5-7 — stale, and it stopped being true between the finding and the fix

Round five found the file this document cites as proof that "filed" is no longer
just a word to be untracked and in no commit on any ref. It is now committed:
`git log --all --oneline -- monitor/inbox/20260730T071500Z-RES-3-two-findings-that-say-filed-but-are-not-on-the-board.md`
returns `98091f99`. The citation now names that commit, so the claim is checkable
from the citation itself rather than from an `ls` on whichever worktree the reader
happens to hold — which was the actual defect, since the file *did* exist, just
not anywhere a reader of this branch could see it. `98091f99`'s own finding is
that 94 of the fleet's 229 `monitor/inbox/` proposals were in no commit.

### F5-3 and F5-4, closed by another hand — recorded so the record does not disagree

Both are about `probe_lp_interface`, which this session did not own. Recorded
because the findings list further up this file still describes the old artefact
and would otherwise read as a description of the current one.

* The A2 measurement that could not terminate was replaced in `b43427f0`, and in
  `9cf779a3` the four keys the round-three finding quotes — `a2_plain_move`,
  `a2_latching_move`, `a2_blocked`, `a2_button_press` — were removed as
  misleading: they held coefficient *sums*, so `a2_plain_move: 0` read as "no
  plain move was seen". **Where those names appear above, they are quotations of
  what was found wrong and are left as written.** The current artefact publishes
  `a2_coefficient_sum_by_kind` (`{blocked: 0, button press: 1, latching move: 1,
  plain move: 0}`), `a2_transitions_by_kind` (`{blocked: 12166, button press: 1,
  latching move: 11376, plain move: 28337}`), `a2_transitions_by_branch`,
  `a2_transitions_enumerated: 51880` over `a2_states_enumerated: 12970`, and
  `a2_thin_coverage`, which names the four branches and one kind observed fewer
  than three times. Cited by key name, not by line: that file regenerates.
* F5-4 refuted a true claim of round four's. The exhaustive loop over role
  assignments really is at n = 5, giving 5^3 = 125 assignments, and round four
  withdrew that as unsourced. It was sourced — in the committed generator. The
  artefact now says it too: `D_role_assignments: {"n": 5, "assignments": 125}`,
  beside `D_coefficient_sums: [-1.0]`, added in `b43427f0` and absent from the
  artefact at `1486875e`, `722b6e8e` and `08820583`. So "the figure 5 appears
  nowhere" was true of the JSON round four was reading and false of the run, which
  is the distinction that turned a true claim into a withdrawn one.

### Round five's remaining findings — fixed in `CRITERION.md`, independently reproduced here

Not this file's to fix, and all of them were landed in `CRITERION.md` by another
session in the same round. Reproduced here anyway, because a finding accepted on
report is the failure mode this ticket exists for, and because two of them sharpen.

* **F5-9 — "`edges/states = 1.7500` … at every rung".** Recomputed from
  `probe_lp_interface.json`'s `E_comb` (the artefact stores `reachable_states` and
  `edges`; the ratio is derived, not a field). Nine rungs, corridor 2 to 10:
  1.7000000, 1.7380952, 1.7470588, 1.7492669, 1.7498168, 1.7499542, 1.7499886,
  1.7499971, 1.7499993. That is 1.7500 to four decimal places at **4 of 9** rungs
  and exactly 1.7500 at **none**. The ratio the corridor-60 arithmetic actually
  uses, 4,893,348 / 2,796,200, is the last rung alone. The convergence is real and
  the phrase "at every rung" is not.
* **F5-13 — "both are recorded as measurements".** Confirmed against `V.build()`
  run here: the seven records with `naive_enumeration_feasible: False` carry
  m = 120, 60, 118, 120, 120, 120, 120, and all seven carry
  `enumeration_attempted: False` and `truncated: None`. Criterion (b) is therefore
  *not* in the record and not in the builder — `_large_space`'s two gates are both
  over `lower_bound` — it is in the test and in `enumeration_probe.json`. The
  record is honest; the sentence describing it claims more than the record holds.
* **F5-14 — the criterion-(b) row covers four of seven.**
  `enumeration_probe.json`'s `deterministic.items` has nine rows, i1-i5 and
  ii1-ii4; the four ii rows all carry `truncated: true`, `hit_cap: true`,
  `states_visited: 200000`, `builder: "_large_space"`. The three `solvable_hard`
  records that also carry `naive_enumeration_feasible: False` — the seven-not-four
  point this file makes above — are absent, so their (b) evidence is the test only.
  `CRITERION.md`'s map row now says so. **Left open on purpose:** the better fix is
  to widen `enumeration_probe.py` to all seven records rather than to annotate the
  map, since the same three records are the ones a check scoped to
  `large_unsolvable` would have missed — which is the mistake this run already made
  once and wrote up above. Not done here because it changes a committed artefact's
  contents rather than a description of them, and this session's remit was the
  descriptions.

  **Done after all, in `e4b25676` — this bullet is the description that then
  lagged.** The probe was widened to all seven and criterion (b) holds on all
  seven; `deterministic.coverage` now reports `criterion_b_records_probed: 7`,
  `_holding: 7`, `_failures: []`, and keeps `superseded_coverage` naming the old
  four-of-seven state. The three `solvable_hard` records iii6/iii7/iii8 each
  truncate at the cap with no solution inside it — and that last conjunct is
  load-bearing for exactly those three *because they are solvable*: a plan found
  inside the cap would have meant the naive method works there and the record's
  refusal was unfounded. Round six confirmed the conjunct is genuinely
  independent (`enumerate_states` has no early return on a solution) and that the
  probe filters on `verdict.build()` with the test's own predicate rather than a
  hardcoded list. Round six also caught that this bullet, `CRITERION.md`'s map
  row and its ruling section all still said "four" afterwards — three descriptions
  left behind by one fix, which is the same shape as the finding they describe.
* **F5-10 and F5-12** were resolved by other hands this round. `0154c8f1` added the
  `<=3.1 ms` entry to `exam/DECISIONS.md` so the decision record no longer holds the
  withdrawn position; and the 1,034-rung sweep, absent from both the map and the
  exception list, is now in `CRITERION.md`'s exception list beside the other
  prose-only figures. One datum this session can add to the first: regenerating
  `probe_answer_key.json` here gives `check_certificate_seconds` of 0.00313 —
  **above 3.1 ms**. So 3.1 ms bounds the four committed samples, as that entry
  says, and does not bound a re-run of the generator that produced them. That is a
  narrower claim than the entry makes and is the reason this file's own headline
  stopped carrying a millisecond figure.

### The artefact reproduction table

Every generator in this directory was re-run and its output diffed leaf-by-leaf
against the committed file, then the committed file was restored. This is the
check that found the CRITICAL last round, so it is run as a matter of course now
rather than when something looks wrong.

| generator | reproduces byte-for-byte | what differs, and how much |
|---|---|---|
| `crux_quotient_settles.py` | **no** | 7 of 93 leaves, every one under `timing_seconds`. ii1 `compute_lower_bound` 0.0021→0.0025, ii2 0.0019→0.0024, ii3 0.0047→0.0048, ii4 0.0012→0.0017. No structural field moves. |
| `probe_answer_key.py` | **no** | 16 leaves, every one a `MEASURED.*_seconds`. `check_certificate_seconds` 0.00306→0.00313 and 0.00149→0.00156; the other two (1e-05, 0.00075) unchanged. |
| `enumeration_probe.py` | **no** | 7 leaves, all under `timings_nondeterministic`. `deterministic_sha256` reproduced. (Then deliberately changed: the note fix above moves `deterministic.note` and therefore the hash over it, 8 leaves of 230, 219 measured values untouched.) |
| `growth_curve.py` | **no** | 34 leaves, all under `timings_seconds`; `total_seconds` 122.247→143.786. `stable_sha256` `1dabe798…` reproduces. |
| `enumeration_sweep.py` | **no** | 30 leaves. Timings, RSS and every extrapolation move: rung 0 `states_per_second` 250784.8→205394.3, `power_law_fit.implied_years` 229.51→332.32 (+45%), `linear_in_states.implied_years` 0.472→0.594. |
| `repro_duplicate_switch.py` | **yes** | 20 of 21 leaves identical; the 21st is `wellformed_runs_at`, rewritten in this session for F5-5. |
| `probe_lp_soundness.py` | **yes** | byte-identical. |
| `probe_lp_interface.py` | not re-run here | owned by another session this round and regenerated in `9cf779a3`; its own docstring declares the artefact non-byte-reproducible because B, C and E record wall-clock costs. |

Three things worth naming out of that table rather than leaving in it.

1. **Two artefacts carry an internal hash over their deterministic fields and both
   reproduce it** — `growth_curve.json`'s `stable_sha256` and
   `enumeration_probe.json`'s `deterministic_sha256`. That is the right shape:
   the file is not byte-stable, and it says exactly which subset is, and that
   subset is checkable in one line. `crux_quotient_settles.json` and
   `probe_answer_key.json` have no such field and are the two whose timing churn
   is load-bearing elsewhere, which is where it would be worth adding.
2. **`crux_quotient_settles.json` reproduced byte-for-byte on the first re-run and
   then differed on each of three consecutive re-runs taken after a 1.5 GB memory
   sweep on the same machine.** All seven differing leaves are timings. The
   artefact is not byte-reproducible; it merely looked it while the machine was
   idle. Anyone auditing this by one re-run can get either answer.
3. **`enumeration_sweep.json`'s non-reproduction is not the rung count.** The
   findings list above records "3 rungs against 4"; re-run here it produced 4 rungs
   at the same four targets — 200,000 / 1,000,000 / 3,000,000 / 10,000,000 — so
   that particular symptom did not recur. What does not reproduce is every derived
   number, and `implied_years` moving 229.51 → 332.32 on one re-run is a stronger
   statement of the same point than a missing rung: the file is machine-dependent
   in its conclusions, not just in its coverage. No audited claim rests on it.

### `MANIFEST.json`

Required fields present and unchanged: `prompt_id`, `branch`, `base_commit`
(`415556f8`), `utc`. Of the 23 `files[].sha256` entries, **17 matched the file on
disk and 6 did not** — `CRITERION.md`, `RUN_STATE.md`, `probe_answer_key.json`,
`probe_lp_interface.json`, `probe_lp_interface.py` and
`repro_duplicate_switch.py`. Every one of the six has a commit later than the
manifest's own last commit (`1486875e`): the artefacts moved in `722b6e8e`,
`b43427f0` and `9cf779a3`, the documents in `08820583` and after. So the
manifest was not wrong when written; it was never re-stamped, which for a
provenance file is the same defect one step removed.

All 23 recomputed, and two tracked files the manifest never listed are now listed:
`adversarial/review-round3.md` and `adversarial/round5-findings.md`, both cited as
evidence by this document. 25 entries, all matching. The one tracked file in this
directory still deliberately unlisted is `BASELINE-cycle94.md`, which belongs to a
different concurrent session's cycle log and is not an artefact of this run; the
manifest's `note` says so rather than leaving it as a silent omission.

The `note` also now states what the field is *for*, because that was the confusion
underneath the six mismatches: a whole-file sha pins the bytes that were published,
which is worth having even for a file that cannot regenerate. It is not a
reproducibility check, and reading it as one turns the reproduction table above into
five false alarms. What it does require is re-stamping in every commit that touches
a listed file. Two artefacts here avoid the problem with an internal hash over
their declared stable subset; the manifest cannot, so it is stamped last.

**Known limitation, stated rather than hidden:** `CRITERION.md`,
`probe_lp_interface.json` and `probe_lp_interface.py` are being edited by other
sessions in this same round, so their entries were true when written and may be
stale by the time this lands. That is the same failure as the six above, one round
later, and the only real fix is a stamp step in the commit path rather than a
person remembering.

### What in this file is still not verifiable from any artefact

Asked for explicitly, and larger than round five's list, because a claim can be
unsourced without being wrong.

* **The wall-clock reruns**, all of them: 153.24 s and 143.786 s for the growth
  ladder, 2.918 s for k≤6, 3.66 and 3.13 ms for `check_certificate` (3.06 is in the
  artefact; these two are not), and 0.0048-0.0051 s for ii3's
  `compute_lower_bound`. Every one exists only in prose in this file or in an
  adversarial report.
  They are kept because what they jointly establish — a spread of roughly 25% on
  one machine — is exactly the claim that no single wall-clock figure is a property
  of an artefact. But not one of them is in a committed `.json`.
* **"758 of 1024", "28,188 of 2^15", "32 of 32"** in the D-EX-029 paragraph, and
  the m = 10 / m = 40 the prose reports where a reconstruction of the removed loop
  gives m = 11 / m = 44. Labelled UNVERIFIABLE in `08820583` and still are: the
  loop that produced them is not committed.
* **"137 commands against a budget of 99"** for the straddle board, same paragraph,
  same status — no artefact emits it.
* **"465 passed, 2 xfailed" and the 456/2 baseline**, and the `verify.py` GREEN
  claims. Reproducible by running the suite, but nothing in this directory records
  them, and the count has since moved to 470/2 in `08820583`'s message. A run
  document that states a test count should emit it.
* **"24 absolute worktree paths" in `build_manifest.json`**, and "most of the churn
  is not mine" — a diff observation, not an artefact.
* **`0.01 s` for the 6,480-state control** in "what the review would have caught".
  It comes from `exam/tests/test_verdict.py`'s docstring, which is prose in a
  tracked file rather than a measurement; the assertions beside it (`6480`,
  `m == 4`, `lower_bound == 16`) are real.
* **"2654 states (t3-full-house)"** for the worldgen catalogue ceiling is in
  `DRILL.json`'s `classes_absent_because` — sourced, but in an artefact this
  branch deliberately does not regenerate, so it is sourced to a file that no
  longer matches its own generator. Named in "One thing deliberately NOT
  regenerated" above; repeated here because it belongs on this list too.
* **The `~4e36` / `~6e36` corridor-60 edge count** rests on carrying a measured
  ×4.0 scaling 50 rungs past the last measured one. The multiplicands are in
  `probe_lp_interface.json`'s `E_comb`; the extrapolation is not measured and is
  labelled as such in `CRITERION.md`.

### State

`repro_duplicate_switch.json` regenerated from its edited generator; the only leaf
that moved is the one this session rewrote. No other artefact in this directory was
left changed by the reproduction sweep. `probe_lp_interface.*`,
`exam/papers/verdict.py`, `exam/DECISIONS.md` and `CRITERION.md` were edited by
other sessions in the same round and are cited here by symbol or key name, never by
line number, for the reason this section keeps having to record.

## Round six — six findings, and the one that mattered was in this document

`adversarial/round6-findings.md`. Round six audited *the round-five fixes*, which
is the right target in a ticket where round three's corrections were wrong, round
four's fix became round five's CRITICAL, and round four withdrew a finding that
was correct.

**F6-1 (HIGH), fixed.** `CRITERION.md` described the A2 measurement as **five**
levels, **51,164** transitions, **12,791** states. The shipped artefact emits
**nine**, **51,880**, **12,970**. The stale figures are exactly the sums over the
first five rows of `a2_levels` — the artefact's state before `9cf779a3` added four
geometries. The paragraph carrying them was written in `824b9fb4`, a **later**
commit, so this is not lag: it described the world as it had been, after it had
changed. `RUN_STATE.md` had the right numbers throughout, so two documents of one
run disagreed about a measurement neither produced. Corrected in place, with the
correction stated rather than silently overwritten.

**F6-2 (MED-HIGH), fixed.** `a2_thin_coverage` — round five's weakest fix, and the
one I asked round six to attack hardest — is *correct*, but `CRITERION.md` never
mentioned it and stated unqualified the two claims it exists to qualify. The
artefact qualified its own numbers and the prose describing the artefact did not.
The qualification is now in the document beside the numbers.

**F6-4 (MED-HIGH), fixed.** `e4b25676` widened the criterion-(b) probe to all
seven records, and **three descriptions of it stayed at four**: the map row, the
ruling section, and this file's own F5-14 bullet, which still read "Left open on
purpose … Not done here". One fix, three descriptions left behind — the same shape
as the finding they describe.

**F6-3 (MED), fixed.** `D_verdict.how` said the corridor sweep gives "4x the latch
bits"; the same file's `a2_levels` shows 4 → 6 → 8 → 10, i.e. **2.5×**. The only
4× in sight is the *shipped* board's 40 bits, which is the thing that was never
enumerated. A ratio nobody recomputed, printed next to the numbers it was a ratio
of. Fixed in the generator and regenerated; the structural diff is the `how`
string and the wall-clock fields, nothing else.

**F6-5 (MED), reverted — my correction was the error.** I had conceded that "only
the *label* `n_pos=5` was wrong". `potential.py` does `n = int(graph["n_pos"])`
and builds each row as `[0.0] * (2 * n)`, so `n_pos` **is** the LP row width and
the original wording was right. Three files still carrying it (`exam/DECISIONS.md`,
`exam/STATUS.md`, `invariant_path_probe.md`) are correct and must not be brought
into line. This is the third correction on one sentence, and the second in the
wrong direction.

**F6-6 (LOW), reason corrected, decision kept.** `e4b25676`'s message argued the
`coverage` block had to sit **inside** the stable hash or "F5-14 could recur — a
row silently dropped — without the hash noticing". `items` has been inside the
hash since the artefact's first version, so both named failure modes move it
either way; round six demonstrated this by recomputing over `deterministic` minus
`coverage`. The decision stands on a different footing — an aggregate should be
pinned with the rows it aggregates, and `criterion_b_records_expected` is a
constant living nowhere else in the hashed subset. Recorded here because **the
commit message is published and cannot be edited**: the argument in it is not the
argument that supports it.

### What round six could not break

Seven load-bearing claims held, and this is a result rather than an absence of
one. `a2_thin_coverage`'s content matches the code exactly and both its factual
claims are true; it is **stronger than I credited it**, because `bits >= 0` holds
identically given the loop's own assertions, so no sample size could produce the
−1 that would matter — the thin coverage cannot touch the conclusion, and the
monotonicity hedge is a property of the code, not a hand-wave. The probe does call
`V.build()` with the test's exact predicate, with no hardcoded list surviving.
`no_solution_inside_cap` is genuinely independent — `enumerate_states` has no early
return on a solution, demonstrated with a solvable board that returns
`truncated=True` *and* a solution — and iii6/7/8's witnesses are 416 long against a
200,000 cap. Every key present in the old i1-i5/ii1-ii4 rows has an identical
value (the rows gained 8 keys, so "byte-identical **rows**" was loose; "byte-identical
**numbers**" is exact — recorded because I wrote the loose form). `deterministic_sha256`
reproduced byte-identically on re-run. **F5-13 was correctly left standing**: all
seven shipped records still carry `enumeration_attempted: false` / `truncated:
null`, so I did not under-close it. And the manifest's 25 entries were
independently recomputed at 0 mismatches — which matters because the previous
round's 0-mismatch report was *self*-verified.

### The manifest is now stamped by a script, not by hand (cycle 106)

The session that dispositioned round six died before committing, and what it
left behind included one omission of exactly the kind round five had already
found once: `adversarial/round6-findings.md` was written, tracked, and **not in
`MANIFEST.json`**. Round five's version of this was six stale hashes; both have
the same cause, which is that the manifest was maintained by hand across six
rounds while the directory kept moving.

So the hand maintenance is retired. `restamp_manifest.py` regenerates the
`files` block from the directory's own bytes and carries the two exclusions in
code rather than in prose — `__pycache__` and `BASELINE-cycle94.md`, both of
which the manifest's `note` already named. `--check` exits non-zero and prints
`UNLISTED` / `ABSENT` / `STALE` per path, so the next round asks the question in
one command instead of recomputing 26 hashes by hand and trusting the count.

Metadata keys are read from the existing manifest and written back unchanged:
the script re-stamps, it does not author. That boundary matters — `note`,
`base_commit` and `prompt_id` are claims a human made and a script has no
standing to regenerate them.

### The manifest was verified against the wrong bytes, six times (cycle 106)

The commit immediately above this section says "Manifest 26 entries, 0
mismatches, recomputed by the script rather than by the round that wrote it."
That count is real and it was computed over the **working copy**. Two of the 26
files — `CRITERION.md` and `RUN_STATE.md` — carried CRLF on disk, and every blob
under `exam/` is LF, because `exam/.gitattributes` pins `* text eol=lf`. So for
those two the manifest's sha256 was not the sha256 of the bytes at the commit
carrying it, which is precisely what the manifest's own `note` says it is. The
correction is appended rather than substituted: the message is published and
cannot be edited, and this is the run's third instance of a claim whose own
artefact refutes it.

**Why nothing saw it.** `git diff` on those two files was *empty*. Check-in
normalisation converts a CRLF working copy back to LF on the way into the index,
so git reports the file unchanged while the bytes a hasher reads are 737 and 769
bytes longer than the bytes git stores. `git status` said `M` and `git diff
--numstat` said nothing, which is the signature. Round five's audit of this
manifest — "17 of the then 23 entries matched and 6 did not" — hashed the
working copy too, so its 17 is a number about this machine's checkout rather
than about the repository. That does not overturn round five's six findings:
all six were files a later commit had genuinely moved without re-stamping, and
they reproduce against the index. It does mean the *method* was wrong in a
direction that could only ever hide mismatches, never invent them.

**Scope, measured rather than assumed.** Four tracked files under `exam/` had
CRLF working copies: `exam/DECISIONS.md`, `exam/STATUS.md`, and this run's
`CRITERION.md` and `RUN_STATE.md` — all four edited by this run, all four by a
tool that writes native line endings. `.gitattributes` governs checkout and
check-in; it does not govern what a program writes to a file afterwards, and
nothing in this repository was watching that gap. All four are normalised.

**Three fixes, one of them a negative control.** `restamp_manifest.py` now
refuses to stamp a file whose working copy contains CRLF, with the reason in the
exception rather than in a comment — hashing the disk is only correct while disk
and index coincide, so the coincidence is asserted instead of assumed.
`exam/tests/test_run_manifest_v23.py` asserts the three-way agreement of stamp,
disk and index (two-way against the index alone passes with an unstaged edit
sitting in the working copy; two-way against the disk alone is the bug being
fixed), that no tracked file under `exam/` carries CRLF, and — the control —
that the guard actually raises on CRLF input and stays quiet on LF. A guard
nobody has watched fire is not a guard.

**Not fixed here, and it is somebody's ticket already.** The same measurement
run across all 13 `exam/runs/*/MANIFEST.json` against published bytes rather
than the working copy (`_survey_manifests.py`, in this directory) finds **36
stale hashes in 8 of 13 manifests**, plus 50 tracked files listed in no
manifest. Two path conventions are in use — some manifests are relative to their
own run directory, others to the repo root — which is why the first version of
that script reported nearly every entry as absent, and why no cross-run checker
existed before. A large share of the 36 are entries pinning files *outside* the
run directory (`exam/leakage.py`, `exam/STATUS.md`, `exam/artifacts/leakage.json`),
which later runs edit by design: **a manifest that pins shared sources is
guaranteed to rot, and that is a design question rather than a defect.** The
rest are runs' own artefacts moving after their stamp, which is the defect.
Both belong to `V2-V25-verify-does-not-check-what-is-committed`, whose subject
is the same sentence one level up — a check that runs, goes green, and is not
measuring what its name claims.

### The claim that round five survives is now a measurement, not an argument

The section above argues that hashing the working copy "could only ever hide
mismatches, never invent them", and concludes round five's six findings survive.
That is a valid argument and it was not a measurement, which is the exact
failure mode this ticket has now produced four times. So it was measured.

`verify_round5_against_index.py` checks a manifest against the blobs in its own
commit's tree — no working copy participates at any point — and splits a
mismatch two ways: **stale** (neither the blob nor its all-CRLF form matches, so
the artefact really moved) versus **eol-only** (the all-CRLF form matches, so the
content was correct and the stamp was taken from a Windows working copy). The
two call for opposite fixes, which is why the distinction is in the tool rather
than in the prose.

| commit | entries | matched | stale | eol-only |
|---|---|---|---|---|
| `b43427f0` round five's audit point | 23 | 17 | **6** | 0 |
| `9cf779a3` | 23 | 17 | 6 | 0 |
| `824b9fb4` | 23 | 17 | 6 | 0 |
| `a29e3dc0` round five's fixes land | 25 | 23 | 0 | **2** |
| `e4b25676` | 25 | 23 | 0 | 2 |
| `1e083de2` "26 entries, 0 mismatches" | 26 | 24 | 1 | 1 |
| `0a9e5865` cycle 107's fix | 26 | **26** | 0 | 0 |
| `34f0cc42` | 31 | 31 | 0 | 0 |

Three things fall out, and two of them are worse than what was claimed.

**Round five reproduces exactly.** 17 matched, 6 mismatched, and all six are
*stale* rather than eol-only — real content drift, in the same six files it
named. Its numbers were right about the repository and not merely about a
checkout, which is more than the argument was entitled to conclude.

**The defect outlived its own fix by three commits.** At `a29e3dc0` and
`e4b25676` the manifest was believed re-stamped and clean, and it was clean *in
content* — 0 stale — while two entries were still hashes of a Windows working
copy. Two commits shipped with a manifest whose author had just verified it. The
audit that verified it used the method that cannot see this, so the audit and
the defect were the same blind spot pointing at each other.

**`0a9e5865` is the first commit in this run's history at which the manifest
matches the bytes git publishes.** Twelve commits touched this directory before
it. The run has been carrying a wrong provenance record since its second commit.

One entry is labelled honestly rather than confidently: at `1e083de2`
`RUN_STATE.md` is `stale` by the tool's rule, meaning neither the blob nor its
all-CRLF form matches. The likely cause is a file written in two passes by tools
that disagree about line endings — round six edited the body while the new
section was appended with LF — leaving mixed endings on disk that no uniform
conversion reproduces. That is a reconstruction and it is **not proven**: the
disk bytes of that moment are gone, and an attempt to rebuild them from the two
neighbouring blobs failed because the body changed as well as the tail. It is
recorded as unproven rather than dropped, because a manifest entry matching no
form of its own file is the more alarming reading and should not be quietly
replaced by the comfortable one.
