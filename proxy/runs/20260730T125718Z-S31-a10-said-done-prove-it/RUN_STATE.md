# S31 — third pickup. What I did, and what I only checked.

Worker W-1710, branch `agent/s31-a10-said-done-prove-it`, base `935728b9`
(= current `origin/master` merged into the branch). Territory `proxy`.
Zero API calls, $0.00, zero sealed-pile contact.

## The first thing was not reading

The branch held **8 commits of finished work and no remote ref.** `ci_merge` only
merges branches present on `origin`, so an unpushed branch is not *red* to it — it
does not exist. That is S36's recorded failure mode, and it had reproduced on the
one item whose own subject is *"the board says done and `master` cannot show it"*.

So the first action was `git push -u origin agent/s31-a10-said-done-prove-it`,
before any assessment. Preserving work outranks judging it: an assessment can be
redone from a pushed branch, and cannot be redone from a disk that dies.

The relay chain on this item is now three deep — W-1691 died mid-sentence,
W-1702 wrote the substance and never pushed, W-1710 (this run).

## What the relay had already delivered, and how I checked it

I did not inherit these conclusions. `proxy/verify.py` was re-run end to end after
merging current `origin/master` into the branch: **green, 414 passed, 5/5 stages**
— suite, spend gate, one offline game through both proxies, artefact self-check
(61 records, dense seq, all 6 envelope fields), degeneracy guard in both
directions. `proxy/tools/audit_delivery.py` was re-run and its verdict read.

| ticket requirement | state | where |
|---|---|---|
| 1 — which of the three cases is A10 | **done** | `proxy/DELIVERY_RULING.md`, executable as `tools/audit_delivery.py` |
| 2 — is the real-arm record being written | **done, without spending** | `../20260730T043824Z-…/real_arm_probe.txt`; decision recorded in `NO_LIVE_CALL.md` |
| 3 — land the reconciliation ruling | **already on master, in amended form** | commit `26b387e5` |
| 4 — negative sample, amount mismatch must go red | **done** | `tests/test_reconcile_amount.py` |

The answer to requirement 1 is **(c) with a fourth thing underneath**: the audit
read `proxy/var/ledger.jsonl`, which `proxy/.gitignore:3` excludes and which has
never been tracked at any commit, so it could not be evidence about `origin/master`
— and separately, the zero-real-arm state it found is real, was already declared,
and is owned by the arm territories rather than by `proxy`. **Both halves are true,
and reporting only one of them has already happened twice.**

Requirement 3 turned out to be a **misattribution in the ticket**: the
(cost × actions × turns) triple is not an S29 ruling, it is monitor finding F-19,
and F-19 withdrew the `turns` leg the same day it was published (`spec.py:633-636`).
On master `RECONCILIATION_KEY` is already `(actions, cost, score_per_run)` with
`turns` as `ABSENT`/`votes=False` and `score_per_step` as
`NOT_CROSS_VERIFIABLE`/`votes=False`. Landing the ticket's literal wording would
add a leg over a field nobody records, which can only ever print agreement.

## Two defects the relay found that the ticket did not ask for

Both are worth surfacing because neither is paperwork:

* **The guard could let a sealed-pile id through.** `_texts` joins body values to
  catch an id split across two fields, but `re.findall` does not overlap, so a stub
  in front of a split sealed id let a manufactured phantom eat it, and under
  `unknown_policy='allow'` the sealed id passed unseen. Fixed by filtering
  join-derived ids to registered stems and scanning overlapping via a zero-width
  lookahead. Latent, not live — nothing sets that knob today. **Do not "fix" this
  with `\b`**, which fails *open* on `x_ar25-0c556536`.
* **1h cache writes were billed at the 5m rate.** The table carried
  `cache_creation_input_tokens_1h` and nothing ever wrote a usage key by that name,
  so the rate sat unused; on the seven real archived calls, all 100 % 1h, the model
  line was understated by 6 % ($1.229967 derived against $1.296152 billed). Now
  exact to 6 dp. And `NOT_APPLICABLE` no longer votes — a run with **no bill** used
  to print the same `PASS` as a run whose bill reconciled.

## What I deliberately did not do

**No live API call.** Reasons in `NO_LIVE_CALL.md`. Short version: requirement 2's
question is answered offline, the ticket makes spending conditional, and
manufacturing one real-arm record to satisfy a requirement *about* real-arm records
is the exact failure this item exists to adjudicate — a `bare_cc` run against
loopback writes records that look real on the axis most audits check.

## Gaps left open

* **The zero-real-arm state is unchanged and still real.** It belongs to the three
  arm territories. This item ruled on who owns it; it did not close it.
* **Cost reconciliation cannot witness an amount on `/v1/messages`**, which returns
  no per-model breakdown. `amount_not_witnessed` reports it and the leg's note says
  so; an inflated usage block still reconciles on that transport.
* The two defects above were found by probing, not by a systematic sweep of either
  the guard or the pricing table. Neither is exhausted.
