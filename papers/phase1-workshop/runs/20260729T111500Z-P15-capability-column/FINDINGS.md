# P15 — findings

Written incrementally.

## Task 3 — "verify P14's ruling actually reached the text": nothing to change, and the item's premise is expired

The work order states the ruling as unconditional — until a held-out validation
item lands, every "verified" in the body must read *self-consistent on the
observed evidence* — and asks me to confirm the eight sites in `PAPER.md` were
really changed, on the principle that **an archived work order is not a changed
text**. That principle is right. This is not an instance of it.

**The sweep was deliberately not run, and the refusal is published in the paper
rather than filed in a run directory.** `sections/10_adjudication.md` §10.6 carries
it, with the eight-way breakdown a reader can check without ever opening `runs/`:
one occurrence is about a *third party's* model, three name a certificate's own
`verified` field in sentences whose whole point is that the consuming side refuses
to trust it, one is the pile digest, and three are in §12 — one of which is the
sentence "no claim is made to have verified any engine". **None of the eight is a
claim to have verified an engine.** 已验证 appears nowhere in the body outside that
paragraph.

Two things checked independently rather than accepted:

* **The condition is partly discharged.** E17 has landed, for two of eight engine
  rows, so the blanket form of the ruling is obsolete on its own terms. A
  find-and-replace would have corrupted correct sentences and changed nothing that
  needed changing.
* **The rule is machine-enforced where it belongs** — on the engine table, not in
  the paper's prose. `engine-rig/tests/test_engine_table.py` asserts the published
  rule text contains `may not say 「已验证」`, and asserts as a strict iff that a row
  claims held-out validation exactly when its engine is one of the two that has it.
  The rule is a test, not a promise.

**So task 3's honest outcome is a confirmation, not an edit**, and it is worth as
much as an edit would have been: the failure class the item hunts — order
archived, text unchanged — did not occur, because the *non-execution* was itself
shipped and reasoned in the paper.

One borderline the check surfaced, left alone and recorded: `sections/05_a2.md`
says "The isomorphism is machine-checked, clause by clause". Every row of the table
under it names its artefact, so the sentence is true — but one row is a Lean proof
and the others are artefact comparisons, and a reader could hear "machine-checked"
as "Lean-proved" for all of them. It is the strongest verb in the paper attached to
a non-proof object. Outside this item and defensible as written; flagged so a later
pass rules on it deliberately rather than inheriting it.

## Task 1 — the capability column: the item's framing is wrong twice, and the corrected version is stronger

**There is no capability column.** No table in `PAPER.md`, in any of the thirteen
sections, or in `PROVENANCE.md` / `REVIEW.md` / `OUTLINE.md` has a capability,
levels, solved, win-rate or success-rate column. The item's task 1 — "change that
column into what it truly is" — has no referent. The design's main table is
`Theoria.md` §1.12's bet table, and this paper does not reproduce it.

**The zero is real and much better evidenced than the audit's say-so.** Across 41
baseline cells, 32 closed scorecards and 939 successful actions on four games,
`levels_completed` is 0 in every record. Four API-side signals agree independently,
including a per-level action histogram that places every action of every run at
index 0. Three non-zero values exist in the whole tree; all three are the ablation
arm's self-built offline worlds — `game_id` `a0-base` / `a2-base` /
`a2-charitable`, `card_id` null, `score` null — disqualified by their own records.
Verified by hand, not inherited.

**But "this quantity has no signal" is the wrong sentence, and the source says so.**
`BUDGET_REPORT.md` §12.2 carries a qualifier the work order's paraphrase drops:
「**在 30 动作预算下**任何重复数都不能让它变得可比」 — *under a 30-action budget*.
The next clause prescribes the remedy: raise the budget if Phase 4 wants capability
rather than economics. The arithmetic is in the A3 level-boundary run: `g50t`'s
first level takes 78 successful actions against a per-cell budget of 30. **The
column is not a measurement that came back empty; it is one that was never
affordable.** That is what §7.10a now says, with `envelope.json`'s
`pooled_cv.levels_completed: null` as the machine-readable witness.

## The contrast the item asked for is refused, and the refusal is the finding

The item asks me to point at the bill-shape column and say it has signal where
capability does not. **It does not, and writing it would have traded one overclaim
for another.**

* At the raw level the bill shape is a null: E2's median over 67 `bare_cc` runs is
  0.229 against a construction null of exactly 0.250, with 53 of the 67 below it.
* Across arms it is not weak but *undefined*: E2's process-1 verdict is `no-data`
  with **zero** pairs, the corpus recording no cost on the other side.
* The one place E2 separates, it separates **by model tier within one arm** — a
  capability gradient, which is precisely the confound §7.8 already registers as
  the thing to break before Phase 4.
* E5, the other candidate, is disqualified twice over: its action count includes
  the RESET, and its declared direction is inverted with a "do not use until
  resolved" warning on the artefact.
* And the paper currently *disclaims* cross-arm cost. Adding a bill-shape claim
  would introduce a cost claim §11 says this paper does not make.

Both columns are honest nulls. The reportable difference is that the bill shape's
null rests on 67 runs and the capability column's rests on none. §7.10a says that
and stops.

## One flat contradiction fixed

§7.2 explained X3's backwards separation by quoting `REPORT_V2.md`: "an arm that
keeps clearing levels finds new states late". **That explanation requires a
level-completion gradient this corpus does not contain**, and it sat about 1 600
lines from §11.2's statement that nothing ever completed a level. The quotation is
kept — the report did say it — and the paper now says why it cannot be the
explanation here. X2, which §7.2 attributes to the same mechanism, inherits the
same objection.

Also added: a row to §7.10's gap table. The table had a row about missing ground
truth and none saying no run in the corpus ever completed a level, which was the
gap the section had been assuming away.

## Task 4 — the adversarial pass, which took my own new section apart

The item asks for a hostile reviewer whose remedy is **deletion, not softening**.
It found more in my own edits than in the pre-existing text, which is the right
outcome for a pass run on fresh writing. Everything below is verified and applied.

**Three sentences deleted outright.**

1. **My X3 rebuttal.** I had written that `REPORT_V2.md`'s explanation of X3's
   backwards sign "cannot be right here" because no run ever cleared a level. Two
   problems: the sign comes from `schema_repro`, whose traces are gitignored and
   which this repository cannot inspect — so I asserted a fact about the one arm
   nobody here can check — and the report's operative mechanism is long walks
   versus early death, which needs no level completion at all. **The correction was
   a larger overclaim than the thing it corrected, and it was set in bold.** Gone;
   the finding it was attached to stands undamaged.
2. **"`state: \"WIN\"` has never appeared … the single non-`NOT_FINISHED`
   observation in ~1 400 rows is a `GAME_OVER`."** Neither half reproduces from
   this tree: no tracked `.jsonl` contains `GAME_OVER`, and the available row
   counts are 560, 1 987 and 1 949. It was the sentence a referee checks first.
3. **"Both columns are honest nulls."** It contradicted my own paragraph three
   lines above — an unpurchased measurement is not a null — and was false about E2
   besides. Its only contribution was a pleasing symmetry manufactured from two
   mischaracterisations.

**Two claims I had to correct rather than cut.**

* **"At the raw level the bill shape is a null" was wrong in the cautious
  direction.** 53 of 67 below a *fixed* construction null is p ≈ 1.8 × 10⁻⁶ — a
  real departure from flat, in the **back-loaded** direction, which is the opposite
  of the front-loading signature C2 predicts. Under-claiming is still misreporting,
  and this one hid a result pointing against the design's own story.
* **"The bill shape will not carry the contrast" was refuted by my own §7.2 table**
  500 lines up: **E4** separates the specified gradient at δ = −0.875 over four
  paired games with its direction holding, and §7.3 spends a paragraph insisting it
  did not collapse. The claim is now scoped to the *cost* shape, E2 and E3.

**And the first paragraph of §7.10a carried no artefact path at all** — six
quantities, zero citations, in the paper whose binding rule is that a number
without a path does not go in. `verify_paper.py` passes 4/4 because it only checks
that cited paths *resolve*; it cannot see a claim that cites nothing. Two of those
six numbers did not reproduce either: "41 baseline cells" and "939 successful
actions" against 33 cells and 546 actions in the tracked records. Rewritten around
what is citable — `ledger.jsonl`'s 560 rows, and the live run's own scorecard
payload — and the four fields are now described as four views of one object rather
than four independent signals, which is what they are.

**The gap row I added to §7.10 was falsified on its own terms.** I wrote that the
metrics ranking arms by achievement "have no achievement to rank"; the battery
reads `a2-refutation`, a self-built world where P4 returns 1.0 with `won: true`,
18 actions against an optimal of 18. The row now names that exception, which is
more informative than the blanket was: the one run in the corpus that reaches a
goal is one nobody played.

**§9.4 understated its own explanation.** I wrote that cache-TTL mispricing
"accounts for part of the gap, not all of it". It accounts for **83.6 %**, taking
the disagreement from 8.3 % to 1.35 %, and the diagnosis is in *this run's own*
manifest rather than a sibling's. "Part, not all" reads as a minority contributor
and it is five-sixths, already located and priced. The abstract inherited the same
error as "recording the disagreement rather than resolving it"; both corrected.

**The pattern worth keeping.** Of the eight defects, six are in text I wrote today
and five of those overclaim in the *modest* direction — understating an
explanation, calling a signal a null, refusing a contrast more broadly than the
evidence requires. Modest overclaims survive review, because a reviewer reads
caution as diligence. That is the failure mode a hostile pass on one's own fresh
prose is actually for.
