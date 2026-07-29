# The canon migrator — interface

**Audience: the `baseline-arms` track (P-12).** F-16 ruled
`proxy/LEDGER_FORMAT.md` the canon and `baseline-arms/harness/ledger.py`'s
spelling the dialect. This document is the interface to the translator. **The
migration of the stock ledgers is yours; the translator is ours.** Nothing here
asks you to change your harness.

---

## 1. The two commands

```bash
# lift a v0 ledger into canonical v1.0
python -m proxy.tools.upgrade_ledger <v0.jsonl> -o <canon.jsonl> \
    [--scorecards <probe_log.jsonl>] [--arm bare_cc]

# judge any stream against the canon, whoever wrote it
python -m proxy.tools.validate_ledger <canon.jsonl>
```

`upgrade_ledger` **never writes to the input**. It reads, translates, writes a
new file, and prints a report:

```json
{"source": "...", "source_sha256": "sha256:…", "out": "...",
 "out_sha256": "sha256:…", "records_in": 1125, "records_out": 1153,
 "runs": 14, "runs_with_scorecard": 8,
 "migrator": "proxy.tools.upgrade_ledger", "migrator_version": "1.0.0"}
```

The output is byte-reproducible for a fixed input: same bytes in, same bytes
out, so `out_sha256` is a fingerprint you can put in a `MANIFEST` and compare
later. `seq` is dense over the whole output; `ts` is the **original** timestamp,
never the migration time — a lifted stream records when things happened, not
when they were translated.

There is a Python entry point if you would rather drive it yourself:

```python
from proxy.tools.upgrade_ledger import lift, scorecards_by_run
canon_records = lift(v0_records, source=path, source_sha256=digest,
                     scorecards=scorecards_by_run(probe_log_path))
```

## 2. Pass `--scorecards`, or half your runs cannot be reconciled

Your closed scorecards live in `probe_log.jsonl` as `note: "close scorecard"`
responses with `opaque.run_id`. Give the migrator that file and it attaches each
card to the synthesised `run_end` for its run. Then the frozen scorer can
actually discharge Phase 1's reconciliation obligation.

On `out/shards/ledger.ar25.jsonl` with `out/shards/probe_log.ar25.jsonl`:
**8 of 14 runs reconcile PASS; 6 come back `UNDETERMINED`** because their card
was lost to the transient close-404 you documented in D-015. `UNDETERMINED` is
not `PASS` and never collapses into it — that distinction is the whole reason
the scorer has three verdicts.

## 3. The mapping, field by field

| v0 | canon v1.0 | note |
|---|---|---|
| `frame` | `frames` | v0's value is already a list of grids, so it carries across unchanged. The rename matters because the *type* is now guaranteed: one command has been observed returning seven frames. |
| `timestamp` | `ts` | `.000` appended. v0 is second-precision; the milliseconds are padding, not precision. |
| `frames_returned` | `n_frames` | when absent, `len(frames)` |
| `win_levels` | `response.win_levels` | **the only place the environment states a game's level count.** Without it no score fraction is computable from the ledger alone. |
| `available_actions` | `response.available_actions` | |
| `http_status` | `http.status` | |
| `http_tries` | `http.attempts` | |
| `reason` | `http.error` | |
| `failed` | — | falls out of `http.status`. v0's single flag conflated "the server refused" with "the guard refused"; canon separates them, and a lifted step always gets `guard.decision: "allow"` because no guard was in the path. |
| `duration_ms` | `http.elapsed_ms` | |
| `attempt` | `http.attempts` | |
| `prompt_chars` | `http.request_chars` | |
| `arm`, `model` | the synthesised `run_start` | they are properties of a run, not of a step |
| `total_cost_usd` | **dropped as a field** | §5 rules cost derived and `canon.py` refuses it. The number is kept as a per-run total in `run_start.lifted.dropped.total_cost_usd_v0`, labelled as your harness's own arithmetic. Recomputing it properly needs a `pricing_ref`, which v0 never wrote. |

### What the migrator synthesises

* one `run_start` per run — `game_id`, `model`, and a `lifted` block (below);
* one `run_end` per run — `outcome: "lifted"` (not an invented outcome),
  `steps`, `model_calls`, `levels_completed`, and the scorecard if one was
  found.

## 4. Provenance lives on `run_start`, not on every record

`LEDGER_FORMAT.md` §7 originally said to mark each lifted record
`"lifted_from": "baseline-arms/v0"`. That was written before the two shapes'
field sets were closed, and a closed shape cannot carry an extra marker. So
provenance moved to the synthesised `run_start`, where the payload is open (§6)
— and it says strictly more there.

(That premise expired: since S9 the two shapes are additive-safe and *could*
carry a per-record marker. The decision stands on the reason that outlived it —
the block below says more than a boolean would, and provenance belongs where it
can be stated once and completely.)

```json
"lifted": {
  "lifted_from": "baseline-arms/v0",
  "source": "out/shards/ledger.ar25.jsonl",
  "source_sha256": "sha256:…",
  "migrator": "proxy.tools.upgrade_ledger", "migrator_version": "1.0.0",
  "records": {"env_step": 569, "model_call": 556},
  "dropped": {"total_cost_usd_v0": 11.5625027, "_note": "…"},
  "holes": ["model_call.request", "model_call.response",
            "env_step.card_id", "env_step.guid", "http.elapsed_ms on env steps"]
}
```

Every lifted record belongs to a run, so nothing is unattributed. **A reader can
tell a lifted stream from a native one by the presence of this block**, which is
what §7 wanted the marker for.

## 5. The holes — read this before comparing a lifted run to a native one

These are not lossy conversions. The bits were never written down:

* **`model_call.request` and `model_call.response` are `null`.** v0 recorded
  `usage` and `prompt_chars` only. §4 says the full text is what stands in for a
  model call being unreplayable, so a lifted `model_call` is strictly *less*
  than a canonical one. Any metric that reads request or response text will find
  nothing, and should say "not available for lifted runs" rather than zero.
* **`env_step.card_id` and `guid` are `null`.** v0 did not record them per step.
  Consequence: check `S-5` ("the steps counted against this very card") comes
  back `UNDETERMINED` on lifted runs. It is not a failure and must not be read
  as one.
* **`http.elapsed_ms` is `null` on env steps.** v0 timed model calls, not
  environment calls.
* **`env_step.score` is `null`** — but that one is not a hole. The live API
  returns no `score` field on a command response at all; it returns
  `levels_completed` and `win_levels`. Canon keeps the field because it is in
  §3, and it stays null on live traffic.

## 6. What the canon will now refuse

`proxy/ledger.py` calls `proxy/canon.py` before anything reaches disk, so a
non-canonical field is an error at write time rather than a surprise at read
time. If you write into a canonical ledger yourself, expect these:

* every v0 spelling in the table above, by name, with its replacement quoted in
  the error message;
* `cost`, `cost_usd`, `total_cost_usd`, `price_usd` anywhere;
* an envelope field (`v`, `seq`, `ts`, `event`, `run_id`, `arm`) set by a
  caller — those are the writer's;
* a **missing required** field on `env_step` or `model_call`;
* `frames` that is not a list; `score`/`levels_completed`/`step_idx`/`level`
  that is a bool; an `action` that is not exactly `{name, id, data}`; a `guard`
  without a decision; a `usage` that is not an object.

**What it will no longer refuse, since S9:** a field on `env_step`/`model_call`
that §3/§4 simply does not list. Those two shapes used to be closed; the closure
refused a live `model_call` after the provider had been paid $2.695 and the
reply was discarded (INC-TA-006), and a writer that runs after the money is
spent may not refuse — refusing cannot un-spend it, only destroy the evidence.
Such a field is now warned about (`canon.UnknownField`, counted in
`Ledger.unknown_fields`) and written, and `validate_ledger.py` reports it as a
**notice** that leaves the verdict alone. The reasoning is `proxy/DECISIONS.md`
D-030; the rule for changing this contract again is `proxy/CONTRACT_CHANGES.md`.

For this migrator that is a widening and nothing you do changes: a lifted stream
that was canonical before is canonical now.

Auxiliary records (`run_start`, `run_end`, `env_meta`, `guard_block`,
`incident`) keep an **open** payload — only their required keys are enforced.

## 7. What we would like back, and what we are not asking for

**Not asking for:** any change to `harness/ledger.py`. Your v0 stream is the
historical record and rewriting history to match a later format would be worse
than translating it.

**Would like back, when P-12 runs the migration:** the `out_sha256` of each
lifted file in your `MANIFEST`, and a line in `PARTNER_SYNC` if the migrator
mis-translates anything. It refuses what it does not understand
(`UnknownDialect`) rather than guessing, so a silent mistranslation should be
impossible — but "should be" is why we are asking.
