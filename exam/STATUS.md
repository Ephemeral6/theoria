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

**And the class (ii) premise itself is false.** The four class (ii) levels have
**180, 180, 600 and 177** reachable `(cart, button)` states. Latching is
monotone and gates no geometry, so the quotient decides the question and a
complete search is a second's work. The rubric was reading `search_credible:
False` off the raw product bound and telling an examinee that had honestly
searched: *"'I searched it all' is not a reason, it is a false statement about
the search."* That sentence was the false statement, and it was aimed at the
four items where the examinee had done the better thing. `search_credible` is
now derived from the quotient. D-EX-022.

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

Tests: **334 passed** (321 before). `python -m exam.verify` GREEN, determinism
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
27. **`positional_states` is measured, and the class (ii) construction is not
    rebuilt around it.** D-EX-022 stopped the marker asserting a falsehood; it
    did not make class (ii) mean what its name says. Switches that gate geometry
    would, and that is a different world family and a different paper.
