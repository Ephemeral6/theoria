# arc-recon — API access check and the pile cut

Phase 1's first two steps, and nothing beyond them. This directory holds the
read-only instrument used to survey the ARC-AGI-3 API, and the knife that splits
the public set before any game is touched.

It is **not** the Phase 1 environment proxy. That proxy — the one all three arms
point at, which makes "arms never see the credential" a physical fact rather than
a promise — is a separate build.

## Credential

Read from the gitignored `.env` at the repo root as `ARC_API_KEY`, sent only in
the `X-API-Key` header, and redacted in every ledger entry. It is never printed,
never written to disk, and appears in no tracked file. See the root
[CLAUDE.md](../CLAUDE.md).

## Run

```bash
cd arc-recon && python recon.py      # read-only survey; burns no action quota
cd arc-recon && python cut_piles.py  # the pile cut; refuses to run twice
cd arc-recon && python precheck.py   # determinism precheck, dev pile only; SPENDS ACTIONS
cd arc-recon && python precheck_resume.py reconstruct   # rebuild runs from the ledger, no API calls
```

```bash
cd arc-recon && python canary.py status          # offline: spec, last replay, freeze state
cd arc-recon && python canary.py replay          # the drift check; 16 actions for the whole dev pile
cd arc-recon && python canary.py check-freeze    # exit 1 if campaigns are frozen
cd arc-recon && python canary_schedule.py status    # offline: cadence, plans, last outcomes
cd arc-recon && python canary_schedule.py due       # offline, free: exit 0 = a sweep is due
cd arc-recon && python canary_schedule.py run       # the daily sweep; 12 actions, SPENDS THEM
cd arc-recon && python canary_schedule.py run --dry-run   # plan and gate, spend nothing
cd arc-recon && python canary_schedule.py install   # prints the scheduled-task command
cd arc-recon && python contamination.py --json   # register, sealed claim set, ledger audit
cd arc-recon && python probe_stickiness.py       # cookie A/B; zero actions
cd arc-recon && python probe_stickiness.py --cross-game   # one jar, all 4 games
cd arc-recon && python redact_ledger.py          # INC-008 check; --apply to redact
cd arc-recon && python -m pytest                 # 111 offline tests, no API, no network
```

The access check itself — every Phase 1 item, what settled it, what is still
open — is [ACCESS_CHECK.md](ACCESS_CHECK.md).

## What the survey found

| Question | Answer |
|---|---|
| base URL / auth | `https://three.arcprize.org`, header `X-API-Key` |
| public set size | **25 games** |
| per-game fields | `game_id`, `title`, `tags`, `baseline_actions` |
| tag families | `keyboard_click` 13, `click` 7, `keyboard` 4, untagged 1 |
| version fingerprint | every `game_id` carries a version suffix (e.g. `ar25-0c556536`) |
| baseline actions | 17,135 across the public set; `len(baseline_actions)` = level count |
| scorecard open | `POST /api/scorecard/open` returns a `card_id` |
| scorecard retrieve/close | **404 on a card with no plays** — the card only materialises once a game is played against it |

## What one RESET on the development pile settled

A single `POST /api/cmd/RESET {game_id, card_id}` on `g50t-5849a774` answered four
open access-check questions:

| Question | Answer |
|---|---|
| **cascade semantics** — one frame per action, or several? | `frame` is a **list of frames** (length 1 on RESET, each 64x64). ⚠️ **The rest of this cell was an inference and has been superseded** — see [`CASCADE_RULING.md`](CASCADE_RULING.md). It read the frame *list* as a statement about the world's *rules*; the batch is a render burst, and `step` is frozen as `S → A → frames[-1]`. Kept rather than rewritten because the mis-reading is the finding: the observation was right and the conclusion drawn from it was not, for three days. |
| **is `level` a response field?** | **Yes** — `levels_completed` and `win_levels`. No need to infer it from score jumps. Cross-check: `win_levels` 7 == `len(baseline_actions)` 7 in the catalogue. |
| session handle | RESET returns a `guid` |
| action space | `available_actions: [1,2,3,4,5]` — no ACTION6 for this `keyboard`-tagged game, matching its tag |

Other fields: `state` (`NOT_FINISHED`), `full_reset` (false — RESET did a level
reset), `action_input`.

## INC-001 / INC-002 — REVERSED (INC-001b, INC-002a). The API works; retry is the key

Both blocking incidents recorded below stand in the ledger as history, but their
diagnoses are **overturned**. The baseline-arms track found the crack first
(its independent re-verification, PARTNER_SYNC 2026-07-28): the same request
that returns `400 game <id> not found` succeeds on retry. arc-recon re-ran the
determinism precheck under that policy and **all four development-pile games
now hold a verdict**:

| game | verdict | steps | notes |
|---|---|---|---|
| `ar25-0c556536` | **PASS** | 9/9 | 1 frame per action |
| `g50t-5849a774` | **PASS** | 3/3 | ACTION2 returns **7 frames** — cascade semantics is real; shortened sequence, see INC-005 |
| `sk48-d8078629` | **PASS** | 9/9 | **2 frames per action**, every action |
| `tn36-ef4dde99` | **PASS** | 9/9 | shallow: see the caveat below |

Full data: `data/precheck.json`; every HTTP exchange: `data/recon_ledger.jsonl`.

**The corrected model of the fault.** `400 "game <id> not found"` is transient.
Unavailability arrives in **waves of roughly 1–3 minutes** (most likely a
multi-instance backend where only some replicas hold the game/session); a retry
envelope has to outlast a wave, not just beat the per-attempt odds. The
precheck now retries up to 40 attempts with backoff capped at 5 s, full id
only, and treats only `400 … not found` / 429 / transport errors as retryable.
Cost: **2.5–10× HTTP calls per executed action** (baseline-arms measured 5.07×
with a smaller envelope). This amplification must enter every quota
extrapolation.

> **This model is superseded — see INC-007 / INC-007a below.** The retry policy
> works and the verdicts above stand, but "waves of unavailability" is not what
> was happening: the client kept no cookie jar, so it was routed to a different
> replica on every call. With a jar, the same 20-command sweep costs 20 HTTP
> calls instead of 190 and never retries once. The amplification was ours.

**Short ids are banned from requests (INC-005).** `ACTION` with a short id
(`sk48` instead of `sk48-d8078629`) can return 200 — but every such 200 in our
ledger carried the *pristine initial frame* regardless of session progress
(6 of 6 on g50t; corroborated by a 200 for the nonexistent `ACTION7` in
baseline-arms' log). A short-id 200 is served from something that is not the
live session. The version suffix is the environment version fingerprint, so
requests always carry the full id; the short↔full mapping the operators need is
recorded in `data/precheck.json` (`id_map`) and in every ledger request body:

`ar25 ↔ ar25-0c556536 · g50t ↔ g50t-5849a774 · sk48 ↔ sk48-d8078629 · tn36 ↔ tn36-ef4dde99`

**tn36 caveat — ~~gameplay-blocked~~ RESOLVED 2026-07-28, and the diagnosis was
wrong.** Its advertised action space is `[6]` only, and `ACTION6` returned
**500 on every attempt** — 128 times with `data:{x,y}`, 200 times with no
coordinates at all. This file concluded "the game's nominal action is broken
server-side". It is not. **The coordinates go at the top level of the request
body, not nested in `data`:**

| request body | result | source |
|---|---|---|
| `{game_id, card_id, guid, data:{x,y}}` | **500** ×128 | baseline-arms `probe_log*.jsonl` |
| `{game_id, card_id, guid}` (no coordinates) | **500** ×200 | same, and reproduced once by P-20 |
| `{game_id, card_id, guid, x, y}` | **200** | P-20, 4 attempts, 4 successes |

The server wraps them itself: a 200's `action_input` echoes
`{"data":{"game_id":…,"x":32,"y":32},"id":6}`. P-20 turned the lucky response
into a checkable claim with predictions written to disk *before* the follow-up
run (`cascade/runs/…-p20-followup/predictions/`): a fresh session and fresh
scorecard clicking (32,32) reproduced frame hash `f24a3446b02c98c2`
**bit-identically**; (5,5) gave `6087981cba345849`, so the coordinates are
genuinely read rather than accepted and discarded; clicking (32,32) again from
the new state gave a third hash, consistent with the state having changed.

**So tn36 is playable and the whole `click` family has its request shape.**
What is *not* shown: `levels_completed` stayed 0, `state` stayed
`NOT_FINISHED`, `available_actions` stayed `[6]` throughout. Proven is "the
action is accepted, the coordinates are read, the world changes" — **not** "one
can win with it".

Worth keeping as a caution about this file's own reasoning: a 500 that
reproduces 328 times looks exactly like a broken server, and was written down
as one. It was a wrong request shape, and nothing distinguished the two until
somebody varied the shape instead of repeating it.

**Access-check items settled by the precheck runs**: cascade semantics —
multi-frame responses confirmed observationally (7-frame and 2-frame batches;
what they *mean* took a second instrument, see below); cross-session residue —
none on any of the four (identical RESET hashes, and g50t's re-check reproduced
the *previous day's* hashes exactly); `levels_completed` / `win_levels`
maintained throughout.

## The access check is closed — all eight items

`ACCESS_CHECK.md` is the ledger, one row per Theoria.md Phase 1 item. As of
2026-07-28 (S5) every row is answered or closed, and the two that were still
open are closed like this:

| # | Item | How it closed | Residuals, named |
|---|---|---|---|
| 4 | does one action return several frames | **yes — and adjudicated**: the batch is a **render burst, not an internal tick**. `step` is frozen `S → A → frames[-1]`; `cascade single_frame` for the four development worlds; `theory.pddl` needs **no** derived predicates. [`CASCADE_RULING.md`](CASCADE_RULING.md) | G-1 the tick criterion has never been run *directly*; G-2 every trace stopped at level 0; G-3 the largest batch has only been counted, never read cell by cell; G-4 see the provenance note below |
| 6 | rate limits and quota | **closed for the question Phase 1 asked** — the campaign fits, worst aggregate peak 432 rpm of 600 (`data/rate_budget.json`, `rate_budget.py`) | no 429 has ever been observed, so the backoff curve is unmeasured — the budget is built on a limit we have never touched |
| 2 | cross-session residue | **closed** — none across four sessions; now standing surveillance (daily canary) rather than an open question | — |
| 8 | frame caching and release licensing | **closed, and less restrictive than first read** — caching is designed behaviour, our own numbers are explicitly publishable, ARC's raw content is not | the salvaged P-20 raw ledgers are ARC content and join the §8 release-redaction obligation |

### Item 6, the other axis: rate is documented, action billing is only measured

S22 asked for the official wording and our measured convention to be put side by
side, because item 6 above closed the *rate* question and left a second one
unstated. They are different axes and only one of them has a source:

| | Official (ARC) | Ours (measured) |
|---|---|---|
| **Rate** | **600 requests per minute**, `429 RATE_LIMIT_EXCEEDED` on breach — `docs.arcprize.org/rate_limits`, quoted in [`../browser-ops/TERMS.md`](../browser-ops/TERMS.md) | worst aggregate peak 432 rpm of 600 (`data/rate_budget.json`) |
| **Action billing** | **nothing.** No published statement on whether a failed call consumes an action | scorecard `total_actions` **equals successful actions only**; failed 400s and retry amplification do not count — 19 samples, 3 model tiers, 4 games, 3 campaigns, no exception (`../baseline-arms/BUDGET_REPORT.md` §4.1, §12, §13) |

**The one line for the record: the rate ceiling is documented and we stay under
it; the action-billing rule is ours, not ARC's.** It is an inference from 19
consistent observations, and it decides budgets — the pessimistic reading it
displaced was 3.2× larger. Nothing has confirmed it and no non-destructive test
can, so it stays labelled as measured rather than promoted to known.

**Two qualifications the source states and the row above is too short to carry.**
Both are from `../baseline-arms/BUDGET_REPORT.md` §4.1, under its own heading
"what this does not answer and must not be said to answer":

1. The 19 samples are all **HTTP 400/500 — requests the server refused or
   failed before executing.** That is evidence that *rejected requests* are not
   billed. It is **not** evidence that a semantically wasted action is not
   billed: a click on empty space or a keypress with no effect returns 200,
   enters `actions_ok`, and is billed like any other. §4.1 says it outright —
   *"别把这条写成「ARC 不为失败动作计费」."* Read as that broader claim, the row
   above is false.
2. **The scorecard's count need not be the quota's count.** Everything measured
   here was read off the scorecard; whether ARC meters against the same ledger
   is unknown. Two books are possible and nothing here would tell them apart.

Neither qualification changes the budget we plan against, and both change what
happens when it is wrong: the failure would arrive as a quota exhausted earlier
than arithmetic predicted, not as an error naming this assumption.

The unmeasured residual named at item 6 is unchanged and belongs to the same
family: **no 429 has ever been observed**, so the backoff curve is built on a
limit never touched. Both are cases of a number we rely on and have not had
confirmed from the other side.

**The cascade item is worth reading for how it went wrong, not just how it came
out.** The observation — `frame` is a list — was correct on day one and is in
the table above. The conclusion drawn from it, "the world has an internal tick,
so `step` must be `action → frame sequence`", was an *inference* that rode the
observation's evidence for three days and reached `ACCESS_CHECK.md` §4 and this
file as though it had been measured. Theoria.md:299 had already named
**animation** and **internal tick** as two candidate causes of one observation;
the syllogism at Theoria.md:301 compressed them into one, and nobody re-opened
it until an instrument that could tell them apart existed. What separated them
was per-frame hashing plus the question "is an intermediate frame a state a rule
could fire *from*" — two different measurements of the same bytes.

**G-4 — the headline number "up to 113 frames" cites data that is not in git.**
`ACCESS_CHECK.md` §4 and `CASCADE_RULING.md` both quote a 113-frame batch. It
comes from `baseline-arms/out/shards/ledger.g50t.jsonl`, which is **untracked**
(`git ls-files` does not know it). What the tree can actually stand behind:

| source | tracked? | max frames in one response |
|---|---|---|
| `arc-recon/cascade/` (P-20, salvaged by S5) | **yes** | 17 (9 distinct) |
| `baseline-arms/out/shards/ledger.a7-g50t.jsonl` | **yes** | **29** |
| `baseline-arms/ledger.jsonl` | yes | 13 |
| `baseline-arms/out/shards/ledger.g50t.jsonl` | **no** | 113 |

The ruling does not turn on the maximum — it turns on *whether the frames within
a batch differ*, and every source above agrees they do. But a Phase 1 accounting
that quotes a number living only in an untracked file is `INC-AR-011` happening
a second time in the same document that records it. **The defensible tracked
maximum is 29.** Anyone citing 113 should commit the shard first or cite 29.

**The evidence nearly did not survive.** P-20's per-frame probe lived as an
untracked directory inside a worktree with no manifest; a `git worktree prune`
would have deleted the evidence for a Phase 1 gate item. It is now
[`cascade/`](cascade/), raw ledgers included, because
`cascade/verify.py` recomputes the frame hashes from the stored bodies — without
them the salvaged evidence would be a summary that agrees with itself.

```bash
cd arc-recon && bash cascade/verify.sh    # 27 steps, 4 games, 31 ledger entries, PASS
```

**Budget.** ≤20 executed ACTIONs per game (RESETs logged, not counted), spent
16 / 20 / 16 / 16 on ar25 / g50t / sk48 / tn36. A 10-minute harness timeout
killed one run mid-flight; both live sessions were resumed from the ledger
(`precheck_resume.py`) with zero lost state — the resumed steps' hashes match
the partner run exactly, which is itself determinism evidence across a
~20-minute gap.

~~The remaining open item for gameplay proper is the ACTION6 `data` shape, which
blocks tn36 and every `click`-family game.~~ **Closed 2026-07-28**: the
coordinates go at the **top level**, not in `data` — see the tn36 caveat above.
Rate limits and quota are now answered — see
[ACCESS_CHECK.md](ACCESS_CHECK.md) §6, and the correction below.

## 金丝雀重放 — the drift check

Theoria.md Phase 1 asks for more than a version suffix: a fixed action sequence
per game, replayed periodically against stored hashes, with drift treated as an
incident that freezes campaigns. That is [`canary.py`](canary.py).

The suffix in a `game_id` is the *declared* fingerprint — it changes when the
operators say the environment changed. The canary is the *observed* one, and it
catches the case the suffix cannot: the same id quietly behaving differently.
Everything built on a game assumes the environment it was measured on is the
environment still being played.

| game | sequence | actions | baseline |
|---|---|---|---|
| `ar25-0c556536` | ACTION 1,2,3,4,5 | 5 | PASS |
| `g50t-5849a774` | ACTION 1,2 | 2 | PASS |
| `sk48-d8078629` | ACTION 1,2,3,4,1 | 5 | PASS |
| `tn36-ef4dde99` | ACTION 1,2,3,4 | 4 | PASS |

16 actions buys a full sweep. The expectations were **not** taken from the
baseline run: they were derived offline from `precheck.json`, using only steps
that the precheck's two independent replays already agreed on, and the baseline
run then had to reproduce them. It did, 4/4, so the development pile now has
six agreeing replays across two days and four sessions — which is also the
strongest evidence on the cross-session-residue item.

Three properties are what make it a check rather than a ritual:

* **A failing run cannot rewrite what it is compared against.** `replay` can only
  fail; re-baselining is a separate command that demands a reason, files its own
  incident, and keeps the superseded hashes.
* **Drift is a file, not a log line.** A mismatch appends an incident *and*
  writes `data/campaign_freeze.json`. Any track can gate on it with
  `python canary.py check-freeze` (exit 1 = frozen) or by reading the JSON. It
  works across sessions and across tracks, which is exactly what INC-BA-003
  showed a per-process counter cannot do.
* **An outage is not drift, and cannot hide drift.** A replay that could not
  finish is `INCOMPLETE` — neither a pass nor a freeze. Only a mismatch with both
  hashes present freezes anything.

### 定期 — the schedule ([`canary_schedule.py`](canary_schedule.py))

A baseline taken once is a photograph. The cadence lives in the tracked
`data/canary_schedule.json`, the state in `data/canary_schedule_state.json`, and
`due` is free — so a 5-minute automation can ask the cheap question 288 times a
day and buy the expensive answer once.

| profile | cadence | actions | discriminating steps bought | what it adds |
|---|---|---|---|---|
| `quick` | daily | **12** | **11 / 11** | the whole drift-detection power of the full sweep |
| `full` | weekly | 16 | 11 / 11 | tn36's four no-ops, whose *invariance* nothing else watches |

The daily sweep is cheaper without being weaker. INC-009 showed only 11 of the
16 expected ACTION hashes can discriminate at all — the rest repeat their own
game's RESET hash or land on the counterfeit fingerprint, so a forged response
would satisfy them too. The plan is **derived from `canary.json` at run time**,
not hardcoded, so a re-baseline cannot leave the schedule pointing at the wrong
prefix. Games with nothing to discriminate stay in as a RESET-only check, which
costs nothing: RESET is a command, not an action.

**The failure mode a scheduled canary adds** is that INCOMPLETE stops being
rare. An outage is correctly not drift — but a canary that is INCOMPLETE every
day has stopped measuring while its log keeps filling. Three in a row files a
`process` incident saying exactly that. It does not freeze campaigns: being
unable to look is not evidence that anything changed.

Exit codes are the interface: `0` PASS · `1` DRIFT (incident + freeze) · `2`
refused on safety grounds · `3` nothing to do · `4` INCOMPLETE · `5` gated.

First scheduled sweep, 2026-07-28T07:57Z: **4/4 PASS, 12 actions, 16 HTTP calls
for 16 commands.**

This belongs in a daily scheduled task, **not** in `monitor/reflex.py`'s
5-minute loop — that cadence would spend 3,456 actions a day to watch something
that changes when an operator deploys a build. The reflex is welcome to call
`due`, which is free, and let it decide.

## INC-006 — F-11 ruled: the sealed claim set is 19, not 21

baseline-arms' INC-BA-001 reported nine sealed games whose mechanics were
partially disclosed to a search subagent's context while it was locating upstream
artifacts. Zero API contact; knowledge contamination only. F-11 ruled the
conservative merge, and this directory has now recorded it:

* all nine are registered in `data/contamination_log.jsonl` at the levels the
  subagent self-reported — **with one deliberate deviation**: `dc22-fdcac232` is
  rated 轻微 in that table, but INC-004 had already placed it at
  `design_document_disclosed`, so taking the rating at face value would have
  downgraded it. It keeps the stronger level;
* `ls20-9607627b` and `ft09-0d8bbf25` (material leaks) are
  **`quarantined_from_claims`** — no result on them counts as held-out evidence.
  (That is claim eligibility, not permission to play: rule 1 of the cut still
  bars every sealed game, and `assert_playable` refuses all 21);
* the other seven stay in the claim set and carry a **sensitivity-analysis
  obligation**: any statistic over the claim set must be reported a second time
  with them excluded, and the weaker figure governs. Note that `dc22` is the
  most exposed game *inside* the claim set, one level above the blurb-level
  rows — retaining it is what F-11 ruled, but calling that bucket "minor" is
  wrong, and INC-006a leaves the question open for the owner.

`data/claim_set.json` is derived from the log by
[`contamination.py`](contamination.py), so 21 → 19 is computed, not asserted.
Two things that file also makes executable rather than promised: `piles.json` is
re-hashed the way `cut_piles.py` produced it (still `3feca53e…41bbc19a`,
unmodified), and every track's call records are audited for a sealed game id in
a *request* — arc-recon's ledger and baseline-arms' `ledger.jsonl` and
`probe_log.jsonl`, **0 sealed games addressed across all three**. A sealed id in
a *response* is not a touch: `GET /api/games` returns all 25 by construction, and
scoring that as contact would make the audit incapable of ever coming back clean.

**That number used to be constructed rather than found (A13, 2026-07-29.)** The
reader extracted `url`, `request_body` and `response_body`; all 560 records of
`baseline-arms/ledger.jsonl` carry a top-level `game_id` and none of those three,
so nothing matched, nothing was flagged, and a file that existed and parsed
returned `clean: True`. "560 calls, sealed ADDRESSED: NONE" was printed over an
audit that had read nothing, and `claim_set.json` recorded it. Three things
changed, and the printed table now names the record shapes it read so the
difference is visible from the outside:

* every record is **classified** first -- `call`, `episode`, `summary` -- and one
  that matches no shape is `unreadable`, not clean. Not audited is not clean.
* the criterion lives in one module, [`sealed.py`](sealed.py), used by both this
  audit and `cascade/verify.py`'s A7. There were three implementations and they
  had drifted: A7 compared full ids only, so the bare stem `cascade/probe.py`
  writes into every scorecard's `tags` was invisible to it, and this file could
  not see it either because it only looked inside `request_body["game_id"]`.
  The criterion is now full id **or** whole-token stem, over the request body,
  the URL and the record's other fields alike.
* a sealed id found in a field neither half classifies counts as a **contact**,
  not a listing. The response carve-out above is earned by a specific argument
  about `GET /api/games`; no such argument exists for a field nobody has
  classified, so that case fails closed.

`arc-recon/verify.sh` now declares its negative sample
([`test_sealed_audit_negatives.py`](test_sealed_audit_negatives.py)), which
builds the records that used to walk through this gate -- an episode record
naming a sealed game, a bare stem in a request body, a misspelled quarantine
registration -- and requires each one to go red. Nothing there touches a sealed
game: the records are fabricated in a temp directory from ids read out of
`piles.json`.

The derivation fails **closed**. An unrecognised or missing `claims` value, or a
game registered at `mechanics_disclosed` or above that is not quarantined, lands
in `needs_adjudication` and is excluded from `clean` rather than falling into it.
The first version did fall into it, which an adversarial review caught and
INC-006a records.

A structural cost worth naming: `ft09-0d8bbf25` is the untagged singleton and the
only member of `sealed_only_families`. Quarantining it leaves the claim set with
no representative of the one tag family the development pile never shows us —
the exact property the cut was designed to preserve.

## INC-007 — the retry amplification was our own missing cookie jar

The API sets `AWSALB*` routing cookies (and a `GAMESESSION` cookie) that must be
echoed. `client.ArcClient` uses bare `urllib.request` and echoes nothing, so
every call is routed afresh. An interleaved A/B — two clients identical except
for a `http.cookiejar` — scored **20/20 first-attempt RESETs with the jar, 0/20
without**, across three runs and three games, with the arms placed on *different*
games and swapped between runs so neither could starve the other of a session.

So INC-001b's "unavailability arrives in waves" named the right suspect (a
multi-instance backend) and the wrong agent: what changes replica on every call
is us. The 40-attempt envelopes, the 2.5–10× amplification (this ticket's canary
measured **9.2×** — 147 HTTP calls for 16 actions) and a large share of both
tracks' wall-clock and dollar estimates are the price of that omission.

### INC-007a — applied, with the before/after the change deserved

Changing the transport is changing the instrument, so the fix landed with a
paired measurement rather than on its own: the same canary sweep, same sequences,
same stored hashes, run once on each transport ~80 seconds apart.

| | before (no jar) | after (jar) |
|---|---|---|
| verdicts | 4/4 PASS | 4/4 PASS |
| **HTTP calls for 16 actions** | **190** | **20** |
| retries | 170 wasted | **0** |

The sweep issues 20 commands (4 RESET + 16 ACTION). After the fix it cost 20 HTTP
calls — every step first-attempt, on all four games.

**The verdicts matter more than the speed.** Identical frame hashes across a
transport change means the fix is behaviour-preserving, and it retires a worse
possibility than slowness: that the cookie-less client had been talking to
something other than the live session all along — the exact shape of INC-005's
counterfeit short-id 200s. It was not. It was reaching the right session after
paying for nine wrong replicas first.

With one correction from INC-009: **11 of the 16** expected ACTION hashes
actually discriminate. tn36's four are accepted no-ops and g50t's ACTION1 expects
the pristine initial frame, so on those five a counterfeit would match too. The
claim rests on the 11 (ar25 5/5, sk48 5/5, g50t 1/2, tn36 0/4) plus the four
RESET hashes.

One jar per client, shared across games — settled by a cross-game probe (all four
games, out and back, 8/8 first-attempt) rather than assumed. `cookies=False` is
kept so the old transport can be reproduced, because every figure this project
has measured was taken on it.

## INC-008 — the probe put session tokens in the ledger

Found while writing the fix above. `probe_stickiness.py` logged raw `Set-Cookie`
headers for 55 calls, and that header carries **values** — the ALB pins and
`GAMESESSION`, a bearer token for a live session. It bypassed `client._record`,
which has always written `X-API-Key` as `<redacted>` precisely so no credential
reaches disk; the ledger is tracked and Phase 4 publishes every tracked file.

Both directions fixed: the probe and the client now log cookie **names** only,
and [`redact_ledger.py`](redact_ledger.py) replaced the 55 values while keeping
the names, marking each entry `redacted: "INC-008"`. It edits at byte level, so
untouched entries are byte-identical and the diff is exactly those 55 lines. A
test asserts no ledger entry carries a cookie value — and was watched failing on
all 55 before the redaction ran.

Editing an append-only ledger was deliberate: its stated invariant is *also* that
credentials never enter it, and the two collided. What is **not** fixed is git
history — the values are in the pushed commit `29c631e`, and removing them means
rewriting a published branch. Exposure is bounded (development-pile sessions,
all abandoned, no sealed game, API key never involved) and the call is the
owner's.

The lesson generalises past cookies: the redaction discipline lived inside
`_record`, so every instrument that wrote its own ledger line went around the
discipline too.

**S10 acted on that lesson, and the shape of the action is the interesting
part.** The repair is *not* "make `_record` the only writer".
`probe_stickiness.py` still opens the ledger itself, because it needs response
headers `_record` does not capture — a legitimate need, and the next instrument
that needs a field the writer does not carry will do the same. The invariant
moved onto the artefact instead:

```bash
python tools/ledger_invariants.py          # this ledger
python tools/ledger_invariants.py --all    # every track's, incl. baseline-arms
```

[`tools/ledger_invariants.py`](tools/ledger_invariants.py) reads the file and
asks what is in it, never who put it there. Four tiers — exact field rules, a
literal search for the live key (schema-independent, and it reports whether it
was able to run rather than counting a skipped check as a pass), a **fail-closed**
refusal of any credential-shaped field nobody declared, and bearer/JWT shapes in
the fields that could carry one. Violations are `(line, field, shape)`: the
scanner never returns the value it found, and a test asserts that over the
serialised report. `verify.sh` runs it over all three ledgers; 29 tests in
[`test_ledger_invariants.py`](test_ledger_invariants.py) plant one synthetic
offender per claimed shape and require the detector to go red, then require a
clean row to stay clean.

Single entry points are worth building only where a capability can genuinely be
taken away — `proxy`'s no-bypass seal holds because the arm never has the
credential, not because of how its code is arranged. Everywhere else, the
invariant belongs to the resource.

<details>
<summary>Original INC-001 / INC-002 text (diagnoses overturned, kept for the record)</summary>

`GET /api/games` lists 25 games, but RESET returned `400 game <id> not found`
for three of the four development-pile games in early probing; only
`g50t-5849a774` started, and a 3-round retry sweep left the other three at 0/6
(INC-001, INC-001a). There is no non-destructive way to enumerate a playable
set: `/api/account`, `/api/me`, `/api/key`, `/api/games/available` all 404,
`/api/user` 401s, `?playable=true` is ignored. The sweep's retry envelopes
(seconds, not minutes) never outlasted an unavailability wave, which is what
produced the 'entitlement boundary' misdiagnosis.

INC-002 then recorded RESET 4/48 and ACTION 0/8 on g50t inside single
availability windows, having ruled out request shape (4 variants), stale
sessions, and unclosed scorecards — all true observations, but the conclusion
"this blocks the whole live-API programme" mistook wave-transient faults for a
hard failure. What did hold up: two independent RESETs returned the identical
initial-frame hash `801726dc499f3f52`, the first cross-session determinism
data point, since confirmed by the full precheck.

</details>

## INC-003 — the first precheck reported a false PASS

Worth recording against my own work: `compare()` originally treated steps with no
hash as agreeing, so two runs that had *both* died on ACTION1 compared as
identical and the verdict read `deterministic: true`. A precheck that cannot fail
is not a check. Fixed — a hash counts only when present on both sides, and PASS
additionally requires the full sequence to have run. Re-scoring the same data
(no new API calls) now yields `INCOMPLETE`, 2 of 21 steps, 1 usable hash.

## The pile cut

`data/piles.json`, sha256 `3feca53e5ede695cfa46ae994cb95fd6b43abb9d97295e8c87e6302b41bbc19a`.

Development pile — 4 games, stratified so it spans the mechanics families:

| game | title | family | levels | baseline actions |
|---|---|---|---|---|
| `ar25-0c556536` | AR25 | keyboard_click | 8 | 748 |
| `g50t-5849a774` | G50T | keyboard | 7 | 879 |
| `sk48-d8078629` | SK48 | keyboard_click | 8 | 1070 |
| `tn36-ef4dde99` | TN36 | click | 7 | 317 |

Sealed pile: the remaining **21**, including the lone untagged game — so the
sealed pile keeps a family the development pile never shows us.

The draw is deterministic: seed `0x7EA17A`, ids sorted lexicographically within
each family, drawn with splitmix64. Anyone can re-run it and get this list.

**Why the cut had to happen before anything else.** Phase 3 iterates until it
gets results; that is only honest if the confirmation runs on problems nobody has
seen. A game that has been played is burnt. So the knife falls before the first
RESET, not after.

**Contamination state (see `data/contamination_log.jsonl`, which supersedes the
register inside the hash-locked file; read it with `python contamination.py`).**
The four development-pile games are `trajectories_reviewed` — played by the
baseline-arms pilots and this precheck, which is what the development pile is
for. On the sealed side, nine games are registered as knowledge-contaminated by
INC-BA-001 and ruled on by F-11 (see INC-006 below): two quarantined out of the
claim set, seven retained with a sensitivity caveat, `dc22-fdcac232` keeping the
stronger `design_document_disclosed` level it got from INC-004. The remaining
twelve are `never_audited`. **No sealed game has been touched via the API**, and
that is now checked over the whole ledger rather than asserted.

**At cut time nothing was contaminated.** The cut was made from catalogue metadata alone —
ids, titles, tags, action counts. No mechanics were observed, so
`contamination_register` records all 25 games as `never_audited`.

### The local engine is the one path the ledger cannot see

`assert_playable` guards every API path, and the ledger audit above proves no
sealed game was ever *requested*. Neither covers the local engine: it makes no
API call at all, so a local run over all 25 games leaves the audit green while
every sealed game's **source** sits on disk. Upstream's defaults make that the
easy mistake, not an exotic one — first run downloads the source for all 25 into
`environment_files/`, and `make play-local`, `make verify-local` and the swarm
runner's `--game` all default to every game in the dataset
(`browser-ops/TERMS.md` §4.2, with URLs).

[`local_engine_guard.py`](local_engine_guard.py) is the fail-closed guard for
that path, and `ACCESS_CHECK.md` §8b is its reasoning. Positive whitelist,
default deny, boundary-anchored prefixes, sealed tested before allow:

```bash
python local_engine_guard.py check -- make play-local             # exit 2 — no documented filter
python local_engine_guard.py check -- uv run main.py --agent=x    # exit 2 — unfiltered is all 25
python local_engine_guard.py check -- uv run main.py --agent=x --game=ar25    # exit 0
python local_engine_guard.py run   -- <argv...>    # vets, then execs only if allowed
python local_engine_guard.py scan  environment_files   # names-only sweep; opens nothing
python local_engine_guard.py selftest              # asserts its own claims, offline
```

An adversarial pass against the first version found **nine working bypasses**;
each is a named regression test now, and `ACCESS_CHECK.md` §8b.1 records the two
that changed the rules rather than just the regexes. The sharpest: this file's
own worked example used to be `make play-local GAME=ar25`, and `GAME=` is a
spelling **we invented** — no filter argument is documented for that target, and
make swallows an unreferenced variable in silence, so it would have played all
25 while looking filtered. It is refused now.

`selftest` and `scan` both run in `verify.sh`. `environment_files/` is
gitignored, and nothing under it may be read except the four development games —
downloading is not reading, and that distinction is the whole of the discipline.

## Ledger

`data/recon_ledger.jsonl` is append-only: one line per API call with method, URL,
redacted headers, request body, status, full response body, and elapsed time.
Every call this directory has ever made is in it.
