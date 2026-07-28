# REDTEAM — an adversarial audit of the double proxy

An independent attempt to falsify the three properties `proxy/README.md` claims
are true **by construction**:

1. **No bypass / sealing** — an arm holds no credential; egress around the two
   proxies fails; a credential never reaches the ledger or an artefact.
2. **The sealed-pile guard holds** — no request naming a sealed game leaves the
   proxy, however the id is spelled or hidden.
3. **The record is faithful** — the ledger and the score reconciliation cannot
   be made to report a clean run for a dirty one.

46 attacks were run. **29 landed, 17 were blocked.** *(Since this report was
delivered, all 29 have been addressed and the suite passes with no xfail
markers left — see "After the fixes" at the end. Four limitations are
documented rather than closed, and one of them, RED-40, is a real hole.)* Every one of them is a test
in `proxy/tests/test_redteam.py`, which stays resident in the suite: a blocked
attack is a passing test and therefore a permanent regression guard; a landed
attack is `xfail(strict=True)`, so the suite stays green while the finding stays
visible, and the day someone fixes it the test goes red as an XPASS and asks to
be re-verdicted.

Nothing here touched the network beyond loopback, no real credential was read or
printed, and no sealed-pile game was played: sealed ids appear only as strings in
payloads aimed at loopback sinks the test file defines itself.

## What was under attack

The audit ran against the working tree at `edb3c37` + uncommitted work, LF-
normalised sha256 prefixes:

| file | sha256 (12) |
|---|---|
| `proxy/guard.py` | `a8b613c4db0f` |
| `proxy/env_proxy.py` | `f23ad57720b2` |
| `proxy/model_proxy.py` | `717a8885156c` |
| `proxy/redact.py` | `31962e6c4b00` |
| `proxy/forward.py` | `896c13c889ff` |
| `proxy/ledger.py` | `6574cc8da714` |
| `proxy/reconcile.py` | `64a4c0f30641` |
| `proxy/scoring/arc_v1.py` | `78259b72a0c4` |

**The target moved during the audit.** A concurrent session was editing this
same worktree: `canon.py`, `scoring/`, `tools/validate_ledger.py` and a rewritten
`reconcile.py` all appeared while these attacks were being written, and they
closed five class-D attacks that had landed an hour earlier (RED-35, RED-37,
RED-46 outright; RED-39 and RED-41 partially). Those are recorded below with
their **current** verdict, and the tests were re-aimed at the code as it now
stands. Class A, B and C were unaffected by that work.

## Findings

| id | class | attack | verdict | severity |
|---|---|---|---|---|
| RED-01 | A/B | 302 from the upstream to another host | **LANDED** | critical |
| RED-02 | A/D | that redirect leaves no trace in the ledger | **LANDED** | medium |
| RED-03 | A | absolute-URI request line retargets the forward | blocked | — |
| RED-04 | A | `//host/path` protocol-relative path | blocked | — |
| RED-05 | A | dot-segment traversal in the path | blocked | — |
| RED-06 | A | `CONNECT` tunnel | blocked | — |
| RED-07 | A | arm-supplied `X-Upstream` / `X-Forwarded-Host` | blocked | — |
| RED-08 | A | `/__proxy/../api/...` forwarded | blocked | — |
| RED-09 | A/B | credential header on `/__proxy/*` is unrecorded | **LANDED** | low |
| RED-10 | B | upstream reflects the key in the body → the arm gets it | **LANDED** | high |
| RED-11 | B | upstream reflects the key in a header → the arm gets it | **LANDED** | high |
| RED-12 | B | same reflection through the model proxy | **LANDED** | high |
| RED-13 | B | the reflected key is scrubbed out of the ledger | blocked | — |
| RED-14 | B | a key shorter than `MIN_SECRET_LEN` reaches the ledger | **LANDED** | medium |
| RED-15 | B | an *unregistered* credential reaches the ledger verbatim | **LANDED** | high |
| RED-16 | B | a UUID-shaped key raises no `credential_in_body` | **LANDED** | medium |
| RED-17 | B | a secret used as an object **key** survives scrubbing | **LANDED** | medium |
| RED-18 | B | a split or base64 secret survives scrubbing | **LANDED** | low |
| RED-19 | B | `run.json` / `/__proxy/state` carry the key | blocked | — |
| RED-20 | C | bare short id (`ls20`) is invisible to the guard | **LANDED** | critical |
| RED-21 | C | uppercase hex suffix (`ls20-9607627B`) evades | **LANDED** | high |
| RED-22 | C | `-v2` / `.old` / uppercase stem | blocked | — |
| RED-23 | C | percent-encoded hyphen in the query | **LANDED** | high |
| RED-24 | C | sealed id elsewhere in the path, incl. `%2F` | **LANDED** | critical |
| RED-25 | C | sealed id in a body the guard cannot parse | **LANDED** | critical |
| RED-26 | C | id split across fields / base64 | **LANDED** | medium |
| RED-27 | C | zero-width and full-width confusables | **LANDED** | low |
| RED-28 | C | id in a passthrough header parameter | **LANDED** | medium |
| RED-29 | C | session-scoped (`guid`-only) command | **LANDED** | medium |
| RED-30 | C | doctored cut with a recomputed sha256 | **LANDED** | high |
| RED-31 | C | stale digest / renamed pile lists | blocked | — |
| RED-32 | C | model proxy has no guard at all | **LANDED** | high |
| RED-33 | C | chunked body smuggled past the guard | blocked | — |
| RED-34 | C | control: sealed id in `body["game_id"]` | blocked | — |
| RED-35 | D | second `run_end` whitewashes a mismatch | blocked (S-7) | — |
| RED-36 | D | float `levels_completed` drops out of the derivation | **LANDED** | medium |
| RED-37 | D | boolean level count | blocked | — |
| RED-38 | D | one step appended under a second `arm` | **LANDED** | high |
| RED-39 | D | duplicate `seq` on the audit path | **LANDED** | medium |
| RED-40 | D | a wholly fabricated run reconciles PASS | **LANDED** | high |
| RED-41 | D | writer accepts a `frame_hash` that does not hash | **LANDED** | medium |
| RED-42 | D | a dollar figure nested inside `usage` | **LANDED** | low |
| RED-43 | D | top-level `cost` / `cost_usd` spellings | blocked | — |
| RED-44 | D | one unknown-`v` line makes the file unauditable | **LANDED** | medium |
| RED-45 | D | a run with no readable scorecard | blocked | — |
| RED-46 | D | a scorecard that contradicts its own environments | blocked (S-10) | — |

---

## Class A — egress around the proxies

### RED-01 — a redirect carries the credential off-host — **LANDED, critical**

*What it tries.* Point the env proxy at an upstream that answers `302 Location:
http://<other host>/stolen`, and see whether the injected `X-API-Key` follows.

*Evidence.* `test_red01_a_redirect_does_not_carry_the_credential_off_host`. The
thief sink received exactly one request, path `/stolen`, carrying
`X-API-Key: <the proxy's key>`. The arm saw a normal `200`.

*Root cause.* `forward.forward` calls `urllib.request.urlopen`, which follows
redirects by default and whose `HTTPRedirectHandler` copies every request header
except `Content-Length`/`Content-Type` onto the new request — so the injected
credential is replayed to whatever host the redirect names, with no redirect
policy and no destination allowlist anywhere in the module.

*Why it matters here.* This is the one attack that breaks sealing without the
arm doing anything: the arm cannot choose the upstream, but anything that can
answer as `three.arcprize.org` (a hostile response, a hijacked CDN edge, a
misconfigured `--upstream`) turns the proxy into a credential courier. The whole
double-proxy argument is "the key exists only inside this process".

### RED-02 — and the redirect is invisible in the record — **LANDED, medium**

The `env_step` for the redirected call records `status 200`, `path
/api/cmd/RESET`, `attempts 1`, `forwarded true`. Nothing names the other host.
Root cause: the ledger records the URL the proxy *intended*, never the URL the
transport actually finished on (`urlopen` knows — `response.url` — and the value
is discarded).

### RED-03…08 — blocked

`POST http://elsewhere/... HTTP/1.1` produces `upstream + absolute-URI`, an
unparseable host, and a 502 with no socket opened. `//host/path` and
`/api/../../x` stay on the configured host. `CONNECT` is a 501 from
`BaseHTTPRequestHandler`. `X-Upstream`/`X-Forwarded-Host` are not on the
passthrough list. `/__proxy/anything` 404s without forwarding. The destination
is genuinely operator-chosen, which is why RED-01 is the only way out.

### RED-09 — `/__proxy/*` is a hole in the record — **LANDED, low**

`_handle` dispatches `/__proxy/` **before** `_check_arm_is_keyless` and before
any ledger write. An arm that hits `/__proxy/health` carrying its own
`X-API-Key` proves it is not sealed, and no `bypass_attempt` incident is written
— nor any record that the request happened, against LEDGER_FORMAT's "every bit
entering or leaving an arm is in the ledger".

---

## Class B — the arm reaching the credential

### RED-10 / RED-11 / RED-12 — reflection hands the key to the arm — **LANDED, high**

*What it tries.* An upstream that echoes the received `X-API-Key` back — in the
JSON body (RED-10, env proxy command path; RED-12, model proxy) or in a response
header (RED-11, env proxy meta path).

*Evidence.* The arm's response body contained the literal key; the arm's
response headers contained `X-Echo-Key: <key>`. The ledger copy was clean
(RED-13 passes), so **the leak is invisible in the record**.

*Root cause.* `VAULT.scrub` is applied on the path to disk and nowhere else.
`_command` writes the parsed upstream body straight back to the arm, `_meta`
and the model proxy write `response.body` plus `passthrough_headers()`, which
filters hop-by-hop names only. Sealing therefore holds only as long as the
upstream never reflects the credential — a property of *the other side*, which
is exactly the kind of assumption this design set out to remove.

### RED-15 — an unregistered credential is written verbatim — **LANDED, high**

LEDGER_FORMAT.md §4 says: a ledger that has been through the writer *cannot*
contain a key. It can. `Vault.scrub` replaces only values `register()` has seen,
which is the ARC key and the provider key. Any other credential — an arm's own
token, a key pasted into a prompt, a key an upstream returned — is recorded in
full. Demonstrated with a foreign 36-char key posted in a scorecard-open body
and then read back out of `l.jsonl`.

### RED-16 — the credential detector misses the ARC key shape — **LANDED, medium**

`looks_like_credential` matches `sk-…` or a run of 32+ alphanumerics. A 36-char
UUID-shaped credential — the shape `CLAUDE.md`'s own masking example implies for
`ARC_API_KEY` (`7171...05dd (len 36)`) — contains no 32-char alphanumeric run,
so no `credential_in_body` incident is raised. The heuristic's docstring says it
is "deliberately loose" because "a false negative costs a published key"; it is
blind to the one key shape this repository actually handles.

### RED-14 / RED-17 / RED-18 — three holes in the scrubber — **LANDED**

* **RED-14 (medium)** `MIN_SECRET_LEN = 12` silently declines to register a
  shorter credential, so it is never scrubbed. A short key reflected by the
  upstream lands in the ledger in clear.
* **RED-17 (medium)** `Vault.scrub` rewrites dict *values* and inspects dict
  *keys* only against `SENSITIVE_HEADERS`. `{"<secret>": 1}` reaches disk with
  the secret as a JSON object key. Both the arm and the upstream control object
  keys in bodies that are recorded whole.
* **RED-18 (low)** Scrubbing is exact substring replacement: a secret split
  across two fields, or base64-encoded, passes through. Inherent to the
  approach, worth stating because §4 claims otherwise without qualification.

### RED-13 / RED-19 — blocked

The *registered* keys are scrubbed out of the ledger (`<redacted>` present, key
absent), and the proxy summaries that `runner` copies into
`var/runs/<run_id>.json` carry only `key_injected: true`.

---

## Class C — guard evasion on the game id

This is the weakest surface by a wide margin: **11 of 15 attacks landed.** The
guard's own docstring is the right standard — "a guard that only looked at
`body["game_id"]` would be a guard by convention again" — and the extractor
falls short of it in every direction at once. All of the following were verified
end-to-end: the request went through a running `EnvProxy` and the sealed id was
then read out of what the upstream sink received.

### RED-20 — a bare short id is invisible — **LANDED, critical**

`_GAME_ID` requires `-[0-9a-f]{8}`, so `ls20` matches nothing and
`check_request` returns `allow`. `stem()` exists precisely because "callers
sometimes pass a bare id without the version suffix" — but the extractor can
never produce one, so `stem` is only ever fed ids that already matched. arc-recon
INC-005 records that the upstream answers short ids with a **fake 200**: a short
id is a live request, not a typo, and this is the single most likely spelling for
an arm or a human to use by accident.

### RED-24 — the path is barely inspected — **LANDED, critical**

`game_ids_in` applies `_GAME_IN_PATH` (`/game(s)/<id>`) to the path and never
applies the generic `_GAME_ID` to it at all. `/api/scorecard/ls20-9607627b`,
`/api/v1/ls20-9607627b/frames` and `/api/games%2Fls20-9607627b` were all
forwarded verbatim to the upstream.

### RED-25 — an unparseable body is an unguarded body — **LANDED, critical**

`_handle` sets `body = None` when `json.loads` raises, the guard then sees
nothing — and `_forward` still sends **the original raw bytes**. Verified for
form encoding, a trailing `{}`, a UTF-8 BOM, and a trailing NUL. One byte of
difference in the encoding turns the guard off while leaving the request intact.

### RED-21 / RED-23 — spelling and encoding — **LANDED, high**

`classify` lowercases the stem, but the extractor's hex class is `[0-9a-f]`, so
`LS20-9607627B` and `ls20-9607627B` never match (an uppercase *stem* is caught —
RED-22). Query strings are matched raw and never percent-decoded, so
`?game_id=ls20%2D9607627b` reaches the upstream, which decodes it back.

### RED-26 / RED-27 / RED-28 / RED-29 — four more channels — **LANDED**

Id split across two fields or base64-encoded (medium); zero-width space,
soft hyphen and full-width hyphen inside the id (low); id parked in a
`Content-Type` parameter, which is on the passthrough list while headers are
never shown to the guard (medium); and a **`guid`-only command** (medium) — the
guard is stateless, so against an upstream that resolves the session from the
guid, a sealed game is stepped without its id appearing anywhere, and the ledger
records `game_id: "?"`.

### RED-30 — the cut certifies itself — **LANDED, high**

`load_piles` hashes the file's own body and compares it with the `sha256` the
file itself carries. Moving `ls20-9607627b` into `dev_pile` and recomputing that
digest passes the integrity check, and `guard.py` pins no expected value —
although `tests/test_guard.py` and `tests/test_seal.py` both assert the real
prefix `3feca53e`, so the constant is known and simply not enforced where it
matters. A stale digest and renamed pile lists both fail closed (RED-31).
*(The same self-certifying shape appears in `proxy/scoring/frozen.json`, which
carries the hash of the scorer beside it. Noted, not separately attacked.)*

### RED-32 — the model proxy has no guard — **LANDED, high**

The guard is wired into the environment proxy only. A prompt reading "describe
the mechanics of ls20-9607627b" was forwarded to the provider unmodified.
`piles.json` rule 2 counts reading *about* a sealed game as contamination —
"reading those teaches the mechanics just as well as playing" — and the model
proxy is the second of the two holes an arm can speak through.

### RED-33 / RED-34 — blocked

A chunked body is invisible to `_read_body` **and** to `_forward`, so the sealed
id does not leave. The ordinary spelling is refused with 403, no socket to the
upstream, and `guard_block` + `sealed_pile_request` + a denied `env_step` in the
ledger.

---

## Class D — forging the record

Five attacks in this class were closed by the concurrent session's obligation
battery (`S-0…S-10`) and `tools/validate_ledger.py` while this audit was
running. What remains:

### RED-40 — nothing authenticates a record — **LANDED, high**

A ledger written entirely by hand — no proxy ever ran — reconciles **PASS**. The
reconciliation checks the file against itself: the ledger's numbers against the
scorecard the ledger also contains, and derived fields against the same records
that carry them. Every check is internal consistency; none is evidence that the
file records anything that happened. Append-only prevents deletion, not
authorship, and any process that can write `var/ledger.jsonl` — including the
arm, which shares the filesystem — can write a clean run.

### RED-38 — one step under a second `arm` whitewashes a run — **LANDED, high**

`reconcile_run` partitions by `run_id` alone. A run whose steps disagree with its
card was turned from FAIL to PASS by appending a single `env_step` with
`arm: "probe"` and the level count the card claims. `arm` is in the envelope and
is simply not used to scope the derivation.

### RED-36 / RED-39 / RED-41 / RED-44 — **LANDED, medium**

* **RED-36** `observed` keeps only `isinstance(x, int)`, so steps recording
  `levels_completed: 2.0` are dropped from the derivation *in silence* and the
  run reconciles clean against a card claiming zero. A non-int should be a
  problem, not a skipped record.
* **RED-39 / RED-41** Duplicate `seq` — LEDGER_FORMAT §2's definition of a
  corrupt file, and the signature of an appended forgery — and a `frame_hash`
  that does not hash its own `frames` are both caught by
  `tools/validate_ledger.py` (positive controls in the tests confirm it) but by
  nothing on the audit path: `read_ledger` accepts them and `reconcile_run`
  reports PASS. The writer also puts a lying `frame_hash` on disk without
  complaint — `canon` checks `n_frames` against `frames` but never the hash.
* **RED-44** One appended line carrying `"v": "2.0"` makes `read_ledger` raise
  for the *whole file*, so every run in it becomes unauditable — and the file is
  append-only, so the poison line cannot be removed. Rejecting an unknown
  version is right; doing it file-wide converts a one-line write into permanent
  loss of the audit.

### RED-42 — the cost ban stops at the top level — **LANDED, low**

`usage` is copied through verbatim by contract and is never inspected, so
`usage: {"cost_usd": 3.5}` reaches the ledger. Top-level spellings are refused
on every event shape (RED-43).

### RED-35 / RED-37 / RED-46 — blocked

A second `run_end` is caught by S-7, a boolean level count by S-2/S-6, and a
scorecard contradicting its own environments by S-10. These three landed against
`reconcile.py` as it stood at the start of this audit and are recorded as blocked
against the version above; the tests remain as regression guards.

---

## The shortest route to closing this

Ranked by what each change buys:

1. **Pin the destination and stop following redirects** in `forward.forward`
   (`urlopen` with a redirect handler that refuses, or a host allowlist checked
   before every attempt), and record `response.url`. Closes RED-01 and RED-02 —
   the only credential-egress path that needs no cooperation from the arm.
2. **Guard the raw bytes, not the parsed body.** Run the id search over the
   decoded request line, the query, the headers the proxy forwards, and
   `raw.decode(errors="replace")` — and refuse a body that does not parse rather
   than forwarding it unguarded. Closes RED-24, RED-25, RED-26, RED-28 and most
   of RED-27 in one change.
3. **Widen the id grammar**: case-insensitive hex, an optional suffix so a bare
   stem matches, percent-decoding first. Closes RED-20, RED-21, RED-23.
4. **Scrub on the way out as well as on the way in** — one `VAULT.scrub` over
   the response body and headers before `_respond`, in both proxies. Closes
   RED-10, RED-11, RED-12.
5. **Put the guard in front of the model proxy too** (RED-32), and pin the cut
   digest as a constant in `guard.py` rather than trusting the file's own
   (RED-30).
6. **Scope the reconciliation by `(run_id, arm)`** and run
   `tools.validate_ledger` from the reconcile path. Closes RED-38, RED-39,
   RED-41.

RED-40 is the one finding no local change fixes: as long as the ledger is a
plain file that the audited party can write, "the record is faithful" is a
property of the filesystem, not of the construction. A hash chain over `seq`
with the head published outside the file is the usual answer, and it would also
subsume RED-39.

---

# After the fixes — P-9's response to this report

*Written by the track that was attacked, not by the red team. Everything above
this line is the audit as it was delivered and has not been edited.*

**All 46 attacks are now blocked. `proxy/tests/test_redteam.py` passes with no
`xfail` markers left in it**, and the attack set stays resident in the suite, so
each finding is now a permanent regression guard aimed at the exact hole it
found. Where a landed attack was closed, the finding's original wording is kept
as a comment on the test that closes it — a fix whose reason is lost is a fix
somebody eventually reverts.

Six of the tests had to be re-aimed rather than merely un-marked, because the
fix removed the thing they were measuring. Each is marked in the file and listed
here so nobody has to wonder whether the goalposts moved:

| test | why it was re-aimed |
|---|---|
| RED-02 | asserted that a *followed* redirect left no trace. Redirects are refused now, so it asserts the refusal is recorded — the same question in its surviving form. |
| RED-16 | opened by asserting `not looks_like_credential(FOREIGN_KEY)` "as the mechanism". The detector knows the UUID shape now, so that line asserts the opposite. |
| RED-18 | decoded the scrubbed base64 to prove it still held the secret. The value is replaced outright now, so the assertion is that the secret is absent rather than that it decodes differently. |
| RED-30, RED-31 | expected `SealedPileGuard` to load a doctored cut and then deny. It raises instead — a stronger closed failure. Both outcomes are accepted; playing the game is not. |
| RED-41, RED-42 | asserted that a validator would catch the forgery later. The writer refuses it now, so they assert the refusal and that nothing reached the file. |
| RED-44 | built its ledger by hand, which no longer reconciles at all — that is RED-40's own fix. It now writes a real run through the writer and asks the same question: does a poison line under *another* `run_id` destroy this run's auditability? |

## What changed, by finding

| finding | how it is closed |
|---|---|
| RED-01, RED-02 | `forward.py` builds an opener whose redirect handler returns `None`, so a 3xx is handed back instead of chased. The response carries `final_url` and `redirect_to`, both land in `http`, and a refused redirect raises a `redirect_refused` incident. `crossed_hosts()` checks the invariant anyway. |
| RED-09 | the keyless check runs before the `/__proxy/` branch. |
| RED-10, RED-11, RED-12 | `redact.scrub_outbound` runs on every response both proxies hand the arm, body and headers; a reflection raises `credential_reflected`. |
| RED-14 | `Vault.register(..., force=True)` for the injected credential: the length floor exists to avoid corrupting text, not to decline to protect the real key. |
| RED-15 | `redact.scrub_keyish` redacts key-shaped strings in environment traffic, with structurally key-shaped fields (`card_id`, `guid`, `frame_hash`, …) exempt and `model_call` bodies exempt. **And `LEDGER_FORMAT.md` §4's claim was cut down to what is true** — see D-023; the over-claim was the actual defect. |
| RED-16 | `_KEYISH` knows the UUID shape, which is the shape of the ARC key's own mask. |
| RED-17 | `Vault.scrub` scrubs dictionary keys as well as values. |
| RED-18 | base64 and percent-encoded spellings are registered as forms of the same secret; a secret split across adjacent fields is caught by a span pass over the concatenated values. |
| RED-20 … RED-29 | the guard rewrite: bare stems against the register, case-insensitive ids, percent-decoding, NFKC and zero-width stripping, raw bytes when the body will not parse, headers, dictionary keys, one level of base64, the concatenation of body values, and `guid` → game attribution with an unattributable command refused. See D-022. |
| RED-30 | `EXPECTED_PILES_SHA256` is pinned in `guard.py`. A document that certifies itself certifies nothing. |
| RED-32 | the model proxy runs the same guard over prompts; a sealed id raises `sealed_pile_in_prompt` and the request is refused. |
| RED-36 | the ledger view rejects a non-integer `levels_completed` as malformed instead of dropping it, and reads the **last** value rather than the maximum. |
| RED-38 | new check S-11: one run is one arm. |
| RED-39, RED-41 | the writer recomputes `frame_hash` and refuses one that disagrees; the scorer runs `tools.validate_ledger` over the run as check S-12, so duplicate `seq` is now on the audit path. |
| RED-42 | `canon` refuses a dollar-shaped key nested inside `usage`. "No dollar figure is ever written" is a property of the file, not of one field. |
| RED-44 | `read_ledger(strict=False)` rejects the *line* instead of the *file*, and the unreadable line is reported as `ledger_health` on the run's report plus a `ledger_unreadable_line` incident — a poison line under another `run_id` no longer decides this run's verdict. |

## What is **not** closed, and is not claimed to be

* **RED-40 stands.** Every check is still internal consistency, so a
  sufficiently careful forger writing canonical records reconciles clean. The
  test passes because the forgery it uses is now detectable, not because
  forgery is. P-9 raised the price; it did not authenticate anything. The
  structural answer is a hash chain with the head published outside the file,
  which changes the envelope and therefore needs a version bump and three arms'
  agreement. Registered as D-024.
* **The value-join is order-dependent.** An id split across two fields is
  caught when the values concatenate in key order and not otherwise.
* **Base64 is chased one level.**
* **A secret the writer has never seen and that does not look like one cannot
  be redacted.** §4 now says so.

The first is a real hole. The other three are defences against a *mistake*
reaching a sealed game, not against a determined smuggler operating inside our
own harness — and the reason that distinction is acceptable is the property none
of these attacks touched: the arm holds no credential, so it cannot go around
the proxy at all.
