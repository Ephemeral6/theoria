# A28 — the baseline zero, examined

**Question.** Forty-six baseline runs, three model tiers, not one point scored.
Either the games are much harder than assumed, or the score is not being read
correctly. The two have completely different consequences for the paper's main
table.

**Answer: neither, cleanly.** The score is genuinely zero and was genuinely
read — but for two of the four development-pile games the zero is a **budget
artefact**, not a capability result, and the paper must not report it as one.

---

## 1 · The score is read, and it is real

The gameplay response (`RESET`, `ACTIONn`) has **no `score` field at all**. It
carries `state`, `levels_completed`, `win_levels`
(`arc-recon/ACCESS_CHECK.md` §5; corroborated here by asserting over every
gameplay record in `ledger.jsonl`). The authoritative score lives only on the
**scorecard body**, returned by a GET on an open card or by a successful
`POST /api/scorecard/close`.

Those bodies were archived. Across **63 observations spanning 57 distinct
run_ids**, every one reports:

| field | value |
|---|---|
| `score` (card) | `0.0` — 63/63 |
| `score` (environment) | `0.0` — 63/63 |
| `score` (run) | `0.0` — 63/63 |
| `level_scores` | all-zero vectors — 63/63 |
| `levels_completed` | `0` — 63/63 |

So the zero is not a missed read. **This is not an incident.**

## 2 · One real defect, and it is a provenance defect, not a wrong number

**No `runs/bare_cc-*/run.json` persists the authoritative score — 0 of 43.**
The harness records `levels_completed`, lifted from the gameplay response.
Anything downstream built from `run.json` or `out/campaign_cells.jsonl` is
therefore quoting `levels_completed`, **not** the score.

Here the two agree, because both are zero. That agreement is luck, not design:
`levels_completed` is a different quantity from `score`, and on a run that
completed a level but scored partially they would diverge. The arm that
produced the paper's left-hand column cannot currently tell you the score of
any run from its own archive; it has to be recovered from `probe_log.jsonl`,
which is what `harness/audit_zero.py` now does.

Logged as a gap, not an incident: no published number is wrong.

## 3 · The finding that changes what the paper may say

`level_baseline_actions` is returned by the API on every scorecard body. Level 1
of each development-pile game costs:

| game | level-1 baseline | best run reached | % of baseline | runs at/over baseline | terminal states |
|---|---|---|---|---|---|
| `ar25-0c556536` | 32 | **67** | 209.4% | 4 | GAME_OVER, NOT_FINISHED |
| `tn36-ef4dde99` | 32 | **32** | 100.0% | 2 | NOT_FINISHED |
| `g50t-5849a774` | 78 | 73 | 93.6% | **0** | NOT_FINISHED |
| `sk48-d8078629` | 61 | 38 | 62.3% | **0** | NOT_FINISHED |

**Every configured budget was 20 or 30 actions. The smallest level-1 baseline on
the pile is 32. 36 of 36 runs carrying a budget were configured below the
level-1 baseline of their own game** — no configured run could have completed
level 1 within budget, on any game.

The runs that *did* exceed a baseline are all from the m4-pilot era
(2026-07-27), have no archived `run.json`, and survive only in the ledger and
probe log.

Consequences, stated separately because they are different claims:

* **`g50t` and `sk48`: the zero is a budget artefact.** No run was ever allowed
  to spend as many actions as level 1 costs. Reporting these as capability
  failures would be reporting the budget as a result.
* **`ar25` and `tn36`: the zero is capability evidence.** Six runs reached or
  exceeded the level-1 baseline and still scored zero. The strongest single
  datum is `bare_cc-ar25-claude-haiku-4-5-20251001-76390591`: **67 actions,
  2.09× the level-1 baseline of 32, terminal state `GAME_OVER`, `level_scores`
  all zero.** That run was not cut short — it played twice the reference budget
  and lost.

## 4 · The number the paper needs, with its denominator and budget

> **Bare Claude Code (`bare_cc`) scored 0.0 on all four development-pile games:
> 0 levels completed in 1,562 successful actions across 57 runs (63 archived
> scorecard bodies), under a per-run budget of 20–30 actions against level-1
> baselines of 32–78.**
>
> Per tier — **opus-5**: 4 runs, 70 actions, max 30, 0 levels;
> **sonnet-5**: 3 runs, 65 actions, max 30, 0 levels;
> **haiku-4.5**: 50 runs, 1,427 actions, max 73, 0 levels.
>
> **The budget is below the level-1 baseline in every configured run.** For
> `g50t` and `sk48` no run reached the level-1 baseline, so their zero is a
> budget artefact and is reported as *not tested at adequate budget*, not as a
> capability result. For `ar25` and `tn36`, six haiku runs reached or exceeded
> the level-1 baseline and still scored zero.
>
> **No opus-5 or sonnet-5 run ever reached a level-1 baseline** (max 30 actions
> against a minimum baseline of 32). The tier the paper's headline compares has
> **zero** capability-tested runs.

The count "46" in the board item does not resolve to a single denominator:
there are **43** archived `runs/bare_cc-*` directories, **57** distinct run_ids
with authoritative scorecard bodies, and **36** runs carrying a configured
budget. Whichever is quoted must be quoted with its name.

## 5 · Absence recorded as absence

* 14 of 43 archived runs never produced a usable play record — outcomes
  `api_unusable` (8), `model_error` (5), `no_reset_window` (1); a further 7 have
  no summary at all and 2 are `gave_up`. Only **20** are `budget_exhausted`.
  These are absences, not zeros, and must not be pooled into a mean.
* No `sk48` or `g50t` capability datum exists at adequate budget. That is
  absence of evidence, and is recorded as such above rather than as a zero.
* The scorecard-close 404 trap (`ACCESS_CHECK.md` §3, `arc_client.close_scorecard`)
  destroyed the authoritative score for runs whose close never succeeded; 57 of
  them survive because a body was archived. The remainder are unrecoverable —
  a closed card cannot be re-fetched.

## 6 · Gates

`cd baseline-arms && python -m pytest -q`, in this worktree:

```
7 passed in 0.36s                      # tests/test_audit_zero.py alone
6 failed, 546 passed, 1 skipped        # whole suite, cold
3 failed, 549 passed, 1 skipped        # whole suite, warm
```

Both failure sets **pre-date this branch** and neither involves `audit_zero`:

* 3 × `tests/test_schema_column.py` — the gitignored `schema_traces/` payload is
  absent in a fresh worktree. `_payload_or_skip()` guards on
  `os.path.isdir(root)`, and the directory *does* exist holding only its
  tracked `MANIFEST.json`, so the guard does not fire and the test fails
  `assert 0 == 8` instead of skipping. Already recorded in
  `runs/2026-08-01T044513Z-A19/MANIFEST.json` as
  "fresh_worktree_without_payload".
* 3 × `tests/test_archive_runs.py` — **flaky**, cold-run only; passes on a warm
  re-run. Consistent with the gate-timeout history in this territory.

Neither was introduced or fixed here.

## 7 · Incidental defect found while running the gate — the gate mutates its own evidence

Running `python -m pytest -q` **rewrites tracked files under
`baseline-arms/runs/`**. After a clean `git reset --hard`, a single suite run
leaves 17 files modified:

```
 M baseline-arms/runs/MANIFEST.json
 M baseline-arms/runs/bare_cc-*/run.json          (14 of them)
 M baseline-arms/runs/fetch-schema-traces-path-a/run.json
 M baseline-arms/runs/s1-full-run-not-archived/run.json
 17 files changed, 184 insertions(+), 120 deletions(-)
```

The rewrites are `evidence[].bytes` / `sha256` corrections and the removal of
evidence rows whose files no longer exist, e.g.:

```
-      "bytes": 2353,
+      "bytes": 2273,
-      "sha256": "sha256:e131df71...e68e69b",
+      "sha256": "sha256:810327d7...4c253af3",
```

This is the mechanism behind the `test_archive_runs.py` flakiness in §6. The
cold run is red because the committed archive is genuinely stale relative to
`out/`; the run then **repairs the archive as a side effect**, so the warm run
is green. A gate that edits the artefact it is auditing cannot certify it —
the second run is green because the first one made it green, not because the
committed state was ever correct.

Two consequences worth carrying:

* **The committed archive on `master` is stale.** `test_every_run_points_at_evidence_that_exists`
  fails cold, which means at least one `run.json` on master cites evidence that
  is not there at the recorded size and hash. That is a provenance defect in the
  arm's own records, independent of A28.
* **This is why the main tree showed `M baseline-arms/runs/MANIFEST.json` and
  `M .../s1-full-run-not-archived/run.json` at session start.** Those are not
  someone's work in flight; they are the residue of a previous suite run.

None of these 17 files are committed on this branch — they were restored with
`git restore` before the commit, which carries only `harness/audit_zero.py`,
`tests/test_audit_zero.py` and this run directory.

Not filed as an incident here because it is outside A28's scope and no
*published* number depends on it; flagged for the territory owner.
