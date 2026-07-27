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

Everything else on Theoria.md's access-check list needs gameplay and is therefore
gated on the cut: RESET semantics and cross-session residue, whether one action
returns one frame or several (the cascade-semantics question that decides the
shape of `step`), whether `level` is a response field or must be inferred from
score jumps, rate limits and action quota, and the determinism precheck.

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
