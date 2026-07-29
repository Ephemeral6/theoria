# A14 · what the four artefacts cost, and what the board item got slightly wrong

## The board figure is right, and it is not the whole number

`$48.39` **reconciles exactly** as the sum the four checkpoints self-report:

| file | `cost_usd` (`campaign_*.json:7`) | in-campaign ledger sum | Δ |
|---|---:|---:|---:|
| `campaign_ar25.json` | 11.5625027 | 11.5625027 | 0 |
| `campaign_g50t.json` | 16.6150282 | 16.6150282 | 0 |
| `campaign_sk48.json` | 11.9327877 | 11.9327877 | 0 |
| `campaign_tn36.json` | 8.2757618 | 8.2757618 | 0 |
| **total** | **48.3860804** | **48.3860804** | **0** |

The rollup agrees with the per-call ledger to full float precision. Nothing is
missing *from the campaign as the checkpoints define it*.

**But the artefacts cost $50.39 to obtain.** Each shard ledger holds **14**
`run_id`s; each checkpoint's `episodes[]` names only **12**. The two extra runs
per game are earlier harness launches that were abandoned and restarted — each
game's log carries three `campaign:` header lines, and every launch re-prints
`$0.00 of $<ceiling> spent`. The spend counter resets on restart, so the first
two launches' money was dropped from `cost_usd` **and from the budget-ceiling
check**:

| game | orphan runs | orphan USD |
|---|---:|---:|
| ar25 | 2 | 0.5494091 |
| g50t | 2 | 0.5031304 |
| sk48 | 2 | 0.4608136 |
| tn36 | 2 | 0.4937198 |
| **total** | **8** | **2.0070729** |

$48.3861 + $2.0071 = **$50.3932**.

Not a gate breach either way — the four ceilings sum to $164.93 and no game
came close. But it is a real accounting defect in the harness's restart path,
and it is worth stating plainly: **the only place the $2.01 still exists is the
shard ledgers**, which were untracked until this commit. Had the rescue taken
only the four JSONs the board item named, the discrepancy would have become
permanently unrecoverable. That is the strongest single argument for the scope
widening in this run.

## Wall clock

`episodes[].wall_seconds` is `null` in all 48 episodes — the field was never
populated, so everything here is reconstructed from `started` / `resumed_at` /
`ended`:

* **machine wall-clock 8.673 h** (2026-07-27T18:19:36Z → 2026-07-28T02:59:58Z);
  all four ran concurrently, so `g50t` sets the envelope;
* **serial-equivalent 26.460 h** (ar25 6.054 + g50t 8.673 + sk48 6.623 + tn36 5.111).

## There is no independent register, and saying so matters

The task was to cross-check $48.39 against independent registers. **None
exists.**

| register | covers this campaign? | note |
|---|---|---|
| `out/shards/ledger.*.jsonl` | yes | the primary record; the JSONs are its rollup |
| `out/campaign/campaign_*.json` | yes | derived, and lossy across restarts |
| `proxy/var/spend_gate.jsonl` | **no** | earliest record 2026-07-28T09:26:25Z — 6.5 h *after* the campaign ended. The shared gate did not exist when this money was spent. |
| `baseline-arms/ledger.jsonl` | **no** | M4 pilot; `run_id` intersection with the shards is empty |
| `out/campaign_cells.jsonl` | **no** | 19 `phase3-*` cells; no cell for any of these four |
| `BUDGET_REPORT.md` §11.4 | **no** | reports $2.5275 for the gated `phase3-variance-envelope` ar25 run |
| `runs/*/MANIFEST.json` | **no** | one manifest, A7 only; its `track_total_including_pilot: 41.57` is a track total and must not be read as this campaign's |

The ledger and the checkpoints are **one measurement written twice**, not two
measurements. So $48.39 / $50.39 is **internally exact and externally
unverified**: it is what Claude Code's own `total_cost_usd` reported, summed
correctly. No provider-side billing record is in this repository, and this run
did not acquire one.

**There was also no `runs/<id>/MANIFEST.json` for these four campaigns at all**
until this directory. The provenance canon was not followed when the money was
spent; this run supplies the record after the fact and labels it as such.

## Per-file attribution

| file | as-published | all-in |
|---|---:|---:|
| `campaign_ar25.json` | $11.56 | **$12.11** |
| `campaign_g50t.json` | $16.62 | **$17.12** |
| `campaign_sk48.json` | $11.93 | **$12.39** |
| `campaign_tn36.json` | $8.28 | **$8.77** |
| **four files** | **$48.39** | **$50.39** |

Arithmetic uncertainty is zero. Provider-level uncertainty is unbounded and
unmeasured, per the paragraph above.

Quote **$48.39** for "what do these artefacts report"; quote **$50.39** for
"what did it cost to obtain them". The board item's phrasing (实测花费) is the
latter, so it is $2.01 light — a correction, not an error worth an incident.
