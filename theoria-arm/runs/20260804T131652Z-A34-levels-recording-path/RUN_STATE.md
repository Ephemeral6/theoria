# RUN_STATE — A34, the levels.jsonl recording path

**Branch** `q/a34-levels` · **base** `4846e66d` · **UTC** 2026-08-04T13:16:52Z
**Spend** $0.00, 0 ARC actions, 0 model calls, no network, no credential read.

## Running notes, in the order things happened

**13:00** — Read the item. Its premise is `runs/*/levels.jsonl` all zero bytes;
confirmed on the main tree: 22 files found, 22 of them zero bytes. Eight further
leg directories carry no `levels.jsonl` at all.

**13:02** — Traced the path. `inner/loop._record` → `LevelLog.observe` →
`_on_level_boundary` → `_save_all` writes `levels.jsonl`. Nothing gates the
call; the detector runs on every recorded step including failed commands. So
"never called" is ruled out by reading.

**13:05** — The strongest lead in the item is the mock legs. Read
`proxy/mock/arc_mock.py`: the mock advances `levels_completed` when the agent
reaches the GOAL glyph, and the increment is in-band with `state` still
`NOT_FINISHED` — the same shape `LevelLog.observe` handles. Drove the mock's own
`Session` directly with the arm's exploration policy (`min(legal, key=(count,
id))`, i.e. 1,2,3,4,5 repeating) for 200 actions: **two distinct positions
visited, zero completions**. The agent steps down and back up forever. That is
why the mock legs are empty, and it means their zero bytes were never evidence
about the recording path in either direction.

**13:10** — First attempt at a positive control failed for a reason worth
keeping: I BFS'd a 9-action solution from the RESET position, and the leg
produced 12 trace rows all reading `levels_completed: 0`. The cause was not the
arm — the loop opens with a five-action sweep (ACTION1..5) before the first
exploration turn, so the scripted walk started from the wrong square and the
budget ran out three actions short. Re-derived the walk with the sweep as a
prefix. **A wrong script and a broken detector produce the same trace**, which
is a small version of exactly the confusion this item is about.

**13:14** — Corrected leg through the real `harness.run.play` shell against
`proxy/mock`: `levels.jsonl` **263 bytes**, one `level_boundary` row at step 13,
`starts == [0, 13]`, one `level` turn row, one witness with the winning grid.
The end-to-end path works. It had simply never been asked.

**13:20** — Item 3: do the two instruments agree? Built a synthetic three-level
win with `win_levels = 3`. **They do not.** `LevelLog` recorded 2 events and
`levels.jsonl` 2 rows; `ScoreWatch` recorded 3 `level_boundary` events and
reported `observed`; `witnessed_wins.json` held 2. The missing row is the win.
`corroborate()` cannot see this: it compares the envelope counter against a
*scorecard* reading, never its own event list against `LevelLog`'s.

**13:30** — Fix. `LevelLog.finals` + `records()`; `loop._on_game_won` as the
non-destructive half of the boundary handler; `_witness_the_win(segmenting=)`
because at a win the increment's step *is* the final frame rather than the first
frame of a next level. After: 3 rows, 3 witnesses, `problem.json` and
`generated/` still present, `levels.level` still 3.

**13:45** — The negative control. `armtools/level_evidence.py`: five verdicts,
and `levels_completed` is `None` in three of them. `armtools/round.py`'s
`sum((l.get("levels_completed") or 0) for l in legs)` replaced.

**13:55** — Confirmed the new tests are red without the fix (`git stash push --
theoria-arm/inner`, run, pop): *"three increments were observed and 2 row(s)
reached disk; the missing one is the win"*.

## Where it is left

Green on the three gates. `q/a34-levels` is not pushed and not merged; the
worktree is left in place at `.worktrees/a34-levels`.

## What is owed

* GAP A34-1 — unexercised on a real positive. Zero archived legs contain a
  boundary; every positive here is synthetic or mock.
* GAP A34-2 — `_on_game_won` cannot be reached through the mock at all
  (`proxy/mock` never returns `win_levels`), so it is exercised through
  hand-built envelopes only.
* GAP A34-3 — the two instruments are reconciled by a test, not at runtime.
* GAP A34-4 — `level_evidence` reads `trace.jsonl`, not the ledger, so a leg
  killed before `_save_all` reads `unmeasured` even if its ledger holds the
  increment.
* GAP A34-5 — `round.json`'s totals changed shape; older files keep the old key.

## What was deliberately not touched

The two `runs/*A26b*` directories are being written by a live leg. They were
read by the sweep (read-only, and they report `unmeasured` because a running
leg's `trace.jsonl` does not exist until `_save_all`) and no conclusion is drawn
about them. Nothing outside `theoria-arm/` was changed.
