# 一件接入核查 — the Phase 1 access check, item by item

[Theoria.md](../Theoria.md) Phase 1 lists the things that must be "逐项核实并入账"
before anything is built on the live API. This file is that ledger: one row per
item, what settled it, and what is still open. Nothing here is settled by reading
the docs alone where a measurement was possible, and nothing is settled by a
measurement where the docs contradict it — both are recorded when they disagree.

| # | Item | Status | Settled by |
|---|---|---|---|
| 1 | RESET semantics — full reset or level reset, hidden random source | **answered** | precheck, 4 games |
| 2 | Cross-session residue | **answered** — none, now across three sessions and two days | precheck ×2 + canary |
| 3 | Scorecard semantics — one card per game, in-card aggregation | **answered, with two traps** | baseline-arms measurement + official docs |
| 4 | Does one action return several frames | **answered** — yes | precheck (7 frames on one command) |
| 5 | Is `level` a response field | **answered** — yes | precheck |
| 6 | Rate limits and quota | **answered** — see below; the binding constraint is not what we assumed | official docs + baseline-arms measurement + this track's probe |
| 7 | Canary replay | **built and baselined** | [`canary.py`](canary.py), [`data/canary.json`](data/canary.json) |
| 8 | Frame caching and release licensing | **answered conservatively** — publishing raw frames is not licensed | official terms |

---

## 1 · RESET semantics

`POST /api/cmd/RESET` returns `full_reset: false` on a fresh session and
`levels_completed: 0`: RESET is a **level reset**, and the level it resets to is
the one the session is on. It returns a `guid` (the session handle), the
`available_actions` list, `state`, `win_levels`, and `frame`.

No hidden random source is visible at the granularity we can see: two RESETs in
different sessions produce a byte-identical initial frame on all four development
games, and did so again a day later (item 2). That rules out per-session
randomisation of the initial state. It does **not** rule out randomness deeper in
a level, which only longer play can show.

## 2 · Cross-session residue — none

The strongest evidence on this item is now the canary rather than the precheck,
because it adds a third session and a second day at zero extra design cost:

| replay | when | source |
|---|---|---|
| precheck run-a | 2026-07-27/28 | `data/precheck.json` |
| precheck run-b | 2026-07-27/28, separate session and scorecard | `data/precheck.json` |
| canary baseline | 2026-07-28T00:35Z, separate session and scorecard | `data/canary_runs.jsonl` |

All three agree hash-for-hash on every step of every development-pile game. A
session leaves nothing behind that a later session can see: same RESET state,
same frames from the same actions.

Note what this does *not* say. It says the environment is reproducible, not that
it is stateless — the server clearly keeps per-session state (that is what the
`guid` and the `GAMESESSION` cookie are for). The claim is only that state does
not leak *between* sessions.

## 3 · Scorecard semantics — one card per game holds, and two traps

**Aggregation.** `total_actions` on a scorecard equals the number of **successful**
ACTIONs, not HTTP attempts. baseline-arms established this against four
independent samples spanning two model tiers, two games and two campaigns
(PARTNER_SYNC 2026-07-28); 30 failed actions backed by 8 HTTP retries each were
counted zero times. So retry amplification does not consume whatever the
scorecard counts.

Two limits on that, both worth carrying: a request the server *executes* costs an
action even if it accomplishes nothing (a click on empty space returns 200 and
counts), and the scorecard counter is not proven to be the same counter as any
server-side quota.

**Trap 1 — a closed scorecard cannot be retrieved.** `GET /api/scorecard/<id>`
after closing returns 404, so the score exists only in the response to the
successful close. baseline-arms lost 13 of 14 pilot cells to this and had to
patch `close_scorecard` with a retry envelope.

**Trap 2 — cards auto-close after 15 minutes of inactivity** (official docs,
`docs.arcprize.org/scorecards.md`). This is very likely the mechanism behind
trap 1's 404s rather than transient failure, and it has a direct consequence for
long runs: **a campaign that thinks slowly loses its scorecard.** Any arm whose
model call between actions can exceed 15 minutes — an LLM arm with a long
context, a planner that runs a search — must keep the card alive or reopen it,
and must not assume the card it opened is the card it is still writing to.
Scorecards are also batched to the leaderboard roughly every 15 minutes.

## 4 · Cascade semantics — one action can return several frames

Settled observationally, not from documentation: a single `ACTION2` on
`g50t-5849a774` returned **7 frames**; every action on `sk48-d8078629` returns
**2**. `frame` is always a list. The environment has an internal tick, so `step`
must be modelled as `action → frame sequence`. This is the answer Theoria.md
Phase 1 wanted before freezing the shape of `step`.

## 5 · `level` is a response field

`levels_completed` and `win_levels` are both returned and maintained throughout
play; no inference from score jumps is needed. Cross-check: `win_levels` = 7 on
g50t matches `len(baseline_actions)` = 7 in the catalogue.

## 6 · Rate limits and quota

**Documented** (`docs.arcprize.org/rate_limits.md`): **600 requests per minute**
during the research preview, breach returns **429** with error code
`RATE_LIMIT_EXCEEDED`, and repeated offenders face progressively longer backoff.
Increases are negotiable by mail. There is no SLA.

Three gaps in the documentation, all of which matter to us:

* **No `Retry-After` and no `RateLimit-*` headers are documented.** A client has
  to back off blind.
* **429 does not appear in the OpenAPI spec** (`arc3v1.yaml` documents only
  200/400/401/404 on every operation). The spec's error list is incomplete;
  do not generate a client from it and assume the result handles rate limiting.
* **No per-key action quota is documented anywhere** — not in the API docs, not
  in the key docs, not in the competition rules. Absence from the documentation
  is not absence from the implementation, so this stays an assumption rather than
  a finding.

**Measured** (this track, and baseline-arms): failed 400/500 attempts do not
appear in the scorecard's action count (item 3). The canary baseline ran 16
actions in 147 HTTP calls — **9.2× amplification**, at the pessimistic end of the
2.5–10× band the precheck recorded.

**The archiving conclusion, which is not the one we expected.** The campaign
budget arithmetic Theoria.md asks for — 三臂 × 局数 × 回合 + 戳探 + 前缀重放 —
was framed around an action quota that "可能先于 token 成为瓶颈". On the evidence
there is no documented action quota to bust. What is documented is a **rate**
limit, and rate is a constraint on *concurrency and retry storms*, not on total
volume. Restated for planners:

* A single-process arm cannot approach 600 rpm; it spends most of its wall clock
  waiting on the model.
* Concurrent campaigns plus retry storms can. Four processes each retrying at the
  precheck's envelope (40 attempts, backoff capped at 5 s) is the shape that gets
  near the limit, and INC-BA-003 is a live instance of exactly that arrangement
  arising by accident between two sessions that could not see each other.
* So the gate that matters is a **shared, cross-session one** — the thing
  INC-BA-003 asked for. `data/campaign_freeze.json` is the file-based half of it;
  see [`canary.py`](canary.py).

And the amplification figure itself turns out to be mostly self-inflicted —
see the next section.

### 6b · The retry amplification is our own missing cookie jar

The official REST overview states the server sets `AWSALB*` cookies that must be
echoed on later requests or routing and game state break. `client.ArcClient` uses
bare `urllib.request` with no cookie jar and echoes nothing.

[`probe_stickiness.py`](probe_stickiness.py) runs an interleaved A/B — two
clients, identical in every way except that one keeps a `http.cookiejar` — and
counts first-attempt RESET success. RESET is a command, not an action, so the
probe costs **zero action quota**. Results are in
[`data/stickiness_probe.json`](data/stickiness_probe.json).

The server issues `AWSALBAPP-0..3` **and a `GAMESESSION` cookie**.

| run | control game | sticky game | cookie-less | cookie jar |
|---|---|---|---|---|
| 1 | g50t | g50t | **0/8** | **8/8** |
| 2 | ar25 | sk48 | **0/6** | **6/6** |
| 3 | sk48 | ar25 | **0/6** | **6/6** |
| | | **total** | **0/20** | **20/20** |

Run 1 has a confound: with both arms on one game, the cookie arm could be
starving the other of a live session, since INC-001a recorded that the API
reports "a session is already open" with the identical `game not found` message.
Runs 2 and 3 remove it — the arms are on different games, and which arm gets
which is swapped between them. The result does not move.

One thing the probe does **not** settle: the cookie-less arm scored 0/20 here,
harsher than the ~1-in-9 per-attempt rate the same cookie-less client showed
during the canary run minutes earlier (0/20 at p=1/9 has probability ≈ 0.10, so
they are not flatly inconsistent, but the gap is unexplained). Something
time-varying may sit on top of the routing effect. What is established is that
the cookie jar removes the failure — not that routing is the whole story.

This reframes INC-001b. "Unavailability arrives in waves of roughly 1–3 minutes"
described the symptom correctly and named the right suspect — a multi-instance
backend where only some replicas hold the session — but the cause is not that the
service is intermittently unavailable. It is that **our client asks a different
replica every time**, and the runs of consecutive failures that looked like
outage waves are what a geometric distribution looks like when you plot it. The
2.5–10× amplification, the 40-attempt envelopes, and a large part of both tracks'
wall clock and dollar estimates are the price of that omission.

### 6c · Applied, and re-measured before and after (INC-007a)

The fix is `urllib.request.build_opener(HTTPCookieProcessor(jar))`, one jar per
client, `cookies=True` by default and `cookies=False` kept so the old transport
can be reproduced — every figure this project has measured was taken on it.

The same canary sweep — same spec, same sequences, same stored hashes — was run
once on each transport, ~80 seconds apart:

| | before (no jar) | after (jar) |
|---|---|---|
| verdicts | 4/4 PASS | 4/4 PASS |
| actions executed | 16 | 16 |
| **HTTP calls** | **190** | **20** |
| HTTP per action | 11.88 | 1.25 |
| **retries** | **170 wasted** | **0** |

Per game, HTTP calls: ar25 72→6, g50t 41→3, sk48 35→6, tn36 42→5.

The cleanest way to state it: the sweep issues **20 commands** (4 RESET + 16
ACTION). After the fix it cost **20 HTTP calls** — 1.00 attempt per command,
every step first-attempt on all four games. Before, the same 20 commands cost
190.

**The verdicts are the real result, not the speed.** The frame hashes are
identical across the transport change, so the fix is behaviour-preserving — and
that retires a worse possibility than slowness: that the cookie-less client had
been talking to something other than the live session all along, which is exactly
the shape of INC-005's counterfeit short-id 200s. It was not. It was reaching the
right session, after paying for nine wrong replicas first.

**Why it works inside the existing retry envelope**, which is not obvious: the
first call of a retry loop is usually the 400, so the jar has to learn the
routing cookie *from an error response*. It does, because urllib sorts response
processors by `handler_order` and `HTTPCookieProcessor` (500) runs before
`HTTPErrorProcessor` (1000), the handler that turns a 400 into an exception. A
future reordering would degrade the fix silently with nothing failing, so
`test_hygiene.py` pins it.

**A third data point on the variance.** The 00:35Z baseline, also cookie-less,
measured 9.19 HTTP/action against the before-run's 11.88 — same transport, same
sequences, 35 minutes apart, 29% apart in cost. The cookie-less regime was not
just expensive, it was high-variance, which is what made it look like weather.

**What this does not claim.** One paired sweep per transport. The amplification
effect rests on the zero-cost probes (20/20 vs 0/20 first-attempt RESETs, plus
8/8 cross-game); the paired canary's job was the behaviour-preservation gate and
that is what it should be cited for. Nothing here says how the API behaves under
concurrency, or whether the documented 600 rpm limit binds once retries stop
dominating traffic.

## 7 · Canary replay — built

Theoria.md asks for a fixed sequence per game, re-run periodically against stored
hashes, with drift treated as an incident that freezes campaigns. Built as
[`canary.py`](canary.py); the spec and expectations are
[`data/canary.json`](data/canary.json), replay history is
`data/canary_runs.jsonl`, the gate is `data/campaign_freeze.json`.

16 actions buys a full sweep of the development pile. Baseline confirmed
2026-07-28: 4/4 PASS.

## 8 · Frame caching and release licensing

Separate the three things that are usually conflated:

**Code — MIT.** `arcprize/ARC-AGI-3-Agents` and `arcprize/arc-agi` both ship a
standard MIT licence. MIT scopes itself to "the Software"; it does not reach the
game data.

**Game/task data — no licence is stated.** There is no Apache/CC/CC0 statement for
ARC-AGI-3 environment data or API-returned frames on the docs site, in the repo
licences, or in the competition rules. The games are server-side; there is no
published dataset with a licence attached. **Do not read the absence as
permissive.**

**What actually governs the data — the site terms** (`arcprize.org/terms`). Two
clauses bite:

* Users get a non-exclusive, revocable licence limited to personal or internal
  business use; republishing or publicly displaying Service content needs
  permission, with attribution if granted.
* Systematically retrieving data from the Services to compile a collection or
  database is prohibited without written permission. **A harvested corpus of
  64×64 frames is on its face such a compilation.**

The same terms also warrant that users will not access the Services by automated
means — boilerplate that contradicts the existence of a machine-facing benchmark
API. Record that as ambiguity, not as permission.

**The conclusions for Phase 4's release manifest:**

1. **Local caching for our own analysis**: not addressed by anything we found;
   proceed, but it is unaddressed rather than permitted.
2. **Publishing raw frames**: treat as **requiring written permission**
   (team@arcprize.org). No licence found grants it and the compilation clause
   arguably bars it.
3. **Publishing derived, non-reconstructive artifacts** — frame *hashes*, counts,
   metrics, the canary's expectation tables — sits on far safer ground and is
   what this repository actually needs. `data/canary.json` stores hashes, not
   frames, for this reason as well as size.
4. The ledger `data/recon_ledger.jsonl` **does** contain full response bodies,
   i.e. raw frames, and it is tracked. Before any public release it must be
   either redacted to hashes or covered by permission. **This is an open
   obligation, flagged here, not discharged by this ticket.**

Confidence is medium-low on this item and the reason is structural: no
ARC-AGI-3-specific API terms of service appears to exist, so a generic website
terms document is doing work it was not written for.

---

## What this ticket did not do

* **The cookie fix ~~is not applied~~ is applied, with the re-measurement
  attached** — see §6c. INC-007 recorded it as deferred and gave reasons; those
  reasons were satisfied rather than waived, because what they asked for was a
  before/after measurement on the instrument being changed, and that is what §6c
  is. INC-007a supersedes.
* **Other tracks' clients are untouched.** baseline-arms keeps its own HTTP
  client; the same cause and the same cure apply there, and it is notified via
  PARTNER_SYNC, but this track does not edit another track's code.
* **The ledger's raw frames are not redacted.** Flagged above as a release
  obligation. Cookie *values* were a second instance of the same class and have
  been redacted (INC-008) — that one was self-inflicted: the stickiness probe
  wrote raw `Set-Cookie` headers, including `GAMESESSION` bearer tokens, into
  the tracked ledger for 55 calls. Values replaced, names kept, git history
  still holds them at the pushed commit `29c631e`, which is an owner call.
* **`available_actions` reporting was not re-examined.** `data/precheck.json`
  records `null` for ar25 and sk48 because those runs were reconstructed from the
  ledger by `precheck_resume.py`, which does not carry the field. Cosmetic, but
  it means the report understates what is known.
* **No sealed game was contacted.** `contamination.py`'s ledger audit checks this
  over every call ever made, and it is a test (`test_hygiene.py`).
