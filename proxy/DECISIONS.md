# `/proxy/` — design calls and their reasons

## D-001 · The format document was written before any code

`LEDGER_FORMAT.md` is normative and dated ahead of `ledger.py`. The ticket
asked for it in that order and the order matters: the ledger is the shared
surface for three arms and the Phase 2 metric battery, and a format that
emerges from one implementation encodes that implementation's accidents. Where
the two ever disagree, the document is right and the code is a bug.

## D-002 · Two event shapes, and auxiliaries kept out of them

`env_step` and `model_call` stay exactly two shapes. Everything else the
proxies observe — scorecard traffic, the game list, guard refusals, incidents —
goes to `run_start` / `run_end` / `env_meta` / `guard_block` / `incident` under
the same envelope. The battery reads two shapes without branching, which is the
whole point of a shared format; the alternative was optional fields on
`env_step` that mean "this is not really a step".

`baseline-arms/harness/ledger.py` reached the same conclusion independently
(its D-003) and sent diagnostics to a separate file. v1.0 keeps them in the
same file but under distinct `event` values, so a single stream stays ordered
by `seq` — ordering that a second file would lose.

## D-003 · A refusal is a record, not an absence

A command the guard denies, or a variant declines to forward, is written as a
full `env_step` with `frames: null` and `guard.decision: "deny"`. Recording
only what succeeded would make "the arm never tried" and "the arm tried and was
stopped" indistinguishable in the ledger — and the second is exactly the
evidence a sealing claim rests on.

## D-004 · No dollar figure is ever written to the ledger

`model_call` carries the provider's `usage` verbatim plus a `pricing_ref`
naming a hashed price table. Cost is computed on demand by `cost.py`. An
append-only file that recorded dollars would be wrong the day a price changed
and could not be corrected; with the conversion outside, a price change
re-prices history instead of contradicting it. `RunLedger.model_call` raises if
a caller passes `cost` or `cost_usd`, so this cannot be eroded by convenience.

## D-005 · Usage is copied through, never reshaped

Whatever keys the provider emits are the keys in the ledger. No renaming, no
summing, no normalising across providers. A normalised usage block is a
derived quantity wearing a recorded quantity's clothes, and the derivation
would be invisible at read time. The one exception is documented and narrow:
for a streamed response the proxy merges the `message_start` and
`message_delta` usage objects, which is a merge of the provider's own keys.

## D-006 · The guard is at the proxy, and it fails closed

The sealed-pile rule was previously enforced by every caller checking. Here an
arm's only route to the environment refuses before the upstream socket opens,
and the arm has no credential with which to go elsewhere — so the cut is
enforced by construction.

Three sub-calls:

* **The data source is `arc-recon/data/piles.json` itself**, not a copy. A copy
  is a second thing to keep in sync, and the failure mode of that drift is
  silently playing a sealed game.
* **Integrity is verified on load** against the digest the cut recorded. A
  silently edited cut raises instead of quietly widening what is reachable.
* **An id in neither pile is denied by default.** The cut covers the 25 public
  games; anything outside it is not something Phase 1 authorised. Widening
  should be a deliberate, recorded act rather than a shrug.

The guard reads the *whole* request for game ids — path, query and every string
in the body — not just `body["game_id"]`. A guard that only checked the field
it expected would be a guard by convention again.

## D-007 · The variant library is limited to what a wrapper can actually do

`forbid_action`, `remap_action`, `step_limit`, `observation_loss`,
`win_tighten` — and `Variant.load` rejects anything else rather than accepting
it and failing later. The environment is hosted; a wrapper cannot change server
internal dynamics, so an operator outside this set would be a claim we could
not honour. The set is small and sufficient: forbidding the only action that
crosses a gap, or declaring a loss on the only cell a path must traverse,
constructs unsolvability that follows from the construction.

**Every spec must carry a constructive justification**, and the loader enforces
it. An exam needs ground truth and ground truth comes from construction, not
from running the variant and seeing what happened. The shipped set is
deliberately three unsolvable plus one solvable: with only unsolvable questions,
"I failed" and "it was impossible" score identically.

## D-008 · `observation_loss` reads the last frame of a command

One command can return several frames. The predicate is evaluated against the
last one — the observation the arm actually acts from. Evaluating it against
intermediate frames would make a variant's behaviour depend on animation
timing, which is exactly the kind of hidden dependency that makes a truth claim
unfalsifiable. The consequence is a real obligation on the spec author, and
`v003`'s justification discharges it explicitly: it argues that neither
declared cell is ever a transient position.

## D-009 · Level boundaries are derived but recorded

`level` and `level_boundary` break the otherwise clean recorded/derived split
(D-004). Two reasons: `level` is not an API field so it must be derived from
score jumps at all, and the derivation needs the live step sequence, which the
proxy has and a later reader would have to reconstruct. The rule that makes
this safe is that a derived-and-recorded field must be recomputable from the
same file — and `reconcile.py` recomputes both and fails if they disagree.

## D-010 · The replay opens its own probe scorecard

A prefix replay is real traffic: it consumes actions and would add to a
scorecard. It therefore opens a separate card marked as a probe, and runs under
its own `run_id` with `arm: "replay"`. Otherwise re-running a game would
silently change the score the reconciler is checking against — the measurement
would alter the thing measured.

## D-011 · The mock world is a fixture, and its solver is too

The stand-in provider is a breadth-first search, not a language model. A
stochastic decider would make the end-to-end run unreproducible, and replay
would fail for reasons that have nothing to do with the harness. Calling it a
model would be the dishonest version; it is a fixture that produces a
deterministic action from a frame.

The mock's transition rule lives in one function (`arc_mock.slide`) that both
the world and the solver import. Two copies would eventually disagree, and the
disagreement would present as the environment being non-deterministic.

The world **requires the credential**: every gameplay route answers 401 without
a valid `X-API-Key`. That is what makes the seal test a proof rather than an
assertion — `tests/test_seal.py` sends the byte-identical request twice, once
directly (401) and once through the proxy (200), and the only difference is the
injected key.

## D-012 · Streaming is buffered before it is answered

The model proxy reads a streamed response to completion, extracts usage and the
assembled message, records both, then hands the original bytes to the arm. The
recording obligation is absolute and incremental delivery is not needed by
anything in Phase 1, so the simple thing wins. It is a real limitation and it
is in the README, not buried here: an arm that renders tokens as they arrive
will see them arrive at once.

## D-013 · An arm that can see a credential refuses to start

`arm_mock.assert_sealed()` raises if any known credential variable is set in
the arm's environment. A run in which the arm *could* have gone around the
proxies demonstrates nothing about a run in which it didn't, so the arm-side
half of the sealing property is checked at startup rather than assumed. The
proxy-side half is separate: an arm that sends a credential header has it
stripped, and a `bypass_attempt` incident is recorded.

## D-014 · Everything a test asserts, it also proves can fail

The replay and reconciliation tests each have a companion that forges the
ledger and asserts the check goes red. A check that has never been observed to
fail is not evidence that anything passed.

---

*Below: P-9, the shell's closing pass. Frozen scorer, canon guard, red team,
replay spot check.*

## D-015 · The score is a conversion, so it is not in the ledger — the failure is

`Theoria.md` Phase 1 §5 says "逐局跑完即打分入库、与 scorecard 对账". The score
lands in `proxy/var/scores/<run_id>.json` and in `run.json`; it does **not** go
into the ledger.

This is D-004's argument applied to a second derived quantity. A score written
into an append-only file is wrong the day the scoring rule changes and cannot be
corrected; with the scorer outside, a re-score re-prices history instead of
contradicting it. §5 already rules score derived — the frozen scorer is the
`cost.py` of levels.

What *does* go into the ledger is the failure. A reconciliation that disagreed
is an `incident` of kind `score_mismatch`, and one that could not be performed
at all is `score_unreconciled`. That second kind is new and it is the point:
`baseline-arms` lost 22 of 23 scorecards to a transient close-404 and the loss
was **silent**, so Phase 1's reconciliation obligation was quietly not being
performed. A scorer that returned PASS for "nothing to compare" would reproduce
exactly that, so the scorer has three verdicts and `UNDETERMINED` never
collapses into `PASS`.

Scoring happens the moment a game ends, inside `runner.run_game`, not in a sweep
afterwards — Phase 3 audits the order results arrive in, and a batch decided all
at once is a batch someone could have decided after seeing it.

## D-016 · The upstream scorer is not vendored, and that is a decision

`Theoria.md` Phase 1 §5 asks for the frozen scorer "原样接入", and
`baseline-arms/SCHEMA_LOCATE.md` §2.4 identified the upstream
`score_trajectories.py` as pure standard-library Python that runs offline —
apparently the exact thing wanted. `baseline-arms` deliberately did not fetch it
(`SCHEMA_PATH_A.md` §2.2) and left the call to a separate deliberate act. This
is that act, and the answer is still no. Three reasons:

* **Judging whether it is safe to read requires reading it**, which is the exact
  shape of INC-BA-001 — the contamination incident in which looking for upstream
  material taught a subagent the mechanics of nine sealed games. The file is
  probably harmless. "Probably" is what INC-BA-001 was made of.
* **The upstream release declares no licence**, and `Theoria.md` Phase 4
  publishes every tracked file. Vendoring it decides its redistributability on
  its author's behalf.
* **Fetching and running third-party code** is not something one track does on
  its own authority.

So `proxy/scoring/arc_v1.py` is ours, and the *freeze* — not the provenance — is
what makes it satisfy the discipline: one scorer, hashed, named in every
artefact, identical across the three arms. `REGISTRY` takes a second scorer by
construction. If the upstream file is ever adopted it registers beside this one
under its own id with its own freeze entry, and every `run.json` already records
which scorer produced its number, so past runs keep their attribution instead of
being silently re-scored.

The honest cost, stated plainly: our scorer is not the upstream scorer, so a
number from it is not directly comparable to the upstream 98.98%. It does not
try to be — it publishes the API's own scorecard numbers and reconciles them,
and refuses to reimplement the partial-credit percentage at all, because all 32
real scorecards we hold report zero completed levels and the formula is
therefore not determined by any evidence we have.

## D-017 · The canon refuses, rather than describing

F-16 ruled `LEDGER_FORMAT.md` the canon. Until P-9 that ruling was a statement
about what the proxies happened to write: `**extra` would carry any field at all
onto disk. `proxy/canon.py` is the refusal — a field registry consulted by the
writer before serialisation and by `tools/validate_ledger.py` on read, so both
directions are judged by one table.

Three lines, and the second is the contentious one:

* **A banned spelling is named with its replacement.** `frame`, `timestamp`,
  `total_cost_usd` and the rest of the v0 vocabulary raise an error that quotes
  the canonical field and points at the migrator. A refusal that does not teach
  is a refusal the next caller routes around by renaming the field — which is
  why every dollar-shaped spelling carries the whole reason rather than "see the
  other entry".
* **`env_step` and `model_call` are closed; auxiliaries are open.** Two shapes
  means two shapes: the Phase 2 battery reads them without branching, and an
  extra field is a branch someone eventually has to write. Auxiliary payloads
  stay loose because §6 exists precisely so the two shapes can stay closed — a
  `run_start` carries whatever a run needs to describe itself.
* **Types are checked only where a wrong one would produce a plausible wrong
  number.** `score` may not be a bool, because `True` sums as 1. `frames` must
  be a list, because a bare frame written where a list belongs is the
  observation-losing bug §7 was written about. This is not a schema validator
  and does not try to become one.

## D-018 · `env_step` gains `response`, because "complete record" was not true

The first closure property is that every bit entering or leaving an arm is in
the ledger. It was not. A live command response carries `win_levels`,
`available_actions`, `full_reset` and `action_input`; `env_step` recorded
`frames`, `state`, `score` and `levels_completed`, and dropped the rest on the
floor. Nobody noticed because no live run has gone through the proxies yet —
the mock did not return those fields.

`response` holds the response body with `frame` removed. Frames are already
stored whole and hashed; storing them twice would be two things to keep in
agreement.

`win_levels` is why this is more than tidiness: it is the only place the
environment states how many levels a game has, so without it **no score
fraction is computable from the ledger alone** — and Phase 1's whole position is
that conclusions come only from the ledger.

Two facts about the live API were learned in the same pass and are worth
recording where someone will find them. `env_step.score` is a field the live API
**does not return**; it stays in §3 (a shape does not change under the same `v`)
and stays null on live traffic, and nothing should be built on it. And the live
scorecard's shape is `environments[]`, not the flat `score` the mock returned
nor the `cards` mapping `reconcile.py` had guessed at — `STATUS.md` predicted
that surprise and it arrived, but from a corpus rather than from a paid run.

## D-019 · The mock now returns the real scorecard, copied from 32 real cards

`baseline-arms`'s campaign left 32 closed scorecards on disk. They are now
`proxy/tests/fixtures/scorecard_corpus.json`, the mock emits that shape, and the
frozen scorer is calibrated against them. Two consequences worth stating:

* **The surprise `STATUS.md` predicted is spent offline.** It said the first
  live run should expect the scorecard's shape to differ, and that
  `reconcile.scorecard_score` "will need a third [reading] if the real one
  differs". It did differ; the third reading exists; it was paid for with a file
  read rather than with actions.
* **One number in the mock is the mock's own and is not a claim about the API.**
  The per-level score. Every real card reports 0.0 with zero levels completed, so
  the partial-credit rule is not determined by evidence. The mock uses 1.0 per
  completed level because a mock needs *some* rule, and the frozen scorer never
  depends on it — S-3 only checks that a positive score and a completed level
  agree in sign, and S-9's bound holds under either reading of `score`.

## D-020 · The migrator preserves time, so it does not use the writer

`tools/upgrade_ledger.py` builds records itself instead of calling
`Ledger.append`. The reason is narrow and is the only one: `append` stamps `ts`
with the current time, and a migration must preserve when things happened. A
lifted stream is a record of the run, not of the translation. Everything else
the writer does — the canon check, the vault scrub, the canonical spelling — is
done explicitly at the same point.

`LEDGER_FORMAT.md` §7 originally said to mark each lifted record
`"lifted_from": "baseline-arms/v0"`. That was written before the two shapes'
field sets were closed, and a closed shape cannot carry an extra marker. So
provenance moved to the synthesised `run_start`, whose payload is open, and it
says strictly more there: source path, source sha256, migrator version, record
counts, the fields dropped and the holes v0 left. Every lifted record belongs to
a run, so nothing is unattributed, and a reader can still tell a lifted stream
from a native one — which is what the marker was for.

The tool refuses what it does not understand (`UnknownDialect`) rather than
guessing. A migrator that guessed would write a canonical-looking record with
invented meaning, and afterwards the invention would be indistinguishable from a
recording.

## D-021 · The replay spot check reads history instead of buying it

Phase 1's acceptance list wants a bit-exact environment-side replay. A real
replay costs actions on a live scorecard, and no live run has gone through the
proxies yet — so that line had no data behind it.

It turned out the evidence was already on disk. `baseline-arms`'s harness opens
every session with the same fixed probe sweep (RESET, ACTION1…ACTION7) before
the model chooses anything, and it opened fourteen sessions on `ar25-0c556536`.
`arc-recon`'s determinism precheck ran the same opening on the same game in a
different campaign, on a different day, through a different harness. Sixteen
sessions with an identical opening are sixteen replays of that opening.

`tools/replay_spotcheck.py` therefore replays nothing. Two rules keep it honest:
a session is **truncated at its first failed step** (a 400 returns no frame, and
what follows a lost frame is a different history, not a divergent replay), and
agreement is only claimed where **at least two sessions reach the position** —
one session agreeing with itself is not evidence.

Result: 16 sessions, 9 positions, 372 pairwise comparisons, zero disagreements.

Stated as narrowly as the evidence allows: this is cross-session, cross-campaign
determinism **of the environment**, on **one** game. It is not evidence that our
proxies reproduce a run — that needs a live replay through `replay.py`, and it
is still owed. The acceptance line asks for two games; this is the first.

## D-022 · The guard reads a request the way a server would, not the way a form does

The red team put a sealed id past the old scan eleven different ways, and most
of them were the same mistake in different clothes: the guard looked where it
expected the id to be. `check_request` now takes the path, the query, every
header, the **raw bytes**, every string in the parsed body including dictionary
keys, and the concatenation of the body's values — and it looks at each of
those in several readings: percent-decoded up to three times, NFKC-normalised,
zero-width characters stripped, and base64 blobs decoded one level.

Four of the eleven are worth naming because each was a wrong assumption rather
than an oversight:

* **A bare stem is a game id.** `ls20` matched nothing, because the pattern
  required a `-<8 hex>` suffix. INC-005 recorded that the live API answers
  short ids — with a *fake* 200, which is worse than a real one — so a request
  naming a bare stem is a request that reaches the game. The scan now
  recognises any token that equals a stem in the register.
* **Case is not decoration.** `[0-9a-f]` let `ls20-9607627B` through while the
  stem's case was being handled two lines above.
* **A body that will not parse is a body that still gets sent.** `json.loads`
  failing set `body = None`, the guard saw nothing, and `_forward` shipped the
  original bytes regardless. Form encoding, a trailing `{}`, a BOM and a
  trailing NUL all worked.
* **A command that names no game still plays one.** A `guid` is a session, and
  a session belongs to a game. The proxy now remembers which game each `guid`
  it opened belongs to, and a command it cannot attribute to a game is refused
  — an unattributable command is exactly how a sealed game would be played
  through a session opened somewhere else.

**What this does not close, stated rather than implied.** The value-join that
catches an id split across two fields depends on the key order; a different
order defeats it. Base64 is chased one level. Neither is a defence against an
attacker who controls both ends of the encoding, and neither claims to be. The
guard's real strength is elsewhere: the arm has no credential, so it cannot go
around the proxy at all, and these are defences against a *mistake* reaching a
sealed game rather than against a determined smuggler inside our own harness.

The model proxy is now guarded too. `piles.json` rule 2 counts *reading about* a
sealed game as contamination, and a prompt that names one teaches the model that
game — the environment proxy being guarded while the model proxy was not is a
gap in the same rule, not a different one.

## D-023 · Two directions of credential handling, and the claim cut to fit

`Vault.scrub` ran toward disk only. An upstream that echoes the key back in a
response body or header handed it straight to the arm, the ledger stayed clean,
and so the leak was unrecorded as well as unstopped. Both proxies now scrub
what they hand the arm, and a reflection raises a `credential_reflected`
incident: the arm holding no credential is the property the whole construction
exists to make true, and a response is as good a way to acquire one as a
request.

Three narrower repairs in the same pass: a secret used as a dictionary **key**
survived a value-only scrubber; a credential shorter than the length floor was
never registered at all, so the floor that exists to avoid corrupting text was
declining to protect the actual key; and the base64 and percent-encoded
spellings of a secret are now registered alongside it, because they are the
same secret.

The claim in `LEDGER_FORMAT.md` §4 has been cut down to what is true. It said a
ledger through the writer cannot contain a key; it can, if the key is one the
proxies have never seen. What holds is that an *injected* credential cannot,
that a key-shaped string in environment traffic is redacted by pattern with the
structurally key-shaped fields exempted, and that `model_call` bodies are exempt
from the pattern pass because §4 requires them verbatim. A writer cannot redact
what it has never been told and cannot see; saying so is worth more than a
sentence that reads better.

## D-024 · The ledger is self-consistent, not authenticated

The red team's sharpest finding has no local fix. `reconcile.py` and the frozen
scorer check the file against itself: every check is internal consistency, so a
file that no proxy ever wrote reconciles clean if it is written carefully
enough. P-9 raised the price of forgery — the frame hash must hash its own
frames, `seq` must be dense and unique, level fields must recompute, the run
must belong to one arm, the card's totals must add up, and the scorer runs the
canon validator over the run before it will judge it — but a price is not a
proof. Anyone who can write the file can write a consistent file.

The structural answer is a hash chain whose head is published outside the file:
each record carrying the digest of its predecessor, and the final digest
recorded somewhere an attacker with write access to the ledger does not reach.
That subsumes the duplicate-`seq` and forged-hash findings as special cases. It
is registered here and written up as a proposal rather than done quietly at the
end of a hardening pass —
`monitor/inbox/20260728T2200Z-proxy-ledger-hash-chain.md`.

**Correction, made while writing that proposal.** This entry first said the
chain "changes the envelope, which under §8 means a version bump and a
conversation with three arms and the Phase 2 battery". That was wrong, and
wrong in the direction that makes a thing not get done: it priced the work at a
cross-track negotiation when it does not need one.

`prev` can be **optional**, and then `v` stays `1.0`. §1 says fields are added
only by appending; §8 bumps `v` when a field's *meaning* changes or a
*required* field is added, and an optional field is neither. v1.0 readers —
the battery's adapter, the other arms — are unaffected and need not move.

The obvious objection is that an optional field is one a forger simply omits.
It is not, because the compulsion does not come from the format. It comes from
the **published head**: `run_start` declares that the run is chained,
`runs/*/MANIFEST.json` declares how long the chain should be and what it hashes
to, and the validator then treats a missing `prev` exactly as it treats a wrong
one. Omitting the head is a decision a person has to make, and it leaves its
trace in git. That is stronger than a required field, which would only have
retired every existing reader.

Two things the chain still would not buy, recorded here so the next person does
not have to rediscover them — and recorded at all because §4's "a ledger
through the writer cannot contain a key" was an over-claim that RED-15
collected on in this same session:

* **Forgery before publication still works.** The property gained is precisely
  *tamper-evidence after the head is published*, not authentication of the
  recording.
* **Nothing local can prove the frames came from ARC.** Only an API-signed
  receipt could, and the API offers none.

There is also a timing argument, which is the reason this is not simply
deferred to Phase 4 where the absence would actually be felt: **a chain is
evidence only for records written after it exists.** Every round it is put off
is a round of ledgers that can never be chained retroactively. It costs nothing
to build before the first live run and cannot be applied to that run
afterwards.

Until it exists, the honest form of the closure claim is: **the ledger is
complete and self-consistent, and the arm cannot write to it — but the operator
can.** Phase 1's "no bypass" property was always about the arm, and it holds.

## D-025 · The spend gate is on the socket, not beside it

`forward.forward()` takes a keyword-only `permit` with **no default**. A caller
that does not pass one gets a `TypeError` at the call site.

The alternative — a `check_budget()` a caller is expected to call first — is
what INC-BA-003 already tried, and the reason it failed is instructive. The
second session obeyed every rule it knew about, including the pile cut, which
is a far more demanding rule than "check the budget". It did not fail at
compliance. **The rule it needed did not exist to be known.** A convention binds
only the people who have read it, and that set is not one you can enumerate at
03:00 when a second session starts.

So the gate is shaped like `assert_playable()`: a function on the first line of
the path that spends, whose refusal is an exception rather than a return value.
A refusal returned as a `Response` would let a budget breach be retried as
though it were weather.

The permit is checked before **every attempt**, not once per `forward()` call.
One call can open up to `max_attempts` sockets; the pool's action unit is one
outbound request; and a retry storm is precisely the shape that reaches the
600 rpm limit. A gate that charged a retry loop as one request would be blind
to the case it was built for.

## D-026 · Undeclared is answered with a small number, not with a shrug

A proxy constructed without a reservation takes one itself, using the policy's
`default_run_caps` ($5.00 / 600 actions).

Three options were on the table and two are worse. **Refusing to construct**
would have made the field required, which breaks `theoria-arm/harness/run.py`
and `proxy/replay.py` — code this ticket may not edit — and a fail-closed
change that another track has to fix before anything runs at all is a change
that gets reverted. **Claiming the pool's whole remaining headroom** would mean
two undeclared runs can never coexist, which is a rule nobody would keep.

The default caps are deliberately small. Not declaring a budget should be
inconvenient rather than unlimited: $5 is under a tenth of the whole approved
programme, so an undeclared run cannot quietly become a campaign, and the global
pool ceiling binds on top of it regardless. The holder record carries
`undeclared: true`, so the monitor can see who did not say.

## D-027 · Blindness is scoped to the quantity it blinds

An unpriced model call makes the pool's **dollar** total a lower bound, so no
further dollar may be spent against it. It says nothing whatever about ARC
actions, which are counted by the request and not by a price table.

The inherited code refused *everything* on one unpriced call, and wiring the
gate to the egress path is what exposed that: a single mock model call with a
name absent from `proxy/pricing/` stopped the **environment** proxy — which
spends no dollars at all — for every session sharing the pool, permanently,
because the ledger is append-only and nothing could take it back.

A gate that can brick the whole programme on one missing price-table row is not
fail-closed. It is a single point of failure wearing fail-closed's clothes, and
the difference matters because the first kind gets fixed and the second kind
gets disabled.

`price_unpriced(reservation, usd=…, resolves=…, reason=…)` is the way back, and
it is narrow on purpose: appended rather than edited, a stated reason required,
and it refuses to resolve more blindness than the pool actually has — otherwise
the count could be driven negative and the gate re-opened on nothing.

## D-028 · The historical ledger is read, not rewritten

`baseline-arms/ledger.jsonl` has 560 lines with no `campaign` field. New lines
carry one; the old ones are attributed at **read** time, by a rule with exactly
one source: a line's own `campaign` wins, otherwise `run_id` is looked up in
`out/campaign_cells.jsonl`, otherwise `unknown`.

Rewriting the file in place would be the INC-008 manoeuvre, and INC-008 was a
deliberate, incident-recorded exception taken because the ledger contained
something that must not be there — session bearer tokens. Nothing here is
*wrong* in those lines. They are silent, and silence is recoverable from a file
that already exists.

The measured result is **151 decidable, 409 not**, and the 409 stay `unknown`.
The other reconstructions available — infer from timestamps, or from which games
ran together — would produce a complete-looking table, and that is the objection
to them: a spend figure that cannot be checked against anything is worse than a
gap that is visible.

## D-029 · D-024 built: the chain, and the two things it does not do

D-024 registered a hash chain as the structural answer to RED-40 and left it
unbuilt. S15 built it, without redesigning it — the shape below is D-024's, and
the value of writing it down again is only that the claims are now measured
rather than predicted.

`prev` is the sha256 of the previous line's bytes **as written**, including that
line's own `prev`. It is optional, so `v` stays `1.0` (§8 bumps for a changed
meaning or a new *required* field; an optional one is neither). It lives in
`canon.ENVELOPE`, so the writer owns it and a caller that supplies one is
refused — a chain a caller can set is a chain a caller can forge. It is assigned
under the same lock as `seq`, so the two cannot disagree about write order.

**Why bytes and not a recomputation.** A verifier that re-serialises each record
before hashing is checking that today's `canonical()` matches the one that wrote
the file. Change that function once and every ledger ever written goes red
simultaneously — which teaches everyone to ignore the alarm. Hashing the bytes
on disk asks the only question worth asking.

**Six verdicts, not two.** `verify_chain` returns PASS / FAIL / PARTIAL /
UNCHAINED / EMPTY / MISSING. Collapsing UNCHAINED into PASS would have been the
fifth time this repo mistook a check that never ran for a check that passed, and
an empty file is refused for the same reason: two builds that produced nothing
are byte-identical.

**Publication is not writing, and this was nearly shipped wrong.** The first
version of this work wrote `ledger_head` into `runs/<run_id>.json` and called
the head published. It is not: `runs_dir` defaults under `proxy/var/`, and
`proxy/.gitignore` ignores `var/` — correctly, it is runtime output. So the
head was being written to a file the forger can rewrite as freely as the ledger
itself, and the tamper-evidence argument bought exactly nothing while looking
complete. One `git check-ignore` on the path settled it.

The publication is therefore explicit and named in two places: `play()` returns
the record so an **arm** lifts `ledger_head` into its tracked
`runs/<slug>/MANIFEST.json`, and an operator outside an arm runs
`verify_chain --emit-head <tracked path>`, which refuses to write a head for
any stream that does not verify — a head witnessing an unverified file is worse
than no head, because it looks like one. `test_the_runners_default_head_location_is_gitignored`
pins the trap so that relocating `var/` forces someone to think about it.

**The two limits, both now pinned as tests.** A forger who rewrites the whole
file and recomputes every link produces a stream that verifies —
`test_rewriting_the_whole_chain_is_NOT_caught_without_a_published_head`. Only
the head published outside the file catches that.
And the converse, found while measuring rather than while designing: **an
interior edit does not move the head at all.** A real 61-record mock run had one
score digit flipped on line 3; the chain walk caught it at line 4 while the head
still matched the published value. Each mechanism misses exactly what the other
catches, so the honest form is that both are load-bearing, not that one is a
backstop for the other.

Unchanged from D-024, and still the closing claim: forgery *before* publication
still works, and nothing local can prove the frames came from ARC — only an
API-signed receipt could, and the API offers none. What the ledger now supports
is: **complete, self-consistent, unwritable by the arm — and, after the head is
published, tamper-evident against the operator.**

Not yet done, and listed so it is not mistaken for done: the frozen scorer has
no chain check and therefore no forged negative control (D-014 requires one),
`validate_ledger.py` does not walk the chain, and `upgrade_ledger.py` does not
yet mark lifted streams unchained.

## D-030 · The two shapes stop being closed, because a writer that runs after the money is spent may not refuse

`canon.py` used to refuse any field `LEDGER_FORMAT.md` §3/§4 did not list. The
reason given was a reader's reason — "the battery reads two shapes without
branching, and an extra field is a branch someone eventually has to write" —
and it was applied to the writer, where the same rule is paid for in a
different currency.

INC-TA-006 is the invoice. `model_call`'s field set was closed *after* P-8
started writing `beat`/`label`/`transport`/`proxied`/`proxy_gap` on that record.
Arms import `proxy/` as a library, so the closure arrived on a commit the
`theoria` arm had never touched, in a directory it may not edit. The first live
desk call was refused at serialisation **after the provider had been paid
$2.695**, the reply was discarded, and the arm's `except Exception` turned it
into "the desk failed" — so the run would have kept paying $2.70 a call until
its ceiling stopped it.

The principle that follows is not "be lenient". It is that a **ledger record is
written after the fact**: by the time the writer sees a `model_call`, the
request is sent and the money is spent. A refusal cannot un-spend it. It can
only destroy the evidence that it happened, which is the one thing an
append-only record surface exists to prevent. **Refusing to record is strictly
worse than recording something a reader may have to skip.**

So an unlisted field on `env_step`/`model_call` is now warned about (`UnknownField`,
tallied in `Ledger.unknown_fields`) and written. What stays a refusal is
everything that is *wrong* rather than merely unknown: a v0 spelling, a dollar
figure (§5), a caller-set envelope field, a missing required field, a type that
would produce a plausible wrong number. Those were the properties the closure
was credited with, and none of them ever depended on it.

The reader side moves with it. `validate_ledger.py` reports an unlisted field as
a **notice** and leaves the verdict alone, because the frozen scorer calls it
from S-12 and a scorer that fails a run over a field it could ignore is the same
mistake one direction over. `notices` is a separate out-parameter rather than a
`severity` key on `problems`, so the widespread `assert validate_records(...) == []`
keeps meaning what it meant and no caller can promote a notice to a failure by
forgetting to filter.

**What is given up.** A typo in a field name is now a typo on disk instead of an
exception, and the two shapes are no longer literally two shapes. The first is
the intended trade — the typo is visible in the warning, the tally and the
validator's notices, and the alternative was losing the record. The second was
never quite true anyway: the format has always promised that a *defined* field
does not change meaning under one `v`, and a reader that handles what it knows
and ignores the rest was correct before this change and is correct after it.

## D-031 · A tightening is announced; the detector is what makes the rule real

`proxy/CONTRACT_CHANGES.md` is the procedure: widening what the proxies accept
is free, narrowing it is a breaking change that needs a PARTNER_SYNC
announcement, one cycle of notice, and a compatibility window in which the old
form warns rather than refuses.

A protocol with no detector is prose, and prose is what failed in D-030 — the
closure was made by someone who had a written reason and did not know they were
breaking another track. So `proxy/canon_contract.json` pins `canon.describe()`,
`proxy/tools/contract.py` diffs the live registry against the pin and labels
each difference `additive` / `tightening` / `neutral`, and
`tests/test_contract_changes.py` fails the suite the moment they disagree.

The classifier earns its keep on one distinction a set-diff gets backwards:
a name added to a shape's `fields` frees writers, and a name added to its
`required` refuses them. Both are "a list grew".

**Stated limits.** It cannot verify that an announcement was made — a test
cannot read PARTNER_SYNC and judge a paragraph. It cannot enforce the wait. And
it only sees `canon.describe()`, so the spend gate's protocol, the guard's
verdict semantics and the pricing tables are covered by the rule in prose and by
nothing in code. What it does is remove the excuse the incident actually had, by
putting the question in front of whoever changes the contract at the moment they
change it.

The half this directory cannot do for itself is the importer's:
`python -m proxy.tools.contract --fingerprint` goes in a run manifest and gets
**diffed between runs**. That is W-1521's standing recommendation after
INC-TA-006, and it is the same shape as the `upstream_pin` finding — a pin that
is written and never compared documents an incident afterwards rather than
preventing one.

---

*Below: V22, from the sealed drill's §4 finding.*

## D-032 · `win_tighten` on a scoreless game: the bit, not the refusal and not the warning

`exam/SEALED_DRILL.md` §4 ran the frozen operator library against a world it was
not designed for. Four of the five operators survived; `win_tighten` did not.
A worldgen trace carries `{t, frame, action, win}` and no score, so `score` is
always `None`, and `after()` read `have is None` and `have < needed` as the same
condition. On such a game `win_tighten` rewrote **every** `WIN` to
`NOT_FINISHED` at **every** requirement value. It did not tighten the win
condition; it removed it.

The conservative reading stays. Treating an absent score as satisfying
`score_at_least` would let a game that never reports a score win a tightened
variant outright, which is the worse of the two errors by a wide margin. What is
wrong is that the collapse was silent: the `applied` record an absent score
produced was byte-identical in shape to the one an honest shortfall produced,
so nothing downstream could tell a variant whose claim followed from its
construction from one whose claim followed from an accident of the protocol.

**Three ways to stop being silent were available, and this is why the third one
was taken.**

*Refuse.* Wrong side of D-030, and for exactly D-030's reason. `after()` runs on
a response that has already been paid for and received; a refusal there cannot
un-send the request, it can only destroy the evidence that the rewrite happened.
INC-TA-006 is the invoice for that manoeuvre. There is a place where refusal is
right — declining to *start* a `win_tighten` run against a game not known to
report a score — but that is a precondition check at run setup with knowledge
the wrapper does not have at response time, and it is stated below as a Phase 4
obligation rather than pretended into the runtime.

*Warn.* A stderr line is not in the artefact. Python dedups a repeated warning
to one line, the record is what survives the session, and this repository has
already paid for the difference: D-030 kept `Ledger.unknown_fields` precisely
because "the tally is the only complete trace". A warning would have made the
collapse audible for as long as somebody was watching the terminal, which is
not the failure mode — the failure mode is a variant claim read six weeks later
from a ledger.

*The bit.* `applied` now carries `reason` (`score_absent` / `score_below`),
`degenerate` (bool), `occurrence`, and, on the first absent-driven rewrite of a
session, `note` — the sentence, so a human meets the argument and not only a
boolean. `VariantRuntime` counts them in `degenerate_wins` and keeps the first
in `first_degenerate`.

**A bit with no reader is decoration, so it has two readers.** D-031 already
says it: a rule with no detector is prose. So —

* `env_proxy` records one `variant_degenerate` incident per session, written
  after the `env_step` it refers to, so it always points at a record that
  already exists. Once per session and not once per WIN: a scoreless game
  rewrites every WIN identically and a per-WIN incident buries the first under
  copies of itself.
* `proxy/tools/check_variant_degeneracy.py` reads any ledger and **exits 2**.
  It reads the marker and nothing else — it does not re-derive degeneracy from
  `score: null`, and that restraint is load-bearing: strip the marker and the
  tool passes the same stream, which is what makes the marker rather than a
  lucky second signal the thing that catches this.
* `verify.py` gains rung 5, which plays a game built to trip the guard and
  requires a refusal, then strips the markers from that same ledger and requires
  a pass. A rung that could only ever be green is decoration one level up: the
  acceptance run on rung 3 carries no variant, so a guard pointed at it would
  pass without ever having fired.

**The negative control runs on both kinds of session.** `tests/
test_variant_degeneracy.py` plays two whole runs: a scoreless one, and a scoring
one whose requirement is set above anything the game can reach so that
`win_tighten` fires for a genuine shortfall. The scoreless run is refused, then
passed with the marker stripped. The scoring run is passed, then refused with a
single marker forged into it. Checking only the first pair would leave open that
the guard reacts to the session rather than to the defect (D-014).

**The mock gained a `scoreless=True` mode** because the claim is about what a
session leaves in a ledger, and a hand-built response body cannot show that. It
is off by default: the mock's job is to look like the live API, and the live API
scores.

### The certificate grammar: no fourth form, and the rule that replaces it

The drill's §4 consequence 2 is that `invariant`, `cut_set` and `counting`
cannot express "the win condition is unsatisfiable because the game reports no
score", so ground truth itself cannot earn the reason half of that item and the
oracle's ceiling is 0.95 rather than 1.0.

**Judgement: do not add a fourth form.** Not primarily because `exam/` is
another territory — that constrains where the rule can be *enforced*, not what
the right answer is. The reason is that the other three certificates are
arguments about the world: the board, the command alphabet, what the arm can
reach. "This game reports no score" is a fact about the **protocol**, and one
the wrapper learns by looking, not by arguing. A fourth form would let a
certificate earn reason-credit for restating a property of the measuring
instrument, and the exam would then be grading arms on how well they discover
defects in the exam. Worse, it would make the degenerate construction
*legitimate*: once there is a form for it, a variant whose unsolvability comes
from a missing score becomes a well-formed exam item, and the library's one
non-game-agnostic operator acquires a certificate that makes it look
game-agnostic.

The right treatment is that these variants are **not exam items at all**. A
`win_tighten` whose verdict came from an absent score does not test anything
about the game; it tests whether the harness noticed. So:

> **Rule R-V22.** A `win_tighten` variant whose run produced any degenerate
> rewrite does not count toward the reason score, and its unsolvability may not
> be cited as following from its construction. The verdict is not thereby
> wrong — the variant really is unwinnable — but the *reason* is the protocol,
> not the board, and the reason is what is being scored.

The executable half lives on this side of the boundary, which is the half
`proxy/` can actually guarantee: `check_variant_degeneracy.py --json` reports
`exam_eligible: false` for such a variant and exits 2, so the fact reaches a
grader in a form that costs something to ignore, and `verify.py` rung 5 keeps
the detector itself honest. What `proxy/` cannot do is make `exam/`'s scorer
subtract the item; that is one line for whoever owns the rubric, and until it
is written the 0.95 ceiling stays a *named* cap rather than a mystery — which
was the drill's actual complaint.

### For Phase 4

**Whether a game reports a score is a protocol question, not a mechanics
question, and it is answerable without breaking the seal.** So it must be
answered *before* `win_tighten` is used against a sealed game — a variant built
on an unchecked assumption there produces an unsolvable item whose
justification is false, and the only thing that would reveal it is the incident
this decision added. Check first; the incident is the backstop, not the plan.

### D-032a · What the adversarial pass took back

Four of the sentences above were wrong or overstated when they were written.
They are corrected here rather than edited in place, because what a decision
claimed before it was tested is part of the record.

**"records one incident per session" was "records at most one, and sometimes
none".** The notifier asked `runtime.degenerate_wins != 1` — a read of a shared
counter *at notify time*. `env_proxy` serves on a `ThreadingHTTPServer` and one
`VariantRuntime` is shared by every command for a game, so two responses can
both be rewritten before either handler reaches its notifier; both then see the
counter at 2, both return, and the incident is written **zero** times. The
adversarial pass drove that interleaving and observed it. The mitigation that
was in place (`_State.degeneracy_reported`) defended the harmless direction —
the incident firing twice — and the test written for it pinned that same
harmless direction while citing the very hazard it was not covering. A
duplicate incident is noise; a missing one is the silence this ticket exists to
remove, reproduced one layer up.

Fixed by moving the claim into the runtime: `VariantRuntime.take_first_degenerate`
hands the first record to exactly one caller under the runtime's own lock, and
the notifier acts on what it was handed rather than re-reading a counter.
`_State.degeneracy_reported` is gone — the handover is the once-guarantee.
`test_the_incident_survives_two_rewrites_landing_before_either_notifier` is the
interleaving, and M23/M24/M26/M27 are the mutants.

**"two readers" was two readers of unequal weight.** The guard exits non-zero;
the incident is a record whose only automated reader was the suite asserting it
had been written. That is a defensible design — an incident is *for* the human
reading the ledger later, which is this decision's stated failure mode — but
"two readers" invited a stronger inference than the wiring supported. It is now
three, and the third one is the load-bearing one: see below.

**"the fact reaches a grader in a form that costs something to ignore" described
a gate, and what existed was a command.** Nothing ran
`check_variant_degeneracy` over a real run's ledger; rung 5 ran it only against
a ledger rung 5 had fabricated seconds earlier. The territory boundary explains
why `proxy/` cannot make `exam/` subtract the item; it does not explain why
`proxy/` was not applying its own rule to its own runs. So `runner` now scans
the ledger the run just wrote and puts `variant_degeneracy` into the run record
— verdict, count, `variant_records`, `exam_eligible`, and the rule's name —
and `verify.py` requires that key on every run record. Recorded, not raised:
by then the game is played and the money is spent, and refusing there would
destroy evidence rather than prevent anything (D-030).

**The guard could not tell "nothing degenerate happened" from "I could not
look".** `scan_file` skipped unparseable lines under a comment claiming that a
skipped line "cannot hide a degenerate rewrite that a readable line would have
shown" — a tautology, since the skipped line is precisely the one that would
have shown it. A ledger truncated mid-record, which is what a killed writer
leaves, produced a `PASS` byte-identical to a clean run's. The report now
carries `variant_records` and `skipped_lines`, and an unreadable line makes the
verdict `INCONCLUSIVE` (exit 1) rather than `PASS`.

**One finding is acknowledged and deliberately not fixed here.** `redact.py`'s
process-global vault scrubs dictionary *keys*, and `register(force=True)`
ignores the length floor, so a short forced credential rewrites field names on
their way to disk. The adversarial pass showed the consequence for this
ticket specifically: a secret that is a substring of `variant`, `applied`, `op`
or `degenerate` turns a stream full of degenerate rewrites into a silent `PASS`
— **the new guard fails open on it**. That is a real hole and it is upstream of
everything here; fixing it means changing `redact.py`'s contract, which is its
own decision and its own ticket. What is owed and paid here is that the guard
being downstream of it is written down (`RUN_STATE.md`, and the filed ticket)
rather than left for the next person to discover.

## D-P12-001 · The model proxy's guard allows an unregistered id; the environment proxy's does not

`SealedPileGuard`'s `unknown_policy` defaults to `deny` and that is right for
the environment proxy: its requests *address* a game, one id, named on purpose,
and an id outside the register is something the cut did not authorise. The
model proxy inherited the default and it is wrong there, measurably rather than
arguably.

`guard._GAME_ID` matches two-to-six alphanumerics, a hyphen, and eight hex
digits. Free text hits that constantly. The first real `claude -p` request ever
put through `ModelProxy` was refused **403 `unknown_game`** on `code-20250219`,
a token inside the CLI's own system prompt — before the missing provider key
could even become the problem. So `deny` on this path bought a 403 on every
request and caught nothing: the sealed pile is a fixed enumeration, so an id
that is not in the register is not a sealed game, and no amount of failing
closed on unknowns makes a sealed one more likely to be caught.

`theoria-arm`'s `ModelDesk._screen_the_pile` had already written the reasoning
down — "the proxy's request path can afford `unknown_policy = deny` because a
request names one game deliberately; a 20,000-character prompt is not that" —
and applied it only to its own screen. This is the same sentence, applied where
it was pointing.

The obvious objection is that a guard was loosened, and the answer is what a
guard is *for*. This one refuses two things: a sealed id, and an id outside the
cut. The first is the property Phase 1 rests on and is untouched — and, as of
P-12, demonstrated rather than asserted, which it had never been on this path
(`DUAL_PROXY.md` §4 step 3). The second is a widening rule for a surface that
is not addressed by id at all.

## D-P12-002 · A development-pile id in a prompt is refused at the proxy too

`SealedPileGuard.verdict` returns *allowed* for a dev game, correctly: it
answers "may this game be played", and the four dev games may. Theoria.md:353's
硬规 is a different and stricter question — **游戏 ID 永不进模型上下文,全程匿名化**
— and it is about every id, not the sealed ones only.

So the model proxy asks the second question itself rather than borrowing the
answer to the first. `verdict()` is left alone: it is shared with the
environment proxy, where refusing a dev id would refuse the whole development
pile, which is the pile we play.

The reason it is at the proxy and not only at the arm is the same reason the
proxies exist at all. `ModelDesk._screen_the_pile` already enforces this, and
that makes it a property of one caller's discipline. Enforced here it is a
property of the recorded path, which is the only kind of property Phase 1's
sealing claim can be built out of. Two independent screens is the intended
shape, not duplication.

## D-P12-003 · The model proxy authenticates its client, when it is told to

`ModelProxyConfig` gains `client_token`. Unset — the default, and every
existing caller — the behaviour is unchanged: any client that can reach the
port is served, and a credential it supplies is recorded as a `bypass_attempt`
and stripped. Set, the proxy requires the caller to present that exact token
(`x-api-key` or `Authorization: Bearer`), compares it with
`hmac.compare_digest`, and answers **401 `client_token_required`** otherwise —
before `_forward` and therefore before the injected provider key can be spent.

The reason it is now worth having: the whole point of P-12 is to make the model
proxy carry a funded key. An unauthenticated loopback port in front of a funded
key is an open relay to that key for every process on the machine. That was
tolerable exactly as long as the key did not exist, which is the condition this
work is trying to remove.

Two consequences of the design, both deliberate:

* **The token is not registered with `redact.VAULT`.** The vault keeps
  credentials out of ledgers and out of subprocess environments; this token's
  entire purpose is to be put into a subprocess environment. Registering it
  would make `theoria-arm/harness/modelcall.py`'s by-value environment scan
  raise `CredentialBreach` on the one variable the transport must set. It is a
  loopback capability, not a credential — it buys nothing anywhere but the port
  that minted it, and it wears the prefix `theoria-local-` so that a reader
  finding one in a log can decide that in ten seconds.
* **Presenting the minted token is not a `bypass_attempt`.** It is the desk
  saying who it is. Recording it as an attempted bypass would put one incident
  on every call and bury the signal the record exists to carry — which is how a
  real bypass gets ignored. A *second* credential header carrying something
  else is still recorded, which is the interesting case.
