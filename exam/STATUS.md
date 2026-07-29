# STATUS — exam

Prompt `P-15`, branch `agent/p15-exam-builder`. What is built, what it measured,
and what it cannot do. The last section is the one to read first.

## Milestone state

| item | state |
|---|---|
| core: two-sided item, paper/key split, report | done |
| guards: zero-network tripwire, sealed + dev pile refusal | done |
| leakage: probes, structural, positional, cheater brief | done |
| rubric registry, source-hashed, digest on sheet and report | done |
| marker + `confusion()` | done |
| calibration: 4 fakes, pre-registered bands, hard block | done |
| 题型 1 held-out prediction (80 items) | done |
| 题型 2 layered handover (29 items, 2 bundles) | done |
| 题型 3 rule-change adaptation (60 items, 6 variants) | done |
| 题型 4 three-class verdict (17 items, 17 specs) | done |
| fresh-reader run, both tiers | done |
| cheater-subagent run, all four sheets | done |
| run archive, `runs/<id>/MANIFEST.json` | done |
| marker self-test: 7 mutants, 8 injected faults, detection matrix (V4) | done |
| sensitivity/specificity matrix, split by verdict class (V4) | done |
| `verify.py`: one command for the whole territory (V4) | done |

Tests: **287 passed** (253 inherited + 34 new). The line above this one said "157 passed, 1 skipped" until
V4-exam-selftest; V2-exam-on-worldgen had added 96 tests without updating it, and
the skip had already unblocked itself. Counted rather than copied forward.

## V4-exam-selftest — the marker was only ever tested at its endpoints

`calibration.py` pins `oracle == 1.0` and `null == 0.0`, exactly, on all four
papers. Both follow from construction, and between them they say nothing about
any submission that is neither ground truth nor silence — which is every real
one. `exam/grading/selftest.py` attacks the middle, and found things.

**A live defect in a shipped rubric, on the mutants' first run.** An answer the
adaptation rubric could not parse was read as the substantive claim `never`, and
on `v-a0-03` — the one variant undetectable on its base level — `never` is the
truth. A submission containing nothing scored **1.600 / 144**, all of it on the
two `v-a0-03.detect` items, and `v-a0-03.detect.match` paid **1.0 of 1.0**. The
item exists to ask whether an examinee can tell "the change is invisible from
here" from "I did not look"; the marker could not tell those apart either.
Fixed, with no calibration number moving. D-EX-014.

**The calibration bands were one-sided.** Every band in `EXPECTED` for the
informative fakes is `Band(0.0, x)` — bounded above, open below — so a marker
that *depresses* scores satisfies all of them. Injecting `truncates_partial`
caught nothing at all on the first fault-matrix run. Closed with a seventh
mutant rather than a fitted lower band. D-EX-013.

**The confusion pair cannot do the job alone.** With the cheater on the matrix,
three examinees report sensitivity 1.000: ground truth, the memoriser, and a
reader who never saw the world. `oracle` and `cheater-v4` are identical in
**every cell** of the class split and differ only in the score. D-EX-015.

**A second digest** now covers `mark.py` and `calibration.py`, pinned by a test,
which closes what used to be open weakness 3. D-EX-016.

## V4 — the cheater pass against the fixed sheets

Old weakness 11 said no adversarial reader had seen the sheets since the two
leaks were fixed. Two have now, and both were scored against the key rather than
believed.

**Verdict sheet: 17 of 17 claims correct**, against a 9/17 majority baseline,
having predicted 13.8 for itself. On the real rubric that is **17.0 / 34 =
0.5000** — the cap is exactly one half because it submitted no certificate and
no witness anywhere, which is the paper's defence working as designed. Most of
its leverage was cheap arithmetic on the board, which is solving cheaply rather
than cheating; three genuine sheet-structure tells are recorded in the run's
`RUN_STATE.md` (a relabelling that is provably a no-op, byte-identical grids
under weaker wrappers, and a unique unwrapped control). The `points` leak P-15
fixed is confirmed dead.

**Held-out sheet: one confirmed leak whose measured yield was negative.**
`instructions` opened with "A0 is a sokoban variant" while `world.description`,
on the same sheet, said the dynamics "are deliberately not stated here". A0's
push slides the box **two** cells; vanilla sokoban slides it one. The cheater
took the genre name, predicted one-cell pushes at confidence 0.97, and scored
**0 of 6** — while scoring 9 of 9 on the edge-blocked items, which need no
dynamics and are the null baseline. Removed anyway: this paper asks whether a
theory learned `push2` from evidence rather than assuming push-one from a prior,
so naming the genre is an undeclared second experiment.

Its third claim — six items whose answers are printed as other items' inputs —
**did not survive checking: 0 of 6**. A full 80×80 successor scan found one real
instance it had not named. Two confident cheater reports, two different failure
modes, both caught by the same rule: verify before believing.

## What the rehearsal actually measured

**The marker is calibrated on all four papers.** `oracle` 1.000 and `null` 0.000
exactly, everywhere. The two informative fakes behaved as the protocol requires:

* **held-out** — the memoriser scored **1.00 on replay and 0.15 on held-out**, a
  gap of **0.85**, with `blocked_crossing` at 0/5 held-out against 5/5 replay.
  That is a0-spike's T-9 finding reproduced as one cell of a table instead of as
  a paragraph in a log.
* **verdict** — the bluffer showed **sensitivity 1.0, specificity 0.0** and
  scored 0.265. A framework that answers "unsolvable" to everything is caught by
  the pair, exactly as `Theoria.md` 1.11 demands.
* **adaptation** — the memoriser tripped **`silently_wrong` twice**: under two of
  the six variants the `mismatch` level becomes solvable, and a theory that keeps
  its old verdict is confidently wrong about a world it no longer describes. The
  bluffer scores the *same total* and trips the flag zero times; the two are
  separated only by `axes()`, which is the argument for having the flag.

**Determinism holds.** Sheets, keys and specs are byte-identical across rebuilds
and across `PYTHONHASHSEED` 7 and 99.

**Leakage: 1,790 probes declared, 0 probe hits, 0 structural hits**, and no
paper is clustered by answer — *after* the two leaks below were fixed.

## The cheater earned its place — two real leaks, both measured

Four sheets went to cheater subagents with no other context. They found two
leaks that the static checks had passed, and both were confirmed against the
answer key before anything was touched.

| leak | measured yield | status |
|---|---|---|
| verdict `points`: 3.0 ⟺ solvable, 2.0 ⟺ unsolvable | **17/17 claims**, the whole claim half, no board reasoning | fixed — uniform points |
| held-out `world.description` published "a push slides the box two cells" | 47.5% → near 100% | fixed — the world block no longer states dynamics |

A third finding, on the handover paper, was measured at **11/12 against a 7/12
majority baseline** — real, but its nature is sharper than a syntax tell: the
`name_class` definitions are *classifying* rather than merely *identifying*, so
those items are answerable from the sheet alone and do not test the delivered
manual at all. Not fixed; see open weakness 9.

Two cheater claims did **not** survive checking, and are recorded because an
unverified cheater is just another confident agent:

* the adaptation `match`-level "tell" was estimated at 50–70% and scores **1/6** —
  the name primes the wrong answer for five of six variants;
* the verdict `points` finding was self-reported with a circularity caveat; it
  was verified directly against the key and is exact.

**The deeper fault was in the checker.** `answer_labels` was an optional hook,
no paper module implemented it, and so checks 3 and 4 silently did nothing on
all four papers. An optional check is a check that does not run. Labels are now
derived from the key directly, a fourth check tests whether `points`/`tags`/`kind`
predicts the answer, and regression tests pin the exact leak that shipped.
Details and the three false positives that shaped it: `DECISIONS.md` D-EX-011.

## The handover result, and why it is weaker than it looks

Two fresh subagent readers — no history, no repository, bundle and sheet only —
both scored **46/46 = 1.000**. The author baseline is also 1.000.

* `reader_minus_author = 0.000`. 新读者打平作者: for this manual and this sheet,
  the understanding is in the document.
* `tier2_minus_tier1 = 0.000`.

**The second number is not a measurement.** Both tiers hit the ceiling, so the
paper had no room left to show a difference. A zero delta from a saturated sheet
is uninformative about the value of the playbook, and reporting it as "the
playbook is worth nothing" would be wrong. The sheet needs harder items — boards
where a manual-only reader must actually pay for the search — before the delta
means anything.

**Worse, the exam measures the wrong side of the pre-registered prediction.**
`Theoria.md` 1.11 predicts that the manual-only reader *catches up*, and that the
difference shows up as **多付的搜索成本 ≈ 玩法书缓存的计算量** — a cost, not an
accuracy. The tier-2 reader said so unprompted: the playbook "saved effort, not
error". The exam has **no cost instrument**, so the quantity 1.11 actually
predicts was never measured. Session cost was incidentally observed (tier 1:
50,475 tokens / 10 tool calls / 134 s; tier 2: 54,944 / 11 / 156 s) but it is
n=1, in the wrong direction, and confounded by tier 2 simply having more to read.
It is recorded as an observation and is not evidence of anything.

## A defect in the A0 manual, found three times independently

The handover builder, the tier-1 reader and the tier-2 reader each arrived at
this without knowledge of the others:

> `a0-spike/theory/theory.dsl` records
> `invariant box_row_parity (Box.pos.row) mod 2 = 1 [status: proven]`.
> What `push2` conserves is the **parity** of each coordinate. The **value** `1`
> is a fact about the board the evidence came from. All three invariants are
> written this way, and `theorem unsolvable_mismatch` inherits the flaw: it
> hard-codes "the box starts even, the target is odd" instead of stating the
> general mismatch test.

So the manual ships, marked `proven`, a sentence that is **false on most boards
of its own world** — including several on the exam sheet. It is a live instance
of the failure mode `Theoria.md` §1.3 is about: a statement that passes its type
check and is false of the world. The bundles keep it verbatim; repairing a
deliverable in order to examine it would be examining a document nobody shipped.

This is a finding about `a0-spike`, which P-15 holds read-only. Nothing was
fixed.

## Cross-track: the A0 manual no longer parses

`pipeline.gen_exec.compile_module` refuses `a0-spike/theory/theory.dsl`:

    SemanticsError: theory.dsl has no `semantics:` section ... see
    CONTRACTS/dsl_grammar_v0.2.md

The grammar moved to v0.2 and made `semantics:` mandatory; the v0.1 A0 manual
predates it. **This reproduces on `master` and was not caused by this branch** —
`a0-spike/tests/test_a0.py` errors on import there too. The handover author
baseline falls back to the checked-in `a0-spike/artifacts/theory_exec.py` and
records both the fallback and the refusal text in the truth file. Raised in
`PARTNER_SYNC.md`; not fixed here, because `a0-spike/` is outside P-15's
territory.

The refusal itself looks correct — assuming a default frame axiom would compile a
manual into a different world silently. The gap is that nothing migrated A0.

## Open weaknesses

1. **The handover sheet saturates.** See above. Until it has items that
   discriminate, neither tier number carries information, and the pre-registered
   1.11 prediction is untested.
2. **No cost instrument anywhere in the exam.** Account for search cost and the
   handover item becomes the measurement 1.11 describes; without it, it is an
   accuracy test of a prediction that is not about accuracy.
3. ~~**`EXPECTED` is not covered by the rubric digest.**~~ **Closed by V4**
   (D-EX-016). `selftest.protocol_digest()` hashes `mark.py`, `calibration.py`
   and `selftest.py` together, and a test pins the value, so widening a band now
   requires a deliberate edit a reviewer sees. It is a *second* digest rather
   than an extension of the first: the rubric digest is the seal on every sheet,
   and extending it would rewrite every stored artefact for a check that has no
   reason to travel to an examinee.
4. **`cart_region` in the verdict certificate checker is sound but incomplete** —
   it takes the undirected closure of a relation that is directed once an action
   is forbidden, so it over-approximates reachability. It can never certify a
   false theorem, but it will refuse a certificate for a level separated only in
   the directed graph. Same shape as `lp_potential`'s standing caveat.
5. **`win_tighten` is exercised only at its no-op boundary.** An A2-family level
   has one binary victory test, so a real threshold would be unsolvable for a
   reason none of the three certificate kinds can state. It is on the paper as a
   control, not as a live operator.
6. **The class (ii) state-space bound assumes comb-shaped geometry.** It is not a
   general-purpose bound and is applied only to the levels it fits.
7. **One examinee per handover tier.** n=1 per tier. Nothing here supports a
   variance claim about fresh readers.
8. **The four papers were built by four separate agents.** Their conventions
   converged because the interface forced them to, not because one mind wrote
   them; the rubric weights across types are not calibrated against each other
   and no cross-type total should be quoted.

## Not attempted

* No live game, no dev-pile game, no API call, no model call from any code path
  in `exam/`. The fresh readers and the cheaters are subagents the *session*
  spawned, never something the exam invokes.
* No Phase 4 sealed-pile question. That is the point of the sequencing: the
  procedure is frozen now so that the only new work later is the per-game
  justification.
9. **The handover `name_class` items are answerable without the manual.** Their
   definitions classify rather than identify, so a cheater scored 11/12 against
   a 7/12 baseline reading syntax alone. The fix is to make each definition a
   pointer ("the name as used in the laws section") rather than a description —
   but five of the twelve names are exam-invented and appear nowhere in the
   manual verbatim, so a pure pointer does not exist for them. Left unfixed and
   documented rather than patched late: the fresh readers sat this sheet, and
   changing it after the fact would invalidate the only handover data there is.
10. **`points` is still on the sheet.** The leak was fixed by making the values
   uniform, not by removing the field. Any future paper that weights items by
   anything correlated with the answer reintroduces it; the new metadata check
   is what stands between that and a shipped leak.
11. ~~**Two cheater agents, four sheets, one pass.**~~ **Partly closed by V4.**
   Two more cheaters have now sat the two sheets that changed — verdict and
   held-out — and both results are above. `adaptation` and `handover` are
   unchanged since P-15's pass, so they are as attacked as they ever were,
   which is once each. The standing form of this weakness is that a cheater
   pass is a sample, not a proof: what it did not find is not absent.

12. **The held-out replay/heldout split is recoverable from the state alone.**
   Measured at **79/80** by V4's cheater and confirmed: all 40 replay items put
   the box on both-odd coordinates drawn from **7 distinct cells**, while the 40
   held-out items use **29**. The two halves are not distributionally matched at
   the level of state, so a memorising theory can tell which half it is standing
   in without reading the tag. It leaks nothing about the *answers* — the
   answer-class stratification is exact to the item, 4/5/4/5/16/6 in both halves
   — but "held-out" here partly means "box on an even coordinate" rather than
   "same situations, unseen transition", and the `gap_replay_minus_heldout`
   headline inherits that. Fixing it means resampling the split, which changes
   the paper substantively and needs its own pre-registration.

13. **One held-out item's answer is printed on the sheet as another item's
   input.** `a0h-074`'s `frame_after` is `a0h-042`'s `frame_before`, both in the
   replay half. Found by a full 80×80 successor scan, not by the cheater, which
   claimed six such pairs and had **none** of them right. Inside the replay
   half consecutive trajectory states are expected to neighbour each other, so
   this is a generation-time check that was never written rather than a
   surprise. Same resampling run as weakness 12.

14. **A cheater's confidence is not evidence, and now there are numbers.**
   Across two passes: the verdict cheater under-predicted itself (13.8 forecast,
   17 measured), and the held-out cheater was *most* confident (0.97) on the six
   claims that were **all wrong**, because the leak it exploited handed it a
   prior — vanilla sokoban — that is false of A0. Every cheater claim must be
   scored against the key before it is believed or acted on.


## V11-handover-auto — the handover test is automated, and the run it produced is not a result

Prompt `V11-handover-auto`, branch `agent/v11-handover-auto`. Run
`exam/runs/20260728T202540Z-V11-handover-auto-r2/`; the voided first cohort is
`exam/runs/20260728T202101Z-V11-handover-auto/`.

**What was built.** The layered handover of Theoria.md 1.11 stopped being a
thing a session does by hand:

* `exam/papers/handover_auto.py` — paper `v11-handover-a0`, 31 items, 58 points,
  on five fresh boards with shortest solutions of 14 to 25 actions and two with
  no solution at all.
* `exam/grading/rubrics_handover_auto.py` — five marking rules, registered in
  `RUBRIC_MODULES`. **The fourth question family of 1.11 now exists**: "why does
  this rule hold", asked as a citation set, marked with a penalty so that
  shotgunning pays nothing (D-EX-017). `optimal_action` splits its points
  between the move and the plan length and accepts `none` on a dead board.
  One item is marked by recomputing the claim where the reader says it fails.
* `exam/tools/run_handover_auto.py` — `build` freezes the sheet, writes the two
  prompts and records the key's sha256 **without writing the key**; `score`
  re-derives the key, refuses to mark on a digest mismatch, calibrates the
  marker, marks, and reports the tier difference with a bootstrap over readers,
  a bootstrap over items and a measured grader-noise floor.
* 34 tests. Suite total 320, zero API calls, zero network, no sealed-pile
  contact.

**What it measured: nothing about the tiers.** Six fresh subagent readers,
three per tier, every one 58/58. Delta 0.000. The pre-registered saturation rule
fired — and then the adversarial review found the real fault, which is worse:
**two `rule_justification` items restate the playbook's two `prune` entries in
English on the tier-1 sheet**, so the control arm was handed the treatment on
exactly the family where a difference had been pre-registered. This is the
second consecutive run of 1.11's handover item that produced no tier number.

**What it did establish.** A fresh instance handed nothing but
`a0-spike/theory/theory.dsl` and its mechanical rendering returned exact
shortest-plan lengths of 14 to 25 actions on six boards and both dead boards.
The adversarial reviewer reproduced every length with its own BFS transcribed
from `MANUAL.md`, showed no monotone function of the geometry yields them, and
showed the readers' disagreements fall inside the tied optimal sets and never
outside — the signature of independent search. It also supplied the reason the
search was tractable, which nobody had claimed: the manual's two parity
invariants pin the Box to a quarter of the board.

**Three leaks, in the order they were found.**

1. `tags` printed `dead` on the two unsolvable items. Found mid-run; the first
   cohort was voided. `leakage.metadata_hits` missed it because it buckets on
   whole `tags` *values*, and a unique `level:` token made every bucket a
   singleton. D-EX-018.
2. `PREREGISTRATION.json` carried `leakage.positional.example_ids_by_answer`, an
   answer-label → item-id map, in the examinees' own run directory. The reviewer
   scored **0.603** from that file alone, above this paper's memoriser arm,
   having never seen the bundle. `build()` no longer persists it.
3. The sheet restated the tier-2-only playbook on the tier-1 paper (above).
   `cross_item_leak_report` and
   `test_no_new_sheet_claim_restates_a_playbook_entry` are the check that did
   not exist; the two known offenders are pinned so a third fails the suite.

Every one of them is the same shape: a fact spelled one way, a checker looking
for another spelling.

## Open weaknesses this run adds

13. **`leakage.metadata_hits` buckets on values, not tokens.** The fix belongs in
    the shared checker and was deliberately not made mid-run. Until it is,
    `p15-adaptation-a0`, `p15-heldout-a0` and `p15-verdict-a2` are unaudited
    against a leak class that has demonstrably shipped once.
    **CLOSED by V21 (2026-07-29)** — token check added, all four papers audited
    and clean. See "V21 — the leak gate was passing, not checking" below; the
    re-audit turned up a second and larger hole on the way.
14. **Nothing compares one item's prose with another tier's bundle.**
    `cross_item_leak_report` lives in the V11 paper module and should be a
    checker every paper runs.
15. **A run has no chain of custody to its examinees.** No transcripts, no
    session ids, no per-reader timestamps — six hand-assembled JSON files whose
    independence rests on six self-reports. Fabrication and honesty look the
    same in the artefacts, and that is a gap the exam should not have.
16. **The delivered message was not the tested message.** The blinding tests run
    against `prompts/*.prompt.md`; readers received a wrapper naming a
    `TASK.md`. The wrapper is now `prompts/DELIVERY_WRAPPER.md` and the tests
    should be pointed at it.
17. **Per-reader delivery directories were named by arm** (`A1`…`B3`). The arm
    label was outside the tested surface.
18. **Still no cost instrument.** With accuracy on A0 exhausted, cost is now the
    *only* channel through which 1.11's actual prediction — 多付的搜索成本 ≈
    玩法书缓存的计算量 — could be measured. Open weakness 2 is no longer one
    weakness among several; it is the blocking one.
19. **`abstain` is unpriced**, which is load-bearing for the memoriser
    calibration: that arm scores what it scores because of how much it abstains.
20. **`exam.verify` GREEN does not mean the committed artefacts are the ones the
    code produces.** Found while shipping V21 (2026-07-29). `build_papers`
    overwrites `exam/artifacts/` in place, and the determinism stage compares two
    *fresh* builds against each other under two hash seeds — nothing ever compares
    a build against what is checked in. Measured on a clean checkout of
    `agent/v21-leakage-gate-token-level` with no V21 changes applied: one
    `python -m exam.tools.build_papers` dirties nine tracked files, every diff the
    same stale `rubric_digest` (`e06bdf52…` committed, `63ce1eab…` rebuilt).
    So the committed papers, truth keys, calibration and build manifest were
    generated by a rubric that no longer exists, and the gate said GREEN the whole
    time. This is V21's own failure mode one level up — the check runs, passes, and
    is not checking the thing its name claims. Filed as `V25-verify-does-not-check-what-is-committed`.


## V21 — the leak gate was passing, not checking

Prompt `V21-leakage-gate-token-level`, branch `agent/v21-leakage-gate-token-level`.

**The reported defect, confirmed.** `metadata_hits` bucketed each metadata field
by `canonical(value)` and then dropped every bucket holding one item. One unique
token anywhere in the value — a `level:` marker, a per-item id — makes *every*
bucket a singleton, so nothing is scored and a genuine leak sharing the rest of
the value is structurally invisible. `tags: [..., "dead"]` on the dead items is
the shape: the tag lists all differ, so the whole-value check never sees the
token that is the answer.

**Fixed in two halves.**

* Each value is now also split into tokens and each token tested as a binary
  rule — does carrying it predict the answer? A token on one item is an
  identifier, not a rule, and a token on every item predicts nothing; both are
  skipped, which is what keeps the check from crying wolf. Whole-value bucketing
  is kept as the second net, not replaced: it is what catches the original
  `points` 2-versus-3 leak, whose tokens are too short to survive tokenising.
* Singleton buckets are still not *scored* — there is no second item to test the
  rule against — but they are no longer discarded inside a comprehension.
  `metadata_scan()` returns what each field declined to score alongside the hits,
  and `check_paper` writes it to `report["metadata_unscored"]`, so
  `exam/artifacts/leakage.json` now distinguishes "no hits" from "nothing was
  examined". Those print the same and mean opposite things. (The first pass added
  the function and called it only from the tests, so the artefact still said
  neither; see the second pass below.)

**The re-audit found something larger than the thing it was sent to check.**
`derive_label_sets` required a truth field to be present on 60% of a paper's
items before treating it as an answer class. A paper built from several item
families has no such field — so `p15-adaptation-a0` and `p15-handover-a0`
derived **no label set at all**, and the metadata check ran on **zero of their
89 items**. Two of four papers, 48% of the exam, green because unexamined. The
threshold was asking "is this *the* paper's class" when the question that
matters is "is this testable at all"; a leak confined to one family is still a
leak. The floor is now `MIN_LABELLED = 4`, matching the minimum
`_metadata_hits_within` already applies before it will score anything.

**Result of the audit, which is the point of the item.** Under the token check
and the wider net, all four papers derive label sets — 3, 1, 2 and 4 fields
respectively, against 0, 0, 2 and 3 before — and **all four come back clean, zero
hits of either kind**. So the papers were in fact clean; what was missing was
the looking. `test_every_shipped_paper_derives_at_least_one_label_set` now fails
if any paper ever again reports green from an empty examination.

**A third defect, uncovered by the wider net rather than reported.** Dropping
singleton buckets can leave a scored subset containing only one answer. The rate
is then 1.0 by arithmetic — each bucket's majority is its whole content — while
the floor still reflects the full group, so a field is flagged for "predicting"
the only answer left. `v11-handover-a0` was the live case: three tag buckets of
two items each, every one `solvable: true`, flagged at 1.000 against a 0.750
floor. `metadata_hits` already refuses to score a group with a single answer in
it ("one possible answer is not a question"); the rule simply was never applied
to the subset it ends up scoring. The floor is now recomputed over the scored
items and a degenerate subset is skipped.

**Negative controls, both directions.** A paper whose per-item `level:NN` markers
make every whole-value bucket a singleton, and whose `dead`/`live` token is the
answer, raises `LeakageError`; a companion test demonstrates that the old
whole-value check alone produces twelve singleton buckets on that same paper and
scores nothing. A clean paper of identical shape — same unique markers, token
uncorrelated with the answer — stays green, as do a constant token and a
one-item token. A gate repaired by refusing everything is a gate that gets
switched off.

### V21, second pass — what the adversarial review overturned

The subagent sent to refute the first pass died before writing anything, leaving
twelve probe scripts and no report. Re-running all twelve (raw output
`exam/runs/20260729T1130Z-V21-leakage-gate-token-level/adversarial/PROBE_OUTPUT.txt`,
verdicts in `ADVERSARIAL.md` beside it) overturned four things, two of them in the
first pass's own tests.

**Two of the ten tests pinned nothing.** `test_a_token_on_one_item_is_an_identifier_not_a_rule`
used a fixture whose single-holder tokens score 0.583 against a 0.900 tolerance, so
deleting the guard it names left the test green — it asserted the tolerance's
outcome, not the guard's. Mutation testing confirmed: guard removed, 0 of 10 tests
noticed. The fixture is now 11 `live` items and one `dead` item that is the sole
carrier of the token, where leave-one-out is 1.000 against a 0.917 floor by
arithmetic. Separately, `test_a_subset_correction_does_not_desensitise_the_token_check`
was a source grep for `floor = max(`, and four of six respellings of the identical
regression walk past it; a behavioural test now stands beside it. Three further
guards — `MIN_TOKEN`, `MIN_LABELLED`, and the strictness of the token-level floor
comparison — had no test at all, and each mutation of them was caught by 0 of 10.
All four are now pinned, and every one of the 23 mutations is caught by at least
one of the 20 tests (`MUTATION_TABLE.txt`).

**The coverage report did not reach the artefact.** `metadata_coverage()` was
added and then called from nowhere but the tests, so `leakage.json` still reported
only "no hits" — the same defect V21 was opened about, reproduced inside V21's own
fix. `metadata_scan()` is now the single traversal that both projections come from,
`check_paper` writes `metadata_unscored`, and constant fields, absent fields and
whole groups too small to score are recorded with a reason instead of skipped
silently. This is what made the next line visible.

**`p15-verdict-a2`'s metadata check scores nothing, on all four of its label
sets.** All three original metadata fields are constant across its 17 items. The
green is *honest* — a constant field cannot predict anything — but it was
indistinguishable from the green of a fully examined paper, which is the whole
complaint. It is now printed rather than inferred.

**`item_id` is now checked, and immediately found a leak in exam's own fixtures.**
A probe built a paper whose ids read `q-dead-01` and walked it past the gate.
Whole-value bucketing could never score that field — it is distinct on every item,
so every bucket is a singleton — which is why adding it only became possible with
the token check. All four shipped papers stay green with it in. Two tests in
`test_core.py` did not: `_labelled` had been building items called `solvable-0` and
`unsolvable-0` since P-15, so the answer was printed in the id of every item in the
fixture used to test the `points` leak. Neutral ids now, with
`test_the_old_labelled_fixture_was_itself_an_item_id_leak` keeping the original
shape as evidence — a fixture repaired in silence teaches nothing, and the first
thing this field did on being switched on was find a real instance of exactly what
it was added for.

**Known limits, stated rather than closed.** Four constructed leaks still pass, and
the reasons differ:

| Construction | Why it is not closed |
|---|---|
| a token carried by exactly one item | leave-one-out on a sole carrier is 1.000 by arithmetic, so closing it makes *every* per-item identifier fire on the minority-class item. A crying-wolf gate is a switched-off gate. Needs the explicit feature-family + baseline framing of `a12_independent_audit.py`, not a loosened guard. |
| list length (`pad` twice versus once) | tokenising to a set destroys multiplicity by construction |
| a token shorter than `MIN_TOKEN = 3` | below the noise floor the tokeniser needs |
| two fields in conjunction / XOR | the check is per-field and independent |

Fields outside `METADATA_FIELDS` are excluded by design, not oversight: `board`,
`definition`, `state` and the rest *are* the question, and a feature of the question
predicting the answer is the task. An independent leave-one-out audit run without
reference to the gate's implementation duly reported `count:board` "predicting"
`v11-handover-a0`'s `solvable` at 1.000 against a 0.750 baseline — which is what
solving the problem looks like, not what leaking it looks like.

**The price of the wider net, measured.** `MIN_LABELLED = 4` buys real coverage
(label sets 0→3, 0→1, 2→2, 3→4 across the four papers) at a false-positive cost
nobody had quantified. Exhaustive enumeration over a two-symbol alphabet gives
P(a random token fires) = 0.20 at n=4 on a balanced split, 0.08 at n=5, 0.036 at
n=6, 0.008 at n=8 — and the real papers' smallest scored groups sit right in that
range (`why` n=5, `plan_len` n=6, `label`/`verdict` n=6). A permutation null on the
shipped papers — shuffle the labels, see how often the gate fires — puts
`v11-handover-a0`'s `solvable` (n=8) at **0.117** and `p15-adaptation-a0`'s
`exact_on_heldout` (n=12) at 0.013, with the remaining eleven label fields at 0.000.

The threshold stays at 4: "green because unexamined" costs more than an occasional
false alarm, and the gate's semantics are already "stop and let a human adjudicate",
not "leak proven". But **the number ships with the gate**. If `v11-handover-a0`'s
`solvable` ever does redden, whoever reads it is entitled to know there is a 11.7%
chance it is coincidence, and that the next step is to re-run
`a9_permutation_null.py`. A multiplicity correction for small n is left as separate
work.
