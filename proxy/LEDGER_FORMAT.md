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
| `prev` | string or null | **optional.** sha256 of the previous line's bytes as written, including that line's own `prev`. `null` on the first record of a file. |

`ts` is wall-clock and therefore **not** part of any hash or comparison. Replay
compares `frame_hash`, never timestamps.

### The `prev` chain

`prev` links each record to the bytes of the one before it, so editing a field,
deleting a line, inserting one, or swapping two records breaks every link after
the change. Verify with:

```bash
python -m proxy.tools.verify_chain proxy/var/ledger.jsonl
python -m proxy.tools.verify_chain <path> --expect-head sha256:9a4e…
```

Four properties of the design, each deliberate:

* **The hash is over the bytes on disk, never over a re-serialised record.** A
  verifier that re-canonicalises is really checking that today's `canonical()`
  agrees with the one that wrote the file — so the day that function's
  behaviour changes, every ledger ever written goes red at once and the alarm
  stops meaning anything. Hashing the bytes asks the only question worth
  asking: are these the bytes that were written?
* **`prev` is optional, so `v` stays `1.0`.** §8 bumps the version when a
  field's meaning changes or a *required* field is added; an optional field is
  neither. A stream without `prev` is **unchained**, not invalid — and the
  verifier reports that as its own verdict rather than as a pass.
* **The writer owns it** (§2, `canon.ENVELOPE`): a caller that supplies `prev`
  is refused. A chain a caller could set is a chain a caller could forge.
* **It is assigned under the same lock as `seq`**, so the two can never
  disagree about the order records were written in.

**What this does and does not prove.** It makes tampering *evident* once a head
has been published; it does not authenticate the recording.

Three holes the chain walk alone cannot close, all of them closed only by a
published head:

* **A wholesale rewrite verifies.** Recompute every link and the file is
  internally perfect.
* **Truncating the tail verifies.** Nothing chains to the last line, so deleting
  records from the *end* — the most attractive tamper, since it is the end of a
  run that went badly — breaks no link at all. Deleting from the middle or the
  front does break links.
* **Duplicate `seq` from two processes — closed 2026-07-29 (A10).** This used
  to read: *"`Ledger`'s lock is in-process, so two processes appending to one
  file fork the chain."* That was true and it happened: a 253-line ledger under
  `theoria-arm/runs/pytest-test_the_shell_turns_end_to_en0/` still carries the
  break, seq 137–143 each written twice, because two test processes overlapped.
  The seed was taken once in `Ledger.__init__` and the lock did not span
  seed→append, so a writer that opened mid-run continued from an already-stale
  `seq`.

  `Ledger` now takes an **OS-level lock on a sidecar file**
  (`<ledger>.jsonl.lock`, `fcntl.flock` / `msvcrt.locking`, the same discipline
  `spend_gate._PoolLock` has carried since INC-BA-003), and **re-derives
  `seq`/`prev` from the bytes on disk inside that lock** immediately before
  writing. It fails closed: no lock primitive, or a timeout, raises
  `LedgerLockUnavailable` and writes nothing.

  Two limits remain, and neither is a forgery either. A writer that does not go
  through `Ledger` can still fork the file — the lock is cooperative, and
  `baseline-arms/harness/ledger.py` writes its own v0 stream knowing nothing
  about the sidecar. And a *hung* (not dead) holder makes other writers time out
  and refuse; a dead one is reclaimed by the kernel on exit.

  `proxy/tests/test_ledger_concurrency.py` holds this down with real spawned
  processes. Its failing path is exercised, not assumed: with the lock and the
  re-seed removed, 7 of its 10 tests go red, reproducing the poisoned file's
  signature — every `seq` from the overlap onward written twice, no gaps and no
  records lost.

**Publishing the head is therefore not optional, and writing it is not
publishing it.** `runner.play()` returns the record carrying `ledger_head`
`{last_seq, sha256, lines, verdict}`, but it *writes* it under `proxy/var/`,
which is gitignored — a witness the forger can rewrite as easily as the ledger
is no witness. Publication means putting it somewhere tracked:

```bash
python -m proxy.tools.verify_chain <ledger> --emit-head runs/<id>/ledger_head.json
git add runs/<id>/ledger_head.json      # the publication is the commit
```

or an arm lifting `ledger_head` into its own tracked `runs/<slug>/MANIFEST.json`.
`--emit-head` refuses to write a head for any stream that does not verify: a
head witnessing an unverified file is worse than none, because it looks like one.

**Checking against a published head:**

```bash
python -m proxy.tools.verify_chain <ledger> --expect-head-file runs/<id>/ledger_head.json
```

This verifies the file's **prefix up to the published `last_seq`**, not the whole
file. That matters because the ledger is one shared append-only file: later runs
append to it, so a whole-file comparison would report FAIL on every honest
ledger as soon as the next run started, and an alarm that fires on honest files
is an alarm nobody reads. Prefix checking is also what catches tail truncation —
a file that ends before the published `last_seq` is missing records that were
witnessed.

**Bytes, modulo the line terminator.** The hash covers each line's bytes with
any trailing `\r\n` stripped, so converting the file's line endings does not
break the chain. Everything inside the line is covered exactly; a canonical
record ends in `}`, so no record content can hide in the terminator.

See `DECISIONS.md` D-024 / D-029 and `REDTEAM.md` RED-40.

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
| `variant` | object \| null | `null` for an unmodified environment. Otherwise `{"variant_id","spec_sha256","applied"}` where `applied` is `null` if the variant did not fire on this step, else an object naming the operator and what it did. A `win_tighten` record also carries `reason` (`score_absent` / `score_below`), `degenerate`, `occurrence`, and `note` on the first absent-driven rewrite of a session: an absent score and a shortfall are different events and the record does not let them look the same (D-032). |
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

### Reconciliation obligation

**Amended 2026-07-29 (A10).** This section previously read: "the score derived
from `env_step` records must equal the score the API's scorecard reports, and
inequality is an incident." Against the live API that obligation **cannot be
discharged in the direction it was written**, because the ledger side of the
comparison has no numbers in it — see the note above §3's table, and
INC-TA-002. A rule nobody can satisfy leaves the gate permanently red or, more
often, quietly skipped, and this document is normative: leaving it stating an
impossible obligation is itself a defect. The rule below is what
`proxy/reconcile.py` performs, and every leg of it has a negative sample in
`proxy/tests/test_reconcile.py` proving it can go red.

The obligation is keyed to **three quantities, each compared per record and per
run, and each required to agree**:

| leg | status of the quantity | compared |
|---|---|---|
| **actions** | **recorded** — one `env_step` per ARC command, `step_idx` monotonic from the RESET at `0` | the sequence against itself (duplicates, gaps, non-integers), *and* the scorecard's `total_actions` against the count of successful non-RESET commands |
| **cost** | **derived, deliberately not recorded** (§5) — `usage` verbatim plus a `pricing_ref` naming the table and its hash | that the bill is still *derivable*: the named table exists and still hashes to the value the record pinned, and `run_end.model_calls` equals the `model_call` records on disk. No dollar figure is compared, because none is in the file |
| **score, per run** | **recorded on the scorecard** — `POST /api/scorecard/close` returns `score`, and 32 real closed cards carry one | the **frozen scorer**'s battery (`proxy/scoring/`, see `proxy/SCORING.md`), run rather than reimplemented: two implementations of one obligation drift, and the drift stays invisible until the day they disagree about a real run |

Any disagreement is an incident, written as a §6 `incident` record of kind
`score_mismatch`. That kind's name is now narrower than what it records — it
covers a failed reconciliation on any leg, and the record's `failing_legs` field
says which. Renaming it would add a kind to `ledger.INCIDENT_KINDS`.

**Two quantities are named here and deliberately not compared.** Naming them is
the requirement; faking a comparison over them would be the defect.

* **Per-step `score` is arm-self-reported and NOT cross-verifiable.** A live
  command response carries no `score` field at all — its key set is
  `action_input, available_actions, frame, full_reset, game_id, guid,
  levels_completed, state, win_levels` (INC-TA-002, confirmed against 196
  successful command responses in `arc-recon/data/recon_ledger.jsonl`, none of
  which carries one). Whatever wrote the record is its only witness. It is
  reported as `gaps.score_per_step` with verdict `NOT_CROSS_VERIFIABLE`, under a
  field name that says so, and **it does not vote** on the verdict.
  **This label is scoped to the per-step quantity only.** The per-run score on
  the scorecard is a different quantity, it *is* cross-verifiable, and the leg
  above keeps checking it — widening the label to "score" would discard a check
  that works.
* **Turn count is not reconcilable, because no turn index exists.**
  `battery/INPUT_FORMAT.md` gap 5: "No turn index distinct from `step_idx`.
  Still open upstream." `theoria-arm` holds its turn axis outside the ledger in
  `turns.json` and rejoins it structurally with a stated `join_confidence`
  because the join is not exact; `ablation-arm`'s count is in `run_report.json`;
  `baseline-arms` has none at any level. The reconciler reports this as
  `gaps.turns` with verdict `ABSENT`, and **it does not vote** — a gap in the
  format is not a defect in the run being reconciled, and making it vote would
  rebuild the permanently-red signal this amendment removes. **What would close
  it:** an *optional* `turn_idx` on `env_step` and `model_call`. §8 bumps `v`
  for a changed meaning or a new *required* field, and an optional one is
  neither — `prev` (§2) is the precedent — so this can be added at `v` `1.0`.
  Until an arm writes one, the leg stays `ABSENT`.

**Kept in sync by a gate, not by care** (added 2026-07-31, S31).
`proxy/tests/test_ledger_format_sync.py` reads the voting legs out of the table
above and the gap names out of a real `reconcile_run` report, and goes red when
the two disagree — in particular when a quantity the reconciler reports as a
non-voting gap gets written up here as a leg of the obligation. That is not a
hypothetical drift: a work item asked for exactly it (a `turns` leg) six days
after the finding that requested it had already withdrawn it, and a document
listing `turns` as the third leg would have made a check with no failing path
look like the specification. It is not a digest check — this file is still being
edited, and a digest would go red on somebody else's correct prose while staying
green on a leg quietly renamed inside the table.

**Four verdicts, and the fourth is the reason for the other three.**
`PASS` (every voting leg agreed) / `FAIL` (a leg disagreed) / `INCOMPLETE`
(nothing disagreed, but a voting leg had no evidence to work with) / `EMPTY`
(no `env_step` records for the run). An obligation that **cannot be
discharged** — no scorecard was captured, so there is nothing to compare
against — is `UNDETERMINED` in the scorer and never `PASS` here, and writes an
`incident` of kind `score_unreconciled`. `baseline-arms` lost 22 of 23
scorecards to a transient close-404 and the loss was silent; silence is the
failure mode this distinction exists to break.

The scorer's fingerprint (`{id, version, sha256, frozen_at}`) is recorded in
`run_start` and in `run.json`, so every number can be traced to the rule that
produced it. The score itself is **not** written into the ledger: it is a
derived quantity and follows §5.

**This amendment changes no field and no record shape**, so `v` stays `1.0` per
§8: it changes which comparison the reconciler is obliged to perform, not what
a record means or which fields it must carry.

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

**`transport` and `proxied` are two questions, and P-12 stopped the answers
being the same answer.** Every ledger written before 2026-08-01 has
`transport: "claude-code-cli"` exactly when it has `proxied: false`, because
the CLI route was the unproxied route: `harness/modelcall.py` writes the record
itself and `http.forwarded` is `false`. A reader could get away with treating
one as a synonym for the other, and at least one would have.

It is no longer true. `proxy/cli_transport.py` puts the same subprocess
*behind* the model proxy — the CLI honours `ANTHROPIC_BASE_URL`, and pointed at
a credential-free `CLAUDE_CONFIG_DIR` it presents a locally-minted token the
proxy strips and replaces (measured in
`runs/20260801T0000Z-P12-model-proxy-cli/FINDING.md`; the whole path is tested
against a loopback provider, and only a funded provider key is still missing).
A record from that route is written by `model_proxy` with `http.forwarded:
true`, so it is a **proxy-observed record of a CLI transport**:

| | `transport` | `proxied` | who wrote the record |
|---|---|---|---|
| the arm's own subprocess | `claude-code-cli` | `false` | `harness/modelcall.py` |
| the same subprocess, behind the proxy | `claude-code-cli-via-model-proxy` | `true` | `proxy/model_proxy.py` |
| a direct `/v1/messages` client | whatever it says | `true` | `proxy/model_proxy.py` |

So a cost comparison must keep reading `transport` — the caching argument above
is about the CLI and survives the route change intact — and a *completeness*
claim must keep reading `proxied`. Collapsing them was always a coincidence of
this repository's history; from here it is a bug.

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
| score | the scorecard, per run — **not** the `env_step.score` sequence, which is null on live traffic (§3, INC-TA-002) | `proxy/scoring/`, reconciled by `proxy/reconcile.py` |
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
