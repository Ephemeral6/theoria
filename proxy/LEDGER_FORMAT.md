# LEDGER_FORMAT v1.0

The ledger is the record surface of the closed system. Phase 1 defines "closed"
with three properties, and this format exists to make each of them checkable
rather than asserted:

* **Complete record** — every bit entering or leaving an arm is in the ledger.
  The two proxies are the only network surface an arm has, and both write here.
* **Replayable** — a game can be re-run from the ledger alone: the environment
  side by replaying the action sequence and comparing frame hashes one by one;
  the model side is not replayable in principle, so its inputs, outputs and
  usage are recorded verbatim as the substitute.
* **No bypass** — an arm never holds the environment credential, so the ledger
  cannot have a hole in it that an arm could have written around.

This document is normative and was written before the code. `proxy/ledger.py`
is its executable form; `proxy/tools/validate_ledger.py` will check any stream
against it. **Three arms and the Phase 2 metric battery share this format.**
Fields are added only by appending; existing field meanings never change under
the same `v`.

---

## 1. The file

One JSON object per line, UTF-8, LF endings, `\n`-terminated, no trailing
whitespace. Keys are sorted, `ensure_ascii=true`, no spaces after separators —
so a line is byte-determined by its content and two writers cannot produce
different bytes for the same record.

**Append-only.** `proxy/ledger.py` exposes no update, rewrite or delete path.
Corrections are new records (see §6, `incident`), never edits.

A ledger holds records for many runs. `run_id` partitions it; `seq` orders it.

## 2. Common envelope

Every record, whatever its type, carries:

| field | type | meaning |
|---|---|---|
| `v` | string | format version, `"1.0"` |
| `event` | string | `"env_step"`, `"model_call"`, or a §6 auxiliary type |
| `seq` | int | monotonic within the file, assigned by the writer under a lock. Gaps are impossible; duplicates are a corrupt file. |
| `ts` | string | ISO-8601 UTC, millisecond precision, `Z` suffix |
| `run_id` | string | one run = one arm playing one game once |
| `arm` | string | which arm produced it (`bare_cc`, `schema_repro`, `theoria`, `probe`, `replay`) |

`ts` is wall-clock and therefore **not** part of any hash or comparison. Replay
compares `frame_hash`, never timestamps.

## 3. `env_step`

One arm↔environment interaction: exactly one HTTP request through the
environment proxy that carries a game command, and its response.

```json
{"v":"1.0","event":"env_step","seq":41,"ts":"2026-07-28T09:14:02.371Z",
 "run_id":"r-8f2c...","arm":"bare_cc","game_id":"ar25-0c556536",
 "card_id":"9d1e...","guid":"7b3a...","step_idx":7,
 "action":{"name":"ACTION2","id":2,"data":null},
 "frames":[[[0,1],[1,0]]],"frame_hash":"sha256:1f0c...","n_frames":1,
 "state":"NOT_FINISHED","score":3,"levels_completed":3,
 "level":3,"level_boundary":false,
 "variant":null,"guard":{"decision":"allow"},
 "http":{"method":"POST","path":"/api/cmd/ACTION2","status":200,
         "elapsed_ms":214,"request_sha256":"sha256:aa1b...","attempts":1}}
```

| field | type | meaning |
|---|---|---|
| `game_id` | string | full id including the version suffix. **The suffix is the environment version fingerprint** and is copied into `run.json`; it is never truncated in the ledger. |
| `card_id` | string \| null | the scorecard this step counts against. One game = one scorecard. Probe and prefix-replay steps use a separate scorecard marked `probe`, so they do not pollute the main game's action and score counts. |
| `guid` | string \| null | session id returned by RESET |
| `step_idx` | int | monotonic within `run_id`. RESET is `0`. Increments once per command, including commands the guard or a variant refused. |
| `action` | object | `{"name","id","data"}`. `name` is `"RESET"` or `"ACTIONn"`; `id` is `n` or `null` for RESET; `data` is the click payload or `null`. **This is the action as the arm sent it**, before any variant rewriting (see `variant.applied`). |
| `frames` | list | the response's frame field, **raw and whole**, as a list of frames. One command may return several — the precheck observed up to 7 — so this is always a list, length 1 in the common case. `null` when no frame came back (refusal, error). |
| `n_frames` | int | `len(frames)`, or `0`. Recorded explicitly because `>1` is what the cascade-semantics ruling turns on. |
| `frame_hash` | string | `"sha256:"` + sha256 over the canonical JSON of `frames`. The unit of replay comparison. `null` when `frames` is `null`. |
| `state` | string \| null | `NOT_FINISHED` / `WIN` / `GAME_OVER`, as returned — or as a variant rewrote it, in which case `variant.applied` says so. |
| `score` | int \| null | as returned |
| `levels_completed` | int \| null | as returned |
| `level` | int \| null | the level this step happened on. Not an API field; derived by the writer from `score`/`levels_completed` jumps. |
| `level_boundary` | bool | true on the step where the derivation says a level ended. Level boundaries live here, in the ledger, and nowhere else. |
| `variant` | object \| null | `null` for an unmodified environment. Otherwise `{"variant_id","spec_sha256","applied"}` where `applied` is `null` if the variant did not fire on this step, else an object naming the operator and what it did. |
| `guard` | object | `{"decision":"allow"}`, or `{"decision":"deny","reason":...,"rule":...}`. A denial is a full record with `frames: null` — a refusal is evidence, not an absence. |
| `http` | object | `method`, `path`, `status`, `elapsed_ms`, `request_sha256` (over the canonical request body, whose interesting parts are already in `action`), `attempts` (retries collapse into one record; each attempt's status is in `attempt_log` when `attempts > 1`). |

Requests through the environment proxy that carry no game command — scorecard
open/close, `GET /api/games` — are **not** `env_step` records. They are §6
`env_meta` records. `env_step` stays exactly one shape so the battery can read
it without branching.

### Score reconciliation obligation

The score derived from `env_step` records must equal the score the API's
scorecard reports. `proxy/reconcile.py` computes both and any inequality is an
incident, written as a §6 `incident` record. This is a hard obligation, not a
diagnostic.

## 4. `model_call`

One arm↔model interaction through the model proxy.

```json
{"v":"1.0","event":"model_call","seq":42,"ts":"2026-07-28T09:14:05.902Z",
 "run_id":"r-8f2c...","arm":"bare_cc","call_idx":7,
 "provider":"anthropic","model":"claude-sonnet-5",
 "request":{"...":"the request body, whole"},
 "response":{"...":"the response body, whole"},
 "usage":{"input_tokens":8123,"output_tokens":214,
          "cache_read_input_tokens":40960},
 "pricing_ref":{"table":"pricing_v1","sha256":"sha256:3c9d..."},
 "step_idx":7,
 "http":{"method":"POST","path":"/v1/messages","status":200,
         "elapsed_ms":3110,"stream":false,"attempts":1}}
```

| field | type | meaning |
|---|---|---|
| `provider` | string | `anthropic`, … — taken from the proxy's upstream configuration, not from anything the arm said |
| `model` | string | as requested |
| `request` | object | the request body **whole**. Model calls are not replayable, so the full text is the substitute for replay. |
| `response` | object | the response body whole. For a streamed response, the reassembled message plus `stream_events` holding the raw event sequence. |
| `usage` | object | **the provider's usage block, copied through verbatim.** Not reshaped, not renamed, not summed. Whatever keys the provider emits are the keys here. |
| `pricing_ref` | object | which price table was in force, by name and hash. **No cost field appears in the ledger.** Cost is a conversion applied later by `proxy/cost.py` from `proxy/pricing/<table>.json`; recording dollars would freeze one price list into an append-only file forever. |
| `call_idx` | int | monotonic within `run_id` |
| `step_idx` | int \| null | the `env_step` this call was deciding, when the arm declares it. Lets the battery put cost on a per-turn axis. |

### Credential handling

`request.headers` is **not** stored. Both proxies strip `Authorization`,
`X-API-Key` and `X-Api-Key` before writing, and `proxy/redact.py` additionally
scans every outgoing record for any known credential value and replaces it with
`"<redacted>"`. A ledger that has been through the writer cannot contain a key,
even if an arm put one in a request body by mistake.

## 5. Derived quantities are not recorded

Recorded: what crossed the wire. Derived: everything computable from it. The
rule keeps the append-only file honest when the derivation changes.

| derived | from | by |
|---|---|---|
| cost in USD | `usage` + `pricing_ref` | `proxy/cost.py` |
| score | `env_step.score` sequence | `proxy/reconcile.py` |
| any Phase 2 metric | the whole stream | the battery |

The two exceptions are `level` / `level_boundary`, which are derived but *are*
recorded — because the derivation needs the live step sequence and because
Phase 1 assigns level boundaries to the ledger by name. The rule they follow:
derived-and-recorded fields must be recomputable from the same file, and
`reconcile.py` checks that they are.

## 6. Auxiliary records

Same envelope, different `event`. They exist so that `env_step` and
`model_call` keep exactly two shapes.

| `event` | when | payload |
|---|---|---|
| `run_start` | a run opens | `arm`, `game_id`, `card_id`, `variant`, `env_base`, `model_base`, `budget`, the proxy build hash |
| `run_end` | a run closes | `outcome`, `steps`, `model_calls`, scorecard as returned at close |
| `env_meta` | non-command environment traffic | `http`, request and response bodies |
| `guard_block` | a request refused by the sealed-pile guard | `game_id`, `rule`, `path`, and the requesting peer. Also emitted for a refused non-command request, which no `env_step` would cover. |
| `incident` | a Phase 1 obligation failed | `kind` (`score_mismatch`, `replay_mismatch`, `nondeterminism`, `credential_in_body`, `bypass_attempt`), `detail` |

## 7. Compatibility

`baseline-arms/harness/ledger.py` writes an earlier two-shape ledger with
fields `{game_id, run_id, arm, model, action, frame, step_idx, timestamp}`.
v1.0 is a superset in meaning but not in spelling: `frame` → `frames` (list),
`timestamp` → `ts`. `proxy/tools/upgrade_ledger.py` lifts the old shape into
v1.0 so the two streams can be concatenated; it fills `frames` from `frame`,
sets `v`, and marks lifted records with `"lifted_from":"baseline-arms/v0"`.
Lifted records carry no `frame_hash` unless the old `frame` was whole.

## 8. Versioning

`v` is bumped when a field's meaning changes or a required field is added.
Readers must reject a record whose `v` they do not know rather than guess.
