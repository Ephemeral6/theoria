# The manifest learns to say the two things it could not say: 17 of 24, and a negative balance

**Branch:** `z/freeze-e2u3` · **Base:** `e8345aff` (master) · **UTC:** 2026-08-01T12:00Z
**Territory:** `freeze`. `exam/` and `battery/` read-only; asks go to `monitor/inbox/`.
**Cost: $0.00.** Zero API call, zero model call, zero network, zero live run, zero
sealed-pile contact. Lean 4.9.0 offline is the only external binary used. The
programme is over its ceiling and this session had no spend authority; nothing
here needed any.

---

## What this ticket found already done, and what it actually did

Two rulings landed earlier today and both had already been written into the kit
on `master`: the U3/E1 shape-based repair (`freeze/theorem_shape.py`,
`runs/20260801T0700Z-E1-kind-census/`) and the E2 withdrawal of the front-load
endpoint (`freeze/e2_withdrawal.py`, `verify.sh` stage [19],
`runs/20260801T0300Z-R2-E2-RULING/`). So this ticket did not redo them. It did
three things they left open:

1. **Re-ran the census on a different checkout** and confirmed it reproduces.
2. **Measured** the exam-side flip list instead of deriving it — and the derived
   list was an undercount.
3. **Made `MANIFEST.json` readiness read the money**, which nothing did before.

---

## 1 · The census, re-run — 17 of 24, and it reproduces

`recensus.py` (a copy of the 07:00Z census script, retimed) on a fresh worktree
at `master`, Lean 4.9.0, `--probe` off:

| label | before the repair | after |
|---|---|---|
| `discharged` | 14 | **17** |
| `vacuous` | 9 | **2** |
| `unclassified` | 0 | **4** |
| `failing_obligation` | 1 | 1 |
| **attained** | **14 / 24** | **17 / 24** |

**Every per-book label reproduces**, on a different checkout and a different
commit from the run that first produced them. The seven that moved, and why:

| book | before | after | why |
|---|---|---|---|
| `theory-compiler/runs/20260728T080019Z-C4-deadlock-lean` | `vacuous` | `discharged` | `dead` is read as `prune`; (a)(b)(c) discharged from `pat_witness` / `no_goal_pinned` / `level_is_winnable`. **This is the development `STATS_RULES.md:123` names as the paradigm of what U3 means** — E1 used to call it vacuous. |
| …`/verify` (same development) | `vacuous` | `discharged` | same |
| `theory-compiler/lean` | `vacuous` | `discharged` | its invariant is called `Inv`, not `I`; the old (c) hard-coded `defs["I"]` and reported "no `def I` found to check". `theory-compiler` goes 0/7 → 3/7. |
| 4 × `theory-compiler/handover_packages/*/levels/*` | `vacuous` | `unclassified` | their only two theorems are a `Reachable` closure lemma and an existential goal witness — neither is one of §1.2.1's three kinds, so **nothing was ever checked**. `vacuous` is an accusation; this is a confession, and they may not share a word. |

**Every move is `vacuous` → something else.** The repair only ever *removes* an
accusation; nothing that attained stopped attaining. Both genuine vacuity
findings survive by shape rather than by prefix, including the frozen §9.2
negative control `cold-start-a3/theory/generated_l1_vacuous` — 抓不住它就不许冻结.

**One difference from the 07:00Z run, recorded rather than smoothed:** the
target count moved 42 → 46. All four additions are today's live R1/R1b leg
directories, every one `declared_refusal`, none of them a book. The book
population is identical at 24, which is the denominator that matters here — and
it is an engineering denominator, **not** §1.2's E1 rate, whose denominator is
the frozen 19 claim-set games.

---

## 2 · The exam flip list: derived as four, measured as six

The 07:00Z letter named four exam tests. That list was re-derived on the freeze
side from what the repair changed — a record of what another file says, with
nothing that rereads it, which is the exact defect this repo keeps catching.

`exam/u3_census.py` and its tests are **not on master**; they live on
`z/exam-u3-followthrough` (tip `01d627e3`, merge-base `e8345aff`, and its
`freeze/u3.py` is byte-identical to master's `77297975…`). Measured there in a
detached read-only worktree, since removed:

```
$ python -m pytest exam/tests/test_u3_census.py -q
6 failed, 15 passed in 79.91s
```

Two were missed by the derivation:

* `test_level_lean_book_is_adjudicated_not_reported_as_no_evidence` — folded
  into another test in the 07:00Z note; it is separate, and it asserts the
  adjudication *route* (`u3.evaluate` vs `u3.eval_lean_source:Level.lean`), not
  the label.
* `test_FINDING_deadlock_paradigm_on_disk_is_labelled_vacuous` — **the headline
  one.** It asserts exam's F1 finding against the real artefact rather than a
  fixture, and its own docstring says its red is the success signal: *"If
  someone fixes freeze/u3.py this test goes red, which is the correct signal."*
  `assert 'discharged' == 'vacuous'`. The derivation walked past the clearest
  single piece of evidence that the repair reached the paradigm case.

All fifteen that must stay green did, including
`test_frozen_negative_control_on_disk_still_fails` — the loosening did not stop
catching the thing it must catch.

The capture is `exam_u3_census_measured.txt`, and **how** it was captured is
itself a finding worth writing down: the first run, with tracebacks, printed the
absolute path of the test file and of every `tmp_path` fixture, which
`tools/check_locations.py` (stage [18]) is red on for any tracked `runs/` file.
That gate explicitly refuses scrubbing — *"deleting the pattern from a captured
log is not one of the options: it falsifies a third party's output"* — so the
suite was **re-run** with `--tb=no`, which emits no path at all, and the
per-failure assertion messages were taken from a second run with `--tb=line`
(message lines only; those strings carry no path). Nothing was edited. Had this
been handled by scrubbing, or by not noticing, this ticket would have handed the
next session a red [18] on its own run directory.

The letter is
`monitor/inbox/20260801T1200Z-freeze-to-exam-the-flip-list-was-four-measured-it-is-six.md`.
**`exam/` was not edited.**

---

## 3 · The three primary endpoints, restated — verified, not re-ruled

| slot | endpoint | state |
|---|---|---|
| 1 | U3 达成率 | **survives**, in the confirmatory family |
| 2 | 判决题准确率（含特异度） | **survives**, in the confirmatory family |
| 3 | 前载指数配对差 | **WITHDRAWN** 2026-08-01 (`STATS_RULES.md` §3.0) — demoted to exploratory |

**Nothing replaces slot 3, and that is the ruling, not an omission.** Swapping in
the step-axis E2L is refused four independent ways (PREREG_V9's R1 demotes only;
E2L has not passed process 1; E2L is itself reached at 1.0 by
`first-turn-bill-coherent`; `n_paired_games` is 0) — and promoting a new metric
into a primary family *after seeing the attack results* is the exact move §8/§10
mark ✅-sealed.

**Holm's divisor stays 3.** This is the price of the withdrawal and it is
deliberate: dropping it to 2 loosens the tightest level from α/3 to α/2 and the
sign test's entry price from k ≥ 7 to k ≥ 6 — i.e. withdrawing an endpoint
nobody can pass would buy the two survivors a whole game.

`STATS_RULES.md` and `CLAIMS_TEXT.md` agree word for word and both stages that
check it are green: **[16]** (56 checks, 0 hard divergences, 6 negative controls
firing including `*/family`) and **[19]** (`e2_withdrawal.py --verify` plus
`--selftest` 8/8). All three verbatim outcome blocks of C2 — 成立版 / 不成立版 /
不可结论版 — are **retained and rewritten**, each opening with the mandatory
identity sentence that the段 is exploratory and outside the Holm family; outcome
三 B-2 is annotated as demoted. Nothing was deleted.

**The withdrawal is not a repair.** The axis-validity defect lives on in every
front-load number that will still be printed, registered as `E2-AXIS` in
`RESIDUALS.json`, and §10's 封不死 list went from two entries to three so this
retreat cannot pass itself off as a gate.

---

## 4 · The money — recorded, not fixed

`freeze/BUDGET_TABLE.json`, as frozen:

```
ceiling_usd               214.9
programme_measured_usd    250.0687
remaining_measured_usd    -35.1687      <- NEGATIVE
```

Recomputed from the ledgers this session, **read-only, deliberately not written**
(`budget_now.json`):

```
programme_measured_usd    293.8347
remaining_measured_usd    -78.9347
```

So the frozen figure is a **floor on the overspend, not the overspend**.
Regenerating the table was refused for the same reason the 03:00Z ruling refused
it: pinning a balance that is still moving into a freeze kit is the failure
stage [15b] exists to catch, and [15b] red *is* the honest state. **Nothing here
touches the money.** Stop, raise the ceiling, or write off the overrun is the
owner's ruling and it is pending.

### The hold, and why it is derived rather than written

Item 12 (预算表) was already `blocked` — for three ⟨…⟩ placeholders that are
fillable in an afternoon. **That is the whole problem.** If the only thing
between item 12 and `ready` were prose, filling the placeholders would flip the
item green while the programme was still overdrawn, and the manifest would
publish a ready budget for an overdrawn programme.

So `freeze/build_manifest.py` grew `BUDGET_HOLD_ITEMS` and
`apply_budget_hold()`: item 12's published status is forced to `blocked`
whenever `remaining_measured_usd < 0`, and `entries[12].budget_hold` records
which self-declared status it overrode and why. **The number clears the hold;
the prose cannot.** `MANIFEST.json` gained a top-level `budget` block and
`verdict.budget_held_items`, and `verdict.statement` now quotes −35.1687 and
214.9 verbatim in the sentence a reader hits first.

One trade, stated: the block reads the **tracked** table, not the gitignored
ledger, so the manifest still reproduces on any checkout and `--verify` cannot
go red for a tree that is in fact identical. The price is freshness, [15b] is
the instrument for it, and `budget.reading` says so in the artefact.

---

## Gate output

```
$ python -m pytest freeze -q
62 passed in 23.62s                       (52 before, +10 new)

$ cd freeze && bash verify.sh
DRAFT INCOMPLETE -- 2 check(s) failed     (79 PASS / 2 FAIL; baseline 77 / 2)
  FAIL  BUDGET_TABLE.{json,md} no longer recompute from the ledgers
  FAIL  tracked artefacts name a machine without an exemption
```

**Exactly three lines moved between `gates_before.txt` and `gates_after.txt`**,
and a diff of every stage's PASS/FAIL confirms nothing else did:

| stage | before | after | why |
|---|---|---|---|
| **[20]** (new) | — | **PASS + PASS** | the manifest publishes the balance, holds item 12 on it, and the 8 budget-hold controls pass |
| [14] | NOTE 19 blocking gaps | NOTE **20** | the new §12 追记 registers itself as a gap that names who clears it and how |
| everything else | — | byte-identical | including [12] `build_manifest.py --verify` PASS after regeneration, [16] 56 checks / 6 controls, [17], [19] |

**The two FAILs are unchanged from clean `master` and neither is freeze's:**
[15b] is red because the balance moved (see above — leaving it red is the
ruling); [18] names two `theoria-arm/runs/20260801T001851Z-R1b-*` directories,
today's live legs, whose files record absolute paths and which have no dated
allowlist entry. Not this territory's files, not touched.

## Mutation check — the new controls were each seen to say no

`mutations.py` breaks the budget hold seven ways on temporary copies
(`build_manifest.py` is never edited) and requires each break to turn a control
red. A control that cannot be *built* is recorded as a failure, never a skip.

```
baseline (unmutated): rc=0  8/8
PASS M1/always-holds      the hold fires whether or not the balance is negative       -> 3 red
PASS M2/boundary          exact zero counts as over-ceiling                           -> 1 red
PASS M3/silent-block      item 12 is blocked without recording what was overridden    -> 1 red
PASS M4/holds-everything  the hold ignores BUDGET_HOLD_ITEMS and blocks the whole list-> 2 red
PASS M5/paraphrase        the verdict describes the overrun instead of quoting it     -> 1 red
PASS M6/absence-as-zero   a missing budget table reads `not over ceiling`, not unknown-> 1 red
PASS M7/no-table          the positive control points at a table that is not there    -> 1 red
7/7 mutations caught
```

M3 originally produced a **traceback** rather than a red control — a crash tells
a reader the harness broke, not that the guarantee failed, and the two must not
look alike. The controls now take a callable and report a raised exception as
`FAIL … [raised KeyError: …]`. That fix is the reason the mutation script exists.

---

## Residual gaps, stated honestly

1. **The hold reads a stale number by construction.** −35.1687 is frozen;
   −78.9347 is today. Anyone reading `MANIFEST.json` alone sees the smaller
   overrun. `budget.reading` says "FLOOR … not the overspend" and names [15b] as
   the instrument, but a reader who ignores both is misled in the flattering
   direction. Clearing this needs a regeneration of `BUDGET_TABLE.json` at a
   moment when no live run is in flight — a scheduling decision, not a code fix.
2. **The hold is keyed on one item.** `BUDGET_HOLD_ITEMS = (12,)`. It is at
   least arguable that an overdrawn programme should hold the *whole* manifest,
   not one row — `freeze_ready` is already `False` for other reasons, so the
   question is untested today and would become live the moment the other twelve
   items landed. Filed, not decided.
3. **Two surviving endpoints, and today neither is computable.** `endpoints.
   computable_today` is **0**: U3 is blocked on §9.2 / §9.14 / §9.17–§9.20 and
   the adjudication question on §9.15 / §9.16 (the latter a *discrimination*
   defect — `memoriser` scores identically to ground truth — not a gaming one).
   Withdrawing one endpoint did not repair the other two.
4. **§3.0.5's criterion has only ever been seen to say no once.** "A value that
   is a total function of the arm's own record cannot be confirmatory" refused
   the front-load endpoint and cleared the other two. **That it cleared them has
   not been independently checked.** It excludes one disease; it is not a
   physical.
5. **`unsolvable`'s sub-check `c_init_has_action` still has no source-level
   test** (carried from the 07:00Z run, and still not registered in
   `RESIDUALS.json`, whose entries are generated from `declared_at` pointers
   into the frozen `MANIFEST_DRAFT.md`). Every affected verdict carries the
   residual line rather than passing open. Registering it before 开跑 is an ask,
   not a done.
6. **The letter to exam is undelivered.** `monitor/` is tracked, so this
   worktree has a private copy of the inbox; nobody reads that file until this
   branch reaches the mainline.

## Discipline

`exam/` and `battery/` were read only — the exam suite was run in a detached,
read-only worktree that has been removed. `PARTNER_SYNC.md` append-only, own
paragraph only. No credential value in any file. No sealed-pile game id anywhere
in this run. Nothing outside `freeze/` and `monitor/inbox/` was written.
