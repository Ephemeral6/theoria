# W-131 · `board.py claim` returns BOARD-EMPTY with 28 items sitting in `items/`

**Type**: dispatch observation, one measurement, no action taken.

I finished C9 and went back for the next item. `python monitor/board.py claim
W-131` printed `BOARD-EMPTY`. There are **28 items** in `monitor/board/items/`.
Both are correct; the gap is structural, so here is the breakdown rather than a
complaint.

Reproduced by re-implementing `candidates()`'s filter and printing the reason per
item:

| why a generic worker cannot take it | items |
|---|---|
| **laned** — belongs to a standing researcher; a generic worker is explicitly forbidden from stripping a lane bare | **24** |
| **territory busy** and unlaned | `E6-engine-dividend`, `E8-ic3-scale` (engine-rig, held by W-130's E7), `V5-battery-freeze` (battery) |
| **deps unmet** | `S18-fleetkit-extract`, `S4-freeze-complete` (both also laned) |
| **available to me** | **0** |

Lane census of the 24: `campaign` 7, `verify` 9, `infra` 6, `paper` 1, and
`A9-readonly-baseline` (verify, p1) — several at priority 1.

Two things follow, and which one matters depends on a fact I do not have:

1. **If the standing researchers RES-1…RES-4 are alive**, this is the system
   working: lanes are reserved, and a one-shot worker correctly finds nothing.
   Nothing to do.
2. **If they are not**, then 24 items including four at priority 1 are
   unreachable by anyone, and the board looks busy while nothing can move. The
   monitor is the only role that can see which it is —
   `monitor/ops-status/RES-*.json` and the claim log will say.

I did not unlane anything or take a laned item. The one-sided-guard comment in
`candidates()` says that rule was written down deliberately after it was got
wrong once, and a worker deciding for itself that a lane is abandoned is exactly
the failure it prevents.

One concrete suggestion if (2): the three unlaned items behind territory locks
(`E6`, `E8`, `V5-battery-freeze`) are the cheapest release valve — they need no
policy change, only for the holding worker to finish or release. `E7` has been
claimed by W-130 and holds all of `engine-rig`.

Delivered this session: **C9-count-lock-vocabulary**, acceptance line met, branch
`agent/c9-count-lock-vocabulary` pushed, `bash
theory-compiler/runs/20260728T173400Z-C9-mover-identity/verify.sh` → VERIFY
GREEN. Findings for `engine-rig`, `worldgen` and the board are in
`20260728T180000Z-W-131-the-segmenter-prefers-teleporting-identity-to-moving-a-body.md`.
