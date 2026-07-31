# exam — Theoria's active instrument, rehearsed offline

> 评测分两器：**被动器**——指标电池，直接从轨迹账本读出，不打扰、免费、可回算
> 历史；**主动器**——考卷，要出题新跑。 — `Theoria.md` 1.11

[`battery/`](../battery/) is the passive half: it opens ledgers that already
exist. This is the active half. It **sets questions** and needs a new run, and
that is the whole difficulty — an exam has to have ground truth, ground truth
has to come from construction, and the construction has to stay away from the
examinee.

Everything here is a **dress rehearsal in self-built worlds** (A0, A0′, A2).
Zero API calls, zero model calls from the code, zero network, zero contact with
the sealed pile. By Phase 4 the operator library, the spec format, the leak
checks and the marker are all proven; the only new work when a sealed game is
finally opened is that game's own justification.

```bash
python -m exam.verify                  # the whole territory, one command
python -m exam.tools.build_papers      # set the papers; split sheet from key
python -m exam.tools.run_exam          # calibrate the marker, then mark
python -m exam.tools.run_selftest      # test the marker between its endpoints
python -m pytest exam/tests -q         # 338 tests
python -m exam.tools.archive_run <id>  # runs/<id>/MANIFEST.json
python -m exam.tools.build_prereg      # endpoint 2's pre-registration + controls
python -m exam.tools.endpoint_verdict --table   # the controls, and what kills each
```

## The third primary endpoint

`Theoria.md:373` names 判决题准确率(含特异度) as one of three primary endpoints.
[`PREREG_VERDICT.md`](PREREG_VERDICT.md) is exam's half of its pre-registration —
scoring rule, per-arm per-class predictions with refutation conditions,
sensitivity and specificity as separate numbers with separate floors — and
[`endpoint.py`](endpoint.py) executes it. Two rulings of `freeze/STATS_RULES.md`
§2 land here because the implementation it cites does the opposite: 弃权计错 is
a **layer** over `mark.confusion()` rather than an edit to it, and the class-(ii)
coverage floor routes to 不可结论 rather than 不成立. Both are registered launch
blockers (`freeze/launch_blockers.json` 9.15, 9.16) and both now have a command
and two targets. D-EX-033.

Seven controls run before any arm does, and each of the three floors refuses
exactly one of them on its own — measured by leave-one-out on every verify run,
not asserted. The one the endpoint credits and should not (`cheater-v4`, a
sheet-only reader, separated from ground truth by `certified_share` alone) is
printed in the same table.

## The four question types

| type | paper | items | pts | what it catches |
|---|---|---|---|---|
| held-out prediction | `p15-heldout-a0` | 80 | 80 | a theory that replays perfectly and cannot predict |
| layered handover | `p15-handover-a0` | 29 | 46 | understanding that lives in a session rather than a document |
| rule-change adaptation | `p15-adaptation-a0` | 60 | 144 | a theorem that quietly became false |
| three-class verdict | `p15-verdict-a2` | 17 | 34 | a framework that says "unsolvable" too readily |

Each is one module under [`papers/`](papers/) behind one interface — `PAPER_ID`,
`build()`, `reference_answers()`, `axes()`. The runner does not know what a
held-out item is, and a fifth type is a new module rather than an edit to the
driver.

### 1 · held-out prediction — the gap is the measurement

Theoria.md is specific about why replay is not enough: 重放是对过去的预测，背题也
能满分. So the paper carries **both**: held-out items drawn from the 39,960
(state, action) pairs the evidence set never witnessed, and a replay control
drawn from the evidence set itself, **with identical class quotas**, so the
`replay`/`heldout` tag on the sheet carries no information about the answer.

The headline is `gap_replay_minus_heldout`. A rule-learner is near zero. The
calibration memoriser scores **1.00 on replay, 0.15 on held-out — a gap of
0.85**, and its held-out breakdown is `blocked_crossing` 0/5 against 5/5 on
replay. That single cell is a0-spike's T-9 finding reproduced mechanically: the
under-guarded `push2` rule was exact on every replayed transition and wrong on
the guard, and in a single percentage it would have shown up as 97%.

Guard classes are over-sampled on purpose (`blocked_crossing` 104×), and the
over-sampling factors are published on the sheet next to the natural shares.

### 2 · layered handover — two tiers, and a fresh reader each

Two bundles under [`handover_bundles/`](handover_bundles/): the manual alone,
and the manual plus the playbook. Each is self-contained — a reader gets the
bundle and the sheet and nothing else, no repository, no history, no earlier
conversation. `READER_BRIEF.md` in each bundle publishes the exact answer
grammar, because a rubric that has to guess what a reader meant is not frozen.

Three families: step semantics, **which names are level data and which are world
law**, and optimal action from a given state. The middle one is the one that
separates a reader who understood the manual from one who pattern-matched a
single board.

`tier2_minus_tier1` is the value of strategic knowledge. `reader_minus_author`
is 新读者打平作者 — the author baseline is the deliverable's own compiled
executable answering the same sheet mechanically, computed and stored in the
truth file, never on the sheet.

An arm with no deliverable scores zero **by construction**, via a real code path
(`no_deliverable_submission()`), not a hardcoded zero.

### 3 · rule-change adaptation — the collateral is the point

Six variants, enumerated over the world's `Rules` fields rather than hand-listed,
each with truth derived mechanically. The sheet never names the changed rule:
variants are `v-a0-01`…`v-a0-06` and the mapping lives only in the truth file.

Four families — `detect`, `describe`, `collateral`, `repair` — with collateral
carrying 41.7% of the marks, because it is the one that matters. `[depends:
push2]` is not decoration: under `v-a0-02` and `v-a0-05` the mismatch level
becomes **solvable**, and a framework that skipped the dependency step would go
on confidently declaring it impossible.

That failure is a named axis, not a percentage: **`silently_wrong`**. The
calibration memoriser trips it twice. The bluffer, which claims everything is
invalidated, trips it zero times and scores the same total — the two are
separated only by `axes()`, and that coincidence is the argument for the flag.

One variant, `v-a0-03`, is **undetectable on the base level** — 341 clean
actions, caught at action 6 on a different level. A guard weakening is invisible
until you stand where the old and new guards disagree. An examinee that answers
"detected at step N" there is wrong.

### 4 · three-class verdict — sensitivity and specificity, always together

Nine unsolvable and eight solvable items across the A2 family, and the classes
are mixed across boards so board identity carries no signal.

* **(i) small-space unsolvable** — exhaustive search works here, so a complete
  searcher also answers correctly, possibly for a reason that does not transfer.
  The rubric therefore scores the **reason** separately: a machine-checked
  certificate scores full, "I searched and found nothing" scores partial.
* **(ii) large-space unsolvable** — **naive** enumeration is out of reach and
  the bound is computed rather than asserted (2⁶⁰ to 2¹²⁰ configurations). Not
  "no exhaustive method is feasible here": every shipped item of this class is
  settled by an exhaustive computation over at most 600 nodes, so
  the item is scored on **selecting a method that is not naive enumeration**, and
  the design document's "only invariant reasoning can answer" is withdrawn.
  D-EX-028.
* **(iii) solvable but hard** — the false-positive trap, each with a computed
  witness plan. A framework with a taste for unsolvability proofs gets caught
  here or nowhere.

**The quotient is published beside the bound, and its unsoundness is one-sided.**
The four class (ii) items have **180, 180, 600 and 177** reachable `(cart,
button)` states against a `lower_bound` of 2^60 to 2^120. The quotient ignores
`step_limit` outright and carries no latch state, so on a `require_all_switches`
board it can report the goal reachable when the level is unsolvable — which is
why `search_credible` is not derived from it (D-EX-022, withdrawn by D-EX-027).
D-EX-028 amends what that unsoundness licenses: it runs **in one direction
only**. An over-approximation yields false `solvable`, never false `unsolvable`,
so a goal in a different component **is** a sound unsolvability proof — which is
why this item's own answer key is allowed to be computed that way, and why the
search barrier here is apparent rather than real. `lower_bound` remains the
honest statement of what a *naive* complete search must cover. Both numbers are
in the truth file and the note beside them says which claim each can carry.
D-EX-027 and D-EX-028, and `STATUS.md` open weakness 27.

**Every solvable item says where its witness came from.** Five of the eight are
breadth-first search output and three are constructions. A plan that replays and
wins proves solvability however it was found, but on a paper whose premise is
由构造即知答案 the key has to say which. D-EX-023.

**The pair is split by class, and never quoted alone.**
[`artifacts/matrix/verdict_confusion.md`](artifacts/matrix/verdict_confusion.md)
is one row per examinee, one column pair per class, each cell `rate (answered /
class size)`. Three separate reasons, all of them measurements:

* an arm that aces class (i) and cannot touch class (ii) reports the **same**
  pooled sensitivity as an arm that reasons — the split is what tells "I
  enumerated it" from "I proved it", which is why they are separate classes;
* abstentions stay out of the denominator (correctly — an abstention is not a
  wrong answer), so the rate alone is inflated by them. The memoriser reports
  sensitivity **1.000** while having answered **0 of 4** large-space items;
* an empty denominator prints `--`, never `0.000`. Class (i) holds no solvable
  items, so specificity there is undefined rather than failed.

**And that last point is worse than it looks, which is why there is a second
split.** The three classes partition the paper *by answer* — 9 unsolvable in (i)
and (ii), 8 solvable in (iii) — so one denominator is empty in **every** class
cell and the pair the protocol asks for appears nowhere except pooled, which is
the reading D-EX-015 exists to say means least. `board_size_class` cross-cuts
the answer (small 5/5, large 4/3) and splits on exactly the distinction classes
(i) and (ii) were invented to draw. Under it the bluffer's signature is
`(1.000, 0.000)` in **one cell, per stratum**, instead of assembled from two
rows whose item sets do not overlap; and the memoriser's `large (--, --)` at
`0/4` and `0/3` says in one place that it has never answered a large board in
either direction. `calibration` asserts the bluffer's pair per stratum rather
than pooled. D-EX-024.

**Not answering has three forms and they are three columns.** *Did not submit*,
*declined*, and *submitted something unreadable* were one counter, and it was
the counter D-EX-006 introduced so that an abstention could not be confused with
anything else. An examinee whose every answer was unparseable printed the
identical row to `null`, which submitted nothing. D-EX-025.

And the result that settles the matter: with the cheater subagent on the matrix
as a row, `oracle` and `cheater-v4` are **identical in every cell** — 1.000 and
1.000 throughout, full coverage — and differ only in the score. A reader handed
the sheet and nothing else is indistinguishable from ground truth on the pair.
The matrix computes and prints its own collisions rather than leaving that to
the reader's eye. D-EX-015.

The certificate checker is a **closed grammar** with exact key sets, and every
number in a submitted certificate is re-derived from the level. A checker that
accepts free text is not a checker. It refuses, among others, a certificate
whose stated values are *true* but whose direction is wrong, and every attempt
to transplant a valid certificate onto a different item (144 transplants tried,
0 accepted).

**It also used to accept certificates for levels that were solvable.** The graph
the checker separates components in was a *second* implementation of
`Level.step`, and the two disagreed about the teleport and the door — so an
over-approximation that was supposed to fail open failed closed, and a
`cart_region` or `cut_set` proof of a false theorem was paid 2.0 of 2.0. There
is one transition function now and the graph asks it. Reproductions and the fuzz
that bounds the blast radius: D-EX-020 and the V5 run directory.

Every item carries a **constructive justification** in
[`proxy/variants.py`](../proxy/variants.py)'s spec format, emitted to
[`artifacts/variant_specs/`](artifacts/variant_specs/) and validated by
constructing a real `proxy.variants.Variant`. All five wrapper-legal operators
are exercised. That is the Phase 4 rehearsal: the format and the procedure are
frozen now.

## The marker is calibrated before it marks anything

An exam is a question-setter and a marker. The question-setter can be checked by
reading it; the marker cannot, because a marking bug produces a plausible number
and a plausible number is indistinguishable from a result. So four fakes with
known scores run first, against **pre-registered bands**, and
`assert_calibrated` refuses to mark a real submission if they miss.

| paper | oracle | null | memoriser | bluffer |
|---|---|---|---|---|
| held-out | 1.000 | 0.000 | 0.575 | 0.450 |
| handover | 1.000 | 0.000 | 0.717 | 0.326 |
| adaptation | 1.000 | 0.000 | 0.171 | 0.171 |
| verdict | 1.000 | 0.000 | 0.588 | 0.265 |

`oracle == 1.0` and `null == 0.0` are exact and follow from construction: a
marker that rejects ground truth depresses every real score, and a marker that
pays for silence inflates every one of them.

**They also calibrate only the paths those two fakes walk, and that is two of
the marker's eleven outcomes.** Fourteen faults injected into the verdict
rubric: thirteen passed this gate, twelve passed all seven mutants, two were
caught by nothing anywhere, and all four fractions above were bit-identical
under every one. The sheet advertises five answer shapes and the fakes submit
three; the mutants inherit those three because they are derived from the oracle.
Five **answer-shape probes** now run at the gate — abstain, unreadable, search,
wrong-claim-with-a-reason, forged certificate — each with a score fixed by
arithmetic over the paper's own points rather than by a band. D-EX-026.

The **verdict bluffer shows sensitivity 1.0 and specificity 0.0** — the
signature the protocol demands be visible. It answers "unsolvable" to everything,
catches every unsolvable case, and is worthless; the score says so.

One pre-registered band **failed on first contact** and was replaced rather than
widened. The reasoning is in [`DECISIONS.md`](DECISIONS.md) D-EX-010, including
the hole that remains.

### …and then tested between the two numbers it is pinned at

`oracle == 1.0` and `null == 0.0` are exact, and they are **endpoints**. A
marker can be exact at both and arbitrary in between, and nothing above would
notice. [`grading/selftest.py`](grading/selftest.py) attacks the middle from two
directions.

**Seven mutants, each with a score predicted by arithmetic rather than
judgement** — there is not a band anywhere in the module, because a band is what
you write when the expectation depends on item mix and none of these do.
Dropping a set of answers must cost exactly what those items were awarded;
dropping one answer must move one item's mark and no other's; reversing the
key's item order must move none; an answer that is ground truth for a *different*
item must not earn full marks; structured nonsense must pay zero.

That last one found a live defect the first time it ran. The adaptation rubric
read any answer it could not parse as the substantive claim `never` — and on
`v-a0-03`, the one variant undetectable on its base level, `never` **is** the
truth. A submission containing nothing scored 1.600 of 144, all of it on the
item that exists to ask whether an examinee can tell "the change is invisible
from here" from "I did not look". D-EX-014.

**Eight faults injected into the marker on purpose**, each a way markers
actually fail: pay for silence, reject truth, mark on the item id instead of the
answer, blend a pair that must stay split, inflate or truncate partial credit.
The output is a matrix of fault × check, read the same way as the leakage table:
**the zeros are the finding.** On the first run `truncates_partial` was caught by
nothing at all — every band for the informative fakes is `Band(0.0, x)`, bounded
above and open below, so a marker that quietly *depresses* scores satisfied all
of them. D-EX-013.

A second digest, `protocol_digest()`, covers `mark.py` and `calibration.py` and
is pinned by a test, so a quietly widened band is now an edit a reviewer sees.

## Red lines

* **The paper and the answer key are never in the same file.** `Item.paper` and
  `Item.truth` are separate fields and `Paper.sheet()` is built from a method
  that never receives the truth, so a leak takes deliberate effort rather than a
  lapse of attention. They land in `artifacts/papers/` and `artifacts/truth/`.
* **Leakage is attacked five ways** — declared probes (1,790 across the four
  papers), structural key disjointness, positional independence, **metadata
  independence**, and a **cheater subagent** handed the sheet alone and told to
  extract answers from it.

  **A cheater's claims are scored against the key before they are believed.**
  Two passes have now run, and each failed in a different direction: the verdict
  cheater *under*-predicted itself (13.8 forecast, **17 of 17** measured, worth
  0.5000 on the rubric because it submitted no certificate anywhere), while the
  held-out cheater was *most* confident — 0.97 — on six claims that were **all
  wrong**, because the leak it found handed it a prior (vanilla sokoban) that is
  false of A0, whose push slides the box two cells. A confirmed leak can have
  negative yield. An unverified cheater is just another confident agent.

  The static checks test the leaks we imagined; the cheater tests the rest, and
  on the first run **it was the cheater that found both real leaks**. The verdict
  paper weighted solvable items 3 against 2, so `points` — which sits on every
  sheet — was a perfect answer key on 17 of 17 items. The held-out sheet's
  `world.description` published the two-cell push rule, which is the thing being
  tested. Both were confirmed against the answer key, then fixed.

  The deeper fault was that `answer_labels` was an *optional* hook no paper
  implemented, so two of the checks silently did nothing on all four papers. An
  optional check is a check that does not run. Labels are now derived from the
  key directly and the metadata check was added; regression tests pin the exact
  leak that shipped. See [`DECISIONS.md`](DECISIONS.md) D-EX-011.
* **Zero network.** `guard.no_network()` makes socket creation raise, and the
  suite builds every paper inside it. It is a tripwire, not a sandbox, and the
  docstring says so.
* **Sealed pile untouched.** `guard.py` reuses `battery.guard` rather than
  forking it, refuses sealed ids by full *and* short form, and refuses even
  **dev-pile** games unless `allow_dev=True` is passed on purpose.
* **Determinism.** Sheets, keys and specs are byte-identical across rebuilds and
  across `PYTHONHASHSEED`. No wall clock in any artefact.

## Layout

| path | what |
|---|---|
| `model.py` | the two-sided item, the paper/key split, the report |
| `guard.py` | the network tripwire and the pile guard |
| `leakage.py` | the three static checks and the cheater brief |
| `papers/` | the four question types |
| `grading/` | rubric registry (source-hashed), marker, calibration |
| `grading/selftest.py` | the mutants, the injected faults, the detection matrix |
| `grading/confusion_matrix.py` | the pair, split by class, with coverage |
| `verify.py` | one command that decides whether the territory is green |
| `handover_bundles/` | the two delivery tiers, self-contained |
| `artifacts/papers/` | sheets — safe to hand out |
| `artifacts/truth/` | keys — **referee only** |
| `artifacts/variant_specs/` | constructive justifications, `proxy`-format |
| `runs/` | archived runs; manifests carry `prompt_id`, seed, digests |
| [`DECISIONS.md`](DECISIONS.md) | design calls and their reasons |
| [`STATUS.md`](STATUS.md) | what is done, and what is not |
