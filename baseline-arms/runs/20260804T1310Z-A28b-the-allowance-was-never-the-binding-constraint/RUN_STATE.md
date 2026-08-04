# A28b — the allowance was never the binding constraint

**Brief.** Finish A28: put the per-game budget comparison on record, settle what
the paper's 42.83 % reference actually is, and write the replacement wording for
every claim that leans on the baseline column.

**Result.** A28's headline does not survive the whole archive, and the item's own
instruction — *if its premises are false, say so with evidence and follow the
evidence* — is the one that applied. The budget was never the binding constraint
on any of the four games. What bound was an abort rule this territory has already
ruled invalid and already replaced, and never re-ran against.

Ruling and replacement wording: [`baseline-arms/BASELINE_COLUMN.md`](../../BASELINE_COLUMN.md).

---

## 1 · What the brief asked for, and what came back

### (1) the per-game comparison — allowance beside achievement

| game | level-1 baseline | max **allowed** | max **achieved** | verdict |
|---|---:|---:|---:|---|
| `ar25-0c556536` | 32 | 748 | 67 | capability tested (one episode, `GAME_OVER`) |
| `g50t-5849a774` | 78 | 879 | 73 | abort artefact |
| `sk48-d8078629` | 61 | 1070 | 38 | abort artefact |
| `tn36-ef4dde99` | 32 | 317 | 32 | abort artefact |

**No game is a budget artefact.** The allowance clears the level-1 baseline on
all four, by 9.7× to 23×.

A28 answered the opposite because it read the allowance out of
`runs/bare_cc-*/run.json`, key `budget` — a population of 36 runs at 20 and 30
actions. The approved **S1 baseline-parity** campaign's 48 episodes have no
`runs/` directory at all: `runs/s1-full-run-not-archived/run.json` records them
as excluded because a concurrent session was mid-write (INC-BA-003). Their
allowance lives in `out/campaign/campaign_*.json` as `total_budget`, and
`campaign.py` hands each episode what is left of it —
`bare_cc.play(game_id, model, remaining, ...)`.

That is a reader defect, not a data defect: every number A28 printed is true of
the rows it could see.

### (2) what stopped the runs that had the actions

* 47 of 48 S1 episodes recorded `api_unusable`, every one at **exactly 10**
  cumulative failed actions — the rule then in force, absolute and unscaled.
* Reconstructed from the ledger shards' per-step `failed` flags, the **longest
  back-to-back failure run anywhere in that campaign is 5**.
* Today's rules are `CONSECUTIVE_FAILURE_ABORT = 10` and
  `cumulative_failure_cap(budget) = max(10, budget)` → 317–1070 here.
  **0 of 48 episodes would abort under them.**

`BUDGET_REPORT.md` §11.2 and `DECISIONS.md` D-016 had already ruled the old rule
"guaranteed by construction rather than earned by the API". The S1 campaign has
never been re-run under the replacement.

**One episode in the entire arm ended because the game ended**:
`bare_cc-ar25-claude-haiku-4-5-20251001-76390591`, 67 successful actions
(2.09× the level-1 baseline of 32), 8 failed, terminal `GAME_OVER`, score 0.0.

### (3) the 42.83 % reference — not commensurable, and not checkable here

Traced to `SCHEMA_LOCATE.md` §1 and
`papers/…/P7/search-traces/line0-schema-attribution.md` Source C: upstream's
self-reported **RHAE** over the **25 public games** (Zeng et al., Impossible
Research; no paper, no code, no published budget regime). Four axes of
incommensurability with anything measured here — metric, game set, allowance,
scaffold — and the metric axis cannot be closed at all, because **RHAE is nowhere
defined in this repository** and `ACCESS_CHECK.md` §3 never states the formula
behind the scorecard `score` this arm reads. Whether 42.83 % and 0.0 are numbers
in the same units is not established anywhere on disk. Ruling: it is an external
reference, and belongs where `SCHEMA_ARM_RULING.md` put 98.98 %.

### (4) replacement wording → `monitor/inbox/`, not edited into their territories

* `monitor/inbox/20260804T1310Z-baseline-arms-to-papers-the-left-hand-column-is-an-external-number.md`
* `monitor/inbox/20260804T1310Z-baseline-arms-to-freeze-the-bare-cc-comparator-is-not-a-measured-arm.md`

The freeze one carries the consequence that costs this project something:
`CLAIMS_TEXT.md:425` makes `bare_cc` the **main comparator** for
`theoria − bare_cc`, and a systematically truncated comparator biases the
front-loading index **in the direction C2 predicts**. That is a limitation, not a
footnote.

### (5) the corrected run, priced and not run

No code change and no budget change is needed — the allowance was adequate and
the rule is already fixed. It is a re-run. At this territory's own unit prices
(`harness/unit_prices.py`: $0.0437/action current transport; S1 measured
$0.0333/action): **$6.76–8.87** for one parity episode per game, **$40.56–53.23**
for the 3-replicate version that can actually fail, **$100.37–131.71** to re-run
the full S1 budget. Full table with the two risks priced in: `BASELINE_COLUMN.md` §5.

**Nothing was run. No network call, no spend, no live game contact.**

---

## 2 · What was built

| file | what it is |
|---|---|
| `harness/baseline_allowance.py` | reads allowance from all three places it is written, keeps provenance attached, classifies each game budget / capability / abort, reconstructs the failure shape from the ledger |
| `tests/test_baseline_allowance.py` | 11 tests: 6 over the real archive, 4 negative controls, 1 positive control on the rule predicate |
| `harness/run_manifest.py` | derives a work-run `MANIFEST.json` rather than typing one; `--verify` re-hashes; `--reference` names a delivery without pretending to pin its bytes |
| `BASELINE_COLUMN.md` | the ruling, the replacement wording, the priced gap |
| `tests/test_audit_zero.py` | two test names and three docstrings corrected — the assertions were true of their populations, the sentences around them were not |

The classifier separates three claims the phrase "the baseline scored zero" runs
together: allowance below baseline → **budget** artefact; allowance adequate and
the game ended → **capability** evidence; allowance adequate and the harness
ended it first → **abort** artefact, which is a fact about this arm's stop rule
and about nothing else.

---

## 3 · Negative controls

Acceptance, not garnish. All in `tests/test_baseline_allowance.py`.

1. **A generous allowance is never a budget artefact.** A mock game with
   allowance 1000 against a 50-action baseline must not come back
   `budget_artefact`. Without this the checker could just recite A28.
2. **A thin allowance still is one.** Allowance 30 against baseline 50 must
   still classify as `budget_artefact` — or the checker has merely been
   inverted.
3. **Absent allowance is absent, not zero.** A run observed on a scorecard with
   no allowance in any of the three sources yields `allowance_max = None`,
   verdict `no_allowance_recorded`, and is named in the absence block. Nothing
   renders it as an allowance of 0.
4. **Spending the baseline is not capability evidence.** achieved 50 against
   baseline 50 with a non-terminal outcome must classify `abort_artefact`;
   flipping only the outcome to `game_over` flips the verdict. This is A28's
   error pointing the other way, and it is what mislabelled `tn36`.
5. **Positive control on the rule predicate.** `would_abort_today` returns False
   on every real S1 episode, so it is driven with synthetic episodes on both
   rules — ten consecutive failures, and a cumulative count at the grind cap —
   and must return True on each; and `None` (not False) when the failure shape
   or the allowance is missing.

Real-archive assertions that would go red if the finding changed: the S1
allowance clears every level-1 baseline; 47/48 `api_unusable`; longest
consecutive run < the current threshold; 0 would abort today; exactly one
terminal-game-end run in the whole arm; and the old reader's population is
pinned at 36 against S1's 48.

---

## 4 · Gates

`cd baseline-arms && python -m pytest -q`, in this worktree:

```
11 passed in 1.88s                     # tests/test_baseline_allowance.py alone
 7 passed in 1.18s                     # tests/test_run_manifest.py alone
18 passed in 1.61s                     # test_baseline_allowance + test_audit_zero

6 failed, 553 passed, 1 skipped        # whole suite, cold, BEFORE this branch
3 failed, 556 passed, 1 skipped        # whole suite, warm,  BEFORE this branch
6 failed, 571 passed, 1 skipped        # whole suite, cold, AFTER  this branch
3 failed, 574 passed, 1 skipped        # whole suite, warm,  AFTER  this branch
```

+18 passing, same 6 cold / 3 warm failures, same 1 skip.

The 6 cold / 3 warm failures pre-date this branch and are the ones A28 §6
documented: 3 × `test_schema_column.py` (the gitignored `schema_traces/` payload
is absent in a fresh worktree and the skip guard does not fire because the
directory exists holding only its tracked `MANIFEST.json`) and 3 ×
`test_archive_runs.py` (cold-only; the first suite run repairs the archive and
the second passes). Neither was introduced or fixed here. Post-branch numbers
are in `MANIFEST.json` under `tests`.

---

## 5 · Residual gaps, stated as gaps

* **Whether the S1 failures were the API's fault is still unknown.** The
  reconstruction proves only that today's rule would not have aborted on them.
  It does not prove those actions would have succeeded. Only a re-run settles
  that, and this run does not do re-runs.
* **`g50t`, `sk48`, `tn36` have no capability datum.** Absence, written as
  absence everywhere in the proposals.
* **2 of 57 observed run_ids have no allowance anywhere** —
  `bare_cc-ar25-…-833db563`, `bare_cc-g50t-…-29065be4`. Named, excluded from
  every maximum, never rendered as 0.
* **The arm still persists no score**: 0 of 43 archived `run.json`. Unchanged
  from A28; a defect in the arm's own records.
* **RHAE is undefined here.** Closing that means reading upstream material, and
  the upstream artefacts are the highest-risk objects on the pile (INC-BA-001).
  Not done, not proposed here.
* **The gate still mutates its own evidence** — 17 tracked files under `runs/`
  rewritten by a suite run (A28 §7). Reproduced exactly; restored with
  `git restore baseline-arms/runs` before committing, so this branch carries
  none of them. Out of scope, observed twice now.
* **The two inbox proposals are named in the manifest but not hashed.**
  `baseline-arms/.gitattributes` pins `eol=lf`; `monitor/inbox/` is covered by
  no such attribute, and `core.autocrlf` is true here — every existing file in
  that directory is CRLF on checkout. A sha256 taken over the LF copy written
  here would be true of nothing on any other machine, so they go under
  `references_not_hashed` rather than into `files`. The nine artefacts that are
  hashed are all under `baseline-arms/`, where the attribute holds; `--verify`
  is green on all nine.
* **The 27-step median in `PAPER.md`:1922 is only partly diagnosed here.** This
  run shows the abort rule is a large part of it; it does not decompose the
  median across the three regimes, and the battery's 80-run `bare_cc` corpus is
  battery territory.
