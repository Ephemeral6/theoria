# A3 change B — the arm was never trying to win

**Prompt** A3 round-2 candidate framework change B.
**Branch** `ep/change-b`. **Base** `21a724ed`. **Territory** `theoria-arm`.
**Spend** zero. No live ARC call, no model call, no network. Offline only.

## 1. The reading, before any code was written

The order asked whether the arm is even *trying* to win before the theory is
blamed. It is not. The four live carried legs of 2026-07-31, read off their own
artefacts:

| leg | `plan` calls | statuses | tiers entered | plans produced | commits |
|---|---|---|---|---|---|
| `20260731T1240Z-A3-level2-carried` | 1 | `no_goal_declared` ×1 | `[]` | 0 | `[]` |
| `20260731T1310Z-A3-level2-carried-r2` | 9 | `no_goal_declared` ×9 | `[]` | 0 | `[]` |
| `20260731T1430Z-A3-level2-carried-r3` | 29 | `no_goal_declared` ×29 | `[]` | 0 | `[]` |
| `20260731T1500Z-A3-sk48-carried-l1` | 17 | `no_goal_declared` ×17 | `[]` | 0 | `[]` |
| **total** | **56** | **one status, 56 times** | never | **0** | **empty** |

`plan()` returns before `_tier_pddl`, so `fd_adapter` was never asked and BFS
never expanded a node. `commit.json` is `[]` in all four. Not one plan was
produced, so not one plan was executed, so not one plan could have failed. The
~$35 and 92 actions did not buy a losing search; they bought exploration that
nothing in the record called exploration.

**Point 2 of the order was the whole story.** Both carried manuals declare no
`goal` section, and both say so deliberately and at length:

* one signs `theorem the_goal_section_is_absent_on_purpose` — *"A goal true in
  the wrong states is worse than none, because the planner stops at the first
  one."*
* the other signs `theorem no_goal_is_signed_and_that_is_deliberate` — *"a
  wrong goal sends the searcher after a fiction and costs the level."*

Those are good arguments, made by the desk, written down. The defect is not in
`inner/plan.py` either: its `no_goal_declared` detail already says, correctly,
that this is a gap in the manual and not an unsolvability claim.

**The gap is between them.** `no_goal_declared` is a leaf value that
`inner/loop.py` compares against `"sat"` and drops. Nothing accumulates it.
Nothing in `summary()`, `RUN_STATE.json`, `turn_series.json` or the campaign
scoreboard says the arm held no winning condition for the entire leg.

## 1b. Master moved under this branch twice, and took two findings with it

This branch was cut at `21a724ed`. It was rebased twice, both times cleanly,
and the record of what that changed is kept rather than smoothed over.

**First move — `dc081309`, `P12-probe-economics` (commit `79b948a1`).** That
session reached the same diagnosis from the same four legs and answered the
*telling* half: `plan.surprises_from` now fires `heuristic_miss` on
`no_goal_declared`, once per playbook token, so the desk is told. This branch
was rebased onto it rather than argued against it; `inner/loop.py` now carries
both that firing and beat 3b below. Two corrections follow:

* The claim "nothing ever asks for a goal" was true when this branch was cut
  and is **no longer true**. `inner/goal.py`'s docstring and `DECISIONS.md`
  D-A3-B-001 say so where the original wording was.
* The one defensible reuse of an existing surprise kind is now spent, and spent
  well — `heuristic_miss` is the computational family, whose book is the
  playbook, which is where a goal belongs. Change B therefore fires nothing at
  all: a second surprise for the same fact would call the desk twice for one
  gap.

What is left for change B, and is untouched by `79b948a1`:

* the **record**. A leg that never holds a goal still reports
  `levels_completed: 0` beside a plan history a reader has to reconstruct from
  `plan.json` by hand, and the campaign scoreboard still cannot separate a
  campaign that searched and lost from one that never searched.
* the **criterion**. `79b948a1` keys its firing on the playbook token, so a
  rewritten playbook that still has no goal speaks up again whether or not any
  new world has arrived to change the answer. That is exactly what
  `proposal_due`'s third conjunct refuses.
* **signed absence versus silence**, which nothing else distinguishes.

**Second move — `27407cb5`, "two stale constants, one shape".** It fixed both
of the suite failures this branch had been reporting as pre-existing
environment drift: the four legs' `env_proxy.log` hashes, and
`OBSERVED_USD_PER_SECOND` for opus-5. Verified: both tests pass on a clean
checkout of `27407cb5` and on this branch. The earlier attribution stands as
history — it was correct when made, and the fix confirms it was not this
branch's doing — but the failures are gone and this branch's gates are green.

**One real defect this branch had, caught by the archive's own check.** The
first draft of `make_manifest.py` put arm-relative source paths
(`inner/goal.py`, `tests/test_goal_state.py`) into `files[]`.
`armtools/verify_provenance.py` check 10 resolves `files[]` against the *run
directory* and went red with "listed, not shipped". That is the check doing its
job on this ticket's own artefact. Fixed: `files[]` now holds this run
directory's four files, and the seven delivered sources are hashed under
`sources[]`, which is this manifest's own key and no reader's contract.

## 2. What was built

`inner/goal.py` — goal-absence as a first-class state. Three things, and one
refused.

1. **Names the state.** `mode` ∈ {`planning`, `exploring_no_goal`,
   `no_manual`}, and a `exploring_no_goal` further separates an absence the
   manual *signed* (a theorem arguing for it) from mere silence. Those read
   identically in the old record and are not the same thing.
2. **Carries a criterion for proposing a goal**, `GoalState.proposal_due`,
   with four conjuncts each of which names the number it read when it refuses.
   The criterion is taken from what the manuals themselves said they were
   waiting for — new world — so it counts **distinct states**, not turns and
   not dollars. A hundred turns over the same twelve states buys nothing.
3. **Says so in the record**: per turn (`turns.json`), per run (`summary()`,
   `RUN_STATE.json`), and as three scoreboard columns in `turn_series` rows and
   four totals in `campaign_series`.

**Refused: an eighth surprise.** `inner/surprise.py` closes the set at seven
and says in its own constructor that an eighth is a change to `Theoria.md`
1.10(d), not to a file. Reusing `search_timeout` would be a lie in the ledger —
no search ran. So the `propose` rung buys **no model call of its own**: it parks
a rider that travels on the next theorize call a surprise has already paid for.
Constraint 8 is untouched and `Register.audit()`'s arithmetic does not move.

**The rungs**, weakest first, default `off`:

| rung | record | decisions changed | model spend |
|---|---|---|---|
| `off` (default) | nothing | none | none |
| `record` | full block per turn + per run | none | none |
| `propose` | + booked proposals and their answers | one rider on a call already made | none |

Switch: `TheoriaArm(goal_protocol=...)`, `Campaign(goal_protocol=...)`,
`python -m harness.campaign --goal-protocol {off,record,propose}`.

## 3. Offline evidence — `evidence.py` → `evidence.json`

**Part 1, the loop end to end against `proxy/mock`** (no key, no network, no
model call, no ARC quota, scratch spend pool):

| | `off` | `record` |
|---|---|---|
| actions | 6 | 6 |
| model calls | 0 | 0 |
| turn-record keys | …no `goal` | …**`goal`** |
| turns carrying a goal block | 0 | 1 |
| `summary()` has `goal` | `false` | `true` |
| `RUN_STATE.json` has `goal` | `false` | `true` |

An offline run makes no model call, so it never gets a compiled manual, so its
honest mode is `no_manual` — and the state machine *says* `no_manual` rather
than "exploring without a goal". That distinction working on the one case the
mock can produce is worth as much as the case it cannot.

**Part 2, the scoreboard**, from real `plan()` reports on real compiled books —
one manual with a reachable goal (`sat` ×6, plan produced), one identical
manual with the goal clause deleted (`no_goal_declared` ×6, no plan) — through
`armtools.archive.turn_series` and `Campaign.campaign_series` unmodified:

| campaign total | `off` (before) | `record` (after) |
|---|---|---|
| `turns` | 12 | 12 |
| `level_boundaries` | 0 | 0 |
| `turns_planning` | 0 | **6** |
| `turns_without_goal` | 0 | **6** |
| `turns_not_measured` | **12** | 0 |
| `goal_proposals_due` | 0 | **5** |

Both campaigns complete zero levels. Before, they are indistinguishable. After,
the scoreboard separates the six turns that were searching from the six that
had nothing to search for — and `turns_not_measured: 12` is why `None` is not
`False`: a campaign of unmeasured legs must not report itself as one that
always had a goal.

(`goal_proposals_due: 5` on six no-goal turns is correct for the `record` rung:
turn 1 refused on the evidence conjunct — 3 distinct states against a bar of 4 —
and `record` observes without booking, so the bar never moves. On `propose` the
first would be booked and the bar would move.)

## 4. Negative controls

Acceptance, not garnish. Every check here that can say *no* is shown saying no.

* **The ticket's control — an arm WITH a goal still plans and commits, at every
  rung.** `test_an_arm_with_a_goal_still_plans_and_commits_at_every_rung`
  (parametrised `off`/`record`/`propose`): `plan` → `sat`, plan
  `[["key",1],["key",1]]`, backend `object-state-bfs`; `commit.execute` →
  `outcome: completed`, `planned == executed == matched == 2`,
  `abandoned_at: None`. The goal state calls it `planning` and refuses to ask,
  **by name**, on conjunct one.
* **Its pair** — one edit to the same manual, deleting the goal clause, and the
  same machinery reports `exploring_no_goal` and `due: True`. Without the pair,
  `planning` could be a constant.
* **Four conjunct refusals, one test each**: a manual that already has a goal;
  no compiled predictor; not enough new distinct states; the leg's proposal
  budget spent. Plus `test_the_criterion_can_say_yes` as the positive control —
  without it, four refusals are also satisfied by a criterion that never fires.
* **The bar moves after a booking**, so the criterion fires once rather than
  every turn thereafter.
* **The signature detector is narrow**: `theorem the_goal_is_probably_the_socket`
  is not an absence signature, and a manual that declares a goal can never
  carry one.
* **`None` is not `False`** on the scoreboard columns, and a reconstructed
  spine (no `turns.json`) reports not-measured rather than inventing a mode.

## 5. Gates

Both gates green, and both also run on a **clean checkout of the same master
commit** (`.worktrees/change-b-baseline` at `27407cb5`) so the delta is
attributable rather than asserted.

```
cd theoria-arm && python -m pytest -q
  ep/change-b        515 collected, all pass, exit 0
  27407cb5 (clean)   481 collected, all pass, exit 0
```

+34 is exactly `tests/test_goal_state.py`.

```
cd theoria-arm && python verify.py

  ep/change-b
    [1/3] suite
       ok    515 tests collected, suite green
    [2/3] one real run -- the whole arm, offline against proxy/mock
       ok    game <dev-pile id>, budget 6 actions, no key, no network
    [3/3] artefact self-check
       ok    11 ledger records (7 env_steps), 17 run files, all 17 manifest
             fields, sealing clean, dev pile only
    theoria-arm: green -- suite, one offline run, artefact fields
    EXIT=0

  27407cb5 (clean)
    ... identical, except "481 tests collected".
    theoria-arm: green -- suite, one offline run, artefact fields
    EXIT=0
```

**What the gates caught on the way, and it was this ticket's own artefact.**
Earlier in this session both gates were RED with two failures. Neither was
change B — both reproduced on a clean `dc081309` worktree, and `27407cb5`
("two stale constants, one shape") fixed both. But after that, check 10 of
`armtools/verify_provenance.py` went red on **this run's manifest**: the first
draft of `make_manifest.py` put arm-relative source paths into `files[]`, and
that check resolves `files[]` against the run directory. "listed, not shipped"
was correct and this branch was wrong. Fixed as described in §1b. A gate that
had never been seen to say no about this ticket would not have shown anything.

Also run: `git diff --name-only master HEAD` is 14 files, all under
`theoria-arm/` plus the one appended `PARTNER_SYNC.md` paragraph; a scan of the
changed files against `arc-recon/data/piles.json` finds **zero** sealed-pile
ids or stems; no credential value anywhere; zero API calls, zero model calls,
$0.00.

## 6. Residual gaps, stated plainly

* **No live leg has run under `record` or `propose`.** The behaviour of the
  rungs on a real carried manual is argued from artefacts and exercised
  offline; it is not measured. That is what the default `off` is for.
* **`exploring_no_goal` is not reachable in a mock run**, because offline means
  no manual. Part 2 gets the state from real plan reports on real books rather
  than from a real loop; the loop's own wiring for that mode is covered by unit
  tests, not by an end-to-end run.
* **The rider's effect on the desk is unmeasured.** Whether a goal request that
  rides along actually gets a goal, an argued refusal, or silence is exactly the
  three-way outcome `answer_proposal` records — and no live call has ever
  carried one.
* **The criterion's constants are judgement, not measurement.** Four new
  distinct states (matching `MIN_NEW_FRAMES_BETWEEN_THEORIZE`) and three
  proposals per leg. Nothing has been run that would calibrate either.
* **Change B does not make the arm win a level.** It makes the arm know, and
  the record say, that it has never been trying to. Whether naming the state
  leads to a goal being signed is the next round's question.
* **Half of the original finding was answered on master while this was being
  written**, by `79b948a1` (`P12-probe-economics`), which fires `heuristic_miss`
  on `no_goal_declared`. This branch was rebased onto it; §1b says what that
  changes. What is left unmeasured is whether the two together do better than
  either alone — nothing has run under both.
* Changes A (probe economics) and C (desk evidence presentation) were **not**
  touched: one change per round.
