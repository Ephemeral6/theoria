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
is its executable form; `proxy/canon.py` is the field registry both directions
consult, and `proxy/tools/validate_ledger.py` checks any stream against it.
**Three arms and the Phase 2 metric battery share this format.**
Fields are added only by appending; existing field meanings never change under
the same `v`.

**F-16 ruled this document the canon** and `baseline-arms/harness/ledger.py`'s
earlier spelling the dialect to be migrated. Since P-9 that ruling is enforced
rather than asserted: a spelling this document *forbids* cannot be written
(`proxy/canon.py` refuses it before serialisation) and cannot be accepted
(`validate_ledger.py` refuses it on read). A field it merely does not mention is
a different case and is kept, with a warning — §6 says why, and the reason has a
price tag on it. The migrator is `proxy/tools/upgrade_ledger.py` and its
interface is `proxy/CANON_MIGRATION.md`; the procedure for changing this
document in a way that narrows it is `proxy/CONTRACT_CHANGES.md`.

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
| `response` | object \| null | **the rest of the response body, with `frame` removed.** Added by P-9. The live API returns `win_levels`, `available_actions`, `full_reset` and `action_input` on every command, and none of them had a home, so they were being dropped — which quietly falsified the first closure property, *complete record*. `win_levels` matters most: it is the only place the environment says how many levels a game has, and without it no score fraction is computable from the ledger alone. The frames are not duplicated here; they are already stored whole and hashed. |
| `http` | object | `method`, `path`, `status`, `elapsed_ms`, `request_sha256` (over the canonical request body, whose interesting parts are already in `action`), `attempts` (retries collapse into one record; each attempt's status is in `attempt_log` when `attempts > 1`). |

Requests through the environment proxy that carry no game command — scorecard
open/close, `GET /api/games` — are **not** `env_step` records. They are §6
`env_meta` records. `env_step` stays exactly one shape so the battery can read
it without branching.

Note that `score` is a field the **live API does not return** on a command
response — it answers `levels_completed` and `win_levels`. The field stays in
this table because a record shape does not change under the same `v`, and
because the mock and any future environment may supply it; on live traffic it is
`null` and nothing should be built on it.

### Score reconciliation obligation

The score derived from `env_step` records must equal the score the API's
scorecard reports. The **frozen scorer** (`proxy/scoring/`, see
`proxy/SCORING.md`) computes both and any inequality is an incident, written as
a §6 `incident` record of kind `score_mismatch`. `proxy/reconcile.py` runs the
same battery rather than a second implementation of it: two implementations of
one obligation drift, and the drift stays invisible until the day they disagree
about a real run.

An obligation that **cannot be discharged** — no scorecard was captured, so
there is nothing to compare against — is `UNDETERMINED`, not `PASS`, and writes
an `incident` of kind `score_unreconciled`. `baseline-arms` lost 22 of 23
scorecards to a transient close-404 and the loss was silent; silence is the
failure mode this distinction exists to break.

The scorer's fingerprint (`{id, version, sha256, frozen_at}`) is recorded in
`run_start` and in `run.json`, so every number can be traced to the rule that
produced it. The score itself is **not** written into the ledger: it is a
derived quantity and follows §5.

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
| `game_id` | string \| null | the game this run is playing. Optional in the format — adding a *required* field is what §8 bumps `v` for — but **this writer always supplies it**, because one run is one arm playing one game once, so the game is a property of the run. The Phase 2 battery asked for it: without it a run that thought and never acted lands as `unknown`, and a sealed-pile guardrail can only filter model traffic by rejoining it to `env_step` records. |
| `beat` | string \| null | which loop beat spent the call (`theorize`, `probe_design`, …) |
| `label` | string \| null | a short free tag distinguishing calls within one beat |
| `transport` | string \| null | how the call was made: `https-proxy`, `claude-code-cli`, … |
| `proxied` | bool \| null | whether this record was observed at `model_proxy` or written by the arm's own writer |
| `proxy_gap` | string \| null | when `proxied` is false, why — one sentence, naming the obstacle |

### The five that describe how the call was made

These arrived in P-8, were in use before this section was written, and are
listed here because they carry things nothing else on the record carries. They
are optional; no `v` bump (§8).

`beat` is the one that changes what the ledger can prove. Theoria.md constraint
8 says the large model appears at theorize and at probe design and **nowhere
else** — execute, certify, plan and the engines are zero-call by construction.
Without `beat` that is a claim in a design document. With it, grouping this
file's `model_call` records by `beat` either returns those two values or returns
the counter-example. A constraint that is checkable from the artefact is a
different kind of object from one that is asserted about it, and this field is
the whole difference.

**Stated at its real size:** that query is over `model_call.beat`. Ledgers
written while §4 was closed have `beat` nested inside `request` instead — the
workaround the closure forced on the one arm that writes it — so a checker over
those must read both depths, which is precisely the reader branch the closure
was invented to avoid. The top-level spelling is canonical again as of C-001
(`CONTRACT_CHANGES.md`); until the arm un-nests, the two depths coexist and any
constraint-8 check has to say which one it read.

`proxied` and `proxy_gap` state the **complete record** property at its real
size rather than one size up. `false` means the bits were written by the arm
rather than observed at the proxy, so completeness rests on the arm's own
writer; `proxy_gap` says what stopped the proxy from seeing it. A reader that
cannot tell the two cases apart reads the weaker one as the stronger one, which
is the failure mode this whole document exists to prevent.

`transport` is load-bearing for cost comparison across arms. An arm that reaches
the model through a `claude-code-cli` subprocess gets no prompt caching, so its
cache-read count is a **structural zero** and not a small number; comparing it
with a proxied arm's ~10⁸ compares a transport property with a framework
property (INC-TA-005). The field is what lets a battery notice before it does.

**These five fields spent $2.695 getting here.** §4 was closed after P-8 landed,
on a commit the arm that writes them never touched, and the closure refused the
first live call's record after the provider had already been paid. That is
INC-TA-006; it is why the two shapes are no longer closed (§6) and why
`proxy/CONTRACT_CHANGES.md` exists.

### Credential handling

`request.headers` is **not** stored. Both proxies strip `Authorization`,
`X-API-Key` and `X-Api-Key` before writing, and `proxy/redact.py` scans every
outgoing record — values **and** dictionary keys — for any credential the
process has registered, including its base64 and percent-encoded spellings and
the case where it has been split across two adjacent fields, and replaces it
with `"<redacted>"`.

This paragraph used to end "a ledger that has been through the writer cannot
contain a key". That was an over-claim and the red team collected on it
(RED-15): only *registered* values were scrubbed, so a credential the proxies
had never seen — another service's key, pasted into a request by an arm — went
to disk verbatim. The claim is now stated at the size it actually holds:

* **A credential the proxies injected cannot reach the ledger.** That one is
  known by construction, and its encodings are known with it.
* **A key-shaped string in environment traffic is redacted on sight**, by
  pattern rather than by identity, with the structural fields that are
  key-shaped by design (`card_id`, `guid`, `frame_hash`, …) exempted. It also
  raises a `credential_in_body` incident.
* **`model_call.request` and `model_call.response` are exempt from the
  pattern pass.** §4 requires them verbatim, and a long run of alphanumerics
  there is ordinary model output. An arm that puts a key in a prompt still
  raises the incident; the bytes still go to disk. **The exemption stops
  there**: a field on a `model_call` that this section does not list is *not*
  required verbatim by anything, so it goes through the pattern pass like
  environment traffic. Before §6 became additive-safe such a field could not
  reach disk at all, and letting it inherit the verbatim exemption would have
  been a new route for a credential the vault has never been told about.
* **A secret that does not look like one cannot be recognised.** A writer
  cannot redact what it has never been told and cannot see. That is a
  limitation, not a bug, and it is written here rather than left to be
  discovered.

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
| `incident` | a Phase 1 obligation failed | `kind` (`score_mismatch`, `score_unreconciled`, `replay_mismatch`, `nondeterminism`, `credential_in_body`, `bypass_attempt`, `sealed_pile_request`, `scorer_drift`), `detail` |

`run_start` additionally carries `scorer` (the frozen scorer's fingerprint) and,
on a migrated stream, a `lifted` block — see §7.

**Auxiliary payloads are open, and the two shapes are additive-safe.**
`canon.py` enforces each auxiliary's required keys and lets anything else
through, because a `run_start` carries whatever a run needs to describe itself.
On `env_step` and `model_call` it enforces the required fields, the banned
spellings and the types — and a field §3/§4 does not list is **warned about and
written**, not refused.

This section used to say the two shapes were closed, and the reason it gave was
that "the battery reads two shapes without branching, and an extra field is a
branch someone eventually has to write". That reasoning is about readers, and it
was applied to the writer, where the price is paid in a different currency. The
writer runs *after* the request: by the time it sees a `model_call`, the
provider has been paid. Refusing the record cannot un-spend the money — it only
destroys the evidence that it was spent. INC-TA-006 is that sentence with a
number attached: $2.695, zero `model_call` records, one discarded reply, and a
run that would have kept paying until its ceiling stopped it.

**Refusing to record is strictly worse than recording something a reader may
have to skip.** So what remains a refusal is the set of things that are *wrong*
rather than merely unknown:

| still refused | why it is not just "unknown" |
|---|---|
| a v0 spelling (`frame`, `timestamp`, …) | two spellings of one thing is the drift F-16 ruled on; the refusal names the replacement and the migrator |
| one of the five banned dollar spellings, **at any depth** | §5 — a price in an append-only file is wrong the day the price changes and cannot be corrected. Scanned inside `usage` and inside every unlisted field, because a field the format has never heard of may not be a back door for one it bans |
| an envelope field set by a caller | §2 — `seq` and `ts` are the writer's, and a caller setting them is forging ordering |
| a missing **required** field | the record is not lossy, it is uninterpretable |
| a type that would produce a plausible wrong number | `True` sums as 1; a bare frame where a list belongs is a lost observation; `bool("false")` is `True`, so a string `proxied` would read as proxy-observed |

**What §5's ban is, exactly.** It is a list of *names* — `cost`, `cost_usd`,
`total_cost_usd`, `price_usd`, `score_pct` — not a semantic price detector. A
field called `usd_spent` is not on the list and is written, and that was already
true of auxiliary payloads, which have always been open. What changed is that
the two shapes now behave like the auxiliaries. If you want a name refused, add
it to `canon.BANNED_SPELLINGS`; §2 of `CONTRACT_CHANGES.md` classes that as a
tightening, so it gets announced.

**`event` and `arm` are still hard refusals** (`ledger.EVENTS`, `ledger.ARMS`),
and the reason that is not the after-the-money refusal this section argues
against: both are fixed when the run's ledger is constructed, so a wrong one
fails on the run's very first record — before any request is sent and any dollar
is spent. A refusal in the first second of a run is a typo caught; a refusal on
record 40 is evidence destroyed.

Readers are not thereby asked to branch. §8's guarantee is that a *defined*
field never changes meaning under one `v`; a reader that handles what it knows
and ignores the rest was always correct and still is. What it now also gets is a
stream that exists. `validate_ledger.py` reports an unlisted field as a
**notice** and leaves the verdict alone, for the same reason in the other
direction — the frozen scorer calls it from S-12, and a scorer that fails a run
over a field it could ignore is INC-TA-006 read-side.

Adding a field to §3 or §4 is free and needs no announcement. **Taking one away
is a breaking change** for every track that imports `proxy/` as a library, and
`proxy/CONTRACT_CHANGES.md` is the procedure for it.

## 7. Compatibility

`baseline-arms/harness/ledger.py` writes an earlier two-shape ledger with
fields `{game_id, run_id, arm, model, action, frame, step_idx, timestamp}`.
v1.0 is a superset in meaning but not in spelling: `frame` → `frames` (list),
`timestamp` → `ts`. `proxy/tools/upgrade_ledger.py` lifts the old shape into
v1.0 so the two streams can be concatenated. **It exists now**, and the full
field-by-field mapping — including what is dropped, what is a hole, and how to
tell a lifted stream from a native one — is `proxy/CANON_MIGRATION.md`. The
original file is never modified.

One thing changed from what this section originally specified. It said to mark
each lifted record `"lifted_from": "baseline-arms/v0"`; that was written before
§3 and §4 became closed field sets, and a closed shape cannot carry an extra
marker. Provenance therefore lives on the synthesised `run_start`, in a `lifted`
block that says strictly more: the source path, its sha256, the migrator's
version, the record counts, the fields dropped and the holes v0 left. Every
lifted record belongs to a run, so nothing is unattributed.

That paragraph's premise expired with §6's closure: a shape *can* carry an extra
marker now. The decision stands anyway, on the reason that outlived the premise
— the `lifted` block says strictly more than a per-record boolean would, and
provenance belongs where it can be stated once and completely. Noted here rather
than quietly rewritten, because "the constraint that forced this is gone" is
exactly the thing a later reader needs to know when they weigh the same choice.

Lifted records **do** carry a `frame_hash`: v0's `frame` was already the whole
frame list, so the hash is computable and is computed.

## 8. Versioning

`v` is bumped when a field's meaning changes or a required field is added.
Readers must reject a record whose `v` they do not know rather than guess.

`v` is **not** bumped when an optional field is added, because nothing breaks:
under §6 an unlisted field was already accepted with a notice, so listing it
only stops the notice. That asymmetry is the whole rule, and it generalises past
this file — **widening what is accepted is free, narrowing it is a breaking
change**, whether the narrowing is a `v` bump, a new required field, a field
removed from §3/§4, a new banned spelling, or a closure like the one that cost
$2.695. A narrowing arrives at the other tracks the moment it is on the mainline,
because they import `proxy/` as a library rather than vendoring it, so it can
land on a commit they never touched.

The procedure for a narrowing — announce, wait a cycle, ship a compatibility
window — is `proxy/CONTRACT_CHANGES.md`. Its mechanical half is
`proxy/canon_contract.json`, which pins `canon.describe()`, and
`python -m proxy.tools.contract`, which diffs the live registry against the pin
and labels each difference `additive` or `tightening`. Importing tracks should
record `python -m proxy.tools.contract --fingerprint` in their run manifests and
**diff it between runs**: a pin that is written and never compared documents an
incident afterwards instead of preventing one.
