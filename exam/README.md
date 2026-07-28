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
python -m exam.tools.build_papers      # set the papers; split sheet from key
python -m exam.tools.run_exam          # calibrate the marker, then mark
python -m pytest exam/tests -q         # 157 tests
python -m exam.tools.archive_run <id>  # runs/<id>/MANIFEST.json
```

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
* **(ii) large-space unsolvable** — enumeration is out of reach and the bound is
  computed rather than asserted (2⁶⁰ to 2¹²⁰ configurations).
* **(iii) solvable but hard** — the false-positive trap, each with a computed
  witness plan. A framework with a taste for unsolvability proofs gets caught
  here or nowhere.

The certificate checker is a **closed grammar** with exact key sets, and every
number in a submitted certificate is re-derived from the level. A checker that
accepts free text is not a checker. It refuses, among others, a certificate
whose stated values are *true* but whose direction is wrong, and every attempt
to transplant a valid certificate onto a different item.

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

The **verdict bluffer shows sensitivity 1.0 and specificity 0.0** — the
signature the protocol demands be visible. It answers "unsolvable" to everything,
catches every unsolvable case, and is worthless; the score says so.

One pre-registered band **failed on first contact** and was replaced rather than
widened. The reasoning is in [`DECISIONS.md`](DECISIONS.md) D-EX-010, including
the hole that remains.

## Red lines

* **The paper and the answer key are never in the same file.** `Item.paper` and
  `Item.truth` are separate fields and `Paper.sheet()` is built from a method
  that never receives the truth, so a leak takes deliberate effort rather than a
  lapse of attention. They land in `artifacts/papers/` and `artifacts/truth/`.
* **Leakage is attacked five ways** — declared probes (1,790 across the four
  papers), structural key disjointness, positional independence, **metadata
  independence**, and a **cheater subagent** handed the sheet alone and told to
  extract answers from it.

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
| `handover_bundles/` | the two delivery tiers, self-contained |
| `artifacts/papers/` | sheets — safe to hand out |
| `artifacts/truth/` | keys — **referee only** |
| `artifacts/variant_specs/` | constructive justifications, `proxy`-format |
| `runs/` | archived runs; manifests carry `prompt_id`, seed, digests |
| [`DECISIONS.md`](DECISIONS.md) | design calls and their reasons |
| [`STATUS.md`](STATUS.md) | what is done, and what is not |
