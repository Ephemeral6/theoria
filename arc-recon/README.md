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

The remaining open items for gameplay proper: ACTION6 `data` shape (blocks
tn36 and every `click`-family game), and rate limits / whether failed HTTP
attempts count against any server-side quota.

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
register inside the hash-locked file).** The four development-pile games are now
`trajectories_reviewed` — played by the baseline-arms pilots and this precheck,
which is what the development pile is for. On the sealed side, `dc22-fdcac232`
is corrected to `design_document_disclosed` (Theoria.md itself prints its
failure structure; INC-004), and baseline-arms' INC-BA-001 reports nine sealed
games whose mechanics were partially disclosed to a search subagent's context
(`ls20`, `ft09` materially; the register upgrade for those is pending an owner
ruling). No sealed game has been touched via the API.

**At cut time nothing was contaminated.** The cut was made from catalogue metadata alone —
ids, titles, tags, action counts. No mechanics were observed, so
`contamination_register` records all 25 games as `never_audited`.

## Ledger

`data/recon_ledger.jsonl` is append-only: one line per API call with method, URL,
redacted headers, request body, status, full response body, and elapsed time.
Every call this directory has ever made is in it.
