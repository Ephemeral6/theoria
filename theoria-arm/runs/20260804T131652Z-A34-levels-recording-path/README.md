# A34 — the levels.jsonl finding: what twenty-two zero-byte files actually meant

**Offline. $0.00, zero ARC actions, zero model calls, no network, no credential read.**

## The question

Twenty-two `runs/*/levels.jsonl` were zero bytes — every one on disk, including
the mock legs — while `inner/levels.py` existed in full. A34 §3: *"项目最重要的
那次事件的记录路径，从未执行过一次。"* If the detector cannot fire, then a day on
which the arm wins reads exactly like a day on which it does not, and the
sentence "nothing has ever completed a level" is not a measurement.

## The answer, in three parts

**The detector is called on every recorded step.** `inner/loop._record` passes
`levels_completed` to `LevelLog.observe` before it returns, on every command,
successful or not. Nothing gates it.

**It has never fired, because no world has ever incremented the counter in front
of it.** On the live side that is A34's own arithmetic. On the mock side it is
sharper, and it is the part that dissolves A34's "strongest lead": the offline
exploration policy is `min(legal, key=(times_tried, id))`, which on the mock's
level 1 oscillates between **two** cells forever. Driven 200 actions, the mock
agent visits two positions and completes nothing. **No mock leg on the default
policy can reach the goal at any budget**, so `a3-gate-mock` and `audit-smoke`
being zero bytes was never evidence about the recording path in either
direction.

**And when it does fire, it writes — except once.** A scripted mock leg that
genuinely reaches the goal, through the real `harness.run.play` shell, writes a
263-byte `levels.jsonl` with the boundary in it, cuts `starts` at the right
step, appends a `level` turn, and captures the winning frame in
`witnessed_wins.json`. The exception is the one that matters.

## The defect the positive control found

`LevelLog.observe` suppressed the event when the counter reached the game's last
level. The suppression is right for the *destructive* half of the handling —
`_on_level_boundary` drops `problem.json` and wipes `generated/`, which on a
winning run deletes the artefacts that say how it was won, and
`test_winning_the_last_level_does_not_open_an_eighth` has pinned that since A3.
But the argument covered the handling, and it was silently extended to the
record, which it never covered.

Measured on a synthetic three-level win:

| | before | after |
|---|---|---|
| `levels.jsonl` rows | 2 | 3 |
| `ScoreWatch` boundary events | 3 | 3 |
| `ScoreWatch` verdict | `observed` | `observed` |
| `witnessed_wins.json` | 2 | 3 |

A seven-level g50t win would have written six rows and left the seventh — the
win — off disk, while the second instrument recorded all seven and said
`observed`. **Two instruments, one event, silently different answers, on the
single run this project exists to produce.**

## And one more, found by fixing the first

`harness/campaign.py` asked "how many levels did this leg finish" twice, both
times as `(summary.get("levels") or {}).get("boundaries", 0)` — once for the
campaign total and once inside `_progress`, the predicate behind
`ZERO_PROGRESS_LIMIT`. `boundaries` excludes the win. So a leg that **won its
game** counted zero completions at both sites: it would have contributed nothing
to the campaign total, and `_progress` would have called the winning leg
unproductive, letting a three-leg zero-progress streak stop the campaign
immediately after the only win in this project's history.

That was already true before this ticket — there was no `game_won` to add, so
the expression could not have been written correctly. Nothing had ever won, so
nothing had ever been wrong. That is not the same as being right, and it is the
second time here that a code path was correct only because the event it
mishandles has never happened.

## What changed

* `inner/levels.py` — `LevelLog.finals` holds the winning increment as a
  `game_won` event, and `records()` is what `levels.jsonl` is written from.
  `finals` is a second list, not an entry in `events`, because `events` and
  `starts` are one structure written down twice and a win appends to neither.
* `inner/loop.py` — `_on_game_won`, the non-destructive half of the boundary
  handler: snapshot the winning books, witness the winning frame, append a turn
  row. `problem.json` and `generated/` are left where they are.
  `_witness_the_win` gains `segmenting`, because at a boundary the increment's
  step is the *first* frame of the next level and at a win it is the *final*
  frame itself; reading one with the other's arithmetic yields a witness that
  looks right and points at the wrong frame.
* `armtools/level_evidence.py` (new) — the readback. Five verdicts, and
  `levels_completed` is `None` in three of them.
* `armtools/round.py` — the round total no longer reads
  `sum((l.get("levels_completed") or 0) for l in legs)`.
* `harness/campaign.py` — `_completions()` = `boundaries + game_won` at both
  call sites; `legs_with_no_level_record` counted rather than summed as zero;
  `campaign_series` marks the winning turn by reading `events + finals`.
* `tests/test_levels_recording_path.py` (new) — six tests: the mechanism, the
  end-to-end positive, the two-instrument cross-check, the campaign reduction,
  and two negative controls.

## The honest status

**No archived leg contains a real boundary.** Of 30 leg directories: 11
`measured_absent` (the counter was read on every envelope and never rose), 19
`unmeasured` (nothing looked), 0 `observed`, 0 `evidence_missing`. So this fix
is unexercised on a real positive, and every positive here is synthetic or
mock.

What changed is not that the arm has won. It is that the instrument is now
*known* to fire and *known* to write, and that a lost record no longer reads as
a zero. A34's step 1 is what makes steps 2 and 3 interpretable, and this is
step 1.

## Reproduce

```bash
cd theoria-arm
python -m pytest tests/test_levels_recording_path.py -q
python -m armtools.level_evidence runs
python runs/20260804T131652Z-A34-levels-recording-path/make_manifest.py --check
```
