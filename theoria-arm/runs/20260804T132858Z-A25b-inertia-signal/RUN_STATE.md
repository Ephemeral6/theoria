# A25b — the audit became a signal, and the signal became a switch

Board item A25 (action economy), second pass. A25 measured that the gate claims
four actions per desk call while the ledgers say 3.096, and that 23 of 58
scored calls changed no later prediction. That work is on master. This asks
what a running arm can do about it.

Offline throughout. No ARC command, no model call, no credential read, no
sealed-pile contact, $0.00.

**The A26b legs in flight were never read, and `census.json`'s `skipped` list
is empty — which is not the same statement.** This work was done in a worktree
cut from master, and the two A26b run directories are *untracked* in the main
tree, so a fresh checkout does not contain them: there was nothing under
`runs/` for the `A26` skip marker to refuse. The guard is still the reason a
run in the main tree would be safe, and it is still in `SKIP_MARKERS`; on this
census it never fired because the legs were absent, not because it caught them.
Recorded here because an empty `skipped` list would otherwise read as "the
guard worked".

---

## 1. The arm can tell, at the call, that it bought nothing

A25's verdict needs the transitions that arrived *after* the call, so it can
explain a finished leg and change nothing about a running one.
`inner/inertia.py` asks the same question over the frames the arm already has,
the instant the call returns: recompile the two book revisions
`inner/theorize.run` snapshotted around the call, replay both over the recorded
prefix, and compare the drawn frame at every step.

Over the 73 archived adjudications:

| at-call verdict | n |
|---|---|
| moved a prediction | 32 |
| **predicted exactly what the old manual predicted** | **25** |
| gained a predictor where there was none | 6 |
| no snapshot pair on disk | 10 |

**54 calls can be scored both ways, and the two verdicts never disagreed —
23 inert, 31 productive, in either direction.** Precision 1.00, recall 1.00,
against a base rate of 0.426.

That is not luck and it should not be read as an independent validation. It is
mechanical: `step` is a fold, so two revisions that have parted company about a
state stay parted, and **31 of the 31 moved-and-changed calls have a tail that
diverges at its very first step** — the tail told us nothing the prefix had not
already said. The prefix windows are not degenerate (5 steps minimum, median
13, max 29), so the agreement is not an artefact of an empty comparison. What
the prefix genuinely cannot see is a rewrite whose only effect is under an
action the arm has never taken. On this archive that cell is empty; it is a
real hole and it is recorded as one.

**The at-call signal also sees $18.67 the audit is structurally blind to.**
Three calls are the last of their leg, so the audit has no tail and returns
`no_later_transition_to_predict`. Two of them —
`20260801T001851Z-R1b-sk48-b` #1 at $8.37 and `20260801T044640Z-R2b-sk48-b` #2
at $10.30 — the at-call signal scores inert. The A25 figure for money spent on
calls that bought nothing was $20.15; measured at the call it is **$38.82**,
and the difference is two end-of-leg calls nobody could previously judge.

## 2. Four levers, all off

`inner/economy.py` gains four fields. `ActionEconomyConfig()` is unchanged in
behaviour and every one of them is at its historic setting.

| lever | what it does | board item's candidate |
|---|---|---|
| `inertia = off \| measure` | compute the at-call verdict; decide nothing | — |
| `adapt = by_prediction_delta` | widen the floor after an inert call, reset on a productive one | "adapt the floor to how much the last call changed" |
| `defer_after_inert` | refuse a call whose pending kinds are all kinds an inert call already covered, until `adapt_max` new evidence arrives | "defer while surprises are of a kind the manual already explains" |
| `min_surprises` | a floor on pending surprises, skipped entirely at the historic 1 | "a minimum new-information threshold" |
| `gate_every_round` | ask the kind clauses before a *continuation* round too | (see §4) |

A config that acts on a signal it does not compute **raises**. A policy that
silently does nothing is indistinguishable, in a round's results, from an
intervention that did not work.

Plumbed on the one path `harness/run.py` already uses: `--action-economy`,
whose `choices` is built from `POLICIES`, so five new policies are selectable
without touching the flag.

## 3. Actions bought per dollar, per policy

`replay.txt`. Two readings, because one of them has a bias worth naming:
`cover` credits a call with the actions between it and the previous one, so
refusing a leg's **last** call drops that leg's trailing actions out of the
numerator; `whole` divides every recorded action by the reduced bill, which is
the pessimistic reading — the leg goes exactly as it went, for less money. The
truth is between them.

| policy | usd | acts/$ (whole) | at the $25 cap | vs today | +inert refused | +productive refused | inert per productive |
|---|---|---|---|---|---|---|---|
| today | 146.20 | 1.546 | 38.6 | 1.00 | — | — | — |
| **measure-inertia** | **146.20** | **1.546** | **38.6** | **1.00** | **0** | **0** | — |
| actions-unit | 140.54 | 1.608 | 40.2 | 1.04 | 0 | 0 | — |
| adaptive | 140.54 | 1.608 | 40.2 | 1.04 | 6 | 0 | — |
| defer-explained | 146.20 | 1.546 | 38.6 | 1.00 | 0 | 0 | — |
| **defer-explained-every-round** | 134.53 | 1.680 | 42.0 | 1.09 | 10 | 2 | **5.0** |
| **inert-guard** | 125.31 | 1.804 | 45.1 | 1.17 | 12 | 4 | **3.0** |
| min-info-2 | 105.26 | 2.147 | 53.7 | 1.39 | 4 | 4 | 1.0 |
| one-round | 110.65 | 2.042 | 51.1 | 1.32 | 14 | 6 | 2.3 |
| inert-guard-one-round | 102.50 | 2.205 | 55.1 | 1.43 | 17 | 9 | 1.9 |
| floor-8 | 79.03 | 2.860 | 71.5 | 1.85 | 12 | 12 | 1.0 |
| one-round-floor-8 | 63.09 | 3.582 | 89.6 | 2.32 | 19 | 16 | 1.2 |
| floor-12 | 31.07 | 7.274 | 181.9 | 4.71 | 15 | 20 | 0.75 |

**The finding is in the last column.** Every row saves money by refusing calls,
and refusing calls at random would save money too. The floors buy their gain by
refusing everything: `floor-12` gets 4.7x by refusing *more productive calls
than inert ones*. The signal-driven levers are the only ones that discriminate
— `defer-explained-every-round` refuses five inert calls for every productive
one, `inert-guard` three — and they are correspondingly modest, 1.09x and 1.17x.

Neither reading of acts/$ gets any policy to 78 in aggregate. `floor-12`'s
181.9 is a projection built on refusing 20 calls the audit says changed a later
prediction; it is in the table to show where the curve stops paying, not as a
recommendation.

## 4. Per leg, and which leg's outcome would have changed

The strict half is a fact: **which recorded calls a policy refuses**. Every leg
not in that list ran exactly as recorded under that policy. The projection half
is a projection and is marked as such.

* `measure-inertia` and `defer-explained` ran **0 of 15 legs** differently.
* `actions-unit` 1, `adaptive` 2, `inert-guard` 4,
  `defer-explained-every-round` 4, `min-info-2` 10, `one-round` 10,
  `inert-guard-one-round` 10, `floor-8` 11, `floor-12` 11,
  `one-round-floor-8` 13.
* On the projection, against **each leg's own level-1 boundary** — 78 for
  g50t, 61 for sk48, read from each leg's own `env_meta` — `inert-guard` newly
  clears one leg (`20260731T1500Z-A3-sk48-carried-l1`, 8.2 acts/$ against a
  boundary of 61), `one-round` three, `inert-guard-one-round` four, `floor-8`
  four, `one-round-floor-8` five, `floor-12` six.

A25's replay quoted 78 for every leg. A third of the archive is sk48, whose
level 1 costs 61; the number is in each leg's own ledger and there was no
reason to borrow g50t's. Six legs recorded no `env_meta` at all (a carried leg
does not reopen the environment); those borrow the same game's number from a
leg that did, and the borrowing is written down in
`census.json`'s `level_baseline_source`.

**No policy was chosen against one leg.** The two policies that look best on
the discrimination column are best on the pooled figure and on 4 of 15 legs
respectively; the two that look best on the pooled projection (`floor-12`,
`one-round-floor-8`) are the two that refuse the most productive calls, and
that is stated rather than hidden.

## 5. `defer-explained` refuses nothing, and that is the finding

The lever aimed at "a kind the manual already explains" refuses **zero** calls
on this archive. Not because the condition never holds: it holds 8 times. **All
8 are second rounds of a turn.** The historic gate is checked once per turn,
above the `while` loop, so the second adjudication never meets it — which is
also why 24 recorded calls had a gap of zero billed actions.

`gate_every_round` is the version that can reach them, and the replay counts
what each policy would have refused had it been asked
(`continuation_rounds_the_kind_clauses_would_refuse_if_asked`: 8 for
`defer-explained`, 15 for `min-info-2`). A null that is only a null because the
question was never put is a different thing from a null result, and the
artefact now says which it is.

**The guard lapses, and it has to.** Nothing clears `_inert_kinds` except a
call that fires, so an unbounded guard that refuses every call is never
cleared. The first version parked the desk for ten consecutive adjudications on
`20260728T083400Z-E3-sk48-carried-v2` and the leg never theorised again. The
clause now applies only while fewer than `adapt_max` new frames have arrived:
do not pay twice for the same question **on substantially the same evidence**.

## 6. Negative controls

* **`measure-inertia` equals `today` in every behavioural field** — fired,
  refused, dollars, actions, both acts/$ readings, and the per-leg fired
  counts. Computing the signal changes no decision. If merely measuring moved
  the numbers, no row in §3 would mean anything. Pinned in
  `tests/test_action_economy_inertia.py`.
* **The published A25 census reproduces byte for byte, and then survives the
  refactor.** Before any change, `census --json` reproduced
  `runs/20260802T131013Z-A25-action-economy/census.json` at
  `85b4c0d0b18a49dd65afea2a6f7d641b56b03ba9a0573fa2d5c304b91c934a03` — the hash
  in that run's own manifest. After moving the compile-and-replay machinery
  into `inner/inertia.py`, a recursive comparison of the two documents reports
  **0 changed values**; the only difference is three added keys
  (`at_call` on 73 calls, `level_baseline_actions` on 15 legs, `at_call_signal`
  at the top).
* **A revision compared against itself is inert.** If that ever fails, every
  `moved_a_prediction` in the census is finding differences that are not in the
  manuals.
* **A missing snapshot, an uncompilable revision and an empty window are
  unknowns, never inert.** `bought_nothing` is three-valued and the floor moves
  on neither unknown. A measurement that raises is recorded as an unknown and
  does not end the leg.
* **`min_surprises` at its historic 1 never refuses**, for any pending count,
  with the economy switched on. A knob that changes behaviour at its historic
  setting is not a knob.
* **The guard refuses a repeat, not the next question**: a kind the inert call
  never saw, an unattributed call, and a call after a productive one all pass.
* **The default arm never computes the signal**: `inner/inertia.py` is imported
  inside the helper, and the helper returns before importing when
  `measures_inertia` is false.
* **`bool("false")` is True**, so `from_env` parses booleans on the same
  positive whitelist as the master switch rather than through `bool`.

## 7. What this does not establish

* **The counterfactual is still a replay, not a simulation.** Skipping a call
  changes what the arm does next and the record cannot say what frames a
  different arm would have seen. Only the strict half is a fact.
* **`productive_calls_refused` still overstates the loss.** `Register.handled`
  closes all pending surprises in one call, so a deferred adjudication's work
  is largely absorbed by the next one. Every non-`today` row is pessimistic in
  that direction and optimistic in the direction of §3's projection.
* **The at-call signal has never run live.** Everything above is the signal
  computed offline over recorded snapshots. `measure-inertia` is the round that
  buys the live measurement without buying an intervention, and it is the one
  to run next.
* **Two legs' worth of the `whole` reading is noise.** The two aborted
  first-contact legs have one adjudication each; their projections (3.8 and
  8.2 acts/$) move on a single call. The per-leg table now prints the
  adjudication count for exactly this reason.
* **10 adjudications still cannot be scored at all** — no snapshot pair on
  disk. Unchanged from A25 and unchanged by this ticket.
* **`REPAIR_ROUNDS` is still measured and still not switchable.** $32.53, 22%
  of desk spend, zero new evidence. It remains the largest single unaddressed
  item, and it is not a cadence lever, so it does not belong on this switch.
* **The level-boundary re-arming path still has no measurement**, because no
  leg in this repo has ever completed a level.
* **`defer_kinds` still ships empty.** `defer_after_inert` is the version this
  measurement supports; a hand-picked list of kinds is not.

## 8. Reproduce

```bash
cd theoria-arm
python -m armtools.action_economy census --json --out census.json   # ~4 min
python -m armtools.action_economy replay --census census.json
python -m pytest tests/test_action_economy.py \
                 tests/test_action_economy_inertia.py -q
```

`replay --census` against a **shallow** census carries no at-call verdicts, so
an inertia-driven policy degrades to its floor and its row means nothing. The
replay counts and prints that case rather than trusting the operator to
remember it.
