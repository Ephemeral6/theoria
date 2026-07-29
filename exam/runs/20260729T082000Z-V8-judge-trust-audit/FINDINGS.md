# V8 — is the marker itself trustworthy?

Four questions, three independent examiners, one worktree each so that the
`verdict.build()` race V7 documented could not make them collide. Zero API spend,
zero network, zero sealed-pile contact.

Coverage: **five papers, 217 items, 362 points** — `heldout`, `handover`,
`adaptation`, `verdict`, and `handover_auto`.

**What is new here, stated narrowly, because the first draft overclaimed it.**
V7 already ran a silence set against the four hand-built papers — its §4b is
where `[]` → 6.500/144 and `"unsolvable"` → 9.000/34 come from — and this run
does not discover that. What is new is the *item-level* work: per-item
discrimination on the hand-built papers (V7's instrument only ever ran on
worldgen), the verdict paper's sensitivity and specificity reported apart, a
wider token sweep, and two payment mechanisms V7 did not find.

## The clean results, first, because they are the load-bearing ones

* **The marker never underpays its own ground truth.** Oracle scores exactly
  `possible` on all five papers — 80/80, 46/46, 144/144, 34/34, 58/58 — every
  item `correct`, no item missing from `reference_answers`.
* **Zero dead items in 217.** Not one item is failed by everybody including the
  oracle. V7 found 0 in 236 worldgen items; that now holds across all four
  question types.
* **`heldout`, `handover` and `handover_auto` pay nothing for silence.** **59**
  spellings of "says nothing" — `[]`, `{}`, `None`, `0`, `False`, `"unsolvable"`,
  `"n/a"`, whitespace, `[[]]`, and every other variant three examiners could
  invent — score **0.000** on those three papers. (The first draft said "roughly
  160", which was 59 × 3 papers counted as tokens. The sweep also passes a list
  where it labels a tuple, so `()` — which *does* pay on adaptation — was never
  actually run against these three.)
* **On the verdict paper the marker is symmetric.** Sensitivity 1.000 and
  specificity 1.000 for both classes it can measure: all 9 true-unsolvable items
  paid when answered `unsolvable` and all 8 true-solvable refused, and the mirror.
  The false-positive trap holds completely, and **0 of 32** certificates built
  from the level blob were accepted on a solvable level. Strengthening the bluff
  with sheet-only material — `unsolvable` + `reason: exhaustive_search` — reaches
  **11.000/34**. *(The first draft quoted 18.000/34 here and called it
  "constructible from the sheet". It is not: that run hands the key's own
  certificate to the nine unsolvable items, so it is what an examinee holding the
  answers scores. The correction matters in the audit's favour — the trap holds
  at a lower bluff ceiling than claimed — but the claim as written was false, and
  it was false in the section headed "the load-bearing ones".)*

Those are worth stating plainly because everything below is a defect, and a
defect list reads as an indictment unless the acquittals are on the same page.

## 1 · Two new hard defects, both on the adaptation rubric, both paying full marks

V7 found `_read_set` paying `[]` 6.500 of 144. These are different mechanisms in
the same file. They are **not bigger** — together they move 1.000 of 144, and both
land on the single item `v-a0-03.detect.match`. What makes them worth leading
with is the shape, not the size: they award **full marks with verdict `correct`**,
where `_read_set` leaks fractions.

**The largest content-free payout in this run's own data is neither of them, and
the first draft omitted it**: the constant string `"unsolvable"` on every item
takes **12.000 of 144 (8.3 %)** on the adaptation paper, four items × 3.0 on
`adapt.collateral.v1`. V7 found that one; leaving it out of a section headed "the
new hard defects" made the new ones look like the worst ones.

**D-1 · A claimed detection with no index is paid as if it had asserted "never".**
`rubrics_adaptation.py:360` computes `fraction = _index_fraction(index if claimed
else None, truth_index)`. `_read_claim(True)` returns `(legible=True,
claimed=True, index=None)`. `grade_detect` passes `None` regardless, and
`_index_fraction:300-301` (`if truth is None: return 1.0 if said is None else
0.0`) cannot distinguish "asserted never" from "asserted a detection and named no
index". On `v-a0-03.detect.match` the answer `True` scores **1.000/1.000,
verdict `correct`** — while the same `ItemScore.detail` carries
`"false_alarm": true`. The module's own pre-registered contract at
`rubrics_adaptation.py:278-282` says false alarms "are NOT on this curve and never
earn anything". **The rubric flags the answer as a false alarm and pays it in
full, in the same object.**

**D-2 · An unparseable index inside a dict is silently converted into the
assertion "never".** `rubrics_adaptation.py:168-174`: a string index that fails
`int()` is set to `None`, and the next line returns `(True, bool(detected),
None)` — with `detected` absent, a legible *"the change was never detected"*. So
`{"index": "x"}` and `{"index": ""}` score **1.000/1.000 `correct`**. This is
precisely the failure `_read_claim`'s own docstring (`:122-138`) says it was
rewritten to prevent — *"a forgiving reader may not invent a claim the examinee
did not make"* — closed for bare illegible values and left open one level down,
inside the dict.

Three smaller ones beside them:

* **`()` pays 6.500 like `[]`**, because `_read_set` accepts tuples at `:204`.
  V7's `xfail(strict=True)` pins the list spelling only, so fixing what the test
  describes would leave the tuple paying.
* **`DETECTION_BANDS` is farmable.** `_index_fraction:304-308` pays 0.25 for any
  index within 8 of the truth. `0`, `-1`, `"0"`, `"-1"` all reach 1.000/144, and
  a bare constant **`18` everywhere pays 6.250/144** — no world model, no dict,
  no reading of anything.
* **A single boolean pays**: `{"exact_on_heldout": False}` scores **6.300/144**
  on `adapt.repair.v1`, `True` scores 4.500.

V7's grouping of `0` / `False` / `"None"` at 1.000 each is also shown to be a
coincidence of totals: they pay by **two different routes** (`_read_claim`'s
"never" alphabet, and `DETECTION_BANDS`), not one.

## 2 · A paper outside the registry — and a claim this run had to withdraw

`exam/papers/handover_auto.py` is a real paper module — `PAPER_ID
v11-handover-a0`, 31 items, 58 points, its own `build()` and
`reference_answers()` — and it is **not in `BUILDERS`**. The five things scoped to
that registry therefore do not reach it: `calibrate_all()`,
`mutant_battery_all()`, `fault_matrix()`, `build_papers.py` and
`discrimination.py`. V7 never mentions it. So every "all four papers" claim in
the exam's aggregate numbers is a claim about four of five, and the
zero-discrimination partition below is genuinely its first.

**But this run first wrote that as "a whole paper that nothing has ever
checked", and that is false.** `exam/tests/test_handover_auto.py` is 518 lines
and 34 passing tests which mark the oracle, null, memoriser and bluffer fakes and
assert exactly the calibration this section claimed to be doing for the first
time; `exam/tools/run_handover_auto.py` is a dedicated driver; the paper is in
`registry.all_rubrics()`; and
`exam/runs/20260728T202540Z-V11-handover-auto-r2/RESULTS.md` **published the
calibration table already — oracle 1.000, memoriser 0.553, bluffer 0.231** — where
0.231 is the number this run recomputed and presented as new. The probe script
that produced it says only "not in BUILDERS", correctly; the write-up inflated
that into "nothing". A gap in one registry is not an absence of coverage, and an
audit is the last document that should confuse the two.

## 3 · The verdict paper tilts toward impossibility, and silence costs more than being wrong

The work order's principle is that a framework that dares to say *unsolvable*
must be able to say nothing. The marker honours it; **the paper and the price
list do not.**

* **`abstain` has no ground truth — but this is not the finding the first draft
  made of it.** The paper's three *item* classes are `small_unsolvable` (5),
  `large_unsolvable` (4) and `solvable_hard` (8), and all three have ground truth.
  `abstain` is a member of `rubrics_verdict._ABSTAIN`, a refusal token on the
  answer side. Sokoban solvability is decidable, so no item *can* carry "abstain"
  as its truth: calling it "a class the instrument can never reward" dressed a
  logical necessity as a defect. What is true and worth keeping is the
  consequence for measurement — the answer-side triple cannot be scored as a
  three-way confusion matrix, because one of its rows is empty by construction.
* **The impossibility bluff outscores the possibility bluff.** Constant
  `unsolvable` takes **9.000/34**; constant `solvable` takes **8.000/34**. Same
  rubric, same absence of reasoning; the paper carries 9 unsolvable items against
  8 solvable at uniform weight. A 12.5 % relative edge, in exactly the direction
  the item says to guard. The same tilt sets the honest ceilings: an examinee that
  only ever proves impossibility correctly tops out at 18.000/34, its mirror at
  16.000/34.
* **Bluffing is a free option.** A wrong verdict and an abstention are both paid
  **0.000** — they differ only in the `verdict` label. Expected marginal gain of
  bluffing `unsolvable` over abstaining: **+0.529 per item**; downside:
  **0.000**. `rubrics_verdict.py:663` states the principle in words — *"a
  framework that will say 'unsolvable' has to be able to say nothing"* — and the
  price list twenty lines away makes silence and error cost the same *in points*.

  **The first draft went on to say the whole anti-bluffer defence rests on
  denominator dilution, and that is refuted by three mechanisms in the repo.**
  The two examinees are not distinguished "only by the `verdict` label": constant
  `unsolvable` yields `fp=8`, **specificity 0.000**; constant `abstain` yields
  specificity **null** with `abstained_on_negative=8` and
  `coverage_negative=0.0`, and both propagate into `verdict.axes()["confusion"]`,
  into `per_class_confusion` and into `mark()`'s counts. On top of that,
  `calibration.py::STRUCTURAL["verdict_bluffer_pair"]` pre-registers "sensitivity
  1.0 and specificity 0.0" as a *hard failure condition*, and the
  `("verdict","bluffer")` band is `Band(0.0, 0.50)` with the stated reason that
  "the score must reflect the pair, not the sensitivity". The defence exists and
  is pre-registered. The narrower claim that survives: **in the points the paper
  awards, a false impossibility claim and an abstention cost the same**, and the
  penalty lives entirely outside the score, in axes a reader has to go and look at.

  *(The +0.529 arithmetic also uses the truth mix, which an examinee cannot know;
  read it as a property of this paper, not as a strategy calculation available to
  a real candidate.)*

Also worth separating, because the repo currently blends them:
`confusion_matrix.py` measures the **examinee** (bluffer: sensitivity 1.000,
specificity 0.000) while the numbers above measure the **marker** (1.000 /
1.000). Both are true of the same run and they are not the same measurement.

## 4 · Zero-discrimination: smaller than on worldgen, and concentrated in one paper

**26 items / 28.0 points (7.7 % of points) are strictly zero-discrimination** —
all three voters awarded byte-identical points. A wider and more useful cut:
**54 items / 60.0 points (16.6 % of all points) hand full marks to a voter with
no world model.**

It is not spread evenly. `heldout` carries **45.0 % of its points** in
frame-unchanged items that the bluffer takes by echoing the input frame — and 18
of those 36 sit in the *held-out* split, the half that exists to do the
discriminating. `handover` gives away 32.6 %, `handover_auto` 15.5 %.
`adaptation` and `verdict` give away nothing.

`handover_auto`'s single largest giveaway by the shipped bluffer is
`v11-why-ce-01` (3.0 points, the paper's only counterexample item): the builder's
hardcoded bluff constant happens to be a *legal* counterexample, so the
all-or-nothing rubric pays it in full — and the memoriser abstains on it.

**Its 15.5 % is a floor, not a ceiling.** The constant string
`"action=none; plan_len=none"` on every item takes **4.000/58 at full marks with
verdict `correct`** on `v11-opt-01` and `v11-opt-04`, the paper's two dead boards,
where the shipped bluffer scores 0. A per-family constant therefore reaches
**9 items / 13.000 of 58 = 22.4 %**. The exam defends this deliberately —
`test_none_and_abstain_are_different_claims` holds that "none" is a claim rather
than silence — but by this run's own standard, which counts the string
`"unsolvable"` among the spellings of "says nothing", declaring every board dead
is the same move it prices at a free option on the verdict paper. Both cannot be
right, and the inconsistency is this run's, not the exam's.

**But the headline number for `adaptation` is a trap in the other direction.**
It reads 98.3 % `theory`, the best-looking paper in the set, while its memoriser
and bluffer land on exactly the same total, **24.600/144 each**. Read that
carefully, because the first draft read it too strongly: they are paid equally on
46 of 60 items, but **41 of those 46 are joint zeros**, and their paid item sets
differ (bluffer pays on 17 items, memoriser on 11). So it is not "the paper fails
to separate them across 46 items" — it is two different distributions whose totals
coincide. The point that survives is narrower and still worth having: a
score-level comparison of these two arms on this paper is uninformative, and the
four-class taxonomy cannot show that while the pairwise table can.

## 5 · The instrument that produced V7's headline does not transfer, and a test pins the artefact

Three findings about `exam/tools/discrimination.py` itself, which is the tool
behind V7's 41.1 %:

* **V7 §6's identity is a property of one builder, not of exams.** "`class` is
  exactly a function of `(split, frame_changes)`, zero violations in 236 items"
  holds on worldgen because the worldgen memoriser is a stasis predictor. On the
  hand-built `heldout` paper it fails: `(heldout, changed)` splits into 6
  `memorised` and 16 `theory`, and `(heldout, unchanged)` lands in a triple the
  identity has no cell for. *(The first draft added that
  `exam/tests/test_discrimination.py` "pins a worldgen artefact as though it were
  a property of the instrument". Withdrawn: that test iterates
  `port.world_ids()`, so it is scoped to exactly the catalogue the published claim
  is about, `discrimination.py:87-95` already says the tool does not measure
  difficulty, and the sibling test's docstring already invites its own deletion
  when the residue changes. The repo says the right thing in three places; the
  scope is correct and there is no defect here.)*
* **A fifth outcome triple is reachable and common.** `oracle=T, memoriser=F,
  bluffer=T` occurs on **32 of 217** items — the bluffer takes the mark and the
  memoriser ranks *below* a theory-free answer. `discrimination.py` treats that
  combination as impossible and its CLI exits 1 on any anomaly. It cannot
  actually be pointed at these papers — `profile_world` goes through
  `heldout_worldgen`, and the hand-built builders take no world argument — so the
  32 is a property of this run's re-implementation of `_classify`, and the finding
  is that **the taxonomy does not port**, not that the shipped tool misfires.
* **`verdict == "correct"` is not points-equivalence outside `rubrics_heldout`.**
  Three of the five rubric families award partial credit, and `rubrics_verdict`
  sets `correct` from the claim alone at 50 % of the points. So the classifier
  over-reports `free` on the verdict paper (5 items called free; none is strictly
  zero) and under-reports what the bluffer earns on adaptation (0 items called
  free; the bluffer collects 24.6 points across 17 of them).

## Caveats the numbers above depend on

* **`handover`'s bluffer reads the answer key.** It plays the modal answer per
  family and the mode is computed from the key (`handover.py:1681-1696`). A
  genuinely theory-free examinee cannot compute it, so handover's 32.6 % giveaway
  and its 0.326 floor are an **upper bound**, not a measurement.
* **`verdict` has no memoriser.** `verdict.py:1191` builds it as the oracle
  restricted to small boards, so it is a bounded enumerator that fails by
  *declining*. The whole partition on that paper is a restatement of
  `board_size_class`, and the 4 large-unsolvable "anomalies" are a property of the
  voter, not of the items.
* **No new voter was invented.** All five papers ship their own oracle /
  memoriser / bluffer, pre-registered against score bands in
  `exam/grading/calibration.py`. Adding a sharper one inside the run that measures
  it is the tuning V7 §8 refused, for the same reason.
* **`theory` is meaningless as an absolute on `adaptation`.** Partial credit plus
  a `fraction >= 1.0` threshold makes "oracle alone is correct" nearly automatic
  there. Quoting 59 items / 143 points as its effective size would be a fabricated
  number; the defensible statements are the pairwise table and the voter fractions.
* **Nothing here is fixed.** Every defect above is reported, not repaired: the
  adaptation rubric is on the marking path for V4's published calibration
  numbers, so changing it moves them, exactly as V7 argued when it pinned
  `_read_set` with a strict xfail instead of fixing it.
