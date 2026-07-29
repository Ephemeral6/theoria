# A3 · what the arithmetic says before any money is spent

Written 2026-07-28T22:10Z by RES-1, before the first authorised live leg.
The bus carries a summary; this file is the record.

## 1 · The authorised package cannot buy the first level

Three independent sources agree.

**What one level costs in actions.** g50t's scorecard carries its own
`level_baseline_actions`: `[78, 175, 179, 230, 96, 54, 67]`
(`runs/20260728T015354Z-g50t-first-contact/run.json`). Level 1's baseline is
**78 successful actions**. The authorised budget is **40 per level** — a little
over half. Level 2's baseline is 175, more than four times it.

**What one action costs.** The single live run of this arm spent 7 successful
actions in 2,756 seconds for $6.317658 (`MANIFEST.json` of that run; the figure
is now confirmed to the cent by `armtools/archive.turn_series`, whose per-turn
dollars sum to exactly 6.317658 and whose surprise counts sum to exactly 8 =
4 `render_mismatch` + 4 `replay_mismatch`). That is **$0.90 per action** and
**394 seconds per action** — roughly 17 minutes per turn.

**Therefore.** Clearing g50t level 1 costs about `78 x $0.90 = $70` and about
`78 x 394s = 8.5 hours`. The authorised per-game ceiling is **$60** and the
arm's wall clock is **3 hours** (`inner/loop.DEFAULT_WALL_CLOCK_S`).

Both money and actions fall short, and wall clock falls short by roughly three
times. **Under this package and this arm's present efficiency, no level will be
completed, so no level boundary will occur, so C3's transfer claim cannot be
observed this round.** That conclusion comes from 先算后花 — computing before
spending — which is what the work order asked for.

## 2 · The bill-shape figure needs turns, not levels — and that is affordable

`battery/metrics/economy.py` sets `MIN_TURNS_FOR_SHAPE = 8` and refuses
`frontload_index` below it. The one live run produced **2 billed turns**, so the
metric returns `status: insufficient-data, value: null`. The raw ratio is
0.287 on the billed-turn axis and 0.0 on the all-turns axis.

That the two axes disagree this violently is itself a finding worth carrying to
`battery/PREDICTIONS.md` before E2 is read as a Phase 4 endpoint:
`battery.model.Run.turn_costs()` buckets *billed* calls by turn, so a turn whose
theorize the evidence gate skipped **cannot appear in it** — and those free turns
are the entire point of both the gate and the C2 "front-loaded, then trending to
zero" claim. Measured on the only run available, the axis choice inverts the
answer. Both series are now emitted (`turn_costs` and
`turn_costs_billed_only`) so the gap is visible rather than a silent convention.

The consequence for this campaign is the useful one: **the deliverable that the
budget can actually buy is the per-turn series, not a cleared level.** Eight to
twelve billed turns per leg is roughly $20–25, and three legs across three
development-pile games is $60–75 — well inside the authorised $200, and it
yields the whole raw material for figure 2.

## 3 · No level completion has ever been observed, by anyone, here

Across every recorded live ARC response in this repository — 1,570 rows in
`baseline-arms/out/shards/ledger.{ar25,g50t,sk48,tn36}.jsonl` plus 379 in the
`a7`/`a7up` shards — `levels_completed` is `0` on all 1,949, and `state` is
`NOT_FINISHED` on all but one (`ledger.ar25.jsonl` line 465 is a `GAME_OVER`
death). A repo-wide scan found non-zero values only in synthetic data:
`proxy/var/**` (the mock) and `ablation-arm/artifacts/**` (worldgen fixtures).

So **which signal ARC sends on a level completion is an unobserved quantity**,
not a known one. The arm now handles both hypotheses and, where it cannot tell,
stops with `outcome: "level_advance_unknown"` rather than guessing — turning the
first real completion into a measurement. `arc-recon/ACCESS_CHECK.md:24-25` adds
the one hard constraint: `RESET` returns `full_reset: false` and resets to *the
level the session is on*, so RESET alone is not an advance mechanism and cannot
be treated as one.

## 4 · The pile cut is intact

Checked before anything else, because it is the one failure that cannot be
repaired afterwards. `arc-recon/data/piles.json` carries `dev_pile` of 4 and
`sealed_pile` of 21, unchanged, one commit in its history, clean working tree.
CLAUDE.md pins sha256 `3feca53e…41bbc19a`; that is the file's own canonical
self-hash over its body excluding the `sha256` field, and it **recomputes
exactly**. The raw file-bytes hash differs, which is expected and is not an
incident. `harness/campaign.assert_dev_pile` now checks every game id against
this file — not against a constant in the source — before a campaign starts.
