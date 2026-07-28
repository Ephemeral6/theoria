# INCIDENTS — theoria-arm

Things that went wrong, or that make a number in this track's reports mean less
than it appears to. Numbered `INC-TA-nnn`. An incident is recorded when it is
noticed, not when it is resolved.

---

## INC-TA-001 · Two arms played `g50t` concurrently, on one quota — severity: high

**What.** The Theoria arm's first live contact on `g50t-5849a774` ran at the
same time as another Claude Code session's `baseline-arms` `bare_cc` campaign
**on the same game**. Both were in flight at `2026-07-28T01:28Z`:

* this arm: `runs/<slug>/ledger.jsonl`, ACTION4, a run of consecutive HTTP 400s;
* the other session: `baseline-arms/out/shards/ledger.g50t.jsonl` last written
  `01:28:59Z`, and `baseline-arms/out/campaign/g50t.log` reading
  `episode 10 died (api_unusable); restarting from level 1` /
  `episode 11, 444 actions left, $13.64 of $48.10 spent`.

**How it was found.** Not by design. This arm's HTTP amplification was running
at 15–19 commands per successful action, far above the 5.07 `baseline-arms`
measured on its own confirmation run, so the repo was checked for other writers.
`find -newermt '-10 minutes'` found the other campaign's shard ledger.

**Why it matters, precisely.** This is `baseline-arms`' own INC-BA-003
recurring, with this track as the second party. Three consequences:

1. **Every wall-clock and amplification number this track reports is
   confounded.** `attempts`, `commands_sent`, `http_amplification` and
   `elapsed_s` in this run's `MANIFEST.json` were measured against a backend
   that another session was also driving. They are an upper bound on this arm's
   own cost, not a measurement of it, and they may not be compared with
   `baseline-arms`' 5.07 or `arc-recon`'s 2.5–10× without this caveat.
2. **Neither side can see the joint total.** Two gates, two ceilings, one
   quota, one bill. This arm's ceilings (120 actions, $20) bound *this arm*
   and nothing else.
3. `episode 10 died (api_unusable)` on the other side is consistent with
   contention but is **not** attributed to it here — the 400 wave is a
   documented property of ARC's multi-instance backend (INC-001b/INC-002a) and
   was already observed in this repo during quiet periods. No causal claim is
   made in either direction.

**What was done.** Nothing to the other session. Its process was not killed,
its files were not touched, and `baseline-arms/` was read only. That is the
discipline that track kept when it found this arm's predecessors, and it is
kept here for the same reason: a run destroyed to make another run's numbers
prettier is worse than a run with a caveat.

This arm continued. Stopping would have delivered nothing, and the action
budget it was given is its own — the contention costs time and inflates the
retry count, but it does not spend another arm's actions.

**What would fix it.** The same thing `baseline-arms` asked for and did not
get: a cross-session gate — a lock file or a shared counter under `arc-recon/`
that any arm must take before opening a scorecard, so that two sessions
serialise instead of interleaving, and so that one of them can see the joint
total. That belongs in shared ground (`arc-recon/`), not in either arm, and
is not built here because building it would mean writing into a directory this
track is read-only in.

---

## INC-TA-002 · The score obligation is undischargeable against the live API — severity: medium

`LEDGER_FORMAT.md` §3 states as a **hard obligation**, not a diagnostic, that
the score derived from `env_step` records must equal the score the scorecard
reports, and that inequality is an incident.

It cannot be computed. Live ARC command responses carry no `score` field at
all. The complete key set, confirmed on this run's own RESET and consistent
with `arc-recon`'s 84 successful command responses, is:

```
action_input, available_actions, frame, full_reset, game_id, guid,
levels_completed, state, win_levels
```

Score exists only inside a successful `POST /api/scorecard/close` response.
`proxy/env_proxy.py` reads `response_body.get("score")` and therefore writes
`score: null` into every `env_step`, and `proxy/reconcile.py` compares that to
the scorecard's number.

**Recorded as an incident rather than waived.** `armtools/archive.py` reports
`score_reconciliation: "unavailable"` with this reason, and reconciles the two
quantities the API *does* return — `levels_completed` and the successful action
count — in its place. The obligation as written in `LEDGER_FORMAT.md` needs
either a new derivation (the scorecard's per-run `level_actions` may support
one) or an amendment. Both are decisions for the track that owns `proxy/`;
this is a report, not a request.

---

## INC-TA-003 · `proxy/cost.py` under-bills 1-hour cache writes — severity: low, but it compounds

**What.** `proxy/pricing/pricing_v1.json` carries three cache multipliers:

```json
"cache_read_input_tokens": 0.1,
"cache_creation_input_tokens": 1.25,
"cache_creation_input_tokens_1h": 2.0
```

`proxy/cost.py` can only ever apply the first two. It reads the provider's flat
`usage.cache_creation_input_tokens` key, and that key does not say which TTL
was bought. The TTL **is** reported — in a nested `usage.cache_creation`
object with `ephemeral_5m_input_tokens` and `ephemeral_1h_input_tokens` — which
`cost.py` does not read. So every 1-hour cache write is priced at 1.25× when it
should be 2.0×.

**Measured, on this arm's first live theorize call.** All 20,736
cache-creation tokens were 1-hour writes:

| | USD |
|---|---|
| `proxy/cost.py` over the recorded usage | 1.218392 |
| the CLI's own `total_cost_usd` | 1.307727 |
| gap | **−0.089335 (−6.8%)** |
| explained by the 1h multiplier | 0.077760 (87% of the gap) |
| residual, unexplained | 0.011575 (0.9%) |

The residual is left unexplained rather than rounded away. It may be
`server_tool_use`, a rounding convention, or a price the table has slightly
stale; this run cannot tell.

**Why it compounds.** Theoria's whole bet is on the *shape* of the bill
(`Theoria.md` 1.12, C5), and cache reads are the axis the bet is placed on. A
systematic 7% under-statement on the cache-write line is small per call and is
not small across a Phase 2 battery that re-prices every arm's history from one
table.

**What was done.** Reported, not fixed — `proxy/` belongs to another track. The
diagnosis is computed automatically for every run by
`armtools/archive.py::_cache_ttl_diagnosis`, so it appears in every
`MANIFEST.json` under `cost.cache_ttl_diagnosis` and cannot quietly stop being
true. The multiplier the table needs is already in the file; what is missing is
the read.

This finding exists only because the run records **two** cost figures. A
cross-check against a single source would have reported the table's number as
the answer.

---

## INC-TA-004 · Two live runs aborted on arm defects, at a cost of 11 actions and $2.05 — severity: medium

Recorded because the cost is real and because "the loop was proved offline"
turned out to mean less than it sounded.

| attempt | died on | actions | model calls | cost |
|---|---|---|---|---|
| 1 | manual declared landmarks the level generator never placed → `ProblemError` on every compile | 5 | 1 | $1.31 |
| 2 | desk had tools, spent its single turn on `mkdir && cat >`, returned no text | 6 | 1 | $0.73 |
| — | verifying the tool fix before spending another action | 0 | 1 | $0.01 |

Neither is world behaviour. Both are defects in this arm that four offline
proof runs — `a0-spike`, `cold-start-a0`, A1, `cold-start-a2`, plus this
track's own 44 tests and two mock dry runs — did not surface, because:

* the offline worlds are small enough that a manual never needs a landmark;
* the offline desk was `claude-haiku-4-5`, which answered in text where
  `claude-opus-5` reached for a file. **The dry run used a different model from
  the live run and that difference hid a defect.** If there is one procedural
  lesson here it is that one: rehearse with the model you will fly with, or
  accept that the rehearsal did not cover the model.

Both aborts are archived in full rather than deleted —
`runs/*-aborted/ABORTED.md` — including the manual attempt 1 produced, which
was good, and the 19,957 output tokens attempt 2 paid for and never printed.
