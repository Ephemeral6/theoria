# A12 · the chain the cross-arm cost claim actually hangs on

Pinned 2026-07-29 by RES-1. Every line carries a file reference. Where the
board item's premise turned out to be wrong, it is corrected here rather than
repeated.

## 0 · Three of the item's premises are wrong, and one of them changes the job

**"图 2 读四个别的来源" — it is five programmatic reads, not four.** The four in
the item are the four keys declared together at `fig02_bill_shape.py:119-122`.
fig02 also reads `battery/artifacts/capability_spectrum.json` at `:546`
(declared `sources.py:119-130`), and `theoria_run` is a **two-member** rule
(`sources.py:355`), so it is two file kinds. Expanded against today's tree,
`sources.SOURCES` yields 34 paths carrying `fig02_bill_shape`, 30 present.
Three further sources are declared and hashed but never parsed
(`sources.py:89-110`) — their numbers are hard-typed into the plate
(`FAILURE_BAND_LOW = 0.283` at `fig02:156`; `USD 0.1459` at `fig02:1449`).

**"论文正文里的跨臂成本主张" — the paper makes no such claim.**
`papers/phase1-workshop/sections/10_limitations.md:12-16` states it outright:
*"This paper reports no cost comparison between arms."* `grep '\$[0-9]|USD'`
over `PAPER.md` and every `sections/*.md` returns zero hits. fig02 is not one of
the paper's three figures (`OUTLINE.md:69-71`, `verify_paper.py:81-86`), and the
per-model dollar figures were deliberately deleted (`PROVENANCE.md:145-146`).

The only cross-arm dollar comparison in the repository is **on the fig02 plate
itself** (`fig02:1447-1452`: `USD 0.9025 (theoria, 7 actions)` against
`USD 0.1459 (bare_cc opus)`), and that plate is not in the paper. So the job is
not to shore up a paper claim; it is to make sure the claim the *plate* carries
is checkable before anything cites it. That is what this run built.

**"消融臂在图 2 里根本没出现" — true, but it is not the missing third arm.**
`Theoria.md:270-272` names the three arms as bare Claude Code / Schema /
Theoria; the ablation arm is a fourth device introduced at `Theoria.md:274`.
fig02's own caveat (`:1466-1468`) names **Schema** as the missing arm. The
ablation arm's absence is real and is recorded below, but correcting it would
not make the plate three-armed.

## 1 · The sources, and what each one covers

| # | Path | Written by | Fields fig02 uses | Arms |
|---|---|---|---|---|
| 1 | `baseline-arms/ledger.jsonl` | `baseline-arms/harness/ledger.py:100-136` | model_call `total_cost_usd`; env_step `action`,`failed` | bare_cc |
| 2 | `baseline-arms/out/shards/ledger.*.jsonl` (11) | same, sharded `ledger.py:26-27,63-81` | same | bare_cc |
| 3 | `baseline-arms/out/pilot_*.json` (6) | `harness/run_pilot.py:82` | `outcome`; `cost_usd` for the tolerance check | bare_cc |
| 4a | `theoria-arm/runs/*/cost_curve.json` (4) | `armtools/archive.py:1180-1183` | `step_idx`,`usd`,`model` | theoria |
| 4b | `theoria-arm/runs/*/MANIFEST.json` (4) | `armtools/archive.py:1138-1179` | `cost.*`, `reconciliation.*` (notes only) | theoria |
| 5 | `battery/artifacts/capability_spectrum.json` | `battery/run_battery.py:325` | E2/E3/E4 cards | bare_cc, schema_repro, theoria_a0/a0_spike/a2 |

**Rule 3 is untracked by design** (`sources.py:394`, `tracked=False`), so `_scan`
skips the git filter and folds in *anything* matching. Seven shards have landed
since `SOURCES.sha256` was written; the committed CSV holds 34 curves, a live
`extract()` yields 41.

**The `_classify` rejection (`fig02:236-260`) drops more than the docstring
says.** It argues only the model_call case, but a v1.0 `env_step` is rejected too
(missing `model`), as are `run_start`, `env_meta` and `run_end`. Everything the
theoria ledger knows about *environment actions and their HTTP outcome* is
dropped; the dollars survive only because `cost_curve.json` is read separately.
That is why `fig02:434` writes `failed_step: None` for every theoria point.

**`theoria-arm/runs/20260728T015354Z-g50t-first-contact/turn_series.json` is the
join fig02 wants and has never read.** `archive.py:1184-1186` says so in as many
words — *"figure 2 needs all three on one axis and this is where they meet"* —
and it is not in `theoria_run`'s `members` tuple (`sources.py:355`). It exists
for one of the four discovered runs.

## 2 · The reconciliation, and the defect it found

`figures/reconcile_cost.py`, gate 9 of `figures/verify.sh`. Unit **`cost x
actions`**, four independent derivations, joined on `run_id`. 99 runs.

**`turns` does not vote** — `battery/INPUT_FORMAT.md:72-76` gap 5, still open
upstream; and `capability_spectrum` publishes *three* different `turns` (run
level, E2/E3 decisions, E4 billed calls: 20 vs 24 on one bare_cc run). Carried
as columns, marked non-voting.

**`score` does not vote, and that is not the same as calling score
unverifiable.** `proxy/SCORING.md:40-43`: all 32 real closed scorecards report
`score == 0.0`. A score anchor would agree everywhere while checking nothing.
The anchor that carries information is `total_actions` (`SCORING.md:60-62`,
32-of-32 exact), so per-run actions are a real check. Per-step is not comparable
between arms and is reported absent, not approximated.

### The finding: E5's denominator counts the RESET

`capability_spectrum.metrics.E5.support.actions` is **exactly one larger** than
both ledger-derived counts, on **every one of the 22 corroborated runs**. Cause:
it counts the run's single successful RESET as an action. `proxy/SCORING.md:60-62`
establishes the opposite — `total_actions` counts successful **non-RESET**
commands, verified 32-of-32 against real cards. Every bare_cc run has exactly one
successful RESET (24 of 24 in `baseline-arms/ledger.jsonl`).

So **E5 — cost per action — systematically understates cost per action**, and the
understatement is worst exactly where the number is most quoted: on a run with
one successful action it is off by half. `CITECHECK.md:108` records that §6.5
once cited E5 (`"haiku $0.031/action"`); that citation has since been removed,
which is the only reason this is not already in print.

Recorded as `KNOWN_DEFECTS["RESET_IN_DENOMINATOR"]` — declared, quantified, and
**asserted to still be true**: if it is fixed upstream the declaration goes stale
and gate 9 fails until it is removed, so the excuse cannot outlive the defect.

### What the reconciliation cannot do

**77 of 99 runs are `UNCORROBORATED` — including every theoria run.**
`capability_spectrum`'s `provenance.arms` lists `theoria_a0`, `theoria_a0_spike`
and `theoria_a2` — the offline worlds — and *not* the arm that played ARC. The
arm whose cost the plate most wants to compare is the one arm nothing
corroborates. `$0.9025/action` rests on a single run of 7 successful actions.

**Not one run is plain `AGREE`.** All 22 corroborated runs are
`AGREE(known-defect)`. There is currently no run in the repository on which two
derivations agree without an excuse.

## 3 · Where the four sources fall short, and the minimum that would close it

1. **The theoria arm has no second opinion.** Minimum fix: add
   `turn_series.json` to `theoria_run`'s `members` and have the battery ingest
   the live arm. It already publishes `totals = {actions, model_calls, usd}` with
   its own self-reconciliation. Cheapest of the four; needs no new run.
2. **E5's RESET.** One-line fix in the battery's E5 support, plus a re-run.
   Territory: `battery/`. Not mine — filed to `monitor/inbox/`.
3. **The ablation arm cannot be folded in and should not be.** It writes
   `arm: "theoria"` (`ablcore/ledger_abl.py:47`) because `proxy.ledger.ARMS` has
   no name for it (D-AB-004), so folding it in merges two arms under one label;
   and it spends nothing by construction (`ledger_abl.py:9`), so its
   `cost x actions` is `0/n`. It needs a registered arm name first.
4. **The shards are untracked.** Any figure built on them cannot be rebuilt from
   a clean checkout, and `SOURCES.md:105-112` already says so. This run did not
   change it; it is a release-manifest decision, not a figures one.

## 4 · The coverage probe was crying wolf twelve times

`check_coverage.py` gate 8 was **red at base** on 12 theoria run directories,
each reported as a "half-written run". Every one is a false positive: seven carry
no `cost` block at all (ordinary work-run directories — `a3-desk-gate`, `A11`,
`E14-crash-is-not-a-finding`), and five state `cli_reported_usd: 0.0`,
`model_calls: 0`. Twelve alarms, no true positive; the case the probe exists for
— a *billing* run whose cost curve never landed — had become the case it could
no longer distinguish.

The predicate now needs evidence: a partial directory fails when **its own
manifest reports spend** and the cost curve is absent. The other twelve are
still **named** (`COVERAGE-NAMED:` lines), which was always the demand — naming
and failing were never the same act. A negative control plants a spend claim on
one of them in memory and requires the probe to fire.
