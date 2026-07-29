# A12 · what the paper's cross-arm cost claim actually reads

Run `20260729T060000Z-A12-cost-claim-sources`. Opened by W-1652; picked up on
2026-07-29T04:45Z by **RES-1** (campaign lane) after that worker's session ended.
Everything below this line is written as it happens.

## 0 · The baseline this run inherited was red, and for two different reasons

W-1652's `MANIFEST.json` recorded one: `fig06_concept_timeline` raised on
`unexpected=['E-08', 'E-09']`. Re-running `bash figures/verify.sh` at the merge
of `master` (a03fe99) found a **second**, and the second one is this item's
subject matter rather than an unrelated nuisance.

### Red 1 — fig06's closed id set, and why widening it is the intended response

`figures/fig06_concept_timeline.py:103-109` declares `EXPECTED_IDS` as a closed
tuple and `:388-393` raises when the log's ids differ in either direction. The
docstring says why: "an id or a verdict this script does not recognise
**raises**, because a silently-dropped adjudication is worse than a broken
build."

The log it reads is `cold-start-a0/THEORIZE_LOG.md` — **the theory-compiler
track's file**, not this track's. That track added two E-family entries
(`cold-start-a0/THEORIZE_LOG.md:364-365`): E-08, the count-lock guard
(`count(Token, present = false) >= k`), and E-09, `faces(T,D)` — a named track in
a place. Both are recorded **discharged**, both have full write-ups
(`:370`, `:424`).

So the guard fired correctly: the log grew and nobody re-declared it. The
response the guard is asking for is to declare the two ids, not to loosen the
check. Added E-08 and E-09 to `EXPECTED_IDS` — the E family is parsed from a
table (`:363-383`) and derives `ledger_state` from the row itself, so no new
verdict vocabulary was needed. fig06 now runs: 27 log entries over 6 lanes, 36
main rows, 119 CSV rows.

**This is a cross-track coupling worth naming, not just fixing.** `figures/`
pins a closed id set against a document another track edits in the normal course
of its work. Every time that track adjudicates something new, this track's
verify goes red, and the two tracks do not talk. Filed to `monitor/inbox/`
rather than fixed here, because the fix is a contract question (who owns the
declaration) and not mine to settle alone.

### Red 2 — gate 8, coverage: twelve theoria runs are invisible to figure 2

`figures/verify.sh` gate 8 (`check_coverage.py`) is red at base, and it is red
about **exactly the chain this item exists to pin**:

```
COVERAGE: theoria run directory <id> (has MANIFEST.json; missing cost_curve.json):
the discovery rule requires every member and so skips it, which means neither the
rule nor this probe would notice it. A half-written run must be named, not
silently dropped by both.
```

Twelve directories, including every A3 campaign run to date
(`20260728T233900Z-A3-campaign-devpile`, `…-a3-desk-gate`, `…-a3-turn-series`,
`…-a3-level-boundary`) and both g50t first-contact salvages.

The paper's account of what a run cost is assembled by a **discovery rule that
requires a full member set and silently skips anything short of it**. A campaign
leg that died halfway — which is the case the bill-shape figure most needs to be
honest about — is not "missing from the plot with a gap"; it is *absent*, and
before this probe existed, absent without a trace.

Detailed source map, reconciliation and negative sample below as they land.

## Delivered

`SOURCE_MAP.md` beside this file is the item's four numbered asks, answered.
Three of the item's own premises turned out to be wrong and are corrected there
rather than repeated: the reads are five not four; **the paper makes no
cross-arm cost claim at all** (`sections/10_limitations.md:12-16` says so
explicitly, and fig02 is not one of the paper's three figures); and the ablation
arm's absence, while real, is not the missing third arm — Schema is.

Code:

* `figures/reconcile_cost.py` — `cost x actions` over four independent
  derivations, joined on `run_id`, with `turns` and `score` excluded on the
  record and for stated reasons. Writes `figures/audit/reconcile_cost.csv`
  (not `csv/`: that directory is `build_all.py`'s output and gate 6 diffs it).
* `figures/verify.sh` gate 9 — runs the negative control **first**, then the
  reconciliation. A check that has never been seen to refuse cannot be read as
  agreement.
* `figures/check_coverage.py` — gate 8's partial-directory predicate now fails
  on the run's own claim of spend instead of on shape, with its own planted
  control.
* `figures/fig06_concept_timeline.py` — `EXPECTED_IDS` widened to the other
  track's E-08/E-09.

## Test state

`bash figures/verify.sh`: **green, nine gates**, from a base where gates 4, 6
and 8 were red. Two builds byte-identical, 61 sources hashed, 24 images.

Zero API calls. Zero network. **$0.00.** Zero sealed-pile contact.

## The two things this run found that outlive it

1. **E5's cost-per-action divides by an action count that includes the RESET**,
   on every run, disagreeing with the scorecard definition the proxy verified
   32-of-32. Filed for `battery/`; declared and quantified in gate 9 so it
   cannot be forgotten, and asserted still-true so the declaration cannot
   outlive the defect.
2. **No run in this repository has two derivations agreeing without an excuse**,
   and every theoria run is uncorroborated — the live arm is absent from
   `capability_spectrum`'s `provenance.arms`. The plate's `$0.9025/action`
   rests on one run of seven successful actions.

## What I did not do, and why

* Did not fold the ablation arm into fig02. It writes `arm: "theoria"`
  (D-AB-004) and spends nothing by construction; folding it in would merge two
  arms under one label and divide zero into every ratio. It needs a registered
  arm name first, which is `proxy/` territory.
* Did not fix E5. `battery/` is not this item's territory.
* Did not add `turn_series.json` to `theoria_run`'s members. It is the single
  cheapest way to give the theoria arm a second opinion and it is the first
  thing the next holder should do — but it changes what fig02 draws, and that
  is a plate change to put in front of RES-2 rather than land beside a gate.
