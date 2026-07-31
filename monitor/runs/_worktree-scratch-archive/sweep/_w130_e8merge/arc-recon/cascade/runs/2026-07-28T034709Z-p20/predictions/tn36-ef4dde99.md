# P-20 cascade probe — prediction for `tn36-ef4dde99`

Written before any action of this run was spent. Sources read: `cascade/spec.py`,
`cascade/probe.py`, and this game's entry in `data/precheck.json` only. The other
three games' entries, `README.md` and `ACCESS_CHECK.md` were deliberately not read.

Frozen sequence (4 actions): `ACTION6{x:32,y:32}` → `ACTION6` (no data) → `ACTION1` → `ACTION2`.

## What I am reasoning from

* Precheck run_a and run_b: 9 steps each, **every** step `n_frames = 1`, **every**
  hash `1491b31f98da62d0` — RESET and all four of ACTION1..4, twice. `state`
  never leaves `NOT_FINISHED`, `levels_completed` never leaves 0. Verdict PASS,
  `max_frames_per_action: 1`, `cross_session_residue: false`, `deterministic: true`.
* `available_actions: [6]`. So the only *nominal* action is ACTION6, and ACTION1..4
  are accepted no-ops that return the unchanged opening frame.
* `spec.py` records that ACTION6 returned **500 on every precheck attempt, with and
  without `{x,y}`**, and that 500 is not retryable.
* `probe.expectations()` aligns `["RESET","ACTION6","ACTION6","ACTION1","ACTION2"]`
  against run_a `[RESET, ACTION1, ACTION2, ACTION3, ACTION4, …]`. Only index 0
  agrees by name. **Therefore only step 0 (RESET) has an offline expectation;
  steps 1–4 have `expected_batch_hash = None` and `matches_expected = None`.**

## The headline call

**The run stops after RESET.** Step 1 (`ACTION6` with `{x:32,y:32}`) returns 500,
`probe.run` takes the `status != 200` branch, writes the error record, sets
`stopped_early_at = 1` and breaks. So `actions_executed = 0`, steps 2/3/4 are
**never executed** and cost nothing from the budget. I predict this run spends
**zero successful actions** and produces **one** usable frame batch (the RESET one).

I am committing to that. If instead ACTION6 returns 200, my entire model of this
game is wrong and everything below it is void.

## Per-step predictions (concrete numbers)

### Step 0 — RESET
| field | prediction |
|---|---|
| `http_status` | 200 |
| `attempts` | 3 |
| `n_frames` | 1 |
| `distinct_frames` | 1 |
| `intra_batch_changes` | 0 |
| `first_equals_prev_last` | `null` (no previous batch — must not read as "did not match") |
| `batch_hash` | `1491b31f98da62d0` |
| `matches_expected` | **true** — expectation exists for this step and I predict it reproduces |
| other | `state = NOT_FINISHED`, `levels_completed = 0`, `win_levels = 7`, `available_actions = [6]`, `guid_present = true` |

### Step 1 — ACTION6, data `{x: 32, y: 32}`
| field | prediction |
|---|---|
| `http_status` | **500** |
| `attempts` | 1 (500 is not retryable) |
| `n_frames` | `null` (error branch: no frame list at all) |
| `distinct_frames` | `null` |
| `intra_batch_changes` | `null` |
| `first_equals_prev_last` | `null` |
| `matches_expected` | `null` — **no offline expectation for this step** |
| consequence | sequence stops; `stopped_early_at = 1`; `actions_executed = 0` |

### Step 2 — ACTION6, no data
**Predicted: not executed** (the run already stopped at step 1). No `http_status`,
no `n_frames`, no record written.
Counterfactual for the record, had it run: `http_status = 500`, `attempts = 1`,
`n_frames = null`, `distinct_frames = null`, `intra_batch_changes = null`,
`first_equals_prev_last = null`, `matches_expected = null` (no expectation).

### Step 3 — ACTION1
**Predicted: not executed.**
Counterfactual: `http_status = 200`, `attempts = 2`, `n_frames = 1`,
`distinct_frames = 1`, `intra_batch_changes = 0`, `first_equals_prev_last = true`
(the frame is byte-identical to the RESET frame, so the batch's first frame equals
the previous batch's last), `matches_expected = null` (no expectation).

### Step 4 — ACTION2
**Predicted: not executed.**
Counterfactual: `http_status = 200`, `attempts = 2`, `n_frames = 1`,
`distinct_frames = 1`, `intra_batch_changes = 0`, `first_equals_prev_last = true`,
`matches_expected = null` (no expectation).

### Steps with no offline expectation
Steps 1, 2, 3, 4 — all four. Only step 0 (RESET) has one.

## Sequence vs. container, and what would surprise me

I would call this game's step `action -> frame SEQUENCE` only if some response
returned `n_frames > 1` **with `distinct_frames > 1` and `intra_batch_changes >= 1`**
— i.e. adjacent frames in one batch genuinely differ, so one command produced
several world states and a single-frame model would silently discard the
intermediate ones. `n_frames > 1` with `distinct_frames == 1` is padding and proves
the opposite; `n_frames == 1` throughout says the list is just a container and
D-A0-004 ("action -> single frame") survives *for this game*. My prediction is the
third: 1 frame everywhere I get to look, and in fact I only get to look once,
because the only nominal action here is broken. So the honest expected outcome for
tn36 is **not** a verdict about cascades at all — it is `no usable evidence`
(one RESET batch, one frame, zero executed actions), plus a re-confirmation that
ACTION6 is 500 across sessions and across a different key/scorecard. That
re-confirmation is the real yield of this game: it turns "ACTION6 was 500 in one
session" into "ACTION6 is 500, reproducibly, in a fresh session and a fresh
scorecard", which is what makes tn36 unplayable rather than unlucky.

What would surprise me, in descending order: (1) **ACTION6 returning 200** — that
would mean the 500 was transient/environmental, tn36 is actually playable, and the
precheck's conclusion needs revisiting; (2) ACTION6 returning **400 or 404 instead
of 500** — the failure is a request-shape problem, not a server fault, and `{x,y}`
at (32,32) may simply be out of range for this game's grid; (3) the RESET frame
hashing to anything other than `1491b31f98da62d0` — that would be cross-session
non-determinism the precheck explicitly ruled out, and would be the most damaging
of the three because it undermines every hash-based expectation in the project;
(4) RESET returning `n_frames > 1` — the precheck saw 1 twice, so a 2- or 7-frame
RESET here would mean batch size is session-dependent, not action-dependent.

Because the probe stops at the first non-200, being right about step 1 costs me all
the observations from steps 2–4. I am accepting that: I predict I will end with a
one-row table and a `no usable evidence` classification for the cascade question,
and the correct reading of that is that tn36 was always the wrong game to ask the
cascade question of — it is here as a liveness/repro check on a known 500.

---

# 结果对照

Run: card `8e1cace3-a803-43fa-bd3c-cb1cd57ba7eb`, 2026-07-28T03:52:50Z–03:52:54Z,
3 HTTP calls, `actions_executed: 1`, `stopped_early_at: 2`.

**The headline call was wrong, and wrong in the direction that matters.** I
predicted `ACTION6` with `{x,y}` would 500 and end the run at step 1. It returned
**200**, and the frame it returned **differs from the RESET frame**
(`first_equals_prev_last: false`, `3e8702e648bb9755` → `f24a3446b02c98c2`). The
500 arrived one step later, on `ACTION6` **without** `{x,y}`. So the failure is a
request-shape failure, not a broken game: ACTION6 requires coordinates, and
omitting them faults the server rather than being rejected as a 400. This is my
surprise (2) from above, not my prediction — and it means **tn36 is playable**,
which contradicts the premise the frozen sequence was built on.

### Step 0 — RESET
| field | predicted | observed | verdict |
|---|---|---|---|
| `http_status` | 200 | 200 | **hit** |
| `attempts` | 3 | 1 | **miss** (I over-budgeted for ALB retries; the first call landed) |
| `n_frames` | 1 | 1 | **hit** |
| `distinct_frames` | 1 | 1 | **hit** |
| `intra_batch_changes` | 0 | 0 | **hit** |
| `first_equals_prev_last` | `null` | `null` | **hit** |
| `batch_hash` / `matches_expected` | `1491b31f98da62d0` / true | `1491b31f98da62d0` / **true** | **hit** |

Frame shape `[64, 64]`; `state NOT_FINISHED`, `levels_completed 0`, `win_levels 7`,
`available_actions [6]`, `full_reset false`, `guid_present true`. Cross-session
determinism holds: a fresh scorecard and a fresh session reproduced the precheck's
opening hash exactly.

### Step 1 — ACTION6, data `{x: 32, y: 32}`
| field | predicted | observed | verdict |
|---|---|---|---|
| `http_status` | **500** | **200** | **MISS — the central error** |
| `attempts` | 1 | 1 | **hit** |
| `n_frames` | `null` | 1 | **miss** |
| `distinct_frames` | `null` | 1 | **miss** |
| `intra_batch_changes` | `null` | 0 | **miss** |
| `first_equals_prev_last` | `null` | **false** | **miss** |
| `matches_expected` | `null` (no expectation) | `null` | **hit** |
| consequence | run stops here, `actions_executed 0` | run continues, `actions_executed 1` | **miss** |

Frame shape `[64, 64]`, batch hash `07428bf1030afccc`, frame hash
`f24a3446b02c98c2`. `state` stayed `NOT_FINISHED`, `levels_completed` stayed 0,
`available_actions` stayed `[6]`, `full_reset false`.

### Step 2 — ACTION6, no data
| field | predicted | observed | verdict |
|---|---|---|---|
| executed at all | **no** | **yes** | **miss** |
| `http_status` (counterfactual) | 500 | **500** | **hit** |
| `attempts` | 1 | 1 | **hit** (500 not retryable, as spec said) |
| `n_frames` / `distinct_frames` / `intra_batch_changes` / `first_equals_prev_last` | all `null` | all `null` | **hit** ×4 |
| `matches_expected` | `null` | `null` | **hit** |

Body: Flask's default `500 Internal Server Error` HTML page — an unhandled
server-side exception, not a structured API refusal.

### Steps 3 and 4 — ACTION1, ACTION2
Predicted **not executed**; observed **not executed**. **Hit** ×2 — but for the
wrong reason: I expected the stop at step 1, it happened at step 2. The
counterfactuals I recorded for them (200 / 1 frame / `first_equals_prev_last`
true) remain **untested**, and are now less likely to be right than when I wrote
them, since the state has moved off the opening frame.

### Steps with no offline expectation
Predicted 1, 2, 3, 4; observed exactly that — only RESET carried an expectation and
it matched. **Hit.**

### Tally
**17 hit / 8 miss** over 25 committed calls. But the arithmetic flatters me: the
hits are concentrated in RESET (which the precheck had already pinned) and in the
mechanical `null`-propagation of an error record. The one call that carried real
information content — does ACTION6 work — I got backwards.

### What this run actually established
1. `ACTION6` on tn36 **works when given `{x,y}`** and produces a state change.
   The frozen sequence's premise ("the one whose nominal action is broken") is
   false as stated; the accurate statement is "ACTION6 500s when `{x,y}` is
   omitted".
2. The 500 is **reproducible and shape-dependent**, not transient or load-related.
3. On the cascade question tn36 gives **no usable evidence**: `max_frames: 1`,
   two single-frame batches, zero multi-frame responses. Consistent with the
   precheck's 9/9 single frames, but from only two batches — this game cannot
   distinguish "list is a container" from "cascade appears later" and I do not
   claim it does.
4. What I cannot rule out: that ACTION6 returns >1 frame at other coordinates,
   at other points in the game, or after level progress; that the observed frame
   change is a cursor/rendering artefact rather than game progress
   (`levels_completed` stayed 0 and `state` stayed `NOT_FINISHED`); and whether
   the precheck's own ACTION6-with-`{x,y}` attempts truly 500'd — I read only
   `spec.py`'s summary of them, not the underlying ledger, so I cannot say
   whether the earlier 500s were mis-recorded, differently shaped, or a genuine
   outage that has since cleared.
