# The frozen scorer

`Theoria.md`'s standing discipline for the three arms: one outer loop, one
ledger format, **one scorer**. Otherwise a difference in the numbers cannot be
attributed to a difference in the arms, and attributing differences to arms is
the entire experiment.

```bash
python -m proxy.scoring --verify-only          # what is frozen, and its hash
python -m proxy.scoring --run-id r-…           # score one run, reconcile, file it
python -m proxy.scoring --all --ledger x.jsonl # every run in a stream
```

---

## 1. What "frozen" means here

Three things, each of them a property of the construction rather than a promise:

* **`proxy/scoring/frozen.json` records the sha256 of the scorer's source.**
  `verify_frozen()` recomputes it; `score_run()` calls it first and refuses to
  score on disagreement. A scorer that could be edited between two arms' runs is
  not a shared scorer, it is two scorers with one name.
* **The fingerprint is in the artefact.** `{id, version, sha256, frozen_at}`
  goes into the `run_start` record and into `run.json`. A number can always be
  traced to the rule that produced it.
* **The freeze is verified before the game starts**, not after. A run that turns
  out to have been scored by an edited scorer has already spent its actions.

Changing the scoring rule means **a new `scorer_id` and a new entry**, never an
edit in place. Runs already scored carry the old id and stay reproducible. The
test `test_an_edited_scorer_refuses_to_score` is the negative control: a freeze
that has never been seen to fire is a comment.

## 2. What `arc_v1` computes, and the one thing it refuses to

It publishes **the scorecard's own numbers** and reconciles them against the
ledger. It does **not** reimplement the ARC-AGI-3 percentage.

That restraint is evidential. `proxy/tests/fixtures/scorecard_corpus.json`
holds 32 real closed scorecards — four development-pile games, two models, two
campaigns — and **every one of them reports `levels_completed == 0` and
`score == 0.0`**. The cards carry `level_scores` as floats next to
`level_baseline_actions`, which hints at efficiency weighting, but hints are not
evidence. A scorer that shipped a guess would emit a plausible number with
nothing behind it, and Phase 1's whole claim is that conclusions come from the
ledger.

So `score.value` is the API's number, `score.basis` says `scorecard`, and
`score.partial_credit_formula` says, in the artefact itself, that the formula is
not reimplemented. When a run finally completes a level the number will be the
API's; the formula stays unimplemented until a corpus pins it down.

## 3. The calibration, and its limits

Two measured constants, both in `arc_v1.CALIBRATION` with their evidence
attached, because a constant whose provenance is lost is a constant nobody dares
change.

**`total_actions` counts successful non-RESET commands.** 32 of 32 exact
agreement over the corpus. `baseline-arms` reported this on 4 samples in
`BUDGET_REPORT.md` §4; this is the same claim on 32, across two campaigns.

**Refused requests are not billed.** The failed commands behind those 32 cards
were 400s and 500s — requests the server rejected before executing — and the
scorecard counted none of them. Over 100 failed commands appear in the corpus,
so the agreement is not vacuous.

**The limit, stated as `baseline-arms` stated it:** this is evidence that a
*refused* request is free. It is **not** evidence that a semantically wasted
action is free. A click on empty space returns 200, counts, and is billed.

One loose end recorded rather than modelled: the card also carries `resets`,
which was `0` in all 32 despite exactly one RESET per run. RESET is counted
somewhere else, or `resets` counts only re-RESETs. The scorer does not model it.

## 4. The checks

| id | claim | fails when |
|---|---|---|
| S-0 | a scorecard was captured | the card is absent or an unrecognised shape → `UNDETERMINED` |
| S-1 | `total_actions` == successful non-RESET commands | the calibration disagrees |
| S-2 | card `levels_completed` == the ledger's | the two records of the same fact differ |
| S-3 | a positive score iff a level was completed | the only score/level relation this corpus pins down |
| S-4 | the card is about the game the ledger played | |
| S-5 | the steps counted against this very card | `UNDETERMINED` on lifted v0 runs, which have no per-step `card_id` |
| S-6 | level boundaries recompute from the step sequence | |
| S-7 | exactly one `run_end` | a second one is a forgery signature: the ledger is append-only, so a later record must not be able to replace an earlier verdict |
| S-8 | card and step responses agree on the level count | the ledger's copy is the API's `win_levels` |
| S-9 | the score is within any reading of it | a forged score. The bound is `max(1.0, levels_completed)`, which holds whether `score` is a fraction or a count — so the check needs no knowledge of the formula |
| S-10 | the card's totals agree with its own environments | pure arithmetic on the card; catches a forger who edits one number |

### Three verdicts, and why the third one exists

```
PASS           every check that could be evaluated agreed
FAIL           a check disagreed — the ledger is not a faithful record
UNDETERMINED   the obligation could not be discharged at all
```

`UNDETERMINED` is not `PASS`. `baseline-arms` lost 22 of 23 scorecards to a
transient close-404 and **the loss was silent**, so Phase 1's reconciliation
obligation was quietly not being performed at all. A scorer that returned `PASS`
for "nothing to compare" would reproduce exactly that failure. Both non-PASS
verdicts write an `incident` into the ledger — `score_mismatch` for a
disagreement, `score_unreconciled` for an obligation that could not be
discharged.

## 5. Where the score is stored, and why not in the ledger

The score is a **derived** quantity and follows §5 of `LEDGER_FORMAT.md`: it is
not written into the ledger. It lands in `proxy/var/scores/<run_id>.json` and in
`run.json`. Same argument as D-004 makes for dollars: a number written into an
append-only file is wrong the day the rule that produced it changes, and cannot
be corrected. With the scorer outside, a re-score re-prices history instead of
contradicting it.

What *does* go into the ledger is the failure. An `incident` is a record, and a
reconciliation that failed — or that could not be performed — is exactly the
thing Phase 1 asked to be recorded.

Scoring happens **the moment a game ends**, in `runner.run_game`, not in a
sweep afterwards. Phase 3 audits the order results arrive in, and a batch
decided all at once is a batch someone could have decided after seeing it.

## 6. The upstream scorer, and why it is not here

`Theoria.md` Phase 1 §5 says the frozen scorer should be adopted as-is, and
`baseline-arms/SCHEMA_LOCATE.md` §2.4 identified the upstream
`score_trajectories.py` as pure offline Python — apparently exactly the thing.
It is **deliberately not vendored**. The reasons are in `DECISIONS.md` D-016;
the short form is that judging whether it is safe to read requires reading it,
which is the precise shape of INC-BA-001, and that the upstream release declares
no licence while Phase 4 publishes every tracked file.

`proxy/scoring/REGISTRY` takes more than one scorer for exactly this reason. If
that file is ever adopted, it registers beside `arc_v1` under its own id with
its own freeze entry, and every `run.json` already records *which* scorer
produced its number — so past runs keep their attribution instead of being
silently re-scored.
