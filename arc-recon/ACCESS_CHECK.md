# 一件接入核查 — the Phase 1 access check, item by item

[Theoria.md](../Theoria.md) Phase 1 lists the things that must be "逐项核实并入账"
before anything is built on the live API. This file is that ledger: one row per
item, what settled it, and what is still open. Nothing here is settled by reading
the docs alone where a measurement was possible, and nothing is settled by a
measurement where the docs contradict it — both are recorded when they disagree.

| # | Item | Status | Settled by |
|---|---|---|---|
| 1 | RESET semantics — full reset or level reset, hidden random source | **answered** | precheck, 4 games |
| 2 | Cross-session residue | **closed** — none, across four sessions; the question is now standing surveillance, not an open item | precheck ×2 + canary ×2 |
| 3 | Scorecard semantics — one card per game, in-card aggregation | **answered, with two traps** | baseline-arms measurement + official docs |
| 4 | Does one action return several frames | **answered** — yes, up to 113; and **adjudicated**: the batch is a render burst, not a tick → [`CASCADE_RULING.md`](CASCADE_RULING.md) | precheck + P-20 per-frame probe ([`cascade/`](cascade/)) + baseline-arms shards |
| 5 | Is `level` a response field | **answered** — yes | precheck |
| 6 | Rate limits and quota | **closed for the question Phase 1 asked** (the campaign fits: 432 rpm of 600, §6d) — with two named residuals: no 429 has ever been observed, and the backoff curve is unmeasured | official docs + `browser-ops/TERMS.md` + baseline-arms + this track's probe + the §6d budget |
| 7 | Canary replay | **standing** — built, baselined, and now on a daily schedule | [`canary.py`](canary.py), [`canary_schedule.py`](canary_schedule.py), [`data/canary.json`](data/canary.json) |
| 8 | Frame caching and release licensing | **closed, and less restrictive than we first read it** — caching is designed behaviour, our own numbers are explicitly publishable, ARC's raw content is not. **Permitted ≠ safe**: the cache upstream fills holds all 25 games' source, so §8b is the fail-closed guard over it | official terms + [`browser-ops/TERMS.md`](../browser-ops/TERMS.md) cross-check + [`local_engine_guard.py`](local_engine_guard.py) |

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
because every replay it makes adds another session at zero extra design cost —
and it now makes one a day without being asked (item 7a):

| replay | when | source |
|---|---|---|
| precheck run-a | 2026-07-27/28 | `data/precheck.json` |
| precheck run-b | 2026-07-27/28, separate session and scorecard | `data/precheck.json` |
| canary baseline | 2026-07-28T00:35Z, separate session and scorecard | `data/canary_runs.jsonl` |
| canary paired sweep ×2 | 2026-07-28T01:10Z / 01:11Z, one per transport | `data/canary_runs.jsonl` |
| first scheduled sweep | 2026-07-28T07:57Z, separate session and scorecard | `data/canary_runs.jsonl` |

All of them agree hash-for-hash on every step they share, across **six replays
spanning two days and two different HTTP transports**. A session leaves nothing
behind that a later session can see: same RESET state, same frames from the same
actions.

*(Corrected by S5: this sentence used to say "six replays in four sessions",
which was a leftover from the three-replay wording incremented instead of
recounted. The four canary sweeps alone opened four scorecards and 16 game
sessions — `data/canary_runs.jsonl` carries 16 distinct `guid`s, all unique —
and the precheck adds more. The replay count is right; "four sessions"
understated it by an order of magnitude.)*

Note what this does *not* say. It says the environment is reproducible, not that
it is stateless — the server clearly keeps per-session state (that is what the
`guid` and the `GAMESESSION` cookie are for). The claim is only that state does
not leak *between* sessions.

**Why this item is now closed rather than merely answered.** Five replays said
the same thing, and a sixth saying it again is not what changes the item's
status. What changes it is that the question has an owner: residue would show up
as a canary mismatch, the canary now runs daily (item 7), and a mismatch freezes
campaigns. "No residue" has stopped being a finding somebody has to remember to
re-check and become a property that is watched. If it ever stops being true, the
freeze file says so before the next campaign spends anything.

One boundary worth keeping in view: the canary would catch residue only where it
changes a frame the canary looks at. Residue confined to steps deeper than the
stored sequences, or to fields other than `frame`, is outside what any of this
measures — and that limit is a property of the instrument, not evidence about
the server.

**Three qualifications S5 added to the closure rationale, because "the question
has an owner" is doing a lot of work above and the owner is smaller than it
sounds.** The finding stands; the *surveillance* is thinner than the sentence
implies:

* **The watchdog is shallower than the evidence that answered the question.**
  The precheck compared 9 steps per game; the daily canary compares 6/3/6/5.
  Residue that first shows up on step 7 is outside the standing check.
* **Its discriminating power is 11 of 16, not 16** (INC-009), and on the daily
  `quick` profile **tn36 degrades to a RESET-only check** — for one of four
  games, daily residue surveillance is a single hash.
* **The schedule is not installed.** `canary_schedule.py install` prints a
  command; nothing has run it, and `schtasks` shows no task. As of this writing
  the "daily" canary has run on schedule **once** (2026-07-28T07:57Z). Installing
  it is an owner decision and deliberately not an agent's (§"What S2 did not
  do") — but until someone does, item 2 is closed on **six agreeing replays**,
  which is the honest basis, and not on a standing instrument.

One more, about the precheck half of the evidence: ar25's `run_a` (18:10:26 →
18:35:03) and `run_b` (18:12:14 → 18:14:59) **overlapped in wall clock** —
`run_b` is nested inside `run_a`. That pair tests concurrent session isolation,
which is a fine property to have, but it is not the sequential "a later session
sees nothing of an earlier one" that the item asks about. The canary sweeps,
which are genuinely sequential, are what carry that claim.

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

## 4 · Cascade semantics — adjudicated, and not the way this section first read it

**The ruling is [`CASCADE_RULING.md`](CASCADE_RULING.md)** (S5, 2026-07-28).
Cite that; this section is the access-check row, not the adjudication.

Settled observationally, not from documentation: `frame` is always a list, and a
single command can return many. The largest batch on disk is **113 frames** (one
`g50t` `ACTION5` in `baseline-arms/out/shards/ledger.g50t.jsonl`), carrying
**10 distinct** states. Batch length is a function of *(state, action)*, not of
the game: `ar25` and `tn36` have never returned more than 1 frame across ~790
responses; `sk48`'s keyboard actions return 2 (58 of 265 returned 1); `g50t`
ranges over `{1, 7, 9, 13, 15, 17, 21, 25, 29, 32, 35, 37, 41, 49, 113}`.

~~The environment has an internal tick, so `step` must be modelled as
`action → frame sequence`. This is the answer Theoria.md Phase 1 wanted before
freezing the shape of `step`.~~ **Withdrawn.** That was an inference from the
frame count, not a measurement, and Theoria.md:299 does not license it — it
names **动画/内部 tick** as two candidate causes of one observation and says the
API answer settles only half the item. Read as the whole answer, it put a claim
about the world's *rules* on evidence about the API's *response shape*, and
INC-002a has been carrying it as "settled" ever since.

What the frames actually show — plateaus quantised at exactly 4, constant
12-cell increments, and an `sk48` intermediate frame that is never a state the
world rests in — is a render burst, not a rule set re-firing to quiescence. So
**`step` is frozen as `S → A → S` on `frames[-1]`**, and `cascade` is
`single_frame` for the development pile, with a named refutation condition.
Evidence, argument and the obligations it places on both tracks are in the
ruling; the per-frame probe it rests on is tracked here in
[`cascade/`](cascade/) and re-verifies with `bash cascade/verify.sh`.

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

**Corroboration this section did not use.** The no-quota finding above rests on
absence from the documentation. `browser-ops/TERMS.md:355-378` gets there from
the product side: the logged-in panel has **no quota, no usage, no rate display
and no billing** — "**不是『配额藏在别处』,是产品里就没有配额这个概念**". Two
independent layers, and the second is positive evidence rather than silence.
The claim above that this "stays an assumption rather than a finding" was
written before that read existed; it is now a finding, though still one about
what is *documented and shown*, not about what the server enforces.

**The archiving conclusion, which is not the one we expected.** The campaign
budget arithmetic Theoria.md asks for — 三臂 × 局数 × 回合 + 戳探 + 前缀重放 —
was framed around an action quota that "可能先于 token 成为瓶颈". On the evidence
there is no documented action quota to bust. What is documented is a **rate**
limit, and rate is a constraint on *concurrency and retry storms*, not on total
volume. Restated for planners:

* A single-process arm cannot approach 600 rpm; it spends most of its wall clock
  waiting on the model. *(Stands — measured at 11 rpm in §6d.)*
* ~~Concurrent campaigns plus retry storms can. Four processes each retrying at
  the precheck's envelope (40 attempts, backoff capped at 5 s) is the shape that
  gets near the limit~~, and INC-BA-003 is a live instance of exactly that
  arrangement arising by accident between two sessions that could not see each
  other. **The first clause is wrong and §6d does the arithmetic that shows it:
  the retry envelope is the *slowest* shape this project runs, because its own
  backoff is a rate limiter. Four storming processes reach 64 rpm — 9.4× inside
  the limit. It takes 38 of them to breach.** INC-BA-003 was a real incident
  about a real hazard; the hazard was the *bill*, not the rate limit.
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

**How much of that is load-bearing (INC-009).** Only **11 of the 16** expected
ACTION hashes differ from their game's RESET hash. `tn36`'s four actions are
accepted no-ops whose frame never changes, and `g50t`'s ACTION1 expects
`801726dc499f3f52` — the exact hash `precheck.py` names as the counterfeit
fingerprint. On those five steps a counterfeit response would match as well as a
genuine one, so they discriminate nothing. The claim rests on the 11 that do
(plus the four RESET hashes, which are real state): ar25 5/5, sk48 5/5, g50t 1/2,
tn36 0/4. Still solid — three games, both frame-cascade shapes — but it is 11,
not 16.

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

### 6d · The budget, finally done — in the unit that exists (S5)

§6 concluded that a volume budget has nothing to bust and stopped. That is right
about volume and was wrong to stop, because Theoria.md:299's obligation survives
the change of unit — 「必须落在限额内」 just becomes a different sum. This is
that sum. It is executable: [`rate_budget.py`](rate_budget.py), inputs declared
in [`data/rate_budget.json`](data/rate_budget.json), run by `verify.sh`.

A rate limit is charged against **requests in any 60-second window**, so the
budget is not total ÷ duration — an average is exactly the statistic a rate
limit ignores. The peak is `concurrency × how fast one process can issue`, and
the second term is set by what the process does *between* requests.

| scenario | Theoria term | shape | conc | peak rpm | headroom | breaches at |
|---|---|---|---|---|---|---|
| `phase3-s1` | 三臂×局数×回合 | LLM arm | 4 | 44 | 13.6× | 55 procs |
| `phase3-s2` | same, 2× actions | LLM arm | 4 | 44 | 13.6× | 55 procs |
| **`probe-and-replay`** | **戳探 + 前缀重放传送** | scripted | 4 | **432** | **1.4×** | **6 procs** |
| `canary-daily` | (the standing spender) | scripted | 1 | 108 | 5.6× | 6 procs |
| `inc-ba-003` | the collision that happened | retry storm | 4 | 64 | 9.4× | 38 procs |

**Verdict: the plan of record fits, at 432 rpm of 600 — but not comfortably, and
not where anyone was looking.** Two results, both the opposite of what §6 said:

**1. Retry storms are the safest shape, not the most dangerous.** The envelope's
own backoff is a rate limiter: 40 attempts spread over ~173 s cannot exceed
~16 rpm however hard it tries. It takes 38 concurrent storming processes to
breach. INC-BA-003's four never came close.

**2. The dangerous shape is the fast, healthy, think-free one** — a scripted
prefix replay issuing back-to-back at transport speed, bounded only by the
fastest round-trip ever measured (0.558 s, over 1,231 ledger entries). That is
**108 rpm per process**, and it breaches at **6**. Which is to say: the risky
term is precisely 前缀重放传送, the one Theoria.md:299 named and nobody costed.
Fixing the cookie amplification (INC-007a) cut HTTP volume ~9× and, by removing
the waiting, raised the achievable *rate* — the same change moved the two
budgets in opposite directions.

**The operating constraint that falls out, and it is the deliverable of this
section: cap concurrent think-free replay at 5 processes.** Model-paced arms are
not the thing to count; a replay, a reconstruction pass or a probe sweep is.

**What this is not.** A bound from a documented number is not a calibration.
**Zero 429s have ever been observed** — 0 across 3,736 logged requests
(`data/recon_ledger.jsonl` 1,231, `baseline-arms/ledger.jsonl` 560,
`baseline-arms/probe_log.jsonl` 1,945). The gate has never been seen to close.
Two residuals follow, and both are open:

* **The backoff curve after a 429 is unmeasured and undocumented.** The docs say
  "exponential"; [`precheck.py`](precheck.py) implements a *linear* ramp capped
  at 5 s. Nothing has ever tested it against a real 429, and neither
  `client.py` nor `canary.py` handles 429 at all — only `precheck.send_command`
  treats it as retryable. `browser-ops/TERMS.md:236` lists this as needing a
  letter to ARC.
* **Rate had never been measured, only bounded.** The canary recorded HTTP
  volume and no wall clock, so its four sweeps carry no rate at all. S5 added
  `elapsed_s` / `observed_rpm` to the replay record; from the next sweep on,
  every canary run is a free observation of the quantity the limit is charged
  against. `python rate_budget.py --observed` reads them back and reports the
  pre-S5 sweeps as unmeasured rather than back-filling a guess.

## 7 · Canary replay — built, and now standing

Theoria.md asks for a fixed sequence per game, re-run **periodically** against
stored hashes, with drift treated as an incident that freezes campaigns. The
check is [`canary.py`](canary.py); the spec and expectations are
[`data/canary.json`](data/canary.json), replay history is
`data/canary_runs.jsonl`, the gate is `data/campaign_freeze.json`.

16 actions buys a full sweep of the development pile. Baseline confirmed
2026-07-28: 4/4 PASS.

### 7a · 定期 — the word the first build did not implement

A baseline taken once is a photograph. [`canary_schedule.py`](canary_schedule.py)
is the clock: cadence in the tracked, human-editable
[`data/canary_schedule.json`](data/canary_schedule.json), state in
`data/canary_schedule_state.json`, and a free `due` check so a 5-minute
automation can ask the cheap question 288 times a day and buy the expensive
answer once.

**The daily sweep costs 12 actions and gives up nothing.** INC-009 established
that only 11 of the full sweep's 16 expected ACTION hashes can discriminate at
all — the other five either repeat their own game's RESET hash or land on the
counterfeit fingerprint `801726dc499f3f52`, so a forged response would satisfy
them exactly as well as a genuine one. `plan_profile` derives, from
`canary.json` at run time, the cheapest plan that still funds every
discriminating step:

| profile | cadence | actions | discriminating steps | RESET checks |
|---|---|---|---|---|
| `quick` | daily | 12 | **11 / 11** | 4 / 4 |
| `full` | weekly | 16 | 11 / 11 | 4 / 4 |

The 4 actions `quick` drops are tn36's, which are accepted no-ops whose frame
never changes; the game stays in the sweep as a **RESET-only check**, because
RESET is a command rather than an action (§6b) and therefore costs nothing. The
weekly `full` sweep exists to buy those four back: they cannot catch a forgery,
but their invariance is a real property of the environment, and a canary that
never looked at it would not notice if those actions started doing something.

The plan is *derived*, not written down. A re-baseline that changes which steps
discriminate changes the plan on the next run, so the schedule cannot quietly
end up pointing at the wrong prefix — the failure mode a hardcoded game list
would have.

**One new failure mode, which the one-off canary did not have.** INCOMPLETE is
deliberately neither a pass nor drift: an outage must not be able to halt the
programme, and must not be able to hide drift either. Run on a schedule, that
verdict acquires a shape of its own — a canary that is INCOMPLETE every day has
stopped measuring, silently, while its log fills with entries. Consecutive
INCOMPLETE runs are therefore counted, and at `blind_after` (3) the module files
a `process`-severity incident saying so. It does **not** freeze campaigns: being
unable to look is not evidence that anything changed. It refuses only to let the
silence go unrecorded.

**First scheduled sweep, 2026-07-28T07:57Z**: 4/4 PASS, 12 actions, 16 HTTP
calls for 16 commands — 1.00 attempt per command, every step first-attempt, the
post-INC-007 figure reproduced in a fourth session.

Exit codes are the interface the scheduler reads: `0` PASS, `1` DRIFT (incident
filed, campaigns frozen), `2` refused on safety grounds, `3` nothing to do,
`4` INCOMPLETE, `5` gated (frozen, or the shared spend gate refused).

**Where it should be installed, and where it should not.** `canary_schedule.py
install` prints a daily Windows scheduled task. It deliberately does not belong
in `monitor/reflex.py`, which runs every 5 minutes: the reflex layer is for work
that costs nothing, and a canary on that cadence would spend 3,456 actions a day
to answer a question that changes on the scale of an operator deploying a new
build. The reflex may call `due` — that is free — and let it decide.

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

**The conclusions for Phase 4's release manifest** (as first written; §8a
supersedes 1 and adds a category to 3):

1. ~~**Local caching for our own analysis**: not addressed by anything we found;
   proceed, but it is unaddressed rather than permitted.~~ **Addressed and
   permitted** — see §8a.1.
2. **Publishing raw frames**: treat as **requiring written permission**
   (team@arcprize.org). No licence found grants it and the compilation clause
   arguably bars it. *(Stands. §8a.2 narrows what counts as "raw frames".)*
3. **Publishing derived, non-reconstructive artifacts** — frame *hashes*, counts,
   metrics, the canary's expectation tables — sits on far safer ground and is
   what this repository actually needs. `data/canary.json` stores hashes, not
   frames, for this reason as well as size. *(Stands, and §8a.2 upgrades it from
   "safer ground" to explicitly permitted, with three disclosure obligations.)*
4. The ledger `data/recon_ledger.jsonl` **does** contain full response bodies,
   i.e. raw frames, and it is tracked. Before any public release it must be
   either redacted to hashes or covered by permission. **This is an open
   obligation, flagged here, not discharged by this ticket.** *(Stands, and
   §8a.3 sharpens why.)* **S5 enlarged it**: salvaging P-20 added
   `cascade/runs/*/ledger.*.jsonl` (~1.0 MB of raw frames) to the tracked set.
   That was a deliberate trade — `cascade/verify.py`'s load-bearing assertion
   recomputes the frame hashes from those bodies, so dropping them would have
   left a summary that only agrees with itself — but it is the same obligation
   in a second file, and the release redaction must cover both paths, not just
   `data/`.

~~Confidence is medium-low on this item and the reason is structural: no
ARC-AGI-3-specific API terms of service appears to exist, so a generic website
terms document is doing work it was not written for.~~ **The document this
sentence said did not exist does exist** — see §8a.

### 8a · Cross-checked against the official-side excerpts, and the reading loosens

[`browser-ops/TERMS.md`](../browser-ops/TERMS.md) is an independent read of the
same terms from the browser side, with the original sentences quoted and each
one's URL attached. Cross-checking it against the above moves three of the four
conclusions, all in the same direction — **we had read the terms more
restrictively than they are written.**

**1. Local caching is not merely unaddressed; it is the officially documented
design.** The Kaggle starter's own troubleshooting text says games "are cached in
`environment_files/` and you're fully offline", and the local-vs-online page
advertises unlimited local instances with no key. Conclusion 1 was written from
the absence of a statement; the statement exists and is permissive.
**One line: caching ARC data locally for our own analysis is permitted, and no
permission needs to be sought for it.**

**And one line immediately after it, because that sentence is about permission
and says nothing about contents: the cache is permitted; what upstream puts in
it is not.** First run downloads *the game source* for all 25 games, and both
`make play-local` and the swarm runner's `--game` default to every game in the
dataset (`browser-ops/TERMS.md` §4.2). By INC-BA-001's own yardstick source
ranks a notch *worse* than trajectories — it hands over the finished answer to
the mechanics rather than an example of it. So the licensing conclusion above is
correct and must not be read as a green light to enable local mode: **permission
is not containment**, and the containment half is [§8b](#8b--the-containment-half-permitted-is-not-safe), which is
executable rather than advisory.

**2. Our own measurements are explicitly publishable; ARC's content is not.**
The decisive document is not the site terms at all — it is the *ARC Prize
Verified Official Testing Policy* (`arcprize.org/policy`), which §8 could not
have weighed because it did not find it: it is linked only from the page footer.
It says, in terms, "You are also free to test on public data and share your
scores independently. Please state clearly the data you tested on, how you
tested, and that your results are not verified by ARC Prize."

That splits the release manifest in two, and the split has to be explicit in the
manifest itself or the permissive half will be read as covering the other:

| what is being released | governed by | verdict |
|---|---|---|
| our scores, metrics, hashes, methods, conclusions | Testing Policy | **permitted**, subject to three disclosures: what data, how tested, not ARC-verified |
| ARC's frames, trajectories, game source, task statements | ToS §2 / §4 | **written permission required** (team@arcprize.org), with attribution if granted |

The Testing Policy's enforcement clauses aim at *submissions* — results
targeting the leaderboard — and its whole frame presumes automated agents are
the normal way to play. That is a specific, recent, ARC-authored document
sitting over a generic 2024 website template, which is what the medium-low
confidence above was hedging against. **The hedge is discharged for the release
question.** It is not discharged for the automation question: ToS §3(3) still
bars "automated or non-human means" in words, and only a written answer from ARC
settles that. The risk there is account termination, which is irreversible, so it
stays open — see §5 of `browser-ops/TERMS.md` for the letter that has not been
sent.

**3. The ledger obligation survives the loosening, and gets sharper.** Nothing
above helps `data/recon_ledger.jsonl`: it holds full response bodies, which are
ARC's content, and ToS §4's first prohibited activity names by description
exactly what it is — data systematically retrieved from the Services to compile
a database. Internal analysis of it is squarely inside §2's "internal business
purpose". **Publishing it is the line, and `redact_ledger.py` is the way over
it.** Note that the first scheduled canary sweep appended 16 more raw response
bodies to that file, so the obligation grows slightly with every replay — which
is an argument for redacting at release time rather than trying to keep the
ledger clean as it goes, since the ledger's completeness is what makes it
evidence at all.

**A disagreement worth recording, since both sides are ours.** §8 above says of
game data that "no licence is stated" and warns against reading absence as
permission. `browser-ops/TERMS.md` reaches the same place from the other
direction — it finds the statement, and the statement is a prohibition. The two
readings agree; what changed is that the second one found the ARC-specific
document, and that document turned out to *grant* the thing this repository
actually needs to publish. Both are kept: the caution was correct given what §8
had read, and it was more caution than the full record requires.

### 8b · The containment half — "permitted" is not "safe"

§8a settled the *licensing* question and settled it correctly. This subsection
exists because the finding it came from had two directions and only one of them
had a box to be filed in: item 8's title is "licensing", so the sealed-pile half
had nowhere to go and, for a while, went nowhere. **A finding cut along a
document's section headings loses the half that does not match a heading.**

What upstream does by default, quoted in `browser-ops/TERMS.md` §4.2 with URLs:

| documented behaviour | what it means for the cut |
|---|---|
| first run will "download the game source", cached in `environment_files/` | all 25 games' **source** lands on disk, 21 of them sealed |
| `make list-games` — "Print every game id available" | enumerates all 25; takes no filter |
| `make play-local` — "Runs your agent against every game in the dataset" | plays all 25 |
| `make verify-local` — "30-second smoke test on two games" | the docs do not say which two |
| swarm `--game` — "If not specified, the agent plays all available games" | silence means all 25 |

So the first thing done on the strength of "permitted, no permission needed"
pulls every sealed game's source down and, by default, plays every one of them.
That is not a licensing risk; it is the whole confirmation set, and it is not
recoverable. Note also that **none of it produces an API call**: a local run
never enters `data/recon_ledger.jsonl`, so `contamination.py`'s audit — which
audits every call we have ever made — stays green through the entire event. The
existing instruments are structurally blind here, which is why the guard had to
be new code rather than another assertion in an existing one.

**The rule.** Any path that pulls `environment_files/`, or invokes
`make list-games` / `make play-local` / `make verify-local` / the swarm runner,
must first filter to the four development-pile games named in
`data/piles.json`. **An unfiltered invocation is refused, with an error, in
code** — not warned about in a document.

**The guard.** [`local_engine_guard.py`](local_engine_guard.py), tested by
[`test_local_engine_guard.py`](test_local_engine_guard.py) and wired into
`verify.sh`. It is a positive whitelist that defaults to deny, in the shape
`baseline-arms/SCHEMA_PATH_A.md` §3 settled on and for the reason it gives: a
negative list meets an unforeseen path shape and fails *open*, and failing open
here cannot be undone.

```bash
python local_engine_guard.py check -- make play-local                    # exit 2
python local_engine_guard.py check -- uv run main.py --agent=x           # exit 2
python local_engine_guard.py check -- uv run main.py --agent=x --game=ar25   # exit 0
python local_engine_guard.py run   -- <argv...>   # vets, then execs only if allowed
python local_engine_guard.py scan  environment_files/   # names-only sweep of a cache
```

Five refusals, one permission:

1. `deny_default_all` — a game-playing or game-pulling command with no `--game`
   selector. Silence is the dangerous case upstream, so it is the refused case here.
2. `deny_sealed` — any of the 21 named anywhere on the line, by full id or by
   4-character prefix, case-insensitively, tested *before* the allow branch so a
   line naming both piles reads as sealed.
3. `deny_unknown` — a selector token that is not exactly a development-pile id
   or its exact prefix. Upstream treats the value as an ID *prefix*, so
   `--game=s` would widen to `sk48` **and** five sealed games; only the two
   exact forms pass. A flag carrying an *empty* value is refused here too:
   with last-wins semantics `--game=ar25 --game=` is no filter at all, wearing
   the costume of a filtered run.
4. `deny_unfiltered` — `make play-local`, `make list-games` and
   `make verify-local`. **No filter argument is documented for any of them** —
   `--game` is documented only for the swarm runner (see the correction below).
5. Refuse-everything if `data/piles.json` is absent, malformed, or no longer
   hashes to the value `CLAUDE.md` pins. A guard that cannot read the cut does
   not know what it is guarding.

Three properties worth stating because they are what the tests are about. The
prefix match is **boundary-anchored on both sides**, so `blobs/9ar25f0e/` does
not read as `ar25` — the exact failure `SCHEMA_PATH_A.md` §3.1 found the hard
way. Each shell **segment is judged alone** (split on `&&`, `||`, `;`, `|`, `&`,
newline, `#`) and the most severe verdict wins, because one dev-pile token must
not license the other statements sharing the line. And `scan` **opens nothing**:
it is a sieve over file *and directory* names, and there is a test that fails if
any file under the swept directory is opened. Downloading is not reading; a
guard that quoted the file it was refusing would be the leak.

#### 8b.1 · What an adversarial pass found, and the one correction that matters

The first version of this guard was attacked by a reviewer briefed to break it,
and it found **nine working bypasses**. Each is now a named regression test in
`test_local_engine_guard.py`. The sealed-name matcher held — every hole was in
the *reach* of the trigger list, in argv flattening, or in Python truthiness.
Two are worth writing down here rather than only in the tests:

**`make play-local GAME=ar25` was this document's own worked example, and it was
wrong.** `GAME=` is a spelling *we invented*. The only evidence we hold —
`browser-ops/TERMS.md` §4.2, quoting the docs with URLs — documents `--game` for
the **swarm runner** and documents `make play-local` as "Runs your agent against
every game in the dataset" **with no argument at all**. GNU make accepts an
unreferenced variable override in silence, so if the Makefile does not consume
`GAME`, that command plays all 25 while looking filtered, and **looking filtered
is worse than looking dangerous**: it is the form somebody copies. The same
reasoning that refuses `verify-local` for an unnamed pair condemns `play-local`
for an unverified variable, so `play-local` moved into the refused set. It can
come back out when the Makefile is in the tree and shown to honour a named
variable — not before.

**`assert_local_pull_allowed` failed open on a generator.** `if not game_ids` is
false for any generator object, so `(g for g in cfg if want(g))` — the
bracket-less twin of a safe list comprehension — skipped the "name your four
games" refusal, returned an empty allowlist, and left the caller pulling
unfiltered. Nothing at the call site looked wrong. It now materialises the
sequence before testing it.

The generalisable lesson: the design attention had gone to the sealed-name
matcher, and that is the part that held. The failures were all in the plumbing
around it.



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

---

## What S2 (the scheduling ticket) did not do

* **Nothing is installed.** `canary_schedule.py install` *prints* a scheduled-task
  command; it does not run `schtasks`. Putting a standing, spending task on this
  machine is an owner decision, and an agent in a temporary worktree is the
  wrong thing to make it: the path it would register is the worktree's, which
  disappears. Install from the main checkout.
* **~~The shared spend gate is not on this path yet~~ — it landed.**
  `proxy/spend_gate.py` is on master as of `ae82ede` (S3), so `open_spend_gate`
  now imports it and reserves rather than writing `spend_gate: "absent"`. No
  flag, no opt-out; any refusal from it stops the sweep, and there is a test for
  that. What is still *not* done is the reverse direction: the gate does not
  know the canary exists, so a campaign's headroom calculation will not
  anticipate 12 actions a day. §6d includes the canary as a budget row for the
  same reason — a rate budget that omits the one recurring spender repeats the
  omission in a second place.
* **The blindness threshold is a guess.** `blind_after: 3` says "three days of
  not being able to look is long enough to be worth an incident". Nothing
  measured that; it is in the config file so it can be argued with in a diff.
* **The canary still only watches what its sequences reach.** Drift deeper in a
  level, or in response fields other than `frame`, is outside the instrument.
  Lengthening the sequences would cost actions daily, which is exactly the
  trade the profiles exist to make explicit.
* **`available_actions` is still not re-examined**, and the raw frames in
  `data/recon_ledger.jsonl` are still unredacted — both inherited, both
  unchanged, and the ledger one now grows by 16 bodies per sweep (§8a.3).
