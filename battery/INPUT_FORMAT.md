# Battery input format — v0 draft

**Status: draft, pending alignment with `proxy/LEDGER_FORMAT.md`.** That file
does not exist yet; the P-2 dual-proxy ticket is writing it in parallel. This
document records what the battery assumes today so the merge is a diff and not
an archaeology exercise.

The battery reads two sources and normalises both into `battery/model.py`. No
metric ever sees a raw record.

---

## 1. The ledger — `env_step` / `model_call`

`baseline-arms/harness/ledger.py` already writes this and it is the de-facto
format in the repository, so the battery targets it rather than inventing a
third shape. Two record types share one JSONL file, told apart structurally:
a row with `frame` is an `env_step`, a row with `usage` is a `model_call`.

### `env_step`

| field | required | used for |
|---|---|---|
| `run_id` | yes | grouping; the unit of a "run" |
| `game_id` | yes | **the sealed-pile guardrail**, and pile provenance |
| `arm` | yes | which arm the row belongs to |
| `model` | yes | the model ladder used for discrimination |
| `step_idx` | yes | ordering |
| `action` | yes | revisit keys; string or `{"id", "data"}` |
| `frame` | yes | state identity (digested, never stored) |
| `frames_returned` | no | cascade width — how many frames one action returned |
| `state` | no | `WIN` detection |
| `levels_completed` | no | level boundaries, cross-level mechanism delay |
| `failed`, `reason`, `http_status` | no | failed steps are kept, not dropped |
| `http_tries` | no | **new in v1.** HTTP attempts the harness burned for this one row. The retry loop is collapsed into a single ledger row, so without this a step costing eight round trips is indistinguishable from one costing a single one. Feeds E6 |
| `available_actions` | no | read but not yet used; a per-state action-space size is the honest denominator the novelty metrics currently lack |
| `win_levels` | no | read but not yet used; total levels in the game |

### `model_call`

| field | required | used for |
|---|---|---|
| `run_id` | yes | grouping |
| `step_idx` | no | tying a call to the turn it decided |
| `usage.input_tokens` | yes | context growth |
| `usage.output_tokens` | yes | economy |
| `usage.cache_read_input_tokens` | no | context growth (dominates, once caching is on) |
| `usage.cache_creation_input_tokens` | no | context growth |
| `total_cost_usd` | no | cost curve, front-load index, convergence point |
| `duration_ms`, `is_error` | no | diagnostics |
| `attempt` | no | **new in v1, and load-bearing.** Retry ordinal. One decision may be billed several times with different token counts and different prices; without this the shape metrics count a retry as deliberation |
| `prompt_chars` | no | **new in v1.** Size of the assembled prompt. On a one-shot-CLI arm this is the only axis that grows — see gap 6 |
| `usage.cache_creation.{ephemeral_1h,ephemeral_5m}_input_tokens` | no | read but not yet used; the two tiers are priced differently, so the scalar cost is not re-derivable without them |
| `provider`, `usage.service_tier`, `usage.speed` | no | not used |

### Known gaps, to raise with `LEDGER_FORMAT.md`

Status as of v1, after reading the variance-envelope cells.

1. **`model_call` rows carry no `arm`.** *Still open.* 0 of 74 envelope rows
   carry one. The battery back-fills from the run's `env_step` rows; a run
   consisting only of model calls still lands as `arm="unknown"`.
2. **`game_id` is optional on `model_call`.** *Closed in practice, still not
   mandatory.* Every envelope `model_call` carries it. Worth making it
   schema-required so a ledger can be screened without being reassembled.
3. **Cost is a scalar (`total_cost_usd`), not a priced breakdown.** *Still
   open, and slightly worse.* `usage.cache_creation` now reveals a 1h/5m
   ephemeral split that is priced differently, and the scalar hides which
   multiplier was applied. A `price_list_version` field would fix it.
4. **No level-boundary event.** *Still open.* `levels_completed` is still a
   running counter, and it is `0` on every envelope row that carries it.
5. **No turn index distinct from `step_idx`.** *Still open upstream; worked
   around locally.* The battery now derives a decision axis by grouping calls
   onto the `step_idx` they were deciding (`Run.turn_costs()`, D-B-014), which
   is what E2/E3 use. `attempt` and `usage.iterations[]` are the two candidate
   native axes and both are degenerate in the material so far.
6. **No campaign field.** *New, and the one request this track would make.*
   `baseline-arms/ledger.jsonl` holds several campaigns in one file with
   nothing on a row to tell them apart, and they are not interchangeable — the
   variance-envelope cells are right-censored at ten cumulative failures by a
   harness rule. The battery reconstructs the label by joining
   `out/campaign_cells.jsonl` and `out/pilot_*.json` (D-B-013). A `campaign`
   field on the row would make the join unnecessary and the label reliable.
7. **Context growth is not observable on a one-shot-CLI arm.** *New.*
   `input_tokens` is a constant 10 and `cache_read_input_tokens` a constant
   24405 on every envelope call, because each turn is a fresh
   `claude -p --max-turns 1` in a clean directory: those numbers describe the
   CLI's own system prompt, not the arm. The history the arm re-reads lives in
   the prompt body. Any consumer computing "context growth" from the token
   fields alone will read approximately zero and will be measuring the harness.

---

## 1b. The offline theory bundles — three of them, and they differ

Each is a self-built world with a manual and no model calls, read by its own
adapter. They are kept as separate arms rather than merged into one `theoria`
because they differ in the only respect the repair metrics care about.

| bundle | arm | runs | traces | repair material |
|---|---|---|---|---|
| `cold-start-a0/` | `theoria_a0` | 2 | 275 + 111 steps | none |
| `a0-spike/` | `theoria_a0_spike` | 1 | **none persisted** | 4 injected rule changes, repaired by **rebuild** |
| `cold-start-a2/` | `theoria_a2` | 4 | 247 / 183 / 195 / 18 steps | 1 refutation, repaired by **patch** |

Three things a consumer of these must know:

* **`a0-spike` persists no trace.** Its evidence set is regenerable in memory by
  `pipeline/explore.py`, which the battery deliberately does not execute — a
  passive instrument reads artefacts and does not run another track's pipeline.
  So `steps=[]`, and the exploration family plus P1/P2/P3 are `not-applicable`
  rather than zero.
* **A2's four runs overlap by construction.** `history_trace[0..182]` is
  byte-identical to `raw_trace[0..182]`, and `probed_trace` shares the same
  prefix. They are one experiment and its variants, not four samples, and each
  run says so in `Run.notes["overlaps"]` so the de-redundancy pass cannot read
  four rows as four observations.
* **"Held-out" means two different things.** A0's denominator is 3 pairs its
  trace never covered; a0-spike's is an exhaustive enumeration of all 39960
  well-formed (state, direction) pairs. `Theory.held_out_frame` carries a
  one-line description of the sampling frame on every theory-bearing run, and
  K2 must not be compared across arms without reading it.

## 2. The A0 bundle — `cold-start-a0/` (read-only)

A0 is a self-built world, not an API game, so it has no ledger. Its adapter
reads the artefact bundle directly:

| file | supplies |
|---|---|
| `artifacts/raw_trace.jsonl` | steps. Row `t` holds the state *before* its action, so step `i` is identified by row `i+1`'s frame |
| `artifacts/trace_summary.json` | when each mechanism was first *used* |
| `artifacts/concept_accounts.json` | per-concept compression accounts (`script_delta_bits`) |
| `artifacts/score_vs_truth.json` | full-history replay accuracy and held-out accuracy |
| `artifacts/engines_report.json` | probes designed vs executable |
| `artifacts/plan_generated*.json` | optimal plan length, for the redundancy ratio |
| `theory/*.dsl` | clause counts, evidence annotations, proof and probe status |
| `theory/playbook.dsl` | playbook entries and deadlock theorems |

**A0 has no model calls.** The cold start was engines plus hand adjudication
with no LLM in the loop, so the economy family returns `not-applicable` on A0
runs. That is the honest answer and the battery prints it as such.

### The weakest joint

`parse_dsl` couples the battery to `dsl_grammar_v0.1`, which the
theory-compiler track owns and may change. The reader is deliberately shallow
— it counts clauses and reads `ev:` / `cov:` / `status:` / `probe:`
annotations, and understands none of the semantics. If the grammar moves, it
degrades to zero counts rather than crashing, and the epistemic family will
report a suspicious drop rather than silently wrong numbers. A real fix is for
the compiler to emit a machine-readable manifest alongside the DSL; that is a
request, not something the battery should do for itself.

---

## 3. What the normalised record looks like

See `battery/model.py`. The short version:

```
Run   run_id, arm, source, model, game_id, pile, steps[], calls[], theory?, truth?
Step  idx, action, state_key, failed, n_frames, level, won
Call  idx, step_idx, input/output/cache tokens, cost_usd, duration_ms, is_error
Theory  concepts[], clauses[], playbook_entries, deadlock_theorems, revisions,
        probes_designed/executable, replay_agree/pairs, held_out_agree/pairs
Truth   optimal_steps, mechanisms{name: {first_seen, first_used}}, levels
```

Three properties are load-bearing:

* **`state_key` is a digest, never a state.** Exploration metrics need state
  *identity* and nothing more. Keeping observations out of the metric layer
  also means a metric cannot learn a game's mechanics.
* **Failed steps survive normalisation.** They consumed a turn and usually a
  model call. Dropping them would flatter every economy metric.
* **Everything optional is `None`, never `0`.** A missing input yields
  `not-applicable` with a stated reason. A battery that reports zero for
  "no data" is a battery that will eventually be believed.
