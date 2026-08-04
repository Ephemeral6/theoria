# A25 — the action economy

Board item A25: *the arm spends its action budget on theorising instead of
playing. Make the actions-per-desk-call ratio a measured, tunable quantity
instead of a constant nobody chose.*

Offline throughout. No ARC command, no model call, no credential read, no
sealed-pile contact, $0.00.

---

## 1. The constant is 4. The ratio is not.

`MIN_NEW_FRAMES_BETWEEN_THEORIZE = 4` has sat in `inner/loop.py` since
2026-07-28. Read off the fifteen legs in this repo that ever reached a desk:

| | |
|---|---|
| adjudications | 73 |
| paid invocations | 104 |
| billed actions | 226 |
| desk spend | $148.89 |
| **actions per adjudication** | **3.096** |
| **actions per paid call** | **2.173** |
| usd per action | $0.659 |

Three reasons the constant and the ratio disagree, and all three are constants
nobody chose either.

**The gate is checked once per turn; the turn may adjudicate twice.**
`MAX_THEORIZE_PER_TURN = 2`, and the check sits *above* the `while` loop, so the
second round never meets it. **24 of 73 adjudications had a gap of zero billed
actions.** They cost **$42.40** — 28% of every dollar this arm has ever paid a
desk — and they are where the waste concentrates: 15 of the 22 scored zero-gap
calls changed nothing downstream (68%), against 8 of 33 (24%) for calls with at
least one new action behind them.

**Each adjudication may buy two more invocations.** `theorize.REPAIR_ROUNDS = 2`
gives the desk up to two extra passes at a manual that will not compile. **31 of
104 paid calls are these, $32.53, 22% of desk spend**, and by construction they
see no new evidence — the same brief again.

**The gate counts what the bill does not.** `_frames_this_level()` is
`len(store.steps) - levels.start`, and `loop._record` appends a Step for *every*
arm-level command, including the ones the world refused. **16 adjudications were
released by 34 commands that bought no transition.** The worst is
`20260801T001851Z-R1b-sk48-b`, where six were failures during the refusal wave —
and the message the arm wrote into `turns.json` said "new transition(s)".

## 2. Did the calls buy anything?

The books are snapshotted `revNN-before-theorize` / `revNN-after-theorize`
around every call. Both revisions were recompiled offline and replayed over the
transitions that arrived *after* the call. If the two predictors draw the same
frame at every subsequent step, the call bought a differently-worded manual and
nothing else.

| verdict | n |
|---|---|
| changed a later prediction | 31 |
| **changed no later prediction** | **23** |
| gained a predictor where there was none | 4 |
| unscorable — no snapshot pair | 10 |
| unscorable — no later transition | 5 |

**23 of 58 scored adjudications (39.7%) changed no later prediction, at a cost
of $20.15.** Ten came back with a byte-identical `theory.dsl`; the other
fifteen were genuine edits that moved nothing the arm predicts.

## 3. Every constant that gates the cadence

`python -m armtools.action_economy constants` — full output in `constants.txt`.
The column that matters is the effective actions-per-call each one imposes if it
alone were binding:

| constant | value | ratio |
|---|---|---|
| `MIN_NEW_FRAMES_BETWEEN_THEORIZE` | 4 | **2.0** (the floor is 4 frames, but a turn may spend 2 calls on them) |
| `MAX_THEORIZE_PER_TURN` | 2 | **2.0** |
| the budget escape (`actions_left > floor`) | — | **1.0** — unnamed in the source; at the end of a leg the floor stops applying entirely |
| `MAX_PROBES_BETWEEN_THEORIZE` | 4 | — downgrades a probe to an exploration; an exploration still makes a frame, so it cannot slow the desk |
| `MAX_VACUOUS_PROBES_IN_A_ROW` | 3 | — same shape |
| `REPAIR_ROUNDS` | 2 | — extra invocations without extra actions |
| the empty-manual escape | — | — a run with no manual skips the floor |
| level re-arming | — | — never observed: no leg here has completed a level |
| `MIN_NEW_STATES_FOR_PROPOSAL`, `MAX_PROPOSALS_PER_LEG` | 4, 3 | — ride on a call a surprise already paid for |
| `LEG_USD_CAP` | 25.0 | — not a cadence knob, but the multiplier that turns a cadence into an action count |

## 4. The switch

`inner/economy.py`. `ActionEconomyConfig()` — the default — is the historic gate
**decision for decision and string for string**, pinned three ways in
`tests/test_action_economy.py`: the refusal string character for character
against the pre-A25 literal, the decision exhaustively over 264 input
combinations against a transcription of the old predicate, and the round cap
against `MAX_THEORIZE_PER_TURN`.

Plumbed on the one path `harness/run.py` already uses for the other four knobs:
`--action-economy {today,one-round,floor-8,floor-12,actions-unit,adaptive,one-round-floor-8}`,
also settable with `THEORIA_ACTION_ECONOMY=1` plus `THEORIA_ECONOMY_*`. Every
run now writes `action_economy.json` — a new file, so a default leg's existing
artefacts are unchanged to the byte.

## 5. What the same money would have bought

`python -m armtools.action_economy replay` — full output in `replay.txt`.

**Control fidelity: 71 of 73 recorded adjudications reproduced.** The two the
control refuses are both on `20260728T015354Z-g50t-first-contact`, which started
at 01:53Z on 2026-07-28 — eight minutes *before* the gate landed in `6717a7e0`
at 02:01Z. It is the leg whose one-action-per-adjudication behaviour the
constant was written to stop, so a control that refuses its calls is the control
working, not the control drifting.

| policy | fired | refused | usd | acts/$ | actions at a $25 leg | vs today |
|---|---|---|---|---|---|---|
| today | 71 | 2 | 146.20 | 1.41 | **35.2** | 1.00 |
| actions-unit | 70 | 3 | 140.54 | 1.47 | 36.6 | 1.04 |
| adaptive | 64 | 9 | 140.54 | 1.38 | 34.5 | 0.98 |
| one-round | 49 | 24 | 110.65 | 1.86 | 46.5 | 1.32 |
| floor-8 | 38 | 35 | 79.03 | 2.39 | 59.8 | 1.70 |
| one-round-floor-8 | 26 | 47 | 63.09 | 3.00 | 74.9 | 2.13 |
| floor-12 | 24 | 49 | 31.07 | 5.09 | **127.1** | 3.61 |

**g50t level 1 needs 78 actions.** Today's cadence projects 35. Only `floor-12`
clears 78 on this projection — and it clears it by refusing 21 adjudications the
replay scores as having changed a later prediction. That is the trade, stated
rather than hidden: **this measurement does not show that a wider floor is
free.**

The projection rests on one measured fact: a desk call's price does not rise
with the wait before it. `corr(step_idx, cost_usd) = -0.039` over 65 priced
calls; mean cost $1.77 at gap 0, $2.31 at gap 4, $2.07 at gap 5. Nine of the
fifteen legs ended on `spend_gate_tripped`, so money is the binding constraint
and the cadence *is* the action count.

## 6. What this does not establish

* **The counterfactual is a replay, not a simulation.** Skipping a call changes
  what the arm does next, and the record cannot say what frames a different arm
  would have seen. Only the strict half — which recorded calls a policy refuses
  and what they cost — is a fact. The $25 column is a projection and says so.
* **`productive_calls_refused` overstates the loss, by an unknown amount.**
  `Register.handled` closes *all* pending surprises in one call, so a deferred
  adjudication's work is largely absorbed by the next one — the surprise stays
  pending, it does not evaporate. The replay cannot model that, so it charges
  the full downstream verdict of every refused call against the policy that
  refused it. Every non-`today` row is pessimistic.
* **10 adjudications could not be scored at all** — 2 on the aborted
  first-contact legs, which predate snapshotting, and 8 whose before or after
  snapshot is not on disk (`Books.snapshot` copies only files that exist, so a
  cold start's first `before` is an empty directory, and git does not track
  those).
* **`defer_kinds` ships typed and empty.** The measurement did not support
  putting anything in it: the 8 adjudications triggered by `probe_refutation`
  alone were productive 6 times, and the kind that co-occurs with the inert
  calls is `replay_mismatch` — certify saying the manual contradicts the
  recorded world, which no policy here may sit on.
* **The adaptive policy is the weakest of the seven on this archive** (0.98x
  today). It is shipped because its signal is available *at* the call while the
  downstream verdict is not, but the archive does not recommend it. Its presence
  is not an endorsement.
* **The level-boundary re-arming path has no measurement on either rung**,
  because no leg in this repo has ever completed a level.
* **`REPAIR_ROUNDS` is measured and not made switchable.** It decides how many
  invocations one adjudication may spend, not when the desk is called. Moving it
  here would be two changes wearing one switch. It is the largest single
  unaddressed item: $32.53, 22% of desk spend, zero new evidence.

## 7. A defect found and deliberately not fixed

The evidence gate counts failed commands as evidence, and the line it writes
into `turns.json` calls them transitions. Fixing the counter would change
default behaviour, which this ticket may not do. The `actions-unit` policy is
the switchable form of the fix, and it is off.

Related, and also left alone: `world/frames.FrameStore`'s docstring says
"Failed commands are not states". That is true of `store.grids` and false of
`store.steps`, which is the attribute the gate reads. The sentence is
load-bearing for readers of `grids`, and the file is not this ticket's to
rewrite.
