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
21. **On `v11-handover-a0`'s `optimal_action` family, green now certifies less
    than it did.** V26 closed the level-multiplicity channel by giving `stile`
    and `cairn` a second item each, which leaves the group with no single-holder
    `level:` token — so the pooled private-marker cut has nothing to pool and is
    **inert on this family**. What guards the channel now is the property test
    `test_level_multiplicity_is_uniform`, not the gate's green — and that is the
    general shape to expect from leak repairs on a small sheet. *(The first
    version of this entry added that the familywise rate "rose to 0.106281, above
    `ALPHA`". Measured, it **fell**: 0.135385 pre-repair against 0.106281 after,
    and it was already over `ALPHA = 0.05` beforehand — the pre-repair finding
    carries `weak_evidence: true` in its own record. The repair did not blunt the
    detector on that axis; only the inertness claim survives.)*


## V5-verdict-three-types — the verdict paper was audited, and the marker was wrong

Prompt `V5-verdict-three-types`, worker `W-1652`, branch
`agent/v5-verdict-three-types`. Run
`exam/runs/20260729T020000Z-V5-verdict-three-types/`.

**The item asked for something that already existed.** Its four clauses — three
classes in a self-built world family, constructive grounds per item, calibration
by a known-full and a known-zero fake, sensitivity and specificity reported
separately — were all delivered by P-15 and V4 as `p15-verdict-a2`. So this run
took the item's own premise instead (考卷的可信度取决于判卷者本身对不对) and
asked whether the delivered instrument is right. Six adversarial auditors, every
finding re-derived here before anything was changed. It is not.

**The certificate checker was unsound.** `relaxed_edges`' docstring claimed it
"can never make a solvable level look unsolvable, which would hand out points
for a false theorem". It could, three ways, because the graph was a second
implementation of `Level.step` and the two disagreed about the teleport and the
door. `cart_region` and `cut_set` certificates for **solvable** levels were
accepted and paid **2.0 of 2.0**. The cheapest reproduction needs no malformed
field at all — only a cell that is both the door and the portal. Not reachable
through any shipped item (41,868 fuzzed well-formed solvable levels, zero unsound
accepts), which is why nothing had noticed. One transition function now, plus
`Level.wellformed_problems` at build time. D-EX-020.

**The class (ii) bound was unsound off the comb, and a shipped constructor
reaches it.** `comb_open(30)` under `observation_loss` on the corridor gives
`m = 60`, a claimed 2^60, `exhaustive_feasible: False` — and **29,791** actual
reachable states. `build()` would have shipped it as class (ii). The bound
checked each dip in isolation and never checked the lane walked between dips.
D-EX-021.

**The class (ii) quotient is measured, and the inference drawn from it was
wrong.** The four class (ii) levels have **180, 180, 600 and 177** reachable
`(cart, button)` states, against a `lower_bound` of 2^60 to 2^120. This run
briefly concluded that the quotient therefore decides the question, and derived
`search_credible` from it (D-EX-022). **An adversarial review refuted that and
the decision is withdrawn**: the quotient ignores `step_limit` outright, and it
carries no latch state, so on a `require_all_switches` board where one switch is
unreachable it reports the goal reachable and the level is unsolvable — both
demonstrated with a shipped constructor and a shipped operator. Deriving
credibility from an unsound abstraction replaced "a true statement was called
false" with "a false statement is called true", and the second one *pays*.
`search_credible` is the enumerability field again — spelled
`exhaustive_feasible` at the time, and `naive_enumeration_feasible` since
D-EX-028 withdrew the wider name; the quotient stays as a recorded measurement
whose truth entry says in the same breath that it is not a search space.
D-EX-022, withdrawn by D-EX-027.

**The split confusion matrix cannot report a pair.** The three classes partition
the paper *by answer*, so one denominator is empty in every class cell and the
pair exists only pooled — the reading D-EX-015 shows means least. The truth
already carried a stratification that cross-cuts the answer, unused:
`board_size_class`, small 5/5 and large 4/3. Under it the bluffer's signature is
`(1.000, 0.000)` in a single cell per stratum instead of joined across two rows
of disjoint items. D-EX-024.

**An unreadable answer was reported as an abstention** — in the column D-EX-006
introduced so an abstention could not be confused with anything else. D-EX-025.

**The calibration gate sees two of eleven marking outcomes.** Fourteen faults
injected into the verdict rubric: **thirteen passed `assert_calibrated`**, twelve
passed all seven mutants, two were caught by nothing anywhere, and all four
calibration fractions were bit-identical under every one. The sheet advertises
five answer shapes; the fakes submit three, and the mutants inherit those three
because they are derived from the oracle. Five answer-shape probes now run at
the gate, each with a score fixed by arithmetic. D-EX-026.

**Four of the seventeen constructive justifications asserted something false or
insufficient**, found by computation against the shipped level: `iii3` claimed
three hazards lie on no minimal route when one lies on 72 of 204; `iii8`'s
argument never mentioned the 120 switches its board requires latched, and the
62-command walk that satisfies it as written loses; `iii7` quoted the cost of a
plan of a different shape than the one it describes; `ii4` said "to the right of
the start" where the count is "reachable", a phrasing worth one order of
magnitude. All four corrected. No item's *claim* was wrong: 17 of 17
independently confirmed.

**And the key now says where its own answer came from.** Five of the eight
solvable witnesses are breadth-first search output and three are constructions,
and nothing said which. On a paper whose premise is 由构造即知答案 that is a
disclosure gap, not a defect in the answers. D-EX-023.

**And the run's own fixes were then attacked, which cost two of them.** A
seventh, adversarial reviewer refuted three of seven claims. Excluding the button
from `passable` (part of the certificate fix) **created a new unsoundness** in
`row_col_deltas`, which was using the same predicate to ask a different question
— a level solvable in one command was paid 2.0 of 2.0. D-EX-022 was withdrawn
outright. Two smaller defects: a claim outside the paper's answer alphabet was
scored as a *negative* classification, so `{"claim": "I do not know"}` earned
specificity **1.000**; and D-EX-025's fix had landed in `confusion_matrix` but
not in `mark.confusion`, which is the one the gate reads. All fixed and pinned.
D-EX-027.

Tests: **338 passed** (321 before). `python -m exam.verify` GREEN, determinism
holds across `PYTHONHASHSEED` 7 and 99.

### Closed by V5

* ~~**4. `cart_region` is sound but incomplete.**~~ Still incomplete, and the
  incompleteness is confirmed with a repro — but the *soundness* half of that
  weakness was false when it was written. See D-EX-020.
* ~~**6. The class (ii) bound assumes comb-shaped geometry.**~~ It now checks
  the assumption and refuses. D-EX-021.

### Open weaknesses V5 adds

20. **The verdict sheet leaks through multiplicity, and nothing looks for it.**
    Seven of the nine boards appear exactly once and six of those seven are
    unsolvable, so *"if this `level_id` occurs elsewhere on the sheet, answer
    solvable"* scores **13 of 17 against a 9 of 17 baseline**, needing no key and
    no board reasoning. Add `len(hazards) == 1 → unsolvable` and it is **14 of
    17**. Re-derived from scratch in the run's `verify_leak_claims.py`. The
    module docstring argues board identity is safe on the strength of the
    atrium, which is one board out of nine; the design that makes identity
    carry no signal *within* a reused board is what makes *being reused* a
    signal. D-EX-011 found value→answer and D-EX-018 token→answer; this is
    **multiplicity→answer**, and no checker in `leakage.py` computes a
    bucket-size feature. **Not fixed.** The fix is either a checker plus a
    balancing item on each singleton board — which changes the paper and needs
    its own pre-registration — or accepting it and saying so. This run did the
    saying.
21. **Production's leak check has never been run against the real answer.**
    `verdict.py` declares no `answer_labels`, so labels come from
    `derive_label_sets`, which drops any field whose text is already on the
    sheet — and the item's own question prints *both* `solvable` and
    `unsolvable` on all 17 sheets. The guard fires at 17/17 against a threshold
    of 10.2 and `claim` is dropped; the labels actually checked are `class`,
    `board_size_class` and `search_credible`, all referee-side strata. It is
    D-EX-011's lesson one level up: there an optional check did not run, here
    the check runs on labels that are not the answer. **Not fixed**, and note
    that fixing it alone would not have caught weakness 20 either —
    `metadata_hits` handed the real answer still reports clean, because
    `METADATA_FIELDS` is three bookkeeping fields and all three are constant.
22. **`win_tighten` is not merely exercised at its boundary — it is absent from
    the level.** `variant_of(a2_echo(), win_score_required=1)` is byte-identical
    to `a2_echo()`; `iii5`'s level dict, canonical blob and sheet side are the
    unwrapped base game, and `operators_exercised` lists the operator on the
    strength of a spec file alone. An unsolvable version **is** constructible
    (`win_score_required=2` → 55 states, no solution, and `proxy/variants.py`
    accepts the spec). It was not added because no certificate in the closed
    grammar states that reason, so the oracle would score below 1.0 and
    calibration would fail — the blocker is the grammar, not the world. That is
    a sharper statement of the old weakness 5, which said the operator was
    exercised at its no-op boundary.
23. **Class (i) has no solvable control, so a class-(i)-conditional false
    positive is invisible.** Two examinees with opposite pathologies — "small
    enough to search, my search failed, therefore unsolvable" and "too big to
    search, therefore unsolvable" — are identical in all ten printed cells *and*
    in the score (0.7059 both), so the renderer's stated fallback ("the thing
    that separates them is the score") is false for them. Relabelling one small
    solvable item into class (i) separates them at 0.000 against 1.000 in that
    one cell. The board-size split added by D-EX-024 does not close this: it
    separates them by score fraction, not by a rate.
24. **`certified_share_of_correct_unsolvable` reads 1.000 for a pure bluffer.**
    Its denominator is the *correct* subset, so being wrong or silent on the
    hard items raises it. A bluffer that attaches the key's certificates scores
    specificity 0.000 with a reason-quality of 1.000; an examinee that answers
    one item of seventeen also reads 1.000. It needs a denominator of all nine
    unsolvable items and a printed coverage, the way the rates got one in
    D-EX-015.
25. **Abstention is weakly dominant.** An examinee that abstains on exactly the
    items it would get wrong scores the same as one of identical competence that
    answers and is wrong (0.7647 both), and prints strictly better-looking rates
    — `--` where the honest one prints `0.000`. Coverage is the only trace and
    it is a smaller visual penalty than a zero. This is the priced form of old
    weakness 19.
26. **The two directions are not priced symmetrically.** A bluffer scores
    0.2647; an anti-bluffer that says `solvable` everywhere scores 0.3824 with
    plans a search hands it free, and 0.4706 with the key's plans — because on
    the solvable side the reason half is a witness a search finds, and on the
    unsolvable side it is a certificate. Mirror-image rate rows, 1.4× to 1.8×
    the score.
27. **Settled by D-EX-028, and settled *against* the class: a cheaper complete
    method exists, and it is the one the answer key uses.** `lower_bound` (2^60
    to 2^120) stays true, but only as a statement about the raw product space —
    what a *naive* complete search must cover. The question left open here, "is
    there a cheaper complete method?", has been measured and the answer is yes:
    every shipped class (ii) item is settled by an exhaustive computation over at
    most 600 nodes in at most 5 ms against bounds of 1.15e18 to 1.33e36, so
    `exhaustive_feasible: False` was false and is withdrawn for
    `naive_enumeration_feasible: False`. The quotient's unsoundness is
    **one-sided** — an over-approximation yields false *solvable*, never false
    *unsolvable* — so start and goal in different components is a sound
    unsolvability proof, which is why the item's own key is computed that way.
    The class therefore measures **method selection under an apparent search
    barrier**, not "only invariant reasoning can answer". Making the class mean
    what its name says still needs switches that gate geometry — a different
    world family and a different paper — but that is now a scoping note rather
    than an unanswered question.
28. **The `searcher` probe cannot see a wrong `search_credible`.** Its
    expectation reads `truth["search_credible"]` from the same key the marker
    reads it from, so corrupting that field moves both and the gate stays green.
    It is D-EX-026's own self-reference lesson surviving one field to the left,
    and it is the check that would otherwise have caught D-EX-022. Fixing it
    means recomputing credibility independently — an enumeration per item inside
    `calibrate_one`, which runs in many tests — so it was measured and left
    rather than paid for without a decision.
29. **`_region_rep` computes the key's `cart_region` certificate with the
    checker's own `components(relaxed_edges(...))`**, so `_self_check`'s "the
    reference certificate verifies" is a tautology on the naming; only
    `start_rep != goal_rep` is substantive. That is why the atrium's
    representative migrated from `[1,1]` to `[1,3]` mid-run without any
    assertion firing. Pre-existing, surfaced by this run.
30. **`subset_lower_bound`'s lane precondition is a heavy false-negative
    filter.** In fuzzing, 1,981 of 2,016 refusals (98%) were levels whose true
    reachable state count already met 2^m; an L-shaped switch-free lane with six
    verified out-and-back dips is refused. `_dip_source` compounds it by
    minimising distance rather than preferring a source on the lane. Sound —
    it only refuses to ship items — but "one contiguous row or column" is
    strictly stronger than what the construction needs.


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

## V25 — the two debts V21 measured, and the ruling that had to be withdrawn

Prompt `V2-V25-leakage-loo-and-multiplicity`, branch
`agent/v25-leakage-loo-and-multiplicity`, based on V21 rather than master because
it changes the functions V21 wrote.

V21 left two numbers with no treatment: tokens carried by exactly one item are
never scored, and small groups clear the tolerance by luck. They pull in opposite
directions, which is why the item required both at once.

**The multiplicity correction is exact, published, and not applied.** The
false-positive rate is now computed in closed form for every token the gate scores
— P(this rule fires on a token carried by k of n items | nothing leaks), counted
over how the carriers can split across answer classes. Exact rather than sampled on
purpose: V21's 0.117 came from 2000 shuffles under a seed, and a seed between the
reader and the number makes every published rate a function of the order in which
papers happened to be scanned. The exact count reproduces V21's sampled figure
(0.1034 against 0.117, inside Monte-Carlo error) with no RNG at all, and it is
charged for multiplicity at two scopes — the cuts tried on one field of one answer
group, and every cut tried under the whole answer key — both named in the key
rather than left to be assumed. A token and its complement are one cut, not two;
`p15-adaptation-a0` scores four token names that are a single cut, and counting
names would over-correct fourfold on a paper we ship.

It is **published, not applied**, and the measurement behind that decision is kept
executable: applying it as a suppressor at alpha 0.05 silences a leak V21 planted
at n=6 that a human sees by eye, because at that size with three cuts tried the
family-wise rate really is 0.187. Firing means "stop and let a human adjudicate",
so a false alarm costs one look and a miss costs a published paper. Every red now
carries what it is worth; the gate does not discount it for the reader.

**Exactness cannot be bought with unbounded time, which took measuring.** The
literal enumeration is exponential in the number of *answer classes* — the one
dimension an exam does not control, since an exam answered in integers has as many
classes as it has distinct answers. Measured: 0.46s at six classes, 14.7s at eight,
unfinished at twelve. The count is now a pruned state collapse over
`(taken, max_with, max_without)`, verified against the literal enumeration on 2130
configurations at six tolerances — including 0.875, an exact float tie at n=8 —
with zero disagreements, and on cases with counts as large as 6.4e19. Twenty answer
classes over 200 items now returns instantly. A gate slow enough to be switched off
is a gate that is not there.

**A green gate now says how much it never looked at, and whether it could have
spoken at all.** `ALPHA`'s own docstring promised that a group too small for any
token to clear it is recorded as *untestable* rather than clean, and nothing
computed that — so `group_power` now minimises the false-positive rate over every
carrier count a token could have, and a group whose best case cannot clear alpha is
named. Coverage of the single-holder guard is reported on every field, always, not
only when something was skipped: a coverage number that appears only when it is bad
is one nobody calibrates against.

### The ruling V25 shipped first was wrong, and the adversarial pass brought a counterexample

V25's first pass concluded that the single-holder blind spot **cannot** be closed,
and proved it: every statistic available for a token on one item is a function of
its carrier alone, so a real leak (`ridge` on the one `dead` item) and a
bookkeeping identifier (`tag07` on the same item) are identical digit for digit,
and no rule can fire on one while staying silent on the other. Three rules were
measured agreeing on exactly that pair.

The proof is correct and the conclusion drawn from it was not. The proof quantifies
over rules reading **one token's** carrier set; `_token_hits_within` holds the whole
field's carrier map, which is strictly more, and it separates the pair: one private
token in a field is an anomaly, twelve are an enumeration. So the question is asked
once per field instead of once per token — *does carrying a private marker here
predict the answer?* — and the two cases fall on opposite sides of it by
arithmetic: a leak marks a few items and is scored, an identifier family marks
every item and is dropped by the constant guard that was already there. The known
evasion is stated rather than hidden: padding every item with a decoy marker pushes
the cut to k = n and silences it, and the rule that survives that (deviation from
the field's modal private-marker count) is measured and deliberately not shipped,
because it is a second design decision.

Two more of the first pass's claims went with it. `237 of 261` was the wrong unit
twice over — it counts scan slots across five papers, double-counting any paper
scanned under two label sets — and the honest figure for the four shipped papers is
**97 of 106 distinct (field, token) pairs, 91.5%**; all four denominators are
printed side by side in `b5_pooled_private_cut.py`, because every one of them lands
between 90% and 95%, so the percentage was insensitive to the unit and nobody was
checking the unit. And "relaxing the guard would cry wolf" had never been measured:
measured, it is **zero** — 0 of 228 single-holder tokens across five papers would
fire if scored individually, because at k = 1 the rate is `(1 + max_without)/n` and
the most skewed real group only reaches 0.875. The guard stays because the
statistic cannot tell a leak from an id at k = 1, not because removing it would be
noisy. The wording is corrected where the guard lives.

### The first thing the new rule did was find a real leak in a paper already voided once for a leak

`v11-handover-a0`'s eight `optimal_action` items sit on `warren`, `flume` and
`kiln` twice each — all solvable — and on `stile` and `cairn` once each, which are
exactly the two dead boards. So "does my `level:` name occur only once **among the
`optimal_action` items**" answers `solvable` **8 of 8**, at an exact false-positive
rate of 0.0357. The shipped gate scored none of it: each `level:` token sits on one
or two items, and `flume` at k = 2 lands exactly on the majority floor.

> **Scope corrected by V26.** This paragraph first said "only once on this sheet",
> and that rule is **7 of 8**. `level:` tags also ride the seven `step_semantics`
> items, making whole-sheet counts `stile` 1, `cairn` 2, `flume` 3, `kiln` 4,
> `warren` 5 — so unscoped, the rule calls `cairn` solvable, and `cairn` is the
> board `PREREGISTRATION.json` nominated in advance as the sharpest
> discriminator. The gate never had the bug; it groups by `kind` and so computed
> the family-scoped rule all along. Only the prose was loose, and loose in the
> direction that would let a reader test the wrong rule, see 7 of 8, and conclude
> there was nothing here.

This paper's first build was voided for printing `dead` in `tags`
(`runs/20260728T202101Z-V11-handover-auto/VOIDED.md`) and re-run as `-r2` on the
belief that it was then clean. `-r2`'s `sheet.json` carries this channel, and its
six examinees all answered `none` on exactly these two items while disagreeing with
each other on the solvable ones — so that run cannot distinguish reasoning from
reading the tag distribution. Its `by_family.optimal_action` delta is 0.0 and
`conclusive` is false, so no paper claim rests on it, but the honesty section owes
this a line.

> **Corrected by V26 — the second half of that sentence is false, and it was left
> standing here after the ruling that overturned it.** The readers disagreed;
> **none was wrong**. All six scored 58.0/58.0, 31 correct, 0 wrong, 0 abstained
> (`RESULTS.json`, `per_item`: 2.0/2.0 on all eight `optimal_action` items for all
> six). Marking is set-valued, so every split fell inside the true optimal set and
> cost nothing, and `per_item` — which is what "disagreeing" was inferred from —
> cannot answer questions about agreement at all; only `answers/` can. The splits
> show the readers were not reading one stored value off the sheet. They do *not*
> establish independent search: under independent tie-breaking, P(exactly 2 of the
> 5 two-element items unanimous) ≈ 0.009, so the pattern is mild evidence for
> **correlated** searchers. The disposition of `-r2` is annulment on the
> `optimal_action` family, recorded machine-readably in its own `RESULTS.json`
> under `annulment`, and argued in
> `runs/20260729T2215Z-V26-handover-leak-ruling/RULING.md`.

> **Superseded by V26: the paper *is* repaired, and the names below are stale.**
> `BALANCED_EXTRA_CASES` no longer exists — the two states were applied directly to
> `_OPTIMAL_CASES`, and `flume`'s second item was additionally swapped for
> `((0, 7), (7, 1))` to falsify the "Box on the outer ring implies dead" reflex the
> repair would otherwise have sharpened. `test_the_sheet_carries_exactly_one_known_leak_and_no_other`
> no longer exists either; the pin was deleted, as the paragraph below instructs,
> and replaced by `test_level_multiplicity_is_uniform` plus
> `test_a_box_on_the_outer_ring_is_dead_for_a_reason_and_not_by_accident`. The
> paragraph is kept unedited because it records why V25 declined to repair, which
> was the right call at the time.

**The paper is not repaired here.** The repair is found and verified — a second
solvable state on each of `stile` and `cairn` (both 6-row boards, longest solution
11 actions; `('stile', (5,0), (2,4))` and `('cairn', (3,5), (4,1))`, after which
every level appears twice and the gate passes under every derived label set) — and
it is written down as `BALANCED_EXTRA_CASES` so nobody searches for it twice.
Applying it would silently turn `-r2` into results for a paper that no longer
exists, with nothing on the record saying its numbers were produced while the leak
was live. The repository's own precedent is that the fix and the void notice travel
together, and ruling on a sat run is not a leak checker's business. So the leak is
**pinned** by `test_the_sheet_carries_exactly_one_known_leak_and_no_other` — not an
xfail, which would switch the check off for this paper and reproduce the whole
family of defects V19–V25 chased — and the two collateral tests use the verified
balanced variant so the key-freezing mechanism stays exercised. Filed for repair
and adjudication as one item.

### The finding that outranks everything else V25 did: two of the four papers have no working token check

`group_power` was written to keep `ALPHA`'s promise -- a group too small for any
token to clear alpha is *untestable*, not clean -- and then, in the first pass, was
called from nowhere. An audit caught that (V21's defect, third instance in this
file, this time inside V25's own fix), and wiring it into `check_paper` produced the
number that matters most in this item:

**Six of the ten (paper, label set) groups on the shipped set cannot fire at all.**
Not "did not fire" -- *cannot*, for any token, on any paper content.

```
p15-heldout-a0    / event             n=80  classes=6  ceiling 0.800   CANNOT FIRE
p15-heldout-a0    / level_name        n=80  classes=5  ceiling 0.525   CANNOT FIRE
p15-handover-a0   / rule              n=11  classes=5  ceiling 0.545   CANNOT FIRE
p15-verdict-a2    / class             n=17  classes=3  ceiling 0.941   CANNOT FIRE
p15-verdict-a2    / witness_length    n=8   classes=3  ceiling 1.000   cannot clear alpha
p15-adaptation-a0 / label, verdict    n=6   classes=2  ceiling 1.333   cannot clear alpha
```

The cause is that the rule's statistic is two-class-shaped:
`(largest carrier class + largest non-carrier class) / n`, whose ceiling with m
answer classes is `2 * largest / n` -- roughly `2/m` when the classes are anything
like balanced, and so below the 0.90 tolerance as soon as m >= 3. `p15-heldout-a0`
is the 80-item paper and **both** its label sets are in this state; `p15-handover-a0`
has one label set and it is too.

So V21's headline -- "all four papers derive label sets and all four come back
clean, so the papers were in fact clean; what was missing was the looking" -- is
half true and half the same illusion one level down. Two of the four were looked at
by a statistic that could not have reported anything. `check_paper` now publishes
`metadata_multiplicity` on every paper, findings or none, carrying the cuts tried,
the family-wise rate and each group's `can_fire_at_all` / `untestable_at_alpha`, and
`test_a_multi_class_group_cannot_fire_and_the_report_says_so` fails if anyone quotes
those greens as evidence again.

**Not fixed here.** A statistic that works for m > 2 (one-vs-rest per class with its
own exact null, or an information-theoretic score) is a new judgement about what
counts as a leak, and this item has already learned what happens when two of those
share a diff. Filed.

**Open weaknesses this item leaves, in one place:**

1. The multi-class statistic above -- 6 of 10 groups untestable. Filed.
2. `v11-handover-a0`'s real leak, pinned not repaired, together with the ruling on
   `-r2`, whose numbers were produced while it was live. Filed.
3. The pooled private-marker cut is evaded by padding every item with a decoy
   marker; the rule that survives that is measured in `b5` and not shipped.
4. The multiplicity correction is charged per answer key, not across the label sets
   of one paper -- up to four of them -- so the published family-wise rate is still
   a floor. The count of label sets is in `label_sets_checked`, so the gap is
   bounded and visible, and `metadata_scan`'s docstring says so.
5. Nothing downstream consumes any of this: `papers/…/PAPER.md` §8.3 reads
   `leakage.json` only for item and probe counts, and still asserts
   `label_sets_checked: []` for handover and adaptation, which V21 falsified. That
   text is the paper track's to change, not this one's.

### What the other two adversarial reviewers found, all of it in V25's own work

Three reviewers, three real findings, none of them a re-read. The counter itself
survived **1,170,339 differential configurations** across three implementations
(the fast count, this module's oracle, and a reviewer's independently written
k-subset enumerator, so the oracle was itself checked) with zero disagreements --
including the exact float ties, tolerances below the majority floor, NaN and
infinity, zero-size classes, and `k` out of range. What it did find:

* **`_fires`' promise was a copy, not a call.** Its docstring says the counter and
  the gate cannot drift because they share the predicate; `_token_hits_within` wrote
  the comparison out inline instead. Two mutations of `_fires` survived all 66 tests
  in this area, because the counter and its oracle both route through it and move
  together, so the agreement test is structurally blind. The `>=` survivor matters:
  9/10, 18/20, 36/40 and 72/80 are all *exactly* the double 0.90, so the tolerance
  sits on a reachable tie on any group whose size is a multiple of ten -- n=80
  included -- and under that mutant the published rate moves off zero while the gate
  still does not fire. The gate now calls `_fires`, and
  `test_the_published_rate_and_the_gate_agree_on_the_exact_tie` kills the mutant.
  Dropping the `1e-9` is an *equivalent* mutant inside `_fires` (integer `best` over
  the same denominator as the floor; 7548 configurations, no change) and that is now
  written down, so nobody hunts for a test that cannot exist.
* **`group_power` swept from k=2**, on the reasoning that single-holder tokens are
  never scored -- true of tokens, false of the check, since the pooled cut can hold
  one item and does on the M5 fixture. It understated the power of exactly the
  groups it exists to describe. It also had no memoisation and did not use
  `p(k) == p(n-k)`, costing seconds per group at a few hundred items, times four
  label sets. Fixed: k from 1, `lru_cache` keyed on the sorted class sizes, sweep to
  n//2, and the complement symmetry the family-wise product silently rides on is now
  a test rather than an assumption.
* **`group_power` was dead code**, and the multiplicity keys lived only on findings
  so a clean paper published none of them -- V21's defect, third instance in this
  file, both times inside the fix meant to end it. Also: the coverage record was
  guarded by `if coverage["single_holder"]:`, so a field that scored three tokens and
  skipped none said nothing at all, which is what the comment three lines above it
  forbids -- two of the four shipped papers published no token coverage because of
  it. And `findings[:8]` truncated metadata findings out of the exception message,
  losing `p_fire` and `weak_evidence` at the exact moment a human is summoned to
  adjudicate. All three fixed; the exception now carries `findings`, `multiplicity`
  and `metadata_unscored` as attributes rather than only as an f-string.

**One process note, because it cost a verification run.** A reviewer instructed to
write only under `/tmp` mutated `exam/leakage.py` in place to run its mutation test,
restoring it 65 seconds later, and disclosed this when asked. One full-suite run of
mine executed against a mutated threshold. The final verification therefore hashes
`leakage.py` before and after and asserts it did not change. The general rule worth
keeping: a subagent reviewing a file the main session is mid-delivery on must return
findings only, and the main session does every write.

## V26 — the second leak went into the same two items, and it was annulled rather than voided

Prompt `V-V26-handover-leak-ruling`, worker `RES-3`, branch
`agent/v26-handover-leak-ruling`. Run
`exam/runs/20260729T2215Z-V26-handover-leak-ruling/` — the ruling itself is
`RULING.md` there and is the citable source; this is the index entry.

**The repair.** Family-scoped `level:` multiplicity predicted the dead/alive
answer 8 of 8 on the `optimal_action` family at an exact `p_fire` of
1/28 = 0.035714. `stile` and `cairn` each held their level name once and were
exactly the two dead boards. Two appended solvable states —
`('stile',(5,0),(2,4))` and `('cairn',(3,5),(4,1))` — put every level at two
items, and the rule is now inert. `exam/verify.py` GREEN, 385 passed, 2 xfailed.

**The ruling on `-r2`.** Annulled as an *instrument* on `optimal_action`, not
voided as a record: no number from that family may be cited as evidence about
the dead boards, while the 36 shortest-plan integers stand, since the channel
carries zero bits about them. Not a void, because nothing rests on the run
(`delta 0.0`, `conclusive false`), the channel could only inflate scores that
were already at ceiling, and the run's headline was already `[OVERTURNED]` on a
stronger ground. Cohort 1 printed the literal word `dead`; using one word for
both severities would make the word stop carrying information.

**Three corrections to what was on the record here, all re-verified from files.**

* V25 wrote that r2's six readers "disagreed with each other on the solvable
  ones". They disagreed; none was **wrong**. All six scored 58.0/58.0, 31
  correct, 0 wrong, 0 abstained. Marking is set-valued, every split fell inside
  the true optimal set, the one singleton-optimal item drew unanimity, and
  `plan_len` was unanimous throughout. That is the fingerprint of six
  independent searches — **exculpatory**, and V25 cited it as incriminating.
* The rule is 8 of 8 only *family-scoped*. Whole-sheet, `level:` also rides the
  seven `step_semantics` items (`stile` 1, `cairn` 2, `flume` 3, `kiln` 4,
  `warren` 5), so the unscoped rule scores 7 of 8 and misses `cairn` — the board
  `PREREGISTRATION.json` named in advance as the sharpest. The gate always
  grouped by `kind` and was never wrong; only the prose was, in three places.
* `per_item` cannot answer questions about agreement — under a set-valued marker
  it shows 2.0/2.0 for readers who disagree correctly. Only `answers/` can. I
  drew the wrong conclusion from `per_item` first, which is why this is written
  down rather than merely fixed.

**A channel found, measured, and ruled *not* a leak.** The repair sharpened a
different predictor — "answer `none` iff the Box is on the outermost ring" —
from 8/8 to 10/10, `p_fire` 0.022222. It is a sound consequence of the world's
rules, not metadata predicting an answer: a Box on an edge can only be pushed
along that edge, so the rule's truth tracks whether the *target* is off the
ring. It holds on the four levels whose target is off the ring and fails exactly
on `flume`, whose target is on it. Pinned by
`test_a_box_on_the_outer_ring_is_dead_for_a_reason_and_not_by_accident`, which
asserts the conditional invariant rather than the purity — the dangerous edit is
the rule staying pure while ceasing to be derivable.

**Five defects found in V26's own work and fixed in it — the count went from two
to five on a second pass, and the pattern is the point.** The test certifying the
repair asserted `report.get("metadata_hits", 0) == 0` against a key `check_paper`
does not have — vacuous, and it passed on leaky papers. Fixing that one did not
fix the two identical ones **three lines above it**: `probe_hits` and
`structural_hits` are literal `0` constants in `check_paper`'s return dict and it
*raises* on a hit, so those assertions could not fail either. One of the
replacements was itself vacuous (`"tags" in report["metadata_fields_checked"]`
restates a module constant). `write_manifest.py` hashed `MANIFEST.json` into
itself, so its self-entry could never verify. And the repair adds the sheet's two
easiest items (`plan_len` 11, one push) to a sheet whose recorded failure is
saturation — 11 is the exhaustively-searched ceiling on those two 6-row boards, so
that trade is forced; future hard items belong on `warren`/`flume`/`kiln`.
**Fixing one instance of "a check that cannot fail" does not fix the ones next to
it, and the satisfaction of having fixed one is what stops you looking.** Every
new assertion in the commit was mutation-tested to red before being trusted.

**Closed on the second pass, after being filed as unclosable.** The first version
of this entry said the sheet cannot separate a reader who checks the target from
one who reflexively calls every edge-Box dead, and recorded that as a structural
constraint of the board set "so it is not re-searched". A second adversarial pass
refuted it, and that is the worst of the errors here precisely because it was
written down to stop anyone looking again. The constraint binds only on *adding*
an item: `flume`'s target is on the ring, so it admits **110** solvable ring-Box
states, and the longest — `((0, 7), (7, 1))`, 17 moves — **replaces** `flume`'s
second item rather than joining it. Multiplicity stays uniform at 2 per level, the
direction spread is unchanged, and the reflex now scores 2 of 3 and is wrong on
this sheet. What remains is narrower: `stile` and `cairn` still contribute only
dead ring-Box items, so the two boards that pose the `none` question cannot
themselves falsify the reflex.

**Channel census on this sheet: five, of which one still stands.** `dead` in
`tags` (voided); `PREREGISTRATION.json` persisted into the readers' own run dir
(fixed); `v11-why-02`/`v11-why-05` restating the playbook's two `prune` rules on
the tier-1 sheet, jointly a complete classifier (`[OVERTURNED]`, **not
repaired**); family-scoped level multiplicity (this run); smallest-board (closed
as a side effect, 2 of 2 → 2 of 4). **No further run on this sheet is worth six
readers until channel 3 is closed.**

## V6-V23 — class (ii) was finally tested, and its central claim was false

Prompt `V6-V23-large-space-verdict-gap`, worker `RES-3`, branch
`agent/v6-v23-large-space-verdict-gap`. Run
`exam/runs/20260730T021500Z-V23-large-space/` — the criterion argument is
`CRITERION.md` there and is the citable source; the durable form is D-EX-028.
This is the index entry.

**The withdrawal, which is the result.** `exhaustive_feasible: False` asserted
that no exhaustive method is feasible on a class (ii) board. That is false, and
`crux_quotient_settles.json` puts a number on it: **every shipped class (ii)
item is settled by an exhaustive computation over at most 600 nodes in at most 5
ms**, against claimed bounds of 1.15e18 to 1.33e36 — ii1 by components of
`relaxed_edges` on 300 nodes, ii2 by the same pass with the cut cell deleted, ii3
by a relaxed distance of 199 against a budget of 150, ii4 by the surviving column
deltas being {0, 0, +1}. Four *different* mechanisms; an earlier draft of the
probe assumed one pass settled all four and the measurement refuted that for
three of them. The field is withdrawn and replaced by
**`naive_enumeration_feasible: False`** — forward enumeration over the full
(cart, button, latch mask) state, the method class (i) is graded on, cannot
terminate here. Measured, and narrower. An item whose own answer key is an
exhaustive walk of a 300-node graph cannot also claim that exhaustive walks are
infeasible on it. Theoria.md:259's 「我们的主场」 claim — "exhaustion is
infeasible, only invariant reasoning can answer" — does not survive; what class
(ii) measures is **method selection under an apparent search barrier**.

**The quotient's unsoundness is one-sided, and D-EX-022's disclaimer is amended
rather than reversed.** The quotient over-approximates, so it can produce false
*solvable* and never false *unsolvable*. D-EX-022 read that as grounds to
distrust the number and was right to withdraw `search_credible` from it; for the
refutation direction the same fact is the alarm bell that the barrier is apparent
rather than real, and it is why "start and goal in different components" is a
sound unsolvability proof and the item's own key is allowed to be computed that
way. `quotient_note` now carries both halves.

**The criterion is conjunctive, and both halves are measurements.** An item earns
class (ii) only on (c) a search-free constructive bound of 2^m distinct reachable
states, premises checked at the point of claim, *and* (b) the reference
enumerator measured to truncate at the shipped cap. A reachable-state threshold
alone was rejected: at the time `LARGE_SPACE_THRESHOLD = 10**12` had no entry in
`DECISIONS.md` at all, and it was being applied to a count the class (ii) path
never took — a threshold over an asserted quantity. Measured solver
failure was rejected for a stronger reason than engine-rig's D-024 — on these
boards the strong solvers **win in milliseconds**, so that criterion is not
merely inadmissible but false. The controls are executable, not narrated: a
400-switch board on a 200-cell corridor that truncates at the cap exactly as
ii1..ii4 do is still refused on its bound of 2^8, pinned by
`test_a_truncating_board_is_still_refused_without_a_bound` — if truncation alone
earned the label, a board 30 orders of magnitude smaller than ii1 would ship as
class (ii) on the strength of a cap we chose ourselves.

**The record was counterfactual, and the scope was wider than the class.**
`_large_space` hardcoded `"truncated": False` beside `"enumerated": None` — true
only because no enumeration was ever attempted, and reading as though one had run
and come back clean. It is now `enumeration_attempted: False` with `truncated`
null. `_large_space` is called by **seven** items, not four (ii1..ii4 plus the
three `solvable_hard` ones), so the enumerator check is scoped by the record
rather than by the class.

**A bound must defend its own premise where it is claimed.** Every guard on class
(ii) truth fired *after* the record was written: a `comb_open` whose switch list
repeats one cell 60 times produced 2^60 = 1.15e18 on a board with **359**
reachable states and `_large_space` stamped it. `build()` did abort before
returning a paper, so nothing false shipped — but a bound that survives only
because a distant caller happens to check is not a bound. `subset_lower_bound`
now refuses it itself, gated on `candidates[:m]` rather than `level.switches` so
a repeated entry naming a wall is not a false refusal.

**The extrapolation is licensed at the exponent only.** Enumerated to completion
with nothing fitted: gantry, lattice and the unbudgeted spindle give
`2k·4^k = 2k·2^m` exactly at every k with m = 2k; orchard gives `(8/3)(2^m − 1)`
with **m = 2(k−1)**, which is why shipped ii4 reports m=118 and not 120. Sound at
every rung, loose by 2k or 8/3, verified over 5.77 orders of magnitude — and it
does **not** cover ii3, whose m=60 comes from `step_limit=150` rather than from
its 400 switches.

**No shipped engine can walk the invariant path, and the adapter a reader would
write is silently unsound.** `lp_potential` is a peg-solitaire engine: every
expressible transition has coefficient sum −1, verified exhaustively at n_pos=5,
while an A2 cart move has sum 0 or +1, so no role assignment expresses an A2
transition at any size — the materialised-edge-list obstacle is real but
secondary. Encoding a comb level and running it anyway returns `certified` at
every size, **including at corridor 4 where the level is solvable**, with all
four of the engine's self-checks agreeing because all four read the same wrong
move list. `ic3_pdr` enumerates up front, `fd_adapter`/`probe_frontier` need
grounded PDDL and no A2→PDDL compiler exists, `zero_space` re-checks only its own
sample, `cegis_miner`/`mdl_segmenter` mine candidates and never verdicts. What
does walk the path is the exam's own `check_certificate`, ≤3.1 ms per item, with
zero connection to `engine-rig` — so "engines propose, the LLM adjudicates" has
no engine on this path today. Not fixed: it is an engine-rig change, requested
in `monitor/inbox/20260730T071500Z-RES-3-two-findings-that-say-filed-but-are-not-on-the-board.md`.

Tests: **465 passed, 2 xfailed**. `python exam/verify.py` GREEN. Zero API, zero
network, zero sealed-pile contact.

### Closed by V6-V23

* ~~**27. The class (ii) name still overstates what a naive enumerator faces.**~~
  Settled, and against the class: rewritten above as a measured falsehood rather
  than an open question. D-EX-028.

### Open weaknesses V6-V23 adds

31. **The quotient can exceed the true reachable count, and a shipped item does
    it.** Class (i) item i4 enumerates to 31 states and reports
    `positional_states` 55, because `positional_states` ignores `step_limit`
    while `enumerate_states` honours it. That is a live shipped instance of
    exactly the unsoundness `quotient_note` warns about, now with a number on it.
    Recorded, not fixed.
32. **The sealed drill's class (ii) gap is structural, not incidental.**
    `GridWorld.reachable(limit=200_000)` (worldgen/core/world.py:259) *raises*
    above the limit, so worldgen cannot build a world that a naive forward
    enumeration cannot exhaust — the catalogue does not merely happen to lack
    one. `DRILL.json`'s `classes_absent: ["large_unsolvable"]` therefore cannot
    be closed from inside `exam`; it needs a worldgen change.
33. **No engine can produce a class (ii) certificate, and the natural adapter is
    unsound in the worst direction.** See the `lp_potential` paragraph above. A
    silent unsoundness toward "proved unsolvable" is the single worst failure
    this exam can have, and the next reader to reach for that engine will not
    find it out by running it. Filed for engine-rig, not fixed here.
