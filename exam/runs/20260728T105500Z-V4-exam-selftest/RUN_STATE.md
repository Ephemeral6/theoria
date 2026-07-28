# V4-exam-selftest — RUN_STATE

Worker RES-1, lane `campaign`, territory `exam`. Zero API, zero network, zero
sealed-pile contact. Written incrementally as the work happens.

## The audit that came first, and why it changed the plan

The item asks for three things. Before building anything I measured what P-15
and V2 had already shipped, on `master` at `98593a0`:

| item asks for | already on master | verdict |
|---|---|---|
| (1) marker calibration with known-full / known-zero fakes | `exam/grading/calibration.py`: four fakes, `oracle == 1.0` and `null == 0.0` exact on all four papers, pre-registered bands, `assert_calibrated` hard-blocks real marking | **delivered** — rebuilding it would be theatre |
| (2) one item per verdict class in a self-built world family, each with a constructive justification | `exam/papers/verdict.py`: 17 items, `small_unsolvable` 5 / `large_unsolvable` 4 / `solvable_hard` 8, every one carrying a `spec` emitted to `artifacts/variant_specs/` and validated by constructing a real `proxy.variants.Variant` | **delivered, and beyond the ask** (17 items, not 3) |
| (3) sensitivity and specificity scored separately, plus a matrix | `grading/mark.py:confusion()` returns the pair and never blends it; calibration asserts the bluffer at 1.0/0.0 | **half delivered** — the pair exists for one fake on one paper; no matrix, and no per-class split |

Commands behind the table are in [`AUDIT.md`](AUDIT.md).

So two thirds of the item as literally written is already on disk. Reporting
that and stopping would satisfy the letter of the item and none of its point.
The point is in the item's own parenthesis — **现在没人验过判卷的人** — and that
sentence is still true after the audit, for a reason the existing calibration
cannot fix by itself:

> `oracle == 1.0` and `null == 0.0` pin the marker at its two **endpoints**.
> A marker can be exactly right at both ends and wrong everywhere between them.
> Nothing on master perturbs a submission by a known amount and checks that the
> score moves by the amount predicted, and nothing breaks the marker on purpose
> to check that the calibration would notice.

That is the gap this run fills.

## What is being built

1. **`exam/grading/selftest.py`** — the marker's self-test, two halves:
   * **submission-side mutants**: mutate a ground-truth submission by a known
     amount and assert the score moves by the *exactly predicted* amount —
     per-item independence, additivity, permutation invariance, transplant
     rejection, monotonicity under increasing corruption. These probe the
     middle of the marker's range, which the endpoints cannot reach.
   * **marker-side fault injection**: break the marker in named ways (pay for
     silence, reject truth, mark by position, blend the sens/spec pair) and
     require that some existing check catches each fault. A fault nothing
     catches is a hole in the calibration, and gets reported as one.
2. **the detection matrix** — fault × check. The zeros are the finding.
3. **the sensitivity/specificity matrix** — examinee × verdict class, the two
   rates always side by side, never a blended accuracy.
4. **closing STATUS open weakness 3** — the rubric digest does not cover the
   calibration bands, so a quiet widening there is invisible. Named in the
   source itself (`calibration.py`, comment above `EXPECTED`).
5. **a cheater subagent against the fixed sheets** — STATUS open weakness 11:
   two cheaters, four sheets, one pass, and no adversarial reader has seen the
   sheets *since the two leaks were fixed*.

## Progress log

* `2026-07-28T10:55Z` — worktree `.worktrees/v4-exam-selftest`, branch
  `agent/v4-exam-selftest` off `98593a0`. Baseline suite on the branch before
  any edit: **253 passed** (`python -m pytest exam/tests -q`). STATUS.md still
  says 157; V2 added 96 and did not update the line. Noted, not yet fixed.

* `2026-07-28T11:20Z` — **the first mutant run found a live defect in a shipped
  rubric.** `mutant_battery_all()` came back with one failure:

  ```
  adaptation/garbage: structured nonsense was awarded 1.600000 of 144.000000
  ```

  Traced to `rubrics_adaptation._read_index`, which had two outcomes where it
  needed three. Everything it could not parse fell through to "did not claim a
  detection", and the caller wrote that down as the substantive answer `never`.
  Measured, all four spellings of *nothing*:

  | submission | adaptation score |
  |---|---|
  | `"__V4_GARBAGE__"` on every item | 1.600 / 144 |
  | `""` on every item | 1.600 / 144 |
  | `{}` on every item | 1.600 / 144 |
  | `null` on every item | 1.600 / 144 |

  and every one of those 1.6 points sits on the two `v-a0-03.detect` items —
  the variant `README.md` singles out as **undetectable on its base level**,
  where `never` *is* the truth. `v-a0-03.detect.match` paid **1.0 of 1.0**, in
  full, to a submission containing no answer at all.

  So the paper's hardest item — can you tell "the change is invisible from
  here" from "I did not look" — was being failed by the marker itself. The
  other three papers pay exactly 0.000 for the same four submissions, which is
  why nothing had ever noticed.

  Fixed in `_read_claim` / `_read_level_claim`: illegibility is now a third
  outcome, scored `wrong` with `said: "unreadable"`. One asymmetry is
  deliberate and documented — a *bare* `null` is illegible, a `null` under a key
  the examinee wrote down (`{"per_level": {"match": null}}`) is a legible
  "never", because presence of the key is the claim. That is the spelling the
  reference answers use, so the distinction is load-bearing.

  **No calibration number moved**: oracle 1.0 / null 0.0 / memoriser 0.1708 /
  bluffer 0.1708 before and after, on all four papers, and 253/253 tests still
  pass. The fix removes credit for illegible answers and nothing else — it is
  not a re-tuning wearing a bugfix's clothes. That no existing test failed is
  itself the finding: nothing covered the illegible path.

* `2026-07-28T11:32Z` — **fault matrix, first run: one fault escaped everything.**
  Eight faults injected, baseline clean, `truncates_partial` (partial credit
  silently zeroed) caught by **no check at all**. The reason is structural and
  general, not an oversight in one band:

  > every band in `calibration.EXPECTED` for the two informative fakes is
  > `Band(0.0, x)` — bounded above, open below. A marker that *depresses*
  > scores satisfies all of them. `oracle == 1.0` is the only lower bound
  > anywhere, and it only sees answers that are already full credit.

  The calibration is one-sided. Closed with a seventh mutant,
  `partial_credit_survives`: remove one component of a composite answer and a
  paper whose rubrics award partial credit must produce a score strictly
  between zero and full. Structural, not a number fitted to the first run —
  and declared **inapplicable** rather than passing on `heldout`/`handover`,
  whose answers have no removable component (D-EX-011's lesson: a check that
  cannot run is not a check that passed).

  Second run: **8 of 8 faults caught, baseline clean.** `truncates_partial` is
  caught by the new check alone, which is what makes it worth its weight.

* `2026-07-28T11:50Z` — papers rebuilt (`python -m exam.tools.build_papers`) because
  the rubric edit moves `registry.digest()`. Two things changed in the sheets,
  and only one of them is mine:

  * `rubric_digest` `f7793742…` → `e06bdf52…` — the adaptation fix, expected.
    `rubric_module_digest` on the verdict sheet is **unchanged**, which is the
    per-module seal doing exactly what it was added for: an edit to the
    adaptation rubrics does not disturb the verdict paper's seal.
  * `generated_worlds_available: 20` appears on every sheet. **That one is not
    mine.** It comes from `guard.provenance()` on master, reading the tracked
    roster `worldgen/out/worlds/INDEX.json`. The checked-in sheets predate the
    20 worlds, so `master`'s artefacts were already stale against their own
    builder — anyone running `build_papers` on master got a different file than
    the one committed. Deterministic (the roster is tracked, not environment
    state), just not regenerated. Fixed by this rebuild; reported rather than
    folded silently into my diff.

* `2026-07-28T12:00Z` — **cheater pass against the fixed verdict sheet, and it
  is the sharpest result of the run.** Weakness 11 said no adversarial reader
  had seen the sheets since the two leaks were fixed. One has now.

  The subagent got `p15-verdict-a2.brief.txt` and nothing else, was told to
  cheat rather than solve, and returned all 17 claims. Scored by the referee
  against the key rather than self-reported:

  | | |
  |---|---|
  | claims correct | **17 of 17** |
  | its own estimate | 13.8 of 17 — it *under*-predicted itself |
  | majority-class baseline | 9 of 17 = 0.529 |
  | per class | small 5/5, large 4/4, solvable_hard 8/8 |
  | **score on the real rubric** | **17.0 / 34 = 0.5000** |

  The cap at exactly one half is the paper's defence working: every item pays 1
  point for the claim and 1 for the reason, and it submitted no certificate and
  no witness anywhere. The rubric's own line — *"without it the claim is
  indistinguishable from a guess"* — stops being a sentence and becomes a
  measurement.

  **What it actually exploited, in its own accounting and mine.** Most of its
  leverage was cheap arithmetic on the ASCII board — budget versus Manhattan
  distance, an all-`#` row separating start from goal, a hazard sitting on the
  only non-wall cell of its row. That is not a leak: the board *must* be on the
  sheet, and reasoning about it cheaply is solving cheaply. Three of its seven
  exploits are genuine sheet structure and are the ones worth recording:

  * **X5** every `relabelled` field is `{LEFT: RIGHT, RIGHT: LEFT}`, a bijection
    on a command set containing both, so it is provably a no-op — a decoy that
    can never bite, on all 4 items carrying it;
  * **X6** 17 items over 5 distinct grid skeletons, several byte-identical, so
    an item whose grid matches another's under a weaker wrapper inherits its
    answer without any reasoning;
  * **X7** exactly one item has every wrapper at its default, and an exam that
    states wrappers per item includes an unrestricted positive control.

  It also reported honestly that the naive metadata cheat — "any non-default
  wrapper means unsolvable" — scores 9 of 16, barely above chance, because the
  builder paired every biting wrapper with a non-biting twin. The `points`
  leak that P-15's cheater found is confirmed dead: `points` is 2.0 on all 17,
  and `question` is byte-identical on all 17.

  **The finding that outranks the score.** The cheater is now a row on the
  confusion matrix, and it is byte-identical to the oracle's row in every cell:

  ```
  | `oracle`     | 1.0000 | 1.000 (9/9) | 1.000 (8/8) | ... |
  | `cheater-v4` | 0.5000 | 1.000 (9/9) | 1.000 (8/8) | ... |
  ```

  Sensitivity and specificity — split by class, with coverage printed — **cannot
  tell ground truth from a reader who never saw the world.** Only the score
  separates them, and on this paper the score means the certificate half. The
  matrix now computes and prints its own collisions rather than leaving that to
  a reader's eye.

* `2026-07-28T12:25Z` — **cheater pass against the fixed held-out sheet: three
  claims, and only checking them tells you which are real.** The subagent got
  `p15-heldout-a0.brief.txt` and nothing else. Every claim below was verified
  mechanically against the key before being believed or acted on — STATUS's
  standing rule that an unverified cheater is just another confident agent, and
  this pass is the sharpest illustration of it yet.

  | claim | as stated | verified |
  |---|---|---|
  | **E1** `instructions` names the genre while `world.description` says the dynamics are withheld | decides 80/80 | **confirmed verbatim** — the sheet contradicted itself |
  | **E2** the replay/heldout split is recoverable from box coordinate parity | 79/80 | **confirmed exactly: 79/80 = 0.9875** |
  | **E3** six items' answers are printed as other items' inputs | 6 items, confidence 0.97 | **refuted: 0 of 6.** A full 80×80 successor scan finds **one** real instance, `a0h-074 → a0h-042`, which it did not name |

  **E1 is real and its yield is negative, which is the interesting part.** A0's
  push slides the box **two** cells — a0-spike's `push2`, the T-9 finding this
  whole paper is built around. Vanilla sokoban slides it one. The cheater took
  the genre name, predicted one-cell pushes on six items at confidence 0.97,
  and scored **0 of 6**. Where it scored, it scored on items needing no
  dynamics at all: **9 of 9** on the edge-blocked and wall-blocked items, which
  is precisely the 26/80 = 0.325 null baseline it had itself identified as the
  floor. Its own forecast was 60–72 of 80.

  So a **confirmed information leak can have negative yield when what leaks is
  a wrong prior**, and the cheater was most confident exactly where it was
  entirely wrong. By the item's acceptance condition — 榨得出即验收失败 —
  the sheet passes: nothing was extracted above the floor.

  **Fixed anyway, and not because of cheating.** The four words are gone from
  `INSTRUCTIONS`, with the measurement recorded above the constant and a
  regression test (`test_no_sheet_names_the_genre_of_the_world_it_asks_about`)
  over all four sheets. The reason is that this paper exists to ask whether a
  theory learned `push2` from evidence instead of assuming push-one from a
  prior — so a sheet naming a genre whose rules differ from the world's is not
  a neutral question with a harmless hint in it. It is an undeclared second
  experiment, and nobody registered it.

  **E2 is confirmed and left unfixed, deliberately.** All 40 replay items put
  the box on both-odd coordinates, drawn from just **7 distinct cells**; the 40
  held-out items use **29**, and only one of them lands on the sublattice. So
  the two halves are not distributionally matched at the level of *state*, and
  a memorising theory can tell which half it is standing in without reading the
  tag. It leaks nothing about the *answers* — the answer-class stratification
  is exact to the item, 4/5/4/5/16/6 in both halves — so the sheet's promise
  that the tag carries no information about the answer holds. Fixing it means
  resampling the held-out split, which changes the paper substantively and
  belongs to its own run with its own pre-registration. Recorded as a new open
  weakness rather than patched at the end of an unrelated one.

  **E3's one real instance** (`a0h-074`'s answer is `a0h-042`'s input, both
  `replay`) is likewise recorded, not patched: it is inside the replay half,
  where the frames are drawn from a trajectory and consecutive states are
  *expected* to appear as each other's neighbours. A successor check at
  generation time would catch it; that is the same resampling run as E2.

## What was delivered, against what the item asked

| the item asked for | what happened |
|---|---|
| (1) 判卷器标定，已知满分/已知零分假被试 | **already shipped** by P-15 and verified here; what was missing was the middle of the range, and that is `grading/selftest.py` — 7 mutants, 8 injected faults, a detection matrix |
| (2) 三类判决题各出一题，带构造性依据 | **already shipped** at 5 / 4 / 8 items with 17 specs; verified rather than rebuilt (`test_all_three_verdict_classes_are_present_with_a_constructive_spec`), which also pins that `class` is on the truth side only |
| (3) 灵敏度与特异度分开打分 + 一张矩阵 | **built** — `grading/confusion_matrix.py`, `artifacts/matrix/verdict_confusion.{json,md}`, split by class, coverage in every cell, collisions computed |
| 红线：零 API、封存堆零接触 | held — no socket is opened anywhere in `exam/`, `verify.py`'s self-test stage runs inside `guard.no_network()`, and no pile game was read, played or named |
| 红线：作弊者 subagent，榨得出即验收失败 | **two** cheaters, on the two sheets that changed. Neither extracted answers above the floor: the verdict cheater capped at 0.5000 for want of certificates, the held-out cheater scored the null baseline and 0/6 where it used the leak. Acceptance holds — and both passes produced findings anyway |
| 红线：出题真值与被试严格隔离 | the cheaters were given one file each and told so explicitly; both reported reading exactly that file, and every claim was scored by the referee against the key rather than self-reported |

## Gaps — what this run did not do

1. **The two held-out defects are recorded, not fixed** (new STATUS weaknesses
   12 and 13). Both need the held-out split resampled — box positions drawn
   from a matched sublattice, and a successor check at generation time — which
   changes the paper substantively and needs its own pre-registration. Patching
   a paper at the end of an unrelated run is how a sheet ends up with an
   undeclared second experiment in it, which is the exact mistake E1 was.
2. **`adaptation` and `handover` were not re-attacked.** Their sheets are
   unchanged since P-15's pass, so they are as attacked as they ever were —
   once each. That is a sample, not a proof.
3. **One examinee per cheater pass.** Same n=1 caveat as the fresh readers.
4. **The fault list is eight faults chosen by one mind.** The matrix says every
   one is caught; it cannot say anything about a fault nobody thought to
   inject. `truncates_partial` was uncaught until it was written down, and the
   next one like it is also currently uncaught.
5. **`partial_credit_survives` is inapplicable on two of four papers.** It
   declares that rather than passing, but it means the marker's middle range is
   probed on `adaptation` and `verdict` only.
