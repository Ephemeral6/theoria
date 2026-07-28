# P-11 · RUN_STATE

Prompt: `monitor/prompts/P-11-arc-hygiene.md` · branch `agent/p11-arc-hygiene` ·
base `df9f748` · 2026-07-28.

## Delivered

**1 · F-11 ledger — done.** Nine sealed games registered in
`data/contamination_log.jsonl` at the levels INC-BA-001 self-reported, with
one disclosed deviation (`dc22-fdcac232` keeps the stronger
`design_document_disclosed` level INC-004 gave it rather than that table's
轻微, since copying the rating would have been a downgrade);
`ls20-9607627b` and `ft09-0d8bbf25` marked `quarantined_from_claims`; `INC-006`
filed with the ruling, its basis, and the 21→19 consequence. `piles.json`
untouched and re-verified against its published sha256.

Beyond the letter of the order, because "21→19" was otherwise an assertion:
`contamination.py` derives the register and the claim set from the append-only
log, re-hashes `piles.json` the way `cut_piles.py` produced it, and audits every
tracked call record — arc-recon's ledger plus baseline-arms' `ledger.jsonl` and
`probe_log.jsonl`, 2489 calls, **0 sealed games addressed**. `data/claim_set.json`
is its output, and the numbers are computed rather than typed.

**The batch was then reviewed by an adversarial pass** whose only brief was to
find registration/ruling mismatches. It earned its keep: it reproduced a
**fail-open bug** in the claim-set derivation — matching two exact strings and
letting everything else fall into `clean`, the fully-uncontaminated bucket, so a
typo'd or missing `claims` field would silently put a contaminated game in the
strongest set while the headline number never moved. Now fails closed, with three
regression tests and a negative control. It also caught four places where the
prose outran the evidence, the sharpest being that **`dc22` is not a
"minor-exposure" game** — `design_document_disclosed` is mechanics prose, one
level above every blurb row, making it the most exposed game *inside* the claim
set. F-11 retains it and this track executes rulings rather than revising them,
so the tension is recorded as a residual question for the owner. All corrections
are `INC-006a` plus six superseding log entries; the ruling, the levels, the
quarantine set and 21→19 all stand.

**2 · Canary replay — done and baselined.** `canary.py`, spec in
`data/canary.json`, history in `data/canary_runs.jsonl`, gate in
`data/campaign_freeze.json` (absent until something drifts; `check-freeze` reads
absence as not frozen). Four games, 16 actions for a full sweep, **4/4
PASS**. Drift files an incident and writes the freeze file; `check-freeze` exits
1 so any harness in any language can gate on it.

The expectations were derived offline from `precheck.json` — only steps the
precheck's two replays already agreed on — so the baseline run was a *test* of
them, not their source. It passed, which makes three agreeing replays across two
days and three sessions.

**3 · Access check — closed, in `ACCESS_CHECK.md`.** Rate limits and quota
archived (600 rpm documented; 429 documented but absent from the OpenAPI spec; no
per-key action quota documented anywhere; failed 400/500 do not reach the
scorecard counter). Frame caching and release licensing resolved conservatively:
code is MIT, **game data has no stated licence**, and the site terms' compilation
clause arguably bars republishing a frame corpus — so publishing raw frames
should be treated as needing written permission, while hashes and metrics are
safe. Cross-session residue answered by the canary baseline: none.

## Two findings the ticket did not ask for

**INC-007 — the retry amplification is our own missing cookie jar.** The API sets
`AWSALB*` routing cookies and a `GAMESESSION` cookie; `client.ArcClient` echoes
none. Interleaved A/B: **20/20 first-attempt RESETs with a cookie jar, 0/20
without**, three runs, three games, arms on *different* games and swapped between
runs to kill the session-competition confound. Zero action cost. This reframes
INC-001b: the backend is multi-instance, but what changes replica every call is
us, and the 9.2× amplification the canary measured is largely self-inflicted.

**A scorecard trap.** Cards auto-close after 15 minutes of inactivity (official
docs). That is very likely the mechanism behind baseline-arms' 22-of-23
close-time 404s, and it means an arm whose model call can exceed 15 minutes loses
its scorecard mid-run.

## 4 · The cookie fix, applied and re-measured (added after the first pass)

INC-007 deferred the fix and asked for a before/after on the instrument being
changed. That was then done rather than waived. Same canary spec, same sequences,
same stored hashes, once on each transport, ~80 seconds apart:

| | before (no jar) | after (jar) |
|---|---|---|
| verdicts | 4/4 PASS | 4/4 PASS |
| HTTP calls for 16 actions | **190** | **20** |
| retries | 170 wasted | **0** |

The sweep issues 20 commands; after the fix it cost 20 HTTP calls, every step
first-attempt on all four games. Per game: ar25 72→6, g50t 41→3, sk48 35→6,
tn36 42→5.

**The verdicts are the result, not the speed.** Identical hashes across a
transport change show the fix is behaviour-preserving, and retire a worse
possibility than slowness — that the cookie-less client had been talking to
something other than the live session, the exact shape of INC-005. It had not.
Scoped by INC-009: **11 of the 16** action hashes discriminate (tn36's four are
no-ops, g50t's ACTION1 expects the pristine frame), so the claim rests on those
11 plus the four RESET hashes — not on 16.

Two design points settled by measurement rather than argument: one jar per client
shared across games is correct (cross-game probe, all four games out and back,
8/8 first-attempt), and the jar learns routing cookies from **error** responses,
which is why it works inside the existing retry envelope — `HTTPCookieProcessor`
(handler_order 500) runs before `HTTPErrorProcessor` (1000). A future reordering
would degrade the fix silently, so a test pins it.

`cookies=False` is kept deliberately: every figure this project has measured was
taken on the old transport, and an instrument you cannot put back is one you
cannot re-verify.

## 5 · INC-008 — the probe leaked session tokens into the tracked ledger

Self-caught while writing the fix. `probe_stickiness.py` wrote raw `Set-Cookie`
headers for 55 calls — values included, `GAMESESSION` being a bearer token for a
live session. It bypassed `client._record`, which has always redacted
`X-API-Key` so that no credential reaches disk; the ledger is tracked and Phase 4
publishes every tracked file.

Fixed both directions: names-only logging going forward, and `redact_ledger.py`
replacing the 55 values while keeping the names and marking each entry. It edits
at byte level, so untouched entries stay byte-identical — the diff is exactly
those 55 lines. A test now asserts no ledger entry carries a cookie value; it was
watched failing on all 55 first.

Editing an append-only file was deliberate and is argued in the incident: the
ledger's other stated invariant is that credentials never enter it, and the two
collided.

## Open, and deliberately not closed here

* **Cookie values remain in git history** at the pushed commit `29c631e`.
  Removing them means rewriting a published branch — destructive, breaks anyone
  who has fetched it, and not this track's call. Exposure is bounded:
  development-pile sessions, all abandoned, no sealed game, API key never
  involved. Owner decision (INC-008).
* **baseline-arms' client is untouched.** Same cause, same cure, its own code.
  Notified via PARTNER_SYNC; not edited.
* **`data/recon_ledger.jsonl` contains raw frames and is tracked.** Phase 4
  publishes every tracked file. Before release it must be redacted to hashes or
  covered by written permission. Flagged in `ACCESS_CHECK.md` §8, not discharged.
* **ACTION6 `data` shape** still blocks tn36 and the whole `click` family.
  Untouched by this ticket.
* **tn36's canary is shallow** for the same reason the precheck's PASS was: its
  four actions are accepted no-ops with an unchanging frame, so the canary
  certifies RESET-state reproducibility and no-op consistency, not gameplay.
* **`available_actions` reads `null`** for ar25 and sk48 in `precheck.json`
  because those runs were reconstructed by `precheck_resume.py`, which does not
  carry the field. Cosmetic; the report understates what is known.
* **No sensitivity-analysis tooling exists yet.** INC-006 obliges every claim-set
  statistic to be reported twice; `claim_set.json` names the two groups, but
  nothing computes the second figure. That belongs to whoever builds the exam.
* **dc22's retention is unsettled** (INC-006a). It is inside the claim set at a
  mechanics-prose level, which the ruling's own basis arguably excludes. Owner
  call, not this track's.
* **`arc-recon/` has no `.gitattributes`** while `core.autocrlf=true`, so the
  committed blobs carry CRLF and `client.py`'s appends carry LF —
  `recon_ledger.jsonl` currently holds both (790 / 194). It parses fine and no
  content-level hash is affected, but file-level hashes are not portable across
  checkouts. Pinning `eol=lf` the way `engine-rig/.gitattributes` does would fix
  it and would also renormalise a 2 MB append-only ledger, which is not a change
  to make from a side branch during a merge round.

## Budget and red lines

| | |
|---|---|
| actions spent | **48** (16 baseline + 16 before + 16 after). The ticket's cap was 30; the paired before/after was authorised afterwards and is the overrun, stated rather than absorbed. |
| probes | **0 actions** — A/B and cross-game are RESETs, which the scorecard does not count |
| sealed-pile API calls | **0**, audited over 2489 calls in three ledgers, two tracks |
| `piles.json` | unmodified, sha256 re-verified |
| tests | 40 passed, offline |

Touched `arc-recon/` only. `PARTNER_SYNC.md` appended, never edited.

## 6 · The patch was reviewed before the after-run's actions were spent (INC-009)

A five-lens adversarial review (transport, secret hygiene, regression blast
radius, experiment soundness, record/code consistency) ran while the before-run
was in flight. 30 findings raised, 17 survived independent refutation, 13 died.
No published number changed — but four defects were real:

* **The redactor leaked through itself.** `cookie_names` split on `,`, so a value
  containing a comma emitted a fragment of the *value* as a name. The one
  function whose job was to drop values could emit one. Now no comma splitting at
  all, plus RFC 6265 token validation, and it under-reports rather than
  over-reports when a caller has already collapsed headers.
* **A failed request left no ledger row** — timeout, reset, or a body dying
  mid-read escaped before the record was written. That breaks the module's own
  completeness promise, and it put a hole in the project's most load-bearing
  check: `contamination.py`'s sealed-pile audit can only see what the ledger
  holds, so a call carrying a sealed id that then timed out would have been
  invisible to it *and* to the test asserting it was clean. Every request that
  leaves the process now records exactly one row and re-raises.
* **The cookie record was in the wrong tense** — snapshotted after the response
  was absorbed, so the first call of every session was logged as holding cookies
  it provably had not sent. Now `cookies_sent` / `cookies_held_after`.
* **The value-detector test could not fail** for two of its three fields, because
  it looked for `=` in lists that cannot contain one. The INC-003 shape, inside
  the test written to prevent an INC-008 repeat. Now a token-charset check with a
  positive control.

Plus: the pinned jar had made the retry envelope weaker than the transport it
replaced (40 retries to one replica instead of 40 draws) — `send_command` now
drops the routing pins every 5 failures and keeps the session cookie. And the
smaller ones: two-call ledger appends, unrecorded redirects, the probe collapsing
five `Set-Cookie` headers to one, a documented `--check` flag that did not exist,
and the baseline confirmation dropping the transport covariate.

**Two of the 17 were stale** — the review snapshotted before INC-007a and INC-008
were filed, so its "code cites INC-008 but none exists" pair was already false.
Checked against the file rather than taken on trust.

The lesson is uncomfortable and worth keeping: all of it was in code written in
the same session that was congratulating itself for catching INC-008. The
instrument you just built to check something is the instrument nobody has
checked.
