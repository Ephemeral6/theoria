# The adversarial round overturned the rewrite's headline

Three reviewers were run against the first draft of this rewrite: a lay reader
under the same no-lookups instruction as the P12 round, an adversarial
fact-checker instructed to find a false statement by opening every artefact, and a
hostile referee instructed to argue that the rewrite made the paper worse. The
fact-checker and the referee **converged independently on the same six defects**,
and they were right. Every one is corrected in the delivered text. Recording them
because the correction is more informative than the draft was.

## The six

1. **The blind round did not take the main table to zero — it took it to two.**
   The last two went to a *sighted* adversarial review
   (`battery/audit/v9/attacks/a7_review.py`, whose own docstring says it is not
   blind) plus `M3`'s retier to `undetermined`. The abstract, §1.2's blockquote and
   §10.5 all credited the blind round with the whole drop. Fixed in all three.
2. **"They wrote 112 attacks, of which 95 landed" was not the blind six's work.**
   They wrote 105, of which 91 landed; the sighted follow-up added 7 more, 4
   landing (`battery/STATUS.md`; `battery/audit/v9/REPORT.md` §9). Fixed.
3. **"moves every one of those numbers further in the same direction" was
   literally false.** Only 34 → 37 moves; there is no blind-round counterpart to
   the 17 contradicted entries or the 14 defence claims — `disagreements_with_b14`
   is 9 and is a different quantity. Removed.
4. **The blind round's pre-registration was breached and the rewrite did not say
   so.** `battery/PREREG_V9.md` revision 1: the adjudication implementation was not
   in the pre-registered commit, and its `NOT defended` clause was collapsed *after
   the results were seen*, in the direction that emptied the table — the file calls
   this the round's worst lapse. The first draft had built a new sentence claiming
   A0's seal was the weaker of the two orderings. That sentence is replaced by one
   saying both fail, differently, and that neither is offered as the standard the
   other should have met.
5. **The poverty certificate rejected nothing.** 105 of 105 passed, so it has zero
   demonstrated selectivity on this data set, and it is written by the round's own
   aggregator — so "an independent poverty certificate had judged to have done no
   real work" was wrong twice (`battery/audit/v9/REPORT.md` §7). Now a stated limit
   rather than a cited control.
6. **"nineteen of the twenty" is eighteen.** `K12` is now refused by the very
   defence §7.7 says was implemented; the referee reproduced `omnibus_manual()` and
   counted 18. Fixed in §1.2, with a note that §7.7 still says nineteen.

## Smaller corrections from the same round

* The first round's numbers are read from a **frozen** artefact; re-running the
  same code today gives 33 landing and 19 contradicted
  (`battery/runs/20260729T025515Z-V18-battery-prereg-check/recompute/gaming_audit.json`).
  §1.2 now says so, and names §7.1's "artefacts regenerate on demand" as no longer
  true of that file.
* `E2`'s 0.993 exists only in `battery/REPORT_V2.md` prose, not in
  `battery/artifacts/`. Now attributed there.
* The consequence of the empty main table belongs to `E2`, the front-load index —
  not to `M3`, which carries a different claim.
* "the three pairs R-05 named" is not verbatim in `A0_REPORT.md` §2; that report
  makes the same gloss in different words. Corrected.
* **"the strongest published result"** contradicted §11.1, which spends a paragraph
  establishing that the result is on a project page, self-reported, with no venue,
  no DOI and no released harness. Now "strongest reported result", with the
  qualification carried in §1.1.
* Printing "98.98 %" and then saying the sources "give no denominator" was
  self-contradicting — a percent sign is a denominator. Rewritten to say what is
  actually missing: the composition of the set it was scored on.
* The $6.32 figure has a $5.80 companion, and the manifest itself records the
  8.3 % disagreement. Both now in the abstract.
* §1.6 cited A2's report as authority for A3. Now cites A3's own, which is stricter
  than the paper was ("the unit under test is a level, not a game").
* Six named beats followed by "8 beats" was a reading trap. The six are `L1`–`L6`;
  the other two build the exhibit. Said in both the abstract and §1.5.

## Two class fixes, created or exposed by this rewrite

* **§2.5 said "It reports no play."** True while the live run "spent nothing";
  false once the abstract says seven actions and $6.32. Rewritten to "no play *by
  the framework*", with the two live runs named — and §8 and §9 added to its
  enumeration, which had omitted them.
* **§9's title, opening and §9.3 heading still fused the two live runs** after
  §9.4 had been un-fused in the first pass. All four now name which run they mean.
  This is the exact failure mode the P12 round criticised: fixing only where the
  reviewer pointed.

## What the lay reader still says is broken

The lay reviewer scored the rewrite **4/10**, up from an implied 2, and confirmed
acceptance-test items 1, 2 and 3 as fixed — ARC-AGI-3 defined, the game/world
convention declared ("the best-written passage in either file"), the five arms
enumerated with counts, `K2`/`K4` glossed where used.

**Item 4 — "I cannot state the paper's claim" — they still report as broken**, now
as three candidate claims that pull against each other (a measurement paper, an
epistemics paper, a systems paper). The abstract's claim sentence was added in
response and §10.5's matches it, but the reviewer read the draft *before* that fix,
so it is untested. **This is the first thing the next reviewer should be asked.**

Their sharpest unactioned observation: §1's rhythm is now four small retractions
instead of one long one — every subsection ends by undercutting itself, which
trains a reader to discount each claim on arrival. The disclosures are correct and
belong in the paper; the finding is that they should not all be in §1. Fixing that
means moving material out of §1 into §10, which is a different item.

Also still open, all theirs: roughly 15 terms used before explanation (`decide`,
pagoda, DC22, `#print axioms`, process-4, examination instrument / leak / probes /
"sat", Schema, scorecard, the bare metric ids); disclaimers are ~35 % of the
abstract; the draft-status block still precedes the abstract; and the paper never
answers "why should a reader who will never use this battery care?", which is the
question contribution 1 now has to survive.

## Follow-up items this run should generate

1. **§7.7 must be re-derived against the blind round.** It reports 34/17/main-9
   under a heading saying the table "moved twice"; it moved three times. §7.2a's
   "the main table holds nine metrics" is present-tense and now false. §7.9's
   punchline — that the published main table contains a metric the battery already
   retired — is void if the table is empty. §7.10's gap list is pre-blind-round.
   This is the largest inconsistency left in the paper, and this item deliberately
   did not fix it: it is a battery-section rewrite, and §7.8–§7.10 must be
   re-derived with it.
2. **`OPEN_ITEMS.md` C1 is now closed** ("§3.3's body is honest; the abstract is
   not") and was not updated; `PROVENANCE.md` carries no row for the blind round.
3. **`verify_paper.py` mutates the tree it verifies** — it rewrote the tracked file
   `figures/fig1_concept_timeline.txt` under this run, because the committed
   payload is stale. Belongs to the figures item, together with the standing
   C FIGDATA failure.
