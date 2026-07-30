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

## Filed, not fixed

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
