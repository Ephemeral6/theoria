# RUN_STATE — A27, the level-boundary detector

**Cell** A27 · **Territory** theoria-arm · **Branch** `w/a27-level-boundary` ·
**Base** `b4540026` · **UTC** 2026-08-02T21:00Z · **Spend** $0, 0 ARC actions,
0 model calls, no network.

## What was asked, and what the evidence said back

The board item states that the arm cannot see a win even if it gets one. Reading
`inner/levels.py`, `inner/loop.py` and `harness/arc.py` before writing anything
showed that claim is half wrong, and the half that survives is sharper than the
original:

* **Not blind to the boundary.** Every `_record` call — every recorded step,
  including probes and commit steps — pushes the envelope's `levels_completed`
  into `LevelLog.observe`, and an increase fires `_on_level_boundary`
  synchronously. `state == "WIN"` is checked at the top of every turn. Both
  candidate signals are handled and neither waits for the close.
* **Blind to the scorecard.** `score`, `level_scores`, `level_actions`,
  `level_count` and `level_baseline_actions` exist on no gameplay response, and
  the only fetch of a scorecard in the whole arm is `close_scorecard` in
  `_finish` — after `_main_loop` returns, on a card that D-015 says can never be
  re-read. So the leg could never hold its own denominator.

The brief was followed where it was right and contradicted where it was not; the
contradiction is recorded in `DECISIONS.md` D-A27-001 rather than smoothed over.

## Built

**`inner/scoreboard.py`** — `ScoreWatch`, the second witness.

* Normalises readings from two sources into one shape:
  `reading_from_envelope` (free, every step; `score` is `None`, never `0.0`,
  because the field does not exist) and `reading_from_scorecard` (the four
  fields no envelope carries; run row selected by `guid`, never summed, with
  `row_selected_by` saying which).
* Diffs each source against **its own** history and fires `score_moved`,
  `level_score_moved` (naming the level) and `level_boundary` (naming the
  source). A first reading is a floor and never a jump; a decrease is never a
  boundary.
* `corroborate()` compares the envelope counter against the scorecard's and
  reports `agree` / `disagree` / `envelope_only` / `scorecard_only` /
  `not_measured` — it reports a disagreement, it does not resolve one.
* `reach()` is the denominator: the level's reference cost, the actions spent on
  it, the actions left, the gap, and a sentence saying that a baseline is a
  reference cost and **not** a lower bound.
* `boundary_verdict()` separates `not_measured` (`null`) from `measured_absent`
  (`false`). This is the negative control's whole subject.

**`harness/arc.py:read_scorecard`** — `GET /api/scorecard/{card_id}`, the
read-only surface `arc-recon/client.py` has had all along. Non-destructive, one
attempt, never raises, spend gate asked first. **`harness/budget.py`** gains
`check_readonly()` / `read()` / `budget.reads` so a read costs a command and no
action, and so a leg inflated by reads cannot be mistaken for one whose retry
envelope ran away.

**`inner/loop.py`** — the watch is fed in `_record` (free rung, every step),
consulted in `_main_loop` as beat 0 **before theorize** (the denominator is only
worth anything to a leg that still has money), fed the closing card in `_finish`,
and reported in `summary()`. At a boundary, `_witness_the_win` writes
`witnessed_wins.json`: the last frame of the cleared level, its hash, the level's
opening hash, the signal, the action, the actions the level cost, the reach
reading at that instant, and the corroboration. It cannot end a leg — every
failure is caught and recorded on the event.

**Rungs.** `off` (byte-identical to before), `envelope` (**default**; free), and
`scorecard` (opt-in; spends requests). Defaulting the free rung to *on* departs
from `inner/goal.py`'s `off` default, deliberately: change B has been
prepared-and-not-adopted since 2026-07-31 and has never run (GAP A3-B-1), and the
`envelope` rung spends nothing. The reasoning is in D-A27-001 decision 4.

## The path from a boundary to a goal clause

Designed in full, implemented to the seam.

`Theoria.md` 1.8 puts the goal clause in the manual. R1b measured what the desk
does when asked for one with no evidence: three refusals in three asks, each
resting on the fact that no winning state had been seen — arguments about reach,
not confidence (`inner/goal.prompt_rider`'s own reading of them). A recorded
boundary is exactly that missing evidence: the step carrying the increment is the
first frame of the next level, so the step before it is a state the world was
observed to treat as won.

* **Observation half — done and wired.** `witness_from_boundary` +
  `witnessed_wins.json`. Written to disk the instant the boundary exists, because
  a leg that dies two actions later must not take the only positive example in
  the project's history with it.
* **Proposal half — written, not wired.** `witness_rider` renders the ask as
  Markdown and is a pure function. Nothing calls it. A rider must ride on a call
  a surprise has already bought (`inner/surprise.py` closes the set at seven);
  the call it should ride on is the one a boundary provokes; no leg has ever
  crossed a boundary, so that call's shape has never been observed. Wiring it now
  would be a guess dressed as a design. The first recorded boundary is the
  evidence that decision needs.

## Negative controls

They are the acceptance, not garnish:

* a 12-step flat leg on the `envelope` rung → `measured_absent`, zero events;
* a single reading → `not_measured` / `boundary_observed: null`, never `false`;
* a first reading against a card already carrying score 3.0 and 3 levels → no
  event (a floor, not a jump);
* a decrease → no event;
* the two sources alternating → no event (separate histories);
* the `off` rung → nothing read, nothing in the summary;
* a leg with no boundary → empty `witnessed_wins`, **no file on disk**;
* a scorecard claiming a completed level, fed straight into the watch → the
  watch fires, `LevelLog` does not, `witnessed_wins` stays empty, and
  `corroborate` says `disagree`;
* an instrument that raises at a boundary → the boundary still lands, the error
  is on the event, the leg continues;
* a mock baseline → labelled as a mock's.

And the synthetic positives that prove the detector can fire at all: a score
jump, a per-level score jump naming the level, a counter jump on each source.

## Honest state

* **No recorded leg contains a boundary.** 2,700 `env_step` rows across three
  arms: `levels_completed` 0 or absent, `state` `NOT_FINISHED` or absent, never
  `WIN`. 47 scorecards: score 0.0, levels 0, all `level_scores` zero. The
  detector is untested on a real positive and says so in a test.
* **The paid rung has never dialled anything.** Every gate here is offline, so
  the `GET` is exercised only against a stubbed transport. Whether `proxy/` (a
  different track) forwards a GET at all is unverified from this side.
* **The 对账义务 is still owed.** Readings go into the summary and the turn
  records, not into `env_step`, so `archive.reconcile` still writes
  `score_reconciliation: "unavailable"`.
* **The archive still carries the mock's `[8, 8, 8]` unlabelled** in seven files.
  Named in `MEASUREMENT.json`; not rewritten.
