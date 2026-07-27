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

### Known gaps, to raise with `LEDGER_FORMAT.md`

1. **`model_call` rows carry no `arm`.** The battery back-fills it from the
   run's `env_step` rows. A run consisting only of model calls — an arm that
   thought for a long time and never acted — currently lands with
   `arm="unknown"`. Worth a field.
2. **`game_id` is optional on `model_call`.** The guardrail therefore leans on
   `env_step` for its screen. It should be mandatory on both, so a ledger can
   be screened without being reassembled first.
3. **Cost is a scalar (`total_cost_usd`), not a priced breakdown.** Phase 1
   says the price list is versioned separately and cost is "a conversion, not a
   record". The battery consumes the scalar today and will prefer a
   `price_list_version` field so a recompute can be re-priced.
4. **No level-boundary event.** `levels_completed` is a running counter on
   `env_step`, so the battery infers boundaries from its jumps. Phase 1
   anticipated this ("level 若非 API 字段则由 score 跳变推导"). An explicit
   boundary record would remove the inference.
5. **No turn index distinct from `step_idx`.** A turn with several actions and
   one model call, or one action and several calls, is currently only
   reconstructible through `step_idx`. The economy family is defined per
   *turn*; it uses model-call order as its turn axis and says so.

---

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
