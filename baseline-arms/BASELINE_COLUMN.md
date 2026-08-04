# The paper's left-hand column — what the baseline arm measured, and what it did not

**A28b · 2026-08-04 · territory `baseline-arms` · offline, no spend**

A28 found that the bare-CC zero is genuinely read and genuinely zero, and then
found what it took to be the finding that changes the paper: that on `g50t` and
`sk48` no run was ever *allowed* enough actions for level 1, so their zero is a
budget artefact. This document does two things: it withdraws that second half —
**it is false, and false in a way that made the arm look better-controlled than
it is** — and it replaces it with the comparison the paper actually needs.

Reproduce every number here with:

```bash
cd baseline-arms && python -m harness.baseline_allowance          # the table
cd baseline-arms && python -m harness.baseline_allowance --json   # the same, machine-readable
cd baseline-arms && python -m pytest -q tests/test_baseline_allowance.py
```

---

## 1 · The honest per-game comparison

Three columns, and they must be printed together or not at all: what level 1
costs, the most any run was ever **allowed** to spend, and the most any run
**did** spend.

| game | level-1 baseline | max allowance | max achieved | what ended the best run | verdict |
|---|---:|---:|---:|---|---|
| `ar25-0c556536` | 32 | **748** | 67 | `game_over` — the game ended | capability tested |
| `g50t-5849a774` | 78 | **879** | 73 | `api_unusable` — the harness stopped it | abort artefact |
| `sk48-d8078629` | 61 | **1070** | 38 | `api_unusable` — the harness stopped it | abort artefact |
| `tn36-ef4dde99` | 32 | **317** | 32 | `api_unusable` — the harness stopped it | abort artefact |

**The allowance clears the level-1 baseline on all four games**, by a factor of
9.7 to 23. Not one of the four zeros is a budget artefact.

### Why A28 read it the other way

A28 read the allowance out of `runs/bare_cc-*/run.json`, key `budget`. That is a
real population — 36 runs, budgets 20 and 30, the M4 pilot (D-008) and the
Phase-3 variance envelope (D-011) — and every one of them is indeed capped below
its own level-1 baseline. It is not the arm's ceiling.

The arm's largest allowance was granted by the approved **S1 baseline-parity**
campaign (`harness/campaign.py`, `BUDGET_REPORT.md` §3.4): a per-game action
budget equal to the sum of that game's official level baselines, with each
episode handed whatever remained of it —

```python
remaining = total_budget - state["actions_ok"]
summary = bare_cc.play(game_id, model, remaining, client=client, ...)
```

Those 48 episodes have **no `runs/` directory**. The archive says so itself, in
`runs/s1-full-run-not-archived/run.json`:

> "the approved S1 haiku full run (BUDGET_REPORT.md 3.4) is driven by a
> concurrent session and its checkpoints and ledger shards were still being
> written when this archive was built. Archiving a file mid-write would record a
> hash that is true of nothing. INCIDENTS.md INC-BA-003."

So a reader that goes through `runs/` cannot see the largest budget this arm ever
approved. Their allowance is in `out/campaign/campaign_*.json` under
`total_budget`, and their per-step record is in `out/shards/ledger.*.jsonl`.
`harness/baseline_allowance.py` reads all three sources and keeps the provenance
attached to each number.

### The same numbers split by regime

Allowance is per run, so the split matters:

| game | regime | runs | allowed ≤ | achieved ≤ | outcomes |
|---|---|---:|---:|---:|---|
| `ar25` | S1 baseline-parity | 12 | 748 | 67 | `api_unusable` 11, **`game_over` 1** |
| `ar25` | m4-pilot | 6 | 20 | 15 | `budget_exhausted` 2, `model_error` 2, `api_unusable` 2 |
| `ar25` | phase3-variance-envelope | 3 | 30 | 19 | `api_unusable` 3 |
| `g50t` | S1 baseline-parity | 12 | 879 | 73 | `api_unusable` 12 |
| `g50t` | m4-pilot | 8 | 20 | 14 | `budget_exhausted` 6, `model_error` 2 |
| `g50t` | phase3 unit-price / envelope | 6 | 30 | 30 | `budget_exhausted` 6 |
| `sk48` | S1 baseline-parity | 12 | 1070 | 38 | `api_unusable` 12 |
| `sk48` | m4-pilot | 8 | 20 | 15 | `budget_exhausted` 4, `model_error` 4 |
| `sk48` | phase3 unit-price / envelope | 5 | 30 | 28 | `budget_exhausted` 5 |
| `tn36` | S1 baseline-parity | 12 | 317 | 32 | `api_unusable` 12 |
| `tn36` | m4-pilot | 6 | 20 | 13 | `budget_exhausted` 2, `model_error` 2, `api_unusable` 2 |
| `tn36` | phase3 unit-price / envelope | 8 | 30 | 24 | `budget_exhausted` 2, `api_unusable` 3, `gave_up` 2, `no_reset_window` 1 |

---

## 2 · What actually stopped the runs that had the actions

All 48 S1 episodes are in the ledger shards, with a per-step `failed` flag, so
the shape of their failures is recoverable without re-running anything.

* Recorded outcome `api_unusable`: **47 of 48**.
* Every one of those 47 stopped at **exactly 10 cumulative failed actions** —
  the rule in force at the time, `actions_failed >= 10`, absolute and not scaled
  to the budget it was judging.
* Longest run of **back-to-back** failures anywhere in the campaign: **5**.
  Modal value 2–3.
* Under the rules in `bare_cc.py` today — `CONSECUTIVE_FAILURE_ABORT = 10` and
  `cumulative_failure_cap(budget) = max(10, budget)`, i.e. 317–1070 at these
  budgets — **0 of 48 episodes would have aborted**.

That rule was already ruled invalid inside this territory. `BUDGET_REPORT.md`
§11.2 and `DECISIONS.md` D-016, verbatim: at a ~0.6 action success rate the
absolute ten is *"guaranteed by construction rather than earned by the API"*, and
collapsing scattered failures into the outcome name `api_unusable` "is how a real
measurement gets thrown away". D-016 split the rule in two. **The S1 campaign has
never been re-run under it.**

So the sentence that survives is not "the budget was too small". It is:

> The only campaign that ever gave the baseline arm enough actions was
> terminated, on 47 of 48 episodes, by a stop rule this territory has since
> replaced — and none of those 47 episodes would abort under the replacement.

### The one datum that is about the arm

`bare_cc-ar25-claude-haiku-4-5-20251001-76390591` — 67 successful actions, 8
failed, **2.09× the level-1 baseline of 32**, terminal state `GAME_OVER`,
`level_scores` all zero. That episode ended because the game ended. It is the
entire stock of capability evidence in the baseline arm: **one episode, one
game, one model tier.**

Note what this costs A28's other half. A28 counted `tn36` as capability-tested
because a run *spent* 32 actions against a 32-action baseline. Two runs did, both
`NOT_FINISHED`, both stopped at the ten-failure cap. Spending the baseline is not
the same as being allowed past it, and a truncation is not a loss.

---

## 3 · The 42.83 % reference, and whether anything here is commensurable with it

`Theoria.md:270` puts **42.83 %** in the 分数 column of the main table, on the
row 裸 Claude Code, beside Schema's 98.98 % and Theoria's ⟨target⟩.

### Where the number comes from

Every occurrence in this repository traces to the same place, and none of them
is a measurement made here:

* `baseline-arms/SCHEMA_LOCATE.md` §1 — the pair 42.83 % / 98.98 % is what
  *identified* the upstream system (Schema, canonically **Zeng et al.**, not
  Feng et al.; Impossible Research / UC Berkeley / CMU). The metric is **RHAE**,
  the set is **the 25 public ARC-AGI-3 games**, and the gap +56.15 pp is what
  `Theoria.md:393` reuses as "+56pp".
* `papers/phase1-workshop/runs/20260728T102014Z-P7/search-traces/line0-schema-attribution.md`
  §Source C — "42.83 % → 98.98 % RHAE on the 25 public games", from third-party
  coverage, marked there as *corroborating, not load-bearing*. The same trace
  rules that 98.98 % "must not be treated as a measurement made here"; the same
  applies to its partner and has never been written down.
* `SCHEMA_LOCATE.md` §2.1–2.2 — there is **no paper and no code**. The only
  publication is a project page whose own BibTeX is `@misc`. The harness that
  produced both numbers has never been released, so the budget regime, the
  scaffold, the retry policy and the stopping rule behind 42.83 % are all
  unknown and unknowable from here.

### Whether it is commensurable with this arm's runs

**No, on four independent axes, and the repository cannot close any of them.**

| axis | 42.83 % | what `baseline-arms` measured |
|---|---|---|
| metric | RHAE, upstream's | scorecard `score` (0.0), `levels_completed` (0) |
| population | 25 public games | 4 development-pile games |
| allowance | unpublished | 20 / 30 per run, or S1 parity 317–1070 |
| scaffold | unpublished harness | `claude -p`, `--max-turns 1`, no tools, no `CLAUDE.md` (D-009/D-010) |

The metric axis is the one that cannot be argued around. **RHAE is nowhere
defined in this repository.** The only structural facts on disk are that it is
baseline-action-relative, that it carries a squared penalty on action flooding
and truncates at 5× baseline
(`monitor/inbox/20260731T1600Z-W-1800-iteration-prior-art-brief.md`), and that
`arc-recon/ACCESS_CHECK.md` §3 — which is the authority on the scorecard body —
never states the formula behind the `score` field this arm reads. So whether
42.83 % and 0.0 are numbers in the same units is **not established anywhere on
disk**, and putting them in one column asserts that they are.

Even granting the units, the regimes do not meet. RHAE is bounded above by level
completion; a run that completes nothing scores zero in it by construction. A
regime that produces 42.83 % is one in which levels get completed, which is a
regime this arm has never been in. Comparing them is the error the main table
exists to avoid: the table is an ablation of division of labour, and an
external number carrying its own unpublished harness is a different shell.

### The ruling

**42.83 % is an external reference, not this project's baseline arm.** It
belongs where `SCHEMA_ARM_RULING.md` (D-BA-023) already put 98.98 %: under the
main table, in the 外部参照 block, labelled 未复现, with its metric, its set and
its unknown budget regime beside it. The 裸 Claude Code **row** of the main table
should carry what this project measured, or be empty — and today it must be
empty, because §2 says the arm has one usable episode.

This is the same disease `SCHEMA_ARM_RULING.md` diagnosed on the right-hand
side — an identity claim and a material claim sharing one cell — showing up
symmetrically on the left.

---

## 4 · Replacement wording

Delivered as proposals to `monitor/inbox/`, not edited into their territories:

* `monitor/inbox/20260804T1310Z-baseline-arms-to-papers-the-left-hand-column-is-an-external-number.md`
* `monitor/inbox/20260804T1310Z-baseline-arms-to-freeze-the-bare-cc-comparator-is-not-a-measured-arm.md`

The wording this territory can stand behind, for any claim that leans on the
baseline column:

> **Bare Claude Code (`bare_cc`), development pile, this project's own runs.**
> Authoritative scorecard score **0.0** on all four development-pile games — 63
> archived scorecard bodies across 57 distinct run_ids, every one reporting 0.0
> at card, environment and run level, and `levels_completed` 0. Action
> allowances were 20 or 30 per run in the pilot and variance-envelope regimes,
> and 317–1070 per game in the approved S1 baseline-parity campaign, against
> level-1 baselines of 32–78. **The allowance was therefore adequate on all four
> games and the zero is not a budget artefact.** It is also not, on three of the
> four games, a capability result: 47 of the S1 campaign's 48 episodes were
> terminated by an absolute ten-failure abort rule that `DECISIONS.md` D-016 has
> since replaced, and reconstructed from the ledger not one of them would abort
> under the current rule. **Exactly one episode in the whole arm ended because
> the game ended** (`ar25`, 67 successful actions, 2.09× the level-1 baseline,
> `GAME_OVER`, score 0.0). On `g50t`, `sk48` and `tn36` the arm has **no**
> capability datum; that is recorded as absent, not as zero.
>
> **The 42.83 % figure is not this arm.** It is upstream's self-reported RHAE
> for a bare-Claude-Code baseline over the 25 public ARC-AGI-3 games (Zeng
> et al., Impossible Research; no paper, no code, no published budget regime).
> It is not commensurable with the numbers above — different metric, different
> game set, different and unpublished allowance, different scaffold — and it is
> reported here as an external reference only.

---

## 5 · The corrected run: what it would cost and what it would settle

**Not run. This document is offline and spends nothing.** Priced from this
territory's own measurements, so the figures can be checked rather than trusted.

Unit price, haiku (the approved tier): `python -m harness.unit_prices` gives
**$0.0437/action** on the current transport (jar-on, 10 cells, action success
0.916) and $0.0461 jar-off. The S1 campaign itself came in at
**$48.3861 / 1453 successful actions = $0.0333/action**. Both are quoted below.

| option | actions | @ $0.0333 | @ $0.0437 | what it settles |
|---|---:|---:|---:|---|
| A. parity, 1 episode per game (Σ level-1 baselines = 203) | 203 | $6.76 | $8.87 | whether `bare_cc` clears level 1 when the abort rule is not in the way — **one draw per game** |
| B. 2× level-1 headroom, 1 episode per game | 406 | $13.52 | $17.74 | the same, at the only depth ever observed to end in a real terminal state (2.09×) |
| C. option B × 3 replicates (D-011's replicate count) | 1218 | $40.56 | $53.23 | a per-game answer with a variance around it, i.e. a control that can fail |
| D. re-run the full S1 budget | 3014 | $100.37 | $131.71 | the approved comparison as originally specified (`campaign.py` docstring: "~$103") |

**What it does not need.** It needs no code change and no budget change: the
allowance was already adequate and the abort rule is already fixed. It is a
re-run, not a new experiment. That is the cheapest thing in this project that
can turn the left-hand column from an artefact into a measurement — option C, at
about $41–53, against the $120-per-leg Theoria legs.

**Two risks to price in, both already recorded here.**

1. `arc-recon/ACCESS_CHECK.md` §3 trap 2 — scorecards auto-close after 15
   minutes of inactivity. An episode of 200–1000 actions at 43 s/action wall is
   2.4–12 hours; the campaign must keep the card alive or it loses the score it
   is buying. This is exactly the trap that destroyed 13 of 14 pilot cells.
2. INC-BA-003 — the degradation the S1 campaign measured (success 0.713 → 0.595,
   HTTP/action 7.11 → 9.66, $/action +68 %) coincided with three workloads on
   one API key. A corrected run that shares the key with a live Theoria leg will
   reproduce the failure rate, if not the abort. **Do not schedule it against the
   A26b legs.**

---

## 6 · Absence, recorded as absence

* **2 of 57** observed run_ids have no allowance in any of the three sources —
  `bare_cc-ar25-…-833db563` and `bare_cc-g50t-…-29065be4`. They are named by the
  tool, excluded from every maximum, and are not rendered as an allowance of 0.
* **`g50t`, `sk48`, `tn36` have zero capability data.** Absence of evidence, and
  it stays written as absence rather than as a zero, in every sentence in §4.
* **The arm still persists no score.** 0 of 43 archived `run.json` carry one
  (A28 §2, unchanged). The score is recoverable only from archived scorecard
  bodies; the 404-on-close trap destroyed it for every run whose close failed.
* **Whether the S1 failures were the API's fault is still unknown.** The
  reconstruction says only that today's rule would not have aborted on them; it
  cannot say the actions would have succeeded. Option A–D is what settles that,
  and nothing on disk can.
* **RHAE is undefined in this repository**, so the units of 42.83 % cannot be
  checked here at all. Closing that gap means reading upstream material, and the
  upstream artefacts are the highest-risk objects on the pile
  (`INCIDENTS.md` INC-BA-001) — the four development-pile directories are the
  only ones that may be touched, and that is a separate, boarded decision
  (`SCHEMA_LOCATE.md` §4 route A).

## 7 · Standing defect, unchanged and re-observed

`python -m pytest -q` under `baseline-arms` **rewrites tracked files under
`runs/`** — 17 of them, cold, then passes warm. A28 §7 filed it; it reproduced
exactly here (6 failed cold / 3 failed warm, the delta being three
`test_archive_runs.py` cases that the first run repairs into green). A gate that
edits the artefact it audits cannot certify it. Not this document's scope; still
true, and now observed twice.
