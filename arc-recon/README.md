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
cd arc-recon && python contamination.py --json   # register, sealed claim set, ledger audit
cd arc-recon && python probe_stickiness.py       # cookie A/B; zero actions
cd arc-recon && python -m pytest test_hygiene.py # 28 offline tests
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
| **cascade semantics** — one frame per action, or several? | `frame` is a **list of frames** (length 1 on RESET, each 64x64). The API models `action -> frame sequence`, so `step` must be shaped that way. Whether it ever exceeds 1 needs an action that triggers an internal tick. |
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

> **This model is itself superseded — see INC-007 below.** The retry policy
> works and the verdicts above stand, but "waves of unavailability" is not what
> is happening: our client keeps no cookie jar, so it is routed to a different
> replica on every call. The amplification is ours, not the server's.

**Short ids are banned from requests (INC-005).** `ACTION` with a short id
(`sk48` instead of `sk48-d8078629`) can return 200 — but every such 200 in our
ledger carried the *pristine initial frame* regardless of session progress
(6 of 6 on g50t; corroborated by a 200 for the nonexistent `ACTION7` in
baseline-arms' log). A short-id 200 is served from something that is not the
live session. The version suffix is the environment version fingerprint, so
requests always carry the full id; the short↔full mapping the operators need is
recorded in `data/precheck.json` (`id_map`) and in every ledger request body:

`ar25 ↔ ar25-0c556536 · g50t ↔ g50t-5849a774 · sk48 ↔ sk48-d8078629 · tn36 ↔ tn36-ef4dde99`

**tn36 caveat.** Its advertised action space is `[6]` only, and `ACTION6`
(with or without `{x,y}` data) returns **500 on every attempt** — the game's
nominal action is broken server-side. The precheck ran on `ACTION1–4`, which
the API accepts but which are visible no-ops (the frame never changed). So the
PASS certifies RESET-state reproducibility and no-op consistency, and tn36
remains **gameplay-blocked until the ACTION6 data shape is resolved**.

**Access-check items settled by the precheck runs**: cascade semantics —
`action → frame sequence` confirmed observationally (7-frame and 2-frame
responses); cross-session residue — none on any of the four (identical RESET
hashes, and g50t's re-check reproduced the *previous day's* hashes exactly);
`levels_completed` / `win_levels` maintained throughout.

**Budget.** ≤20 executed ACTIONs per game (RESETs logged, not counted), spent
16 / 20 / 16 / 16 on ar25 / g50t / sk48 / tn36. A 10-minute harness timeout
killed one run mid-flight; both live sessions were resumed from the ledger
(`precheck_resume.py`) with zero lost state — the resumed steps' hashes match
the partner run exactly, which is itself determinism evidence across a
~20-minute gap.

The remaining open item for gameplay proper is the ACTION6 `data` shape, which
blocks tn36 and every `click`-family game. Rate limits and quota are now
answered — see [ACCESS_CHECK.md](ACCESS_CHECK.md) §6, and the correction below.

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
three agreeing replays across two days and three sessions — which is also the
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

**The fix is not applied here.** Changing the transport is changing the
instrument: every determinism verdict, the canary baseline, and both tracks' cost
figures were measured on the current one. It deserves its own change with a
before/after re-measurement attached. The probe is reproducible
([`probe_stickiness.py`](probe_stickiness.py), zero action cost) and the finding
is filed.

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

## Ledger

`data/recon_ledger.jsonl` is append-only: one line per API call with method, URL,
redacted headers, request body, status, full response body, and elapsed time.
Every call this directory has ever made is in it.
