# 预测 — tn36-ef4dde99 · P-20 follow-up (ACTION6 coordinate shape)

Written before any follow-up action is spent. Three actions, from a fresh RESET
on a fresh scorecard:

| # | action | body |
|---|---|---|
| 1 | ACTION6 | `x=32, y=32` |
| 2 | ACTION6 | `x=5, y=5` |
| 3 | ACTION6 | `x=32, y=32` |

## What this is testing

The main run got **one** 200 out of `ACTION6 {x:32,y:32}` where every earlier
attempt in either track 500'd. One observation is not a finding. Two questions:

1. **Does it reproduce?** If the 200 was a fluke — a transient server state, a
   lucky replica — a fresh session should not repeat it.
2. **Are the coordinates read, or merely tolerated?** If `x`/`y` are parsed and
   acted on, clicking (5,5) should not produce the same frame as clicking
   (32,32) from the same state. If the server accepts the field and ignores it,
   the two clicks are the same command and the frames will follow the same
   trajectory as two identical clicks would.

## 逐步预测

| # | action | http | n_frames | distinct | intra_changes | first==prev_last | expected hash |
|---|---|---|---|---|---|---|---|
| 0 | RESET | 200 | 1 | 1 | 0 | `None` | `1491b31f98da62d0` — **match** |
| 1 | ACTION6 (32,32) | **200** | 1 | 1 | 0 | **false** | no expectation |
| 2 | ACTION6 (5,5) | **200** | 1 | 1 | 0 | **false** | no expectation |
| 3 | ACTION6 (32,32) | **200** | 1 | 1 | 0 | **false** | no expectation |

Further commitments, so this can be scored rather than narrated:

* **Step 1's per-frame hash is `f24a3446b02c98c2`** — the exact frame the main
  run got from the same click on the same starting state. This is the strong
  form of "does it reproduce" and the one most likely to be wrong: if the game
  has any hidden per-session state (a randomised board, a cursor that starts
  somewhere different) the click will land somewhere else and the hash will not
  match. I predict it matches.
* **Step 2's frame differs from step 1's.** This is the coordinate test.
* `state` stays `NOT_FINISHED`, `levels_completed` stays 0, and
  `available_actions` stays `[6]` on all three steps.
* No step returns more than one frame. tn36's precheck saw 9/9 single frames and
  the main run saw 2/2; I do not expect the click family to cascade here, and I
  expect this game to contribute **no** evidence for verdict (a).
* All three succeed on the first attempt (the cookie jar is on).

## 会让我改口的观测

If step 1 returns 500, the main run's 200 was noise and the ACTION6 finding
collapses to "one anomalous response" — I would withdraw the claim entirely
rather than explain it. If step 1 returns 200 but with a hash other than
`f24a3446b02c98c2`, the command works but the game is not session-deterministic,
which contradicts the RESET-hash evidence and would be the more interesting
result. If step 2's frame equals step 1's, the server is accepting `x`/`y` and
discarding them, and "tn36 is playable" would be too strong: the action would be
accepted but uncontrollable.

The result that would most surprise me is a multi-frame response. Two single
frames in the main run and nine in the precheck make it unlikely, but a click
game is exactly where an animation would live, and if it happens here it means
batch length is not a property of a game at all.
