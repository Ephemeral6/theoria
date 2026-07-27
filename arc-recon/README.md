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

## INC-001 — the key does not cover the whole public set

`GET /api/games` lists 25 games, but RESET returns `400 game <id> not found` for
**three of the four development-pile games**. Only `g50t-5849a774` started.

The pile cut assumed the 25 listed games are playable. That premise is false, so
the development pile is effectively **one** game. The playable subset of the
sealed pile is unknown and was **deliberately not probed**: a successful RESET
returns the first frame, so an accessibility sweep would burn exactly the sealed
games that are accessible — the worst possible outcome.

**Refined by INC-001a.** A 3-round retry sweep over the development pile gave
`g50t` OK/400/400 and the other three 400 every time — so g50t succeeded 2 of 4
attempts overall and the others 0 of 6. Three games look genuinely unavailable to
this key, and a *second* effect refuses repeat RESETs on g50t (most likely a live
session already open, or a start-rate limit). The API reports both with the same
message, `game <id> not found`.

There is no non-destructive way to enumerate the playable set: `/api/account`,
`/api/me`, `/api/key`, `/api/games/available` all 404, `/api/user` 401s (it exists
but `X-API-Key` is not its auth), and `?playable=true` is ignored. Determining
playability requires a RESET, which burns the game.

`data/piles.json` is hash-locked and was left untouched; the incident lives in
`data/incidents.jsonl`, and `data/contamination_log.jsonl` supersedes the
register inside the locked file. **No sealed game has been touched.**

The remaining access-check items still need gameplay: cross-session residue (does RESET fully clear
state?), rate limits and action quota, and the determinism precheck — a fixed
action sequence replayed twice with frame hashes compared. All of these are now
runnable on `g50t-5849a774` alone.

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

**Nothing is contaminated yet.** The cut was made from catalogue metadata alone —
ids, titles, tags, action counts. No mechanics were observed, so
`contamination_register` records all 25 games as `never_audited`.

## Ledger

`data/recon_ledger.jsonl` is append-only: one line per API call with method, URL,
redacted headers, request body, status, full response body, and elapsed time.
Every call this directory has ever made is in it.
